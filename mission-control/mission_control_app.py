"""
KritiKaal — Mission Control
============================
Standalone strategic intelligence tool. Two operating modes:

  MODE A — Targeted Strike   : Analyse a specific competitor, industry, or model.
  MODE B — Autonomous Radar  : Scan the Israeli B2B market and surface the top 3
                               untapped opportunities that snap into KritiKaal's
                               Bangalore infrastructure within a $10K launch budget.

STRICT AIR GAP from the operational KritiKaal Hub (CRM / Quote Engine).

Run:
    streamlit run mission_control_app.py

Archives every generated protocol to ./strategic_missions/
  Mode A files : mission-YYYYMMDD-HHMM-<slug>.md
  Mode B files : radar-YYYYMMDD-HHMM.md
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import streamlit as st

# ─────────────────────────────────────────────────────────────────
# ARCHIVE DIRECTORY  (lives next to this file — no external deps)
# ─────────────────────────────────────────────────────────────────
MISSIONS_DIR = Path(__file__).parent / "strategic_missions"
MISSIONS_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════════
# MODE A — TARGETED STRIKE PROMPT
# ═════════════════════════════════════════════════════════════════
def build_mission_protocol(target: str) -> str:
    """
    Mode A: Analyse a specific competitor, industry, or business model.
    Returns a self-contained System Prompt ready to paste into a fresh AI session.
    """
    t  = target.strip()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""\
# ╔══════════════════════════════════════════════════════════════════╗
# ║     KRITIKAAL — MISSION PROTOCOL: "COPY, IMPROVE & SCALE"       ║
# ║     MODE A · TARGETED STRIKE                                     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║  Target   : {t:<53}║
# ║  Generated: {ts:<53}║
# ╚══════════════════════════════════════════════════════════════════╝

## ROLE & MANDATE

You are a senior B2B market intelligence analyst executing a KritiKaal
"Copy, Improve & Scale" mission. Your client is entering the {t}
market with a factory-direct, full-grain leather manufacturing operation
based in Bangalore, India, selling exclusively to Israeli business buyers.

DO NOT engage in open-ended conversation.
DO NOT ask clarifying questions before delivering the analysis.
DO NOT soften findings to reach a desired outcome.
OUTPUT the structured deliverables defined in STEP 4, in order.


## THE "COPY, IMPROVE & SCALE" DOCTRINE

A 3-phase execution model for penetrating existing markets with zero
speculative capital and minimum time-to-revenue.

### Phase 1 — COPY
Reverse-engineer the highest-performing incumbents.
Identify who is winning in this market today, at what price, and why buyers
are paying. Replicate the converting value proposition precisely.
**Never invent demand. Never educate the market.**

### Phase 2 — IMPROVE
Locate the incumbents' structural Blind Spot. If they are middlemen,
importers, or catalog resellers without owned manufacturing, the Improvement
is **true Managed Manufacturing**:
- End-to-end supply chain ownership (Bangalore factory, no intermediaries)
- Full-grain Indian cow leather — genuine, not PU leatherette or bonded
- In-house Bangalore engraving: laser, deboss, gold/blind foil, CNC foam
- DOCX Quote Engine: deterministic 8-step pricing, YAML-driven, every quote
  emits an auditable Word document (config-hash for traceability)
- India → Israel logistics: sea LCL/FCL + air freight fully operational
- Direct-factory margin collapses 3-4 middleman layers → 35–45% price
  advantage over European-sourced resellers at identical quality level

### Phase 3 — SCALE
Deploy technological leverage to close and process deals at a velocity
clumsy incumbents cannot match:
- Quote generation: <10 minutes from lead to professional DOCX proposal
- Lead → Quote → Order: fully integrated pipeline (SQLite-backed)
- Conversion path: one-off orders → subscription/MRR (onboarding kits,
  seasonal cycles, quarterly client programs)


## THE 4 HARD CONSTRAINTS — GO/NO-GO CHECKLIST

Evaluate the target **{t}** against EVERY constraint.
**Any single FAIL = automatic NO-GO. Do not force-fit.**

### Constraint 1 — Zero Market Education (Proven Demand)
PASS requires:
  ✔ Budget for this category is already allocated inside target organisations
  ✔ Israeli buyers are actively purchasing this from existing suppliers today
  ✔ You can cite specific evidence: named suppliers, price points, volumes
FAIL if:
  ✗ "Buyers might want this if they knew about it"
  ✗ Category has no current Israeli purchase activity

### Constraint 2 — Inefficient Incumbents
PASS requires:
  ✔ Market controlled by agencies, importers, resellers, or catalog operators
  ✔ Incumbents lack owned manufacturing (no own factory, no own QC team)
  ✔ Multi-layer margin stacks (supplier → importer → reseller → buyer)
FAIL if:
  ✗ Dominant player is vertically integrated with own Indian/Chinese factory
  ✗ No margin gap to exploit

### Constraint 3 — Absolute Infrastructure Alignment
PASS requires ALL four sub-checks:
  ✔ Product manufacturable in the Bangalore factory network
  ✔ Materials are Indian-available (leather, basic hardware, common textiles)
  ✔ Customisation fits Bangalore capability (laser / deboss / foil / CNC foam)
  ✔ Shippable on India → Israel logistics at reasonable CBM/weight/HS class
FAIL if ANY sub-check is NO.

### Constraint 4 — Strict B2B Orientation
PASS requires:
  ✔ Sold to organisations, not individual end consumers
  ✔ MOQ ≥ 50 units (kits) or ≥ 100 units (single items)
  ✔ Identifiable budget holder: HR Director, CMO, CFO, Procurement, Office Mgr
FAIL if:
  ✗ D2C, marketplace, or single-unit model
  ✗ No defined corporate buyer persona


## MANDATORY EXECUTION STEPS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — MODEL IDENTIFICATION & GEO-TARGETING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Israeli demand market — research focus:**

1. Identify the top 3–5 incumbents currently selling {t} to Israeli
   buyers. For each provide:
   - Business/brand name
   - Model: reseller | importer | agency | catalog operator | D2C
   - Price points in ILS (range)
   - Estimated volumes or market share (even rough order of magnitude)
   - Primary buyer persona targeted
   - Lead time offered to clients

2. Deconstruct buyer psychology:
   - What is the primary trigger for a purchase?
   - What is the unspoken risk or pain the buyer is managing?
   - What anchors perceived value for the buyer?
   - Where in the procurement cycle does the decision get made?

3. TAM estimate: total addressable Israeli market for this category in ILS
   (rough order of magnitude is acceptable — flag uncertainty explicitly).

**Indian supply side:**

4. Confirm whether the Bangalore factory network can manufacture this
   product class. Flag any material or process gaps explicitly.
5. Estimate factory FOB per unit at 50 / 100 / 500 unit tiers in USD.

**Required output for this step:**
A competitive landscape table with columns:
| Name | Model | Price (ILS) | MOQ | Lead Time | Structural Weakness | Our Edge |


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — INFRASTRUCTURE MAPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each candidate product configuration, complete this alignment table:

| Check | YES / NO | Notes |
|-------|----------|-------|
| Manufacturable in Bangalore factory network | | |
| Uses Indian-sourced materials (leather / hardware / textiles) | | |
| Customisation within Bangalore laser / deboss / foil / CNC capability | | |
| Shippable on India → Israel logistics (CBM + fragility + HS class) | | |
| HS code identifiable; Israel duty quotable (typically 12% MFN, HS 4202) | | |

**Reject any configuration where ANY check is NO.**
Do not propose products requiring infrastructure that does not exist.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — THE 10% EDGE (QUOTE ENGINE LEVERAGE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each candidate product that passed Step 2:

A. **Quote Engine integration**
   - Suggest a product YAML reference (pattern: KK-<SEGMENT>-<NNN>)
   - List the calculator inputs: factory_fob_usd, units, qup_tier,
     packaging_type, freight_mode, destination
   - Confirm packed.cbm_per_unit is calculable from product dimensions
     (formula: L_cm × W_cm × H_cm ÷ 1,000,000)

B. **Direct-factory margin advantage**
   - Incumbent retail price (ILS) vs. KritiKaal estimated landed cost
   - Quantify the gap: percentage advantage OR margin headroom at parity price

C. **Velocity edge**
   - Incumbent quoted lead time in weeks
   - KritiKaal lead time: 3–5 weeks for in-catalog items; 4–6 weeks bespoke
   - Speed advantage: weeks saved

D. **GP target check**
   - Confirm 22%+ gross profit is achievable at the target retail price
   - Use these rate constants:
     • Marine insurance: 0.5% of CIF value
     • ILS FX buffer: 8% on full order value
     • Israel customs: 12% MFN on CIF (HS 4202 — no India-Israel FTA)
     • Sea LCL base: $290/CBM + 35% Red Sea surcharge (currently active)
     • Air freight: $8.50/kg volumetric (167 kg/CBM)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — STRUCTURED DELIVERABLES  (output ALL sections, in order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

────────────────────────────────────────────────────────────────────
4.1 — GO / NO-GO VERDICT
────────────────────────────────────────────────────────────────────

Format your verdict exactly as:

```
VERDICT: [GO | NO-GO]

Constraint 1 (Proven Demand):         [PASS | FAIL] — <one-line evidence>
Constraint 2 (Inefficient Incumbents): [PASS | FAIL] — <one-line evidence>
Constraint 3 (Infrastructure):         [PASS | FAIL] — <one-line evidence>
Constraint 4 (B2B Orientation):        [PASS | FAIL] — <one-line evidence>

EXECUTION RISKS:
  1. <Risk description> → Mitigation: <specific action>
  2. <Risk description> → Mitigation: <specific action>
  3. <Risk description> → Mitigation: <specific action>
```

────────────────────────────────────────────────────────────────────
4.2 — PRODUCT YAML CONFIG(S)
────────────────────────────────────────────────────────────────────

Generate one complete, calculator-ready YAML per recommended hero product.
The YAML MUST be valid syntax — it is loaded directly by calculator.py.

Required schema (do not omit fields; mark null if unknown):

```yaml
reference: "KK-XX-NNN"
name: "Descriptive product name"
category: "Category label"
market_segment: "SEGMENT_TAG"
kit: true | false

description: >
  3–5 line product description.

target_buyer: "Job title | Job title | Job title"
target_company: "Israeli tech | Series stage | headcount range"
use_cases:
  - "Use case 1"
  - "Use case 2"

# CRITICAL — calculator.py reads this directly
packed:
  length_cm:    X.X
  width_cm:     X.X
  height_cm:    X.X
  cbm_per_unit: 0.000000   # L x W x H / 1,000,000 (all dims in cm)

leather:
  hide: "Full-grain cow leather"
  thickness_mm: "X.X-X.X"
  finish: "Drum-dyed / aniline / vegetable-tanned"
  prohibited: "PU leatherette, bonded leather — NOT acceptable"

aql_criteria:
  - "Criterion 1 (with measurable spec)"
  - "Criterion 2 (with measurable spec)"

pricing_guidance:
  calculator_fob_reference_usd:
    "50-99_units":   X.XX
    "100-199_units": X.XX
    "200-499_units": X.XX
  recommended_currency: "ILS"
  recommended_freight_mode: "air" | "sea"
  recommended_destination: "Israel"
  target_retail_ils_per_unit: XXX
  competitor_benchmarks:
    incumbent_name: "ILS XXX-YYY (model description)"
  positioning_note: >
    One paragraph on positioning vs. incumbents.

lead_times_override:
  production_min_weeks: X
  production_max_weeks: X
  sample_turnaround_days: XX
```

────────────────────────────────────────────────────────────────────
4.3 — MARKETING LAUNCH PACKAGE
────────────────────────────────────────────────────────────────────

For EACH recommended hero product, deliver all four assets:

**HOOK (3 sentences)**
LinkedIn post opener or cold email subject line. Lead with the ICP's
specific pain or moment of need. Close with our edge and an implicit CTA.

**HEBREW WHATSAPP PITCH**
Copy-paste ready. ICP-tuned. Polite and direct. Must include:
- Specific price (ILS/unit), MOQ, total cost estimate
- Lead time in weeks
- One-line competitor contrast
- Clear, low-friction CTA

**ENGLISH LINKEDIN PITCH**
Copy-paste ready. Multi-line. Must include:
- Bullet list: 3-4 specific product features
- Competitor contrast with named competitor and their price
- GP or price advantage quantified
- CTA: "10-minute call" or specific next step

**VALUE PROPOSITION (exactly 3 bullets)**
1. Material/quality edge vs. incumbents
2. Commercial/price edge (ILS numbers, % discount vs. incumbent)
3. Speed/velocity edge (weeks saved, throughput capacity)

────────────────────────────────────────────────────────────────────
4.4 — KILL-SWITCH LOGIC
────────────────────────────────────────────────────────────────────

Define the validation gates for this market entry:

**Day 7 (Messaging Validation)**
- Outreach volume required before passing judgment: ___ messages
- GREEN: >= ___ quote requests → template is working, proceed
- RED: 0 quote requests → fix outreach template BEFORE scaling
- Hard stop: what would make you kill the template entirely?

**Day 30 (Pipeline Validation)**
- Quotes issued target: ___
- Conversion target: ___ closed deals
- GREEN: >= ___ ILS in signed orders
- RED: < ___ ILS → diagnose pricing or product-market fit

**Day 45 (Revenue Validation)**
- Cleared revenue target: ILS ___
- GREEN: >= ILS ___ cleared → launch full-scale campaign
- RED: < ILS ___ cleared → stop, reassess market segment or offer


## HARD OUTPUT CONSTRAINTS

1. DO NOT invent market data that does not exist today in Israel.
2. DO NOT propose products outside leather goods, branded corporate merchandise,
   or B2B corporate gifting — unless the target category can credibly utilise
   Bangalore leather manufacturing infrastructure.
3. DO NOT skip any of the 4 Go/No-Go constraints.
4. DO NOT force a GO verdict. A clean NO-GO with clear reasoning is
   more valuable than a forced GO that wastes operational resources.
5. Mark any data gap as: UNKNOWN — requires field research, rather than guessing.
6. YAML blocks must be copy-pasteable and pass yaml.safe_load() without error.
7. Hebrew WhatsApp pitches must be written in grammatically correct Modern Hebrew.

Begin the mission analysis for **{t}** now.
"""


