"""
KritiKaal Leads Hunter — Database Initialization & Lead Upsert Logic
File: T-tools/db_init.py
Governed by: B-brain/01-tech-stack.md (Iron Principle 5)
Classification: C-core/02-target-audience.md

Responsibilities of this module (SRP boundary):
  - Open / close SQLite connections (isolation_level=None for explicit tx control)
  - Initialize schema from db_schema.sql
  - Sanitize and normalize all lead field inputs before any DB operation
  - Resolve whether an incoming lead matches an existing record
    (Three-Vector deduplication: domain → whatsapp → company_id)
  - Insert new leads / merge data into existing leads (forward-only status)
  - Consolidate two distinct lead records proven to be the same entity
  - Insert source provenance records
  - Flag stale leads exceeding a TTL threshold (last_verified_at age)

TRANSACTION CONTRACT:
  Write sub-functions (insert_lead, merge_lead, insert_source,
  _consolidate_no_tx) do NOT commit. The caller owns the transaction.
  Public orchestrators (upsert_lead, consolidate_entities, flag_stale_leads)
  issue BEGIN IMMEDIATE / COMMIT / ROLLBACK themselves.

TTL / DECAY PREVENTION CONTRACT:
  last_verified_at is refreshed to CURRENT_TIMESTAMP whenever an existing
  lead is successfully matched by incoming fresh data — in the ON CONFLICT
  DO UPDATE path of upsert_lead, in merge_lead, and in _consolidate_no_tx.
  flag_stale_leads() reads but never writes last_verified_at; it only sets
  is_stale = 1 and status = REQUIRES_REVERIFICATION.

This module does NOT:
  - Fetch or scrape any data
  - Run NLP classification
  - Produce Output lists
  - Execute any network I/O
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_PATH = Path(__file__).parent / "db_schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent / "leads.db"

# Status values ordered by lifecycle progression.
# A lead's status may only move forward through this list during merge
# operations. REQUIRES_REVERIFICATION sits at position 1 so that stale
# leads re-enter the enrichment pipeline and can advance back to qualified
# states through normal processing.
# NOTE: flag_stale_leads() bypasses this order intentionally — it is an
# administrative operation that writes status directly.
STATUS_ORDER = [
    "RAW",
    "REQUIRES_REVERIFICATION",
    "ENRICHED",
    "PENDING_LEGAL",
    "UNCLASSIFIED",
    "QUALIFIED_B_PENDING_VERIFY",
    "QUALIFIED_A",
    "DISQUALIFIED_C",
]

# Integer rank for each status — used by _advance_status and the SQL CASE expr.
_STATUS_RANK: dict[str, int] = {s: i for i, s in enumerate(STATUS_ORDER)}


# ---------------------------------------------------------------------------
# SQL helpers — built once at import time
# ---------------------------------------------------------------------------

def _status_rank_sql(col: str) -> str:
    """Return a SQL CASE expression mapping a status column to its integer rank."""
    cases = " ".join(f"WHEN '{s}' THEN {r}" for s, r in _STATUS_RANK.items())
    return f"CASE {col} {cases} ELSE 0 END"


# Atomic upsert: INSERT on success, merge-in-place on domain conflict.
# Uses RETURNING to get the id regardless of which path was taken.
# On conflict (existing lead matched by domain):
#   - Scalar fields filled via COALESCE (existing value wins over NULL).
#   - Status advanced using embedded rank comparison.
#   - last_verified_at reset to CURRENT_TIMESTAMP — fresh data arrived.
#   - is_stale cleared to 0 — lead is no longer considered decayed.
_UPSERT_SQL = """
    INSERT INTO leads (
        entity_name, domain, whatsapp, company_id,
        physical_address, status, legal_flag
    ) VALUES (
        :entity_name, :domain, :whatsapp, :company_id,
        :physical_address, :status, :legal_flag
    )
    ON CONFLICT(domain) DO UPDATE SET
        whatsapp         = COALESCE(leads.whatsapp,         excluded.whatsapp),
        company_id       = COALESCE(leads.company_id,       excluded.company_id),
        physical_address = COALESCE(leads.physical_address, excluded.physical_address),
        legal_flag       = COALESCE(leads.legal_flag,       excluded.legal_flag),
        status           = CASE
                               WHEN {current_rank} >= {excluded_rank}
                               THEN leads.status
                               ELSE excluded.status
                           END,
        last_verified_at = CURRENT_TIMESTAMP,
        is_stale         = 0,
        last_updated_at  = CURRENT_TIMESTAMP
    RETURNING id
""".format(
    current_rank=_status_rank_sql("leads.status"),
    excluded_rank=_status_rank_sql("excluded.status"),
)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Open and return a SQLite connection.

    isolation_level=None disables Python's implicit transaction management,
    giving callers full control over BEGIN / COMMIT / ROLLBACK.
    """
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    """Commit any open transaction and close the connection."""
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Schema initialization
# ---------------------------------------------------------------------------

def initialize_schema(conn: sqlite3.Connection) -> None:
    """
    Execute db_schema.sql, then apply any pending one-time migrations.

    Migration order is intentional:
      1. schema script first  — guarantees all tables exist (including the new
         domain_blacklist table added in Phase 2 M-002).
      2. migrations second    — operate on tables that are now guaranteed present.
      3. bootstrap blacklist  — auto-populate from existing high-confidence
         DISQUALIFIED_C leads so the blacklist is immediately useful on upgrade.
    """
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    _migrate_remove_vector_check(conn)
    _migrate_add_is_priority(conn)       # Sprint 10 — priority flag
    _migrate_add_exported_at(conn)       # Sprint 11C — CRM export timestamp
    bootstrap_blacklist(conn)  # idempotent — INSERT OR IGNORE


def _migrate_add_is_priority(conn: sqlite3.Connection) -> None:
    """M-002: add is_priority column if absent (Sprint 10 migration)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(leads)").fetchall()}
    if "is_priority" not in cols:
        conn.execute(
            "ALTER TABLE leads ADD COLUMN is_priority INTEGER NOT NULL DEFAULT 0"
            " CHECK (is_priority IN (0, 1))"
        )
        conn.commit()


def _migrate_add_exported_at(conn: sqlite3.Connection) -> None:
    """M-003: add exported_at column if absent (Sprint 11C CRM sync migration)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(leads)").fetchall()}
    if "exported_at" not in cols:
        conn.execute("ALTER TABLE leads ADD COLUMN exported_at TIMESTAMP DEFAULT NULL")
        conn.commit()


