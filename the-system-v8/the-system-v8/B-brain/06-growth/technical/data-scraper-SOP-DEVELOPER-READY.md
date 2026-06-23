# Data Scraper SOP — Developer Ready Package
# KritiKaal Authority Engine
# Prepared by Adam (COO) | Status: CEO APPROVED
# Date: 2026-04-25 | Estimated total dev time: 3–4 hours

---

## OVERVIEW

Two Python scripts. Run on cron schedule. Output is JSON files read directly by the `/daily-scout` Claude Code command.

No database required. No server required beyond what already hosts the Next.js site.
Scripts can run on the same server/VPS, on a free-tier cloud function, or locally via Windows Task Scheduler.

Output path for both scripts: `B-brain/06-growth/data-feeds/`
(Adjust to absolute path on your server — must match where Claude Code reads from)

---

## SCRIPT 1 — `reddit-monitor.py`

**Purpose:** Monitor 10 target subreddits every 4 hours. Capture posts mentioning KritiKaal-relevant keywords. Score by recency and relevance. Save top 20 opportunities to JSON.

**Prerequisites:**
```bash
pip install praw
```

**Reddit API setup (5 minutes):**
1. Go to `https://www.reddit.com/prefs/apps`
2. Click "Create App"
3. Type: `script`
4. Name: `KritiKaal Scout`
5. Redirect URI: `http://localhost:8080`
6. Copy the `client_id` (under the app name) and `client_secret`
7. Set as environment variables:
   ```
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   ```

**The script:**

```python
import praw
import json
import os
from datetime import datetime, timezone

# --- CONFIGURATION ---
TARGET_SUBREDDITS = [
    'supplychain', 'manufacturing', 'ecommerce', 'UKBusiness',
    'fashiondesign', 'sustainability', 'smallbusiness', 'Leathercraft',
    'EntrepreneurUK', 'financeuk'
]

KEYWORDS_PRIMARY = [
    'leather', 'EUDR', 'india manufacturing', 'managed manufacturing',
    'leather sourcing', 'leather goods', 'leather supply chain'
]

KEYWORDS_SECONDARY = [
    'supply chain', 'sourcing agent', 'procurement', 'china plus one',
    'factory quality', 'AQL', 'LWG', 'BSCI', 'deforestation regulation',
    'uk sourcing', 'india sourcing', 'uk fashion'
]

# Output path — adjust to absolute path on your server
OUTPUT_PATH = 'B-brain/06-growth/data-feeds/reddit-signals.json'

# --- REDDIT CLIENT ---
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    user_agent='KritiKaal Scout 1.0 (by /u/your_reddit_username)'
)

# --- SCORING ---
def score_opportunity(post, matched_keywords):
    score = 0
    now = datetime.now(timezone.utc).timestamp()
    age_hours = (now - post.created_utc) / 3600

    # Recency scoring — hard exclude >6 hours
    if age_hours < 2:
        score += 30
    elif age_hours < 4:
        score += 20
    elif age_hours < 6:
        score += 10
    else:
        return 0  # Too old — exclude entirely

    # Upvote ratio
    if post.upvote_ratio > 0.85:
        score += 20
    elif post.upvote_ratio > 0.70:
        score += 15

    # Keyword relevance
    primary_hits = sum(1 for kw in KEYWORDS_PRIMARY if kw in matched_keywords)
    secondary_hits = sum(1 for kw in KEYWORDS_SECONDARY if kw in matched_keywords)
    score += min(primary_hits, 1) * 25  # Max 1 primary hit counted
    score += min(secondary_hits, 1) * 15  # Max 1 secondary hit counted

    # Subreddit authority tier
    high_value_subs = ['supplychain', 'manufacturing', 'ecommerce']
    if post.subreddit.display_name.lower() in high_value_subs:
        score += 15
    else:
        score += 5

    # Active conversation (not too quiet, not saturated)
    if 5 <= post.num_comments <= 20:
        score += 10

    return min(score, 100)

# --- MAIN SCAN ---
opportunities = []

for sub_name in TARGET_SUBREDDITS:
    try:
        sub = reddit.subreddit(sub_name)
        for post in sub.new(limit=50):
            combined_text = (post.title + ' ' + (post.selftext or '')).lower()
            matched = [kw for kw in KEYWORDS_PRIMARY + KEYWORDS_SECONDARY
                      if kw in combined_text]

            if not matched:
                continue

            age_hours = (datetime.now(timezone.utc).timestamp() - post.created_utc) / 3600
            score = score_opportunity(post, matched)

            if score == 0:
                continue

            hours_remaining = max(0, round(6 - age_hours, 1))

            opportunities.append({
                'subreddit': f'r/{post.subreddit.display_name}',
                'post_title': post.title,
                'post_url': f'https://reddit.com{post.permalink}',
                'post_age_hours': round(age_hours, 1),
                'upvote_ratio': post.upvote_ratio,
                'comment_count': post.num_comments,
                'relevance_keywords': matched,
                'window_status': f'OPEN — {hours_remaining} hours remaining',
                'opportunity_score': score
            })

    except Exception as e:
        print(f'Error scanning r/{sub_name}: {e}')
        continue

# Sort by score, keep top 20 for S6 to filter to 5
opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

output = {
    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'source': 'Reddit PRAW API',
    'scan_timestamp_utc': datetime.utcnow().isoformat(),
    'subreddits_scanned': TARGET_SUBREDDITS,
    'opportunities': opportunities[:20]
}

# Write output
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f'Reddit monitor complete: {len(opportunities)} opportunities found at {datetime.now()}')
```

