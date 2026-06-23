# KritiKaal Mission Control
# OSINT BI Hunting Playbook  ·  v1.0
*Doctrine of record for the Autonomous Radar (Mode B) discovery engine.*

---

## §0 — AIR GAP CODIFICATION  (READ FIRST. NEVER VIOLATE.)

This playbook governs **Mission Control** — a standalone Business Intelligence
discovery engine. Mission Control is structurally and operationally separate
from the **KritiKaal Command Center** (Leads Hunter · Quote Engine · CRM Bridge ·
Corporate Gifts catalog). These are two distinct entities with distinct purposes.

| | KritiKaal (Core Business) | Mission Control (BI Engine) |
|---|---|---|
| Purpose | Operate the managed leather manufacturing business | Hunt for new profitable B2B models to clone |
| State | Production-grade revenue operations | Strategic discovery — opportunity scouting |
| Data | `leads.db`, `quotes.db`, CG product YAMLs | `strategic_missions/` — generated protocols only |
| Codebase | `kritikaal-hub/` (Streamlit hub) | `mission-control/` (standalone Streamlit app) |
| Imports from each other | **NONE** | **NONE** |
| Shared paths in `nav.py` | **NONE** | **NONE** |
| When activated | Daily — this IS the business | Only during deliberate breaks from operating KritiKaal |

**Operating Rule:**
Mission Control is the tool we open when we step back from the factory floor —
not while we are running it. We do not blend datasets. We do not import strategy
from one into the other without a formal "transition gate" (a new product line
clone moving from BI hunt → KritiKaal operations only happens after a deliberate
strategic decision, not by accident or data leakage).

**Codified directive:**
> No code path in `mission-control/` reads from `kritikaal-hub/`.
> No code path in `kritikaal-hub/` reads from `mission-control/`.
> No shared imports. No shared databases. No shared `nav.py` constants.
> Two filesystems, one operator, two distinct mental modes.

---

## §1 — THE OSINT ARSENAL  (Free / Open Tools, Available Today)

Thirteen tool families. Every one is free or has a usable free tier.
Every one targets a different signal layer of a B2B business.

### 1.1  Google Dorks — The Free Apollo

Advanced Google operators surface buying behavior, pricing, supplier lists,
and operator identities that no surface search returns.

**Core dork patterns to deploy:**
```
# Find suppliers actively selling to Israeli buyers
site:linkedin.com/in "corporate gifts" "Israel" ("HR" OR "procurement")

# Find pricing pages incumbents forgot to no-index
site:co.il "מחיר" "מינימום הזמנה" intext:"מתנות לעובדים"

# Find Indian micro-manufacturers with English-facing pages
site:indiamart.com "leather" "manufacturer" "Bangalore" "OEM"

# Catch leaked RFP / tender response documents
"RFP" OR "RFQ" "corporate gifts" filetype:pdf site:gov.il

# Find Israeli company catalogs (price lists in PDF/XLS)
filetype:pdf "מחירון" "מתנות" site:co.il

# Surface review pages buried in subdomains
site:trustpilot.com "tel aviv" corporate gifts

# Find competitor's hiring posts (reveals tech stack + scale)
site:linkedin.com/jobs "logistics coordinator" "India" "Israel"
```

**Output to track:** Operator names, price points, RFP language, buyer titles,
admitted MOQs, lead times — all from public Google search results.

### 1.2  LinkedIn X-Ray Search  (No Login Required)

Bypass LinkedIn's login wall using Google's index of LinkedIn pages.

**X-Ray dork templates:**
```
site:linkedin.com/in "Head of People" "Israel" "tech"
site:linkedin.com/company "import" "Israel" "promotional"
site:linkedin.com/jobs "procurement manager" "Tel Aviv"

# Find decision makers by funding stage
site:linkedin.com/in "Office Manager" ("Series B" OR "Series C") "Israel"

# Reverse-find incumbents from their employees
site:linkedin.com/in "sales manager" "[suspected incumbent name]"
```

**Pro move:** Use `&num=100` URL parameter on Google to get 100 results per
page. Combine with `inurl:` to filter by LinkedIn page type. Save results
with a clipping tool (free: Web Scraper Chrome extension, Instant Data
Scraper).

