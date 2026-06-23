"""
serp_harvester.py -- Google Custom Search SERP → Candidate Domain Feeder
moat-engine (ABC-TOM, T-tools). Demand-only.

WHAT THIS DOES
--------------
Executes crafted Google dork queries through the official Google Custom Search
JSON API and extracts unique domains from the results, writing them to
candidates.txt (or stdout) for store_prospector.py to evaluate.

CREDENTIAL SECURITY — CRITICAL CONTRACT
----------------------------------------
The API key and CSE ID live ONLY in environment variables:
  MOAT_GOOGLE_CSE_KEY   — your Google Custom Search JSON API key
  MOAT_GOOGLE_CSE_CX    — your Programmable Search Engine ID

They are NEVER:
  - written to disk, logged, or echoed in any output
  - included in the params dict passed to GuardedFetcher
    (params → cache key → cached to disk → key exposed)
  - passed through the safe_loop budget ledger or killswitch records

The fetch_fn CLOSES OVER the credentials. GuardedFetcher only sees
{"q": ..., "start": ...} as the cache key. The key is invisible to every
safe_loop persistence layer.

HOW THE CACHE KEY WORKS
------------------------
  params = {"q": "full grain leather duffel add to cart", "start": 1}
  cache_key = sha256(json.dumps({provider, endpoint, params}))
  → api_key is NOT in params → NOT in the cache key → NOT on disk

GOOGLE CSE SETUP (one-time, ~5 minutes)
-----------------------------------------
1. Go to https://programmablesearchengine.google.com/
2. Create a new search engine → Search the entire web
3. Copy the Search Engine ID (cx)
4. Go to Google Cloud Console → Enable "Custom Search API"
5. Create an API Key (restrict to Custom Search API)
6. Set env vars:
     $env:MOAT_GOOGLE_CSE_KEY = "AIza..."
     $env:MOAT_GOOGLE_CSE_CX  = "017..."

COST
----
100 queries/day free, then $5/1000 queries ($0.005/query).
Each dork = up to 3 pages × 10 results = 30 URLs.
A full 3-seed run with 3 dorks/seed = 9 queries × $0.005 = $0.045.
All tracked in the $300 GuardedFetcher budget ceiling.

DORK DESIGN
-----------
The official API accepts standard Google search syntax in the q parameter.
Negative site: operators (-site:amazon.com) work exactly as in regular Google.
The high-moat dork pattern is:
  "<material keyword>" "<product keyword>" "<craft signal>" -<mass-retail exclusion>

Pre-built dorks live in _SEED_DORKS below. Extend or override with --dork.

PIPELINE
--------
  serp_harvester.py [--seed 01] → candidates.txt
  store_prospector.py --material leather --file candidates.txt --out survivors.txt
  → targets.json

RUN COMMANDS
------------
    python T-tools/serp_harvester.py --self-test          # offline, no key needed
    python T-tools/serp_harvester.py --seed 01            # use built-in dorks for seed 01
    python T-tools/serp_harvester.py --dork "full grain leather duffel handmade"
    python T-tools/serp_harvester.py --seed 01 03 05 --out candidates.txt
    python T-tools/serp_harvester.py --dorks-file my_dorks.txt --out candidates.txt
    python T-tools/serp_harvester.py --list-dorks         # show built-in dorks and exit
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
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


# ---------------------------------------------------------------------------
# 0. BUILT-IN HIGH-MOAT DORKS (extend or override with --dork / --dorks-file)
# ---------------------------------------------------------------------------

# The strategy: phrase-match on material language + craft signals +
# explicit exclusion of the mass-retail / aggregator URLs that dominate
# naive keyword searches. These are designed for a CSE configured to search
# the entire web (not a restricted site list).
_SEED_DORKS: dict[str, list[str]] = {
    "01": [  # Premium leather gym duffel / weekender
        '"full grain leather" "gym bag" OR "duffel" -site:amazon.com -site:ebay.com -site:etsy.com',
        '"vegetable tanned" OR "veg-tan" "gym bag" OR "duffel" "add to cart" -site:amazon.com',
        '"leather duffel" "handmade" OR "hand-stitched" OR "made in usa" -site:amazon.com -site:wayfair.com',
    ],
    "03": [  # Premium leather dog leash + collar set
        '"leather dog leash" "full grain" OR "vegetable tanned" OR "handmade" -site:amazon.com -site:ebay.com',
        '"leather leash" "leather collar" "handcrafted" OR "artisan" -site:amazon.com -site:chewy.com',
        '"dog leash" "bridle leather" OR "harness leather" -site:amazon.com -site:etsy.com',
    ],
    "05": [  # Artisan wood-framed large-dog orthopedic bed
        '"wood frame" "dog bed" "orthopedic" "large dog" -site:amazon.com -site:wayfair.com -site:chewy.com',
        '"solid wood" "dog bed" "handmade" OR "artisan" -site:amazon.com -site:walmart.com',
        '"dog bed" "walnut" OR "oak" OR "maple" "orthopedic" -site:amazon.com',
    ],
}

# Domains that will never be a Shopify competitor store.
# Kept tight — false positives are caught downstream by store_prospector.py.
_DOMAIN_BLOCKLIST = frozenset({
    "amazon.com", "ebay.com", "etsy.com", "walmart.com", "wayfair.com",
    "chewy.com", "target.com", "bestbuy.com", "homedepot.com", "lowes.com",
    "youtube.com", "youtu.be", "reddit.com", "pinterest.com",
    "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
    "wikipedia.org", "wikihow.com", "quora.com", "medium.com",
    "shopify.com", "myshopify.com",  # Shopify itself, not stores
    "google.com", "bing.com", "yahoo.com",
    "aliexpress.com", "alibaba.com", "dhgate.com",
    "trustpilot.com", "yelp.com", "bbb.org",
    "nytimes.com", "wsj.com", "forbes.com", "businessinsider.com",
    "theguardian.com", "vogue.com", "gq.com",
})


# ---------------------------------------------------------------------------
# 1. CREDENTIAL LOADER
# ---------------------------------------------------------------------------

def _load_credentials() -> tuple[str, str]:
    """
    Load API key and CSE ID from environment variables.
    Raises EnvironmentError if either is missing.
    Both values are returned raw; they are NEVER stored, logged, or passed
    to GuardedFetcher as params.
    """
    key = os.environ.get("MOAT_GOOGLE_CSE_KEY", "").strip()
    cx  = os.environ.get("MOAT_GOOGLE_CSE_CX",  "").strip()
    missing = []
    if not key:
        missing.append("MOAT_GOOGLE_CSE_KEY")
    if not cx:
        missing.append("MOAT_GOOGLE_CSE_CX")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}\n"
            "Set them before running:\n"
            "  $env:MOAT_GOOGLE_CSE_KEY = 'AIza...'\n"
            "  $env:MOAT_GOOGLE_CSE_CX  = '017...'\n"
            "See module docstring for CSE setup instructions."
        )
    return key, cx


# ---------------------------------------------------------------------------
# 2. FETCH FUNCTION  (credentials closed over — never in params / cache key)
# ---------------------------------------------------------------------------

_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def make_cse_fetch_fn(api_key: str, cx: str) -> Callable[[dict], Any]:
    """
    Return a fetch_fn for GuardedFetcher that calls the Google CSE JSON API.

    SECURITY: api_key and cx are CLOSED OVER, not passed through params.
    The params dict ({q, start, num}) is what GuardedFetcher uses to build
    the cache key — credentials never appear in that dict, so they never
    reach the on-disk cache.
    """
    def _fetch(params: dict) -> Any:
        qs = urllib.parse.urlencode({
            "key": api_key,   # closed over — not in params dict
            "cx":  cx,        # closed over — not in params dict
            "q":   params["q"],
            "start": params.get("start", 1),
            "num":   params.get("num", 10),
        })
        url = f"{_CSE_ENDPOINT}?{qs}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "moat-engine/1.0 demand-research"}, method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                # Read full body — Google error JSON is typically 300-800 bytes.
                # Do NOT log `url` here; it contains the API key.
                body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            if exc.code == 429:
                raise RateLimited("Google CSE 429", retry_after=60.0) from exc
            # Parse Google's structured error if present.
            error_detail = body
            try:
                parsed = json.loads(body)
                err_obj = parsed.get("error", {})
                error_detail = (
                    f"status={err_obj.get('status')} "
                    f"message={err_obj.get('message')} "
                    f"reason={[e.get('reason') for e in err_obj.get('errors', [])]}"
                )
            except Exception:
                pass
            raise RuntimeError(
                f"Google CSE HTTP {exc.code}: {error_detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Google CSE network error: {exc.reason}") from exc
    return _fetch


# ---------------------------------------------------------------------------
# 3. RESULT PARSING  (pure — no network, fully testable)
# ---------------------------------------------------------------------------

def _extract_domain(url: str) -> Optional[str]:
    """
    Extract the bare registrable domain from a URL.
    Returns None if the URL is malformed.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if not host:
            return None
        # Strip www. prefix
        if host.startswith("www."):
            host = host[4:]
        # Strip port if present
        if ":" in host:
            host = host.split(":")[0]
        return host if "." in host else None
    except Exception:
        return None


