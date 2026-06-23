"""
BoL Data Ingestion Layer.
Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only.

Converts a raw ImportYeti text export (tab- or comma-separated) into structured
IngestResult objects that are ready to hand directly to pipeline_runner.run_pipeline().

Processing order per row:
  1. Parse and normalise fields.
  2. Reject the entire consignee if is_forwarder() matches the name.
  3. For each row, call match_hs_group() and drop rows that return None.
  4. Discard a consignee whose rows produce zero leather-matched rows.
  5. Compute per-consignee scoring inputs (china_share, intervals, HHI, etc.)
  6. Call score_lead() once per consignee to produce input_b.
  7. Pack into IngestResult ready for pipeline_runner.

Hold vs discard: filtered consignees are written to IngestReport.filtered with
a reason code. They are never deleted. A forwarder hold can be manually reviewed.

AIR-GAP CONTRACT: imports only from the local core_engines directory.
No kritikaal-hub import, no database, no network.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import statistics
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from us_bol_scoring_engine import (
    DataConfidence, HsGroup, VolumeBand,
    is_forwarder, match_hs_group, score_lead,
)
from a1_trigger_validator import RawRow


# ---------------------------------------------------------------------------
# Section 1: header-to-field mapping (flexible, case-insensitive)
# ---------------------------------------------------------------------------

# Each key is a normalised column header substring; value is the canonical field.
# First match wins if multiple aliases appear in the same header row.
_COL_ALIASES: list[tuple[str, str]] = [
    # consignee
    ("consignee",        "consignee"),
    ("importer",         "consignee"),
    ("us consignee",     "consignee"),
    ("buyer",            "consignee"),
    # shipper (used for HHI only; not stored in RawRow)
    ("supplier",         "shipper"),
    ("shipper",          "shipper"),
    ("foreign supplier", "shipper"),
    ("exporter",         "shipper"),
    ("vendor",           "shipper"),
    # origin country
    ("country of origin","country"),
    ("origin country",   "country"),
    ("origin",           "country"),
    ("country",          "country"),
    # HS code
    ("harmonized",       "hs_code"),
    ("hs code",          "hs_code"),
    ("hts code",         "hs_code"),
    ("tariff code",      "hs_code"),
    ("hs",               "hs_code"),
    # product description
    ("product description", "description"),
    ("commodity description","description"),
    ("product",          "description"),
    ("commodity",        "description"),
    ("description",      "description"),
    ("goods",            "description"),
    # arrival date
    ("estimated arrival","arrival_date"),
    ("arrival date",     "arrival_date"),
    ("est. arrival",     "arrival_date"),
    ("arrival",          "arrival_date"),
    ("date",             "arrival_date"),
    # bill of lading
    ("bill of lading",   "bol"),
    ("bol number",       "bol"),
    ("bl number",        "bol"),
    ("b/l",              "bol"),
    ("bol",              "bol"),
]

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%d-%b-%Y")


# ---------------------------------------------------------------------------
# Section 2: parsing utilities
# ---------------------------------------------------------------------------

def _detect_delimiter(text: str) -> str:
    """Return the delimiter that produces the most columns in the first row."""
    first_line = text.split("\n")[0]
    return "\t" if first_line.count("\t") >= first_line.count(",") else ","


def _map_headers(raw_headers: list[str]) -> dict[str, int]:
    """Map canonical field names to column indices from the header row."""
    mapping: dict[str, int] = {}
    for idx, col in enumerate(raw_headers):
        normalised = col.strip().lower()
        for alias, canonical in _COL_ALIASES:
            if alias in normalised and canonical not in mapping:
                mapping[canonical] = idx
                break
    return mapping


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse a date string in any supported format. Return None on failure."""
    if not value:
        return None
    value = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            from datetime import datetime
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _normalise_hs(raw: str) -> str:
    """Strip spaces, ensure at least one dot if digits run together."""
    raw = raw.strip()
    # "420221" → "4202.21", "420231" → "4202.31"
    if re.match(r"^\d{6,}$", raw):
        raw = raw[:4] + "." + raw[4:]
    return raw


