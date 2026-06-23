"""Optional YouTube Data API v3 discovery backend.

Requires:
  - pip install google-api-python-client
  - YOUTUBE_API_KEY set in environment / .env

Advantages over yt-dlp: official API, returns ISO-8601 duration (exact), full
metadata in one pass, no scraping. Quota: ~100 units per channel scan
(list channels: 1 unit + list playlist items: 1/page + list videos: 1/50 items).
Daily free quota is 10,000 units — sufficient for hundreds of channels.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from .base import DiscoveryError
from ..models import Video

log = logging.getLogger(__name__)


def _iso8601_to_sec(iso: str) -> int:
    """PT1H15M30S → 4530."""
    h = int((re.search(r"(\d+)H", iso) or ("", 0))[1] or 0)
    m = int((re.search(r"(\d+)M", iso) or ("", 0))[1] or 0)
    s = int((re.search(r"(\d+)S", iso) or ("", 0))[1] or 0)
    return h * 3600 + m * 60 + s


class DataApiDiscoverer:
    name = "dataapi"

    def __init__(self, api_key: str) -> None:
        try:
            from googleapiclient.discovery import build  # type: ignore
            self._yt = build("youtube", "v3", developerKey=api_key)
        except ImportError as exc:
            raise DiscoveryError(
                "google-api-python-client is not installed. "
                "Run: pip install google-api-python-client"
            ) from exc

    def _resolve_channel_id(self, channel_url: str) -> str:
        m = re.search(r"/channel/(UC[A-Za-z0-9_-]{22})", channel_url)
        if m:
            return m.group(1)

        m = re.search(r"/@([^/?]+)", channel_url)
        if m:
            resp = self._yt.channels().list(
                forHandle=m.group(1), part="id"
            ).execute()
            items = resp.get("items") or []
            if items:
                return items[0]["id"]

        m = re.search(r"/(?:c|user)/([^/?]+)", channel_url)
        if m:
            resp = self._yt.channels().list(
                forUsername=m.group(1), part="id"
            ).execute()
            items = resp.get("items") or []
            if items:
                return items[0]["id"]

        raise DiscoveryError(f"Cannot resolve channel ID from URL: {channel_url}")

    def list_videos(
        self,
        channel_url: str,
        limit: int,
        channel_id: Optional[str] = None,
        **kwargs,
    ) -> list[Video]:
        try:
            cid = channel_id or self._resolve_channel_id(channel_url)

            # Get the uploads playlist ID
            ch = self._yt.channels().list(id=cid, part="contentDetails").execute()
            if not ch.get("items"):
                raise DiscoveryError(f"Channel not found: {cid}")
            uploads_id = (
                ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            )

            # Page through the uploads playlist
            video_ids: list[str] = []
            page_token: Optional[str] = None
            while len(video_ids) < limit:
                batch = min(50, limit - len(video_ids))
                resp = self._yt.playlistItems().list(
                    playlistId=uploads_id,
                    part="contentDetails",
                    maxResults=batch,
                    pageToken=page_token,
                ).execute()
                for item in resp.get("items") or []:
                    video_ids.append(item["contentDetails"]["videoId"])
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

            # Fetch full metadata in chunks of 50
            videos: list[Video] = []
            for i in range(0, len(video_ids), 50):
                chunk = video_ids[i : i + 50]
                resp = self._yt.videos().list(
                    id=",".join(chunk),
                    part="snippet,contentDetails,statistics",
                ).execute()
                for item in resp.get("items") or []:
                    snip = item.get("snippet") or {}
                    cd = item.get("contentDetails") or {}
                    stats = item.get("statistics") or {}
                    pub = snip.get("publishedAt") or ""
                    upload_date = pub[:10].replace("-", "") if pub else ""
                    vid_id = item["id"]
                    videos.append(
                        Video(
                            id=vid_id,
                            title=snip.get("title") or "",
                            url=f"https://www.youtube.com/watch?v={vid_id}",
                            channel_url=channel_url,
                            channel_id=cid,
                            duration_sec=_iso8601_to_sec(
                                cd.get("duration") or "PT0S"
                            ),
                            view_count=int(stats.get("viewCount") or 0),
                            like_count=int(stats.get("likeCount") or 0),
                            comment_count=int(stats.get("commentCount") or 0),
                            upload_date=upload_date,
                            description=(snip.get("description") or "")[:2000],
                        )
                    )
            log.info("Data API: discovered %d videos", len(videos))
            return videos

        except DiscoveryError:
            raise
        except Exception as exc:
            raise DiscoveryError(f"YouTube Data API error: {exc}") from exc

    def hydrate(self, video_id: str) -> Optional[Video]:
        try:
            resp = self._yt.videos().list(
                id=video_id, part="snippet,contentDetails,statistics"
            ).execute()
            for item in resp.get("items") or []:
                snip = item.get("snippet") or {}
                cd = item.get("contentDetails") or {}
                stats = item.get("statistics") or {}
                pub = snip.get("publishedAt") or ""
                return Video(
                    id=video_id,
                    title=snip.get("title") or "",
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    channel_url="",
                    channel_id=snip.get("channelId") or "",
                    duration_sec=_iso8601_to_sec(cd.get("duration") or "PT0S"),
                    view_count=int(stats.get("viewCount") or 0),
                    like_count=int(stats.get("likeCount") or 0),
                    comment_count=int(stats.get("commentCount") or 0),
                    upload_date=pub[:10].replace("-", "") if pub else "",
                    description=(snip.get("description") or "")[:2000],
                )
        except Exception as exc:
            log.warning("Data API hydration failed for %s: %s", video_id, exc)
        return None
