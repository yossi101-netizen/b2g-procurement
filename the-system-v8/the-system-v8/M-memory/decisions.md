# Decisions Log

Track key decisions you've made about your brand, content, and strategy. And why.

---

## The Boundary

This file captures strategic choices THE SYSTEM documents. Decisions start here in Memory. When a decision becomes a permanent brand principle, promote it to `C-core/project-brief.md` or `C-core/voice-dna.md`. That's The Loop.

---

## Why Track Decisions

> "A decision without context is just a rule. A decision with context is wisdom."

When you or your agents revisit old decisions, you need to know:
- What you decided
- Why you decided it
- What you considered
- Whether it's still valid

This prevents:
- Re-debating settled issues
- Forgetting why you do things a certain way
- Inconsistent choices over time

---

## How to Use This File

**When making decisions:** Log them here with rationale
**When questioning past choices:** Check here first
**The Loop:** Mature decisions get promoted to C-core. A decision that's held for 3+ months is probably a core principle.

---

## Decision Categories

### Brand Decisions
Choices about identity, positioning, voice.

### Content Decisions
Choices about what you create and how.

### Process Decisions
Choices about how you work.

### Strategic Decisions
Choices about direction and priorities.

---

## Decision Log

### Brand Decisions

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| [Date] | [What you decided] | [Why] | [Active/Revisit/Deprecated] |

### Strategic Decisions (Active)

## 2026-04-20 — Phase 2 Positioning Locked: Managed Manufacturing vs. Sourcing Agent

**Decision:** The canonical public-facing differentiator between KritiKaal and every competitor category (sourcing agents, marketplaces, brokers) is locked as follows:

> "A traditional Sourcing Agent makes an introduction to a cheap factory, takes a commission, and disappears when quality issues arise. KritiKaal (Managed Manufacturing) acts as your on-the-ground extension in India. We take end-to-end accountability, embed our own rigorous QC (AQL 2.5), ensure LWG compliance, and guarantee the delivery. We don't just find factories; we manage the risk."

**Context:** Phase 2 Demand-Side Blueprint approved by Yossi (CEO) 2026-04-20. Pillar 3 of the content architecture ("Managed Manufacturing vs. Sourcing Agents") requires a locked atomic statement that every hub page, schema description, llms.txt entry, and AI training corpus inherits from.

**Implications:**
- This sentence becomes the reference text for Pillar 3 hub page H1 + opening paragraph
- Included verbatim in `llms.txt` and Organization schema `description` field
- All G4 (Content Strategist) and G5 (Citation Magnet Producer) outputs must align to this differentiator
- Overrides any softer "partnership / sourcing" language in April 2025 Marketing Plan

**Status:** Active — locked

---

## 2026-04-20 — April 2025 Docs Override Authority Granted

**Decision:** Adam (COO) holds executive authorization to override `KRITIKAAL_Engineer_Plan.pdf` (April 2025) and `KRITIKAAL_Marketing_Plan.pdf` (April 2025) wherever they conflict with Phase 1 supply-side reality or the Phase 2 Demand-Side Blueprint (2026-04-20).

**Context:** The April 2025 docs are 12 months stale. Six content/strategy conflicts identified (geography, MOQ, certifications priority, positioning, target markets, product categories). Yossi granted absolute override authority.

**The New Source of Truth (in priority order):**
1. This file (`M-memory/decisions.md`)
2. `B-brain/00-MASTER-PLAN.md`
3. `B-brain/06-growth/00-phase-2-blueprint-geo-seo.md`
4. `B-brain/05-research/supply-intelligence/00-master-factory-bench.md`
5. `C-core/voice-dna.md` + `C-core/project-brief.md` + `C-core/icp-profile.md`

April 2025 docs retained as historical reference only.

**Status:** Active — locked

---

## 2026-04-19 — Trimurthi Lederwaren Eliminated from Supply Pipeline

**Decision:** Trimurthi Lederwaren Pvt Ltd (Chennai) is permanently removed from KritiKaal's operational supply pipeline. No golden sample order. No further research. No client engagement using this factory.

**Context:** Trimurthi was identified during Sprint 01 as a test-case POC factory. The State of the Union audit (2026-04-19) surfaced the supply-side blind spot: the demand pipeline was 6 weeks ahead of a factory bench of zero qualified partners. Before escalating, Yossi confirmed that Trimurthi held no strategic value — it was a POC exercise only, never a real candidate.

