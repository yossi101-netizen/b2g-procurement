# KritiKaal — Master Plan
# ABC-TOM v8 Single Source of Truth

**Version:** 1.0
**Created:** 2026-04-20
**Owner:** Yossi (CEO / Founder) + Adam (COO / System Operator)
**Status:** LIVE — updated at each phase gate

> This file is the north star of the entire KritiKaal AI system. When in doubt about direction, priorities, or what was decided — read this first. Everything else in the system is a subordinate document.

---

## SECTION 1 — THE ARCHITECTURE OF $1M PROFIT

### The Business Model in One Sentence

KritiKaal connects premium UK and European fashion brands to a curated, fully audited, production-grade supply chain in India — charging a margin on the manufacturing spread and a management premium for the compliance, quality, and relationship layer that brand sourcing teams cannot build themselves.

This is **Managed Manufacturing**. Not a trading house. Not a freight forwarder. Not a factory agent. A managed service that owns the supply relationship on behalf of the client brand.

---

### The $1M Financial Target — Corrected Model

**Critical clarification (logged 2026-04-17):** The $1,000,000 annual goal is $1M in GROSS PROFIT — not top-line sales revenue.

| Input | Value |
|-------|-------|
| Gross profit target | $1,000,000 |
| Average gross margin (Phase 1 baseline) | 22% |
| Required gross revenue at 22% margin | $4.54M |
| Average Order Value (confirmed, per transaction) | $5,000 |
| Required transactions at $5K AOV | 909/year (~76/month) |

**This is hard.** 76 transactions per month at $5K is a volume game. The leverage points are:

| Strategic Lever | Effect |
|----------------|--------|
| Raise AOV → $10K | Cuts required orders in half (454/year) |
| Raise margin → 30% | Requires only $3.33M revenue |
| Anchor clients ($50K–$100K/year deal volume) | 20–40 clients replaces 909 transactions |

**The Planning Default (Combined Mid Scenario):**

| Parameter | Value |
|-----------|-------|
| Target AOV | $10,000 |
| Target margin | 30% |
| Required revenue | $3.33M |
| Required orders/year | 333 (~28/month) |
| Active clients needed (6 orders/yr avg) | ~56 |

**The Ideal State (Anchor-Tier Dominance):**

| Parameter | Value |
|-----------|-------|
| Target AOV | $20,000 |
| Target margin | 35% |
| Required revenue | $2.86M |
| Required orders/year | 143 (~12/month) |
| Active clients needed (6 orders/yr avg) | ~24 |

**Strategic implication:** KritiKaal cannot grind its way to $1M profit at $5K AOV without enormous volume infrastructure. The fastest path is Anchor-tier clients (£50K–£150K annual deal volume each), a margin expansion strategy (LWG-certified factories enable premium pricing), and AOV growth (broader SKU coverage per client per order).

---

### The Managed Manufacturing Model — How Margin Works

```
CLIENT BRAND pays KritiKaal: £X per unit (UK market rate)
         ↓
KritiKaal pays FACTORY: £Y per unit (India ex-factory FOB)
         ↓
KritiKaal MARGIN: £X - £Y - logistics - QC overhead
         ↓
TARGET GROSS MARGIN: 22% (floor) → 30%+ (target) → 35% (Anchor tier)
```

**What justifies the margin:**
1. Factory qualification, audit management, and certification maintenance
2. QC oversight and golden sample approval (AQL 2.5 standard)
3. Compliance documentation chain from raw hide to finished goods
4. Relationship capital — multi-year factory agreements, priority production slots
5. Risk absorption — KritiKaal absorbs factory failure risk on behalf of client brands

---

## SECTION 2 — SYSTEM INVENTORY (THE BUILD)

### What Has Been Built and Written to Disk

#### C-CORE — The Rules Layer (Brand DNA)

