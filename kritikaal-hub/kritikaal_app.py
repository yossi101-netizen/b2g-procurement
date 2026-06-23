"""
KritiKaal Command Center — Entry Point
=======================================
Run:  streamlit run kritikaal_app.py

This is the ONLY file that calls st.set_page_config().
All pages import from their source systems via sys.path injection.
"""
import sys
from pathlib import Path

import streamlit as st

# ── Path bootstrap — hub must be importable ───────────────────────
HERE = Path(__file__).parent.resolve()
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# ── Page config (called exactly once for the whole app) ───────────
st.set_page_config(
    page_title="KritiKaal Command Center",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Hub-wide header metrics ───────────────────────────────────────
from shared.nav import hub_metrics  # noqa: E402

m = hub_metrics()

st.markdown("""
<style>
/* Command Center top bar */
.hub-metric { text-align: center; }
.hub-metric .label  { font-size: 0.72rem; color: #888; text-transform: uppercase; letter-spacing: .05em; }
.hub-metric .value  { font-size: 1.6rem; font-weight: 700; color: #1A2942; line-height: 1.1; }
.hub-metric .subval { font-size: 0.8rem; color: #555; }
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""
    <div class="hub-metric">
        <div class="label">Qualified Leads</div>
        <div class="value">{m['qualified_leads']}</div>
        <div class="subval">of {m['total_leads']} total</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="hub-metric">
        <div class="label">Quotes This Week</div>
        <div class="value">{m['quotes_this_week']}</div>
        <div class="subval">{m['quotes_total']} all-time</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="hub-metric">
        <div class="label">Open Pipeline</div>
        <div class="value">${m['pipeline_usd']:,.0f}</div>
        <div class="subval">USD issued, not closed</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="hub-metric">
        <div class="label">Avg GP%</div>
        <div class="value">{m['avg_gp_pct']:.1%}</div>
        <div class="subval">across all quotes</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""
    <div class="hub-metric">
        <div class="label">Won</div>
        <div class="value">{m['accepted_quotes']}</div>
        <div class="subval">quotes accepted</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Page navigation ───────────────────────────────────────────────
leads_page  = st.Page("pages/1_Leads.py",  title="Lead Machine",       icon="🎯", default=True)
quotes_page = st.Page("pages/2_Quotes.py", title="Quote Engine",        icon="💼")
bridge_page = st.Page("pages/3_Bridge.py", title="Lead → Quote Bridge", icon="🔗")

pg = st.navigation(
    {"Operations": [leads_page, quotes_page, bridge_page]},
    position="sidebar",
)
pg.run()
