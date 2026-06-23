# Developer Brief — KritiKaal.com
# Prepared by Adam (COO) | 2026-04-26 | Updated 2026-04-29 (Task 5a added)
# For: Next.js developer
# Status: READY TO IMPLEMENT — all specs written, no design work needed

---

## HOW TO USE THIS BRIEF

All implementation files are already written and exist in the vault. Your job is to take the file referenced in each task and deploy it. No new creative or strategic decisions are required from you.

Tasks are ordered: Priority 1 (deploy immediately) → Priority 2 (deploy this week) → Priority 3 (deploy Month 1).

For questions, contact Yossi (CEO). For file access, all files are in the project vault at `B-brain/06-growth/`.

---

## PRIORITY 1 — Deploy This Week (Critical Path)

---

### Task 1: Deploy robots.txt with AI crawler permissions

**What:** Update the site's robots.txt to explicitly permit AI crawlers (GPTBot, Claude-Web, Gemini) while blocking scrapers. This enables GEO (Generative Engine Optimisation) — AI models can cite KritiKaal content.

**Spec file:** `B-brain/06-growth/technical/robots-txt-DEVELOPER-READY.md`

**Action:** Read the spec file. The exact robots.txt content is in the file. Replace or create `/public/robots.txt` with the specified content.

**Verification:** After deploy, visit `https://www.kritikaal.com/robots.txt` — confirm content matches spec.

**Time estimate:** 15 minutes.

---

### Task 2: Deploy llms.txt

**What:** Create a new file at `https://www.kritikaal.com/llms.txt`. This is an emerging standard that tells AI systems how to understand and cite your site. No existing standard conflicts with this.

**Spec file:** `B-brain/06-growth/technical/llms-txt-v2-FINAL.md`

**Action:** Read the spec file. The exact llms.txt content is in the file. Create `/public/llms.txt` with the specified content.

**Verification:** After deploy, visit `https://www.kritikaal.com/llms.txt` — confirm plain text file loads.

**Time estimate:** 15 minutes.

---

### Task 3: Create /blog section and confirm URL structure

**What:** Confirm whether kritikaal.com has a `/blog` route. If not, create one. Individual blog posts should resolve at `/blog/[slug]`.

**Required URL for Article 1:** `https://www.kritikaal.com/blog/eudr-india-leather-uk-brands`

**Action:**
1. Confirm or create `/blog` section in Next.js routing
2. Confirm individual posts resolve at `/blog/[slug]`
3. Reply to Yossi with the confirmed URL structure

**No content work needed from you** — the article file is ready (see Task 4). Just confirm the routing exists.

**Time estimate:** 30–60 minutes if route needs creating.

---

### Task 4: Publish Article 1 to CMS/blog

**What:** Publish the EUDR article to the live blog. Content is fully written, edited, and approved. No copy changes needed.

**Content file:** `B-brain/06-growth/content/FOR-DEVELOPER/article-01-eudr-india-leather-PUBLICATION-READY.md`

**Target URL:** `https://www.kritikaal.com/blog/eudr-india-leather-uk-brands`

**Action:**
1. Read the content file — it contains the complete article with title, headings, body, and metadata notes
2. Create the blog post in your CMS at the specified slug
3. Publish (or set to scheduled publish — confirm date with Yossi)

**Important:** The article uses cluster language only (no specific factory names or facility locations). Do not add any facility names or supply chain specifics.

**Time estimate:** 30 minutes to format and publish.

---

### Task 5: Deploy Schema JSON-LD structured data

**What:** Add JSON-LD structured data to the homepage `<head>`. This enables rich results in Google and citation markup for AI systems.

**Spec file:** `B-brain/06-growth/technical/schema-jsonld-DEVELOPER-READY.html`