| File | Status | Contents |
|------|--------|----------|
| `C-core/project-brief.md` | LIVE | KritiKaal service definition, ICP summary, Phase 1 scope |
| `C-core/icp-profile.md` | LIVE | Ideal Client Profile — UK leather brands, revenue thresholds, buying signals |
| `C-core/voice-dna.md` | LIVE — PARTIAL | Brand voice framework. **BOTTLENECK: no real writing samples loaded. Voice is defined but not calibrated.** |
| `C-core/00-master-context.md` | LIVE | Two-layer context file: brief summary + deep detail for agent sessions |

#### B-BRAIN — The Intelligence Layer (Research & Memory)

| File | Status | Contents |
|------|--------|----------|
| `B-brain/00-MASTER-strategy.md` | LIVE | Central business reference — AOV, margin model, service definition, Phase 1 scope |
| `B-brain/00-MASTER-PLAN.md` | LIVE — THIS FILE | Single Source of Truth. System inventory, roadmap, operating model |
| `B-brain/01-about-me.md` | LIVE | Founder profile — background, credibility, personal context |
| `B-brain/05-research/global-hunting-playbook-uk.md` | LIVE | UK Demand-Side Research Playbook — methodology, vectors, scoring logic |
| `B-brain/05-research/demand-intelligence/week-01-directional-report.md` | LIVE | Week 1 UK brand sweep — 38 brands identified, initial scoring |
| `B-brain/05-research/demand-intelligence/week-02-intelligence-report.md` | LIVE | Week 2 manufacturing verification, COGS extraction, 3-play framework, 5 decision-maker contacts |
| `B-brain/05-research/demand-intelligence/uk-pipeline/00-master-pipeline.md` | LIVE | 47 brands. Anchor/Core/Ethical tiers. 3-play framework. Week 3 actions defined. |
| `B-brain/05-research/demand-intelligence/prospect-dossiers-sprint-01.md` | LIVE | Sprint 01 Israeli brand dossiers |
| `B-brain/05-research/demand-intelligence/sprint-01-strategist-synthesis.md` | LIVE | Sprint 01 strategic synthesis — Israeli market conclusions |
| `B-brain/05-research/supply-intelligence/india-factory-longlist.md` | LIVE | Desktop scoring matrix. 11 factories scored. Geographic pivot: CLC Kolkata > Kanpur for finished goods. |
| `B-brain/05-research/supply-intelligence/00-master-factory-bench.md` | LIVE | **Master Factory Bench v1.0.** Track A (5 TN factories) + Track B (3 Kolkata Elite). Absolute Criteria Rule. 21-Day Test protocol. |
| `B-brain/05-research/supply-intelligence/trimurthi-factory-brief.md` | HISTORICAL ONLY | Sprint 01 POC factory. Eliminated from cold outreach. Track A Founder access only. Do not use operationally. |
| `M-memory/decisions.md` | LIVE | 4 active strategic decisions with full context and rationale |
| `M-memory/learning-log.md` | EXISTS — sparse | Needs updating post-Sprint 01 and UK sweep |
| `M-memory/feedback.md` | EXISTS — empty | No client or market feedback logged yet (pre-revenue) |

#### A-AGENTS — The Personas Layer (AI Roles)

| Agent | Status | Role |
|-------|--------|------|
| `A-agents/adam-agent.md` | LIVE | COO — system operator, project manager, workflow director |
| `A-agents/researcher-agent.md` | LIVE | Market intelligence, web research, competitor analysis |
| `A-agents/analyst-agent.md` | LIVE | Structured data analysis, financial modelling, scoring |
| `A-agents/strategist-agent.md` | LIVE | Business strategy, go-to-market, positioning analysis |
| `A-agents/copywriter-agent.md` | LIVE — **UNDERUTILISED** | Content creation. **Blocked by Voice DNA calibration gap.** |
| `A-agents/gatekeeper-agent.md` | LIVE | Quality review, consistency enforcement before publish |
| `A-agents/devils-advocate-agent.md` | LIVE | Assumption challenge, blind spot identification |
| `A-agents/chief-of-staff-agent.md` | LIVE | Multi-perspective synthesis, executive decision briefs |
| `A-agents/tom-agent.md` | LIVE | System guide — explains ABC-TOM framework and folder structure |

