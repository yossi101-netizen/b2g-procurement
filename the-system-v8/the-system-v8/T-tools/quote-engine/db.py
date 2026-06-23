"""
KritiKaal Quote Engine — SQLite Persistence Layer
=================================================
Single source of truth for quote history, sequence numbering, and audit trail.

Database: quotes.db  (created on first run, in the quote-engine directory)
Table:    quotes      (append-only — quotes are never deleted, only status-updated)

Usage:
    from db import QuoteDB

    db = QuoteDB()                          # Initialises DB if needed
    seq = db.next_sequence()               # Non-colliding day-scoped number
    db.save_quote(result)                  # Persist a QuoteResult permanently
    rows = db.all_quotes()                 # Quote history (newest first)
    row  = db.get_by_ref("KK-20260524-001")
"""
import dataclasses
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────
# DB PATH — lives next to db.py in the quote-engine/ directory
# ─────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.resolve() / "quotes.db"

# DDL — forward-compatible: adding columns later only requires ALTER TABLE
_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS quotes (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_ref            TEXT    NOT NULL UNIQUE,
    generated_at         TEXT    NOT NULL,   -- Human date: "24 May 2026"
    created_at           TEXT    NOT NULL,   -- ISO timestamp: "2026-05-24T09:31:00"
    client_name          TEXT    NOT NULL,
    product_ref          TEXT    NOT NULL,
    config_version       TEXT    NOT NULL,   -- MD5 hash of rates_config.yaml used
    destination          TEXT    NOT NULL,
    units                INTEGER NOT NULL,
    factory_fob_usd      REAL    NOT NULL,
    total_usd            REAL    NOT NULL,
    total_quote_currency REAL    NOT NULL,
    quote_currency       TEXT    NOT NULL,
    gp_pct               REAL    NOT NULL,
    gp_status            TEXT    NOT NULL,   -- on_target | amber | below_target
    output_format        TEXT    NOT NULL,
    status               TEXT    NOT NULL DEFAULT 'issued',  -- issued | accepted | rejected | expired
    inputs_json          TEXT    NOT NULL,   -- Full QuoteInputs as JSON (for re-calculation)
    result_json          TEXT    NOT NULL    -- Full QuoteResult as JSON (for DOCX regeneration)
)
"""

_CREATE_IDX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_quotes_ref
    ON quotes (quote_ref)
"""


# ─────────────────────────────────────────────────────────────────
# SERIALISATION HELPERS
# ─────────────────────────────────────────────────────────────────

