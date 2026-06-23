"""
KritiKaal Leads Hunter — Competitor Lookalike Agent
File: T-tools/competitor_agent.py
Governed by: B-brain/01-tech-stack.md (Iron Principles 1, 2, 4, 5)

Responsibilities (SRP boundary):
  - Accept a list of seed competitor domains.
  - For each seed, try known client/testimonial page slugs until a page
    scoring above _MIN_CLIENT_SIGNALS is found.
  - Extract two signal types from the page:
      (1) Domain links (href attributes) → direct AgentResult objects,
          bypassing Serper entirely.  Vector: V1_COMPETITOR.
      (2) Hebrew company names (בע"מ suffix) → targeted Serper queries
          combined with B2B purchase-intent keywords.
  - V3-enrich all direct-domain results.
  - Run Serper queries and V3-enrich those results.

Execution model:
  Overrides ScraperAgent.run() with a two-phase loop.
  build_queries() and parse_response() are implemented as required stubs;
  only parse_response() is actually called (for the Serper phase).

This module does NOT:
  - Run NLP classification.
  - Write to SQLite.
  - Override _safe_request() — inherits SocialFootprintAgent's Serper POST.
"""

import asyncio
import random
import re
import time
from typing import Optional
from urllib.parse import quote as _url_quote

import aiohttp

from db_init import normalize_domain
from scrapers import (
    DELAY_MIN,
    DELAY_MAX,
    V3_FETCH_TIMEOUT,
    AgentResult,
    AntiBotSignal,
    SocialFootprintAgent,
    _apply_universal_query_filters,
    fetch_raw_html,
    is_aggregator_domain,
    strip_html_to_text,
)

# ---------------------------------------------------------------------------
# Module-level extraction patterns
# ---------------------------------------------------------------------------

# Extracts the host portion from any href attribute in raw HTML.
# Captures everything after the optional www. up to the first path/query/
# fragment delimiter or closing quote.  normalize_domain() is applied
# afterwards to strip known subdomain prefixes (shop., store., m., he.).
_HREF_DOMAIN_RE = re.compile(
    r'href=["\']https?://(?:www\.)?'
    r'([\w.\-]+)'                      # host (letters, digits, dot, hyphen)
    r'(?:["\'/?\s#]|$)',               # terminated by quote, slash, ?, space, #, or EOL
    re.IGNORECASE,
)

# Hebrew company name immediately preceding בע"מ / בע''מ / בע״מ.
# Group 1 captures the name (1–35 characters: Hebrew letters, spaces,
# hyphens, and apostrophes).  Dots are intentionally excluded: they mark
# sentence endings and including them allows the regex to cross sentence
# boundaries when the text is collapsed to a single line by strip_html_to_text.
_HEBREW_BVM_RE = re.compile(
    r'([\u05D0-\u05EA][\u05D0-\u05EA \-\'\"]{1,35}?)\s+בע["\u05F4\']\u05DE',
    re.UNICODE,
)

