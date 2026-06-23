"""
KritiKaal Quote Engine — DB Persistence Smoke Test
Run from quote-engine/:  python test_db.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(HERE))

from engine import (
    QuoteCalculator, QuoteInputs, generate_quote_ref,
    Destination, OrderType, QUPTier, FreightMode,
    QuoteCurrency, PackagingType, OutputFormat,
)
from db import QuoteDB, DB_PATH

print("\n" + "="*60)
print("  KritiKaal Quote Engine — DB Persistence Test")
print("="*60)

# ── 1. Initialise DB ─────────────────────────────────────────────
db = QuoteDB(DB_PATH)
print(f"  DB path   : {DB_PATH}")
print(f"  DB exists : {DB_PATH.exists()}")

# ── 2. Check sequence before save ────────────────────────────────
seq = db.next_sequence()
print(f"  Sequence before save : {seq}")

# ── 3. Calculate a quote ─────────────────────────────────────────
calc = QuoteCalculator(
    config_path=HERE / "rates_config.yaml",
    product_path=HERE / "products" / "KK-TB-001.yaml",
)
inputs = QuoteInputs(
    client_name="Persistence Test Client",
    product_ref="KK-TB-001",
    factory_fob_usd=38.50,
    units=100,
    destination=Destination.UK,
    order_type=OrderType.FIRST_STYLE_FACTORY,
    sample_costs_usd=350.00,
    qup_tier=QUPTier.STANDARD,
    rex_certified=False,
    freight_mode=FreightMode.AUTO,
    quote_currency=QuoteCurrency.GBP,
    packaging_type=PackagingType.STANDARD,
    output_format=OutputFormat.FULL_UNBUNDLED,
    fx_rate_override=0.79,
)
ref    = generate_quote_ref(sequence=seq)
result = calc.calculate(inputs, quote_ref=ref)
print(f"  Quote ref : {result.quote_ref}")
print(f"  Total GBP : £{result.total_quote_currency:,.2f}")

# ── 4. Save to DB ────────────────────────────────────────────────
db.save_quote(result)
print("  Save      : OK")

# ── 5. Verify sequence incremented ───────────────────────────────
seq_after = db.next_sequence()
expected  = seq + 1
status    = "OK" if seq_after == expected else f"FAIL (got {seq_after}, expected {expected})"
print(f"  Sequence after save  : {seq_after}  → {status}")

# ── 6. Retrieve and verify ───────────────────────────────────────
row = db.get_by_ref(ref)
assert row is not None, f"Quote {ref} not found in DB!"
print(f"  Retrieved : {row['quote_ref']} | {row['client_name']} | status={row['status']}")

# ── 7. Status update ─────────────────────────────────────────────
updated = db.update_status(ref, "accepted")
assert updated, "update_status() returned False — row not found"
row2 = db.get_by_ref(ref)
assert row2["status"] == "accepted", f"Status not updated: {row2['status']}"
print(f"  Status updated to 'accepted' : OK")

# ── 8. Stats ─────────────────────────────────────────────────────
s = db.stats()
print(f"  DB total quotes      : {s['total_quotes']}")
print(f"  DB total USD quoted  : ${s['total_usd_quoted']:,.2f}")
print(f"  DB accepted count    : {s['accepted_count']}")

# ── Clean up test row ─────────────────────────────────────────────
import sqlite3
conn = sqlite3.connect(DB_PATH)
conn.execute("DELETE FROM quotes WHERE client_name = 'Persistence Test Client'")
conn.commit()
conn.close()
print("  Cleaned up test row  : OK")

print()
print("="*60)
print("  DB PERSISTENCE TEST PASSED")
print("="*60 + "\n")
