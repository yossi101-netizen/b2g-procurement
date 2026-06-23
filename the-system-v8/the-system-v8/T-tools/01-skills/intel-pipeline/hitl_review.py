"""
hitl_review.py — KritiKaal Intel Pipeline: Stage 3 Commander's Terminal

Fetches the highest-scored, LLM-approved items from intel.db and presents
them one at a time for human decision. Single keystroke per item — no Enter
required. Approved items are immediately written to approved-intel.json and
marked in the database.

USAGE:
    cd T-tools/01-skills/intel-pipeline/
    python hitl_review.py --run                  # Review llm_approved items
    python hitl_review.py --run --all-pending    # Include raw pending (skip LLM step)
    python hitl_review.py --run --limit 20       # Cap the queue at N items
    python hitl_review.py --export               # Re-export approved-intel.json without review
    python hitl_review.py --stats               # Show queue counts

KEYSTROKES (during review):
    A  →  Approve item (saved to approved-intel.json, marked approved in DB)
    S  →  Skip item (marked skipped in DB, hidden from future queues)
    N  →  Add a note to the item before approving/skipping
    Q  →  Quit and export current approved set

INSTALL:
    No extra dependencies — uses only stdlib + intel_core.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Shared pipeline core
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE))
from intel_core import (
    db_stats,
    export_approved_json,
    fetch_for_review,
    init_db,
    update_item_status,
    QUEUE_DIR,
)

# ---------------------------------------------------------------------------
# Cross-platform single-keystroke input
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import msvcrt

    def _getch() -> str:
        """Read one character without waiting for Enter (Windows)."""
        ch = msvcrt.getch()
        try:
            return ch.decode("utf-8", errors="ignore").lower()
        except Exception:
            return ""
else:
    import termios
    import tty

    def _getch() -> str:
        """Read one character without waiting for Enter (Unix/macOS)."""
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1).lower()
        except Exception:
            return ""
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _input_line(prompt: str) -> str:
    """Read a full line of text (used for notes — needs Enter)."""
    # Restore normal terminal mode if on Unix before reading a line
    if sys.platform != "win32":
        try:
            import termios
            fd  = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass
    return input(prompt)


# ---------------------------------------------------------------------------
# Terminal display helpers
# ---------------------------------------------------------------------------

# ANSI colours — disabled automatically when stdout is not a real terminal
_USE_COLOUR = sys.stdout.isatty() and os.name != "nt" or (
    os.name == "nt" and os.environ.get("TERM") not in (None, "")
)

def _c(code: str, text: str) -> str:
    if not _USE_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"

def _bold(t: str)    -> str: return _c("1", t)
def _cyan(t: str)    -> str: return _c("96", t)
def _green(t: str)   -> str: return _c("92", t)
def _yellow(t: str)  -> str: return _c("93", t)
def _red(t: str)     -> str: return _c("91", t)
def _dim(t: str)     -> str: return _c("2", t)

_DIVIDER = "─" * 68


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _wrap(text: str, width: int = 66, indent: str = "  ") -> str:
    """Wrap long text to width, preserving paragraph breaks."""
    import textwrap
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.append(
                textwrap.fill(paragraph.strip(), width=width,
                              initial_indent=indent, subsequent_indent=indent)
            )
        else:
            lines.append("")
    return "\n".join(lines)


def _format_date(iso_str: str) -> str:
    if not iso_str:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return iso_str[:10]


def display_item(item: dict, index: int, total: int, note: str = "") -> None:
    """Render one item to the terminal."""
    _clear()

    score        = item.get("raw_score", 0.0)
    source       = item.get("source", "?")
    title        = item.get("title", "(no title)")
    body         = (item.get("body") or "").strip()
    url          = item.get("url", "")
    pub_date     = _format_date(item.get("published_at", ""))
    cluster_tags = item.get("cluster_tags", [])
    meta         = item.get("meta", {})

    # Source label (enrich with subreddit/feed name if available)
    if source == "reddit":
        subreddit  = meta.get("subreddit", "")
        source_lbl = f"reddit — r/{subreddit}" if subreddit else "reddit"
        karma      = meta.get("reddit_score", 0)
        n_comments = meta.get("num_comments", 0)
        engagement = f"  {_dim(f'↑{karma}  💬{n_comments}')}"
    else:
        feed_label = meta.get("feed_label", source)
        source_lbl = f"rss — {feed_label}"
        engagement = ""

    # Header bar
    header_mid = f"  KritiKaal Intel Review  │  {index} / {total}  │  Score: {score:.1f}  "
    print(_bold(_cyan(f"{'━' * 68}")))
    print(_bold(_cyan(header_mid)))
    print(_bold(_cyan(f"{'━' * 68}")))
    print()

    # Metadata block
    print(f"  {_bold('SOURCE  ')} {source_lbl}{engagement}")
    print(f"  {_bold('DATE    ')} {pub_date}")
    if cluster_tags:
        tags_str = ", ".join(_yellow(t) for t in cluster_tags)
        print(f"  {_bold('CLUSTERS')} {tags_str}")
    if url:
        print(f"  {_bold('URL     ')} {_dim(url[:80])}")
    print()

    # Title
    print(_bold("  TITLE"))
    print(_wrap(title, width=64))
    print()

    # Body excerpt
    if body:
        excerpt = body[:600]
        if len(body) > 600:
            excerpt += " …"
        print(_bold("  CONTENT"))
        print(_wrap(excerpt, width=64))
        print()

    # Top comments (Reddit only)
    top_comments = meta.get("top_comments", [])
    if top_comments:
        print(_bold("  TOP COMMENTS"))
        for c in top_comments[:3]:
            karma_str = _dim(f"[{c.get('score', 0)}]")
            snippet   = c.get("body", "")[:140].replace("\n", " ")
            print(f"  ▸ {karma_str} {snippet}")
        print()

    # Existing note (if operator added one)
    existing_note = item.get("user_notes", "")
    if existing_note:
        print(f"  {_bold('NOTE    ')} {_yellow(existing_note)}")
        print()

    # Pending note (typed this session before final decision)
    if note:
        print(f"  {_bold('PENDING NOTE')} {_yellow(note)}")
        print()

    # Action bar
    print(_dim(_DIVIDER))
    print(
        f"  {_green('[A]')} Approve   "
        f"{_yellow('[S]')} Skip   "
        f"{_cyan('[N]')} Add Note   "
        f"{_red('[Q]')} Quit"
    )


# ---------------------------------------------------------------------------
# Review session
# ---------------------------------------------------------------------------

def run_review(
    limit: int = 50,
    include_pending: bool = False,
) -> dict:
    """
    Interactive review loop. Returns a summary dict.
    """
    statuses = ("llm_approved", "pending") if include_pending else ("llm_approved",)
    items    = fetch_for_review(statuses=statuses, limit=limit)

    if not items:
        status_desc = "/".join(statuses)
        print(f"\nNo items with status [{status_desc}] in the queue.")
        if not include_pending:
            print("Tip: run  python llm_filter.py --run  first, or use --all-pending flag.")
        return {"reviewed": 0, "approved": 0, "skipped": 0}

    total    = len(items)
    approved = skipped = 0
    pending_note = ""

    for idx, item in enumerate(items, 1):
        while True:  # inner loop lets N re-display the item before final decision
            display_item(item, idx, total, note=pending_note)
            key = _getch()

            if key == "a":
                update_item_status(
                    item["item_id"], "approved",
                    notes=pending_note or None,
                )
                approved += 1
                pending_note = ""
                # Immediately re-export so the file stays current
                export_approved_json()
                print(f"\n  {_green('✓ Approved')} — approved-intel.json updated.")
                _getch()  # brief pause so user sees the confirmation
                break

            elif key == "s":
                update_item_status(
                    item["item_id"], "skipped",
                    notes=pending_note or None,
                )
                skipped += 1
                pending_note = ""
                print(f"\n  {_yellow('→ Skipped')}")
                break

            elif key == "n":
                _clear()
                display_item(item, idx, total, note=pending_note)
                print()
                try:
                    pending_note = _input_line("  Note: ").strip()
                except (EOFError, KeyboardInterrupt):
                    pending_note = ""
                # Loop back to display with note visible

            elif key == "q":
                print(f"\n  {_red('Quit')} — session ended.")
                export_approved_json()
                return {
                    "reviewed": idx - 1,
                    "approved": approved,
                    "skipped":  skipped,
                }

            # Any other key → re-display (no-op)

    _clear()
    return {"reviewed": total, "approved": approved, "skipped": skipped}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal Intel Pipeline — Stage 3: HITL Commander's Terminal"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Start the interactive review session"
    )
    parser.add_argument(
        "--all-pending", action="store_true",
        help="Include raw 'pending' items (use when skipping the LLM filter step)"
    )
    parser.add_argument(
        "--limit", type=int, default=50, metavar="N",
        help="Max items to load per session (default: 50)"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Re-export approved-intel.json without starting a review session"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show database status counts"
    )
    args = parser.parse_args()

    init_db()

    if args.stats:
        stats = db_stats()
        if not stats:
            print("Database is empty. Run rss_poller.py or reddit_intel.py first.")
        else:
            print("\nIntel Queue — Status Breakdown")
            print("=" * 45)
            grand_total = 0
            order = ("pending", "llm_approved", "approved", "skipped", "rejected")
            for status in order:
                sources = stats.get(status, {})
                if sources:
                    n = sum(sources.values())
                    grand_total += n
                    src_str = ", ".join(f"{s}:{c}" for s, c in sorted(sources.items()))
                    print(f"  {status:<14} {n:>5}  ({src_str})")
            print(f"  {'TOTAL':<14} {grand_total:>5}")
        return

    if args.export:
        path = export_approved_json()
        import json as _json
        data = _json.loads(path.read_text(encoding="utf-8"))
        print(f"Exported {data['total_approved']} approved items → {path}")
        return

    if args.run:
        print(f"\nLoading review queue (limit: {args.limit}) ...")
        result = run_review(
            limit=args.limit,
            include_pending=args.all_pending,
        )
        print(
            f"\nSession complete — "
            f"Reviewed: {result['reviewed']}  │  "
            f"Approved: {result['approved']}  │  "
            f"Skipped: {result['skipped']}"
        )
        path = QUEUE_DIR / "approved-intel.json"
        if path.exists():
            import json as _json
            data = _json.loads(path.read_text(encoding="utf-8"))
            print(f"approved-intel.json → {data['total_approved']} total approved items")
            print(f"Path: {path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