# Keywords that indicate a page is a genuine client / partner showcase.
# A page must score ≥ _MIN_CLIENT_SIGNALS matches to be mined.
_CLIENT_PAGE_KEYWORDS: list[str] = [
    "לקוחות",        "לקוחותינו",     "לקוח שלנו",   "לקוחות שלנו",
    "שיתוף פעולה",   "ממליצים",       "חברות מובילות", "עבדנו עם",
    "הצטרפו ל",      "clients",        "testimonials", "our clients",
    "partners",      "case studies",
]


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class CompetitorLookalikeAgent(SocialFootprintAgent):
    """
    Offensive discovery agent: mines competitor client/testimonial pages to
    surface pre-qualified B2B leads that are proven leather buyers.

    Two extraction modes per competitor client page:
      1. Domain links (href attributes) — added directly as AgentResult
         objects with vector='V1_COMPETITOR', bypassing Serper.  These are
         the highest-quality leads: the competitor explicitly linked to their
         client's site.
      2. Hebrew company names followed by בע"מ — converted into targeted
         Serper queries and processed through the standard search pipeline.

    Seed domains are passed via the constructor so live_run.py owns the
    configuration without any edits to this file.
    """

    # Default seeds — overridden by the seed_domains constructor argument.
    COMPETITOR_SEED_DOMAINS: list[str] = [
        "shugon.co.il",
    ]

    # Slugs tried in order on each competitor domain.
    # Stops at the first slug that returns a scoreable client page.
    _CLIENT_PAGE_SLUGS: list[str] = [
        "/לקוחות",
        "/לקוחותינו",
        "/לקוחות-שלנו",
        "/clients",
        "/our-clients",
        "/testimonials",
        "/case-studies",
        "/partners",
        "/about",        # fallback — about pages often list key clients
    ]

    # Minimum _CLIENT_PAGE_KEYWORDS hits to treat a page as a real client list.
    _MIN_CLIENT_SIGNALS: int = 2

    # Serper query templates for extracted Hebrew company names.
    # {name} is replaced with the clean company name.
    _QUERY_TEMPLATES: list[str] = [
        '"{name}" ספק עור ישראל site:.co.il',
        '"{name}" מוצרי עור B2B',
    ]

    # Hard cap on Serper queries generated per competitor page.
    # Prevents runaway spend when a competitor lists hundreds of clients.
    _MAX_SERPER_QUERIES: int = 10

    # -------------------------------------------------------------------------
    # Constructor — accepts seed_domains override
    # -------------------------------------------------------------------------

    def __init__(
        self,
        api_key: str,
        proxy_pool: list[str],
        seed_domains: Optional[list[str]] = None,
        ua_pool: Optional[list[str]] = None,
    ) -> None:
        super().__init__(api_key, proxy_pool, ua_pool)
        # Override class-level seeds with caller-supplied list if provided.
        # This lets live_run.py configure seeds without editing this file.
        if seed_domains is not None:
            self.COMPETITOR_SEED_DOMAINS = list(seed_domains)

    # -------------------------------------------------------------------------
    # Abstract method stubs (required by ScraperAgent ABC)
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
        Delegates to SocialFootprintAgent.parse_response() — standard Serper
        organic result parsing.  Called only during the company-name Serper
        phase inside run().
        """
        return await SocialFootprintAgent.parse_response(self, raw_response, query)

    # -------------------------------------------------------------------------
    # Main orchestration — overrides ScraperAgent.run()
    # -------------------------------------------------------------------------

    async def run(self, session: aiohttp.ClientSession) -> list[AgentResult]:
        """
        Two-phase discovery loop across all competitor seed domains.

        Phase 1 — Mine client pages:
          For each seed, scan _CLIENT_PAGE_SLUGS until a scoreable page is
          found.  Extract domain links (direct results) and Hebrew company
          names (Serper queries).

        Phase 2 — Enrich and search:
          a. V3-enrich all direct-domain AgentResults concurrently.
          b. Apply _apply_universal_query_filters to generated queries, then
             run each through Serper and V3-enrich the results.

        All requests respect Iron Principle 5b: jitter is applied between
        every slug fetch and every Serper call.
        """
        start = time.monotonic()
        all_results: list[AgentResult] = []

        try:
            for competitor in self.COMPETITOR_SEED_DOMAINS:
                self._run_log.queries_attempted += 1

                direct_results, serper_queries = await self._mine_competitor(
                    session, competitor
                )

                # ── Phase 2a: V3-enrich direct domain results ─────────────────
                if direct_results:
                    enriched = await asyncio.gather(
                        *[self._enrich_with_direct_html(session, r)
                          for r in direct_results],
                        return_exceptions=True,
                    )
                    for item in enriched:
                        if isinstance(item, AgentResult):
                            all_results.append(item)
                        elif isinstance(item, Exception):
                            self._log_event("ENRICH_ERROR", error=str(item))

                # ── Phase 2b: Serper queries for extracted company names ───────
                filtered_queries = [
                    _apply_universal_query_filters(q)
                    for q in serper_queries[:self._MAX_SERPER_QUERIES]
                ]

                for query in filtered_queries:
                    self._run_log.queries_attempted += 1
                    try:
                        raw = await self._safe_request(session, query)
                        if raw is None:
                            continue

                        serper_results = await self.parse_response(raw, query)

                        serper_enriched = await asyncio.gather(
                            *[self._enrich_with_direct_html(session, r)
                              for r in serper_results],
                            return_exceptions=True,
                        )
                        for item in serper_enriched:
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
    # Competitor page mining
    # -------------------------------------------------------------------------

    async def _mine_competitor(
        self,
        session: aiohttp.ClientSession,
        competitor_domain: str,
    ) -> tuple[list[AgentResult], list[str]]:
        """
        Fetch the first valid client/testimonial page for one competitor domain
        and return extracted signals.

        Tries each slug in _CLIENT_PAGE_SLUGS (with jitter between requests).
        Stops at the first page scoring ≥ _MIN_CLIENT_SIGNALS on
        _CLIENT_PAGE_KEYWORDS.

        Args:
            competitor_domain: bare apex domain, e.g. 'shugon.co.il'

        Returns:
            (direct_results, serper_queries) — both empty if no suitable page
            was found on this competitor domain.
        """
        self._log_event("COMPETITOR_MINE_START", domain=competitor_domain)

        for slug in self._CLIENT_PAGE_SLUGS:
            encoded = _url_quote(slug, safe="/")
            url = f"https://{competitor_domain}{encoded}"

            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            html = await fetch_raw_html(
                session, url,
                headers=self._build_headers(),
                timeout_sec=V3_FETCH_TIMEOUT,
            )
            if not html:
                continue

            # Score: count how many client-showcase keywords appear in the HTML
            lower_html = html.lower()
            score = sum(
                1 for kw in _CLIENT_PAGE_KEYWORDS
                if kw.lower() in lower_html
            )
            if score < self._MIN_CLIENT_SIGNALS:
                continue   # generic page — try the next slug

            self._log_event("COMPETITOR_PAGE_FOUND", url=url, signal_score=score)

            direct_results = self._extract_domains(html, url, competitor_domain)
            serper_queries  = self._extract_company_queries(html)

            self._log_event(
                "COMPETITOR_EXTRACTION",
                direct_leads=len(direct_results),
                serper_queries=len(serper_queries),
            )
            return direct_results, serper_queries

        # No client page found on this competitor — log and return empty
        self._log_event("COMPETITOR_NO_PAGE", domain=competitor_domain)
        return [], []

    def _extract_domains(
        self,
        html: str,
        source_url: str,
        exclude_domain: str,
    ) -> list[AgentResult]:
        """
        Extract all outbound domains from href attributes in raw HTML.

        Filters applied:
          - Excludes the competitor's own domain (self-referential links).
          - Excludes .gov.il (government portals — not B2B leads).
          - Excludes known aggregator / directory domains.
          - Deduplicates: each domain is returned at most once.
          - Rejects single-label tokens (URL fragments without a dot).

        Returns AgentResult objects with vector='V1_COMPETITOR'.
        entity_name is a best-effort title-case of the domain's first label
        (e.g. 'braker.co.il' → 'Braker').  V3 enrichment in run() overwrites
        raw_text with actual page content before NLP classification.
        """
        results: list[AgentResult] = []
        seen:    set[str] = set()

        for raw in _HREF_DOMAIN_RE.findall(html):
            domain = normalize_domain(raw)
            if not domain or "." not in domain:
                continue
            if domain in seen or domain == exclude_domain:
                continue
            if domain.endswith(".gov.il"):
                continue
            if is_aggregator_domain(domain):
                continue

            seen.add(domain)
            name = domain.split(".")[0].replace("-", " ").title()
            results.append(AgentResult(
                entity_name= name,
                domain=      domain,
                source_url=  source_url,
                vector=      "V1_COMPETITOR",
            ))

        return results

    def _extract_company_queries(self, html: str) -> list[str]:
        """
        Extract Hebrew company names (identified by the בע"מ Ltd suffix) from
        the stripped page text and convert them into Serper query strings.

        Name validation rules:
          - Minimum 3 characters after stripping stray punctuation.
          - Maximum 6 whitespace-separated words — longer matches are almost
            always sentence fragments, not real company names.
          - Deduplicated: the same clean name generates queries only once.

        Returns a flat list of query strings (one per template per name).
        The list is not capped here — the caller applies _MAX_SERPER_QUERIES.
        """
        text     = strip_html_to_text(html)
        seen:    set[str]  = set()
        queries: list[str] = []

        for match in _HEBREW_BVM_RE.finditer(text):
            raw_name   = match.group(1).strip()
            # Collapse multiple whitespace, strip stray punctuation at edges
            clean_name = re.sub(r'\s+', ' ', raw_name).strip(' \'".,;:()')

            if len(clean_name) < 3:
                continue
            if len(clean_name.split()) > 6:
                continue
            if clean_name in seen:
                continue

            seen.add(clean_name)
            for template in self._QUERY_TEMPLATES:
                queries.append(template.format(name=clean_name))

        return queries
