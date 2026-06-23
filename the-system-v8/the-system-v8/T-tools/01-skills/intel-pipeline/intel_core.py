"""
intel_core.py — Shared database, scoring, and constants for the KritiKaal Intel Pipeline.

All source adapters (reddit_intel.py, rss_poller.py, etc.) import from here.
Keeps the cluster keyword map, scoring logic, and SQLite schema in one place.

Database: B-brain/04-INBOX/intel-queue/intel.db
Exports:  B-brain/04-INBOX/intel-queue/pending-review-YYYY-MM-DD_HHMM.json
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).parent.resolve()
# intel-pipeline/ → 01-skills/ → T-tools/ → workspace root
_WORKSPACE = _THIS_DIR.parent.parent.parent

QUEUE_DIR = _WORKSPACE / "B-brain" / "04-INBOX" / "intel-queue"
DB_PATH   = QUEUE_DIR / "intel.db"

# ---------------------------------------------------------------------------
# Pain-cluster keyword map  (mirrors C-core/04-youtube-pain-matrix.md)
# ---------------------------------------------------------------------------
CLUSTER_KEYWORDS: dict[str, list[str]] = {
    "eudr-compliance": [
        "EUDR", "EU deforestation", "deforestation regulation",
        "EU 2023/1115", "due diligence statement", "DDS",
        "farm-level geolocation", "LWG", "leather working group",
        "bovine traceability", "June 2026", "December 2026",
        "forest risk", "deforestation-free", "tannery traceability",
    ],
    "china-plus-one": [
        "China plus one", "china+one", "25% tariff", "tariff increase",
        "supply chain diversification", "DCTS", "duty arbitrage",
        "India vs China", "manufacturing India", "de-risking China",
        "reshoring", "nearshoring", "alt sourcing", "tariff mitigation",
        "section 301", "US tariffs China",
    ],
    "qc-disaster": [
        "defect", "defective shipment", "AQL", "quality control fail",
        "inspection fail", "bad quality", "factory blamed",
        "shipment wrong", "production error", "out of spec",
        "rejected shipment", "customs hold quality", "chargebacks quality",
        "wrong colour", "wrong dimensions", "stitching fail",
    ],
    "sourcing-agent-betrayal": [
        "sourcing agent", "agent disappeared", "commission",
        "middleman", "no accountability", "agent scam",
        "PO placed", "factory direct", "agent ghosted",
        "sourcing intermediary", "third party agent",
        "agent paid", "lost deposit",
    ],
    "golden-sample-trap": [
        "sample approval", "production doesn't match sample",
        "golden sample", "spec sheet", "sample match",
        "you approved the sample", "production inconsistent",
        "bulk different from sample", "counter sample",
        "pre-production sample", "top of production",
    ],
    "uk-import-duty": [
        "UK import duty", "DCTS", "UK customs",
        "developing countries trading scheme", "UK GSP",
        "certificate of origin", "Form A", "HS 4202",
        "leather bag duty UK", "zero duty UK India",
        "preferential tariff UK", "import tax leather UK",
    ],
    "missing-middle-moq": [
        "minimum order quantity", "MOQ", "small batch leather",
        "low MOQ", "300 units", "500 units", "small brand manufacturing",
        "can't meet MOQ", "factory minimum", "too small for factory",
        "brand vs factory", "low volume production",
        "scale-up production", "growth brand manufacturing",
    ],
    "managed-vs-alternatives": [
        "managed manufacturing", "sourcing agent vs",
        "Alibaba factory", "direct factory relationship",
        "trade show sourcing", "Alibaba leather",
        "how to source leather", "India leather factory direct",
        "manufacturer vs agent", "sourcing model comparison",
    ],
}

# Flat set for fast pre-filter before scoring
_ALL_KEYWORDS_LOWER: set[str] = {
    kw.lower() for kws in CLUSTER_KEYWORDS.values() for kw in kws
}


# ---------------------------------------------------------------------------
# Classification & scoring
# ---------------------------------------------------------------------------

def assign_clusters(text: str) -> list[str]:
    """Return cluster IDs whose keywords appear in text (case-insensitive)."""
    text_lower = text.lower()
    return [
        cluster_id
        for cluster_id, keywords in CLUSTER_KEYWORDS.items()
        if any(kw.lower() in text_lower for kw in keywords)
    ]


def has_any_keyword(text: str) -> bool:
    """Fast pre-filter: True if text contains at least one tracked keyword."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in _ALL_KEYWORDS_LOWER)


