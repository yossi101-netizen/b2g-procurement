"""
rss_poller.py — KritiKaal RSS Intelligence Poller

Monitors trade journal and regulatory RSS/Atom feeds for B2B supply chain
signals matching KritiKaal's 8 pain clusters. Saves structured records to
the shared intel-queue SQLite database for HITL review.

INSTALL:
    pip install feedparser python-dotenv

USAGE:
    cd T-tools/01-skills/intel-pipeline/
    python rss_poller.py --run              # Poll all feeds
    python rss_poller.py --test             # Check which feeds are live (no DB write)
    python rss_poller.py --stats            # Show database stats
    python rss_poller.py --export           # Export pending items to JSON
    python rss_poller.py --export --min-score 3.0
"""
from __future__ import annotations

import argparse
import html
import logging
import random
import re
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Shared pipeline core
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent.resolve()
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
# Feed registry
#
# Each entry: (label, url, confidence)
#   confidence: "high" = known-working  |  "medium" = likely live, may 404
#
# All feeds have been selected for B2B supply chain / leather / trade relevance.
# Run --test to verify which are currently live before the first --run.
# ---------------------------------------------------------------------------
FEEDS: list[dict] = [
    # --- Trade journals ---
    {
        "label":      "Sourcing Journal",
        "url":        "https://sourcingjournal.com/feed/",
        "confidence": "high",
        "tags":       ["fashion", "sourcing", "manufacturing"],
    },
    {
        "label":      "Just Style",
        "url":        "https://www.just-style.com/feed/",
        "confidence": "high",
        "tags":       ["apparel", "sourcing", "trade"],
    },
    {
        "label":      "Fashion United (Global)",
        "url":        "https://fashionunited.com/news/rss.xml",
        "confidence": "high",
        "tags":       ["fashion", "manufacturing", "supply chain"],
    },
    {
        "label":      "The Manufacturer (UK)",
        "url":        "https://www.themanufacturer.com/feed/",
        "confidence": "high",
        "tags":       ["manufacturing", "UK industry", "supply chain"],
    },
    {
        "label":      "Fibre2Fashion",
        "url":        "https://www.fibre2fashion.com/rss/news.xml",
        "confidence": "high",
        "tags":       ["textile", "leather", "export", "India"],
    },
    {
        "label":      "World Footwear",
        "url":        "https://www.worldfootwear.com/rss/news.xml",
        "confidence": "medium",
        "tags":       ["footwear", "leather", "manufacturing"],
    },
    {
        "label":      "Leather International",
        "url":        "https://leatherinternational.com/feed/",
        "confidence": "medium",
        "tags":       ["leather", "tannery", "trade"],
    },
    {
        "label":      "CBI Netherlands — Leather Goods",
        "url":        "https://www.cbi.eu/market-information/rss",
        "confidence": "medium",
        "tags":       ["EU market", "leather", "developing countries"],
    },
    # --- Regulatory / government ---
    {
        "label":      "UK GOV — Leather & Customs",
        "url":        "https://www.gov.uk/search/all.atom?keywords=leather+import+duty",
        "confidence": "high",
        "tags":       ["UK regulation", "customs", "duty"],
    },
    {
        "label":      "UK GOV — DCTS",
        "url":        "https://www.gov.uk/search/all.atom?keywords=DCTS+developing+countries",
        "confidence": "high",
        "tags":       ["UK regulation", "DCTS", "GSP"],
    },
    {
        "label":      "UK GOV — EUDR",
        "url":        "https://www.gov.uk/search/all.atom?keywords=EU+deforestation+regulation",
        "confidence": "high",
        "tags":       ["EUDR", "regulation", "supply chain"],
    },
    {
        "label":      "UK GOV — Supply Chain",
        "url":        "https://www.gov.uk/search/all.atom?keywords=supply+chain+resilience",
        "confidence": "high",
        "tags":       ["UK policy", "supply chain"],
    },
    # --- Broader supply chain intelligence ---
    {
        "label":      "Supply Chain Dive",
        "url":        "https://www.supplychaindive.com/feeds/news/",
        "confidence": "high",
        "tags":       ["supply chain", "logistics", "procurement"],
    },
    {
        "label":      "Logistics Management",
        "url":        "https://www.logisticsmgmt.com/rss/rss_news.xml",
        "confidence": "medium",
        "tags":       ["logistics", "import", "supply chain"],
    },
]

# Random delay range between feed fetches (seconds).
# Randomisation breaks the fixed-interval pattern that anti-bot systems detect.
INTER_FEED_SLEEP_MIN = 1.0
INTER_FEED_SLEEP_MAX = 4.0

# 2026 Chrome 131 / Windows 11 UA — current enough to pass most WAF fingerprint checks.
# feedparser's default "python-feedparser/6.x" UA triggers 403 on most trade journal CDNs.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "application/rss+xml, application/atom+xml, "
        "application/xml, text/xml, */*"
    ),
    "Accept-Language":  "en-US,en;q=0.9",
    "Accept-Encoding":  "gzip, deflate, br",
    "Cache-Control":    "no-cache",
    "Pragma":           "no-cache",
    "Sec-Fetch-Dest":   "document",
    "Sec-Fetch-Mode":   "navigate",
    "Sec-Fetch-Site":   "none",
}

# Max characters of article body to store
MAX_BODY_CHARS = 2000


# ---------------------------------------------------------------------------
# HTML / text utilities
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    # Collapse runs of whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def _parse_published(entry) -> Optional[datetime]:
    """
    Extract a timezone-aware datetime from a feedparser entry.
    Tries: published_parsed → updated_parsed → published (raw string).
    Returns None if no date can be parsed.
    """
    # feedparser gives us time.struct_time tuples
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass

    # Try raw string (RFC 2822 / RFC 3339)
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass

    return None