#### T-TOOLS — The Skills Layer (Executable Processes)

| Category | Count | Key Tools |
|----------|-------|-----------|
| Skills (`01-skills/`) | 16 | Social post, blog post, sales proposal, web research, revenue roadmap, strategic decision, case study, newsletter, meeting notes, PRD, professional email, research briefing, stakeholder update, document summary, Hebrew writing, adam-coo |
| Prompts (`02-prompts/`) | 12 (×3 tracks) | Content / Sales / Thinking tracks — each with learn, style, create, close-the-loop |
| Workflows (`03-workflows/`) | 4 | Content, Sales, Thinking-Decision, Thinking-Summary |
| Bonus prompts | 9 | Calendar, hooks, competitor analysis, API keys, agent creator |

#### O-OUTPUT — The Deliverables Layer

| Folder | Status | Contents |
|--------|--------|----------|
| `O-output/01-decision-master-strategy/` | LIVE | Full thinking-track output: Strategist analysis, Devil's Advocate review, Gatekeeper review, Chief of Staff brief, Final decision brief |

---

## SECTION 3 — STATUS LEDGER: LIVE vs. PENDING

### LIVE — Operational and Complete

| Workstream | What's Done | Quality |
|------------|-------------|---------|
| **UK Demand Intelligence** | 47 brands identified and scored. 3-play framework built. 5 decision-maker contacts mapped. COGS savings argument built (Aspinal: £2.31M). Week 3 actions defined. | Production-grade |
| **Supply-Side Factory Bench** | 8 factories advancing (5 Track A TN, 3 Track B Kolkata). Absolute Criteria Rule applied. Desktop scoring complete. 21-Day Test protocol ready. Standard Brief v1.0 drafted (pending Founder approval). | Production-grade |
| **Financial Model** | $1M = gross profit. 22% floor margin. $5K AOV baseline. Planning default: Combined Mid ($10K, 30%). Profit path matrix built. | Locked — do not re-debate |
| **Partner Stack Model** | Tier 1 (2–3 named), Tier 2 (1–2 backup), Tier 3 (sampling). Replaces "15+ surveyed factories" approach. | Architecture locked |
| **Decisions Log** | 4 active strategic decisions logged with full rationale and context | Current |
| **Agent Team** | 9 agents defined and operational | Operational |

### PENDING — Not Yet Executed

| Workstream | What's Missing | Blocking Factor | Priority |
|------------|---------------|-----------------|----------|
| **Standard Brief Dispatch (21-Day Test)** | Founder approval of technical spec, then dispatch | Founder must approve leather thickness, hardware, handle type | **IMMEDIATE** |
| **Track A Factory Visits** | Founder's TN circuit — physical delivery of Standard Brief to TA-1 through TA-4 (TA-5 floor visit condition) | Standard Brief approval | **IMMEDIATE** |
| **Week 3 UK Demand Dossiers** | Full dossiers for Aspinal, Knomo, Fiorelli. COGS extraction for Osprey. Companies House check for Apatchy, N'Damus, TORRO. | PAUSED — supply side must be qualified first | High (resume after 21-Day Test launch) |
| **Voice DNA Calibration** | No real Founder writing samples loaded. Copywriter agent is structurally blind. | Founder must provide 3–5 writing samples | **CRITICAL BLOCKER for all content** |
| **Outreach Copywriting** | Cold email scripts, APLF approach framework, LinkedIn outreach templates | Voice DNA must be calibrated first | Blocked |
| **Client Proposal Template** | KritiKaal capability deck for Anchor-tier outreach | Supply side must have qualified Tier 1 factory before any proposal goes out | Sequential |
| **Phase 2 — First Anchor Client Engagement** | Approach to Sarah Hawksworth (Aspinal). Knomo + Fiorelli dossiers completed. | 21-Day Test results required. Voice DNA required. | Q2 2026 |
| **Vida Vida Founder Interview** | Social proof asset for India narrative | 3-question framework drafted, not sent | Low (after outreach infrastructure) |
| **Or Ve'Hadar Outreach (Israel)** | Highest-scoring Israeli ICP brand from Sprint 01 | Outreach template not built | Medium |
| **Learning Log + Feedback.md Update** | Post-Sprint 01 learnings not consolidated | 20 minutes work | Housekeeping |