def _migrate_remove_vector_check(conn: sqlite3.Connection) -> bool:
    """
    Migration M-001 — remove the hardcoded vector CHECK constraint from
    lead_sources so that any new agent vector can be inserted without
    a schema change.

    Background: SQLite cannot ALTER TABLE ... DROP CONSTRAINT.  The only
    option is the standard table-rebuild pattern:
        CREATE new table (no constraint)
        INSERT … SELECT  (copy all rows)
        DROP old table
        RENAME new → old

    Safety guards:
      - Reads sqlite_master to detect whether the constraint is present.
        If the table has already been migrated (or was created fresh from
        the updated schema) this function is a fast no-op.
      - PRAGMA foreign_keys = OFF during rebuild so the DROP TABLE does
        not trigger cascade actions on referencing tables.
      - PRAGMA foreign_keys = ON restored before returning.
      - Index idx_sources_lead_id recreated after rename.

    Returns True if the migration ran, False if it was already applied.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='lead_sources'"
    ).fetchone()

    if not row:
        return False  # table not yet created — fresh schema will be correct

    create_sql: str = row[0] or ""
    if "CHECK (vector IN" not in create_sql:
        return False  # already migrated or never had the constraint

    # executescript() issues an implicit COMMIT first, then runs each
    # statement. That is acceptable here: initialize_schema() has no
    # open transaction of its own when it calls this function.
    conn.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE lead_sources_m001 (
            id            INTEGER   PRIMARY KEY AUTOINCREMENT,
            lead_id       INTEGER   NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            vector        TEXT      NOT NULL,
            source_url    TEXT      NOT NULL,
            raw_snippet   TEXT,
            discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        INSERT INTO lead_sources_m001
            SELECT id, lead_id, vector, source_url, raw_snippet, discovered_at
            FROM lead_sources;

        DROP TABLE lead_sources;

        ALTER TABLE lead_sources_m001 RENAME TO lead_sources;

        CREATE INDEX IF NOT EXISTS idx_sources_lead_id
            ON lead_sources(lead_id);

        PRAGMA foreign_keys = ON;
    """)

    return True


# ---------------------------------------------------------------------------
# Sanitization — must run before any find_* or insert_* call
# ---------------------------------------------------------------------------

def normalize_domain(raw: str) -> str:
    """
    Normalize a raw URL or domain string to a canonical apex domain.

    Transformations applied (in order):
      1. Lowercase and strip surrounding whitespace.
      2. Strip protocol prefix (http:// or https://).
      3. Strip known subdomain prefixes — B-brain/01-tech-stack.md §5 Canonicalization:
            www.    shop.   store.   m.   he.
         These prefixes never distinguish a business entity — they only reflect
         the URL routing layer (mobile, locale, storefront). Stripping them
         ensures `shop.braker.co.il` and `braker.co.il` map to the same record.
      4. Discard any path, query string, or fragment (keep host only).

    Limitations (by design):
      - Rebranded domains (old.co.il → new.co.il) and international variants
        (company.co.il vs company.com) cannot be resolved automatically.
        These remain as separate DB records until manual review.
      - HTTP redirect following is handled at the V3 enrichment layer in
        scrapers.py, upstream of this function.
    """
    _STRIP_PREFIXES = ("www.", "shop.", "store.", "m.", "he.")

    domain = raw.strip().lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0]    # discard path
    domain = domain.split('?')[0]    # discard query string
    domain = domain.split('#')[0]    # discard fragment

    for prefix in _STRIP_PREFIXES:
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
            break    # only strip one prefix level

    return domain


def normalize_whatsapp(raw: str) -> Optional[str]:
    """
    Normalize an Israeli phone number to the strict format 972XXXXXXXXX (12 digits).

    Accepted input formats:
      - 054-123-4567   (local with dashes)
      - 054 123 4567   (local with spaces)
      - 0541234567     (local, no separator)
      - +972-54-123-4567
      - +972 54 123 4567
      - 972541234567   (already normalized)

    Returns None if the result is not a valid 12-digit Israeli mobile number.
    """
    digits = re.sub(r'\D', '', raw)  # strip everything except digits

    if digits.startswith('972'):
        normalized = digits
    elif digits.startswith('0'):
        normalized = '972' + digits[1:]   # replace leading trunk prefix
    else:
        normalized = '972' + digits       # bare 9-digit number, prepend country code

    # Validate: exactly 12 digits, Israeli country code, mobile prefix 5x
    if len(normalized) == 12 and normalized.startswith('9725'):
        return normalized
    return None


def sanitize_lead_data(lead_data: dict) -> dict:
    """
    Return a new dict with domain and whatsapp normalized.
    All other fields are passed through unchanged.
    Raises ValueError if domain is missing or normalizes to an empty string.
    """
    if not lead_data.get('domain'):
        raise ValueError("lead_data must include a non-empty 'domain' field.")

    sanitized = dict(lead_data)
    sanitized['domain'] = normalize_domain(lead_data['domain'])

    if not sanitized['domain']:
        raise ValueError(f"Domain normalized to empty string from input: {lead_data['domain']!r}")

    raw_whatsapp = lead_data.get('whatsapp')
    if raw_whatsapp:
        sanitized['whatsapp'] = normalize_whatsapp(raw_whatsapp)
    else:
        sanitized['whatsapp'] = None

    return sanitized


# ---------------------------------------------------------------------------
# Single-vector lookup functions
# (No transaction management — read-only, callable anywhere)
# ---------------------------------------------------------------------------

def find_lead_by_domain(conn: sqlite3.Connection, domain: str) -> Optional[sqlite3.Row]:
    """Return the leads row whose domain matches exactly, or None."""
    return conn.execute(
        "SELECT * FROM leads WHERE domain = ?", (domain,)
    ).fetchone()


def find_lead_by_whatsapp(conn: sqlite3.Connection, whatsapp: str) -> Optional[sqlite3.Row]:
    """Return the leads row whose whatsapp matches exactly, or None."""
    return conn.execute(
        "SELECT * FROM leads WHERE whatsapp = ?", (whatsapp,)
    ).fetchone()


def find_lead_by_company_id(conn: sqlite3.Connection, company_id: str) -> Optional[sqlite3.Row]:
    """Return the leads row whose company_id matches exactly, or None."""
    return conn.execute(
        "SELECT * FROM leads WHERE company_id = ?", (company_id,)
    ).fetchone()


# ---------------------------------------------------------------------------
# Three-Vector deduplication resolver
# ---------------------------------------------------------------------------

def resolve_existing_lead(
    conn: sqlite3.Connection,
    domain: str,
    whatsapp: Optional[str],
    company_id: Optional[str],
) -> Optional[sqlite3.Row]:
    """
    Check all three deduplication vectors in priority order.

    Priority:
      1. domain      — most reliable canonical identifier
      2. whatsapp    — catches one business reachable via multiple domains
      3. company_id  — catches same legal entity under different brand names

    Returns the first matching leads row, or None.
    """
    match = find_lead_by_domain(conn, domain)
    if match:
        return match

    if whatsapp:
        match = find_lead_by_whatsapp(conn, whatsapp)
        if match:
            return match

    if company_id:
        match = find_lead_by_company_id(conn, company_id)
        if match:
            return match

    return None


# ---------------------------------------------------------------------------
# Status progression guard
# ---------------------------------------------------------------------------

