"""
KritiKaal Leads Hunter — CRM Webhook Emitter
File: T-tools/crm_sync.py
Sprint 11C → Phase 1 Upgrade

Responsibility (SRP):
  Push qualified lead records to the operator's CRM via an outbound
  HTTP POST webhook. Reads the target URL from CRM_WEBHOOK_URL in .env.
  If the variable is absent or empty, every call is a graceful no-op.

Phase 1 Upgrade (Section 3 Data Dictionary):
  - derive_platform()          KONIMBO / CASHCOW / SHOPIFY / WIX / OTHER
  - get_leads_for_crm_export() Full multi-join SQL per Section 3 spec
  - turkey_disruption_score    Extracted from signals JSON array
  - operator_notes             Concatenated 3 most recent lead_notes
  - stage                      Derived: NEW / CONTACTED / MEETING_SCHEDULED /
                                         CONSORTIUM_PITCH / COMMITTED / ACTIVE
  - exported_at stamping       Atomic per-lead DB update after successful push

Usage from dashboard:
    from crm_sync import push_lead_to_crm, CRM_CONFIGURED, push_leads_batch_from_db

Configuration (add to .env):
    CRM_WEBHOOK_URL=https://your-crm.example.com/webhook/leads

Payload contract (schema_version 2.0):
    {
      "source":         "kritikaal_leads_hunter",
      "schema_version": "2.0",
      "pushed_at":      "<ISO-8601 UTC>",
      "lead": {
        "hunter_lead_id":         <int>,
        "brand_name":             <str>,
        "website":                <str>,
        "whatsapp":               <str|null>,
        "company_registration":   <str|null>,
        "address":                <str|null>,
        "qualification_status":   <str>,
        "is_priority":            <int>,
        "business_type":          <str|null>,
        "nlp_confidence":         <float|null>,
        "detected_signals":       [<str>, ...],
        "turkey_disruption_score":<float|null>,
        "platform":               <str>,
        "discovery_vector":       <str|null>,
        "first_seen_at":          <str|null>,
        "last_verified_at":       <str|null>,
        "outreach_status":        <str|null>,
        "outreach_template":      <str|null>,
        "last_outreach_at":       <str|null>,
        "replied_at":             <str|null>,
        "operator_notes":         <str|null>,
        "stage":                  <str>
      }
    }

Dependencies:
    stdlib only (urllib.request + json + sqlite3) — zero new packages required.
"""

import json
import os
import re
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_DB   = _HERE / "leads.db"

def _crm_url() -> str:
    """Return CRM_WEBHOOK_URL from environment, stripped. Empty = not configured."""
    return os.environ.get("CRM_WEBHOOK_URL", "").strip()


def CRM_CONFIGURED() -> bool:
    """True if a webhook URL is set in the environment."""
    return bool(_crm_url())


# ---------------------------------------------------------------------------
# Platform Detection — Section 3: derive_platform()
#
# Source: lead_sources.source_url — the scraper discovery URL.
# Detects whether the brand's storefront runs on Konimbo (dominant Israeli
# e-com platform), CashCow (second major Israeli platform), Shopify,
# Wix, or Other.  Konimbo / CashCow are strong proxy signals for
# Israel-domestic brand operation.
# ---------------------------------------------------------------------------

def derive_platform(source_url: str) -> str:
    """
    Derive the e-commerce platform from the lead's discovery source URL.

    Detection is case-insensitive substring match on the source_url.
    Konimbo is checked for both its current CDN pattern and its known
    subdomain pattern (brand.konimbo.co.il).

    Returns one of: "KONIMBO" | "CASHCOW" | "SHOPIFY" | "WIX" | "OTHER"
    """
    if not source_url:
        return "OTHER"
    url_lower = source_url.lower()
    if "konimbo" in url_lower:
        return "KONIMBO"
    if "cashcow" in url_lower or "cash-cow" in url_lower:
        return "CASHCOW"
    if "shopify" in url_lower or "myshopify" in url_lower:
        return "SHOPIFY"
    if "wix" in url_lower:
        return "WIX"
    return "OTHER"


# ---------------------------------------------------------------------------
# Turkish Disruption Score Extraction
#
# Signals are stored in lead_classifications.signals as a JSON array
# containing strings like "TURKEY_ORIGIN", "SUPPLY_DISRUPTION",
# "POST_EMBARGO_SIGNAL", and "turkey_disruption_score:0.90".
# This function extracts the float from the score token.
# ---------------------------------------------------------------------------

