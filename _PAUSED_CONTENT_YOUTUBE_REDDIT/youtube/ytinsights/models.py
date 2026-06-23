from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Video:
    id: str
    title: str
    url: str
    channel_url: str = ""
    channel_id: str = ""
    duration_sec: int = 0
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    upload_date: str = ""   # YYYYMMDD
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScoredVideo:
    video: Video
    title_relevance: float = 0.0        # Stage A score (0-10)
    category_tag: str = ""              # e.g. "pricing", "hiring"
    desc_relevance: Optional[float] = None  # Stage B score; None if not hydrated
    final: float = 0.0                  # combined score used for ordering


@dataclass
class Summary:
    video_id: str
    markdown: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_cached_read: int = 0
    tokens_cached_write: int = 0