def _advance_status(current: str, incoming: str) -> str:
    """
    Return whichever status is further along STATUS_ORDER.
    Falls back to current if either value is not a recognised status.
    """
    try:
        return STATUS_ORDER[max(_STATUS_RANK[current], _STATUS_RANK[incoming])]
    except KeyError:
        return current


# ---------------------------------------------------------------------------
# Write operations — NO transaction management (caller owns BEGIN/COMMIT)
# ---------------------------------------------------------------------------

def insert_lead(conn: sqlite3.Connection, lead_data: dict) -> int:
    """
    Insert a new row into leads.

    Required keys in lead_data: entity_name, domain.
    Optional keys: whatsapp, company_id, physical_address, status, legal_flag.

    last_verified_at and is_stale default to CURRENT_TIMESTAMP and 0
    respectively via schema defaults — no explicit values needed here.

    Returns the new lead id.
    Does NOT commit — caller manages the transaction.
    """
    cursor = conn.execute(
        """
        INSERT INTO leads
            (entity_name, domain, whatsapp, company_id,
             physical_address, status, legal_flag)
        VALUES
            (:entity_name, :domain, :whatsapp, :company_id,
             :physical_address, :status, :legal_flag)
        """,
        {
            "entity_name":      lead_data["entity_name"],
            "domain":           lead_data["domain"],
            "whatsapp":         lead_data.get("whatsapp"),
            "company_id":       lead_data.get("company_id"),
            "physical_address": lead_data.get("physical_address"),
            "status":           lead_data.get("status", "RAW"),
            "legal_flag":       lead_data.get("legal_flag"),
        }
    )
    return cursor.lastrowid


def merge_lead(conn: sqlite3.Connection, existing_id: int, incoming: dict) -> int:
    """
    Enrich an existing lead with non-null values from incoming data.

    Merge rules:
      - whatsapp, company_id, physical_address, legal_flag:
          fill if currently NULL; never overwrite a verified value.
      - status: only advance forward in STATUS_ORDER; never regress.
      - entity_name, domain: immutable (first-seen wins).
      - last_verified_at: reset to CURRENT_TIMESTAMP (fresh data confirmed).
      - is_stale: cleared to 0 (lead is no longer considered decayed).
      - last_updated_at: always refreshed.

    Returns the existing lead id (unchanged).
    Does NOT commit — caller manages the transaction.
    """
    existing = conn.execute(
        "SELECT * FROM leads WHERE id = ?", (existing_id,)
    ).fetchone()

    conn.execute(
        """
        UPDATE leads SET
            whatsapp         = COALESCE(whatsapp,         ?),
            company_id       = COALESCE(company_id,       ?),
            physical_address = COALESCE(physical_address, ?),
            legal_flag       = COALESCE(legal_flag,       ?),
            status           = ?,
            last_verified_at = CURRENT_TIMESTAMP,
            is_stale         = 0,
            last_updated_at  = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            incoming.get("whatsapp"),
            incoming.get("company_id"),
            incoming.get("physical_address"),
            incoming.get("legal_flag"),
            _advance_status(existing["status"], incoming.get("status", "RAW")),
            existing_id,
        )
    )
    return existing_id


def insert_source(
    conn: sqlite3.Connection,
    lead_id: int,
    vector: str,
    source_url: str,
    raw_snippet: Optional[str] = None,
) -> None:
    """
    Append one discovery event to lead_sources.
    vector must be one of: V1_SERPER | V2_SERPAPI | V3_DIRECT.
    Does NOT commit — caller manages the transaction.
    """
    conn.execute(
        """
        INSERT INTO lead_sources (lead_id, vector, source_url, raw_snippet)
        VALUES (?, ?, ?, ?)
        """,
        (lead_id, vector, source_url, raw_snippet)
    )


# ---------------------------------------------------------------------------
# Consolidation — private implementation (no transaction management)
# ---------------------------------------------------------------------------

def _consolidate_no_tx(
    conn: sqlite3.Connection,
    survivor_id: int,
    duplicate_id: int,
) -> None:
    """
    Merge duplicate into survivor within an already-open transaction.

    Steps:
      1. Merge all non-null fields from duplicate into survivor (null-safe).
         Resets last_verified_at and clears is_stale — consolidation counts
         as fresh verification of the survivor entity.
      2. Migrate all lead_sources rows from duplicate to survivor.
      3. Migrate all lead_classifications rows from duplicate to survivor.
      4. Delete the duplicate lead row (CASCADE handles any remaining FKs).

    Must be called inside an active BEGIN IMMEDIATE transaction.
    Does NOT commit or rollback.
    """
    survivor = conn.execute(
        "SELECT * FROM leads WHERE id = ?", (survivor_id,)
    ).fetchone()
    duplicate = conn.execute(
        "SELECT * FROM leads WHERE id = ?", (duplicate_id,)
    ).fetchone()

    if survivor is None:
        raise ValueError(f"Survivor lead id={survivor_id} not found.")
    if duplicate is None:
        raise ValueError(f"Duplicate lead id={duplicate_id} not found.")

    # Merge non-null fields (survivor values take priority).
    # Consolidation proves this entity is live — reset TTL fields.
    conn.execute(
        """
        UPDATE leads SET
            whatsapp         = COALESCE(whatsapp,         ?),
            company_id       = COALESCE(company_id,       ?),
            physical_address = COALESCE(physical_address, ?),
            legal_flag       = COALESCE(legal_flag,       ?),
            status           = ?,
            last_verified_at = CURRENT_TIMESTAMP,
            is_stale         = 0,
            last_updated_at  = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            duplicate["whatsapp"],
            duplicate["company_id"],
            duplicate["physical_address"],
            duplicate["legal_flag"],
            _advance_status(survivor["status"], duplicate["status"]),
            survivor_id,
        )
    )

    # Migrate provenance: re-point all source records to survivor
    conn.execute(
        "UPDATE lead_sources SET lead_id = ? WHERE lead_id = ?",
        (survivor_id, duplicate_id)
    )

    # Migrate classification audit trail to survivor
    conn.execute(
        "UPDATE lead_classifications SET lead_id = ? WHERE lead_id = ?",
        (survivor_id, duplicate_id)
    )

    # Delete the now-empty duplicate (ON DELETE CASCADE cleans remaining FKs)
    conn.execute("DELETE FROM leads WHERE id = ?", (duplicate_id,))


# ---------------------------------------------------------------------------
# Public orchestrators — manage their own BEGIN IMMEDIATE transactions
# ---------------------------------------------------------------------------

