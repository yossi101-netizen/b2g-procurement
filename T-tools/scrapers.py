"""
KritiKaal Leads Hunter — Scraper Agents
File: T-tools/scrapers.py
Governed by: B-brain/01-tech-stack.md (Iron Principles 1, 2, 4, 5)
Observability contract: A-agents/01-architect-agent.md

Responsibilities (SRP boundary):
  - Provide a resilient async base class (ScraperAgent) handling proxy
    rotation, UA rotation, jitter backoff, and structured run logging.
  - Implement two concrete discovery agents:
      LocalDirectoryAgent  — SerpApi V2 (Google Maps / local Israeli directories)
      SocialFootprintAgent — Serper V1 (web search, LinkedIn, Facebook pages)
  - Provide DomExtractor utility functions: fetch raw HTML, strip to plain
    text, extract WhatsApp numbers and Company IDs from page content.
  - Expose a pipeline entry point (run_agent_pipeline) that wires agent
    results through nlp_classifier and into db_init.upsert_lead.

This module does NOT:
  - Run NLP classification (delegated to nlp_classifier.py)
  - Write directly to SQLite except via upsert_lead (db_init.py)
  - Implement any Outreach or contact initiation
  - Use Selenium or Playwright

APPROVED LIBRARIES (B-brain/01-tech-stack.md):
  asyncio, aiohttp, re, logging, json, dataclasses, abc, html.parser (stdlib)
  openai dependency is in nlp_classifier.py only — not imported here.
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import quote as _url_quote

import aiohttp

from db_init import upsert_lead, get_connection, normalize_whatsapp, normalize_domain

# ---------------------------------------------------------------------------
# Constants — Anti-Bot (Iron Principle 5b)
# ---------------------------------------------------------------------------

DELAY_MIN: float = 1.5
DELAY_MAX: float = 4.0
MAX_RETRIES: int = 3
BACKOFF_BASE: float = 2.0   # exponential base for retry delays
REQUEST_TIMEOUT: int  = 20   # seconds per request
V3_FETCH_TIMEOUT: int  = 10  # aiohttp-level timeout for each V3 HTML fetch.
                              # Most Israeli sites respond in <5 s; 10 s avoids
                              # blocking the entire gather() on a slow host.
V3_HARD_TIMEOUT: float = 15.0
# Hard asyncio.wait_for() ceiling around every V3 fetch coroutine.
# Must be > V3_FETCH_TIMEOUT so aiohttp's internal timeout fires first
# under normal conditions. V3_HARD_TIMEOUT activates ONLY when aiohttp's
# timeout silently fails — observed on Windows when DNS resolution is
# delegated to the OS thread pool and cannot be cancelled by asyncio.

# Tri-Vector API endpoints (Iron Principle 2)
SERPER_ENDPOINT = "https://google.serper.dev/search"
SERPAPI_ENDPOINT = "https://serpapi.com/search"

# Regex patterns for core data extraction (Iron Principle 4)
# Non-capturing groups: finditer().group(0) returns the full match string.
# Allows separators (spaces/dashes) between digit groups; normalize_whatsapp()
# strips them during normalization.
_WHATSAPP_PATTERN = re.compile(r'(?:\+?972[\s\-]?|0)5[0-9][\d\s\-]{7,9}')
_COMPANY_ID_PATTERN = re.compile(r'\b(5[0-9]{8}|[5-9][0-9]{8})\b')
_DOMAIN_FROM_URL_PATTERN = re.compile(r'^(?:https?://)?(?:www\.)?([^/?\s]+)')

# ---------------------------------------------------------------------------
# Layer 1 — Aggregator / Directory Domain Blocklist
#
# Domains in this set are NEVER leads — they are search directories, business
# profile aggregators, news sites, social platforms, or reference pages.
# Applied in SocialFootprintAgent.parse_response() BEFORE V3 HTML enrichment
# so we never waste an HTTP request on a known aggregator.
#
# When to ADD a domain: any site that lists *other businesses* rather than
# selling or manufacturing products itself (i.e., it is an index, not an entity).
# ---------------------------------------------------------------------------

_AGGREGATOR_DOMAINS: frozenset[str] = frozenset({
    # Israeli business directories
    "d.co.il",             # DapeiZahav / Yellow Pages Israel
    "b144.co.il",          # B144 Israeli directory
    "easy.co.il",          # EasyBusiness
    "bizportal.co.il",     # BizPortal
    "all.co.il",           # All.co.il directory
    "hotfrog.co.il",       # HotFrog Israel
    "eniro.co.il",         # Eniro Israel
    "izhaki.co.il",        # Izhaki directory
    # Israeli service marketplaces
    "starofservice.co.il",
    "bark.com",
    "thumbtack.com",
    "fixmasters.co.il",
    "homely.co.il",
    # Israeli classifieds (not B2B suppliers)
    "yad2.co.il",
    "janglo.net",
    # Business profile / credit aggregators
    "dunsguide.co.il",     # Dun & Bradstreet Israel — profile pages, not company sites
    "duns100.co.il",
    "bguid.com",
    "kompass.com",
    "europages.co.il",
    "europages.com",
    "dnb.com",
    "opencorporates.com",
    # Israeli price-comparison / e-commerce platforms
    "zap.co.il",
    "ivory.co.il",         # retailer aggregator
    "ksp.co.il",
    "amazon.co.il",
    "ebay.co.il",
    "aliexpress.com",
    "alibaba.com",
    # Israeli news media (no B2B leads)
    "ynet.co.il",
    "walla.co.il",
    "mako.co.il",
    "calcalist.co.il",
    "themarker.com",
    "globes.co.il",
    "haaretz.co.il",
    "israelhayom.co.il",
    "nrg.co.il",
    "sport5.co.il",
    # Review sites
    "tripadvisor.com",
    "yelp.com",
    "google.com",
    # Social / UGC platforms
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
    # Reference / encyclopedia
    "wikipedia.org",
    "he.wikipedia.org",
    "en.wikipedia.org",
    "wikimedia.org",
    # Government / public-sector portals
    "gov.il",
    "taxes.gov.il",
    # Telco directories
    "bezeqint.net",
    "yellow.co.il",
    "012.net.il",
    # Israeli job boards — return job-posting pages, not employer homepages
    "drushim.co.il",
    "alljobs.co.il",
    "jobmaster.co.il",
    "hotjobs.co.il",
    "il.indeed.com",
    "careerjet.co.il",
    "jobnet.co.il",
    "gowork.co.il",
    # Israeli SaaS / accounting platforms — not B2B product companies
    "greeninvoice.co.il",
    "icount.co.il",
    "takbull.co.il",
    "hashavshevet.co.il",
    "priority.co.il",
    # Coupon / deal aggregators
    "dlz.co.il",
    "groupon.co.il",
    "btdeal.co.il",
    # Travel / experience platforms
    "lametayel.co.il",
    "issta.co.il",
    "goisrael.com",
    # Real estate portals
    "madlan.co.il",
    "yad2.co.il",     # already listed above under classifieds — idempotent
})

# ---------------------------------------------------------------------------
# Layer 1b — Hard-Skip Domain Keywords
#
# If the domain NAME itself contains any of these substrings, skip before
# issuing any HTTP request. These are romanized transliterations of Hebrew
# terms that unambiguously identify ritual/religious businesses or Italy-only
# brand identity domains — both are permanent supply-chain incompatibilities.
#
# Scope: domain string only (not page content — that is handled by Tier 1
# in nlp_classifier). This is a zero-cost pre-filter on the domain name.
# ---------------------------------------------------------------------------

_HARD_SKIP_DOMAIN_KEYWORDS: frozenset[str] = frozenset({
    # Ritual leather — requires kosher-certified hides (we cannot supply)
    "tefilin", "tefillin", "tfilin", "teffilin",
    "stam", "sofer", "sofrim",
    "kedusha", "kodesh", "kadosh",
    "mezuza", "mezuzot", "mezuza",
    "torahscroll", "sefer-torah",
    # Italy-only brand identity
    "madeinitaly", "made-in-italy", "italianleather",
})


def is_hard_skip_domain(domain: str) -> bool:
    """
    Layer 1b filter: Return True if the domain name contains a hard-skip keyword.

    Called in SocialFootprintAgent.parse_response() alongside is_aggregator_domain()
    before any HTTP request — zero cost.
    """
    if not domain:
        return False
    lower = domain.lower()
    return any(kw in lower for kw in _HARD_SKIP_DOMAIN_KEYWORDS)


# ---------------------------------------------------------------------------
# Layer 2 — Directory Page Content Fingerprint
#
# These are Hebrew and English signals found in directory/aggregator page text
# but almost never in a real company's homepage.
# is_directory_page() requires MULTIPLE hits to fire (reduces false positives).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Query-Level Negative Modifiers — עור Homograph Filter
#
# Applied to all Serper queries that contain the bare word עור (leather/skin)
# WITHOUT an unambiguous leather-product anchor. Suppresses cosmetics and
# skincare companies from appearing in Serper results, reducing both API
# spend (fewer false-positive fetches) and NLP cost (fewer LLM calls).
#
# The Tier 0 check in nlp_classifier._is_skincare_page() handles any
# cosmetics pages that slip through query-level filtering. These two layers
# are complementary — neither is a replacement for the other.
# ---------------------------------------------------------------------------

_SKINCARE_QUERY_NEGATIVES: str = (
    '-"קרם פנים" -"טיפוח עור" -"קוסמטיקה" -"מוצרי יופי" -skincare -"קרם לחות"'
)

# Queries containing any of these terms are already specific to the leather
# industry and do not need the negation appended.
_LEATHER_QUERY_ANCHORS: frozenset[str] = frozenset({
    "תיקים", "ארנקים", "נעלים", "נעלי", "כפפות",
    "סינר", "חגורות", "אביזרי", "מפעל", "יבואן",
    "סיטונאי", "מינימום הזמנה", "מחיר סיטונאי",
    "עור איטלקי", "עור טורקי", "הוסף לסל",
})


def _apply_universal_query_filters(query: str) -> str:
    """
    Append skincare negative modifiers to queries containing the עור homograph
    without a leather-specific anchor term.

    Rules:
      - Only modifies queries that contain the Hebrew word עור.
      - Skips modification if the query already contains a leather anchor
        (it's already specific enough to avoid skincare results).
      - Does NOT modify queries that contain 'site:maps' or are SerpApi/Maps
        queries (these are place-name queries, not text queries).

    This is a pure string transformation — no API calls, no side effects.
    """
    if 'עור' not in query:
        return query
    # Skip Maps / SerpApi queries
    if 'engine=google_maps' in query or 'site:maps' in query:
        return query
    # Skip if already anchored to a leather-specific product/context
    if any(anchor in query for anchor in _LEATHER_QUERY_ANCHORS):
        return query
    return query + ' ' + _SKINCARE_QUERY_NEGATIVES


_DIRECTORY_PAGE_SIGNALS: list[str] = [
    # Hebrew listing/results language
    "תוצאות עבור",
    "רשימת עסקים",
    "כל העסקים",
    "כל הרשימות",
    "חפש עסק",
    "מצא את הטוב ביותר",
    "השאר ביקורת",
    "ביקורות לקוחות",
    "השווה מחירים",
    "קבל הצעות מחיר",
    "מקצוענים באזורך",
    "בחר מקצוען",
    "מקצוענים מומלצים",
    # English directory language
    "business directory",
    "service directory",
    "find professionals",
    "compare quotes",
    "get quotes",
    "best professionals",
    "read reviews",
    "write a review",
    "yellow pages",
    "white pages",
    "all categories",
    "browse listings",
    # Known aggregator brand names
    "דפי זהב",
    "starof service",
    "starofservice",
    "dunsguide",
    "kompass",
    "europages",
    "bark.com",
]

_DIRECTORY_SIGNAL_THRESHOLD: int = 2   # require ≥2 hits to avoid false positives

# Observability paths (M-Memory layer)
LOG_DIR = Path(__file__).parent.parent / "M-memory" / "logs"
RUN_SUMMARY_PATH = Path(__file__).parent.parent / "M-memory" / "run_summary.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """
    Normalized output schema from any scraper agent.
    All fields map 1:1 to leads table columns plus pipeline metadata.
    Strict schema: downstream consumers must not add fields.
    """
    entity_name:      str
    domain:           str                   # normalized by normalize_domain()
    whatsapp:         Optional[str] = None  # normalized by normalize_whatsapp()
    company_id:       Optional[str] = None  # 9-digit ח.פ / עוסק מורשה
    physical_address: Optional[str] = None
    raw_text:         str = ""              # stripped page body — fed to NLP
    source_url:       str = ""             # exact URL or query that found this result
    vector:           str = "V1_SERPER"    # V1_SERPER | V2_SERPAPI | V3_DIRECT
    scraped_at:       str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_lead_dict(self, status: str = "RAW") -> dict:
        """Return a dict shaped for db_init.upsert_lead(lead_data=...)."""
        return {
            "entity_name":      self.entity_name,
            "domain":           self.domain,
            "whatsapp":         self.whatsapp,
            "company_id":       self.company_id,
            "physical_address": self.physical_address,
            "status":           status,
            "legal_flag":       None if self.company_id else "PENDING_LEGAL",
        }


@dataclass
class AgentRunLog:
    """
    Structured log record written after every agent run.
    Maps to M-memory/run_summary.json and M-memory/logs/<date>_run.log.
    Aligns with observability contract (Operations Manual Section 2).

    domains_new          : domains that passed the skip gate and were sent for
                           NLP classification (genuinely new discoveries this run).
    domains_already_known: domains that passed the aggregator check but were
                           already in skip_domains (DB or blacklist) — corroborated
                           by this agent but not re-processed (zero NLP cost).
                           Written by _run_agent_loop() after agent.run() returns.
    """
    agent_id:              str
    run_timestamp:         str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status:                str = "OK"   # OK | PARTIAL | FAILED | BLOCKED | CRASHED
    queries_attempted:     int = 0
    results_collected:     int = 0
    leads_upserted:        int = 0
    antibot_triggers:      int = 0
    error_message:         Optional[str] = None
    duration_seconds:      float = 0.0
    domains_new:           int = 0      # passed skip gate → NLP processed
    domains_already_known: int = 0      # blocked by skip gate → zero NLP cost


# ---------------------------------------------------------------------------
# Base class — ScraperAgent
# ---------------------------------------------------------------------------

class ScraperAgent(ABC):
    """
    Abstract base for all Israel-Hunter scraper agents.

    Provides resilience infrastructure:
      - Proxy rotation from a configurable pool
      - User-Agent rotation from a configurable pool
      - Randomized jitter between requests (Iron Principle 5b)
      - Exponential backoff with jitter on failures
      - Structured logging to M-memory (observability contract)

    Subclasses implement build_queries() and parse_response() only.
    All HTTP I/O goes through _safe_request() — never bypass it.
    """

    # Default User-Agent pool (20+ entries as required by Iron Principle 5b)
    _DEFAULT_UA_POOL: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) "
            "Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Vivaldi/6.7.3329.21",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) "
            "Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(
        self,
        api_key: str,
        proxy_pool: list[str],
        ua_pool: Optional[list[str]] = None,
    ) -> None:
        self.api_key    = api_key
        self.proxy_pool = proxy_pool
        self.ua_pool    = ua_pool or self._DEFAULT_UA_POOL
        self.agent_id   = self.__class__.__name__
        self._run_log   = AgentRunLog(agent_id=self.agent_id)
        self._logger    = self._build_logger()

    # ------------------------------------------------------------------
    # Abstract interface — subclasses implement these two methods only
    # ------------------------------------------------------------------

    @abstractmethod
    async def build_queries(self) -> list[str]:
        """
        Return a list of query strings or endpoint URLs for this agent's
        source. Called once per run before any HTTP requests are made.
        """

    @abstractmethod
    async def parse_response(
        self,
        raw_response: dict,
        query: str,
    ) -> list[AgentResult]:
        """
        Parse the raw API JSON response for one query into a list of
        AgentResult objects. Must return an empty list (never raise) on
        malformed or empty responses.
        """

    # ------------------------------------------------------------------
    # Orchestration — do not override in subclasses
    # ------------------------------------------------------------------

    async def run(self, session: aiohttp.ClientSession) -> list[AgentResult]:
        """
        Full agent execution loop.

        For each query returned by build_queries():
          1. Issue _safe_request() with proxy + UA rotation + jitter.
          2. Parse response via parse_response().
          3. For each result: fetch V3 direct HTML and enrich raw_text.
          4. Accumulate and return all AgentResult objects.

        Updates self._run_log throughout for observability.
        """
        start = time.monotonic()
        all_results: list[AgentResult] = []

        try:
            queries = await self.build_queries()
            # Apply universal query filters: append skincare negatives to any
            # bare-עור query without a leather anchor (homograph disambiguation).
            queries = [_apply_universal_query_filters(q) for q in queries]
            self._run_log.queries_attempted = len(queries)

            for query in queries:
                try:
                    raw = await self._safe_request(session, query)
                    if raw is None:
                        continue

                    results = await self.parse_response(raw, query)

                    # V3 enrichment: fetch direct website for raw_text
                    enriched = await asyncio.gather(
                        *[self._enrich_with_direct_html(session, r) for r in results],
                        return_exceptions=True,
                    )
                    for item in enriched:
                        if isinstance(item, AgentResult):
                            all_results.append(item)
                        # Exceptions from individual enrichments are logged
                        # but do not abort the run
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
            if self._run_log.status == "OK" and self._run_log.antibot_triggers == 0:
                self._run_log.status = "OK"

        except Exception as exc:
            self._run_log.status = "CRASHED"
            self._run_log.error_message = str(exc)
            self._log_event("CRASH", error=str(exc))
            raise

        finally:
            self._run_log.duration_seconds = round(time.monotonic() - start, 2)
            self._flush_run_log()

        return all_results

    # ------------------------------------------------------------------
    # HTTP resilience — proxy + UA rotation, jitter, backoff
    # ------------------------------------------------------------------

    async def _safe_request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Execute one GET request with:
          - Random proxy selection from pool
          - Random User-Agent from pool
          - Standard Referer and Accept-Language headers
          - Pre-request random jitter (Iron Principle 5b)
          - Exponential backoff with jitter on failure (up to MAX_RETRIES)
          - AntiBotSignal raised on 403 / 429 / CAPTCHA detection

        Returns parsed JSON dict, or None if all retries are exhausted.
        """
        proxy   = random.choice(self.proxy_pool)
        headers = self._build_headers()

        for attempt in range(1, MAX_RETRIES + 1):
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # jitter

            try:
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    proxy=proxy,
                    timeout=timeout,
                ) as resp:

                    if resp.status in (403, 429):
                        raise AntiBotSignal(
                            f"HTTP {resp.status} on attempt {attempt}"
                        )

                    text = await resp.text(encoding="utf-8", errors="replace")

                    if _is_captcha_response(text):
                        raise AntiBotSignal(f"CAPTCHA detected on attempt {attempt}")

                    return json.loads(text)

            except AntiBotSignal:
                # Rotate proxy and UA on anti-bot signal, then re-raise
                proxy   = random.choice(self.proxy_pool)
                headers = self._build_headers()
                if attempt == MAX_RETRIES:
                    raise
                backoff = BACKOFF_BASE ** attempt + random.uniform(0, 1)
                await asyncio.sleep(backoff)

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                self._log_event(
                    "REQUEST_ERROR", url=url, attempt=attempt,
                    exc_type=type(exc).__name__,
                    error=str(exc) or repr(exc),   # repr() catches OS errors whose str() is ""
                )
                if attempt == MAX_RETRIES:
                    return None
                backoff = BACKOFF_BASE ** attempt + random.uniform(0, 1)
                await asyncio.sleep(backoff)

        return None

    async def _enrich_with_direct_html(
        self,
        session: aiohttp.ClientSession,
        result: AgentResult,
    ) -> AgentResult:
        """
        V3 Direct HTTP: fetch the lead's website, strip to plain text,
        and attempt to extract additional WhatsApp and Company ID fields.

        Updates result.raw_text, result.whatsapp (if still None),
        and result.company_id (if still None) in place.
        Returns the same result object.

        Timeout layering (Sprint 10.5 — Silent Freeze fix):
          Layer 1: aiohttp.ClientTimeout(total=V3_FETCH_TIMEOUT) inside fetch_raw_html
                   — handles normal slow-server scenarios.
          Layer 2: asyncio.wait_for(timeout=V3_HARD_TIMEOUT) around the entire call
                   — fires if Layer 1 silently fails (DNS thread-pool hang on Windows).
        """
        if not result.domain or result.domain.startswith("maps::"):
            return result

        url = f"https://{result.domain}"
        print(f"  [V3] {result.domain} ...", flush=True)

        headers = self._build_headers()   # realistic browser headers — prevents 403s
        try:
            html = await asyncio.wait_for(
                fetch_raw_html(session, url, headers=headers, timeout_sec=V3_FETCH_TIMEOUT),
                timeout=V3_HARD_TIMEOUT,
            )
        except asyncio.TimeoutError:
            print(f"  [V3 TIMEOUT] {result.domain} exceeded {V3_HARD_TIMEOUT:.0f}s — skipped", flush=True)
            return result
        except Exception as exc:
            print(f"  [V3 ERROR] {result.domain}: {type(exc).__name__}: {str(exc)[:80]}", flush=True)
            return result

        if not html:
            return result

        result.raw_text = strip_html_to_text(html)

        if not result.whatsapp:
            result.whatsapp = select_best_phone(extract_whatsapp_numbers(html))

        if not result.company_id:
            result.company_id = select_best_company_id(extract_company_ids(html))

        return result

    # ------------------------------------------------------------------
    # Headers builder (SRP: one function, one responsibility)
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict:
        """Return a realistic browser header dict with a random User-Agent."""
        return {
            "User-Agent":      random.choice(self.ua_pool),
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept":          "application/json, text/html, */*",
            "Referer":         "https://www.google.co.il/",
            "DNT":             "1",
        }

    # ------------------------------------------------------------------
    # Structured logging (observability contract)
    # ------------------------------------------------------------------

    def _build_logger(self) -> logging.Logger:
        """Configure and return a file + console logger for this agent."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{self.agent_id}.log"

        logger = logging.getLogger(self.agent_id)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            fmt = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            logger.addHandler(fh)
            logger.addHandler(ch)

        return logger

    def _log_event(self, event_type: str, **kwargs) -> None:
        """Write one structured log entry as a JSON line."""
        entry = {"event": event_type, "agent": self.agent_id, **kwargs}
        self._logger.info(json.dumps(entry, ensure_ascii=False))

    def _flush_run_log(self) -> None:
        """
        Write the completed AgentRunLog to M-memory/run_summary.json.
        Merges with existing summary rather than overwriting other agents' entries.
        """
        RUN_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

        summary: dict = {}
        if RUN_SUMMARY_PATH.exists():
            try:
                summary = json.loads(RUN_SUMMARY_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                summary = {}

        summary[self.agent_id] = asdict(self._run_log)
        RUN_SUMMARY_PATH.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Concrete Agent 1 — LocalDirectoryAgent (V2_SERPAPI / Google Maps)
# ---------------------------------------------------------------------------

class LocalDirectoryAgent(ScraperAgent):
    """
    Discovers Israeli B2B businesses via Google Maps using SerpApi (V2).

    Target profile: businesses with a physical Israeli address, phone number,
    and website — strong Class A / B signals before NLP even runs.

    Query strategy: city × category matrix covering major Israeli commercial
    centres and B2B-relevant business types.
    """

    # Israeli cities × B2B categories — cross-product produces the query set
    _CITIES: list[str] = [
        "תל אביב", "ירושלים", "חיפה", "ראשון לציון", "פתח תקווה",
        "אשדוד", "נתניה", "בני ברק", "באר שבע", "רמת גן",
        "הרצליה", "כפר סבא", "רעננה", "חולון", "קריות",
    ]
    _CATEGORIES: list[str] = [
        "יצרן", "יבואן", "סיטונאי", "מפיץ", "מחסן",
        "ספק ציוד", "מפעל", "חברת ייצור", "יבוא יצוא",
    ]

    async def build_queries(self) -> list[str]:
        """
        Build (city, category) query strings for Google Maps search.
        Returns one query per combination — total: cities × categories.
        """
        return [
            f"{category} {city}"
            for city in self._CITIES
            for category in self._CATEGORIES
        ]

    async def parse_response(
        self,
        raw_response: dict,
        query: str,
    ) -> list[AgentResult]:
        """
        Parse SerpApi Google Maps JSON response.

        Expected structure: raw_response["local_results"] is a list of
        place objects with keys: title, address, phone, website, place_id.
        """
        results: list[AgentResult] = []
        places = raw_response.get("local_results") or []

        for place in places:
            domain = _extract_domain_from_place(place)
            phone  = _extract_phone_from_place(place)

            results.append(AgentResult(
                entity_name=      place.get("title", ""),
                domain=           domain or f"maps::{place.get('place_id', '')}",
                whatsapp=         normalize_whatsapp(phone) if phone else None,
                physical_address= place.get("address"),
                source_url=       place.get("link", f"serpapi::{query}"),
                vector=           "V2_SERPAPI",
            ))

        return [r for r in results if r.entity_name]

    async def _safe_request(
        self,
        session: aiohttp.ClientSession,
        query: str,
        params: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Override to call SerpApi Maps endpoint with required parameters.
        Inherits all proxy / UA / jitter / backoff behaviour from base.
        """
        serpapi_params = {
            "engine":    "google_maps",
            "q":         query,
            "hl":        "iw",       # Hebrew results
            "gl":        "il",       # Israel locale
            "api_key":   self.api_key,
        }
        return await super()._safe_request(
            session, SERPAPI_ENDPOINT, params=serpapi_params
        )


# ---------------------------------------------------------------------------
# Concrete Agent 2 — SocialFootprintAgent (V1_SERPER / Web + Social)
# ---------------------------------------------------------------------------

class SocialFootprintAgent(ScraperAgent):
    """
    Discovers Israeli B2B businesses via Serper web search (V1).

    Targets: company websites, LinkedIn company pages, Facebook business
    pages, and Israeli business news — sources that surface entity names,
    domains, and phone numbers not listed on Maps.

    Specialises in surfacing businesses showing distress or transition
    signals (Class A targets) by including intent-based query suffixes.
    """

    _SEARCH_TEMPLATES: list[str] = [
        '"{keyword}" אתר site:il',
        '"{keyword}" ישראל LinkedIn',
        '"{keyword}" ישראל WhatsApp',
        '"{keyword}" מפעל ישראל',
        '"{keyword}" יבואן בלעדי ישראל',
        '"{keyword}" מכירה עסק ישראל',          # distress: business for sale
        '"{keyword}" פירוק מלאי ישראל',          # distress: liquidation
        '"{keyword}" שינוי בעלות ישראל',         # distress: ownership change
    ]

    _KEYWORDS: list[str] = [
        # Leather-industry volume-buyer targets (KritiKaal Phase 1 pivot)
        "יבואן מוצרי עור",        # leather product importer
        "סיטונאי עורות",           # leather wholesaler
        "מותג עור ישראלי",         # Israeli leather brand
        "קולקציית עור",            # leather collection
        "אספקה לסיטונאים עור",     # leather supply to wholesalers
        "יבוא ושיווק מוצרי עור",   # leather import & marketing
        "ייצור ארנקים ישראל",      # wallet manufacturing Israel
        "יצרן תיקי עור",           # leather bag manufacturer
        # General B2B categories (retained as fallback)
        "ציוד תעשייתי", "מוצרי צריכה", "חומרי גלם", "ביגוד",
    ]

    async def build_queries(self) -> list[str]:
        """
        Build search query strings from keyword × template matrix.
        Distress-intent templates are included to surface Class A targets.
        """
        return [
            template.format(keyword=kw)
            for kw in self._KEYWORDS
            for template in self._SEARCH_TEMPLATES
        ]

    async def parse_response(
        self,
        raw_response: dict,
        query: str,
    ) -> list[AgentResult]:
        """
        Parse Serper organic search JSON response.

        Expected structure: raw_response["organic"] is a list of result
        objects with keys: title, link, snippet, sitelinks (optional).
        """
        results: list[AgentResult] = []
        organic = raw_response.get("organic") or []

        for item in organic:
            raw_url = item.get("link", "")
            domain  = normalize_domain(raw_url) if raw_url else None
            if not domain:
                continue

            # Layer 1 — block known aggregator/directory domains before
            # any V3 HTTP enrichment is attempted (saves HTTP requests)
            if is_aggregator_domain(domain) or is_hard_skip_domain(domain):
                continue

            # Attempt phone extraction from snippet text (V1 does not
            # return structured phone fields — V3 enrichment fills the gap)
            snippet = item.get("snippet", "")
            phones  = extract_whatsapp_numbers(snippet)

            results.append(AgentResult(
                entity_name= item.get("title", domain),
                domain=      domain,
                whatsapp=    select_best_phone(phones),
                raw_text=    snippet,   # enriched further by V3 in base.run()
                source_url=  raw_url,
                vector=      "V1_SERPER",
            ))

        return results

    async def _safe_request(
        self,
        session: aiohttp.ClientSession,
        query: str,
        params: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Override to call Serper search endpoint with Hebrew/Israel parameters.
        Inherits all proxy / UA / jitter / backoff behaviour from base.
        """
        headers = self._build_headers()
        headers["X-API-KEY"] = self.api_key
        headers["Content-Type"] = "application/json"

        payload = json.dumps({
            "q":  query,
            "hl": "iw",
            "gl": "il",
            "num": 10,
        })

        for attempt in range(1, MAX_RETRIES + 1):
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            try:
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                async with session.post(
                    SERPER_ENDPOINT,
                    data=payload,
                    headers=headers,
                    proxy=random.choice(self.proxy_pool),
                    timeout=timeout,
                ) as resp:
                    if resp.status in (403, 429):
                        raise AntiBotSignal(f"HTTP {resp.status}")
                    return await resp.json()

            except AntiBotSignal:
                if attempt == MAX_RETRIES:
                    raise
                await asyncio.sleep(BACKOFF_BASE ** attempt + random.uniform(0, 1))

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt == MAX_RETRIES:
                    return None
                self._log_event(
                    "REQUEST_ERROR", attempt=attempt,
                    exc_type=type(exc).__name__,
                    error=str(exc) or repr(exc),   # repr() catches OS errors whose str() is ""
                )
                await asyncio.sleep(BACKOFF_BASE ** attempt + random.uniform(0, 1))

        return None


# ---------------------------------------------------------------------------
# DomExtractor — HTML utility functions (SRP: one function, one job)
# ---------------------------------------------------------------------------

class _TagStripper(HTMLParser):
    """
    Minimal HTMLParser subclass that discards all tags and collects text.
    Also drops <script> and <style> blocks entirely.
    """
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


async def fetch_raw_html(
    session: aiohttp.ClientSession,
    url: str,
    headers: Optional[dict] = None,
    proxy: Optional[str] = None,
    timeout_sec: Optional[int] = None,
) -> Optional[str]:
    """
    Fetch the raw HTML body of a URL.
    Returns None on network error, non-200 status, or timeout.
    Does NOT apply jitter — callers are responsible for pacing.

    timeout_sec: per-request timeout in seconds. Defaults to REQUEST_TIMEOUT (20 s).
                 Pass V3_FETCH_TIMEOUT (10 s) from _enrich_with_direct_html so a
                 slow Israeli site does not block the entire asyncio.gather() call.
    headers:     Must be provided by V3 callers to pass browser-like User-Agent /
                 Accept-Language headers — otherwise many .co.il sites return 403.
    """
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec or REQUEST_TIMEOUT)
        async with session.get(
            url,
            headers=headers or {},
            proxy=proxy,
            timeout=timeout,
            allow_redirects=True,
        ) as resp:
            if resp.status != 200:
                return None
            return await resp.text(encoding="utf-8", errors="replace")
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None


def strip_html_to_text(html: str) -> str:
    """
    Strip all HTML tags, scripts, and styles from a raw HTML string.
    Returns a single whitespace-normalised plain-text string.
    Suitable as the text_payload input for nlp_classifier.classify_lead().
    """
    parser = _TagStripper()
    parser.feed(html)
    raw = parser.get_text()
    # Collapse multiple whitespace / newlines into single spaces
    return re.sub(r'\s+', ' ', raw).strip()


def extract_whatsapp_numbers(text: str) -> list[str]:
    """
    Find all candidate Israeli phone numbers in a text or HTML string.
    Returns full raw matched strings (not yet normalized).
    Uses finditer so group(0) always captures the complete digit sequence
    including any separators — normalize_whatsapp() strips them downstream.
    """
    return [m.group(0) for m in _WHATSAPP_PATTERN.finditer(text)]


def extract_company_ids(text: str) -> list[str]:
    """
    Find all candidate ח.פ / עוסק מורשה numbers (9-digit patterns) in text.
    Returns raw matched strings.
    """
    return _COMPANY_ID_PATTERN.findall(text)


def select_best_phone(candidates: list) -> Optional[str]:
    """
    Given a list of raw phone matches (from extract_whatsapp_numbers),
    normalize each and return the first valid result, or None.
    Prefer numbers that start with 05x (Israeli mobile) over landlines.
    """
    for candidate in candidates:
        normalized = normalize_whatsapp(candidate)
        if normalized:
            return normalized
    return None


def select_best_company_id(candidates: list[str]) -> Optional[str]:
    """
    Given a list of raw company ID matches (from extract_company_ids),
    return the first 9-digit string, or None.
    """
    for raw in candidates:
        digits = re.sub(r'\D', '', raw)
        if len(digits) == 9:
            return digits
    return None


def is_aggregator_domain(domain: str) -> bool:
    """
    Layer 1 filter: Return True if the domain is a known business directory,
    aggregator, news site, social platform, or reference page.

    Checks the _AGGREGATOR_DOMAINS blocklist. The check is exact-match on the
    root domain so subdomains (he.wikipedia.org) are also caught because the
    full subdomain is in the blocklist.

    Called from SocialFootprintAgent.parse_response() before V3 HTML enrichment
    to prevent wasted HTTP requests on known non-lead domains.
    """
    if not domain:
        return False
    lower = domain.lower().strip()
    # Exact match (includes subdomains already in the set)
    if lower in _AGGREGATOR_DOMAINS:
        return True
    # Root domain match: strip one leading label (e.g. "news.walla.co.il" → "walla.co.il")
    parts = lower.split(".")
    if len(parts) > 2:
        root = ".".join(parts[-3:])   # e.g. "walla.co.il" from 4-part domain
        if root in _AGGREGATOR_DOMAINS:
            return True
        root2 = ".".join(parts[-2:])  # e.g. "wikipedia.org" from "he.wikipedia.org"
        if root2 in _AGGREGATOR_DOMAINS:
            return True
    return False


def is_directory_page(text: str) -> bool:
    """
    Layer 2 filter: Return True if the page text exhibits content patterns
    typical of a directory or aggregator listing page rather than a company site.

    Requires at least _DIRECTORY_SIGNAL_THRESHOLD (2) distinct signal matches to
    fire, reducing false positives on legitimate company pages that may mention
    one directory term incidentally.

    Called in live_run.process_agent_result() AFTER HTML fetch but BEFORE the
    OpenAI NLP call — prevents wasting tokens on known directory pages.
    """
    if not text:
        return False
    lower = text.lower()
    hits = sum(1 for sig in _DIRECTORY_PAGE_SIGNALS if sig.lower() in lower)
    return hits >= _DIRECTORY_SIGNAL_THRESHOLD


# ---------------------------------------------------------------------------
# Phase 2A — Multi-Page Contact Enrichment (V3.5)
# ---------------------------------------------------------------------------

# Ordered list of contact/about page slugs to probe for phone numbers.
# Tried in sequence; first slug that yields a valid Israeli phone wins.
_CONTACT_PAGE_SLUGS: list[str] = [
    "/contact",
    "/contact-us",
    "/contacts",
    "/about",
    "/about-us",
    "/צור-קשר",          # Hebrew: "contact us"
    "/אודות",            # Hebrew: "about"
    "/contact.html",
    "/contact-us.html",
    "/about.html",
    "/info",
]


def build_browser_headers() -> dict:
    """
    Return a realistic browser header dict with a random User-Agent.

    Module-level equivalent of ScraperAgent._build_headers().
    Used by enrich_contact_pages() which runs outside any agent instance.
    """
    return {
        "User-Agent":      random.choice(ScraperAgent._DEFAULT_UA_POOL),
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept":          "text/html, */*",
        "Referer":         "https://www.google.co.il/",
        "DNT":             "1",
    }


