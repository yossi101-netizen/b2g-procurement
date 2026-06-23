from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from .models import Video


SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    url         TEXT PRIMARY KEY,
    channel_id  TEXT DEFAULT '',
    last_backend TEXT DEFAULT '',
    discovered_count INTEGER DEFAULT 0,
    last_run    TEXT                 -- ISO-8601 UTC
);

CREATE TABLE IF NOT EXISTS videos (
    id              TEXT PRIMARY KEY,
    channel_url     TEXT NOT NULL,
    channel_id      TEXT DEFAULT '',
    title           TEXT DEFAULT '',
    url             TEXT DEFAULT '',
    duration_sec    INTEGER DEFAULT 0,
    view_count      INTEGER DEFAULT 0,
    like_count      INTEGER DEFAULT 0,
    comment_count   INTEGER DEFAULT 0,
    upload_date     TEXT DEFAULT '',
    description     TEXT DEFAULT '',

    -- Scoring
    title_relevance REAL,
    category_tag    TEXT,
    desc_relevance  REAL,       -- NULL until Stage B hydration
    final_score     REAL,
    queue_pos       INTEGER,    -- diversity-sorted rank; lower = processed first

    -- Lifecycle
    status      TEXT DEFAULT 'unscored',
    transcript  TEXT,
    summary     TEXT,
    user_notes  TEXT,
    error       TEXT,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_videos_queue
    ON videos(channel_url, status, queue_pos ASC, final_score DESC);
"""

# Statuses that the HITL loop should surface
ACTIONABLE_STATUSES = ("pending", "summarized")


def _row_to_video(row: sqlite3.Row) -> Video:
    return Video(
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


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # ------------------------------------------------------------------
    # Channel-level operations
    # ------------------------------------------------------------------

    def get_channel_id(self, channel_url: str) -> Optional[str]:
        cur = self._conn.execute(
            "SELECT channel_id FROM channels WHERE url=?", (channel_url,)
        )
        row = cur.fetchone()
        return (row["channel_id"] or None) if row else None

    def get_last_run(self, channel_url: str) -> Optional[datetime]:
        cur = self._conn.execute(
            "SELECT last_run FROM channels WHERE url=?", (channel_url,)
        )
        row = cur.fetchone()
        if not row or not row["last_run"]:
            return None
        try:
            dt = datetime.fromisoformat(row["last_run"])
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    def set_channel_meta(
        self, url: str, channel_id: str, backend: str, count: int
    ) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO channels(url, channel_id, last_backend, "
                "  discovered_count, last_run) "
                "VALUES (?, ?, ?, ?, datetime('now')) "
                "ON CONFLICT(url) DO UPDATE SET "
                "  channel_id=COALESCE(NULLIF(excluded.channel_id,''), channels.channel_id), "
                "  last_backend=excluded.last_backend, "
                "  discovered_count=excluded.discovered_count, "
                "  last_run=excluded.last_run",
                (url, channel_id, backend, count),
            )

    # ------------------------------------------------------------------
    # Video CRUD
    # ------------------------------------------------------------------

    def upsert_video(self, v: Video) -> None:
        d = v.to_dict()
        with self.tx() as c:
            c.execute(
                "INSERT INTO videos("
                "  id, channel_url, channel_id, title, url, duration_sec, "
                "  view_count, like_count, comment_count, upload_date, description"
                ") VALUES ("
                "  :id, :channel_url, :channel_id, :title, :url, :duration_sec, "
                "  :view_count, :like_count, :comment_count, :upload_date, :description"
                ") ON CONFLICT(id) DO UPDATE SET "
                "  title=excluded.title, "
                "  view_count=excluded.view_count, "
                "  duration_sec=CASE WHEN excluded.duration_sec > 0 "
                "    THEN excluded.duration_sec ELSE videos.duration_sec END, "
                "  upload_date=COALESCE(NULLIF(excluded.upload_date,''), videos.upload_date), "
                "  description=CASE WHEN LENGTH(excluded.description) > LENGTH(COALESCE(videos.description,'')) "
                "    THEN excluded.description ELSE videos.description END",
                d,
            )

    def update_description(self, video_id: str, description: str) -> None:
        """Persist a newly hydrated description (only if we got more text than before)."""
        with self.tx() as c:
            c.execute(
                "UPDATE videos SET description=?, last_updated=datetime('now') "
                "WHERE id=? AND LENGTH(?) > LENGTH(COALESCE(description, ''))",
                (description, video_id, description),
            )

    def update_duration(self, video_id: str, duration_sec: int) -> None:
        if duration_sec > 0:
            with self.tx() as c:
                c.execute(
                    "UPDATE videos SET duration_sec=? WHERE id=? AND duration_sec=0",
                    (duration_sec, video_id),
                )

    def get_all_videos(self, channel_url: str) -> list[Video]:
        cur = self._conn.execute(
            "SELECT * FROM videos WHERE channel_url=?", (channel_url,)
        )
        return [_row_to_video(r) for r in cur]

    def get_unscored_videos(self, channel_url: str) -> list[Video]:
        cur = self._conn.execute(
            "SELECT * FROM videos WHERE channel_url=? AND status='unscored'",
            (channel_url,),
        )
        return [_row_to_video(r) for r in cur]

    def has_unscored(self, channel_url: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM videos WHERE channel_url=? AND status='unscored' LIMIT 1",
            (channel_url,),
        )
        return cur.fetchone() is not None

    def get_max_queue_pos(self, channel_url: str) -> int:
        cur = self._conn.execute(
            "SELECT MAX(queue_pos) FROM videos WHERE channel_url=?", (channel_url,)
        )
        row = cur.fetchone()
        return int(row[0] or 0)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def set_score(
        self,
        video_id: str,
        title_relevance: float,
        category_tag: str,
        desc_relevance: Optional[float],
        final_score: float,
        queue_pos: int,
    ) -> None:
        with self.tx() as c:
            c.execute(
                "UPDATE videos SET "
                "  title_relevance=?, category_tag=?, desc_relevance=?, "
                "  final_score=?, queue_pos=?, last_updated=datetime('now') "
                "WHERE id=?",
                (title_relevance, category_tag, desc_relevance,
                 final_score, queue_pos, video_id),
            )

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def set_status(self, video_id: str, status: str, **fields) -> None:
        """Update status and any extra columns in one shot."""
        allowed_cols = {
            "transcript", "summary", "user_notes", "error",
            "duration_sec", "description",
        }
        parts = ["status=?", "last_updated=datetime('now')"]
        vals: list = [status]
        for k, v in fields.items():
            if k not in allowed_cols:
                raise ValueError(f"Unknown column: {k}")
            parts.append(f"{k}=?")
            vals.append(v)
        vals.append(video_id)
        with self.tx() as c:
            c.execute(
                f"UPDATE videos SET {', '.join(parts)} WHERE id=?", vals
            )

    # ------------------------------------------------------------------
    # HITL queue
    # ------------------------------------------------------------------

    def next_actionable(self, channel_url: str) -> Optional[sqlite3.Row]:
        """Return the highest-priority video that still needs a HITL decision."""
        placeholders = ",".join("?" * len(ACTIONABLE_STATUSES))
        cur = self._conn.execute(
            f"SELECT * FROM videos "
            f"WHERE channel_url=? AND status IN ({placeholders}) "
            f"ORDER BY "
            f"  CASE WHEN queue_pos IS NULL THEN 1 ELSE 0 END ASC, "
            f"  queue_pos ASC, "
            f"  final_score DESC "
            f"LIMIT 1",
            (channel_url, *ACTIONABLE_STATUSES),
        )
        return cur.fetchone()

    def get_video(self, video_id: str) -> Optional[sqlite3.Row]:
        cur = self._conn.execute("SELECT * FROM videos WHERE id=?", (video_id,))
        return cur.fetchone()

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def stats(self, channel_url: str) -> dict[str, int]:
        cur = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM videos WHERE channel_url=? "
            "GROUP BY status",
            (channel_url,),
        )
        base = {
            "unscored": 0, "pending": 0, "summarized": 0,
            "approved": 0, "skipped": 0,
            "no_transcript": 0, "error": 0,
            "filtered_short": 0, "filtered_long": 0,
        }
        for row in cur:
            base[row["status"]] = row["n"]
        return base

    def export_approved(self, channel_url: str, out_path: Path) -> int:
        cur = self._conn.execute(
            "SELECT id, title, url, final_score, summary, user_notes "
            "FROM videos WHERE channel_url=? AND status='approved' "
            "ORDER BY queue_pos ASC",
            (channel_url,),
        )
        rows = [dict(r) for r in cur]
        out_path.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return len(rows)