# ---------------------------------------------------------------------------
# Feed processing
# ---------------------------------------------------------------------------

def _fetch_feed(feed_def: dict) -> Optional[object]:
    """Fetch and parse a single feed. Returns feedparser result or None on error."""
    try:
        import feedparser
    except ImportError:
        log.error("feedparser is not installed. Run: pip install feedparser")
        sys.exit(1)

    url   = feed_def["url"]
    label = feed_def["label"]
    try:
        result = feedparser.parse(url, request_headers=_BROWSER_HEADERS)
        if result.bozo and not result.entries:
            log.warning("  [WARN] %s — parse error: %s", label, result.bozo_exception)
            return None
        return result
    except Exception as exc:
        log.warning("  [FAIL] %s — %s", label, exc)
        return None


def _entry_to_item(entry, feed_def: dict) -> Optional[dict]:
    """
    Convert a feedparser entry to a normalised intel item.
    Returns None if the entry doesn't pass keyword pre-filter.
    """
    title = _strip_html(getattr(entry, "title", "") or "")
    if not title:
        return None

    # Prefer full content, fall back to summary
    body = ""
    content_list = getattr(entry, "content", None)
    if content_list:
        body = _strip_html(content_list[0].get("value", ""))
    if not body:
        body = _strip_html(getattr(entry, "summary", "") or "")

    url = getattr(entry, "link", "") or ""
    if not url:
        return None

    full_text = f"{title} {body}"
    if not has_any_keyword(full_text):
        return None

    cluster_tags = assign_clusters(full_text)
    if not cluster_tags:
        return None

    published_at = _parse_published(entry)
    score        = pre_score(
        cluster_tags=cluster_tags,
        published_at=published_at,
    )

    item_id = make_item_id("rss", url)

    return {
        "item_id":      item_id,
        "source":       "rss",
        "title":        title[:300],
        "body":         body[:MAX_BODY_CHARS],
        "url":          url,
        "published_at": published_at.isoformat() if published_at else "",
        "author":       getattr(entry, "author", "") or "",
        "cluster_tags": cluster_tags,
        "raw_score":    score,
        "meta": {
            "feed_label": feed_def["label"],
            "feed_url":   feed_def["url"],
            "feed_tags":  feed_def.get("tags", []),
        },
    }


# ---------------------------------------------------------------------------
# Main poll logic
# ---------------------------------------------------------------------------

def poll(max_per_feed: int = 200) -> dict:
    """
    Fetch all configured feeds, filter for pain signals, insert new items.
    Returns a summary dict with counts.
    """
    total_inserted  = 0
    total_skipped   = 0
    total_duplicate = 0
    feeds_ok        = 0
    feeds_failed    = 0

    for feed_def in FEEDS:
        label = feed_def["label"]
        log.info("Fetching: %s", label)

        result = _fetch_feed(feed_def)
        if result is None:
            feeds_failed += 1
            time.sleep(random.uniform(INTER_FEED_SLEEP_MIN, INTER_FEED_SLEEP_MAX))
            continue

        feeds_ok += 1
        entries   = result.entries[:max_per_feed]
        log.info("  → %d entries", len(entries))

        for entry in entries:
            item = _entry_to_item(entry, feed_def)
            if item is None:
                total_skipped += 1
                continue

            item_id = item["item_id"]
            if is_seen(item_id):
                total_duplicate += 1
                continue

            if insert_item(item):
                total_inserted += 1
                log.debug(
                    "    + [%.1f] %s — %s",
                    item["raw_score"], label, item["title"][:65]
                )
            else:
                total_duplicate += 1

        time.sleep(random.uniform(INTER_FEED_SLEEP_MIN, INTER_FEED_SLEEP_MAX))

    return {
        "feeds_ok":      feeds_ok,
        "feeds_failed":  feeds_failed,
        "inserted":      total_inserted,
        "skipped":       total_skipped,
        "duplicate":     total_duplicate,
    }


def test_feeds() -> None:
    """
    Test each configured feed without writing to the database.
    Prints a live/dead status table.
    """
    try:
        import feedparser
    except ImportError:
        log.error("feedparser is not installed. Run: pip install feedparser")
        sys.exit(1)

    print(f"\n{'Feed':<40} {'Status':<8} {'Entries':>7}  URL")
    print("-" * 100)

    for feed_def in FEEDS:
        label = feed_def["label"]
        url   = feed_def["url"]
        try:
            result  = feedparser.parse(url)
            n       = len(result.entries)
            status  = "OK" if n > 0 else ("EMPTY" if not result.bozo else "ERROR")
        except Exception:
            n, status = 0, "ERROR"

        print(f"{label:<40} {status:<8} {n:>7}  {url}")
        time.sleep(0.3)

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal RSS Intelligence Poller"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Poll all configured RSS/Atom feeds"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test all feed URLs and print a live/dead table (no DB writes)"
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
    parser.add_argument(
        "--max-per-feed", type=int, default=200, metavar="N",
        help="Max entries to process per feed (default: 200)"
    )
    args = parser.parse_args()

    if args.test:
        test_feeds()
        return

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
        log.info("Starting RSS poll — %d feeds configured ...", len(FEEDS))
        result = poll(max_per_feed=args.max_per_feed)
        log.info(
            "Done. Feeds OK: %d | Failed: %d | Inserted: %d | "
            "Skipped (no signal): %d | Duplicates: %d",
            result["feeds_ok"], result["feeds_failed"],
            result["inserted"], result["skipped"], result["duplicate"]
        )
        stats   = db_stats()
        pending = sum(stats.get("pending", {}).values())
        log.info("Total pending review: %d items", pending)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