async def enrich_contact_pages(
    session: aiohttp.ClientSession,
    domain: str,
    max_pages: int = 3,
) -> Optional[str]:
    """
    Probe up to max_pages contact/about slugs for a domain, searching for an
    Israeli phone number not captured on the homepage.

    Flow:
      1. Iterate _CONTACT_PAGE_SLUGS in order (up to max_pages attempts).
      2. Fetch raw HTML with browser headers and V3_FETCH_TIMEOUT.
      3. Run extract_whatsapp_numbers() + select_best_phone() on the HTML.
      4. Return the first normalized 972XXXXXXXXX string found, or None.

    Jitter (DELAY_MIN–DELAY_MAX) is applied between requests (Iron Principle 5b).
    Returns None if no phone is found across all probed pages.
    No LLM cost — pure HTML fetch + regex.

    Called by live_run._run_contact_enrichment_phase() for every QUALIFIED_A /
    QUALIFIED_B_PENDING_VERIFY lead that has no WhatsApp number after the main
    classification pass.
    """
    if not domain:
        return None

    probed = 0
    for slug in _CONTACT_PAGE_SLUGS:
        if probed >= max_pages:
            break
        # Percent-encode the slug so Hebrew characters (e.g. /צור-קשר) become
        # valid URL path components. safe='/' preserves the leading slash and
        # any internal slashes; only non-ASCII and reserved chars are encoded.
        encoded_slug = _url_quote(slug, safe="/")
        url = f"https://{domain}{encoded_slug}"
        try:
            await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # jitter
            # Sprint 10.5: double-layer timeout — aiohttp inner + asyncio.wait_for outer.
            # Prevents Windows DNS thread-pool hangs from stalling the contact phase.
            html = await asyncio.wait_for(
                fetch_raw_html(
                    session,
                    url,
                    headers=build_browser_headers(),
                    timeout_sec=V3_FETCH_TIMEOUT,
                ),
                timeout=V3_HARD_TIMEOUT,
            )
            probed += 1
            if not html:
                continue
            phone = select_best_phone(extract_whatsapp_numbers(html))
            if phone:
                return phone
        except asyncio.TimeoutError:
            probed += 1
            continue
        except Exception:
            probed += 1
            continue

    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_domain_from_place(place: dict) -> Optional[str]:
    """Extract and normalize domain from a SerpApi place object."""
    website = place.get("website") or place.get("link") or ""
    if not website:
        return None
    match = _DOMAIN_FROM_URL_PATTERN.match(website)
    return normalize_domain(match.group(1)) if match else None


