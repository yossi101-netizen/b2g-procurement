# KRITIKAAL CORE — INTENT HUNTING PLAN
# The Precision Discovery-Call Engine (Claude + Emergent + Data Intelligence)

**Status:** PROPOSED (architecture + recommendation) | **Date:** 2026-06-14
**Owner:** Yossi (Founder) | **Scope:** KRITIKAAL CORE only (demand-side)
**Aligned to:** voice-dna.md, MASTER_CONTEXT_MANIFEST.md v5, Israel-Hunter V3
(leads.db), BI_HUNTING_PLAYBOOK.md (doctrine borrowed, code air-gap respected)

> **Air-gap flag (read first).** This is a CORE lead-generation plan. It lives at
> the requested path inside `mission-control/`, but `BI_HUNTING_PLAYBOOK.md` §0
> defines `mission-control/` as an air-gapped BI engine that shares no code paths,
> databases, or imports with the CORE business. This DOCUMENT borrows OSINT
> *doctrine* from that playbook, but the engine it specifies is CORE-side and
> governed by `leads.db`. No code path described here reads from or writes to
> `mission-control/`. If you prefer, the natural home for this file is a CORE
> ops folder, not the BI engine. Saved here per explicit instruction; relocation
> is a one-line move.

---

## 0. THE GOAL, STATED PLAINLY

Put Yossi on the phone with buyers who, with high probability, need managed India
leather manufacturing right now. The machine does everything up to the call. The
human does the call. We automate discovery and outreach. We never automate
conversion, because conversion in this business is trust, and trust does not
scale through a script.

---

## 1. EVALUATION OF THE THESIS

### 1.1 The thesis is correct, for a specific structural reason

In a high-trust, MOQ 300+ sale gated by a physical Golden Sample and compliance
documentation, the bottleneck is never message volume. It is trust and proof.
The "Money Machine" video confirmed the rule from the other side: low-ticket
self-serve sales can automate the close, high-ticket sales cannot. Tane's own
words: high-ticket conversion needs a human in the loop. KritiKaal is the
definition of high-ticket. Automating the conversion layer would not just fail,
it would actively burn trust. Automating the discovery layer multiplies the
founder's reach without touching the part that closes deals.

So the thesis holds: automate top-of-funnel intent detection and outreach,
keep the discovery call and everything after it fully human.

### 1.2 The reframe you should accept: this is a rifle, not a shotgun

Your unit economics decide the architecture. 28 clients at $35K is $1M ARR.
28 closes a year is roughly 2 to 3 a month. Working backward through a realistic
funnel (call to sample to client), you need on the order of 150 to 250 genuinely
high-intent, well-timed conversations a year. You do not need thousands of
outreaches a month. You need a small number of precisely-timed, correctly-targeted
ones.

This matters because the obvious failure mode is over-building. A large scraping
stack is expensive to run, expensive to maintain, produces false precision, and
risks the founder's sending reputation through volume. The correct system is
small, sharp, and timing-driven. Build the precision instrument, not the volume
machine. This is the same lesson the Wispr Flow analysis surfaced: do not chase a
1,000-per-month number designed for a different business.

### 1.3 The core mechanic: Trigger = Fit x Timing

A list of leather brands that source from China is a FIT list. It tells you WHO.
It does not tell you WHEN, and WHEN is the entire game in intent hunting. A fit
lead contacted at a random moment is cold. The same lead contacted in the week
their Chinese supplier went silent, or a new tariff hit their HS code, or their
EUDR deadline landed, is hot.

```
HIGH-INTENT TRIGGER = FIT SIGNAL  x  TIMING SIGNAL
  FIT    = right market, right volume (300-3,000), sources or should source India
  TIMING = a dated event that creates pain or budget right now
```

The engine must hold both and only fire outreach when both are present. This
single rule is what turns a generic prospecting tool into the "high probability
they need us now" machine you asked for.

---

## 2. THE OPTIMAL THREE-LAYER ARCHITECTURE

### 2.1 Layer 1 — Data Intelligence (The Intent Engine)

**Design principle:** separate Fit from Timing, then multiply them. Reuse what
exists. Build only what is missing.

