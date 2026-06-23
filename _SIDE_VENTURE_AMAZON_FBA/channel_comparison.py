"""
Channel Comparison Model — B2C Amazon FBA vs B2B Wholesale
===========================================================
Routes ONE identical vetted lot (held in Bangalore) through three exit paths
and computes unit economics, lot-level P&L, Cash Conversion Cycle (CCC), and
— the metric that actually decides this — ANNUALIZED RETURN ON CAPITAL.

The insight this model exists to prove:
    Net margin % is a vanity metric. Capital VELOCITY (margin × turns/year)
    is what fills the bank account. A 35% margin that takes 180 days can lose
    to a 14% margin that takes 45 days.

Channels modeled:
    1. FBA_B2C       — Amazon FBA, sell individual units to consumers
    2. FAIRE_B2B     — Faire.com wholesale marketplace (you ship to US 3PL,
                       fulfill wholesale orders, Faire takes commission)
    3. DIRECT_FOB    — Direct bulk buyer, sold FOB Bangalore (buyer takes
                       possession in India; you never touch US logistics)

Baseline lot: HTS 6304.92.0000 cotton cushion cover, 600 units @ INR 175/pc
Reuses FX + duty logic from landed_cost_calculator.py for consistency.
"""

from __future__ import annotations

import sys, os
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landed_cost_calculator import MockRateProvider
from tariff_heatmap import ParametricRateProvider

# ---------------------------------------------------------------------------
# Shared lot definition
# ---------------------------------------------------------------------------

@dataclass
class Lot:
    sku: str            = "CUSHION-COVER-18x18"
    hts: str            = "6304.92.0000"
    unit_cost_inr: float= 175.0
    qty: int            = 600
    weight_kg: float    = 0.18
    cubic_ft: float     = 0.08
    # India-side prep (per unit, INR) — bulk packing cheaper than FBA prep
    prep_inr_b2c: float = 40.0    # FNSKU, polybag, hangtag, retail-ready
    prep_inr_b2b: float = 18.0    # bulk poly, master cartons only
    qc_inr: float       = 12.0
    inland_inr: float   = 8.0
    # US market anchors
    retail_price_usd: float    = 19.99   # Amazon consumer price (Helium10)
    faire_wholesale_usd: float = 9.50    # wholesale price on Faire (~48% of retail)
    direct_bulk_usd: float     = 6.25    # FOB India bulk price to a US importer
    tariff: float       = 0.313


@dataclass
class ChannelResult:
    name: str
    sell_price_unit: float
    landed_cost_unit: float
    selling_costs_unit: float
    net_profit_unit: float
    net_margin_pct: float
    # Lot level
    units_sold: int
    total_capital_deployed: float
    total_net_profit: float
    lot_roi_pct: float
    # Velocity
    ccc_days: int
    turns_per_year: float
    annualized_roi_pct: float
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared cost components
# ---------------------------------------------------------------------------

def india_side_cost(lot: Lot, prep_inr: float, fx: float) -> float:
    """Per-unit goods + prep + QC + inland, in USD."""
    return (lot.unit_cost_inr + prep_inr + lot.qc_inr + lot.inland_inr) * fx


def duty_block(cif_unit: float, lot: Lot, qty: int, sea: bool = True) -> float:
    """Duty + MPF (amortized) + HMF per unit."""
    provider = ParametricRateProvider(lot.tariff)
    duty = cif_unit * provider.duty_rate(lot.hts, "IN")
    mpf  = max(32.71, min(634.62, cif_unit * qty * 0.003464)) / qty
    hmf  = cif_unit * 0.00125 if sea else 0.0
    return duty + mpf + hmf


# ---------------------------------------------------------------------------
# CHANNEL 1 — Amazon FBA B2C
# ---------------------------------------------------------------------------