# ---------------------------------------------------------------------------
# Section 3: volume band heuristic
# ---------------------------------------------------------------------------

def _estimate_volume_band(n_china_rows: int) -> VolumeBand:
    """
    Estimate volume band from China-origin shipment count.
    Unit volumes are not available in BoL text exports; shipment frequency is
    the best available proxy. Recalibrate once real unit data is available.
    """
    if n_china_rows >= 15:
        return VolumeBand.ABOVE_MISSING_MIDDLE
    if n_china_rows >= 4:
        return VolumeBand.MISSING_MIDDLE
    return VolumeBand.BELOW_MISSING_MIDDLE


# ---------------------------------------------------------------------------
# Section 4: consignee-level scoring inputs
# ---------------------------------------------------------------------------

def _compute_hhi(shippers: list[str]) -> float:
    """Herfindahl-Hirschman Index of supplier concentration (0 to 1)."""
    if not shippers:
        return 1.0
    counts: dict[str, int] = {}
    for s in shippers:
        key = s.strip().lower()
        counts[key] = counts.get(key, 0) + 1
    n = len(shippers)
    return sum((c / n) ** 2 for c in counts.values())


def _score_result_to_input_b(res) -> dict:
    """Serialise a ScoreResult from score_lead() into the Input B JSON shape."""
    gap = res.gap
    return {
        "verdict": res.verdict.value,
        "reason": res.reason,
        "fit": res.fit,
        "timing": res.timing,
        "score": res.score,
        "band": res.band.value if res.band else None,
        "gap": None if gap is None else {
            "cadence_days": gap.cadence_days,
            "days_since_last": gap.days_since_last,
            "overdue_ratio": gap.overdue_ratio,
            "stage": gap.stage.value,
        },
    }


