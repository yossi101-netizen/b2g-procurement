"""
KritiKaal Quote Engine — Data Models
All input/output types for the quote calculation pipeline.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# ENUMS — mirrors valid values in rates_config.yaml
# ─────────────────────────────────────────────────────────────────

class Destination(str, Enum):
    UK     = "UK"
    ISRAEL = "Israel"
    EU     = "EU"


class OrderType(str, Enum):
    FIRST_STYLE_FACTORY       = "first_style_factory"
    REORDER_SAME_STYLE        = "reorder_same_style"
    NEW_STYLE_EXISTING_FACTORY = "new_style_existing_factory"

    def display(self) -> str:
        return {
            self.FIRST_STYLE_FACTORY:        "First Style / New Factory",
            self.REORDER_SAME_STYLE:         "Reorder — Same Style",
            self.NEW_STYLE_EXISTING_FACTORY: "New Style / Existing Factory",
        }[self]


class QUPTier(str, Enum):
    BASIC    = "basic"
    STANDARD = "standard"
    MAXIMUM  = "maximum"

    def display(self) -> str:
        return {
            self.BASIC:    "Basic (2%)",
            self.STANDARD: "Standard (3%)",
            self.MAXIMUM:  "Maximum (4%)",
        }[self]


class FreightMode(str, Enum):
    AUTO          = "auto"
    LCL           = "lcl"
    CONSOLIDATION = "consolidation"
    FCL           = "fcl"
    AIR           = "air"

    def display(self) -> str:
        return {
            self.AUTO:          "Auto-select",
            self.LCL:           "LCL (Less than Container Load)",
            self.CONSOLIDATION: "Consolidated LCL",
            self.FCL:           "FCL (Full Container — 20ft)",
            self.AIR:           "Air freight",
        }[self]


class QuoteCurrency(str, Enum):
    USD = "USD"
    GBP = "GBP"
    ILS = "ILS"
    EUR = "EUR"

    def symbol(self) -> str:
        return {"USD": "$", "GBP": "£", "ILS": "₪", "EUR": "€"}[self.value]


class PackagingType(str, Enum):
    STANDARD = "standard"
    BRANDED  = "branded"

    def display(self) -> str:
        return {"standard": "Standard", "branded": "Branded (premium)"}[self.value]


class OutputFormat(str, Enum):
    BOTTOM_LINE    = "bottom_line"      # Type B — single page, total only
    FULL_UNBUNDLED = "full_unbundled"   # Type A/C — Page 1 + Page 2 breakdown


# ─────────────────────────────────────────────────────────────────
# INPUT MODEL
# ─────────────────────────────────────────────────────────────────

@dataclass
class QuoteInputs:
    """All variables Yossi enters in the Streamlit UI."""
    client_name:       str
    product_ref:       str
    factory_fob_usd:   float          # Per unit — from factory tender response
    units:             int
    destination:       Destination
    order_type:        OrderType
    sample_costs_usd:  float          # Actual paid from sample invoice
    qup_tier:          QUPTier
    rex_certified:     bool
    freight_mode:      FreightMode
    quote_currency:    QuoteCurrency
    packaging_type:    PackagingType
    output_format:     OutputFormat
    fx_rate_override:  Optional[float] = None   # Live rate — required for non-USD
    notes:             Optional[str]   = None


# ─────────────────────────────────────────────────────────────────
# OUTPUT MODEL
# ─────────────────────────────────────────────────────────────────

@dataclass
class QuoteResult:
    """Complete calculation output — drives both Streamlit UI and DOCX generator."""

    # ── Identity ────────────────────────────────────────────────
    inputs:           QuoteInputs
    quote_ref:        str
    generated_at:     str        # "24 May 2026"
    config_version:   str        # MD5 hash of rates_config for audit

    # ── Manufacturing passthrough ────────────────────────────────
    factory_fob_per_unit:   float
    factory_fob_total:      float
    packaging_per_unit:     float
    packaging_total:        float

    # ── Pre-production & compliance (internal; bundled into PMQ line on quote) ──
    preproduction_total:    float    # Actual sample costs paid
    compliance_total:       float    # REACH + azo + CoO + conditional REX setup

    # ── Logistics passthrough ────────────────────────────────────
    cbm_total:              float
    freight_mode_used:      str      # Resolved mode (e.g. "lcl" after auto-select)
    freight_mode_display:   str      # Human label
    freight_total:          float
    duty_rate_applied:      float    # e.g. 0.035 or 0.0
    duty_display:           str      # e.g. "3.5% MFN — HS 4202.21"
    duty_total:             float
    broker_total:           float
    port_total:             float
    insurance_total:        float

    # ── Passthrough subtotals ────────────────────────────────────
    manufacturing_passthrough:  float   # factory_fob + packaging
    logistics_passthrough:      float
    total_cost_passthrough:     float

    # ── KritiKaal service fees ───────────────────────────────────
    mmf:                        float   # Raw MMF from lookup
    qup_rate:                   float   # e.g. 0.03
    qup_total:                  float
    qup_description:            str     # From config

    # Combined display line for Page 2 (hides MMF + preproduction + compliance)
    production_management_qa:   float   # = mmf + preproduction + compliance

    # ── FX ──────────────────────────────────────────────────────
    fx_buffer_rate:         float
    fx_buffer_amount:       float
    fx_rate_used:           float       # Actual conversion rate applied

    # ── Grand totals ─────────────────────────────────────────────
    total_usd:                    float
    total_quote_currency:         float
    per_unit_quote_currency:      float

    # ── Gross profit (internal — never printed on DOCX) ──────────
    kritikaal_gross_margin_usd:   float
    gp_pct:                       float
    gp_status:                    str   # "on_target" | "amber" | "below_target"
    gp_alert:                     str   # Human-readable alert string
    gp_recommendation:            Optional[str]

    # ── Lead times ───────────────────────────────────────────────
    production_lead_time_str:  str
    transit_days_str:          str
    total_lead_time_str:       str
    destination_port:          str
