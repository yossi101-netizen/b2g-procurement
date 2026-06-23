# CEO Action Checklist — KritiKaal Authority Engine
# 7 personal actions only you can take. Ordered by impact × speed.
# Prepared by Adam (COO) | 2026-04-26
# Status: LIVE — work through this top to bottom

---

## How to use this file

Each action is blocked by you personally — no developer, no Adam. When you complete an action, mark it `[DONE]` and note the date. Each completed action unblocks something downstream. The unblocking chain is shown for each item.

---

## ACTION 1 — Reddit Account: Create + Verify (30 minutes)
**Priority: HIGHEST — every day without an account is a day the karma clock doesn't run**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**Exact steps:**
1. From home network (NOT VPN, NOT office network — Reddit flags unusual IPs)
2. Go to: `https://www.reddit.com/register`
3. Create account — use a personal, non-branded username (not "KritiKaal" or "Yossi" — something neutral)
4. Immediately: Settings → Account → Add phone number (verification SMS)
5. Immediately: Settings → Account → Confirm email address
6. Both verifications move CQS from "New" to "Moderate" — this is the only way to bypass the 6-hour new-account shadow period

**What unlocks:** The Authority Engine (/daily-scout) can generate Reddit drafts but they can't be posted until this account exists at "Moderate" CQS. Warm-up phase: Weeks 1-2 post only in r/AskUK, r/CasualConversation, r/UKFoods, r/unitedkingdom (see `social-queue/README.md`).

**Record your username here (no password):** `reddit_username: ___________`

---

## ACTION 2 — GPTZero API Key: Get + Set (20 minutes)
**Priority: HIGH — S8 (Humanization Layer) is non-functional without this key**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**Exact steps:**
1. Go to: `https://gptzero.me/api`
2. Create account with your email
3. Choose Standard tier: $10/month (covers 150 checks/month — exactly what the system needs)
4. Copy the API key
5. In Claude Code terminal, run: `claude config set env.GPTZERO_API_KEY your_key_here`
   OR add to `.env` file in project root: `GPTZERO_API_KEY=your_key_here`

**What unlocks:** S8 humanization verification. Without it, /daily-scout still generates drafts but skips the GPTZero scoring step — drafts are delivered unverified. Post-key: every draft gets a human score before it reaches you.

**Update `B-brain/03-api-keys-registry.md`** when done — mark GPTZero as Active with today's date.

---

## ACTION 3 — LinkedIn Profile: Update (15 minutes)
**Priority: HIGH — Authority Engine LinkedIn posts point back to your profile; it must be live before posting begins**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**Exact steps:**
1. Open: `B-brain/06-growth/linkedin-profile-copy.md` (already written — copy-paste ready)
2. Go to: `https://www.linkedin.com/in/[your-profile]/`
3. Edit → paste Headline (156 characters — ready to copy)
4. Edit → paste About section (250 words — ready to copy)
5. Edit Skills → add the 10 skills listed
6. Featured section: add /bookacall link NOW. Add article link once developer deploys the blog.

**What unlocks:** All LinkedIn content from S7/S8 drives back to this profile. A weak profile converts zero engagement. This profile converts warm readers to qualification calls.

---

## ACTION 4 — Schema JSON-LD Placeholders: Provide 3 Values (5 minutes)
**Priority: HIGH — Developer cannot deploy Schema without these. Blocks structured data entirely.**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**The 3 values needed:**

| Placeholder | What to put | Where to find it |
|---|---|---|
| `[YOUR_LINKEDIN_PROFILE_URL]` | Full LinkedIn URL e.g. `https://www.linkedin.com/in/yossi-daniel` | Your LinkedIn profile page |
| `[FOUNDING_YEAR]` | 4-digit year KritiKaal was founded e.g. `2023` | You know this |
| `[LOGO_URL]` | Full URL to KritiKaal logo on your site e.g. `https://www.kritikaal.com/logo.png` | Ask your developer or check site assets |