### 1.3  B2B Directory Mining — The Operator Goldmine

| Directory | Geography | Free? | What to extract |
|---|---|---|---|
| **IndiaMART** | India | Yes | Indian micro-manufacturers, FOB price ranges, MOQs |
| **TradeIndia** | India | Yes | Indian exporters by HS code, contact details |
| **JustDial** | India | Yes | Local Indian B2B operators, phone numbers, services |
| **Exporters India** | India | Yes | Export-focused operators, target geographies |
| **Dun's 100** (`dnb.co.il`) | Israel | Limited free | Top 100 Israeli companies by sector, revenue bands |
| **B144 / 144** (`b144.co.il`) | Israel | Yes | Israeli yellow-pages-style B2B listings |
| **Zap Group** (`zap.co.il`) | Israel | Yes | Israeli vendor catalogs with price comparisons |
| **IsraelExporter** (`israelexporter.com`) | Israel | Yes | Israeli companies seeking export — reverse signal |
| **Companies Registrar Israel** (`ica.justice.gov.il`) | Israel | Yes | Registered companies, directors, status |
| **MCA21 (mca.gov.in)** | India | Yes | Indian Pvt Ltd filings, director DIN lookup |

**Hunting move:** Scrape category landing pages, build operator lists, then
cross-reference against LinkedIn X-Ray for headcount and recent activity.

### 1.4  Job Board Reverse Engineering — Tech Stack & Pain Points

Job postings are the most underrated BI signal in existence. A company's
hiring tells you exactly what they cannot do today.

**What to mine from job posts:**
- **Tech stack** ("experience with SAP" → no modern quote engine)
- **Pain points** ("must reduce 5-day quote turnaround" → they admit the lag)
- **Scale** (3 sales reps hired in 90 days → revenue is real)
- **Workflow** ("coordinate with Chinese suppliers" → no direct factory)
- **Buyer base** ("manage portfolio of 50+ Israeli tech clients")

**Sources:**
- LinkedIn Jobs (X-Ray as above)
- AllJobs.co.il, Drushim, JobMaster (Israeli)
- Naukri.com, Foundit, Internshala (Indian)
- AngelList / Wellfound (startup-scale tells)

### 1.5  Review Mining — The Blind Spot Detector

The Mode B prompt's R3 (Incumbent Blind Spot) is built from this.
**Negative reviews are the most concentrated source of operational vulnerability
data in existence.** Every 1-star review names a specific operational weakness.

**Review sources to mine:**
- **Google Maps reviews** (B2B vendors with physical presence)
- **Trustpilot** (filter by country)
- **G2 / Capterra** (for SaaS-adjacent service operators)
- **Glassdoor** (employee complaints reveal *internal* operational rot)
- **Reddit** (`r/Israel`, `r/IndianBusiness`, `r/sysadmin` for procurement pain)
- **Hebrew forums:** Tapuz, Whatsapp business groups, Facebook B2B groups

**Mining patterns:**
- Sort all reviews by lowest rating
- Tag every complaint by category: PRICE / LEAD TIME / QUALITY / SERVICE / MOQ / CUSTOMISATION
- The dominant complaint category IS the Blind Spot
- The repeated phrase IS the Domination Vector copy in your pitch

**Example:** If 14 of 20 negative reviews of an Israeli corporate gifting
incumbent mention "took 6 weeks for samples" — your domination vector is:
*"Samples in your hands within 14 days, or your sample fee is refunded."*

### 1.6  Import/Export Records — The Margin X-Ray

Public customs and trade data reveals what incumbents actually pay at the
border. This is the single most powerful tool for reconstructing competitor
unit economics.

**Free / freemium sources:**
| Source | Coverage | Free Access |
|---|---|---|
| **UN Comtrade** (`comtradeplus.un.org`) | Global, by HS code | Full free API |
| **Indian DGFT / Tradestat** | Indian imports/exports | Web search free |
| **Israel Customs (`tax.gov.il`)** | Israeli import statistics | Public bulletins |
| **ImportGenius** | US imports (proxy for global shippers) | 7-day free trial |
| **Volza** (`volza.com`) | Cross-border B2B trade | Limited free queries |
| **Panjiva** (now part of S&P) | Bill of lading data | Limited free |

