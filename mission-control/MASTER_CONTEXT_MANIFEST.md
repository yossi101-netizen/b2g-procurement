# MASTER CONTEXT MANIFEST — KritiKaal (v7.0)

> **Purpose:** Universal brain-injection document for any AI session on any platform.
> Paste this file first before doing any work on the KritiKaal ecosystem.
> **Version:** v7.0 (2026-06-23). Major consolidation of the B2G Israeli-tenders
> initiative (§1.4): Model B (Israeli ח.פ. prime + India captive backend), 3-layer
> procurement pipeline (automated scrape → analyst PDF enrichment → penalty scoring),
> DOM-verified against live mr.gov.il HTML. Incorporates all v6.x patches (volatility
> tags, MOQ bypass, update protocol, landed-cost engine, workspace GC).
> **Portability:** This document is self-contained. No external file reads required.

---

## ⚠ SESSION START — MANDATORY VALIDATION GATE

**Before using ANY numbers from this document in calculations, quotes, or
recommendations, the AI session MUST verify the following volatile constants
against current reality.** This document was last verified on **2026-06-23**.
If today's date is more than 30 days after that, treat ALL `[VOLATILE]` constants
as potentially decayed and verify before calculating.

| Constant | Value at last verification | Volatility | Validation action |
|---|---|---|---|
| **FX INR/USD** | 86 | `[VOLATILE]` — drifts daily | Web-search current rate before any currency conversion |
| **Section 122 surcharge** | 10% | `[VOLATILE]` — **HARD EXPIRY: Jul 23 2026** | If today > Jul 23 2026: this rate is DEAD. Search for its replacement before calculating any US duty. |
| **EMS rate table (§4.2)** | Per table below | `[SEMI-STABLE]` — annual India Post revision | If > 6 months since last verification: confirm rates at indiapost.gov.in or counter |
| **Courier ₹/kg** | 1,100 | `[VOLATILE]` — estimate, not a reseller quote | Replace with actual contracted rate before any courier quote |
| **MFN HTS 4205** | 0% (Free) | `[STABLE]` — legislative change only | No action unless a new tariff bill is announced |
| **Packing buffer** | 15% | `[STABLE]` — product-line dependent | No action unless product line changes |

**If any `[VOLATILE]` constant cannot be verified, the session MUST flag it
explicitly in its output rather than silently using the stale value.**

---

## 1. THE HIERARCHY — two businesses, one network

### 1.1 KRITIKAAL CORE OPERATIONS (the real, revenue-bearing business)

**Quick reference:**
- **What:** "Managed Leather Manufacturing" (kritikaal.com). B2B2B intermediary
  between global brands and India's leather factory clusters.
- **GTM phasing (strict):** Phase 1 Israel → Phase 2 UK → Phase 3 USA.
  Secondary markets (EU/AU) engaged opportunistically, not before Phase 2.
- **Model:** "Single Point of Accountability" — KritiKaal owns the manufacturing
  relationship so the client brand doesn't have to manage factories directly.
- **MOQ for CORE manufacturing clients:** 300+ units/style for recurring B2B
  production orders. **This threshold applies ONLY to CORE manufacturing
  engagements — see §1.3 for explicit bypass conditions.**
- **Lead-gen engine:** leads.db / Israel-Hunter V3 (Class A/B/C importer-wholesaler-OEM
  schema). **Demand-only stack: census → bol_pipeline → digest.** Supply-side
  automation was permanently killed (2026-06-12). KritiKaal manages existing factory
  relationships for clients; it does not autonomously hunt, discover, or qualify new
  factories through software.
- **This is the default meaning of "KritiKaal"** in any cross-project conversation.

#### 1.1.1 Objective & Purpose

**KRITIKAAL.COM is a Managed Manufacturing platform** — India-based, Bangalore HQ
(§2), operating Agra/Kanpur/Kolkata factory clusters as its production network.
Its function is to be the **outsourced production department** for international
leather brands that want India-made goods but cannot or will not build their own
on-the-ground sourcing team.

