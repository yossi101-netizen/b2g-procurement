# Israel-Hunter V3 — Tech Stack & Iron Principles
**גרסה:** 2.0 | **עודכן:** 2026-04-09 | **סיבת עדכון:** TOM Protocol VERIFY Phase — 11 ממצאים

## חוקת הפיתוח

קובץ זה הוא **חוקה קשיחה ובלתי-ניתנת לעקיפה** עבור כל סוכן במערכת Israel-Hunter V3.
כל סטייה מהעקרונות הבאים דורשת אישור מפורש ותיעוד מנומק.

---

## עיקרון 1 — סביבת הרצה אסינכרונית

**שפה:** Python בלבד.
**ספריות חובה:** `asyncio`, `aiohttp`.
**מטרה:** סריקה מקבילית של מקורות מרובים ללא חסימה.

```python
# דפוס ההרצה הסטנדרטי
async def scan_source(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url) as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [scan_source(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
```

**איסור מוחלט:** שימוש ב-Selenium או Playwright אסור, אלא אם הוכח תיעודית שאין כל חלופה.

---

## עיקרון 2 — מנוע חקירה Tri-Vector + Social

איסוף דאטה מתבצע דרך **ארבעה וקטורים**:

| וקטור | API | שימוש |
|-------|-----|-------|
| **V1** | **Serper Web Search** | חיפוש אורגני — אתרי חברות, חדשות עסקיות |
| **V2** | **SerpApi Maps** | Google Maps — עסקים מקומיים, כתובות, טלפונים |
| **V3** | **Direct HTTP** | גישה ישירה לאתר העסק לאחר זיהוי |
| **V1-Social** | **Serper Image Search** | חיפוש פוסטי Instagram ציבוריים — סיגנלי OEM וקולקציה. **ללא auth, ללא גישה ישירה לאינסטגרם.** שאילתא לדוגמה: `site:instagram.com "שם חברה" קולקציה עור` |

**כלל:** אין להוסיף APIs חדשים ללא עדכון קובץ זה.

**Agent Decisions (TOM Protocol 2026-04-09):**
- **Proxy Pool:** נדחה ל-Phase 3. לא נדרש כעת. Issue פתוח ב-M-Memory.
- **Importer Registry Agent (פנקס יבואנים):** **בוטל לצמיתות.** קודי HS נוקשים יחמיצו קונים מחוץ לקטגוריה (למשל רהיטים + עור). הסמנטיקה של ה-LLM עדיפה.
- **Instagram Signal Agent:** **מאושר** דרך V1-Social (Serper Image Search בלבד).

---

## עיקרון 3 — מנגנון סיווג מבוסס AI (NLP)

### ארכיטקטורת שני-שלבים

```
Tier-1 (heuristics מקומיות, ללא עלות):
    → DISQUALIFIED_C אם סיגנל דרופשיפ מובהק
    → UNCLASSIFIED אם תוכן לא מספיק

Tier-2 (LLM — OpenAI gpt-4o-mini):
    → הבורר הסופי לכל מקרה שלא פוסל ב-Tier-1
    → מחזיר: {status, confidence, signals, reasoning}
```

### קטגוריות סיווג

| קטגוריה | SQLite status | תיאור |
|---------|--------------|-------|
| Volume Buyer | `QUALIFIED_A` | יבואן / OEM Brand / סיטונאי / מפיץ B2B / יצרן |
| Unverified | `QUALIFIED_B_PENDING_VERIFY` | פוטנציאל לא מאושר, לאימות ידני |
| Dropshipper | `DISQUALIFIED_C` | אין מלאי ישראלי, העברת הזמנות |
| Insufficient | `UNCLASSIFIED` | תוכן לא מספיק לסיווג |
| Legal Gap | `PENDING_LEGAL` | ישות לגיטימית, חסר ח.פ. |

### סף ה-Confidence — כלל קוד מחייב

```python
if confidence >= 0.75:
    status = "QUALIFIED_A"
elif 0.60 <= confidence < 0.75:
    status = "QUALIFIED_B_PENDING_VERIFY"
else:  # confidence < 0.60
    status = "DISQUALIFIED_C"

# חריג יחיד — OEM Override:
if oem_brand_detected:  # LLM זיהה OEM Brand במפורש
    status = "QUALIFIED_A"  # ללא קשר ל-confidence
```

**הערה:** ה-LLM מחזיר status ו-confidence ביחד. כלל ה-confidence הוא validation layer — אם ה-LLM החזיר `QUALIFIED_A` עם confidence 0.65, הקוד מוריד אותו ל-`QUALIFIED_B`.

---

## עיקרון 4 — חילוץ נתוני ליבה (Core Data Extraction)

### 4א — מספר WhatsApp
- חיפוש בדפי האתר, כפתורי "צור קשר", מטא-תגיות
- נורמליזציה לפורמט: `972XXXXXXXXX` (ללא `+` בDB, עם `+972-XX-XXX-XXXX` ב-CSV)
- אימות: בדיקת ספרות ותחילית ישראלית תקנית

### 4ב — ח.פ. / עוסק מורשה
- חיפוש בדפי האתר
- שמירת מספר 9 ספרות
- ליד ללא ח.פ. תקין מסומן `PENDING_LEGAL` בשדה נפרד (לא מעכב סיווג)

