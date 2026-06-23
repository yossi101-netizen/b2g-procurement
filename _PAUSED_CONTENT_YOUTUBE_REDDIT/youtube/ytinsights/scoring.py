"""Six-stage relevance-first video prioritization.

Key design principle: engagement metrics (views, likes) are NEVER used as
quality signals. Low view-count niche content scores identically to viral
content when their titles/descriptions are equally relevant to the user's
stated interests.

Stage A — Title + duration scored by Haiku 4.5 on ALL duration-filtered videos.
Stage B — Descriptions hydrated in parallel (yt-dlp); top-N re-scored by Haiku.
Stage C — Diversity rebalancing: round-robin across LLM-assigned topic categories
           so the queue isn't dominated by one theme.

Final score = 0.4 × stage_a + 0.6 × stage_b  (or stage_a if no description).
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from anthropic import Anthropic

from .models import ScoredVideo, Video
from .state import Store

log = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"
_FALLBACK_CATEGORY = "general"

# ── System prompt cached across all scoring calls in a session ──────────────
_SCORER_SYSTEM = """\
You are a precision content classifier for a senior business operator who \
wants DEEP, ACTIONABLE business insights — not motivation, not biographies, \
not generic productivity content.

SCORE GUIDE (0–10):
  9–10  Highly specific practitioner content: named case studies, precise \
metrics, novel frameworks, niche tactical depth. Domain jargon in title \
signals expertise, not reach.
  7–8   Strong signal: domain depth implied, frameworks or concrete playbooks \
suggested.
  5–6   Moderate: title is generic but topic is plausible; could be good or \
shallow — score in the middle.
  3–4   Low signal: common surface-level advice, probable listicle.
  1–2   Likely noise: motivational, biographical, news recap, trend commentary.
  0     Off-topic: unrelated to the user's interests.

POSITIVE MARKERS: domain-specific jargon, numbers in the title, "how we …", \
"lessons from …", named companies/products, concrete mechanisms (e.g. \
"seat-expansion model", "ICP segmentation"), duration ≥ 15 min.
NEGATIVE MARKERS: "X ways to", "you need to", "I made $X", clickbait \
punctuation (!!), ALL-CAPS words, "mindset", "motivation", vague \
superlatives ("best ever", "secret to"), duration < 8 min.