**Hunting move:** Pull HS code 4202 (leather goods / cases) import volumes
into Israel by year. Identify importer names. Cross-reference importer
names against LinkedIn for org size. Estimate revenue from declared CIF
values × typical 2.2x markup.

### 1.7  Government Registries — Director & Filing Data

| Source | Country | Reveals |
|---|---|---|
| **ICA Registrar of Companies** (`ica.justice.gov.il`) | Israel | Company status, directors, founding date |
| **Rashut HaHevrot** | Israel | Annual filings (some free) |
| **MCA21** (`mca.gov.in`) | India | Indian Pvt Ltd filings, DIN, registered capital |
| **GST Portal** (`gst.gov.in`) | India | Active GST registrations — proves operational status |
| **Open Corporates** (`opencorporates.com`) | Global | Cross-jurisdictional company data |

**Hunting move:** Verify an operator is actually trading (not dormant) before
investing analysis time. Filter by recent filings, GST returns, address.

### 1.8  Tender / RFP Databases — What Corporates Actually Buy

Government and large-corporate tenders reveal exact line items, quantities,
prices, and incumbent winners.

**Sources:**
- **Mimshal.gov.il** (Israeli government tenders) — search by category
- **Central Public Procurement Portal** (`eprocure.gov.in`) — Indian govt tenders
- **GeM (Government e-Marketplace)** (India) — actual transaction data
- Corporate sustainability reports (procurement spend breakdowns)

**Hunting move:** Search past 24 months of awarded tenders. Note the
winning supplier, the award amount, the unit price. That's verified
willing-to-pay data.

### 1.9  Wayback Machine / Archive.org — Time-Series Intelligence

`web.archive.org` lets you see how a competitor's pricing, product range,
and positioning has evolved over 3–10 years.

**What it reveals:**
- Price trajectory (raising prices = pricing power; cutting = pressure)
- Product line expansion (which categories worked, which got dropped)
- Hiring page snapshots (headcount history)
- Catalog changes (what they added/removed and when)

### 1.10  Social Signal Mining — The Real-Time Layer

| Channel | Use |
|---|---|
| **Reddit** | Honest complaints, vendor recommendations, war stories |
| **Twitter / X** | Real-time procurement frustration, vendor callouts |
| **Hacker News** | B2B SaaS / tech procurement signals |
| **Facebook B2B Groups** (Hebrew) | Israeli HR/Ops/procurement groups |
| **WhatsApp business directory groups** | Direct WTB / WTS signals |
| **Telegram channels** (Israeli + Indian) | Trade-specific channels |
| **Product Hunt / BetaList** | Adjacent SaaS competitors emerging |

### 1.11  Tech Stack Fingerprinting — Operational Maturity Audit

Reveals whether an incumbent uses modern tooling or is operating on
spreadsheets and email.

| Tool | Free? | What it shows |
|---|---|---|
| **BuiltWith** (`builtwith.com`) | Limited free | Full tech stack of any domain |
| **Wappalyzer** (Chrome extension) | Free | Real-time tech detection |
| **SimilarWeb** (free tier) | Yes | Traffic volume + sources |
| **WHOIS / DomainTools** | Free | Domain age, registrar, ownership history |
| **Crt.sh** | Free | SSL certificate history (reveals subdomains) |

**Hunting move:** If an incumbent's site runs on WordPress + WooCommerce + a
generic contact form, they have zero quote automation. That's a Domination
Vector entry written for you.

### 1.12  Trade Show & Exhibitor List Mining

Companies that pay to exhibit are companies with budget AND intent.
Conference exhibitor lists are pre-qualified B2B lead lists.

**Sources:**
- **10times.com** — global event listings, exhibitor lists often free
- **eventseye.com** — trade show database
- Israeli industry associations (`leather.org.il` if it exists, similar)
- LinkedIn event pages

**Hunting move:** Pull exhibitor lists from 3 major Israeli HR/procurement/
corporate gifting trade shows over the last 24 months. That's a curated
list of active incumbents AND active buyers in one document.

### 1.13  Glassdoor + Payscale — Inside Operations

Employee-reported salary data lets you reconstruct an incumbent's cost
structure with surprising accuracy.

