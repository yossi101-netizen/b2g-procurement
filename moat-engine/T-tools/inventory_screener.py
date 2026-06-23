"""
inventory_screener.py -- Shopify Inventory Exposure Qualifier
moat-engine (ABC-TOM, T-tools). Demand-only.

PURPOSE
-------
One-shot domain classifier. Before adding a competitor to targets.json,
run it through this screener to determine whether its Shopify store exposes
inventory_quantity. Only EXPOSES_QTY stores can feed Signal S1 (inventory
delta). All stores — regardless of status — can be probed for S2 (stockout
frequency) and S3 (restock cadence).

Uses raw urllib directly (not GuardedFetcher) because this is a one-shot
qualification tool, not a recurring scheduled probe.

OUTPUT STATES
-------------
  EXPOSES_QTY   ≥1 variant has inventory_management=="shopify" with a numeric qty
  HIDES_QTY     /products.json loads but all variants have qty=null
  NOT_SHOPIFY   HTTP error, no products key, or domain unreachable
  LOCKED        Store returned 401 or 403 (password-protected or API-gated)

RUN COMMANDS
------------
    python T-tools/inventory_screener.py --self-test
    python T-tools/inventory_screener.py knkg.com vonbaer.com hardgraft.com
    python T-tools/inventory_screener.py --file candidates.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 1. SINGLE-DOMAIN PROBE  (raw urllib, no GuardedFetcher)
# ---------------------------------------------------------------------------

def _get_products_json(domain: str, timeout: int = 20) -> Optional[dict]:
    """
    Fetch /products.json?limit=5 from domain.
    Returns the parsed JSON dict or None on failure (sets _get_products_json.error).
    """
    url = f"https://{domain}/products.json?limit=5"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "moat-engine/1.0 demand-research"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _get_products_json.last_error = ("HTTP", exc.code)
        return None
    except Exception as exc:
        _get_products_json.last_error = ("NET", str(exc))
        return None


_get_products_json.last_error = ("", "")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. CLASSIFICATION  (testable without network)
# ---------------------------------------------------------------------------

def _classify_response(payload: Optional[dict]) -> tuple[str, list[float], list[int]]:
    """
    Given a parsed /products.json payload (or None), return:
      (status, sample_prices, sample_qtys)

    status is one of: EXPOSES_QTY | HIDES_QTY | NOT_SHOPIFY
    (LOCKED is set upstream from the HTTP error code, not here)

    sample_prices: up to 3 prices from the catalog
    sample_qtys:   inventory_quantity values where management=="shopify" and qty is int
    """
    if payload is None:
        return ("NOT_SHOPIFY", [], [])

    products = payload.get("products")
    if not isinstance(products, list):
        return ("NOT_SHOPIFY", [], [])

    prices:   list[float] = []
    qtys:     list[int]   = []
    has_qty   = False

    for prod in products:
        for v in prod.get("variants", []):
            try:
                p = float(v.get("price") or 0)
                if p > 0 and len(prices) < 3:
                    prices.append(p)
            except (ValueError, TypeError):
                pass

            mgmt = v.get("inventory_management")
            qty  = v.get("inventory_quantity")
            if mgmt == "shopify" and isinstance(qty, int):
                has_qty = True
                if len(qtys) < 5:
                    qtys.append(qty)

    if has_qty:
        return ("EXPOSES_QTY", prices, qtys)

    if products:  # responded with a valid products list but no qty
        return ("HIDES_QTY", prices, [])

    return ("NOT_SHOPIFY", [], [])


def _price_band(prices: list[float]) -> str:
    if not prices:
        return "?"
    avg = sum(prices) / len(prices)
    if avg >= 500:
        return "HIGH_TICKET"
    if avg >= 100:
        return "MID"
    return "LOW"


# ---------------------------------------------------------------------------
# 3. SCREEN A LIST OF DOMAINS
# ---------------------------------------------------------------------------

def screen_domains(
    domains:        list[str],
    sleep_seconds:  float = 1.5,
) -> list[dict]:
    """
    Classify each domain. Returns a list of result dicts.
    """
    results: list[dict] = []
    for domain in domains:
        domain = domain.strip().lower()
        if not domain:
            continue

        payload = _get_products_json(domain)
        err     = _get_products_json.last_error  # type: ignore[attr-defined]
        _get_products_json.last_error = ("", "")  # type: ignore[attr-defined]

        # Locked stores identified by HTTP 401/403
        if payload is None and err[0] == "HTTP" and err[1] in (401, 403):
            results.append({
                "domain":        domain,
                "status":        "LOCKED",
                "prices":        [],
                "price_band":    "?",
                "sample_qtys":   [],
            })
        else:
            status, prices, qtys = _classify_response(payload)
            results.append({
                "domain":      domain,
                "status":      status,
                "prices":      prices,
                "price_band":  _price_band(prices),
                "sample_qtys": qtys,
            })

        if domain != domains[-1]:
            time.sleep(sleep_seconds)

    return results


# ---------------------------------------------------------------------------
# 4. FORMATTED TERMINAL REPORT
# ---------------------------------------------------------------------------

def _print_report(results: list[dict]) -> None:
    col_status  = 13
    col_domain  = 26
    col_prices  = 22
    col_band    = 12

    header = (
        f"{'Status':<{col_status}}"
        f"{'Domain':<{col_domain}}"
        f"{'Prices (sample)':<{col_prices}}"
        f"{'Band':<{col_band}}"
    )
    bar = "─" * len(header)
    print()
    print(header)
    print(bar)

    for r in results:
        status = r["status"]
        domain = r["domain"]

        if r["prices"]:
            price_str = ", ".join(f"${p:.0f}" for p in r["prices"])
        else:
            price_str = "—"

        band = r["price_band"] if r["prices"] else "—"

        suffix = ""
        if status == "EXPOSES_QTY" and r["sample_qtys"]:
            suffix = f"  qty={r['sample_qtys']}"

        print(
            f"{status:<{col_status}}"
            f"{domain:<{col_domain}}"
            f"{price_str:<{col_prices}}"
            f"{band:<{col_band}}"
            f"{suffix}"
        )

    # Summary
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print()
    print("Summary:")
    for status, label in [
        ("EXPOSES_QTY", "→ add to targets.json after moat check"),
        ("HIDES_QTY",   "→ S2/S3 signals only"),
        ("NOT_SHOPIFY", "→ discard"),
        ("LOCKED",      "→ discard or try authenticated endpoint"),
    ]:
        n = counts.get(status, 0)
        print(f"  {status}: {n}  {label}")
    print()


# ---------------------------------------------------------------------------
# 5. SELF-TEST  (no network, deterministic)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    # EXPOSES_QTY: at least one variant with management=="shopify" and int qty
    payload_exposes = {
        "products": [{
            "id": 1, "title": "Wallet",
            "variants": [
                {"price": "89.00", "inventory_management": "shopify",
                 "inventory_quantity": 12, "available": True},
                {"price": "89.00", "inventory_management": None,
                 "inventory_quantity": None, "available": True},
            ]
        }]
    }
    status, prices, qtys = _classify_response(payload_exposes)
    assert status == "EXPOSES_QTY",  status
    assert 89.0 in prices,           prices
    assert qtys   == [12],           qtys

    # HIDES_QTY: all null
    payload_hides = {
        "products": [{
            "id": 2, "title": "Belt",
            "variants": [
                {"price": "165.00", "inventory_management": None,
                 "inventory_quantity": None, "available": True},
                {"price": "190.00", "inventory_management": None,
                 "inventory_quantity": None, "available": True},
            ]
        }]
    }
    status, prices, qtys = _classify_response(payload_hides)
    assert status == "HIDES_QTY", status
    assert qtys   == [],          qtys
    assert len(prices) == 2,      prices

    # NOT_SHOPIFY: None payload
    status, prices, qtys = _classify_response(None)
    assert status == "NOT_SHOPIFY", status
    assert prices == [], prices
    assert qtys   == [], qtys

    # NOT_SHOPIFY: no products key
    status, prices, qtys = _classify_response({"collections": []})
    assert status == "NOT_SHOPIFY", status

    # price_band
    assert _price_band([110.0, 120.0, 130.0]) == "MID"          # avg 120 → MID
    assert _price_band([250.0, 270.0, 260.0]) == "MID"          # avg 260 → MID
    assert _price_band([550.0])               == "HIGH_TICKET"
    assert _price_band([35.0, 25.0])          == "LOW"
    assert _price_band([89.0, 75.0])          == "LOW"           # avg 82 → LOW
    assert _price_band([])                    == "?"

    # Multi-variant prices capped at 3
    payload_many = {
        "products": [{
            "id": 3, "title": "Bag",
            "variants": [
                {"price": "100.00", "inventory_management": "shopify",
                 "inventory_quantity": 5, "available": True},
                {"price": "110.00", "inventory_management": "shopify",
                 "inventory_quantity": 3, "available": True},
                {"price": "120.00", "inventory_management": "shopify",
                 "inventory_quantity": 8, "available": True},
                {"price": "130.00", "inventory_management": "shopify",
                 "inventory_quantity": 2, "available": True},
            ]
        }]
    }
    status, prices, qtys = _classify_response(payload_many)
    assert status      == "EXPOSES_QTY",  status
    assert len(prices) == 3,              prices   # capped at 3
    assert len(qtys)   == 4,              qtys     # capped at 5

    print("self-test PASSED: EXPOSES_QTY, HIDES_QTY, NOT_SHOPIFY, "
          "price_band — all hold")


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Classify Shopify competitor domains by inventory exposure."
    )
    ap.add_argument("domains", nargs="*", metavar="DOMAIN",
                    help="bare domain(s) to probe (e.g. knkg.com vonbaer.com)")
    ap.add_argument("--file", metavar="FILE",
                    help="text file with one domain per line")
    ap.add_argument("--sleep", type=float, default=1.5, metavar="SEC",
                    help="seconds between probes (default: 1.5)")
    ap.add_argument("--self-test", action="store_true",
                    help="run offline self-test and exit")
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

    results = screen_domains(domains, sleep_seconds=args.sleep)
    _print_report(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