def consolidate_entities(
    conn: sqlite3.Connection,
    survivor_lead_id: int,
    duplicate_lead_id: int,
) -> int:
    """
    Resolve a split-brain: two lead records proven to be the same entity.

    Merges all non-null fields of duplicate into survivor, resets
    last_verified_at and clears is_stale on the survivor, migrates all
    associated foreign keys (lead_sources, lead_classifications), then
    deletes the duplicate record — all within a single atomic transaction.

    Returns the survivor lead id.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        _consolidate_no_tx(conn, survivor_lead_id, duplicate_lead_id)
        conn.commit()
        return survivor_lead_id
    except Exception:
        conn.rollback()
        raise


def upsert_lead(
    conn: sqlite3.Connection,
    lead_data: dict,
    vector: str,
    source_url: str,
    raw_snippet: Optional[str] = None,
) -> int:
    """
    Atomic, concurrency-safe insert-or-merge for one incoming lead.

    Full flow (all steps within a single BEGIN IMMEDIATE transaction):

      1. Sanitize — normalize domain and whatsapp before any lookup.
      2. Secondary-vector resolution — check whatsapp and company_id against
         existing records BEFORE the INSERT attempt.
         a. Single secondary match (different domain):
            Redirect incoming domain to the existing record's domain so the
            INSERT ON CONFLICT(domain) fires and merges fields in-place.
         b. Split-brain detected (whatsapp matches lead A, company_id matches
            lead B, A ≠ B): consolidate A and B into one survivor first, then
            redirect incoming domain to the survivor.
      3. INSERT ... ON CONFLICT(domain) DO UPDATE — native SQLite upsert that
         is immune to concurrent worker races on the same domain. On conflict,
         last_verified_at is reset and is_stale cleared automatically.
      4. Append a lead_sources provenance record.

    Returns the lead id (new or existing).
    """
    lead_data = sanitize_lead_data(lead_data)

    conn.execute("BEGIN IMMEDIATE")
    try:
        whatsapp_match = (
            find_lead_by_whatsapp(conn, lead_data["whatsapp"])
            if lead_data.get("whatsapp") else None
        )
        company_match = (
            find_lead_by_company_id(conn, lead_data["company_id"])
            if lead_data.get("company_id") else None
        )

        # Detect split-brain: two separate existing records proven to be one entity
        if (
            whatsapp_match and company_match
            and whatsapp_match["id"] != company_match["id"]
        ):
            # Consolidate within the current transaction (no nested BEGIN)
            _consolidate_no_tx(conn, whatsapp_match["id"], company_match["id"])
            lead_data["domain"] = whatsapp_match["domain"]

        # Single secondary-vector match: redirect to existing domain
        elif whatsapp_match and whatsapp_match["domain"] != lead_data["domain"]:
            lead_data["domain"] = whatsapp_match["domain"]

        elif company_match and company_match["domain"] != lead_data["domain"]:
            lead_data["domain"] = company_match["domain"]

        # Atomic upsert — immune to concurrent domain collisions.
        # ON CONFLICT path resets last_verified_at and is_stale via _UPSERT_SQL.
        row = conn.execute(
            _UPSERT_SQL,
            {
                "entity_name":      lead_data["entity_name"],
                "domain":           lead_data["domain"],
                "whatsapp":         lead_data.get("whatsapp"),
                "company_id":       lead_data.get("company_id"),
                "physical_address": lead_data.get("physical_address"),
                "status":           lead_data.get("status", "RAW"),
                "legal_flag":       lead_data.get("legal_flag"),
            }
        ).fetchone()
        lead_id: int = row[0]

        insert_source(conn, lead_id, vector, source_url, raw_snippet)
        conn.commit()
        return lead_id

    except Exception:
        conn.rollback()
        raise


def insert_classification(
    conn: sqlite3.Connection,
    lead_id: int,
    status: str,
    confidence: float,
    signals: list,
    model_version: str,
) -> int:
    """
    Insert one classification record into lead_classifications.

    Maps the NLP status to the table's category enum, stores signals as a
    JSON array string, and sets disqualify_reason for DISQUALIFIED_C leads.

    Called by live_run.process_agent_result() immediately after upsert_lead()
    so that every successfully upserted lead has a classification record.

    Returns the new lead_classifications.id.
    """
    _STATUS_TO_CATEGORY = {
        "QUALIFIED_A":               "MANUFACTURER",
        "QUALIFIED_B_PENDING_VERIFY": "IMPORTER",
        "DISQUALIFIED_C":            "DROPSHIPPER",
    }
    category = _STATUS_TO_CATEGORY.get(status, "MANUFACTURER")
    disqualify_reason = status if status == "DISQUALIFIED_C" else None
    signals_json = json.dumps(signals, ensure_ascii=False) if signals else "[]"

    cursor = conn.execute(
        """
        INSERT INTO lead_classifications
            (lead_id, category, confidence, signals, disqualify_reason, model_version)
        VALUES
            (:lead_id, :category, :confidence, :signals, :disqualify_reason, :model_version)
        """,
        {
            "lead_id":          lead_id,
            "category":         category,
            "confidence":       max(0.0, min(1.0, float(confidence))),
            "signals":          signals_json,
            "disqualify_reason": disqualify_reason,
            "model_version":    model_version or "unknown",
        },
    )
    return cursor.lastrowid


# ---------------------------------------------------------------------------
# Domain Blacklist — Phase 2 Global State & Deduplication Manager
# ---------------------------------------------------------------------------

def load_blacklist(conn: sqlite3.Connection) -> frozenset:
    """
    Return all blacklisted domains as an immutable frozenset.

    Called once at pipeline startup. The returned set is OR'd with
    known_domains (from the leads table) to form skip_domains — a combined
    gate that prevents Serper API calls, V3 fetches, and NLP calls being
    spent on any domain already seen or permanently disqualified.

    Returns frozenset[str] (empty if the table is empty or not yet created).
    """
    try:
        rows = conn.execute("SELECT domain FROM domain_blacklist").fetchall()
        return frozenset(row[0] for row in rows if row[0])
    except Exception:
        # Table may not exist yet on very old DB files before the schema
        # migration runs. Return empty set — the migration will create it.
        return frozenset()


def add_to_blacklist(
    conn: sqlite3.Connection,
    domain: str,
    reason: str,
    added_by: str = "system",
) -> None:
    """
    Permanently blacklist a domain.

    Uses INSERT OR IGNORE — safe to call repeatedly for the same domain
    (idempotent). Does not raise if the domain is already blacklisted.

    reason must be one of:
      AUTO_HIGH_CONF_DISQUALIFY — LLM confidence ≥ 0.90 DISQUALIFIED_C
      HALACHIC                  — halachic material incompatibility
      MANUAL                    — human rejection via UI
      AGGREGATOR                — newly discovered aggregator domain

    Commits immediately — the blacklist is safety-critical and must be
    durable even if the calling classification transaction rolls back.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO domain_blacklist (domain, reason, added_by)
        VALUES (?, ?, ?)
        """,
        (domain, reason, added_by),
    )
    conn.commit()


def bootstrap_blacklist(conn: sqlite3.Connection) -> int:
    """
    One-time (idempotent) auto-population of domain_blacklist from existing
    DISQUALIFIED_C leads with high-confidence LLM rejections.

    Called by initialize_schema() on every startup. INSERT OR IGNORE ensures
    this is safe to run repeatedly — it only adds domains not yet blacklisted.

    Criteria:
      - leads.status = 'DISQUALIFIED_C'
      - MAX(lead_classifications.confidence) >= 0.90 for that lead
      - lead_classifications.model_version != 'tier1'
        (tier1 fires for technical reasons — empty page, non-Hebrew, 403 error —
         which may be transient. We only blacklist domains the LLM deliberately
         rejected at high confidence based on actual page content.)

    Returns the count of rows inserted (0 on all subsequent runs once fully
    bootstrapped).
    """
    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO domain_blacklist (domain, reason, added_by)
            SELECT l.domain, 'AUTO_HIGH_CONF_DISQUALIFY', 'system'
            FROM   leads l
            JOIN   lead_classifications lc ON lc.lead_id = l.id
            WHERE  l.status = 'DISQUALIFIED_C'
              AND  lc.model_version != 'tier1'
            GROUP  BY l.id
            HAVING MAX(lc.confidence) >= 0.90
            """
        )
        conn.commit()
        return cursor.rowcount
    except Exception:
        # Graceful degradation: if lead_classifications table is missing
        # (fresh DB with no runs yet), skip silently.
        return 0


