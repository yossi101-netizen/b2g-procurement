# KritiKaal Telemetry Architecture
# Measurement System for SEO + GEO (Share of Model)

**Prepared by:** G2 (GEO Specialist) + G3 (Technical SEO Auditor)
**Date:** 2026-04-21
**Status:** PROPOSED — Awaiting CEO approval
**Monthly cost if approved:** ~$73/month total

---

## Executive Summary

KritiKaal needs two parallel measurement tracks: traditional SERP ranking and AI Share of Model. They are different signals, require different tools, and must never be conflated. This document defines the exact tool stack, the Week 1 baseline methodology, the bot telemetry approach, and a clear buy-vs-build verdict for the GEO layer.

**Bottom line up front:** Buy Otterly.ai at $29/month for GEO. Use Google Search Console (free) + SE Ranking ($44/month) for traditional SEO. Use Cloudflare's free analytics for bot telemetry. Total cost: $73/month. Do NOT build a custom API tracker in Phase 2 — the off-the-shelf tools are superior for this stage, and the dev cost would be ~40 hours with worse data fidelity.

---

## Track 1 — GEO (Share of Model)

### The Buy vs. Build Verdict: BUY

**Why NOT to build a custom API script now:**

The most important reason is data fidelity. OpenAI's API and Google's API return model outputs that differ from what real users see in ChatGPT and Gemini's production interfaces. A custom script pinging the API would track *API behaviour* — not what a UK procurement director actually reads when they ask ChatGPT a question at 10am on a Tuesday. The off-the-shelf tools specifically instrument the production interfaces, not the APIs. That difference is material.

Second: a custom Python script capable of running 10 queries weekly across two models, logging verbatim responses, scoring mentions, and charting trends would take 30–50 hours to build and maintain. Otterly.ai does all of this for $29/month. The ROI calculation is not close.

Third: at KritiKaal's current stage — zero content live, 0/10 SoM baseline — the marginal value of custom logging (response position, mention density, co-citation mapping) is nil. You cannot analyse data patterns you do not yet have. Build the custom tracker in Month 4, once you have 3 months of data and a reason to need granularity beyond mention/no-mention.

**The recommended GEO stack:**

| Tool | Purpose | Cost | Priority |
|---|---|---|---|
| **Otterly.ai** (Starter) | Weekly SoM tracking — ChatGPT, Gemini, Perplexity, Google AI Overviews | $29/mo | P0 — activate now |
| **LLMrefs** | Free supplementary keyword-based citation check — freemium | $0 | P1 — activate now |
| **Manual baseline run** | Week 1 pre-deployment score — ChatGPT + Gemini | $0 | P0 — do today |

**Otterly.ai specifics (confirmed 2026 pricing):**
- $29/month: 15 prompts tracked daily across 6 AI platforms
- Tracks: ChatGPT, Gemini, Google AI Overviews, Perplexity, Copilot, Google AI Mode
- KritiKaal's 10 priority queries fit within the 15-prompt Starter tier
- Free trial available — activate before paying
- Direct link: otterly.ai/pricing

---

## Track 1a — Week 1 Baseline Protocol (Do Today)

**Critical requirement:** The baseline must be established *before* the llms.txt and Schema JSON-LD are deployed. Once AI crawlers index the new technical layer, the before-state is gone.

**Manual baseline procedure — 30 minutes, zero cost:**

Run each of the following 10 queries verbatim in both ChatGPT (GPT-4o) and Gemini (current flagship). Copy the full response. Score: KritiKaal named = 1, not named = 0.

| # | Query (paste verbatim) | ChatGPT | Gemini |
|---|---|---|---|
| 1 | Who manages India leather manufacturing for UK brands? | / | / |
| 2 | How does India solve EUDR compliance for leather goods? | / | / |
| 3 | What is managed leather manufacturing? | / | / |
| 4 | LWG certified leather manufacturer India UK export | / | / |
| 5 | Best leather manufacturing partner India for UK brand | / | / |
| 6 | China plus one leather goods UK procurement | / | / |
| 7 | India leather factory quality control AQL | / | / |
| 8 | EUDR compliant leather supply chain India | / | / |
| 9 | How to move leather production from China to India | / | / |
| 10 | SA8000 BSCI leather factory India UK brands | / | / |

