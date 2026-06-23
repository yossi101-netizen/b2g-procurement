"""
KritiKaal Leads Hunter — Lateral Industry Agent
File: T-tools/lateral_industry_agent.py
Governed by: B-brain/01-tech-stack.md §2 (V1 Serper vector)
Strategy: C-core/02-target-audience.md v2.0 — Volume Buyer Targeting

Purpose:
  Discover Israeli B2B volume buyers across five industry verticals that are
  completely invisible to the core leather-keyword search. Each vertical is a
  distinct "query pack" — a curated list of Hebrew/English Serper queries
  targeting a specific buyer persona.

The Five Packs:
  1. CORPORATE_GIFTING   — Ad agencies and gift suppliers that order branded
                           leather goods in bulk for corporate clients.
  2. FOOTWEAR_INDUSTRY   — Israeli shoe manufacturers, importers, and wholesalers.
                           Footwear is one of the largest leather-consuming industries:
                           uppers, insoles, and heels all require processed hide.
                           Replaces RELIGIOUS_CEREMONIAL (halachic incompatibility —
                           tefillin/STa"M leather must be kosher-certified).
  3. INDUSTRIAL_SAFETY   — Workwear distributors importing leather safety
                           gloves, aprons, and welding gear.
  4. COMPETITOR_REVERSE  — Israeli importers who already reference Italian or
                           Turkish leather sourcing on their websites. These are
                           pre-qualified volume buyers currently paying Western
                           manufacturing prices — KritiKaal's ideal target.
  5. PURCHASE_INTENT     — Companies that publicly express a need for a
                           manufacturing partner or supplier on their own site.
                           Queries target company homepages and trade contexts —
                           NOT job board portals, which return job pages (not
                           company pages) and are blocked by the aggregator list.

Vector: V1_LATERAL (Serper web search, pack-specific queries)
All packs restricted to site:.co.il — job board domains are in the
aggregator blocklist and will be filtered even if they slip through.
"""

from dotenv import load_dotenv
load_dotenv()

from scrapers import SocialFootprintAgent

# ---------------------------------------------------------------------------
# Query Packs — the core of the lateral strategy
# ---------------------------------------------------------------------------