def update_contact_fields(
    conn: sqlite3.Connection,
    lead_id: int,
    whatsapp: str,
) -> None:
    """
    Write an enriched WhatsApp number to an existing lead.

    COALESCE guard: only fills the column if it is currently NULL — never
    overwrites a phone number that was already captured during initial
    discovery or a prior enrichment pass. Safe to call repeatedly.

    Resets last_updated_at and last_verified_at to CURRENT_TIMESTAMP to
    signal that fresh contact data has been confirmed for this lead.

    Does NOT open a transaction — the caller
    (live_run._run_contact_enrichment_phase) owns the BEGIN / COMMIT /
    ROLLBACK cycle.

    Called for QUALIFIED_A and QUALIFIED_B_PENDING_VERIFY leads where
    whatsapp is NULL after the main classification pass.
    """
    conn.execute(
        """
        UPDATE leads SET
            whatsapp         = COALESCE(whatsapp, ?),
            last_updated_at  = CURRENT_TIMESTAMP,
            last_verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (whatsapp, lead_id),
    )


# ---------------------------------------------------------------------------
# Sprint 5 — Dashboard interface helpers
# These functions are called exclusively by dashboard.py and carry no
# transaction ownership — callers commit/rollback where noted.
# ---------------------------------------------------------------------------

_RUN_HISTORY_PATH = Path(__file__).parent.parent / "M-memory" / "run_history.json"

_DASHBOARD_QUERY = """
    SELECT
        l.id,
        l.entity_name,
        l.domain,
        l.whatsapp,
        l.status,
        l.is_priority,
        l.first_seen_at,
        l.is_stale,
        -- Best NLP classification (correlated subqueries — no GROUP BY complexity)
        (SELECT MAX(lc.confidence)
         FROM   lead_classifications lc WHERE lc.lead_id = l.id)              AS confidence,
        (SELECT lc.category
         FROM   lead_classifications lc WHERE lc.lead_id = l.id
         ORDER  BY lc.confidence DESC LIMIT 1)                                AS classification,
        (SELECT lc.signals
         FROM   lead_classifications lc WHERE lc.lead_id = l.id
         ORDER  BY lc.confidence DESC LIMIT 1)                                AS signals,
        -- Discovery vectors
        (SELECT GROUP_CONCAT(DISTINCT ls.vector)
         FROM   lead_sources ls WHERE ls.lead_id = l.id)                      AS source_vectors,
        -- Outreach summary
        (SELECT COUNT(*) FROM outreach_log ol WHERE ol.lead_id = l.id)        AS outreach_count,
        (SELECT MAX(ol.initiated_at)
         FROM   outreach_log ol WHERE ol.lead_id = l.id)                      AS last_outreach_at,
        (SELECT ol.status FROM outreach_log ol WHERE ol.lead_id = l.id
         ORDER  BY ol.initiated_at DESC LIMIT 1)                              AS last_outreach_status,
        -- CRM sync (Sprint 11C)
        l.exported_at
    FROM  leads l
    {where_clause}
    ORDER BY l.is_priority DESC, confidence DESC NULLS LAST, l.first_seen_at DESC
"""


def get_leads_for_dashboard(
    conn: sqlite3.Connection,
    status_filter: Optional[str] = None,
    search_query: Optional[str] = None,
) -> list[dict]:
    """
    Return leads as a list of dicts, optionally filtered by status and/or a
    free-text search query.

    Each row contains: id, entity_name, domain, whatsapp, status, is_priority,
    first_seen_at, is_stale, confidence, classification, signals,
    source_vectors, outreach_count, last_outreach_at, last_outreach_status.

    Search is applied in Python (after SQL) for simplicity — with 300-500 leads
    this is fast and avoids complex LIKE parameterisation across multiple tables.

    Ordering: is_priority DESC, confidence DESC, first_seen_at DESC.
    """
    conn.row_factory = sqlite3.Row
    where = "WHERE l.status = ?" if status_filter else ""
    params = (status_filter,) if status_filter else ()
    rows = conn.execute(_DASHBOARD_QUERY.format(where_clause=where), params).fetchall()
    conn.row_factory = None
    results = [dict(r) for r in rows]

    if search_query:
        q = search_query.lower().strip()
        filtered = []
        for r in results:
            haystack = " ".join(filter(None, [
                r.get("entity_name") or "",
                r.get("domain")      or "",
                r.get("whatsapp")    or "",
                r.get("signals")     or "",
                r.get("classification") or "",
            ])).lower()
            if q in haystack:
                filtered.append(r)
        return filtered

    return results


def toggle_lead_priority(conn: sqlite3.Connection, lead_id: int) -> int:
    """
    Toggle the is_priority flag for a lead (0 → 1, 1 → 0).
    Returns the NEW value. Caller must commit.
    Used by the dashboard ⭐ priority button.
    """
    conn.execute(
        "UPDATE leads SET is_priority = 1 - is_priority, "
        "last_updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (lead_id,),
    )
    row = conn.execute(
        "SELECT is_priority FROM leads WHERE id = ?", (lead_id,)
    ).fetchone()
    return row[0] if row else 0


def mark_lead_exported(conn: sqlite3.Connection, lead_id: int) -> None:
    """
    Stamp exported_at = CURRENT_TIMESTAMP on a lead after a successful CRM push.
    Caller must commit. Idempotent — calling again updates the timestamp to the
    latest push time (useful for re-syncs after CRM schema changes).
    Sprint 11C — CRM Sync.
    """
    conn.execute(
        "UPDATE leads SET exported_at = CURRENT_TIMESTAMP WHERE id = ?",
        (lead_id,),
    )


def get_pipeline_stats(conn: sqlite3.Connection) -> dict:
    """
    Return aggregate KPI metrics for the dashboard header row.

    Returns a dict with keys:
      total, qualified_a, qualified_b, unclassified, disqualified,
      blacklisted, avg_confidence, total_api_spend_usd (placeholder 0.0).
    """
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                                       AS total,
            SUM(CASE WHEN status = 'QUALIFIED_A'   THEN 1 ELSE 0 END)    AS qualified_a,
            SUM(CASE WHEN status LIKE 'QUALIFIED_B%' THEN 1 ELSE 0 END)  AS qualified_b,
            SUM(CASE WHEN status = 'UNCLASSIFIED'  THEN 1 ELSE 0 END)    AS unclassified,
            SUM(CASE WHEN status = 'DISQUALIFIED_C' THEN 1 ELSE 0 END)   AS disqualified,
            ROUND(AVG(sub.conf), 3)                                        AS avg_confidence
        FROM leads l
        LEFT JOIN (
            SELECT lead_id, MAX(confidence) AS conf
            FROM   lead_classifications
            GROUP  BY lead_id
        ) sub ON sub.lead_id = l.id
        """
    ).fetchone()
    bl_count = conn.execute(
        "SELECT COUNT(*) FROM domain_blacklist"
    ).fetchone()[0]
    return {
        "total":             row[0] or 0,
        "qualified_a":       row[1] or 0,
        "qualified_b":       row[2] or 0,
        "unclassified":      row[3] or 0,
        "disqualified":      row[4] or 0,
        "blacklisted":       bl_count or 0,
        "avg_confidence":    row[5] or 0.0,
        "total_api_spend_usd": 0.0,   # tracked externally via token report
    }


