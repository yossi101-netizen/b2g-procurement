"""
KritiKaal Leads Hunter — Instagram Signal Agent  (V1-Social)
File: T-tools/instagram_agent.py
Governed by: B-brain/01-tech-stack.md §2 (V1-Social vector)

Purpose:
  Detect OEM and collection-drop signals from publicly indexed Instagram
  posts — without directly scraping Instagram or requiring auth.

Architecture — V1-Social (Serper Web Search, site:instagram.com):
  Google indexes public Instagram posts and returns them as organic results.
  Each result has a title and snippet that often contains caption text.
  We query Serper with `site:instagram.com "{entity_name}"` + OEM vocabulary
  and score the returned snippets for manufacturing/collection intent signals.

  This approach:
    ✅ Uses the existing V1 (Serper) infrastructure — no new API
    ✅ Requires zero Instagram auth or direct scraping
    ✅ Respects rate limits (Serper credits, not Instagram)
    ✅ Stays within the approved Tri-Vector architecture

Signal scoring:
  Each matched vocabulary term scores +1. A score >= IG_MIN_SCORE (default 2)
  in live_run.py triggers automatic promotion to QUALIFIED_A.

Integration:
  Called from live_run.py Phase 2.5 on UNCLASSIFIED and QUALIFIED_B leads.
  Results are written to lead_classifications with model_version='ig_signal_v1'.

This module does NOT:
  - Access Instagram directly or require cookies / OAuth
  - Write to leads.db directly (callers use insert_classification + upsert)
  - Classify general web content (NLP is nlp_classifier.py's job)
"""

from dotenv import load_dotenv
load_dotenv()

import re

import aiohttp

from scrapers import SocialFootprintAgent

# ---------------------------------------------------------------------------
# OEM / Collection signal vocabulary
# Covers Hebrew and English terms that appear in captions of brands
# that design locally but commission manufacturing abroad.
# ---------------------------------------------------------------------------

_IG_SIGNAL_VOCABULARY: list[str] = [
    # Collection / seasonal drop signals
    "קולקציה",          # collection
    "קולקציית",         # collection (construct state)
    "collection",
    "new collection",
    "קולקציה חדשה",
    "עונת",             # "season" (e.g., "עונת חורף")
    "drop",             # "collection drop"

    # OEM manufacturing signals
    "מיוצר",            # "manufactured" / "made"
    "ייצור",            # production
    "ייצרנו",           # "we produced/manufactured"
    "עיצוב ישראלי",     # Israeli design
    "עיצוב עצמי",       # own design
    "עיצבנו",           # "we designed"
    "made to order",
    "custom made",
    "לפי הזמנה",        # to order

    # Brand identity signals
    "מותג",             # brand
    "המותג שלנו",       # our brand
    "המותג",
    "בית המותג",        # brand house
    "הקולקציה שלנו",    # our collection

    # Wholesale / B2B signals visible on IG
    "סיטונאי",          # wholesaler
    "מחיר סיטונאי",     # wholesale price
    "לעסקים",           # for businesses
    "b2b",

    # Manufacturing country signals (OEM confirmation)
    "טורקיה",           # Turkey
    "turkey",
    "איטליה",           # Italy
    "italy",
    "סין",              # China (OEM, not dropship)
    "פורטוגל",          # Portugal
    "ספרד",             # Spain
]

# Compile patterns once for performance
_IG_PATTERNS: list[re.Pattern] = [
    re.compile(re.escape(term), re.IGNORECASE | re.UNICODE)
    for term in _IG_SIGNAL_VOCABULARY
]

# ---------------------------------------------------------------------------
# Instagram Signal Agent
# ---------------------------------------------------------------------------

class InstagramSignalAgent(SocialFootprintAgent):
    """
    Searches for Instagram posts from a known business entity using Serper
    web search (V1-Social: site:instagram.com queries).

    Inherits all HTTP, retry, and rate-limit behaviour from SocialFootprintAgent.
    Override: build_queries() is replaced by enrich_lead(), which drives
    targeted entity-specific queries rather than broad keyword queries.
    """

    # Instagram-specific Serper query templates
    _IG_QUERY_TEMPLATES: list[str] = [
        'site:instagram.com "{name}" קולקציה',
        'site:instagram.com "{name}" עיצוב עור',
        'site:instagram.com "{name}" collection',
        'site:instagram.com "{name}" מותג',
    ]

    async def build_queries(self) -> list[str]:
        """Not used in this agent — see enrich_lead()."""
        return []

    def _score_text(self, text: str) -> tuple[int, list[str]]:
        """
        Score a text snippet against _IG_SIGNAL_VOCABULARY.

        Returns (score, matched_signals) where score is the count of
        distinct vocabulary terms matched (not total occurrences).
        """
        matched: list[str] = []
        for term, pattern in zip(_IG_SIGNAL_VOCABULARY, _IG_PATTERNS):
            if pattern.search(text) and term not in matched:
                matched.append(term)
        return len(matched), matched

    async def enrich_lead(
        self,
        session: aiohttp.ClientSession,
        entity_name: str,
        domain: str,
    ) -> tuple[int, list[str]]:
        """
        Run Instagram signal detection for one business entity.

        Strategy:
          1. Build entity-specific site:instagram.com queries.
          2. Call Serper for each query; collect organic result titles + snippets.
          3. Score all collected text against _IG_SIGNAL_VOCABULARY.
          4. Return (total_score, list_of_matched_signals).

        Args:
            session:     aiohttp.ClientSession (caller-managed).
            entity_name: Business name from leads.entity_name.
            domain:      Business domain (used for fallback name extraction).

        Returns:
            (score: int, signals: list[str])
            score >= IG_MIN_SCORE (2) in live_run.py → auto-promote to QUALIFIED_A.
        """
        # Build a clean search name: use entity_name if meaningful, else domain stem
        name = entity_name.strip() if entity_name and len(entity_name) > 3 else \
               domain.split(".")[0]

        queries = [
            tmpl.format(name=name)
            for tmpl in self._IG_QUERY_TEMPLATES
        ]

        all_text: list[str] = []

        for query in queries:
            raw_response = await self._safe_request(session, query)
            if not raw_response:
                continue
            organic = raw_response.get("organic") or []
            for item in organic:
                # Only consider results that genuinely come from instagram.com
                link = item.get("link", "")
                if "instagram.com" not in link:
                    continue
                title   = item.get("title", "")
                snippet = item.get("snippet", "")
                all_text.append(f"{title} {snippet}")

        if not all_text:
            return (0, [])

        combined_text = " ".join(all_text)
        score, signals = self._score_text(combined_text)
        return (score, signals)