| Source | What it reveals |
|---|---|
| **Glassdoor** | Salaries, role counts, internal pain points (reviews) |
| **AmbitionBox** (India) | Indian company salary data |
| **Salary.com / Payscale Israel** | Israeli market rates |
| **LinkedIn Salary** (limited free) | Cross-validation |

**Hunting move:** Number of sales reps × average comp + estimated rent + estimated
inventory turn = rough OpEx. If their revenue (inferred from import volumes
× markup) exceeds OpEx by 3–5x, they're printing money on a clonable model.

---

## §2 — THE HUNTING METHODOLOGY:  THE 7-STAGE PROFIT-MODEL HUNT

A deterministic, repeatable cycle. Every Mode B radar scan runs this loop.
Each stage has a specific OSINT toolset, a specific output, and a specific
go/kill decision.

### Stage 1 — SIGNAL SCAN  (Cast Wide)

**Goal:** Surface 20–30 candidate B2B models worth investigating.

**Tools deployed:**
- Google Dorks (§1.1) for "Israel + B2B + [category]"
- B2B Directory category browsing (§1.3) — IndiaMART + B144
- Reddit / Facebook group scraping (§1.10) for vendor recommendation threads
- Trade show exhibitor lists (§1.12) — past 12 months

**Output:** A spreadsheet of 20–30 candidates with columns:
`model_hypothesis | geography | candidate_operators | first_signal_source`

**Kill rule:** Drop any candidate where signal is single-source (one mention).
Real money leaves multiple footprints.

### Stage 2 — CANDIDATE CAPTURE  (Identify Real Operators)

**Goal:** For each surviving candidate, name 2–4 actual operators.

**Tools deployed:**
- LinkedIn X-Ray (§1.2) for company pages
- Government registries (§1.7) to confirm trading status
- Wayback Machine (§1.9) to verify 24+ months of operation
- Tech stack fingerprinting (§1.11) for operational maturity baseline

**Output:** For each model, 2–4 named operators with:
`name | URL | headcount_band | founded | tech_stack | verified_trading`

**Kill rule:** Drop any model where we cannot name ≥2 operators with confirmed
trading status. Anonymous markets are theoretical markets.

### Stage 3 — VULNERABILITY MAP  (Find the Blind Spot)

**Goal:** For each operator, identify the specific structural weakness.

**Tools deployed:**
- Review mining (§1.5) — negative reviews categorized
- Job board reverse-engineering (§1.4) — admitted operational gaps
- Tech stack audit (§1.11) — automation gaps
- Glassdoor (§1.13) — internal operational complaints
- Wayback Machine (§1.9) — has the weakness persisted?

**Output:** Per operator, a Blind Spot Card:
`primary_weakness | evidence_count | customer_complaint_phrase | persistence_years`

**Kill rule:** Drop any candidate where the weakness is invisible to OSINT.
If the public web does not surface the vulnerability, we cannot weaponize
the pitch against it.

### Stage 4 — MARGIN RECONSTRUCTION  (Reverse-Engineer Unit Economics)

**Goal:** Estimate the incumbent's revenue, gross margin, and cost base.

**Tools deployed:**
- Import/export records (§1.6) — declared CIF value × inferred markup
- Glassdoor / AmbitionBox (§1.13) — headcount × salary = labor cost floor
- Tender data (§1.8) — actual contract values where public
- Tech stack (§1.11) — SaaS subscription costs estimable
- BuiltWith traffic data (§1.11) — visitor volume × conversion estimate

**Output:** A unit economics estimate:
`est_annual_revenue | est_GM% | est_OpEx | est_net_margin | confidence_HML`

**Kill rule:** Drop any candidate where the estimated net margin is below 15%.
We are hunting profit machines, not break-even operators.

### Stage 5 — CLONE FEASIBILITY  ($10K Math)

**Goal:** Determine if we can stand up an operational equivalent for ≤ $10K.

**Tools deployed:**
- IndiaMART / TradeIndia (§1.3) — Indian factory FOB pricing
- DGFT / Israel customs (§1.6) — duty & freight rates
- SaaS pricing pages — operational tool costs
- Quote Engine internal models — landed cost math

