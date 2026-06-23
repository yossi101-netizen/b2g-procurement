"""Discovery chain: cache-first orchestrator wrapping multiple backends.

Fallback order: yt-dlp → YouTube Data API (if key set) → RSS feed
Stale-cache safety net: if every backend fails but SQLite has prior data,
return that and warn — so a yt-dlp outage never kills an active session.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from .base import DiscoveryError
from .rss import RssDiscoverer
from .ytdlp import YtDlpDiscoverer
from ..models import Video
from ..state import Store

log = logging.getLogger(__name__)


def build_chain(api_key: Optional[str] = None) -> list:
    """Return backends in priority order. Data API sits between yt-dlp and RSS
    because it's official and returns full duration metadata (unlike RSS)."""
    backends: list = [YtDlpDiscoverer()]

    if api_key:
        try:
            from .dataapi import DataApiDiscoverer
            backends.append(DataApiDiscoverer(api_key))
            log.info("YouTube Data API backend enabled")
        except Exception as exc:
            log.debug("DataApiDiscoverer unavailable: %s", exc)

    backends.append(RssDiscoverer())
    return backends


class CachedDiscoverer:
    """Cache-first wrapper: hit the DB first, refresh from backends when stale."""

    def __init__(self, backends: list, store: Store, ttl_hours: int = 24) -> None:
        self.backends = backends
        self.store = store
        self.ttl = ttl_hours

    def _cache_is_fresh(self, channel_url: str) -> bool:
        last = self.store.get_last_run(channel_url)
        if last is None:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.ttl)
        return last > cutoff

    def discover(
        self,
        channel_url: str,
        limit: int,
        force_refresh: bool = False,
    ) -> list[Video]:
        if not force_refresh and self._cache_is_fresh(channel_url):
            cached = self.store.get_all_videos(channel_url)
            if cached:
                log.info(
                    "Cache hit (%d videos, TTL %dh not expired)",
                    len(cached), self.ttl,
                )
                return cached

        stored_cid = self.store.get_channel_id(channel_url)
        last_error: Optional[Exception] = None

        for backend in self.backends:
            log.info("Trying backend: %s", backend.name)
            try:
                videos = backend.list_videos(
                    channel_url, limit, channel_id=stored_cid
                )
                # Capture channel_id for RSS fallback on future runs
                if not stored_cid:
                    cid = next(
                        (v.channel_id for v in videos if v.channel_id), ""
                    )
                else:
                    cid = stored_cid

                for v in videos:
                    self.store.upsert_video(v)

                self.store.set_channel_meta(
                    channel_url,
                    channel_id=cid,
                    backend=backend.name,
                    count=len(videos),
                )
                log.info("Discovery via %s: %d videos", backend.name, len(videos))
                return videos

            except DiscoveryError as exc:
                log.warning("Backend '%s' failed: %s", backend.name, exc)
                last_error = exc
            except Exception as exc:
                log.warning("Backend '%s' unexpected error: %s", backend.name, exc)
                last_error = exc

        # Every backend failed — try stale cache as safety net
        stale = self.store.get_all_videos(channel_url)
        if stale:
            log.warning(
                "All backends failed (%s). Using stale cache (%d videos). "
                "Re-run once connectivity is restored.",
                last_error,
                len(stale),
            )
            return stale

        raise DiscoveryError(
            f"All discovery backends failed and no cached data available.\n"
            f"Last error: {last_error}\n\n"
            f"Try running: pip install -U yt-dlp"
        )

    def primary_hydrator(self):
        """Return the first backend that can hydrate per-video metadata."""
        for b in self.backends:
            if b.name in ("ytdlp", "dataapi"):
                return b.hydrate
        return None
