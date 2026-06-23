-- =============================================================================
-- KritiKaal Leads Hunter — Database Schema
-- File: T-tools/db_schema.sql
-- Governed by: B-brain/01-tech-stack.md (Iron Principle 5)
-- Classification logic: C-core/02-target-audience.md
-- =============================================================================
-- DEDUPLICATION STRATEGY (Three-Vector Match):
--   Primary key:   domain       (normalized root domain or maps::<place_id>)
--   Secondary key: whatsapp     (UNIQUE — same phone = same business entity)
--   Tertiary key:  company_id   (UNIQUE — same ח.פ/עוסק מורשה = same legal entity)
--
-- UNIQUENESS + NULL HANDLING:
--   Column-level UNIQUE constraints are used (not partial indexes) because:
--   (a) SQLite column UNIQUE already permits multiple NULLs (NULL != NULL in SQL).
--   (b) ON CONFLICT(column) resolution in Python upsert requires column-level
--       UNIQUE constraints, not partial index constraints.
--   The DB-level UNIQUE acts as a hard safety net behind the Python merge logic.
--
-- CONCURRENCY:
--   Python callers must use BEGIN IMMEDIATE before any upsert sequence to
--   acquire a write lock and prevent TOCTOU races between workers.
--
-- DATA DECAY PREVENTION (TTL):
--   last_verified_at tracks the last time a lead was confirmed by fresh data.
--   is_stale is set to TRUE by flag_stale_leads() when last_verified_at
--   exceeds the configured days_threshold. Stale leads receive status
--   REQUIRES_REVERIFICATION and re-enter the enrichment pipeline on next match.
-- =============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Table 1: leads
-- One row per unique business entity.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS leads (
    id                INTEGER  PRIMARY KEY AUTOINCREMENT,

    -- Identity
    entity_name       TEXT     NOT NULL,
    domain            TEXT     NOT NULL UNIQUE,   -- Primary dedup key
                                                  -- Normalized: no www., no scheme,
                                                  -- no trailing slash.
                                                  -- Fallback for map-only: 'maps::<place_id>'

    -- Core extraction fields (Iron Principle 4)
    whatsapp          TEXT     UNIQUE,            -- Secondary dedup key
                                                  -- Strict numeric: 972XXXXXXXXX (12 digits)
                                                  -- No +, no dashes, no spaces.
    company_id        TEXT     UNIQUE,            -- Tertiary dedup key
                                                  -- ח.פ / עוסק מורשה, exactly 9 digits.
    physical_address  TEXT,                       -- Full Israeli street address (free text).

    -- Classification (C-core/02-target-audience.md)
    -- Allowed values:
    --   RAW                        | inserted, no enrichment attempted
    --   REQUIRES_REVERIFICATION    | previously qualified; marked stale by TTL engine
    --   ENRICHED                   | core extraction run, awaiting NLP
    --   QUALIFIED_A                | Class A: manufacturer / official importer
    --   QUALIFIED_B_PENDING_VERIFY | Class B: needs phone verification
    --   DISQUALIFIED_C             | Class C: dropshipper — excluded from Output
    --   UNCLASSIFIED               | NLP confidence < 0.75, manual review needed
    --   PENDING_LEGAL              | no valid company_id found
    status            TEXT     NOT NULL DEFAULT 'RAW'
                               CHECK (status IN (
                                   'RAW',
                                   'REQUIRES_REVERIFICATION',
                                   'ENRICHED',
                                   'QUALIFIED_A',
                                   'QUALIFIED_B_PENDING_VERIFY',
                                   'DISQUALIFIED_C',
                                   'UNCLASSIFIED',
                                   'PENDING_LEGAL'
                               )),

    -- Legal flag (Iron Principle 4b)
    legal_flag        TEXT     CHECK (legal_flag IS NULL OR legal_flag = 'PENDING_LEGAL'),

    -- Timestamps
    first_seen_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- TTL / Decay Prevention
    -- last_verified_at: refreshed to CURRENT_TIMESTAMP on every successful
    --   match (upsert conflict, merge, or consolidation). Never touched by
    --   flag_stale_leads() — its age is precisely what that function measures.
    last_verified_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- is_stale: 0 = fresh, 1 = stale (set by flag_stale_leads, cleared on
    --   any subsequent successful match).
    is_stale          INTEGER   NOT NULL DEFAULT 0
                                CHECK (is_stale IN (0, 1)),

    -- is_priority: operator-set flag for high-priority follow-up (Sprint 10).
    -- 0 = normal, 1 = starred / priority. Set via dashboard toggle.
    is_priority       INTEGER   NOT NULL DEFAULT 0
                                CHECK (is_priority IN (0, 1)),

    -- exported_at: timestamp of last CRM push via crm_sync.py (Sprint 11C).
    -- NULL = never exported. Set by mark_lead_exported(); cleared by re-export override.
    exported_at       TIMESTAMP DEFAULT NULL
);