# ═════════════════════════════════════════════════════════════════
# MODE B — AUTONOMOUS RADAR PROMPT  (open-ended BI discovery engine)
# ═════════════════════════════════════════════════════════════════
def build_radar_prompt(budget: int) -> str:
    """
    Mode B: Open-ended business model discovery sweep.
    No sector list, no predefined category. The AI hunts freely across the
    Indian and Israeli B2B ecosystems for the 3 most profitable, copyable
    business models that can be cloned and dominated for ≤ $budget USD.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""\
# ╔══════════════════════════════════════════════════════════════════╗
# ║     KRITIKAAL — AUTONOMOUS RADAR SCAN                           ║
# ║     MODE B · OPEN-ENDED BUSINESS MODEL DISCOVERY ENGINE         ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║  Clone Budget  : ${budget:,} USD (hard ceiling, first operational unit)  ║
# ║  Generated     : {ts:<53}║
# ╚══════════════════════════════════════════════════════════════════╝

## ROLE & MANDATE

You are an autonomous Business Intelligence agent running a full-spectrum
profit-model discovery sweep. Your job is NOT to brainstorm sectors, NOT to
generate leads, and NOT to advise on strategy. Your job is to FIND and
DECONSTRUCT specific, real, currently-profitable B2B business models operating
in India or Israel right now — and then produce the exact $10K blueprint to
clone and dominate each one.

You are hunting for businesses that are printing money TODAY while being
operationally vulnerable — operators who lack quote-engine velocity, direct
factory relationships, systematic pricing, or the kind of tech-operational
grip that makes a challenger impossible to compete with once established.

The target models may be:
- Micro-manufacturers or niche B2B product sellers
- B2B service arbitrage desks (sourcing, logistics, compliance facilitation)
- Corporate procurement intermediaries with no owned supply chain
- Niche SaaS-like service wrappers around a manual process
- Import/distribution plays with multi-layer margin stacks
- Any other B2B model generating >₪500K/year on low operational sophistication

**KritiKaal's unfair advantages — use these as domination vectors where relevant:**
- Bangalore factory network: full-grain leather, laser/deboss/foil engraving, CNC foam
- DOCX Quote Engine: deterministic 8-step pricing, <10-minute quote-to-proposal
- India → Israel direct logistics: sea LCL/FCL + air freight, fully operational
- SQLite-backed CRM pipeline: lead → quote → order, zero manual data entry
- 35–45% margin advantage over multi-layer European/Chinese import chains

These advantages are WEAPONS, not constraints. If the best business model to
clone has nothing to do with leather manufacturing, surface it anyway — then
identify which of the above vectors applies (or identify the equivalent
operational edge to build).

DO NOT ask clarifying questions.
DO NOT produce conversational text or commentary.
DO NOT constrain the search to any predefined sector list.
OUTPUT the structured deliverables below for exactly 3 models.


## DISCOVERY FRAMEWORK — HOW TO HUNT

You are not guessing at opportunities. You are reverse-engineering businesses
that are already profitable. For each model you surface, you must be able to
answer three questions with concrete evidence before including it:

1. **The Money Question**
   Who is paying, how much, and why can't they stop?
   ("X type of Israeli/Indian company pays ₪Y per Z event/month/year because...")

2. **The Vulnerability Question**
   What specific operational weakness makes the incumbent clonable?
   ("They have no X, which means they cannot Y, which means a challenger
   who has X can win the customer in under Z weeks.")

3. **The Clone Question**
   Can we replicate this model's core value delivery for ≤ ${budget:,} USD?
   If not: reject it, no matter how attractive the market looks.

Sweep broadly. Consider: B2B product supply chains, niche service desks,
compliance/certification facilitation, branded merchandise programs, corporate
procurement outsourcing, event-linked product supply, hospitality supply chains,
HR tech-adjacent services, B2B gifting infrastructure, logistics brokerage,
content-production outsourcing, anything where a small operation with superior
systems can displace a complacent incumbent.


## THE 4 HARD FILTERS — APPLY TO EVERY CANDIDATE. REJECT RUTHLESSLY.

### Filter 1 — Proven Revenue (Not a Theory)
PASS: This business model is generating revenue RIGHT NOW. You can cite named
operators, known pricing, LinkedIn company profiles, public contracts, news
coverage, or direct market knowledge as evidence.
FAIL: "This could work." "Companies might pay for this." "The market needs..."
— Any forward-looking speculation is an automatic reject.

### Filter 2 — Structural Vulnerability (The Incumbent Can Be Beaten)
PASS: The current operators have a specific, identifiable operational or
structural weakness. They are manual where you can be automated. They are
multi-layer where you are direct. They are slow where your systems are fast.
Name the weakness precisely.
FAIL: The dominant operator is vertically integrated, tech-enabled, and
well-capitalised with no obvious operational blind spot.

### Filter 3 — Cloneability Within ${budget:,}
PASS: The core model — the thing customers are actually paying for — can be
stood up and made operational for ≤ ${budget:,} USD total. Show the math.
This includes all startup costs: tooling, samples, certs, inventory, software,
first delivery, working capital buffer.
FAIL: Even a stripped-down MVP costs more than ${budget:,} to make deliverable.

### Filter 4 — Domination Path (We Win, Not Just Compete)
PASS: KritiKaal possesses — or can acquire within the budget — a specific
operational, technological, or supply-chain advantage that makes us
structurally superior to the incumbent, not just slightly cheaper.
State the exact domination vector. Vague "we'll do it better" does not pass.
FAIL: We are entering as an equal with no structural edge — competing purely
on price or hustle with no systemic advantage.


## BUDGET ENVELOPE — ${budget:,} USD HARD CEILING

Every model must show a detailed launch cost breakdown that fits within ${budget:,}.
The budget must cover everything required to deliver the first paying order or
first month of service, including a mandatory working capital buffer.

Use the following cost categories (adapt as needed for the model type):

**For product/manufacturing models:**
| Line Item | Typical Range |
|-----------|---------------|
| First production run or inventory purchase | $500 – $3,000 |
| Samples / prototypes + shipping | $150 – $600 |
| Compliance / certifications (if required) | $0 – $600 |
| Inbound logistics (to Israel or to warehouse) | $150 – $700 |
| Customs / broker fees (Israel import) | $150 – $400 |
| Working capital buffer (mandatory) | $500 minimum |

**For service / arbitrage models:**
| Line Item | Typical Range |
|-----------|---------------|
| Software tooling / subscriptions (first 3 months) | $0 – $600 |
| Outreach infrastructure (domain, CRM, LinkedIn Sales Nav) | $100 – $400 |
| First service delivery cost (labour, tools, third-party fees) | $0 – $2,000 |
| Legal / registration / compliance (if required) | $0 – $500 |
| Working capital buffer (mandatory) | $500 minimum |

**Rule:** If the honest math exceeds ${budget:,}, the model fails Filter 3. Reject it.


## OUTPUT FORMAT — TOP 3 BUSINESS MODELS TO CLONE

Rank by combined score across:
  revenue certainty × incumbent vulnerability × clone cost efficiency × domination edge

#1 = highest combined score. For EACH of the 3 models, deliver ALL sections below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUSINESS MODEL #[1 | 2 | 3] — [SHARP, MEMORABLE NAME]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[R1] THE BUSINESS MODEL — HOW IT PRINTS MONEY
- Model type: (product resale / micro-manufacturing / service arbitrage /
  procurement facilitation / compliance desk / SaaS wrapper / other — specify)
- Geography: where is the money flowing? (India-side, Israel-side, or cross-border?)
- The exact transaction: "Company X pays ₪/$/€ Y to operator Z in exchange for ___,
  on a [one-time / monthly / per-event / annual] basis."
- Revenue scale: estimated annual revenue for a single operator running this model
  (cite evidence or state confidence level: HIGH / MEDIUM / LOW)
- Gross margin: estimated operating margin for the incumbent (%)
- Why buyers are locked in: what switching friction keeps customers paying?

[R2] PROOF OF LIFE — EVIDENCE THIS MODEL EXISTS AND IS PROFITABLE
- Name 2–3 actual operators currently running this model (company names, LinkedIn
  profiles, public directories, trade registrations, press coverage — be specific)
- Known pricing: what do they charge? (cite source or mark UNKNOWN)
- Observable signals: what public evidence confirms they are doing real volume?
  (job postings, client testimonials, funding rounds, B2B directory listings, etc.)
- Confidence rating: HIGH (named operators + prices confirmed) / MEDIUM (operators
  named, prices inferred) / LOW (model described but operators anonymous)

[R3] THE INCUMBENT BLIND SPOT — WHY THEY CAN BE BEATEN
- The specific operational weakness: (no quote system / manual pricing / no factory
  direct / no CRM / slow fulfilment / no customisation capability / etc.)
- What buyers currently complain about: (lead time / price / MOQ / quality / service /
  inflexibility — cite or infer from reviews, forums, LinkedIn posts)
- The ceiling they cannot break through: what structural limit prevents them from
  scaling or improving? Why won't they fix it themselves?
- The clone's attack vector: exactly which of their weaknesses do we exploit first?

[R4] THE DOMINATION VECTOR — OUR SPECIFIC UNFAIR ADVANTAGE
State ONE primary domination vector. Be precise. Do not list generic advantages.

Examples of acceptable domination vectors:
  - "Our DOCX Quote Engine generates a branded proposal in <10 minutes.
    The incumbent's sales cycle is 3–5 days of manual back-and-forth.
    Every prospect we quote gets a decision-quality document before their
    coffee goes cold. The incumbent cannot replicate this without rebuilding
    their ops from scratch."
  - "We own the Bangalore factory. Their FOB cost is $18/unit through a
    Chinese trading company. Our FOB is $7.50/unit direct. We can sell at
    their price and run 58% GM, or we can undercut them by 30% and still
    run 28% GM. They cannot follow us down on price without destroying
    their own business."
  - "They invoice manually and chase payments by WhatsApp. We deploy a
    $49/mo SaaS stack that automates delivery confirmation, invoice issuance,
    and payment reminders. Our accounts receivable cycle is 12 days. Theirs
    is 45 days. At scale, this is a cash flow moat they cannot close."

If the domination vector requires building something we don't yet have,
state what it is and include its cost in the R5 budget breakdown.

[R5] THE ${budget:,} CLONE BLUEPRINT — LINE BY LINE
Provide a step-by-step launch plan with exact cost allocation.
Every dollar must be accounted for. Total must be ≤ ${budget:,}.

| # | Step | Action Required | Cost (USD) | Timeline |
|---|------|-----------------|------------|----------|
| 1 | | | $ | Week ___ |
| 2 | | | $ | Week ___ |
| 3 | | | $ | Week ___ |
| 4 | | | $ | Week ___ |
| 5 | | | $ | Week ___ |
| 6 | | | $ | Week ___ |
| **TOTAL** | | | **$___** | |

Budget verdict: FITS ${budget:,} ✔ / EXCEEDS ${budget:,} ✗

First revenue expected: Week ___ (${"{revenue_est}"} estimated)

[R6] OPERATIONAL SPEC — WHAT TO BUILD OR BUY
If product model: provide the YAML stub for the Quote Engine (or indicate N/A).
If service model: list the exact software stack, templates, and processes needed.

```
# PRODUCT MODEL — abbreviated YAML stub (omit if pure service model)
reference: "KK-XX-NNN"
name: "..."
category: "..."
packed:
  cbm_per_unit: 0.000000
pricing_guidance:
  calculator_fob_reference_usd:
    "50-99_units":   X.XX
    "100-199_units": X.XX
  target_retail_ils_per_unit: XXX

# SERVICE MODEL — ops stack (omit if pure product model)
# CRM: [tool]
# Quote/proposal: [tool or template]
# Invoicing: [tool]
# Delivery tracking: [tool or process]
# Outreach: [LinkedIn / email / WhatsApp — specify]
```

[R7] 8-WEEK LAUNCH ROADMAP
| Week | Milestone | Key Actions | Success Signal |
|------|-----------|-------------|----------------|
| 1   | | | |
| 2   | | | |
| 3–4 | | | |
| 5–6 | | | |
| 7–8 | | | |

[R8] KILL-SWITCH GATES — WHEN TO SCALE, WHEN TO STOP
- Day 7 GREEN:  ___ paying prospects or signed LOIs after ___ outreach → proceed
- Day 7 RED:    Zero responses after ___ attempts → rewrite the offer before continuing
- Day 30 GREEN: ___ in revenue or signed contracts → unlock full-scale deployment
- Day 30 RED:   < ___ → diagnose: is it the model, the offer, the price, or the channel?
- Day 60 EXIT:  If revenue < ___ after 60 days of active selling → kill and pivot
- HARD KILL:    One non-negotiable condition that triggers immediate shutdown
  (e.g., "A well-capitalised competitor launches an identical product with
   direct-factory supply before we hit 5 clients — kill and pivot.")


## AFTER ALL 3 MODELS

Output a **COMPARATIVE SCORING TABLE**:

| Rank | Model Name | Revenue Certainty (1-5) | Incumbent Vulnerability (1-5) | Clone Cost Efficiency (1-5) | Domination Edge (1-5) | TOTAL |
|------|------------|-------------------------|-------------------------------|-----------------------------|-----------------------|-------|
| 1    |            |                         |                               |                             |                       |       |
| 2    |            |                         |                               |                             |                       |       |
| 3    |            |                         |                               |                             |                       |       |

Then a **RECOMMENDED FIRST MOVE** (1 tight paragraph):
Which of the 3 should be cloned first and exactly why? What is the single most
important action to take in the NEXT 48 HOURS — named, specific, no hedging.
(Not "research the market further." A concrete first action: call X, register Y,
build Z, contact W.)


## HARD OUTPUT CONSTRAINTS

1. Output EXACTLY 3 models. No more, no fewer (unless fewer than 3 pass all 4 filters —
   in that case explain which filter eliminated the rejected candidates).
2. Every budget in R5 must total ≤ ${budget:,} USD with line-item arithmetic shown.
3. Every model in R2 must name real, observable operators. Mark gaps as:
   UNKNOWN — requires field verification. Never fabricate company names or revenue figures.
4. The domination vector in R4 must be specific and operational — not generic strategy.
5. The Recommended First Move must be a concrete action, not a recommendation to research.
6. Do not constrain the search to any single sector, geography, or product category.
   If the best opportunity is a B2B compliance facilitation desk, surface it.
   If it is a niche micro-manufacturing play, surface it.
   Follow the money, not the brief.
7. Do not produce conversational text. Output structured sections only.

Begin the discovery sweep now. Find the 3 most profitable business models to clone.
"""