---

## SECTION 4 — THE INTERFACE & OPERATING LOOP (UX)

### How You, the CEO, Interact With This System

This is a **three-tool stack**. Each tool has a specific role. They do not compete — they compound.

---

#### Tool 1: Claude Desktop App — The Brain

**What it is:** Conversational interface. Long-form reasoning. Strategic dialogue.

**What you use it for:**
- Strategic thinking sessions ("should we pursue X?")
- Reviewing reports and asking questions
- Making decisions and logging them to `M-memory/decisions.md`
- Reading and interpreting research outputs

**What it cannot do:** Write to disk. Create files. Run code. Execute workflows. (It has no tools by default.)

**The constraint:** Every session starts cold — no memory of prior sessions unless you paste context or reference files. This is why `B-brain/00-MASTER-strategy.md` and this file exist. They are your external memory, injected at session start.

---

#### Tool 2: Obsidian — The Library

**What it is:** Local vault editor. Your file system made navigable.

**What you use it for:**
- Reading and navigating the full file system visually
- Seeing the full `B-brain/` research library in one panel
- Reviewing factory bench, pipeline, and decision logs without a terminal
- Editing files manually when you want to make quick corrections without AI

**What it cannot do:** Run agents. Execute logic. Update itself automatically.

**The relationship:** Obsidian is the human-readable view of what the AI has built. Think of it as the dashboard — you read here, you instruct the AI to update.

---

#### Tool 3: Claude Code / Terminal — The Executioner

**What it is:** Claude with full file system access, code execution, and tool use. This is where work is actually done.

**What you use it for:**
- Creating, editing, and updating files (exactly what this session is doing)
- Running research sweeps (web search + Companies House extractions)
- Building structured documents from raw intelligence
- Executing the full ABC-TOM workflow (Researcher → Analyst → Strategist → Copywriter → Gatekeeper)
- Reading Excel files, processing data, scoring matrices

**What makes it different:** It can act, not just advise. Every file written in this session exists permanently on disk and is visible in Obsidian instantly.

---

### Why `--dangerously-skip-permissions` Mode Is Critical

By default, Claude Code asks for permission before every file write. In a deep research or document-building session, this creates:
- Permission interruptions every 2–5 minutes
- Flow destruction — you lose the strategic thread
- Significant time cost — 10–20 permission prompts per session is normal

`--dangerously-skip-permissions` tells Claude Code to trust you and execute without interruption. In the context of **this specific project** — building internal research files in a personal workspace — there are no security risks. You are not running production code. You are building a knowledge system.

**The rule:** Use `--dangerously-skip-permissions` for any session that involves building, updating, or restructuring files in the KritiKaal workspace. Do not use it for sessions that touch external systems (APIs, databases, emails).

---

### The Operating Loop (How a Session Works)

```
SESSION START
     ↓
[1] CEO opens Terminal → navigates to workspace
[2] Runs: claude --dangerously-skip-permissions
[3] CEO states the mission for the session (1-3 sentences)
     ↓
ADAM ACTIVATES
     ↓
[4] Adam reads relevant context files (MASTER-PLAN, pipeline, bench)
[5] Adam assigns the right agents for the task
[6] Agents execute — files created/updated in real time (visible in Obsidian)
[7] Adam presents output in chat for CEO review
     ↓
CEO REVIEW
     ↓
[8] CEO approves / modifies / redirects
[9] Adam closes The Loop: updates M-memory/ if a decision was made
     ↓
SESSION END
     ↓
[10] Obsidian shows all new/updated files
[11] CEO exits terminal — all work persists on disk
```