- **Core mechanism — "Single Point of Accountability":** the client deals with
  ONE entity (KritiKaal) for everything between "I have a design" and "stock
  arrives at my warehouse" — supplier vetting, costing, sampling, QC, production
  oversight, compliance documentation, and export logistics. KritiKaal is
  **asset-light** (doesn't own the factories) but runs **embedded QA inside
  partner factories**, so the client gets factory-floor control without
  factory-floor presence.
- **The USP, verbatim from doctrine:** *"Western management on the ground"* —
  100% accountability for outcome from **Golden Sample → export**. This is the
  antidote to the standard Alibaba/direct-sourcing failure mode (deposit paid,
  sample looks great, bulk order arrives degraded, no recourse).
- **Strategic framing for the client:** KritiKaal is the **"China Plus One"**
  play — a way for brands to diversify production out of China into India without
  inheriting China-sourcing's operational playbook (different ports, different
  document regimes, different factory culture).
- **Product capabilities:** Bags, belts, SLGs (small leather goods), and custom
  brand developments, sourced across India's specialised leather-manufacturing
  clusters (Agra/Kanpur/Kolkata — see §2).
- **Commercial shape:** MOQ 300+ units/style (CORE only — see §1.3), recurring
  B2B relationship (not one-off), target $1M ARR in Year 1.

In one line: **KritiKaal sells the *removal of operational risk* from India-based
leather manufacturing — not leather goods themselves.** The leather goods are the
deliverable; the product being sold is accountability.

#### 1.1.2 Target Audience / Client Profile — by Market (Phase 1 → 2 → 3)

> **Disambiguation note (cross-references §1.2/§3):** In all three markets below,
> the "client" is a **brand/importer who *manufactures through* KritiKaal** — the
> buy-side of CORE's B2B2B model. This is structurally distinct from The Hybrid
> Premium, where Israeli HR Directors/Founders are *recipients* of KritiKaal's own
> gifted product. An Israeli company can appear in *both* funnels (CORE
> manufacturing client AND Hybrid Premium gift recipient) without it being the
> same relationship.

##### Israel (Phase 1 — immediate focus)

**Client profile:** Three sub-segments map to the existing Israel-Hunter V3
Class A/B/C schema:
- **Class A** — established importers with existing China/Turkey relationships,
  looking to diversify sourcing geography (the "China Plus One" pitch lands
  directly here).
- **Class B** — wholesalers/distributors currently buying finished goods through
  intermediaries (Turkish/Chinese trading houses), who want to cut a markup layer
  by going direct-to-factory via KritiKaal.
- **Class C** — OEM/private-label brand owners (often DTC, sometimes ex-tech
  founders) wanting their own branded leather line without owning production.

**Why Phase 1:** Founder's physical presence in Israel, Hebrew-fluent operations,
existing local network. All outbound effort concentrates here until repeatable
revenue is established.

**Compliance & regulatory:** Israel has no domestic leather-specific compliance
regime comparable to Prop65 or REACH. The real compliance angle is **re-export
exposure**: a large share of Israeli wholesale/import houses re-sell into the EU,
so their downstream obligations under EU REACH become KritiKaal's problem
indirectly. Frame compliance documentation to Israeli clients as
**"future-proofing your re-export," not "meeting a domestic mandate."**

**Logistics:** India (Nhava Sheva/Chennai) → Israel (Haifa/Ashdod), **~2-3 weeks**
via Suez (fastest market). Red Sea disruption may add 1-2 weeks via Cape routing.

**Buyer psychology:** WhatsApp-speed, founder-to-founder, trust-driven. Dominant
pain: prior burns with Chinese suppliers (quality drift, communication silence
post-deposit). Lead with "Single Point of Accountability."

##### United Kingdom (Phase 2)

**Client profile:** Shopify-based leather goods brands, small fashion houses, and
B2B importers/wholesalers supplying UK retail. Generally more established and
slower-moving than DTC segments.