**Status:** File has 3 placeholders that CEO must fill before you deploy. Check with Yossi whether he has provided:
1. `[YOUR_LINKEDIN_PROFILE_URL]` — e.g. `https://www.linkedin.com/in/yossi-daniel`
2. `[FOUNDING_YEAR]` — e.g. `2023`
3. `[LOGO_URL]` — e.g. `https://www.kritikaal.com/logo.png`

**Action:** Once CEO confirms all 3 values are filled in the spec file, add the JSON-LD script block to homepage `<head>`.

**Verification:** After deploy, use Google's Rich Results Test (`search.google.com/test/rich-results`) to confirm valid schema.

**Time estimate:** 20 minutes once placeholders are confirmed.

---

### Task 5a: Deploy FAQPage JSON-LD schema *(Added 2026-04-29)*

**What:** Add FAQPage structured data to the FAQ page `<head>`. This is the highest-leverage GEO (Generative Engine Optimisation) asset in the brief — it directly enables Google AI Overviews and AI citation systems (ChatGPT, Perplexity, Gemini) to pull KritiKaal answers verbatim from the FAQ page.

**Spec file:** `B-brain/06-growth/technical/faq-jsonld-DEVELOPER-READY.html`

**Status:** File is complete. No placeholders. No CEO input required before deployment.

**Action:**
1. Read the spec file — it contains a single `<script type="application/ld+json">` block
2. Add this block to the `<head>` of the FAQ page (`https://www.kritikaal.com/faq` or equivalent slug)
3. The FAQ page content must also match the 29 Q&A pairs in `B-brain/06-growth/content/FOR-DEVELOPER/faq-PUBLICATION-READY.md` — if the FAQ page is not yet live, create it from that file first

**FAQ content source for the page itself:** `B-brain/06-growth/content/FOR-DEVELOPER/faq-PUBLICATION-READY.md` (29 questions — 28 original + 1 new EUDR question)

**Verification:** After deploy, test at `https://search.google.com/test/rich-results` — enter the FAQ page URL, confirm FAQPage entity detected with 29 entries.

**Why this is Priority 1:** FAQPage JSON-LD is the fastest path to AI citation. Google AI Overviews pull directly from FAQPage entities. Every day this is not deployed, competitor FAQ pages can be cited instead of KritiKaal's.

**Time estimate:** 20 minutes (schema is written; this is a copy-paste deploy).

---

## PRIORITY 2 — Deploy This Week (Site Fixes)

These are live site errors identified in the site audit. All are small changes.

---

### Task 6: Remove MOQ from product cards

**What:** The phrase "Minimum Order Quantity" or MOQ appears on approximately 34 product cards across the site. KritiKaal serves The Missing Middle (300–3,000 units) — displaying a specific MOQ number prematurely screens out anchor-tier leads who start with questions, not order volumes.

**Action:** Remove the MOQ field/text from all product cards sitewide. Do not replace with alternative text — just remove.

**Verification:** Check 5 product cards after change — confirm MOQ language is gone.

**Time estimate:** 30–60 minutes (if product card component is centralised, 15 minutes).

---

### Task 7: Fix /why-india comparison table headers

**What:** The comparison table on `/why-india` has misaligned or incorrect column headers. The table compares KritiKaal vs competitors but headers are unclear.

**Action:** Check `/why-india` table. Confirm column headers read: KritiKaal | Competitor Platforms (or similar clear labelling). Fix any header that is blank, misaligned, or confusing.

**Verification:** View `/why-india` on mobile and desktop — table headers must be clearly readable.

**Time estimate:** 20 minutes.

---

### Task 8: Fix /bookacall timezone display

**What:** The booking calendar on `/bookacall` displays timezone incorrectly — it does not show "United Kingdom" / GMT+0/BST as the default timezone. UK procurement directors see the wrong timezone and drop off.

**Action:** Set the booking widget (Calendly or equivalent) default timezone to "Europe/London" / United Kingdom. Confirm the label displayed to users shows "United Kingdom" or "GMT+1 (BST)".

**Verification:** Open `/bookacall` in an incognito window — confirm UK timezone is displayed by default.