**Once you have these 3 values:** Tell Adam (type them in this session or a new session). Adam edits `B-brain/06-growth/technical/schema-jsonld-DEVELOPER-READY.html` in under 60 seconds. Developer deploys same day.

---

## ACTION 5 — Otterly.ai Free Trial: Start (10 minutes)
**Priority: MEDIUM — SoM (Share of Mind) baseline cannot be measured without this tool**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**Exact steps:**
1. Go to: `https://otterly.ai`
2. Start free trial (no credit card required on free tier)
3. Add your brand: "KritiKaal"
4. Add competitors: "Fashinza", "Geniemode", "Zetwerk"
5. Add keywords to track: "managed leather manufacturing India", "leather sourcing India UK", "EUDR leather compliance", "AQL 2.5 leather factory"
6. Run your first report — screenshot or export it as `som-week-00-baseline.md` baseline

**What unlocks:** SoM tracking. Without this, you cannot measure whether the Authority Engine's content is moving the needle in AI search results.

**Update `B-brain/03-api-keys-registry.md`** when done — mark Otterly.ai as Active.

---

## ACTION 6 — SoM Baseline: Run Queries in ChatGPT + Gemini (20 minutes)
**Priority: MEDIUM — establishes Week 0 baseline before Authority Engine output begins**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**Exact steps:**
1. Open: `B-brain/06-growth/som-week-00-baseline.md` (file is ready — contains exact queries to run)
2. Open ChatGPT (https://chat.openai.com) — use a new chat each time
3. Run each query, paste the response into the file
4. Open Google Gemini (https://gemini.google.com) — new chat each time
5. Run the same queries, paste responses
6. Note whether KritiKaal is mentioned anywhere in any response

**Why production interfaces matter:** API responses and production UI responses differ. SoM measures what users actually see. Do not use the Claude API or any other programmatic interface for this test.

---

## ACTION 7 — Blog Section Confirmation: Verify with Developer (5 minutes)
**Priority: MEDIUM — Article 1 is publication-ready but has nowhere to land**

```
Status: [ ] TODO → [ ] IN PROGRESS → [ ] DONE
Completed date: ___________
```

**Exact steps:**
1. Contact your Next.js developer
2. Ask: "Does kritikaal.com have a /blog section? If yes, what's the exact URL structure? If no, can you create one at /blog with individual posts at /blog/[slug]?"
3. Confirm the slug for Article 1 will be: `eudr-india-leather-uk-brands`
4. Final URL should be: `https://www.kritikaal.com/blog/eudr-india-leather-uk-brands`
5. Note the answer here: `blog_status: ___________`

**What unlocks:** Developer can publish Article 1. LinkedIn Featured section Article link can go live. EUDR authority content reaches the UK market before the June 2026 deadline.

---

## COMPLETION TRACKER

| # | Action | Done | Date | Unlocks |
|---|---|---|---|---|
| 1 | Reddit account + verification | [ ] | | /daily-scout Reddit drafts can be posted |
| 2 | GPTZero API key | [ ] | | S8 humanization verification active |
| 3 | LinkedIn profile update | [ ] | | LinkedIn content converts; Authority Engine live |
| 4 | Schema placeholders (3 values) | [ ] | | Adam edits file → developer deploys structured data |
| 5 | Otterly.ai trial | [ ] | | SoM tracking active |
| 6 | SoM baseline queries | [ ] | | Week 0 baseline locked in |
| 7 | Blog section confirmation | [ ] | | Article 1 can be published; EUDR window opens |

---

## TOTAL TIME ESTIMATE

All 7 actions: **~105 minutes** if done in one session, or spread across 2 days.

**Suggested sequence if doing in one session:**
Morning block (45 min): Actions 1, 2, 3
Afternoon block (30 min): Actions 5, 6
Next day (30 min): Actions 4 (needs developer input), 7 (needs developer contact)

---

*CEO Action Checklist | KritiKaal Authority Engine | 2026-04-26*
*This file replaces the scattered action items across the audit report. One file. Seven actions. Nothing else needed from Yossi.*