QUERY_PACKS: dict[str, list[str]] = {

    # ── Pack 1: Corporate Gifting ────────────────────────────────────────────
    # Companies that order branded leather goods for corporate gift programs.
    # Vocabulary: "מוצרי פרסום" (promotional products), "מתנות עסקיות"
    # (business gifts), "ספק מתנות" (gift supplier).
    "corporate_gifting": [
        '"מוצרי פרסום" עור site:.co.il',
        '"מתנות עסקיות" עור site:.co.il',
        '"ספק מתנות" "עור" site:.co.il',
        '"מתנות לחברות" "עור" site:.co.il',
        '"מתנות קורפורייט" "עור" OR "ארנקים" OR "תיקים" site:.co.il',
        '"מתנות סוף שנה" "עור" ישראל site:.co.il',
        '"מיתוג" "מוצרי עור" site:.co.il',
    ],

    # ── Pack 2: Footwear Industry ─────────────────────────────────────────────
    # Israeli shoe manufacturers, importers, and wholesalers are among the
    # largest B2B consumers of processed leather (uppers, linings, insoles).
    # The Israeli footwear market sources heavily from Italy, Turkey, and
    # Portugal — these are established volume importers KritiKaal can replace.
    #
    # NOTE: The former "religious_ceremonial" pack (Tefillin / STa"M) has been
    # permanently removed. Halachic items require kosher-certified leather from
    # ritually slaughtered animals. Our supply chain uses commercial leather →
    # material incompatibility. These leads are now hard-disqualified at Tier 1.
    "footwear_industry": [
        '"יבואן נעלים" "עור" ישראל site:.co.il',
        '"מפעל נעלים" "עור" ישראל site:.co.il',
        '"ייצור נעלים" "עור" OR "חומרי גלם" ישראל site:.co.il',
        '"נעלי עור" יצרן OR יבואן OR סיטונאי site:.co.il',
        '"נעלי עבודה" "עור" יבואן OR מפיץ ישראל site:.co.il',
        '"סיטונאי נעלים" ישראל site:.co.il',
        '"נעל אורטופדית" "עור" ישראל site:.co.il',
        '"נעלי עור איטלקיות" OR "נעלי עור טורקיות" ישראל site:.co.il',
    ],

    # ── Pack 3: Industrial / Safety ──────────────────────────────────────────
    # Workwear importers: leather safety gloves, welding aprons, boot
    # distributors. These are repeat, high-MOQ buyers in a market KritiKaal
    # can supply at scale.
    "industrial_safety": [
        '"כפפות עבודה" "עור" יבואן OR סיטונאי site:.co.il',
        '"סינרי עור" תעשייה ישראל site:.co.il',
        '"ציוד מגן" "עור" יבואן ישראל site:.co.il',
        '"כפפות עור" סיטונאי ישראל site:.co.il',
        '"ביגוד מגן" עור יבואן site:.co.il',
        'יבואן "ציוד בטיחות" "עור" ישראל site:.co.il',
    ],

    # ── Pack 4: Competitor Reverse Lookup ────────────────────────────────────
    # Israeli companies that already reference Italian or Turkish leather
    # origin on their own websites. These are CONFIRMED volume importers
    # currently paying Western manufacturing prices. The strategy: find them
    # by the trail their sourcing language leaves in Google's index.
    # Also includes known luxury brand authorized distributors — they hold
    # local inventory and have established import operations.
    "competitor_reverse": [
        '"עור איטלקי" יבואן בלעדי ישראל site:.co.il',
        '"עור טורקי" יבואן OR מפיץ ישראל site:.co.il',
        '"מיוצר באיטליה" עור ישראל site:.co.il',
        '"מיוצר בטורקיה" עור ישראל site:.co.il',
        '"full grain leather" יבואן ישראל site:.co.il',
        '"vegetable tanned" leather ישראל site:.co.il',
        '"Samsonite" מפיץ בלעדי ישראל site:.co.il',
        '"Tumi" נציג רשמי ישראל site:.co.il',
        '"Kipling" ישראל מפיץ site:.co.il',
        '"Ecco" נציג ישראל site:.co.il',
    ],

    # ── Pack 5: Purchase / Sourcing Intent ──────────────────────────────────
    # Companies that publicly express a need for a manufacturing partner,
    # supplier, or raw-material source. These are active buyers announcing
    # their purchasing intent on their own website or in trade contexts —
    # not job-board pages. Queries target employer homepages and trade press,
    # NOT job listing portals (which return job pages, not company pages).
    "purchase_intent": [
        '"מחפשים ספק" "עור" OR "תיקים" ישראל site:.co.il',
        '"מחפשים יצרן" "עור" OR "אביזרים" ישראל site:.co.il',
        '"שותף ייצור" "עור" ישראל site:.co.il',
        '"ספק עור" "ישראל" site:.co.il',
        '"חומרי גלם" "עור" יבואן ישראל site:.co.il',
        '"נמצאים בחיפוש" "ספק" "עור" ישראל site:.co.il',
        '"קולקציה חדשה" "עור" ישראל site:.co.il',
        '"הרחבת קולקציה" "עור" OR "תיקים" site:.co.il',
    ],
}


# ---------------------------------------------------------------------------
# LateralIndustryAgent
# ---------------------------------------------------------------------------

class LateralIndustryAgent(SocialFootprintAgent):
    """
    Multi-pack discovery agent for lateral B2B buyer personas.

    Runs all five query packs in a single Serper sweep. Results are tagged
    with vector='V1_LATERAL' so the run log can distinguish them from core
    leather queries.

    Inherits all HTTP, anti-bot, retry, and parse_response() behaviour from
    SocialFootprintAgent. Only build_queries() is overridden.
    """

    # Job posting and competitor reverse queries intentionally span beyond
    # .co.il — LinkedIn Jobs and Italian supplier sites are off-.co.il by design.
    # The existing is_aggregator_domain() blocklist filters noise at parse time.

    async def build_queries(self) -> list[str]:
        """
        Return all queries from all five packs as a flat list.
        Approximately 39 queries × up to 10 Serper results = ~390 raw candidates.
        """
        queries: list[str] = []
        for pack_queries in QUERY_PACKS.values():
            queries.extend(pack_queries)
        return queries

    def pack_for_query(self, query: str) -> str:
        """Return the pack name for a given query string (for logging/analysis)."""
        for pack_name, pack_queries in QUERY_PACKS.items():
            if query in pack_queries:
                return pack_name
        return "unknown"