**Disqualifying signals (on record):**
- Quality assurance page under construction at time of brief
- MOQ of 1–5 pieces flagged as suspicious for a factory claiming production-scale capability
- No BSCI / SA8000 / ISO certification on record
- LWG certification was held by parent tannery (Trinity Lederwaren) — applies to raw material sourcing, not finished goods production
- Ex-factory price (Rs.2,000–3,000/unit) was bottom-of-market — quality risk signal

**Implications:**
- `B-brain/05-research/supply-intelligence/trimurthi-factory-brief.md` is retained as historical reference only — do not use operationally
- Supply-side hunt restarts from zero with a clean slate
- New Supply-Side Factory Qualification Playbook to be built before any demand-side outreach

**Status:** Closed — do not revisit

---

## 2026-03-22 — Create MASTER Strategy File for KritiKaal.com

**Decision:** Create `B-brain/00-MASTER-strategy.md` as the central business reference document for all AI-assisted work on KritiKaal.

**Context:** Starting to build recurring AI processes for KritiKaal. Every session without a central reference is a degraded session. Sufficient source material existed to build it immediately.

**Options Considered:**
1. Single comprehensive file now — chosen
2. Two-layer architecture (BRIEF + DEEP) — good long-term option, deferred until file exceeds 3,000 words
3. Skeleton + incremental — rejected (skeletons stay empty)
4. Do nothing — rejected (unacceptable compounding cost)

**Rationale:** Source material was sufficient. Cost of delay paid in every future session. Single file with embedded two-layer structure captures the benefits without adding maintenance complexity on day one.

**Implications:**
- MASTER file must be updated whenever core service, pricing, or market strategy changes
- Numbers labeled as [TARGET] vs. [OPERATIONAL] — this distinction must be maintained
- 90-day mandatory review: 2026-06-22
- CLAUDE.md should eventually be updated to instruct agents to read MASTER file at session start

**Review Date:** 2026-06-22

**The Loop:** Not ready for C-core yet — this is a process decision, not a brand principle.

**Status:** Active

---

## 2026-04-17 — Financial Model Correction: $35K/Client Retired, $5K Deal Baseline Adopted

**Decision:** Replace the "$28 clients × $35K = $1M ARR" model with the confirmed $5,000 average deal size as the Phase 1 financial baseline.

**Context:** The original MASTER file derived the $35K/client figure from research samples (sample-03). Yossi confirmed this was aspirational, not operational. The true baseline is $5,000 per deal. Path to $1M ARR now runs through deal volume: 200 deals/year (~17/month).

**Options Considered:**
1. Keep $35K model as a long-term target — rejected (misleads agents in near-term analysis)
2. Adopt $5,000 baseline and reframe ARR math — chosen
3. Remove all financial targets until confirmed — rejected (leaves agents with no anchor)

**Rationale:** Agents making pricing, go-to-market, and capacity recommendations need an accurate financial baseline. Stale optimistic numbers produce stale optimistic analysis.

**Implications:**
- All future deal-size references use $5,000 unless Yossi updates this
- The "28 clients" framing is retired from all documents
- The $1M ARR goal is unchanged — the unit economics changed

**Review Date:** 2026-07-17

**The Loop:** Not ready for C-core — financial baseline may still evolve in Phase 1.

**Status:** Active

---

## 2026-04-17 — CRITICAL CORRECTION: $1M Goal is PROFIT, Not Revenue

**Decision:** The $1,000,000 annual goal is $1M in GROSS PROFIT — not top-line sales revenue (ARR).

**Previous (wrong) model:**
- $1M gross revenue
- At 22% margin = ~$220K gross profit
- Required: 200 orders/year at $5,000 AOV

**Corrected model:**
- $1M gross profit
- At 22% margin → required gross revenue = $4.54M
- At $5,000 AOV → required: 909 orders/year (~76 orders/month)
- At 6 reorders/year per client → 152 active clients needed
- This is a 4.5× scale-up in deal volume vs. the previous model

**Implications — Three Paths to $1M Profit:**

