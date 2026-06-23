"""
KritiKaal Quote Engine — Calculation Engine
Single source of truth for all cost calculations.
Edit rates_config.yaml to change rates — never hardcode values here.
"""
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import yaml

from .models import (
    Destination,
    FreightMode,
    OrderType,
    QuoteCurrency,
    QuoteInputs,
    QuoteResult,
    QUPTier,
)


# ─────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _config_hash(cfg: dict) -> str:
    """Stable 8-char MD5 hash of config for audit trail."""
    serialized = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()[:8].upper()


def generate_quote_ref(sequence: int = 1) -> str:
    """Generate quote reference: KK-YYYYMMDD-NNN.
    Pass sequence from SQLite quotes table for uniqueness."""
    today = date.today().strftime("%Y%m%d")
    return f"KK-{today}-{sequence:03d}"


# ─────────────────────────────────────────────────────────────────
# INTERNAL CALCULATION HELPERS
# ─────────────────────────────────────────────────────────────────

def _mmf_lookup(cfg: dict, order_type: str, units: int) -> float:
    """Look up MMF midpoint from band table."""
    table = cfg["mmf"][order_type]
    if units < 100:
        return float(table["50-99"])
    elif units < 300:
        return float(table["100-299"])
    elif units < 500:
        return float(table["300-499"])
    elif units < 1000:
        return float(table["500-999"])
    else:
        return float(table["1000+"])


def _select_freight_mode(
    cbm_total: float, cfg: dict, requested: FreightMode
) -> FreightMode:
    """Resolve AUTO to a concrete mode; return others unchanged."""
    if requested != FreightMode.AUTO:
        return requested
    thresholds = cfg["freight_mode_thresholds"]
    if cbm_total <= thresholds["lcl_max_cbm"]:
        return FreightMode.LCL
    elif cbm_total >= thresholds["fcl_min_cbm"]:
        return FreightMode.FCL
    else:
        return FreightMode.CONSOLIDATION


def _calc_freight(cbm_total: float, mode: FreightMode, route: dict) -> float:
    """Calculate freight cost. Applies Red Sea premium where active."""
    if mode == FreightMode.LCL:
        cost = route["lcl_per_cbm_usd"] * cbm_total
        if route.get("red_sea_active", False):
            cost *= 1 + route.get("red_sea_premium", 0)
    elif mode == FreightMode.CONSOLIDATION:
        cost = route["consolidation_per_cbm_usd"] * cbm_total
        if route.get("red_sea_active", False):
            cost *= 1 + route.get("red_sea_premium", 0)
    elif mode == FreightMode.FCL:
        cost = float(route["fcl_20ft_usd"])
    elif mode == FreightMode.AIR:
        # 167 kg per CBM (volumetric standard). Rate read from rates_config.yaml.
        # Never hardcode rates in Python — edit rates_config.yaml to update.
        air_rate = float(route.get("air_rate_usd_per_kg", 8.0))
        cost = cbm_total * 167 * air_rate
    else:
        cost = route["lcl_per_cbm_usd"] * cbm_total
    return round(cost, 2)


def _duty_display(cfg: dict, destination: Destination, rex_certified: bool) -> str:
    dest_cfg = cfg["customs"][destination.value]
    if rex_certified:
        return dest_cfg.get("duty_note_rex", f"{dest_cfg['rex_rate']*100:.1f}%")
    else:
        return dest_cfg.get("duty_note_mfn", f"{dest_cfg['mfn_rate']*100:.1f}% MFN")


# ─────────────────────────────────────────────────────────────────
# MAIN CALCULATOR CLASS
# ─────────────────────────────────────────────────────────────────

