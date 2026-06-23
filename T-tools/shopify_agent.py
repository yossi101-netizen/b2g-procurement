"""
KritiKaal Leads Hunter — Shopify Footprint Agent
File: T-tools/shopify_agent.py
Governed by: B-brain/01-tech-stack.md §2 (V1 Serper vector)
Strategy: Market Scaling Blueprint — Sensor Expansion Pathway 1

Purpose:
  Detect Israeli e-commerce stores by their technology platform footprint
  rather than by keyword/SEO ranking. This agent finds businesses that
  have zero SEO investment but are actively selling and would benefit from
  a volume manufacturing partner.

Why technology fingerprinting works:
  A Shopify store loads assets from cdn.shopify.com on every page load.
  Google indexes those pages and records the content. The footer of every
  Shopify store says "Powered by Shopify". WooCommerce stores have
  /wp-content/plugins/woocommerce/ in their source. These are stable,
  deterministic signals that are independent of the business's SEO effort.

  A business can have a terrible website, no blog, no backlinks — but if
  they run Shopify and sell leather goods in Hebrew, Google has indexed it
  and Serper can return it.

Platforms detected:
  - Shopify     ("powered by shopify", cdn.shopify.com, .myshopify.com)
  - WooCommerce ("woocommerce", "added to cart" + Hebrew)
  - Wix         (wixstatic.com assets in indexed pages)

Domain handling for .myshopify.com:
  When Serper returns a .myshopify.com domain, it's the store's default
  Shopify subdomain. Most production Shopify stores redirect this to a
  custom domain. The V3 enrichment layer (aiohttp) follows the redirect
  and fetches content from the final destination. The domain stored in DB
  will be the myshopify.com subdomain, not the custom domain — this is an
  accepted Phase 1 limitation (Phase 2 will add redirect-following in
  normalize_domain).

Vector: V1_SHOPIFY_FINGERPRINT
"""

from dotenv import load_dotenv
load_dotenv()

import re
from typing import Optional

from db_init import normalize_domain
from scrapers import (
    AgentResult,
    SocialFootprintAgent,
    is_aggregator_domain,
    extract_whatsapp_numbers,
    select_best_phone,
)

# ---------------------------------------------------------------------------
# Technology fingerprint queries
# ---------------------------------------------------------------------------

_SHOPIFY_QUERIES: list[str] = [
    # ── Shopify default subdomain — Israeli Hebrew stores ────────────────────
    # myshopify.com stores that haven't set up a custom domain yet. These are
    # real active stores; the domain will be stored as-is (Phase 1 limitation).
    'site:myshopify.com "ישראל" ("עור" OR "תיקים" OR "ארנקים")',
    'site:myshopify.com "ישראל" ("קולקציה" OR "יבואן" OR "מותג")',
    'site:myshopify.com "ישראל" "סיטונאי" OR "מינימום הזמנה"',

    # ── Hebrew storefront UI — platform-agnostic ─────────────────────────────
    # "הוסף לסל" (add to cart) and "עגלת קניות" (shopping cart) appear on the
    # live pages of any Hebrew e-commerce store regardless of platform.
    # These find real stores that sell leather goods — not articles about stores.
    '"הוסף לסל" "עור" site:.co.il -site:yad2.co.il',
    '"הוסף לסל" ("תיקים" OR "ארנקים" OR "אביזרים") site:.co.il',
    '"עגלת קניות" "עור" site:.co.il',
    '"עגלת קניות" ("תיקים" OR "ארנקים") "ישראל" site:.co.il',

    # ── Wholesale checkout signals — B2B buyer indicator ─────────────────────
    # Storefront pages that combine a checkout mechanism with wholesale pricing.
    '"מינימום הזמנה" "עור" site:.co.il',
    '"מינימום הזמנה" ("תיקים" OR "ארנקים" OR "אביזרים") site:.co.il',
    '"מחיר סיטונאי" "עור" OR "תיקים" site:.co.il',

    # ── Collection/catalog pages ──────────────────────────────────────────────
    # Active brands publish their seasonal collection. "קולקציה" on a product
    # page is a strong QUALIFIED_A signal (own brand, not a dropshipper).
    '"קולקציה" "עור" "ישראל" site:.co.il -site:zap.co.il',
    '"קולקציית עור" OR "קולקציה חדשה" site:.co.il',
]

# Regex to detect custom .co.il domains referenced inside a snippet
# e.g., "Visit us at www.mybrand.co.il" or "shop.mybrand.co.il"
_COIL_DOMAIN_RE = re.compile(
    r'(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.co\.il)\b',
    re.IGNORECASE,
)


def _extract_coil_from_snippet(snippet: str) -> Optional[str]:
    """
    Try to extract a .co.il domain from a Serper snippet.
    Used when the primary result URL is .myshopify.com but the snippet
    mentions the store's custom Israeli domain.
    """
    match = _COIL_DOMAIN_RE.search(snippet)
    if match:
        return normalize_domain(match.group(1))
    return None


# ---------------------------------------------------------------------------
# ShopifyFootprintAgent
# ---------------------------------------------------------------------------

class ShopifyFootprintAgent(SocialFootprintAgent):
    """
    Technology-fingerprint discovery agent for Israeli e-commerce stores.

    Queries Serper for pages that contain Shopify/WooCommerce/Wix platform
    signatures combined with Hebrew fashion/leather vocabulary. Surfaces
    stores that are invisible to keyword-based SEO search.

    Two domain extraction modes:
      1. .co.il result   → standard normalize_domain(), existing pipeline
      2. .myshopify.com  → attempt to extract .co.il from snippet; fall
                           back to myshopify domain if not found
    """

    async def build_queries(self) -> list[str]:
        """Return the full set of technology fingerprint queries."""
        return list(_SHOPIFY_QUERIES)

    async def parse_response(
        self,
        raw_response: dict,
        query: str,
    ) -> list[AgentResult]:
        """
        Parse Serper organic results with special handling for myshopify.com.

        For .myshopify.com results: attempts to resolve the custom .co.il
        domain from the snippet text before falling back to the myshopify
        subdomain. This improves deduplication when the same store appears
        via both Serper paths.
        """
        results: list[AgentResult] = []
        organic = raw_response.get("organic") or []

        for item in organic:
            raw_url = item.get("link", "")
            snippet = item.get("snippet", "")
            title   = item.get("title", "")

            if not raw_url:
                continue

            # Resolve domain — with myshopify custom-domain upgrade
            raw_domain = normalize_domain(raw_url)
            if not raw_domain:
                continue

            if raw_domain.endswith(".myshopify.com"):
                # Attempt to find the .co.il custom domain in the snippet
                custom = _extract_coil_from_snippet(snippet)
                domain = custom if custom else raw_domain
            else:
                domain = raw_domain

            # Layer 1 — aggregator blocklist
            if is_aggregator_domain(domain):
                continue

            phones = extract_whatsapp_numbers(snippet)

            results.append(AgentResult(
                entity_name= title or domain,
                domain=      domain,
                whatsapp=    select_best_phone(phones),
                raw_text=    snippet,
                source_url=  raw_url,
                vector=      "V1_SHOPIFY_FINGERPRINT",
            ))

        return results
