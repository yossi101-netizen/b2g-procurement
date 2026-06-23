"""
KritiKaal Leads Hunter — Dry Run Pipeline Test
File: T-tools/test_pipeline.py

Validates the end-to-end flow WITHOUT touching the production database
or making live OpenAI API calls:

  Raw HTML → DomExtractor → Normalization → NLP (Tier 1 + mocked Tier 2)
           → upsert_lead() → in-memory SQLite

Run with:  python T-tools/test_pipeline.py
"""

import asyncio
import io
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure T-tools/ is on the path regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

from db_init import (
    initialize_schema,
    upsert_lead,
    normalize_domain,
)
from scrapers import (
    AgentResult,
    strip_html_to_text,
    extract_whatsapp_numbers,
    extract_company_ids,
    select_best_phone,
    select_best_company_id,
)
from nlp_classifier import (
    classify_lead_full,
    _tier1_check,
    VALID_LLM_STATUSES,
)

# ============================================================
# Formatting helpers
# ============================================================

SEP  = "=" * 66
THIN = "-" * 66

def header(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def section(title: str) -> None:
    print(f"\n{THIN}")
    print(f"  {title}")
    print(THIN)

def ok(msg: str)   -> None: print(f"  [OK]  {msg}")
def info(msg: str) -> None: print(f"        {msg}")
def warn(msg: str) -> None: print(f"  [!!]  {msg}")

# ============================================================
# HTML Fixtures
# ============================================================
# Three representative Israeli business pages.
# Each is designed to exercise a different classification path.

# Fixture A — Class C: explicit English "dropshipping" keyword
# guarantees Tier 1 disqualification with zero OpenAI cost.
FIXTURE_A_HTML = """
<html>
<head><title>SuperDeal Store - מוצרים בזול</title></head>
<body>
<script>var x = 1;</script>
<style>body { font-family: sans-serif; }</style>
<h1>SuperDeal Store - מוצרים במחירים הכי נמוכים</h1>
<p>ברוכים הבאים לחנות שלנו! אנחנו מציעים מגוון עצום של מוצרים.</p>
<p>אנחנו עובדים בשיטת dropshipping עם הספקים הטובים ביותר.</p>
<p>זמן אספקה: 14-28 ימי עסקים. המשלוח מ-AliExpress ישירות אליכם.</p>
<p>יצירת קשר: 054-1234567</p>
<p>כתובת דואר: ת.ד. 1234, תל אביב</p>
<p>אין כתובת עסקית פיזית.</p>
</body>
</html>
""".strip()
FIXTURE_A_META = {
    "entity_name": "SuperDeal Store",
    "domain_raw":  "https://www.superdeal-store.co.il/products/all",
    "vector":      "V1_SERPER",
    "source_url":  "https://www.superdeal-store.co.il",
}

# Fixture B — Class A: Israeli manufacturer in distress.
# Contains ח.פ, WhatsApp, physical address, manufacturer signals,
# and a liquidation signal → high-value KritiKaal target.
FIXTURE_B_HTML = """
<html>
<head><title>מפעל טכנולוגיה ישראלי בע"מ</title></head>
<body>
<h1>מפעל טכנולוגיה ישראלי בע"מ - ציוד תעשייתי מאז 1995</h1>
<p>אנחנו מייצרים ציוד תעשייתי מתקדם בפס ייצור משלנו בפתח תקווה.</p>
<p>כל המוצרים הם ייצור ישראלי מאה אחוז, עם אחריות מלאה.</p>
<p>אנחנו לא שולחים מחו"ל — כל המלאי שלנו מוחזק בישראל.</p>
<p>פירוק מלאי מיוחד! בעקבות פרישת הבעלים נמכר ציוד במחירי עלות.</p>
<p>עוסק מורשה: 514123456</p>
<p>כתובת: רחוב התעשייה 15, פתח תקווה 4951234</p>
<p>משלוח תוך 1-3 ימי עסקים לכל הארץ.</p>
<p>WhatsApp: +972-52-9876543</p>
<p>שעות פעילות: ראשון-חמישי 08:00-17:00</p>
</body>
</html>
""".strip()
FIXTURE_B_META = {
    "entity_name": "מפעל טכנולוגיה ישראלי בע\"מ",
    "domain_raw":  "http://israel-tech-factory.co.il/about",
    "vector":      "V2_SERPAPI",
    "source_url":  "https://serpapi:maps::ChIJ123",
}

# Fixture C — Class B: small independent importer, neutral signals.
# No manufacturer evidence, no dropship evidence.
# Passes Tier 1 → Tier 2 mock returns QUALIFIED_B_PENDING_VERIFY.
FIXTURE_C_HTML = """
<html>
<head><title>Online Shop IL - אלקטרוניקה ואביזרים</title></head>
<body>
<h1>Online Shop IL - חנות אינטרנטית לאלקטרוניקה</h1>
<p>ברוכים הבאים לחנות האינטרנטית שלנו למוצרי אלקטרוניקה ואביזרים.</p>
<p>אנחנו יבואנים קטנים של מוצרים מאיכות גבוהה מאירופה.</p>
<p>יש לנו מחסן קטן ומלאי בתל אביב.</p>
<p>משלוח תוך 5-7 ימי עסקים לכל הארץ עם חברת שליחויות.</p>
<p>החזרות ותנאי אחריות לפי חוק הגנת הצרכן.</p>
<p>טלפון ו-WhatsApp: 050-7654321</p>
<p>שירות לקוחות: info@onlineshop-il.co.il</p>
</body>
</html>
""".strip()
FIXTURE_C_META = {
    "entity_name": "Online Shop IL",
    "domain_raw":  "https://www.onlineshop-il.co.il",
    "vector":      "V1_SERPER",
    "source_url":  "https://www.onlineshop-il.co.il",
}

FIXTURES = [
    (FIXTURE_A_HTML, FIXTURE_A_META, "A — Class C Dropshipper"),
    (FIXTURE_B_HTML, FIXTURE_B_META, "B — Class A Manufacturer in Distress"),
    (FIXTURE_C_HTML, FIXTURE_C_META, "C — Class B Small Importer"),
]

# ============================================================
# OpenAI mock factory
# ============================================================

def _make_openai_response(status: str, confidence: float, signals: list[str]) -> MagicMock:
    """Return a mock object shaped like openai.ChatCompletion."""
    payload = json.dumps({
        "status":     status,
        "confidence": confidence,
        "signals":    signals,
        "reasoning":  f"Mock classification: {status}",
    })
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = payload
    return mock_resp


def build_mock_openai_client() -> MagicMock:
    """
    Return a mock AsyncOpenAI client whose chat.completions.create
    returns pre-scripted responses in call order.

    Call 1 → Fixture B: QUALIFIED_A  (0.92)
    Call 2 → Fixture C: QUALIFIED_B_PENDING_VERIFY  (0.78)

    Fixture A never reaches Tier 2 (Tier 1 disqualifies it).
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=[
        _make_openai_response(
            "QUALIFIED_A", 0.92,
            ["מייצרים", "פירוק מלאי", "פס ייצור", "עוסק מורשה"],
        ),
        _make_openai_response(
            "QUALIFIED_B_PENDING_VERIFY", 0.78,
            ["יבואנים קטנים", "מחסן בישראל"],
        ),
    ])
    return mock_client


# ============================================================
# In-memory database setup
# ============================================================

def build_test_db() -> sqlite3.Connection:
    """
    Create an in-memory SQLite connection and initialize the full schema.
    Uses isolation_level=None to match db_init transaction contract.
    """
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL mode is not applicable to :memory: but does not error — SQLite
    # silently returns 'memory' instead of 'wal'.
    initialize_schema(conn)
    return conn


# ============================================================
# Main test coroutine
# ============================================================

async def run_dry_run() -> None:

    header("ISRAEL-HUNTER V3 — DRY RUN PIPELINE TEST")
    print("  Database : :memory: (no file I/O)")
    print("  OpenAI   : MOCKED  (no API charges)")
    print("  Scrapers : MOCKED  (no HTTP requests)")

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------
    conn        = build_test_db()
    mock_client = build_mock_openai_client()
    all_passed  = True

    # --------------------------------------------------------
    # STEP 1 — DomExtractor: strip HTML → plain text
    # --------------------------------------------------------
    section("STEP 1 — DomExtractor: Strip HTML → Plain Text")

    stripped: dict[str, str] = {}
    for html, meta, label in FIXTURES:
        text = strip_html_to_text(html)
        stripped[label] = text
        # Verify script/style tags were removed
        has_script = "<script>" in text or "<style>" in text
        info(f"Fixture {label[:1]}: {len(text)} chars | "
             f"tags removed={'YES' if not has_script else 'NO'}")
        if has_script:
            warn("Script/style tags found in stripped text!")
            all_passed = False

    ok("HTML stripped to plain text — no tag residue")

    # --------------------------------------------------------
    # STEP 2 — Core data extraction
    # --------------------------------------------------------
    section("STEP 2 — Core Data Extraction (WhatsApp + ח.פ + Domain)")

    extracted: list[AgentResult] = []
    for html, meta, label in FIXTURES:
        text   = stripped[label]
        domain = normalize_domain(meta["domain_raw"])
        phones = extract_whatsapp_numbers(html)
        wa     = select_best_phone(phones)
        cids   = extract_company_ids(html)
        cid    = select_best_company_id(cids)

        result = AgentResult(
            entity_name=      meta["entity_name"],
            domain=           domain,
            whatsapp=         wa,
            company_id=       cid,
            raw_text=         text,
            source_url=       meta["source_url"],
            vector=           meta["vector"],
        )
        extracted.append(result)

        info(f"Fixture {label[:1]}:")
        info(f"  domain     = {domain}")
        info(f"  whatsapp   = {wa   or 'None (not found)'}")
        info(f"  company_id = {cid  or 'None (not found)'}")

    # Assertions on expected extractions
    assert extracted[0].domain     == "superdeal-store.co.il",        "Domain A mismatch"
    assert extracted[1].domain     == "israel-tech-factory.co.il",    "Domain B mismatch"
    assert extracted[1].whatsapp   == "972529876543",                  "WhatsApp B mismatch"
    assert extracted[1].company_id == "514123456",                     "Company ID B mismatch"
    assert extracted[2].whatsapp   == "972507654321",                  "WhatsApp C mismatch"
    ok("Domain normalization correct")
    ok("WhatsApp normalization correct (972XXXXXXXXX format)")
    ok("Company ID extraction correct (9 digits)")

    # --------------------------------------------------------
    # STEP 3 — NLP Tier 1: local heuristics
    # --------------------------------------------------------
    section("STEP 3 — NLP Tier 1: Local Heuristics (zero-cost)")

    tier1_results: list[tuple] = []
    openai_calls_expected = 0

    for result, (_, _, label) in zip(extracted, FIXTURES):
        t1 = _tier1_check(result.raw_text)
        tier1_results.append(t1)
        if t1:
            info(f"Fixture {label[:1]}: TIER 1 FIRED → {t1[0]} "
                 f"(confidence={t1[1]}) — OpenAI NOT called")
        else:
            info(f"Fixture {label[:1]}: TIER 1 PASS → proceeding to Tier 2")
            openai_calls_expected += 1

    # Fixture A must be caught by Tier 1 (contains "dropshipping")
    assert tier1_results[0] is not None,                           "Fixture A should fail Tier 1"
    assert tier1_results[0][0] == "DISQUALIFIED_C",                "Fixture A should be DISQUALIFIED_C"
    # Fixtures B and C must pass Tier 1
    assert tier1_results[1] is None,                               "Fixture B should pass Tier 1"
    assert tier1_results[2] is None,                               "Fixture C should pass Tier 1"
    ok("Tier 1 correctly disqualified Fixture A without calling OpenAI")
    ok(f"Tier 2 required for {openai_calls_expected} fixture(s)")

    # --------------------------------------------------------
    # STEP 4 — NLP Tier 2: mocked OpenAI call
    # --------------------------------------------------------
    section("STEP 4 — NLP Tier 2: OpenAI Mock (JSON mode)")

    final_classifications: list[tuple[str, float, list, str]] = []

    for result, (_, _, label), t1 in zip(extracted, FIXTURES, tier1_results):
        if t1:
            # Tier 1 already classified — no Tier 2 needed
            status, confidence = t1
            final_classifications.append((status, confidence, [], "tier1"))
            info(f"Fixture {label[:1]}: skipped (Tier 1 result reused)")
        else:
            status, confidence, signals, model_v = await classify_lead_full(
                result.raw_text,
                client=mock_client,
                model="gpt-4o-mini",
            )
            final_classifications.append((status, confidence, signals, model_v))
            info(f"Fixture {label[:1]}:")
            info(f"  status     = {status}")
            info(f"  confidence = {confidence}")
            info(f"  signals    = {signals}")
            info(f"  model      = {model_v}")

            # Enum guard: status must be in VALID_LLM_STATUSES
            assert status in VALID_LLM_STATUSES, \
                f"INVALID STATUS from LLM: {status!r} — would cause SQLite IntegrityError!"

    # Verify mock was called exactly the expected number of times
    actual_calls = mock_client.chat.completions.create.call_count
    assert actual_calls == openai_calls_expected, \
        f"Expected {openai_calls_expected} OpenAI calls, got {actual_calls}"

    assert final_classifications[0][0] == "DISQUALIFIED_C",             "Fixture A final status"
    assert final_classifications[1][0] == "QUALIFIED_A",                "Fixture B final status"
    assert final_classifications[2][0] == "QUALIFIED_B_PENDING_VERIFY", "Fixture C final status"

    ok(f"OpenAI mock called exactly {actual_calls} time(s) — "
       f"Fixture A correctly saved API cost")
    ok("All returned statuses are valid db_schema.sql enum values")
    ok("Enum guard validated — no SQLite CHECK violations possible")

    # --------------------------------------------------------
    # STEP 5 — DB Upsert: write to in-memory SQLite
    # --------------------------------------------------------
    section("STEP 5 — upsert_lead(): Write to In-Memory SQLite")

    lead_ids: list[int] = []
    for result, (_, _, label), (status, confidence, signals, _) in \
            zip(extracted, FIXTURES, final_classifications):

        lead_data = result.to_lead_dict(status=status)
        try:
            lead_id = upsert_lead(
                conn,
                lead_data,
                vector=result.vector,
                source_url=result.source_url,
                raw_snippet=result.raw_text[:300],
            )
            lead_ids.append(lead_id)
            ok(f"Fixture {label[:1]} upserted → lead_id={lead_id} "
               f"status={status}")
        except Exception as exc:
            warn(f"Fixture {label[:1]} FAILED: {exc}")
            all_passed = False
            lead_ids.append(None)

    assert None not in lead_ids, "One or more upserts raised an exception"
    assert len(set(lead_ids)) == 3, "Expected 3 distinct lead IDs"

    # --------------------------------------------------------
    # STEP 6 — Deduplication test
    # --------------------------------------------------------
    section("STEP 6 — Deduplication: Re-insert Fixture B (same domain)")

    # Simulate re-discovering the same manufacturer with updated WhatsApp
    duplicate_data = {
        "entity_name":      "מפעל טכנולוגיה ישראלי בע\"מ",
        "domain":           "israel-tech-factory.co.il",  # SAME domain
        "whatsapp":         "972541111222",               # NEW phone (would enrich)
        "company_id":       None,                         # not found this time
        "physical_address": None,
        "status":           "ENRICHED",
        "legal_flag":       None,
    }
    try:
        dup_id = upsert_lead(
            conn,
            duplicate_data,
            vector="V1_SERPER",
            source_url="https://serper::duplicate-query",
            raw_snippet="duplicate discovery",
        )
        # Must return the SAME lead_id as the original Fixture B insert
        assert dup_id == lead_ids[1], \
            f"Dedup failed: expected lead_id={lead_ids[1]}, got {dup_id}"
        ok(f"Re-insert returned existing lead_id={dup_id} (no duplicate created)")
    except Exception as exc:
        warn(f"Deduplication test FAILED: {exc}")
        all_passed = False

    # Verify DB has exactly 3 leads (not 4)
    row_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    assert row_count == 3, f"Expected 3 leads in DB, found {row_count}"
    ok(f"DB contains exactly {row_count} lead(s) — no phantom duplicates")

    # Verify source provenance: Fixture B now has 2 source records
    src_count = conn.execute(
        "SELECT COUNT(*) FROM lead_sources WHERE lead_id = ?",
        (lead_ids[1],)
    ).fetchone()[0]
    ok(f"Fixture B has {src_count} source record(s) in lead_sources "
       f"(original + re-discovery)")

    # --------------------------------------------------------
    # STEP 7 — Final DB verification
    # --------------------------------------------------------
    section("STEP 7 — Final Database State")

    rows = conn.execute(
        """
        SELECT l.id, l.entity_name, l.domain, l.whatsapp, l.company_id,
               l.status, l.is_stale, l.legal_flag,
               COUNT(s.id) AS source_count
        FROM leads l
        LEFT JOIN lead_sources s ON s.lead_id = l.id
        GROUP BY l.id
        ORDER BY l.id
        """
    ).fetchall()

    print()
    print(f"  {'ID':<4} {'STATUS':<30} {'DOMAIN':<35} {'SOURCES'}")
    print(f"  {'--':<4} {'------':<30} {'------':<35} {'-------'}")
    for row in rows:
        print(
            f"  {row['id']:<4} "
            f"{row['status']:<30} "
            f"{row['domain']:<35} "
            f"{row['source_count']}"
        )
    print()
    info(f"Total leads  : {len(rows)}")
    info(f"  QUALIFIED_A                : "
         f"{sum(1 for r in rows if r['status'] == 'QUALIFIED_A')}")
    info(f"  QUALIFIED_B_PENDING_VERIFY : "
         f"{sum(1 for r in rows if r['status'] == 'QUALIFIED_B_PENDING_VERIFY')}")
    info(f"  DISQUALIFIED_C             : "
         f"{sum(1 for r in rows if r['status'] == 'DISQUALIFIED_C')}")
    info(f"  Stale (is_stale=1)         : "
         f"{sum(1 for r in rows if r['is_stale'] == 1)}")

    total_sources = conn.execute(
        "SELECT COUNT(*) FROM lead_sources"
    ).fetchone()[0]
    info(f"Total source records in lead_sources: {total_sources}")

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------
    print(f"\n{SEP}")
    if all_passed:
        print("  ALL TESTS PASSED")
        print("  Pipeline flow confirmed:")
        print("    HTML → DomExtractor → Normalization →")
        print("    NLP Tier 1 (heuristics) → NLP Tier 2 (mock LLM) →")
        print("    upsert_lead() → SQLite :memory: — zero IntegrityErrors")
    else:
        print("  SOME TESTS FAILED — see warnings above")
    print(SEP)

    conn.close()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    asyncio.run(run_dry_run())
