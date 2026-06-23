"""
KritiKaal Command Center — Lead → Quote Bridge
===============================================
Connects the two systems:
  1. Reads QUALIFIED leads from leads.db
  2. Pre-populates the Quote Engine with the selected lead's data
  3. On quote generation: saves to quotes.db AND logs a note in leads.db
  4. Displays all existing quotes linked to each lead

Concurrency: leads.db is opened READ-ONLY for the table view.
             The note-write is a short single-row INSERT (WAL-safe).
             quotes.db is written via QuoteDB — same as the Quote Engine page.
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────────────
# PATH BOOTSTRAP
# ─────────────────────────────────────────────────────────────────
HERE         = Path(__file__).parent.resolve()
HUB          = HERE.parent
WORKSPACE    = HUB.parent
LEADS_HUNTER = WORKSPACE / "T-tools"
QUOTE_ENGINE = (
    WORKSPACE
    / "the-system-v8"
    / "the-system-v8"
    / "T-tools"
    / "quote-engine"
)
LEADS_DB  = LEADS_HUNTER / "leads.db"
QUOTES_DB = QUOTE_ENGINE  / "quotes.db"

for p in [str(QUOTE_ENGINE), str(LEADS_HUNTER), str(HUB)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─────────────────────────────────────────────────────────────────
# IMPORTS FROM BOTH SYSTEMS
# ─────────────────────────────────────────────────────────────────
from engine import (  # noqa: E402
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
from output import QuoteDocxGenerator  # noqa: E402
from db import QuoteDB, DB_PATH        # noqa: E402

CONFIG_PATH                  = QUOTE_ENGINE / "rates_config.yaml"
CORPORATE_GIFTS_PRODUCTS_DIR = HUB / "corporate_gifts" / "products"


# ─────────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────────

def _leads_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(LEADS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")   # read-only guard for lead queries
    return conn


def _get_qualified_leads() -> list[dict]:
    """Return all QUALIFIED_A and QUALIFIED_B leads with their linked quotes."""
    with sqlite3.connect(str(LEADS_DB)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        rows = conn.execute("""
            SELECT
                l.id,
                l.entity_name,
                l.domain,
                COALESCE(l.whatsapp, '—') AS whatsapp,
                l.status,
                l.last_verified_at,
                (
                    SELECT note_text
                    FROM   lead_notes
                    WHERE  lead_id = l.id
                      AND  note_text LIKE 'Quote KK-%'
                    ORDER  BY created_at DESC
                    LIMIT  1
                ) AS last_quote_note
            FROM leads l
            WHERE l.status IN ('QUALIFIED_A', 'QUALIFIED_B_PENDING_VERIFY')
              AND l.is_stale = 0
            ORDER BY l.status ASC, l.entity_name ASC
        """).fetchall()
    return [dict(r) for r in rows]


def _write_lead_note(lead_id: int, note_text: str) -> None:
    """
    Append a note to leads.db.lead_notes.
    Short single-row INSERT — WAL-safe under concurrent scraper writes.
    """
    with sqlite3.connect(str(LEADS_DB)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "INSERT INTO lead_notes (lead_id, note_text) VALUES (?, ?)",
            (lead_id, note_text),
        )


def _get_lead_quote_history(lead_id: int) -> list[str]:
    """Return all quote notes for a given lead (newest first)."""
    with sqlite3.connect(str(LEADS_DB)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT note_text, created_at
            FROM   lead_notes
            WHERE  lead_id = ?
              AND  note_text LIKE 'Quote KK-%'
            ORDER  BY created_at DESC
        """, (lead_id,)).fetchall()
    return [dict(r) for r in rows]


