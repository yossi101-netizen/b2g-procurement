"""
KritiKaal Quote Engine — Sprint 1 + Sprint 2 Smoke Test
Run from the quote-engine/ directory:

    python test.py

Expected: Total GBP printed, GP% printed, test_quote.docx written.
"""
import sys
from pathlib import Path

# ── Make sure we can import from this directory ──────────────────
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


# ─────────────────────────────────────────────────────────────────
# 1. INITIALISE CALCULATOR
# ─────────────────────────────────────────────────────────────────
config_path  = HERE / "rates_config.yaml"
product_path = HERE / "products" / "KK-TB-001.yaml"

print(f"\n{'='*60}")
print("  KritiKaal Quote Engine — Smoke Test")
print(f"{'='*60}")
print(f"  Config:  {config_path}")
print(f"  Product: {product_path}\n")

assert config_path.exists(),  f"MISSING: {config_path}"
assert product_path.exists(), f"MISSING: {product_path}"

calc = QuoteCalculator(config_path=config_path, product_path=product_path)
print(f"  ✓  Calculator loaded   (config hash: {calc.config_version})")


# ─────────────────────────────────────────────────────────────────
# 2. DEFINE TEST INPUTS
#    100 units KK-TB-001 | Pioneer TA-1 → UK | FOB $38.50
#    First order, Standard QUP, GBP output, Full Unbundled DOCX
# ─────────────────────────────────────────────────────────────────
inputs = QuoteInputs(
    client_name      = "Pioneer Leathers (Test)",
    product_ref      = "KK-TB-001",
    factory_fob_usd  = 38.50,          # Pioneer TA-1 test FOB
    units            = 100,
    destination      = Destination.UK,
    order_type       = OrderType.FIRST_STYLE_FACTORY,
    sample_costs_usd = 350.00,         # Sample invoice paid
    qup_tier         = QUPTier.STANDARD,
    rex_certified    = False,          # REX not yet in place — 3.5% MFN applies
    freight_mode     = FreightMode.AUTO,
    quote_currency   = QuoteCurrency.GBP,
    packaging_type   = PackagingType.STANDARD,
    output_format    = OutputFormat.FULL_UNBUNDLED,
    fx_rate_override = 0.79,           # Live GBP/USD rate — update before real quotes
)

print(f"  ✓  Inputs defined      ({inputs.units} units @ ${inputs.factory_fob_usd}/unit FOB → {inputs.destination.value})")


# ─────────────────────────────────────────────────────────────────
# 3. VALIDATE INPUTS
# ─────────────────────────────────────────────────────────────────
errors = calc.validate(inputs)
if errors:
    print("\n  ✗  VALIDATION FAILED:")
    for e in errors:
        print(f"     - {e}")
    sys.exit(1)

print("  ✓  Validation passed")


# ─────────────────────────────────────────────────────────────────
# 4. CALCULATE
# ─────────────────────────────────────────────────────────────────
quote_ref = generate_quote_ref(sequence=1)
result    = calc.calculate(inputs, quote_ref=quote_ref)

print(f"  ✓  Calculation complete (ref: {quote_ref})\n")


# ─────────────────────────────────────────────────────────────────
# 5. PRINT RESULTS
# ─────────────────────────────────────────────────────────────────
sym = inputs.quote_currency.symbol()

print(f"{'─'*60}")
print(f"  QUOTE RESULTS — {quote_ref}")
print(f"{'─'*60}")
print(f"  Factory FOB total       ${result.factory_fob_total:>10,.2f}  (${result.factory_fob_per_unit:.2f}/unit)")
print(f"  Packaging               ${result.packaging_total:>10,.2f}  (${result.packaging_per_unit:.2f}/unit)")
print(f"  Pre-production          ${result.preproduction_total:>10,.2f}")
print(f"  Compliance docs         ${result.compliance_total:>10,.2f}")
print(f"  ─── Manufacturing ────────────────────────────────")
print(f"  Passthrough subtotal    ${result.manufacturing_passthrough:>10,.2f}")
print(f"")
print(f"  Freight ({result.freight_mode_display})")
print(f"                          ${result.freight_total:>10,.2f}")
print(f"  Duty   ({result.duty_display})")
print(f"                          ${result.duty_total:>10,.2f}")
print(f"  Broker + port           ${result.broker_total + result.port_total:>10,.2f}")
print(f"  Marine insurance        ${result.insurance_total:>10,.2f}")
print(f"  ─── Logistics ────────────────────────────────────")
print(f"  Passthrough subtotal    ${result.logistics_passthrough:>10,.2f}")
print(f"")
print(f"  ─── Total Cost Passthrough ───────────────────────")
print(f"                          ${result.total_cost_passthrough:>10,.2f}")
print(f"")
print(f"  Prod. Mgmt & QA Svcs    ${result.production_management_qa:>10,.2f}  (MMF + preproduction + compliance)")
print(f"  QUP {inputs.qup_tier.display():<20}  ${result.qup_total:>10,.2f}  ({result.qup_rate:.0%} of passthrough)")
print(f"  FX Buffer ({result.fx_buffer_rate:.0%})          ${result.fx_buffer_amount:>10,.2f}")
print(f"{'─'*60}")
print(f"  TOTAL ORDER (USD)       ${result.total_usd:>10,.2f}")
print(f"  TOTAL ORDER ({inputs.quote_currency.value})        {sym}{result.total_quote_currency:>10,.2f}  (@ {result.fx_rate_used:.4f})")
print(f"  PER UNIT   ({inputs.quote_currency.value})        {sym}{result.per_unit_quote_currency:>10,.2f}")
print(f"{'─'*60}")
print(f"")
print(f"  ── INTERNAL GP SUMMARY ───────────────────────────")
print(f"  KritiKaal gross margin  ${result.kritikaal_gross_margin_usd:>10,.2f}")
print(f"  GP %                       {result.gp_pct:>8.1%}")
print(f"  Status: {result.gp_alert}")
if result.gp_recommendation:
    print(f"  Action: {result.gp_recommendation}")
print(f"{'─'*60}")
print(f"")
print(f"  Lead time: {result.production_lead_time_str}")
print(f"  Transit:   {result.transit_days_str}")
print(f"  Total:     {result.total_lead_time_str}")
print(f"  Port:      {result.destination_port}")
print(f"{'─'*60}\n")


# ─────────────────────────────────────────────────────────────────
# 6. GENERATE DOCX (Full Unbundled — both pages)
# ─────────────────────────────────────────────────────────────────
docx_path = HERE / "test_quote.docx"

print("  Generating DOCX...")
generator  = QuoteDocxGenerator()
docx_bytes = generator.generate(result)

with open(docx_path, "wb") as f:
    f.write(docx_bytes)

size_kb = len(docx_bytes) / 1024
print(f"  ✓  DOCX written → {docx_path.name}  ({size_kb:.1f} KB)")
print(f"\n{'='*60}")
print("  SMOKE TEST PASSED — Sprint 1 + Sprint 2 operational")
print(f"{'='*60}\n")
print("  Next steps:")
print("  1. Open test_quote.docx — verify Page 1 layout and price box")
print("  2. Check Page 2 — confirm 'Production Management & QA Services' is the only services line")
print("  3. Verify GP% matches expectations for 100-unit first order")
print("  4. Run 'streamlit run app.py' when Sprint 3 is ready\n")
