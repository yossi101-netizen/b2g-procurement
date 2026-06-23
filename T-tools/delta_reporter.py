"""
KritiKaal Leads Hunter — Post-Run Delta Report Generator
File: T-tools/delta_reporter.py

Responsibilities (SRP boundary):
  - After every pipeline run, generate a Markdown summary of new results
  - Save to M-memory/delta_report_YYYY-MM-DD_HH-MM.md
  - Optionally build a wa.me self-notification link for the operator
    (requires OPERATOR_WHATSAPP in .env)

Called from:
  - live_run.main() after export_leads() completes

This module does NOT:
  - Write to SQLite
  - Send any messages
  - Make network requests
  - Block the pipeline (all errors are caught and logged non-fatally)
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote as _url_quote

_HERE    = Path(__file__).parent.resolve()
_ROOT    = _HERE.parent
_DB      = _HERE / "leads.db"
_MEMORY  = _ROOT / "M-memory"
_HISTORY = _MEMORY / "run_history.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_run_history() -> list[dict]:
    if not _HISTORY.exists():
        return []
    try:
        data = json.loads(_HISTORY.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _latest_run_meta() -> dict:
    history = _load_run_history()
    if not history:
        return {}
    return sorted(history, key=lambda r: r.get("run_at", ""), reverse=True)[0]


def _penultimate_run_at() -> Optional[str]:
    """Return run_at of the second-most-recent run (the previous run cutoff)."""
    history = _load_run_history()
    if len(history) < 2:
        return None
    sorted_runs = sorted(history, key=lambda r: r.get("run_at", ""), reverse=True)
    return sorted_runs[1].get("run_at")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_delta_report(db_path: Optional[str] = None) -> Path:
    """
    Generate a Markdown delta report for the most recent pipeline run.

    Opens its own read-only SQLite connection (safe to call after live_run
    closes its connection). Writes to M-memory/delta_report_YYYY-MM-DD_HH-MM.md.

    Returns the path to the written file.
    """
    db_file  = Path(db_path) if db_path else _DB
    now      = datetime.now()
    filename = f"delta_report_{now.strftime('%Y-%m-%d_%H-%M')}.md"
    _MEMORY.mkdir(exist_ok=True)
    out_path = _MEMORY / filename

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row

    try:
        run_meta = _latest_run_meta()
        cutoff   = _penultimate_run_at()

        # ── New Class A leads ────────────────────────────────────────────
        if cutoff:
            new_a_rows = conn.execute(
                """
                SELECT l.domain, l.entity_name, l.whatsapp,
                       MAX(lc.confidence) AS confidence,
                       GROUP_CONCAT(DISTINCT ls.vector) AS sources
                FROM   leads l
                LEFT   JOIN lead_classifications lc ON lc.lead_id = l.id
                LEFT   JOIN lead_sources         ls ON ls.lead_id  = l.id
                WHERE  l.status = 'QUALIFIED_A'
                  AND  l.first_seen_at >= ?
                GROUP  BY l.id
                ORDER  BY confidence DESC NULLS LAST
                """,
                (cutoff,),
            ).fetchall()
            new_b_count = conn.execute(
                """
                SELECT COUNT(*) FROM leads
                WHERE  status = 'QUALIFIED_B_PENDING_VERIFY'
                  AND  first_seen_at >= ?
                """,
                (cutoff,),
            ).fetchone()[0]
            new_bl_count = conn.execute(
                "SELECT COUNT(*) FROM domain_blacklist WHERE added_at >= ?",
                (cutoff,),
            ).fetchone()[0]
        else:
            # First ever run — show top 20 Class A as a welcome report
            new_a_rows = conn.execute(
                """
                SELECT l.domain, l.entity_name, l.whatsapp,
                       MAX(lc.confidence) AS confidence,
                       GROUP_CONCAT(DISTINCT ls.vector) AS sources
                FROM   leads l
                LEFT   JOIN lead_classifications lc ON lc.lead_id = l.id
                LEFT   JOIN lead_sources         ls ON ls.lead_id  = l.id
                WHERE  l.status = 'QUALIFIED_A'
                GROUP  BY l.id
                ORDER  BY confidence DESC NULLS LAST
                LIMIT  20
                """,
            ).fetchall()
            new_b_count  = 0
            new_bl_count = 0

        new_a = [dict(r) for r in new_a_rows]

        # ── Aggregate stats ──────────────────────────────────────────────
        total_a = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = 'QUALIFIED_A'"
        ).fetchone()[0]
        total_all = conn.execute(
            "SELECT COUNT(*) FROM leads"
        ).fetchone()[0]

    finally:
        conn.close()

    # ── Build Markdown ───────────────────────────────────────────────────
    duration = run_meta.get("duration_seconds", "N/A")
    run_at   = run_meta.get("run_at", now.isoformat())

    lines: list[str] = [
        f"# Delta Report — {now.strftime('%d/%m/%Y %H:%M')}",
        "",
        "## Run Summary",
        f"- **Run timestamp:** {run_at}",
        f"- **Duration:** {duration}s",
        f"- **Total leads in DB:** {total_all}",
        f"- **Total Class A in DB:** {total_a}",
        "",
        "## New This Run",
        f"- **New Class A leads:** {len(new_a)}",
        f"- **New Class B leads:** {new_b_count}",
        f"- **New blacklist entries:** {new_bl_count}",
        "",
    ]

    if new_a:
        lines += [
            "## New Class A Leads",
            "",
            "| Company | Domain | WhatsApp | Confidence | Source |",
            "|---------|--------|----------|------------|--------|",
        ]
        for r in new_a:
            conf   = f"{r['confidence']:.0%}" if r["confidence"] else "—"
            wa     = r["whatsapp"] or "—"
            name   = (r["entity_name"] or r["domain"] or "—")[:35].replace("|", "/")
            domain = (r["domain"] or "—")
            src    = (r["sources"] or "—")
            lines.append(f"| {name} | {domain} | {wa} | {conf} | {src} |")
        lines.append("")
    else:
        lines += ["*No new Class A leads in this run.*", ""]

    lines += [
        "---",
        "*Generated by KritiKaal Leads Hunter — delta_reporter.py*",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def get_operator_wa_link(report_path: Path) -> Optional[str]:
    """
    Build a wa.me self-notification link for the operator.

    Reads OPERATOR_WHATSAPP from environment or .env file.
    Returns None if not configured (silent — non-blocking).
    """
    phone = os.environ.get("OPERATOR_WHATSAPP", "").strip()
    if not phone:
        env_file = _ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPERATOR_WHATSAPP="):
                    phone = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not phone:
        return None

    phone_digits = "".join(c for c in phone if c.isdigit())

    # Build a short summary from the report
    summary = f"KritiKaal Leads Hunter run complete\nReport: {report_path.name}"
    try:
        for line in report_path.read_text(encoding="utf-8").splitlines():
            if "New Class A leads:" in line:
                summary = f"KritiKaal Leads Hunter\n{line.strip('- *')}"
                break
    except OSError:
        pass

    return f"https://wa.me/{phone_digits}?text={_url_quote(summary)}"