_TURKEY_SCORE_RE = re.compile(
    r'turkey_disruption_score:(\d+(?:\.\d+)?)',
    re.IGNORECASE,
)

def extract_turkey_disruption_score(signals: list[str]) -> Optional[float]:
    """
    Scan the signals list for a "turkey_disruption_score:X.XX" token and
    return the float value. Returns None if no such token is present.

    Example:
        extract_turkey_disruption_score(
            ["TURKEY_ORIGIN", "SUPPLY_DISRUPTION", "turkey_disruption_score:0.90"]
        ) → 0.90
    """
    for sig in signals:
        m = _TURKEY_SCORE_RE.search(str(sig))
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


# ---------------------------------------------------------------------------
# CRM Stage Derivation
#
# Stage is a derived field — computed from outreach_log status and the
# operator's most recent lead_notes (the Dual Boots state machine
# from Section 4 of the architecture doc).
# ---------------------------------------------------------------------------

# Note signatures for each stage. Checked in priority order (highest first).
_STAGE_NOTE_PATTERNS: list[tuple[str, str]] = [
    ("COMMITTED",          r'commitment\s+letter\s+signed|חוזה\s+נחתם|מחויבות\s+אושרה'),
    ("CONSORTIUM_PITCH",   r'consortium\s+pitch|הזמנה\s+רשמית\s+לחבר\s+מייסד|חבר\s+מייסד'),
    ("MEETING_SCHEDULED",  r'meeting\s+confirmed|פגישה\s+אושרה|live\s+(factory\s+)?video|שיחת\s+וידאו\s+חיה'),
]


def derive_crm_stage(
    outreach_status: Optional[str],
    operator_notes: Optional[str],
) -> str:
    """
    Derive the CRM pipeline stage from outreach_log status + operator notes.

    Stage hierarchy (evaluated top-down, first match wins):
      COMMITTED          — commitment letter signed (note keyword match)
      CONSORTIUM_PITCH   — consortium one-pager sent (note keyword match)
      MEETING_SCHEDULED  — meeting confirmed / live video (note keyword match)
      CONTACTED          — outreach_log.status IN (sent, replied, no_response)
      NEW                — no outreach record yet

    The stage is informational and does not affect DB status — it is only
    pushed to the CRM for pipeline view rendering.
    """
    notes_lower = (operator_notes or "").lower()

    # Check highest-priority note signatures first
    for stage, pattern in _STAGE_NOTE_PATTERNS:
        if re.search(pattern, notes_lower, re.IGNORECASE):
            return stage

    # Fall back to outreach status
    if outreach_status in ("sent", "replied", "no_response"):
        return "CONTACTED"

    return "NEW"


# ---------------------------------------------------------------------------
# CRM Export SQL — Section 3: Full Data Dictionary Query
#
# Joins: leads → lead_classifications (latest) → lead_sources (earliest) →
#        outreach_log (latest) → lead_notes (3 most recent, concatenated)
# Filters: QUALIFIED_A / QUALIFIED_B only, not yet exported
# ---------------------------------------------------------------------------

_CRM_EXPORT_SQL = """
SELECT
    l.id                  AS hunter_lead_id,
    l.entity_name         AS brand_name,
    l.domain              AS website,
    l.whatsapp,
    l.company_id          AS company_registration,
    l.physical_address    AS address,
    l.status              AS qualification_status,
    l.is_priority,
    l.first_seen_at,
    l.last_verified_at,

    lc.category           AS business_type,
    lc.confidence         AS nlp_confidence,
    lc.signals            AS detected_signals_json,

    ls.vector             AS discovery_vector,
    ls.source_url,

    ol.template_track     AS outreach_template,
    ol.status             AS outreach_status,
    ol.initiated_at       AS last_outreach_at,
    ol.replied_at

FROM leads l

-- Latest classification (correlated subquery on classified_at)
LEFT JOIN lead_classifications lc
       ON lc.lead_id = l.id
      AND lc.classified_at = (
              SELECT MAX(lc2.classified_at)
              FROM   lead_classifications lc2
              WHERE  lc2.lead_id = l.id
          )

-- Earliest discovery source (first-seen provenance)
LEFT JOIN lead_sources ls
       ON ls.lead_id = l.id
      AND ls.discovered_at = (
              SELECT MIN(ls2.discovered_at)
              FROM   lead_sources ls2
              WHERE  ls2.lead_id = l.id
          )

-- Latest outreach attempt
LEFT JOIN outreach_log ol
       ON ol.lead_id = l.id
      AND ol.initiated_at = (
              SELECT MAX(ol2.initiated_at)
              FROM   outreach_log ol2
              WHERE  ol2.lead_id = l.id
          )

WHERE l.status IN ('QUALIFIED_A', 'QUALIFIED_B_PENDING_VERIFY')
  AND l.is_stale = 0
  AND l.exported_at IS NULL

ORDER BY l.is_priority DESC, lc.confidence DESC
"""