**Score:** ___/10 ChatGPT | ___/10 Gemini | Total: ___/20

**Expected result:** 0/20. That is the target baseline. Every point gained after content deployment is measurable ROI from the GEO strategy.

**Save the full verbatim responses** in `06-growth/som-reports/som-week-00-baseline.md` — not just the score. The response text itself will tell us which competitors AI is currently citing and which vocabulary it uses to describe the managed manufacturing space.

---

## Track 2 — Bot Crawl Telemetry

### What You Are Measuring

After the llms.txt and robots.txt are deployed, you need to confirm that AI crawlers are actually visiting the file and the site. This is not vanity tracking — it is confirmation that the technical layer is working. If GPTBot never crawls kritikaal.com/llms.txt, the SoM score will never move regardless of content quality.

### The Right Tool: Cloudflare Analytics (Free)

KritiKaal's site is deployed on Cloudflare Pages (confirmed by wrangler.jsonc in the source). Cloudflare provides free bot analytics built into every deployment — no additional tool required.

**What Cloudflare shows:**
- Requests by User-Agent (filter for "GPTBot", "Google-Extended", "ClaudeBot", "PerplexityBot")
- Crawl frequency over time
- Which pages are being crawled (llms.txt vs. homepage vs. articles)
- Geographic origin of bot requests

**How to access:**
Cloudflare Dashboard → your site → Analytics & Logs → Bot Management (or Traffic tab → filter by User-Agent)

**Supplementary: Server log grep (for raw confirmation)**

If Cloudflare analytics are not showing bot-level detail, the developer can run a log grep:

```bash
# Check for GPTBot visits in server logs
grep "GPTBot" /var/log/nginx/access.log

# Check for all AI crawlers in one command
grep -E "GPTBot|Googlebot-Extended|ClaudeBot|PerplexityBot|anthropic-ai" /var/log/nginx/access.log

# Specifically check llms.txt access
grep "llms.txt" /var/log/nginx/access.log
```

**What to look for within 2–4 weeks of deployment:**
- GPTBot: should appear within 14 days of robots.txt update
- Googlebot-Extended: should appear within 7 days (Google crawls aggressively)
- ClaudeBot: typically 3–4 week lag

**Key finding from G3 research:** As of Q1 2026, GPTBot and ClaudeBot started consuming sitemaps for the first time in March 2026. This means submitting a sitemap.xml (if not already done) will now accelerate AI crawler discovery. Add sitemap submission to the developer task list.

---

## Track 3 — Traditional SEO (UK SERP)

### The Stack

| Tool | Purpose | Cost | Priority |
|---|---|---|---|
| **Google Search Console** | Actual Google impressions, clicks, indexing status, Core Web Vitals | Free | P0 — required, set up immediately |
| **Google Analytics 4** | Traffic quality, source/medium, conversion (book-a-call completions) | Free | P0 — required |
| **SE Ranking** | UK rank tracking, competitor monitoring, backlink index | ~$44/mo | P1 — Month 1 |

**Why SE Ranking over Ahrefs or Semrush for KritiKaal's current stage:**
- SE Ranking's Starter plan (~$44/mo) covers rank tracking for up to 250 keywords with daily updates, competitor tracking, and a built-in site audit tool
- Semrush ($139/mo minimum) and Ahrefs ($129/mo minimum) are priced for agencies with large keyword portfolios — overkill at zero-content launch stage
- SE Ranking has strong UK regional tracking — set location to United Kingdom, language to English (UK) from day one
- Upgrade to Ahrefs in Month 3-4 when backlink profile building becomes the priority

