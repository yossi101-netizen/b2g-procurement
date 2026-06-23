"""
KritiKaal Leads Hunter — WhatsApp Outreach Template Engine
File: T-tools/outreach_helper.py

Responsibilities (SRP boundary):
  - Select the correct message template track based on NLP classification
  - Inject lead-specific personalization (company name, detected B2B signals,
    discovery source hint)
  - Build and return the wa.me Click-to-Chat URL with URL-encoded pre-filled text
  - No DB writes, no HTTP requests (pure-function module, zero side effects)

Three template tracks (selected by lead_classifications.category):
  importer     — Company imports / distributes leather goods
  manufacturer — Company manufactures leather goods
  generic      — Insufficient data / DROPSHIPPER / fallback

Called by:
  - dashboard.py (Outreach tab, before log_outreach_attempt)

This module does NOT:
  - Write to SQLite
  - Send any messages
  - Make network requests
"""

from __future__ import annotations

import json
from typing import Optional
from urllib.parse import quote as _url_quote

# ---------------------------------------------------------------------------
# Message templates — Hebrew, professional, non-spammy
#
# Placeholders:
#   {company}      — entity_name (or domain if no name)
#   {signal_hook}  — first detected B2B signal ("יבוא בלעדי" etc.) or ""
#   {source_hint}  — subtle relevance line based on discovery vector or ""
# ---------------------------------------------------------------------------

_TEMPLATE_IMPORTER = (
    "שלום לצוות {company}!\n\n"
    "ראיתי שאתם עוסקים ביבוא ושיווק מוצרי עור בישראל{signal_hook} — "
    "אנחנו KritiKaal, יצרן עור מנוהל בהודו.\n\n"
    "אנחנו עובדים עם יבואנים ישראלים ומציעים:\n"
    "• ייצור Private Label לפי המפרט שלכם\n"
    "• מחירים תחרותיים לעומת ספקים אירופאים\n"
    "• MOQ גמיש החל מ-50 יחידות\n"
    "• פיתוח מוצר ודוגמאות ללא עלות\n\n"
    "האם תשמחו לשמוע יותר? נשמח לתאם שיחה קצרה 🤝"
)

_TEMPLATE_MANUFACTURER = (
    "שלום לצוות {company}!\n\n"
    "ראיתי שאתם עוסקים בתחום ייצור מוצרי עור{signal_hook} — "
    "אנחנו KritiKaal, שותף ייצור מנוהל בהודו.\n\n"
    "אנחנו מתמחים ב:\n"
    "• ייצור תיקים, ארנקים ואביזרי עור לפי הזמנה\n"
    "• עיצוב ופיתוח מוצר מ-A עד Z\n"
    "• כמויות גמישות החל מ-50 יחידות לדגם\n"
    "• משלוח ישיר לישראל עם בקרת איכות\n\n"
    "אם אתם מחפשים שותף ייצור אמין, נשמח להכיר 🤝"
)

_TEMPLATE_GENERIC = (
    "שלום לצוות {company}!\n\n"
    "אנחנו KritiKaal — יצרן עור מנוהל בהודו המתמחה בייצור מוצרי עור "
    "לשוק הישראלי.{source_hint}\n\n"
    "אנחנו מציעים ייצור לפי הזמנה (Private Label), MOQ גמיש, "
    "ואיכות גבוהה במחיר תחרותי.\n\n"
    "אם יש לכם עניין לשמוע יותר, נשמח לדבר 🤝"
)

_TEMPLATES: dict[str, str] = {
    "importer":     _TEMPLATE_IMPORTER,
    "manufacturer": _TEMPLATE_MANUFACTURER,
    "generic":      _TEMPLATE_GENERIC,
}

# NLP category → template track
_TRACK_MAP: dict[str, str] = {
    "IMPORTER":     "importer",
    "MANUFACTURER": "manufacturer",
    "DROPSHIPPER":  "generic",
}

