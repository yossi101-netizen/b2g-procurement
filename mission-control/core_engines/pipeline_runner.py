"""
Phase 1 Pipeline Orchestrator.
KritiKaal CORE, US market, demand-only.

Wires A1 through A4 into a single callable that takes raw ImportYeti rows and
a pre-computed engine ScoreResult (Input B from us_bol_scoring_engine.py),
runs every gate in sequence, and returns either a fully-gated send-ready
outreach package or a structured hold record.

Stage order:
  A1  Trigger Validator   (deterministic runner, a1_trigger_validator.py)
  A2  OSINT Researcher    (stub default; inject a real Claude agent in prod)
  A3  Voice-DNA Copywriter(stub default; inject a real Claude agent in prod)
  A4  Gatekeeper          (deterministic runner, a4_gatekeeper.py)

A3 → A4 is a retry loop. If A4 returns FAIL, A3 is called again with the same
baseline and the A4 violation list. Maximum 2 redraft attempts (3 A4 calls
total) before the lead is held with reason A4_RETRY_CAP_EXCEEDED.

Hold vs discard: a held lead is never deleted. Its A1 proof and A2 context
remain valid. The pipeline log carries the full audit trail so the lead can
re-enter at any stage once the blocking condition resolves.

AIR-GAP CONTRACT: imports only from the local core_engines directory.
No kritikaal-hub import, no database, no network.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from a1_trigger_validator import RawRow, run_a1
from a4_gatekeeper import run_a4

# ---------------------------------------------------------------------------
# Section 1: type aliases for injectable stage handlers
# ---------------------------------------------------------------------------

# A2 handler: receives the VALIDATED A1 result, the consignee name, and the
# HS group string; returns a context object shaped per A2_OSINT_RESEARCHER_SPEC.
A2Handler = Callable[[dict, str, str], dict]

# A3 handler: receives the A2 context object, the A1 baseline, and an optional
# list of A4 violations from the previous attempt (empty list on first call);
# returns a draft shaped per A3_VOICE_DNA_COPYWRITER_SPEC.
A3Handler = Callable[[dict, dict, list], dict]

# Retry cap: maximum A3 redraft cycles after an initial A4 FAIL.
MAX_A3_RETRIES: int = 2


# ---------------------------------------------------------------------------
# Section 2: result containers
# ---------------------------------------------------------------------------

@dataclass
class StageEntry:
    """One entry in the pipeline audit log."""
    stage: str
    attempt: int
    status: str
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"stage": self.stage, "attempt": self.attempt,
                "status": self.status, "detail": self.detail}


@dataclass
class PipelineResult:
    status: str        # READY_TO_SEND | HELD
    package: Optional[dict]      # populated on READY_TO_SEND
    hold_reason: Optional[str]   # populated on HELD
    hold_detail: Optional[dict]  # supporting data for the hold reason
    log: list[StageEntry]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "package": self.package,
            "hold_reason": self.hold_reason,
            "hold_detail": self.hold_detail,
            "log": [e.to_dict() for e in self.log],
        }


# ---------------------------------------------------------------------------
# Section 3: stub handlers (A2 and A3)
# ---------------------------------------------------------------------------

def _stub_a2(a1_validated: dict, consignee_name: str, hs_group: str) -> dict:
    """
    A2 stub. Returns a PARTIAL_CONTEXT object carrying the A1 gap summary and
    UNKNOWN for all OSINT-derived fields. Swap for a real Claude agent call
    in production (A2_OSINT_RESEARCHER_SPEC.md Section 4 system prompt).
    """
    dsl = a1_validated.get("recomputed_days_since_last", 0)
    cad = a1_validated.get("recomputed_cadence_days", 0)
    return {
        "consignee_name": consignee_name,
        "hs_group": hs_group,
        "trigger_context": {
            "citation": a1_validated.get("citation", ""),
            "score": a1_validated.get("score", 0),
            "gap_summary": (
                f"{dsl} days silent on a {cad} day cadence, "
                f"China-origin {hs_group.lower().replace('_', ' ')} line"
            ),
        },
        "company_profile": {
            "size_estimate": "UNKNOWN",
            "size_source_url": "UNKNOWN",
            "headquarters": "UNKNOWN",
            "hq_source_url": "UNKNOWN",
        },
        "decision_maker": {
            "name": "UNKNOWN",
            "title": "UNKNOWN",
            "profile_url": "UNKNOWN",
            "recency_evidence": "UNKNOWN",
            "corroboration": "NONE",
            "confidence": "UNKNOWN",
        },
        "product_line_context": {
            "shipped_product_description": "UNKNOWN",
            "current_catalog_match": "UNKNOWN",
            "catalog_source_url": "UNKNOWN",
        },
        "research_log": [
            {"query": "STUB_MODE", "result_summary": "no OSINT performed", "used": False}
        ],
        "overall_status": "PARTIAL_CONTEXT",
    }


def _stub_a3(a2_context: dict, a1_baseline: dict, previous_violations: list) -> dict:
    """
    A3 stub. Builds a mechanically compliant draft from the baseline numbers.
    Swap for a real Claude agent call in production (A3_VOICE_DNA_COPYWRITER_SPEC.md
    Section 4 system prompt). In production, previous_violations is appended to
    the agent prompt so the redraft corrects prior failures.
    """
    dsl = int(a1_baseline.get("recomputed_days_since_last", 0))
    cad = int(a1_baseline.get("recomputed_cadence_days", 0))
    trigger = a2_context.get("trigger_context", {})
    citation = trigger.get("citation", "")
    product_desc = (
        citation.split("|")[3].strip()
        if "|" in citation and len(citation.split("|")) > 3
        else "leather goods"
    )

    subject = f"{dsl}-day gap on your {product_desc.lower()} line"
    subject = subject[:60]

    body = (
        f"Hi Sourcing Team,\n\n"
        f"{dsl} days have passed since your last China-origin shipment of "
        f"{product_desc.lower()}, against a {cad} day average over your recent "
        f"shipments. That is nearly twice your normal reorder cycle, inside the "
        f"window where brands in the Missing Middle absorb real sourcing friction.\n\n"
        f"KritiKaal operates as a Single Point of Accountability for leather goods "
        f"production in India. We manage the factory cluster and compliance stack for "
        f"the product line your shipment data points to, from prototype through to "
        f"AQL 2.5-certified production runs.\n\n"
        f"This is not for brands not yet running production orders of 300 units or "
        f"more on this category.\n\n"
        f"If the scale fits, we offer a 30-unit starter pack of your exact SKU. "
        f"100 percent of that cost is credited against your first production order "
        f"of 300 units or more, placed within 90 days.\n\n"
        f"Would a 20-minute call this week to discuss whether a starter pack fits "
        f"your current timeline be useful?"
    )

    return {"subject_line": subject, "email_body": body}


# ---------------------------------------------------------------------------
# Section 4: pipeline orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(
    *,
    raw_rows: list[RawRow],
    input_b: dict,
    pulled_at: date,
    consignee_name: str,
    hs_group: str,
    a2_handler: A2Handler = _stub_a2,
    a3_handler: A3Handler = _stub_a3,
    max_a3_retries: int = MAX_A3_RETRIES,
) -> PipelineResult:
    """
    Run the full A1→A2→A3→A4 pipeline for 1 consignee.

    Parameters
    ----------
    raw_rows        : RawRow list from ImportYeti for this consignee.
    input_b         : JSON-serialised ScoreResult from us_bol_scoring_engine.py.
    pulled_at       : The date the rows were fetched (needed by A1 for recency).
    consignee_name  : The importer name, carried forward to the send package.
    hs_group        : The matched HS group string (e.g. "LEATHER_BAGS_CASES").
    a2_handler      : Injectable A2 callable. Defaults to the stub.
    a3_handler      : Injectable A3 callable. Defaults to the stub.
    max_a3_retries  : Max A3 redraft cycles after an initial A4 FAIL (default 2).
    """
    log: list[StageEntry] = []

    # ------------------------------------------------------------------
    # Stage A1: prove the gap from raw text.
    # ------------------------------------------------------------------
    a1_result = run_a1(raw_rows, input_b, pulled_at)
    log.append(StageEntry(
        stage="A1", attempt=1,
        status=a1_result["status"],
        detail=a1_result,
    ))

    if a1_result["status"] != "VALIDATED":
        reason_map = {
            "FABRICATION_DETECTED": "A1_FABRICATION_DETECTED",
            "REJECTED": "A1_REJECTED",
        }
        hold_reason = reason_map.get(a1_result["status"], "A1_REJECTED")
        return PipelineResult(
            status="HELD",
            package=None,
            hold_reason=hold_reason,
            hold_detail=a1_result,
            log=log,
        )

    # A1 baseline is what A4 will use to audit A3's draft.
    a1_baseline = {
        "status": a1_result["status"],
        "score": a1_result["score"],
        "citation": a1_result["citation"],
        "recomputed_days_since_last": a1_result["recomputed_days_since_last"],
        "recomputed_cadence_days": a1_result["recomputed_cadence_days"],
    }

    # ------------------------------------------------------------------
    # Stage A2: build verified contact context.
    # ------------------------------------------------------------------
    a2_context = a2_handler(a1_result, consignee_name, hs_group)
    log.append(StageEntry(
        stage="A2", attempt=1,
        status=a2_context.get("overall_status", "UNKNOWN"),
        detail={"overall_status": a2_context.get("overall_status"),
                "decision_maker_confidence": a2_context.get("decision_maker", {}).get("confidence"),
                "research_log_entries": len(a2_context.get("research_log", []))},
    ))

    if a2_context.get("overall_status") == "NO_USABLE_CONTEXT":
        return PipelineResult(
            status="HELD",
            package=None,
            hold_reason="A2_NO_USABLE_CONTEXT",
            hold_detail={"note": "A1 proof intact. Re-run A2 when public OSINT improves."},
            log=log,
        )

    # ------------------------------------------------------------------
    # Stage A3→A4: draft and gate, with retry on FAIL.
    # ------------------------------------------------------------------
    a4_violations: list = []
    a4_result: Optional[dict] = None
    draft: Optional[dict] = None

    for attempt in range(1, max_a3_retries + 2):  # attempts: 1, 2, 3
        draft = a3_handler(a2_context, a1_baseline, a4_violations)
        log.append(StageEntry(
            stage="A3", attempt=attempt,
            status="DRAFTED",
            detail={"subject_line": draft.get("subject_line", ""),
                    "word_count": len(draft.get("email_body", "").split()),
                    "redraft_from_violations": len(a4_violations)},
        ))

        a4_result = run_a4(draft, a1_baseline, a2_context)
        violation_count = len(a4_result.get("line_level_edits", []))
        log.append(StageEntry(
            stage="A4", attempt=attempt,
            status=a4_result["status"],
            detail={"violations": violation_count,
                    "rules_broken": sorted({
                        e["rule_broken"] for e in a4_result.get("line_level_edits", [])
                    })},
        ))

        if a4_result["status"] == "PASS":
            break

        # FAIL: collect violations for the next A3 attempt.
        a4_violations = a4_result.get("line_level_edits", [])
        if attempt == max_a3_retries + 1:
            # Retry cap exhausted: hold the lead.
            return PipelineResult(
                status="HELD",
                package=None,
                hold_reason="A4_RETRY_CAP_EXCEEDED",
                hold_detail={
                    "a4_attempts": attempt,
                    "final_violations": violation_count,
                    "rules_broken": sorted({
                        e["rule_broken"] for e in a4_violations
                    }),
                    "note": (
                        "A4 failed on all 3 attempts. A1 proof and A2 context intact. "
                        "Hold for human review before next redraft cycle."
                    ),
                },
                log=log,
            )

    # ------------------------------------------------------------------
    # A4 PASS: assemble the send-ready package.
    # ------------------------------------------------------------------
    dm = a2_context.get("decision_maker", {})
    return PipelineResult(
        status="READY_TO_SEND",
        package={
            "consignee_name": consignee_name,
            "score": a1_baseline["score"],
            "citation": a1_baseline["citation"],
            "recomputed_days_since_last": a1_baseline["recomputed_days_since_last"],
            "recomputed_cadence_days": a1_baseline["recomputed_cadence_days"],
            "decision_maker": {
                "name": dm.get("name", "UNKNOWN"),
                "title": dm.get("title", "UNKNOWN"),
                "confidence": dm.get("confidence", "UNKNOWN"),
            },
            "company_profile": a2_context.get("company_profile", {}),
            "overall_status": a2_context.get("overall_status", "UNKNOWN"),
            "subject_line": draft["subject_line"],
            "email_body": draft["email_body"],
        },
        hold_reason=None,
        hold_detail=None,
        log=log,
    )


# ---------------------------------------------------------------------------
# Section 5: self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """
    End-to-end stress test using mocked inputs.

    Case 1: Lo & Sons clean run. All 4 stages pass. Output is READY_TO_SEND.
    Case 2: Same lead, A3 replaced with a stub that always returns a
            non-compliant draft. A4 FAIL on all 3 attempts → HELD with reason
            A4_RETRY_CAP_EXCEEDED.
    """

    # Build test inputs from the approved 2026-06-15 Lo & Sons data.
    # Same parameters as the A1 and A4 stress tests for full continuity.
    try:
        from us_bol_scoring_engine import (
            DataConfidence, HsGroup, VolumeBand, score_lead,
        )
    except ImportError as exc:
        print(f"self-test requires us_bol_scoring_engine.py in the same directory: {exc}")
        sys.exit(1)

    PULLED_AT = date(2026, 6, 15)
    LO_SONS_INTERVALS = [42, 45, 48, 44, 46, 43, 47]
    LO_SONS_DSL = 85

    def _build_rows(intervals: list[int], dsl: int) -> list[RawRow]:
        """Generate dated China handbag rows that reproduce the given intervals."""
        latest = date.fromordinal(PULLED_AT.toordinal() - dsl)
        dates = [latest]
        cursor = latest
        for iv in reversed(intervals):
            cursor = date.fromordinal(cursor.toordinal() - iv)
            dates.append(cursor)
        dates.sort()
        return [
            RawRow(
                arrival_date=d.isoformat(),
                shipper_country="China",
                hs_code="4202.21",
                product_description="Cowhide Leather Handbag",
                bol_number=f"BOL{1000 + i}",
            )
            for i, d in enumerate(dates)
        ]

    def _build_input_b(intervals: list[int], dsl: int) -> dict:
        """Run the scoring engine and serialise its output to Input B shape."""
        res = score_lead(
            hs_group=HsGroup.LEATHER_BAGS_CASES,
            n_shipments=len(intervals) + 1,
            data_confidence=DataConfidence.HIGH,
            intervals=intervals,
            days_since_last=dsl,
            china_share=0.85,
            volume_band=VolumeBand.MISSING_MIDDLE,
            supplier_hhi=0.75,
            seasonal_confidence=0.0,
            origin_shift_flag=False,
        )
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

    raw_rows = _build_rows(LO_SONS_INTERVALS, LO_SONS_DSL)
    input_b = _build_input_b(LO_SONS_INTERVALS, LO_SONS_DSL)

    # ------------------------------------------------------------------
    # Case 1: happy path — all stages pass.
    # ------------------------------------------------------------------
    print("PIPELINE SELF-TEST")
    print("=" * 72)
    print("\n[CASE 1: Lo & Sons — full clean run, expected READY_TO_SEND]")
    print(f"  engine score: {input_b['score']}  engine band: {input_b['band']}")
    print(f"  pulled_at: {PULLED_AT.isoformat()}")

    result1 = run_pipeline(
        raw_rows=raw_rows,
        input_b=input_b,
        pulled_at=PULLED_AT,
        consignee_name="Lo & Sons",
        hs_group="LEATHER_BAGS_CASES",
    )

    print(f"\n  pipeline status: {result1.status}")
    print("\n  stage-by-stage log:")
    for entry in result1.log:
        extra = ""
        if entry.stage == "A1":
            extra = f"citation={entry.detail.get('citation', '')[:40]}"
        elif entry.stage == "A2":
            extra = f"overall_status={entry.detail.get('overall_status')}"
        elif entry.stage == "A3":
            extra = f"words={entry.detail.get('word_count')}  subject={entry.detail.get('subject_line', '')[:40]}"
        elif entry.stage == "A4":
            extra = f"violations={entry.detail.get('violations')}  rules={entry.detail.get('rules_broken')}"
        print(f"    {entry.stage} attempt={entry.attempt}  status={entry.status}  {extra}")

    assert result1.status == "READY_TO_SEND", result1.to_dict()
    pkg = result1.package
    assert pkg is not None
    print(f"\n  send-ready package:")
    print(f"    consignee   : {pkg['consignee_name']}")
    print(f"    score       : {pkg['score']}")
    print(f"    citation    : {pkg['citation'][:55]}")
    print(f"    subject     : {pkg['subject_line']}")
    print(f"    body (first sentence): {pkg['email_body'].split(chr(10))[2][:70]}")
    print(f"\n  CASE 1 PASSED.")

    # ------------------------------------------------------------------
    # Case 2: hard rejection — A3 always returns a non-compliant draft.
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("\n[CASE 2: Lo & Sons — A3 always non-compliant, expected HELD]")

    def _bad_a3_stub(a2_context: dict, a1_baseline: dict, previous_violations: list) -> dict:
        """
        Planted A3 stub. Every call returns the same jargon-heavy, sample-offering,
        em-dash-infected draft regardless of previous_violations. This stresses
        the retry cap and confirms the lead is held, never sent.
        """
        dsl = int(a1_baseline.get("recomputed_days_since_last", 0))
        cad = int(a1_baseline.get("recomputed_cadence_days", 0))
        return {
            "subject_line": "Quick question — could we help with your supply chain?",
            "email_body": (
                "Hi Team,\n\n"
                f"I hope this finds you well — I wanted to reach out because we noticed "
                f"your shipping has slowed down a bit. We'd love to send you a free sample "
                f"of our cowhide handbag work as we believe we could be a game-changer for "
                f"your sourcing. We are seamless and will revolutionize how you leverage "
                f"your supply chain relationships to move the needle on quality.\n\n"
                f"We can offer a small batch of {cad} brands complimentary starter kits at "
                f"no cost, which is a no-brainer for brands in your position. Let's touch "
                f"base and circle back on a time that works for you to connect.\n\n"
                f"Just wanted to follow up and reach out because I came across your company "
                f"and felt this could be a great synergy.\n\n"
                f"Best regards,\nThe KritiKaal Team"
            ),
        }

    result2 = run_pipeline(
        raw_rows=raw_rows,
        input_b=input_b,
        pulled_at=PULLED_AT,
        consignee_name="Lo & Sons",
        hs_group="LEATHER_BAGS_CASES",
        a3_handler=_bad_a3_stub,
    )

    print(f"\n  pipeline status: {result2.status}")
    print(f"  hold_reason   : {result2.hold_reason}")
    print("\n  stage-by-stage log:")
    for entry in result2.log:
        extra = ""
        if entry.stage == "A1":
            extra = f"status={entry.status}"
        elif entry.stage == "A2":
            extra = f"overall_status={entry.detail.get('overall_status')}"
        elif entry.stage == "A3":
            rviol = entry.detail.get("redraft_from_violations", 0)
            extra = f"redraft_from={rviol}_violations"
        elif entry.stage == "A4":
            rules = entry.detail.get("rules_broken", [])
            extra = (
                f"violations={entry.detail.get('violations')}  "
                f"rules_broken={rules}"
            )
        print(f"    {entry.stage} attempt={entry.attempt}  status={entry.status}  {extra}")

    print(f"\n  hold_detail:")
    hd = result2.hold_detail or {}
    print(f"    a4_attempts   : {hd.get('a4_attempts')}")
    print(f"    final violations: {hd.get('final_violations')}")
    print(f"    rules_broken  : {hd.get('rules_broken')}")
    print(f"    note          : {hd.get('note')}")

    assert result2.status == "HELD", result2.to_dict()
    assert result2.hold_reason == "A4_RETRY_CAP_EXCEEDED"
    assert result2.package is None

    # Confirm all 3 A4 attempts fired.
    a4_entries = [e for e in result2.log if e.stage == "A4"]
    assert len(a4_entries) == 3, f"expected 3 A4 attempts, got {len(a4_entries)}"
    assert all(e.status == "FAIL" for e in a4_entries)

    print(f"\n  CASE 2 PASSED: lead held after {len(a4_entries)} A4 attempts, "
          f"draft never sent.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("self-test passed: clean run produced READY_TO_SEND, "
          "non-compliant run held after retry cap.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 1 Pipeline Orchestrator for KritiKaal CORE US market."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the built-in end-to-end stress test and exit.",
    )
    args = parser.parse_args()

    if args.self_test:
        _self_test()
    else:
        parser.print_help()