**The Loop is what makes this compound.** Every session that closes The Loop (updates memory, promotes decisions) makes the next session smarter. Sessions that skip The Loop are wasted compounding opportunities.

---

## SECTION 5 — MAXIMISING PERFORMANCE (OPTIMISATION)

### The 3 Things That Will Double Output Quality

---

#### 1. Load Voice DNA — Solve the Copywriter's Blindness

**Current state:** `C-core/voice-dna.md` describes how KritiKaal should sound — the principles, the tone, the rules. But the Copywriter agent has never read real Yossi writing. It has principles, not patterns.

**The problem this creates:** Every piece of outreach, every client email, every LinkedIn post will sound generic. Not wrong — but not distinctly *yours*. Anchor-tier clients (Sarah Hawksworth at Aspinal, procurement directors at £30M+ brands) will notice when an email sounds like every other sourcing pitch they receive.

**The fix (1-hour investment):**
1. Find 3–5 examples of your best writing — emails to clients, LinkedIn posts, WhatsApp messages that landed well, any written communication you're proud of
2. Paste them into `B-brain/02-my-samples/` (content, sales, or thinking track)
3. Run the `T-tools/02-prompts/content/02-learn-my-style.md` prompt → this trains the Copywriter agent on your actual patterns

**What unlocks:** Cold email to Knomo sourcing team. APLF approach framework for Sarah Hawksworth. LinkedIn content that sounds like you, not a template.

---

#### 2. Gate the Demand Side Behind the Supply Side — Don't Flinch

**Current state:** The UK pipeline has 47 brands, 5 decision-makers mapped, a boardroom-level COGS argument for Aspinal ready to deploy. It is tempting to start outreach now.

**The risk:** An Anchor-tier client like Aspinal of London asks: "Can you handle 2,000 units by September?" and KritiKaal cannot name a factory that has passed an AQL 2.5 sample evaluation. The deal dies — and the relationship is poisoned.

**The discipline:** Complete the 21-Day Factory Test first. Get at least one golden sample pass from a Tier 1 factory before any client-facing outreach. The supply constraint is not a delay — it is the thing that makes every client conversation credible.

**Timeline:** 21-Day Test launches → results by Day 21 → Tier 1 assignment by Day 25 → client outreach begins Week 7.

---

#### 3. Use the Agents Sequentially — Don't Skip Straight to Copywriter

**The temptation:** "Write me a cold email to Aspinal."

**The failure mode:** The Copywriter produces a generic, ungrounded email that doesn't reference the specific £2.31M COGS savings argument, doesn't name Sarah Hawksworth's 30-year sourcing background, and doesn't hit the right tone for a CFO-adjacent decision-maker with a new CEO watching.

**The correct sequence for any outreach asset:**

```
Researcher → builds intelligence profile (what we know about this person, brand, moment)
      ↓
Analyst → extracts the 1-3 sharpest hooks from the intelligence
      ↓
Strategist → selects the play (Play 1/2/3), defines the pitch angle
      ↓
Copywriter → writes from the brief the Strategist produces
      ↓
Gatekeeper → reviews against Voice DNA and factual accuracy
```

This is the difference between a good email and a great one. The system is built for sequential use — trust the sequence.

---

## SECTION 6 — THE 90-DAY ROADMAP

### From Today's Test to the First Anchor Order

**Today:** 2026-04-20

---

#### PHASE 1: SUPPLY QUALIFICATION (Days 1–25)
**Milestone: Tier 1 factory named, golden sample passed**

| Day | Action | Owner |
|-----|--------|-------|
| 0–2 | Founder approves Standard Brief v1.0 (leather thickness, hardware, handles confirmed) | CEO |
| 3–5 | Track A: Founder's TN circuit — physical delivery to Pioneer Inc., Sastha, Rittz, Apex, Trimurthi floor visit | Founder |
| 3–5 | Track B: Cold email dispatch to Dugros, Om Leather, XL Enterprises (Kolkata) | Adam/System |
| 6–21 | 21-Day Test runs — 8 factories evaluated on 6 variables | Factories + Adam tracking |
| 22 | 21-Day Test results collated — response speed, quote accuracy, price, lead time, certs, sample quality | Adam |
| 23–25 | Golden sample evaluation (AQL 2.5 — 8 criteria) — fastest, best-quality sample triggers Tier 1 assignment | Founder + Adam |
| 25 | **MILESTONE: Tier 1 factory named. Partner Stack v1.0 published.** | — |

