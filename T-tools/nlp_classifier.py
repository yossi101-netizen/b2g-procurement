"""
KritiKaal Leads Hunter — Hybrid NLP Classification Engine
File: T-tools/nlp_classifier.py
Governed by: B-brain/01-tech-stack.md (Iron Principle 3)
Classification rules: C-core/02-target-audience.md

Responsibilities (SRP boundary):
  - Tier 1: Fast zero-cost local heuristics that disqualify obviously
    invalid pages before an OpenAI API call is made.
  - Tier 2: Structured OpenAI JSON-mode API call for surviving leads.
  - Strict enum validation: LLM output is validated against the exact
    CHECK constraint values in db_schema.sql before any return.
  - Expose one public async entry point: classify_lead(text) -> (status, confidence).

TIER FLOW:
  text_payload
      │
      ▼
  Tier 1: local heuristics
      ├─ FAIL (zero text / error page / non-Hebrew)  →  DISQUALIFIED_C, 1.0
      ├─ FAST DISQUALIFY (explicit dropship patterns) →  DISQUALIFIED_C, 0.95
      └─ PASS                                         ↓
  Tier 2: OpenAI structured call
      ├─ returns valid status + confidence
      └─ validation fail / API error              →  UNCLASSIFIED, 0.0

ENUM CONTRACT:
  The LLM is instructed to return ONLY values from VALID_LLM_STATUSES.
  Any other string is caught by _validate_llm_status() and replaced
  with UNCLASSIFIED — preventing SQLite CHECK constraint violations.

SEMANTIC NEGATION:
  The Tier 1 fast-disqualify regex only fires on POSITIVE assertions
  (e.g., "נשלח מסין"). Phrases containing negation markers (לא, אין,
  אנחנו לא) are passed through to Tier 2 for LLM understanding.

This module does NOT:
  - Write to SQLite (that is db_init.py's responsibility)
  - Perform HTML fetching (that is scrapers.py's responsibility)
  - Log to M-memory directly (scrapers.run_agent_pipeline handles logging)
"""

from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
from typing import NamedTuple, Optional

import openai

# ---------------------------------------------------------------------------
# Constants — Enum alignment with db_schema.sql CHECK constraint
# ---------------------------------------------------------------------------

# Statuses the LLM is permitted to return.
# Subset of STATUS_ORDER — lifecycle states (RAW, ENRICHED, etc.) are
# never returned by classification; only semantic labels are.
VALID_LLM_STATUSES: frozenset[str] = frozenset({
    "QUALIFIED_A",
    "QUALIFIED_B_PENDING_VERIFY",
    "DISQUALIFIED_C",
    "UNCLASSIFIED",
    "PENDING_LEGAL",
})

class TokenUsage(NamedTuple):
    """Token counts from a single OpenAI API call."""
    prompt_tokens:     int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def cost_usd(self, model: str = "gpt-4o-mini") -> float:
        """Approximate cost in USD. Rates: gpt-4o-mini $0.15/$0.60 per 1M tokens."""
        rates = {
            "gpt-4o-mini": (0.15, 0.60),   # (input, output) per 1M tokens
            "gpt-4o":      (2.50, 10.00),
        }
        in_rate, out_rate = rates.get(model, (0.15, 0.60))
        return (self.prompt_tokens * in_rate + self.completion_tokens * out_rate) / 1_000_000


_ZERO_USAGE = TokenUsage(0, 0)

# Fallback used whenever LLM output cannot be validated.
_FALLBACK_STATUS = "UNCLASSIFIED"
_FALLBACK_CONFIDENCE = 0.0

# Minimum confidence required to trust LLM output.
# Below this threshold → status overridden to UNCLASSIFIED.
# Mirrors B-brain/01-tech-stack.md Iron Principle 3 (sף קבלה).
# Confidence thresholds — aligned with C-core/02-target-audience.md v2.0
# 0.75+        → QUALIFIED_A
# 0.60 – 0.74  → QUALIFIED_B_PENDING_VERIFY
# < 0.60       → DISQUALIFIED_C
# OEM override → QUALIFIED_A regardless of confidence (if >= 0.50 and is_oem_brand)
CONFIDENCE_THRESHOLD_A:   float = 0.75
CONFIDENCE_THRESHOLD_B:   float = 0.60
CONFIDENCE_OEM_OVERRIDE:  float = 0.50   # minimum confidence to trust OEM detection

# ---------------------------------------------------------------------------
# Constants — Contradiction guard (dropship signals in a QUALIFIED_A response)
#
# LLMs sometimes echo quoted examples from the system prompt back into the
# signals list while still returning QUALIFIED_A. Any of these keywords in
# the signals list is a hard contradiction and forces a downgrade to UNCLASSIFIED
# for human review — better to under-qualify than to pass a dropshipper.
# ---------------------------------------------------------------------------

_DROPSHIP_SIGNAL_MARKERS: frozenset[str] = frozenset({
    "dropshipping", "dropship", "print-on-demand", "print on demand",
    "14-28", "14 to 28", "28+ day", "overseas fulfillment",
    "overseas warehouse", "aliexpress", "dhgate", "wish.com",
    "china post", "epacket", "no inventory", "אין מלאי פיזי",
    "נשלח מסין", "נשלח מחו\"ל", "זמן אספקה 14", "זמן אספקה 21",
    "dropshipper", "fulfillment center abroad",
})

# ---------------------------------------------------------------------------
# Constants — Hebrew language detection
# ---------------------------------------------------------------------------

# Unicode block: Hebrew letters (alef–tav)
_HEBREW_RE = re.compile(r'[\u05D0-\u05EA]')
_MIN_HEBREW_CHARS = 50       # minimum Hebrew characters for a valid page
_MIN_TOTAL_CHARS  = 100      # minimum total text length for a valid page

# ---------------------------------------------------------------------------
# Constants — Error page detection
# ---------------------------------------------------------------------------

_ERROR_PAGE_SIGNALS: list[str] = [
    "404", "page not found", "עמוד לא נמצא", "שגיאה 404",
    "403 forbidden", "access denied", "הגישה נדחתה",
    "500 internal server error", "שגיאת שרת",
    "this site can't be reached", "err_connection_refused",
    "domain for sale", "דומיין למכירה",
    "parked domain", "coming soon", "בקרוב",
    "under construction",
]

# ---------------------------------------------------------------------------
# Constants — Tier 1 fast-disqualify patterns (Class C)
# Matches ONLY positive (non-negated) dropship signals.
# Negation check runs first — if the sentence contains a negation marker,
# the regex is NOT applied and the lead passes to Tier 2.
# ---------------------------------------------------------------------------

# Negation markers that invalidate a co-occurring disqualifier
_NEGATION_RE = re.compile(
    r'(?:לא|אין|אנחנו לא|אנו לא|ללא|בלי|לא\s+\w+)',
    re.UNICODE,
)

# Positive-assertion dropship patterns (applied per-sentence after negation check)
_TIER1_DISQUALIFY_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.UNICODE | re.IGNORECASE) for p in [
        r'נשלח\s+(?:ישירות\s+)?מ(?:סין|סינ|חו"ל|חוץ\s+לארץ)',  # shipped from China/abroad
        r'משלוח\s+(?:ישיר\s+)?מ(?:המחסן|מחסן)\s+(?:שלנו\s+)?ב(?:חו"ל|סין|אמזון)',
        r'dropshipp?ing',
        r'print[\s-]on[\s-]demand',
        r'(?:aliexpress|alibaba|dhgate|wish\.com)\s+(?:ספק|מחסן|משלוח)',
        r'(?:epacket|china\s+post|usps\s+tracking)',
        r'זמן\s+(?:אספקה|משלוח)\s*[:\-]?\s*(?:[2-9][0-9]|1[4-9])\s*(?:ימ|יום)',  # 14-99 day delivery
        r'(?:3|4|5|6|7|8)\s*[–\-]\s*(?:[3-9]|1[0-9])\s*שבועות',                   # 3-9 weeks
        r'fulfillment\s+center\s+(?:abroad|overseas|china)',
        r'no\s+inventory',
        r'אין\s+מלאי\s+(?:פיזי|אצלנו)',
    ]
]

