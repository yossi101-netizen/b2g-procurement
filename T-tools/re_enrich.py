"""
KritiKaal Leads Hunter — Re-Enrichment Runner
File: T-tools/re_enrich.py

PURPOSE
-------
One-time (and repeatable) pass that retries phone number discovery for
QUALIFIED_A and QUALIFIED_B_PENDING_VERIFY leads that have no WhatsApp
number in the database.

The main pipeline's Phase 2A only enriches leads found in the *current* run.
This script covers the historical backlog — leads that were classified in
prior runs before contact-enrichment was added, or that simply had no
contact page at the time.

HOW IT WORKS
------------
For each phoneless qualified lead:
  1. Probe up to 3 contact/about page slugs (Hebrew + English)
  2. Run the same regex phone extractor used in Phase 2A
  3. If a phone is found: write to DB via update_contact_fields() (COALESCE
     guard ensures we never overwrite an existing number)
  4. Print per-lead result; commit after every successful write

No Serper quota consumed — pure HTML fetches only.
No NLP/OpenAI calls — zero API cost.

USAGE
-----
    cd T-tools && python re_enrich.py

    # Dry-run (no DB writes, shows what would be found):
    cd T-tools && python re_enrich.py --dry-run

    # Limit to N leads (useful for testing):
    cd T-tools && python re_enrich.py --limit 10

EXIT CODES
----------
  0 — completed normally (even if 0 phones found)
  1 — fatal error (missing API keys, DB not found, etc.)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path + env setup (mirrors live_run.py pattern)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    from dotenv import load_dotenv
    _env = _HERE / ".env"
    load_dotenv(dotenv_path=_env if _env.exists() else _HERE.parent / ".env")
except Exception:
    pass

import io
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import aiohttp

from db_init import get_connection, update_contact_fields
from scrapers import enrich_contact_pages

_DB_PATH = str(_HERE / "leads.db")

# ---------------------------------------------------------------------------
# Candidate query
# ---------------------------------------------------------------------------

_QUERY = """
    SELECT id, domain, entity_name
    FROM   leads
    WHERE  status IN ('QUALIFIED_A', 'QUALIFIED_B_PENDING_VERIFY')
    AND    (whatsapp IS NULL OR whatsapp = '')
    ORDER  BY status DESC, id ASC
"""


# ---------------------------------------------------------------------------
# Core async runner
# ---------------------------------------------------------------------------

async def _run(dry_run: bool, limit: int | None) -> dict:
    conn   = get_connection(_DB_PATH)
    rows   = conn.execute(_QUERY).fetchall()

    if limit is not None:
        rows = rows[:limit]

    total     = len(rows)
    found     = 0
    not_found = 0

    print(f"\n  Re-Enrichment Pass — {total} phoneless qualified lead(s)")
    print(f"  Mode: {'DRY-RUN (no writes)' if dry_run else 'LIVE'}")
    print(f"{'─' * 60}")

    if not rows:
        print("  Nothing to do.")
        conn.close()
        return {"total": 0, "found": 0, "not_found": 0}

    async with aiohttp.ClientSession() as session:
        for idx, (lead_id, domain, entity_name) in enumerate(rows, start=1):
            label = (entity_name or domain)[:50]
            print(f"  [{idx:>3}/{total}] {label:<50}  ({domain})")

            phone = await enrich_contact_pages(session, domain)

            if phone:
                found += 1
                if dry_run:
                    print(f"         → FOUND {phone}  [dry-run — not written]")
                else:
                    conn.execute("BEGIN IMMEDIATE")
                    try:
                        update_contact_fields(conn, lead_id, phone)
                        conn.commit()
                    except Exception as exc:
                        conn.rollback()
                        print(f"         ! DB write failed: {exc}")
                        continue
                    print(f"         → FOUND {phone}  ✓ written")
            else:
                not_found += 1
                print("         → no phone found")

    conn.close()

    print(f"\n{'-' * 60}")
    print(f"  Results   : {found} found / {not_found} not found / {total} total")
    if not dry_run and found:
        print(f"  DB updated: {found} lead(s) now have WhatsApp numbers")
    print()

    return {"total": total, "found": found, "not_found": not_found}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-enrich phoneless QUALIFIED_A/B leads with contact phone numbers."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print results without writing to the database."
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Process at most N leads (useful for quick testing)."
    )
    args = parser.parse_args()

    try:
        asyncio.run(_run(dry_run=args.dry_run, limit=args.limit))
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        sys.exit(0)
    except Exception as exc:
        print(f"\n  FATAL: {exc}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