def _discover_products() -> dict[str, tuple[str, Path]]:
    """
    Scan both catalogs and return {display_label: (product_ref, product_path)}.
    Corporate Gifts [CG] products listed first, Managed Manufacturing [MM] after.
    CG products live in  kritikaal-hub/corporate_gifts/products/
    MM products stay in  quote-engine/products/  (never mixed with CG files)
    """
    products: dict[str, tuple[str, Path]] = {}

    # ── Corporate Gifts catalog ───────────────────────────────────
    if CORPORATE_GIFTS_PRODUCTS_DIR.exists():
        for path in sorted(CORPORATE_GIFTS_PRODUCTS_DIR.glob("KK-CG-*.yaml")):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                ref  = data.get("reference", path.stem)
                name = data.get("name", path.stem)
                products[f"[CG] {ref} — {name}"] = (ref, path)
            except Exception:
                products[f"[CG] {path.stem}"] = (path.stem, path)

    # ── Managed Manufacturing catalog (kept separate) ─────────────
    mm_path = QUOTE_ENGINE / "products" / "KK-TB-001.yaml"
    if mm_path.exists():
        try:
            with open(mm_path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            ref  = data.get("reference", "KK-TB-001")
            name = data.get("name", "KK-TB-001")
            products[f"[MM] {ref} — {name}"] = (ref, mm_path)
        except Exception:
            products["[MM] KK-TB-001"] = ("KK-TB-001", mm_path)

    return products


# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
# Product tracking — calc is initialised dynamically in Step 2 once a product is chosen
if "bridge_product_label" not in st.session_state:
    st.session_state.bridge_product_label = None
if "bridge_product_ref" not in st.session_state:
    st.session_state.bridge_product_ref = None
if "bridge_calc" not in st.session_state:
    st.session_state.bridge_calc = None

if "bridge_db" not in st.session_state:
    try:
        st.session_state.bridge_db = QuoteDB(QUOTES_DB)
    except Exception as e:
        st.error(f"❌ Failed to open Quotes DB: {e}")
        st.stop()

if "bridge_result" not in st.session_state:
    st.session_state.bridge_result = None

if "bridge_lead_id" not in st.session_state:
    st.session_state.bridge_lead_id = None


# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown("## 🔗 Lead → Quote Bridge")
st.caption(
    "Select a qualified lead, configure the quote, and generate it. "
    "The quote reference is automatically logged against the lead record."
)
st.divider()


# ─────────────────────────────────────────────────────────────────
# STEP 1 — SELECT A QUALIFIED LEAD
# ─────────────────────────────────────────────────────────────────
st.markdown("### Step 1 — Select a Qualified Lead")

try:
    leads = _get_qualified_leads()
except Exception as e:
    st.error(f"❌ Cannot read leads database: {e}")
    st.info(f"Expected at: `{LEADS_DB}`")
    st.stop()

if not leads:
    st.warning("No qualified leads found (QUALIFIED_A or QUALIFIED_B_PENDING_VERIFY, non-stale).")
    st.stop()

# ── Search & filter controls ──────────────────────────────────────
col_search, col_filter = st.columns([3, 1])
with col_search:
    search_term = st.text_input(
        "Search by name or domain",
        placeholder="e.g. leather, bags, tel aviv...",
        label_visibility="collapsed",
    )
with col_filter:
    status_filter = st.selectbox(
        "Status",
        options=["All Qualified", "QUALIFIED_A only"],
        label_visibility="collapsed",
    )

# ── Apply filters ─────────────────────────────────────────────────
filtered = leads
if search_term:
    s = search_term.lower()
    filtered = [
        l for l in filtered
        if s in l["entity_name"].lower() or s in l["domain"].lower()
    ]
if status_filter == "QUALIFIED_A only":
    filtered = [l for l in filtered if l["status"] == "QUALIFIED_A"]

st.caption(f"Showing {len(filtered)} of {len(leads)} qualified leads")

# ── Build display dataframe ───────────────────────────────────────
import pandas as pd  # noqa: E402

STATUS_BADGE = {
    "QUALIFIED_A":               "⭐ A",
    "QUALIFIED_B_PENDING_VERIFY": "🔵 B",
}

df = pd.DataFrame([
    {
        "Entity Name":   r["entity_name"],
        "Domain":        r["domain"],
        "WhatsApp":      r["whatsapp"][:6] + "••••" if r["whatsapp"] != "—" else "—",
        "Status":        STATUS_BADGE.get(r["status"], r["status"]),
        "Last Verified": r["last_verified_at"][:10] if r["last_verified_at"] else "—",
        "Quoted?":       "✅ " + r["last_quote_note"][:30] + "…"
                         if r["last_quote_note"] else "—",
    }
    for r in filtered
])

event = st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun",
    key="bridge_lead_table",
)

# ── Resolve selected lead ─────────────────────────────────────────
selected_lead = None
if event.selection and event.selection.rows:
    idx = event.selection.rows[0]
    if idx < len(filtered):
        selected_lead = filtered[idx]


