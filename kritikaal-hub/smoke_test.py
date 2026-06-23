"""
KritiKaal Command Center — Hub Smoke Test
Run: python smoke_test.py  (from kritikaal-hub/)
"""
import sys
from pathlib import Path

HERE      = Path(__file__).parent.resolve()
WORKSPACE = HERE.parent
QUOTE_ENG = WORKSPACE / "the-system-v8" / "the-system-v8" / "T-tools" / "quote-engine"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WORKSPACE / "T-tools"))
sys.path.insert(0, str(QUOTE_ENG))

print("\n" + "="*60)
print("  KritiKaal Command Center — Hub Smoke Test")
print("="*60)

# ── Test 1: shared/nav.py resolves both DBs ───────────────────────
from shared.nav import LEADS_DB, QUOTES_DB, hub_metrics  # noqa

print(f"\n  Leads DB  : {'EXISTS' if LEADS_DB.exists() else 'MISSING'}")
print(f"             {LEADS_DB}")
print(f"  Quotes DB : {'EXISTS' if QUOTES_DB.exists() else 'MISSING'}")
print(f"             {QUOTES_DB}")
assert LEADS_DB.exists(),  f"MISSING: {LEADS_DB}"
assert QUOTES_DB.exists(), f"MISSING: {QUOTES_DB}"

# ── Test 2: hub_metrics pulls from both DBs ───────────────────────
m = hub_metrics()
print(f"\n  Qualified leads : {m['qualified_leads']} (of {m['total_leads']} total)")
print(f"  Quotes total    : {m['quotes_total']}")
print(f"  Pipeline USD    : ${m['pipeline_usd']:,.2f}")
print(f"  Avg GP          : {m['avg_gp_pct']:.1%}")
assert m["qualified_leads"] > 0, "Expected qualified leads in DB"

# ── Test 3: Quote Engine imports clean from hub context ───────────
from engine import (   # noqa
    QuoteCalculator, QuoteInputs, generate_quote_ref,
    Destination, OrderType, QUPTier, FreightMode,
    QuoteCurrency, PackagingType, OutputFormat,
)
from db import QuoteDB, DB_PATH  # noqa
print("\n  Quote Engine imports : OK")

# ── Test 4: Calculator loads with correct config ──────────────────
calc = QuoteCalculator(
    config_path =QUOTE_ENG / "rates_config.yaml",
    product_path=QUOTE_ENG / "products" / "KK-TB-001.yaml",
)
print(f"  Calculator loaded    : config={calc.config_version}")

# ── Test 5: Bridge DB (QuoteDB) initialises ───────────────────────
db = QuoteDB(QUOTES_DB)
seq = db.next_sequence()
print(f"  Quote DB next_seq    : {seq}")

# ── Test 6: Bridge can read leads from leads.db ───────────────────
import sqlite3  # noqa
with sqlite3.connect(str(LEADS_DB)) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT COUNT(*) as c FROM leads WHERE status IN ('QUALIFIED_A','QUALIFIED_B_PENDING_VERIFY')"
    ).fetchone()
    print(f"  Qualified leads (direct query) : {rows['c']}")

print()
print("="*60)
print("  HUB SMOKE TEST PASSED — Command Center ready to launch")
print("="*60)
print()
print("  Launch command:")
print("  streamlit run kritikaal_app.py")
print()
