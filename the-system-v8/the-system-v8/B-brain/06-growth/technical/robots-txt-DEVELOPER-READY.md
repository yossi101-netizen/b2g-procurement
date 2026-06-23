# Developer Ready Package — robots.txt AI Crawler Permissions
# Prepared by G3 (Technical SEO Auditor)
# Date: 2026-04-22 | Status: CEO APPROVED — Deploy immediately

---

## WHAT THIS IS

A standalone AI crawler permissions block for kritikaal.com/robots.txt.

These User-agent entries explicitly permit GPTBot (ChatGPT), Googlebot-Extended (Gemini), PerplexityBot, ClaudeBot (Claude/Anthropic), anthropic-ai, and CCBot to crawl the entire kritikaal.com domain — including the llms.txt file, all blog articles, and all core pages.

**Why this matters:** Framer, Webflow, Vercel, and most modern site builders block AI crawlers in their default robots.txt configuration. Without these entries, GPTBot and Googlebot-Extended cannot index KritiKaal's content — meaning ChatGPT and Gemini cannot cite us regardless of how good our content is. This is the gate that must open before any GEO strategy can function.

**Estimated deployment time: 2 minutes.**

---

## DEPLOYMENT INSTRUCTIONS

**Do NOT replace the existing robots.txt file.**
Add the block below to the bottom of the existing file.

If no robots.txt exists at kritikaal.com/robots.txt, create one at the public root with the content below (omitting the preface comment block).

**Verification:** After deployment, visit `https://kritikaal.com/robots.txt` in a browser. Confirm the six new User-agent entries are visible in the file.

**Crawl lag:** GPTBot should visit within 14 days of this update. Googlebot-Extended typically within 7 days. ClaudeBot within 3–4 weeks.

---

## THE FILE — COPY AND PASTE TO BOTTOM OF EXISTING robots.txt

```
# ================================================================================
# DEVELOPER PREFACE — READ BEFORE DEPLOYING
# ================================================================================
#
# FILE PURPOSE:
#   This block grants explicit crawl permission to six AI crawler User-agents.
#   It must be added to the existing kritikaal.com/robots.txt file.
#   Without these lines, AI models (ChatGPT, Gemini, Perplexity, Claude) cannot
#   index kritikaal.com content and cannot cite KritiKaal in responses.
#
# EXACT PLACEMENT:
#   Add to the BOTTOM of the existing robots.txt file at kritikaal.com/robots.txt.
#   Do NOT replace the existing file. Only add this block.
#   If no robots.txt exists, create one at the public root containing this block.
#
# ACTION REQUIRED:
#   DELETE THIS PREFACE (all lines beginning with "#" in the preface section)
#   before deploying. The User-agent entries below are NOT comments — they are
#   functional directives and must remain in the file.
#
#   SAFE IF FORGOTTEN: Comment lines are ignored by all crawlers and browsers.
#   The preface will not break functionality if left in — but removing it
#   produces a cleaner, more readable robots.txt file.
#
# VERIFY DEPLOYMENT:
#   Visit https://kritikaal.com/robots.txt and confirm all six User-agent
#   entries appear in the live file.
#
# ================================================================================

# ------------------------------------------------
# AI Crawler Permissions — KritiKaal GEO Infrastructure
# Added: 2026-04-22
# Purpose: Enable ChatGPT, Gemini, Perplexity, and Claude to crawl and cite kritikaal.com
# ------------------------------------------------

User-agent: GPTBot
Allow: /

User-agent: Googlebot-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: CCBot
Allow: /
```

---

## POST-DEPLOYMENT VERIFICATION CHECKLIST

- [ ] Visit `https://kritikaal.com/robots.txt` — confirm all six User-agent entries are live
- [ ] Existing robots.txt rules above the new block are unchanged
- [ ] No existing `Disallow: /` or blanket bot-blocking rules override the new entries
- [ ] Also verify `https://kritikaal.com/llms.txt` is accessible (no robots.txt redirect blocking it)

**If you find an existing `User-agent: *` block with `Disallow: /`:**
Check whether it is meant to block all bots or only non-essential crawlers. If it blocks everything, the new AI crawler entries must be placed ABOVE the catch-all block — in robots.txt, the first matching rule wins for most crawlers.

---

## WHAT TO MONITOR AFTER DEPLOYMENT

Check Cloudflare Analytics → Traffic → filter by User-Agent within 14 days:

| Crawler | Expected First Visit | What It Means |
|---|---|---|
| GPTBot | Within 14 days | ChatGPT has discovered and crawled kritikaal.com |
| Googlebot-Extended | Within 7 days | Gemini is indexing for AI Overviews |
| ClaudeBot | Within 21–28 days | Claude/Anthropic has indexed the site |
| PerplexityBot | Within 14 days | Perplexity is crawling for citations |

**Key G3 finding (Q1 2026):** GPTBot and ClaudeBot began consuming sitemaps for the first time in March 2026. If a sitemap.xml exists at kritikaal.com/sitemap.xml, submitting it to Google Search Console and Bing Webmaster Tools now will accelerate all AI crawler discovery times.

---

*robots.txt Developer Ready Package | G3 (Technical SEO Auditor) | KritiKaal Growth Team | 2026-04-22*
