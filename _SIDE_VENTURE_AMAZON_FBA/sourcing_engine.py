"""
AI Sourcing Engine — India → US Physical Arbitrage
====================================================
Hunts for physical goods (distressed lots, export surplus, liquidations) in
India that pass the Landed-Cost gate and fall inside the Survival Zone
defined by tariff_heatmap.py.

Architecture
------------
  SourceAdapter  (pluggable per data source)
      ↓  RawListing
  LLMExtractor   (Anthropic SDK — structured extraction)
      ↓  ExtractedListing
  GateChecker    (landed_cost_calculator.py — hard financial gate)
      ↓  OpportunityCandidate  (if passes)
  Scorer         (demand × margin × source-reliability × recency)
      ↓  ranked list
  Triage Queue   (human-in-the-loop review)
      ↓  ReviewDecision  (approve / reject / snooze)
  FeedbackLog    (trains the scorer over time)

Design principles
-----------------
  • Variable yield: 0–N approved, never forced to N.
  • Independent verification: LLM extracts, calculator decides — not the same
    model doing both and grading its own output.
  • Hard gate before human sees it: no human time wasted below the margin floor.
  • Every decision logged for feedback loop.

Quick start
-----------
  pip install anthropic rich requests
  export ANTHROPIC_API_KEY=sk-...
  python sourcing_engine.py --run mock       # demo with synthetic listings
  python sourcing_engine.py --run live       # real adapters (configure below)

Integration points (replace TODOs with real credentials/endpoints)
-----------
  IndiaMART  : register at developers.indiamart.com → get client_id/secret
  Volza      : paid API — volza.com/api-documentation
  Helium10   : Cerebro / Magnet API — developers.helium10.com
  IBBI       : scrape ibbi.gov.in/auctions (public, no auth)
"""

from __future__ import annotations

import os
import sys
import json
import math
import time
import logging
import hashlib
import argparse
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landed_cost_calculator import (
    ProductInputs, calculate, MockRateProvider, LandedCostBreakdown
)
from tariff_heatmap import ParametricRateProvider, SURVIVAL_FLOOR, WARNING_FLOOR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("sourcing")

# ---------------------------------------------------------------------------
# CONFIG — edit these before going live
# ---------------------------------------------------------------------------

class Config:
    ANTHROPIC_API_KEY: str    = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL:   str    = "claude-sonnet-4-5"

    # Gate thresholds (must survive BOTH scenarios)
    GATE_NET_MARGIN_BASE:     float = 0.15   # at current tariff
    GATE_NET_MARGIN_STRESS:   float = 0.10   # at stress tariff (+15pp)
    GATE_MAX_PPC_ASSUMPTION:  float = 0.25   # reject if category ACoS > this

    # Financial
    MARKET_SELL_ANCHOR_USD:  float = 19.99   # override per-listing from Helium10
    TARIFF_STRESS_ADD_PP:    float = 0.15    # +15pp stress scenario
    CURRENT_INDIA_TARIFF:    float = 0.313   # planning baseline

    # Sourcing parameters
    MAX_UNIT_COST_USD:        float = 8.00   # don't bother above this landed
    MIN_QTY:                  int   = 50     # minimum lot size worth shipping
    MAX_QTY:                  int   = 5000   # above this = capital-lock risk

    # Human review
    REVIEW_BATCH_SIZE:        int   = 20     # candidates per review session
    FEEDBACK_LOG_PATH:        str   = "feedback_log.jsonl"

    # Allowed HTS chapters (whitelist — keeps the engine focused)
    ALLOWED_HTS_CHAPTERS = {
        "42",  # leather goods
        "43",  # fur (genuine)
        "44",  # wood articles
        "57",  # carpets/rugs
        "58",  # lace/embroidery
        "61",  # knit apparel
        "62",  # woven apparel
        "63",  # other textiles
        "67",  # feather/down
        "69",  # ceramics
        "70",  # glass
        "71",  # jewellery (imitation)
        "83",  # misc base metal articles
    }


# ---------------------------------------------------------------------------
# 1. CORE DATA MODELS
# ---------------------------------------------------------------------------