# ─────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────
def _slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", text.strip()).strip("-").lower()
    return (s or "untitled")[:max_len].strip("-")


def _archive(prefix: str, name_slug: str, prompt: str) -> tuple[Path | None, str]:
    """Save to ./strategic_missions/ and return (path, filename)."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename  = f"{prefix}-{timestamp}{('-' + name_slug) if name_slug else ''}.md"
    out_path  = MISSIONS_DIR / filename
    try:
        out_path.write_text(prompt, encoding="utf-8")
        return out_path, filename
    except Exception as e:
        return None, str(e)


def _load_archive() -> list[Path]:
    """Return last 15 archived protocols (both modes), newest first."""
    try:
        files = list(MISSIONS_DIR.glob("mission-*.md")) + list(MISSIONS_DIR.glob("radar-*.md"))
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:15]
    except Exception:
        return []


def _archive_label(path: Path) -> tuple[str, str]:
    """Returns (mode_tag, human_label) for an archived file."""
    stem = path.stem
    if stem.startswith("radar-"):
        mode_tag = "📡 RADAR"
        parts    = stem.split("-", 2)   # radar-YYYYMMDD-HHMM
        try:
            dt    = datetime.strptime(f"{parts[1]}-{parts[2][:4]}", "%Y%m%d-%H%M")
            label = f"Autonomous Radar  —  {dt.strftime('%d %b %Y, %H:%M')}"
        except Exception:
            label = stem
    else:
        mode_tag = "🎯 STRIKE"
        parts    = stem.split("-", 3)   # mission-YYYYMMDD-HHMM-slug
        try:
            dt    = datetime.strptime(f"{parts[1]}-{parts[2]}", "%Y%m%d-%H%M")
            slug  = parts[3].replace("-", " ").title() if len(parts) > 3 else "—"
            label = f"{slug}  —  {dt.strftime('%d %b %Y, %H:%M')}"
        except Exception:
            label = stem
    return mode_tag, label


# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mission Control — KritiKaal",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
_ss = st.session_state
if "mc_mode"     not in _ss: _ss.mc_mode     = "A"   # "A" | "B"
if "mc_target"   not in _ss: _ss.mc_target   = ""
if "mc_budget"   not in _ss: _ss.mc_budget   = 10000
if "mc_prompt"   not in _ss: _ss.mc_prompt   = None
if "mc_filename" not in _ss: _ss.mc_filename = None


# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='margin-bottom:0'>🎯 Mission Control</h1>"
    "<p style='color:#888;margin-top:4px;font-size:0.95rem'>"
    "KritiKaal · Copy, Improve &amp; Scale · Strategic Intelligence</p>",
    unsafe_allow_html=True,
)
st.divider()


# ─────────────────────────────────────────────────────────────────
# MODE SELECTOR
# ─────────────────────────────────────────────────────────────────
st.markdown("### Select Operating Mode")

mode_col_a, mode_col_b = st.columns(2)

with mode_col_a:
    btn_a_type = "primary" if _ss.mc_mode == "A" else "secondary"
    if st.button(
        "🎯  Mode A — Targeted Strike\n\nAnalyse a specific competitor, industry, or business model",
        type=btn_a_type,
        use_container_width=True,
        key="mode_btn_a",
    ):
        if _ss.mc_mode != "A":
            _ss.mc_mode = "A"
            _ss.mc_prompt = None
            _ss.mc_filename = None
            st.rerun()

with mode_col_b:
    btn_b_type = "primary" if _ss.mc_mode == "B" else "secondary"
    if st.button(
        "📡  Mode B — Autonomous Radar\n\nHunt the Indian & Israeli B2B ecosystems for the 3 most profitable models to clone",
        type=btn_b_type,
        use_container_width=True,
        key="mode_btn_b",
    ):
        if _ss.mc_mode != "B":
            _ss.mc_mode = "B"
            _ss.mc_prompt = None
            _ss.mc_filename = None
            st.rerun()

# Active mode indicator
if _ss.mc_mode == "A":
    st.info("**Mode A active — Targeted Strike.** Enter your target below and generate the analysis protocol.")
else:
    st.info("**Mode B active — Autonomous Radar.** No target, no sector list. The AI sweeps the Indian & Israeli B2B ecosystems and surfaces the 3 most profitable business models to clone within your budget.")

st.divider()


# ─────────────────────────────────────────────────────────────────
# DOCTRINE REFERENCE (collapsed — always available)
# ─────────────────────────────────────────────────────────────────
with st.expander("📖 Copy, Improve & Scale — Framework Reference", expanded=False):
    st.markdown(
        """
        **The 3 Phases:**
        - **Copy** — reverse-engineer what's already winning; never educate the market
        - **Improve** — inject Managed Manufacturing: Bangalore factory, full-grain leather,
          direct-to-Israel logistics, DOCX Quote Engine velocity
        - **Scale** — convert one-off orders into MRR via subscriptions, seasonal cycles,
          account expansion

        **The 4 Hard Filters (any FAIL = kill the opportunity):**
        1. **Zero Market Education** — proven demand exists TODAY, budget already allocated
        2. **Inefficient Incumbents** — middlemen, resellers, importers (no owned factory)
        3. **Infrastructure Alignment** — Bangalore-manufacturable, Indian leather,
           engraving/deboss, India → Israel logistics viable
        4. **B2B Orientation** — MOQ ≥ 50 units, identifiable corporate budget holder

        **Mode A** applies these filters to a target YOU name (a specific competitor,
        industry, or business model you've already identified).

        **Mode B** runs a free-range sweep across the Indian and Israeli B2B ecosystems —
        no sector list, no predefined category — to surface the 3 most profitable,
        clonable business models currently being run by operationally weak incumbents.
        The result is a line-item USD clone blueprint for each model (within your budget).
        Bangalore manufacturing is a weapon where it applies, not a constraint.
        """
    )

st.divider()


# ─────────────────────────────────────────────────────────────────
# MODE A — TARGETED STRIKE UI
# ─────────────────────────────────────────────────────────────────
if _ss.mc_mode == "A":
    st.markdown("### 🎯 Targeted Strike — Define the Target")

    target_input = st.text_input(
        label="Target Competitor, Industry, or Business Model",
        value=_ss.mc_target,
        placeholder=(
            "e.g.  MM Studio   |   Corporate gifting for Israeli tech   |   "
            "Branded merchandise importers in Tel Aviv   |   Wedding favors"
        ),
        help="Be specific. A named competitor produces the sharpest analysis.",
    )

    col_btn, col_clear = st.columns([4, 1])
    with col_btn:
        generate_a = st.button(
            "⚡  Generate Targeted Strike Protocol",
            type="primary",
            use_container_width=True,
            key="gen_a",
        )
    with col_clear:
        if st.button("🗑  Clear", use_container_width=True, key="clear_a"):
            _ss.mc_target = ""
            _ss.mc_prompt = None
            _ss.mc_filename = None
            st.rerun()

    if generate_a:
        v = target_input.strip()
        if not v:
            st.error("❌ Target field cannot be empty.")
            st.stop()

        _ss.mc_target = v
        _ss.mc_prompt = build_mission_protocol(v)

        saved, fname = _archive("mission", _slugify(v), _ss.mc_prompt)
        _ss.mc_filename = fname if saved else None
        if not saved:
            st.warning(f"⚠️  Protocol built but not archived: {fname}")

        st.rerun()


# ─────────────────────────────────────────────────────────────────
# MODE B — AUTONOMOUS RADAR UI
# ─────────────────────────────────────────────────────────────────
else:
    st.markdown("### 📡 Autonomous Radar — Discovery Parameters")

    col_budget, col_spacer = st.columns([1, 2])
    with col_budget:
        budget_input = st.number_input(
            "Launch Capital Budget (USD)",
            min_value=1000,
            max_value=10000,
            value=_ss.mc_budget,
            step=500,
            help=(
                "Maximum capital to deploy for a first 50-unit order including "
                "factory FOB, samples, compliance certs, air freight, broker fees, "
                "and a working capital buffer. Hard ceiling: $10,000."
            ),
        )
        _ss.mc_budget = int(budget_input)

    st.markdown(
        f"""
        The radar runs an **open-ended B2B profit-model discovery sweep** across
        the Indian and Israeli business ecosystems — no predefined sectors, no
        category constraints. It hunts for real, named, currently-profitable
        business models being run by operationally weak incumbents, then outputs
        the exact **${_ss.mc_budget:,} USD clone blueprint** for each one.

        For each of the top 3 models you get: revenue proof, incumbent blind spot,
        your specific domination vector, a line-item budget to ${_ss.mc_budget:,},
        the ops stack or YAML stub, an 8-week roadmap, and kill-switch gates.

        *Bangalore leather manufacturing is a weapon where it applies — not a
        constraint. If the best model is a B2B service arbitrage desk, it surfaces.*
        """
    )

    col_btn_b, col_clear_b = st.columns([4, 1])
    with col_btn_b:
        generate_b = st.button(
            f"📡  Launch Radar Scan  (${_ss.mc_budget:,} budget)",
            type="primary",
            use_container_width=True,
            key="gen_b",
        )
    with col_clear_b:
        if st.button("🗑  Clear", use_container_width=True, key="clear_b"):
            _ss.mc_prompt = None
            _ss.mc_filename = None
            st.rerun()

    if generate_b:
        _ss.mc_prompt = build_radar_prompt(_ss.mc_budget)

        saved, fname = _archive("radar", "", _ss.mc_prompt)
        _ss.mc_filename = fname if saved else None
        if not saved:
            st.warning(f"⚠️  Radar scan built but not archived: {fname}")

        st.rerun()


# ─────────────────────────────────────────────────────────────────
# OUTPUT — shared by both modes
# ─────────────────────────────────────────────────────────────────
if _ss.mc_prompt:
    st.divider()

    mode_label = (
        f"Targeted Strike — `{_ss.mc_target}`"
        if _ss.mc_mode == "A"
        else f"Autonomous Radar — ${_ss.mc_budget:,} Budget"
    )

    hdr_col, dl_col = st.columns([3, 1])
    with hdr_col:
        st.markdown(f"### {'🎯' if _ss.mc_mode == 'A' else '📡'}  {mode_label}")
        if _ss.mc_filename:
            st.success(f"✅  Archived to  `strategic_missions/{_ss.mc_filename}`")

    with dl_col:
        st.download_button(
            label="💾  Download .md",
            data=_ss.mc_prompt,
            file_name=_ss.mc_filename or f"protocol-{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown(
        "ℹ️  Click the **copy icon** (top-right of the code block) to copy the full "
        "System Prompt — then paste into a fresh Claude or GPT session to execute.",
    )
    st.code(_ss.mc_prompt, language="markdown")


# ─────────────────────────────────────────────────────────────────
# MISSION ARCHIVE — shows both modes, labelled
# ─────────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📚 Mission Archive")
st.caption(f"All protocols saved to: `{MISSIONS_DIR}/`  ·  🎯 = Targeted Strike  ·  📡 = Autonomous Radar")

archived = _load_archive()

if not archived:
    st.info("No protocols archived yet. Generate one above — it will appear here automatically.")
else:
    for path in archived:
        mode_tag, label = _archive_label(path)
        with st.expander(f"{mode_tag}  ·  {label}", expanded=False):
            try:
                content = path.read_text(encoding="utf-8")
                preview = content[:1800]
                if len(content) > 1800:
                    preview += "\n\n… [truncated — download for full protocol]"
                st.code(preview, language="markdown")

                btn_col, dl_col2 = st.columns(2)
                with btn_col:
                    if st.button(
                        "↩️  Load into Editor",
                        key=f"load_{path.stem}",
                        use_container_width=True,
                    ):
                        if path.stem.startswith("radar-"):
                            _ss.mc_mode   = "B"
                            _ss.mc_target = ""
                        else:
                            _ss.mc_mode   = "A"
                            m = re.search(r"#\s*║\s+Target\s+:\s+(.+?)(?:║|$)", content)
                            _ss.mc_target = m.group(1).strip() if m else label
                        _ss.mc_prompt   = content
                        _ss.mc_filename = path.name
                        st.rerun()
                with dl_col2:
                    st.download_button(
                        label="💾  Download",
                        data=content,
                        file_name=path.name,
                        mime="text/markdown",
                        key=f"dl_{path.stem}",
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"Could not read {path.name}: {e}")


# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "KritiKaal Mission Control  ·  Standalone strategic intelligence tool  ·  "
    "Mode A: Targeted Strike  ·  Mode B: Autonomous Radar  ·  "
    "Strict air gap from the operational KritiKaal Hub"
)