def update_lead_status(
    conn: sqlite3.Connection,
    lead_id: int,
    new_status: str,
) -> None:
    """
    Force-set a lead's status bypassing the normal lifecycle ordering.
    Used by dashboard CRM actions ("Promote to A", "Reject Permanently").
    Caller must commit.
    """
    if new_status not in STATUS_ORDER:
        raise ValueError(f"Unknown status: {new_status!r}")
    conn.execute(
        "UPDATE leads SET status = ?, last_updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, lead_id),
    )


def add_lead_note(
    conn: sqlite3.Connection,
    lead_id: int,
    note_text: str,
) -> int:
    """
    Append a human annotation for a lead.
    Returns the new note id.
    Caller must commit.
    """
    note_text = note_text.strip()
    if not note_text:
        raise ValueError("note_text must not be empty")
    cursor = conn.execute(
        "INSERT INTO lead_notes (lead_id, note_text) VALUES (?, ?)",
        (lead_id, note_text),
    )
    return cursor.lastrowid


def get_lead_notes(
    conn: sqlite3.Connection,
    lead_id: int,
) -> list[dict]:
    """
    Return all notes for a lead, newest first.
    Each dict has: id, lead_id, note_text, created_at.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, lead_id, note_text, created_at
        FROM   lead_notes
        WHERE  lead_id = ?
        ORDER  BY created_at DESC
        """,
        (lead_id,),
    ).fetchall()
    conn.row_factory = None
    return [dict(r) for r in rows]


def get_run_history() -> list[dict]:
    """
    Return the pipeline run history from M-memory/run_history.json.
    Each dict has at minimum: run_at, leads_found, api_calls.
    Returns [] if the file does not exist yet (fresh install).
    """
    if not _RUN_HISTORY_PATH.exists():
        return []
    try:
        with _RUN_HISTORY_PATH.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


# ---------------------------------------------------------------------------
# Sprint 6 — Outreach log helpers
# All write helpers follow the module's transaction contract:
# callers own BEGIN / COMMIT / ROLLBACK.
# ---------------------------------------------------------------------------

def log_outreach_attempt(
    conn: sqlite3.Connection,
    lead_id: int,
    template_track: str,
    message_text: str,
    wa_link: Optional[str],
    tenant_id: str = "kritikaal",
) -> int:
    """
    Record a sent WhatsApp outreach attempt in outreach_log.
    Status is set to 'sent' immediately — only call after the user confirms send.
    Returns the new outreach_log row id. Caller must commit.
    """
    cursor = conn.execute(
        """
        INSERT INTO outreach_log
            (lead_id, tenant_id, channel, template_track, message_text, wa_link, status)
        VALUES (?, ?, 'whatsapp', ?, ?, ?, 'sent')
        """,
        (lead_id, tenant_id, template_track, message_text, wa_link),
    )
    return cursor.lastrowid


def update_outreach_status(
    conn: sqlite3.Connection,
    outreach_id: int,
    status: str,
) -> None:
    """
    Update the outcome of an existing outreach attempt.
    Valid status values: 'sent' | 'replied' | 'no_response'.
    Sets replied_at to CURRENT_TIMESTAMP when status is 'replied'.
    Caller must commit.
    """
    if status not in ("sent", "replied", "no_response"):
        raise ValueError(f"Invalid outreach status: {status!r}")
    if status == "replied":
        conn.execute(
            "UPDATE outreach_log SET status = ?, replied_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, outreach_id),
        )
    else:
        conn.execute(
            "UPDATE outreach_log SET status = ? WHERE id = ?",
            (status, outreach_id),
        )


def get_outreach_history(
    conn: sqlite3.Connection,
    lead_id: int,
) -> list[dict]:
    """
    Return all outreach attempts for a lead, newest first.
    Each dict has: id, template_track, message_text, wa_link, status,
    initiated_at, replied_at.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, template_track, message_text, wa_link, status,
               initiated_at, replied_at
        FROM   outreach_log
        WHERE  lead_id = ?
        ORDER  BY initiated_at DESC
        """,
        (lead_id,),
    ).fetchall()
    conn.row_factory = None
    return [dict(r) for r in rows]