# Separate query to fetch the 3 most recent notes per lead (post-join)
_NOTES_SQL = """
SELECT lead_id, note_text
FROM   lead_notes
WHERE  lead_id IN ({placeholders})
ORDER  BY created_at DESC
"""


def get_leads_for_crm_export(conn: sqlite3.Connection) -> list[dict]:
    """
    Execute the Section 3 CRM export query and return a list of fully
    assembled lead dicts ready for _build_payload_v2().

    Processing steps:
      1. Run the main join query for qualified, un-exported leads.
      2. Collect all lead_ids and run a single notes fetch (max 3 notes
         per lead concatenated with " | " separator).
      3. Parse detected_signals_json → list, extract turkey_disruption_score.
      4. Derive platform from source_url.
      5. Derive CRM stage from outreach_status + operator_notes.

    Returns an empty list if no qualifying leads are found.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(_CRM_EXPORT_SQL).fetchall()
    conn.row_factory = None

    if not rows:
        return []

    # Fetch operator notes for all qualifying leads in one query
    lead_ids = [row["hunter_lead_id"] for row in rows]
    notes_by_lead: dict[int, list[str]] = {}

    if lead_ids:
        placeholders = ",".join("?" * len(lead_ids))
        note_rows = conn.execute(
            _NOTES_SQL.format(placeholders=placeholders),
            lead_ids,
        ).fetchall()
        for nr in note_rows:
            lid  = nr[0]
            text = nr[1]
            if lid not in notes_by_lead:
                notes_by_lead[lid] = []
            if len(notes_by_lead[lid]) < 3:
                notes_by_lead[lid].append(text)

    leads = []
    for row in rows:
        r = dict(row)
        lid = r["hunter_lead_id"]

        # Parse signals JSON → list
        raw_signals = r.get("detected_signals_json") or "[]"
        try:
            signals: list[str] = (
                json.loads(raw_signals) if isinstance(raw_signals, str) else raw_signals
            )
        except (json.JSONDecodeError, TypeError):
            signals = []

        # Extract turkey_disruption_score from signals list
        turkey_score = extract_turkey_disruption_score(signals)

        # Derive platform from discovery source_url
        platform = derive_platform(r.get("source_url") or "")

        # Concatenate operator notes (most recent 3)
        note_texts  = notes_by_lead.get(lid, [])
        operator_notes = " | ".join(note_texts) if note_texts else None

        # Derive CRM stage
        stage = derive_crm_stage(
            outreach_status=r.get("outreach_status"),
            operator_notes=operator_notes,
        )

        leads.append({
            # Lead identity
            "hunter_lead_id":         lid,
            "brand_name":             r.get("brand_name"),
            "website":                r.get("website"),
            "whatsapp":               r.get("whatsapp"),
            "company_registration":   r.get("company_registration"),
            "address":                r.get("address"),
            # Qualification
            "qualification_status":   r.get("qualification_status"),
            "is_priority":            r.get("is_priority", 0),
            # NLP classification
            "business_type":          r.get("business_type"),
            "nlp_confidence":         r.get("nlp_confidence"),
            "detected_signals":       signals,
            "turkey_disruption_score": turkey_score,
            # Discovery provenance
            "platform":               platform,
            "discovery_vector":       r.get("discovery_vector"),
            # Timestamps
            "first_seen_at":          r.get("first_seen_at"),
            "last_verified_at":       r.get("last_verified_at"),
            # Outreach
            "outreach_status":        r.get("outreach_status"),
            "outreach_template":      r.get("outreach_template"),
            "last_outreach_at":       r.get("last_outreach_at"),
            "replied_at":             r.get("replied_at"),
            # CRM-derived
            "operator_notes":         operator_notes,
            "stage":                  stage,
        })

    return leads


# ---------------------------------------------------------------------------
# Payload Builder — Schema Version 2.0 (Section 3 Data Dictionary)
# ---------------------------------------------------------------------------

def _build_payload_v2(lead: dict) -> dict:
    """
    Construct the v2.0 CRM webhook payload from a lead dict produced by
    get_leads_for_crm_export(). All Section 3 fields are mapped directly.
    """
    return {
        "source":         "kritikaal_leads_hunter",
        "schema_version": "2.0",
        "pushed_at":      datetime.now(timezone.utc).isoformat(),
        "lead": {
            "hunter_lead_id":          lead.get("hunter_lead_id"),
            "brand_name":              lead.get("brand_name"),
            "website":                 lead.get("website"),
            "whatsapp":                lead.get("whatsapp"),
            "company_registration":    lead.get("company_registration"),
            "address":                 lead.get("address"),
            "qualification_status":    lead.get("qualification_status"),
            "is_priority":             lead.get("is_priority", 0),
            "business_type":           lead.get("business_type"),
            "nlp_confidence":          lead.get("nlp_confidence"),
            "detected_signals":        lead.get("detected_signals", []),
            "turkey_disruption_score": lead.get("turkey_disruption_score"),
            "platform":                lead.get("platform", "OTHER"),
            "discovery_vector":        lead.get("discovery_vector"),
            "first_seen_at":           lead.get("first_seen_at"),
            "last_verified_at":        lead.get("last_verified_at"),
            "outreach_status":         lead.get("outreach_status"),
            "outreach_template":       lead.get("outreach_template"),
            "last_outreach_at":        lead.get("last_outreach_at"),
            "replied_at":              lead.get("replied_at"),
            "operator_notes":          lead.get("operator_notes"),
            "stage":                   lead.get("stage", "NEW"),
        },
    }


# ---------------------------------------------------------------------------
# Payload Builder — Schema Version 1.0 (backward compat for dashboard)
# Used by the existing push_lead_to_crm() called from the dashboard with
# a get_leads_for_dashboard() dict (not a get_leads_for_crm_export() dict).
# ---------------------------------------------------------------------------

def _build_payload_v1(lead: dict) -> dict:
    """
    Backward-compatible v1.0 payload builder for leads from
    get_leads_for_dashboard(). Called by push_lead_to_crm().
    """
    signals_raw = lead.get("signals") or "[]"
    try:
        signals: list = (
            json.loads(signals_raw) if isinstance(signals_raw, str) else signals_raw
        )
    except (json.JSONDecodeError, TypeError):
        signals = []

    turkey_score = extract_turkey_disruption_score(signals)

    return {
        "source":         "kritikaal_leads_hunter",
        "schema_version": "1.0",
        "pushed_at":      datetime.now(timezone.utc).isoformat(),
        "lead": {
            "id":                    lead.get("id"),
            "entity_name":           lead.get("entity_name"),
            "domain":                lead.get("domain"),
            "whatsapp":              lead.get("whatsapp"),
            "status":                lead.get("status"),
            "classification":        lead.get("classification"),
            "confidence":            lead.get("confidence"),
            "signals":               signals,
            "turkey_disruption_score": turkey_score,
            "source_vectors":        lead.get("source_vectors"),
            "first_seen_at":         lead.get("first_seen_at"),
            "outreach_count":        lead.get("outreach_count", 0),
            "last_outreach_at":      lead.get("last_outreach_at"),
            "last_outreach_status":  lead.get("last_outreach_status"),
            "is_priority":           lead.get("is_priority", 0),
            "exported_at":           lead.get("exported_at"),
        },
    }


# ---------------------------------------------------------------------------
# HTTP Emitter
# ---------------------------------------------------------------------------

def _http_post(
    url: str,
    payload: dict,
    timeout: int = 10,
) -> tuple[bool, str]:
    """
    POST a JSON payload to url. Returns (True, "") on 2xx, else (False, reason).
    Never raises — all exceptions are caught and returned as (False, message).
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req  = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent":   "KritiKaalLeadsHunter/2.0",
            "X-Source":     "kritikaal_leads_hunter",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            return (True, "") if 200 <= code < 300 else (False, f"CRM returned HTTP {code}")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Public API — Single lead push (dashboard "Push to CRM" button)