**Time estimate:** 15 minutes.

---

### Task 9: Replace "World-Class Quality" text on /why-india

**What:** The phrase "World-Class Quality" appears on the `/why-india` page. This is generic marketing language that the Voice DNA explicitly bans. It weakens the technical credibility of the page.

**Action:** Replace "World-Class Quality" with: `AQL 2.5 — the premium inspection standard used by LVMH and Hermès supply chains`

(Or shorter variant if space is limited: `AQL 2.5 Inspection Standard`)

**Verification:** View `/why-india` — confirm "World-Class Quality" no longer appears anywhere on the page.

**Time estimate:** 10 minutes.

---

### Task 9b: Configure UTM-tagged booking links for social attribution *(Added 2026-04-30)*

**What:** The Authority Engine will generate Reddit and LinkedIn posts driving traffic to `/bookacall`. Without UTM parameters on those links, there is no way to know which booking came from which platform or post. This is the minimum viable conversion tracking for the social media Authority Engine.

**Action:**
1. Confirm the booking widget (Calendly or equivalent) accepts UTM parameters in the URL and passes them through to the booking confirmation event
2. If UTM passthrough is not native to the widget, create redirect routes in Next.js that capture UTM params before redirecting to the booking widget
3. Ensure the following URLs resolve correctly to the booking page:
   - `https://www.kritikaal.com/bookacall?utm_source=reddit&utm_medium=comment`
   - `https://www.kritikaal.com/bookacall?utm_source=linkedin&utm_medium=comment`
   - `https://www.kritikaal.com/bookacall?utm_source=linkedin&utm_medium=post`
4. Verify UTM data is captured in your analytics platform (Google Analytics 4 or equivalent) as a traffic source dimension on the booking conversion event

**Verification:** Click each UTM URL — confirm page loads and analytics registers the correct source/medium.

**Note for CEO:** When Yossi posts to Reddit or LinkedIn, he uses the UTM-tagged URL as his CTA link — not the bare `/bookacall`. This is a 5-second habit change with 100% attribution benefit.

**Time estimate:** 30 minutes (15 if Calendly UTM passthrough is already enabled).

---

## PRIORITY 3 — Deploy Month 1 (Authority Engine Infrastructure)

These require server-side setup beyond the Next.js frontend.

---

### Task 10: Deploy reddit-monitor.py with cron

**What:** A Python script that monitors 10 subreddits every 4 hours for KritiKaal-relevant posts. Output is a JSON file that feeds the `/daily-scout` command.

**Spec file:** `B-brain/06-growth/technical/data-scraper-SOP-DEVELOPER-READY.md` → Script 1

**Prerequisites:**
- Python 3.x on server
- `pip install praw`
- Reddit API credentials (Yossi will provide: `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`)

**Action:**
1. Read Script 1 in the spec file
2. Create `scripts/reddit-monitor.py` in project root
3. Create `logs/` folder for cron output
4. Set environment variables on server
5. Add cron job: `0 */4 * * * cd /your/project/path && python3 scripts/reddit-monitor.py >> logs/reddit.log 2>&1`
6. Test manually: `python3 scripts/reddit-monitor.py`
7. Confirm `B-brain/06-growth/data-feeds/reddit-signals.json` is created

**Time estimate:** 1.5–2 hours including Reddit API setup and first test run.

---

### Task 11: Deploy linkedin-monitor.py with Google Alerts RSS

**What:** A Python script that pulls LinkedIn-adjacent signals from Google Alerts RSS feeds daily at 06:00 UK. Output is a JSON file that feeds the `/daily-scout` command.

**Spec file:** `B-brain/06-growth/technical/data-scraper-SOP-DEVELOPER-READY.md` → Script 2

**Prerequisites:**
- Python 3.x on server
- `pip install feedparser`
- 7 Google Alerts RSS URLs (Yossi will create these — see spec file for exact queries)

