# KritiKaal Business Roadmap & Strategic Goals
# Prepared by Adam (COO) | 2026-05-12
# Status: DRAFT — Pending CEO Review and Approval
# Purpose: Baseline verification before multi-agent strategic brainstorm

---

> **Instructions to CEO:**
> This document maps exactly what has been built, what is pending, and what the confirmed
> business goals are — based solely on documented decisions, completed work, and active
> briefings on record. No recommendations are included.
>
> Please review each section for accuracy. Mark any item that is incorrect, outdated, or
> missing. Once you confirm this baseline is 100% accurate, the multi-agent brainstorm
> session will be authorised to run against it.

---

## SECTION 1 — BUSINESS GOALS (Confirmed)

### 1.1 Company Identity

**Entity:** KritiKaal — UK's managed leather manufacturing partner in India.

**Business model:** End-to-end production management for leather goods brands. KritiKaal is not a sourcing agency. KritiKaal owns the manufacturing outcome from specification locking to port delivery.

**Canonical differentiator (locked 2026-04-20):**
> "A traditional Sourcing Agent makes an introduction to a cheap factory, takes a commission, and disappears when quality issues arise. KritiKaal (Managed Manufacturing) acts as your on-the-ground extension in India. We take end-to-end accountability, embed our own rigorous QC (AQL 2.5), ensure LWG compliance, and guarantee the delivery. We don't just find factories; we manage the risk."

---

### 1.2 Primary Market

| Dimension | Confirmed Detail |
|-----------|-----------------|
| **Geography served** | United Kingdom (primary), European Union, United States, Australia |
| **Buyer type** | B2B only — brand founders, heads of product, procurement leads, operations directors |
| **Order bracket** | 300–3,000 units per production run (The Missing Middle) |
| **Sector** | Leather goods: bags, wallets, belts, small leather goods, accessories |
| **Excluded** | Retail consumers, hobbyists, Etsy sellers, DIY makers, fast-fashion volume buyers, price-only buyers |

---

### 1.3 Quality & Compliance Standards

| Standard | Detail |
|----------|--------|
| **AQL 2.5** | Final inspection across 8 criteria on every production run. The standard used by LVMH and Hermès supply chains. |
| **LWG** | Leather Working Group — tannery-level environmental and material traceability |
| **SA8000 / BSCI / SEDEX SMETA 4-Pillar** | Social accountability and labour compliance |
| **EUDR** | EU Deforestation Regulation — full due diligence statement preparation and supply chain traceability |
| **REACH** | European chemical safety compliance for all leathers and hardware |

---

### 1.4 Manufacturing Clusters Operated

| Cluster | Profile |
|---------|---------|
| Chennai, Tamil Nadu | Speed-optimised. 40+ years European export experience. LWG-certified tanneries. 2–5 day prototype turnaround. |
| Calcutta Leather Complex, West Bengal | Certification-optimised. LWG-recognised cluster. Preferred for EU/UK compliance documentation. |
| Kanpur, Uttar Pradesh | High-volume full-grain leather goods. Largest domestic buffalo hide supply concentration. |
| Agra, Uttar Pradesh | Heritage artisan production. Premium small leather goods, hand-stitched accessories. |

---

### 1.5 Financial Goals (Confirmed — Locked 2026-04-17)

| Model Variable | Confirmed Value |
|----------------|----------------|
| **Financial target** | $1,000,000 gross profit (NOT gross revenue) |
| **Gross margin** | 22% baseline |
| **Required gross revenue** | $4.54M at 22% margin |
| **Average deal value (AOV)** | $5,000 per transaction |
| **Transaction model** | Per-order (not retainer — clients order on-demand) |
| **Orders required** | 909 orders/year (~76/month) at $5K AOV and 22% margin |
| **Ideal-state path** | $20K AOV × 35% margin × 143 orders/year = $1M profit from 24 active clients |

**The four paths to $1M profit:**

