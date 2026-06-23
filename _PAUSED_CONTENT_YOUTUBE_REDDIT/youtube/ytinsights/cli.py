"""CLI entry point — orchestrates discovery, scoring, and the HITL review loop.

Commands:
  run     — main workflow: discover → score → HITL loop
  status  — show queue stats for a channel
  export  — export approved summaries to JSON
  doctor  — health-check all system components
"""
from __future__ import annotations

import json
import logging
import os
import sys
import urllib.request
from pathlib import Path
from typing import Optional

import typer
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .discovery import CachedDiscoverer, DiscoveryError, build_chain
from .models import Video
from .scoring import (
    apply_duration_filter,
    combine_and_rank,
    recheck_duration_filter,
    stage_a_score,
    stage_b_score,
)
from .state import Store
from .summarize import summarize_video
from .transcripts import fetch_transcript

load_dotenv()

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="YouTube channel insight extractor with human-in-the-loop approval.",
)
console = Console()
log = logging.getLogger("ytinsights")

_DEFAULT_PROFILE = (
    "I am a business operator looking for actionable, non-obvious insights — "
    "frameworks, practitioner case studies, and operator-level playbooks. "
    "Skip motivational, biographical, and generic productivity content."
)

_DEFAULT_CFG: dict = {
    "interest_profile": _DEFAULT_PROFILE,
    "max_summary_tokens": 1500,
    "discovery": {
        "cache_ttl_hours": 24,
        "limit": 300,
        "hydration_pool_size": 40,
        "hydration_workers": 3,
    },
    "scoring": {
        "stage_a_batch_size": 50,
        "diversity_enabled": True,
    },
    "duration_filter": {"min_sec": 90, "max_sec": 3599},
    "transcript": {
        "languages": ["en", "en-US", "en-GB"],
        "use_whisper_fallback": False,
    },
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_config(path: Path) -> dict:
    if not path.exists():
        return _DEFAULT_CFG
    user = json.loads(path.read_text(encoding="utf-8"))
    # Deep-merge user config over defaults
    merged = dict(_DEFAULT_CFG)
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return merged


def _make_client() -> Anthropic:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or not key.startswith("sk-ant-"):
        console.print(
            "[red]ANTHROPIC_API_KEY missing or invalid. "
            "Add it to .env or your shell environment.[/red]"
        )
        raise typer.Exit(2)
    return Anthropic(api_key=key)


def _fmt_stats(s: dict[str, int]) -> str:
    parts = [
        f"[green]{s['approved']} approved[/green]",
        f"[yellow]{s['pending']} pending[/yellow]",
        f"[dim]{s['skipped']} skipped · "
        f"{s['no_transcript']} no-transcript · "
        f"{s['filtered_long']} ≥60min · "
        f"{s['filtered_short']} <90s · "
        f"{s['error']} errors[/dim]",
    ]
    return "  ".join(parts)


# ── Scoring orchestration ─────────────────────────────────────────────────────

def _run_scoring(
    channel_url: str,
    store: Store,
    client: Anthropic,
    cfg: dict,
    cached_discoverer: CachedDiscoverer,
) -> None:
    unscored = store.get_unscored_videos(channel_url)
    if not unscored:
        console.print("[dim]No new videos to score.[/dim]")
        return

    console.print(f"[cyan]Scoring {len(unscored)} new videos…[/cyan]")
    dur = cfg["duration_filter"]
    min_s, max_s = dur["min_sec"], dur["max_sec"]

    # ── Duration pre-filter ──────────────────────────────────────────────────
    passing, n_short, n_long, n_unknown = apply_duration_filter(
        unscored, min_s, max_s, store, channel_url
    )
    console.print(
        f"[dim]Duration filter: [green]{len(passing)} pass[/green] · "
        f"{n_long} ≥60 min removed · "
        f"{n_short} <90 s removed · "
        f"{n_unknown} unknown (deferred to Stage B)[/dim]"
    )
    if not passing:
        console.print("[yellow]No videos survive the duration filter.[/yellow]")
        return

    # ── Stage A — title scoring (all passing videos) ─────────────────────────
    with console.status(
        f"[cyan]Stage A — title relevance ({len(passing)} videos)…[/cyan]"
    ):
        a_scores, a_tags = stage_a_score(
            client,
            passing,
            cfg["interest_profile"],
            cfg["scoring"]["stage_a_batch_size"],
        )

    # Sort by Stage A to select Stage B pool
    passing_sorted = sorted(passing, key=lambda v: a_scores.get(v.id, 0), reverse=True)

    # ── Stage B — description hydration + re-score ───────────────────────────
    hydrate_fn = cached_discoverer.primary_hydrator()
    b_scores: dict[str, float] = {}
    pool = cfg["discovery"]["hydration_pool_size"]
    workers = cfg["discovery"]["hydration_workers"]

    if hydrate_fn:
        with console.status(
            f"[cyan]Stage B — hydrating top {min(pool, len(passing_sorted))} "
            f"descriptions ({workers} workers)…[/cyan]"
        ):
            b_scores = stage_b_score(
                client,
                passing_sorted,
                cfg["interest_profile"],
                hydrate_fn,
                pool_size=pool,
                workers=workers,
                store=store,
            )
    else:
        console.print("[yellow]No hydration backend available — skipping Stage B.[/yellow]")

    # ── Re-check duration filter on freshly hydrated videos ─────────────────
    passing_sorted = recheck_duration_filter(passing_sorted, min_s, max_s, store)
    for vid_id in list(b_scores):
        row = store.get_video(vid_id)
        if row and row["status"] in ("filtered_short", "filtered_long"):
            del b_scores[vid_id]

    if not passing_sorted:
        console.print("[yellow]All videos removed by duration filter after hydration.[/yellow]")
        return

    # ── Stage C — combine + diversity rebalance ──────────────────────────────
    final_scored = combine_and_rank(
        passing_sorted,
        a_scores,
        a_tags,
        b_scores,
        diversity_enabled=cfg["scoring"]["diversity_enabled"],
    )

    # ── Persist queue positions ──────────────────────────────────────────────
    offset = store.get_max_queue_pos(channel_url)
    for i, s in enumerate(final_scored):
        store.set_score(
            s.video.id,
            title_relevance=s.title_relevance,
            category_tag=s.category_tag,
            desc_relevance=s.desc_relevance,
            final_score=s.final,
            queue_pos=offset + i + 1,
        )
        store.set_status(s.video.id, "pending")

    # ── Show ranking table ───────────────────────────────────────────────────
    table = Table(title=f"Top {min(15, len(final_scored))} ranked videos", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Rel", justify="right")
    table.add_column("Desc", justify="right")
    table.add_column("Cat", style="cyan")
    table.add_column("Min", justify="right")
    table.add_column("Views", justify="right", style="dim")
    table.add_column("Title")

    for i, s in enumerate(final_scored[:15], 1):
        desc_str = f"{s.desc_relevance:.1f}" if s.desc_relevance is not None else "—"
        table.add_row(
            str(i),
            f"{s.title_relevance:.1f}",
            desc_str,
            s.category_tag[:10],
            str(s.video.duration_sec // 60),
            f"{s.video.view_count:,}",
            s.video.title[:72],
        )
    console.print(table)
    console.print(
        f"[dim]Rel = Stage A title score · Desc = Stage B description score · "
        f"Cat = topic category · Views shown for context only (not used in ranking)[/dim]"
    )


# ── HITL loop ─────────────────────────────────────────────────────────────────

def _hitl_loop(channel_url: str, store: Store, client: Anthropic, cfg: dict) -> None:
    console.rule("[bold magenta]Human-in-the-Loop Review[/bold magenta]")
    while True:
        row = store.next_actionable(channel_url)
        if row is None:
            stats = store.stats(channel_url)
            console.print("\n[green]No more videos to review.[/green]")
            console.print(_fmt_stats(stats))
            console.print(
                "[dim]Re-run with --fresh to re-discover, "
                "or --rescore to rebuild the queue.[/dim]"
            )
            break
        _process_one(row, store, client, cfg)


def _process_one(row, store: Store, client: Anthropic, cfg: dict) -> None:
    video = Video(
        id=row["id"],
        title=row["title"] or "",
        url=row["url"] or f"https://www.youtube.com/watch?v={row['id']}",
        channel_url=row["channel_url"],
        channel_id=row["channel_id"] or "",
        duration_sec=row["duration_sec"] or 0,
        view_count=row["view_count"] or 0,
        like_count=row["like_count"] or 0,
        comment_count=row["comment_count"] or 0,
        upload_date=row["upload_date"] or "",
        description=row["description"] or "",
    )

    stats = store.stats(video.channel_url)
    console.print(f"\n[dim]{_fmt_stats(stats)}[/dim]")

    rel = f"{row['title_relevance']:.1f}" if row["title_relevance"] is not None else "?"
    desc_rel = (
        f"/ {row['desc_relevance']:.1f}" if row["desc_relevance"] is not None else ""
    )
    header = (
        f"[bold white]{video.title}[/bold white]\n"
        f"[dim]{video.url}\n"
        f"{video.duration_sec // 60} min  ·  "
        f"{video.view_count:,} views  ·  "
        f"relevance {rel}{desc_rel}  ·  "
        f"[cyan]{row['category_tag'] or '—'}[/cyan][/dim]"
    )
    console.print(Panel(header, border_style="cyan", padding=(0, 1)))

    # ── Transcript ───────────────────────────────────────────────────────────
    transcript = row["transcript"]
    if not transcript:
        with console.status("[cyan]Fetching transcript…[/cyan]"):
            transcript = fetch_transcript(
                video.id,
                languages=cfg["transcript"]["languages"],
                use_whisper_fallback=cfg["transcript"]["use_whisper_fallback"],
            )
        if transcript:
            store.set_status(video.id, "pending", transcript=transcript)
        else:
            store.set_status(video.id, "no_transcript",
                             error="No transcript available from any source")
            console.print("[yellow]No transcript found — skipping.[/yellow]")
            return

    # ── Summary ──────────────────────────────────────────────────────────────
    summary_md = row["summary"]
    if not summary_md:
        summary_md = _generate_summary(client, video, transcript, cfg)
        store.set_status(video.id, "summarized", summary=summary_md)

    console.print(Markdown(summary_md))

    # ── HITL prompt ──────────────────────────────────────────────────────────
    _hitl_prompt(video, store, client, cfg, transcript)


def _generate_summary(
    client: Anthropic,
    video: Video,
    transcript: str,
    cfg: dict,
    extra_focus: Optional[str] = None,
) -> str:
    with console.status("[cyan]Summarising with Claude Sonnet 4.6…[/cyan]"):
        s = summarize_video(
            client=client,
            video=video,
            transcript=transcript,
            interest_profile=cfg["interest_profile"],
            max_tokens=cfg.get("max_summary_tokens", 1500),
            extra_focus=extra_focus,
        )

    cache_note = ""
    if s.tokens_cached_read:
        cache_note = f", cache hit {s.tokens_cached_read} tok"
    elif s.tokens_cached_write:
        cache_note = f", cache write {s.tokens_cached_write} tok"
    console.print(
        f"[dim]Tokens — in: {s.tokens_input}, out: {s.tokens_output}"
        f"{cache_note}[/dim]"
    )
    return s.markdown


def _hitl_prompt(
    video: Video,
    store: Store,
    client: Anthropic,
    cfg: dict,
    transcript: str,
) -> None:
    menu = (
        "\n[bold yellow]Decision:[/bold yellow] "
        "[a]pprove  [s]kip  [r]egenerate  [n]ote  [o]pen  [q]uit"
    )
    while True:
        console.print(menu)
        raw = Prompt.ask("", choices=["a", "s", "r", "n", "o", "q"],
                         default="a", show_choices=False)

        if raw == "a":
            store.set_status(video.id, "approved")
            console.print("[green]✓ Approved.[/green]")
            return

        if raw == "s":
            reason = Prompt.ask("Reason (optional)", default="")
            store.set_status(video.id, "skipped", error=reason or None)
            console.print("[yellow]Skipped.[/yellow]")
            return

        if raw == "r":
            focus = Prompt.ask(
                "Additional focus for regeneration "
                "(e.g. 'pricing model', 'GTM tactics')",
                default="",
            )
            new_md = _generate_summary(
                client, video, transcript, cfg, extra_focus=focus or None
            )
            store.set_status(video.id, "summarized", summary=new_md)
            console.print(Markdown(new_md))
            continue

        if raw == "n":
            note = Prompt.ask("Note")
            existing = store.get_video(video.id)["user_notes"] or ""
            combined = f"{existing}\n{note}".strip()
            store.set_status(video.id, "summarized", user_notes=combined)
            console.print("[green]Note saved.[/green]")
            continue

        if raw == "o":
            console.print(f"[blue]{video.url}[/blue]")
            try:
                import webbrowser
                webbrowser.open(video.url)
            except Exception:
                pass
            continue

        if raw == "q":
            console.print("[dim]Session saved. Re-run to continue.[/dim]")
            sys.exit(0)


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def run(
    channel_url: str = typer.Argument(..., help="YouTube channel URL."),
    config: Path = typer.Option(Path("config.json"), help="Config file path."),
    db: Path = typer.Option(Path("ytinsights.db"), help="SQLite state file."),
    limit: int = typer.Option(300, help="Max videos to discover."),
    fresh: bool = typer.Option(False, help="Force re-discovery (ignore cache)."),
    rescore: bool = typer.Option(False, help="Re-score already-scored videos."),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Discover, prioritize, and review channel videos one at a time."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = _load_config(config)
    client = _make_client()
    store = Store(db)

    yt_api_key = os.getenv("YOUTUBE_API_KEY") or None
    chain = build_chain(api_key=yt_api_key)
    cached = CachedDiscoverer(chain, store, ttl_hours=cfg["discovery"]["cache_ttl_hours"])

    # ── Discovery ──────────────────────────────────────────────────────────
    console.rule(f"[bold cyan]{channel_url}[/bold cyan]")
    with console.status("[cyan]Discovering videos…[/cyan]"):
        try:
            videos = cached.discover(channel_url, limit=limit, force_refresh=fresh)
        except DiscoveryError as exc:
            console.print(f"[red]Discovery failed:[/red] {exc}")
            raise typer.Exit(1)

    console.print(f"[green]{len(videos)} videos in library.[/green]")

    # ── Scoring ────────────────────────────────────────────────────────────
    if rescore:
        # Mark all pending/scored videos as unscored so they re-enter pipeline
        for v in videos:
            row = store.get_video(v.id)
            if row and row["status"] in ("pending", "scored"):
                store.set_status(v.id, "unscored")

    if store.has_unscored(channel_url):
        _run_scoring(channel_url, store, client, cfg, cached)
    else:
        console.print("[dim]All videos already scored. Use --rescore to rebuild.[/dim]")

    # ── HITL loop ──────────────────────────────────────────────────────────
    _hitl_loop(channel_url, store, client, cfg)


@app.command()
def status(
    channel_url: str = typer.Argument(...),
    db: Path = typer.Option(Path("ytinsights.db")),
) -> None:
    """Show queue stats for a channel."""
    s = Store(db).stats(channel_url)
    table = Table(title=f"Queue: {channel_url}", show_lines=False)
    table.add_column("Status")
    table.add_column("Count", justify="right")
    for k, v in s.items():
        style = "green" if k == "approved" else ("yellow" if k == "pending" else "dim")
        table.add_row(k, str(v), style=style)
    console.print(table)


@app.command()
def export(
    channel_url: str = typer.Argument(...),
    out: Path = typer.Option(Path("approved.json")),
    db: Path = typer.Option(Path("ytinsights.db")),
) -> None:
    """Export all approved summaries to a JSON file."""
    n = Store(db).export_approved(channel_url, out)
    console.print(f"[green]Exported {n} approved summaries → {out}[/green]")


@app.command()
def doctor(
    db: Path = typer.Option(Path("ytinsights.db")),
) -> None:
    """Health-check all system components."""
    table = Table(title="System diagnostics", show_lines=False)
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Detail")

    def _row(name: str, ok: bool, detail: str = "") -> None:
        icon = "[green]✓ OK[/green]" if ok else "[red]✗ FAIL[/red]"
        table.add_row(name, icon, detail)

    # 1. Anthropic API key
    key = os.getenv("ANTHROPIC_API_KEY", "")
    _row("ANTHROPIC_API_KEY", key.startswith("sk-ant-"),
         "Present" if key.startswith("sk-ant-") else "Missing or malformed")

    # 2. yt-dlp version
    try:
        import importlib.metadata
        current = importlib.metadata.version("yt-dlp")
        try:
            with urllib.request.urlopen(
                "https://pypi.org/pypi/yt-dlp/json", timeout=3
            ) as r:
                latest = json.loads(r.read())["info"]["version"]
            outdated = current != latest
            _row(
                "yt-dlp version",
                not outdated,
                f"{current}" + (f" → {latest} available" if outdated else " (latest)"),
            )
        except Exception:
            _row("yt-dlp version", True, f"{current} (PyPI check failed)")
    except Exception as exc:
        _row("yt-dlp version", False, str(exc))

    # 3. yt-dlp functional test (first YouTube video — always public)
    try:
        from .discovery.ytdlp import YtDlpDiscoverer
        disc = YtDlpDiscoverer()
        result = disc.hydrate("jNQXAC9IVRw")  # "Me at the zoo" — first YT video
        _row("yt-dlp functional", result is not None,
             f"title={result.title[:40]!r}" if result else "hydration returned None")
    except Exception as exc:
        _row("yt-dlp functional", False, str(exc)[:80])

    # 4. RSS feed
    try:
        from .discovery.rss import RssDiscoverer
        rss = RssDiscoverer()
        # YouTube's official channel — always has videos
        vids = rss.list_videos("", 3, channel_id="UCBR8-60-B28hp2BmDPdntcQ")
        _row("RSS feed", len(vids) > 0, f"returned {len(vids)} videos")
    except Exception as exc:
        _row("RSS feed", False, str(exc)[:80])

    # 5. YouTube Data API (optional)
    yt_key = os.getenv("YOUTUBE_API_KEY", "")
    if yt_key:
        try:
            from .discovery.dataapi import DataApiDiscoverer
            da = DataApiDiscoverer(yt_key)
            result = da.hydrate("jNQXAC9IVRw")
            _row("YouTube Data API", result is not None,
                 "key valid" if result else "hydration returned None")
        except Exception as exc:
            _row("YouTube Data API", False, str(exc)[:80])
    else:
        table.add_row("YouTube Data API", "[dim]—[/dim]", "YOUTUBE_API_KEY not set (optional)")

    # 6. SQLite
    try:
        s = Store(db)
        _ = s.stats("__doctor__")
        _row("SQLite state", True, str(db))
    except Exception as exc:
        _row("SQLite state", False, str(exc)[:80])

    # 7. transcript-api import
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # noqa: F401
        _row("youtube-transcript-api", True, "importable")
    except ImportError as exc:
        _row("youtube-transcript-api", False, str(exc))

    console.print(table)
    console.print(
        "\n[dim]If yt-dlp is broken: run [bold]pip install -U yt-dlp[/bold] — "
        "the RSS fallback will serve recent videos in the meantime.[/dim]"
    )