def pre_score(
    cluster_tags: list[str],
    published_at: Optional[datetime] = None,
    engagement_score: int = 0,   # karma / likes / shares
    comment_count: int = 0,
) -> float:
    """
    Compute a raw relevance score (range: 0 – ~12).

    Breakdown:
      Base         = number of distinct clusters matched (0–8)
      Recency mult = 1.5x (<30d), 1.2x (<90d), 1.0x (<365d), 0.7x (older)
      Engagement   = up to +3 pts based on karma/likes
      Discussion   = up to +1 pt based on comment depth
    """
    base = float(len(cluster_tags))

    # Recency multiplier
    recency = 1.0
    if published_at:
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - published_at).days
        if age_days < 30:
            recency = 1.5
        elif age_days < 90:
            recency = 1.2
        elif age_days > 365:
            recency = 0.7

    # Engagement bonus (Reddit karma, RSS shares, etc.)
    eng_bonus = 0.0
    if engagement_score >= 1000:
        eng_bonus = 3.0
    elif engagement_score >= 500:
        eng_bonus = 2.0
    elif engagement_score >= 100:
        eng_bonus = 1.0
    elif engagement_score >= 25:
        eng_bonus = 0.5

    # Comment/discussion depth bonus
    disc_bonus = 0.0
    if comment_count >= 50:
        disc_bonus = 1.0
    elif comment_count >= 10:
        disc_bonus = 0.5

    return round((base * recency) + eng_bonus + disc_bonus, 2)