def _build_consignee(
    consignee_name: str,
    records: list[dict],
    pulled_at: date,
) -> Optional[tuple]:
    """
    Build (IngestResult, None) for a pipeline-ready consignee or
    (None, hold_dict) for a consignee that must be filtered.

    A record dict has keys: consignee, shipper, country, hs_code,
    description, arrival_date (str or None), bol.
    """
    # Gate 1: forwarder check on the consignee name.
    if is_forwarder(consignee_name):
        return None, {
            "consignee_name": consignee_name,
            "reason": "FORWARDER",
            "row_count": len(records),
        }

    # Gate 2: match hs_group for each row; drop non-leather rows.
    matched: list[dict] = []
    for rec in records:
        grp = match_hs_group(rec["hs_code"], rec["description"])
        if grp is not None:
            rec["_hs_group"] = grp
            matched.append(rec)

    if not matched:
        return None, {
            "consignee_name": consignee_name,
            "reason": "NO_LEATHER_ROWS",
            "row_count": len(records),
        }

    # Determine the dominant HS group (mode among matched rows).
    from collections import Counter
    hs_group: HsGroup = Counter(r["_hs_group"] for r in matched).most_common(1)[0][0]

    # Separate China-origin matched rows for gap computation.
    china_rows = [r for r in matched if r.get("country", "").strip().lower() == "china"]

    # china_share: fraction of leather rows that came from China.
    china_share = len(china_rows) / len(matched) if matched else 0.0

    # Parse dates from China rows; sort ascending.
    china_dated: list[tuple[dict, date]] = []
    for r in china_rows:
        d = _parse_date(r.get("arrival_date"))
        if d is not None:
            china_dated.append((r, d))
    china_dated.sort(key=lambda rd: rd[1])

    # Compute scoring inputs from China-dated rows.
    n_shipments = len(china_rows)
    if china_dated:
        dates = [d for _, d in china_dated]
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        days_since_last = (pulled_at - dates[-1]).days
    else:
        intervals = []
        days_since_last = 0

    # date_coverage: fraction of China rows with parseable dates.
    date_coverage = len(china_dated) / n_shipments if n_shipments else 0.0
    data_confidence = (
        DataConfidence.HIGH
        if date_coverage >= 0.7 and len(china_dated) >= 4
        else DataConfidence.LOW
    )

    # supplier_hhi from the China rows (factory concentration).
    shippers = [r.get("shipper", "UNKNOWN") for r in china_rows]
    supplier_hhi = _compute_hhi(shippers)

    # Volume band heuristic from China shipment count.
    volume_band = _estimate_volume_band(n_shipments)

    # origin_shift_flag: China share dropped sharply in the 3 most recent rows.
    origin_shift_flag = False
    if len(matched) >= 6:
        matched_sorted = sorted(
            matched,
            key=lambda r: r.get("arrival_date") or "",
        )
        recent_china = sum(
            1 for r in matched_sorted[-3:] if r.get("country", "").lower() == "china"
        ) / 3
        hist_china = sum(
            1 for r in matched_sorted[:-3] if r.get("country", "").lower() == "china"
        ) / (len(matched) - 3)
        if hist_china > 0 and (hist_china - recent_china) >= 0.4:
            origin_shift_flag = True

    # Score this consignee.
    score_res = score_lead(
        hs_group=hs_group,
        n_shipments=n_shipments,
        data_confidence=data_confidence,
        intervals=intervals,
        days_since_last=days_since_last,
        china_share=china_share,
        volume_band=volume_band,
        supplier_hhi=supplier_hhi,
        seasonal_confidence=0.0,
        origin_shift_flag=origin_shift_flag,
    )

    # Build RawRow list (all matched rows, all origins; A1 filters China internally).
    raw_rows = [
        RawRow(
            arrival_date=r.get("arrival_date"),
            shipper_country=r.get("country", "UNKNOWN"),
            hs_code=r.get("hs_code", ""),
            product_description=r.get("description", ""),
            bol_number=r.get("bol", f"NBOL-{i:04d}"),
        )
        for i, r in enumerate(matched)
    ]

    result = IngestResult(
        consignee_name=consignee_name,
        hs_group=hs_group.value,
        raw_rows=raw_rows,
        input_b=_score_result_to_input_b(score_res),
        pulled_at=pulled_at,
        china_row_count=n_shipments,
        total_row_count=len(matched),
        date_coverage=round(date_coverage, 2),
        china_share=round(china_share, 2),
        supplier_hhi=round(supplier_hhi, 3),
        estimated_volume_band=volume_band.value,
        estimated_band=score_res.band.value if score_res.band else "NONE",
        estimated_score=score_res.score,
    )
    return result, None


# ---------------------------------------------------------------------------
# Section 5: result containers
# ---------------------------------------------------------------------------

@dataclass
class IngestResult:
    """One pipeline-ready consignee, ready for pipeline_runner.run_pipeline()."""
    consignee_name: str
    hs_group: str
    raw_rows: list[RawRow]
    input_b: dict
    pulled_at: date
    # scoring metadata
    china_row_count: int
    total_row_count: int
    date_coverage: float
    china_share: float
    supplier_hhi: float
    estimated_volume_band: str
    estimated_band: str   # pre-flight band from the scoring engine
    estimated_score: Optional[int]

    def pipeline_kwargs(self) -> dict:
        """Return kwargs ready to unpack directly into run_pipeline()."""
        return {
            "raw_rows": self.raw_rows,
            "input_b": self.input_b,
            "pulled_at": self.pulled_at,
            "consignee_name": self.consignee_name,
            "hs_group": self.hs_group,
        }


@dataclass
class IngestReport:
    """Summary of one ImportYeti text parse."""
    pulled_at: date
    total_raw_rows: int
    consignees_seen: int
    results: list[IngestResult]   # pipeline-ready, sorted by estimated_score desc
    filtered: list[dict]           # held with reason code


# ---------------------------------------------------------------------------
# Section 6: main ingest function
# ---------------------------------------------------------------------------

