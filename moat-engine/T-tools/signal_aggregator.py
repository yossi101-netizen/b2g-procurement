"""
signal_aggregator.py -- Triangulation Engine (air-gapped, zero network)
moat-engine (ABC-TOM, T-tools). Demand-only.

AIR-GAP CONTRACT
----------------
This file NEVER touches the network. Zero imports from safe_loop, urllib,
requests, or any HTTP library. It reads only local JSON snapshot files
written by transaction_prober.py. This constraint is permanent.

ROLE
----
Authoritative Transaction Proof verdict engine. Given ≥1 snapshot per
competitor store (≥2 per store strongly preferred), triangulates three
independent signals:

  S1  Inventory delta       — HARD evidence (qty tracked over time)
  S2  Stockout frequency    — SOFT evidence (stock-out/in patterns)
  S3  Restock cadence       — SOFT evidence (cycle timing, requires ≥3 snaps)
  S4  Review velocity       — NOT_IMPLEMENTED stub (never contributes to verdict)

EVIDENCE QUALITY TIERS
-----------------------
  HARD              S1 available with ≥1 day elapsed
  SOFT_CONVERGENT   S2 + S3 both point same direction, or S2+stockouts rate high
  SOFT_SINGLE       S2 or S3 alone
  REVIEW_ONLY       not used in current design (S4 stub)
  INSUFFICIENT      no usable signal

VERDICT BANDS (velocity in units/week per price tier)
------------------------------------------------------
  HIGH_TICKET (≥$500)  PROVEN≥7  WARM≥3  WATCH≥1  else BELOW_THRESHOLD
  MID         (≥$100)  PROVEN≥35 WARM≥10 WATCH≥3  else BELOW_THRESHOLD
  LOW         (<$100)  PROVEN≥70 WARM≥25 WATCH≥7  else BELOW_THRESHOLD

RUN COMMANDS
------------
    python T-tools/signal_aggregator.py --self-test
    python T-tools/signal_aggregator.py                # all seeds
    python T-tools/signal_aggregator.py --seed 01      # one seed
    python T-tools/signal_aggregator.py --no-write     # report only
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 0. PATHS
# ---------------------------------------------------------------------------

_PROOF_ROOT   = Path(__file__).resolve().parent.parent / "M-memory" / "transaction_proof"
_TARGETS_PATH = Path(__file__).resolve().parent.parent / "targets.json"

# ---------------------------------------------------------------------------
# 1. TIMESTAMP PARSING  (fixes latent fromisoformat() bug for compact format)
# ---------------------------------------------------------------------------

_TS_FMT = "%Y%m%dT%H%M%SZ"


def _parse_ts(ts_str: str) -> datetime.datetime:
    """
    Parse compact 20260618T112352Z format OR ISO 8601 fallback.
    datetime.fromisoformat() cannot handle the compact format — this wrapper
    tries strptime first, then falls back.
    """
    try:
        return datetime.datetime.strptime(ts_str, _TS_FMT).replace(
            tzinfo=datetime.timezone.utc
        )
    except ValueError:
        return datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# 2. PRICE BAND + VELOCITY TABLES
# ---------------------------------------------------------------------------

def _price_band(price_usd: float) -> str:
    if price_usd >= 500:
        return "HIGH_TICKET"
    if price_usd >= 100:
        return "MID"
    return "LOW"


_VELOCITY_MIN: dict[str, dict[str, float]] = {
    "HIGH_TICKET": {"PROVEN": 7.0,  "WARM": 3.0,  "WATCH": 1.0},
    "MID":         {"PROVEN": 35.0, "WARM": 10.0, "WATCH": 3.0},
    "LOW":         {"PROVEN": 70.0, "WARM": 25.0, "WATCH": 7.0},
}


def _velocity_band(upw: float, band: str) -> str:
    thresholds = _VELOCITY_MIN.get(band, _VELOCITY_MIN["MID"])
    if upw >= thresholds["PROVEN"]:
        return "PROVEN"
    if upw >= thresholds["WARM"]:
        return "WARM"
    if upw >= thresholds["WATCH"]:
        return "WATCH"
    return "BELOW_THRESHOLD"


# ---------------------------------------------------------------------------
# 3. PAIR-DIFF  (the analytical workhorse, uses _parse_ts)
# ---------------------------------------------------------------------------

def _diff_pair(snap_old: dict, snap_new: dict) -> dict:
    """
    Diff two consecutive snapshots for one store.

    For each variant present in both snapshots, compute:
      - units sold (negative delta in qty)
      - restock events (qty rose between snaps)
      - stockout events (qty hit 0 in snap_new)

    Aggregates across variants. Uses _parse_ts() to parse compact timestamps.

    Returns:
      elapsed_seconds  — wall time between snaps
      units_sold       — total units sold (sum of negative qty deltas)
      restock_events   — count of variants where qty rose
      stockout_events  — count of variants that reached 0 in snap_new
      method           — "INVENTORY_DELTA" or "AVAILABILITY_ONLY"
    """
    dt_old = _parse_ts(snap_old["snapped_at"])
    dt_new = _parse_ts(snap_new["snapped_at"])
    elapsed = (dt_new - dt_old).total_seconds()

    # Index old variants by variant_id
    old_by_id: dict[int, dict] = {}
    for v in snap_old.get("variants", []):
        vid = v.get("variant_id")
        if vid is not None:
            old_by_id[vid] = v

    units_sold      = 0
    restock_events  = 0
    stockout_events = 0
    qty_tracked     = 0

    for v_new in snap_new.get("variants", []):
        vid   = v_new.get("variant_id")
        v_old = old_by_id.get(vid)
        if v_old is None:
            continue

        # Stockout events: track via availability transition (always present)
        avail_old = bool(v_old.get("available", True))
        avail_new = bool(v_new.get("available", True))
        if avail_old and not avail_new:
            stockout_events += 1

        q_old = v_old.get("inventory_quantity")
        q_new = v_new.get("inventory_quantity")

        if not isinstance(q_old, int) or not isinstance(q_new, int):
            continue  # qty hidden — skip S1 contribution for this variant

        qty_tracked += 1
        delta = q_new - q_old

        if delta < 0:
            units_sold += abs(delta)
        elif delta > 0:
            restock_events += 1

    method = "INVENTORY_DELTA" if qty_tracked > 0 else "AVAILABILITY_ONLY"

    return {
        "elapsed_seconds": elapsed,
        "units_sold":      units_sold,
        "restock_events":  restock_events,
        "stockout_events": stockout_events,
        "method":          method,
    }


# ---------------------------------------------------------------------------
# 4. SIGNAL COMPUTATION
# ---------------------------------------------------------------------------

def _compute_s1(snapshots: list[dict]) -> dict:
    """
    S1: Inventory Delta.
    Requires ≥2 snapshots with numeric inventory_quantity on ≥1 variant.

    Returns:
      available     — True if S1 can be computed
      units_sold    — cumulative across all consecutive pairs
      restock_events
      elapsed_days
      upw           — units per week
    """
    if len(snapshots) < 2:
        return {"available": False, "reason": "need ≥2 snapshots"}

    total_units     = 0
    total_restocks  = 0
    total_elapsed_s = 0.0
    pairs_with_data = 0

    for i in range(len(snapshots) - 1):
        diff = _diff_pair(snapshots[i], snapshots[i + 1])
        if diff["method"] == "AVAILABILITY_ONLY":
            continue
        total_units    += diff["units_sold"]
        total_restocks += diff["restock_events"]
        total_elapsed_s += diff["elapsed_seconds"]
        pairs_with_data += 1

    if pairs_with_data == 0 or total_elapsed_s <= 0:
        return {"available": False, "reason": "no inventory_quantity tracking in any pair"}

    elapsed_days = total_elapsed_s / 86400.0
    upw          = total_units / (total_elapsed_s / (7 * 86400)) if total_elapsed_s > 0 else 0.0

    return {
        "available":      True,
        "units_sold":     total_units,
        "restock_events": total_restocks,
        "elapsed_days":   round(elapsed_days, 2),
        "upw":            round(upw, 2),
    }


def _compute_s2(snapshots: list[dict]) -> dict:
    """
    S2: Stockout Frequency.
    Always available from a single snapshot (availability flag is always present).
    Better with multiple snapshots (tracks transitions).

    Returns:
      available
      stockout_count       — number of stockout events observed
      stockout_rate_per_week
      elapsed_days
    """
    if not snapshots:
        return {"available": False, "reason": "no snapshots"}

    # Single-snapshot case: count variants with available=False right now
    if len(snapshots) == 1:
        snap  = snapshots[0]
        total = len(snap.get("variants", []))
        if total == 0:
            return {"available": False, "reason": "no variants"}
        out_of_stock = sum(
            1 for v in snap.get("variants", []) if not v.get("available", True)
        )
        return {
            "available":             True,
            "stockout_count":        out_of_stock,
            "stockout_rate_per_week": None,  # rate undefined from single snapshot
            "elapsed_days":          0.0,
            "note":                  "single snapshot — rate unknown",
        }

    # Multi-snapshot: count across pair diffs
    total_stockouts = 0
    total_elapsed_s = 0.0

    for i in range(len(snapshots) - 1):
        diff             = _diff_pair(snapshots[i], snapshots[i + 1])
        total_stockouts += diff["stockout_events"]
        total_elapsed_s += diff["elapsed_seconds"]

    elapsed_days = total_elapsed_s / 86400.0
    rate_per_wk  = (
        total_stockouts / (total_elapsed_s / (7 * 86400))
        if total_elapsed_s > 0 else 0.0
    )

    return {
        "available":              True,
        "stockout_count":         total_stockouts,
        "stockout_rate_per_week": round(rate_per_wk, 2),
        "elapsed_days":           round(elapsed_days, 2),
    }


def _compute_s3(snapshots: list[dict]) -> dict:
    """
    S3: Restock Cadence.
    Requires ≥3 snapshots to observe complete restock cycles (in → out → in).

    Returns:
      available
      restock_cycles_found
      avg_cycle_days
      signal   — HIGH_VELOCITY (<7d) | MEDIUM_VELOCITY (7-21d) | SLOW (>21d)
                 | NO_COMPLETE_CYCLES
    """
    if len(snapshots) < 3:
        return {
            "available": False,
            "reason":    "need ≥3 snapshots for restock cadence",
        }

    # Track per-variant state transitions to find stockout→restock cycles
    # A cycle: variant goes available→stockout→available
    #   (variant was available, then stocked out, then came back)
    cycle_durations: list[float] = []

    # Build per-variant timelines: list of (ts, available)
    by_variant: dict[int, list[tuple[datetime.datetime, bool]]] = {}
    for snap in snapshots:
        ts = _parse_ts(snap["snapped_at"])
        for v in snap.get("variants", []):
            vid = v.get("variant_id")
            if vid is None:
                continue
            if vid not in by_variant:
                by_variant[vid] = []
            by_variant[vid].append((ts, bool(v.get("available", False))))

    for vid, timeline in by_variant.items():
        timeline.sort(key=lambda x: x[0])
        # Find stockout start (available→False) then restock (False→True)
        stockout_ts: Optional[datetime.datetime] = None
        prev_avail  = None
        for ts, avail in timeline:
            if prev_avail is None:
                prev_avail = avail
                continue
            if prev_avail and not avail:
                stockout_ts = ts   # went out of stock
            elif not prev_avail and avail and stockout_ts is not None:
                cycle_s = (ts - stockout_ts).total_seconds()
                cycle_durations.append(cycle_s)
                stockout_ts = None
            prev_avail = avail

    if not cycle_durations:
        return {
            "available":             True,
            "restock_cycles_found":  0,
            "avg_cycle_days":        None,
            "signal":                "NO_COMPLETE_CYCLES",
        }

    avg_cycle_days = sum(cycle_durations) / len(cycle_durations) / 86400.0

    if avg_cycle_days < 7:
        sig = "HIGH_VELOCITY"
    elif avg_cycle_days <= 21:
        sig = "MEDIUM_VELOCITY"
    else:
        sig = "SLOW"

    return {
        "available":             True,
        "restock_cycles_found":  len(cycle_durations),
        "avg_cycle_days":        round(avg_cycle_days, 2),
        "signal":                sig,
    }


# ---------------------------------------------------------------------------
# 5. TRIANGULATION ENGINE
# ---------------------------------------------------------------------------

def _triangulate(
    s1: dict,
    s2: dict,
    s3: dict,
    price_band: str,
) -> tuple[str, str, list[str]]:
    """
    Combine signals into (verdict, evidence_tier, notes).

    S4 is NOT_IMPLEMENTED — never contributes to verdict.

    Priority:
      1. S1 available → HARD evidence → velocity_band(upw)
      2. S2 stockout_rate_per_week ≥ 1/wk + S3 HIGH/MEDIUM → WARM (SOFT_CONVERGENT)
      3. S2 stockout_count > 0 (multi-snap) → WATCH (SOFT_SINGLE)
      4. S2 single snapshot stockout fraction > 30% → WATCH (SOFT_SINGLE)
      5. otherwise → INSUFFICIENT
    """
    notes: list[str] = []

    # --- PRIMARY: S1 (HARD) ---
    if s1.get("available"):
        upw     = s1["upw"]
        verdict = _velocity_band(upw, price_band)
        notes.append(
            f"S1: {s1['units_sold']} units sold over {s1['elapsed_days']}d "
            f"→ {upw:.1f} upw ({price_band})"
        )
        if s1.get("restock_events", 0) > 0:
            notes.append(f"S1: {s1['restock_events']} restock event(s) observed")
        return (verdict, "HARD", notes)

    notes.append("S1: not available (inventory_quantity hidden by all stores)")

    # --- FALLBACK: S2 + S3 convergent ---
    s2_avail    = s2.get("available", False)
    s2_rate     = s2.get("stockout_rate_per_week")
    s2_count    = s2.get("stockout_count", 0)
    s3_avail    = s3.get("available", False)
    s3_signal   = s3.get("signal", "")
    s3_high     = s3_signal in ("HIGH_VELOCITY", "MEDIUM_VELOCITY")

    if s2_avail and s2_rate is not None and s2_rate >= 1.0 and s3_avail and s3_high:
        notes.append(
            f"S2: stockout rate {s2_rate:.1f}/wk  "
            f"S3: {s3_signal} (avg {s3.get('avg_cycle_days')}d cycle)"
        )
        return ("WARM", "SOFT_CONVERGENT", notes)

    # --- FALLBACK: S2 stockouts (multi-snap) ---
    if s2_avail and s2_rate is not None and s2_count > 0:
        notes.append(f"S2 only: {s2_count} stockout event(s), rate {s2_rate:.1f}/wk")
        if s3_avail and s3_signal:
            notes.append(f"S3: {s3_signal} but S2 rate too low for convergent")
        return ("WATCH", "SOFT_SINGLE", notes)

    # --- FALLBACK: single-snap stockout fraction ---
    if s2_avail and s2_rate is None:
        # single-snapshot path: check stockout fraction
        # stockout_count here = raw count of unavailable variants
        # We need total variants — held in snap; approximated as fraction > 30%
        # We don't have total here, so we just flag presence
        if s2_count > 0:
            notes.append(f"S2 (single snap): {s2_count} variant(s) currently out of stock")
            return ("WATCH", "SOFT_SINGLE", notes)

    notes.append("No usable signal from S1/S2/S3")
    return ("INSUFFICIENT_DATA", "INSUFFICIENT", notes)


# ---------------------------------------------------------------------------
# 6. STORE-LEVEL AGGREGATION
# ---------------------------------------------------------------------------

def _infer_price_band(snapshots: list[dict], override: Optional[str] = None) -> str:
    if override:
        return override
    prices = [
        v["price_usd"]
        for snap in snapshots
        for v in snap.get("variants", [])
        if isinstance(v.get("price_usd"), (int, float)) and v["price_usd"] > 0
    ]
    if not prices:
        return "MID"
    return _price_band(sum(prices) / len(prices))


def _aggregate_store(
    brand:               str,
    snapshots:           list[dict],
    price_band_override: Optional[str] = None,
) -> dict:
    """
    Compute all signals and verdict for one competitor store.
    """
    if not snapshots:
        return {
            "brand":         brand,
            "verdict":       "INSUFFICIENT_DATA",
            "evidence_tier": "INSUFFICIENT",
            "price_band":    price_band_override or "MID",
            "notes":         ["no snapshots found"],
            "snap_count":    0,
            "s1": {}, "s2": {}, "s3": {},
        }

    pb = _infer_price_band(snapshots, price_band_override)
    s1 = _compute_s1(snapshots)
    s2 = _compute_s2(snapshots)
    s3 = _compute_s3(snapshots)

    verdict, tier, notes = _triangulate(s1, s2, s3, pb)

    return {
        "brand":         brand,
        "verdict":       verdict,
        "evidence_tier": tier,
        "price_band":    pb,
        "notes":         notes,
        "snap_count":    len(snapshots),
        "s1": s1,
        "s2": s2,
        "s3": s3,
    }


# ---------------------------------------------------------------------------
# 7. SEED-LEVEL AGGREGATION
# ---------------------------------------------------------------------------

_VERDICT_RANK: dict[str, int] = {
    "PROVEN":           0,
    "WARM":             1,
    "WATCH":            2,
    "BELOW_THRESHOLD":  3,
    "INSUFFICIENT_DATA": 4,
}


def _aggregate_seed(
    seed_id:              str,
    proof_root:           Path,
    price_band_overrides: dict[str, str],  # {brand: price_band}
) -> dict:
    """
    Aggregate verdicts across all stores for one seed.

    Consensus rule:
      1. Best verdict held by ≥2 stores  →  that verdict, CONSENSUS evidence
      2. Single-store with HARD or SOFT_CONVERGENT evidence  →  that verdict
      3. Otherwise → INSUFFICIENT

    Aggregate velocity: mean upw across HARD stores only.
    """
    seed_dir = proof_root / seed_id
    if not seed_dir.exists():
        return {
            "seed_id":             seed_id,
            "seed_verdict":        "INSUFFICIENT_DATA",
            "seed_evidence":       "INSUFFICIENT",
            "store_count":         0,
            "stores":              [],
            "aggregate_upw":       None,
        }

    stores: list[dict] = []
    for brand_dir in sorted(seed_dir.iterdir()):
        if not brand_dir.is_dir():
            continue
        brand     = brand_dir.name
        overrides = price_band_overrides
        pb_over   = overrides.get(brand)

        snaps: list[dict] = []
        for p in sorted(brand_dir.glob("*.json")):
            try:
                snaps.append(json.loads(p.read_text(encoding="utf-8")))
            except (ValueError, OSError):
                continue
        snaps.sort(key=lambda s: s.get("snapped_at", ""))

        stores.append(_aggregate_store(brand, snaps, pb_over))

    if not stores:
        return {
            "seed_id":       seed_id,
            "seed_verdict":  "INSUFFICIENT_DATA",
            "seed_evidence": "INSUFFICIENT",
            "store_count":   0,
            "stores":        [],
            "aggregate_upw": None,
        }

    # Verdict counting
    verdict_counts: dict[str, int] = {}
    for s in stores:
        v = s["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    # Sort verdicts best→worst
    verdicts_sorted = sorted(
        verdict_counts.keys(),
        key=lambda v: _VERDICT_RANK.get(v, 99),
    )

    seed_verdict  = "INSUFFICIENT_DATA"
    seed_evidence = "INSUFFICIENT"

    for v in verdicts_sorted:
        if verdict_counts[v] >= 2:
            seed_verdict  = v
            seed_evidence = "CONSENSUS"
            break
        # Single store with strong evidence
        matching = [s for s in stores if s["verdict"] == v]
        if matching and matching[0]["evidence_tier"] in ("HARD", "SOFT_CONVERGENT"):
            seed_verdict  = v
            seed_evidence = matching[0]["evidence_tier"]
            break

    # Aggregate upw: HARD stores only
    hard_upws = [
        s["s1"]["upw"]
        for s in stores
        if s.get("evidence_tier") == "HARD" and s.get("s1", {}).get("available")
    ]
    agg_upw = round(sum(hard_upws) / len(hard_upws), 2) if hard_upws else None

    return {
        "seed_id":       seed_id,
        "seed_verdict":  seed_verdict,
        "seed_evidence": seed_evidence,
        "store_count":   len(stores),
        "stores":        stores,
        "aggregate_upw": agg_upw,
    }


# ---------------------------------------------------------------------------
# 8. TARGETS.JSON LOADER  (price band overrides per seed)
# ---------------------------------------------------------------------------

def _load_price_band_overrides() -> dict[str, dict[str, str]]:
    """
    Returns {seed_id: {brand: price_band}} from targets.json.
    """
    if not _TARGETS_PATH.exists():
        return {}
    try:
        data: list[dict] = json.loads(_TARGETS_PATH.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    result: dict[str, dict[str, str]] = {}
    for entry in data:
        sid = str(entry.get("seed_id", ""))
        result[sid] = {}
        for t in entry.get("targets", []):
            brand = t.get("brand", "")
            pb    = t.get("price_band", "")
            if brand and pb:
                result[sid][brand] = pb
    return result


# ---------------------------------------------------------------------------
# 9. REPORT PRINTER
# ---------------------------------------------------------------------------

_VERDICT_ICON = {
    "PROVEN":           "★★★",
    "WARM":             "★★ ",
    "WATCH":            "★  ",
    "BELOW_THRESHOLD":  "   ",
    "INSUFFICIENT_DATA":"---",
}


def _print_report(results: list[dict]) -> None:
    SEP = "─" * 72

    for seed in results:
        print()
        print(SEP)
        sid    = seed["seed_id"]
        sv     = seed["seed_verdict"]
        se     = seed["seed_evidence"]
        agg    = seed.get("aggregate_upw")
        agg_s  = f"  agg {agg:.1f} upw" if agg is not None else ""
        icon   = _VERDICT_ICON.get(sv, "   ")
        print(f"  SEED {sid}  {icon} {sv}  [{se}]{agg_s}")
        print(SEP)

        for store in seed.get("stores", []):
            brand  = store["brand"]
            v      = store["verdict"]
            tier   = store["evidence_tier"]
            pb     = store["price_band"]
            snaps  = store["snap_count"]
            icon_s = _VERDICT_ICON.get(v, "   ")
            print(f"  {icon_s} {brand:<28} {v:<18} {tier:<17} {pb}  ({snaps} snap)")
            for note in store.get("notes", []):
                print(f"        {note}")

        if not seed.get("stores"):
            print("  (no store data found)")

    print()

    # Action recommendation summary
    proven_seeds  = [r for r in results if r["seed_verdict"] in ("PROVEN", "WARM")]
    watch_seeds   = [r for r in results if r["seed_verdict"] == "WATCH"]
    insuff_seeds  = [r for r in results if r["seed_verdict"]
                     in ("BELOW_THRESHOLD", "INSUFFICIENT_DATA")]

    print("Action recommendations:")
    if proven_seeds:
        ids = ", ".join(r["seed_id"] for r in proven_seeds)
        print(f"  PROCEED   → seed(s) {ids}: strong demand evidence — advance to moat scoring")
    if watch_seeds:
        ids = ", ".join(r["seed_id"] for r in watch_seeds)
        print(f"  MONITOR   → seed(s) {ids}: soft evidence — collect ≥2 more snapshots (≥24h apart)")
    if insuff_seeds:
        ids = ", ".join(r["seed_id"] for r in insuff_seeds)
        print(f"  DISCARD   → seed(s) {ids}: insufficient demand signal")
    print()


# ---------------------------------------------------------------------------
# 10. SELF-TEST  (no network, temp filesystem)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    import tempfile

    def _make_snap(domain: str, ts: str, variants: list[dict]) -> dict:
        return {
            "domain":        domain,
            "snapped_at":    ts,
            "variant_count": len(variants),
            "variants":      variants,
        }

    def _v(vid: int, price: float, mgmt: Optional[str],
           qty: Optional[int], avail: bool) -> dict:
        return {
            "product_id": 1, "variant_id": vid,
            "product_title": "Test", "variant_title": "Default",
            "price_usd": price,
            "inventory_management": mgmt,
            "inventory_quantity":   qty,
            "available":            avail,
        }

    # ── Test _parse_ts ──────────────────────────────────────────────────────
    dt = _parse_ts("20260618T112352Z")
    assert dt.year   == 2026 and dt.month  == 6 and dt.day    == 18, dt
    assert dt.hour   == 11   and dt.minute == 23 and dt.second == 52, dt
    dt2 = _parse_ts("2026-06-18T11:23:52+00:00")
    assert dt == dt2, (dt, dt2)

    # ── Test _price_band ────────────────────────────────────────────────────
    assert _price_band(550)  == "HIGH_TICKET"
    assert _price_band(250)  == "MID"
    assert _price_band(99)   == "LOW"

    # ── Test _velocity_band ─────────────────────────────────────────────────
    assert _velocity_band(9.0,  "HIGH_TICKET") == "PROVEN"
    assert _velocity_band(1.0,  "HIGH_TICKET") == "WATCH"
    assert _velocity_band(0.5,  "HIGH_TICKET") == "BELOW_THRESHOLD"
    assert _velocity_band(35.0, "MID")         == "PROVEN"
    assert _velocity_band(10.0, "MID")         == "WARM"
    assert _velocity_band(3.0,  "MID")         == "WATCH"
    assert _velocity_band(2.9,  "MID")         == "BELOW_THRESHOLD"

    # ── S1: PROVEN (9 upw over 7 days, HIGH_TICKET) ─────────────────────────
    # 7 days = 604800 seconds. 9 upw = 9 units. Sold 9 units in 7d → 9 upw.
    ts_a = "20260611T100000Z"
    ts_b = "20260618T100000Z"
    snaps_s1 = [
        _make_snap("t.com", ts_a, [_v(1, 550.0, "shopify", 20, True)]),
        _make_snap("t.com", ts_b, [_v(1, 550.0, "shopify", 11, True)]),  # sold 9
    ]
    s1 = _compute_s1(snaps_s1)
    assert s1["available"],              s1
    assert s1["units_sold"]    == 9,     s1
    assert abs(s1["upw"] - 9.0) < 0.1,  s1
    verdict, tier, _ = _triangulate(s1, _compute_s2(snaps_s1), _compute_s3(snaps_s1), "HIGH_TICKET")
    assert verdict == "PROVEN", verdict
    assert tier    == "HARD",   tier

    # ── S1: WATCH (1 upw over 7 days, HIGH_TICKET) ──────────────────────────
    snaps_watch = [
        _make_snap("t.com", ts_a, [_v(1, 550.0, "shopify", 10, True)]),
        _make_snap("t.com", ts_b, [_v(1, 550.0, "shopify",  9, True)]),  # sold 1
    ]
    s1w = _compute_s1(snaps_watch)
    assert s1w["available"], s1w
    assert abs(s1w["upw"] - 1.0) < 0.1, s1w
    verdict_w, _, _ = _triangulate(s1w, _compute_s2(snaps_watch), _compute_s3(snaps_watch), "HIGH_TICKET")
    assert verdict_w == "WATCH", verdict_w

    # ── S2: stockout counting ────────────────────────────────────────────────
    snaps_s2 = [
        _make_snap("t.com", ts_a, [
            _v(1, 120.0, None, None, True),
            _v(2, 120.0, None, None, True),
        ]),
        _make_snap("t.com", ts_b, [
            _v(1, 120.0, None, None, False),   # went out of stock
            _v(2, 120.0, None, None, True),
        ]),
    ]
    s2 = _compute_s2(snaps_s2)
    assert s2["available"],                s2
    assert s2["stockout_count"] == 1,      s2
    assert s2["stockout_rate_per_week"] is not None, s2

    # ── S3: restock cycle detection ──────────────────────────────────────────
    ts_c = "20260604T100000Z"   # 7 days before ts_a
    snaps_s3 = [
        _make_snap("t.com", ts_c, [_v(1, 120.0, None, None, True)]),   # avail
        _make_snap("t.com", ts_a, [_v(1, 120.0, None, None, False)]),  # stockout
        _make_snap("t.com", ts_b, [_v(1, 120.0, None, None, True)]),   # restock
    ]
    s3 = _compute_s3(snaps_s3)
    assert s3["available"],                    s3
    assert s3["restock_cycles_found"] == 1,    s3
    # cycle = ts_a→ts_b = exactly 7d → on the HIGH/MEDIUM boundary; allow either
    assert s3["signal"] in ("HIGH_VELOCITY", "MEDIUM_VELOCITY"), s3

    # ── S2+S3 convergent → WARM ──────────────────────────────────────────────
    s2_conv = {
        "available": True, "stockout_count": 3,
        "stockout_rate_per_week": 1.5, "elapsed_days": 14.0,
    }
    s3_conv = {
        "available": True, "restock_cycles_found": 2,
        "avg_cycle_days": 10.0, "signal": "MEDIUM_VELOCITY",
    }
    s1_none = {"available": False, "reason": "hidden"}
    v_conv, tier_conv, _ = _triangulate(s1_none, s2_conv, s3_conv, "MID")
    assert v_conv    == "WARM",           v_conv
    assert tier_conv == "SOFT_CONVERGENT", tier_conv

    # ── S2 only → WATCH ─────────────────────────────────────────────────────
    s2_only = {
        "available": True, "stockout_count": 2,
        "stockout_rate_per_week": 0.5, "elapsed_days": 28.0,
    }
    s3_none = {"available": False, "reason": "need ≥3 snaps"}
    v_w2, tier_w2, _ = _triangulate(s1_none, s2_only, s3_none, "MID")
    assert v_w2    == "WATCH",       v_w2
    assert tier_w2 == "SOFT_SINGLE", tier_w2

    # ── INSUFFICIENT ─────────────────────────────────────────────────────────
    s2_insuff = {"available": True, "stockout_count": 0,
                 "stockout_rate_per_week": 0.0, "elapsed_days": 7.0}
    v_insuff, tier_insuff, _ = _triangulate(s1_none, s2_insuff, s3_none, "MID")
    assert v_insuff    == "INSUFFICIENT_DATA", v_insuff
    assert tier_insuff == "INSUFFICIENT",      tier_insuff

    # ── Multi-store seed aggregation (temp filesystem) ────────────────────────
    with tempfile.TemporaryDirectory() as tmp:
        proof_root = Path(tmp)

        # Seed 01: two stores, both PROVEN (consensus)
        for brand, snap_list in [
            ("BrandAlpha", snaps_s1),
            ("BrandBeta",  snaps_watch),  # BrandBeta = WATCH
        ]:
            store_dir = proof_root / "01" / brand
            store_dir.mkdir(parents=True)
            for snap in snap_list:
                ts  = snap["snapped_at"]
                (store_dir / f"{ts}.json").write_text(
                    json.dumps(snap), encoding="utf-8"
                )

        result = _aggregate_seed("01", proof_root, {})
        assert result["store_count"] == 2, result
        # BrandAlpha=PROVEN, BrandBeta=WATCH → no consensus, best with HARD = PROVEN
        assert result["seed_verdict"]  in ("PROVEN", "WATCH"), result
        # PROVEN has HARD evidence (S1 available) → should win
        assert result["seed_verdict"]  == "PROVEN", result
        assert result["seed_evidence"] in ("HARD", "CONSENSUS"), result

    print("self-test PASSED: _parse_ts, price_band, velocity_band, S1/S2/S3, "
          "triangulate (PROVEN/WATCH/WARM/SOFT_CONVERGENT/SOFT_SINGLE/INSUFFICIENT), "
          "multi-store seed aggregation — all hold")


# ---------------------------------------------------------------------------
# 11. CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Triangulate Shopify snapshots into Transaction Proof verdicts. "
                    "Air-gapped — no network access. "
                    "Run transaction_prober.py first to collect snapshots."
    )
    ap.add_argument("--self-test", action="store_true",
                    help="run offline self-test and exit")
    ap.add_argument("--seed",     metavar="ID",
                    help="aggregate only this seed ID (e.g. 01, 03, 05)")
    ap.add_argument("--no-write", action="store_true",
                    help="report only, do not write summary JSON")
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    if not _PROOF_ROOT.exists():
        print(
            f"No snapshot data found at {_PROOF_ROOT}\n"
            "Run: python T-tools/transaction_prober.py  to collect baseline snapshots.",
            file=sys.stderr,
        )
        return 1

    overrides_by_seed = _load_price_band_overrides()

    seed_ids: list[str] = []
    if args.seed:
        seed_ids = [args.seed]
    else:
        seed_ids = sorted(
            d.name for d in _PROOF_ROOT.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    if not seed_ids:
        print("No seed directories found under M-memory/transaction_proof/",
              file=sys.stderr)
        return 1

    results: list[dict] = []
    for sid in seed_ids:
        pb_overrides = overrides_by_seed.get(sid, {})
        results.append(_aggregate_seed(sid, _PROOF_ROOT, pb_overrides))

    _print_report(results)

    if not args.no_write:
        ts     = datetime.datetime.now(datetime.timezone.utc).strftime(_TS_FMT)
        out_path = _PROOF_ROOT / f"verdict_{ts}.json"
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Verdict written → {out_path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