def make_item_id(source: str, unique_key: str) -> str:
    """Stable 16-char hex ID — used for deduplication across runs."""
    return hashlib.sha256(f"{source}:{unique_key}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# SQLite database
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS intel_items (
    item_id      TEXT PRIMARY KEY,
    source       TEXT NOT NULL,          -- 'reddit' | 'rss'
    title        TEXT NOT NULL,
    body         TEXT,                   -- post body, article excerpt, or comments
    url          TEXT NOT NULL,
    published_at TEXT,                   -- ISO 8601 UTC
    author       TEXT,
    meta_json    TEXT,                   -- source-specific extra fields (JSON)
    cluster_tags TEXT,                   -- JSON array of matched cluster IDs
    raw_score    REAL DEFAULT 0.0,
    status       TEXT DEFAULT 'pending', -- 'pending' | 'llm_approved' | 'rejected' | 'approved' | 'skipped' | 'reviewed'
    user_notes   TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    reviewed_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_status    ON intel_items(status);
CREATE INDEX IF NOT EXISTS idx_source    ON intel_items(source);
CREATE INDEX IF NOT EXISTS idx_raw_score ON intel_items(raw_score DESC);
CREATE INDEX IF NOT EXISTS idx_created   ON intel_items(created_at DESC);
"""


def get_db() -> sqlite3.Connection:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()


def is_seen(item_id: str) -> bool:
    """Return True if this item_id already exists in the database."""
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM intel_items WHERE item_id = ?", (item_id,)
    ).fetchone()
    conn.close()
    return row is not None


def insert_item(item: dict) -> bool:
    """
    Insert a new intel item. Returns True if inserted, False if duplicate.

    Required keys: item_id, source, title, url
    Optional keys: body, published_at, author, meta (dict),
                   cluster_tags (list), raw_score
    """
    conn = get_db()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO intel_items
            (item_id, source, title, body, url, published_at, author,
             meta_json, cluster_tags, raw_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["item_id"],
            item["source"],
            item["title"],
            item.get("body", ""),
            item["url"],
            item.get("published_at", ""),
            item.get("author", ""),
            json.dumps(item.get("meta", {})),
            json.dumps(item.get("cluster_tags", [])),
            item.get("raw_score", 0.0),
        ),
    )
    inserted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return inserted


def db_stats() -> dict:
    """Return counts grouped by status and source."""
    conn = get_db()
    rows = conn.execute(
        "SELECT status, source, COUNT(*) AS n "
        "FROM intel_items GROUP BY status, source ORDER BY status, source"
    ).fetchall()
    conn.close()
    stats: dict = {}
    for row in rows:
        stats.setdefault(row["status"], {})[row["source"]] = row["n"]
    return stats


def update_item_status(
    item_id: str,
    status: str,
    notes: Optional[str] = None,
    score_delta: float = 0.0,
) -> None:
    """
    Update an item's status (and optionally its score and notes) in-place.

    Valid statuses used by the pipeline:
      pending       → not yet LLM-filtered
      llm_approved  → Haiku said YES; queued for HITL
      rejected      → Haiku said NO; hidden from HITL
      approved      → human approved; will be in approved-intel.json
      skipped       → human skipped; ignored in future exports
    """
    conn = get_db()
    if notes is not None:
        conn.execute(
            "UPDATE intel_items SET status = ?, user_notes = ?, reviewed_at = datetime('now'), "
            "raw_score = raw_score + ? WHERE item_id = ?",
            (status, notes, score_delta, item_id),
        )
    else:
        conn.execute(
            "UPDATE intel_items SET status = ?, reviewed_at = datetime('now'), "
            "raw_score = raw_score + ? WHERE item_id = ?",
            (status, score_delta, item_id),
        )
    conn.commit()
    conn.close()


def fetch_for_review(
    statuses: tuple[str, ...] = ("llm_approved",),
    limit: int = 50,
) -> list[dict]:
    """
    Fetch items ready for HITL review, highest-scored first.

    Pass statuses=('pending', 'llm_approved') to include items
    that skipped the LLM filter step.
    """
    placeholders = ",".join("?" for _ in statuses)
    conn = get_db()
    rows = conn.execute(
        f"SELECT * FROM intel_items WHERE status IN ({placeholders}) "
        f"ORDER BY raw_score DESC, created_at DESC LIMIT ?",
        (*statuses, limit),
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        d = dict(row)
        d["cluster_tags"] = json.loads(d.get("cluster_tags") or "[]")
        d["meta"]         = json.loads(d.get("meta_json") or "{}")
        del d["meta_json"]
        items.append(d)
    return items


def export_approved_json() -> Path:
    """
    Write ALL approved items to approved-intel.json (rolling, overwrite each call).

    Output is grouped by cluster so generate_script.py can quickly find
    relevant evidence for a specific pain cluster.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM intel_items WHERE status = 'approved' "
        "ORDER BY raw_score DESC, reviewed_at DESC"
    ).fetchall()
    conn.close()

    items = []
    by_cluster: dict[str, list] = {}
    for row in rows:
        d = dict(row)
        d["cluster_tags"] = json.loads(d.get("cluster_tags") or "[]")
        d["meta"]         = json.loads(d.get("meta_json") or "{}")
        del d["meta_json"]
        # Keep only the fields generate_script.py needs
        slim = {
            "item_id":      d["item_id"],
            "source":       d["source"],
            "title":        d["title"],
            "body_excerpt": (d.get("body") or "")[:800],
            "url":          d["url"],
            "published_at": d.get("published_at", ""),
            "cluster_tags": d["cluster_tags"],
            "raw_score":    d["raw_score"],
            "user_notes":   d.get("user_notes") or "",
        }
        items.append(slim)
        for tag in d["cluster_tags"]:
            by_cluster.setdefault(tag, []).append(slim)

    payload = {
        "exported_at":   datetime.now(timezone.utc).isoformat(),
        "total_approved": len(items),
        "by_cluster":    by_cluster,
        "items":         items,
    }

    out_path = QUEUE_DIR / "approved-intel.json"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out_path


def export_pending_json(min_score: float = 2.0) -> Path:
    """
    Export all pending items at or above min_score to a timestamped JSON file.
    Returns the path of the written file.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM intel_items WHERE status = 'pending' AND raw_score >= ? "
        "ORDER BY raw_score DESC, created_at DESC",
        (min_score,),
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        d = dict(row)
        d["cluster_tags"] = json.loads(d.get("cluster_tags") or "[]")
        d["meta"]         = json.loads(d.get("meta_json") or "{}")
        del d["meta_json"]
        items.append(d)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path  = QUEUE_DIR / f"pending-review-{timestamp}.json"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out_path
