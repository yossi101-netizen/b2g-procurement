"""RSS fallback discovery — pure stdlib, zero scraping.

YouTube's Atom feed (youtube.com/feeds/videos.xml) has been stable for 10+ years.
Limitation: returns only the most recent ~15 videos. Used when yt-dlp is broken,
so the user still gets new content even during a yt-dlp outage.

Channel ID resolution order:
  1. Directly embedded in the URL  (/channel/UC...)
  2. Stored in SQLite from a prior successful yt-dlp run (passed in by caller)
  3. Light HTML fetch — regex for channelId in the page's inline JSON
"""
from __future__ import annotations

import logging
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

from .base import DiscoveryError
from ..models import Video

log = logging.getLogger(__name__)

_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"

_NS = {
    "atom":   "http://www.w3.org/2005/Atom",
    "yt":     "http://www.youtube.com/xml/schemas/2015",
    "media":  "http://search.yahoo.com/mrss/",
}
for _p, _u in _NS.items():
    ET.register_namespace(_p, _u)

_UA = "Mozilla/5.0 (compatible; ytinsights/0.2; +https://github.com/ytinsights)"


def _resolve_channel_id(channel_url: str, stored_id: Optional[str]) -> str:
    if stored_id:
        return stored_id

    # Direct /channel/UC... URL
    m = re.search(r"/channel/(UC[A-Za-z0-9_-]{22})", channel_url)
    if m:
        return m.group(1)

    # Scrape the channel page for embedded JSON
    try:
        req = urllib.request.Request(
            channel_url.rstrip("/"),
            headers={"User-Agent": _UA},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        for pattern in (
            r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
            r'"externalId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
            r'<link rel="canonical" href="[^"]*channel/(UC[A-Za-z0-9_-]{22})',
        ):
            m = re.search(pattern, html)
            if m:
                return m.group(1)
    except Exception as exc:
        log.debug("Channel ID HTML scrape failed: %s", exc)

    raise DiscoveryError(
        "Cannot resolve channel ID for RSS fallback.\n"
        "  • Run once with a working yt-dlp to cache the channel ID, OR\n"
        "  • Use a direct /channel/UC... URL"
    )


class RssDiscoverer:
    name = "rss"

    def list_videos(
        self,
        channel_url: str,
        limit: int,
        channel_id: Optional[str] = None,
        **kwargs,
    ) -> list[Video]:
        cid = _resolve_channel_id(channel_url, channel_id)
        feed_url = _RSS_URL.format(cid)
        log.info("RSS fallback fetch: %s", feed_url)

        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_bytes = resp.read()
        except urllib.error.URLError as exc:
            raise DiscoveryError(f"RSS feed unreachable: {exc}") from exc

        return self._parse(xml_bytes, channel_url, cid, limit)

    def _parse(
        self, xml_bytes: bytes, channel_url: str, channel_id: str, limit: int
    ) -> list[Video]:
        root = ET.fromstring(xml_bytes)

        def _text(el: ET.Element, tag: str) -> str:
            return el.findtext(tag, namespaces=_NS) or ""

        videos: list[Video] = []
        for entry in root.findall("atom:entry", _NS):
            if len(videos) >= limit:
                break
            vid_id = _text(entry, "yt:videoId")
            if not vid_id:
                continue

            title = _text(entry, "atom:title")
            published = _text(entry, "atom:published")
            upload_date = ""
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    upload_date = dt.strftime("%Y%m%d")
                except ValueError:
                    pass

            desc = ""
            view_count = 0
            mg = entry.find("media:group", _NS)
            if mg is not None:
                desc = (_text(mg, "media:description"))[:2000]
                community = mg.find("media:community", _NS)
                if community is not None:
                    stats = community.find("media:statistics", _NS)
                    if stats is not None:
                        view_count = int(stats.get("views") or 0)

            videos.append(
                Video(
                    id=vid_id,
                    title=title,
                    url=f"https://www.youtube.com/watch?v={vid_id}",
                    channel_url=channel_url,
                    channel_id=channel_id,
                    duration_sec=0,  # RSS does not carry duration
                    view_count=view_count,
                    upload_date=upload_date,
                    description=desc,
                )
            )

        log.info("RSS: parsed %d videos (most recent only)", len(videos))
        return videos

    def hydrate(self, video_id: str) -> Optional[Video]:
        # RSS has no per-video endpoint; hydration must come from another backend
        return None
