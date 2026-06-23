from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from ..models import Video


class DiscoveryError(Exception):
    """Raised when a discovery backend fails in a non-retryable way."""


@runtime_checkable
class Discoverer(Protocol):
    name: str

    def list_videos(self, channel_url: str, limit: int, **kwargs) -> list[Video]:
        """Return metadata for up to `limit` videos from `channel_url`."""
        ...

    def hydrate(self, video_id: str) -> Optional[Video]:
        """Fetch full per-video metadata. Return None on any failure."""
        ...