# ---------------------------------------------------------------------------
# Constants — Tier 0 עור homograph disambiguation (pre-Tier-1, zero LLM cost)
#
# Hebrew "עור" (ayin-vav-resh) is orthographically identical for both:
#   (a) עוֹר = leather/hide — our target industry
#   (b) עוֹר = skin/complexion — the cosmetics/skincare industry
#
# Search queries containing "עור" therefore return a significant false-positive
# stream of cosmetics companies. This Tier 0 check catches pages that are
# overwhelmingly skincare in vocabulary AND have zero leather product anchors,
# immediately returning DISQUALIFIED_C without an API call.
#
# Threshold-based design (≥3 signals) prevents false positives on:
#   - A leather goods company whose newsletter mentions SPF once
#   - A general health & beauty store that also sells a leather wallet
# ---------------------------------------------------------------------------

_SKINCARE_SIGNALS: list[str] = [
    # Hebrew skincare product/concept vocabulary
    "קרם פנים", "קרם לילה", "קרם יום", "קרם לחות",
    "סרום", "מסכת פנים", "טיפוח עור הפנים", "טיפוח עור",
    "אנטי אייג'ינג", "אנטי-אייג'ינג", "אנטי אייגינג",
    "מיצוק עור", "עור מוצק", "עור צעיר", "עור בריא",
    "קרם שמש", "פילינג", "ניקוי פנים", "לחות עמוקה",
    "מוצרי יופי", "קוסמטיקה", "קרם גוף", "קרם ידיים",
    # English skincare vocabulary (Israeli cosmetics brands often mix languages)
    "skincare", "moisturizer", "anti-aging", "anti aging",
    "spf", "serum", "face cream", "skin care",
]

_LEATHER_CONTEXT_ANCHORS: list[str] = [
    # Specific leather products — confirms the page is in the leather industry
    "תיקים", "ארנקים", "נעלים", "נעלי עור", "כפפות עור",
    "סינר עור", "חגורות עור", "ארנק עור", "תיק עור",
    "אביזרי עור", "מוצרי עור", "קולקציית עור",
    "יבואן עור", "סיטונאי עור", "מפעל עור", "עור גולמי",
    "עור איטלקי", "עור טורקי", "עור ספרדי",
]

_SKINCARE_SIGNAL_THRESHOLD: int = 3   # ≥ 3 distinct skincare signals required to fire


def _is_skincare_page(text: str) -> bool:
    """
    Return True if the page is a skincare/cosmetics page misidentified as a
    leather-industry lead due to the עור (leather/skin) homograph.

    Two conditions must BOTH hold:
      1. At least _SKINCARE_SIGNAL_THRESHOLD distinct skincare signals present.
      2. Zero leather context anchors present.

    The dual-condition design prevents false positives — a leather goods
    company that mentions SPF in a newsletter will have skincare signals
    but will also have leather anchors, so this returns False correctly.
    """
    lower = text.lower()
    skincare_count = sum(1 for sig in _SKINCARE_SIGNALS if sig.lower() in lower)
    if skincare_count < _SKINCARE_SIGNAL_THRESHOLD:
        return False
    leather_count = sum(1 for anchor in _LEATHER_CONTEXT_ANCHORS if anchor.lower() in lower)
    return leather_count == 0


# ---------------------------------------------------------------------------
# Constants — Turkish Disruption Signal Detection (Tier 2 NLP enrichment)
#
# Signal Group A: Explicit Turkish Origin (highest confidence, 0.70+ base score)
# When detected alone or combined with other signals, indicates Turkish supply chain.
# ---------------------------------------------------------------------------

_TURKISH_ORIGIN_KEYWORDS: tuple[str, ...] = (
    "ייצור בטורקיה",
    "מוצר טורקי",
    "עיצוב טורקי",
    "עור טורקי",
    "יבוא מטורקיה",
    "תוצרת טורקיה",
    "made in turkey",
    "turkish leather",
    "manufactured in turkey",
    "מפעל בטורקיה",
    "שותפות עם מפעל טורקי",
)

# Signal Group B: Supply Chain Disruption Indicators (medium confidence, 0.40+ base score)
# Indicates active inventory/supply challenges — may be Turkey-related or general.
_SUPPLY_DISRUPTION_KEYWORDS: tuple[str, ...] = (
    "מחסור במלאי",
    "הזמנות מושהות",
    "אזל מהמלאי",
    "עיכובים בספקות",
    "עיכובים בייצור",
    "מחפשים ספק חלופי",
    "שינוי ספק",
    "בעיות שרשרת אספקה",
    "עיכוב בהגעת הסחורה",
    "temporarily out of stock",
    "supply delay",
    "sourcing challenges",
    "מלאי מוגבל עקב",
    "בשל בעיות ייצור",
)

# Signal Group C: Post-Embargo Behavioral Signals (derived pattern match, 0.30+ base score)
# Behavioral indicators of production/supplier transition (not explicit statements).
_POST_EMBARGO_KEYWORDS: tuple[str, ...] = (
    "החלטנו לשנות את הייצור",
    "אנו עובדים על קולקציה חדשה",
    "הייצור עבר ל",
    "שיתוף פעולה חדש עם מפעל",
    "under new production partnership",
    "מקור חדש לחומרי גלם",
    "ספק עור חדש",
)

# Halachic blacklist keywords (in addition to existing Tier 1 patterns)
# These should trigger immediate HALACHIC blacklist routing
_HALACHIC_BLACKLIST_KEYWORDS: tuple[str, ...] = (
    "עור כשר",
    "מוצר מהודר",
    "בד כשר לפסח",
    "הכשר על העור",
    "מאושר על ידי הרבנות",
)

# ---------------------------------------------------------------------------
# Constants — Tier 1 halachic hard-disqualify patterns
#
# BUSINESS RULE (non-negotiable, permanent):
#   Leather used for Tefillin, Sifrei Torah, Mezuzot, or any Tashmishei
#   Kedusha MUST come from animals slaughtered according to Halacha (Jewish
#   law) — i.e., it must be "kosher leather" certified by a rabbinic authority.
#   Our manufacturing partner uses standard commercial (non-kosher) leather.
#   Therefore we CANNOT supply ANY of these markets, regardless of volume.
#
# Implementation:
#   A single match in this list on the lead's page text is sufficient to
#   immediately disqualify the lead with DISQUALIFIED_C (no LLM call needed).
#   Patterns are specific enough (manufacturing/supply context) that a single
#   match indicates the primary business, not an incidental mention.
# ---------------------------------------------------------------------------

_TIER1_HALACHIC_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.UNICODE | re.IGNORECASE) for p in [
        r'יצרן\s+תפילין',                                     # tefillin manufacturer
        r'ייצור\s+תפילין',                                     # tefillin manufacturing
        r'עור\s+לתפילין',                                      # leather for tefillin
        r'עורות?\s+לסת"ם|עורות?\s+לסת״ם',                    # hides for STa"M scribal use
        r'רצועות?\s+תפילין',                                   # tefillin straps (product)
        r'בתי?\s+תפילין',                                      # tefillin housings (product)
        r'סופר\s+סת"ם|סופר\s+סת״ם',                          # Torah scribe (primary identity)
        r'כתיבת\s+ספרי?\s+תורה',                              # writing Sifrei Torah
        r'מכירת\s+תפילין\s+(?:מהודרות?|כשרות?|בדוקות?)',     # sale of premium/kosher tefillin
        r'תשמישי\s+קדושה\s+(?:עור|מעור)',                     # leather Tashmishei Kedusha
    ]
]


def _detect_turkish_origin_signals(text: str) -> bool:
    """Return True if any Turkish origin keyword is found in the text."""
    lower_text = text.lower()
    return any(kw.lower() in lower_text for kw in _TURKISH_ORIGIN_KEYWORDS)