**Output:** The R5 Clone Blueprint table (from the Mode B prompt) — fully
populated, totaling ≤ $10,000.

**Kill rule:** If honest math exceeds $10K, even after stripping to MVP,
the candidate fails Filter 3. Reject it.

### Stage 6 — DOMINATION VECTOR LOCK  (Name Our Specific Edge)

**Goal:** State the ONE operational advantage that makes us structurally
superior, not just slightly cheaper.

**Tools deployed:**
- KritiKaal capability inventory (Bangalore factory, Quote Engine, logistics)
- Generic operational vectors (speed-to-quote, payment automation, SLA gating)
- Identified Blind Spot from Stage 3 — the vector must attack it directly

**Output:** A Domination Vector statement matching the Mode B R4 format —
specific, operational, with named tech / process / supply chain edge.

**Kill rule:** If the only edge we can name is "we'll be cheaper" or "we'll
try harder," reject. Hustle is not a moat.

### Stage 7 — KILL DECISION  (GO / REJECT)

**Goal:** Final score against the 4 Hard Filters. Surface only models that
PASS all 4. Generate the Mode B output for survivors.

**The 4 Hard Filters re-applied:**
1. Proven Revenue (Stage 4 confirmed, HIGH or MEDIUM confidence)
2. Structural Vulnerability (Stage 3 named, evidence cited)
3. Cloneability ≤ $10K (Stage 5 math holds)
4. Domination Path (Stage 6 locked)

**Output:** Top 3 survivors, fully written into the Mode B output format
(R1 through R8 + comparative ranking + Recommended First Move).

---

## §3 — COPY / IMPROVE / SCALE  —  OSINT DOCTRINE INTEGRATION

The framework is not just an output structure — it is a data-gathering
doctrine. Each phase of Copy/Improve/Scale maps to specific OSINT activities.
This is how the BI machine *thinks*.

### Phase 1 — COPY  ·  OSINT Translation: "Listen, Don't Innovate"

**Doctrine:** Reverse-engineer what is already winning. Never invent demand.
Never educate the market.

**OSINT activities for Phase 1:**
| Activity | Tool | Output |
|---|---|---|
| Identify who is currently winning | LinkedIn X-Ray, B2B directories, tenders | Operator list |
| Document their exact value proposition | Wayback Machine, current site, customer reviews | VP statement (verbatim) |
| Capture their pricing | Catalog PDFs (Google Dorks), tender data, review mentions | Price table |
| Map their sales motion | Job posts, social activity, hire patterns | Sales playbook outline |
| Identify their buyer persona | LinkedIn X-Ray of their employees' connections | ICP profile |

**Phase 1 Kill Rule:** If we cannot reproduce the incumbent's value proposition
in one sentence from public data, we don't understand the model. Don't proceed.

### Phase 2 — IMPROVE  ·  OSINT Translation: "Find the Crack, Drive the Wedge"

**Doctrine:** Locate the incumbent's structural blind spot. Inject our
specific operational superiority into that gap.

**OSINT activities for Phase 2:**
| Activity | Tool | Output |
|---|---|---|
| Surface every customer complaint | Trustpilot, Google Reviews, Reddit, Glassdoor | Complaint frequency map |
| Identify what they cannot physically do | Tech stack audit, hiring gaps, factory geography | Capability gap list |
| Reconstruct their unit economics | Import data, Glassdoor, traffic estimates | Margin model |
| Find the constraint they cannot fix | Multi-year Wayback comparison — has the gap persisted? | Persistence proof |
| Define our wedge | Match identified gap to KritiKaal capability OR new cheap stack | Domination Vector |

**Phase 2 Kill Rule:** If the same customer complaint appears for 3+ years
in reviews, the incumbent cannot or will not fix it. That is a confirmed
wedge. If complaints have disappeared, the wedge has closed. Move on.

### Phase 3 — SCALE  ·  OSINT Translation: "Velocity From Day Zero"

**Doctrine:** Deploy technological and operational leverage to close deals
at a velocity incumbents cannot match. Convert one-offs to recurring.

