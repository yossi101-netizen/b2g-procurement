"""
A1 Trigger Validator, thin runner.
Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only.

This is the deterministic encoding of A1_TRIGGER_VALIDATOR_SPEC.md. A1 audits
the scoring engine. A1 does not find leads. It recomputes the gap from the raw
shipment rows alone (Input A), compares against the engine ScoreResult (Input B),
and proves or disproves that the scored gap is real.

In production the recompute reasoning runs inside a Claude sub-agent driven by
the verbatim system prompt in the spec. This runner encodes the same arithmetic
and the same disposition rules so the loop can be stress-tested end to end before
the model is wired in. The model and this runner must agree by construction.

AIR-GAP CONTRACT: standalone. Imports the local scoring engine only. No
kritikaal-hub import, no database, no network.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import date
from typing import Optional

from us_bol_scoring_engine import (
    DataConfidence, HsGroup, VolumeBand, score_lead, ScoreResult,
)

# A1 agreement tolerances (spec Section 2).
RECENCY_TOLERANCE_DAYS = 3
CADENCE_TOLERANCE_FRACTION = 0.10
LATENCY_BUFFER = 30
MIN_DATED_ROWS = 4


@dataclass
class RawRow:
    arrival_date: Optional[str]   # YYYY-MM-DD, or None when stripped or unparseable
    shipper_country: str
    hs_code: str
    product_description: str
    bol_number: str

    def as_text(self) -> str:
        d = self.arrival_date if self.arrival_date else "UNKNOWN"
        return f"{d} | {self.shipper_country} | {self.hs_code} | {self.product_description} | {self.bol_number}"


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse 1 YYYY-MM-DD string. Return None on missing or unparseable input. Never estimate."""
    if not value:
        return None
    try:
        y, m, d = value.strip().split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def _engine_result_to_input_b(result: ScoreResult) -> dict:
    """Serialize the engine ScoreResult into the JSON shape A1 audits (Input B)."""
    gap = result.gap
    return {
        "verdict": result.verdict.value,
        "reason": result.reason,
        "fit": result.fit,
        "timing": result.timing,
        "score": result.score,
        "band": result.band.value if result.band else None,
        "gap": None if gap is None else {
            "cadence_days": gap.cadence_days,
            "days_since_last": gap.days_since_last,
            "overdue_ratio": gap.overdue_ratio,
            "stage": gap.stage.value,
        },
    }


