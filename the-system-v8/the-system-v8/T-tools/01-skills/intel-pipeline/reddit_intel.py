"""
reddit_intel.py — KritiKaal Reddit Intelligence Adapter

Searches target subreddits for B2B supply chain pain signals matching
KritiKaal's 8 pain clusters. Saves structured records to the shared
intel-queue SQLite database for HITL review.

SETUP (one-time):
    1. Go to https://www.reddit.com/prefs/apps → "create another app"
    2. Choose type: "script"
    3. Name: KritiKaal-Intel  |  Redirect: http://localhost:8080
    4. Copy client_id (under app name) and client_secret
    5. Create T-tools/01-skills/intel-pipeline/.env with:
           REDDIT_CLIENT_ID=your_client_id
           REDDIT_CLIENT_SECRET=your_client_secret

INSTALL:
    pip install praw python-dotenv

USAGE:
    cd T-tools/01-skills/intel-pipeline/
    python reddit_intel.py --run               # Full scrape (default: last 365 days)
    python reddit_intel.py --run --since 30    # Only posts from last 30 days
    python reddit_intel.py --stats             # Show database stats
    python reddit_intel.py --export            # Export pending items to JSON
    python reddit_intel.py --export --min-score 3.0
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Load .env from this directory
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent.resolve()
_ENV  = _HERE / ".env"
if _ENV.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV)
    except ImportError:
        # Manual fallback if python-dotenv isn't installed
        for line in _ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# ---------------------------------------------------------------------------
# Shared pipeline core
# ---------------------------------------------------------------------------
sys.path.insert(0, str(_HERE))
from intel_core import (
    assign_clusters,
    db_stats,
    export_pending_json,
    has_any_keyword,
    init_db,
    insert_item,
    is_seen,
    make_item_id,
    pre_score,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Target subreddits
# ---------------------------------------------------------------------------
TARGET_SUBREDDITS = [
    # Core B2B operations — procurement leads, supply chain managers, brand founders
    "supplychain",
    "manufacturing",
    "procurement",
    # Brand owner communities — the primary ICP for KritiKaal
    "smallbusiness",
    "entrepreneur",
    "ecommerce",
    # Geography-specific B2B — UK brands are the primary target market
    "UKBusiness",
]
# REMOVED (consumer / hobby — misaligned with B2B ICP):
#   "leathercraft"        — DIY hobbyists, not brand founders or procurement leads
#   "frugalmalefashion"   — consumer retail community, not sourcing decision-makers
#   "femalefashionadvice" — consumer retail community, not sourcing decision-makers

# ---------------------------------------------------------------------------
# Search queries mapped to pain clusters
# Run each query across all subreddits combined.
# ---------------------------------------------------------------------------
SEARCH_QUERIES = [
    # EUDR / regulatory
    "EUDR leather compliance 2026",
    "EU deforestation regulation leather",
    "leather supply chain traceability EU",
    # China Plus One / tariffs
    "China plus one leather sourcing",
    "25% tariff leather goods",
    "India leather sourcing alternative China",
    "DCTS duty UK leather",
    # QC disasters
    "leather goods quality control India",
    "defective shipment leather factory",
    "AQL inspection manufacturing",
    "factory quality control failure",
    # Sourcing agent betrayal
    "sourcing agent scam leather",
    "sourcing agent disappeared purchase order",
    "leather sourcing agent problems India",
    # Golden sample trap
    "sample approval production doesn't match",
    "factory sample different production",
    "golden sample leather manufacturing",
    # MOQ / missing middle
    "minimum order quantity leather India",
    "small batch leather manufacturing",
    "low MOQ leather goods manufacturer",
    # General sourcing pain
    "leather goods manufacturer India experience",
    "Alibaba leather goods quality problems",
    "managed manufacturing leather India",
]

# Minimum Reddit karma for a post to enter the scoring pipeline.
# Posts below this threshold are almost always noise.
MIN_POST_KARMA = 5

# Number of top comments to extract per post (by comment score).
MAX_COMMENTS = 12

# Rate-limit pause between API bursts (PRAW handles per-request limits,
# but this prevents aggressive hammering across subreddits).
INTER_QUERY_SLEEP = 1.0  # seconds


# ---------------------------------------------------------------------------
# PRAW helpers
# ---------------------------------------------------------------------------

def _get_reddit():
    """Authenticate and return a read-only PRAW Reddit instance."""
    try:
        import praw
    except ImportError:
        log.error("praw is not installed. Run: pip install praw")
        sys.exit(1)

    client_id     = os.getenv("REDDIT_CLIENT_ID", "").strip()
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        log.error(
            "Missing Reddit credentials.\n"
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in:\n"
            "  %s", _ENV
        )
        sys.exit(1)

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="KritiKaal-Intel/1.0 (B2B supply chain research)",
    )
    reddit.read_only = True
    log.info("Reddit authenticated (read-only)")
    return reddit


def _parse_dt(utc_timestamp: float) -> datetime:
    """Convert a PRAW UTC timestamp float to an aware datetime."""
    return datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)


def _extract_comments(submission, limit: int = MAX_COMMENTS) -> list[dict]:
    """
    Return the top `limit` comments sorted by score.
    Replaces MoreComments stubs without fetching additional pages.
    """
    try:
        submission.comments.replace_more(limit=0)
    except Exception:
        return []

    comments = []
    for comment in submission.comments.list():
        if not hasattr(comment, "body") or comment.body in ("[deleted]", "[removed]"):
            continue
        comments.append({
            "author": str(getattr(comment, "author", "unknown") or "unknown"),
            "body":   comment.body[:1000],
            "score":  comment.score,
        })

    comments.sort(key=lambda c: c["score"], reverse=True)
    return comments[:limit]


def _submission_to_item(submission) -> Optional[dict]:
    """
    Convert a PRAW Submission to a normalised intel item dict.
    Returns None if the post doesn't pass keyword pre-filter or karma gate.
    """
    if submission.score < MIN_POST_KARMA:
        return None

    title = submission.title or ""
    body  = getattr(submission, "selftext", "") or ""
    full_text = f"{title} {body}"

    if not has_any_keyword(full_text):
        return None

    # Pull comments and append their text to the searchable corpus
    comments     = _extract_comments(submission)
    comments_txt = " ".join(c["body"] for c in comments)
    full_text    = f"{full_text} {comments_txt}"

    cluster_tags = assign_clusters(full_text)
    if not cluster_tags:
        return None

    published_at = _parse_dt(submission.created_utc)
    score        = pre_score(
        cluster_tags=cluster_tags,
        published_at=published_at,
        engagement_score=submission.score,
        comment_count=submission.num_comments,
    )

    item_id = make_item_id("reddit", submission.id)

    return {
        "item_id":      item_id,
        "source":       "reddit",
        "title":        title[:300],
        "body":         body[:3000],
        "url":          f"https://reddit.com{submission.permalink}",
        "published_at": published_at.isoformat(),
        "author":       str(getattr(submission, "author", "unknown") or "unknown"),
        "cluster_tags": cluster_tags,
        "raw_score":    score,
        "meta": {
            "subreddit":    submission.subreddit.display_name,
            "reddit_score": submission.score,
            "num_comments": submission.num_comments,
            "top_comments": comments,
            "post_id":      submission.id,
            "flair":        submission.link_flair_text or "",
        },
    }


# ---------------------------------------------------------------------------
# Main scrape logic
# ---------------------------------------------------------------------------

def scrape(since_days: int = 365) -> dict:
    """
    Run the full Reddit scrape.

    Strategy:
      1. Keyword search across all target subreddits combined
         (Reddit's search index, time-filtered)
      2. Browse hot + top posts in each subreddit individually
         (catches practitioner posts that use no tracked keywords in title)

    Returns a summary dict with counts.
    """
    reddit    = _get_reddit()
    subreddit = reddit.subreddit("+".join(TARGET_SUBREDDITS))
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=since_days)

    inserted  = 0
    skipped   = 0
    duplicate = 0

    # --- Phase 1: Keyword searches ---
    log.info("Phase 1: keyword searches across %d subreddits ...", len(TARGET_SUBREDDITS))
    for query in SEARCH_QUERIES:
        log.info("  Searching: %r", query)
        try:
            results = subreddit.search(
                query,
                sort="top",
                time_filter="year",
                limit=50,
            )
            for submission in results:
                if _parse_dt(submission.created_utc) < cutoff_dt:
                    continue
                item_id = make_item_id("reddit", submission.id)
                if is_seen(item_id):
                    duplicate += 1
                    continue
                item = _submission_to_item(submission)
                if item is None:
                    skipped += 1
                    continue
                if insert_item(item):
                    inserted += 1
                    log.debug("    + [%.1f] %s", item["raw_score"], item["title"][:70])
                else:
                    duplicate += 1
        except Exception as exc:
            log.warning("  Search failed for %r: %s", query, exc)

        time.sleep(INTER_QUERY_SLEEP)

    # --- Phase 2: Browse hot + top posts per subreddit ---
    log.info("Phase 2: browsing hot/top posts per subreddit ...")
    for sub_name in TARGET_SUBREDDITS:
        log.info("  r/%s", sub_name)
        sub = reddit.subreddit(sub_name)
        feeds = [
            ("hot",  sub.hot(limit=100)),
            ("top",  sub.top(time_filter="year", limit=100)),
        ]
        for feed_name, feed in feeds:
            try:
                for submission in feed:
                    if _parse_dt(submission.created_utc) < cutoff_dt:
                        continue
                    item_id = make_item_id("reddit", submission.id)
                    if is_seen(item_id):
                        duplicate += 1
                        continue
                    item = _submission_to_item(submission)
                    if item is None:
                        skipped += 1
                        continue
                    if insert_item(item):
                        inserted += 1
                        log.debug(
                            "    + [%.1f] r/%s/%s — %s",
                            item["raw_score"], sub_name, feed_name, item["title"][:60]
                        )
                    else:
                        duplicate += 1
            except Exception as exc:
                log.warning("  r/%s %s feed error: %s", sub_name, feed_name, exc)

        time.sleep(INTER_QUERY_SLEEP)

    return {
        "inserted":  inserted,
        "skipped":   skipped,
        "duplicate": duplicate,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal Reddit Intelligence Adapter"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Run the full Reddit scrape"
    )
    parser.add_argument(
        "--since", type=int, default=365, metavar="DAYS",
        help="Only include posts from the last N days (default: 365)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show database statistics"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export pending items to a JSON file"
    )
    parser.add_argument(
        "--min-score", type=float, default=2.0, metavar="N",
        help="Minimum raw_score for export (default: 2.0)"
    )
    args = parser.parse_args()

    init_db()

    if args.stats:
        stats = db_stats()
        if not stats:
            print("Database is empty. Run --run first.")
        else:
            print("\nIntel Queue — Database Stats")
            print("=" * 40)
            for status, sources in stats.items():
                for source, count in sources.items():
                    print(f"  [{status:10s}] {source:10s}: {count}")
        return

    if args.export:
        path = export_pending_json(min_score=args.min_score)
        print(f"Exported to: {path}")
        return

    if args.run:
        log.info("Starting Reddit scrape (last %d days) ...", args.since)
        result = scrape(since_days=args.since)
        log.info(
            "Done. Inserted: %d | Skipped (no signal): %d | Duplicates: %d",
            result["inserted"], result["skipped"], result["duplicate"]
        )
        stats = db_stats()
        pending = sum(
            v for s in stats.get("pending", {}).values() for v in [s]
        )
        log.info("Total pending review: %d items", pending)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