-- -----------------------------------------------------------------------------
-- Table 2: lead_sources
-- Provenance log — one row per (lead × discovery event).
-- A lead found via both V1 and V2 gets two rows here, one lead_id.
-- This table is append-only; rows are never updated.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lead_sources (
    id            INTEGER   PRIMARY KEY AUTOINCREMENT,
    lead_id       INTEGER   NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Discovery vector identifier (B-brain/01-tech-stack.md Iron Principle 2)
    -- Known values: V1_SERPER | V2_SERPAPI | V3_DIRECT
    --               V1_LATERAL | V1_SHOPIFY_FINGERPRINT (Phase 1 expansion)
    -- CHECK constraint intentionally absent: every new agent adds a new vector
    -- name. Enforcing an enum here requires a migration per agent. Validation
    -- lives in insert_source() at the application layer instead.
    vector        TEXT      NOT NULL,

    source_url    TEXT      NOT NULL,  -- Exact URL or query string used
    raw_snippet   TEXT,                -- Raw text captured from this source

    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Table 3: lead_classifications
-- NLP audit trail — append-only. One row per classification run.
-- The active classification is the row with the latest classified_at.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lead_classifications (
    id                 INTEGER   PRIMARY KEY AUTOINCREMENT,
    lead_id            INTEGER   NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- NLP result (B-brain/01-tech-stack.md Iron Principle 3)
    -- Allowed values: MANUFACTURER | IMPORTER | DROPSHIPPER
    category           TEXT      NOT NULL
                                 CHECK (category IN ('MANUFACTURER', 'IMPORTER', 'DROPSHIPPER')),

    confidence         REAL      NOT NULL
                                 CHECK (confidence >= 0.0 AND confidence <= 1.0),

    signals            TEXT,     -- JSON array of detected linguistic signals
                                 -- e.g. '["יבוא בלעדי", "נציג רשמי"]'

    disqualify_reason  TEXT,     -- Populated for Class C: the specific signal matched

    model_version      TEXT      NOT NULL,  -- LLM model ID + prompt version tag

    classified_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Domain UNIQUE index (column constraint already creates this; explicit for documentation)
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_domain
    ON leads(domain);

-- Output filtering by classification status
CREATE INDEX IF NOT EXISTS idx_leads_status
    ON leads(status);

-- TTL scan: flag_stale_leads() queries by last_verified_at age, filtered by
-- is_stale=0 to skip leads already flagged in a prior pass.
CREATE INDEX IF NOT EXISTS idx_leads_ttl
    ON leads(last_verified_at, is_stale)
    WHERE is_stale = 0;

-- Source provenance joins
CREATE INDEX IF NOT EXISTS idx_sources_lead_id
    ON lead_sources(lead_id);

-- Classification audit trail joins + latest-row lookup
CREATE INDEX IF NOT EXISTS idx_classifications_lead_id_time
    ON lead_classifications(lead_id, classified_at DESC);

-- =============================================================================
-- Table 4: domain_blacklist                                    (Phase 2 — M-002)
-- Permanent disqualification registry. One row per domain that must never be
-- re-scraped or re-evaluated in any future pipeline run.
--
-- POPULATION PATHS:
--   (a) system / AUTO_HIGH_CONF_DISQUALIFY: written by live_run.py after any
--       DISQUALIFIED_C classification at confidence ≥ 0.90 via the LLM (not
--       tier1 technical rejections). These are structurally irrelevant domains —
--       cosmetics, automotive, news media, SaaS — that slipped past the
--       aggregator blocklist.
--   (b) system / HALACHIC: written for businesses whose primary product requires
--       halachically-certified leather (incompatible raw material supply).
--   (c) human / MANUAL: written by the dashboard UI "Reject Permanently" action.
--   (d) system / AGGREGATOR: written when an aggregator domain is discovered via
--       a search result that should be added to the static blocklist.
--
-- USAGE:
--   load_blacklist(conn) is called once at pipeline startup. The returned
--   frozenset is OR'd with known_domains to form skip_domains — a combined
--   gate that prevents any Serper query, V3 fetch, or NLP call being spent on
--   blacklisted domains in all subsequent runs.
-- =============================================================================

CREATE TABLE IF NOT EXISTS domain_blacklist (
    domain      TEXT      PRIMARY KEY,
    reason      TEXT      NOT NULL
                          CHECK (reason IN (
                              'AUTO_HIGH_CONF_DISQUALIFY',
                              'HALACHIC',
                              'MANUAL',
                              'AGGREGATOR'
                          )),
    added_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by    TEXT      NOT NULL DEFAULT 'system'
                          CHECK (added_by IN ('system', 'human'))
);

-- Fast membership test on every result in parse_response()
CREATE INDEX IF NOT EXISTS idx_blacklist_domain
    ON domain_blacklist(domain);

-- =============================================================================
-- Table 5: lead_notes                                        (Phase 3 — Sprint 5)
-- Human annotations — one row per note per lead. Append-only.
-- Written by the Streamlit dashboard CRM actions panel.
-- =============================================================================

CREATE TABLE IF NOT EXISTS lead_notes (
    id          INTEGER   PRIMARY KEY AUTOINCREMENT,
    lead_id     INTEGER   NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    note_text   TEXT      NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notes_lead_id
    ON lead_notes(lead_id);

-- =============================================================================
-- Table 6: outreach_log                                      (Phase 3 — Sprint 6)
-- Audit trail of all WhatsApp outreach attempts. Append-only.
-- tenant_id defaults to 'kritikaal'; forward-compatible with multi-tenant SaaS.
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_log (
    id              INTEGER   PRIMARY KEY AUTOINCREMENT,
    lead_id         INTEGER   NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tenant_id       TEXT      NOT NULL DEFAULT 'kritikaal',
    channel         TEXT      NOT NULL DEFAULT 'whatsapp'
                              CHECK (channel IN ('whatsapp', 'email', 'phone', 'other')),
    template_track  TEXT,     -- 'manufacturer' | 'importer' | 'generic'
    message_text    TEXT      NOT NULL,
    wa_link         TEXT,
    status          TEXT      NOT NULL DEFAULT 'sent'
                              CHECK (status IN ('sent', 'replied', 'no_response')),
    initiated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    replied_at      TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outreach_lead   ON outreach_log(lead_id);
CREATE INDEX IF NOT EXISTS idx_outreach_tenant ON outreach_log(tenant_id, initiated_at DESC);

-- =============================================================================
-- Table 7: lead_feedback                                    (Sprint 6.5 — HITL)
-- Human-in-the-Loop rejection reasons.
-- One row per operator rejection that includes a typed reason.
-- Used to build the Operator Feedback Calibration Block injected into the NLP
-- system prompt at classification time (Dynamic Exemplar Injection, Stage 1).
--
-- DESIGN NOTES:
--   - append-only: rejections are never deleted — they are the training signal.
--   - guardrail_triggered: 1 if the Smart Guardrail warning was shown to the
--     operator before they confirmed this rejection.
--   - guardrail_override: 1 if the operator explicitly confirmed despite the
--     guardrail warning. Useful for future Stage 2 curation (which overrides
--     deserve to become pinned calibration rules vs. which were mistakes).
--   - nlp_signals: JSON array snapshotted from lead_classifications at the
--     moment of rejection — preserves the evidence the guardrail reasoned about.
-- =============================================================================

CREATE TABLE IF NOT EXISTS lead_feedback (
    id                  INTEGER   PRIMARY KEY AUTOINCREMENT,
    lead_id             INTEGER   NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tenant_id           TEXT      NOT NULL DEFAULT 'kritikaal',
    domain              TEXT      NOT NULL,
    rejection_reason    TEXT      NOT NULL,
    nlp_signals         TEXT,     -- JSON array snapshotted at time of rejection
    nlp_confidence      REAL,     -- confidence score snapshotted at time of rejection
    guardrail_triggered INTEGER   NOT NULL DEFAULT 0 CHECK (guardrail_triggered IN (0, 1)),
    guardrail_override  INTEGER   NOT NULL DEFAULT 0 CHECK (guardrail_override  IN (0, 1)),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_lead   ON lead_feedback(lead_id);
CREATE INDEX IF NOT EXISTS idx_feedback_tenant ON lead_feedback(tenant_id, created_at DESC);
