"""
KritiKaal Command Center — Shared Navigation & Metrics
Canonical path constants and cross-system metrics for the hub header.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# CANONICAL PATHS  (resolved relative to this file's location)
# kritikaal-hub/
#   shared/nav.py         ← this file
# ../T-tools/             ← Leads Hunter
# ../the-system-v8/…/quote-engine/ ← Quote Engine
# ─────────────────────────────────────────────────────────────────
WORKSPACE    = Path(__file__).parent.parent.parent.resolve()  # …/yossi-workspace/
LEADS_HUNTER = WORKSPACE / "T-tools"
QUOTE_ENGINE = (
    WORKSPACE
    / "the-system-v8"
    / "the-system-v8"
    / "T-tools"
    / "quote-engine"
)
LEADS_DB  = LEADS_HUNTER / "leads.db"
QUOTES_DB = QUOTE_ENGINE  / "quotes.db"

# ─────────────────────────────────────────────────────────────────
# CORPORATE GIFTS  (isolated from core MM business files)
# All KK-CG-*.yaml product files live here — never in quote-engine/products/
# ─────────────────────────────────────────────────────────────────
HUB_ROOT                 = Path(__file__).parent.parent.resolve()
CORPORATE_GIFTS_DIR      = HUB_ROOT / "corporate_gifts"
CORPORATE_GIFTS_PRODUCTS = CORPORATE_GIFTS_DIR / "products"


# ─────────────────────────────────────────────────────────────────
# QUICK-CONNECT HELPERS  (read-only, WAL-safe)
# ─────────────────────────────────────────────────────────────────

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ─────────────────────────────────────────────────────────────────
# CROSS-SYSTEM METRICS  (drives the hub header bar)
# ─────────────────────────────────────────────────────────────────

def hub_metrics() -> dict:
    """
    Returns a single dict of metrics drawn from both databases.
    All queries are READ-ONLY — safe to call any time.
    Returns zeroed dict on any error so the header never crashes the app.
    """
    result = {
        "qualified_leads":   0,
        "total_leads":       0,
        "quotes_this_week":  0,
        "quotes_total":      0,
        "pipeline_usd":      0.0,
        "avg_gp_pct":        0.0,
        "accepted_quotes":   0,
    }

    # ── Leads metrics ────────────────────────────────────────────
    try:
        with _connect(LEADS_DB) as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status IN ('QUALIFIED_A','QUALIFIED_B_PENDING_VERIFY')
                             THEN 1 ELSE 0 END) AS qualified
                FROM leads
            """).fetchone()
            if row:
                result["total_leads"]     = row["total"] or 0
                result["qualified_leads"] = row["qualified"] or 0
    except Exception:
        pass  # DB not accessible — degrade gracefully

    # ── Quote metrics ─────────────────────────────────────────────
    try:
        with _connect(QUOTES_DB) as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE
                        WHEN created_at >= datetime('now', '-7 days')
                        THEN 1 ELSE 0 END) AS this_week,
                    COALESCE(SUM(CASE WHEN status='issued'   THEN total_usd ELSE 0 END), 0) AS pipeline,
                    COALESCE(AVG(gp_pct), 0) AS avg_gp,
                    SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) AS accepted
                FROM quotes
            """).fetchone()
            if row:
                result["quotes_total"]    = row["total"]     or 0
                result["quotes_this_week"]= row["this_week"] or 0
                result["pipeline_usd"]    = row["pipeline"]  or 0.0
                result["avg_gp_pct"]      = row["avg_gp"]    or 0.0
                result["accepted_quotes"] = row["accepted"]  or 0
    except Exception:
        pass  # quotes.db may not exist yet

    return result