---

#### PHASE 2: OUTREACH INFRASTRUCTURE (Days 20–45)
**Milestone: Voice DNA calibrated. Aspinal approach framework ready.**

| Day | Action | Owner |
|-----|--------|-------|
| 20–22 | Voice DNA calibration — Founder provides 3–5 writing samples | CEO |
| 22–24 | Copywriter agent trains on samples — `02-learn-my-style.md` prompt executed | Adam |
| 25–30 | Aspinal full dossier complete — Sarah Hawksworth profile, COGS one-pager, APLF approach framework | Researcher + Analyst + Strategist |
| 30–35 | Knomo full dossier — China dependency map, Changshu Maydiang relationship intelligence, UK sourcing contact identified | Researcher + Analyst |
| 30–35 | Fiorelli procurement mapping — post-acquisition org chart, sourcing team contact | Researcher |
| 35–40 | Cold email scripts drafted (Play 1, Play 2, Play 3 variants) | Copywriter + Gatekeeper |
| 40–45 | **MILESTONE: Outreach infrastructure complete. 3 dossiers done. Email scripts approved.** | — |

---

#### PHASE 3: FIRST CLIENT OUTREACH (Days 45–65)
**Milestone: First meeting booked with an Anchor or Core-tier target**

| Day | Action | Owner |
|-----|--------|-------|
| 45 | APLF Hong Kong / trade show outreach to Sarah Hawksworth (Aspinal) — warm intro via UKFT network if available | Founder |
| 45–50 | Fiorelli/Centric cold email — Post-acquisition procurement reset window approaching close | System (Play 1 script) |
| 45–50 | Knomo LinkedIn outreach — UK sourcing contact (identified in dossier) | Founder |
| 50–60 | Follow-up sequence — 3-touch email + LinkedIn + (if no response) direct WhatsApp | Adam |
| 60 | **MILESTONE: Minimum 1 discovery call booked.** |  — |

---

#### PHASE 4: FIRST ORDER (Days 65–90)
**Milestone: First paid order placed. $5K+ transaction. Client brief received and fulfilled.**

| Day | Action | Owner |
|-----|--------|-------|
| 60–70 | Discovery call → capability presentation → KritiKaal proposal delivered | Founder + Adam |
| 65–75 | Client sends first product brief → KritiKaal translates to factory brief → Tier 1 factory engaged | Founder |
| 75–85 | Golden sample round with client brand — approval cycle | Founder + Factory |
| 85–90 | **MILESTONE: First production order placed. Invoice raised. $5K+ transaction in motion.** | — |

---

#### PHASE 5: ANCHOR-TIER TARGET (Days 60–180)
**Milestone: First £150K+ deal in pipeline**

| Day | Action | Owner |
|-----|--------|-------|
| 60+ | Aspinal relationship development — multiple touches, APLF meeting, follow-on COGS presentation | Founder |
| 90+ | KritiKaal capability deck built — 1 Tier 1 factory on record, 1 golden sample passed, 1 active client reference | Adam |
| 120+ | Aspinal proposal: COGS reduction partnership. £2.31M savings argument. Production capacity demonstration. | Founder + Adam |
| 150–180 | **MILESTONE: £150K+ Anchor-tier deal in negotiation or signed.** | — |

---

## PHASE GATES — GO / NO-GO DECISIONS