**Why Phase 2:** Regulatory-heavy market (UK REACH, GPSR, EUDR) — requires
proven operational maturity from Phase 1 before entry. Compliance documentation
must arrive before the commercial conversation.

**Compliance & regulatory:** The most regulatorily front-loaded market:
- **UK REACH** — Chromium VI capped at 3mg/kg in leather articles.
- **GPSR** — general consumer-goods safety duty.
- **EUDR** — cattle/leather is a named commodity; most UK brands resell into EU,
  pulling EUDR due-diligence into scope indirectly.
- **Post-Brexit customs** — EORI numbers, DDP terms frequently requested.

**Logistics:** India → UK (Felixstowe, Southampton, London Gateway), **~3-4 weeks**
via Suez. Same Red Sea rerouting exposure as Israel.

**Buyer psychology:** Formal, multi-stakeholder, docs-upfront. Sustainability/ESG
narrative resonates strongly. Dominant pain: compounding compliance/logistics burden
(Brexit + EUDR stacking).

##### United States (Phase 3)

**Client profile:** Shopify-native DTC leather brands, private-label Amazon FBA
sellers, and small-to-mid accessory/footwear brands — almost always 1-10 person
operations with direct Alibaba-sourcing scars.

**Why Phase 3:** Highest compliance burden (Prop 65, CPSIA, FTC labeling) requires
a mature operational pipeline. Longest transit time. Activated after UK playbook
is operational.

**Compliance & regulatory:** Compliance-dominant market, different stack than UK/EU:
- **California Prop 65** — warning-label triggers for heavy metals in hardware/dyes
  and tanning byproducts.
- **CPSIA** — lead-content limits on hardware.
- **FTC labeling** — country-of-origin and care labeling requirements.
- **India-origin goods are NOT subject to Section 301 China tariffs** — active
  competitive talking point.
- Standard MFN duty rates on HS 4202/4203 (8-20% depending on subheading).

**Logistics:** India → US (LA/Long Beach, NY/NJ, Savannah), **~30-45 days** ocean.

**Buyer psychology:** Process/documentation-oriented, async SLA-driven. Certifications
matter as marketing assets for their own listings. Dominant pain: Alibaba ghosting +
sample/bulk quality divergence.

#### 1.1.3 Cross-Market Comparison (Phase 1 → 2 → 3 order)

| Dimension | Israel (Phase 1) | United Kingdom (Phase 2) | United States (Phase 3) |
|---|---|---|---|
| **Client role** | leads.db Class A/B/C | Shopify B2B/wholesale | Shopify/FBA DTC |
| **Compliance driver** | None domestic (re-export to EU REACH) | UK REACH Cr(VI), GPSR, EUDR | Prop 65, CPSIA, FTC labeling |
| **Tariff angle** | Standard import tax | MFN + post-Brexit EORI | India NOT hit by Section 301 |
| **Key ports** | Haifa, Ashdod | Felixstowe, Southampton | LA/Long Beach, NY/NJ |
| **Transit (Suez)** | ~2-3 weeks | ~3-4 weeks | ~30-45 days |
| **Red Sea exposure** | High | High | Lower (Cape/Pacific) |
| **Communication** | WhatsApp, founder-to-founder | Formal, docs-upfront | Async, SLA-driven |
| **#1 pain we solve** | China-supplier trust collapse | Compliance stacking | Alibaba ghosting + drift |
| **Certification role** | Future-proofing re-export | Onboarding gate | Marketing asset |

---

### 1.2 THE HYBRID PREMIUM (isolated incubation project)

- **What:** KritiKaal acting as the BRAND itself — selling 50-100 unit premium
  corporate gift kits (leather + stainless steel/tech "Functional Luxury")
  direct to Israeli HR Directors and Tech Founders (Series B-D), as
  milestone/onboarding/board kits.
- **Master brand: "Alloy & Grain"** — the public-facing name. Encodes the thesis:
  Alloy (steel/tech) + Grain (full-grain leather).
- **Bespoke sub-line: "The Vellum Collection"** — reserved for KK-CG-CFS bespoke
  tier (₪500-1,200/unit, Series C/D milestone gifts).