def ingest(
    raw_text: str,
    pulled_at: Optional[date] = None,
) -> IngestReport:
    """
    Parse a raw ImportYeti text export and return an IngestReport.

    Parameters
    ----------
    raw_text  : Tab- or comma-separated text with a header row.
    pulled_at : The date the export was fetched. Defaults to today.
    """
    if pulled_at is None:
        pulled_at = date.today()

    delimiter = _detect_delimiter(raw_text)
    reader = csv.reader(io.StringIO(raw_text.strip()), delimiter=delimiter)
    rows_iter = iter(reader)

    # Parse header row.
    try:
        raw_headers = next(rows_iter)
    except StopIteration:
        return IngestReport(
            pulled_at=pulled_at,
            total_raw_rows=0,
            consignees_seen=0,
            results=[],
            filtered=[{"consignee_name": "N/A", "reason": "EMPTY_INPUT", "row_count": 0}],
        )

    col_map = _map_headers(raw_headers)
    required = {"consignee", "country", "hs_code", "description"}
    missing_cols = required - set(col_map.keys())
    if missing_cols:
        return IngestReport(
            pulled_at=pulled_at,
            total_raw_rows=0,
            consignees_seen=0,
            results=[],
            filtered=[{
                "consignee_name": "N/A",
                "reason": f"MISSING_COLUMNS: {sorted(missing_cols)}",
                "row_count": 0,
            }],
        )

    def _get(row: list[str], field: str, default: str = "") -> str:
        idx = col_map.get(field)
        if idx is None or idx >= len(row):
            return default
        return row[idx].strip()

    # Group raw rows by consignee.
    groups: dict[str, list[dict]] = {}
    total_raw = 0
    for raw_row in rows_iter:
        if not any(cell.strip() for cell in raw_row):
            continue
        total_raw += 1
        consignee = _get(raw_row, "consignee") or "UNKNOWN_CONSIGNEE"
        rec = {
            "consignee":    consignee,
            "shipper":      _get(raw_row, "shipper", "UNKNOWN"),
            "country":      _get(raw_row, "country", "UNKNOWN"),
            "hs_code":      _normalise_hs(_get(raw_row, "hs_code")),
            "description":  _get(raw_row, "description"),
            "arrival_date": _get(raw_row, "arrival_date") or None,
            "bol":          _get(raw_row, "bol", f"BOL-{total_raw:05d}"),
        }
        groups.setdefault(consignee, []).append(rec)

    # Build per-consignee results.
    results: list[IngestResult] = []
    filtered: list[dict] = []

    for consignee_name, records in groups.items():
        result, hold = _build_consignee(consignee_name, records, pulled_at)
        if result is not None:
            results.append(result)
        else:
            filtered.append(hold)

    results.sort(key=lambda r: r.estimated_score or 0, reverse=True)

    return IngestReport(
        pulled_at=pulled_at,
        total_raw_rows=total_raw,
        consignees_seen=len(groups),
        results=results,
        filtered=filtered,
    )


# ---------------------------------------------------------------------------
# Section 7: self-test
# ---------------------------------------------------------------------------