# Discovery vector → subtle context line for generic template
_SOURCE_HINTS: dict[str, str] = {
    "V1_COMPETITOR":          " ראיתי שאתם פועלים בתחום דומה לחברות שכבר עובדות איתנו.",
    "V1_SHOPIFY_FINGERPRINT": " ראיתי את החנות המקוונת שלכם.",
    "V1_PURCHASE_INTENT":     " ראיתי שאתם מחפשים ספק ייצור.",
    "V1_SOCIAL_PAGE":         " ראיתי את הפעילות שלכם ברשתות החברתיות.",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_signal_hook(signals_json: Optional[str]) -> str:
    """
    Extract the first NLP signal from the JSON array and wrap it as
    a parenthetical context phrase.

    Example: '["יבוא בלעדי","מינימום הזמנה"]' → " (שמתי לב: יבוא בלעדי)"
    Returns "" if no usable signal found.
    """
    if not signals_json:
        return ""
    try:
        signals = json.loads(signals_json)
        if signals and isinstance(signals, list):
            first = str(signals[0]).strip()
            if first and len(first) < 40:  # sanity cap
                return f" (שמתי לב: {first})"
    except (json.JSONDecodeError, IndexError, TypeError):
        pass
    return ""


def _build_source_hint(source_vectors: Optional[str]) -> str:
    """
    Return a brief relevance phrase based on how the lead was discovered.
    Used only in the generic template's {source_hint} placeholder.
    Returns "" for unknown or empty vectors.
    """
    if not source_vectors:
        return ""
    for vector, hint in _SOURCE_HINTS.items():
        if vector in source_vectors:
            return hint
    return ""


def _clean_company_name(lead: dict) -> str:
    """
    Return a display-friendly company name.
    Prefers entity_name; falls back to domain; strips long URL-style titles.
    """
    name = (lead.get("entity_name") or "").strip()
    domain = (lead.get("domain") or "").strip()

    # If entity_name looks like a full page title (long, contains |, -, common)
    # fall back to just the domain for a cleaner greeting
    if not name or len(name) > 45 or "|" in name:
        # Use domain root label: "acme.co.il" → "Acme"
        root = domain.split(".")[0].replace("-", " ").title() if domain else ""
        return root or "צוות החברה"
    return name


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_wa_link(lead: dict) -> tuple[Optional[str], Optional[str], str]:
    """
    Build a personalized WhatsApp wa.me Click-to-Chat link for the given lead.

    Args:
        lead: dict with at minimum 'whatsapp'. Enriched if 'entity_name',
              'domain', 'classification', 'source_vectors', 'signals' are
              present (all optional — graceful fallback for missing fields).

    Returns:
        (message_text, wa_link, template_track)

        message_text  — the full Hebrew message string (for preview)
        wa_link       — "https://wa.me/{phone}?text={encoded_message}"
        template_track — "importer" | "manufacturer" | "generic"

        Returns (None, None, "generic") if lead has no WhatsApp number.
    """
    phone_raw = lead.get("whatsapp")
    if not phone_raw:
        return (None, None, "generic")

    # Normalise to pure digits starting with 972
    phone_digits = "".join(c for c in str(phone_raw) if c.isdigit())
    if not phone_digits.startswith("972"):
        phone_digits = "972" + phone_digits.lstrip("0")

    classification = (lead.get("classification") or "").upper().strip()
    track          = _TRACK_MAP.get(classification, "generic")
    company        = _clean_company_name(lead)
    signal_hook    = _build_signal_hook(lead.get("signals"))
    source_hint    = _build_source_hint(lead.get("source_vectors"))

    message = _TEMPLATES[track].format(
        company=company,
        signal_hook=signal_hook,
        source_hint=source_hint,
    )

    wa_link = f"https://wa.me/{phone_digits}?text={_url_quote(message)}"
    return (message, wa_link, track)


def track_display_name(track: str) -> str:
    """Human-readable label for a template track."""
    return {
        "importer":               "Importer track",
        "manufacturer":           "Manufacturer track",
        "generic":                "Generic track",
        "phase1_importer":        "Phase 1 — Turkey-disrupted (Importer)",
        "phase1_manufacturer":    "Phase 1 — Domestic Manufacturer",
    }.get(track, track)


# ---------------------------------------------------------------------------
# Phase 1 Templates — Section 4: WhatsApp Outreach Dual Boots Flow
#
# Two precision tracks designed for the Israeli market Phase 1 campaign:
#   phase1_importer     — Turkey-disrupted brands (supply chain disruption angle)
#   phase1_manufacturer — Domestic Israeli producers (cost-saving angle)
#
# These replace the generic Workspace tab templates for leads in the
# Phase 1 Operations tab. The messaging is more direct and tightly
# tied to the business pain-point identified by the NLP signals.
# ---------------------------------------------------------------------------

_TEMPLATE_PHASE1_IMPORTER = (
    "שלום {company},\n\n"
    "אני יוסי, מנכ\"ל KritiKaal — חברת ייצור מנוהל להודו.\n"
    "ראיתי שאתם עובדים עם ספקים טורקיים.\n"
    "מאז מאי 2024 הסחר עם טורקיה מורכב — "
    "ואנחנו מציעים חלופה מלאה בהודו עם בקרת איכות AQL 2.5.\n\n"
    "יש לי עובד על רצפת המפעל בהודו עכשיו. "
    "אפשר שיחת וידאו חיה ממש מהמפעל?\n"
    "15 דקות — אני מבטיח שיהיה שווה."
)

_TEMPLATE_PHASE1_MANUFACTURER = (
    "שלום {company},\n\n"
    "אני יוסי, מנכ\"ל KritiKaal.\n"
    "אתם מייצרים בארץ — עיצוב מדהים. "
    "אבל עלות העבודה הישראלית על כל יחידה גבוהה.\n\n"
    "יש לי הצעה: העיצוב נשאר בתל אביב, "
    "הייצור עובר להודו — עם עור LWG מאושר ובקרת איכות AQL 2.5.\n"
    "אפשר לדבר 15 דקות?"
)

_PHASE1_TEMPLATES: dict[str, str] = {
    "phase1_importer":     _TEMPLATE_PHASE1_IMPORTER,
    "phase1_manufacturer": _TEMPLATE_PHASE1_MANUFACTURER,
}

# Turkish signal tokens that indicate the phase1_importer track
_TURKEY_SIGNAL_TOKENS: frozenset[str] = frozenset({
    "TURKEY_ORIGIN", "SUPPLY_DISRUPTION", "POST_EMBARGO_SIGNAL",
    "turkey_disruption_score", "TURKEY_DISRUPTION",
    "טורקיה", "ייצור טורקי", "עור טורקי", "יבוא מטורקיה",
})


def _has_turkey_origin_signals(signals_json: Optional[str]) -> bool:
    """
    Return True if the signals JSON contains any Turkish disruption token.
    Used to auto-assign phase1_importer vs phase1_manufacturer template.
    """
    if not signals_json:
        return False
    try:
        signals = json.loads(signals_json) if isinstance(signals_json, str) else signals_json
        if not isinstance(signals, list):
            return False
        blob = " ".join(str(s) for s in signals).lower()
        return any(token.lower() in blob for token in _TURKEY_SIGNAL_TOKENS)
    except (json.JSONDecodeError, TypeError):
        return False


def build_phase1_wa_link(
    lead: dict,
    force_track: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], str]:
    """
    Build a Phase 1 WhatsApp link using the Section 4 Hebrew templates.

    Template selection (auto, unless force_track is provided):
      - phase1_importer     if lead has Turkish disruption signals
      - phase1_manufacturer otherwise (domestic manufacturer angle)

    Args:
        lead        : dict with at minimum 'whatsapp'.
        force_track : override auto-selection ('phase1_importer' or
                      'phase1_manufacturer').

    Returns:
        (message_text, wa_link, template_track)
        Returns (None, None, "phase1_importer") if no WhatsApp number.
    """
    phone_raw = lead.get("whatsapp")
    if not phone_raw:
        return (None, None, "phase1_importer")

    # Normalise phone to 972XXXXXXXXX
    phone_digits = "".join(c for c in str(phone_raw) if c.isdigit())
    if not phone_digits.startswith("972"):
        phone_digits = "972" + phone_digits.lstrip("0")

    # Auto-select track
    if force_track in _PHASE1_TEMPLATES:
        track = force_track
    elif _has_turkey_origin_signals(lead.get("signals")):
        track = "phase1_importer"
    else:
        track = "phase1_manufacturer"

    company = _clean_company_name(lead)
    message = _PHASE1_TEMPLATES[track].format(company=company)
    wa_link = f"https://wa.me/{phone_digits}?text={_url_quote(message)}"
    return (message, wa_link, track)