| Path | AOV | Margin | Revenue Required | Orders/Year | Active Clients (6×/yr reorder) |
|------|-----|--------|-----------------|-------------|-------------------------------|
| Volume play | $5K | 22% | $4.54M | 909 | 152 |
| AOV uplift | $10K | 22% | $4.54M | 454 | 76 |
| Margin + AOV | $15K | 30% | $3.33M | 222 | 37 |
| Ideal state | $20K | 35% | $2.86M | 143 | 24 |

---

### 1.6 Strategic Context

- **China Plus One:** The primary macro tailwind. UK/EU brands migrating leather production from China to India due to Section 301 equivalents, EUDR risk profile differences, and supply chain concentration risk.
- **EUDR enforcement:** EU Deforestation Regulation enforcement (December 2025 for large companies, June 2026 for SMEs). India-origin leather carries materially lower EUDR risk than Chinese-routed South American hide chains.
- **UK DCTS:** India-origin goods receive preferential UK import duty rates vs. China MFN rates.
- **UK-India FTA:** In active negotiation — directional improvement toward zero duty.

---

## SECTION 2 — COMPLETED WORK

### 2.1 Intelligence & Operational Infrastructure

| System | Status | Detail |
|--------|--------|--------|
| **The System v8** | ✅ Live | Full folder architecture: C-core, M-memory, A-agents, T-tools, B-brain |
| **CLAUDE.md** | ✅ Live | Session protocol — all agents auto-load context on session start |
| **Agent team defined** | ✅ Live | Adam (COO), Copywriter, Gatekeeper, Researcher, Analyst, Strategist, Devil's Advocate, Chief of Staff, Tom |
| **Voice DNA** | ✅ Live | Entity separation (KritiKaal vs The Intel Agents), brand personality, communication patterns, banned language |
| **ICP profile** | ✅ Documented | B2B brand founders, procurement leads, ops directors — UK/EU focus |
| **Decisions log** | ✅ Active | All major strategic decisions on record with rationale |

---

### 2.2 Intel Pipeline (Automated Intelligence System)

| Component | Status | Detail |
|-----------|--------|--------|
| **intel_core.py** | ✅ Built | Shared SQLite database (intel.db), 8 intel clusters defined, full item lifecycle (pending → approved/rejected) |
| **rss_poller.py** | ✅ Built | RSS feed monitoring for trade/regulatory sources |
| **reddit_intel.py** | ✅ Built | PRAW-based Reddit monitoring — 3 hobby subreddits removed, 3 B2B subreddits added (procurement, ecommerce, UKBusiness) |
| **llm_filter.py** | ✅ Built | Claude-powered relevance scoring with dynamic model resolution |
| **doc_ingestor.py** | ✅ Built | Phase 1 document ingestor — PDF/TXT/MD/URL, chunking, circuit breakers |
| **generate_script.py** | ✅ Built | Intel-enriched Stage 4 script brief generator — reads approved intel, injects into Claude Sonnet prompt |
| **Phase 1 cold-start** | ✅ Complete | 5 AI Knowledge Synthesis Briefs generated and ingested (45 qualifying intel items): EUDR compliance mechanics, UK DCTS duty mechanics, China Plus One tariff arbitrage, QC failure patterns, Sourcing agent betrayal patterns |
| **NotebookLM notebook** | ✅ Live | "Reddit - Master Plan" (ID: e250d043-deb0-4e13-ae5e-6f56286e7e7d) — tactical Reddit engagement rules loaded |

---

### 2.3 Website — Completed

| Task | Status | Evidence |
|------|--------|----------|
| **Website live** | ✅ | kritikaal.com — Next.js, deployed |
| **Blog section** | ✅ | `/blog/` route and dynamic `/blog/[slug]/` routing confirmed |
| **EUDR article published** | ✅ | `kritikaal.com/blog/eudr-india-leather-uk-brands/` — HTTP 200 |
| **FAQ page — 29 Q&A live** | ✅ | `kritikaal.com/faq/` — full Q&A set confirmed |
| **FAQPage JSON-LD (T05a)** | ✅ | Confirmed in source code and live via curl — 29 questions in schema |
| **robots.txt — partial** | ⚠️ | Live. GPTBot, ClaudeBot, PerplexityBot, Googlebot present. **Missing 3 agents.** |
| **llms.txt — wrong version** | ⚠️ | Live but deployed with earlier draft, not the approved v2-FINAL |