def _detect_supply_disruption_signals(text: str) -> bool:
    """Return True if any supply disruption keyword is found in the text."""
    lower_text = text.lower()
    return any(kw.lower() in lower_text for kw in _SUPPLY_DISRUPTION_KEYWORDS)


def _detect_post_embargo_signals(text: str) -> bool:
    """Return True if any post-embargo behavioral keyword is found in the text."""
    lower_text = text.lower()
    return any(kw.lower() in lower_text for kw in _POST_EMBARGO_KEYWORDS)


def _detect_halachic_blacklist_keywords(text: str) -> bool:
    """
    Return True if any halachic blacklist keyword is found in the text.
    These are additional keywords beyond the Tier 1 patterns.
    """
    lower_text = text.lower()
    return any(kw.lower() in lower_text for kw in _HALACHIC_BLACKLIST_KEYWORDS)


def _calculate_turkey_disruption_score(
    has_turkey_origin: bool,
    has_supply_disruption: bool,
    has_post_embargo: bool,
) -> float:
    """
    Calculate the turkey_disruption_score (0.0–1.0) based on detected signals.

    Composite scoring rules:
      - TURKEY_ORIGIN alone: 0.70
      - TURKEY_ORIGIN + SUPPLY_DISRUPTION: 0.90
      - TURKEY_ORIGIN + POST_EMBARGO_SIGNAL: 0.95
      - SUPPLY_DISRUPTION alone: 0.40
      - POST_EMBARGO_SIGNAL alone: 0.30
      - No signals: 0.0
    """
    if has_turkey_origin and has_supply_disruption:
        return 0.90
    elif has_turkey_origin and has_post_embargo:
        return 0.95
    elif has_turkey_origin:
        return 0.70
    elif has_supply_disruption:
        return 0.40
    elif has_post_embargo:
        return 0.30
    else:
        return 0.0


def _has_halachic_incompatibility(text: str) -> bool:
    """
    Return True if the text contains a pattern indicating the business
    operates in a market requiring halachically-certified (kosher) leather.

    This is a hard disqualification: our supply chain uses commercial leather
    and CANNOT serve these markets regardless of volume or price.

    A single pattern match is sufficient — all patterns are specific enough
    to the manufacturing/supply context that a false positive is extremely
    unlikely. General mentions of religious Jewish culture (a store that
    carries tefillin bags among its leather goods) will NOT match these
    patterns because the patterns require production/supply language.

    Also checks the additional _HALACHIC_BLACKLIST_KEYWORDS.
    """
    for pattern in _TIER1_HALACHIC_PATTERNS:
        if pattern.search(text):
            return True
    # Check additional halachic blacklist keywords
    if _detect_halachic_blacklist_keywords(text):
        return True
    return False


# ---------------------------------------------------------------------------
# Constants — Tier 1 "Italy-origin brand identity" hard-disqualify patterns
#
# BUSINESS RULE (non-negotiable):
#   Brands whose PRIMARY value proposition is certified Italian manufacturing
#   ("Made in Italy" certification, "handmade in Italy") are incompatible with
#   KritiKaal's India manufacturing model. Their brand promise cannot survive
#   a supplier switch — the Italian origin IS the product.
#
#   IMPORTANT NUANCE — do NOT confuse with Italian leather SOURCING:
#     "עור איטלקי" / "מיובא מאיטליה" = Italian leather as raw material input.
#     These are QUALIFIED_A prospects (volume buyers paying EU leather prices).
#     Only disqualify when Italian MANUFACTURING is the core identity claim.
# ---------------------------------------------------------------------------

_TIER1_ITALY_BRAND_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.UNICODE | re.IGNORECASE) for p in [
        r'מיוצר\s+(?:ביד\s+)?באיטליה',                   # manufactured (by hand) in Italy
        r'תוצרת\s+איטליה',                                 # product of Italy
        r'(?:100%|מאה\s+אחוז)\s+(?:עשוי\s+)?באיטליה',    # 100% made in Italy
        r'certified\s+made\s+in\s+italy',                   # English certification mark
        r'made\s+in\s+italy\s+(?:certified|only|exclusively|guarantee)',
        r'artisan(?:al)?\s+(?:handmade\s+)?italian\s+(?:leather\s+)?(?:craftsmanship|brand)',
        r'אומנות\s+איטלקית\s+(?:מסורתית|אותנטית)',        # traditional Italian craftsmanship
        r'מותג\s+איטלקי\s+(?:מקורי|אותנטי|אמיתי)',        # authentic original Italian brand
    ]
]


def _is_italy_identity_brand(text: str) -> bool:
    """
    Return True if the text identifies the business as a certified
    "Made in Italy" brand (Italian manufacturing as core identity).

    NOT fired by Italian leather sourcing ("עור איטלקי", "מיובא מאיטליה").
    Only fires when Italian manufacturing IS the product's core promise.
    """
    for pattern in _TIER1_ITALY_BRAND_PATTERNS:
        if pattern.search(text):
            return True
    return False


# ---------------------------------------------------------------------------
# Constants — Tier 1 fast-qualify patterns (Class A distress / strength)
# A hit here does NOT grant QUALIFIED_A alone — it boosts the LLM prompt
# context and is passed as a hint. Final decision stays with Tier 2.
# ---------------------------------------------------------------------------

_TIER1_CLASS_A_HINTS: list[re.Pattern] = [
    re.compile(p, re.UNICODE | re.IGNORECASE) for p in [
        # ── Manufacturing signals ──────────────────────────────────────────
        r'מייצרים\s+(?:את|ב|ל)',                # "we manufacture ..."
        r'פס\s+ייצור',                           # production line
        r'מפעל(?:\s+שלנו)?',                     # factory
        # ── Importer / distributor signals ───────────────────────────────
        r'יבוא\s+בלעדי',                         # exclusive import
        r'נציג\s+(?:רשמי|בלעדי)\s+של',          # official/exclusive rep
        r'יבואן\s+(?:מוצרי|עורות?|תיקים?)',     # leather product importer
        r'יבוא\s+(?:ומ)?שיווק',                  # import & marketing
        r'מיובא\s+(?:מ(?:איטליה|טורקיה|ספרד|פורטוגל|סין))',  # imported from EU/Turkey/China
        # ── Wholesale / B2B volume signals ───────────────────────────────
        r'סיטונאות',                             # wholesale (noun)
        r'(?:מכירה|אספקה)\s+לסיטונאים',         # supply to wholesalers
        r'מחיר\s+סיטונאי',                       # wholesale price
        r'(?:מינימום|כמות\s+מינימלית)\s+הזמנה', # minimum order quantity
        r'מכירה\s+בכמויות',                      # bulk sales
        # ── Independent brand signals ─────────────────────────────────────
        r'מותג\s+(?:עור|ישראלי|עצמאי)',         # leather / Israeli / independent brand
        r'קולקצי[הת]\s+(?:עור|חדשה|חורף|קיץ)',  # leather / seasonal collection
        r'עיצוב\s+(?:עצמי|ייחודי|בית)',          # in-house / unique design
        # ── Religious leather removed (Phase 2 halachic fix) ────────────────
        # Tefillin, STa"M, Sifrei Torah require kosher-certified leather.
        # Our supply chain uses commercial leather → material incompatibility.
        # These patterns are now in _TIER1_HALACHIC_PATTERNS (hard disqualify).
        r'כריכ[הות]+\s+עור',                     # leather book binding (secular use OK)
        # ── Corporate gifting (Phase 1 lateral expansion) ─────────────────
        r'מוצרי\s+פרסום',                        # promotional products
        r'מתנות?\s+(?:לעסקים|עסקיות?|לחברות)',  # business / corporate gifts
        r'ספק\s+מתנות',                          # gift supplier
        r'מיתוג\s+(?:עסקי|חברות)',               # corporate branding
        r'מתנות?\s+(?:קורפורייט|קורפרייט)',       # corporate gifts (transliterated)
        r'מוצרי\s+(?:פרסום|קד"מ)',               # promotional / sales-promotion items
        # ── Industrial / safety leather (Phase 1 lateral expansion) ───────
        r'כפפות?\s+(?:עבודה|עור)',               # work / leather gloves
        r'סינר\s+עור',                           # leather apron
        r'ציוד\s+(?:בטיחות|מגן).*עור|עור.*ציוד\s+(?:בטיחות|מגן)',  # safety gear + leather
        # ── Distress / transition signals (Class A acquisition targets) ──
        r'פירוק\s+מלאי',                         # liquidation
        r'מכירה\s+(?:בגלל\s+)?פרישה',           # selling due to retirement
        r'שינוי\s+בעלות',                        # ownership change
        r'עסק\s+למכירה',                         # business for sale
        # ── Fast delivery (proof of local stock) ─────────────────────────
        r'משלוח\s+(?:תוך\s+)?(?:1|2|3|4)\s*ימ', # 1-4 day delivery
    ]
]

