"""
procurement_ingest.py — B2G Israeli-tender intelligence (DOM-verified 2026-06-23)

Top-of-funnel only: scrape mr.gov.il, apply Hebrew keyword filter, surface
manufacturing-relevant tenders for human evaluation. No automated financial
scoring — the operator handles penalty math, bond assessment, and bid decisions.

Pipeline: ingest (scrape + filter + store) → review (readable output for analyst)

  deps: pip install requests selectolax
  optional: pip install playwright (Akamai JS-challenge fallback)
"""
import re, time, sqlite3, json, os
from typing import Optional
from datetime import datetime, timezone
import requests
from selectolax.parser import HTMLParser

# ══════════════════════════════════════════════════════════════════
# CONFIG (locked from live DOM capture 2026-06-23)
# ══════════════════════════════════════════════════════════════════
MR_HOST    = "https://mr.gov.il"
STOREFRONT = "/ilgstorefront/he"
SEARCH_URL = MR_HOST + STOREFRONT + "/search/"
ACTIVE_TENDERS_Q = ":updateDate:archive:false"
SCOPE_TENDER     = "TENDER"

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "tenders.db")

BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
    "Referer": MR_HOST + STOREFRONT + "/",
    "Connection": "keep-alive",
}

# ══════════════════════════════════════════════════════════════════
# HEBREW KEYWORD MATRIX (from Master Context v7.0)
# ══════════════════════════════════════════════════════════════════
def _heb(root): return rf"(?:[והבכלמש]{{0,2}})?{root}"

INCLUDE_ROOTS = [
    "עור","מוצרי עור","תיק","תיקים","חגורה","חגורות","ארנק","נרתיק","נרתיקים","רצועות",
    "טקסטיל","מדים","ביגוד","בגדי עבודה","חולצות","מעילים","כובעים","ריפוד","אריג",
    "הנעלה","נעליים","מגפיים","נעלי בטיחות","נעלי עבודה",
    "ציוד מיגון","אפוד","אפודים","ציוד טקטי","אמצעי מיגון","נשאים","אביזרי שטח",
    "מוצרי קידום","מתנות","שי לעובדים","מזכרות","פריטי מיתוג",
    "מזוודות","כיסויים","מארזים",
]
EXCLUDE_ROOTS = [
    "מחשוב","תוכנה","שירותי מידע","סייבר","רישוי תוכנה","חומרה","תקשורת נתונים",
    "בנייה","בינוי","שיפוץ","תשתיות","עבודות עפר","חשמל","אינסטלציה","אחזקת מבנים",
    "ייעוץ","ליווי","אדריכלות","תכנון","ביקורת","ראיית חשבון","שירותים משפטיים",
    "הסעדה","קייטרינג","מזון","ארוחות","מטבח",
    "כוח אדם","השמה","מיקור חוץ",
    "רכב","כלי רכב","הסעות","ליסינג","תחבורה",
    "ניקיון","גינון","שמירה","אבטחה","אחזקה",
    "עורכי דין","ייצוג משפטי",
    "עורקים","כלי דם","צנתור",
]
INCLUDE_RX = re.compile("|".join(_heb(r) for r in INCLUDE_ROOTS))
EXCLUDE_RX = re.compile("|".join(_heb(r) for r in EXCLUDE_ROOTS))

SEARCH_TERMS = ["עור", "מדים", "ביגוד", "טקסטיל", "הנעלה", "נעליים",
                "ציוד מיגון", "אפוד", "תיקים", "חגורות", "מוצרי קידום", "מתנות"]

CATEGORY_MAP = {
    "leather_slg":  ["עור", "ארנק", "חגורה", "נרתיק", "רצועות", "יריעות עור"],
    "uniforms":     ["מדים", "ביגוד", "טקסטיל", "חולצות", "בגדי עבודה"],
    "footwear":     ["הנעלה", "נעליים", "מגפיים"],
    "tactical":     ["מיגון", "אפוד", "טקטי", "נשאים"],
    "promotional":  ["קידום", "מתנות", "שי", "מזכרות", "מיתוג"],
    "bags_cases":   ["תיק", "מזוודות", "מארזים"],
}

# ══════════════════════════════════════════════════════════════════
# DOM PARSING (verified against live HTML 2026-06-23)
# ══════════════════════════════════════════════════════════════════
CODE_RE = re.compile(r"/p/(\d{6,})")

def _normalize(text: str) -> str:
    text = re.sub(r"[֑-ׇ]", "", text or "")
    return re.sub(r"\s+", " ", text).strip()

