"""Claude Sonnet 4.6 summarization with prompt caching.

The analyst system prompt (~500 tokens) is marked ephemeral so it is cached
after the first call. Subsequent summaries in the same session pay ~10% of the
normal input cost for that portion.

Cache economics per 30-video session:
  Write: first call pays +25% on system prompt tokens (~125 extra tokens)
  Reads: remaining 29 calls save ~90% on system prompt tokens
  Net: roughly 26× fewer tokens billed for the system prompt portion.
"""
from __future__ import annotations

import logging
from typing import Optional

from anthropic import Anthropic

from .models import Summary, Video

log = logging.getLogger(__name__)

SUMMARY_MODEL = "claude-sonnet-4-6"

_SYSTEM = """\
You are an elite business analyst with deep operator experience. Your job: \
distill a YouTube video transcript into a tight, decision-grade insight \
document — tailored to the user's stated business focus.

OUTPUT FORMAT (strict Markdown, in this order):

# {Concise title — reframed around the core insight, not the video's title}

**TL;DR** — 1–2 sentences. The single most important takeaway, stated as a \
claim.

## Why This Matters For You
2–4 sentences explicitly connecting the video's content to the user's \
business focus. If the fit is weak, say so plainly.

## Key Insights
5–8 bullets. Each must be a *non-obvious* assertive claim anchored in \
transcript evidence (numbers, named examples, direct quotes preferred over \
abstractions). Format: "- **Claim.** Supporting evidence."

## Frameworks / Mental Models
List any reusable frameworks or mental models introduced. One-line description \
each. Write "None — purely tactical/anecdotal." if absent.

## Actionable Takeaways
3–6 checkboxes. Specific enough to put on a to-do list *this week*. \
Avoid "consider doing X" — write the action itself.
- [ ] Action

## Notable Quotes
1–3 verbatim quotes (≤25 words each) with the most signal. Omit section if \
nothing stands out.

## Caveats / What This Video Misses
1–3 bullets on weaknesses, missing context, or non-generalizable claims. \
This section is mandatory — never write "no caveats."

## Verdict
ONE of:
- **STUDY** — rewatch and work through the content actively
- **READ** — this summary captures what you need; move on
- **SKIP** — low signal relative to your priorities (explain in one sentence)

RULES:
- Never invent content absent from the transcript. Flag ambiguities: \
"transcript is unclear on X."
- Optimize for a busy operator skim-reading on a phone.
- No greetings, no meta-commentary, no "I hope this helps."\
"""


def summarize_video(
    client: Anthropic,
    video: Video,
    transcript: str,
    interest_profile: str,
    max_tokens: int = 1500,
    extra_focus: Optional[str] = None,
) -> Summary:
    # Transcripts beyond ~80 K chars (≈ 20 K tokens) rarely add signal;
    # truncating saves cost without material quality loss.
    if len(transcript) > 80_000:
        log.info("Transcript truncated to 80000 chars for %s", video.id)
        transcript = transcript[:80_000] + "\n\n[… transcript truncated …]"

    lines = [
        "## Video",
        f"- Title: {video.title}",
        f"- URL: {video.url}",
        f"- Duration: {video.duration_sec // 60} min",
        f"- Views: {video.view_count:,}",
        f"- Uploaded: {video.upload_date}",
        "",
        "## User's business focus",
        interest_profile.strip(),
    ]
    if extra_focus:
        lines += ["", "## Additional focus for this summary", extra_focus.strip()]
    lines += ["", "## Transcript", transcript]

    resp = client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=max_tokens,
        system=[{
            "type": "text",
            "text": _SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": "\n".join(lines)}],
    )

    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    u = resp.usage
    return Summary(
        video_id=video.id,
        markdown=text,
        tokens_input=getattr(u, "input_tokens", 0),
        tokens_output=getattr(u, "output_tokens", 0),
        tokens_cached_read=getattr(u, "cache_read_input_tokens", 0) or 0,
        tokens_cached_write=getattr(u, "cache_creation_input_tokens", 0) or 0,
    )