def run_a1(raw_rows: list[RawRow], input_b: dict, pulled_at: Optional[date]) -> dict:
    """
    Execute the A1 audit on 1 consignee.

    Returns 1 of 3 dispositions: VALIDATED, REJECTED, or FABRICATION_DETECTED.
    A1 trusts only raw_rows. Every number is recomputed, never copied from input_b.
    """
    # Rule: both inputs mandatory.
    if not raw_rows or input_b is None:
        return {"status": "REJECTED", "reason": "MISSING_INPUT: Input A or Input B absent"}
    if pulled_at is None:
        return {"status": "REJECTED", "reason": "MISSING_PULLED_AT: no fetch date to measure recency against"}

    # Step 1. Parse dates from raw rows. Keep only China-origin dated rows for the gap.
    dated = [(r, _parse_date(r.arrival_date)) for r in raw_rows]
    china_dated = [(r, d) for (r, d) in dated if d is not None and r.shipper_country.lower() == "china"]

    # Rule: no parseable dates at all is UNVERIFIABLE, not thin history.
    if len([d for (_, d) in dated if d is not None]) == 0:
        return {"status": "REJECTED", "reason": "UNVERIFIABLE_DATES: no row carries a parseable arrival date"}

    # Rule: fewer than 4 dated China rows is thin history.
    if len(china_dated) < MIN_DATED_ROWS:
        return {"status": "REJECTED",
                "reason": f"INSUFFICIENT_HISTORY: {len(china_dated)} dated China rows, under the {MIN_DATED_ROWS} minimum"}

    # Step 3. Sort ascending, compute intervals, median cadence.
    china_dated.sort(key=lambda rd: rd[1])
    dates = [d for (_, d) in china_dated]
    intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    recomputed_cadence = statistics.median(intervals)

    # Step 4. Recompute days_since_last against pulled_at.
    latest_row, latest_date = china_dated[-1]
    recomputed_dsl = (pulled_at - latest_date).days

    engine_gap = input_b.get("gap") or {}
    engine_cadence = engine_gap.get("cadence_days")
    engine_dsl = engine_gap.get("days_since_last")

    # Rule 4. Halt on fabrication. Recency first, then cadence.
    if engine_dsl is not None and abs(recomputed_dsl - engine_dsl) > RECENCY_TOLERANCE_DAYS:
        return {
            "status": "FABRICATION_DETECTED",
            "reason": (f"recency disagreement: A1 recomputed days_since_last {recomputed_dsl}, "
                       f"engine claimed {engine_dsl}, gap of {abs(recomputed_dsl - engine_dsl)} days "
                       f"exceeds the {RECENCY_TOLERANCE_DAYS} day tolerance"),
            "a1_value": recomputed_dsl,
            "engine_value": engine_dsl,
        }
    if engine_cadence and abs(recomputed_cadence - engine_cadence) > CADENCE_TOLERANCE_FRACTION * engine_cadence:
        return {
            "status": "FABRICATION_DETECTED",
            "reason": (f"cadence disagreement: A1 recomputed cadence_days {recomputed_cadence}, "
                       f"engine claimed {engine_cadence}, beyond the 10 percent tolerance"),
            "a1_value": recomputed_cadence,
            "engine_value": engine_cadence,
        }

    # Rule 7. Latency buffer, applied only after the number is proven.
    if recomputed_dsl <= LATENCY_BUFFER:
        return {"status": "REJECTED",
                "reason": f"WITHIN_LATENCY_BUFFER: recomputed days_since_last {recomputed_dsl}, "
                          f"at or under the {LATENCY_BUFFER} day buffer"}

    # Business actionability. A1 advances only an engine HOT band.
    if input_b.get("band") != "HOT":
        stage = engine_gap.get("stage", "UNKNOWN")
        return {"status": "REJECTED",
                "reason": f"NOT_ACTIONABLE: engine band {input_b.get('band')}, gap stage {stage}, "
                          f"recomputed days_since_last {recomputed_dsl}"}

    # VALIDATED. Quote the latest China row as the citation.
    return {
        "status": "VALIDATED",
        "score": input_b.get("score"),
        "citation": latest_row.as_text(),
        "recomputed_days_since_last": recomputed_dsl,
        "recomputed_cadence_days": recomputed_cadence,
    }


# ---------------------------------------------------------------------------
# STRESS TEST: the full engine-to-A1 loop on the approved 2026-06-15 set
# ---------------------------------------------------------------------------

PULLED_AT = date(2026, 6, 15)


def _build_china_rows(intervals: list[int], days_since_last: int, n: int,
                      latest_offset: Optional[int] = None) -> list[RawRow]:
    """
    Build dated China handbag rows that reproduce the given intervals exactly.
    latest_offset, when set, overrides the true latest arrival to plant a
    mis-parsed-year fabrication (engine still sees days_since_last).
    """
    dsl = latest_offset if latest_offset is not None else days_since_last
    latest = PULLED_AT.fromordinal(PULLED_AT.toordinal() - dsl)
    dates = [latest]
    cursor = latest
    for iv in reversed(intervals):
        cursor = cursor.fromordinal(cursor.toordinal() - iv)
        dates.append(cursor)
    dates.sort()
    rows = []
    for i, d in enumerate(dates):
        rows.append(RawRow(
            arrival_date=d.isoformat(), shipper_country="China",
            hs_code="4202.21", product_description="Cowhide Leather Handbag",
            bol_number=f"BOL{1000 + i}",
        ))
    return rows


def _engine_for(intervals, dsl, n, china_share, band_inputs):
    """Run the real scoring engine and return its Input B JSON."""
    res = score_lead(
        hs_group=HsGroup.LEATHER_BAGS_CASES, n_shipments=n,
        data_confidence=DataConfidence.HIGH, intervals=intervals,
        days_since_last=dsl, china_share=china_share,
        volume_band=band_inputs["volume_band"], supplier_hhi=band_inputs["hhi"],
        seasonal_confidence=band_inputs.get("seasonal", 0.0),
        origin_shift_flag=band_inputs.get("origin_shift", False),
    )
    return _engine_result_to_input_b(res)