def _parse_date(s: str) -> Optional[str]:
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s or "")
    if not m: return None
    return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

def _parse_list_page(html: str) -> list[dict]:
    tree = HTMLParser(html)
    stubs, seen = [], set()
    for container in tree.css("div.result-container"):
        link = container.css_first("a[href*='/p/']")
        if not link: continue
        href = link.attributes.get("href", "")
        m = CODE_RE.search(href)
        if not m or m.group(1) in seen: continue
        code = m.group(1); seen.add(code)

        title_el = container.css_first("h2.search-results-content-head")
        title = title_el.text().strip() if title_el else ""

        details = container.css_first("div.details-wrapper")
        block = details.text(separator=" ") if details else ""

        publisher = ""
        pm = re.search(r"שם המפרסם\s*:?\s*(.+?)(?:מס|$)", block)
        if pm: publisher = pm.group(1).strip()

        status = ""
        sm = re.search(r"סטטוס\s*:?\s*(.+?)(?:\||מס|$)", block)
        if sm: status = sm.group(1).strip()

        pub_date = _parse_date(re.search(r"תאריך פרסום\s*:?\s*(\S+)", block).group(1)) if re.search(r"תאריך פרסום", block) else None
        deadline_m = re.search(r"מועד אחרון להגשה\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})", block)
        deadline = _parse_date(deadline_m.group(1)) if deadline_m else None

        proc_num = ""
        pn = re.search(r"מס.?\s*הליך\s*:?\s*([\w/]+)", block)
        if pn: proc_num = pn.group(1).strip()

        stubs.append({
            "tender_id": code, "title": title,
            "url": MR_HOST + href if href.startswith("/") else href,
            "publisher": publisher, "status": status,
            "pub_date": pub_date, "deadline": deadline,
            "proc_number": proc_num,
        })
    return stubs

_debug_pagination_logged = False

def _has_next_page(html: str) -> Optional[str]:
    global _debug_pagination_logged
    tree = HTMLParser(html)

    # Strategy 1: Look for href patterns containing page/offset numbers or search query
    page_link_patterns = []
    search_params = []

    for a in tree.css("a[href]"):
        href = a.attributes.get("href", "")
        text = (a.text() or "").strip()

        # Capture links with pagination-related parameters
        if href and any(param in href.lower() for param in ["page=", "offset=", "start=", "rows="]):
            page_link_patterns.append((href, text))

        # Also look for search results links (contain the search query or storefront path)
        if href and "/search/" in href.lower():
            search_params.append((href, text))

    # Debug: log first occurrence of search links
    if not _debug_pagination_logged and (page_link_patterns or search_params):
        print(f"      [DEBUG] Found pagination patterns:")
        for href, text in (page_link_patterns + search_params)[:5]:
            print(f"        href: {href[:120]}")
        _debug_pagination_logged = True

    # Prefer explicit page-param links
    if page_link_patterns:
        for href, text in page_link_patterns:
            # Prefer ones with "next" in text
            if any(x in text.lower() for x in ("הבא", "next", "»", "→")):
                return MR_HOST + href if href.startswith("/") else href
        # Return last pagination link
        href = page_link_patterns[-1][0]
        return MR_HOST + href if href.startswith("/") else href

    # If search links exist but no page params, pagination might be JS-based
    if search_params:
        # Try to find a "next" version of the search
        for href, text in search_params:
            if any(x in text.lower() for x in ("הבא", "next", "»", "→")):
                return MR_HOST + href if href.startswith("/") else href

    # Strategy 2: Try standard pagination selectors
    selectors = [
        "a.pagination-next",
        "a[rel='next']",
        "a.next",
        "a.btn-next",
        "a[aria-label*='next']",
        "li.next a",
        "span.next a",
    ]
    for selector in selectors:
        for a in tree.css(selector):
            href = a.attributes.get("href", "")
            if href: return MR_HOST + href if href.startswith("/") else href

    # Strategy 3: Look for any link containing "next" patterns (Hebrew + English)
    next_patterns = ("הבא", "הבא »", "»", ">", "next", "Next", "→")
    for a in tree.css("a[href]"):
        t = (a.text() or "").strip()
        if t in next_patterns:
            href = a.attributes.get("href", "")
            if href: return MR_HOST + href if href.startswith("/") else href

    return None

