"""
KritiKaal Leads Hunter — Government Procurement Agent (Sprint 7A)
File: T-tools/procurement_agent.py
Governed by: B-brain/01-tech-stack.md (Iron Principles 1, 2, 4, 5)

Responsibilities (SRP boundary):
  - Mine the Israeli government procurement portal (mr.gov.il) for
    recent tender winners and registered suppliers in the leather / accessories
    / industrial-safety product categories.
  - Two-phase discovery:
      Phase 1 — Serper queries targeting mr.gov.il: extract Israeli company
                 names (Hebrew בע"מ entities) from snippet / title text.
                 Results from gov.il are intentionally NOT passed through
                 parse_response() (gov.il is in _AGGREGATOR_DOMAINS), so
                 company names are pulled from the raw Serper JSON.
      Phase 2 — Convert extracted company names into site:.co.il Serper
                 queries to locate their own websites.
  - Also runs a set of credential-signal queries that find companies which
    publicly advertise government supplier credentials on their own .co.il site.

Vector: V1_PROCUREMENT

This module does NOT:
  - Run NLP classification.
  - Write to SQLite.
  - Override _safe_request() — inherits SocialFootprintAgent's Serper POST.
"""

from __future__ import annotations

import asyncio
import random
import re
import time

import aiohttp

from scrapers import (
    DELAY_MIN,
    DELAY_MAX,
    AgentResult,
    AntiBotSignal,
    SocialFootprintAgent,
    _apply_universal_query_filters,
)

# ---------------------------------------------------------------------------
# Hebrew company name pattern — same as competitor_agent.py
# ---------------------------------------------------------------------------

_HEBREW_BVM_RE = re.compile(
    r'([\u05D0-\u05EA][\u05D0-\u05EA \-\'\"]{1,35}?)\s+בע["\u05F4\']\u05DE',
    re.UNICODE,
)

# ---------------------------------------------------------------------------
# Phase 1 — Government portal queries
# These are NOT site:.co.il — they deliberately target gov.il.
# Names extracted from snippets feed Phase 2 site:.co.il queries.
# ---------------------------------------------------------------------------

_PROCUREMENT_PORTAL_QUERIES: list[str] = [
    # Tender winners / registered suppliers on the central government
    # procurement portal (mr.gov.il = מרכז הרכש הממשלתי)
    'site:mr.gov.il "מוצרי עור" ספק',
    'site:mr.gov.il "תיקים" OR "ארנקים" ספק זוכה',
    'site:mr.gov.il "אביזרי עור" OR "ציוד מגן"',
    'site:mr.gov.il "כפפות עור" OR "סינרי עור" ספק',
    'site:mr.gov.il "ייצור תיקים" OR "ייצור ארנקים"',
    # Other government / IDF procurement contexts
    'site:idf.il "ספק מאושר" "עור" OR "תיקים"',
    'site:gov.il "מכרז" "מוצרי עור" זוכה',
    'site:gov.il "ספק מאושר" "תיקים" OR "ארנקים" OR "כפפות"',
]

# ---------------------------------------------------------------------------
# Phase 2 — Direct credential-signal queries (companies on their own sites)
# These ARE site:.co.il and pass through standard parse_response().
# ---------------------------------------------------------------------------

_CREDENTIAL_SIGNAL_QUERIES: list[str] = [
    '"ספק מורשה" "מרכז רכש" "עור" OR "תיקים" site:.co.il',
    '"ספק מאושר" "משרד הביטחון" "עור" OR "תיקים" site:.co.il',
    '"זוכה מכרז" "עור" OR "ארנקים" OR "תיקים" ישראל site:.co.il',
    '"ספק ממשלתי" "מוצרי עור" ישראל site:.co.il',
    '"מרכז הרכש" "ספק" "עור" ישראל site:.co.il',
    '"משרד הביטחון" "ספק" "כפפות" OR "ציוד מגן" site:.co.il',
    '"idf" OR "צה\"ל" "ספק" "ביגוד" OR "ציוד" "עור" site:.co.il',
    '"ISO 9001" "ייצור" "עור" OR "תיקים" ישראל site:.co.il',
]

# Serper query template for Phase 2 company-name follow-up
_COMPANY_QUERY_TEMPLATES: list[str] = [
    '"{name}" site:.co.il',
    '"{name}" מוצרי עור ישראל',
]