def _extract_phone_from_place(place: dict) -> Optional[str]:
    """Return the raw phone string from a SerpApi place object."""
    return place.get("phone") or place.get("phone_number")


def _is_captcha_response(text: str) -> bool:
    """Detect common CAPTCHA page signatures in an HTML response body."""
    captcha_signals = [
        "captcha", "robot", "are you human", "verify you are",
        "unusual traffic", "security check", "ddos-guard",
        "cf-browser-verification",
    ]
    lower = text.lower()
    return any(sig in lower for sig in captcha_signals)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class AntiBotSignal(Exception):
    """Raised when an anti-bot mechanism is detected during a request."""


# ---------------------------------------------------------------------------
# Pipeline entry point — wires agents → NLP → upsert_lead
# ---------------------------------------------------------------------------

async def run_agent_pipeline(
    agent: ScraperAgent,
    db_path: Path,
    nlp_classify_fn,            # callable: (text: str) -> (status, confidence)
    insert_classification_fn,   # callable: (conn, lead_id, category, confidence, signals, model_v)
) -> AgentRunLog:
    """
    Top-level pipeline orchestrator for a single agent run.

    Flow:
      1. Run the agent — collects AgentResult list with raw_text populated.
      2. For each result: call nlp_classify_fn to get (status, confidence).
      3. Upsert the lead into SQLite via upsert_lead().
      4. Record the NLP classification in lead_classifications table.
      5. Return the completed AgentRunLog for observability.

    This function owns the SQLite connection lifecycle for the entire run.
    nlp_classify_fn is injected (not imported) to avoid circular imports
    between scrapers.py and nlp_classifier.py.
    """
    conn = get_connection(db_path)
    leads_upserted = 0

    async with aiohttp.ClientSession() as session:
        results = await agent.run(session)

    for result in results:
        try:
            status, confidence = await nlp_classify_fn(result.raw_text)
            lead_data = result.to_lead_dict(status=status)
            lead_id = upsert_lead(
                conn,
                lead_data,
                vector=result.vector,
                source_url=result.source_url,
                raw_snippet=result.raw_text[:500] if result.raw_text else None,
            )
            insert_classification_fn(
                conn,
                lead_id=lead_id,
                category=_status_to_category(status),
                confidence=confidence,
                signals=None,           # populated by nlp_classifier
                model_version="tier1"   # overwritten by nlp_classifier for tier 2
            )
            leads_upserted += 1
        except Exception as exc:
            agent._log_event("UPSERT_ERROR", domain=result.domain, error=str(exc))

    agent._run_log.leads_upserted = leads_upserted
    conn.close()
    return agent._run_log


def _status_to_category(status: str) -> str:
    """
    Map a leads.status value to the lead_classifications.category enum.
    Falls back to MANUFACTURER for unresolved statuses.
    """
    mapping = {
        "QUALIFIED_A":                  "MANUFACTURER",
        "QUALIFIED_B_PENDING_VERIFY":   "IMPORTER",
        "DISQUALIFIED_C":               "DROPSHIPPER",
    }
    return mapping.get(status, "MANUFACTURER")
