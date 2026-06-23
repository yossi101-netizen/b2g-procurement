"""
llm_filter.py — KritiKaal Intel Pipeline: Stage 2 Haiku Sieve

Fetches all `pending` items from intel.db and sends each to Claude 3 Haiku
with a binary relevance question. Items that pass (YES) are promoted to
`llm_approved` and their score is boosted (+2.0) to surface them first in
HITL review. Items that fail (NO) are marked `rejected` and hidden from the
human operator permanently.

This stage is optional but strongly recommended before running hitl_review.py.
It eliminates noise before the human ever sees it, keeping the HITL queue
signal-dense.

INSTALL:
    pip install anthropic python-dotenv

USAGE:
    cd T-tools/01-skills/intel-pipeline/
    python llm_filter.py --run                  # Process all pending items
    python llm_filter.py --run --limit 50       # Process first N items by score
    python llm_filter.py --dry-run              # Show what would be sent, no API calls
    python llm_filter.py --stats               # Show queue counts by status

COST ESTIMATE (Claude 3 Haiku):
    ~$0.00025 per 1K input tokens.
    Each item ≈ 400–600 tokens (system prompt cached after first call).
    100 items ≈ $0.01–0.02. Negligible.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Load .env — check intel-pipeline first, then youtube-extraction fallback
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent.resolve()

def _load_env() -> None:
    candidates = [
        _HERE / ".env",
        _HERE.parent / "youtube-extraction" / ".env",
        _HERE.parent / "script-generation" / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path, override=False)
                return
            except ImportError:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip())
                return

_load_env()

# ---------------------------------------------------------------------------
# Shared pipeline core
# ---------------------------------------------------------------------------
sys.path.insert(0, str(_HERE))
from intel_core import (
    db_stats,
    fetch_for_review,
    init_db,
    update_item_status,
    get_db,
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
# Model configuration — dynamic resolution, hardcoded fallback
# ---------------------------------------------------------------------------
# The filter task is binary YES/NO — haiku tier is optimal (cheapest, fastest).
# _resolve_model() queries the live API at startup to pick the best available
# Claude 4 model. MODEL_FALLBACK is used only if that API call fails.
MODEL_FALLBACK = "claude-haiku-4-5"

# Tier preference for model selection: cheapest first.
_MODEL_TIER_PREFERENCE = ("haiku", "sonnet", "opus")

MAX_TOKENS = 5       # We only need "YES" or "NO"
SCORE_BOOST = 2.0    # Added to raw_score when the model says YES

# System prompt is sent with cache_control so it is cached after the first
# call — all subsequent calls within the 5-minute TTL reuse the cache,
# cutting per-item cost roughly in half.
_SYSTEM_PROMPT = (
    "You are a strict B2B content relevance filter for KritiKaal, "
    "a managed leather goods manufacturing service for UK, EU, and US brands "
    "sourcing from India. You evaluate whether content is operationally useful "
    "for understanding supply chain pain points that affect our target buyers.\n\n"
    "Respond ONLY with the single word YES or NO. No punctuation. No explanation."
)

# Per-item user prompt template
_USER_TEMPLATE = (
    "Does this text contain a specific, operational B2B pain point, failure mode, "
    "or verifiable data point regarding supply chains, leather manufacturing quality "
    "control, customs tariffs, regulatory compliance (EUDR, DCTS), or sourcing "
    "intermediary problems?\n\n"
    "Title: {title}\n\n"
    "Content: {body}"
)

# Seconds to wait between API calls (stay within Haiku's 50 RPM free tier)
INTER_CALL_SLEEP = 1.3

# How many times to retry a single item on transient API errors
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------

def _get_client():
    try:
        import anthropic
    except ImportError:
        log.error("anthropic is not installed. Run: pip install anthropic")
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        log.error(
            "ANTHROPIC_API_KEY not found.\n"
            "Add it to T-tools/01-skills/intel-pipeline/.env or "
            "T-tools/01-skills/youtube-extraction/.env"
        )
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


def _resolve_model(client) -> str:
    """
    Query the Anthropic API for currently available models and return the
    best one for binary classification (cheapest Claude 4 haiku, then sonnet).
    Falls back to MODEL_FALLBACK if the API call fails or no Claude 4 is found.
    """
    try:
        ids = [m.id for m in client.models.list().data]
        # Target Claude 4 family — skip deprecated 3.x series
        claude4 = [
            m for m in ids
            if "claude" in m.lower()
            and any(marker in m for marker in ("-4-", "claude-4", "haiku-4", "sonnet-4", "opus-4"))
        ]
        for tier in _MODEL_TIER_PREFERENCE:
            matches = sorted(m for m in claude4 if tier in m.lower())
            if matches:
                chosen = matches[-1]  # highest version suffix alphabetically
                log.info("Model resolved via API: %s", chosen)
                return chosen
        log.warning("No Claude 4 models found in listing — using fallback: %s", MODEL_FALLBACK)
    except Exception as exc:
        log.warning("Model resolution failed (%s) — using fallback: %s", exc, MODEL_FALLBACK)
    return MODEL_FALLBACK


# ---------------------------------------------------------------------------
# Single-item filter
# ---------------------------------------------------------------------------

def _build_user_content(item: dict) -> str:
    body = (item.get("body") or "")[:800].strip()
    title = (item.get("title") or "").strip()
    return _USER_TEMPLATE.format(title=title, body=body)


def filter_item(client, item: dict, model_id: str) -> str:
    """
    Send one item to the resolved model. Returns 'YES', 'NO', or 'ERROR'.

    Uses prompt caching on the system prompt (ephemeral, 5-min TTL).
    Retries up to MAX_RETRIES times on rate-limit / transient errors.
    """
    import anthropic

    user_content = _build_user_content(item)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model_id,
                max_tokens=MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_content}],
            )
            verdict = response.content[0].text.strip().upper()
            # Normalise — Haiku sometimes returns "YES." or "NO."
            if verdict.startswith("YES"):
                return "YES"
            if verdict.startswith("NO"):
                return "NO"
            log.warning("Unexpected Haiku response: %r — treating as NO", verdict)
            return "NO"

        except anthropic.RateLimitError:
            wait = 10 * attempt
            log.warning("Rate limit hit — waiting %ds (attempt %d/%d)", wait, attempt, MAX_RETRIES)
            time.sleep(wait)

        except anthropic.APIError as exc:
            log.warning("API error on attempt %d: %s", attempt, exc)
            time.sleep(3 * attempt)

        except Exception as exc:
            log.warning("Unexpected error on attempt %d: %s", attempt, exc)
            time.sleep(2)

    return "ERROR"


# ---------------------------------------------------------------------------
# Fetch pending items directly (not llm_approved — these haven't been filtered)
# ---------------------------------------------------------------------------

def _fetch_pending(limit: Optional[int] = None) -> list[dict]:
    import json
    conn = get_db()
    query = (
        "SELECT * FROM intel_items WHERE status = 'pending' "
        "ORDER BY raw_score DESC, created_at DESC"
    )
    if limit:
        query += f" LIMIT {int(limit)}"
    rows = conn.execute(query).fetchall()
    conn.close()

    items = []
    for row in rows:
        d = dict(row)
        d["cluster_tags"] = json.loads(d.get("cluster_tags") or "[]")
        d["meta"]         = json.loads(d.get("meta_json") or "{}")
        del d["meta_json"]
        items.append(d)
    return items


# ---------------------------------------------------------------------------
# Main filter run
# ---------------------------------------------------------------------------

def run_filter(dry_run: bool = False, limit: Optional[int] = None) -> dict:
    """
    Process all pending items through the Haiku sieve.

    dry_run=True: print what would be sent but make no API calls and no DB writes.
    """
    items = _fetch_pending(limit=limit)

    if not items:
        log.info("No pending items to filter.")
        return {"total": 0, "approved": 0, "rejected": 0, "errors": 0}

    # Resolve the active model once before the loop — not per-item
    if dry_run:
        client   = None
        model_id = MODEL_FALLBACK
    else:
        client   = _get_client()
        model_id = _resolve_model(client)

    log.info(
        "Filtering %d pending item(s) with %s%s ...",
        len(items), model_id, " [DRY RUN]" if dry_run else ""
    )

    approved = rejected = errors = 0

    for idx, item in enumerate(items, 1):
        title   = item["title"][:70]
        item_id = item["item_id"]
        score   = item["raw_score"]

        if dry_run:
            print(f"  [{idx:>3}/{len(items)}] [{score:>5.1f}] {title}")
            print(f"         → Would send to {model_id} ({len(_build_user_content(item))} chars)")
            continue

        try:
            verdict = filter_item(client, item, model_id)
        except Exception as exc:
            # Hard safety net — one broken item must never abort the entire batch
            log.error("  [%3d/%d] FATAL on item %s: %s — skipping", idx, len(items), item_id, exc)
            errors += 1
            time.sleep(INTER_CALL_SLEEP)
            continue

        if verdict == "YES":
            update_item_status(item_id, "llm_approved", score_delta=SCORE_BOOST)
            approved += 1
            log.info("  [%3d/%d] YES [%.1f→%.1f] %s", idx, len(items), score, score + SCORE_BOOST, title)
        elif verdict == "NO":
            update_item_status(item_id, "rejected")
            rejected += 1
            log.debug("  [%3d/%d] NO  [%.1f] %s", idx, len(items), score, title)
        else:
            errors += 1
            log.warning("  [%3d/%d] ERR [%.1f] %s — left as pending", idx, len(items), score, title)

        time.sleep(INTER_CALL_SLEEP)

    return {
        "total":    len(items),
        "approved": approved,
        "rejected": rejected,
        "errors":   errors,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal Intel Pipeline — Stage 2: Haiku Sieve"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Process all pending items through Claude 3 Haiku"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview items that would be sent — no API calls, no DB writes"
    )
    parser.add_argument(
        "--limit", type=int, metavar="N",
        help="Process only the top N pending items (by score)"
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
            print("Database is empty.")
        else:
            print("\nIntel Queue — Status Breakdown")
            print("=" * 45)
            grand_total = 0
            for status in ("pending", "llm_approved", "approved", "rejected", "skipped"):
                sources = stats.get(status, {})
                if sources:
                    n = sum(sources.values())
                    grand_total += n
                    src_str = ", ".join(f"{s}:{c}" for s, c in sources.items())
                    print(f"  {status:<14} {n:>5}  ({src_str})")
            print(f"  {'TOTAL':<14} {grand_total:>5}")
        return

    if args.dry_run:
        init_db()
        result = run_filter(dry_run=True, limit=args.limit)
        print(f"\nDry run complete — {result['total']} items would be sent to Haiku.")
        return

    if args.run:
        result = run_filter(dry_run=False, limit=args.limit)
        log.info(
            "Filter complete — Total: %d | Approved: %d | Rejected: %d | Errors: %d",
            result["total"], result["approved"], result["rejected"], result["errors"]
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
