---
name: revenue-roadmap-skill
description: Model KritiKaal's path to $1M gross profit. Use when evaluating deal structures, pricing decisions, client acquisition targets, or any financial projection. Always models PROFIT, not revenue.
---

# Revenue Roadmap Skill — KritiKaal

**CRITICAL:** KritiKaal's financial goal is $1,000,000 in GROSS PROFIT per year. Not revenue. Not ARR. Not GMV. PROFIT. All models in this skill work backward from that number.

---

## The Corrected Financial Foundation

| Metric | Value | Source |
|--------|-------|--------|
| Annual Profit Target | $1,000,000 GP | Confirmed by Yossi, 2026-04-17 |
| Average deal size (AOV) | $5,000 (per-transaction baseline) | Confirmed by Yossi, 2026-04-17 |
| Current gross margin | ~22% | Sprint 01 unit economics (Trimurthi model) |
| Revenue implied at 22% margin | ~$4.54M | Calculated |
| Orders required at $5K AOV | ~909/year (~76/month) | Calculated |

**The gap:** 909 orders/year at $5K AOV is a very high acquisition burden. The model must grow AOV, margin, or both. See paths below.

---

## The Three Levers

Every financial projection for KritiKaal manipulates three variables:

```
Gross Profit = Orders/Year × AOV × Gross Margin %
```

### Lever 1: Order Volume
More transactions per year. Requires more active clients or higher reorder frequency per client.

### Lever 2: Average Order Value (AOV)
Larger deals per transaction. Requires upmarket clients, broader SKU coverage per order, or premium tier pricing.

### Lever 3: Gross Margin %
More retained per dollar billed. Requires premium positioning (higher price), lower factory cost (better supplier terms), or reduced overhead per deal.

---

## Profit Path Matrix

Use this table when evaluating any strategic option. Find the scenario closest to the opportunity being analyzed.

| Scenario | AOV | Margin | Revenue Needed | Orders/Year | Active Clients (6×/yr reorder) |
|----------|-----|--------|----------------|-------------|-------------------------------|
| Floor (current baseline) | $5K | 22% | $4.54M | 909 | 152 |
| AOV uplift only | $10K | 22% | $4.54M | 454 | 76 |
| Margin uplift only | $5K | 35% | $2.86M | 571 | 95 |
| Combined mid | $10K | 30% | $3.33M | 333 | 56 |
| Optimized state | $15K | 35% | $2.86M | 191 | 32 |
| Ideal state | $20K | 40% | $2.5M | 125 | 21 |

**The Strategist's default planning assumption:** Model against the "Combined Mid" scenario ($10K AOV, 30% margin) unless Yossi specifies otherwise. This requires 333 orders/year from ~56 active clients reordering 6×/year — achievable within a 3-year horizon.

---

## Client Value Tiers

Not all clients are equal. Model clients by annual deal volume (ADV = total annual spend):

| Tier | Annual Deal Volume | Orders at $5K | Orders at $10K | Clients needed for $1M profit (35% margin) |
|------|-------------------|---------------|----------------|----------------------------------------------|
| Micro | $5K–$15K | 1–3 | 1 | ~571 |
| Small | $15K–$50K | 3–10 | 2–5 | ~95 |
| Core | $50K–$150K | 10–30 | 5–15 | ~19 |
| Anchor | $150K–$500K | 30–100 | 15–50 | ~6 |

**Strategic implication:** 19 Core clients ($50K–$150K/year each) at 35% margin generates $1M GP. This is the realistic Phase 1 target profile. The Global Demand-Side Playbook must hunt for brands capable of $50K–$150K annual deal volume, not $5K one-off buyers.

---

## Deal-Level Margin Model

Use this template when evaluating any specific deal or factory partner:

```
Client invoice (AOV)                    = [X]
  Less: Manufacturing cost              = [Y]
  Less: Freight + duties                = [Z]
  Less: KritiKaal QC flat fee           = [$300–$500]
  Less: KritiKaal admin / overhead      = [estimate]
  ────────────────────────────────────
  Gross Profit per deal                 = [X - Y - Z - fees]
  Gross Margin %                        = GP / X
```

**Minimum acceptable margin:** 25% GP per deal. Below 25%, the deal does not contribute meaningfully to the $1M profit target and ties up operational capacity that could serve a better-margin client.

**Stretch target:** 35%+ GP per deal. Achievable through: (a) premium factory pricing to client, (b) volume discount from factory, (c) simplified QC (fewer inspection stages for repeat, proven factory orders).

---

## The Repeat Order Multiplier

The single most important variable in the model is **reorder frequency**. A client who orders 10×/year at $5K AOV is worth 10× a client who orders 1×/year.

| Client reorder freq | Annual revenue (at $5K AOV) | Annual GP (at 30% margin) |
|---------------------|----------------------------|---------------------------|
| 1×/year | $5,000 | $1,500 |
| 4×/year | $20,000 | $6,000 |
| 6×/year | $30,000 | $9,000 |
| 12×/year | $60,000 | $18,000 |
| 24×/year | $120,000 | $36,000 |

**Design implication:** KritiKaal's service model (fast turnaround, zero admin burden, single point of contact) must be engineered to maximize reorder frequency. Every friction that makes a client delay reordering is a direct cost to the $1M profit target.

---

## How to Use This Skill

When the Strategist is evaluating:

- **A new factory partner:** Calculate what AOV and order volume that factory can support. Does the margin hit 25%+?
- **A new client prospect:** Estimate their annual deal volume. Are they Micro/Small/Core/Anchor? What margin tier is realistic?
- **A pricing decision:** Model the margin impact. What happens to the $1M profit path if we drop price 10%?
- **A market entry decision:** How many addressable clients exist in that market? At what ADV? Does it move the needle on 333 orders/year?

---

## Integration

- Read `B-brain/00-MASTER-strategy.md` for the business model context
- Read `C-core/00-master-context.md` for Phase 1 priorities
- Log all financial projections in `M-memory/decisions.md`
- Save outputs to `O-output/[project-folder]/revenue-model.md`

---

*Every number in this system ultimately answers one question: does this move us closer to $1,000,000 in gross profit? If the answer is unclear, run the model before deciding.*
