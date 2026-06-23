"""
Landed-Cost Calculator — India -> US (Amazon FBA primary, B2B secondary)

Designed for future API integration: every external rate (FX, duty, freight,
FBA fees, PPC benchmarks) is injected via a Rate provider, not hardcoded in
the math. Swap MockRateProvider for a real one (USITC HTS API, Freightos,
SP-API GetMyFeesEstimate, Helium10) without touching the math layer.

Currency convention: all internal math in USD. INR inputs converted at the
FX rate supplied by the provider at calc time.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Protocol, Literal, Optional
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# 1. Rate provider interface (swap mock -> real APIs later)
# ---------------------------------------------------------------------------

class RateProvider(Protocol):
    def fx_inr_to_usd(self) -> float: ...
    def duty_rate(self, hts_code: str, origin: str) -> float: ...  # decimal, e.g. 0.313
    def freight_usd_per_kg(self, mode: Literal["air", "sea_lcl", "sea_fcl"]) -> float: ...
    def fba_fulfillment_fee_usd(self, weight_lb: float, size_tier: str) -> float: ...
    def fba_storage_usd_per_month(self, cubic_ft: float, peak: bool = False) -> float: ...


class MockRateProvider:
    """Hardcoded 2026 planning baselines. Replace with API-backed provider."""

    def fx_inr_to_usd(self) -> float:
        return 1 / 83.5  # ~83.5 INR per USD planning rate

    def duty_rate(self, hts_code: str, origin: str) -> float:
        # 2026 planning baseline; pull live from USITC + CSMS in production
        table = {
            ("6304.92.0000", "IN"): 0.313,   # 6.3% MFN + 25% India add-on
            ("6302.21.9020", "IN"): 0.317,
            ("8306.29.0000", "IN"): 0.250,
            ("4420.90.8000", "IN"): 0.282,
            ("4205.00.8000", "IN"): 0.250,
            ("7117.90.9000", "IN"): 0.360,
        }
        return table.get((hts_code, origin), 0.30)  # conservative default

    def freight_usd_per_kg(self, mode: str) -> float:
        # Door-to-door, India -> US, 2026 planning numbers
        return {"air": 6.50, "sea_lcl": 1.20, "sea_fcl": 0.55}[mode]

    def fba_fulfillment_fee_usd(self, weight_lb: float, size_tier: str) -> float:
        # Simplified 2026 US FBA fee schedule (small/standard size, non-apparel)
        # Real provider should call SP-API GetMyFeesEstimate per ASIN.
        if size_tier == "small_standard":
            if weight_lb <= 0.5:
                return 3.27
            if weight_lb <= 1.0:
                return 3.95
            return 4.45
        if size_tier == "large_standard":
            return 5.40 + max(0.0, weight_lb - 1.0) * 0.20
        return 9.00  # oversize fallback

    def fba_storage_usd_per_month(self, cubic_ft: float, peak: bool = False) -> float:
        rate = 2.40 if peak else 0.78  # standard-size, off-peak vs Q4
        return cubic_ft * rate


# ---------------------------------------------------------------------------
# 2. Inputs
# ---------------------------------------------------------------------------

@dataclass
class ProductInputs:
    # Identity
    sku: str
    hts_code: str
    origin: str = "IN"

    # Sourcing (India)
    unit_cost_inr: float = 0.0
    qty: int = 1

    # India-side prep / branding / QC (per unit, INR)
    india_prep_inr: float = 0.0          # labeling, branding, FNSKU sticker, polybag
    india_qc_inr: float = 0.0            # third-party inspection share
    india_inland_inr: float = 0.0        # factory -> port

    # Physical (per unit)
    weight_kg: float = 0.0
    cubic_ft: float = 0.0                # for FBA storage
    weight_lb: float = field(init=False)

    # Freight mode + insurance
    freight_mode: Literal["air", "sea_lcl", "sea_fcl"] = "sea_lcl"
    insurance_pct_of_cif: float = 0.005  # 0.5% of CIF

    # US-side
    customs_broker_usd_per_shipment: float = 175.0
    us_prep_usd_per_unit: float = 0.0    # if not pre-prepped in India
    inbound_to_fba_usd_per_unit: float = 0.35
    fba_size_tier: str = "small_standard"
    fba_storage_months: float = 2.5
    fba_peak_storage: bool = False

    # Selling (Amazon US)
    target_sell_price_usd: Optional[float] = None  # if None, computed
    amazon_referral_pct: float = 0.15
    returns_reserve_pct: float = 0.06
    ppc_pct_of_revenue: float = 0.18      # ACoS planning buffer
    target_net_margin_pct: float = 0.20   # after all costs

    def __post_init__(self):
        self.weight_lb = self.weight_kg * 2.20462


# ---------------------------------------------------------------------------
# 3. Output
# ---------------------------------------------------------------------------

@dataclass
class LandedCostBreakdown:
    # Per-unit costs (USD)
    goods_cost: float
    india_prep: float
    india_qc: float
    india_inland: float
    international_freight: float
    insurance: float
    cif_value: float
    duty: float
    mpf: float
    hmf: float
    customs_broker: float
    us_prep: float
    inbound_to_fba: float
    fba_fulfillment: float
    fba_storage: float
    landed_cost_pre_amazon: float

    # Revenue-side variables (USD)
    target_sell_price: float
    amazon_referral_fee: float
    ppc_cost: float
    returns_cost: float
    total_amazon_side_costs: float

    # Verdict
    net_profit_per_unit: float
    net_margin_pct: float
    multiple_on_landed: float
    passes_3x: bool

    def as_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# 4. The calculation
# ---------------------------------------------------------------------------

def _round(x: float, places: int = 4) -> float:
    return float(Decimal(str(x)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP))


def calculate(p: ProductInputs, r: RateProvider) -> LandedCostBreakdown:
    fx = r.fx_inr_to_usd()

    # --- India side, per unit, in USD ---
    goods_cost = p.unit_cost_inr * fx
    india_prep = p.india_prep_inr * fx
    india_qc = p.india_qc_inr * fx
    india_inland = p.india_inland_inr * fx

    fob_value = goods_cost + india_prep + india_qc + india_inland

    # --- Freight + insurance (CIF) ---
    freight_per_unit = p.weight_kg * r.freight_usd_per_kg(p.freight_mode)
    cif_pre_ins = fob_value + freight_per_unit
    insurance = cif_pre_ins * p.insurance_pct_of_cif
    cif_value = cif_pre_ins + insurance

    # --- US duties & fees ---
    duty_rate = r.duty_rate(p.hts_code, p.origin)
    duty = cif_value * duty_rate

    # Merchandise Processing Fee: 0.3464% of entered value, min $32.71 / max $634.62 PER SHIPMENT
    # Amortized per unit using qty.
    mpf_shipment = max(32.71, min(634.62, cif_value * p.qty * 0.003464))
    mpf = mpf_shipment / max(p.qty, 1)

    # Harbor Maintenance Fee: 0.125% of value, sea only
    hmf = (cif_value * 0.00125) if p.freight_mode.startswith("sea") else 0.0

    broker_per_unit = p.customs_broker_usd_per_shipment / max(p.qty, 1)

    # --- US logistics + FBA prep ---
    us_prep = p.us_prep_usd_per_unit
    inbound = p.inbound_to_fba_usd_per_unit
    fba_fulfill = r.fba_fulfillment_fee_usd(p.weight_lb, p.fba_size_tier)
    fba_storage_total = r.fba_storage_usd_per_month(p.cubic_ft, p.fba_peak_storage) * p.fba_storage_months

    # --- Landed cost before Amazon revenue-side fees ---
    landed = (
        goods_cost + india_prep + india_qc + india_inland +
        freight_per_unit + insurance +
        duty + mpf + hmf + broker_per_unit +
        us_prep + inbound + fba_fulfill + fba_storage_total
    )

    # --- Sell price: either supplied, or solved to hit target net margin ---
    if p.target_sell_price_usd is not None:
        sell = p.target_sell_price_usd
    else:
        # Solve: sell - landed - referral*sell - ppc*sell - returns*sell = margin*sell
        # => sell * (1 - referral - ppc - returns - margin) = landed
        denom = 1 - p.amazon_referral_pct - p.ppc_pct_of_revenue - p.returns_reserve_pct - p.target_net_margin_pct
        if denom <= 0:
            raise ValueError("Fee + PPC + returns + target margin >= 100% of revenue. Unsolvable.")
        sell = landed / denom

    referral = sell * p.amazon_referral_pct
    ppc = sell * p.ppc_pct_of_revenue
    returns = sell * p.returns_reserve_pct
    amazon_side = referral + ppc + returns

    net_profit = sell - landed - amazon_side
    net_margin = net_profit / sell if sell else 0
    multiple = sell / landed if landed else 0
    passes_3x = multiple >= 3.0

    return LandedCostBreakdown(
        goods_cost=_round(goods_cost),
        india_prep=_round(india_prep),
        india_qc=_round(india_qc),
        india_inland=_round(india_inland),
        international_freight=_round(freight_per_unit),
        insurance=_round(insurance),
        cif_value=_round(cif_value),
        duty=_round(duty),
        mpf=_round(mpf),
        hmf=_round(hmf),
        customs_broker=_round(broker_per_unit),
        us_prep=_round(us_prep),
        inbound_to_fba=_round(inbound),
        fba_fulfillment=_round(fba_fulfill),
        fba_storage=_round(fba_storage_total),
        landed_cost_pre_amazon=_round(landed),
        target_sell_price=_round(sell, 2),
        amazon_referral_fee=_round(referral),
        ppc_cost=_round(ppc),
        returns_cost=_round(returns),
        total_amazon_side_costs=_round(amazon_side),
        net_profit_per_unit=_round(net_profit),
        net_margin_pct=_round(net_margin, 4),
        multiple_on_landed=_round(multiple, 3),
        passes_3x=passes_3x,
    )


# ---------------------------------------------------------------------------
# 5. Pretty-print
# ---------------------------------------------------------------------------

def report(p: ProductInputs, b: LandedCostBreakdown) -> str:
    lines = [
        f"SKU: {p.sku}  |  HTS {p.hts_code}  |  Origin {p.origin}  |  Qty {p.qty}",
        f"Freight mode: {p.freight_mode}  |  Weight {p.weight_kg} kg  |  Volume {p.cubic_ft} ft^3",
        "-" * 72,
        "INDIA-SIDE (per unit, USD)",
        f"  Goods cost ................. {b.goods_cost:>8.2f}",
        f"  India prep / branding ...... {b.india_prep:>8.2f}",
        f"  India QC ................... {b.india_qc:>8.2f}",
        f"  Inland to port ............. {b.india_inland:>8.2f}",
        "FREIGHT & INSURANCE",
        f"  International freight ...... {b.international_freight:>8.2f}",
        f"  Insurance .................. {b.insurance:>8.2f}",
        f"  CIF value .................. {b.cif_value:>8.2f}",
        "US ENTRY",
        f"  Duty ....................... {b.duty:>8.2f}",
        f"  MPF ........................ {b.mpf:>8.2f}",
        f"  HMF ........................ {b.hmf:>8.2f}",
        f"  Customs broker (per unit) .. {b.customs_broker:>8.2f}",
        "US LOGISTICS & FBA",
        f"  US prep .................... {b.us_prep:>8.2f}",
        f"  Inbound to FBA ............. {b.inbound_to_fba:>8.2f}",
        f"  FBA fulfillment fee ........ {b.fba_fulfillment:>8.2f}",
        f"  FBA storage (total months) . {b.fba_storage:>8.2f}",
        "-" * 72,
        f"LANDED COST (pre-Amazon-revenue-fees) . {b.landed_cost_pre_amazon:>8.2f}",
        "",
        f"Target sell price ............ {b.target_sell_price:>8.2f}",
        f"  Amazon referral (15%) ...... {b.amazon_referral_fee:>8.2f}",
        f"  PPC ({p.ppc_pct_of_revenue:.0%} of revenue) .... {b.ppc_cost:>8.2f}",
        f"  Returns reserve ({p.returns_reserve_pct:.0%}) ... {b.returns_cost:>8.2f}",
        f"  Total Amazon-side .......... {b.total_amazon_side_costs:>8.2f}",
        "-" * 72,
        f"NET PROFIT / unit ............ {b.net_profit_per_unit:>8.2f}",
        f"Net margin ................... {b.net_margin_pct:>8.1%}",
        f"Sell / Landed multiple ....... {b.multiple_on_landed:>8.2f}x",
        f"Passes 3x gate ............... {'YES' if b.passes_3x else 'NO'}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. Mock simulation — generic cotton cushion cover
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    provider = MockRateProvider()

    p = ProductInputs(
        sku="CUSHION-COVER-18x18-NATURAL",
        hts_code="6304.92.0000",       # cotton furnishing, decorative throw / cushion cover
        origin="IN",

        # A distressed export-surplus lot: 500 units at ~INR 180 each (~$2.16)
        unit_cost_inr=180.0,
        qty=500,

        # India-side branding & prep done at the factory:
        india_prep_inr=35.0,            # polybag, hangtag, FNSKU, care label
        india_qc_inr=12.0,              # share of SGS inspection cost
        india_inland_inr=8.0,           # factory -> Mundra/Nhava Sheva

        # Physical
        weight_kg=0.18,
        cubic_ft=0.08,

        freight_mode="sea_lcl",         # 500 units doesn't fill an FCL
        insurance_pct_of_cif=0.005,

        customs_broker_usd_per_shipment=175.0,
        us_prep_usd_per_unit=0.0,       # pre-prepped in India
        inbound_to_fba_usd_per_unit=0.35,
        fba_size_tier="small_standard",
        fba_storage_months=2.5,
        fba_peak_storage=False,

        # Let calculator solve sell price for 20% net margin
        target_sell_price_usd=None,
        amazon_referral_pct=0.15,
        returns_reserve_pct=0.06,
        ppc_pct_of_revenue=0.18,
        target_net_margin_pct=0.20,
    )

    breakdown = calculate(p, provider)
    print(report(p, breakdown))
