"""
KritiKaal Leads Hunter — False-Positive Cleanup Script
File: T-tools/cleanup_false_positives.py

PURPOSE:
  One-time retroactive cleanup of leads that slipped through the pipeline
  before the Sprint 5 Hotfix tightened Tier 1 disqualification rules.

  Targets two false-positive categories:
    1. RITUAL / RELIGIOUS leads — Tefillin, STa"M, Sifrei Torah, Tashmishei
       Kedusha. Incompatible supply chain (require kosher-certified leather).
    2. ITALY-IDENTITY BRANDS — Businesses whose primary brand promise is
       "Made in Italy" / certified Italian craftsmanship. Supplier switch is
       impossible without destroying brand identity.

  Action taken per matched lead:
    - status       → DISQUALIFIED_C
    - domain       → added to domain_blacklist (reason = HALACHIC or MANUAL)
    - No hard DELETE — keeps audit trail intact.

  After cleanup, re-exports the Excel file so kritikaal_leads_export.xlsx
  reflects the sanitised data.

RUN:
    python T-tools/cleanup_false_positives.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).parent.resolve()
_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))

import sqlite3

from db_init import add_to_blacklist, initialize_schema

_DB = _HERE / "leads.db"

# ---------------------------------------------------------------------------
# Keyword sets — checked against domain (lower) and entity_name (lower)
# ---------------------------------------------------------------------------

# Romanized domain-name fragments (checked against domain string)
_RITUAL_DOMAIN_KEYWORDS: frozenset[str] = frozenset({
    "tefilin", "tefillin", "tfilin", "teffilin",
    "stam", "sofer", "sofrim",
    "kedusha", "kodesh", "kadosh",
    "mezuza", "mezuzot",
    "torahscroll", "sefer-torah",
    "tefila", "tfila",           # prayer items
})

_ITALY_BRAND_DOMAIN_KEYWORDS: frozenset[str] = frozenset({
    "madeinitaly", "made-in-italy", "italianleather",
    "italian-leather", "italiancraft",
})

# Hebrew/English substrings checked against entity_name (lower)
_RITUAL_NAME_KEYWORDS: frozenset[str] = frozenset({
    "תפילין", "תפיל",
    "סת\"מ", 'סת"מ', "סת\u05f4מ",  # STa"M with gershayim variants
    "ספר תורה", "ספרי תורה",
    "מזוזות", "מזוזה",
    "תשמישי קדושה",
    "עור כשר",
    "סופר סת",
})

_ITALY_BRAND_NAME_KEYWORDS: frozenset[str] = frozenset({
    # Only catch TRUE brand-identity claims — not product snippet descriptions.
    # "מיוצר באיטליה" is intentionally excluded: it appears in product titles
    # of legitimate Israeli resellers (QUALIFIED_A importers).
    "certified made in italy",
    "madeinitaly",
    "תוצרת איטליה certified",
    "100% made in italy",
    "certified italian leather",
})


def _matches(value: str | None, keywords: frozenset[str]) -> bool:
    if not value:
        return False
    lower = value.lower()
    return any(kw in lower for kw in keywords)


def _find_false_positives(conn: sqlite3.Connection) -> list[dict]:
    """
    Return rows for leads matching ritual or Italy-identity keywords.
    Excludes leads already DISQUALIFIED_C.
    """
    rows = conn.execute(
        "SELECT id, domain, entity_name, status FROM leads WHERE status != 'DISQUALIFIED_C'"
    ).fetchall()

    hits: list[dict] = []
    for lead_id, domain, entity_name, status in rows:
        reason: str | None = None

        if _matches(domain, _RITUAL_DOMAIN_KEYWORDS) or _matches(entity_name, _RITUAL_NAME_KEYWORDS):
            reason = "HALACHIC"
        elif _matches(domain, _ITALY_BRAND_DOMAIN_KEYWORDS) or _matches(entity_name, _ITALY_BRAND_NAME_KEYWORDS):
            reason = "MANUAL"

        if reason:
            hits.append({
                "id":          lead_id,
                "domain":      domain,
                "entity_name": entity_name,
                "status":      status,
                "bl_reason":   reason,
            })
    return hits


def run_cleanup(dry_run: bool = False) -> int:
    """
    Mark false-positive leads as DISQUALIFIED_C and blacklist their domains.
    Returns the number of leads cleaned.
    """
    conn = sqlite3.connect(str(_DB))
    initialize_schema(conn)

    hits = _find_false_positives(conn)

    if not hits:
        print("No false-positive leads found — database is already clean.")
        conn.close()
        return 0

    print(f"\nFound {len(hits)} false-positive lead(s):\n")
    for h in hits:
        tag = "[RITUAL]" if h["bl_reason"] == "HALACHIC" else "[ITALY-BRAND]"
        name = (h["entity_name"] or "").encode("ascii", errors="replace").decode()
        print(f"  {tag}  id={h['id']:>4}  {h['domain']:<35}  {name}")

    if dry_run:
        print("\n[DRY RUN] No changes written.")
        conn.close()
        return len(hits)

    print("\nApplying cleanup…")
    conn.execute("BEGIN IMMEDIATE")
    try:
        for h in hits:
            conn.execute(
                "UPDATE leads SET status = 'DISQUALIFIED_C', last_updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (h["id"],),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    # Blacklist each domain (commits individually inside add_to_blacklist)
    for h in hits:
        if h["domain"]:
            add_to_blacklist(conn, h["domain"], h["bl_reason"], "human")

    print(f"  OK: {len(hits)} lead(s) marked DISQUALIFIED_C and blacklisted.")
    conn.close()
    return len(hits)


def run_export() -> None:
    """Re-run the exporter to overwrite kritikaal_leads_export.xlsx."""
    import importlib
    spec = importlib.util.spec_from_file_location("exporter", _HERE / "exporter.py")
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    exporter.export_leads()
    print(f"  OK: Excel re-exported -> {_ROOT / 'kritikaal_leads_export.xlsx'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean false-positive leads from leads.db")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report matches without writing any changes")
    parser.add_argument("--no-export", action="store_true",
                        help="Skip re-exporting the Excel file after cleanup")
    args = parser.parse_args()

    cleaned = run_cleanup(dry_run=args.dry_run)

    if cleaned > 0 and not args.dry_run and not args.no_export:
        print("\nRe-exporting Excel…")
        try:
            run_export()
        except Exception as exc:
            print(f"  ⚠ Export failed: {exc}")

    print("\nDone.")


if __name__ == "__main__":
    main()