_MOCK_EXPORT = """\
Consignee Name\tForeign Supplier\tOrigin Country\tHS Code\tProduct Description\tArrival Date\tBill of Lading
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2025-05-11\tBOL-LS-001
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2025-06-22\tBOL-LS-002
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2025-08-06\tBOL-LS-003
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2025-09-23\tBOL-LS-004
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2025-11-06\tBOL-LS-005
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2025-12-22\tBOL-LS-006
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2026-02-03\tBOL-LS-007
Lo & Sons\tFujian Handbag Co.\tChina\t4202.21\tCowhide Leather Handbag\t2026-03-22\tBOL-LS-008
Bag Studio\tGuangzhou Leather Ltd.\tChina\t4202.21\tGenuine Leather Tote Bag\t2026-01-20\tBOL-BS-001
Bag Studio\tGuangzhou Leather Ltd.\tChina\t4202.21\tGenuine Leather Tote Bag\t2026-02-17\tBOL-BS-002
Bag Studio\tGuangzhou Leather Ltd.\tChina\t4202.21\tGenuine Leather Tote Bag\t2026-03-19\tBOL-BS-003
Bag Studio\tGuangzhou Leather Ltd.\tChina\t4202.21\tGenuine Leather Tote Bag\t2026-04-20\tBOL-BS-004
Bag Studio\tGuangzhou Leather Ltd.\tChina\t4202.21\tGenuine Leather Tote Bag\t2026-05-19\tBOL-BS-005
Oneill Logistics\tShenzhen Trans Ltd.\tChina\t4202.21\tLeather Bags\t2026-01-15\tBOL-OL-001
Oneill Logistics\tShenzhen Trans Ltd.\tChina\t4202.21\tLeather Bags\t2026-02-28\tBOL-OL-002
Oneill Logistics\tShenzhen Trans Ltd.\tChina\t4202.21\tLeather Bags\t2026-04-10\tBOL-OL-003
Oneill Logistics\tShenzhen Trans Ltd.\tChina\t4202.21\tLeather Bags\t2026-05-20\tBOL-OL-004
Vetta Capsule\tHangzhou Canvas Co.\tChina\t4202.22\tNylon Canvas Crossbody Bag\t2026-01-10\tBOL-VC-001
Vetta Capsule\tHangzhou Canvas Co.\tChina\t4202.22\tNylon Canvas Crossbody Bag\t2026-02-18\tBOL-VC-002
Vetta Capsule\tHangzhou Canvas Co.\tChina\t4202.22\tNylon Canvas Crossbody Bag\t2026-03-28\tBOL-VC-003
Vetta Capsule\tHangzhou Canvas Co.\tChina\t4202.22\tNylon Canvas Crossbody Bag\t2026-04-30\tBOL-VC-004
"""

_PULLED_AT = date(2026, 6, 15)