def model_fba_b2c(lot: Lot, fx: float,
                  ppc_pct: float = 0.22,      # blended launch+steady ACoS
                  returns_pct: float = 0.08,  # home textiles run high
                  sellthrough_units_per_day: float = 7.0) -> ChannelResult:
    india   = india_side_cost(lot, lot.prep_inr_b2c, fx)
    freight = lot.weight_kg * MockRateProvider().freight_usd_per_kg("sea_lcl")
    insurance = (india + freight) * 0.005
    cif     = india + freight + insurance
    duties  = duty_block(cif, lot, lot.qty, sea=True)
    broker  = 175.0 / lot.qty
    inbound = 0.35
    fba_fulfill = 3.27
    fba_storage = 0.78 * lot.cubic_ft * 2.5   # ~2.5 months avg dwell

    landed = india + freight + insurance + duties + broker + inbound + fba_fulfill + fba_storage

    sell    = lot.retail_price_usd
    referral= sell * 0.15
    ppc     = sell * ppc_pct
    returns = sell * returns_pct
    selling = referral + ppc + returns

    net_unit = sell - landed - selling
    margin   = net_unit / sell

    units_sold = lot.qty
    capital    = landed * lot.qty
    total_net  = net_unit * units_sold
    lot_roi    = total_net / capital

    # CCC: deposit -> production(20) + freight(40) + customs/inbound(12) +
    #      FBA receive(5) + sellthrough(qty/rate) ; Amazon pays every 14d
    logistics_days = 20 + 40 + 12 + 5
    sellthrough_days = lot.qty / sellthrough_units_per_day
    ccc = int(logistics_days + sellthrough_days * 0.6)  # 0.6: cash arrives mid-stream
    turns = 365 / ccc
    ann_roi = lot_roi * turns

    return ChannelResult(
        name="Amazon FBA B2C",
        sell_price_unit=sell, landed_cost_unit=landed,
        selling_costs_unit=selling, net_profit_unit=net_unit,
        net_margin_pct=margin, units_sold=units_sold,
        total_capital_deployed=capital, total_net_profit=total_net,
        lot_roi_pct=lot_roi, ccc_days=ccc, turns_per_year=turns,
        annualized_roi_pct=ann_roi,
        notes=[
            f"PPC assumed {ppc_pct:.0%} ACoS, returns {returns_pct:.0%}",
            f"Sell-through {sellthrough_units_per_day:.0f} units/day = "
            f"{lot.qty/sellthrough_units_per_day:.0f} days to clear lot",
            "Revenue arrives as a STREAM (Amazon disburses every 14 days)",
            "Capital fully recovered only after last unit sells",
        ],
    )


# ---------------------------------------------------------------------------
# CHANNEL 2 — Faire B2B (ship to US 3PL, wholesale fulfillment)
# ---------------------------------------------------------------------------

def model_faire_b2b(lot: Lot, fx: float,
                    faire_commission: float = 0.18,  # blended new+rebuy
                    sellthrough_units_per_day: float = 12.0) -> ChannelResult:
    india   = india_side_cost(lot, lot.prep_inr_b2b, fx)
    freight = lot.weight_kg * MockRateProvider().freight_usd_per_kg("sea_lcl")
    insurance = (india + freight) * 0.005
    cif     = india + freight + insurance
    duties  = duty_block(cif, lot, lot.qty, sea=True)
    broker  = 175.0 / lot.qty
    threepl = 0.45   # 3PL pick/pack/store per unit (cheaper than FBA, bulk-ish)

    landed = india + freight + insurance + duties + broker + threepl

    sell    = lot.faire_wholesale_usd
    commission = sell * faire_commission
    # no PPC (Faire surfaces you), minimal returns in B2B (~2%)
    returns = sell * 0.02
    selling = commission + returns

    net_unit = sell - landed - selling
    margin   = net_unit / sell

    units_sold = lot.qty
    capital    = landed * lot.qty
    total_net  = net_unit * units_sold
    lot_roi    = total_net / capital

    # CCC: production(20)+freight(40)+customs(12)+3PL receive(5) + wholesale
    #      sellthrough (faster, bulk orders) ; Faire pays ~ next business day after ship
    logistics_days = 20 + 40 + 12 + 5
    sellthrough_days = lot.qty / sellthrough_units_per_day
    ccc = int(logistics_days + sellthrough_days * 0.5)
    turns = 365 / ccc
    ann_roi = lot_roi * turns

    return ChannelResult(
        name="Faire B2B Wholesale",
        sell_price_unit=sell, landed_cost_unit=landed,
        selling_costs_unit=selling, net_profit_unit=net_unit,
        net_margin_pct=margin, units_sold=units_sold,
        total_capital_deployed=capital, total_net_profit=total_net,
        lot_roi_pct=lot_roi, ccc_days=ccc, turns_per_year=turns,
        annualized_roi_pct=ann_roi,
        notes=[
            f"Faire commission {faire_commission:.0%}, no PPC, returns ~2%",
            f"Wholesale orders clear faster ({sellthrough_units_per_day:.0f} u/day)",
            "Faire pays out fast (≈ next business day after you ship order)",
            "Still requires US 3PL + you carry customs/freight risk",
        ],
    )


# ---------------------------------------------------------------------------
# CHANNEL 3 — Direct bulk buyer, FOB Bangalore (you never touch US logistics)
# ---------------------------------------------------------------------------