- **Downgrade Trap — hard rule:** never use "Swag," "Promo," "Merch," or "Gifts"
  in external-facing copy.
- **Status:** pre-revenue, sample-seeding phase as of 2026-06-14.
- **MOQ:** 50-100 units per kit/run (by design — see §1.3).

---

### 1.3 MOQ RULES & BYPASS CONDITIONS

The "MOQ 300+" rule is frequently cited in this document. To prevent an AI from
mechanically rejecting viable deals, the following scoping rules apply:

| Context | MOQ | Rationale |
|---|---|---|
| **CORE manufacturing client** (standard B2B2B) | 300+ units/style | Factory economics: setup costs, fabric minimums, QC amortization. This is the default. |
| **Hybrid Premium / Alloy & Grain** | 50-100 units/kit run | By design — corporate gifting operates at lower volume, higher margin. |
| **Client sample/onboarding run** | No minimum | Sample runs (5-50 units) are the entry funnel. Never reject a sample request on MOQ grounds. |
| **Enterprise high-margin deal** | **Operator discretion** | If a deal's gross margin exceeds 50% AND the client is a named enterprise account, the operator may override the 300-unit floor. The AI should flag the MOQ exception and present the margin math — not auto-reject. |

**Decision rule for AI sessions:** If a deal falls below 300 units and does not
match one of the bypass conditions above, **present the MOQ constraint to the
operator as a flag, not as an automatic rejection.** Include the unit economics
so the operator can make the commercial judgment.

---

### 1.4 B2G — ISRAELI GOVERNMENT TENDERS (Phase 1 sub-initiative)

- **Structure (Model B — confirmed 2026-06-23):** Operator owns an active registered
  Israeli company (ח.פ., est. 2013) with local banking. **The Israeli entity is the
  Prime Contractor; KritiKaal India (Agra/Kanpur/Kolkata) is the captive
  manufacturing backend.** No foreign-prime bidding. The entity gate is SOLVED.
- **Domestic-preference thesis (key reframe):** The statutory תוצרת הארץ preference
  is treated as an **absorbable cost delta, NOT a disqualifier.** India-cluster
  landed cost vs Israeli domestic production routinely exceeds the preference margin,
  so KritiKaal can absorb the penalty and still underbid. **"No domestic producer
  exists" is NO LONGER a gate** — we compete head-on against Israeli makers.