# ---------------------------------------------------------------------------

def push_lead_to_crm(lead: dict, timeout: int = 10) -> tuple[bool, str]:
    """
    POST a single lead dict (from get_leads_for_dashboard()) to CRM_WEBHOOK_URL.

    This is the dashboard-facing API. It uses the v1.0 schema for backward
    compatibility. The dashboard is responsible for stamping exported_at
    (via mark_lead_exported()) after a True return.

    Returns:
        (True, "")            on success (HTTP 2xx)
        (False, reason: str)  on failure or not-configured
    """
    url = _crm_url()
    if not url:
        return False, "CRM_WEBHOOK_URL not set in .env — skipping push."
    payload = _build_payload_v1(lead)
    return _http_post(url, payload, timeout=timeout)


def push_leads_to_crm(leads: list[dict], timeout: int = 10) -> dict:
    """
    Bulk-push multiple dashboard leads (v1.0 schema).
    Stops after 5 consecutive failures.

    Returns: {"success": int, "failed": int, "errors": [(lead_id, reason), ...]}
    """
    success = 0
    failed  = 0
    errors: list[tuple] = []
    consecutive_failures = 0

    for lead in leads:
        if consecutive_failures >= 5:
            errors.append((lead.get("id"), "Aborted: 5 consecutive failures"))
            failed += 1
            continue
        ok, reason = push_lead_to_crm(lead, timeout=timeout)
        if ok:
            success += 1
            consecutive_failures = 0
        else:
            failed += 1
            consecutive_failures += 1
            errors.append((lead.get("id"), reason))

    return {"success": success, "failed": failed, "errors": errors}


