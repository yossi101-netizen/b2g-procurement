"""
KritiKaal Leads Hunter — Social-Only Discovery Agent (Sprint 7B)
File: T-tools/social_agent.py
Governed by: B-brain/01-tech-stack.md (Iron Principles 1, 2, 4, 5)

Responsibilities (SRP boundary):
  - Surface Israeli leather / accessories businesses that operate primarily
    or exclusively via a Facebook business page (no independent .co.il site
    in Serper's index, or their site is not well-indexed).
  - Two-phase discovery:
      Phase 1 — Serper queries with site:facebook.com: extract business
                 names from Facebook page titles (strip "| Facebook" suffix)
                 and optionally extract .co.il URLs from snippet text.
      Phase 2 — Resolve extracted names to their own websites via
                 site:.co.il Serper queries, then V3-enrich.
  - Any .co.il domain found directly in a Phase 1 snippet is also added
    as a direct AgentResult with vector V1_SOCIAL_PAGE.

Vector: V1_SOCIAL_PAGE

Note on aggregator filter:
  facebook.com is in _AGGREGATOR_DOMAINS, so standard parse_response()
  filters it out. Phase 1 reads the raw Serper JSON directly and extracts
  names/URLs from title + snippet fields without domain resolution.

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
    extract_whatsapp_numbers,
    select_best_phone,
    is_aggregator_domain,
    is_hard_skip_domain,
)
from db_init import normalize_domain

# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

# Match a bare .co.il domain in snippet text
_CO_IL_DOMAIN_RE = re.compile(
    r'(?:https?://)?(?:www\.)?'
    r'([\w\-]+\.co\.il)'
    r'(?:[/\s"\']|$)',
    re.IGNORECASE,
)

# Strip Facebook / Instagram suffix from page title
# e.g. "חנות עור ישראל | Facebook" → "חנות עור ישראל"
_SOCIAL_TITLE_SUFFIX_RE = re.compile(
    r'\s*[|\-]\s*(?:Facebook|Instagram|LinkedIn|Twitter|X|TikTok)\s*$',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Phase 1 — Facebook/social page queries
# Targets the social platform directly — these results are filtered by
# is_aggregator_domain() in standard parse_response(), so we parse raw.
# ---------------------------------------------------------------------------

_SOCIAL_PLATFORM_QUERIES: list[str] = [
    # Facebook — Hebrew leather / accessories businesses
    'site:facebook.com "מוצרי עור" ישראל עסק',
    'site:facebook.com "תיקי עור" ישראל "חנות" OR "מפעל"',
    'site:facebook.com "ארנקי עור" ישראל עסק',
    'site:facebook.com "יבואן" "מוצרי עור" ישראל',
    'site:facebook.com "אביזרי עור" ישראל עסק',
    'site:facebook.com "עור ישראל" קולקציה OR מותג',
    'site:facebook.com "כפפות עור" ישראל עסק OR מפיץ',
    'site:facebook.com "חגורות עור" ישראל יצרן OR יבואן',
    # Instagram — visual-first brands sometimes Facebook-linked
    'site:instagram.com "מוצרי עור" ישראל מותג',
    'site:instagram.com "leather" ישראל brand OR מותג',
]

# Serper follow-up templates for extracted business names
_NAME_QUERY_TEMPLATES: list[str] = [
    '"{name}" site:.co.il',
    '"{name}" ישראל מוצרי עור',
]

# Hard cap on Phase 2 follow-up queries per social query result set
_MAX_PHASE2_QUERIES_PER_SOCIAL: int = 6


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class SocialOnlyAgent(SocialFootprintAgent):
    """
    Two-phase social-platform discovery agent.

    Phase 1 mines Serper results for Facebook business pages of Israeli
    leather businesses. Since facebook.com is in _AGGREGATOR_DOMAINS, raw
    Serper JSON is read directly. Business names are extracted from page
    titles; .co.il domains extracted from snippets become direct results.

    Phase 2 searches extracted business names at site:.co.il via standard
    Serper + V3 enrichment.
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
        Delegates to SocialFootprintAgent.parse_response() for Phase 2
        site:.co.il queries. Overrides vector to V1_SOCIAL_PAGE.
        """
        results = await SocialFootprintAgent.parse_response(self, raw_response, query)
        for r in results:
            r.vector = "V1_SOCIAL_PAGE"
        return results

    # -------------------------------------------------------------------------
    # Main orchestration — overrides ScraperAgent.run()
    # -------------------------------------------------------------------------

    async def run(self, session: aiohttp.ClientSession) -> list[AgentResult]:
        """
        Two-phase social-only discovery.

        Phase 1 — Social platform scan:
          Issue Serper queries targeting Facebook/Instagram pages.
          Parse raw JSON to extract:
            (a) Business names from page titles (for Phase 2 follow-ups).
            (b) .co.il domains from snippet text (added as direct results).

        Phase 2 — Website resolution:
          Run site:.co.il follow-up queries for extracted names through the
          standard Serper + V3 enrichment pipeline.
        """
        start = time.monotonic()
        all_results: list[AgentResult] = []

        try:
            phase2_queries: list[str] = []

            # ── Phase 1: Social platform scan ─────────────────────────────────
            for query in _SOCIAL_PLATFORM_QUERIES:
                self._run_log.queries_attempted += 1
                try:
                    await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                    raw = await self._safe_request(session, query)
                    if raw is None:
                        continue

                    names, direct = self._extract_from_social_results(raw)

                    self._log_event(
                        "SOCIAL_PAGE_SCAN",
                        query=query,
                        names_found=len(names),
                        direct_domains=len(direct),
                    )

                    # Direct .co.il domains found in snippets — V3 enrich now
                    if direct:
                        enriched = await asyncio.gather(
                            *[self._enrich_with_direct_html(session, r)
                              for r in direct],
                            return_exceptions=True,
                        )
                        for item in enriched:
                            if isinstance(item, AgentResult):
                                all_results.append(item)
                            elif isinstance(item, Exception):
                                self._log_event("ENRICH_ERROR", error=str(item))

                    # Business names → Phase 2 follow-up queries
                    for name in names[:_MAX_PHASE2_QUERIES_PER_SOCIAL]:
                        for tmpl in _NAME_QUERY_TEMPLATES:
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

            # ── Phase 2: Name-to-website resolution ───────────────────────────
            for query in phase2_queries:
                self._run_log.queries_attempted += 1
                try:
                    raw = await self._safe_request(session, query)
                    if raw is None:
                        continue

                    parsed = await self.parse_response(raw, query)

                    enriched = await asyncio.gather(
                        *[self._enrich_with_direct_html(session, r)
                          for r in parsed],
                        return_exceptions=True,
                    )
                    for item in enriched:
                        if isinstance(item, AgentResult):
                            all_results.append(item)
                        elif isinstance(item, Exception):
                            self._log_event("ENRICH_ERROR", error=str(item))

                except AntiBotSignal as exc:
                    self._run_log.antibot_triggers += 1
                    self._run_log.status = "PARTIAL"
                    self._log_event("ANTIBOT", query=query, detail=str(exc))

                except Exception as exc:
                    self._run_log.status = "PARTIAL"
                    self._log_event("QUERY_ERROR", query=query, error=str(exc))

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

    def _extract_from_social_results(
        self,
        raw: dict,
    ) -> tuple[list[str], list[AgentResult]]:
        """
        Parse raw Serper JSON from social-platform queries.

        Returns:
            names   — deduplicated business names extracted from page titles
                      (Facebook "| Facebook" suffix stripped).
            direct  — AgentResult objects for .co.il domains found in snippets.
        """
        seen_names:   set[str] = set()
        seen_domains: set[str] = set()
        names:        list[str] = []
        direct:       list[AgentResult] = []

        organic = raw.get("organic") or []
        for item in organic:
            title   = item.get("title", "")
            snippet = item.get("snippet", "")
            source  = item.get("link", "")

            # ── Extract business name from page title ──────────────────────
            clean = _SOCIAL_TITLE_SUFFIX_RE.sub("", title).strip()
            if clean and clean not in seen_names and len(clean) > 3:
                seen_names.add(clean)
                names.append(clean)

            # ── Extract .co.il domain from snippet ─────────────────────────
            phones = extract_whatsapp_numbers(snippet)
            for match in _CO_IL_DOMAIN_RE.finditer(snippet):
                domain = normalize_domain(match.group(1))
                if not domain:
                    continue
                if is_aggregator_domain(domain) or is_hard_skip_domain(domain):
                    continue
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
                direct.append(AgentResult(
                    entity_name= clean or domain,
                    domain=      domain,
                    whatsapp=    select_best_phone(phones),
                    raw_text=    snippet,
                    source_url=  source,
                    vector=      "V1_SOCIAL_PAGE",
                ))

        return names, direct