def _to_json(obj) -> str:
    """
    Serialise a dataclass (QuoteResult or QuoteInputs) to JSON.
    Handles str-Enum fields transparently — they serialise as their string value.
    Raises TypeError for unhandled types so failures are loud, not silent.
    """
    def _default(o):
        # Enum members that inherit from str are already strings — this branch
        # exists as a safety net for any future non-str enum additions.
        if hasattr(o, "value"):
            return o.value
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serialisable")

    return json.dumps(dataclasses.asdict(obj), default=_default, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────
# MAIN CLASS
# ─────────────────────────────────────────────────────────────────

class QuoteDB:
    """
    Lightweight wrapper around the quotes SQLite database.
    Stateless: creates a new connection on each operation (safe for Streamlit).
    WAL mode enabled for concurrent read safety.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ── Setup ────────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create DB and table if they don't exist. Safe to call multiple times."""
        with self._connect() as conn:
            conn.execute(_CREATE_SQL)
            conn.execute(_CREATE_IDX)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row          # Named column access
        conn.execute("PRAGMA journal_mode=WAL")  # Concurrent read safety
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Sequence Numbering ───────────────────────────────────────

    def next_sequence(self) -> int:
        """
        Return the next available sequence number for today's quotes.

        Design: counts existing quotes with today's date prefix and adds 1.
        This is idempotent — correct even after DB restore, app restart,
        or multiple Streamlit sessions running simultaneously.

        Example: If KK-20260524-001 and KK-20260524-002 exist, returns 3.
        On a new day, always returns 1 regardless of yesterday's count.
        """
        today = date.today().strftime("%Y%m%d")
        prefix = f"KK-{today}-%"
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM quotes WHERE quote_ref LIKE ?",
                (prefix,),
            ).fetchone()
        return (row[0] or 0) + 1

    # ── Write ────────────────────────────────────────────────────

    def save_quote(self, result) -> None:
        """
        Persist a QuoteResult permanently.
        Raises sqlite3.IntegrityError if quote_ref already exists (UNIQUE constraint).
        Caller should check next_sequence() first to avoid duplicates.
        """
        inputs_json  = _to_json(result.inputs)
        result_json  = _to_json(result)
        created_at   = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO quotes (
                    quote_ref, generated_at, created_at,
                    client_name, product_ref, config_version,
                    destination, units, factory_fob_usd,
                    total_usd, total_quote_currency, quote_currency,
                    gp_pct, gp_status, output_format,
                    status, inputs_json, result_json
                ) VALUES (
                    :quote_ref, :generated_at, :created_at,
                    :client_name, :product_ref, :config_version,
                    :destination, :units, :factory_fob_usd,
                    :total_usd, :total_quote_currency, :quote_currency,
                    :gp_pct, :gp_status, :output_format,
                    :status, :inputs_json, :result_json
                )
                """,
                {
                    "quote_ref":            result.quote_ref,
                    "generated_at":         result.generated_at,
                    "created_at":           created_at,
                    "client_name":          result.inputs.client_name,
                    "product_ref":          result.inputs.product_ref,
                    "config_version":       result.config_version,
                    "destination":          result.inputs.destination.value,
                    "units":                result.inputs.units,
                    "factory_fob_usd":      result.inputs.factory_fob_usd,
                    "total_usd":            result.total_usd,
                    "total_quote_currency": result.total_quote_currency,
                    "quote_currency":       result.inputs.quote_currency.value,
                    "gp_pct":               result.gp_pct,
                    "gp_status":            result.gp_status,
                    "output_format":        result.inputs.output_format.value,
                    "status":               "issued",
                    "inputs_json":          inputs_json,
                    "result_json":          result_json,
                },
            )

    def update_status(self, quote_ref: str, new_status: str) -> bool:
        """
        Update quote lifecycle status.
        Valid statuses: 'issued' | 'accepted' | 'rejected' | 'expired'
        Returns True if a row was updated, False if ref not found.
        """
        valid = {"issued", "accepted", "rejected", "expired"}
        if new_status not in valid:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of: {valid}")

        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE quotes SET status = ? WHERE quote_ref = ?",
                (new_status, quote_ref),
            )
        return cursor.rowcount > 0

    # ── Read ─────────────────────────────────────────────────────

    def all_quotes(self, limit: int = 500) -> list[sqlite3.Row]:
        """
        Return all quotes, newest first.
        Each row supports both index access (row[0]) and name access (row["client_name"]).
        """
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT id, quote_ref, created_at, client_name, product_ref,
                       destination, units, factory_fob_usd,
                       total_usd, total_quote_currency, quote_currency,
                       gp_pct, gp_status, status, output_format, config_version
                FROM   quotes
                ORDER  BY id DESC
                LIMIT  ?
                """,
                (limit,),
            ).fetchall()

    def get_by_ref(self, quote_ref: str) -> Optional[sqlite3.Row]:
        """Return a single quote by reference, or None if not found."""
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM quotes WHERE quote_ref = ?",
                (quote_ref,),
            ).fetchone()

    def stats(self) -> dict:
        """
        Aggregate stats for the dashboard.
        Returns: total_quotes, total_usd_quoted, avg_gp_pct, accepted_count
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*)                           AS total_quotes,
                    COALESCE(SUM(total_usd), 0)        AS total_usd_quoted,
                    COALESCE(AVG(gp_pct), 0)           AS avg_gp_pct,
                    SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) AS accepted_count,
                    SUM(CASE WHEN gp_status='on_target' THEN 1 ELSE 0 END) AS on_target_count,
                    SUM(CASE WHEN gp_status='amber' THEN 1 ELSE 0 END) AS amber_count,
                    SUM(CASE WHEN gp_status='below_target' THEN 1 ELSE 0 END) AS red_count
                FROM quotes
                """
            ).fetchone()
        return dict(row) if row else {}
