# Data Feeds — KritiKaal Shadow Board
# Ground truth inputs for S1 (Chief Strategy Officer)

**Status:** NOT YET LIVE — scrapers deploy on Day 10 (developer scoping call)
**Current mode:** FALLBACK — S1 uses G1 intelligence only until feeds are live

---

## Expected Feed Files

When scrapers are live, this folder will contain three JSON files updated weekly
(Saturday night, before Sunday 8pm board meeting trigger):

### 1. `weekly-trade-data.json`
**Source:** ImportYeti UK customs data
**Data captured:** UK leather goods import volume by supplier country; trend direction week-on-week; top importing UK brands by volume
**Update frequency:** Weekly — Saturday 23:00 UK
**S1 uses this to:** Identify UK brands actively importing leather and shifting sourcing country

```json
{
  "last_updated": "YYYY-MM-DD",
  "source": "ImportYeti",
  "period": "last_30_days",
  "uk_leather_imports": [],
  "top_importing_brands": [],
  "country_trend": {}
}
```

### 2. `linkedin-signals.json`
**Source:** LinkedIn public job postings (scraper on public data)
**Data captured:** UK fashion brands posting procurement, sourcing, or supply chain roles; job title, company, posting date
**Update frequency:** Weekly — Saturday 23:00 UK
**S1 uses this to:** Identify brands actively rebuilding sourcing infrastructure (strong buying signal)

```json
{
  "last_updated": "YYYY-MM-DD",
  "source": "LinkedIn public postings",
  "signals": [],
  "high_priority_companies": []
}
```

### 3. `companies-house.json`
**Source:** Companies House API (UK government — free)
**Data captured:** UK fashion brand entities with recent director changes, capital raises, or new company registrations; filtered to SIC codes 14110-14190 (leather and textile manufacture/retail)
**Update frequency:** Weekly — Saturday 23:00 UK
**S1 uses this to:** Identify UK brands in growth or transition phases (fundraised = buying season incoming)

```json
{
  "last_updated": "YYYY-MM-DD",
  "source": "Companies House API",
  "recent_raises": [],
  "director_changes": [],
  "new_entities": []
}
```

---

## Developer Setup Notes (Day 10)

Three lightweight scrapers. Target runtime: <5 minutes each. Run on Saturday night via cron.

| Scraper | Source | Auth required | Estimated dev time |
|---|---|---|---|
| UK customs / ImportYeti | ImportYeti.com | Free account | 1–2 hours |
| LinkedIn job postings | Public HTML scrape | None (public data) | 1–2 hours |
| Companies House | Official API | Free API key | 30 minutes |

**Output format:** JSON files saved directly to this folder.
**No database required.** Files are read directly by S1 during board meeting execution.
**Failure mode:** If a scraper fails, the file is missing. S1 detects missing files and switches to fallback mode automatically.

---

## Fallback Protocol

If any feed file is missing or contains a `last_updated` date more than 8 days old:
- S1 flags: `DATA FEED STALE OR MISSING — [feed name]`
- S1 operates on G1 intelligence only for that signal category
- S5 flags the gap in System Health under "Data feeds status: FALLBACK"
- CEO does not need to take action — the system degrades gracefully

---

*Data Feeds | KritiKaal Shadow Board | Initialised 2026-04-23 | Scrapers: pending Day 10*