**OSINT activities for Phase 3:**
| Activity | Tool | Output |
|---|---|---|
| Map the buyer's annual purchase calendar | Tender history, social posts, calendar mining | Cyclical buy moments |
| Identify what makes accounts expand | Press releases, LinkedIn announcements, funding events | Trigger events list |
| Surface adjacent product categories | What else do these buyers post about buying? | Cross-sell map |
| Find the referral mechanic | Who currently refers business to incumbents? | Network entry points |
| Detect subscription / retainer signals | Job posts mentioning "client portfolio management" | MRR opportunity score |

**Phase 3 Kill Rule:** If we cannot identify a clear path from one-off
transaction → recurring revenue, the model only scales by hiring more sales
people. That's a job, not a leverage business.

---

## §4 — OPERATING CADENCE  (When This Machine Runs)

**Mission Control is a deliberate, scheduled activity — not an ambient process.**

| State | When | Mode |
|---|---|---|
| **KritiKaal Operations Day** | Mon–Fri operating hours | Hub only. Mission Control closed. |
| **Mission Control Session** | Pre-scheduled "BI block" (suggested: Fri afternoon, weekly or biweekly) | Hub closed. Mission Control open. |
| **Discovery Sprint** | Dedicated half-day or full-day | Multiple Mode A + B scans run in sequence |
| **Transition Gate** | When a discovered model graduates to operations | Documented decision, then ported into hub catalog |

**Why this matters:** Switching between operating mode (executing quotes,
chasing leads, manufacturing) and discovery mode (open-ended hunting) is
cognitively expensive. Doing both simultaneously degrades both. Mission
Control's value depends on it being a focused activity, not a constant
distraction during KritiKaal operations.

**Rule:** Mission Control opens when KritiKaal closes for the day.

---

## §5 — THE OSINT-TO-OUTPUT TRACE  (Audit Layer)

Every Mode B output cell must be traceable to a specific OSINT source.
This is the anti-fabrication enforcement layer.

**Required trace metadata per R2 (Proof of Life) cell:**
- `operator_name` ← source URL
- `pricing_evidence` ← URL or "INFERRED FROM [source]"
- `revenue_signal` ← specific OSINT artifact (job count, import volume, etc.)
- `confidence_rating` ← HIGH / MEDIUM / LOW
- `last_verified` ← date the source was checked

**If a cell cannot be traced, it is marked: `UNKNOWN — REQUIRES FIELD VERIFICATION`.
Never fabricate.**

This trace requirement is the operational backbone of the entire BI engine.
Without it, Mode B becomes elegant hallucination at speed. With it, every
recommendation rests on observable public evidence.

---

## §6 — TOOLS TO ADD WHEN BUDGET ALLOWS  (Future State)

Listed here only so we know what we are deliberately *not* doing today.

| Tier | Tool | Adds |
|---|---|---|
| 1 | Apollo.io API | Verified operator contacts + revenue bands |
| 1 | LinkedIn Sales Nav | Decision-maker targeting |
| 2 | Crunchbase Pro | Israeli tech funding signals |
| 2 | SimilarWeb API | Traffic & buyer-intent telemetry |
| 3 | Hunter.io | Email verification for outreach |
| 3 | Indian MCA21 paid | Hard financial filings |

**Until then:** §1's 13-tool free arsenal is the entire toolkit. We stretch
it ruthlessly before we spend a dollar on data.

---

## §7 — DOCTRINE PRINCIPLES  (The Five Laws)

1. **Follow the money, not the brief.** No sector list. No category bias.
   If the best opportunity is a B2B compliance facilitation desk in Mumbai
   selling to Israeli importers, surface it.

2. **Public evidence or it doesn't exist.** Every claim traces to an OSINT
   source. Unverifiable claims are marked UNKNOWN, never inferred into existence.

3. **The complaint is the blueprint.** Every dominant customer complaint is
   a domination vector waiting to be operationalized. Mine reviews like ore.

4. **$10K or kill it.** No model survives that cannot be launched for ≤ $10K.
   Capital efficiency is the third filter for a reason — it is what makes
   the engine actually deployable, not theoretically interesting.

5. **Air gap or rot.** Mission Control never imports from, writes to, or
   shares state with KritiKaal. The day they merge is the day both degrade.

---

*End of Playbook v1.0.*
*Stored at: `mission-control/BI_HUNTING_PLAYBOOK.md`*
*Authored: 2026-05-28*
