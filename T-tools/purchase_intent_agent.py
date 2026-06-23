"""
KritiKaal Leads Hunter — Purchase Intent Agent (Sprint 7C)
File: T-tools/purchase_intent_agent.py
Governed by: B-brain/01-tech-stack.md (Iron Principles 1, 2, 4, 5)

Responsibilities (SRP boundary):
  - Discover Israeli B2B companies that have published explicit, active
    signals of sourcing intent — RFQs, supplier search announcements,
    or supply-chain restructuring statements on their own websites or in
    Israeli B2B trade contexts.
  - Standard build_queries() override. All results pass through the
    inherited SocialFootprintAgent.run() pipeline (Serper + V3 enrich).

Vector: V1_PURCHASE_INTENT

Differentiation from lateral_industry_agent.py purchase_intent pack:
  - Lateral pack (8 queries): Company homepages stating sourcing need.
  - This agent (20 queries): Trade press, B2B marketplaces, Yad2 business
    section, WinWin, Chambers of Commerce, export/import service ads,
    and active RFQ / tender announcement contexts.
    Queries use distinct vocabulary (not duplicated from lateral pack).

This module does NOT:
  - Run NLP classification.
  - Write to SQLite.
  - Override _safe_request() or run() — uses inherited pipeline.
"""

from __future__ import annotations

from scrapers import AgentResult, SocialFootprintAgent

# ---------------------------------------------------------------------------
# Query pack — active sourcing / purchase intent signals
#
# Design constraints:
#   1. No query duplicates lateral agent's purchase_intent pack.
#   2. All queries target site:.co.il, trade-press .co.il, or well-indexed
#      Israeli B2B contexts (not job boards — those are in _AGGREGATOR_DOMAINS).
#   3. Vocabulary focuses on RFQ / tender / supplier-search announcements,
#      not general product descriptions.
# ---------------------------------------------------------------------------

_PURCHASE_INTENT_QUERIES: list[str] = [

    # ── Trade press and B2B marketplaces ─────────────────────────────────────
    # Israeli trade press articles covering sourcing decisions
    '"מחפש ספק" "מוצרי עור" OR "תיקים" OR "ארנקים" ישראל site:.co.il',
    '"מחפשת ספק" "עור" OR "אביזרים" ישראל site:.co.il',
    '"בחיפוש אחר ספק" "עור" OR "ייצור" ישראל site:.co.il',
    '"נמצאים בתהליך" "ספק" "עור" OR "תיקים" ישראל site:.co.il',
    # WinWin and Israeli B2B communities (not job boards)
    '"winwin" "ספק עור" OR "יצרן תיקים" ישראל',
    '"מגזין עסקי" "ספק" "מוצרי עור" ישראל site:.co.il',

    # ── Supply-chain restructuring signals ───────────────────────────────────
    '"מחליפים ספק" "עור" OR "תיקים" ישראל site:.co.il',
    '"מחפשים חלופה" "ספק" "עור" OR "ייצור" ישראל site:.co.il',
    '"ספק חדש" "עור" OR "תיקים" OR "ארנקים" ישראל site:.co.il',
    '"שינוי ספק" "מוצרי עור" OR "ייצור" ישראל site:.co.il',
    '"גיוון ספקים" "עור" ישראל site:.co.il',

    # ── RFQ / tender announcement contexts ───────────────────────────────────
    '"בקשה להצעת מחיר" "עור" OR "תיקים" OR "ארנקים" ישראל site:.co.il',
    '"קול קורא" "ספק" "עור" OR "ייצור תיקים" ישראל site:.co.il',
    '"הזמנה להגיש הצעה" "עור" OR "אביזרים" ישראל site:.co.il',
    '"RFQ" "leather" OR "bags" Israel manufacturer site:.co.il',

    # ── Export/import restructuring — companies looking to shift sourcing ─────
    '"יבואן" "מחפש" "ספק ייצור" "עור" ישראל site:.co.il',
    '"מחפשים יצרן" "תיקים" OR "ארנקים" OR "אביזרי עור" site:.co.il',
    '"ייצור בהודו" "עור" OR "תיקים" ישראל site:.co.il',
    '"ייצור באסיה" "עור" OR "תיקים" ישראל site:.co.il',

    # ── Israeli Chamber of Commerce / Exporters Institute ─────────────────────
    '"התאחדות התעשיינים" "עור" OR "תיקים" ספק ישראל site:.co.il',
    '"המכון לייצוא" "עור" OR "תיקים" OR "אביזרים" ישראל site:.co.il',
]


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class PurchaseIntentAgent(SocialFootprintAgent):
    """
    Standard Serper agent targeting active sourcing / purchase-intent signals.

    Overrides build_queries() only — the full Serper + V3 enrichment pipeline
    is inherited from SocialFootprintAgent.run(). Results are tagged with
    vector V1_PURCHASE_INTENT.
    """

    async def build_queries(self) -> list[str]:
        """Return all purchase-intent queries as a flat list."""
        return list(_PURCHASE_INTENT_QUERIES)

    async def parse_response(
        self,
        raw_response: dict,
        query: str,
    ) -> list[AgentResult]:
        """
        Delegates to SocialFootprintAgent.parse_response().
        Overrides vector on all results to V1_PURCHASE_INTENT.
        """
        results = await SocialFootprintAgent.parse_response(self, raw_response, query)
        for r in results:
            r.vector = "V1_PURCHASE_INTENT"
        return results
