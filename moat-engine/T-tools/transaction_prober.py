"""
transaction_prober.py -- Shopify Snapshot Collector (pure data, no analysis)
moat-engine (ABC-TOM, T-tools). Demand-only.

ROLE AFTER PHASE 3 REFACTOR
-----------------------------
This file is a DUMB DATA COLLECTOR. It has zero analytical opinion.
All signal computation and verdicts live exclusively in signal_aggregator.py.

What it does:
  1. GET https://<domain>/products.json?limit=250&page=N  (up to 3 pages)
  2. Extract per-variant state: price, inventory_management, inventory_quantity, available
  3. Persist snapshot → M-memory/transaction_proof/<seed_id>/<brand>/<ts>.json
  4. Write a run manifest → M-memory/transaction_proof/<seed_id>/run_<ts>.json
     (summary of what was collected — no verdicts, no velocity, no scoring)

After collecting ≥2 snapshots spaced ≥24h apart, run signal_aggregator.py
to triangulate signals and produce an authoritative Transaction Proof verdict.

RUN COMMANDS
------------
    python T-tools/transaction_prober.py --self-test    # offline verification
    python T-tools/transaction_prober.py                # snapshot all HOT seeds
    python T-tools/transaction_prober.py --seed 01      # one seed only
    python T-tools/transaction_prober.py --dry-run      # fetch + print, no disk writes
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from safe_loop import (
    BudgetExceeded,
    GuardedFetcher,
    KillSwitchEngaged,
    RateLimited,
    default_config,
    default_state_dir,
)


# ---------------------------------------------------------------------------
# 0. PATHS + CONSTANTS
# ---------------------------------------------------------------------------

_PROOF_ROOT  = Path(__file__).resolve().parent.parent / "M-memory" / "transaction_proof"
_TARGETS_PATH = Path(__file__).resolve().parent.parent / "targets.json"

_PRODUCTS_ENDPOINT = "/products.json"
_PAGE_LIMIT = 250


# ---------------------------------------------------------------------------
# 1. SHOPIFY FETCH  (sole network-touching layer)
# ---------------------------------------------------------------------------

def make_shopify_fetch_fn(domain: str) -> Callable[[dict], Any]:
    """
    Return a fetch_fn for GuardedFetcher that GETs a Shopify JSON endpoint.
    params must include 'path'; optionally 'page' and 'limit'.
    domain is the bare hostname (no https:// prefix).
    """
    def _fetch(params: dict) -> Any:
        path  = params["path"]
        page  = params.get("page", 1)
        limit = params.get("limit", _PAGE_LIMIT)
        url   = f"https://{domain}{path}?limit={limit}&page={page}"
        req   = urllib.request.Request(
            url,
            headers={"User-Agent": "moat-engine/1.0 demand-research"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = float(exc.headers.get("Retry-After", 60))
                raise RateLimited(f"Shopify {domain} 429", retry_after=retry_after) from exc
            if exc.code in (401, 403):
                raise RuntimeError(
                    f"{domain!r} returned HTTP {exc.code}: store locked or /products.json disabled"
                ) from exc
            raise
    return _fetch


# ---------------------------------------------------------------------------
# 2. SNAPSHOT: parse + persist
# ---------------------------------------------------------------------------

def _extract_variants(payload: dict) -> list[dict]:
    """
    Flatten all variants from a /products.json response into a list of dicts.
    inventory_quantity is None when the store does not expose it
    (inventory_management != "shopify" or native tracking disabled).
    """
    variants: list[dict] = []
    for product in payload.get("products", []):
        pid    = product.get("id")
        ptitle = product.get("title", "")
        for v in product.get("variants", []):
            try:
                price_usd = float(v.get("price") or 0)
            except (ValueError, TypeError):
                price_usd = 0.0
            variants.append({
                "product_id":           pid,
                "variant_id":           v.get("id"),
                "product_title":        ptitle,
                "variant_title":        v.get("title", ""),
                "price_usd":            price_usd,
                "inventory_management": v.get("inventory_management"),
                "inventory_quantity":   v.get("inventory_quantity"),  # None = hidden
                "available":            bool(v.get("available", False)),
            })
    return variants


def _make_snapshot(domain: str, variants: list[dict], ts: str) -> dict:
    return {
        "domain":        domain,
        "snapped_at":    ts,
        "variant_count": len(variants),
        "variants":      variants,
    }


def _snapshot_dir(proof_root: Path, seed_id: str, brand: str) -> Path:
    d = proof_root / seed_id / brand
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_snapshots(proof_root: Path, seed_id: str, brand: str) -> list[dict]:
    """Load all persisted snapshots for one store, sorted oldest-first."""
    snap_dir = proof_root / seed_id / brand
    if not snap_dir.exists():
        return []
    snaps: list[dict] = []
    for p in sorted(snap_dir.glob("*.json")):
        try:
            snaps.append(json.loads(p.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    snaps.sort(key=lambda s: s.get("snapped_at", ""))
    return snaps


# ---------------------------------------------------------------------------
# 3. PROBE ONE STORE  (collect + persist, no analysis)
# ---------------------------------------------------------------------------

def _probe_store(
    target:     dict,
    seed_id:    str,
    gf:         GuardedFetcher,
    proof_root: Path,
    ts_now:     str,
    dry_run:    bool = False,
) -> dict:
    """
    Fetch a fresh /products.json snapshot for one competitor store and persist it.
    Returns a brief status dict (no velocity, no verdict — that belongs to signal_aggregator).
    """
    domain = target["domain"]
    brand  = target["brand"]
    fetch_fn = make_shopify_fetch_fn(domain)
    all_variants: list[dict] = []

    for page in range(1, 4):   # hard cap: 3 pages = 750 products maximum
        params = {"path": _PRODUCTS_ENDPOINT, "page": page, "limit": _PAGE_LIMIT}
        try:
            payload = gf.fetch(
                provider="shopify",
                endpoint=f"{domain}{_PRODUCTS_ENDPOINT}",
                params=params,
                fetch_fn=fetch_fn,
                ttl=3 * 24 * 3600,
                cost=0.0,
            )
        except (KillSwitchEngaged, BudgetExceeded):
            raise
        except Exception as exc:
            print(f"     WARNING ({brand}): {exc}", file=sys.stderr)
            break

        page_variants = _extract_variants(payload)
        if not page_variants:
            break
        all_variants.extend(page_variants)
        if len(payload.get("products", [])) < _PAGE_LIMIT:
            break   # reached last page

    if not all_variants:
        return {
            "brand":  brand,
            "domain": domain,
            "status": "NO_DATA",
            "error":  "no variants returned (store locked, empty, or /products.json disabled)",
        }

    snapshot = _make_snapshot(domain, all_variants, ts_now)

    if not dry_run:
        snap_dir  = _snapshot_dir(proof_root, seed_id, brand)
        snap_path = snap_dir / f"{ts_now}.json"
        snap_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        snap_count = len(list(snap_dir.glob("*.json")))
        print(f"     saved: {snap_path.name}  "
              f"({len(all_variants)} variants, {snap_count} total snapshot(s) for this store)")
    else:
        print(f"     [dry-run] {len(all_variants)} variants — snapshot not written")

    return {
        "brand":         brand,
        "domain":        domain,
        "status":        "OK",
        "variant_count": len(all_variants),
    }


# ---------------------------------------------------------------------------
# 4. RUN PROBE  (seed-level orchestration, no verdict)
# ---------------------------------------------------------------------------

def run_probe(
    seed_id:    str,
    targets:    list[dict],
    gf:         GuardedFetcher,
    proof_root: Path = _PROOF_ROOT,
    *,
    dry_run:    bool = False,
) -> dict:
    """
    Collect snapshots for all competitor stores assigned to one seed.
    Writes a run manifest (what was collected, no verdict) and returns it.
    Run signal_aggregator.py after ≥2 runs to produce the authoritative verdict.
    """
    ts_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"\n[seed {seed_id}] Snapshot collection — {len(targets)} target(s)  @{ts_now}")

    per_store: list[dict] = []
    for t in targets:
        print(f"  → {t['brand']} ({t['domain']})")
        result = _probe_store(t, seed_id, gf, proof_root, ts_now, dry_run=dry_run)
        per_store.append(result)

    ok_count = sum(1 for s in per_store if s.get("status") == "OK")
    print(f"  Collection complete: {ok_count}/{len(targets)} stores OK")

    manifest = {
        "seed_id":          seed_id,
        "run_at":           ts_now,
        "stores_attempted": len(targets),
        "stores_ok":        ok_count,
        "per_store":        per_store,
    }

    if not dry_run:
        seed_dir = proof_root / seed_id
        seed_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = seed_dir / f"run_{ts_now}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest


# ---------------------------------------------------------------------------
# 5. SELF-TEST  (extraction and snapshot mechanics — no analysis)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """
    Offline verification of:
      1. _extract_variants: parses Shopify /products.json response correctly
      2. _make_snapshot: assembles correct structure
      3. Snapshot round-trip: save to disk + load back sorted
    No network calls. No analysis logic (that lives in signal_aggregator.py).
    """
    import tempfile

    mock_payload = {
        "products": [
            {
                "id":    111,
                "title": "Leather Duffel",
                "variants": [
                    {
                        "id": 201, "title": "Black", "price": "249.00",
                        "inventory_management": None,
                        "inventory_quantity":   None,
                        "available":            True,
                    },
                    {
                        "id": 202, "title": "Brown", "price": "249.00",
                        "inventory_management": "shopify",
                        "inventory_quantity":   15,
                        "available":            True,
                    },
                ],
            },
            {
                "id":    112,
                "title": "Leather Backpack",
                "variants": [
                    {
                        "id": 203, "title": "Default Title", "price": "195.00",
                        "inventory_management": "shopify",
                        "inventory_quantity":   0,
                        "available":            False,
                    },
                ],
            },
        ]
    }

    # 1. Extraction
    variants = _extract_variants(mock_payload)
    assert len(variants) == 3, variants
    assert variants[0]["variant_id"]           == 201
    assert variants[0]["price_usd"]            == 249.0
    assert variants[0]["inventory_management"] is None
    assert variants[0]["inventory_quantity"]   is None
    assert variants[0]["available"]            is True
    assert variants[1]["inventory_quantity"]   == 15
    assert variants[2]["inventory_quantity"]   == 0
    assert variants[2]["available"]            is False

    # 2. Snapshot assembly
    ts   = "20260618T100000Z"
    snap = _make_snapshot("test.com", variants, ts)
    assert snap["domain"]        == "test.com"
    assert snap["snapped_at"]    == ts
    assert snap["variant_count"] == 3
    assert len(snap["variants"]) == 3

    # 3. Round-trip: save two snapshots, load back sorted oldest-first
    with tempfile.TemporaryDirectory() as tmp:
        proof_root = Path(tmp)
        ts_a = "20260611T100000Z"
        ts_b = "20260618T100000Z"

        snap_a = _make_snapshot("test.com", variants[:2], ts_a)
        snap_b = _make_snapshot("test.com", variants,     ts_b)

        snap_dir = _snapshot_dir(proof_root, "99", "TestStore")
        (snap_dir / f"{ts_a}.json").write_text(json.dumps(snap_a), encoding="utf-8")
        (snap_dir / f"{ts_b}.json").write_text(json.dumps(snap_b), encoding="utf-8")

        loaded = _load_snapshots(proof_root, "99", "TestStore")
        assert len(loaded)                == 2,  loaded
        assert loaded[0]["snapped_at"]    == ts_a
        assert loaded[1]["snapped_at"]    == ts_b
        assert loaded[0]["variant_count"] == 2
        assert loaded[1]["variant_count"] == 3

    print("self-test PASSED: variant extraction, snapshot assembly, "
          "snapshot save + load round-trip — all hold")


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------

def _load_targets(seed_id: Optional[str] = None) -> dict[str, list[dict]]:
    if not _TARGETS_PATH.exists():
        raise FileNotFoundError(
            f"targets.json not found at {_TARGETS_PATH}\n"
            "Create it with seed entries and competitor Shopify domains."
        )
    data: list[dict] = json.loads(_TARGETS_PATH.read_text(encoding="utf-8"))
    result: dict[str, list[dict]] = {}
    for entry in data:
        sid = str(entry.get("seed_id", ""))
        if seed_id and sid != seed_id:
            continue
        result[sid] = entry.get("targets", [])
    return result


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Shopify snapshot collector — pure data, no analysis. "
                    "Run signal_aggregator.py after ≥2 runs for verdicts."
    )
    ap.add_argument("--self-test", action="store_true",
                    help="run offline self-test and exit")
    ap.add_argument("--dry-run",   action="store_true",
                    help="fetch but do not write snapshots to disk")
    ap.add_argument("--seed",      metavar="ID",
                    help="collect only this seed ID (e.g. 01, 03, 05)")
    ap.add_argument("--run-budget", type=float, default=5.0,
                    help="per-run spend ceiling in USD (default: 5.0)")
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    targets_by_seed = _load_targets(args.seed)
    if not targets_by_seed:
        print(f"No targets found{f' for seed {args.seed}' if args.seed else ''}.",
              file=sys.stderr)
        return 1

    gf = GuardedFetcher(
        config=default_config(),
        state_dir=default_state_dir(),
        run_budget_usd=args.run_budget,
    )

    for seed_id, targets in targets_by_seed.items():
        if not targets:
            print(f"[seed {seed_id}] No targets defined — skipping.")
            continue
        try:
            run_probe(seed_id, targets, gf, _PROOF_ROOT, dry_run=args.dry_run)
        except KillSwitchEngaged as exc:
            print(f"\nKILL SWITCH ENGAGED: {exc}", file=sys.stderr)
            return 2
        except BudgetExceeded as exc:
            print(f"\nBUDGET EXCEEDED: {exc}", file=sys.stderr)
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
