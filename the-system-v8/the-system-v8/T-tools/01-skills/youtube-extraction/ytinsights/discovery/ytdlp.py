"""Primary discovery backend: yt-dlp.

Resilience strategy:
  - tenacity retries (3 attempts, exponential back-off) on every network call
  - Non-retryable errors (private/unavailable channel) fail fast
  - yt-dlp version staleness check cached to a stamp file (24 h TTL)
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yt_dlp
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .base import DiscoveryError
from ..models import Video

log = logging.getLogger(__name__)

_VERSION_STAMP = Path(".ytdlp_ver_check")
_VERSION_TTL = timedelta(hours=24)

# Resolve cookies.txt relative to this file's location:
# ytdlp.py  →  discovery/  →  ytinsights/  →  youtube-extraction/  ← cookies.txt lives here
_COOKIE_PATH: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "cookies.txt")
)

print(f"\n[SYSTEM] Cookie file path resolved to: {_COOKIE_PATH} | Exists: {os.path.exists(_COOKIE_PATH)}\n")

if not os.path.exists(_COOKIE_PATH):
    log.warning(
        "[SYSTEM] cookies.txt NOT FOUND at %s — yt-dlp will run without cookies "
        "and may be blocked by YouTube bot detection.",
        _COOKIE_PATH,
    )

_FLAT_OPTS: dict = {
    "extract_flat": "in_playlist",
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "sleep_requests": 0.5,
    "retries": 5,
    "extractor_retries": 3,
    "cookiefile": _COOKIE_PATH,
}

_HYDRATE_OPTS: dict = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "sleep_requests": 0.5,
    "retries": 3,
    "cookiefile": _COOKIE_PATH,
}

_NON_RETRYABLE = (
    "channel not found",
    "this channel does not exist",
    "video is unavailable",
    "video is private",
    "unrecognized url",
    "unable to extract",
)


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return not any(p in msg for p in _NON_RETRYABLE)


def _normalize_channel_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not re.search(r"/(videos|streams|shorts)$", url):
        if re.search(r"youtube\.com/(channel/|@|c/|user/)", url):
            url += "/videos"
    return url


def check_ytdlp_update() -> None:
    """One-time (per 24 h) nudge if yt-dlp is outdated."""
    try:
        import importlib.metadata
        current = importlib.metadata.version("yt-dlp")
    except Exception:
        return

    if _VERSION_STAMP.exists():
        age = datetime.now() - datetime.fromtimestamp(_VERSION_STAMP.stat().st_mtime)
        if age < _VERSION_TTL:
            return

    try:
        with urllib.request.urlopen(
            "https://pypi.org/pypi/yt-dlp/json", timeout=3
        ) as r:
            latest = json.loads(r.read())["info"]["version"]
        _VERSION_STAMP.write_text(f"{current}→{latest}")
        if current != latest:
            log.warning(
                "yt-dlp %s is outdated (latest: %s). "
                "Update with: pip install -U yt-dlp",
                current,
                latest,
            )
    except Exception:
        pass  # version check is best-effort


class YtDlpDiscoverer:
    name = "ytdlp"

    def __init__(self) -> None:
        check_ytdlp_update()

    # ------------------------------------------------------------------
    # Channel listing
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        before_sleep=before_sleep_log(log, logging.DEBUG),
        reraise=True,
    )
    def _flat_extract(self, url: str, limit: int) -> list[dict]:
        opts = dict(_FLAT_OPTS)
        opts["playlistend"] = limit
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(_normalize_channel_url(url), download=False)
        return [e for e in (info.get("entries") or []) if e and e.get("id")]

    def list_videos(self, channel_url: str, limit: int, **kwargs) -> list[Video]:
        try:
            entries = self._flat_extract(channel_url, limit)
        except Exception as exc:
            raise DiscoveryError(f"yt-dlp channel listing failed: {exc}") from exc

        videos: list[Video] = []
        channel_id = ""
        for e in entries:
            if not channel_id:
                channel_id = e.get("channel_id") or ""
            videos.append(
                Video(
                    id=e["id"],
                    title=e.get("title") or "",
                    url=e.get("url") or f"https://www.youtube.com/watch?v={e['id']}",
                    channel_url=channel_url,
                    channel_id=channel_id,
                    duration_sec=int(e.get("duration") or 0),
                    view_count=int(e.get("view_count") or 0),
                    like_count=int(e.get("like_count") or 0),
                    comment_count=int(e.get("comment_count") or 0),
                    upload_date=str(e.get("upload_date") or ""),
                    description=(e.get("description") or "")[:2000],
                )
            )
        log.info("yt-dlp: discovered %d videos", len(videos))
        return videos

    # ------------------------------------------------------------------
    # Per-video hydration (Stage B descriptions + duration correction)
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        reraise=True,
    )
    def _fetch_info(self, video_id: str) -> dict:
        with yt_dlp.YoutubeDL(_HYDRATE_OPTS) as ydl:
            return ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )

    def hydrate(self, video_id: str) -> Optional[Video]:
        try:
            info = self._fetch_info(video_id)
        except Exception as exc:
            if not _is_retryable(exc):
                log.debug("Non-retryable hydration skip for %s: %s", video_id, exc)
            else:
                log.warning("Hydration failed for %s: %s", video_id, exc)
            return None

        return Video(
            id=video_id,
            title=info.get("title") or "",
            url=f"https://www.youtube.com/watch?v={video_id}",
            channel_url="",
            channel_id=info.get("channel_id") or "",
            duration_sec=int(info.get("duration") or 0),
            view_count=int(info.get("view_count") or 0),
            like_count=int(info.get("like_count") or 0),
            comment_count=int(info.get("comment_count") or 0),
            upload_date=str(info.get("upload_date") or ""),
            description=(info.get("description") or "")[:2000],
        )