**What already exists and should be reused:**
- **Israel-Hunter V3 / leads.db** produces FIT for Israel (Class A volume buyers:
  importers, OEM brands, wholesalers, distributors, local manufacturers). It even
  carries primitive timing in its distress query suffixes (business-for-sale,
  liquidation, ownership-change). For Israel, we add a timing overlay and an
  outreach layer on top. We do not rebuild discovery.
- **The macro intel-pipeline** (rss_poller, llm_filter, intel_core) already
  monitors EUDR and tariff events to fuel content. That same feed is a ready-made
  TIMING source. One signal stream, two consumers (intent and content).

**The best data sources for our ICP, ranked by predictive power.** Your three
hypotheses (customs data, job boards, compliance pain) are all correct and all
included below. The two highest-value sources are ones not on your list, marked
[HIDDEN].

**Tier S — Behavioral (a business voting with its money, highest signal):**

1. **Bill-of-Lading / customs import data.** The single strongest fit-and-timing
   source. From shipment records you can detect:
   - China-sourcing concentration (a brand 100% dependent on Chinese tanneries is
     the China-Plus-One pitch, pre-qualified).
   - **[HIDDEN] The shipment-gap signal.** A brand that imported leather goods
     from China on a regular cadence and then STOPPED 60 to 90 days ago is a
     brand in acute supply pain right now. This is the purest timing trigger in
     the entire system, and almost nobody hunts on it. It beats "imports from
     China" because it captures the moment of pain, not the static state.
   - New and growing importers landing in the 300-3,000 unit Missing Middle.
   - Importers on HS 4202 / 4203 (leather bags, cases, goods).
   - Sources: ImportYeti (free), UN Comtrade (free, macro), Volza and
     ImportGenius and Panjiva (freemium). Market fit: US strong (public
     shipment-level data), UK weak (HMRC is aggregated, not shipment-level), 
     Israel weak (not publicly available at shipment level).

2. **Macro shock cross-referenced against the import list (the timing
   multiplier).** When a new Section 301 tariff action hits leather HS codes, or
   an EUDR enforcement date moves, or REACH Cr(VI) enforcement tightens, every
   importer on those codes is in pain on the same day. Cross-reference the macro
   event (from the existing intel-pipeline) against the BoL fit list and you have
   an instant hot list with a dated reason to call. This is where the content
   engine and the intent engine share one feed.

**Tier A — Stated intent (a business telling you its plans):**

3. **Hiring signals.** Roles like "Sourcing Manager," "Production Manager Asia,"
   "Supply Chain India," "QA Manager leather/accessories." A brand hiring this
   has both volume and admitted pain. Sources: LinkedIn Jobs X-ray (free, no
   login), company career pages, Indeed; Israel: AllJobs, Drushim, JobMaster.
   Note: these Israeli job boards are blocklisted in `scrapers.py` as discovery
   *noise*, but they are valuable here as a *timing* feed. Different use, separate
   path, no conflict with the discovery engine.

4. **Funding signals.** Seed and Series A leather/accessory DTC raises mean a
   brand is scaling past artisan suppliers into the Missing Middle. Sources:
   Crunchbase (free tier), press. Market fit: US and UK strong, Israel moderate.

5. **Compliance pain expression.** Brands publicly posting about traceability,
   EUDR readiness, Digital Product Passport, or sustainability commitments, or
   filing B-Corp applications. Sources: brand ESG pages, LinkedIn posts. Strong
   for UK (compliance-front-loaded market).

**Tier B — Supplementary (high intent, lower scale, more manual):**

6. **[HIDDEN] Shopify out-of-stock and restock velocity.** A leather brand on
   Shopify showing repeated "sold out" or "restocking soon" states across SKUs
   is a brand with a supply problem it cannot solve. This is a real-time
   supply-distress proxy that is almost never used for prospecting. Source:
   Shopify store crawl plus availability monitoring. Works across all three
   markets wherever the brand runs Shopify.

7. **Negative-review and community pain mining.** One-star reviews citing quality
   drops, delays, and defects map directly to the QC Disaster cluster. Founder
   pain-posts on Reddit, LinkedIn, and X about supplier ghosting map to the
   Sourcing Agent Betrayal cluster. Highest intent of any source, lowest scale,
   hardest to automate cleanly. Treat as a P2 enrichment, not the core feed.