# ─────────────────────────────────────────────────────────────────
# STEP 2 — QUOTE CONFIGURATION  (only shown after lead selected)
# ─────────────────────────────────────────────────────────────────
if selected_lead is None:
    st.info("👆 Click a row above to select a lead and open the quote form.")
    st.stop()

st.divider()
st.markdown(f"### Step 2 — Configure Quote for **{selected_lead['entity_name']}**")

# Show existing quote history for this lead
history = _get_lead_quote_history(selected_lead["id"])
if history:
    with st.expander(f"📋 Quote History ({len(history)} previous quotes)", expanded=False):
        for h in history:
            st.markdown(f"- `{h['created_at'][:16]}` — {h['note_text']}")

# ── Product selector ─────────────────────────────────────────────
st.markdown("#### Product")
_all_products   = _discover_products()
_product_labels = list(_all_products.keys())

if not _product_labels:
    st.error("❌ No product files found. Check `corporate_gifts/products/` and `quote-engine/products/`.")
    st.stop()

# Default to first CG product on first load
if st.session_state.bridge_product_label not in _product_labels:
    st.session_state.bridge_product_label = _product_labels[0]

selected_product_label = st.selectbox(
    "Select Product",
    options=_product_labels,
    index=_product_labels.index(st.session_state.bridge_product_label),
    help=(
        "**[CG]** Corporate Gifts products → `kritikaal-hub/corporate_gifts/products/`  "
        "**[MM]** Managed Manufacturing products → `quote-engine/products/`"
    ),
    key="bridge_product_selector",
)

# Reinitialise calculator whenever product changes or on first load
if (
    selected_product_label != st.session_state.bridge_product_label
    or st.session_state.bridge_calc is None
):
    _ref, _path = _all_products[selected_product_label]
    try:
        st.session_state.bridge_calc          = QuoteCalculator(config_path=CONFIG_PATH, product_path=_path)
        st.session_state.bridge_product_label = selected_product_label
        st.session_state.bridge_product_ref   = _ref
        # Clear any cached result from a different product
        st.session_state.bridge_result        = None
    except Exception as e:
        st.error(f"❌ Failed to load calculator for **{selected_product_label}**: {e}")
        st.stop()

# FOB guidance hint + smart default from the product YAML
_prod_pricing = st.session_state.bridge_calc.product.get("pricing_guidance", {})
_fob_tiers    = _prod_pricing.get("calculator_fob_reference_usd", {})
_fob_bespoke  = _prod_pricing.get("factory_fob_sanity_ranges_usd", {})
if _fob_tiers:
    _fob_default = float(list(_fob_tiers.values())[0])
    _fob_hint    = " | ".join(f"{k}: ${v}" for k, v in _fob_tiers.items())
    st.caption(f"📋 FOB reference (from product spec): {_fob_hint}")
elif _fob_bespoke:
    _fob_default = 35.0
    _fob_hint    = " | ".join(f"{k}: {v}" for k, v in _fob_bespoke.items())
    st.caption(f"📋 FOB sanity range (bespoke — get factory quote first): {_fob_hint}")
else:
    _fob_default = 38.50

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    client_name = st.text_input(
        "Client Name",
        value=selected_lead["entity_name"],
        help="Pre-filled from lead record — edit if needed",
    )
    units = st.number_input(
        "Order Quantity (units)",
        min_value=50, max_value=50000, value=100, step=50,
    )
    fob_usd = st.number_input(
        "Factory FOB per Unit ($)",
        min_value=0.01,
        value=_fob_default,
        step=1.00,
        format="%.2f",
        key=f"bridge_fob_{st.session_state.bridge_product_ref}",
        help="Auto-filled from product spec. Update to your confirmed factory quote.",
    )
    order_type = st.selectbox(
        "Order Type",
        options=[OrderType.FIRST_STYLE_FACTORY, OrderType.REORDER_SAME_STYLE, OrderType.NEW_STYLE_EXISTING_FACTORY],
        format_func=lambda x: x.display(),
    )