**Cron schedule (runs every 4 hours):**
```bash
0 */4 * * * cd /your/project/path && python3 scripts/reddit-monitor.py >> logs/reddit.log 2>&1
```

**Dev time estimate:** 1.5–2 hours including setup and first test run.

---

## SCRIPT 2 — `linkedin-monitor.py`

**Purpose:** Pull LinkedIn-adjacent signals from Google Alerts RSS feeds daily at 06:00 UK. Save opportunities to JSON.

**Prerequisites:**
```bash
pip install feedparser
```

**Google Alerts setup (15 minutes — one-time):**

1. Go to `https://google.com/alerts`
2. Create ONE alert for each query below (7 alerts total):
   - `site:linkedin.com EUDR leather`
   - `site:linkedin.com "India sourcing" fashion`
   - `site:linkedin.com "managed manufacturing"`
   - `site:linkedin.com "leather goods" procurement`
   - `site:linkedin.com "supply chain" UK leather`
   - `site:linkedin.com EUDR "supply chain"`
   - `site:linkedin.com "China plus one" sourcing`
3. For each alert: set **Deliver to** → **RSS Feed**
4. After creating, click the RSS icon — copy that URL
5. Paste the 7 RSS URLs into the `RSS_FEEDS` list below

**The script:**

```python
import feedparser
import json
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Paste your 7 Google Alerts RSS URLs here after setup
RSS_FEEDS = [
    # 'https://www.google.com/alerts/feeds/XXXXX/YYYYY',  # EUDR leather
    # 'https://www.google.com/alerts/feeds/XXXXX/YYYYY',  # India sourcing fashion
    # Add all 7 feeds here
]

# Output path — adjust to absolute path on your server
OUTPUT_PATH = 'B-brain/06-growth/data-feeds/linkedin-signals.json'

# Only include posts from last 48 hours
CUTOFF_HOURS = 48

# --- MAIN SCAN ---
opportunities = []
cutoff_time = datetime.now() - timedelta(hours=CUTOFF_HOURS)

for feed_url in RSS_FEEDS:
    try:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            # Parse publication date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            else:
                published = datetime.now()  # Default to now if no date

            if published < cutoff_time:
                continue

            age_hours = round((datetime.now() - published).total_seconds() / 3600, 1)

            # Only include if URL contains linkedin.com
            entry_url = entry.get('link', '')
            if 'linkedin.com' not in entry_url:
                continue

            opportunities.append({
                'platform': 'LinkedIn',
                'post_title': entry.get('title', 'No title'),
                'post_snippet': entry.get('summary', '')[:400],
                'post_url': entry_url,
                'posted_hours_ago': age_hours,
                'opportunity_type': 'LinkedIn expert comment opportunity',
                'source_feed': feed_url
            })

    except Exception as e:
        print(f'Error parsing feed {feed_url}: {e}')
        continue

# Sort by recency
opportunities.sort(key=lambda x: x['posted_hours_ago'])

# Check if setup is complete
setup_status = 'ACTIVE' if RSS_FEEDS else 'SETUP_REQUIRED'
if not RSS_FEEDS:
    print('WARNING: No RSS feeds configured. Add Google Alerts RSS URLs to RSS_FEEDS list.')

output = {
    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'source': 'Google Alerts RSS (LinkedIn)',
    'setup_status': setup_status,
    'feeds_configured': len(RSS_FEEDS),
    'opportunities': opportunities
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f'LinkedIn monitor complete: {len(opportunities)} opportunities found at {datetime.now()}')
```