| Gate | Trigger | Go Condition | No-Go Action |
|------|---------|-------------|--------------|
| Gate 1: Begin Outreach | Day 25 | Tier 1 factory named + golden sample pass | Extend 21-Day Test, do not begin outreach |
| Gate 2: Send Aspinal Approach | Day 45 | Voice DNA calibrated + dossier complete | Delay outreach, finish dossier first |
| Gate 3: Send Proposal | Post-discovery call | Client interest confirmed + Tier 1 factory confirmed | Never send a proposal to a hot lead backed by an unqualified supply chain |
| Gate 4: Accept First Order | First client brief received | Tier 1 factory can meet spec, lead time, and MOQ | Negotiate timeline, do not over-promise |

---

## THE LOOP — WHAT TO UPDATE AND WHEN

| Trigger | File to Update |
|---------|---------------|
| New strategic decision made | `M-memory/decisions.md` |
| 21-Day Test results received | `B-brain/05-research/supply-intelligence/00-master-factory-bench.md` |
| New brand added to pipeline | `B-brain/05-research/demand-intelligence/uk-pipeline/00-master-pipeline.md` |
| Client meeting completed | `M-memory/feedback.md` (log what landed, what didn't) |
| Any insight on what works in this market | `M-memory/learning-log.md` |
| Decision held for 3+ months | Promote from `M-memory/decisions.md` → `C-core/` (project-brief or voice-dna) |
| New factory qualified | `B-brain/05-research/supply-intelligence/00-master-factory-bench.md` |
| Financial model updated | `B-brain/00-MASTER-strategy.md` + this file (Section 1) |

---

## APPENDIX — QUICK REFERENCE

### KritiKaal Financial Constants (as of 2026-04-20)

| Constant | Value | Status |
|----------|-------|--------|
| $1M target | Gross PROFIT (not revenue) | Locked |
| Phase 1 AOV | $5,000 per transaction | Confirmed baseline |
| Planning default AOV | $10,000 | Combined Mid scenario |
| Gross margin floor | 22% | Operational |
| Target margin | 30–35% | Phase 2 goal |
| Min annual deal volume (Core client) | £50,000 | ICP threshold |
| Min annual deal volume (Anchor client) | £150,000 | Anchor threshold |

### The Three Demand-Side Plays

| Play | Pitch | Lead Targets | Urgency |
|------|-------|-------------|---------|
| Play 1 — China Plus One | "One audit failure away from retail delisting. Here is your India alternative." | Knomo, Fiorelli | HIGH |
| Play 2 — India Upgrade | "You're already in India. Can your factory survive an LWG audit and 48% growth? Ours can." | Aspinal, Osprey, Scaramanga | MEDIUM |
| Play 3 — Europe Cost Pressure | "Spanish artisan costs rising 8–12%/yr. Here is Kanpur quality at Kanpur pricing." | Strathberry, Maxwell Scott, Fairfax & Favor | LOW-MEDIUM |

### The Partner Stack Target

| Tier | Role | Target Count | Assignment Trigger |
|------|------|-------------|-------------------|
| Tier 1 — Named Partners | Client-facing, fully audited | 2–3 | 21-Day Test pass + golden sample AQL 2.5 |
| Tier 2 — Qualified Backup | Overflow, SKU specialisation | 1–2 | Desktop score 16+ + Standard Brief response |
| Tier 3 — Sampling Specialist | Speed-to-sample only | 1 | Fastest Track A or B responder |

### The Absolute Criteria Rule (Supply Side)

No factory advances without ALL FOUR:
1. **G1:** LWG OR BSCI/SA8000/SMETA certification
2. **G2:** Bags and accessories as primary or confirmed category
3. **G3:** Active exports to EU, UK, North America, or Middle East
4. **G4:** 5+ years operating, 50+ workers

Geography is never a criterion. If a factory meets all four gates and is in Tamil Nadu, the geography is a compounding strategic advantage.

---

*This file is the master. When documents conflict, this file wins. When priorities are unclear, check Section 3. When strategy is debated, Section 1 resolves it. The Loop keeps it current.*

---

**Document History**

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-04-20 | Initial creation. Full system inventory. 90-day roadmap. Operating model defined. |