---

### 2.4 Strategic Documents Produced

| Document | Location | Status |
|----------|----------|--------|
| Phase 2 Demand-Side Blueprint | `B-brain/06-growth/00-phase-2-blueprint-geo-seo.md` | ✅ Approved 2026-04-20 |
| Developer Brief V1.0 | `B-brain/06-growth/technical/DEVELOPER-BRIEF-2026-04-26.md` | ✅ Issued |
| Remediation Brief V1.1 | `B-brain/06-growth/technical/REMEDIATION-BRIEF-V1.1.md` | ✅ Issued 2026-05-12 |
| Schema JSON-LD (Homepage) | `B-brain/06-growth/technical/schema-jsonld-DEVELOPER-READY.html` | ✅ Ready — not yet deployed |
| FAQPage JSON-LD | `B-brain/06-growth/technical/faq-jsonld-DEVELOPER-READY.html` | ✅ Deployed |
| robots.txt spec | `B-brain/06-growth/technical/robots-txt-DEVELOPER-READY.md` | ✅ Approved — partially deployed |
| llms.txt v2-FINAL | `B-brain/06-growth/technical/llms-txt-v2-FINAL.md` | ✅ Ready — not yet deployed |
| FAQ content | `B-brain/06-growth/content/FOR-DEVELOPER/faq-PUBLICATION-READY.md` | ✅ Live |
| EUDR article | `B-brain/06-growth/content/FOR-DEVELOPER/article-01-eudr-india-leather-PUBLICATION-READY.md` | ✅ Live |

---

## SECTION 3 — PENDING WORK

### 3.1 Developer Remediation (Briefed — Awaiting Execution)

Remediation Brief V1.1 issued 2026-05-12. Developer has copy-pasteable code for all items below.

| Task | Description | Priority |
|------|-------------|----------|
| **T05 — Homepage JSON-LD** | Organization, Service, Person schema blocks not deployed in `app/layout.tsx`. Highest-value GEO asset still missing. | CRITICAL |
| **T01 — robots.txt gaps** | `Googlebot-Extended`, `anthropic-ai`, `CCBot` missing. `Googlebot-Extended` is Gemini's AI Overviews indexer. | HIGH |
| **T02 — llms.txt version** | Live file is an earlier draft. Approved v2-FINAL with AQL criteria, founder bio, and EUDR article URL not deployed. | HIGH |
| **T09 — AQL 2.5 text** | "World-Class Quality" text still appears twice on `/why-india`. Replace with "AQL 2.5 Inspection Standard". | MEDIUM |
| **FAQ title bug** | `"FAQ — Leather Manufacturing from India \| KRITIKAAL \| KRITIKAAL"` — double suffix in `app/faq/page.tsx`. | LOW |
| **T06 — MOQ removal** | Cannot verify server-side — requires manual browser check of 5 product cards. | VERIFY |
| **T07 — Table headers** | Cannot verify server-side — requires manual browser check of `/why-india` comparison table. | VERIFY |
| **T08 — Timezone** | Cannot verify server-side — requires incognito check of `/bookacall` calendar timezone. | VERIFY |
| **T09b — UTM analytics** | URLs resolve (200). GA4 passthrough on booking conversion not confirmed. Requires test booking. | VERIFY |

---

### 3.2 AWS CRM + Lead Generation Integration

| Item | Status |
|------|--------|
| **Custom CRM deployment** | Pending — to be deployed on AWS |
| **Lead generation system linkage** | Pending — existing lead-gen system to be connected to the deployed CRM |
| **Specs / architecture** | To be defined |
| **Dependencies** | AWS environment, CRM application code, lead-gen system API/webhook details |

---