# Hard cap on Phase 2 follow-up queries per portal query result set
_MAX_PHASE2_QUERIES_PER_PORTAL: int = 8


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class ProcurementAgent(SocialFootprintAgent):
    """
    Two-phase government procurement discovery agent.

    Phase 1 mines Serper results for gov.il procurement portal pages,
    extracting Hebrew company names (בע"מ entities) from snippet text.

    Phase 2 searches those company names at site:.co.il plus runs a set
    of direct credential-signal queries that find companies advertising
    their government supplier status on their own websites.

    All gov.il results are intentionally bypassed for domain extraction
    (gov.il is in _AGGREGATOR_DOMAINS) — only snippet text is used.
    """

    # -------------------------------------------------------------------------
    # Abstract method stubs
    # -------------------------------------------------------------------------

    async def build_queries(self) -> list[str]:
        """Not called — this agent overrides run() with a two-phase flow."""
        return []

    async def parse_response(
        self,
        raw_response: dict,
        query: str,
    ) -> list[AgentResult]:
        """
        Delegates to SocialFootprintAgent.parse_response() — used only during
        Phase 2 credential-signal queries and company-name follow-ups.
        Overrides the vector to V1_PROCUREMENT.
        """
        results = await SocialFootprintAgent.parse_response(self, raw_response, query)
        for r in results:
            r.vector = "V1_PROCUREMENT"
        return results

    # -------------------------------------------------------------------------
    # Main orchestration — overrides ScraperAgent.run()
    # -------------------------------------------------------------------------

    async def run(self, session: aiohttp.ClientSession) -> list[AgentResult]:
        """
        Two-phase procurement discovery.

        Phase 1 — Portal name extraction:
          Issue Serper queries targeting gov.il procurement portal pages.
          Parse raw Serper JSON directly (bypassing is_aggregator_domain filter)
          to extract Hebrew company names from snippet + title text.
          Convert extracted names into Phase 2 follow-up queries.

        Phase 2 — Company website resolution:
          a. Follow-up queries for extracted company names at site:.co.il.
          b. Direct credential-signal queries on site:.co.il.
          Both run through standard Serper + V3 enrichment pipeline.
        """
        start = time.monotonic()
        all_results: list[AgentResult] = []

        try:
            # ── Phase 1: Portal name extraction ──────────────────────────────
            phase2_queries: list[str] = []

            for query in _PROCUREMENT_PORTAL_QUERIES:
                self._run_log.queries_attempted += 1
                try:
                    await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                    raw = await self._safe_request(session, query)
                    if raw is None:
                        continue

                    names = self._extract_names_from_serper(raw)
                    self._log_event(
                        "PROCUREMENT_PORTAL_SCAN",
                        query=query,
                        names_found=len(names),
                    )

                    for name in names[:_MAX_PHASE2_QUERIES_PER_PORTAL]:
                        for tmpl in _COMPANY_QUERY_TEMPLATES:
                            phase2_queries.append(
                                _apply_universal_query_filters(
                                    tmpl.format(name=name)
                                )
                            )

                except AntiBotSignal as exc:
                    self._run_log.antibot_triggers += 1
                    self._run_log.status = "PARTIAL"
                    self._log_event("ANTIBOT", query=query, detail=str(exc))

                except Exception as exc:
                    self._run_log.status = "PARTIAL"
                    self._log_event("QUERY_ERROR", query=query, error=str(exc))

            # ── Phase 2a: Follow-up queries for extracted company names ───────
            all_results.extend(
                await self._run_serper_batch(session, phase2_queries)
            )

            # ── Phase 2b: Direct credential-signal queries ────────────────────
            credential_queries = [
                _apply_universal_query_filters(q)
                for q in _CREDENTIAL_SIGNAL_QUERIES
            ]
            all_results.extend(
                await self._run_serper_batch(session, credential_queries)
            )

            self._run_log.results_collected = len(all_results)

        except Exception as exc:
            self._run_log.status = "CRASHED"
            self._run_log.error_message = str(exc)
            self._log_event("CRASH", error=str(exc))
            raise

        finally:
            self._run_log.duration_seconds = round(time.monotonic() - start, 2)
            self._flush_run_log()

        return all_results

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _extract_names_from_serper(self, raw: dict) -> list[str]:
        """
        Extract Hebrew company names (בע"מ entities) from Serper organic results.

        Scans title + snippet text of every organic result for _HEBREW_BVM_RE
        matches. Returns deduplicated list of company name strings.
        """
        seen: set[str] = set()
        names: list[str] = []

        organic = raw.get("organic") or []
        for item in organic:
            text = f"{item.get('title', '')} {item.get('snippet', '')}"
            for match in _HEBREW_BVM_RE.finditer(text):
                name = match.group(1).strip()
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)

        return names

    async def _run_serper_batch(
        self,
        session: aiohttp.ClientSession,
        queries: list[str],
    ) -> list[AgentResult]:
        """
        Run a batch of Serper queries through the standard parse + V3 enrich
        pipeline. Returns all collected AgentResult objects.
        """
        results: list[AgentResult] = []

        for query in queries:
            self._run_log.queries_attempted += 1
            try:
                raw = await self._safe_request(session, query)
                if raw is None:
                    continue

                parsed = await self.parse_response(raw, query)

                enriched = await asyncio.gather(
                    *[self._enrich_with_direct_html(session, r) for r in parsed],
                    return_exceptions=True,
                )
                for item in enriched:
                    if isinstance(item, AgentResult):
                        results.append(item)
                    elif isinstance(item, Exception):
                        self._log_event("ENRICH_ERROR", error=str(item))

            except AntiBotSignal as exc:
                self._run_log.antibot_triggers += 1
                self._run_log.status = "PARTIAL"
                self._log_event("ANTIBOT", query=query, detail=str(exc))

            except Exception as exc:
                self._run_log.status = "PARTIAL"
                self._log_event("QUERY_ERROR", query=query, error=str(exc))

        return results
