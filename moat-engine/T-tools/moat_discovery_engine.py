"""
Single-Product Moat Discovery Engine
ABC-TOM project: moat-engine. Demand-only, made-in-India -> West.

This module scores a candidate SINGLE-PRODUCT opportunity (the PillowCube /
Vessi / BigFig playbook) on three axes and decides whether it is worth pursuing:

    DEMAND      is anyone searching for it AND are real US importers buying it?
    MOAT        can it be branded / premium-built, or is it a cheap commodity
                that cheap algorithmic sellers will knock off in a month?
    COMPLIANCE  can it actually clear Western import regulation from India?

The output mirrors the proven us_bol_scoring_engine.py shape:
FINAL = 100 * DEMAND * MOAT * compliance_factor, with hard gates that collapse a
candidate to DISCARD regardless of the other axes, then HOT / WARM / WATCH bands.

AIR-GAP CONTRACT (same as us_bol_scoring_engine.py, BI_HUNTING_PLAYBOOK Section 0):
This file is a standalone math and logic processor. It imports nothing from any
hub, reads no database, performs no network access, and scrapes nothing. It takes
plain data structures in and returns plain results out. All ingestion lives
outside this module:
  - keyword metrics (volume, KD, breadth, trend) are gathered by hand from Ahrefs
    or the free-tier stack (Google Keyword Planner / Trends / autocomplete /
    Keyword Surfer) -- see B-brain/02-data-sources.md.
  - import-validation metrics (unique / repeat US importers) come from the
    ImportYeti CSV export that already feeds INDIA-STOCKS/src/bol_pipeline.py.
The human (or a thin ingestion layer) fills an OpportunityInput and calls
score_opportunity(). This module never decides where the numbers came from.

DESIGN SOURCE:
B-brain/01-scoring-model.md is the canonical spec. The constants and formulas
below ARE that spec. If you change a weight or a gate here, bump the spec
version and re-run the self-test. The self-test at the bottom freezes five
reference cases (one HOT, one WARM, and the three hard-gate DISCARDs).

CALIBRATION STATUS:
v0.1 -- initial thresholds, NOT yet validated against a real provider pull.
Recalibrate against the first batch of real ImportYeti + Ahrefs candidates
before trusting the absolute scores; until then treat the BANDS as directional
and the GATE REASONS as the real product.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# 0. ENUMS AND CONSTANTS (v0.1, frozen against the self-test)
# ---------------------------------------------------------------------------

class TrendDirection(str, Enum):
    RISING = "RISING"        # Google Trends slope up, or rising related queries
    FLAT = "FLAT"
    DECLINING = "DECLINING"


class Level(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriceBand(str, Enum):
    HIGH_TICKET = "HIGH_TICKET"  # >$120 sell, or strongly giftable (BigBarker, BikeTowLeash, Nutr)
    MID = "MID"                  # ~$30-120 (MindJournals $50, gym bag)
    LOW = "LOW"                  # <$30 impulse / commodity territory


class ComplianceStatus(str, Enum):
    CLEAR = "CLEAR"                      # no material friction for India -> target market
    DOCUMENTED_LOAD = "DOCUMENTED_LOAD"  # passable, but needs certs/test reports (REACH Cr(VI), EUDR DD, Prop65 labelling)
    HARD_BLOCK = "HARD_BLOCK"            # CITES/banned input/named-restriction -> do not pursue


class Verdict(str, Enum):
    SCORED = "SCORED"


class Band(str, Enum):
    HOT = "HOT"
    WARM = "WARM"
    WATCH = "WATCH"
    DISCARD = "DISCARD"


# --- DEMAND axis weights (sum = 1.00) ---------------------------------------
W_VOLUME = 0.25       # how many people are searching the cluster
W_DIFFICULTY = 0.30   # headline signal: low keyword difficulty = winnable discovery
W_BREADTH = 0.15      # the "fan of zero-comp long-tail" pattern (BikeTowLeash, Nutr)
W_IMPORT = 0.30       # hard cross-reference: real US importers actually buying (BoL)

# --- MOAT axis weights (sum = 1.00) -----------------------------------------
W_MATERIAL = 0.25     # can premium material (full-grain leather, real finishing) elevate it?
W_WEDGE = 0.15        # "best X for [specific subset]" defensible sub-segment
W_BRAND = 0.20        # giftable / story-driven / B2B positioning vs price-only
W_KNOCKOFF = 0.30     # headline defense: resistance to cheap algorithmic knock-offs
W_UNIT_ECON = 0.10    # high-ticket / giftable supports a real brand build

# --- Hard gates -------------------------------------------------------------
KD_GATE = 35.0        # cluster KD above this: discovery is not winnable, DISCARD
DEMAND_GATE = 0.40    # below this DEMAND: nobody is searching/buying enough, DISCARD
MOAT_GATE = 0.40      # below this MOAT: a cheap knock-off target, DISCARD (the core filter)

# --- Compliance haircut -----------------------------------------------------
COMPLIANCE_FACTOR = {
    ComplianceStatus.CLEAR: 1.0,
    ComplianceStatus.DOCUMENTED_LOAD: 0.85,
    # HARD_BLOCK never reaches the multiply; it is a veto gate.
}

# --- Score bands (shared with us_bol_scoring_engine.py for consistency) ------
HOT_FLOOR = 55
WARM_FLOOR = 35
WATCH_FLOOR = 20

# Import-validation reference gates, kept aligned with bol_pipeline.py defaults.
BOL_MIN_UNIQUE = 5
BOL_MIN_REPEAT = 2


# ---------------------------------------------------------------------------
# 1. INPUT / OUTPUT STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class OpportunityInput:
    """One candidate single-product opportunity, hand-filled from the data stack."""
    name: str

    # --- DEMAND: keyword cluster (Ahrefs or free-tier equivalents) ---
    cluster_volume: int          # SUM of monthly searches across the keyword cluster
    cluster_kd: float            # difficulty to beat, 0-100 (Ahrefs KD or a free proxy)
    n_low_comp_terms: int        # how many cluster terms sit at KD <= 10 (breadth of easy wins)
    trend: TrendDirection        # Google Trends direction for the cluster

    # --- DEMAND: import validation (ImportYeti CSV -> bol_pipeline metrics) ---
    bol_unique_importers: int    # distinct US consignees buying this category
    bol_repeat_importers: int    # consignees with >= 2 shipments (real reorder behaviour)
    india_is_proven_origin: bool = False  # India already ships this category (de-risks "made in India")

    # --- MOAT ---
    material_premium: Level = Level.LOW      # can full-grain / premium material meaningfully elevate it?
    niche_wedge: bool = False                # is there a "best X for [subset]" defensible wedge?
    brandability: Level = Level.LOW          # giftable / story / B2B vs price-only commodity
    commodity_risk: Level = Level.HIGH       # how easily a cheap algorithmic seller knocks it off
    price_band: PriceBand = PriceBand.LOW

    # --- COMPLIANCE ---
    compliance_status: ComplianceStatus = ComplianceStatus.CLEAR
    compliance_notes: list[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    verdict: Verdict
    name: str
    reason: str
    demand: Optional[float] = None
    moat: Optional[float] = None
    compliance_factor: Optional[float] = None
    score: Optional[int] = None
    band: Optional[Band] = None
    components: dict = field(default_factory=dict)
    gates_tripped: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. DEMAND COMPONENTS (each returns 0.0 .. 1.0)
# ---------------------------------------------------------------------------

def volume_score(cluster_volume: int) -> float:
    """D1. Aggregate monthly search volume across the cluster, banded."""
    v = cluster_volume
    if v >= 20000:
        return 1.0
    if v >= 10000:
        return 0.85
    if v >= 5000:
        return 0.65
    if v >= 2000:
        return 0.45
    if v >= 500:
        return 0.25
    return 0.10


def difficulty_score(cluster_kd: float) -> float:
    """D2. Inverse of keyword difficulty. Low KD = winnable = high score."""
    kd = cluster_kd
    if kd <= 5:
        return 1.0
    if kd <= 10:
        return 0.85
    if kd <= 15:
        return 0.65
    if kd <= 25:
        return 0.40
    if kd <= 40:
        return 0.20
    return 0.05


def breadth_score(n_low_comp_terms: int) -> float:
    """D3. The 'fan of many zero-competition long-tails' pattern."""
    n = n_low_comp_terms
    if n >= 8:
        return 1.0
    if n >= 5:
        return 0.80
    if n >= 3:
        return 0.60
    if n >= 1:
        return 0.35
    return 0.10


def import_validation_score(unique_importers: int, repeat_importers: int) -> float:
    """
    D4. Hard demand cross-reference from US Bill-of-Lading data.
    The 0.80 tier is exactly the bol_pipeline.py default gate (>=5 unique, >=2 repeat).
    """
    u, r = unique_importers, repeat_importers
    if r >= 3 and u >= 8:
        return 1.0
    if r >= BOL_MIN_REPEAT and u >= BOL_MIN_UNIQUE:
        return 0.80
    if u >= BOL_MIN_UNIQUE:
        return 0.50
    if u >= 2:
        return 0.30
    return 0.10


_TREND_MULT = {
    TrendDirection.RISING: 1.0,
    TrendDirection.FLAT: 0.90,
    TrendDirection.DECLINING: 0.60,
}


def compute_demand(opp: OpportunityInput) -> tuple[float, dict]:
    d1 = volume_score(opp.cluster_volume)
    d2 = difficulty_score(opp.cluster_kd)
    d3 = breadth_score(opp.n_low_comp_terms)
    d4 = import_validation_score(opp.bol_unique_importers, opp.bol_repeat_importers)
    base = W_VOLUME * d1 + W_DIFFICULTY * d2 + W_BREADTH * d3 + W_IMPORT * d4
    mult = _TREND_MULT[opp.trend]
    demand = base * mult
    parts = {
        "D1_volume": round(d1, 4),
        "D2_difficulty": round(d2, 4),
        "D3_breadth": round(d3, 4),
        "D4_import": round(d4, 4),
        "trend_mult": mult,
    }
    return round(demand, 4), parts


# ---------------------------------------------------------------------------
# 3. MOAT COMPONENTS (each returns 0.0 .. 1.0)
# ---------------------------------------------------------------------------

_LEVEL_SCORE = {Level.HIGH: 1.0, Level.MEDIUM: 0.60, Level.LOW: 0.25}
# Knock-off resistance is the INVERSE of commodity risk.
_KNOCKOFF_RESISTANCE = {Level.LOW: 1.0, Level.MEDIUM: 0.55, Level.HIGH: 0.15}
_PRICE_SCORE = {PriceBand.HIGH_TICKET: 1.0, PriceBand.MID: 0.70, PriceBand.LOW: 0.40}


def compute_moat(opp: OpportunityInput) -> tuple[float, dict]:
    m1 = _LEVEL_SCORE[opp.material_premium]
    m2 = 1.0 if opp.niche_wedge else 0.40
    m3 = _LEVEL_SCORE[opp.brandability]
    m4 = _KNOCKOFF_RESISTANCE[opp.commodity_risk]
    m5 = _PRICE_SCORE[opp.price_band]
    moat = (
        W_MATERIAL * m1
        + W_WEDGE * m2
        + W_BRAND * m3
        + W_KNOCKOFF * m4
        + W_UNIT_ECON * m5
    )
    parts = {
        "M1_material_premium": round(m1, 4),
        "M2_niche_wedge": round(m2, 4),
        "M3_brandability": round(m3, 4),
        "M4_knockoff_resistance": round(m4, 4),
        "M5_unit_econ": round(m5, 4),
    }
    return round(moat, 4), parts


# ---------------------------------------------------------------------------
# 4. SCORING ENGINE (gates -> score -> band)
# ---------------------------------------------------------------------------

def score_opportunity(opp: OpportunityInput) -> ScoreResult:
    """
    Run the full pipeline on one candidate.

    Order of operations (gates are vetoes, evaluated cheapest/hardest first):
      1. Compliance HARD_BLOCK   -> DISCARD (you cannot legally land it).
      2. KD above KD_GATE        -> DISCARD (you cannot win discovery).
      3. Compute DEMAND, MOAT.
      4. DEMAND below DEMAND_GATE -> DISCARD (nobody is searching/buying).
      5. MOAT below MOAT_GATE     -> DISCARD (cheap knock-off target).
      6. Otherwise score = 100 * DEMAND * MOAT * compliance_factor, then band.

    A gated DISCARD returns score 0 but still reports the computed axes it had,
    so the reason is auditable -- the gate reason is the real product here.
    """
    gates: list[str] = []

    # --- Gate 1: hard regulatory block ---
    if opp.compliance_status == ComplianceStatus.HARD_BLOCK:
        notes = "; ".join(opp.compliance_notes) or "regulatory hard block"
        gates.append("COMPLIANCE_HARD_BLOCK")
        return ScoreResult(
            verdict=Verdict.SCORED, name=opp.name,
            reason=f"DISCARD: compliance HARD_BLOCK ({notes})",
            score=0, band=Band.DISCARD, compliance_factor=0.0,
            gates_tripped=gates,
        )

    # --- Gate 2: keyword difficulty too high to win ---
    if opp.cluster_kd > KD_GATE:
        gates.append("KD_GATE")
        return ScoreResult(
            verdict=Verdict.SCORED, name=opp.name,
            reason=f"DISCARD: cluster KD {opp.cluster_kd} above winnable ceiling {KD_GATE}",
            score=0, band=Band.DISCARD, gates_tripped=gates,
        )

    # --- Compute axes ---
    demand, dparts = compute_demand(opp)
    moat, mparts = compute_moat(opp)
    cfactor = COMPLIANCE_FACTOR[opp.compliance_status]
    components = {**dparts, **mparts, "compliance_factor": cfactor}

    # --- Gate 4: demand floor ---
    if demand < DEMAND_GATE:
        gates.append("DEMAND_GATE")
        return ScoreResult(
            verdict=Verdict.SCORED, name=opp.name,
            reason=f"DISCARD: DEMAND {demand} below floor {DEMAND_GATE}",
            demand=demand, moat=moat, compliance_factor=cfactor,
            score=0, band=Band.DISCARD, components=components, gates_tripped=gates,
        )

    # --- Gate 5: moat floor (the cheap-knock-off filter) ---
    if moat < MOAT_GATE:
        gates.append("MOAT_GATE")
        return ScoreResult(
            verdict=Verdict.SCORED, name=opp.name,
            reason=f"DISCARD: MOAT {moat} below floor {MOAT_GATE} -- cheap-knock-off risk",
            demand=demand, moat=moat, compliance_factor=cfactor,
            score=0, band=Band.DISCARD, components=components, gates_tripped=gates,
        )

    # --- Score and band ---
    score = round(100 * demand * moat * cfactor)
    if score >= HOT_FLOOR:
        band = Band.HOT
    elif score >= WARM_FLOOR:
        band = Band.WARM
    elif score >= WATCH_FLOOR:
        band = Band.WATCH
    else:
        band = Band.DISCARD

    return ScoreResult(
        verdict=Verdict.SCORED, name=opp.name,
        reason=f"scored {score} -> {band.value}",
        demand=demand, moat=moat, compliance_factor=cfactor,
        score=score, band=band, components=components, gates_tripped=gates,
    )


def rank(opportunities: list[OpportunityInput]) -> list[ScoreResult]:
    """Score a batch and return survivors first, highest score first."""
    results = [score_opportunity(o) for o in opportunities]
    return sorted(results, key=lambda r: (r.score or 0), reverse=True)


# ---------------------------------------------------------------------------
# 5. SELF-TEST (freezes five reference cases: HOT, WARM, 3 gate DISCARDs)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    # Case A -- HOT. KritiKaal-native: a premium leather men's desk/EDC organizer,
    # strong low-KD cluster + proven repeat importers. (MindJournals 'men's X' shape.)
    inp_a = OpportunityInput(
        name="Full-grain leather valet tray / EDC organizer (men)",
        cluster_volume=14000, cluster_kd=6, n_low_comp_terms=6, trend=TrendDirection.RISING,
        bol_unique_importers=9, bol_repeat_importers=3, india_is_proven_origin=True,
        material_premium=Level.HIGH, niche_wedge=True, brandability=Level.HIGH,
        commodity_risk=Level.LOW, price_band=PriceBand.MID,
        compliance_status=ComplianceStatus.CLEAR,
    )
    a = score_opportunity(inp_a)
    assert a.band == Band.HOT and a.score == 86, a

    # Case E -- WARM. Decent but not exceptional on every axis; mid material / mid
    # brand / mid commodity-risk pull it into WARM, not HOT.
    inp_e = OpportunityInput(
        name="Waxed-canvas + leather trim dopp kit",
        cluster_volume=6000, cluster_kd=14, n_low_comp_terms=3, trend=TrendDirection.RISING,
        bol_unique_importers=5, bol_repeat_importers=2,
        material_premium=Level.MEDIUM, niche_wedge=True, brandability=Level.MEDIUM,
        commodity_risk=Level.MEDIUM, price_band=PriceBand.MID,
        compliance_status=ComplianceStatus.CLEAR,
    )
    e = score_opportunity(inp_e)
    assert e.band == Band.WARM and e.score == 45, e

    # Case B -- DISCARD via MOAT gate. High demand, but a generic dropship commodity
    # any cheap seller can list tomorrow. This is the core filter the system exists for.
    inp_b = OpportunityInput(
        name="Generic PU/plastic phone stand",
        cluster_volume=22000, cluster_kd=8, n_low_comp_terms=5, trend=TrendDirection.RISING,
        bol_unique_importers=6, bol_repeat_importers=2,
        material_premium=Level.LOW, niche_wedge=False, brandability=Level.LOW,
        commodity_risk=Level.HIGH, price_band=PriceBand.LOW,
        compliance_status=ComplianceStatus.CLEAR,
    )
    b = score_opportunity(inp_b)
    assert b.band == Band.DISCARD and "MOAT_GATE" in b.gates_tripped, b

    # Case C -- DISCARD via compliance HARD_BLOCK. Good demand/moat, but CITES-restricted
    # exotic leather: do not pursue regardless of how well it would sell.
    inp_c = OpportunityInput(
        name="Exotic python-leather wallet",
        cluster_volume=8000, cluster_kd=12, n_low_comp_terms=4, trend=TrendDirection.FLAT,
        bol_unique_importers=7, bol_repeat_importers=2,
        material_premium=Level.HIGH, niche_wedge=True, brandability=Level.HIGH,
        commodity_risk=Level.LOW, price_band=PriceBand.HIGH_TICKET,
        compliance_status=ComplianceStatus.HARD_BLOCK,
        compliance_notes=["CITES Appendix II reptile leather -- export/import permits"],
    )
    c = score_opportunity(inp_c)
    assert c.band == Band.DISCARD and "COMPLIANCE_HARD_BLOCK" in c.gates_tripped, c

    # Case D -- DISCARD via KD gate. Everything else strong, but the keyword space is
    # saturated (KD 45): you cannot realistically win discovery, so it never scores.
    inp_d = OpportunityInput(
        name="Leather laptop bag (saturated term)",
        cluster_volume=30000, cluster_kd=45, n_low_comp_terms=2, trend=TrendDirection.RISING,
        bol_unique_importers=10, bol_repeat_importers=4,
        material_premium=Level.HIGH, niche_wedge=False, brandability=Level.HIGH,
        commodity_risk=Level.MEDIUM, price_band=PriceBand.HIGH_TICKET,
        compliance_status=ComplianceStatus.CLEAR,
    )
    d = score_opportunity(inp_d)
    assert d.band == Band.DISCARD and "KD_GATE" in d.gates_tripped, d

    # Ranking: HOT before WARM before the DISCARDs.
    order = rank([inp_d, inp_c, inp_b, inp_e, inp_a])
    assert order[0].name == inp_a.name and order[1].name == inp_e.name, [r.name for r in order]

    print("self-test passed: HOT=86, WARM=45, and 3 hard-gate DISCARDs reproduced exactly")


if __name__ == "__main__":
    _self_test()