### 3.3 Reddit Execution Phase

| Item | Status |
|------|--------|
| **Reddit API credentials** | Pending — Yossi to create app at `reddit.com/prefs/apps`, obtain `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` |
| **reddit_intel.py activation** | Blocked by credentials — code is built and ready |
| **Windows Task Scheduler — 5 tasks** | Architecture designed, not configured. Requires: rss_poller (06:00), llm_filter (06:45), reddit_intel (06:05), doc_ingestor, manual review workflow |
| **Reddit content creation** | Not started — awaiting pipeline activation and credential setup |
| **Reddit posting execution** | Not started |

---

### 3.4 Intel Pipeline Phase 2 (Continuous Expert Maintenance)

| Item | Status |
|------|--------|
| **Windows Task Scheduler setup** | 5 tasks designed, not yet created in Windows Task Scheduler |
| **Reddit subreddit monitoring** | Code ready, credentials pending |
| **RSS feed monitoring** | Code ready, cron scheduling pending |
| **LLM filter daily batch** | Code ready, scheduling pending |
| **Phase 2 ongoing intel flow** | All blocked by Task Scheduler setup and Reddit credentials |

---

### 3.5 Supply Side (Factory Bench)

| Item | Status |
|------|--------|
| **Qualified factory bench** | Currently zero. Trimurthi Lederwaren eliminated (2026-04-19). No replacement factory qualified. |
| **Factory qualification playbook** | Flagged as prerequisite in decisions.md — not built |
| **Golden sample orders** | None placed — supply bench not established |

---

### 3.6 Priority 3 Developer Tasks (Month 1 — Not Started)

| Task | Status | Blocker |
|------|--------|---------|
| T10 — reddit-monitor.py with cron | Not started | Reddit API credentials from Yossi |
| T11 — linkedin-monitor.py with Google Alerts RSS | Not started | Google Alerts RSS URLs from Yossi |
| T12 — Server environment variables | Not started | Credentials from Yossi |

---

## SECTION 4 — MASTER STATUS MATRIX

| Domain | Status |
|--------|--------|
| **Business identity & positioning** | ✅ Locked |
| **Financial model** | ✅ Locked |
| **Target market definition** | ✅ Locked |
| **Intelligence infrastructure** | ✅ Built — Phase 2 automation pending |
| **Website — core pages** | ✅ Live |
| **Website — SEO schema** | ⚠️ Partial (FAQ ✅, Homepage ❌) |
| **Website — GEO infrastructure** | ⚠️ Partial (llms.txt wrong version, robots.txt incomplete) |
| **Website — content** | ✅ EUDR article live, FAQ live |
| **Developer remediation** | ⏳ Brief issued — execution pending |
| **CRM + lead generation** | ❌ Not started |
| **Reddit execution** | ❌ Not started (credentials pending) |
| **Factory bench (supply side)** | ❌ Zero qualified factories |
| **Client pipeline** | ❌ No active clients on record |

---

## SECTION 5 — OPEN DEPENDENCIES (CEO ACTION REQUIRED)

The following items are blocked pending input or action from Yossi (CEO):

| Item | Required Action | Blocks |
|------|----------------|--------|
| Reddit API credentials | Create app at reddit.com/prefs/apps → provide `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` | Reddit intel pipeline, T10 server script |
| Google Alerts RSS URLs | Create 7 Google Alerts → provide RSS feed URLs to developer | T11 LinkedIn monitor |
| GPTZero API key | Subscribe at gptzero.me/api ($10/mo) → provide key | T12 environment variables |
| AWS CRM specs | Define CRM architecture, application code, and lead-gen integration requirements | 3.2 CRM deployment |
| Factory qualification playbook | Initiate supply-side factory bench rebuild | Supply side, all client delivery |

---

*KritiKaal Business Roadmap V1.0 | 2026-05-12 | Prepared by Adam (COO)*
*Status: AWAITING CEO REVIEW AND APPROVAL*
*Next action: Upon approval — multi-agent strategic brainstorm authorised*