def model_direct_fob(lot: Lot, fx: float,
                     net_terms_days: int = 45) -> ChannelResult:
    # You sell FOB India: NO freight, NO duty, NO US fees. Buyer takes title in India.
    india   = india_side_cost(lot, lot.prep_inr_b2b, fx)
    # You still incur inland to port if FOB (included in india), nothing else US-side.
    landed  = india   # your cost basis is just landed-in-Bangalore

    sell    = lot.direct_bulk_usd   # FOB India price
    selling = 0.0                   # no platform, no PPC; maybe small broker fee
    broker_fee = sell * 0.02        # sourcing-broker commission if any
    selling = broker_fee

    net_unit = sell - landed - selling
    margin   = net_unit / sell

    units_sold = lot.qty
    capital    = landed * lot.qty
    total_net  = net_unit * units_sold
    lot_roi    = total_net / capital

    # CCC: production/QC(20) + buyer inspects & lifts goods(7) + net terms
    ccc = int(20 + 7 + net_terms_days)
    turns = 365 / ccc
    ann_roi = lot_roi * turns

    return ChannelResult(
        name="Direct Bulk (FOB India)",
        sell_price_unit=sell, landed_cost_unit=landed,
        selling_costs_unit=selling, net_profit_unit=net_unit,
        net_margin_pct=margin, units_sold=units_sold,
        total_capital_deployed=capital, total_net_profit=total_net,
        lot_roi_pct=lot_roi, ccc_days=ccc, turns_per_year=turns,
        annualized_roi_pct=ann_roi,
        notes=[
            f"FOB Bangalore — buyer takes title in India, net-{net_terms_days} terms",
            "ZERO freight/duty/US-fee exposure — buyer bears all of it",
            "Lowest price but lowest risk and fastest capital return",
            "Single transaction clears entire lot at once",
        ],
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_channel(r: ChannelResult):
    print(f"\n{'═'*68}")
    print(f"  {r.name.upper()}")
    print(f"{'═'*68}")
    print(f"  PER UNIT (USD)")
    print(f"    Sell price ............... {r.sell_price_unit:>8.2f}")
    print(f"    Landed cost .............. {r.landed_cost_unit:>8.2f}")
    print(f"    Selling costs ............ {r.selling_costs_unit:>8.2f}")
    print(f"    Net profit ............... {r.net_profit_unit:>8.2f}")
    print(f"    Net margin ............... {r.net_margin_pct:>8.1%}")
    print(f"  LOT LEVEL ({r.units_sold} units)")
    print(f"    Capital deployed ......... {r.total_capital_deployed:>8.0f}")
    print(f"    Total net profit ......... {r.total_net_profit:>8.0f}")
    print(f"    Lot ROI .................. {r.lot_roi_pct:>8.1%}")
    print(f"  CAPITAL VELOCITY")
    print(f"    Cash Conversion Cycle .... {r.ccc_days:>6} days")
    print(f"    Turns per year ........... {r.turns_per_year:>8.2f}")
    print(f"    ★ ANNUALIZED ROI ......... {r.annualized_roi_pct:>8.1%}")
    print(f"  NOTES")
    for n in r.notes:
        print(f"    • {n}")


def print_verdict(results: list):
    print(f"\n\n{'█'*68}")
    print(f"  HEAD-TO-HEAD  —  same lot, same capital, three exits")
    print(f"{'█'*68}")
    hdr = f"  {'Metric':<26}" + "".join(f"{r.name.split()[0]:>14}" for r in results)
    print(hdr)
    print("  " + "-"*(len(hdr)-2))
    def row(label, fmt, key):
        vals = "".join(f"{fmt(getattr(r,key)):>14}" for r in results)
        print(f"  {label:<26}{vals}")
    row("Net margin %",      lambda v: f"{v:.1%}",  "net_margin_pct")
    row("Net profit / unit", lambda v: f"${v:.2f}", "net_profit_unit")
    row("Total lot profit",  lambda v: f"${v:,.0f}","total_net_profit")
    row("Capital deployed",  lambda v: f"${v:,.0f}","total_capital_deployed")
    row("Lot ROI %",         lambda v: f"{v:.1%}",  "lot_roi_pct")
    row("CCC (days)",        lambda v: f"{v}d",     "ccc_days")
    row("Turns / year",      lambda v: f"{v:.2f}x", "turns_per_year")
    print("  " + "-"*(len(hdr)-2))
    row("★ ANNUALIZED ROI",  lambda v: f"{v:.0%}",  "annualized_roi_pct")

    best = max(results, key=lambda r: r.annualized_roi_pct)
    print(f"\n  ► Highest capital velocity: {best.name} "
          f"({best.annualized_roi_pct:.0%} annualized)")
    rich = max(results, key=lambda r: r.net_margin_pct)
    print(f"  ► Richest per-unit margin:  {rich.name} "
          f"({rich.net_margin_pct:.1%} net)")


if __name__ == "__main__":
    lot = Lot()
    fx  = MockRateProvider().fx_inr_to_usd()

    print(f"\n{'━'*68}")
    print(f"  CHANNEL COMPARISON  —  {lot.sku}")
    print(f"  {lot.qty} units @ INR {lot.unit_cost_inr}/pc  |  "
          f"FX {1/fx:.1f} INR/USD  |  tariff {lot.tariff:.1%}")
    print(f"{'━'*68}")

    r1 = model_fba_b2c(lot, fx)
    r2 = model_faire_b2b(lot, fx)
    r3 = model_direct_fob(lot, fx)

    for r in (r1, r2, r3):
        print_channel(r)

    print_verdict([r1, r2, r3])
