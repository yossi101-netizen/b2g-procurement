"""
US BoL Shipment-Gap Scoring Engine
Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only.

This module is the permanent, validated encoding of US_BOL_TRIGGER_SPEC.md.
It isolates US leather-goods importers whose regular China shipments have gone
silent for longer than their own normal cadence, then ranks the survivors by
Fit times Timing.

AIR-GAP CONTRACT (BI_HUNTING_PLAYBOOK.md, Section 0):
This file is a standalone math and logic processor. It imports nothing from
kritikaal-hub. It reads no database. It performs no network access. It takes
plain data structures in and returns plain results out. Any ingestion, storage,
provider pull, or dashboard layer lives outside this module and calls into it.

VALIDATION STATUS:
Eyeball test on the 13 reverse-engineered ImportYeti leads was approved on
2026-06-15. The constants and formulas below are frozen at that approved state.
The self-test block at the bottom reproduces 3 of the approved cases exactly.

Spec fidelity notes (2 fixes found during validation, both folded in here):
1. Material exclusion runs at the matching layer (match_hs_group), not as a
   product weight of 0 inside FIT. A 0 product weight does not reliably trip
   the FIT < 0.40 hard gate, so non-leather records must be dropped before
   they ever reach the formula.
2. The forwarder check matches a name pattern, not only the literal blocklist,
   so a consignee such as "Oneill Logistics" is caught and marked LOW.

Thresholds are the initial approved values. Recalibrate against the first real
provider pull before scaling, then version this file.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# 0. ENUMS AND CONSTANTS (frozen at the approved state)
# ---------------------------------------------------------------------------

class HsGroup(str, Enum):
    LEATHER_BAGS_CASES = "LEATHER_BAGS_CASES"
    LEATHER_SLG = "LEATHER_SLG"
    LEATHER_APPAREL_ACCESS = "LEATHER_APPAREL_ACCESS"
    LEATHER_OTHER = "LEATHER_OTHER"
    LEATHER_FOOTWEAR = "LEATHER_FOOTWEAR"


class VolumeBand(str, Enum):
    BELOW_MISSING_MIDDLE = "BELOW_MISSING_MIDDLE"
    MISSING_MIDDLE = "MISSING_MIDDLE"
    ABOVE_MISSING_MIDDLE = "ABOVE_MISSING_MIDDLE"


class DataConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Verdict(str, Enum):
    SCORED = "SCORED"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


class Band(str, Enum):
    HOT = "HOT"
    WARM = "WARM"
    WATCH = "WATCH"
    DISCARD = "DISCARD"


class GapStage(str, Enum):
    HOT = "HOT"
    WATCH = "WATCH"
    NONE = "NONE"
    STALE = "STALE"


# FIT component weights. Sum is 1.00.
W_PRODUCT = 0.35
W_CHINA_SHARE = 0.25
W_VOLUME_BAND = 0.25
W_MATURITY = 0.15

# TIMING component weights. Inner sum is 1.00 before the 2 multipliers.
W_GAP_SEVERITY = 0.45
W_FRESHNESS = 0.25
W_CONCENTRATION_SHOCK = 0.30

# Hard gates and preconditions.
MIN_SHIPMENTS = 4            # 4 shipments give 3 intervals, the floor to trust a cadence
FIT_GATE = 0.40             # below this FIT, discard regardless of timing
TIMING_GATE = 0.30          # below this TIMING, discard regardless of fit

# Gap-detection thresholds (US_BOL_TRIGGER_SPEC.md Section 2).
DATA_LATENCY_BUFFER = 30    # provider indexing lag in days, silence inside it is ignored
ABS_FLOOR = 45             # nothing under 45 days is pain yet
ABS_CEILING = 180          # beyond 180 days they likely re-sourced or churned
REL_CEILING = 2.5          # overdue_ratio above this reads as resolved or dead
MAD_TO_SIGMA = 1.4826      # MAD to robust sigma conversion constant

# Score bands.
HOT_FLOOR = 55
WARM_FLOOR = 35
WATCH_FLOOR = 20

# FIT F1 product-fit scores by HS group.
PRODUCT_FIT = {
    HsGroup.LEATHER_BAGS_CASES: 1.0,
    HsGroup.LEATHER_SLG: 1.0,
    HsGroup.LEATHER_APPAREL_ACCESS: 0.7,
    HsGroup.LEATHER_OTHER: 0.5,
    HsGroup.LEATHER_FOOTWEAR: 0.4,
}

# FIT F3 volume-fit scores by band. The Missing Middle is the target.
VOLUME_FIT = {
    VolumeBand.MISSING_MIDDLE: 1.0,
    VolumeBand.BELOW_MISSING_MIDDLE: 0.5,
    VolumeBand.ABOVE_MISSING_MIDDLE: 0.3,
}


# ---------------------------------------------------------------------------
# 1. MATERIAL MATCHING LAYER (Spec Section 1.3, fix 1)
# ---------------------------------------------------------------------------

# A record joins a HS group only if it is genuine leather. Synthetic, PU,
# bonded, and vegan descriptions are the wrong material and must be dropped
# here, before scoring, never weighted to 0 inside FIT.

_LEATHER_TERMS = ("leather", "cowhide", "calfskin", "goat leather", "genuine leather")
_NON_LEATHER_TERMS = (
    "vegan", "pu ", "p.u", "synthetic", "faux", "bonded", "pleather",
    "cotton", "canvas", "nylon", "polyester", "pvc", "rattan", "straw",
)

_HS_PREFIX_GROUP = {
    "4202.11": HsGroup.LEATHER_BAGS_CASES,
    "4202.21": HsGroup.LEATHER_BAGS_CASES,
    "4202.91": HsGroup.LEATHER_BAGS_CASES,
    "4202.31": HsGroup.LEATHER_SLG,
    "4202.32": HsGroup.LEATHER_SLG,
    "4203.10": HsGroup.LEATHER_APPAREL_ACCESS,
    "4203.21": HsGroup.LEATHER_APPAREL_ACCESS,
    "4203.29": HsGroup.LEATHER_APPAREL_ACCESS,
    "4203.30": HsGroup.LEATHER_APPAREL_ACCESS,
    "4205": HsGroup.LEATHER_OTHER,
    "6403": HsGroup.LEATHER_FOOTWEAR,
}

_DESC_GROUP_TERMS = (
    (HsGroup.LEATHER_BAGS_CASES, ("handbag", "tote", "briefcase", "suitcase", "case", "bag", "crossbody", "satchel")),
    (HsGroup.LEATHER_SLG, ("wallet", "cardholder", "card holder", "key fob", "pouch", "wristlet", "coin purse")),
    (HsGroup.LEATHER_APPAREL_ACCESS, ("belt", "glove", "jacket")),
    (HsGroup.LEATHER_OTHER, ("strap", "leather article", "leather goods")),
    (HsGroup.LEATHER_FOOTWEAR, ("shoe", "boot", "footwear")),
)

# Freight forwarder and 3PL name patterns. A hit forces data_confidence LOW.
_FORWARDER_PATTERNS = (
    "logistics", "freight", "forward", "expeditors", "dhl", "kuehne",
    "flexport", "dsv", "oocl", "3pl", "supply chain solutions", "customs broker",
)


def match_hs_group(hs_code: Optional[str], product_description: str) -> Optional[HsGroup]:
    """
    Resolve a record to 1 target HS group, or return None to drop it.

    Drop rules, applied in order:
    1. Any non-leather material term in the description drops the record.
    2. An HS prefix in the target table assigns the group directly.
    3. Otherwise a leather term plus a group keyword in the description assigns
       the group. No leather term means drop.
    """
    desc = (product_description or "").lower()

    # Rule 1. Wrong material drops immediately.
    if any(term in desc for term in _NON_LEATHER_TERMS):
        return None

    # Rule 2. Direct HS prefix match.
    if hs_code:
        code = hs_code.strip()
        for prefix, group in _HS_PREFIX_GROUP.items():
            if code.startswith(prefix):
                return group

    # Rule 3. Description match, but only for genuine leather.
    if not any(term in desc for term in _LEATHER_TERMS):
        return None
    for group, terms in _DESC_GROUP_TERMS:
        if any(term in desc for term in terms):
            return group

    return None


def is_forwarder(consignee_name: str) -> bool:
    """Return True when the consignee name matches a forwarder or 3PL pattern."""
    name = (consignee_name or "").lower()
    return any(pattern in name for pattern in _FORWARDER_PATTERNS)


# ---------------------------------------------------------------------------
# 2. GAP-DETECTION RULE (Spec Section 2)
# ---------------------------------------------------------------------------

@dataclass
class GapResult:
    cadence_days: float
    cadence_mad: float
    sigma_robust: float
    expected_ceiling: float
    days_since_last: int
    overdue_ratio: float
    anomaly: bool
    rule_used: str
    actionable: bool
    stage: GapStage


def compute_gap(intervals: list[int], days_since_last: int) -> GapResult:
    """
    Compute the robust cadence baseline and the gap stage from inter-arrival
    intervals plus the days since the last arrival.

    Caller guarantees at least 3 intervals, which is 4 shipments. The median
    and MAD are used, never the mean, because import schedules are spiky.
    """
    cadence = statistics.median(intervals)
    mad = statistics.median([abs(iv - cadence) for iv in intervals])
    sigma = MAD_TO_SIGMA * mad
    expected_ceiling = cadence + 2 * sigma

    if sigma == 0:
        anomaly = days_since_last > 1.5 * cadence
        rule_used = "FALLBACK sigma 0: days_since_last > 1.5 times cadence"
    else:
        anomaly = days_since_last > expected_ceiling
        rule_used = "PRIMARY: days_since_last > cadence plus 2 sigma"

    ratio = days_since_last / cadence

    actionable = (
        days_since_last >= max(ABS_FLOOR, DATA_LATENCY_BUFFER)
        and days_since_last <= ABS_CEILING
        and ratio <= REL_CEILING
    )

    if ratio > REL_CEILING or days_since_last > ABS_CEILING:
        stage = GapStage.STALE
    elif 1.5 <= ratio <= REL_CEILING and actionable:
        stage = GapStage.HOT
    elif 1.25 <= ratio < 1.5 and days_since_last >= ABS_FLOOR:
        stage = GapStage.WATCH
    elif ratio < 1.25:
        stage = GapStage.NONE
    else:
        stage = GapStage.STALE

    return GapResult(
        cadence_days=cadence,
        cadence_mad=mad,
        sigma_robust=round(sigma, 4),
        expected_ceiling=round(expected_ceiling, 4),
        days_since_last=days_since_last,
        overdue_ratio=round(ratio, 4),
        anomaly=anomaly,
        rule_used=rule_used,
        actionable=actionable,
        stage=stage,
    )


# ---------------------------------------------------------------------------
# 3. FIT AND TIMING COMPONENTS (Spec Section 3)
# ---------------------------------------------------------------------------

def maturity_score(n_shipments: int, data_confidence: DataConfidence) -> float:
    """
    FIT F4 importer maturity.
    1.0 at 8 or more shipments with HIGH confidence.
    0.7 at 4 to 7 shipments.
    0.4 at MEDIUM confidence otherwise.
    A high count with only MEDIUM confidence falls through to 0.4 by design.
    """
    if n_shipments >= 8 and data_confidence == DataConfidence.HIGH:
        return 1.0
    if 4 <= n_shipments <= 7:
        return 0.7
    if data_confidence == DataConfidence.MEDIUM:
        return 0.4
    return 0.0


def gap_severity_score(overdue_ratio: float) -> float:
    """
    TIMING T1 gap severity, a plateau on the overdue ratio R.
    0 below 1.25, linear ramp 1.25 to 1.5, flat 1.0 across 1.5 to 2.5,
    linear decay 2.5 to 3.5, 0 above 3.5.
    """
    r = overdue_ratio
    if r < 1.25:
        return 0.0
    if r <= 1.5:
        return (r - 1.25) / 0.25
    if r <= 2.5:
        return 1.0
    if r <= 3.5:
        return (3.5 - r) / 1.0
    return 0.0


def freshness_score(days_since_last: int) -> float:
    """
    TIMING T2 freshness.
    1.0 across 45 to 120 days, linear decay to 0 by 180 days, 0 below 45 days.
    """
    d = days_since_last
    if d < ABS_FLOOR:
        return 0.0
    if d <= 120:
        return 1.0
    if d < ABS_CEILING:
        return (ABS_CEILING - d) / 60.0
    return 0.0


# ---------------------------------------------------------------------------
# 4. SCORING ENGINE (Spec Section 3, hard gates and bands)
# ---------------------------------------------------------------------------

@dataclass
class ScoreResult:
    verdict: Verdict
    reason: str
    fit: Optional[float] = None
    timing: Optional[float] = None
    score: Optional[int] = None
    band: Optional[Band] = None
    gap: Optional[GapResult] = None
    components: dict = field(default_factory=dict)


def score_lead(
    *,
    hs_group: HsGroup,
    n_shipments: int,
    data_confidence: DataConfidence,
    intervals: list[int],
    days_since_last: int,
    china_share: float,
    volume_band: VolumeBand,
    supplier_hhi: float,
    seasonal_confidence: float = 0.0,
    origin_shift_flag: bool = False,
) -> ScoreResult:
    """
    Run the full validated pipeline on 1 lead.

    Order of operations:
    1. Preconditions. Under 4 shipments or LOW confidence returns
       INSUFFICIENT_HISTORY and is never scored.
    2. Gap detection. Robust cadence, anomaly test, stage.
    3. FIT and TIMING.
    4. Hard gate. FIT under 0.40 or TIMING under 0.30 collapses to DISCARD.
    5. Score and band.

    The caller is responsible for material matching (match_hs_group) and for
    setting data_confidence LOW on forwarder-masked records before this call.
    """
    # 1. Preconditions.
    if n_shipments < MIN_SHIPMENTS:
        return ScoreResult(
            verdict=Verdict.INSUFFICIENT_HISTORY,
            reason=f"{n_shipments} shipments, under the {MIN_SHIPMENTS} minimum",
        )
    if data_confidence == DataConfidence.LOW:
        return ScoreResult(
            verdict=Verdict.INSUFFICIENT_HISTORY,
            reason="LOW data confidence, forwarder-masked or HS inferred from text only",
        )
    if len(intervals) < 3:
        return ScoreResult(
            verdict=Verdict.INSUFFICIENT_HISTORY,
            reason=f"{len(intervals)} intervals, under the 3 minimum to trust a cadence",
        )

    # 2. Gap detection.
    gap = compute_gap(intervals, days_since_last)

    # 3. FIT.
    f1 = PRODUCT_FIT[hs_group]
    f2 = china_share
    f3 = VOLUME_FIT[volume_band]
    f4 = maturity_score(n_shipments, data_confidence)
    fit = W_PRODUCT * f1 + W_CHINA_SHARE * f2 + W_VOLUME_BAND * f3 + W_MATURITY * f4

    # 3. TIMING.
    t1 = gap_severity_score(gap.overdue_ratio)
    t2 = freshness_score(days_since_last)
    t3 = supplier_hhi
    origin_factor = 0.5 if origin_shift_flag else 1.0
    timing_inner = W_GAP_SEVERITY * t1 + W_FRESHNESS * t2 + W_CONCENTRATION_SHOCK * t3
    timing = timing_inner * (1.0 - seasonal_confidence) * origin_factor

    components = {
        "F1_product": round(f1, 4), "F2_china_share": round(f2, 4),
        "F3_volume_band": round(f3, 4), "F4_maturity": round(f4, 4),
        "T1_gap_severity": round(t1, 4), "T2_freshness": round(t2, 4),
        "T3_concentration_shock": round(t3, 4),
        "seasonal_confidence": round(seasonal_confidence, 4),
        "origin_factor": origin_factor,
    }

    fit = round(fit, 4)
    timing = round(timing, 4)

    # 4. Hard gate.
    if fit < FIT_GATE or timing < TIMING_GATE:
        return ScoreResult(
            verdict=Verdict.SCORED,
            reason=f"HARD GATE: FIT {fit} or TIMING {timing} below floor, collapsed to DISCARD",
            fit=fit, timing=timing, score=0, band=Band.DISCARD,
            gap=gap, components=components,
        )

    # 5. Score and band.
    score = round(100 * fit * timing)
    if score >= HOT_FLOOR:
        band = Band.HOT
    elif score >= WARM_FLOOR:
        band = Band.WARM
    elif score >= WATCH_FLOOR:
        band = Band.WATCH
    else:
        band = Band.DISCARD

    return ScoreResult(
        verdict=Verdict.SCORED,
        reason=f"scored {score}, gap stage {gap.stage.value}",
        fit=fit, timing=timing, score=score, band=band,
        gap=gap, components=components,
    )


# ---------------------------------------------------------------------------
# 5. SELF-TEST (reproduces 3 approved cases from the 2026-06-15 validation)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """
    Regression check against approved results. Any drift here means a constant
    or formula changed and the change was not yet revalidated and versioned.
    """
    # Case A. The founder worked case from the spec. Perfect HOT, SCORE 100.
    a = score_lead(
        hs_group=HsGroup.LEATHER_BAGS_CASES, n_shipments=10,
        data_confidence=DataConfidence.HIGH,
        intervals=[30, 30, 30, 30, 30, 30, 30, 30, 30], days_since_last=65,
        china_share=1.0, volume_band=VolumeBand.MISSING_MIDDLE,
        supplier_hhi=1.0, seasonal_confidence=0.0, origin_shift_flag=False,
    )
    assert a.score == 100 and a.band == Band.HOT, a

    # Case B. Lo & Sons, top approved HOT lead, SCORE 89.
    b = score_lead(
        hs_group=HsGroup.LEATHER_BAGS_CASES, n_shipments=8,
        data_confidence=DataConfidence.HIGH,
        intervals=[42, 45, 48, 44, 46, 43, 47], days_since_last=85,
        china_share=0.85, volume_band=VolumeBand.MISSING_MIDDLE,
        supplier_hhi=0.75, seasonal_confidence=0.0, origin_shift_flag=False,
    )
    assert b.score == 89 and b.band == Band.HOT, b

    # Case C. Modern Picnic, approved hard-gate DISCARD on TIMING under 0.30.
    c = score_lead(
        hs_group=HsGroup.LEATHER_BAGS_CASES, n_shipments=8,
        data_confidence=DataConfidence.HIGH,
        intervals=[48, 50, 52, 49, 51, 47, 53], days_since_last=40,
        china_share=0.90, volume_band=VolumeBand.BELOW_MISSING_MIDDLE,
        supplier_hhi=0.90, seasonal_confidence=0.0, origin_shift_flag=False,
    )
    assert c.band == Band.DISCARD and c.timing < TIMING_GATE, c

    # Matching layer. Pure canvas drops, genuine leather handbag joins bags.
    assert match_hs_group("4202.92", "Cotton Canvas Wallet") is None
    assert match_hs_group("4202.21", "Cowhide Leather Handbag") == HsGroup.LEATHER_BAGS_CASES
    assert is_forwarder("Oneill Logistics") is True

    print("self-test passed: 3 approved cases and 3 matching checks reproduced exactly")


if __name__ == "__main__":
    _self_test()