```python
WHATSAPP_PATTERN = r'(\+972|972|0)(5[0-9])\d{7}'
COMPANY_ID_PATTERN = r'\b5[0-9]{8}\b|\b[5-9][0-9]{8}\b'
```

---

## עיקרון 5 — Domain Canonicalization

### הכלל
**תמיד אחסן רק את ה-apex domain.** לפני כל DB INSERT, strip prefixes ועקוב אחרי redirects.

```python
STRIP_PREFIXES = ("www.", "shop.", "store.", "m.", "he.")

def canonicalize_domain(raw_url: str) -> str:
    """
    1. Parse URL → extract hostname
    2. Follow HTTP 301/302 redirects to final destination
    3. Strip known subdomain prefixes
    4. Return lowercase apex domain
    """
    from urllib.parse import urlparse
    hostname = urlparse(raw_url).netloc.lower()
    for prefix in STRIP_PREFIXES:
        if hostname.startswith(prefix):
            hostname = hostname[len(prefix):]
            break
    return hostname
```

### מקרי קצה מוגדרים

| מצב | דוגמה | התנהגות נדרשת |
|-----|-------|---------------|
| Subdomain | `shop.braker.co.il` | → `braker.co.il` |
| Redirect | `old.co.il` → 301 → `new.co.il` | → `new.co.il` |
| www | `www.oor.co.il` | → `oor.co.il` |
| International | `company.com` + `company.co.il` | שני records — חברה אחת, לא ניתן לקבוע אוטומטית |
| Rebrand | `old.co.il` + `new.co.il` | שני records — זיהוי ידני בלבד |

**הבהרה:** Rebrand ו-International variants אינם ניתנים לזיהוי אוטומטי בלבד. הם יישארו כשני records עד לאימות ידני.

---

## עיקרון 6 — סכמת SQLite (גרסה עדכנית)

```sql
-- טבלה 1: ישויות עסקיות
CREATE TABLE leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name     TEXT NOT NULL,
    domain          TEXT UNIQUE NOT NULL,    -- apex domain בלבד (canonicalized)
    whatsapp        TEXT,                    -- פורמט: 972XXXXXXXXX
    company_id      TEXT,                    -- ח.פ. 9 ספרות
    physical_address TEXT,
    status          TEXT NOT NULL CHECK(status IN (
                        'QUALIFIED_A',
                        'QUALIFIED_B_PENDING_VERIFY',
                        'DISQUALIFIED_C',
                        'UNCLASSIFIED',
                        'PENDING_LEGAL'
                    )),
    source_url      TEXT,
    first_seen_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_domain ON leads(domain);

-- טבלה 2: היסטוריית סיווגים (כל ריצה שומרת שורה)
CREATE TABLE lead_classifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id         INTEGER NOT NULL REFERENCES leads(id),
    category        TEXT,                    -- MANUFACTURER / IMPORTER / WHOLESALER / OEM_BRAND / DROPSHIPPER
    confidence      REAL,                    -- 0.0 – 1.0
    signals         TEXT,                    -- JSON array: ["סיגנל1", "סיגנל2"]
    disqualify_reason TEXT,
    model_version   TEXT,                    -- "gpt-4o-mini" וכו׳
    classified_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lc_lead_id ON lead_classifications(lead_id);
```

**כלל Deduplication:** בדיקת `domain` (canonicalized) לפני כל INSERT. כפילות → UPDATE בלבד.

---

## עיקרון 7 — O-Output: Excel עם שלושה Tabs

הפלט הסופי הוא קובץ **Excel (.xlsx)** עם שלושה sheets:

| Sheet | תוכן | מיון |
|-------|------|------|
| `Class A` | `QUALIFIED_A` | confidence יורד |
| `Class B` | `QUALIFIED_B_PENDING_VERIFY` | confidence יורד |
| `Class C` | `DISQUALIFIED_C` + `UNCLASSIFIED` | first_seen_at עולה |

**ספרייה:** `openpyxl` — נוסף ל-requirements.txt.
**קידוד:** UTF-8 (openpyxl מטפל בכך; אין צורך ב-BOM).
**שם קובץ:** `kritikaal_leads_export.xlsx` (מחליף את ה-.csv הקיים).

---

## עיקרון 8 — Anti-Bot (סטטוס עדכני)

| מנגנון | מצב | הערות |
|--------|-----|-------|
| **User-Agent Rotation** | ✅ ממומש | רשימת UAs ב-scrapers.py |
| **Random Delays** | ✅ ממומש | `asyncio.sleep(random.uniform(1.5, 4.0))` |
| **Request Headers** | ✅ ממומש | Referer, Accept-Language |
| **Rate Limiting** | ✅ ממומש | מגבלות per-domain |
| **Proxy Pool** | ⏸ נדחה ל-Phase 3 | Issue פתוח ב-M-Memory |

---

## טבלת ספריות מאושרות

| ספרייה | גרסה מינימלית | שימוש |
|--------|--------------|-------|
| `aiohttp` | 3.9 | HTTP אסינכרוני |
| `asyncio` | stdlib | event loop |
| `openai` | 1.x | LLM classification |
| `python-dotenv` | 1.x | ניהול סביבה |
| `sqlite3` | stdlib | DB |
| `openpyxl` | 3.1 | **חדש** — Excel output |

---

*גרסה 2.0 — עדכון מקיף בעקבות TOM Protocol VERIFY Phase. אין לשנות עיקרון ברזל ללא עדכון גרסה מתועד.*