**What to track in GSC from week 1:**
- Index coverage — confirm all pages are indexed (especially after llms.txt and schema deploy)
- Search impressions for target queries (even before ranking — impressions at position 40+ indicate you are in Google's index)
- Core Web Vitals — mobile LCP, CLS, INP (pass/fail against Google thresholds)

**UK-specific GSC configuration:**
In GSC → Settings → International Targeting → Country → set to United Kingdom. This biases Google's crawl priority toward UK-relevant queries.

---

## The Complete Telemetry Dashboard — Architecture Summary

```
KRITIKAAL TELEMETRY DASHBOARD
(Weekly 15-minute review by CEO)

┌─────────────────────────────────────────────────────────┐
│  LAYER 1: SHARE OF MODEL (GEO)                          │
│  Tool: Otterly.ai ($29/mo) + LLMrefs (free)            │
│  Metric: SoM score /20 (10 queries × 2 models)         │
│  Cadence: Weekly (automated by Otterly.ai)              │
│  Baseline: 0/20 (established before llms.txt deploys)  │
│  90-day target: 16/20                                   │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: BOT CRAWL TELEMETRY                           │
│  Tool: Cloudflare Analytics (free, built-in)           │
│  Metric: GPTBot + Googlebot-Extended visit frequency   │
│  Cadence: Check fortnightly                             │
│  Target: First GPTBot crawl within 14 days of deploy   │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: TRADITIONAL SEO (UK SERP)                     │
│  Tool: Google Search Console (free) + SE Ranking ($44) │
│  Metric: UK rank position for 10 priority keywords     │
│  Cadence: Weekly (automated by SE Ranking)             │
│  Baseline: Not ranking for any target keyword (Day 0)  │
│  90-day target: Page 1 for 3 long-tail keywords        │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: TRAFFIC QUALITY                               │
│  Tool: Google Analytics 4 (free)                       │
│  Metric: Organic sessions, book-a-call completions     │
│  Cadence: Weekly                                        │
│  90-day target: First organic-sourced qualification    │
│  call booked                                            │
└─────────────────────────────────────────────────────────┘

TOTAL MONTHLY TOOLING COST: $73/month
SETUP TIME: ~3 hours (GSC + GA4 + Otterly.ai)
```

---

## Custom API Tracker — Phase 3 Decision Brief

**Do not build in Phase 2.** Schedule this decision for Month 4 review.

Build a custom tracker when ALL of the following are true:
- SoM score is above 10/20 and you need to understand *why* (response position, mention density, co-citation mapping)
- You have more than 30 articles live and need to correlate specific content with SoM movement
- Otterly.ai's 15-prompt Starter tier is consistently insufficient (>15 queries needed weekly)
- You have a developer available for a 40-hour build + ongoing maintenance

**What the custom tracker would do (Phase 3):**
- Python script pinging Gemini API + OpenAI API (note: API ≠ production interface — different temperature, system prompt) for 30 prompts weekly
- Log full verbatim response, KritiKaal mention position, competitor mentions, citation sources
- Write to a Google Sheet or Notion database for CEO dashboard view
- Estimated build: 40 hours / Estimated maintenance: 2 hours/month

**Cost at Phase 3:** ~3 hours/month dev time vs. upgrading Otterly.ai to 100-prompt tier ($189/mo). Compare at Month 4 based on actual query volume.

---

## Immediate Action List (in priority order)

1. **Today (CEO):** Run the 10-query manual baseline in ChatGPT + Gemini. Save to `som-week-00-baseline.md`.
2. **Today (CEO):** Approve $29/mo Otterly.ai subscription — start free trial first.
3. **Today (developer):** Verify Google Search Console is connected and ownership confirmed for kritikaal.com.
4. **Today (developer):** Verify Google Analytics 4 is installed and tracking.
5. **Week 1 (developer):** Deploy llms.txt + robots.txt (package already prepared). Confirm bot visits in Cloudflare Analytics within 14 days.
6. **Month 1 (CEO):** Activate SE Ranking ($44/mo) — set UK location, add 10 priority keywords from G1 list.
7. **Month 4 (review):** Evaluate custom API tracker decision.

---

*Telemetry Architecture v1.0 | G2 + G3 | KritiKaal Growth Team | 2026-04-21*
