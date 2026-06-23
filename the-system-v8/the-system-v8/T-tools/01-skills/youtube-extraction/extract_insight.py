"""
extract_insight.py — KritiKaal YouTube Extraction Interface
Phase 1 entry point. Thin API wrapper around the ytinsights package.

The ytinsights package handles discovery, scoring, and the human-in-the-loop
review loop. This module exposes a clean programmatic interface for Phase 2
(generate_script.py) to consume approved insights without touching the CLI.

USAGE (CLI):
    python extract_insight.py --list
    python extract_insight.py --tag operations
    python extract_insight.py --export path/to/output.json
    python extract_insight.py --n 10

USAGE (import):
    from extract_insight import extract_approved_insights, get_insights_by_tag
    insights = extract_approved_insights()
    eudr_insights = get_insights_by_tag("operations")

RUNNING THE FULL PIPELINE (ytinsights):
    cd T-tools/01-skills/youtube-extraction/
    python -m ytinsights run --channel https://www.youtube.com/@channel_name
    python -m ytinsights export --channel https://www.youtube.com/@channel_name

APPROVED INSIGHTS DATABASE:
    B-brain/04-INBOX/youtube-research/ytinsights.db
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Resolve paths relative to the workspace root (4 levels up from this file)
_THIS_DIR = Path(__file__).parent.resolve()
_WORKSPACE = _THIS_DIR.parent.parent.parent  # T-tools/01-skills/youtube-extraction -> workspace root

DB_PATH = _WORKSPACE / "B-brain" / "04-INBOX" / "youtube-research" / "ytinsights.db"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """Return a read-only connection to the research database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at:\n  {DB_PATH}\n\n"
            "Run the ytinsights pipeline first:\n"
            "  python -m ytinsights run --channel <channel_url>\n"
            "Then approve videos in the HITL loop before extracting."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_insight(row: sqlite3.Row) -> dict:
    """Normalise a database row into a clean insight dict for Phase 2."""
    summary_raw = row["summary"] or ""
    user_notes  = row["user_notes"] or ""

    # The ytinsights summary is stored as markdown. Extract the TL;DR line if present.
    tldr = ""
    for line in summary_raw.splitlines():
        if line.startswith("**TL;DR**"):
            tldr = line.replace("**TL;DR**", "").replace("—", "").strip(" —-")
            break

    return {
        "video_id":        row["id"],
        "title":           row["title"] or "",
        "url":             row["url"] or f"https://www.youtube.com/watch?v={row['id']}",
        "channel_url":     row["channel_url"],
        "duration_min":    round((row["duration_sec"] or 0) / 60, 1),
        "upload_date":     row["upload_date"] or "",
        "final_score":     row["final_score"],
        "category_tag":    row["category_tag"] or "",
        "tldr":            tldr,
        "summary_markdown": summary_raw,
        "user_notes":      user_notes,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_approved_insights(limit: Optional[int] = None) -> list[dict]:
    """
    Return all CEO-approved video insights from the research database.

    Each dict contains:
        video_id, title, url, channel_url, duration_min, upload_date,
        final_score, category_tag, tldr, summary_markdown, user_notes

    Returns an empty list if no approved summaries exist yet.
    """
    conn = _get_connection()
    try:
        cur = conn.execute(
            "SELECT v.id, v.channel_url, v.title, v.url, v.duration_sec, "
            "       v.upload_date, v.final_score, v.category_tag, "
            "       v.summary, v.user_notes "
            "FROM videos v "
            "WHERE v.status = 'approved' "
            "ORDER BY v.queue_pos ASC, v.final_score DESC"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    results = [_row_to_insight(r) for r in rows]
    return results[:limit] if limit else results


def get_insights_by_tag(tag: str) -> list[dict]:
    """
    Filter approved insights by the LLM-assigned category tag.

    Tags are assigned by ytinsights/scoring.py during Stage A/B scoring.
    Common tags: operations, pricing, gtm, hiring, retention, fundraising,
                 product, content, engineering, leadership.
    """
    all_insights = extract_approved_insights()
    tag_lower = tag.lower()
    return [
        i for i in all_insights
        if tag_lower in (i.get("category_tag") or "").lower()
    ]


def get_insights_for_cluster(cluster_keywords: list[str]) -> list[dict]:
    """
    Return approved insights whose title or TL;DR contains any cluster keyword.

    Use this to pre-filter insights relevant to a specific Pain Matrix cluster
    before passing them to generate_script.py as context.

    Example:
        get_insights_for_cluster(["EUDR", "deforestation", "leather compliance"])
    """
    all_insights = extract_approved_insights()
    kw_lower = [k.lower() for k in cluster_keywords]
    matched = []
    for i in all_insights:
        searchable = (i["title"] + " " + i["tldr"] + " " + i["summary_markdown"]).lower()
        if any(kw in searchable for kw in kw_lower):
            matched.append(i)
    return matched


def export_to_json(output_path: Optional[str] = None) -> str:
    """
    Export all approved insights to a JSON file.

    Default output: B-brain/04-INBOX/youtube-research/approved-insights.json
    This file is the primary data source for youtube-analyst-agent.md.
    """
    insights = extract_approved_insights()
    if output_path is None:
        output_path = str(DB_PATH.parent / "approved-insights.json")
    Path(output_path).write_text(
        json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return output_path


def database_summary() -> dict:
    """Return a quick stats summary of the research database."""
    conn = _get_connection()
    try:
        cur = conn.execute(
            "SELECT status, COUNT(*) AS n FROM videos GROUP BY status"
        )
        stats = {row["status"]: row["n"] for row in cur}
    finally:
        conn.close()

    total = sum(stats.values())
    return {
        "total_videos": total,
        "approved": stats.get("approved", 0),
        "pending_review": stats.get("pending", 0) + stats.get("summarized", 0),
        "skipped": stats.get("skipped", 0),
        "no_transcript": stats.get("no_transcript", 0),
        "unscored": stats.get("unscored", 0),
        "database_path": str(DB_PATH),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="KritiKaal YouTube Insight Extractor — Phase 1 interface"
    )
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all approved insights (title + score)")
    parser.add_argument("--tag", "-t",
                        help="Filter by LLM category tag (e.g. operations, gtm)")
    parser.add_argument("--keywords", "-k", nargs="+",
                        help="Filter by cluster keywords (space-separated)")
    parser.add_argument("--export", "-e", metavar="PATH",
                        help="Export all approved insights to JSON file")
    parser.add_argument("--n", type=int, metavar="N",
                        help="Limit number of results")
    parser.add_argument("--stats", "-s", action="store_true",
                        help="Show database statistics")
    args = parser.parse_args()

    try:
        if args.stats:
            summary = database_summary()
            print(json.dumps(summary, indent=2))

        elif args.export:
            path = export_to_json(args.export)
            print(f"Exported {len(extract_approved_insights())} approved insights to: {path}")

        elif args.tag:
            insights = get_insights_by_tag(args.tag)
            insights = insights[: args.n] if args.n else insights
            print(json.dumps(insights, indent=2, ensure_ascii=False))

        elif args.keywords:
            insights = get_insights_for_cluster(args.keywords)
            insights = insights[: args.n] if args.n else insights
            print(json.dumps(insights, indent=2, ensure_ascii=False))

        elif args.list:
            insights = extract_approved_insights(args.n)
            if not insights:
                print("No approved insights in database. Run ytinsights first.")
            else:
                print(f"Approved insights ({len(insights)} total):\n")
                for idx, ins in enumerate(insights, 1):
                    score = f"{ins['final_score']:.1f}" if ins["final_score"] else "?"
                    print(f"  {idx:>2}. [{score}] {ins['title']}")
                    if ins["tldr"]:
                        print(f"       {ins['tldr'][:90]}...")
        else:
            parser.print_help()

    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
