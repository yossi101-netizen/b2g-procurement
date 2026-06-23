"""
KritiKaal Quote Engine — Sprint 3 (Streamlit UI)
Interactive quote generation with real-time calculations, error boundaries, and audit trail.
"""
import sys
from pathlib import Path
import json

import streamlit as st
from datetime import datetime

# ── Add quote-engine to path ──────────────────────────────────────
HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(HERE))

from engine import (
    QuoteCalculator,
    QuoteInputs,
    generate_quote_ref,
    Destination,
    OrderType,
    QUPTier,
    FreightMode,
    QuoteCurrency,
    PackagingType,
    OutputFormat,
)
from output import QuoteDocxGenerator
from db import QuoteDB, DB_PATH


# ─────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────
CONFIG_PATH = HERE / "rates_config.yaml"
PRODUCT_PATH = HERE / "products" / "KK-TB-001.yaml"


# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG & STYLING — moved to kritikaal-hub/kritikaal_app.py
# Uncomment the block below to run app.py as a STANDALONE app.
# ─────────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="KritiKaal Quote Engine",
#     page_icon="💼",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# ── Custom CSS for theme ──────────────────────────────────────────
st.markdown("""
<style>
    /* Brand colors */
    :root {
        --primary: #1A2942;      /* Dark navy */
        --accent: #C4972F;       /* Warm gold */
        --error: #D32F2F;        /* Red */
        --warning: #F57C00;      /* Orange */
        --success: #388E3C;      /* Green */
    }

    /* Header styling */
    .header-box {
        background: linear-gradient(135deg, #1A2942 0%, #2C4563 100%);
        color: white;
        padding: 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }

    .header-box h1 {
        margin: 0;
        font-size: 2.5rem;
    }

    .header-box p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    /* Price box styling */
    .price-box {
        background: #F5F5F5;
        border-left: 4px solid #C4972F;
        padding: 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }

    .price-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1A2942;
    }

    /* Alert styling */
    .alert-on-target {
        background: #E8F5E9;
        border-left: 4px solid #388E3C;
    }

    .alert-amber {
        background: #FFF3E0;
        border-left: 4px solid #F57C00;
    }

    .alert-red {
        background: #FFEBEE;
        border-left: 4px solid #D32F2F;
    }

    /* Dimmed state for irrelevant UI */
    .dimmed {
        opacity: 0.5;
        pointer-events: none;
    }

    /* Cost breakdown table */
    .cost-table {
        font-size: 0.9rem;
    }

    .cost-table td {
        padding: 0.5rem;
    }

    /* Config version badge */
    .config-badge {
        display: inline-block;
        background: #1A2942;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-family: monospace;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────
if "calculator" not in st.session_state:
    try:
        st.session_state.calculator = QuoteCalculator(
            config_path=CONFIG_PATH,
            product_path=PRODUCT_PATH,
        )
    except Exception as e:
        st.error(f"❌ Failed to initialize calculator: {str(e)}")
        st.stop()

# QuoteDB instance — initialises quotes.db on first run
if "db" not in st.session_state:
    try:
        st.session_state.db = QuoteDB(DB_PATH)
    except Exception as e:
        st.error(f"❌ Failed to initialize quote database: {str(e)}")
        st.stop()

if "last_quote" not in st.session_state:
    st.session_state.last_quote = None


# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <h1>💼 KritiKaal Quote Engine</h1>
    <p>Generate professional custom quotes with real-time calculations</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# SIDEBAR: CLIENT & ORDER INPUTS
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Quote Inputs")

    # ── Client information ────────────────────────────────────────
    st.subheader("Client Information")
    client_name = st.text_input(
        "Client Name",
        placeholder="e.g., Pioneer Leathers (Test)",
        help="Legal company name for quote header",
    )

    # ── Order details ────────────────────────────────────────────
    st.subheader("Order Details")

    col1, col2 = st.columns(2)
    with col1:
        units = st.number_input(
            "Units",
            min_value=50,
            max_value=50000,
            value=100,
            step=50,
            help="Order quantity (minimum 50, maximum 50,000)",
        )
    with col2:
        fob_per_unit = st.number_input(
            "FOB per Unit ($)",
            min_value=0.01,
            value=38.50,
            step=1.00,
            format="%.2f",
            help="Factory gate price per unit",
        )

    # ── Order type selector ───────────────────────────────────────
    order_type = st.selectbox(
        "Order Type",
        options=[OrderType.FIRST_STYLE_FACTORY, OrderType.REORDER_SAME_STYLE, OrderType.NEW_STYLE_EXISTING_FACTORY],
        format_func=lambda x: x.display(),
        help="Determines Managed Manufacturing Fee (MMF) tier",
    )

    # ── Destination ──────────────────────────────────────────────
    st.subheader("Shipment Details")
    destination = st.selectbox(
        "Destination",
        options=[Destination.UK, Destination.ISRAEL, Destination.EU],
        help="Determines duty rate and freight cost",
    )

    # ── REX certification toggle ──────────────────────────────────
    rex_certified = st.checkbox(
        "REX Certified",
        value=False,
        help="Reduces duty (except Israel). For UK: 3.5% → 0%. For EU: 3.0% → 0%.",
    )

    # ── Conditional REX note ──────────────────────────────────────
    if destination == Destination.ISRAEL and rex_certified:
        st.info("ℹ️ Israel has no India-Israel FTA. REX has no effect on duty rate.")

    # ── Freight mode ──────────────────────────────────────────────
    freight_mode = st.selectbox(
        "Freight Mode",
        options=[FreightMode.AUTO, FreightMode.LCL, FreightMode.CONSOLIDATION, FreightMode.FCL, FreightMode.AIR],
        format_func=lambda x: x.display(),
        help="Auto: <3 CBM→LCL, 3-15 CBM→Consolidation, >15 CBM→FCL",
    )

    # ── Costs ────────────────────────────────────────────────────
    st.subheader("Costs & Fees")

    col1, col2 = st.columns(2)
    with col1:
        sample_costs = st.number_input(
            "Sample Costs Paid ($)",
            min_value=0.00,
            value=350.00,
            step=50.00,
            format="%.2f",
            help="Actual amounts paid for sample development",
        )
    with col2:
        qup_tier = st.selectbox(
            "QUP Tier",
            options=[QUPTier.BASIC, QUPTier.STANDARD, QUPTier.MAXIMUM],
            format_func=lambda x: x.display(),
            help="Quality underwriting obligation level",
        )

    # ── Packaging type ───────────────────────────────────────────
    packaging_type = st.selectbox(
        "Packaging",
        options=[PackagingType.STANDARD, PackagingType.BRANDED],
        format_func=lambda x: x.display(),
    )

    # ── Quote output format ──────────────────────────────────────
    st.subheader("Quote Format")
    output_format = st.radio(
        "Output Style",
        options=[OutputFormat.BOTTOM_LINE, OutputFormat.FULL_UNBUNDLED],
        format_func=lambda x: {
            OutputFormat.BOTTOM_LINE: "📄 Bottom-Line (Type B — Single Page)",
            OutputFormat.FULL_UNBUNDLED: "📊 Full Breakdown (Type A/C — 2 Pages)",
        }[x],
        help="Bottom-Line: total only. Full Unbundled: detailed cost breakdown.",
    )

    # ── Quote currency & FX ──────────────────────────────────────
    st.subheader("Currency & Exchange Rate")

    quote_currency = st.selectbox(
        "Quote Currency",
        options=[QuoteCurrency.USD, QuoteCurrency.GBP, QuoteCurrency.ILS, QuoteCurrency.EUR],
    )

    # ── FX rate input ────────────────────────────────────────────
    fx_fallback = {
        QuoteCurrency.USD: 1.0000,
        QuoteCurrency.GBP: 0.7900,
        QuoteCurrency.ILS: 3.7000,
        QuoteCurrency.EUR: 0.9200,
    }

    default_fx = fx_fallback.get(quote_currency, 1.0)
    fx_rate = st.number_input(
        f"Exchange Rate (1 USD = ? {quote_currency.value})",
        min_value=0.001,
        value=float(default_fx),
        step=0.01,
        format="%.4f",
        help=f"Live rate — fallback: {default_fx:.4f}",
    )

    # ── Generate button ──────────────────────────────────────────
    st.divider()
    generate_button = st.button(
        "🔄 Generate Quote",
        type="primary",
        use_container_width=True,
        help="Calculate and generate quote",
    )


# ─────────────────────────────────────────────────────────────────
# MAIN CONTENT: CALCULATION & RESULTS
# ─────────────────────────────────────────────────────────────────

if generate_button:
    # ── Build inputs ──────────────────────────────────────────────
    try:
        inputs = QuoteInputs(
            client_name=client_name,
            product_ref="KK-TB-001",
            factory_fob_usd=fob_per_unit,
            units=int(units),
            destination=destination,
            order_type=order_type,
            sample_costs_usd=sample_costs,
            qup_tier=qup_tier,
            rex_certified=rex_certified,
            freight_mode=freight_mode,
            quote_currency=quote_currency,
            packaging_type=packaging_type,
            output_format=output_format,
            fx_rate_override=fx_rate if quote_currency != QuoteCurrency.USD else None,
        )
    except Exception as e:
        st.error(f"❌ Input error: {str(e)}")
        st.stop()

    # ── Validate inputs ───────────────────────────────────────────
    validation_errors = st.session_state.calculator.validate(inputs)
    if validation_errors:
        st.error("❌ Validation Failed:")
        for error in validation_errors:
            st.write(f"  • {error}")
        st.stop()

    # ── Calculate & persist ───────────────────────────────────────
    try:
        # Get non-colliding sequence from DB (day-scoped, survives restarts)
        seq = st.session_state.db.next_sequence()
        quote_ref = generate_quote_ref(sequence=seq)
        result = st.session_state.calculator.calculate(inputs, quote_ref=quote_ref)
    except Exception as e:
        st.error(f"❌ Calculation error: {str(e)}")
        st.stop()

    try:
        st.session_state.db.save_quote(result)
    except Exception as e:
        st.error(f"❌ Quote generated but could not be saved to database: {str(e)}")
        st.warning("⚠️ Your quote is displayed below but is NOT persisted. Copy the reference now.")
        # Do NOT stop — let the user at least see and download the quote

    st.session_state.last_quote = result

    # ── SUCCESS STATE ─────────────────────────────────────────────
    st.success("✅ Quote generated successfully!")
    st.divider()

    # ── QUOTE HEADER ──────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### {client_name}")
        st.markdown(f"**Product:** KK-TB-001 — Structured Tote Bag (Medium)")
    with col2:
        st.markdown(f"**Quote Ref**  \n`{result.quote_ref}`")
    with col3:
        st.markdown(f"**Generated**  \n{result.generated_at}")

    # ── MAIN PRICE BOX ────────────────────────────────────────────
    sym = result.inputs.quote_currency.symbol()
    st.markdown(f"""
    <div class="price-box">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <div style="color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;">Per Unit</div>
                <div class="price-value">{sym}{result.per_unit_quote_currency:,.2f}</div>
            </div>
            <div>
                <div style="color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;">Total Order ({result.inputs.units:,} units)</div>
                <div class="price-value">{sym}{result.total_quote_currency:,.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABS: SUMMARY | BREAKDOWN | AUDIT ─────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Summary", "🔍 Cost Breakdown", "🔐 Audit Trail"])

    # ── TAB 1: SUMMARY ────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Order Summary")
            summary_data = {
                "Quantity": f"{result.inputs.units:,} units",
                "FOB per Unit": f"${result.factory_fob_per_unit:.2f}",
                "FOB Subtotal": f"${result.factory_fob_total:,.2f}",
                "Packaging per Unit": f"${result.packaging_per_unit:.2f}",
                "Packaging Subtotal": f"${result.packaging_total:,.2f}",
                "Manufacturing Passthrough": f"${result.manufacturing_passthrough:,.2f}",
            }
            for key, val in summary_data.items():
                st.write(f"**{key}:** {val}")

        with col2:
            st.subheader("Logistics & Duties")
            logistics_data = {
                "CBM Total": f"{result.cbm_total:.3f} m³",
                "Freight Mode": result.freight_mode_display,
                "Freight Cost": f"${result.freight_total:,.2f}",
                "Duty Rate": result.duty_display,
                "Duty Amount": f"${result.duty_total:,.2f}",
                "Broker + Port": f"${result.broker_total + result.port_total:,.2f}",
                "Insurance": f"${result.insurance_total:,.2f}",
                "Logistics Subtotal": f"${result.logistics_passthrough:,.2f}",
            }
            for key, val in logistics_data.items():
                st.write(f"**{key}:** {val}")

        # ── KritiKaal Fees ────────────────────────────────────────
        st.subheader("KritiKaal Service Fees")
        fees_data = {
            "MMF (Managed Manufacturing Fee)": f"${result.mmf:,.2f}",
            "Pre-production & Compliance": f"${result.preproduction_total + result.compliance_total:,.2f}",
            "Production Management & QA": f"${result.production_management_qa:,.2f}",
            f"QUP {result.inputs.qup_tier.display()}": f"${result.qup_total:,.2f} ({result.qup_rate:.0%} of passthrough)",
            "FX Buffer": f"${result.fx_buffer_amount:,.2f} ({result.fx_buffer_rate:.0%})",
        }
        for key, val in fees_data.items():
            st.write(f"**{key}:** {val}")

        # ── LEAD TIMES ────────────────────────────────────────────
        st.subheader("Timelines")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Production", result.production_lead_time_str)
        with col2:
            st.metric("Transit", result.transit_days_str)
        with col3:
            st.metric("Total Door-to-Door", result.total_lead_time_str)

    # ── TAB 2: COST BREAKDOWN ─────────────────────────────────────
    with tab2:
        st.markdown("### Detailed Cost Breakdown")

        breakdown_data = [
            ("MANUFACTURING PASSTHROUGH", None, None),
            ("Factory FOB", result.factory_fob_total, result.factory_fob_per_unit),
            ("Packaging", result.packaging_total, result.packaging_per_unit),
            ("  ", None, None),
            ("LOGISTICS & CUSTOMS", None, None),
            ("Freight", result.freight_total, result.freight_total / result.inputs.units),
            (f"Duty ({result.duty_display})", result.duty_total, result.duty_total / result.inputs.units),
            ("Broker Fee", result.broker_total, result.broker_total / result.inputs.units),
            ("Port Handling", result.port_total, result.port_total / result.inputs.units),
            ("Marine Insurance", result.insurance_total, result.insurance_total / result.inputs.units),
            ("  ", None, None),
            ("KRITIKAAL SERVICES", None, None),
            ("Production Management & QA", result.production_management_qa, result.production_management_qa / result.inputs.units),
            (f"Quality Underwriting Premium (QUP)", result.qup_total, result.qup_total / result.inputs.units),
            ("FX Buffer", result.fx_buffer_amount, result.fx_buffer_amount / result.inputs.units),
            ("  ", None, None),
            ("TOTALS", None, None),
        ]

        # ── Build table HTML ──────────────────────────────────────
        table_html = '<table class="cost-table" style="width: 100%; border-collapse: collapse;">'
        for desc, total, unit in breakdown_data:
            if total is None:
                if desc == "TOTALS":
                    table_html += f'<tr style="border-top: 2px solid #1A2942; font-weight: bold;"><td colspan="3"></td></tr>'
                    table_html += f'<tr><td><strong>{desc}</strong></td><td style="text-align: right;"><strong>{sym}{result.total_quote_currency:,.2f}</strong></td><td style="text-align: right;"><strong>{sym}{result.per_unit_quote_currency:,.2f}</strong></td></tr>'
                else:
                    table_html += f'<tr style="background: #F5F5F5;"><td colspan="3"><strong>{desc}</strong></td></tr>'
            else:
                table_html += f'<tr><td>{desc}</td><td style="text-align: right;">{sym}{total:,.2f}</td><td style="text-align: right;">{sym}{unit:,.2f}</td></tr>'

        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

    # ── TAB 3: AUDIT TRAIL ────────────────────────────────────────
    with tab3:
        st.markdown("### Configuration & Audit Information")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Quote Metadata**")
            st.write(f"Ref: `{result.quote_ref}`")
            st.write(f"Generated: {result.generated_at}")
            st.write(f"Client: {result.inputs.client_name}")

        with col2:
            st.markdown("**Configuration Version**")
            st.markdown(f'<div class="config-badge">{result.config_version}</div>', unsafe_allow_html=True)
            st.caption("MD5 hash of rates_config.yaml — ensures rate consistency")

        st.divider()

        # ── Input parameters ──────────────────────────────────────
        st.markdown("**Input Parameters (Immutable Record)**")
        inputs_json = json.dumps({
            "client_name": result.inputs.client_name,
            "product_ref": result.inputs.product_ref,
            "units": result.inputs.units,
            "factory_fob_usd": result.inputs.factory_fob_usd,
            "destination": result.inputs.destination.value,
            "order_type": result.inputs.order_type.value,
            "sample_costs_usd": result.inputs.sample_costs_usd,
            "qup_tier": result.inputs.qup_tier.value,
            "rex_certified": result.inputs.rex_certified,
            "freight_mode": result.inputs.freight_mode.value,
            "quote_currency": result.inputs.quote_currency.value,
            "packaging_type": result.inputs.packaging_type.value,
            "output_format": result.inputs.output_format.value,
            "fx_rate_override": result.inputs.fx_rate_override,
        }, indent=2)
        st.code(inputs_json, language="json")

        # ── Gross profit info ─────────────────────────────────────
        st.divider()
        st.markdown("**Gross Profit Analysis (Internal Only)**")
        st.write(f"KritiKaal Gross Margin: ${result.kritikaal_gross_margin_usd:,.2f}")
        st.write(f"GP%: **{result.gp_pct:.1%}**")

        # ── GP Status Alert ───────────────────────────────────────
        gp_alert_class = {
            "on_target": "alert-on-target",
            "amber": "alert-amber",
            "below_target": "alert-red",
        }.get(result.gp_status, "")

        st.markdown(f'<div class="{gp_alert_class}" style="padding: 1rem; border-radius: 4px; margin: 1rem 0;">{result.gp_alert}</div>', unsafe_allow_html=True)

        if result.gp_recommendation:
            st.info(f"💡 **Recommendation:** {result.gp_recommendation}")

    # ── DOWNLOAD DOCX ────────────────────────────────────────────
    st.divider()
    st.subheader("📥 Export Quote")

    try:
        generator = QuoteDocxGenerator()
        docx_bytes = generator.generate(result)

        st.download_button(
            label=f"💾 Download Quote ({result.quote_ref}).docx",
            data=docx_bytes,
            file_name=f"{result.quote_ref}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.caption(f"DOCX file size: {len(docx_bytes) / 1024:.1f} KB")

    except Exception as e:
        st.error(f"❌ DOCX generation failed: {str(e)}")

else:
    # ── IDLE STATE (before first quote) ───────────────────────────
    st.info(
        "👈 **Fill in the sidebar** and click **Generate Quote** to create a new quote. "
        "All calculations are driven by rates_config.yaml — change rates there, not in code."
    )

    # ── Live stats from DB ────────────────────────────────────────
    try:
        s = st.session_state.db.stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Quotes", s.get("total_quotes", 0))
        with col2:
            total_usd = s.get("total_usd_quoted", 0)
            st.metric("Total Quoted (USD)", f"${total_usd:,.0f}")
        with col3:
            avg_gp = s.get("avg_gp_pct", 0)
            st.metric("Avg GP%", f"{avg_gp:.1%}")
        with col4:
            config_ver = st.session_state.calculator.config_version if "calculator" in st.session_state else "—"
            st.metric("Config Version", config_ver)
    except Exception:
        pass  # DB not ready yet — silent fail on idle screen

    # ── Recent quotes preview ─────────────────────────────────────
    st.subheader("Recent Quotes")
    try:
        rows = st.session_state.db.all_quotes(limit=10)
        if rows:
            import pandas as pd
            df = pd.DataFrame([dict(r) for r in rows])
            display_cols = ["quote_ref", "created_at", "client_name", "destination",
                            "units", "total_usd", "quote_currency",
                            "total_quote_currency", "gp_pct", "gp_status", "status"]
            df = df[[c for c in display_cols if c in df.columns]]
            df["gp_pct"] = df["gp_pct"].apply(lambda x: f"{x:.1%}")
            df["total_usd"] = df["total_usd"].apply(lambda x: f"${x:,.2f}")
            df["total_quote_currency"] = df["total_quote_currency"].apply(lambda x: f"{x:,.2f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("No quotes generated yet. Your first quote will appear here.")
    except Exception as e:
        st.caption(f"Quote history unavailable: {e}")


# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
---
**KritiKaal Quote Engine v3.0** — Sprint 3 (Streamlit UI)
*Configuration-driven pricing. Zero hardcoded rates. Full audit trail.*

📧 Contact: Yossi Daniel | 🔐 Proprietary System
""")