| Path | AOV | Margin | Revenue Needed | Orders/Year | Active Clients (6×/yr) |
|------|-----|--------|----------------|-------------|------------------------|
| Volume play | $5K | 22% | $4.54M | 909 | 152 |
| AOV uplift | $10K | 22% | $4.54M | 454 | 76 |
| Margin + AOV | $15K | 30% | $3.33M | 222 | 37 |
| Ideal state | $20K | 35% | $2.86M | 143 | 24 |

**Strategic implication:** The $5K AOV baseline is a floor, not a ceiling. Every deal that grows to $10K–$20K cuts the required order volume in half. Growing AOV (larger batches, broader SKU coverage per client) is as important as growing client count. The Global Demand-Side Playbook must target clients capable of $50K–$100K/year deal volume, not $5K one-off orders.

**Rationale:** The correction came after Sprint 01 unit economics revealed that a 22% gross margin model requires 4.5× the previously modeled deal volume to hit $1M profit. This was previously unmodeled because the $1M figure was treated as revenue.

**Review Date:** 2026-07-17

**The Loop:** Promote to C-core/00-master-context.md — this is a fundamental financial correction. [PENDING YOSSI CONFIRMATION]

**Status:** Active

---

## 2026-04-17 — $5,000 Confirmed as Per-Transaction AOV (Not Retainer)

**Decision:** The $5,000 average deal size is a per-transaction average order value. Clients order on-demand — some once a year, some 10 times a year. This is NOT a monthly retainer model.

**Implication for $1M ARR math:** 200 transactions/year (~17/month) at $5,000 AOV = $1M ARR. The path to $1M is a transactional volume game, not a client-concentration game. The Strategist must model all projections using transaction volume, not client headcount.

**Implication for acquisition strategy:** Repeat-order frequency is a key lever. A client ordering 10x/year at $5K = $50K LTV. A client ordering 1x/year = $5K. Increasing order frequency per client is as important as new client acquisition.

**Status:** Active

**Example:**
| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2024-01-15 | No emojis in headlines | Feels more professional, matches voice DNA | Active |
| 2024-01-10 | Always use "you" not "we" | More direct, creates connection | Active |

---

### Content Decisions

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| [Date] | [What you decided] | [Why] | [Active/Revisit/Deprecated] |

**Example:**
| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2024-01-12 | LinkedIn posts max 300 words | Longer posts lose engagement | Active |
| 2024-01-08 | One CTA per post only | Multiple CTAs dilute action | Active |

---

### Process Decisions

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| [Date] | [What you decided] | [Why] | [Active/Revisit/Deprecated] |

**Example:**
| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2024-01-14 | Gatekeeper reviews all content before publish | Quality control is non-negotiable | Active |
| 2024-01-11 | Version files as v1, v2, final | Need to track iterations | Active |

---

### Strategic Decisions

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| [Date] | [What you decided] | [Why] | [Active/Revisit/Deprecated] |

**Example:**
| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2024-01-16 | Focus on LinkedIn over Twitter | Audience is more active there | Active |
| 2024-01-05 | Educational content over promotional | Builds trust, aligns with brand | Active |

---

## Decision Template

When logging a significant decision:

```markdown
## [Date] - [Decision Title]

**Decision:** [Clear statement of what was decided]

**Context:** [What prompted this decision]

**Options Considered:**
1. [Option A] - [Pros/cons]
2. [Option B] - [Pros/cons]
3. [Chosen option] - [Why this one]

**Rationale:** [The reasoning behind the choice]

**Implications:**
- [What this means for X]
- [What this means for Y]

**Review Date:** [When to revisit this decision]

**The Loop:** Is this ready to promote to C-core? [Yes/Not yet/N/A]

**Status:** Active / Revisit / Deprecated
```

---

## Quarterly Review Template

```markdown
## Q[X] Decision Review

### Decisions Still Valid
- [Decision] - Still working because [reason]

### Decisions to Revisit
- [Decision] - Questioning because [reason]

### Decisions to Promote to C-core (The Loop)
- [Decision] - Held for 3+ months, ready to become a core principle

### Decisions to Deprecate
- [Decision] - No longer relevant because [reason]

### New Decisions Needed
- [Topic] - Need to decide [what]
```

---

*Decisions age. Context helps them age well. Strong decisions graduate to C-core. That's The Loop.*

---

> **© Tom Even**
> Workshops & future dates: [www.getagents.today](https://www.getagents.today)
> Newsletter: [www.agentsandme.com](https://www.agentsandme.com)