# ---------------------------------------------------------------------------
# Public API — Full batch export (Section 3 complete flow)
# Fetches directly from DB, pushes v2.0 payloads, stamps exported_at.
# ---------------------------------------------------------------------------

def push_leads_batch_from_db(
    db_path: Optional[Path] = None,
    timeout: int = 10,
) -> dict:
    """
    Full Section 3 CRM export flow:
      1. Connect to leads.db
      2. Run the Section 3 multi-join query for un-exported QUALIFIED leads
      3. Build a v2.0 payload for each lead
      4. POST to CRM_WEBHOOK_URL
      5. Stamp exported_at = CURRENT_TIMESTAMP on each successfully pushed lead
      6. Return a summary dict

    Args:
        db_path: Path to leads.db (defaults to T-tools/leads.db next to this file)
        timeout: HTTP timeout per request in seconds

    Returns:
        {
          "success": int,
          "failed":  int,
          "skipped": int,         # leads fetched but not yet attempted (circuit breaker)
          "errors":  [(lead_id, reason), ...],
          "exported_lead_ids": [int, ...]
        }
    """
    url = _crm_url()
    if not url:
        return {
            "success": 0, "failed": 0, "skipped": 0,
            "errors": [(None, "CRM_WEBHOOK_URL not set in .env")],
            "exported_lead_ids": [],
        }

    target_db = db_path or _DB
    success   = 0
    failed    = 0
    skipped   = 0
    errors: list[tuple]       = []
    exported_ids: list[int]   = []
    consecutive_failures      = 0

    try:
        conn = sqlite3.connect(str(target_db))
        conn.execute("PRAGMA journal_mode=WAL")
        leads = get_leads_for_crm_export(conn)
    except Exception as e:  # noqa: BLE001
        return {
            "success": 0, "failed": 0, "skipped": 0,
            "errors": [(None, f"DB error: {e}")],
            "exported_lead_ids": [],
        }

    for lead in leads:
        lead_id = lead["hunter_lead_id"]

        # Circuit breaker — abort remaining leads after 5 consecutive failures
        if consecutive_failures >= 5:
            skipped += 1
            errors.append((lead_id, "Skipped: circuit breaker (5 consecutive failures)"))
            continue

        payload = _build_payload_v2(lead)
        ok, reason = _http_post(url, payload, timeout=timeout)

        if ok:
            # Stamp exported_at atomically per lead
            try:
                conn.execute(
                    "UPDATE leads SET exported_at = CURRENT_TIMESTAMP,"
                    "  last_updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (lead_id,),
                )
                conn.commit()
                exported_ids.append(lead_id)
            except Exception as db_err:  # noqa: BLE001
                # Push succeeded but DB stamp failed — log as partial error
                errors.append((lead_id, f"Push OK but DB stamp failed: {db_err}"))
            success += 1
            consecutive_failures = 0
        else:
            failed += 1
            consecutive_failures += 1
            errors.append((lead_id, reason))

    try:
        conn.close()
    except Exception:
        pass

    return {
        "success":           success,
        "failed":            failed,
        "skipped":           skipped,
        "errors":            errors,
        "exported_lead_ids": exported_ids,
    }