# ---------------------------------------------------------------------------
# Tier 1 — Local heuristics (zero-cost, synchronous)
# ---------------------------------------------------------------------------

def _has_sufficient_content(text: str) -> bool:
    """Return True if the text has enough characters to be a real page."""
    return len(text.strip()) >= _MIN_TOTAL_CHARS


def _has_sufficient_hebrew(text: str) -> bool:
    """Return True if the text contains enough Hebrew characters."""
    hebrew_chars = _HEBREW_RE.findall(text)
    return len(hebrew_chars) >= _MIN_HEBREW_CHARS


def _is_error_page(text: str) -> bool:
    """Return True if the text matches a known error or parked-page pattern."""
    lower = text.lower()
    return any(sig in lower for sig in _ERROR_PAGE_SIGNALS)


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into rough sentence-level chunks for per-sentence analysis.
    Uses punctuation and Hebrew sentence-end markers as delimiters.
    """
    return re.split(r'[.!?|\n।]', text)


def _sentence_has_negation(sentence: str) -> bool:
    """Return True if the sentence contains a Hebrew negation marker."""
    return bool(_NEGATION_RE.search(sentence))


def _has_explicit_disqualifier(text: str) -> bool:
    """
    Return True if any sentence contains a positive-assertion (non-negated)
    dropship signal from _TIER1_DISQUALIFY_PATTERNS.

    Semantic negation handling: if the sentence containing the pattern
    also contains a negation marker, it is NOT counted as a disqualifier.
    Example:
      "אנחנו לא שולחים מסין"  → negated → False (passes to Tier 2)
      "נשלח ישירות מסין"      → positive → True (DISQUALIFIED_C immediately)
    """
    for sentence in _split_into_sentences(text):
        if _sentence_has_negation(sentence):
            continue   # negated sentence — skip all pattern checks
        for pattern in _TIER1_DISQUALIFY_PATTERNS:
            if pattern.search(sentence):
                return True
    return False


# Human-readable labels paired with each _TIER1_CLASS_A_HINTS pattern.
# These are what we pass to the LLM — never the raw regex patterns, which
# (a) leak regex syntax into signals and (b) may contain control characters
# that openpyxl rejects as illegal XML characters.
_TIER1_CLASS_A_LABELS: list[str] = [
    # Manufacturing signals
    "מייצרים (active manufacturer language)",
    "פס ייצור (production line)",
    "מפעל (factory)",
    # Importer / distributor signals
    "יבוא בלעדי (exclusive import)",
    "נציג רשמי/בלעדי (official/exclusive rep)",
    "יבואן מוצרי עור (leather product importer)",
    "יבוא ושיווק (import & marketing)",
    "מיובא מ... (imported from EU/Turkey/China)",
    # Wholesale / B2B volume signals
    "סיטונאות (wholesale noun)",
    "מכירה/אספקה לסיטונאים (supply to wholesalers)",
    "מחיר סיטונאי (wholesale price)",
    "מינימום הזמנה (minimum order quantity)",
    "מכירה בכמויות (bulk sales)",
    # Independent brand signals
    "מותג עור/ישראלי/עצמאי (leather/Israeli/independent brand)",
    "קולקציה עור/חדשה/עונתית (seasonal leather collection)",
    "עיצוב עצמי/ייחודי/בית (in-house/unique design)",
    # Religious leather removed — see _TIER1_HALACHIC_PATTERNS (hard disqualify)
    "כריכות עור (leather book binding — secular use)",
    # Corporate gifting
    "מוצרי פרסום (promotional products)",
    "מתנות עסקיות/לחברות (corporate gifts)",
    "ספק מתנות (gift supplier)",
    "מיתוג עסקי/חברות (corporate branding)",
    "מתנות קורפורייט (corporate gifts transliterated)",
    "מוצרי פרסום/קד\"מ (promotional/sales-promotion items)",
    # Industrial / safety leather
    "כפפות עבודה/עור (work/leather gloves)",
    "סינר עור (leather apron)",
    "ציוד בטיחות + עור (safety gear + leather)",
    # Distress / transition signals
    "פירוק מלאי (liquidation)",
    "מכירה בגלל פרישה (selling due to retirement)",
    "שינוי בעלות (ownership change)",
    "עסק למכירה (business for sale)",
    # Fast delivery (proof of local stock)
    "משלוח תוך 1-4 ימים (fast local delivery)",
]


def _extract_class_a_hints(text: str) -> list[str]:
    """
    Return a list of human-readable Class A hint labels found in the text.
    Used to enrich the Tier 2 prompt context — does not classify alone.

    Returns labels (not regex patterns) so they are safe to store in the
    signals column and write to openpyxl cells without illegal-character issues.
    """
    return [
        label
        for pattern, label in zip(_TIER1_CLASS_A_HINTS, _TIER1_CLASS_A_LABELS)
        if pattern.search(text)
    ]


def _tier1_check(text: str) -> Optional[tuple[str, float]]:
    """
    Run all Tier 1 heuristics in sequence.

    Returns (status, confidence) if a Tier 1 rule fires, else None
    (meaning: proceed to Tier 2).

    Decision order:
      1. Empty / insufficient content         → DISQUALIFIED_C, 1.0
      2. Error page detected                  → DISQUALIFIED_C, 1.0
      3. Insufficient Hebrew content          → DISQUALIFIED_C, 1.0
      4. Skincare / cosmetics page            → DISQUALIFIED_C, 1.0
         (עור homograph: skin ≠ leather — saves an LLM call on each hit)
      5. Halachic material incompatibility    → DISQUALIFIED_C, 1.0
         (Tefillin/STa"M/Sifrei Torah require kosher leather — we cannot supply)
      6. Italy-identity manufacturing brand   → DISQUALIFIED_C, 1.0
         ("Made in Italy certified" as brand promise — supplier switch impossible)
      7. Explicit dropship signal             → DISQUALIFIED_C, 0.95
      8. None of the above                    → None (pass to Tier 2)
    """
    if not _has_sufficient_content(text):
        return ("DISQUALIFIED_C", 1.0)

    if _is_error_page(text):
        return ("DISQUALIFIED_C", 1.0)

    if not _has_sufficient_hebrew(text):
        return ("DISQUALIFIED_C", 1.0)

    if _is_skincare_page(text):
        return ("DISQUALIFIED_C", 1.0)

    if _has_halachic_incompatibility(text):
        return ("DISQUALIFIED_C", 1.0)

    if _is_italy_identity_brand(text):
        return ("DISQUALIFIED_C", 1.0)

    if _has_explicit_disqualifier(text):
        return ("DISQUALIFIED_C", 0.95)

    return None   # Tier 2 required


# ---------------------------------------------------------------------------
# Tier 2 — OpenAI Structured Output (JSON mode)
# ---------------------------------------------------------------------------

# The prompt is built once at module level (immutable template).
# Text payload and hint context are injected at call time.
_SYSTEM_PROMPT = """\
You are a B2B lead classifier for the Israeli e-commerce market.
Your task: classify a business based on its website text into one of the following statuses.

## HARD EXCLUSION — Halachic Material Incompatibility (evaluate FIRST, overrides all other rules)

The following business types MUST always be classified as DISQUALIFIED_C, regardless
of volume, confidence, or any other signal. This is a permanent, non-negotiable
material incompatibility: our leather supply uses standard commercial animal hides,
which are NOT halachically certified. Jewish Law (Halacha) REQUIRES that leather
used for sacred ritual items come from ritually slaughtered animals. We cannot
supply this market under any circumstances.

Classify as DISQUALIFIED_C immediately if the business primarily produces or supplies:
  - תפילין (Tefillin / phylacteries) or their straps, housings, or cases
  - מזוזות (Mezuzot) or their parchments (even if also selling the leather cases)
  - ספרי תורה (Sifrei Torah / Torah scrolls) or related scribal materials
  - תשמישי קדושה (Tashmishei Kedusha — ritual sacred objects governed by Halacha)
  - עור כשר / עורות לסת"ם (kosher leather certified for scribal use)
  - Any product where the kashrut (ritual fitness) of the raw material is a
    legal or religious requirement under Halacha

Important nuance: A general leather goods store that INCIDENTALLY sells a leather
pouch to carry tefillin (but does not manufacture the tefillin themselves) is NOT
automatically disqualified — evaluate it on its primary business. Only businesses
where the PRIMARY product requires halachically-certified leather are excluded.

## HARD EXCLUSION 2 — Italian-Origin Manufacturing Identity (evaluate BEFORE scoring wholesale signals)

Classify as DISQUALIFIED_C if the business's PRIMARY brand identity is
"Made in Italy" manufacturing or certified Italian craftsmanship:
  - "מיוצר ביד באיטליה" / "תוצרת איטליה" as a certification or identity claim
  - "100% מיוצר באיטליה" / "Certified Made in Italy"
  - "אומנות איטלקית מסורתית / אותנטית" as the primary brand pillar
  - "מותג איטלקי אמיתי/מקורי" — authentic Italian brand positioning

This disqualification OVERRIDES any positive wholesale or volume signals.
A brand built on Italian manufacturing authenticity CANNOT switch to KritiKaal's
India-based supply chain without destroying its core value proposition.

CRITICAL NUANCE — Do NOT disqualify for these:
  - "עור איטלקי" or "עור מאיטליה" (Italian leather as a raw material input — QUALIFIED_A)
  - "מיובא מאיטליה" (imported from Italy — opportunity signal, they pay EU prices)
  - Any Israeli brand that SOURCES Italian leather but designs, brands, or sells locally
  These businesses CAN switch to KritiKaal — they are QUALIFIED_A prospects.

## Valid Return Values (EXACT STRINGS ONLY — no other values accepted)
- QUALIFIED_A        : HIGH-VALUE KritiKaal target. Any of the following qualifies:
                       (1) Israeli manufacturer with local production facility ("מפעל", "פס ייצור",
                           "מייצרים").
                       (2) Importer or exclusive distributor holding local inventory — INCLUDING
                           businesses that source from Italy, Turkey, Spain, Portugal, or China.
                           Sourcing from abroad is an OPPORTUNITY signal (they have volume needs
                           and currently pay Western manufacturing prices), NOT a disqualifier.
                           Strong signals: "יבוא בלעדי", "נציג רשמי", "יבואן מוצרי עור",
                           "יבוא ושיווק", "מיובא מאיטליה / טורקיה".
                       (3) Wholesaler supplying other retailers ("סיטונאות", "מכירה לסיטונאים",
                           "מחיר סיטונאי", "מינימום הזמנה", "מכירה בכמויות").
                       (4) Independent brand with own collection or designs:
                           (4a) Brand with named collection ("מותג עור", "קולקציה", "עיצוב
                                עצמי") that sells in Israel — they need a production partner.
                           (4b) OEM brand: designs in Israel, commissions manufacturing overseas
                                ("מיוצר בטורקיה", "מיוצר בסין", "ייצור לפי הזמנה", "עיצוב
                                ישראלי"). **CRITICAL**: this is KritiKaal's ideal prospect —
                                they already have volume orders and are actively paying an
                                overseas factory. They are QUALIFIED_A, not DISQUALIFIED_C.
                                The overseas production is the PAIN POINT we solve.
                       (5) Corporate gift / promotional product supplier: company that
                           sources branded leather goods in bulk for corporate clients.
                           MOQ is typically 200-1000 units per campaign. High repeat rate.
                           Signals: "מוצרי פרסום", "מתנות עסקיות", "ספק מתנות לחברות",
                           "מיתוג", "קד"מ", "מתנות קורפורייט". These businesses do NOT
                           manufacture — they source. They are volume buyers.
                       (6) Industrial / safety leather supplier: imports or distributes
                           leather work gloves, welding aprons, protective gear in bulk.
                           Signals: "כפפות עבודה עור", "סינרי עור", "ציוד בטיחות עור".
                       (7) Business showing distress / transition: liquidation ("פירוק מלאי"),
                           sale due to retirement ("מכירה בגלל פרישה"), ownership change
                           ("שינוי בעלות") — motivated sellers, high acquisition probability.
                       Physical Israeli address and 1-4 day shipping strongly support QUALIFIED_A.
- QUALIFIED_B_PENDING_VERIFY : Independent e-commerce shop. No confirmed local manufacturing,
                       wholesale operation, exclusive import, or named collection. May hold
                       partial inventory. Needs phone verification to determine volume potential.
- DISQUALIFIED_C     : A business that holds NO local inventory and whose entire
                       fulfilment model relies on forwarding orders directly to an
                       overseas warehouse or on-demand production service. The
                       defining characteristic is the complete absence of any local
                       stock, warehouse, or physical inventory investment.
                       **CRITICAL — OEM ≠ No-inventory**: A brand that DESIGNS in
                       Israel and commissions overseas manufacturing to its own spec
                       is an OEM buyer (QUALIFIED_A), not a no-inventory dropshipper.
                       **CRITICAL — Semantic Negation**: Phrases that explicitly deny
                       overseas sourcing ("אנחנו לא שולחים מחו\"ל", "המלאי אצלנו")
                       CONFIRM local inventory — lean towards QUALIFIED_A.
- UNCLASSIFIED       : Insufficient or contradictory signals. Confidence below threshold.
                       Also use when the business is entirely unrelated to leather,
                       fashion accessories, or any vertical listed under QUALIFIED_A.
- PENDING_LEGAL      : Business appears legitimate but no ח.פ / עוסק מורשה number was found.

## Turkish Disruption Signal Detection — PHASE 1 (NLP Enrichment)
When analyzing the text, ALSO detect and report the following signal groups:

**Signal Group A — Explicit Turkish Origin (Highest Confidence)**
Flag these strings if found: "ייצור בטורקיה", "מוצר טורקי", "עור טורקי", "יבוא מטורקיה",
"תוצרת טורקיה", "Made in Turkey", "Turkish leather", "manufactured in Turkey".
Label as: "TURKEY_ORIGIN"

**Signal Group B — Supply Chain Disruption Indicators (Medium Confidence)**
Flag these strings if found: "מחסור במלאי", "הזמנות מושהות", "אזל מהמלאי", "עיכובים בספקות",
"עיכובים בייצור", "מחפשים ספק חלופי", "שינוי ספק", "בעיות שרשרת אספקה", "supply delay",
"sourcing challenges", "מלאי מוגבל עקב".
Label as: "SUPPLY_DISRUPTION"

**Signal Group C — Post-Embargo Behavioral Signals (Derived Pattern)**
Flag these strings if found: "החלטנו לשנות את הייצור", "אנו עובדים על קולקציה חדשה",
"הייצור עבר ל", "שיתוף פעולה חדש עם מפעל", "מקור חדש לחומרי גלם", "ספק עור חדש".
Label as: "POST_EMBARGO_SIGNAL"

**Composite Turkey Disruption Score:**
After detecting the above signals, compute a composite score (0.0–1.0):
  - TURKEY_ORIGIN + SUPPLY_DISRUPTION = 0.90
  - TURKEY_ORIGIN + POST_EMBARGO = 0.95
  - TURKEY_ORIGIN alone = 0.70
  - SUPPLY_DISRUPTION alone = 0.40
  - POST_EMBARGO alone = 0.30
  - No signals = omit this field
Include this score in the signals array as: "turkey_disruption_score:0.90" (or the calculated value).

## Response Format (JSON — exactly these seven fields, no others)
{
  "status":              "<one of the five VALID RETURN VALUES above>",
  "confidence":          <float between 0.0 and 1.0>,
  "signals":             ["<signal 1 found in WEBSITE TEXT>", "<signal 2>", ..., "turkey_disruption_score:X.XX"],
  "reasoning":           "<one sentence in Hebrew or English>",
  "is_oem_brand":        <true if the business designs products locally but has them manufactured abroad to its own spec; false otherwise>,
  "is_leather_relevant": <true if the business operates in leather goods, fashion accessories, bags, footwear, industrial leather, ritual leather, or corporate gifting with leather products; false if it is in a completely unrelated industry>,
  "has_halachic_conflict": <true if the business requires halachically-certified leather; false otherwise>
}

## Signal Extraction Rule
ONLY list signals that appear verbatim or as close paraphrases in the WEBSITE TEXT
provided below. Do NOT reproduce example phrases from these instructions. If a signal
is not present in the actual text, omit it.

Turkish Disruption signals (TURKEY_ORIGIN, SUPPLY_DISRUPTION, POST_EMBARGO_SIGNAL):
Include these in the signals array IF the corresponding keywords are found in the text.
The turkey_disruption_score (if any of these signals are detected) MUST appear last
in the signals array in the format: "turkey_disruption_score:X.XX"

Halachic Conflict Detection:
Set "has_halachic_conflict": true if the business appears to require halachically-certified
leather (Tefillin, Mezuzot, Sifrei Torah, Tashmishei Kedusha, כשר leather, סת"ם materials,
עור כשר, מוצר מהודר, הכשר על העור, מאושר על ידי הרבנות). Otherwise false.

## is_oem_brand Decision Rule
Set "is_oem_brand": true ONLY if ALL of the following are present:
  (a) Evidence of own design / brand identity (collection, catalog, unique product)
  (b) Evidence of overseas manufacturing (explicit country mention OR "מיוצר לפי הזמנה")
  (c) The business is clearly the brand owner, not a pure reseller of another brand
If in doubt, set false. A wrong true is more costly than a wrong false here.

## is_leather_relevant Decision Rule
Set "is_leather_relevant": false ONLY when the website is clearly about a completely
unrelated business (e.g., a restaurant, construction company, software firm, travel
agency). If there is ANY plausible connection to leather goods, accessories, fashion,
gifting, or industrial materials — set true.
"""

_USER_PROMPT_TEMPLATE = """\
## Website Text (smart-extracted excerpt, up to 6,000 characters)
The text below is assembled from three sections of the page: the header/hero,
a B2B-signal keyword window from the body, and the footer. Section markers
([HEADER], [MID-PAGE B2B CONTEXT], [FOOTER]) appear when the page was long
enough to require slicing. Read all sections before classifying.

{text}

## Pre-detected Tier-1 Hints
{hints}

Classify this business. Return ONLY the JSON object described in the system prompt.
"""


# ---------------------------------------------------------------------------
# Smart text extraction — Sprint 3 / Priority 4
#
# Israeli company homepages commonly bury the highest-value B2B signals
# (MOQ, wholesale price, factory address, import volume) in the footer or
# deep in the body, well past the 3,000-character mark after HTML stripping.
# A naive head-truncation misses this data and produces false UNCLASSIFIED
# results.  The smart extractor pieces together three targeted sections to
# maximise signal density within the 6,000-character token budget.
# ---------------------------------------------------------------------------

# Total character budget fed to the LLM (≈ 1,500–2,000 tokens for Hebrew text).
_EXCERPT_TOTAL:  int = 6_000
_HEAD_SIZE:      int = 3_000   # header + hero — brand identity, product intro
_FOOT_SIZE:      int = 1_500   # footer — contact, address, legal, MOQ tables
_KW_WINDOW_SIZE: int = 1_500   # keyword-centred context bubble
_KW_HALF:        int = _KW_WINDOW_SIZE // 2   # 750 chars either side of anchor

# High-intent B2B Hebrew terms.  The first occurrence in the body is used to
# centre the keyword window.  Ordered roughly by signal strength so the most
# discriminating terms are checked first.
_B2B_ANCHOR_KEYWORDS: tuple[str, ...] = (
    "מינימום הזמנה",    # minimum order quantity (strongest signal)
    "מחיר סיטונאי",     # wholesale price
    "נציג בלעדי",       # exclusive representative
    "יבוא בלעדי",       # exclusive import
    "סיטונאי",          # wholesale (general)
    "יבואן",            # importer
    "יבוא",             # import
    "מינימום",          # minimum (generic)
    "מפעל",             # factory
    "אספקה",            # supply
    "כמויות",           # quantities / bulk
    "ייצור",            # manufacturing / production
    "מחסן",             # warehouse / stockroom
)


def _build_smart_excerpt(text: str) -> str:
    """
    Build a signal-rich excerpt of up to _EXCERPT_TOTAL (6,000) characters.

    Strategy — three sections assembled in reading order:
      1. HEAD  (3,000 chars): top of the page — brand intro and value proposition.
      2. MID-PAGE KEYWORD WINDOW (1,500 chars): a context bubble centred on the
         first occurrence of any _B2B_ANCHOR_KEYWORDS in the body (between head
         and footer).  Falls back to the raw next 1,500 chars if no anchor is
         found.  This window captures MOQ tables, wholesale terms, factory details
         that appear mid-page but are missed by head-only truncation.
      3. FOOTER (1,500 chars): the absolute bottom of the page — contact details,
         physical address, legal entity number, shipping policies.

    Section markers ([HEADER] / [MID-PAGE B2B CONTEXT] / [FOOTER]) are injected
    only when the text is long enough to require slicing, so the LLM always reads
    coherent prose rather than abrupt mid-sentence cuts.

    Short text (≤ 6,000 chars): returned unchanged — no markers, no slicing.
    Empty sections are silently omitted from the assembled result.

    All slice boundaries are clamped so head and footer can never overlap,
    even on unusually short pages that still exceed the 6,000-char threshold.
    """
    if len(text) <= _EXCERPT_TOTAL:
        return text   # nothing to do — full text fits in budget

    # ── Section 1: HEAD ──────────────────────────────────────────────────────
    head = text[:_HEAD_SIZE]

    # ── Section 3: FOOTER ────────────────────────────────────────────────────
    # foot_start is clamped so it never overlaps with the head section.
    # When text > 6,000 chars, foot_start >= max(3000, len-1500) >= 4500,
    # which is always beyond _HEAD_SIZE=3000, so overlap is impossible.
    foot_start = max(_HEAD_SIZE, len(text) - _FOOT_SIZE)
    foot       = text[foot_start:]

    # ── Section 2: KEYWORD WINDOW ─────────────────────────────────────────────
    # Search only the middle region — text already covered by head and footer
    # is excluded to avoid redundancy.
    middle_start = _HEAD_SIZE
    middle_end   = foot_start     # guaranteed > middle_start when len > 6000

    kw_pos       = -1
    lower_middle = text[middle_start:middle_end].lower()

    for kw in _B2B_ANCHOR_KEYWORDS:
        idx = lower_middle.find(kw.lower())
        if idx != -1 and (kw_pos == -1 or idx < kw_pos):
            kw_pos = idx   # keep the earliest (highest on page) match

    if kw_pos != -1:
        # Translate relative middle-position to absolute text position,
        # then build a symmetric window clamped within the middle region.
        abs_pos   = middle_start + kw_pos
        win_start = max(middle_start, abs_pos - _KW_HALF)
        win_end   = min(middle_end,   win_start + _KW_WINDOW_SIZE)
        kw_window = text[win_start:win_end]
    else:
        # No B2B anchor found — fall back to the raw next 1,500 chars after head.
        kw_window = text[middle_start : middle_start + _KW_WINDOW_SIZE]

    # ── Assemble ──────────────────────────────────────────────────────────────
    parts = [f"[HEADER]\n{head}"]

    if kw_window.strip():
        parts.append(f"[MID-PAGE B2B CONTEXT]\n{kw_window}")

    if foot.strip():
        parts.append(f"[FOOTER]\n{foot}")

    return "\n\n".join(parts)


def build_feedback_context(feedback_list: list[dict]) -> str:
    """
    Format a list of operator rejection records into the Calibration Block
    that is appended to the NLP system prompt at classification time.

    Called by live_run.py once per pipeline run (loaded from DB), then
    passed into classify_lead_full() for every classification call.

    Anti-overfitting design:
      - The block is explicitly framed as "calibration examples", not rules.
      - The injected instruction tells the LLM to reason about SPECIFICITY —
        one rejected company does not condemn its entire product category.
      - Injection cap (n=10 in get_recent_feedback) prevents prompt bloat.

    Returns an empty string if feedback_list is empty (no-op injection).
    """
    if not feedback_list:
        return ""

    lines = [
        "\n## OPERATOR FEEDBACK — Recent Human Rejections (Calibration Only)",
        "",
        "The following leads were manually rejected by the operator with specific reasons.",
        "Use these as calibration examples to sharpen your judgment.",
        "",
        "CRITICAL ANTI-OVERFITTING RULE:",
        "  - These are SPECIFIC rejections about SPECIFIC companies. Do NOT generalize",
        "    them into categorical bans. One rejected plastic-bag company does not mean",
        "    all bag companies are disqualified. One rejected retailer does not mean all",
        "    retailers are disqualified.",
        "  - Only apply a rejection example if the current lead shows the SAME specific",
        "    disqualifying characteristic described in the reason, not merely the same",
        "    product category.",
        "  - If the NLP signals for the current lead clearly CONTRADICT a rejection",
        "    reason (e.g., reason says 'no leather' but lead shows wholesale leather",
        "    catalog), IGNORE that rejection example entirely — the data overrides the",
        "    generalized pattern.",
        "",
        "Recent rejections:",
    ]

    for i, fb in enumerate(feedback_list, 1):
        domain = fb.get("domain", "unknown")
        reason = fb.get("rejection_reason", "")
        conf   = fb.get("nlp_confidence")
        sigs   = fb.get("nlp_signals") or []

        conf_str = f" (NLP confidence was {conf:.0%})" if conf is not None else ""
        sigs_str = f" | NLP signals: {', '.join(sigs[:3])}" if sigs else ""
        lines.append(f"  {i}. [{domain}] Reason: \"{reason}\"{conf_str}{sigs_str}")

    return "\n".join(lines)


def _build_messages(
    text: str,
    hints: list[str],
    feedback_context: str = "",
) -> list[dict]:
    """
    Build the OpenAI messages array for one classification request.

    Uses _build_smart_excerpt() to assemble up to 6,000 characters of the
    most signal-rich content (header + B2B keyword window + footer) instead
    of a naive head truncation at 3,000 characters.

    feedback_context: optional Calibration Block string produced by
    build_feedback_context(). Appended to the system prompt when non-empty.
    """
    excerpt   = _build_smart_excerpt(text)
    hints_str = "\n".join(f"- {h}" for h in hints) if hints else "None detected."

    system_content = _SYSTEM_PROMPT
    if feedback_context:
        system_content = _SYSTEM_PROMPT + feedback_context

    return [
        {"role": "system", "content": system_content},
        {"role": "user",   "content": _USER_PROMPT_TEMPLATE.format(
            text=excerpt,
            hints=hints_str,
        )},
    ]


def _validate_llm_status(raw_status: str) -> str:
    """
    Validate that the LLM-returned status is an exact match to one of the
    VALID_LLM_STATUSES. Returns the status if valid, else UNCLASSIFIED.

    This is the critical safety guard preventing SQLite CHECK constraint
    violations caused by hallucinated or malformed LLM output.
    """
    if raw_status in VALID_LLM_STATUSES:
        return raw_status
    return _FALLBACK_STATUS


def _validate_confidence(raw: float) -> float:
    """Clamp confidence to [0.0, 1.0] regardless of LLM output."""
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return _FALLBACK_CONFIDENCE


def _signals_contain_dropship(signals: list[str]) -> bool:
    """
    Return True if any signal string contains a known dropship marker.

    Called as part of _apply_contradiction_guard() to catch cases where the
    LLM returns QUALIFIED_A but its own signals list contains a dropship
    indicator — a contradiction that reveals prompt echo-leaking or confusion.

    Matching is case-insensitive substring search (no regex needed here).
    """
    signals_blob = " ".join(signals).lower()
    return any(marker.lower() in signals_blob for marker in _DROPSHIP_SIGNAL_MARKERS)


def _apply_contradiction_guard(
    status: str,
    signals: list[str],
) -> str:
    """
    Downgrade QUALIFIED_A to UNCLASSIFIED when the LLM's own signals
    contradict its verdict (i.e., the LLM echoed a dropship phrase while
    still returning QUALIFIED_A).

    Why UNCLASSIFIED and not DISQUALIFIED_C:
      We cannot be certain it is a dropshipper — the LLM may have echoed
      example phrases from the system prompt without the business actually
      being one. UNCLASSIFIED routes the lead to the Class C tab for human
      review, which is the correct outcome: let a human decide.

    Only fires on QUALIFIED_A — QUALIFIED_B and DISQUALIFIED_C are left
    unchanged because a dropship signal in B is expected (it's pending
    verify) and in C it's already disqualified.
    """
    if status == "QUALIFIED_A" and _signals_contain_dropship(signals):
        return "UNCLASSIFIED"
    return status


def _apply_confidence_threshold(
    status: str,
    confidence: float,
    is_oem_brand: bool,
    is_leather_relevant: bool = True,
) -> str:
    """
    Apply the canonical confidence→status mapping from C-core/02-target-audience.md.

    Rules (evaluated in priority order):
      0. Leather relevance gate: if is_leather_relevant is False the business
         has no connection to leather/accessories/fashion — force DISQUALIFIED_C
         regardless of any other signal. This prevents irrelevant industries
         from leaking into Class A when the LLM is given ambiguous content.
      1. OEM Override: if is_oem_brand AND confidence >= CONFIDENCE_OEM_OVERRIDE
         → always QUALIFIED_A. OEM brands are unconditionally Class A because
         they have existing manufacturing volume and are KritiKaal's ideal customer.
      2. Standard thresholds:
           >= 0.75  → QUALIFIED_A
           >= 0.60  → QUALIFIED_B_PENDING_VERIFY
           <  0.60  → DISQUALIFIED_C

    Note: Tier-1 fast-disqualify results (DISQUALIFIED_C, confidence=1.0 or 0.95)
    never reach this function — they are returned before the LLM is called.
    """
    # Rule 0 — leather relevance gate
    if not is_leather_relevant:
        return "DISQUALIFIED_C"

    if is_oem_brand and confidence >= CONFIDENCE_OEM_OVERRIDE:
        return "QUALIFIED_A"

    if confidence >= CONFIDENCE_THRESHOLD_A:
        return "QUALIFIED_A"
    if confidence >= CONFIDENCE_THRESHOLD_B:
        return "QUALIFIED_B_PENDING_VERIFY"
    return "DISQUALIFIED_C"


def _parse_llm_json(raw_content: str) -> tuple[str, float, list[str], bool, bool, bool]:
    """
    Parse the LLM JSON response string into
    (status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict).

    Validation guards:
      - status:              must be in VALID_LLM_STATUSES → else UNCLASSIFIED
      - confidence:          clamped to [0.0, 1.0]
      - signals:             list of strings; defaults to []
      - is_oem_brand:        boolean from LLM; defaults to False on parse failure
      - is_leather_relevant: boolean from LLM; defaults to True on parse failure
                             (conservative: unknown relevance passes through rather
                              than silently disqualifying a valid lead)
      - has_halachic_conflict: boolean from LLM; defaults to False on parse failure

    Turkish Disruption Score Processing:
      If the signals array contains "turkey_disruption_score:X.XX", it is kept in the
      signals array and will be inserted into the database as-is for phase 1 query filtering.

    NOTE: confidence thresholds are NOT applied here — that is the
    responsibility of _apply_confidence_threshold(), called by the public
    entry points after receiving this raw parse result.

    Returns (status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict).
    """
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        return (_FALLBACK_STATUS, _FALLBACK_CONFIDENCE, [], False, True, False)

    status               = _validate_llm_status(parsed.get("status", ""))
    confidence           = _validate_confidence(parsed.get("confidence", 0.0))
    signals              = parsed.get("signals", [])
    is_oem_brand         = bool(parsed.get("is_oem_brand", False))
    is_leather_relevant  = bool(parsed.get("is_leather_relevant", True))
    has_halachic_conflict = bool(parsed.get("has_halachic_conflict", False))

    if not isinstance(signals, list):
        signals = []

    return (status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict)


async def _call_openai(
    client: openai.AsyncOpenAI,
    text: str,
    hints: list[str],
    model: str = "gpt-4o-mini",
    feedback_context: str = "",
) -> tuple[str, float, list[str], bool, bool, bool, TokenUsage]:
    """
    Execute one OpenAI chat completion with JSON mode enforced.

    Uses response_format={"type": "json_object"} to guarantee parseable JSON.
    Model defaults to gpt-4o-mini for cost efficiency.

    feedback_context: optional Calibration Block string from build_feedback_context().
    Injected into the system prompt when non-empty.

    Returns (status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict, token_usage).
    NOTE: confidence thresholds are NOT applied here — callers must call
    _apply_confidence_threshold() on the returned values.
    On any API exception returns (UNCLASSIFIED, 0.0, [], False, True, False, _ZERO_USAGE).
    """
    messages = _build_messages(text, hints, feedback_context=feedback_context)

    try:
        response = await client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0.1,    # low temperature: deterministic classification
            max_tokens=400,     # enlarged for 6,000-char smart excerpt + turkish signals + is_leather_relevant
        )
        raw_content = response.choices[0].message.content or ""
        status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict = _parse_llm_json(raw_content)
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        return (status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict, usage)

    except openai.APITimeoutError:
        # OpenAI call exceeded 45s timeout — propagate so caller can handle
        raise

    except openai.RateLimitError:
        return (_FALLBACK_STATUS, _FALLBACK_CONFIDENCE, [], False, True, False, _ZERO_USAGE)

    except openai.APIStatusError:
        return (_FALLBACK_STATUS, _FALLBACK_CONFIDENCE, [], False, True, False, _ZERO_USAGE)

    except Exception:
        # Any other exception (network, JSON parse, etc.) → fallback
        return (_FALLBACK_STATUS, _FALLBACK_CONFIDENCE, [], False, True, False, _ZERO_USAGE)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def classify_lead(
    text_payload: str,
    client: Optional[openai.AsyncOpenAI] = None,
    model: str = "gpt-4o-mini",
    feedback_context: str = "",
) -> tuple[str, float]:
    """
    Two-tier classification of a lead's text payload.

    Returns a (status, confidence) tuple where status is always a valid
    value from VALID_LLM_STATUSES, safe to write into leads.status.

    Tier 1 (local heuristics — zero cost, synchronous):
      Immediately returns DISQUALIFIED_C for:
        - Empty, too-short, or non-Hebrew pages
        - Known error / parked-page signatures
        - Explicit (non-negated) dropship signal patterns
        - Halachic material incompatibility (including new keywords)

    Tier 2 (OpenAI JSON mode — cost incurred only if Tier 1 passes):
      Sends text + Tier 1 Class A hints to OpenAI.
      Extracts Turkish disruption signals and has_halachic_conflict flag.
      Validates the response against VALID_LLM_STATUSES before returning.
      Falls back to UNCLASSIFIED on API errors or low-confidence outputs.

    If client is None and Tier 2 is required, returns UNCLASSIFIED.
    This allows the module to run in offline/test mode via Tier 1 alone.

    Args:
        text_payload: Plain-text page body from scrapers.strip_html_to_text().
        client:       Instantiated openai.AsyncOpenAI client (inject from caller).
        model:        OpenAI model name. Defaults to gpt-4o-mini.

    Returns:
        (status: str, confidence: float)
    """
    # --- Tier 1 ---
    tier1_result = _tier1_check(text_payload)
    if tier1_result is not None:
        return tier1_result

    # --- Tier 2 ---
    if client is None:
        # No client provided; cannot classify without LLM
        return (_FALLBACK_STATUS, _FALLBACK_CONFIDENCE)

    hints = _extract_class_a_hints(text_payload)
    status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict, _usage = await _call_openai(
        client, text_payload, hints, model=model, feedback_context=feedback_context
    )
    final_status = _apply_confidence_threshold(status, confidence, is_oem_brand, is_leather_relevant)
    final_status = _apply_contradiction_guard(final_status, signals)
    return (final_status, confidence)


# ---------------------------------------------------------------------------
# Extended entry point — returns signals for lead_classifications table
# ---------------------------------------------------------------------------

async def classify_lead_full(
    text_payload: str,
    client: Optional[openai.AsyncOpenAI] = None,
    model: str = "gpt-4o-mini",
    feedback_context: str = "",
) -> tuple[str, float, list[str], str, TokenUsage]:
    """
    Extended version of classify_lead that also returns signals, model_version,
    and token usage for direct insertion into lead_classifications + cost tracking.

    STEP 1 (NLP Tuning) Enhancement:
      - Signals now include Turkish disruption indicators (TURKEY_ORIGIN, SUPPLY_DISRUPTION,
        POST_EMBARGO_SIGNAL) extracted by the LLM.
      - Signals array includes "turkey_disruption_score:X.XX" (if any Turkish signals detected)
        for Phase 1 query filtering and lead ranking.
      - Has_halachic_conflict flag is computed by LLM and informs Tier 1 checks.

    Returns:
        (status, confidence, signals, model_version, token_usage)
        where model_version is "tier1" if Tier 1 fired, else the model name.
        signals includes Turkish disruption scores for downstream SQL filtering.
    """
    tier1_result = _tier1_check(text_payload)
    if tier1_result is not None:
        status, confidence = tier1_result
        return (status, confidence, [], "tier1", _ZERO_USAGE)

    if client is None:
        return (_FALLBACK_STATUS, _FALLBACK_CONFIDENCE, [], "tier1_only", _ZERO_USAGE)

    hints = _extract_class_a_hints(text_payload)
    status, confidence, signals, is_oem_brand, is_leather_relevant, has_halachic_conflict, usage = await _call_openai(
        client, text_payload, hints, model=model, feedback_context=feedback_context
    )
    # Apply canonical confidence→status mapping (leather gate + OEM override + thresholds)
    final_status = _apply_confidence_threshold(status, confidence, is_oem_brand, is_leather_relevant)
    # Apply contradiction guard (dropship signals in a QUALIFIED_A response)
    final_status = _apply_contradiction_guard(final_status, signals)
    return (final_status, confidence, signals, model, usage)


# ---------------------------------------------------------------------------
# OpenAI client factory
# ---------------------------------------------------------------------------

def build_openai_client(api_key: Optional[str] = None, timeout_seconds: float = 45.0) -> openai.AsyncOpenAI:
    """
    Build and return an AsyncOpenAI client with strict timeout.
    Reads OPENAI_API_KEY from environment if api_key is not provided.
    Raises ValueError if no key is available.

    CRITICAL: timeout_seconds must be set to prevent indefinite API hangs.
    Default 45s covers normal API latency but kills slow/broken connections.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
            "or pass api_key explicitly to build_openai_client()."
        )
    # Sprint 10.5+ CRITICAL FIX: Strict timeout on OpenAI client (was missing, causing hangs)
    # Timeout applies to all HTTP operations (connect, read, write, pool)
    return openai.AsyncOpenAI(
        api_key=key,
        timeout=timeout_seconds,
    )