def get_outreach_queue(
    conn: sqlite3.Connection,
    tenant_id: str = "kritikaal",
) -> list[dict]:
    """
    Return QUALIFIED_A leads that have a WhatsApp number, enriched with their
    latest outreach status and the best NLP classification data.

    Ordered by confidence DESC (best leads first).

    Each row: id, entity_name, domain, whatsapp, confidence, classification,
    signals, source_vectors, last_outreach_status, last_outreach_at, outreach_count.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            l.id,
            l.entity_name,
            l.domain,
            l.whatsapp,
            lc_best.confidence,
            lc_best.category          AS classification,
            lc_best.signals           AS signals,
            GROUP_CONCAT(DISTINCT ls.vector) AS source_vectors,
            ol_latest.status          AS last_outreach_status,
            ol_latest.initiated_at    AS last_outreach_at,
            COALESCE(ol_cnt.cnt, 0)   AS outreach_count
        FROM leads l
        -- Best classification per lead (highest confidence)
        LEFT JOIN (
            SELECT lc2.lead_id, lc2.category, lc2.signals, lc2.confidence
            FROM   lead_classifications lc2
            WHERE  lc2.confidence = (
                SELECT MAX(lc3.confidence)
                FROM   lead_classifications lc3
                WHERE  lc3.lead_id = lc2.lead_id
            )
            GROUP BY lc2.lead_id
        ) lc_best ON lc_best.lead_id = l.id
        -- Source vectors
        LEFT JOIN lead_sources ls ON ls.lead_id = l.id
        -- Latest outreach attempt
        LEFT JOIN (
            SELECT ol.lead_id, ol.status, ol.initiated_at
            FROM   outreach_log ol
            WHERE  ol.tenant_id = ?
              AND  ol.initiated_at = (
                  SELECT MAX(ol2.initiated_at)
                  FROM   outreach_log ol2
                  WHERE  ol2.lead_id  = ol.lead_id
                    AND  ol2.tenant_id = ?
              )
            GROUP BY ol.lead_id
        ) ol_latest ON ol_latest.lead_id = l.id
        -- Total outreach count per lead
        LEFT JOIN (
            SELECT lead_id, COUNT(*) AS cnt
            FROM   outreach_log
            WHERE  tenant_id = ?
            GROUP  BY lead_id
        ) ol_cnt ON ol_cnt.lead_id = l.id
        WHERE l.status   = 'QUALIFIED_A'
          AND l.whatsapp IS NOT NULL
        GROUP BY l.id
        ORDER BY lc_best.confidence DESC NULLS LAST
        """,
        (tenant_id, tenant_id, tenant_id),
    ).fetchall()
    conn.row_factory = None
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Sprint 6.5 — HITL Feedback Loop helpers
# ---------------------------------------------------------------------------

def log_lead_rejection(
    conn: sqlite3.Connection,
    lead_id: int,
    domain: str,
    rejection_reason: str,
    nlp_signals: Optional[list] = None,
    nlp_confidence: Optional[float] = None,
    guardrail_triggered: bool = False,
    guardrail_override: bool = False,
    tenant_id: str = "kritikaal",
) -> int:
    """
    Record one human rejection with its typed reason into lead_feedback.

    Called by the dashboard after the operator confirms a permanent rejection.
    Captures the NLP signals and confidence at the moment of rejection so the
    guardrail history is preserved for Stage 2 curation review.

    Returns the new lead_feedback.id.
    Caller must commit.
    """
    signals_json = json.dumps(nlp_signals, ensure_ascii=False) if nlp_signals else None
    cursor = conn.execute(
        """
        INSERT INTO lead_feedback
            (lead_id, tenant_id, domain, rejection_reason,
             nlp_signals, nlp_confidence,
             guardrail_triggered, guardrail_override)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            tenant_id,
            domain,
            rejection_reason.strip(),
            signals_json,
            nlp_confidence,
            int(guardrail_triggered),
            int(guardrail_override),
        ),
    )
    return cursor.lastrowid


def get_recent_feedback(
    conn: sqlite3.Connection,
    tenant_id: str = "kritikaal",
    n: int = 10,
) -> list[dict]:
    """
    Return the n most recent rejection reasons for injection into the NLP
    system prompt (Dynamic Exemplar Injection — Sprint 6.5 Stage 1).

    Each returned dict has:
        domain            — the rejected domain
        rejection_reason  — the operator's typed reason
        nlp_signals       — list[str] or [] (parsed from JSON snapshot)
        nlp_confidence    — float or None

    Only rows with a non-empty rejection_reason are returned; silent
    (reason-less) rejections are excluded — they carry no calibration signal.

    Ordered newest-first so the injection cap always keeps the most recent
    operator feedback when the total exceeds n.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT domain, rejection_reason, nlp_signals, nlp_confidence
        FROM   lead_feedback
        WHERE  tenant_id = ?
          AND  rejection_reason != ''
        ORDER  BY created_at DESC
        LIMIT  ?
        """,
        (tenant_id, n),
    ).fetchall()
    conn.row_factory = None

    result = []
    for r in rows:
        try:
            signals = json.loads(r["nlp_signals"]) if r["nlp_signals"] else []
        except (json.JSONDecodeError, TypeError):
            signals = []
        result.append({
            "domain":           r["domain"],
            "rejection_reason": r["rejection_reason"],
            "nlp_signals":      signals,
            "nlp_confidence":   r["nlp_confidence"],
        })
    return result


def get_lead_classification_snapshot(
    conn: sqlite3.Connection,
    lead_id: int,
) -> Optional[dict]:
    """
    Return the highest-confidence classification record for a lead.
    Used by the dashboard Smart Guardrail to check what signals the NLP
    extracted before the operator attempts a rejection.

    Returns dict with: confidence, signals (list), category — or None if
    no classification record exists yet.
    """
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT confidence, signals, category
        FROM   lead_classifications
        WHERE  lead_id = ?
        ORDER  BY confidence DESC, classified_at DESC
        LIMIT  1
        """,
        (lead_id,),
    ).fetchone()
    conn.row_factory = None

    if row is None:
        return None

    try:
        signals = json.loads(row["signals"]) if row["signals"] else []
    except (json.JSONDecodeError, TypeError):
        signals = []

    return {
        "confidence": row["confidence"],
        "signals":    signals,
        "category":   row["category"],
    }


def get_agent_roi_stats(conn: sqlite3.Connection, tenant_id: str = "kritikaal") -> list[dict]:
    """
    Return per-agent qualification statistics for the Pipeline ROI table.

    Joins:
      lead_sources.vector   — discovery vector (agent identity)
      leads.status          — current lead status
      lead_classifications  — highest-confidence classification per lead

    Returns a list of dicts, one per vector, sorted by Class-A count desc:
      vector, display_name, leads_found, class_a, disqualified,
      unclassified, avg_confidence, class_a_pct
    """
    # Mirrors exporter._VECTOR_DISPLAY — covers both legacy and current vector names.
    _VECTOR_DISPLAY = {
        "V1_SERPER":              "Core Leather",       # legacy name (pre-Sprint 7)
        "V1_LATERAL":             "Lateral Industries",
        "V1_SHOPIFY_FINGERPRINT": "Shopify Footprint",  # legacy name (pre-Sprint 7)
        "V1_COMPETITOR":          "Competitor Lookalike",
        "V1_PROCUREMENT":         "Gov Procurement",
        "V1_SOCIAL_PAGE":         "Social-Only",
        "V1_PURCHASE_INTENT":     "Purchase Intent",
        "V2_SERPAPI":             "Maps / Local",
        "V3_DIRECT":              "Direct",
        "ig_signal_v1":           "Instagram",
    }

    rows = conn.execute(
        """
        WITH best_cls AS (
            -- Highest-confidence classification per lead
            -- NOTE: lead_classifications uses 'category', not 'status'
            SELECT   lead_id,
                     MAX(confidence) AS confidence
            FROM     lead_classifications
            GROUP BY lead_id
        ),
        per_lead AS (
            -- One row per lead, carrying vector + current status + best confidence
            -- NOTE: leads table has no tenant_id column; all rows are single-tenant
            SELECT  ls.lead_id,
                    ls.vector,
                    l.status,
                    bc.confidence
            FROM    lead_sources  ls
            JOIN    leads         l   ON l.id       = ls.lead_id
            LEFT JOIN best_cls    bc  ON bc.lead_id = ls.lead_id
            GROUP BY ls.lead_id, ls.vector   -- handle multi-source leads once per vector
        )
        SELECT
            vector,
            COUNT(*)                                          AS leads_found,
            SUM(CASE WHEN status = 'QUALIFIED_A'  THEN 1 ELSE 0 END) AS class_a,
            SUM(CASE WHEN status = 'DISQUALIFIED_C' THEN 1 ELSE 0 END) AS disqualified,
            SUM(CASE WHEN status IN ('UNCLASSIFIED','QUALIFIED_B_PENDING_VERIFY')
                     THEN 1 ELSE 0 END)                       AS unclassified,
            ROUND(AVG(COALESCE(confidence, 0)), 3)            AS avg_confidence
        FROM  per_lead
        GROUP BY vector
        ORDER BY class_a DESC, leads_found DESC
        """,
    ).fetchall()

    result = []
    for row in rows:
        vector     = row[0]
        leads      = row[1]
        class_a    = row[2]
        disq       = row[3]
        unclass    = row[4]
        avg_conf   = row[5] or 0.0
        class_a_pct = round((class_a / leads * 100) if leads else 0, 1)
        result.append({
            "vector":        vector,
            "display_name":  _VECTOR_DISPLAY.get(vector, vector),
            "leads_found":   leads,
            "class_a":       class_a,
            "disqualified":  disq,
            "unclassified":  unclass,
            "avg_confidence": avg_conf,
            "class_a_pct":   class_a_pct,
        })

    return result


