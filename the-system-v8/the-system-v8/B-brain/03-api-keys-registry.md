# API Keys Registry — KritiKaal System
# Tracks which external services are connected. Never store actual keys here.
# Last updated: 2026-04-26

---

## CRITICAL: Security Rule

**NEVER store actual API keys in this file.**
Keys go in: Claude Code environment settings OR `.env` file in project root.
This file only tracks which services are connected, their status, and what they unlock.

---

## Service Status Overview

| Service | Purpose | Status | Activated | Monthly Cost | Used By |
|---|---|---|---|---|---|
| **GPTZero API** | AI detection scoring for S8 | INACTIVE — key needed | — | $10/mo | S8 Humanization Layer |
| **Reddit API (PRAW)** | Subreddit monitoring for S6 | INACTIVE — key needed | — | Free | reddit-monitor.py |
| **Otterly.ai** | Share of Mind (SoM) tracking | INACTIVE — trial needed | — | Free trial / ~$49/mo | CEO manual review |
| **Companies House API** | UK brand financial intelligence | INACTIVE — free | — | Free | S6, researcher-agent |
| **ImportYeti** | China import records (UK brands) | INACTIVE — manual use | — | Free tier | researcher-agent |
| **SE Ranking** | SEO rank tracking | INACTIVE — optional | — | ~$49/mo | CEO manual review |
| **Phantombuster** | LinkedIn scraping (Month 2 upgrade) | NOT YET — Month 2 | — | $56/mo | linkedin-monitor.py |

---

## Detailed Service Records

---

### GPTZero API
**Status:** INACTIVE — API key required
**Activated:** Not yet
**Monthly cost:** $10/month (Standard tier)
**Where to get it:** https://gptzero.me/api
**Setup command:** `claude config set env.GPTZERO_API_KEY [your_key]`
**Used by:** S8 (Humanization Layer) — `/daily-scout` pipeline Step 3

**What it does:**
- Scores each draft on AI-detectability (0–100% human)
- Returns `completely_generated_prob` — S8 converts this to human score
- Target: ≥85% human score before draft reaches CEO

**Score thresholds:**
- ≥85% → CLEARED — post as-is
- 70–84% → FLAGGED — CEO sees flags + suggested edits
- <70% → FAILED — returned to S7 for full rewrite

**Capacity:** 150 checks/month (exactly covers 5 drafts/day × 30 days)
**API endpoint:** `https://api.gptzero.me/v2/predict/text`

**Activation blockers:** CEO must create account + enter payment + set environment variable
**CEO action file:** `B-brain/06-growth/CEO-ACTION-CHECKLIST.md` → Action 2

---

### Reddit API (PRAW)
**Status:** INACTIVE — credentials required
**Activated:** Not yet
**Monthly cost:** Free
**Where to get it:** https://www.reddit.com/prefs/apps
**Setup:**
1. Create app at `/prefs/apps` → type: script → redirect URI: `http://localhost:8080`
2. Copy `client_id` and `client_secret`
3. Set env variables: `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`

**Used by:** `scripts/reddit-monitor.py` → feeds `data-feeds/reddit-signals.json`
**Developer brief:** `B-brain/06-growth/technical/data-scraper-SOP-DEVELOPER-READY.md`
**Subreddits monitored:** supplychain, manufacturing, ecommerce, UKBusiness, fashiondesign, sustainability, smallbusiness, Leathercraft, EntrepreneurUK, financeuk
**Cron schedule:** Every 4 hours

**Activation blockers:** Developer must deploy the script + set environment variables on server

---

### Otterly.ai
**Status:** INACTIVE — free trial not started
**Activated:** Not yet
**Monthly cost:** Free trial → ~$49/month (paid tier)
**Where to get it:** https://otterly.ai
**Used by:** CEO manual review — Share of Mind (SoM) tracking

**What it does:**
- Monitors how AI search systems (ChatGPT, Gemini, Perplexity) answer questions in your category
- Tracks brand mentions across AI platforms over time
- Shows competitor SoM vs KritiKaal SoM

**Setup:**
1. Start free trial at otterly.ai
2. Add brand: "KritiKaal"
3. Add competitors: "Fashinza", "Geniemode", "Zetwerk"
4. Add tracked queries: "managed leather manufacturing India", "leather sourcing India UK", "EUDR leather compliance UK", "AQL 2.5 leather factory India"

**Activation blockers:** CEO must create account (personal email + payment method for paid tier)
**CEO action file:** `B-brain/06-growth/CEO-ACTION-CHECKLIST.md` → Action 5

---

### Companies House API
**Status:** INACTIVE — free, no key required for basic use
**Activated:** Not yet
**Monthly cost:** Free
**Where to get it:** https://developer.company-information.service.gov.uk/
**Used by:** researcher-agent, future `scripts/companies-house-monitor.py`

**What it does:**
- UK company financial data (statutory accounts, turnover, COGS ratio)
- SIC code filtering (15120, 47710, 46420) for UK leather brands
- Decision-maker identification via People endpoint

**Capacity:** 600 requests/minute on free tier — sufficient for weekly scans
**Activation blockers:** None (public API, free registration only)

---

### ImportYeti
**Status:** INACTIVE — free tier, manual use only
**Activated:** Not yet
**Monthly cost:** Free (limited searches) / paid for bulk
**Where to get it:** https://www.importyeti.com
**Used by:** researcher-agent — manual research sessions

**What it does:**
- US Bills of Lading (public records): maps which UK brands import from China
- Cross-matches brand names with shipper data
- Identifies China-dependent supply chains — highest-confidence prospect signal

**Activation blockers:** None — free tier usable immediately in research sessions

---

### SE Ranking (SEO monitoring)
**Status:** OPTIONAL — not yet started
**Monthly cost:** ~$49/month (basic)
**Where to get it:** https://seranking.com
**Used by:** CEO manual review — SERP position tracking

**What it tracks:**
- "managed leather manufacturing India" keyword position
- "EUDR leather goods UK" keyword position
- "leather sourcing agent India" and related terms
- Backlinks to kritikaal.com after Article 1 publication

**Activation trigger:** Start tracking when Article 1 is published (so baseline is accurate)

---

### Phantombuster (Month 2 upgrade)
**Status:** NOT YET — planned for Month 2
**When to activate:** If Google Alerts RSS (current LinkedIn feed) produces low signal quality
**Monthly cost:** $56/month (Growth tier)
**Where to get it:** https://phantombuster.com
**Used by:** `scripts/linkedin-monitor.py` — replaces Google Alerts RSS

**What it does:**
- Scrapes LinkedIn posts directly via LinkedIn Search Scraper phantom
- Targets hashtags: #EUDR #leathergoods #indiasourcing #supplychain #sustainablesourcing #ukfashion
- Returns structured JSON with author details (title, company) — fixes the API contract gap in S6

**Developer brief:** Upgrade instructions in `B-brain/06-growth/technical/data-scraper-SOP-DEVELOPER-READY.md` → Upgrade Path section

---

## Environment Variables Required (Summary)

| Variable | Value source | Used by | Status |
|---|---|---|---|
| `REDDIT_CLIENT_ID` | reddit.com/prefs/apps | reddit-monitor.py | NOT SET |
| `REDDIT_CLIENT_SECRET` | reddit.com/prefs/apps | reddit-monitor.py | NOT SET |
| `GPTZERO_API_KEY` | gptzero.me/api | S8 / daily-scout | NOT SET |

---

*API Keys Registry | KritiKaal System | Updated 2026-04-26*
*Update status column whenever a service is activated. This file is the live service dashboard.*