with col_right:
    # Destination defaults to ISRAEL (Leads Hunter is Israel-focused)
    destination = st.selectbox(
        "Destination",
        options=[Destination.ISRAEL, Destination.UK, Destination.EU],
        index=0,
        help="Defaults to Israel — change if client ships elsewhere",
    )
    rex_certified = st.checkbox("REX Certified", value=False)
    if destination == Destination.ISRAEL and rex_certified:
        st.caption("ℹ️ REX has no effect for Israel (no India-Israel FTA)")

    qup_tier = st.selectbox(
        "QUP Tier",
        options=[QUPTier.STANDARD, QUPTier.BASIC, QUPTier.MAXIMUM],
        format_func=lambda x: x.display(),
    )
    sample_costs = st.number_input(
        "Sample Costs Paid ($)",
        min_value=0.0, value=350.0, step=50.0, format="%.2f",
    )

# ── Currency row ──────────────────────────────────────────────────
col_cur, col_fx, col_pkg, col_fmt = st.columns(4)
with col_cur:
    # For Israeli clients default to ILS or USD
    quote_currency = st.selectbox(
        "Quote Currency",
        options=[QuoteCurrency.ILS, QuoteCurrency.USD, QuoteCurrency.GBP, QuoteCurrency.EUR],
    )
with col_fx:
    fx_defaults = {
        QuoteCurrency.USD: 1.0, QuoteCurrency.GBP: 0.79,
        QuoteCurrency.ILS: 3.70, QuoteCurrency.EUR: 0.92,
    }
    fx_rate = st.number_input(
        f"Rate (1 USD → {quote_currency.value})",
        min_value=0.001,
        value=float(fx_defaults.get(quote_currency, 1.0)),
        step=0.01, format="%.4f",
    )
with col_pkg:
    packaging_type = st.selectbox(
        "Packaging",
        options=[PackagingType.STANDARD, PackagingType.BRANDED],
        format_func=lambda x: x.display(),
    )
with col_fmt:
    output_format = st.selectbox(
        "Output Format",
        options=[OutputFormat.FULL_UNBUNDLED, OutputFormat.BOTTOM_LINE],
        format_func=lambda x: {
            OutputFormat.FULL_UNBUNDLED: "Full Breakdown",
            OutputFormat.BOTTOM_LINE:    "Bottom-Line Only",
        }[x],
    )

# ── Generate button ───────────────────────────────────────────────
st.divider()
generate_btn = st.button(
    f"⚡ Generate Quote for {selected_lead['entity_name']}",
    type="primary",
    use_container_width=True,
)


# ─────────────────────────────────────────────────────────────────
# STEP 3 — GENERATE, PERSIST, LINK
# ─────────────────────────────────────────────────────────────────
if generate_btn:
    # ── Build inputs ──────────────────────────────────────────────
    try:
        inputs = QuoteInputs(
            client_name     = client_name.strip() or selected_lead["entity_name"],
            product_ref     = st.session_state.bridge_product_ref,
            factory_fob_usd = fob_usd,
            units           = int(units),
            destination     = destination,
            order_type      = order_type,
            sample_costs_usd= sample_costs,
            qup_tier        = qup_tier,
            rex_certified   = rex_certified,
            freight_mode    = FreightMode.AUTO,
            quote_currency  = quote_currency,
            packaging_type  = packaging_type,
            output_format   = output_format,
            fx_rate_override= fx_rate if quote_currency != QuoteCurrency.USD else None,
        )
    except Exception as e:
        st.error(f"❌ Input error: {e}")
        st.stop()

    # ── Validate ──────────────────────────────────────────────────
    errors = st.session_state.bridge_calc.validate(inputs)
    if errors:
        st.error("❌ Validation failed:")
        for e in errors:
            st.write(f"  • {e}")
        st.stop()

    # ── Calculate ─────────────────────────────────────────────────
    try:
        seq       = st.session_state.bridge_db.next_sequence()
        quote_ref = generate_quote_ref(sequence=seq)
        result    = st.session_state.bridge_calc.calculate(inputs, quote_ref=quote_ref)
    except Exception as e:
        st.error(f"❌ Calculation error: {e}")
        st.stop()

    # ── Save to quotes.db ─────────────────────────────────────────
    db_save_ok = True
    try:
        st.session_state.bridge_db.save_quote(result)
    except Exception as e:
        st.warning(f"⚠️ Quote calculated but not persisted to quotes.db: {e}")
        db_save_ok = False

    # ── Write bidirectional note to leads.db ─────────────────────
    sym       = result.inputs.quote_currency.symbol()
    note_text = (
        f"Quote {result.quote_ref} generated — "
        f"{sym}{result.total_quote_currency:,.2f} "
        f"| GP {result.gp_pct:.1%} "
        f"| {result.generated_at}"
    )
    lead_note_ok = True
    try:
        _write_lead_note(selected_lead["id"], note_text)
    except Exception as e:
        st.warning(f"⚠️ Could not log note to lead record: {e}")
        lead_note_ok = False

    # ── Store result in session state for display ─────────────────
    st.session_state.bridge_result  = result
    st.session_state.bridge_lead_id = selected_lead["id"]
    st.rerun()


