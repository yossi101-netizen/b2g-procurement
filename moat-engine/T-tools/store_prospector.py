"""
store_prospector.py -- High-Moat Candidate Qualifier + Screener Front Door
moat-engine (ABC-TOM, T-tools). Demand-only.

WHAT THIS IS
------------
A funnel, not a firehose. It takes a stream of candidate Shopify domains
(from any discovery surface) and does the expensive, high-judgement work of
SEPARATING high-moat artisan/DTC makers from the dropshipper/print-on-demand
noise that dominates any naive Shopify harvest — BEFORE a single domain
reaches the inventory screener or targets.json.

It fetches each candidate ONCE through GuardedFetcher and derives TWO verdicts
from the same payload (no double network spend):

  1. MOAT verdict        (this file): ARTISAN | PREMIUM_GENERIC | LOW_MOAT
                                      | DROPSHIP | THIN | NOT_SHOPIFY
  2. INVENTORY verdict   (reuses inventory_screener._classify_response):
                                      EXPOSES_QTY | HIDES_QTY | NOT_SHOPIFY

Survivors (ARTISAN / PREMIUM_GENERIC) are piped straight into the screener's
classifier and written to an output file ready to paste into targets.json.

WHY DISCOVERY ITSELF IS NOT FULLY AUTOMATED HERE
------------------------------------------------
Clean cross-store discovery of NEW premium domains has no free, ToS-safe
primitive: web-scale footprint dorking optimises *recall* (find every Shopify
store) when our thesis needs *precision* (a handful of bona-fide makers), and
its raw yield is ~95% dropshippers — exactly the population a moat thesis must
reject. So discovery is left pluggable (a curated list, inline domains, or an
operator-supplied search provider), and the genuine engineering value — the
95%-rejection filter — is automated here, where it belongs.

The AIR-GAPPED scoring core (_extract_features / _classify_moat) touches no
network and is fully unit-tested. Only the per-candidate fetch is networked,
and it goes through GuardedFetcher's killswitch + budget + throttle + cache.

RUN COMMANDS
------------
    python T-tools/store_prospector.py --self-test
    python T-tools/store_prospector.py --material leather knkg.com vonbaer.com
    python T-tools/store_prospector.py --material wood --file candidates.txt
    python T-tools/store_prospector.py --material leather --file in.txt --out survivors.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from safe_loop import (
    BudgetExceeded,
    GuardedFetcher,
    KillSwitchEngaged,
    RateLimited,
    default_config,
    default_state_dir,
)
from inventory_screener import _classify_response as _screen_inventory  # reuse, same payload


# ---------------------------------------------------------------------------
# 0. MOAT VOCABULARY  (the discriminators that separate makers from dropshippers)
# ---------------------------------------------------------------------------

# Material-coherence vocabulary, keyed by --material.
_MATERIAL_TERMS: dict[str, set[str]] = {
    "leather": {
        "leather", "full-grain", "full grain", "vegetable-tanned", "veg-tan",
        "veg tan", "cowhide", "bridle", "latigo", "horween", "tannery",
        "hand-stitched", "hand stitched", "saddle",
    },
    "wood": {
        "wood", "walnut", "oak", "maple", "ash", "solid wood", "kiln-dried",
        "kiln dried", "hardwood", "timber", "joinery", "dovetail", "live edge",
        "live-edge",
    },
    "generic": set(),  # coherence neutral when material is unknown
}

# Cross-material premium / craft language (positive moat signal).
_CRAFT_TERMS = {
    "handmade", "hand-made", "handcrafted", "hand-crafted", "artisan",
    "heirloom", "made to order", "made-to-order", "small batch",
    "small-batch", "lifetime warranty", "lifetime guarantee",
}

# Dropship import apps — near-automatic reject (the storefront is a reseller).
_DROPSHIP_APPS = {
    "dsers", "oberlo", "cjdropshipping", "cj dropshipping", "zendrop",
    "spocket", "dropified", "aliexpress", "importify", "eprolo", "autods",
    "sup dropshipping",
}

# Print-on-demand apps — a strong tell against a physical-material moat.
_POD_APPS = {"printful", "printify", "gooten", "gelato"}

# Premium retention/review/subscription stack — positive moat signal.
_PREMIUM_APPS = {
    "klaviyo", "yotpo", "recharge", "rebuy", "gorgias", "okendo",
    "judge.me", "loopreturns", "loop returns", "shopify-plus", "shopifyplus",
}

_SHOPIFY_MARKERS = {"cdn.shopify.com", "myshopify.com", "shopifycloud", "shopify"}


# ---------------------------------------------------------------------------
# 1. NETWORK FETCH LAYER  (the only network touch; goes through GuardedFetcher)
# ---------------------------------------------------------------------------

def make_products_fetch_fn(domain: str) -> Callable[[dict], Any]:
    def _fetch(params: dict) -> Any:
        url = f"https://{domain}/products.json?limit={params.get('limit', 250)}&page={params.get('page', 1)}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "moat-engine/1.0 demand-research"}, method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RateLimited(f"{domain} 429",
                                  retry_after=float(exc.headers.get("Retry-After", 60))) from exc
            # 401/403/404 etc. → not a usable Shopify products endpoint
            return {"_http_error": exc.code}
        except Exception as exc:
            return {"_net_error": str(exc)}
    return _fetch


def make_html_fetch_fn(domain: str) -> Callable[[dict], Any]:
    def _fetch(params: dict) -> Any:
        url = f"https://{domain}/"
        req = urllib.request.Request(
            url, headers={"User-Agent": "moat-engine/1.0 demand-research"}, method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read(200_000)  # head + early body carry the app fingerprints
                return raw.decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RateLimited(f"{domain} 429 (html)",
                                  retry_after=float(exc.headers.get("Retry-After", 60))) from exc
            return ""
        except Exception:
            return ""
    return _fetch


# ---------------------------------------------------------------------------
# 2. FEATURE EXTRACTION  (pure — no network, fully testable)
# ---------------------------------------------------------------------------

def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _hits(haystack: str, terms: set[str]) -> list[str]:
    return sorted(t for t in terms if t in haystack)


def _extract_features(products_payload: dict, html: str, material: str) -> dict:
    """
    Derive moat discriminators from an already-fetched /products.json payload
    and storefront HTML. Pure function: no I/O.
    """
    html_l = (html or "").lower()
    products = products_payload.get("products") if isinstance(products_payload, dict) else None
    shopify = any(m in html_l for m in _SHOPIFY_MARKERS) or isinstance(products, list)

    if not isinstance(products, list):
        return {
            "shopify": shopify, "n_products": 0, "n_variants": 0,
            "median_price": 0.0, "min_price": 0.0,
            "vendor_count": 0, "category_coherence": 0.0,
            "material_language_hits": 0, "psych_pricing_ratio": 0.0,
            "dropship_app_hits": [], "pod_app_hits": [], "premium_app_hits": [],
        }

    material_terms = _MATERIAL_TERMS.get(material, set())
    prices: list[float] = []
    vendors: set[str] = set()
    coherent = 0
    craft_terms_seen: set[str] = set()
    material_terms_seen: set[str] = set()
    psych = 0
    n_priced = 0

    for prod in products:
        vendors.add((prod.get("vendor") or "").strip().lower())

        blob = " ".join([
            str(prod.get("title", "")),
            str(prod.get("product_type", "")),
            " ".join(prod.get("tags", []) if isinstance(prod.get("tags"), list)
                     else [str(prod.get("tags", ""))]),
            str(prod.get("body_html", "")),
        ]).lower()

        if material_terms and any(t in blob for t in material_terms):
            coherent += 1
        material_terms_seen |= {t for t in material_terms if t in blob}
        craft_terms_seen   |= {t for t in _CRAFT_TERMS if t in blob}

        for v in prod.get("variants", []):
            try:
                p = float(v.get("price") or 0)
            except (ValueError, TypeError):
                p = 0.0
            if p > 0:
                prices.append(p)
                n_priced += 1
                cents = round((p - int(p)) * 100)
                if cents in (99, 95):
                    psych += 1

    n_products = len(products)
    coherence = (coherent / n_products) if n_products else 0.0
    # When material is "generic" we have no coherence signal — treat as neutral 0.5.
    if not material_terms:
        coherence = 0.5

    return {
        "shopify":                shopify,
        "n_products":             n_products,
        "n_variants":             n_priced,
        "median_price":           round(_median(prices), 2),
        "min_price":              round(min(prices), 2) if prices else 0.0,
        "vendor_count":           len({v for v in vendors if v}),
        "category_coherence":     round(coherence, 3),
        "material_language_hits": len(material_terms_seen) + len(craft_terms_seen),
        "psych_pricing_ratio":    round(psych / n_priced, 3) if n_priced else 0.0,
        "dropship_app_hits":      _hits(html_l, _DROPSHIP_APPS),
        "pod_app_hits":           _hits(html_l, _POD_APPS),
        "premium_app_hits":       _hits(html_l, _PREMIUM_APPS),
    }


# ---------------------------------------------------------------------------
# 3. MOAT CLASSIFIER  (pure — the actual engineering value-add)
# ---------------------------------------------------------------------------

def _classify_moat(f: dict, min_price: float) -> tuple[str, int, list[str]]:
    """
    Return (moat_class, score 0..100, reasons).

    Hard gates first (dropship apps, not-shopify, thin catalog), then a
    weighted score that pushes bona-fide makers up and resellers down.
    """
    if not f["shopify"] and f["n_products"] == 0:
        return ("NOT_SHOPIFY", 0, ["no /products.json and no Shopify signature"])

    if f["n_products"] < 3:
        return ("THIN", 0, [f"only {f['n_products']} product(s) — too few to judge moat"])

    reasons: list[str] = []
    score = 50

    if f["dropship_app_hits"]:
        score -= 45
        reasons.append("dropship app(s): " + ", ".join(f["dropship_app_hits"]))
    if f["pod_app_hits"]:
        score -= 20
        reasons.append("print-on-demand: " + ", ".join(f["pod_app_hits"]))

    if f["category_coherence"] >= 0.6:
        score += 15
        reasons.append(f"catalog {int(f['category_coherence']*100)}% on-material (focused maker)")
    elif f["category_coherence"] < 0.25:
        score -= 20
        reasons.append(f"catalog only {int(f['category_coherence']*100)}% on-material (sprawl)")

    if f["material_language_hits"] >= 2:
        score += 15
        reasons.append(f"{f['material_language_hits']} premium-material/craft term(s)")

    if f["median_price"] >= min_price:
        score += 10
        reasons.append(f"median ${f['median_price']:.0f} ≥ ${min_price:.0f} floor")
    else:
        score -= 20
        reasons.append(f"median ${f['median_price']:.0f} < ${min_price:.0f} floor (cheap goods)")

    if f["psych_pricing_ratio"] >= 0.5:
        score -= 15
        reasons.append(f"{int(f['psych_pricing_ratio']*100)}% prices end .99/.95 (mass-retail pricing)")

    if f["premium_app_hits"]:
        score += 10
        reasons.append("premium stack: " + ", ".join(f["premium_app_hits"]))

    if f["n_products"] > 400:
        score -= 15
        reasons.append(f"{f['n_products']} products — aggregator-scale catalog")

    score = max(0, min(100, score))

    if f["dropship_app_hits"]:
        moat_class = "DROPSHIP"
    elif score >= 70 and f["category_coherence"] >= 0.5:
        moat_class = "ARTISAN"
    elif score >= 50:
        moat_class = "PREMIUM_GENERIC"
    else:
        moat_class = "LOW_MOAT"

    return (moat_class, score, reasons)


_SURVIVOR_CLASSES = {"ARTISAN", "PREMIUM_GENERIC"}


# ---------------------------------------------------------------------------
# 4. PROSPECT ONE DOMAIN  (fetch once → moat verdict + inventory verdict)
# ---------------------------------------------------------------------------

def prospect_domain(
    domain:    str,
    material:  str,
    min_price: float,
    gf:        GuardedFetcher,
) -> dict:
    domain = domain.strip().lower()

    products_payload = gf.fetch(
        provider="shopify",
        endpoint=f"{domain}/products.json",
        params={"path": "/products.json", "page": 1, "limit": 250},
        fetch_fn=make_products_fetch_fn(domain),
        ttl=3 * 24 * 3600, cost=0.0,
    )

    # Short-circuit hard failures without spending a second call.
    if not isinstance(products_payload, dict) or "_http_error" in products_payload \
            or "_net_error" in products_payload or "products" not in products_payload:
        return {
            "domain": domain, "moat_class": "NOT_SHOPIFY", "moat_score": 0,
            "inventory": "NOT_SHOPIFY", "price_band": "—",
            "reasons": ["/products.json not served (locked, 404, or not Shopify)"],
            "survivor": False,
        }

    html = gf.fetch(
        provider="shopify",
        endpoint=f"{domain}/",
        params={"path": "/"},
        fetch_fn=make_html_fetch_fn(domain),
        ttl=3 * 24 * 3600, cost=0.0,
    )

    features = _extract_features(products_payload, html, material)
    moat_class, score, reasons = _classify_moat(features, min_price)

    inv_status, inv_prices, _qtys = _screen_inventory(products_payload)
    band = _band_from_prices(inv_prices)

    return {
        "domain":     domain,
        "moat_class": moat_class,
        "moat_score": score,
        "inventory":  inv_status,
        "price_band": band,
        "reasons":    reasons,
        "survivor":   moat_class in _SURVIVOR_CLASSES,
    }


def _band_from_prices(prices: list[float]) -> str:
    if not prices:
        return "—"
    avg = sum(prices) / len(prices)
    if avg >= 500:
        return "HIGH_TICKET"
    if avg >= 100:
        return "MID"
    return "LOW"


# ---------------------------------------------------------------------------
# 5. RUN THE FUNNEL OVER A LIST
# ---------------------------------------------------------------------------

def prospect(
    domains:   list[str],
    material:  str,
    min_price: float,
    gf:        GuardedFetcher,
) -> list[dict]:
    results: list[dict] = []
    for d in domains:
        d = d.strip().lower()
        if not d:
            continue
        print(f"  → {d}", file=sys.stderr)
        try:
            results.append(prospect_domain(d, material, min_price, gf))
        except (KillSwitchEngaged, BudgetExceeded):
            raise
        except Exception as exc:
            results.append({
                "domain": d, "moat_class": "ERROR", "moat_score": 0,
                "inventory": "—", "price_band": "—",
                "reasons": [str(exc)], "survivor": False,
            })
    return results


# ---------------------------------------------------------------------------
# 6. REPORT
# ---------------------------------------------------------------------------

_RANK = {"ARTISAN": 0, "PREMIUM_GENERIC": 1, "LOW_MOAT": 2,
         "THIN": 3, "DROPSHIP": 4, "NOT_SHOPIFY": 5, "ERROR": 6}


def _print_report(results: list[dict]) -> None:
    ordered = sorted(results, key=lambda r: (_RANK.get(r["moat_class"], 9), -r["moat_score"]))

    cls_w, dom_w, sc_w, inv_w, band_w = 16, 26, 6, 12, 12
    header = (f"{'Moat':<{cls_w}}{'Domain':<{dom_w}}{'Score':<{sc_w}}"
              f"{'Inventory':<{inv_w}}{'Band':<{band_w}}")
    print()
    print(header)
    print("─" * len(header))
    for r in ordered:
        print(f"{r['moat_class']:<{cls_w}}{r['domain']:<{dom_w}}"
              f"{r['moat_score']:<{sc_w}}{r['inventory']:<{inv_w}}{r['price_band']:<{band_w}}")
        for reason in r["reasons"][:3]:
            print(f"      · {reason}")

    survivors = [r for r in ordered if r["survivor"]]
    rejected  = [r for r in ordered if not r["survivor"]]
    print()
    print("Summary:")
    print(f"  SURVIVORS (ARTISAN/PREMIUM_GENERIC): {len(survivors)}")
    exposing = [r for r in survivors if r["inventory"] == "EXPOSES_QTY"]
    if exposing:
        print(f"    of which EXPOSES_QTY (S1-ready): {len(exposing)} → "
              + ", ".join(r["domain"] for r in exposing))
    print(f"  REJECTED (dropship/thin/low-moat/not-shopify): {len(rejected)}")
    print()


# ---------------------------------------------------------------------------
# 7. OPTIONAL DISCOVERY SEAM (documented; intentionally not auto-wired)
# ---------------------------------------------------------------------------

def discover_via_search(footprint: str, gf: GuardedFetcher) -> list[str]:
    """
    Seam for an operator-supplied search provider (e.g. a metered SERP API
    registered as a safe_loop provider). Deliberately NOT wired to the CLI:
    raw footprint dorking yields ~95% dropshippers and must never feed
    targets.json unfiltered. If you wire a provider here, every domain it
    returns must still pass through prospect() before use.
    """
    raise NotImplementedError(
        "No search provider configured. Supply candidate domains via "
        "--file / positional args, then prospect() filters them. "
        "To automate discovery, register a SERP provider in safe_loop.default_config() "
        "and route it through GuardedFetcher here."
    )


# ---------------------------------------------------------------------------
# 8. SELF-TEST  (offline, deterministic — scoring core only)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    def _prod(title, price, vendor="Brand", ptype="", tags=None, body=""):
        return {
            "title": title, "vendor": vendor, "product_type": ptype,
            "tags": tags or [], "body_html": body,
            "variants": [{"price": f"{price:.2f}"}],
        }

    # ── ARTISAN leather maker: coherent, premium-priced, premium stack ──────
    artisan_products = {"products": [
        _prod("Full-Grain Leather Duffel", 245, ptype="Bags",
              tags=["leather", "full-grain"], body="vegetable-tanned, hand-stitched"),
        _prod("Leather Weekender", 320, tags=["leather"], body="full grain cowhide"),
        _prod("Bridle Leather Holdall", 280, tags=["bridle"], body="heirloom, handmade"),
        _prod("Leather Dopp Kit", 95, tags=["leather"]),
    ]}
    artisan_html = '<script src="cdn.shopify.com/...klaviyo.js"></script> yotpo reviews recharge'
    f = _extract_features(artisan_products, artisan_html, "leather")
    assert f["category_coherence"] >= 0.6, f
    assert f["material_language_hits"] >= 2, f
    assert "klaviyo" in f["premium_app_hits"], f
    cls, score, _ = _classify_moat(f, min_price=60.0)
    assert cls == "ARTISAN", (cls, score, f)
    assert score >= 70, score

    # ── DROPSHIP store: dropship app present → hard reject regardless of score
    drop_products = {"products": [
        _prod("Mens Leather Wallet RFID", 12.99, vendor="A", tags=["wallet"]),
        _prod("Phone Case Silicone", 9.99, vendor="B", tags=["phone"]),
        _prod("Kitchen Gadget Set", 19.99, vendor="C", tags=["kitchen"]),
        _prod("Fitness Resistance Band", 14.99, vendor="D", tags=["fitness"]),
    ]}
    drop_html = '<script src="dsers.com/app.js"></script> aliexpress import'
    f = _extract_features(drop_products, drop_html, "leather")
    assert "dsers" in f["dropship_app_hits"], f
    assert f["psych_pricing_ratio"] >= 0.5, f
    assert f["category_coherence"] <= 0.25, f
    cls, score, _ = _classify_moat(f, min_price=60.0)
    assert cls == "DROPSHIP", (cls, score)

    # ── THIN catalog: too few products to judge
    thin = {"products": [_prod("Leather Bag", 200, tags=["leather"])]}
    f = _extract_features(thin, "cdn.shopify.com", "leather")
    cls, score, _ = _classify_moat(f, min_price=60.0)
    assert cls == "THIN", (cls, score)

    # ── NOT_SHOPIFY: HTTP error sentinel payload
    f = _extract_features({"_http_error": 404}, "", "leather")
    assert f["n_products"] == 0 and not f["shopify"], f
    cls, score, _ = _classify_moat(f, min_price=60.0)
    assert cls == "NOT_SHOPIFY", (cls, score)

    # ── PREMIUM_GENERIC: real focused maker but no premium stack, modest signals
    pg_products = {"products": [
        _prod("Leather Tote", 140, tags=["leather"]),
        _prod("Leather Belt", 90, tags=["leather"]),
        _prod("Leather Card Holder", 70, tags=["leather"]),
        _prod("Canvas Tote", 60, tags=["canvas"]),
    ]}
    f = _extract_features(pg_products, "cdn.shopify.com store", "leather")
    cls, score, _ = _classify_moat(f, min_price=60.0)
    assert cls in ("PREMIUM_GENERIC", "ARTISAN"), (cls, score, f)
    assert 50 <= score, score

    # ── median + psych helpers
    assert _median([10, 20, 30]) == 20
    assert _median([10, 20]) == 15
    assert _band_from_prices([250.0, 270.0]) == "MID"
    assert _band_from_prices([600.0]) == "HIGH_TICKET"
    assert _band_from_prices([]) == "—"

    # ── generic material → neutral coherence (0.5), still scores on price/apps
    gen = {"products": [
        _prod("Walnut Desk Organizer", 120), _prod("Oak Tray", 95),
        _prod("Maple Coasters", 45), _prod("Ash Stool", 180),
    ]}
    f = _extract_features(gen, "cdn.shopify.com klaviyo", "generic")
    assert f["category_coherence"] == 0.5, f
    cls, score, _ = _classify_moat(f, min_price=80.0)
    assert cls in ("PREMIUM_GENERIC", "ARTISAN", "LOW_MOAT"), (cls, score)

    print("self-test PASSED: feature extraction + moat classifier "
          "(ARTISAN/DROPSHIP/THIN/NOT_SHOPIFY/PREMIUM_GENERIC), "
          "median/band helpers — all hold")


# ---------------------------------------------------------------------------
# 9. CLI
# ---------------------------------------------------------------------------

# Sensible per-material price floors (median below this = mass-market / dropship).
_DEFAULT_FLOOR = {"leather": 60.0, "wood": 80.0, "generic": 40.0}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Qualify candidate Shopify domains by moat + inventory exposure, "
                    "then pipe survivors toward the screener/targets.json."
    )
    ap.add_argument("domains", nargs="*", metavar="DOMAIN",
                    help="candidate domain(s), e.g. knkg.com vonbaer.com")
    ap.add_argument("--material", choices=sorted(_MATERIAL_TERMS.keys()), default="generic",
                    help="material family for coherence scoring (default: generic)")
    ap.add_argument("--file", metavar="FILE", help="text file, one candidate domain per line")
    ap.add_argument("--min-price", type=float, default=None,
                    help="median-price floor in USD (default: per-material)")
    ap.add_argument("--out", metavar="FILE",
                    help="write surviving domains (one per line) to this file")
    ap.add_argument("--run-budget", type=float, default=5.0,
                    help="per-run spend ceiling in USD (default: 5.0)")
    ap.add_argument("--self-test", action="store_true", help="run offline self-test and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    domains: list[str] = list(args.domains)
    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"ERROR: file not found: {args.file}", file=sys.stderr)
            return 1
        domains.extend(l.strip() for l in p.read_text(encoding="utf-8").splitlines()
                       if l.strip() and not l.startswith("#"))

    if not domains:
        ap.print_help()
        return 1

    min_price = args.min_price if args.min_price is not None else _DEFAULT_FLOOR[args.material]

    gf = GuardedFetcher(
        config=default_config(), state_dir=default_state_dir(),
        run_budget_usd=args.run_budget,
    )

    print(f"Prospecting {len(domains)} candidate(s) — material={args.material}, "
          f"price floor=${min_price:.0f}", file=sys.stderr)
    try:
        results = prospect(domains, args.material, min_price, gf)
    except KillSwitchEngaged as exc:
        print(f"\nKILL SWITCH ENGAGED: {exc}", file=sys.stderr)
        return 2
    except BudgetExceeded as exc:
        print(f"\nBUDGET EXCEEDED: {exc}", file=sys.stderr)
        return 3

    _print_report(results)

    if args.out:
        survivors = [r["domain"] for r in results if r["survivor"]]
        Path(args.out).write_text("\n".join(survivors) + ("\n" if survivors else ""),
                                  encoding="utf-8")
        print(f"Wrote {len(survivors)} surviving domain(s) → {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