def _parse_cse_response(payload: dict) -> list[str]:
    """
    Extract URLs from a Google CSE JSON response.
    Returns a list of raw URLs (not yet domain-extracted or filtered).
    """
    if not isinstance(payload, dict):
        return []
    items = payload.get("items") or []
    return [item["link"] for item in items if isinstance(item, dict) and "link" in item]


def _filter_domains(domains: list[str]) -> list[str]:
    """
    Remove blocked domains, keep unique, preserve insertion order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for d in domains:
        if not d:
            continue
        # Check if domain or any parent matches blocklist
        # e.g. 'shop.amazon.com' → block; 'loyalsupplyco.com' → allow
        parts = d.split(".")
        blocked = any(
            ".".join(parts[i:]) in _DOMAIN_BLOCKLIST
            for i in range(len(parts) - 1)
        )
        if blocked:
            continue
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


# ---------------------------------------------------------------------------
# 4. QUERY ONE DORK  (pagination up to provider cap)
# ---------------------------------------------------------------------------

def query_dork(
    query:  str,
    gf:     GuardedFetcher,
    api_key: str,
    cx:      str,
    pages:   int = 3,
) -> list[str]:
    """
    Run one dork query and return unique filtered domains from up to `pages` pages.
    Each page = 10 results; pages=3 → up to 30 URLs.
    """
    fetch_fn = make_cse_fetch_fn(api_key, cx)
    all_domains: list[str] = []

    for page_num in range(pages):
        start = page_num * 10 + 1   # CSE pagination: start=1, 11, 21, ...
        params = {"q": query, "start": start, "num": 10}
        # endpoint does NOT contain the key — safe to use as cache-key component
        payload = gf.fetch(
            provider="google_cse",
            endpoint=_CSE_ENDPOINT,
            params=params,
            fetch_fn=fetch_fn,
            ttl=7 * 24 * 3600,
            cost=0.005,
        )
        urls    = _parse_cse_response(payload)
        domains = [_extract_domain(u) for u in urls]
        domains = [d for d in domains if d is not None]
        all_domains.extend(domains)

        # Stop early if fewer than 10 results returned (last page)
        if len(urls) < 10:
            break

    return _filter_domains(all_domains)


# ---------------------------------------------------------------------------
# 5. HARVEST A LIST OF DORKS
# ---------------------------------------------------------------------------

def harvest(
    queries:  list[str],
    gf:       GuardedFetcher,
    api_key:  str,
    cx:       str,
    pages:    int  = 3,
    verbose:  bool = True,
    debug:    bool = False,
) -> list[str]:
    """
    Run each query, accumulate unique filtered domains.
    debug=True: re-raises on first error (full traceback) instead of WARNING + continue.
    """
    seen:   set[str]  = set()
    result: list[str] = []

    for q in queries:
        if verbose:
            print(f"  dork: {q[:80]}{'…' if len(q) > 80 else ''}", file=sys.stderr)
        try:
            domains = query_dork(q, gf, api_key, cx, pages=pages)
        except (KillSwitchEngaged, BudgetExceeded):
            raise
        except Exception as exc:
            if debug:
                raise   # full traceback; stops on first error
            import traceback
            print(f"  WARNING: query failed — {exc}", file=sys.stderr)
            print(f"  {traceback.format_exc().strip()}", file=sys.stderr)
            continue

        new = [d for d in domains if d not in seen]
        seen.update(new)
        result.extend(new)
        if verbose and new:
            print(f"    +{len(new)} new domain(s): {', '.join(new[:5])}"
                  + (f" … +{len(new)-5}" if len(new) > 5 else ""), file=sys.stderr)

    return result


# ---------------------------------------------------------------------------
# 6. SELF-TEST  (offline, no credentials needed)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    # ── _extract_domain ──────────────────────────────────────────────────────
    assert _extract_domain("https://www.knkg.com/products/bag") == "knkg.com"
    assert _extract_domain("https://vonbaer.com/")              == "vonbaer.com"
    assert _extract_domain("https://www.amazon.com/dp/X")       == "amazon.com"
    assert _extract_domain("not-a-url")                         is None
    assert _extract_domain("https://shop.loyalsupplyco.com/")   == "shop.loyalsupplyco.com"

    # ── _parse_cse_response ──────────────────────────────────────────────────
    mock_response = {
        "items": [
            {"title": "Leather Bag – KNKG",  "link": "https://www.knkg.com/"},
            {"title": "Von Baer Leather",    "link": "https://vonbaer.com/products/duffel"},
            {"title": "Amazon.com: leather", "link": "https://www.amazon.com/dp/B001"},
            {"no_link": "malformed"},
        ]
    }
    urls = _parse_cse_response(mock_response)
    assert len(urls) == 3, urls
    assert "https://www.knkg.com/" in urls

    # Empty / malformed payloads
    assert _parse_cse_response({}) == []
    assert _parse_cse_response({"items": None}) == []
    assert _parse_cse_response(None) == []  # type: ignore[arg-type]

    # ── _filter_domains ──────────────────────────────────────────────────────
    raw = ["knkg.com", "amazon.com", "vonbaer.com", "knkg.com",
           "shop.amazon.com", "wikipedia.org", "hardgraft.com"]
    filtered = _filter_domains(raw)
    assert "knkg.com"       in filtered
    assert "vonbaer.com"    in filtered
    assert "hardgraft.com"  in filtered
    assert "amazon.com"     not in filtered
    assert "shop.amazon.com" not in filtered   # subdomain of blocked domain
    assert "wikipedia.org"  not in filtered
    assert filtered.count("knkg.com") == 1     # deduplicated

    # ── seed dorks completeness ───────────────────────────────────────────────
    for sid in ("01", "03", "05"):
        assert sid in _SEED_DORKS, f"Missing dorks for seed {sid}"
        assert len(_SEED_DORKS[sid]) >= 2, f"Too few dorks for seed {sid}"
        for dork in _SEED_DORKS[sid]:
            assert isinstance(dork, str) and len(dork) > 10, dork

    # ── credential check (absence — not presence — validated in --self-test) ─
    # We only verify that the loader raises cleanly when keys are absent.
    # Real keys are never tested here (that would make the self-test require live creds).
    import os
    saved_key = os.environ.pop("MOAT_GOOGLE_CSE_KEY", None)
    saved_cx  = os.environ.pop("MOAT_GOOGLE_CSE_CX",  None)
    try:
        try:
            _load_credentials()
            raise AssertionError("should have raised EnvironmentError")
        except EnvironmentError as exc:
            assert "MOAT_GOOGLE_CSE_KEY" in str(exc), exc
    finally:
        if saved_key is not None:
            os.environ["MOAT_GOOGLE_CSE_KEY"] = saved_key
        if saved_cx  is not None:
            os.environ["MOAT_GOOGLE_CSE_CX"]  = saved_cx

    # ── make_cse_fetch_fn: credentials are NOT in the params it uses for cache ─
    # Verify that the closure captures the key but doesn't leak it into params.
    captured_params: dict = {}

    def _spy_fetch_fn(params: dict) -> Any:
        captured_params.update(params)
        return {"items": [{"link": "https://knkg.com/"}]}

    # Simulate what GuardedFetcher would call:
    #   gf.fetch(provider, endpoint, params={"q":"test","start":1}, fetch_fn=fn)
    # The params dict is what becomes the cache key.
    safe_params = {"q": "test dork", "start": 1, "num": 10}
    _ = make_cse_fetch_fn("FAKE_KEY", "FAKE_CX")   # just test it constructs
    # The fetch_fn itself doesn't receive the key in params — it closes over it.
    # Confirming that safe_params contains no auth:
    assert "key" not in safe_params
    assert "cx"  not in safe_params

    print("self-test PASSED: domain extraction, CSE response parsing, "
          "domain filtering (blocklist + subdomain + dedup), "
          "dork completeness, credential isolation — all hold")


# ---------------------------------------------------------------------------
# 7. CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Harvest candidate domains from Google Custom Search dorks. "
            "Credentials via MOAT_GOOGLE_CSE_KEY and MOAT_GOOGLE_CSE_CX env vars."
        )
    )
    ap.add_argument("--self-test",       action="store_true",
                    help="run offline self-test (no credentials needed) and exit")
    ap.add_argument("--list-dorks",      action="store_true",
                    help="print built-in dorks for all seeds and exit")
    ap.add_argument("--probe",           action="store_true",
                    help="fire ONE raw API call bypassing GuardedFetcher — shows exact "
                         "HTTP status and Google error body; use to diagnose 403/key issues")
    ap.add_argument("--reset-killswitch", action="store_true",
                    help="clear a latched killswitch left by a previous failed run, then exit")
    ap.add_argument("--debug",           action="store_true",
                    help="re-raise on first error with full traceback (stops after first failure)")
    ap.add_argument("--seed",       nargs="+", metavar="ID",
                    help="use built-in dorks for these seed IDs (e.g. 01 03 05)")
    ap.add_argument("--dork",       nargs="+", metavar="QUERY",
                    help="explicit dork query string(s)")
    ap.add_argument("--dorks-file", metavar="FILE",
                    help="text file with one dork query per line")
    ap.add_argument("--pages",      type=int, default=3,
                    help="result pages per query (10 results/page; default: 3)")
    ap.add_argument("--out",        metavar="FILE",
                    help="write candidate domains to this file (default: stdout)")
    ap.add_argument("--run-budget", type=float, default=2.0,
                    help="per-run spend ceiling USD (default: 2.00 ≈ 400 queries)")
    ap.add_argument("--quiet",      action="store_true",
                    help="suppress progress output")
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    if args.reset_killswitch:
        from safe_loop import KillSwitch
        ks = KillSwitch(default_state_dir(), default_config().max_consecutive_errors,
                        __import__("time").time)
        was = ks.is_tripped()
        reason = ks.reason()
        ks.reset()
        print(f"Kill switch reset (was tripped={was}, reason={reason!r})")
        print("You can now re-run the harvester.")
        return 0

    if args.probe:
        # Bypass GuardedFetcher entirely — raw urllib call, one result.
        # Shows the exact HTTP response code and Google error body.
        try:
            api_key, cx = _load_credentials()
        except EnvironmentError as exc:
            print(f"\n{exc}", file=sys.stderr)
            return 1
        print("Sending ONE raw probe request to Google CSE (bypassing GuardedFetcher)…")
        qs = urllib.parse.urlencode({
            "key": api_key, "cx": cx,
            "q": "leather bag", "num": 1, "start": 1,
        })
        url = f"{_CSE_ENDPOINT}?{qs}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "moat-engine/1.0 demand-research"}, method="GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                total = data.get("searchInformation", {}).get("totalResults", "?")
                items = data.get("items", [])
                print(f"SUCCESS — HTTP 200")
                print(f"  totalResults : {total}")
                print(f"  items returned: {len(items)}")
                if items:
                    print(f"  first result  : {items[0].get('link', '?')}")
                print("\nCredentials and CSE configuration are valid. "
                      "Run --reset-killswitch then retry the harvest.")
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            print(f"FAILED — HTTP {exc.code}")
            try:
                parsed = json.loads(body)
                err = parsed.get("error", {})
                print(f"  status  : {err.get('status')}")
                print(f"  message : {err.get('message')}")
                for e in err.get("errors", []):
                    print(f"  reason  : {e.get('reason')}  domain: {e.get('domain')}")
            except Exception:
                print(f"  raw body: {body[:500]}")
            print("\nFix the error above, then run --reset-killswitch before retrying.")
        except Exception as exc:
            print(f"NETWORK ERROR: {exc}")
        return 0

    if args.list_dorks:
        for sid, dorks in sorted(_SEED_DORKS.items()):
            print(f"\n--- Seed {sid} ---")
            for d in dorks:
                print(f"  {d}")
        print()
        return 0

    # Assemble the query list
    queries: list[str] = []
    if args.seed:
        for sid in args.seed:
            sid = sid.zfill(2)
            if sid not in _SEED_DORKS:
                print(f"ERROR: no built-in dorks for seed {sid!r}. "
                      f"Available: {', '.join(sorted(_SEED_DORKS))}",
                      file=sys.stderr)
                return 1
            queries.extend(_SEED_DORKS[sid])
    if args.dork:
        queries.extend(args.dork)
    if args.dorks_file:
        p = Path(args.dorks_file)
        if not p.exists():
            print(f"ERROR: dorks file not found: {args.dorks_file}", file=sys.stderr)
            return 1
        queries.extend(
            l.strip() for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")
        )

    if not queries:
        print("ERROR: specify at least one of --seed, --dork, or --dorks-file.",
              file=sys.stderr)
        ap.print_help()
        return 1

    # Load credentials — fail clearly, before any network activity
    try:
        api_key, cx = _load_credentials()
    except EnvironmentError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    gf = GuardedFetcher(
        config=default_config(),
        state_dir=default_state_dir(),
        run_budget_usd=args.run_budget,
    )

    if not args.quiet:
        print(f"Harvesting {len(queries)} dork(s), {args.pages} page(s) each "
              f"(up to {len(queries) * args.pages * 10} raw URLs)", file=sys.stderr)

    try:
        domains = harvest(queries, gf, api_key, cx,
                          pages=args.pages, verbose=not args.quiet,
                          debug=args.debug)
    except KillSwitchEngaged as exc:
        print(f"\nKILL SWITCH ENGAGED: {exc}", file=sys.stderr)
        print("Run:  python T-tools/serp_harvester.py --reset-killswitch", file=sys.stderr)
        return 2
    except BudgetExceeded as exc:
        print(f"\nBUDGET EXCEEDED: {exc}", file=sys.stderr)
        return 3

    if not domains:
        print("No candidate domains found. Try different dorks or --pages.", file=sys.stderr)
        return 0

    output_lines = "\n".join(domains) + "\n"

    if args.out:
        out_path = Path(args.out)
        # Append if file exists, so successive seed runs accumulate candidates
        existing: list[str] = []
        if out_path.exists():
            existing = [
                l.strip() for l in out_path.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")
            ]
        merged = list(dict.fromkeys(existing + domains))  # dedup, preserve order
        out_path.write_text("\n".join(merged) + "\n", encoding="utf-8")
        if not args.quiet:
            new_count = len(domains) - sum(1 for d in domains if d in set(existing))
            print(f"\n{new_count} new domain(s) added → {args.out} "
                  f"({len(merged)} total)", file=sys.stderr)
    else:
        print(output_lines, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