class QuoteCalculator:
    """
    Loads rates_config.yaml and a product YAML once at startup.
    Call calculate() for each quote — pure function, no side effects.
    """

    def __init__(self, config_path: Path, product_path: Path):
        # ── Load and validate config
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        self.cfg = _load_yaml(config_path)
        self.config_version = _config_hash(self.cfg)

        # ── Load and validate product
        if not product_path.exists():
            raise FileNotFoundError(f"Product file not found: {product_path}")
        self.product = _load_yaml(product_path)

        if not self.product or "reference" not in self.product:
            raise ValueError(f"Invalid product file: {product_path} (missing 'reference' key)")

    # ── Public API ───────────────────────────────────────────────

    def validate(self, inputs: QuoteInputs) -> list:
        """Returns list of error strings. Empty = valid."""
        errors = []

        # ── Volume validation
        if inputs.units < 50:
            errors.append("Minimum order quantity is 50 units.")
        if inputs.units > 50000:
            errors.append("Order quantity exceeds maximum (50,000 units). Contact sales for special pricing.")

        # ── FOB price validation
        if inputs.factory_fob_usd <= 0:
            errors.append("Factory FOB price must be greater than zero.")

        # ── Sample costs validation
        if inputs.sample_costs_usd < 0:
            errors.append("Sample costs cannot be negative.")

        # ── Client name validation
        if not inputs.client_name or not inputs.client_name.strip():
            errors.append("Client name is required.")

        # ── FX rate validation
        if inputs.fx_rate_override is not None and inputs.fx_rate_override <= 0:
            errors.append("FX rate override must be positive. (e.g., GBP: 0.79, ILS: 3.70)")

        # ── FX availability check
        if (
            inputs.quote_currency != QuoteCurrency.USD
            and inputs.fx_rate_override is None
            and inputs.quote_currency.value not in self.cfg.get("fx_fallback_rates", {})
        ):
            errors.append(
                f"No FX rate for {inputs.quote_currency.value}. "
                "Provide an override rate or add fallback to rates_config.yaml."
            )

        return errors

    def calculate(self, inputs: QuoteInputs, quote_ref: str) -> QuoteResult:
        """
        Execute the full calculation pipeline.
        All business rules are driven from rates_config.yaml.
        Returns an immutable QuoteResult dataclass.
        """
        cfg = self.cfg
        prod = self.product
        units = inputs.units

        # ── 1. MANUFACTURING PASSTHROUGH ────────────────────────
        factory_fob_total = round(inputs.factory_fob_usd * units, 2)

        pkg_type = inputs.packaging_type.value
        pkg_per_unit = float(cfg["packaging"][pkg_type]["total_per_unit"])
        packaging_total = round(pkg_per_unit * units, 2)

        manufacturing_passthrough = factory_fob_total + packaging_total

        # ── 2. PRE-PRODUCTION & COMPLIANCE (bundled on client quote) ──
        preproduction_total = round(inputs.sample_costs_usd, 2)

        comp = cfg["compliance"]
        compliance_total = (
            float(comp["reach_test_per_batch"])
            + float(comp["azo_dye_test_per_batch"])
            + float(comp["coo_per_shipment"])
        )
        # Add REX setup cost for UK orders without REX
        if (
            not inputs.rex_certified
            and inputs.destination == Destination.UK
        ):
            compliance_total += float(comp["rex_setup_if_needed"])
        compliance_total = round(compliance_total, 2)

        # ── 3. LOGISTICS PASSTHROUGH ─────────────────────────────
        cbm_per_unit = float(prod["packed"]["cbm_per_unit"])
        cbm_total = round(cbm_per_unit * units, 3)

        route_key = f"india_{inputs.destination.value}"
        route_cfg = cfg["freight"][route_key]

        freight_mode_used = _select_freight_mode(cbm_total, cfg, inputs.freight_mode)
        freight_total = _calc_freight(cbm_total, freight_mode_used, route_cfg)

        # CIF base for duty and insurance calculation
        # (manufacturing passthrough + pre-prod + compliance + freight)
        cif_value = (
            manufacturing_passthrough
            + preproduction_total
            + compliance_total
            + freight_total
        )

        customs_cfg = cfg["customs"][inputs.destination.value]
        duty_rate = (
            float(customs_cfg["rex_rate"])
            if inputs.rex_certified
            else float(customs_cfg["mfn_rate"])
        )
        duty_total = round(cif_value * duty_rate, 2)

        broker_total = round(float(customs_cfg["broker_fee_usd"]), 2)
        port_total = round(
            float(customs_cfg["port_handling_per_unit_usd"]) * units, 2
        )
        insurance_total = round(cif_value * float(cfg["insurance_rate"]), 2)

        logistics_passthrough = round(
            freight_total + duty_total + broker_total + port_total + insurance_total,
            2,
        )

        total_cost_passthrough = round(
            manufacturing_passthrough + logistics_passthrough, 2
        )

        # ── 4. KRITIKAAL SERVICE FEES ─────────────────────────────
        mmf = round(_mmf_lookup(cfg, inputs.order_type.value, units), 2)

        qup_tier_cfg = cfg["qup_tiers"][inputs.qup_tier.value]
        qup_rate = float(qup_tier_cfg["rate"])
        qup_total = round(total_cost_passthrough * qup_rate, 2)
        qup_description = str(qup_tier_cfg["description"])

        # CRITICAL: This is the combined display line.
        # Bundles MMF + pre-production + compliance to prevent
        # line-by-line negotiation on the unbundled view.
        production_management_qa = round(
            mmf + preproduction_total + compliance_total, 2
        )

        # ── 5. FX BUFFER ─────────────────────────────────────────
        fx_buffer_rate = float(cfg["fx_buffers"].get(inputs.quote_currency.value, 0.0))
        subtotal_before_fx = round(
            total_cost_passthrough + production_management_qa + qup_total, 2
        )
        fx_buffer_amount = round(subtotal_before_fx * fx_buffer_rate, 2)

        # ── 6. GRAND TOTALS ──────────────────────────────────────
        total_usd = round(subtotal_before_fx + fx_buffer_amount, 2)

        # FX conversion
        if inputs.fx_rate_override is not None:
            fx_rate_used = float(inputs.fx_rate_override)
        else:
            fallbacks = cfg.get("fx_fallback_rates", {})
            fx_rate_used = float(fallbacks.get(inputs.quote_currency.value, 1.0))

        if inputs.quote_currency == QuoteCurrency.USD:
            total_quote_currency = total_usd
        else:
            total_quote_currency = round(total_usd * fx_rate_used, 2)

        per_unit_quote_currency = round(total_quote_currency / units, 2)

        # ── 7. GROSS PROFIT ──────────────────────────────────────
        # KritiKaal earns: MMF + QUP + FX buffer
        # Pre-production and compliance are KritiKaal costs billed through PMQ line
        kritikaal_gross_margin_usd = round(
            production_management_qa + qup_total + fx_buffer_amount
            - preproduction_total - compliance_total,
            2,
        )
        gp_pct = round(kritikaal_gross_margin_usd / total_usd, 4) if total_usd > 0 else 0.0

        gp_target = float(cfg["gp_target"])
        gp_amber  = float(cfg["gp_amber_threshold"])
        gp_red    = float(cfg.get("gp_red_threshold", 0.14))

        if gp_pct >= gp_target:
            gp_status = "on_target"
            gp_alert  = f"✅ ON TARGET — {gp_pct:.1%} GP (target: {gp_target:.0%})"
            gp_recommendation = None
        elif gp_pct >= gp_amber:
            gp_status = "amber"
            gp_alert  = f"⚠️  BELOW TARGET — {gp_pct:.1%} GP (target: {gp_target:.0%})"
            shortfall = round((gp_target * total_usd - kritikaal_gross_margin_usd) / (1 - gp_target), 0)
            gp_recommendation = (
                f"Increase MMF by ${shortfall:,.0f} "
                f"(to ${mmf + shortfall:,.0f}) to reach {gp_target:.0%} target."
            )
        else:
            gp_status = "below_target"
            gp_alert  = f"🔴 UNACCEPTABLE — {gp_pct:.1%} GP. Do not issue this quote."
            shortfall = round((gp_target * total_usd - kritikaal_gross_margin_usd) / (1 - gp_target), 0)
            gp_recommendation = (
                f"Increase MMF by ${shortfall:,.0f} "
                f"(to ${mmf + shortfall:,.0f}), or upgrade to Maximum QUP (4%)."
            )

        # ── 8. LEAD TIMES ────────────────────────────────────────
        # Product YAML can override global lead times via lead_times_override.
        # This allows corporate gift accessories (2–4 weeks) to show correct
        # lead times rather than the global default (10–14 weeks for large bags).
        lt = cfg["lead_times"]
        prod_lt_override = prod.get("lead_times_override", {})
        prod_min = int(prod_lt_override.get("production_min_weeks", lt["production_min_weeks"]))
        prod_max = int(prod_lt_override.get("production_max_weeks", lt["production_max_weeks"]))
        # Air freight uses route-specific air transit days when available
        if freight_mode_used == FreightMode.AIR:
            tr_min = int(route_cfg.get("transit_days_air_min", route_cfg["transit_days_min"]))
            tr_max = int(route_cfg.get("transit_days_air_max", route_cfg["transit_days_max"]))
        else:
            tr_min = int(route_cfg["transit_days_min"])
            tr_max = int(route_cfg["transit_days_max"])

        production_lead_time_str = (
            f"{prod_min}–{prod_max} weeks from sample approval"
        )
        transit_mode_label = "air transit" if freight_mode_used == FreightMode.AIR else "sea transit"
        transit_days_str = f"{tr_min}–{tr_max} days {transit_mode_label}"
        total_weeks_min  = prod_min + (tr_min // 7)
        total_weeks_max  = prod_max + (tr_max // 7)
        total_lead_time_str = f"{total_weeks_min}–{total_weeks_max} weeks door-to-door"

        return QuoteResult(
            inputs=inputs,
            quote_ref=quote_ref,
            generated_at=datetime.now().strftime("%d %B %Y"),
            config_version=self.config_version,

            factory_fob_per_unit=inputs.factory_fob_usd,
            factory_fob_total=factory_fob_total,
            packaging_per_unit=pkg_per_unit,
            packaging_total=packaging_total,

            preproduction_total=preproduction_total,
            compliance_total=compliance_total,

            cbm_total=cbm_total,
            freight_mode_used=freight_mode_used.value,
            freight_mode_display=freight_mode_used.display(),
            freight_total=freight_total,
            duty_rate_applied=duty_rate,
            duty_display=_duty_display(cfg, inputs.destination, inputs.rex_certified),
            duty_total=duty_total,
            broker_total=broker_total,
            port_total=port_total,
            insurance_total=insurance_total,

            manufacturing_passthrough=manufacturing_passthrough,
            logistics_passthrough=logistics_passthrough,
            total_cost_passthrough=total_cost_passthrough,

            mmf=mmf,
            qup_rate=qup_rate,
            qup_total=qup_total,
            qup_description=qup_description,
            production_management_qa=production_management_qa,

            fx_buffer_rate=fx_buffer_rate,
            fx_buffer_amount=fx_buffer_amount,
            fx_rate_used=fx_rate_used,

            total_usd=total_usd,
            total_quote_currency=total_quote_currency,
            per_unit_quote_currency=per_unit_quote_currency,

            kritikaal_gross_margin_usd=kritikaal_gross_margin_usd,
            gp_pct=gp_pct,
            gp_status=gp_status,
            gp_alert=gp_alert,
            gp_recommendation=gp_recommendation,

            production_lead_time_str=production_lead_time_str,
            transit_days_str=transit_days_str,
            total_lead_time_str=total_lead_time_str,
            destination_port=str(route_cfg["port"]),
        )