class ReviewStatus(str, Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SNOOZED  = "snoozed"


@dataclass
class RawListing:
    """Raw, unprocessed listing as pulled from a source adapter."""
    source:       str            # adapter name
    source_id:    str            # unique ID within that source
    url:          str
    raw_text:     str            # full text blob for LLM extraction
    scraped_at:   datetime       = field(default_factory=datetime.utcnow)
    extra:        dict           = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Dedup key — prevents re-processing identical listings."""
        blob = f"{self.source}:{self.source_id}:{self.raw_text[:200]}"
        return hashlib.md5(blob.encode()).hexdigest()


@dataclass
class ExtractedListing:
    """Structured fields extracted by the LLM from RawListing.raw_text."""
    raw:               RawListing
    product_name:      str
    category:          str             # e.g. "cotton home textile"
    hts_guess:         str             # e.g. "6304.92.0000"
    unit_cost_inr:     float
    qty_available:     int
    weight_kg:         float           # per unit
    cubic_ft:          float           # per unit (for FBA storage)
    seller_name:       str
    seller_city:       str
    seller_contact:    str             # phone or email
    listing_age_days:  int
    llm_confidence:    float           # 0.0 – 1.0
    llm_reasoning:     str             # why the LLM thinks this is real
    extraction_error:  Optional[str]   = None


@dataclass
class OpportunityCandidate:
    """An ExtractedListing that has passed the financial gate."""
    listing:            ExtractedListing
    calc_base:          LandedCostBreakdown   # at current tariff
    calc_stress:        LandedCostBreakdown   # at current tariff + stress add-on
    demand_score:       float                  # 0.0 – 1.0 (Helium10 rank)
    source_reliability: float                  # per-adapter weight
    score:              float                  # final composite score
    created_at:         datetime               = field(default_factory=datetime.utcnow)
    status:             ReviewStatus           = ReviewStatus.PENDING
    reviewer_note:      str                    = ""


@dataclass
class ReviewDecision:
    candidate_fingerprint: str
    decision:              ReviewStatus
    reviewer_note:         str
    decided_at:            datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# 2. SOURCE ADAPTERS
# ---------------------------------------------------------------------------

class SourceAdapter(ABC):
    name:              str   = "base"
    reliability_score: float = 0.5   # prior on data quality (0–1)

    @abstractmethod
    def fetch(self, **kwargs) -> Iterator[RawListing]:
        """Yield RawListings from this source. Lazy / streaming preferred."""
        ...


class IndiaMARTAdapter(SourceAdapter):
    """
    IndiaMART Buy Leads + Product Catalogue.

    Real integration:
        POST https://imapi.indiamart.com/imaccount/lead/getleads
        Credentials: register at developers.indiamart.com
        Rate limit: 1 req/sec on free tier

    Filter strategy:
        keywords = ["export surplus", "stock lot", "ready stock",
                    "urgent sale", "liquidation", "cancelled order"]
        category_ids = [textiles, handicraft, home furnishing, leather]
    """
    name              = "indiamart"
    reliability_score = 0.65    # listings are real but frequently stale/inaccurate

    # TODO: replace with real API credentials
    CLIENT_ID     = os.getenv("INDIAMART_CLIENT_ID",     "")
    CLIENT_SECRET = os.getenv("INDIAMART_CLIENT_SECRET", "")

    SEARCH_KEYWORDS = [
        "export surplus stock lot",
        "ready stock urgent sale textile",
        "cancelled export order home furnishing",
        "liquidation stock cotton",
        "distressed inventory leather",
    ]

    def fetch(self, max_listings: int = 200) -> Iterator[RawListing]:
        if not self.CLIENT_ID:
            log.warning("IndiaMART: CLIENT_ID not set — yielding nothing. "
                        "Set INDIAMART_CLIENT_ID env var.")
            return

        import requests
        for keyword in self.SEARCH_KEYWORDS:
            params = {
                "glusr_usr_name": self.CLIENT_ID,
                "glusr_usr_pwd":  self.CLIENT_SECRET,
                "keyword":        keyword,
                "page_count":     "1",
            }
            try:
                r = requests.get(
                    "https://imapi.indiamart.com/imaccount/product/getproducts",
                    params=params, timeout=15
                )
                r.raise_for_status()
                data = r.json()
                for item in data.get("Products", [])[:max_listings]:
                    yield RawListing(
                        source    = self.name,
                        source_id = str(item.get("prod_id", "")),
                        url       = item.get("prod_link", ""),
                        raw_text  = json.dumps(item, ensure_ascii=False),
                        extra     = {"keyword": keyword},
                    )
                time.sleep(1.1)   # respect rate limit
            except Exception as exc:
                log.error(f"IndiaMART fetch error (keyword={keyword!r}): {exc}")


class VolzaAdapter(SourceAdapter):
    """
    Volza.com — India export shipment records (US buyer + Indian supplier data).
    Use as DEMAND VALIDATION (what's already shipping India→US) not as a
    liquidation source.  The real value: identify categories with real trade
    volume and existing supplier networks.

    Real integration: paid subscription → REST API key
    Docs: https://www.volza.com/api-documentation
    """
    name              = "volza"
    reliability_score = 0.85    # shipment records are factual

    API_KEY = os.getenv("VOLZA_API_KEY", "")
    BASE_URL = "https://api.volza.com/v1"

    def fetch(self, hts_chapters: List[str] = None, **kwargs) -> Iterator[RawListing]:
        if not self.API_KEY:
            log.warning("Volza: API_KEY not set — skipping.")
            return

        chapters = hts_chapters or list(Config.ALLOWED_HTS_CHAPTERS)[:5]
        import requests
        for chapter in chapters:
            try:
                r = requests.get(
                    f"{self.BASE_URL}/export-records",
                    headers={"Authorization": f"Bearer {self.API_KEY}"},
                    params={"hs_code": chapter, "origin": "IN",
                            "destination": "US", "limit": 50},
                    timeout=20,
                )
                r.raise_for_status()
                for record in r.json().get("data", []):
                    yield RawListing(
                        source    = self.name,
                        source_id = str(record.get("shipment_id", "")),
                        url       = f"https://www.volza.com/shipment/{record.get('shipment_id')}",
                        raw_text  = json.dumps(record, ensure_ascii=False),
                    )
            except Exception as exc:
                log.error(f"Volza fetch error (chapter={chapter}): {exc}")


class IBBIAdapter(SourceAdapter):
    """
    IBBI (Insolvency and Bankruptcy Board of India) — liquidation auction notices.
    PUBLIC, no auth required. PDFs scraped from ibbi.gov.in/auctions.

    These are the HIGHEST quality distressed-asset signals in the system:
    physical assets legally mandated for sale, with verified valuations.

    Real integration:
        1. Scrape https://ibbi.gov.in/home/pending_applications  (HTML table)
        2. Download each PDF
        3. Use pdfplumber to extract lot descriptions + valuations
        4. Feed raw text to LLM extractor

    Dependencies: pip install requests beautifulsoup4 pdfplumber
    """
    name              = "ibbi"
    reliability_score = 0.95   # legal filings — highest data quality

    BASE_URL = "https://ibbi.gov.in"

    def fetch(self, max_pages: int = 3) -> Iterator[RawListing]:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            log.error("IBBI adapter requires: pip install requests beautifulsoup4")
            return

        for page in range(1, max_pages + 1):
            try:
                r = requests.get(
                    f"{self.BASE_URL}/home/pending_applications",
                    params={"page": page},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=20,
                )
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                for row in soup.select("table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 3:
                        continue
                    pdf_link = row.find("a", href=True)
                    url = (self.BASE_URL + pdf_link["href"]) if pdf_link else ""
                    yield RawListing(
                        source    = self.name,
                        source_id = hashlib.md5(url.encode()).hexdigest()[:12],
                        url       = url,
                        raw_text  = " | ".join(cells),
                        extra     = {"pdf_url": url},
                    )
                time.sleep(2)
            except Exception as exc:
                log.error(f"IBBI fetch error (page={page}): {exc}")


class MockAdapter(SourceAdapter):
    """
    Synthetic listings for testing the pipeline end-to-end without live APIs.
    Designed to produce a realistic mix: some survivors, some dead, some edge cases.
    """
    name              = "mock"
    reliability_score = 1.0   # fully deterministic for testing

    SYNTHETIC_LISTINGS = [
        {
            "id": "mock-001",
            "text": (
                "URGENT SALE — Export surplus cotton cushion covers, 18x18 inch, "
                "natural weave, 600 pcs available. Factory price Rs 175/pc. "
                "Weight approx 180g each. Ready stock Surat Gujarat. "
                "Buyer defaulted — need to clear by end of month. "
                "Contact: Rajesh Patel +91-98765-43210 rajesh@suratfab.co.in"
            ),
        },
        {
            "id": "mock-002",
            "text": (
                "Leather passport wallets, genuine buffalo leather, unbranded. "
                "Lot of 200 pcs at Rs 350/pc. Weight 120g each. "
                "Colour: tan and dark brown. Made in Kanpur UP. "
                "GSTIN verified supplier. Contact Farhan Ali 9876501234"
            ),
        },
        {
            "id": "mock-003",
            "text": (
                "Brass decorative elephant figurines 4-inch, hand-polished. "
                "Export overstock 400 pieces at Rs 280 each. "
                "Approx 350g per piece. Moradabad UP manufacturer. "
                "WhatsApp only: Suresh Kumar 9812345678"
            ),
        },
        {
            "id": "mock-004",
            "text": (
                "Imitation jewellery lot — mixed earrings and necklaces, "
                "gold-plated German silver. 1000 units. Rs 120/pc. "
                "Weight 50g average. Jaipur Rajasthan. "
                "Note: some pieces carry visible brand markings — REJECT."
            ),
        },
        {
            "id": "mock-005",
            "text": (
                "Cotton bed sheets king size, 300 thread count, solid colours. "
                "Factory seconds (minor weave inconsistency, not visible to end user). "
                "500 sets at Rs 420/set. Weight 1.1kg per set. "
                "Panipat Haryana mill. Contact: production@northtex.in"
            ),
        },
        {
            "id": "mock-006",
            "text": (
                "Wooden picture frames 4x6 and 5x7, mango wood, natural finish. "
                "Cancelled US order — 800 units mixed sizes. Rs 95/pc avg. "
                "Weight 280g avg, already US-spec labeled. "
                "Saharanpur UP. Contact Mahesh 9012345678"
            ),
        },
    ]

    def fetch(self, **kwargs) -> Iterator[RawListing]:
        for item in self.SYNTHETIC_LISTINGS:
            yield RawListing(
                source    = self.name,
                source_id = item["id"],
                url       = f"mock://listing/{item['id']}",
                raw_text  = item["text"],
            )
            time.sleep(0.05)   # simulate IO


# ---------------------------------------------------------------------------
# 3. LLM EXTRACTOR
# ---------------------------------------------------------------------------

EXTRACTION_TOOL = {
    "name": "extract_listing_fields",
    "description": (
        "Extract structured product and seller information from an Indian "
        "wholesale/liquidation listing. Return null for any field you cannot "
        "determine with reasonable confidence."
    ),
    "input_schema": {
        "type": "object",
        "required": [
            "product_name", "category", "hts_guess",
            "unit_cost_inr", "qty_available", "weight_kg", "cubic_ft",
            "seller_name", "seller_city", "seller_contact",
            "listing_age_days", "llm_confidence", "llm_reasoning",
            "has_registered_brand", "red_flags"
        ],
        "properties": {
            "product_name":        {"type": "string"},
            "category":            {"type": "string"},
            "hts_guess":           {"type": "string",  "description": "Best-guess 10-digit HTS code"},
            "unit_cost_inr":       {"type": "number",  "description": "Price per unit in Indian Rupees"},
            "qty_available":       {"type": "integer"},
            "weight_kg":           {"type": "number",  "description": "Weight per unit in kg"},
            "cubic_ft":            {"type": "number",  "description": "Volume per unit in cubic feet (estimate if not given)"},
            "seller_name":         {"type": "string"},
            "seller_city":         {"type": "string"},
            "seller_contact":      {"type": "string",  "description": "Phone or email"},
            "listing_age_days":    {"type": "integer", "description": "Estimated days since listed; 0 if not stated"},
            "llm_confidence":      {"type": "number",  "minimum": 0.0, "maximum": 1.0,
                                    "description": "Your confidence that this is a real, accurately described listing"},
            "llm_reasoning":       {"type": "string",  "description": "1-2 sentence justification for the confidence score"},
            "has_registered_brand":{"type": "boolean", "description": "True if ANY registered brand mark appears on goods"},
            "red_flags":           {"type": "array",   "items": {"type": "string"},
                                    "description": "List of concerns: IP risk, too-good-to-be-true pricing, missing contact, etc."},
        }
    }
}

EXTRACTION_SYSTEM_PROMPT = textwrap.dedent("""
    You are a senior import/export analyst. Your job is to extract structured
    product data from raw Indian wholesale or liquidation listings.

    Rules:
    1. Never invent data. If a field is absent, use a conservative estimate
       and flag it in red_flags. Do NOT guess contact details.
    2. Weight: if not stated, estimate from product type (e.g. cushion cover ~0.18kg).
       Always flag estimated weights in red_flags.
    3. HTS code: give your best 6-digit guess (pad remaining digits with zeros).
    4. has_registered_brand = true if ANY brand name, logo, or trademark is
       mentioned on the goods — even if the seller says it's generic.
    5. llm_confidence: be harsh. 0.9+ means you have name + contact + price +
       weight + quantity + location. Deduct heavily for missing fields.
    6. cubic_ft estimate guide: cushion cover ~0.08, sheet set ~0.40, wallet ~0.03,
       figurine (4") ~0.02, frame (5x7) ~0.04.
""").strip()


class LLMExtractor:
    """Calls Anthropic SDK to extract structured fields from raw listing text."""

    def __init__(self, api_key: str = Config.ANTHROPIC_API_KEY,
                 model:   str = Config.ANTHROPIC_MODEL):
        self.model   = model
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("pip install anthropic  required for LLM extraction.")
        return self._client

    def extract(self, raw: RawListing) -> ExtractedListing:
        """
        Returns an ExtractedListing. On any API error, returns a placeholder
        with extraction_error set — never raises, so the pipeline continues.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=EXTRACTION_SYSTEM_PROMPT,
                tools=[EXTRACTION_TOOL],
                tool_choice={"type": "tool", "name": "extract_listing_fields"},
                messages=[{
                    "role": "user",
                    "content": (
                        f"Extract all fields from this listing:\n\n"
                        f"SOURCE: {raw.source}  |  URL: {raw.url}\n\n"
                        f"{raw.raw_text}"
                    )
                }]
            )
            # Tool use response — find the tool_result block
            tool_block = next(
                (b for b in response.content if b.type == "tool_use"), None
            )
            if tool_block is None:
                raise ValueError("LLM returned no tool_use block")
            f = tool_block.input

            return ExtractedListing(
                raw              = raw,
                product_name     = f["product_name"],
                category         = f["category"],
                hts_guess        = f["hts_guess"],
                unit_cost_inr    = float(f["unit_cost_inr"]),
                qty_available    = int(f["qty_available"]),
                weight_kg        = float(f["weight_kg"]),
                cubic_ft         = float(f["cubic_ft"]),
                seller_name      = f["seller_name"],
                seller_city      = f["seller_city"],
                seller_contact   = f["seller_contact"],
                listing_age_days = int(f.get("listing_age_days", 0)),
                llm_confidence   = float(f["llm_confidence"]),
                llm_reasoning    = f["llm_reasoning"],
                extraction_error = (
                    " | ".join(f.get("red_flags", [])) or None
                    if f.get("has_registered_brand") or f.get("red_flags")
                    else None
                ),
            )

        except Exception as exc:
            log.error(f"LLM extraction failed ({raw.source_id}): {exc}")
            return ExtractedListing(
                raw=raw, product_name="EXTRACTION_FAILED", category="",
                hts_guess="0000.00.0000", unit_cost_inr=0, qty_available=0,
                weight_kg=0, cubic_ft=0, seller_name="", seller_city="",
                seller_contact="", listing_age_days=0, llm_confidence=0.0,
                llm_reasoning="", extraction_error=str(exc),
            )


# ---------------------------------------------------------------------------
# 4. FINANCIAL GATE CHECKER
# ---------------------------------------------------------------------------

class GateResult(str, Enum):
    PASS    = "PASS"
    WARNING = "WARNING"
    FAIL    = "FAIL"


@dataclass
class GateReport:
    result:          GateResult
    margin_base:     float   # at current tariff
    margin_stress:   float   # at stress tariff
    landed_base:     float
    landed_stress:   float
    sell_price:      float
    fail_reasons:    List[str] = field(default_factory=list)


class GateChecker:
    """
    Runs the landed-cost calculator at two tariff scenarios and applies
    all hard-gate rules. Independent of the LLM — separate failure modes.
    """
    def __init__(self,
                 current_tariff: float = Config.CURRENT_INDIA_TARIFF,
                 stress_add_pp:  float = Config.TARIFF_STRESS_ADD_PP,
                 sell_price:     float = Config.MARKET_SELL_ANCHOR_USD):
        self.current_tariff = current_tariff
        self.stress_tariff  = current_tariff + stress_add_pp
        self.sell_price     = sell_price

    def check(self, ex: ExtractedListing) -> Tuple[GateReport, Optional[LandedCostBreakdown], Optional[LandedCostBreakdown]]:
        fails = []

        # --- Pre-calc hard filters ---
        if ex.extraction_error and "brand" in ex.extraction_error.lower():
            fails.append("IP RISK: registered brand detected")

        chapter = ex.hts_guess[:2]
        if chapter not in Config.ALLOWED_HTS_CHAPTERS:
            fails.append(f"HTS chapter {chapter} not in allowlist (out-of-scope category)")

        if ex.qty_available < Config.MIN_QTY:
            fails.append(f"Qty {ex.qty_available} below minimum {Config.MIN_QTY}")

        if ex.qty_available > Config.MAX_QTY:
            fails.append(f"Qty {ex.qty_available} above cap {Config.MAX_QTY} (capital lock risk)")

        if ex.llm_confidence < 0.45:
            fails.append(f"LLM confidence too low ({ex.llm_confidence:.0%}) — likely garbage data")

        if fails:
            return GateReport(GateResult.FAIL, 0, 0, 0, 0, self.sell_price, fails), None, None

        # --- Build calculator inputs ---
        def _inputs(ppc: float = Config.GATE_MAX_PPC_ASSUMPTION) -> ProductInputs:
            return ProductInputs(
                sku              = ex.raw.source_id,
                hts_code         = ex.hts_guess,
                origin           = "IN",
                unit_cost_inr    = ex.unit_cost_inr,
                qty              = ex.qty_available,
                india_prep_inr   = 40.0,    # fixed branding/label allowance
                india_qc_inr     = 12.0,
                india_inland_inr = 8.0,
                weight_kg        = ex.weight_kg,
                cubic_ft         = ex.cubic_ft,
                freight_mode     = "sea_lcl",
                customs_broker_usd_per_shipment = 175.0,
                inbound_to_fba_usd_per_unit     = 0.35,
                fba_size_tier    = "small_standard",
                fba_storage_months = 2.5,
                target_sell_price_usd = self.sell_price,
                ppc_pct_of_revenue    = ppc,
                returns_reserve_pct   = 0.06,
                amazon_referral_pct   = 0.15,
            )

        try:
            calc_base   = calculate(_inputs(), ParametricRateProvider(self.current_tariff))
            calc_stress = calculate(_inputs(), ParametricRateProvider(self.stress_tariff))
        except Exception as exc:
            fails.append(f"Calculator error: {exc}")
            return GateReport(GateResult.FAIL, 0, 0, 0, 0, self.sell_price, fails), None, None

        m_base   = calc_base.net_margin_pct
        m_stress = calc_stress.net_margin_pct

        # --- Apply margin gates ---
        if m_base < Config.GATE_NET_MARGIN_BASE:
            fails.append(
                f"Base margin {m_base:.1%} < floor {Config.GATE_NET_MARGIN_BASE:.0%} "
                f"(landed ${calc_base.landed_cost_pre_amazon:.2f} too high)"
            )
        if m_stress < Config.GATE_NET_MARGIN_STRESS:
            fails.append(
                f"Stress margin {m_stress:.1%} < stress floor {Config.GATE_NET_MARGIN_STRESS:.0%} "
                f"(tariff spike kills deal)"
            )

        if fails:
            return GateReport(
                GateResult.FAIL, m_base, m_stress,
                calc_base.landed_cost_pre_amazon,
                calc_stress.landed_cost_pre_amazon,
                self.sell_price, fails
            ), calc_base, calc_stress

        result = GateResult.PASS if m_base >= Config.GATE_NET_MARGIN_BASE else GateResult.WARNING
        return GateReport(
            result, m_base, m_stress,
            calc_base.landed_cost_pre_amazon,
            calc_stress.landed_cost_pre_amazon,
            self.sell_price, fails
        ), calc_base, calc_stress


# ---------------------------------------------------------------------------
# 5. SCORING
# ---------------------------------------------------------------------------

class Scorer:
    """
    Composite score for ranking candidates in the triage queue.

    score = net_margin_base
            × demand_score         (Helium10 search-volume proxy; mock=0.5)
            × source_reliability   (per adapter)
            × recency_decay        (e-^(age/30) — prefer fresh listings)
            × confidence           (LLM confidence in the extraction)

    Range: 0.0 – 1.0 (higher = better candidate for human review)
    """

    def score(self, ex: ExtractedListing, gate: GateReport,
              source_reliability: float) -> float:
        if gate.result == GateResult.FAIL:
            return 0.0

        recency = math.exp(-ex.listing_age_days / 30.0)
        demand  = self._mock_demand_score(ex.hts_guess)

        raw = (
            gate.margin_base
            * demand
            * source_reliability
            * recency
            * ex.llm_confidence
        )
        return round(min(raw, 1.0), 4)

    @staticmethod
    def _mock_demand_score(hts_guess: str) -> float:
        """
        Stub — replace with live Helium10 Magnet API call.
        Maps HTS chapter to a rough demand proxy based on US market research.
        """
        chapter_scores = {
            "63": 0.80,  # home textiles — strong US demand
            "62": 0.75,  # woven apparel
            "42": 0.72,  # leather goods
            "44": 0.65,  # wood articles
            "71": 0.60,  # imitation jewellery
            "83": 0.55,  # misc base metal
            "69": 0.50,  # ceramics
        }
        return chapter_scores.get(hts_guess[:2], 0.45)


# ---------------------------------------------------------------------------
# 6. TRIAGE QUEUE
# ---------------------------------------------------------------------------

class TriageQueue:
    """Sorted list of OpportunityCandidates waiting for human review."""

    def __init__(self):
        self._candidates: List[OpportunityCandidate] = []
        self._seen_fingerprints: set = set()

    def add(self, candidate: OpportunityCandidate) -> bool:
        fp = candidate.listing.raw.fingerprint
        if fp in self._seen_fingerprints:
            log.debug(f"Duplicate skipped: {fp[:8]}")
            return False
        self._seen_fingerprints.add(fp)
        self._candidates.append(candidate)
        self._candidates.sort(key=lambda c: c.score, reverse=True)
        return True

    def pending(self) -> List[OpportunityCandidate]:
        return [c for c in self._candidates if c.status == ReviewStatus.PENDING]

    def top_n(self, n: int) -> List[OpportunityCandidate]:
        return self.pending()[:n]

    def __len__(self) -> int:
        return len(self.pending())


# ---------------------------------------------------------------------------
# 7. HUMAN REVIEW INTERFACE
# ---------------------------------------------------------------------------

def _try_rich() -> bool:
    try:
        import rich  # noqa
        return True
    except ImportError:
        return False


def _plain_review_row(i: int, c: OpportunityCandidate) -> str:
    ex = c.listing
    g  = c.calc_base
    lines = [
        f"\n{'─'*72}",
        f"#{i+1}  SCORE {c.score:.3f}  |  {ex.raw.source.upper()}  |  {ex.raw.url}",
        f"  {ex.product_name}",
        f"  Seller: {ex.seller_name}, {ex.seller_city}  |  Contact: {ex.seller_contact}",
        f"  INR {ex.unit_cost_inr:.0f}/pc  ×  {ex.qty_available} pcs  |  "
        f"{ex.weight_kg:.2f}kg/unit  |  HTS {ex.hts_guess}",
        f"  Landed ${g.landed_cost_pre_amazon:.2f}  |  Sell ${g.target_sell_price:.2f}  |  "
        f"Net {g.net_margin_pct:.1%}  (stress: {c.calc_stress.net_margin_pct:.1%})",
        f"  LLM confidence: {ex.llm_confidence:.0%}  —  {ex.llm_reasoning}",
    ]
    if ex.extraction_error:
        lines.append(f"  ⚠ FLAGS: {ex.extraction_error}")
    return "\n".join(lines)


def _rich_review_table(candidates: List[OpportunityCandidate]):
    from rich.console import Console
    from rich.table   import Table
    from rich         import box

    console = Console()
    table   = Table(box=box.ROUNDED, title="[bold]Triage Queue[/bold]",
                    show_lines=True, highlight=True)
    table.add_column("#",         style="dim",    width=3)
    table.add_column("Score",     style="cyan",   width=6)
    table.add_column("Product",   style="white",  width=30)
    table.add_column("Seller",    style="yellow", width=20)
    table.add_column("INR/pc",    style="green",  width=8)
    table.add_column("Qty",       style="green",  width=6)
    table.add_column("Landed $",  style="magenta",width=9)
    table.add_column("Net Margin",style="bold",   width=10)
    table.add_column("Stress",    style="dim",    width=8)
    table.add_column("Flags",     style="red",    width=25)

    for i, c in enumerate(candidates):
        ex = c.listing
        margin_color = (
            "green" if c.calc_base.net_margin_pct >= 0.20 else
            "yellow" if c.calc_base.net_margin_pct >= 0.15 else "red"
        )
        table.add_row(
            str(i+1),
            f"{c.score:.3f}",
            ex.product_name[:30],
            f"{ex.seller_name[:15]}, {ex.seller_city[:8]}",
            f"{ex.unit_cost_inr:.0f}",
            str(ex.qty_available),
            f"${c.calc_base.landed_cost_pre_amazon:.2f}",
            f"[{margin_color}]{c.calc_base.net_margin_pct:.1%}[/{margin_color}]",
            f"{c.calc_stress.net_margin_pct:.1%}",
            (ex.extraction_error or "")[:25],
        )
    console.print(table)
    return console


def run_review_session(queue: TriageQueue,
                       feedback_log: str = Config.FEEDBACK_LOG_PATH,
                       batch_size: int   = Config.REVIEW_BATCH_SIZE
                      ) -> List[ReviewDecision]:
    """
    Interactive human review. Presents top-N candidates; reviewer types
    A (approve), R (reject), S (snooze), Q (quit session).
    Decisions are logged to feedback_log for scorer improvement.
    """
    batch = queue.top_n(batch_size)
    if not batch:
        print("\nQueue is empty — no candidates to review.")
        return []

    use_rich = _try_rich()

    if use_rich:
        console = _rich_review_table(batch)
    else:
        for i, c in enumerate(batch):
            print(_plain_review_row(i, c))

    print(f"\n{'='*72}")
    print(f"Reviewing {len(batch)} candidates.  Commands: A=Approve  R=Reject  S=Snooze  Q=Quit")
    print(f"{'='*72}")

    decisions: List[ReviewDecision] = []
    for i, candidate in enumerate(batch):
        ex = candidate.listing
        print(f"\n[{i+1}/{len(batch)}]  {ex.product_name}  —  {ex.seller_city}  "
              f"|  Net {candidate.calc_base.net_margin_pct:.1%}  "
              f"|  Score {candidate.score:.3f}")

        while True:
            raw = input("  Decision [A/R/S/Q]: ").strip().upper()
            if raw in ("A", "R", "S", "Q"):
                break
            print("  Invalid — enter A, R, S, or Q.")

        if raw == "Q":
            print("Review session ended early.")
            break

        note = ""
        if raw in ("R", "S"):
            note = input("  Note (optional): ").strip()

        status_map = {"A": ReviewStatus.APPROVED, "R": ReviewStatus.REJECTED,
                      "S": ReviewStatus.SNOOZED}
        candidate.status        = status_map[raw]
        candidate.reviewer_note = note

        dec = ReviewDecision(
            candidate_fingerprint = ex.raw.fingerprint,
            decision              = status_map[raw],
            reviewer_note         = note,
        )
        decisions.append(dec)

        # Append to JSONL feedback log
        with open(feedback_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(dec), default=str) + "\n")

        color = {"A": "\033[92m", "R": "\033[91m", "S": "\033[93m"}[raw]
        print(f"  {color}→ {status_map[raw].value.upper()}\033[0m")

    approved = [d for d in decisions if d.decision == ReviewStatus.APPROVED]
    print(f"\n{'='*72}")
    print(f"Session complete: {len(approved)} approved / "
          f"{len(decisions) - len(approved)} rejected-or-snoozed "
          f"/ {len(batch) - len(decisions)} not reached")
    return decisions


# ---------------------------------------------------------------------------
# 8. PIPELINE ORCHESTRATOR
# ---------------------------------------------------------------------------

class SourcingPipeline:
    """
    Wires all components together for a single run.

    run() flow:
        1. Fetch from all configured adapters
        2. LLM-extract each raw listing
        3. Hard-gate filter (calculator, no LLM)
        4. Score and enqueue passing candidates
        5. Optionally run interactive human review

    This is deliberately stateless per run — the feedback_log provides
    continuity between runs.
    """

    def __init__(self,
                 adapters:  List[SourceAdapter],
                 extractor: LLMExtractor,
                 gate:      GateChecker,
                 scorer:    Scorer,
                 queue:     TriageQueue):
        self.adapters  = adapters
        self.extractor = extractor
        self.gate      = gate
        self.scorer    = scorer
        self.queue     = queue

    def run(self,
            interactive_review: bool = True,
            max_per_adapter: int = 50) -> TriageQueue:

        stats = dict(fetched=0, extraction_errors=0, gate_fails=0, enqueued=0)

        for adapter in self.adapters:
            log.info(f"Fetching from {adapter.name}...")
            count = 0
            for raw in adapter.fetch():
                if count >= max_per_adapter:
                    break
                stats["fetched"] += 1
                count            += 1

                # --- Extract ---
                ex = self.extractor.extract(raw)
                if ex.extraction_error and "EXTRACTION_FAILED" in ex.product_name:
                    stats["extraction_errors"] += 1
                    continue

                # --- Gate ---
                gate_report, calc_base, calc_stress = self.gate.check(ex)
                if gate_report.result == GateResult.FAIL:
                    stats["gate_fails"] += 1
                    log.debug(
                        f"GATE FAIL {raw.source_id[:12]}: "
                        f"{'; '.join(gate_report.fail_reasons)}"
                    )
                    continue

                # --- Score ---
                s = self.scorer.score(ex, gate_report, adapter.reliability_score)

                candidate = OpportunityCandidate(
                    listing            = ex,
                    calc_base          = calc_base,
                    calc_stress        = calc_stress,
                    demand_score       = Scorer._mock_demand_score(ex.hts_guess),
                    source_reliability = adapter.reliability_score,
                    score              = s,
                )
                if self.queue.add(candidate):
                    stats["enqueued"] += 1
                    log.info(
                        f"QUEUED [{adapter.name}] {ex.product_name[:40]}  "
                        f"score={s:.3f}  margin={gate_report.margin_base:.1%}"
                    )

        log.info(
            f"Run complete — fetched={stats['fetched']}  "
            f"extraction_errors={stats['extraction_errors']}  "
            f"gate_fails={stats['gate_fails']}  "
            f"enqueued={stats['enqueued']}"
        )

        if interactive_review and len(self.queue) > 0:
            run_review_session(self.queue)
        elif not interactive_review:
            log.info(f"Non-interactive mode — {len(self.queue)} candidates in queue.")

        return self.queue


# ---------------------------------------------------------------------------
# 9. FACTORY — assemble a ready-to-run pipeline
# ---------------------------------------------------------------------------

def build_pipeline(mode: str = "mock",
                   interactive: bool = True) -> SourcingPipeline:
    """
    mode = "mock"  : MockAdapter only (no API keys required)
    mode = "live"  : all real adapters (requires env vars)
    """
    if mode == "mock":
        adapters = [MockAdapter()]
    else:
        adapters = [
            IndiaMARTAdapter(),
            IBBIAdapter(),
            # VolzaAdapter(),   # enable when you have an API key
        ]

    return SourcingPipeline(
        adapters  = adapters,
        extractor = LLMExtractor(),
        gate      = GateChecker(),
        scorer    = Scorer(),
        queue     = TriageQueue(),
    )


# ---------------------------------------------------------------------------
# 10. CLI ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI Sourcing Engine — India → US Arbitrage"
    )
    parser.add_argument(
        "--run", choices=["mock", "live"], default="mock",
        help="mock = synthetic test data | live = real adapters"
    )
    parser.add_argument(
        "--no-review", action="store_true",
        help="Skip interactive review (useful for automated/cron runs)"
    )
    parser.add_argument(
        "--sell-price", type=float, default=Config.MARKET_SELL_ANCHOR_USD,
        help=f"Override anchor sell price (default: ${Config.MARKET_SELL_ANCHOR_USD})"
    )
    parser.add_argument(
        "--tariff", type=float, default=Config.CURRENT_INDIA_TARIFF,
        help=f"Override current tariff rate (default: {Config.CURRENT_INDIA_TARIFF:.1%})"
    )
    args = parser.parse_args()

    if not Config.ANTHROPIC_API_KEY and args.run != "mock":
        print("ERROR: ANTHROPIC_API_KEY not set. "
              "Set it or run with --run mock for demo mode.")
        sys.exit(1)

    # Override config from CLI
    Config.CURRENT_INDIA_TARIFF  = args.tariff
    Config.MARKET_SELL_ANCHOR_USD = args.sell_price

    print(f"\n{'='*72}")
    print(f"  AI SOURCING ENGINE  |  mode={args.run.upper()}  "
          f"tariff={args.tariff:.1%}  sell=${args.sell_price}")
    print(f"  Survival gate: Net Margin ≥ {Config.GATE_NET_MARGIN_BASE:.0%} base "
          f"/ ≥ {Config.GATE_NET_MARGIN_STRESS:.0%} stress")
    print(f"{'='*72}\n")

    pipeline = build_pipeline(mode=args.run, interactive=not args.no_review)
    pipeline.run(interactive_review=not args.no_review)


if __name__ == "__main__":
    main()