8. **Competitor-displacement.** Ex-customers of struggling managed-sourcing
   competitors (Fashinza, Geniemode, Zetwerk, named per voice-dna competitive
   anchoring) are warm by definition. Mine via reviews, LinkedIn, and news.

9. **Trade-show exhibitor and attendee lists.** Lineapelle, Magic Las Vegas,
   Moda UK, and similar. Paying to exhibit equals budget plus active sourcing
   intent. Source: 10times.com, eventseye.com, event pages.

### 2.2 Layer 2 — Cognitive (Claude Sub-Agents)

A five-agent chain, orchestrated from a master `CLAUDE.md` instruction file (the
video's key efficiency insight: the agents carry voice-dna, named mechanisms,
the pain-cluster map, and market rules so they never re-derive context per run).

- **A1 Trigger Validator and Scorer.** Ingests raw signals, deduplicates, kills
  noise, excludes anything already in leads.db or a known client, applies the
  Israel-Hunter V3 disqualifiers (dropship, ritual leather, B2C micro-retail),
  and scores Fit x Timing from 0 to 100. Enforces the anti-fabrication trace
  (borrowed from playbook §5): every score cell cites a source URL or is marked
  `UNKNOWN — REQUIRES VERIFICATION`. A fabricated trigger sent to a real prospect
  burns the founder's name, so this gate is non-negotiable.

- **A2 OSINT Brand Researcher.** For each surviving candidate, builds the brand
  profile: what they sell, current sourcing (from BoL), market (IL / US / UK),
  and the specific pain hypothesis mapped to one of the eight YouTube pain
  clusters (qc-disaster, china-plus-one, eudr-compliance, sourcing-agent-betrayal,
  golden-sample-trap, missing-middle-moq, uk-import-duty, managed-vs-alternatives).
  Output: a one-paragraph "why now" plus the named mechanism that answers it.