def _self_test() -> None:
    print("BOL INGESTOR SELF-TEST")
    print("=" * 72)

    report = ingest(_MOCK_EXPORT, pulled_at=_PULLED_AT)

    print(f"\nINGESTION SUMMARY")
    print(f"  pulled_at            : {report.pulled_at}")
    print(f"  total raw rows       : {report.total_raw_rows}")
    print(f"  consignees seen      : {report.consignees_seen}")
    print(f"  pipeline-ready       : {len(report.results)}")
    print(f"  filtered (held)      : {len(report.filtered)}")

    print(f"\nFILTERED CONSIGNEES:")
    for f in report.filtered:
        print(f"  {f['consignee_name']:<30} reason={f['reason']}  rows={f['row_count']}")

    # Assert both expected filters fired.
    filtered_names = {f["consignee_name"] for f in report.filtered}
    filtered_reasons = {f["consignee_name"]: f["reason"] for f in report.filtered}
    assert "Oneill Logistics" in filtered_names, "forwarder filter missed Oneill Logistics"
    assert filtered_reasons["Oneill Logistics"] == "FORWARDER"
    assert "Vetta Capsule" in filtered_names, "non-leather filter missed Vetta Capsule"
    assert filtered_reasons["Vetta Capsule"] == "NO_LEATHER_ROWS"
    print("  both expected filters confirmed.")

    print(f"\nPIPELINE-READY CONSIGNEES (sorted by score desc):")
    print(f"  {'CONSIGNEE':<22} {'HS_GROUP':<22} {'SCORE':>5}  {'BAND':<8}  "
          f"{'CHINA_ROWS':>10}  {'DSL':>5}  {'HHI':>5}")
    for r in report.results:
        gap = r.input_b.get("gap") or {}
        dsl = gap.get("days_since_last", "n/a")
        print(f"  {r.consignee_name:<22} {r.hs_group:<22} {str(r.estimated_score):>5}  "
              f"{r.estimated_band:<8}  {r.china_row_count:>10}  {str(dsl):>5}  "
              f"{r.supplier_hhi:>5.3f}")

    # Assert Lo & Sons scored HOT and Bag Studio did not.
    result_map = {r.consignee_name: r for r in report.results}
    assert "Lo & Sons" in result_map, "Lo & Sons not in pipeline-ready results"
    assert result_map["Lo & Sons"].estimated_band == "HOT", (
        f"Lo & Sons expected HOT, got {result_map['Lo & Sons'].estimated_band}"
    )
    assert "Bag Studio" in result_map, "Bag Studio not in pipeline-ready results"
    assert result_map["Bag Studio"].estimated_band != "HOT", (
        f"Bag Studio should not be HOT (dsl inside latency buffer)"
    )

    print(f"\nSCORING ASSERTION: Lo & Sons=HOT confirmed, "
          f"Bag Studio={result_map['Bag Studio'].estimated_band} (not HOT) confirmed.")

    # Show the pipeline_kwargs for the top result.
    top = report.results[0]
    print(f"\nPIPELINE HANDOFF PREVIEW (top result: {top.consignee_name})")
    kw = top.pipeline_kwargs()
    print(f"  consignee_name : {kw['consignee_name']}")
    print(f"  hs_group       : {kw['hs_group']}")
    print(f"  pulled_at      : {kw['pulled_at']}")
    print(f"  raw_rows count : {len(kw['raw_rows'])}")
    print(f"  input_b.band   : {kw['input_b']['band']}")
    print(f"  input_b.score  : {kw['input_b']['score']}")
    gap = kw["input_b"].get("gap") or {}
    print(f"  input_b.gap    : cadence={gap.get('cadence_days')} days  "
          f"dsl={gap.get('days_since_last')} days  "
          f"stage={gap.get('stage')}")
    print(f"\n  ready to call: pipeline_runner.run_pipeline(**top.pipeline_kwargs())")

    # Demonstrate the pipeline handoff actually works.
    try:
        from pipeline_runner import run_pipeline
        pipeline_result = run_pipeline(**top.pipeline_kwargs())
        print(f"\nPIPELINE RUN (end-to-end smoke test):")
        print(f"  pipeline status : {pipeline_result.status}")
        if pipeline_result.status == "READY_TO_SEND":
            pkg = pipeline_result.package
            print(f"  subject_line    : {pkg['subject_line']}")
            print(f"  body (line 3)   : {pkg['email_body'].split(chr(10))[2][:70]}")
        else:
            print(f"  hold_reason     : {pipeline_result.hold_reason}")
    except ImportError:
        print("  (pipeline_runner not importable in this context, skipping smoke test)")

    print("\n" + "=" * 72)
    print("self-test passed: 2 filtered, 2 scored, top result handed to pipeline.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BoL Data Ingestion Layer for KritiKaal CORE US market."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the built-in ingestion stress test and exit.",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a raw ImportYeti text export to ingest.",
    )
    parser.add_argument(
        "--pulled-at",
        type=str,
        help="Fetch date in YYYY-MM-DD format (default: today).",
    )
    args = parser.parse_args()

    if args.self_test:
        _self_test()
    elif args.file:
        pulled = _parse_date(args.pulled_at) if args.pulled_at else date.today()
        with open(args.file, "r", encoding="utf-8") as fh:
            raw = fh.read()
        rep = ingest(raw, pulled_at=pulled)
        import json as _json
        print(_json.dumps(
            {
                "pulled_at": str(rep.pulled_at),
                "total_raw_rows": rep.total_raw_rows,
                "pipeline_ready": len(rep.results),
                "filtered": rep.filtered,
                "results": [
                    {
                        "consignee_name": r.consignee_name,
                        "hs_group": r.hs_group,
                        "estimated_band": r.estimated_band,
                        "estimated_score": r.estimated_score,
                        "china_row_count": r.china_row_count,
                        "input_b": r.input_b,
                    }
                    for r in rep.results
                ],
            },
            indent=2,
        ))
    else:
        parser.print_help()