CRITICAL: Low view count is NOT a negative signal. Niche practitioner content \
routinely has small audiences and very high information density.\
"""


# ── Prompt builders ──────────────────────────────────────────────────────────

def _stage_a_user_msg(interest_profile: str, listing: str) -> str:
    return (
        f"USER INTEREST PROFILE:\n{interest_profile}\n\n"
        f"VIDEOS (N. [duration-min] Title):\n{listing}\n\n"
        "Return a single JSON object — NO prose, NO markdown fences:\n"
        '{"scores":[<float 0-10>,...], "tags":["<1-word category>",...]}\n'
        "Both arrays must be the same length as the video list, in order.\n"
        "Category tag examples: pricing, gtm, hiring, retention, fundraising, "
        "operations, product, content, engineering, leadership, fluff, other"
    )


def _stage_b_user_msg(interest_profile: str, listing: str) -> str:
    return (
        f"USER INTEREST PROFILE:\n{interest_profile}\n\n"
        "Re-score these videos now that you have their descriptions. "
        "Adjust upward where descriptions reveal depth hidden by a weak title; "
        "adjust downward where descriptions reveal shallowness despite a good title.\n\n"
        f"VIDEOS (N. [duration-min] Title | Description excerpt):\n{listing}\n\n"
        'Return ONLY: {"scores":[<float 0-10>,...]}  — same length and order.'
    )


# ── LLM call helper ──────────────────────────────────────────────────────────

def _haiku(client: Anthropic, user_msg: str) -> str:
    resp = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=2048,
        system=[{
            "type": "text",
            "text": _SCORER_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_msg}],
    )
    return "".join(b.text for b in resp.content if hasattr(b, "text"))


# ── JSON parsers ─────────────────────────────────────────────────────────────

def _parse_scores(raw: str, expected: int, key: str = "scores") -> list[float]:
    try:
        m = re.search(r"\{[\s\S]+\}", raw)
        obj = json.loads(m.group(0)) if m else {}
        arr = [float(x) for x in obj.get(key, [])]
    except Exception:
        log.debug("Score parse failed on: %.200s", raw)
        arr = []
    arr += [5.0] * max(0, expected - len(arr))
    return arr[:expected]


def _parse_tags(raw: str, expected: int) -> list[str]:
    try:
        m = re.search(r"\{[\s\S]+\}", raw)
        obj = json.loads(m.group(0)) if m else {}
        tags = [
            (str(x).lower().split()[0] if x else _FALLBACK_CATEGORY)
            for x in obj.get("tags", [])
        ]
    except Exception:
        tags = []
    tags += [_FALLBACK_CATEGORY] * max(0, expected - len(tags))
    return tags[:expected]


# ── Public pipeline stages ───────────────────────────────────────────────────

def stage_a_score(
    client: Anthropic,
    videos: list[Video],
    interest_profile: str,
    batch_size: int = 50,
) -> tuple[dict[str, float], dict[str, str]]:
    """Score ALL videos by title alone. Returns (score_map, tag_map)."""
    scores: dict[str, float] = {}
    tags: dict[str, str] = {}

    for start in range(0, len(videos), batch_size):
        chunk = videos[start : start + batch_size]
        listing = "\n".join(
            f"{i + 1}. [{v.duration_sec // 60}min] {v.title}"
            for i, v in enumerate(chunk)
        )
        raw = _haiku(client, _stage_a_user_msg(interest_profile, listing))
        chunk_scores = _parse_scores(raw, len(chunk), "scores")
        chunk_tags = _parse_tags(raw, len(chunk))
        for v, s, t in zip(chunk, chunk_scores, chunk_tags):
            scores[v.id] = s
            tags[v.id] = t
        log.info(
            "Stage A: scored %d / %d",
            min(start + batch_size, len(videos)),
            len(videos),
        )

    return scores, tags


def stage_b_score(
    client: Anthropic,
    videos: list[Video],   # pre-sorted by Stage A desc; only top pool_size used
    interest_profile: str,
    hydrate_fn: Callable[[str], Optional[Video]],
    pool_size: int = 40,
    workers: int = 3,
    store: Optional[Store] = None,
) -> dict[str, float]:
    """Hydrate descriptions in parallel, then re-score. Returns desc_relevance_map."""
    candidates = videos[:pool_size]
    if not candidates:
        return {}

    # Parallel hydration — failures are silently skipped (graceful degradation)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(hydrate_fn, v.id): v for v in candidates}
        for fut in as_completed(futures, timeout=120):
            v = futures[fut]
            try:
                hydrated = fut.result()
                if hydrated:
                    if hydrated.description:
                        v.description = hydrated.description
                        if store:
                            store.update_description(v.id, hydrated.description)
                    # Correct duration for RSS-discovered videos (duration_sec==0)
                    if hydrated.duration_sec > 0 and v.duration_sec == 0:
                        v.duration_sec = hydrated.duration_sec
                        if store:
                            store.update_duration(v.id, hydrated.duration_sec)
            except Exception as exc:
                log.debug("Hydration future error for %s: %s", v.id, exc)

    hydrated_vids = [v for v in candidates if v.description]
    if not hydrated_vids:
        log.info("Stage B: no descriptions obtained — skipping re-score")
        return {}

    listing = "\n".join(
        f"{i + 1}. [{v.duration_sec // 60}min] {v.title} | {v.description[:300]}"
        for i, v in enumerate(hydrated_vids)
    )
    raw = _haiku(client, _stage_b_user_msg(interest_profile, listing))
    b_scores = _parse_scores(raw, len(hydrated_vids), "scores")
    log.info("Stage B: re-scored %d / %d candidates", len(hydrated_vids), pool_size)
    return {v.id: s for v, s in zip(hydrated_vids, b_scores)}


def apply_duration_filter(
    videos: list[Video],
    min_sec: int,
    max_sec: int,
    store: Store,
    channel_url: str,
) -> tuple[list[Video], int, int, int]:
    """Filter by duration. Returns (passing, n_short, n_long, n_unknown_kept)."""
    passing: list[Video] = []
    n_short = n_long = n_unknown = 0
    for v in videos:
        if v.duration_sec == 0:
            # Unknown duration (e.g. RSS-discovered): keep for now; Stage B
            # hydration may fill it in, and we re-check after Stage B.
            n_unknown += 1
            passing.append(v)
        elif v.duration_sec < min_sec:
            n_short += 1
            store.set_status(v.id, "filtered_short")
        elif v.duration_sec >= max_sec:
            n_long += 1
            store.set_status(v.id, "filtered_long")
        else:
            passing.append(v)
    return passing, n_short, n_long, n_unknown


def recheck_duration_filter(
    videos: list[Video],
    min_sec: int,
    max_sec: int,
    store: Store,
) -> list[Video]:
    """Re-apply duration filter after Stage B hydration updated durations."""
    passing: list[Video] = []
    for v in videos:
        if v.duration_sec > 0 and v.duration_sec >= max_sec:
            store.set_status(v.id, "filtered_long")
        elif v.duration_sec > 0 and v.duration_sec < min_sec:
            store.set_status(v.id, "filtered_short")
        else:
            passing.append(v)
    return passing


def combine_and_rank(
    videos: list[Video],
    a_scores: dict[str, float],
    a_tags: dict[str, str],
    b_scores: dict[str, float],
    diversity_enabled: bool = True,
) -> list[ScoredVideo]:
    """Merge stage scores → ScoredVideo list, optionally diversity-rebalanced."""
    result: list[ScoredVideo] = []
    for v in videos:
        a = a_scores.get(v.id, 5.0)
        b = b_scores.get(v.id)
        final = (a * 0.4 + b * 0.6) if b is not None else a
        result.append(
            ScoredVideo(
                video=v,
                title_relevance=a,
                category_tag=a_tags.get(v.id, _FALLBACK_CATEGORY),
                desc_relevance=b,
                final=final,
            )
        )

    result.sort(key=lambda s: s.final, reverse=True)

    if diversity_enabled:
        result = _diversity_rebalance(result)

    return result


def _diversity_rebalance(scored: list[ScoredVideo]) -> list[ScoredVideo]:
    """Round-robin across topic categories so no single theme dominates the queue.

    Each bucket is already sorted best-first (from the sort above), so the
    round-robin picks the best available video per category at each slot.
    """
    buckets: dict[str, list[ScoredVideo]] = defaultdict(list)
    for s in scored:
        buckets[s.category_tag].append(s)

    # Preserve deterministic order of category first-appearances
    order = list(dict.fromkeys(s.category_tag for s in scored))

    out: list[ScoredVideo] = []
    while any(buckets[k] for k in order):
        for k in order:
            if buckets[k]:
                out.append(buckets[k].pop(0))
    return out