def _extract_attachment_urls(html: str) -> list[dict]:
    tree = HTMLParser(html)
    attachments = []
    for a in tree.css("a.download-link[href]"):
        href = a.attributes.get("href", "")
        name = a.attributes.get("data-name", "")
        label = (a.text() or "").strip()
        if href:
            attachments.append({
                "url": MR_HOST + href if href.startswith("/") else href,
                "data_name": name, "label": label,
            })
    seen = set()
    return [x for x in attachments if x["url"] not in seen and not seen.add(x["url"])]

# ══════════════════════════════════════════════════════════════════
# KEYWORD FILTER + CATEGORY
# ══════════════════════════════════════════════════════════════════
def keyword_filter(title: str) -> str:
    blob = _normalize(title)
    if EXCLUDE_RX.search(blob): return "EXCLUDED"
    if INCLUDE_RX.search(blob): return "MATCH"
    return "NO_MATCH"

def map_category(title: str) -> str:
    blob = _normalize(title)
    for cat, kws in CATEGORY_MAP.items():
        if any(re.search(_heb(kw), blob) for kw in kws): return cat
    return "_uncategorized"

# ══════════════════════════════════════════════════════════════════
# AKAMAI SESSION
# ══════════════════════════════════════════════════════════════════
class _WafBlocked(Exception): pass

def _primed_session(cookies: Optional[dict] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    r = s.get(MR_HOST + STOREFRONT + "/", timeout=30)
    if r.status_code in (401, 403):
        raise _WafBlocked(f"WAF blocked priming: {r.status_code}")
    if cookies: s.cookies.update(cookies)
    return s

def _harvest_cookies() -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(locale="he-IL", user_agent=BROWSER_HEADERS["User-Agent"])
        pg = ctx.new_page()
        pg.goto(MR_HOST + STOREFRONT + "/", wait_until="networkidle")
        time.sleep(3)
        c = {x["name"]: x["value"] for x in ctx.cookies()}
        b.close()
        return c

def _get(s: requests.Session, url: str, params=None) -> str:
    r = s.get(url, params=params, timeout=30)
    if r.status_code in (401, 403): raise _WafBlocked(f"{r.status_code} {r.url}")
    r.raise_for_status()
    return r.text

# ══════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════
def _init_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS tenders (
        tender_id TEXT PRIMARY KEY,
        title TEXT, url TEXT, publisher TEXT, status TEXT,
        pub_date TEXT, deadline TEXT, proc_number TEXT,
        category TEXT, keyword_verdict TEXT,
        attachments TEXT,
        first_seen TEXT, last_updated TEXT
    )""")
    conn.commit()
    return conn

def _upsert(conn, rec: dict):
    now = datetime.now(timezone.utc).isoformat()
    existing = conn.execute("SELECT tender_id FROM tenders WHERE tender_id=?",
                            (rec["tender_id"],)).fetchone()
    if existing:
        conn.execute("""UPDATE tenders SET status=?, deadline=?, last_updated=?
                        WHERE tender_id=?""",
                     (rec.get("status"), rec.get("deadline"), now, rec["tender_id"]))
    else:
        conn.execute("""INSERT INTO tenders
            (tender_id, title, url, publisher, status, pub_date, deadline,
             proc_number, category, keyword_verdict, attachments,
             first_seen, last_updated)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rec["tender_id"], rec["title"], rec["url"], rec["publisher"],
             rec["status"], rec.get("pub_date"), rec.get("deadline"),
             rec.get("proc_number"), rec.get("category"), rec.get("keyword_verdict"),
             json.dumps(rec.get("attachments", []), ensure_ascii=False),
             now, now))
    conn.commit()