def flag_stale_leads(conn: sqlite3.Connection, days_threshold: int) -> int:
    """
    Scan the database and mark decayed leads that have not been confirmed
    by fresh incoming data within the last `days_threshold` days.

    For each lead where last_verified_at < (now - days_threshold days):
      - is_stale is set to 1.
      - status is set to REQUIRES_REVERIFICATION.

    Exclusions:
      - DISQUALIFIED_C leads are never flagged. They are permanently
        disqualified and re-verification would be meaningless.
      - Leads already at REQUIRES_REVERIFICATION are updated idempotently
        (is_stale written again as 1; no harmful side effects).

    TTL contract: this function reads last_verified_at to decide which
    leads to flag but does NOT modify it. The timestamp is only ever
    written by successful match operations (upsert, merge, consolidation).

    Returns the count of leads flagged in this pass.
    """
    if days_threshold < 1:
        raise ValueError(f"days_threshold must be >= 1, got {days_threshold!r}")

    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute(
            """
            UPDATE leads
            SET
                is_stale = 1,
                status   = 'REQUIRES_REVERIFICATION'
            WHERE
                last_verified_at < datetime('now', ?)
                AND status != 'DISQUALIFIED_C'
            """,
            (f"-{days_threshold} days",)
        )
        count: int = cursor.rowcount
        conn.commit()
        return count
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# Sprint 11D — Feedback Export & Analytics
# ---------------------------------------------------------------------------

def export_feedback_to_csv_format(
    conn: sqlite3.Connection,
    tenant_id: str = "kritikaal",
) -> str:
    """
    Export all operator rejection feedback to CSV format for external audit,
    calibration review, or data integration.

    Returns a CSV string (with header row) suitable for writing to disk or
    downloading via Streamlit. Columns:

        domain, rejection_reason, nlp_category, nlp_confidence,
        nlp_signals, guardrail_triggered, guardrail_override, recorded_at

    Ordered newest-first (most recent rejections first).
    Caller is responsible for writing to disk if needed.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT domain, rejection_reason,
               nlp_signals, nlp_confidence,
               guardrail_triggered, guardrail_override, created_at
        FROM   lead_feedback
        WHERE  tenant_id = ?
        ORDER  BY created_at DESC
        """,
        (tenant_id,),
    ).fetchall()
    conn.row_factory = None

    if not rows:
        # Header-only CSV if no feedback yet
        return "domain,rejection_reason,nlp_confidence,nlp_signals,guardrail_triggered,guardrail_override,recorded_at\n"

    # Build CSV with proper escaping
    lines = [
        "domain,rejection_reason,nlp_confidence,nlp_signals,"
        "guardrail_triggered,guardrail_override,recorded_at"
    ]

    for r in rows:
        domain = (r["domain"] or "").replace('"', '""')        # CSV escape inner quotes
        reason = (r["rejection_reason"] or "").replace('"', '""')
        confidence = f"{r['nlp_confidence']:.4f}" if r["nlp_confidence"] else ""
        signals_raw = r["nlp_signals"] or "[]"
        signals_list = []
        try:
            parsed = json.loads(signals_raw) if isinstance(signals_raw, str) else signals_raw
            signals_list = parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            pass
        signals_str = "; ".join(str(s) for s in signals_list).replace('"', '""')
        guardrail_triggered = "1" if r["guardrail_triggered"] else "0"
        guardrail_override = "1" if r["guardrail_override"] else "0"
        created_at = r["created_at"] or ""

        # CSV line — text fields wrapped in double-quotes, numerics bare
        line = (
            f'"{domain}","{reason}",{confidence},'
            f'"{signals_str}",{guardrail_triggered},{guardrail_override},"{created_at}"'
        )
        lines.append(line)

    return "\n".join(lines) + "\n"


def get_top_rejection_reasons(
    conn: sqlite3.Connection,
    limit: int = 5,
    tenant_id: str = "kritikaal",
) -> list[dict]:
    """
    Return the most common rejection reasons from the feedback table.

    Each result dict contains:
        reason        — the rejection reason text
        count         — number of times this reason was used
        percentage    — percentage of all rejections

    Ordered by count descending.
    Only includes non-empty rejection_reason values.
    """
    conn.row_factory = sqlite3.Row
    total_row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM   lead_feedback
        WHERE  tenant_id = ?
               AND rejection_reason != ''
               AND rejection_reason IS NOT NULL
        """,
        (tenant_id,),
    ).fetchone()
    conn.row_factory = None

    total_count = total_row["total"] if total_row else 0
    if total_count == 0:
        return []

    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT rejection_reason,
               COUNT(*) AS cnt
        FROM   lead_feedback
        WHERE  tenant_id = ?
               AND rejection_reason != ''
               AND rejection_reason IS NOT NULL
        GROUP  BY rejection_reason
        ORDER  BY cnt DESC
        LIMIT  ?
        """,
        (tenant_id, limit),
    ).fetchall()
    conn.row_factory = None

    result = []
    for r in rows:
        pct = round((r["cnt"] / total_count) * 100, 1) if total_count > 0 else 0
        result.append({
            "reason": r["rejection_reason"],
            "count": r["cnt"],
            "percentage": pct,
        })

    return result