# ─────────────────────────────────────────────────────────────────
# RESULT DISPLAY  (shown after successful generation)
# ─────────────────────────────────────────────────────────────────
if st.session_state.bridge_result is not None:
    result = st.session_state.bridge_result
    sym    = result.inputs.quote_currency.symbol()

    st.divider()
    st.markdown("### Step 3 — Quote Result")

    # ── Status badges ─────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.success(f"✅ Quote `{result.quote_ref}` generated and saved")
    with col_b:
        if st.session_state.bridge_lead_id == selected_lead["id"]:
            st.success("✅ Note logged to lead record")
        else:
            st.info("ℹ️ Select the same lead to see the linked note")

    # ── Price box ─────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Per Unit", f"{sym}{result.per_unit_quote_currency:,.2f}")
    with m2:
        st.metric(f"Total ({result.inputs.units:,} units)", f"{sym}{result.total_quote_currency:,.2f}")
    with m3:
        gp_color = "normal" if result.gp_status == "on_target" else "inverse"
        st.metric("GP%", f"{result.gp_pct:.1%}", delta=result.gp_status.replace("_", " "))
    with m4:
        st.metric("Freight Mode", result.freight_mode_display)

    # ── GP alert ──────────────────────────────────────────────────
    gp_bg = {"on_target": "#E8F5E9", "amber": "#FFF3E0", "below_target": "#FFEBEE"}
    gp_border = {"on_target": "#388E3C", "amber": "#F57C00", "below_target": "#D32F2F"}
    st.markdown(
        f'<div style="background:{gp_bg.get(result.gp_status,"#fff")};'
        f'border-left:4px solid {gp_border.get(result.gp_status,"#999")};'
        f'padding:.75rem 1rem;border-radius:4px;margin:.5rem 0">'
        f'{result.gp_alert}</div>',
        unsafe_allow_html=True,
    )
    if result.gp_recommendation:
        st.info(f"💡 {result.gp_recommendation}")

    # ── Lead timelines ────────────────────────────────────────────
    with st.expander("📅 Lead Times", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Production", result.production_lead_time_str)
        c2.metric("Transit",    result.transit_days_str)
        c3.metric("Door-to-Door", result.total_lead_time_str)

    # ── WhatsApp quick-link (if lead has WhatsApp) ────────────────
    if selected_lead.get("whatsapp") and selected_lead["whatsapp"] != "—":
        wa_num = selected_lead["whatsapp"]
        wa_msg = (
            f"Hello, I wanted to share a quote for your review: "
            f"{result.quote_ref} — "
            f"{sym}{result.per_unit_quote_currency:,.2f}/unit "
            f"({result.inputs.units:,} units). "
            f"Valid 14 days. Let me know if you'd like to discuss."
        )
        from urllib.parse import quote as url_quote
        wa_link = f"https://wa.me/{wa_num}?text={url_quote(wa_msg)}"
        st.link_button(
            f"💬 Open WhatsApp → {wa_num[:6]}••••",
            url=wa_link,
            use_container_width=False,
        )

    # ── DOCX download ─────────────────────────────────────────────
    try:
        generator  = QuoteDocxGenerator()
        docx_bytes = generator.generate(result)
        st.download_button(
            label=f"💾 Download {result.quote_ref}.docx",
            data=docx_bytes,
            file_name=f"{result.quote_ref}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.caption(f"File size: {len(docx_bytes)/1024:.1f} KB | Config: `{result.config_version}`")
    except Exception as e:
        st.error(f"❌ DOCX generation failed: {e}")

    # ── Clear result button ────────────────────────────────────────
    if st.button("🔄 Start New Quote", use_container_width=False):
        st.session_state.bridge_result  = None
        st.session_state.bridge_lead_id = None
        st.rerun()
