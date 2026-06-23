"""
Blended Channel Strategy Optimizer
====================================
For a single compliant lot held in Bangalore, finds the optimal split
across Direct FOB, Faire B2B, and Amazon FBA to maximize a chosen objective.

The key insight this model exists to prove:
  The "best channel" is not a single answer — it changes based on whether
  you are optimizing for CASH TODAY, PROFIT TOTAL, or CAPITAL VELOCITY.
  The optimal blended strategy is different for each objective, and the
  difference in real-dollar outcomes is significant.

Three optimization objectives:
  1. MAX_VELOCITY  — maximize annualized ROI on full capital (deploy faster)
  2. MAX_TOTAL     — maximize total net profit from the lot
  3. MAX_LIQUIDITY — maximize cash returned within 45 days (capital conservation)

The model also produces a STAGING PLAN:
  Deploy capital in tranches — FOB first (cash back fastest), fund next lot
  from proceeds, then scale to Faire/FBA with validated demand.

Usage:
  python3 blended_strategy.py                        # default 600-unit lot
  python3 blended_strategy.py --units 400 --budget 8000
  python3 blended_strategy.py --objective MAX_TOTAL
"""

from __future__ import annotations

import sys
import os
import argparse
from dataclasses import dataclass
from itertools import product as iproduct
from typing import List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from channel_comparison import (
    Lot, model_fba_b2c, model_faire_b2b, model_direct_fob,
    MockRateProvider, ChannelResult
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

STEP = 0.10       # allocation sweep granularity (10% increments)
INF  = float("inf")

ANSI = dict(
    green  = "\033[92m", yellow = "\033[93m",
    red    = "\033[91m", bold   = "\033[1m",
    cyan   = "\033[96m", reset  = "\033[0m",
)

def c(color: str, text: str) -> str:
    return f"{ANSI[color]}{text}{ANSI['reset']}"


# ---------------------------------------------------------------------------
# Per-channel unit economics (thin wrapper around channel_comparison models)
# ---------------------------------------------------------------------------

@dataclass
class ChannelMetrics:
    name:         str
    capital_unit: float   # $ you must deploy per unit (your out-of-pocket)
    profit_unit:  float   # $ net profit per unit after all costs
    margin_pct:   float
    ccc_days:     int
    turns_year:   float
    ann_roi:      float


def get_channel_metrics(lot: Lot, fx: float) -> Tuple[ChannelMetrics, ChannelMetrics, ChannelMetrics]:
    fba   = model_fba_b2c(lot, fx)
    faire = model_faire_b2b(lot, fx)
    fob   = model_direct_fob(lot, fx)

    def to_metrics(r: ChannelResult, name: str) -> ChannelMetrics:
        return ChannelMetrics(
            name         = name,
            capital_unit = r.landed_cost_unit,
            profit_unit  = r.net_profit_unit,
            margin_pct   = r.net_margin_pct,
            ccc_days     = r.ccc_days,
            turns_year   = r.turns_per_year,
            ann_roi      = r.annualized_roi_pct,
        )

    return (
        to_metrics(fob,   "Direct FOB"),
        to_metrics(faire, "Faire B2B"),
        to_metrics(fba,   "Amazon FBA"),
    )


# ---------------------------------------------------------------------------
# Cash flow timeline
# ---------------------------------------------------------------------------

def cash_at_day(n: int, metrics: ChannelMetrics, day: int) -> float:
    """
    Approximate cash returned by `day` for n units in this channel.

    Modelling assumptions:
    - FOB: lump sum payment at CCC day (single transaction)
    - Faire: 70% of orders fulfilled in first half of sellthrough, rest in second half
    - FBA: revenue streams in evenly over sellthrough period (daily disbursements)
    """
    if n == 0:
        return 0.0
    total_cash = n * (metrics.capital_unit + metrics.profit_unit)  # full recovery

    if metrics.name == "Direct FOB":
        return total_cash if day >= metrics.ccc_days else 0.0

    elif metrics.name == "Faire B2B":
        # 60% of wholesale orders arrive in first 30 days of availability,
        # 30% days 30-60, 10% tail. Availability starts at logistics end (77d).
        avail_day = metrics.ccc_days - 25   # logistics complete before full sellthrough
        if day < avail_day:
            return 0.0
        elapsed = day - avail_day
        frac = min(1.0, 0.6 * min(elapsed / 30, 1.0)
                      + 0.3 * max(0, min((elapsed - 30) / 30, 1.0))
                      + 0.1 * max(0, min((elapsed - 60) / 30, 1.0)))
        return total_cash * frac

    else:   # Amazon FBA — revenue streams linearly over sellthrough window
        logistics_days = 77   # same as CCC calc base
        if day < logistics_days:
            return 0.0
        sell_days = metrics.ccc_days - logistics_days
        elapsed   = day - logistics_days
        frac = min(1.0, elapsed / sell_days)
        return total_cash * frac


# ---------------------------------------------------------------------------
# Blended allocation evaluator
# ---------------------------------------------------------------------------

@dataclass
class BlendedResult:
    fob_pct:   float
    faire_pct: float
    fba_pct:   float
    # unit counts
    n_fob:   int
    n_faire: int
    n_fba:   int
    # economics
    capital_deployed: float
    total_profit:     float
    blended_margin:   float
    blended_ccc:      float
    blended_ann_roi:  float
    # liquidity checkpoints
    cash_day_45:  float
    cash_day_90:  float
    cash_day_180: float
    # capital recovered (as fraction) by day
    pct_recovered_45:  float
    pct_recovered_90:  float
    pct_recovered_180: float


def evaluate_blend(
    n_fob: int, n_faire: int, n_fba: int,
    fob_m: ChannelMetrics, faire_m: ChannelMetrics, fba_m: ChannelMetrics,
    budget: float
) -> Optional[BlendedResult]:
    total_units = n_fob + n_faire + n_fba
    if total_units == 0:
        return None

    capital = (n_fob   * fob_m.capital_unit
             + n_faire * faire_m.capital_unit
             + n_fba   * fba_m.capital_unit)
    if capital > budget:
        return None  # over budget

    profit = (n_fob   * fob_m.profit_unit
            + n_faire * faire_m.profit_unit
            + n_fba   * fba_m.profit_unit)

    if capital <= 0:
        return None

    blended_margin = profit / (capital + profit)   # profit / revenue
    blended_ann_roi = profit / capital * (365 / (
        (n_fob   * fob_m.ccc_days
       + n_faire * faire_m.ccc_days
       + n_fba   * fba_m.ccc_days) / total_units
    ))

    blended_ccc = (
        n_fob   * fob_m.ccc_days
      + n_faire * faire_m.ccc_days
      + n_fba   * fba_m.ccc_days
    ) / total_units

    def cash(d: int) -> float:
        return (cash_at_day(n_fob, fob_m, d)
              + cash_at_day(n_faire, faire_m, d)
              + cash_at_day(n_fba, fba_m, d))

    total_expected_cash = capital + profit
    c45  = cash(45)
    c90  = cash(90)
    c180 = cash(180)

    return BlendedResult(
        fob_pct   = n_fob / total_units,
        faire_pct = n_faire / total_units,
        fba_pct   = n_fba / total_units,
        n_fob     = n_fob,
        n_faire   = n_faire,
        n_fba     = n_fba,
        capital_deployed  = round(capital, 2),
        total_profit      = round(profit, 2),
        blended_margin    = blended_margin,
        blended_ccc       = round(blended_ccc, 1),
        blended_ann_roi   = blended_ann_roi,
        cash_day_45  = round(c45,  2),
        cash_day_90  = round(c90,  2),
        cash_day_180 = round(c180, 2),
        pct_recovered_45  = c45  / total_expected_cash,
        pct_recovered_90  = c90  / total_expected_cash,
        pct_recovered_180 = c180 / total_expected_cash,
    )


# ---------------------------------------------------------------------------
# Sweep all allocations
# ---------------------------------------------------------------------------

def sweep(lot: Lot, budget: float,
          fob_m: ChannelMetrics, faire_m: ChannelMetrics, fba_m: ChannelMetrics
         ) -> List[BlendedResult]:
    """
    Enumerate all unit splits in ~10-unit increments.
    Returns all feasible (capital ≤ budget) results.
    """
    results = []
    step = max(1, lot.qty // 20)   # 20 increments across lot

    for n_fob in range(0, lot.qty + 1, step):
        for n_faire in range(0, lot.qty - n_fob + 1, step):
            n_fba = lot.qty - n_fob - n_faire
            if n_fba < 0:
                continue
            r = evaluate_blend(n_fob, n_faire, n_fba,
                               fob_m, faire_m, fba_m, budget)
            if r is not None:
                results.append(r)

    # also always evaluate the single-unit boundary cases
    for (f, fa, fb) in [(lot.qty, 0, 0), (0, lot.qty, 0), (0, 0, lot.qty)]:
        r = evaluate_blend(f, fa, fb, fob_m, faire_m, fba_m, budget)
        if r:
            results.append(r)

    return results


# ---------------------------------------------------------------------------
# Optimal picks
# ---------------------------------------------------------------------------

def find_optima(results: List[BlendedResult]) -> dict:
    return {
        "MAX_VELOCITY":  max(results, key=lambda r: r.blended_ann_roi),
        "MAX_TOTAL":     max(results, key=lambda r: r.total_profit),
        "MAX_LIQUIDITY": max(results, key=lambda r: r.pct_recovered_45),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_blend(r: BlendedResult, label: str = "", highlight: bool = False):
    prefix = c("bold", f"★ {label}") if highlight else f"  {label}"
    print(f"\n{prefix}")
    print(f"  Allocation:  FOB {r.fob_pct:.0%} ({r.n_fob}u)  "
          f"| Faire {r.faire_pct:.0%} ({r.n_faire}u)  "
          f"| FBA {r.fba_pct:.0%} ({r.n_fba}u)")
    print(f"  Capital:     ${r.capital_deployed:,.0f}  "
          f"| Profit: ${r.total_profit:,.0f}  "
          f"| Margin: {r.blended_margin:.1%}")
    print(f"  Blended CCC: {r.blended_ccc:.0f}d  "
          f"| Ann ROI: {c('cyan', f'{r.blended_ann_roi:.0%}')}")

    liq_color = lambda p: "green" if p >= 0.5 else "yellow" if p >= 0.25 else "red"
    print(f"  Cash at d45: {c(liq_color(r.pct_recovered_45),  f'${r.cash_day_45:,.0f} ({r.pct_recovered_45:.0%})')}"
          f"  | d90: {c(liq_color(r.pct_recovered_90), f'${r.cash_day_90:,.0f} ({r.pct_recovered_90:.0%})')}"
          f"  | d180: {c(liq_color(r.pct_recovered_180), f'${r.cash_day_180:,.0f} ({r.pct_recovered_180:.0%})')}")


def print_full_report(lot: Lot, results: List[BlendedResult],
                      optima: dict,
                      fob_m: ChannelMetrics, faire_m: ChannelMetrics, fba_m: ChannelMetrics):

    print(f"\n{'═'*72}")
    print(c("bold", f"  BLENDED CHANNEL OPTIMIZER — {lot.sku}"))
    print(f"  {lot.qty} units @ INR {lot.unit_cost_inr}/pc  |  "
          f"{len(results)} feasible allocations evaluated")
    print(f"{'═'*72}")

    # Channel reference
    print(f"\n{c('bold', 'SINGLE-CHANNEL BENCHMARKS')}")
    for m in (fob_m, faire_m, fba_m):
        print(f"  {m.name:<16} cap/u=${m.capital_unit:.2f}  "
              f"profit/u=${m.profit_unit:.2f}  "
              f"margin={m.margin_pct:.1%}  "
              f"CCC={m.ccc_days}d  "
              f"AnnROI={c('cyan', f'{m.ann_roi:.0%}')}")

    # Three optima
    print(f"\n{c('bold', 'OPTIMAL BLENDS BY OBJECTIVE')}")
    for obj, r in optima.items():
        print_blend(r, label=obj, highlight=True)

    # Insight matrix
    best_vel   = optima["MAX_VELOCITY"]
    best_tot   = optima["MAX_TOTAL"]
    best_liq   = optima["MAX_LIQUIDITY"]

    print(f"\n{'─'*72}")
    print(c("bold", "  THE THREE OBJECTIVES — WHAT EACH COSTS YOU"))
    print(f"{'─'*72}")
    print(f"  {'Objective':<20} {'Allocation':<28} {'Ann ROI':>8} {'Total $':>9} {'d45 cash':>10}")
    print(f"  {'-'*69}")
    for obj, r in optima.items():
        alloc = (f"FOB {r.fob_pct:.0%} / "
                 f"Faire {r.faire_pct:.0%} / "
                 f"FBA {r.fba_pct:.0%}")
        print(f"  {obj:<20} {alloc:<28} "
              f"{r.blended_ann_roi:>8.0%} "
              f"${r.total_profit:>7,.0f} "
              f"${r.cash_day_45:>8,.0f}")

    # Staging recommendation
    _print_staging_plan(lot, optima, fob_m, faire_m, fba_m)


def _print_staging_plan(lot: Lot, optima: dict,
                        fob_m: ChannelMetrics, faire_m: ChannelMetrics, fba_m: ChannelMetrics):
    """
    The practical operating doctrine: stage the lot in tranches to get
    FOB cash back before you've fully committed to FBA capital.
    """
    # Staged plan: 40% FOB first (smallest capital, fastest return)
    #              30% Faire (medium capital, Faire validates demand)
    #              30% FBA   (fund from FOB proceeds when they return)
    qty = lot.qty
    n_fob   = int(qty * 0.40)
    n_faire = int(qty * 0.30)
    n_fba   = qty - n_fob - n_faire

    fob_cap   = n_fob   * fob_m.capital_unit
    faire_cap = n_faire * faire_m.capital_unit
    fba_cap   = n_fba   * fba_m.capital_unit
    fob_ret   = n_fob   * (fob_m.capital_unit + fob_m.profit_unit)

    print(f"\n{'═'*72}")
    print(c("bold", "  RECOMMENDED STAGING PLAN"))
    print(f"{'═'*72}")
    print(f"""
  The staged approach turns a single lot into a CAPITAL RECYCLING engine.
  You don't deploy all capital at once — FOB cash returns BEFORE FBA is
  even live, and that cash funds the next lot.

  TRANCHE 1 (deploy immediately):
    ✓ {n_fob} units → Direct FOB   capital ${fob_cap:,.0f}
    ✓ {n_faire} units → Faire B2B  capital ${faire_cap:,.0f}
    ─ Total upfront: ${fob_cap + faire_cap:,.0f}

  TRANCHE 2 (deploy at day ~72 from FOB proceeds):
    ✓ {n_fba} units → Amazon FBA  capital ${fba_cap:,.0f}
    → FOB returns ${fob_ret:,.0f} at day 72 — covers FBA capital entirely
    → FBA launch funded by FOB profit, not new capital

  NET EFFECT:
    You operate as if you only spent ${fob_cap + faire_cap:,.0f} of new capital.
    FBA runs on recycled money. You never have all ${fob_cap + faire_cap + fba_cap:,.0f}
    deployed simultaneously — the CCC overlap does that for you.

  CRITICAL GATE:
    Only route Tranche 2 (FBA) if Faire B2B reveals real US retailer demand.
    If Faire wholesale orders come in slowly → route Tranche 2 to FOB instead.
    Never escalate to FBA based on faith — only on Faire demand signal.
""")

    print(f"{'─'*72}")
    print(c("bold", "  ROUTING DECISION RULES (per lot, per SKU)"))
    print(f"{'─'*72}")
    print(f"""
  Route 100% FOB if:
    • Estimated ACoS > 25% (heatmap dead zone)
    • Need capital back within 60 days (liquidity constraint)
    • Category is commodity/undifferentiated
    • Lot is a distressed "unknown" with no US demand validation

  Route 100% Faire if:
    • ACoS 18–25% (margin is real but PPC would be expensive)
    • Product has retail-shelf aesthetic (buyers will see it at trade shows)
    • You want B2B brand relationships without full FBA commitment
    • Budget below ${n_fba * fba_m.capital_unit + n_faire * faire_m.capital_unit:,.0f} (can't fund FBA)

  Route to FBA only if:
    • ACoS ≤ 18% (heatmap survival with margin)
    • Faire orders confirm real US retail demand at this price point
    • Product has repeat-purchase or subscription potential
    • You can afford 128-day CCC without capital stress

  Route to BLEND (staged) if:
    • None of the above is definitively true
    • You want data before committing full capital to one channel
    • This is a new SKU with no prior US sales history
""")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Blended Channel Optimizer")
    parser.add_argument("--units",     type=int,   default=600)
    parser.add_argument("--cost-inr",  type=float, default=175.0)
    parser.add_argument("--budget",    type=float, default=10000.0,
                        help="Max capital to deploy (USD)")
    parser.add_argument("--objective", choices=["MAX_VELOCITY","MAX_TOTAL","MAX_LIQUIDITY"],
                        default=None, help="Print only the top result for this objective")
    args = parser.parse_args()

    lot           = Lot(unit_cost_inr=args.cost_inr, qty=args.units)
    fx            = MockRateProvider().fx_inr_to_usd()
    fob_m, faire_m, fba_m = get_channel_metrics(lot, fx)

    print(f"\nSweeping {args.units} units × 3 channels × budget ${args.budget:,.0f}...")
    results = sweep(lot, args.budget, fob_m, faire_m, fba_m)
    print(f"Feasible allocations: {len(results)}")

    optima = find_optima(results)

    if args.objective:
        print_blend(optima[args.objective], label=args.objective, highlight=True)
    else:
        print_full_report(lot, results, optima, fob_m, faire_m, fba_m)


if __name__ == "__main__":
    main()