- `[VOLATILE]` **Preference tiers:** base 15% (תקנות חובת המכרזים – העדפת תוצרת הארץ,
  תשנ"ה-1995). Gaza-envelope uplift verified at +20% (1.9.2023–1.9.2028). Operator
  cited 35% — **CONFIRM exact tier before hardcoding** (false-high = lost bids).
- **Tool:** `T-tools/procurement_ingest.py` (top-of-funnel intelligence only,
  DOM-verified 2026-06-23). mr.gov.il = SSR Hybris; financials are inside attached
  PDFs, never in HTML DOM. **`ingest`:** scrape search pages → Hebrew keyword filter
  → `tenders.db`. **`review`:** output clean list of manufacturing-relevant tenders
  with metadata, deadlines, publisher, and PDF download links for human evaluation.
  **No automated financial scoring** — operator handles penalty math, bond assessment,
  and bid decisions manually per tender. CATEGORY_COST_TABLE and penalty_filter killed
  (2026-06-23) as premature optimization / maintenance debt. Akamai WAF → cookie-primed
  session + Playwright fallback. data.gov.il = annual archive (rejected); gov.il RSS =
  news (rejected). MoD out of scope until defense categories.
- **Financial evaluation:** Operator-manual. The tool surfaces relevant tenders;
  the operator opens the PDF, reads ערבות/אומדן, and runs the penalty math
  (`max_bid = אומדן ÷ 1.15`, then `margin = max_bid − landed_cost`) by hand.
- **GPA note:** India is WTO-GPA observer only (Israel is a full party). Irrelevant
  under Model B because the Israeli prime holds the contract.

---

## 2. GEOGRAPHY — one network, two layers

| Location | Role |
|---|---|
| **Bangalore** | KritiKaal **HQ / management / operations** — not a factory cluster. |
| **Agra** | Factory cluster — footwear. |
| **Kanpur** | Factory cluster — SLGs (wallets, cardholders, key fobs, notebook covers). |
| **Kolkata** | Factory cluster — bags, garments. |

Bangalore manages production happening in the clusters, the same way
KritiKaal-as-intermediary manages production for its global brand clients.

---

## 3. VOICE & BRAND PERSONALITY

**Entity separation (hold both at all times):**
- **KritiKaal** — the operating firm. Managed Manufacturing, 300-3,000 unit bracket.
  Sells operational certainty, not product.
- **The Intel Agents** — KritiKaal's intelligence/content division. Monitors macro
  events (EUDR, tariffs, supply chain disruptions), translates into data-driven B2B
  video content. Speaks as analysts, not salespeople. Target viewer is always the
  business, never the consumer.

**Personality:** A senior operations and supply chain manager — authoritative,
pragmatic, transparent, data-driven. Calm confidence. We know what we're talking about.

**What we are:** Operational (units, timelines, defect rates, SLAs). Transparent.
Pragmatic. Partner-minded (extension of the client's ops team).

**What we are NOT:** A creative design agency. A cheap fast-fashion middleman.
A passive marketplace. Vague — we use specific numbers and verified commitments.

---

## 4. LANDED-COST LOGISTICS ENGINE (India → USA, B2C parcel)

> **Context:** Built for the Indore Leather Craft product line (animal showpieces,
> wall hangings, key holders, pen holders) — composite items with iron/steel
> skeleton + wood-wool body + leather covering. HTS 4205.00.80.00 (other articles
> of leather), MFN rate = 0% (Free). Most items FOB < $80.

### 4.1 Regulatory Framework (2026)

- **De Minimis eliminated** (Aug 29 2025) — every B2C parcel from India pays duty.
- `[VOLATILE]` **IEEPA tariffs struck down** by SCOTUS (Feb 20 2026). Replaced
  same day by **Section 122 of the Trade Act of 1974** — 10% global surcharge,
  effective Feb 24 2026, **HARD EXPIRY: Jul 23 2026.** After this date, search for
  the replacement regime before calculating any US duty.
- **Postal and courier pay the SAME duty** under Section 122: MFN + 10% = 10% of
  FOB for HTS 4205 goods. The old 50% postal "DDP rate" is dead (IEEPA artifact).

### 4.2 Two-Lane Shipping Architecture

**Postal lane (India Post EMS Merchandise, Zone C / USA):**
- Charges on **actual weight only** (no volumetric penalty).
- `[SEMI-STABLE]` EMS rate table — discrete non-linear slabs (last verified 2026-06-23,
  source: India Post Schedule of Rates 2025-26 via ClickPost, flagged indicative):

| Slab | Rate (INR) | Status |
|---|---|---|
| 0 – 500g | 1,290 | Verified (secondary source) |
| 501g – 1kg | 1,720 | Verified (secondary source) |
| 1 – 2kg | 2,580 | Verified (secondary source) |
| 2 – 5kg | 5,010 | Verified (secondary source) |
| 5 – 10kg | 8,800 | Verified (secondary source) |
| 10 – 20kg | 15,500 | Verified (secondary source) |
| 20 – 30kg | 25,200 | Verified (secondary source) |

- **GST on freight:** `[SEMI-STABLE]` 18% (9% CGST + 9% SGST) charged at counter.
  **Zeroed if exporter holds a Letter of Undertaking (LUT)** — registered exporters
  can file LUT annually for zero-rated export of services.
- **Volume discounts (India Post corporate):** Published tiers from 10% (₹50K/mo)
  to 30% (₹5Cr/mo) + up to 3% bonus for advance deposit. Not hardcoded in the
  calculator — configurable constant.
- **Duty:** `[VOLATILE]` Section 122 (10%) + `[STABLE]` MFN (0%) = **10% of FOB**
  (identical to courier). See §4.1 expiry warning.
- **Brokerage:** $0 (postal customs clearance, no broker fee).

**Courier lane (Shiprocket/DHL/FedEx):**
- Charges on **chargeable weight = MAX(actual, volumetric)**. Volumetric = L×W×H / 5000.
- `[STABLE]` **15% packing buffer** applied to raw item dimensions before volumetric
  calc (accounts for bubble wrap, outer carton). Configurable, overridable per item.
- `[VOLATILE]` Freight: ₹1,100/kg (estimate — replace with reseller quote), floor ₹1,449.
- GST: 18% on courier freight.
- **Duty:** Same as postal — `[VOLATILE]` Section 122 (10%) + `[STABLE]` MFN (0%).
- **Brokerage:** $15/parcel (courier disbursement fee).

**Structural verdict for Indore Leather Craft catalog:** Items are bulky and light
(e.g., 12" leather elephant: 0.8kg actual, 4.57kg volumetric packed). Postal wins
by ~3.5× because courier bills volumetric while postal bills actual.

### 4.3 Calculator Tool

Production-ready `.xlsx`: `3 - KritiKaal_Landed_Cost_Calculator.xlsx`.
Builder script: `build_calculator_v3.py` in workspace root.

**Architecture:**
- VLOOKUP-based discrete EMS rate table (7 slabs, rows 44-50).
- LUT toggle dropdown (B10): Yes = GST-exempt, No = 18% GST at counter.
- Postal and courier duty use **identical formula:** `(Section_122 + MFN) * FOB`.
- Weight cliff alert: warns when within 5% of slab boundary.
- Slab capacity display: shows free weight before next slab (bundling insight).
- Sheet-protected: partner edits Input Zone only; Admin/Output zones locked.
- Password: `kritikaal2026`.

### 4.4 Constants Reference (with volatility classification)

> **Last verified: 2026-06-23.** Before using these in any calculation, check the
> Session Start Validation Gate at the top of this document.

| Constant | Value | Cell | Volatility | Decay trigger |
|---|---|---|---|---|
| FX (INR/USD) | 86 | B29 | `[VOLATILE]` | Drifts daily. Web-search before any session that produces quotes. |
| Section 122 | 10% | B30 | `[VOLATILE]` | **HARD EXPIRY: Jul 23 2026.** Dead after that date. |
| MFN HTS 4205 | 0% (Free) | B31 | `[STABLE]` | Legislative change only. |
| MFN HTS 6809 | 0% (Free) | B32 | `[STABLE]` | Legislative change only. |
| Brokerage | $15 | B33 | `[SEMI-STABLE]` | Varies by broker/reseller. Verify per contract. |
| Courier ₹/kg | 1,100 | B34 | `[VOLATILE]` | **ESTIMATE — not a contracted rate.** Replace immediately with real reseller quote. |
| Courier floor | ₹1,449 | B35 | `[VOLATILE]` | Same as above — estimate. |
| Courier GST | 18% | B36 | `[SEMI-STABLE]` | Indian GST policy change. |
| Courier fuel | 0% | B37 | `[SEMI-STABLE]` | Carrier-specific. Update per contract. |
| Vol divisor | 5,000 | B38 | `[STABLE]` | Industry standard. |
| Packing buffer | 15% | B39 | `[STABLE]` | Product-line dependent. Override per SKU if measured. |
| Postal GST | 18% | B40 | `[SEMI-STABLE]` | Zeroed by LUT toggle. Base rate = Indian GST policy. |

---

## 5. WORKSPACE ARCHITECTURE (as of 2026-06-23)

### 5.1 Active directories

| Directory | Purpose |
|---|---|
| `C-core\` | Brand identity: `project-brief.md`, `voice-dna.md`, `icp-profile.md` |
| `mission-control\` | This manifest, SWAG/catalog docs, strategic missions, pipeline engines |
| `moat-engine\` | Demand validation engine (HIGH DEMAND + HIGH MOAT thesis) |
| `kritikaal-hub\` | Streamlit app (leads CRM, quotes, bridge) |
| `T-tools\` | Dashboard, procurement agent, leads pipeline, **`procurement_ingest.py`** (B2G tender pipeline) |
| `M-memory\` | Agent run logs, delta reports |
| `A-agents\` | Agent definitions (architect) |
| `B-brain\` | Tech stack docs |

### 5.2 Isolated directories (do not merge back without operator approval)

| Directory | Status | Contents |
|---|---|---|
| `_SIDE_VENTURE_AMAZON_FBA\` | **Active side-strategy** | FBA landed-cost calculator, tariff heatmap, channel comparison, sourcing engine, blended strategy optimizer, FBA compliance SOP |
| `_PAUSED_CONTENT_YOUTUBE_REDDIT\` | **Paused — in strategic pipeline** | YouTube ytinsights tool (full codebase), YouTube migration plan. To be reactivated on operator signal. |

### 5.3 Archived

| Directory | Status |
|---|---|
| `B-brain\05-research\supply-intelligence_ARCHIVE\` | Historical factory research. Reference only — not active planning. |

---

## 6. HARD RULES (violation = immediate correction)

1. **Demand-only:** Never propose supply-side automation, factory-finding features,
   or autonomous web-scale harvesting. KritiKaal manages existing factory
   relationships; it does not discover new ones through software.
2. **Thesis = defensibility, not luxury:** HIGH DEMAND + HIGH MOAT is the objective.
   "Premium" = moat mechanism (material quality), never brand positioning.
3. **Faire is blocked:** Do not re-propose Faire.com as a sales channel.
4. **Prospector = precision over recall:** `store_prospector.py` is a moat
   pre-filter (95% dropshipper rejection). Discovery is pluggable; never build
   autonomous web-scale harvester.
5. **Signals must aggregate across all runs:** In `exporter.py`, use
   `GROUP_CONCAT + MAX(confidence)`, never latest-run-only.
6. **No supply in leads.db:** leads.db is CORE-only, demand-only. Hybrid Premium
   gets its own mechanism when activated.
7. **MOQ is scoped, not global:** 300+ applies to CORE manufacturing only. See §1.3
   for bypass conditions. Never auto-reject a deal on MOQ grounds — flag and present
   the math to the operator.
8. **Stale numbers kill margins:** Never use a `[VOLATILE]` constant in a customer-facing
   quote without verifying it first. See Session Start Validation Gate.

---

## 7. DECISION LOG

| Date | Decision | Status |
|---|---|---|
| 2026-06-12 | Demand-only pivot — supply automation killed | PERMANENT |
| 2026-06-14 | Bangalore=HQ/Kanpur=factory resolved; leads.db CORE-only | RESOLVED |
| 2026-06-14 | Brand locked: "Alloy & Grain" / "The Vellum Collection" | RESOLVED |
| 2026-06-14 | Three-market framing (Israel/US/UK as primary) | RESOLVED |
| 2026-06-18 | Thesis = defensibility not luxury; Vector A = Shopify inventory-delta | RESOLVED |
| 2026-06-18 | Prospector = precision-over-recall; Particl/Charm/Grips demoted | RESOLVED |
| 2026-06-23 | GTM phasing locked: Phase 1 Israel → Phase 2 UK → Phase 3 USA | RESOLVED |
| 2026-06-23 | Landed-cost engine: EMS VLOOKUP table, 50% DDP killed, LUT toggle added | RESOLVED |
| 2026-06-23 | Workspace GC: 47K+ files purged, side-ventures isolated | RESOLVED |
| 2026-06-23 | Volatility tags, MOQ bypass rules, update protocol added | RESOLVED |
| 2026-06-23 | B2G Model B: Israeli ח.פ. (est. 2013) prime + India captive backend; domestic preference = absorbable cost delta (flat 15%), not a gate | RESOLVED |
| 2026-06-23 | B2G pipeline: mr.gov.il SSR scrape → keyword filter → analyst PDF enrichment → penalty scoring. data.gov.il/RSS rejected (archive/news). Tool: `T-tools/procurement_ingest.py` | RESOLVED |
| 2026-06-23 | v7.0: Major consolidation of all v6.x patches + B2G pipeline deployment | RESOLVED |

---

## 8. OPEN ITEMS

- [ ] Field-verify Kanpur routing for Seed-10 SLG items before first sample PO.
- [ ] Rename `THE_SWAG_UPGRADE_CATALOG.md` → "Alloy & Grain" naming.
- [ ] Update outward-facing materials to drop "Swag Upgrade" / "Hybrid Premium" codenames.
- [ ] Build product-agnostic Master Factory Compliance & QA Template for CORE B2B
      (the FBA-specific SOP was moved to `_SIDE_VENTURE_AMAZON_FBA`).
- [ ] Confirm EMS rates at India Post counter (secondary-source verified only).
- [ ] Negotiate India Post corporate volume discount — get real tier into constants.
- [ ] Monitor Section 122 expiry (Jul 23 2026) — duty rate will change.
- [ ] Replace courier ₹/kg estimate (B34/B35) with contracted reseller rate.
- [ ] B2G: Schedule `procurement_ingest.py ingest` as a daily Windows Task Scheduler job.
- [ ] B2G: Validate first live ingest against mr.gov.il — confirm Akamai passes, confirm
      DOM selectors parse correctly, confirm keyword filter precision on real data.

---

## 9. UPDATE PROTOCOL — Keeping This Document Alive

This document is the single source of truth. A static file that is never updated
becomes a liability. The following protocol governs how and when to version-bump.

### 9.1 When to Update (mandatory triggers)

| Trigger | Action | Priority |
|---|---|---|
| **Any `[VOLATILE]` constant changes** (FX shift >5%, tariff expiry/replacement, new carrier contract) | Update the constant value, the "Last verified" date in §4.4, and the Session Start gate date. Bump patch version (e.g., v6.1 → v6.2). | **IMMEDIATE** |
| **Strategic decision made** (new market entered, new product line, new hard rule) | Add to Decision Log (§7), update the relevant section, bump minor version (e.g., v6.2 → v7.0). | **Within 24 hours** |
| **AI session produces a reusable insight** (new compliance finding, market intel, validated pricing model) | Operator extracts the insight and integrates it into the relevant section. | **End of session** |
| **Open Item resolved** (§8) | Check it off, move any resulting data into the document body, bump patch version. | **When resolved** |
| **30 days since last verification date** | Run the Session Start Validation Gate manually. Verify all `[VOLATILE]` constants. Update "Last verified" date even if nothing changed. | **Scheduled** |

### 9.2 How to Update

1. **Never edit in the AI session directly** unless the operator explicitly instructs it.
   The AI should propose changes; the operator approves and applies.
2. **Version numbering:** `MAJOR.MINOR` — major = structural change (new section,
   removed section, thesis pivot); minor = data update (constant refresh, new decision,
   resolved open item).
3. **Change log:** Every version bump adds one row to the Decision Log (§7) with
   the date, what changed, and status.
4. **Distribution:** After any update, re-export the full document and replace it in
   all locations where it's stored (workspace file, pinned messages, external AI
   platforms).

### 9.3 The Round-Trip Workflow (session → manifest → session)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  AI SESSION      │     │  OPERATOR         │     │  MANIFEST v6.x  │
│  (any platform)  │────→│  reviews output   │────→│  updated & re-  │
│                  │     │  extracts insights │     │  exported        │
│  Produces:       │     │  applies updates   │     │                 │
│  - new intel     │     │  bumps version     │     │  Fed into next  │
│  - decisions     │     │                    │     │  AI session     │
│  - corrections   │     │                    │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**The operator is the gatekeeper.** AI sessions propose; the operator decides what
persists. This prevents context pollution while ensuring valuable insights survive
session boundaries.