**Action:**
1. Read Script 2 in the spec file — note the Google Alerts setup instructions (Yossi creates 7 alerts, you get the RSS URLs from him)
2. Once Yossi provides 7 RSS URLs, paste them into the `RSS_FEEDS` list in the script
3. Create `scripts/linkedin-monitor.py` in project root
4. Add cron job: `0 5 * * * cd /your/project/path && python3 scripts/linkedin-monitor.py >> logs/linkedin.log 2>&1`
5. Test manually
6. Confirm `B-brain/06-growth/data-feeds/linkedin-signals.json` is created

**Time estimate:** 1–1.5 hours including Google Alerts setup coordination.

---

### Task 12: Set environment variables on server

**What:** Three environment variables required by the Authority Engine scripts.

| Variable | Who provides the value |
|---|---|
| `REDDIT_CLIENT_ID` | Yossi (from reddit.com/prefs/apps) |
| `REDDIT_CLIENT_SECRET` | Yossi (from reddit.com/prefs/apps) |
| `GPTZERO_API_KEY` | Yossi (from gptzero.me/api — requires $10/mo subscription) |

**Action:** Once Yossi provides values, set as server environment variables (`.env` file or hosting panel). Never commit these to git.

**Time estimate:** 10 minutes once values are provided.

---

## SUMMARY TABLE

| # | Task | Priority | Est. Time | Spec File | Status |
|---|---|---|---|---|---|
| 1 | robots.txt AI permissions | 1 — Deploy now | 15 min | `technical/robots-txt-DEVELOPER-READY.md` | Ready |
| 2 | llms.txt | 1 — Deploy now | 15 min | `technical/llms-txt-v2-FINAL.md` | Ready |
| 3 | /blog section + URL confirm | 1 — Deploy now | 30–60 min | — (confirm routing) | Ready |
| 4 | Article 1 publication | 1 — Deploy now | 30 min | `content/FOR-DEVELOPER/article-01-eudr-india-leather-PUBLICATION-READY.md` | Ready (pending blog URL) |
| 5 | Schema JSON-LD (homepage) | 1 — Deploy now | 20 min | `technical/schema-jsonld-DEVELOPER-READY.html` | Waiting for 3 CEO values |
| 5a | FAQPage JSON-LD ⭐ NEW | 1 — Deploy now | 20 min | `technical/faq-jsonld-DEVELOPER-READY.html` | **Ready — no placeholders** |
| 6 | Remove MOQ from 34 product cards | 2 — This week | 30–60 min | — (site edit) | Ready |
| 7 | Fix /why-india table headers | 2 — This week | 20 min | — (site edit) | Ready |
| 8 | Fix /bookacall timezone | 2 — This week | 15 min | — (widget setting) | Ready |
| 9 | Replace "World-Class Quality" text | 2 — This week | 10 min | — (site edit) | Ready |
| 9b | UTM tracking on /bookacall links NEW | 2 — This week | 30 min | — (redirect + analytics) | Ready |
| 10 | reddit-monitor.py + cron | 3 — Month 1 | 1.5–2 hrs | `technical/data-scraper-SOP-DEVELOPER-READY.md` | Waiting for Reddit credentials |
| 11 | linkedin-monitor.py + RSS | 3 — Month 1 | 1–1.5 hrs | `technical/data-scraper-SOP-DEVELOPER-READY.md` | Waiting for Google Alerts URLs |
| 12 | Set environment variables | 3 — Month 1 | 10 min | — (server config) | Waiting for CEO values |

**Total Priority 1 time:** ~2.5 hours (Task 5a adds 20 min — fully written, no blockers)
**Total Priority 2 time:** ~2 hours (Task 9b adds 30 min)
**Total Priority 3 time:** ~3–4 hours

---

*Developer Brief | KritiKaal | 2026-04-26 | Prepared by Adam (COO)*
*Single file replaces scattered instructions. Questions → Yossi (CEO).*