# ══════════════════════════════════════════════════════════════════
# INGEST — scrape + keyword filter + store
# ══════════════════════════════════════════════════════════════════
def ingest():
    try:
        s = _primed_session()
    except _WafBlocked:
        s = _primed_session(cookies=_harvest_cookies())

    conn = _init_db()
    total_new, total_match = 0, 0

    for term in SEARCH_TERMS:
        # Construct search parameters - include pagination params for Hybris
        params_base = {"q": f"{term}{ACTIVE_TENDERS_Q}", "text": term, "s": SCOPE_TENDER}

        pages_done = 0
        seen_on_term = set()
        consecutive_duplicates = 0
        max_pages = 100  # Safety limit to prevent infinite loops

        while pages_done < max_pages:
            # Add pagination offset for Hybris Storefront (Hybris uses 1-based pageNumber, not 0-based)
            params = params_base.copy()
            params["pageNumber"] = pages_done + 1  # Hybris pagination: 1-based page numbering

            try:
                html = _get(s, SEARCH_URL, params)
            except _WafBlocked:
                s = _primed_session(cookies=_harvest_cookies())
                html = _get(s, SEARCH_URL, params)

            stubs = _parse_list_page(html)
            pages_done += 1
            print(f"  [{term}] Page {pages_done}: {len(stubs)} tenders")

            # If empty page, we've reached the end
            if not stubs:
                print(f"    → End of results for '{term}' (total: {pages_done - 1} pages)")
                break

            # Check for all duplicates on this page (indicates we're recycling results)
            page_ids = {stub["tender_id"] for stub in stubs}
            if page_ids.issubset(seen_on_term):
                consecutive_duplicates += 1
                if consecutive_duplicates >= 2:
                    print(f"    → All results duplicate on page {pages_done}, stopping for '{term}' (total: {pages_done - 1} pages)")
                    break
            else:
                consecutive_duplicates = 0
                seen_on_term.update(page_ids)

            for stub in stubs:
                verdict = keyword_filter(stub["title"])
                if verdict == "EXCLUDED": continue
                stub["keyword_verdict"] = verdict
                stub["category"] = map_category(stub["title"]) if verdict == "MATCH" else ""

                existing = conn.execute("SELECT tender_id FROM tenders WHERE tender_id=?",
                                        (stub["tender_id"],)).fetchone()
                if not existing:
                    total_new += 1
                    if verdict == "MATCH":
                        total_match += 1
                        try:
                            detail_html = _get(s, f"{MR_HOST}{STOREFRONT}/p/{stub['tender_id']}")
                            stub["attachments"] = _extract_attachment_urls(detail_html)
                        except Exception:
                            stub["attachments"] = []
                _upsert(conn, stub)

            # Partial page means we've reached the end
            if len(stubs) < 20:
                print(f"    → End of results for '{term}' (partial page, total: {pages_done} pages)")
                break

            print(f"    → Fetching next page...")
            time.sleep(1.0)

        time.sleep(1.0)

    conn.close()
    print(f"\nIngest complete: {total_new} new tenders, {total_match} keyword MATCH")

# ══════════════════════════════════════════════════════════════════
# REVIEW — readable output for the analyst
# ══════════════════════════════════════════════════════════════════
def review(show_all: bool = False):
    conn = _init_db()
    where = "WHERE keyword_verdict='MATCH'" if not show_all else ""
    rows = conn.execute(f"""SELECT tender_id, title, category, deadline, publisher,
                                   status, pub_date, url, attachments
                            FROM tenders {where}
                            ORDER BY deadline ASC NULLS LAST""").fetchall()
    conn.close()

    if not rows:
        print("No matched tenders in the database."); return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    active = [r for r in rows if r[3] is None or r[3] >= today]
    expired = [r for r in rows if r[3] is not None and r[3] < today]

    print(f"\n{'='*80}")
    print(f"  B2G TENDER INTELLIGENCE — {today}")
    print(f"  Active: {len(active)}  |  Expired: {len(expired)}  |  Total in DB: {len(rows)}")
    print(f"{'='*80}")

    if active:
        print(f"\n  ACTIVE TENDERS (deadline not passed)\n  {'-'*74}")
        for tid, title, cat, dl, pub, status, pub_date, url, att_json in active:
            atts = json.loads(att_json) if att_json else []
            print(f"\n  [{tid}]  {title}")
            print(f"    Category:  {cat or '-'}")
            print(f"    Publisher: {pub or '-'}")
            print(f"    Status:    {status or '-'}")
            print(f"    Published: {pub_date or '-'}    Deadline: {dl or 'N/A'}")
            print(f"    URL:       {url}")
            if atts:
                print(f"    Documents: {len(atts)} attached")
                for a in atts:
                    print(f"      - {a.get('label') or 'download'}: {a['url']}")

    if expired:
        print(f"\n  EXPIRED ({len(expired)} tenders, deadline passed)")
        for tid, title, cat, dl, *_ in expired:
            print(f"    [{tid}] {title[:60]}  (expired {dl})")

    print()

# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ingest"
    if cmd == "ingest":
        ingest()
    elif cmd in ("review", "digest"):
        review()
    elif cmd == "all":
        review(show_all=True)
    else:
        print("Usage: python procurement_ingest.py [ingest|review|digest|all]")
        print("  ingest  — scrape mr.gov.il, filter, store MATCH tenders")
        print("  review  — show matched tenders (alias: digest)")
        print("  all     — show all tenders including NO_MATCH")