def _stress_test() -> None:
    print("A1 STRESS TEST, engine-to-A1 loop, approved 2026-06-15 set")
    print("pulled_at:", PULLED_AT.isoformat())
    print("=" * 72)

    cases = []

    # 1. Clean VALIDATED. Lo & Sons, the approved top lead, engine band HOT.
    iv = [42, 45, 48, 44, 46, 43, 47]
    b = _engine_for(iv, 85, 8, 0.85, {"volume_band": VolumeBand.MISSING_MIDDLE, "hhi": 0.75})
    rows = _build_china_rows(iv, 85, 8)
    cases.append(("Lo & Sons (clean HOT)", rows, b))

    # 2. WITHIN_LATENCY_BUFFER. Rebecca Minkoff, ships every 20 days, silent 18.
    iv = [18, 19, 20, 21, 20, 22, 18, 20, 21]
    b = _engine_for(iv, 18, 10, 0.80, {"volume_band": VolumeBand.ABOVE_MISSING_MIDDLE, "hhi": 0.40})
    rows = _build_china_rows(iv, 18, 10)
    cases.append(("Rebecca Minkoff (latency buffer)", rows, b))

    # 3. NOT_ACTIONABLE, under the 45 day pain floor. Modern Picnic, silent 40.
    iv = [48, 50, 52, 49, 51, 47, 53]
    b = _engine_for(iv, 40, 8, 0.90, {"volume_band": VolumeBand.BELOW_MISSING_MIDDLE, "hhi": 0.90})
    rows = _build_china_rows(iv, 40, 8)
    cases.append(("Modern Picnic (under pain floor)", rows, b))

    # 4. NOT_ACTIONABLE, stale. Staud, silent 200 days, engine stage STALE.
    iv = [38, 40, 42, 39, 41, 37, 43]
    b = _engine_for(iv, 200, 8, 0.50, {"volume_band": VolumeBand.MISSING_MIDDLE, "hhi": 0.45})
    rows = _build_china_rows(iv, 200, 8)
    cases.append(("Staud (stale)", rows, b))

    # 5. UNVERIFIABLE_DATES. Lo & Sons rows with every date stripped.
    iv = [42, 45, 48, 44, 46, 43, 47]
    b = _engine_for(iv, 85, 8, 0.85, {"volume_band": VolumeBand.MISSING_MIDDLE, "hhi": 0.75})
    stripped = _build_china_rows(iv, 85, 8)
    for r in stripped:
        r.arrival_date = None
    cases.append(("Date-stripped rows (planted)", stripped, b))

    # 6. FABRICATION_DETECTED. Engine ran on a mis-parsed year and claims
    #    days_since_last 85. The true raw latest arrival is only 41 days back.
    iv = [38, 40, 42, 39, 41, 37, 43]
    b = _engine_for(iv, 85, 8, 0.70, {"volume_band": VolumeBand.MISSING_MIDDLE, "hhi": 0.85})
    rows = _build_china_rows(iv, 85, 8, latest_offset=41)   # raw truth: 41 days, not 85
    cases.append(("Mis-parsed year (planted)", rows, b))

    fabrication_json = None
    advanced = []
    for name, rows, input_b in cases:
        out = run_a1(rows, input_b, PULLED_AT)
        print(f"\n[{name}]")
        print(f"  engine band: {input_b.get('band')}  engine score: {input_b.get('score')}")
        print(f"  A1 status  : {out['status']}")
        if out["status"] == "VALIDATED":
            print(f"  citation   : {out['citation']}")
            print(f"  A1 dsl/cad : {out['recomputed_days_since_last']} / {out['recomputed_cadence_days']}")
            advanced.append(name)
        else:
            print(f"  reason     : {out['reason']}")
        if out["status"] == "FABRICATION_DETECTED":
            fabrication_json = out

    print("\n" + "=" * 72)
    print("FABRICATION_DETECTED exact JSON output:")
    print(json.dumps(fabrication_json, indent=2))

    print("\n" + "=" * 72)
    print(f"advanced to A2: {advanced}")
    # Zero Trust contract: exactly 1 clean lead advances, every planted failure held.
    assert advanced == ["Lo & Sons (clean HOT)"], advanced
    assert fabrication_json is not None and fabrication_json["status"] == "FABRICATION_DETECTED"
    print("contract holds: 1 proven lead advanced, every planted failure was held")


if __name__ == "__main__":
    _stress_test()