**Cron schedule (runs daily at 06:00 UK / 05:00 UTC):**
```bash
0 5 * * * cd /your/project/path && python3 scripts/linkedin-monitor.py >> logs/linkedin.log 2>&1
```

**Dev time estimate:** 1–1.5 hours including Google Alerts setup.

---

## DEPLOYMENT CHECKLIST

```
[ ] Create scripts/ folder in project root
[ ] Save reddit-monitor.py to scripts/reddit-monitor.py
[ ] Save linkedin-monitor.py to scripts/linkedin-monitor.py
[ ] Create logs/ folder for cron output
[ ] Set REDDIT_CLIENT_ID environment variable
[ ] Set REDDIT_CLIENT_SECRET environment variable
[ ] Set GPTZERO_API_KEY environment variable (for S8 — get from gptzero.me/api)
[ ] Create 7 Google Alerts with RSS delivery
[ ] Paste 7 RSS URLs into linkedin-monitor.py RSS_FEEDS list
[ ] Install dependencies: pip install praw feedparser
[ ] Test reddit-monitor.py manually: python3 scripts/reddit-monitor.py
[ ] Confirm reddit-signals.json appears in data-feeds/
[ ] Test linkedin-monitor.py manually: python3 scripts/linkedin-monitor.py
[ ] Confirm linkedin-signals.json appears in data-feeds/
[ ] Add cron jobs (reddit: every 4 hours, linkedin: daily 05:00 UTC)
[ ] Verify cron is running: check logs/ after first scheduled run
```

**Total estimated dev time: 3–4 hours including setup, testing, and cron configuration.**

---

## ENVIRONMENT VARIABLES REQUIRED

| Variable | Where to get it | Used by |
|---|---|---|
| `REDDIT_CLIENT_ID` | reddit.com/prefs/apps | reddit-monitor.py |
| `REDDIT_CLIENT_SECRET` | reddit.com/prefs/apps | reddit-monitor.py |
| `GPTZERO_API_KEY` | gptzero.me/api ($10/mo) | S8 via /daily-scout |

Store in `.env` file or server environment — never commit to git.

---

## UPGRADE PATH — Month 2 (Optional)

If Google Alerts RSS produces low signal quality, upgrade LinkedIn monitoring to Phantombuster ($56/month):

1. Sign up at phantombuster.com
2. Use the "LinkedIn Search Scraper" phantom
3. Target hashtags: `#EUDR #leathergoods #indiasourcing #supplychain #sustainablesourcing #ukfashion`
4. Set to run daily — export results as JSON
5. Replace `linkedin-signals.json` output with Phantombuster's export
6. Update `linkedin-monitor.py` to parse Phantombuster's JSON format instead of RSS

Dev time for upgrade: 1 hour.

---

*Data Scraper SOP | KritiKaal Authority Engine | Developer Ready | 2026-04-25*