- **A3 Decision-Maker Finder.** Identifies the right human and the right channel
  per market. Israel: founder or owner, WhatsApp plus LinkedIn. US: founder or
  ops lead, email plus LinkedIn. UK: head of sourcing, product, or procurement,
  email plus LinkedIn, formal. Uses LinkedIn X-ray. Returns 1 to 3 options when
  not certain (the video's "give me three options" move), so Yossi can pick.

- **A4 Voice-DNA Copywriter.** Drafts ONE low-pressure, discovery-call-seeking
  message per prospect. Never a template blast. Strict encoding of voice-dna:
  - **No em-dashes. Hard ban.** Use colons, periods, parentheses.
  - **Numbers before adjectives.** "A 500-unit run with sub-2% defect tolerance,"
    never "a large high-quality run."
  - **Admission before solution.** Open with a concrete problem or failure moment
    (the 2012 China shipment structure), then the mechanism. Never lead with the
    pitch.
  - **Named mechanisms verbatim:** Single Point of Accountability, The Golden
    Sample Trap, Double-Back Guarantee, AQL 2.5, The Missing Middle.
  - **Negative qualification.** State who this is not for. It is both a trust
    signal and a sales filter.
  - **Low-friction CTA.** A 20-minute call, free, zero risk to start.
  - **Market register and English variant.** British English for UK, American
    English for US, British English as the Israel default (per the context-rationale
    v1.1 sync). WhatsApp-speed and short for Israel, async and SLA-aware for US,
    formal and docs-aware for UK.

- **A5 Gatekeeper (G6).** Red-teams every draft against the voice-dna blacklist,
  scans for em-dashes, rejects sentences over 30 words, rejects any claim without
  a specific proof point, and verifies the correct English variant and register.
  Pass or fail with line-level edits. Nothing reaches Yossi un-passed.

Human-in-the-loop checkpoints follow the video's phased model: at first Yossi
reads every card and every message; as trust in the chain builds, high-score
low-risk cards graduate to auto-approval, then to exception-only review.

### 2.3 Layer 3 — Execution (Emergent)

Emergent is the orchestrator and the dashboard. It schedules the data pulls, runs
the A1 to A5 chain, persists results CORE-side, and renders one surface: the
**Triage Dashboard**, a ranked queue of **Intent Cards**.

Each Intent Card is one screen, designed for a decision in under 30 seconds:
- Brand and market flag
- Fit x Timing score and the trigger ("why now," one sourced line)
- Pain hypothesis and the named mechanism that answers it
- Decision-maker and channel, with the contact path
- The G6-passed drafted message
- Three actions: **Approve and Send** | **Edit** (optionally by Wispr dictation)
  | **Reject** (reason captured, fed back to A1 scoring)
- A **Book Call** action that appears when a reply lands (calendar link)

Frictionless means highest-scoring card first, one at a time, decide, move on.
The system handles the send, logs the outcome to leads.db and the CRM bridge,
and schedules follow-ups.

**Build-vs-reuse, stated honestly:** a Streamlit dashboard (`mission_control_app.py`)
and the `kritikaal-hub` already exist. Per the air gap, the Intent triage
dashboard belongs CORE-side (in or beside `kritikaal-hub`), not in
`mission-control/`. Emergent is the fastest way to stand up the orchestration and
dashboard if you do not want to extend the existing hub. Either is valid. The
constraint is the air gap, not the framework.

---

## 3. PROS AND CONS OF TRIGGER-SYSTEM CONFIGURATIONS

### Config A — Customs / BoL-Led (behavioral)
- **How:** pull shipment records, detect China concentration and the shipment-gap
  signal, score, enrich, draft.
- **Pros:** highest signal, behavioral not stated, captures the moment of pain,
  reveals actual sourcing dependency.
- **Cons:** data availability is wildly uneven by market. Medium-to-high build.
- **Complexity:** Medium-High. **Quality:** US high, UK low, Israel near-zero.

### Config B — Hiring + Compliance + Funding (stated-intent)
- **How:** monitor job boards, ESG pages, funding news; cross-reference to fit.
- **Pros:** works across all three markets, including the two where customs data
  is closed. Cheap (mostly free sources).
- **Cons:** noisier, more false positives, stated intent lags behavioral intent.
- **Complexity:** Medium. **Quality:** IL medium, US medium, UK high.

### Config C — Website De-anonymization (reverse-IP on kritikaal.com)
- **How:** identify which companies visit the site and which pages they view.
- **Pros:** highest intent per lead (they came to you). Low build complexity.
- **Cons:** requires existing site traffic. The CORE site is early, so yield is
  near-zero today. Premature until the SoM and SEO content stack drives volume.
- **Complexity:** Low. **Quality:** potentially high, but near-zero volume now.
  **Verdict: defer.** Revisit once content drives traffic.

### Config D — Fit x Timing Composite (RECOMMENDED)
- **How:** market-weighted blend. Each market uses the configuration its data
  reality allows, unified by the Fit x Timing score and the single Intent Card
  surface.
- **Pros:** matches the data asymmetry across markets instead of pretending one
  source fits all. Reuses the existing engines. Right-sized to the call target.
- **Cons:** more moving parts than a single-source system; needs disciplined
  scoring to stay precise.
- **Complexity:** Medium (because it reuses existing assets). **Quality:** high
  across all three when weighted correctly.

### Config E — Competitor-Displacement + Community Listening (P2 supplement)
- **How:** mine ex-customers of struggling competitors and founder pain-posts.
- **Pros:** warmest leads in the system. **Cons:** low scale, manual.
- **Verdict:** keep as a P2 enrichment feeding A1, not a core engine.

### The market-weighted recommendation (Config D in detail)

| Market | Primary config | Secondary | Why |
|---|---|---|---|
| **US** | A (BoL-led) | D-funding overlay | Public shipment data makes Fit x Timing cleanest and fastest to validate |
| **UK** | B (compliance + hiring + Companies House + Shopify crawl) | A secondary | HMRC customs data is closed; UK is compliance-front-loaded, so compliance triggers lead |
| **Israel** | extend leads.db (fit) + B timing overlay (distress, hiring, LinkedIn) | E | BoL not available; the discovery engine already exists, so add timing and outreach on top |

---

## 4. THE FOUNDER WORKFLOW (15 minutes, daily)

The overnight machine has already pulled signals, scored Fit x Timing, run OSINT,
drafted, and passed G6. Yossi opens a ready queue.

- **Minute 0 to 2:** open the Intent Card queue. Cards are pre-ranked.
- **Minute 2 to 10:** triage the top 10 to 15 cards. Approve, Edit, or Reject.
  Approved cards send. For a card worth a personal touch, dictate one extra line
  with Wispr before sending. Reject reasons are captured and retune the scorer.
- **Minute 10 to 13:** review replies from prior days. One-click Book Discovery
  Call for the warm ones. This is the north-star output of the entire system.
- **Minute 13 to 15:** feed one real-world signal back in (a name heard, a market
  event, a factory observation). It seeds A1. This closes the loop.

**Weekly, Friday, 30 minutes:** review KPIs and reject-reason patterns; retune
the Fit x Timing weights.

**KPIs (and the one anti-KPI):**
- North-star: discovery calls booked per week. Target 2 to 3.
- Supporting: cards per day, approve rate, reply rate, call-to-sample-to-client
  conversion.
- Anti-KPI: do not optimize raw outreach volume. Volume is the failure mode.

---

## 5. RISKS, AIR-GAP, AND SECOND-ORDER INSIGHTS

- **Air-gap compliance.** This engine is CORE-side, governed by leads.db, sharing
  no code path with `mission-control/`. It borrows OSINT doctrine, not code. The
  only open item is the location of this document (see top flag).
- **Anti-fabrication.** Enforce the OSINT-to-output trace on every trigger. A
  hallucinated reason to call, sent under the founder's name, is worse than no
  outreach at all.
- **Deliverability and reputation.** Cold outreach at any volume risks the
  sending domain and the founder's name. Mitigate with warm-up, deliberately low
  daily volume (which the rifle-not-shotgun target already enforces), and
  per-market channels (WhatsApp for Israel reduces email exposure).
- **Legal.** UK and EU personal data fall under UK-GDPR and PECR; Israel under the
  Privacy Protection Law; US under CAN-SPAM. B2B cold contact rules differ by
  market. Get a legal pass on the outreach templates before scaling, UK first.
- **Data-cost discipline.** Start on free and freemium tiers (ImportYeti, UN
  Comtrade, LinkedIn X-ray). Do not buy Apollo, Panjiva, or Sales Navigator until
  the funnel has proven it converts.
- **Second-order insight.** The same signal that triggers 40 US outreaches after
  a tariff shock is also a YouTube video for the Intel Agents. One feed, two
  consumers. Wire the intent engine and the content engine to the same
  intel-pipeline rather than duplicating it.
- **Third-order insight.** Every reject reason and every reply is training data.
  Over 6 to 12 months the Fit x Timing scorer becomes a proprietary, compounding
  asset. That scorer, not the scraping, is the real moat.

---

## 6. DEFINITIVE RECOMMENDATION

Build **Config D, the Fit x Timing Composite**, market-weighted, right-sized to 2
to 3 discovery calls per week. Sequence it the way the video teaches: solve one
small piece, verify it, then clone.

- **Phase 0 (week 1 to 2):** wire the existing intel-pipeline as a timing feed and
  start ImportYeti US BoL pulls. Reuse leads.db for Israel fit. No new heavy
  infrastructure yet.
- **Phase 1 (US first):** stand up the A1 to A5 Claude chain and a minimal Emergent
  triage dashboard, CORE-side. Prove the full loop on US, because BoL data makes
  Fit x Timing cleanest and fastest to validate. Target the first booked
  discovery call from the machine.
- **Phase 2:** clone the loop to UK with the compliance-and-hiring configuration.
- **Phase 3:** deepen Israel by adding the timing overlay and outreach layer on
  top of the existing Israel-Hunter V3 engine.
- **Defer:** Config C (de-anonymization) until site traffic exists. Defer all paid
  data until the funnel converts.

Start with one market, one trigger type, one verified loop. Then rinse and repeat.

---

## 7. META-LAYER — THE IMPROVED NEXT PROMPT

When you commission Phase 1, the prompt that will get the best result is narrow,
not broad: "Build the US BoL shipment-gap trigger only. Define the exact data
fields, the gap-detection rule (cadence broken for 60 to 90 days), the Fit x
Timing scoring formula with weights, and the A1 Trigger Validator spec including
the anti-fabrication trace. Do not build the other markets or the dashboard yet."
One small problem, verified, before the next.

---

*KRITIKAAL CORE — Intent Hunting Plan v1.0 | 2026-06-14 | Demand-side only*
*Engine is CORE-side and governed by leads.db. Doctrine borrowed from*
*BI_HUNTING_PLAYBOOK.md; no shared code paths (air gap respected).*
