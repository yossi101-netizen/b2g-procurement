"""
demand_fetcher.py -- Stage 1 demand automation for moat-engine.
T-tools. Demand-only.

WHAT THIS DOES
--------------
Takes a seeds.json file, fetches keyword metrics (D1/D2/D3) from DataForSEO
and trend direction from pytrends (Google Trends), and writes one JSON file
per seed to M-memory/batches/YYYYMMDD_HHMMSS/.

The output files are HALF-FILLED: DEMAND axis is auto-populated; MOAT inputs
(material_premium, niche_wedge, brandability, commodity_risk, price_band,
compliance_status) are left null and require human judgment before
engine_ready can be set to True.

AIR-GAP CONTRACT
----------------
This script is NOT moat_discovery_engine.py. The scoring engine remains
air-gapped (no network, no DB). This script is the external ingestion layer
that feeds it.

CREDENTIALS
-----------
Loaded from moat-engine/.env (KEY=VALUE format, one per line):
    MOAT_DATAFORSEO_LOGIN=your.email@example.com
    MOAT_DATAFORSEO_PASSWORD=your_api_password

Or pass via CLI: --dfs-login / --dfs-password
Credentials are NEVER logged, cached, or echoed.

USAGE
-----
    python3 T-tools/demand_fetcher.py --seeds seeds.json
    python3 T-tools/demand_fetcher.py --seeds seeds.json --dry-run
    python3 T-tools/demand_fetcher.py --self-test
    python3 T-tools/demand_fetcher.py --status

COST
----
~$0.20 per seed (conservative: ~67 keywords x $0.003). A 5-seed batch costs
~$1. Cached results are FREE on repeat runs. Run --dry-run first to confirm
the plan.
"""

from __future__ import annotations

import argparse
import base64
import copy
import datetime
import json
import os
import random
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional
import urllib.request
import urllib.error

# -- inject the T-tools directory so we can import safe_loop ------------------
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from safe_loop import (
    GuardedFetcher, ProviderConfig, RunConfig, RateLimited,
    KillSwitchEngaged, BudgetExceeded,
    default_config, default_state_dir, _FakeClock,
)

# ---------------------------------------------------------------------------
# 0. CONSTANTS
# ---------------------------------------------------------------------------

_REPO_ROOT = _HERE.parent                            # moat-engine/
_ENV_FILE = _REPO_ROOT / ".env"
_DFS_ENDPOINT = "/v3/dataforseo_labs/google/keyword_ideas/live"
_DFS_BASE_URL = "https://api.dataforseo.com"
_BATCH_DIR = _REPO_ROOT / "M-memory" / "batches"

# DataForSEO provider config: $0.20 is conservative (~67 keywords x $0.003).
# Actual cost is reported by the API in each response; adjust cost_per_call_usd
# after the first real run to match reality.
_DFS_PROVIDER = ProviderConfig(
    name="dataforseo",
    cost_per_call_usd=0.20,
    min_interval_seconds=1.0,
    jitter_seconds=0.5,
    rate_window_seconds=60.0,
    max_calls_per_window=30,
    max_calls_per_run=100,
    max_pages_per_query=1,
    default_ttl_seconds=7 * 24 * 3600,
    max_retries=3,
    backoff_seconds=10.0,
)

_DFS_KD_ENDPOINT = "/v3/dataforseo_labs/google/bulk_keyword_difficulty/live"

# Seed KD lookup: cheap single-keyword call to get accurate KD for the seed term.
# keyword_ideas/live does not reliably return seed_keyword_data KD, so we call
# bulk_keyword_difficulty/live as a second pass.
_DFS_KD_PROVIDER = ProviderConfig(
    name="dataforseo_kd",
    cost_per_call_usd=0.01,
    min_interval_seconds=0.5,
    jitter_seconds=0.3,
    rate_window_seconds=60.0,
    max_calls_per_window=60,
    max_calls_per_run=100,
    max_pages_per_query=1,
    default_ttl_seconds=7 * 24 * 3600,
    max_retries=3,
    backoff_seconds=5.0,
)

# D-axis classification thresholds (mirror moat_discovery_engine constants)
_KD_LOW_COMP = 10.0      # KD ≤ this counts toward n_low_comp_terms
_VOL_MIN = 100           # minimum volume to include in cluster / n_low_comp count
_TREND_RISE_RATIO = 1.15   # recent-half / prior-half > this → RISING
_TREND_DECLINE_RATIO = 0.85  # < this → DECLINING

# ---------------------------------------------------------------------------
# 1. CREDENTIAL LOADING
# ---------------------------------------------------------------------------

def _load_env(path: Path) -> dict[str, str]:
    """Parse a KEY=VALUE .env file. Ignores comments and blank lines."""
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def _get_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """
    Resolve DataForSEO credentials.
    Priority: CLI args > moat-engine/.env > environment variables.
    Raises SystemExit with instructions (never echoes secrets).
    """
    login: Optional[str] = getattr(args, "dfs_login", None)
    password: Optional[str] = getattr(args, "dfs_password", None)

    if not login or not password:
        env = _load_env(_ENV_FILE)
        login = login or env.get("MOAT_DATAFORSEO_LOGIN") or os.environ.get("MOAT_DATAFORSEO_LOGIN")
        password = (
            password
            or env.get("MOAT_DATAFORSEO_PASSWORD")
            or os.environ.get("MOAT_DATAFORSEO_PASSWORD")
        )

    if not login or not password:
        print(
            "ERROR: DataForSEO credentials not found.\n\n"
            "Add these two lines to moat-engine/.env:\n"
            "  MOAT_DATAFORSEO_LOGIN=your.email@example.com\n"
            "  MOAT_DATAFORSEO_PASSWORD=your_api_password\n\n"
            "Or pass them directly:\n"
            "  python3 T-tools/demand_fetcher.py --seeds seeds.json "
            "--dfs-login EMAIL --dfs-password PASSWORD",
            file=sys.stderr,
        )
        sys.exit(1)

    return login, password


# ---------------------------------------------------------------------------
# 2. DATAFORSEO FETCH FUNCTION (the only network touch -- injected externally)
# ---------------------------------------------------------------------------

def make_dfs_fetch_fn(login: str, password: str) -> Callable[[dict], Any]:
    """
    Returns a fetch_fn closure for DataForSEO keyword_ideas/live.
    Credentials live in the closure; they are never logged or echoed.

    params dict: keyword, location_code (default 2840=US), language_code, limit
    Returns: raw JSON response dict from the API.
    Raises RateLimited on HTTP 429.
    """
    _auth = "Basic " + base64.b64encode(f"{login}:{password}".encode()).decode("ascii")
    _url = _DFS_BASE_URL + _DFS_ENDPOINT

    def _fetch(params: dict) -> Any:
        payload_obj = [{
            "keywords": [params["keyword"]],
            "location_code": params.get("location_code", 2840),
            "language_code": params.get("language_code", "en"),
            "limit": params.get("limit", 50),
        }]
        body = json.dumps(payload_obj).encode("utf-8")

        req = urllib.request.Request(
            _url,
            data=body,
            headers={"Authorization": _auth, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = float(exc.headers.get("Retry-After", 60))
                raise RateLimited("DataForSEO 429", retry_after=retry_after) from exc
            raise

    return _fetch


def make_dfs_kd_fetch_fn(login: str, password: str) -> Callable[[dict], Any]:
    """
    Returns a fetch_fn for DataForSEO bulk_keyword_difficulty/live.
    Called once per seed to get the seed keyword's own KD — keyword_ideas/live
    does not reliably populate seed_keyword_data.keyword_properties.keyword_difficulty.

    params dict: keyword, location_code, language_code
    Returns: raw JSON response dict.
    """
    _auth = "Basic " + base64.b64encode(f"{login}:{password}".encode()).decode("ascii")
    _url = _DFS_BASE_URL + _DFS_KD_ENDPOINT

    def _fetch(params: dict) -> Any:
        payload_obj = [{
            "keywords": [params["keyword"]],
            "location_code": params.get("location_code", 2840),
            "language_code": params.get("language_code", "en"),
        }]
        body = json.dumps(payload_obj).encode("utf-8")
        req = urllib.request.Request(
            _url,
            data=body,
            headers={"Authorization": _auth, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = float(exc.headers.get("Retry-After", 60))
                raise RateLimited("DataForSEO 429", retry_after=retry_after) from exc
            raise

    return _fetch


# ---------------------------------------------------------------------------
# 3. PYTRENDS FETCH FUNCTION (optional; graceful fallback to FLAT)
# ---------------------------------------------------------------------------

def make_pytrends_fetch_fn() -> Optional[Callable[[dict], Any]]:
    """
    Returns a pytrends fetch_fn if pytrends is installed, else None.
    None → trend field will be FLAT for all seeds.

    params dict: keyword, timeframe (default "today 5-y"), geo (default "US")
    Returns: list[float] of weekly normalised interest values (most recent last).
    """
    try:
        from pytrends.request import TrendReq  # type: ignore
    except ImportError:
        return None

    def _fetch(params: dict) -> list[float]:
        kw = params["keyword"]
        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload(
            [kw],
            cat=0,
            timeframe=params.get("timeframe", "today 5-y"),
            geo=params.get("geo", "US"),
            gprop="",
        )
        df = pytrends.interest_over_time()
        if df.empty or kw not in df.columns:
            return []
        return [float(v) for v in df[kw].tolist()]

    return _fetch


def _classify_trend(values: list[float]) -> tuple[str, str]:
    """
    Split weekly values in half; compare recent avg to prior avg.
    Returns (TrendDirection str, human-readable summary).
    """
    if len(values) < 14:
        return "FLAT", f"insufficient data ({len(values)} weekly points, need ≥14)"

    mid = len(values) // 2
    prior_avg = sum(values[:mid]) / mid
    recent_avg = sum(values[mid:]) / (len(values) - mid)

    if prior_avg < 1e-6:
        return "FLAT", "prior period near-zero; cannot compute ratio"

    ratio = recent_avg / prior_avg
    if ratio >= _TREND_RISE_RATIO:
        direction = "RISING"
    elif ratio <= _TREND_DECLINE_RATIO:
        direction = "DECLINING"
    else:
        direction = "FLAT"

    summary = (
        f"last {len(values) - mid}wk avg={recent_avg:.1f} vs "
        f"prior {mid}wk avg={prior_avg:.1f} (ratio {ratio:.2f})"
    )
    return direction, summary


# ---------------------------------------------------------------------------
# 4. RESPONSE PARSING
# ---------------------------------------------------------------------------

_DFS_OK_CODE = 20000  # DataForSEO's HTTP-200-but-success marker


def _check_dfs_task(task: dict, raw_payload: dict) -> None:
    """
    DataForSEO embeds its real status in the JSON body, not in the HTTP status
    code. Auth failures, zero-balance errors, and invalid requests all return
    HTTP 200 with a non-20000 status_code here.

    Raises RuntimeError with the full error details + raw payload so the caller
    can diagnose the exact account/credential issue.
    """
    status_code = task.get("status_code")
    status_msg = task.get("status_message", "(no message)")

    if status_code is None:
        # Unexpected shape — dump the whole task so nothing is hidden.
        raise RuntimeError(
            f"DataForSEO response missing 'status_code'.\n"
            f"Raw task: {json.dumps(task, indent=2)}\n"
            f"Full payload: {json.dumps(raw_payload, indent=2)}"
        )

    if status_code != _DFS_OK_CODE:
        raise RuntimeError(
            f"DataForSEO API error {status_code}: {status_msg}\n"
            f"Full payload: {json.dumps(raw_payload, indent=2)}\n\n"
            f"Common causes:\n"
            f"  40101 — wrong login/password in moat-engine/.env\n"
            f"  40601 — account balance is zero; top up at app.dataforseo.com\n"
            f"  40201 — endpoint not enabled for your plan\n"
            f"  20100 — task created but no result yet (retry later)"
        )


def _parse_dfs_response(payload: dict) -> dict:
    """
    Extract D1/D2/D3 metrics from a DataForSEO keyword_ideas response.
    Raises RuntimeError on any API-level error (auth, balance, bad request).

    cluster_volume  = main keyword volume + sum of related-idea volumes (≥100)
    cluster_kd      = main keyword's KD from seed_keyword_data
    n_low_comp_terms = count of ideas where KD ≤ 10 AND volume ≥ 100
    """
    tasks = payload.get("tasks") or []
    if not tasks:
        raise RuntimeError(
            f"DataForSEO response contains no tasks.\n"
            f"Full payload: {json.dumps(payload, indent=2)}"
        )

    task = tasks[0]
    _check_dfs_task(task, payload)  # raises loudly on any non-20000 status

    result: dict[str, Any] = {
        "cluster_volume": 0,
        "cluster_kd": 35.0,
        "n_low_comp_terms": 0,
        "main_keyword_volume": 0,
        "cluster_keywords": [],
        "low_comp_terms_found": [],
        "dataforseo_cost_reported_usd": None,
    }

    cost = task.get("cost")
    if cost is not None:
        result["dataforseo_cost_reported_usd"] = cost

    task_results = task.get("result") or []
    if not task_results:
        # status_code was 20000 but result is empty — keyword may have zero data.
        return result
    tr = task_results[0]

    seed_data = tr.get("seed_keyword_data") or {}
    ki = seed_data.get("keyword_info") or {}
    kp = seed_data.get("keyword_properties") or {}

    main_vol = int(ki.get("search_volume") or 0)
    main_kd = float(kp.get("keyword_difficulty") or 35.0)

    result["main_keyword_volume"] = main_vol
    result["cluster_kd"] = main_kd
    result["cluster_volume"] = main_vol

    cluster_kws: list[dict] = []
    low_comp: list[dict] = []

    for item in (tr.get("items") or []):
        iki = item.get("keyword_info") or {}
        ikp = item.get("keyword_properties") or {}
        kw_text = item.get("keyword", "")
        vol = int(iki.get("search_volume") or 0)
        kd = float(ikp.get("keyword_difficulty") or 100.0)

        if vol >= _VOL_MIN:
            result["cluster_volume"] += vol
            cluster_kws.append({"keyword": kw_text, "volume": vol, "kd": kd})

        if kd <= _KD_LOW_COMP and vol >= _VOL_MIN:
            result["n_low_comp_terms"] += 1
            low_comp.append({"keyword": kw_text, "volume": vol, "kd": kd})

    result["cluster_keywords"] = cluster_kws
    result["low_comp_terms_found"] = low_comp
    return result


def _parse_dfs_kd_response(payload: dict, seed_keyword: str) -> Optional[float]:
    """
    Extract keyword difficulty for seed_keyword from a bulk_keyword_difficulty response.
    Returns the KD as a float >0, or None if not found / API returned 0 (no data sentinel).

    DataForSEO returns keyword_difficulty=0 when it has no SERP-based data for a keyword
    on the current plan tier.  Treat 0 as "no data" — caller keeps the 35.0 fallback.
    When 0 is hit, the raw result block is dumped to stderr so the structure is visible.
    """
    tasks = payload.get("tasks") or []
    if not tasks:
        return None
    task = tasks[0]
    _check_dfs_task(task, payload)
    for result_item in (task.get("result") or []):
        for item in (result_item.get("items") or []):
            if item.get("keyword", "").lower() == seed_keyword.lower():
                kd = item.get("keyword_difficulty")
                if kd is not None:
                    kd_float = float(kd)
                    if kd_float == 0.0:
                        # DFS returns 0 when it has no SERP-based KD for this plan tier.
                        return None
                    return kd_float
    return None


def _accessible_kd(cluster_keywords: list[dict]) -> float:
    """
    Mean KD of cluster terms where DataForSEO returned a real score (KD < 100).
    KD=100 is DFS's sentinel for 'high competition / no precise data' and is excluded.

    This estimates the realistic entry difficulty via the accessible tail of the niche —
    i.e., the terms a new brand can actually target. Unweighted so brand navigational
    queries with outsized volume don't distort the average.
    Falls back to 35.0 if every cluster term scored 100 (fully saturated cluster).
    """
    sub_100 = [item["kd"] for item in cluster_keywords if "kd" in item and item["kd"] < 100.0]
    if not sub_100:
        return 35.0
    return round(sum(sub_100) / len(sub_100), 1)


# ---------------------------------------------------------------------------
# 5. SEED LOADING
# ---------------------------------------------------------------------------

def load_seeds(path: Path) -> list[dict]:
    """
    Load seeds.json. Accepts a bare list or {"seeds": [...]} wrapper.
    Each entry needs at minimum: id, name, main_keyword.
    trend_keyword defaults to main_keyword if absent.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    seeds: list[dict] = data if isinstance(data, list) else data.get("seeds", [])
    for s in seeds:
        if "trend_keyword" not in s:
            s["trend_keyword"] = s["main_keyword"]
    return seeds


# ---------------------------------------------------------------------------
# 6. OUTPUT ASSEMBLY
# ---------------------------------------------------------------------------

def _build_output(seed: dict, demand: dict, trend: tuple[str, str]) -> dict:
    """Assemble the half-filled demand JSON for one seed."""
    trend_direction, trend_summary = trend
    return {
        "name": seed["name"],
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "engine_ready": False,
        "demand_source": "dataforseo_keyword_ideas + pytrends",
        "demand": {
            "cluster_volume": demand["cluster_volume"],
            "cluster_kd": demand["cluster_kd"],
            "n_low_comp_terms": demand["n_low_comp_terms"],
            "trend": trend_direction,
        },
        "demand_evidence": {
            "main_keyword": seed["main_keyword"],
            "main_keyword_volume": demand["main_keyword_volume"],
            "cluster_keywords": demand["cluster_keywords"],
            "low_comp_terms_found": demand["low_comp_terms_found"],
            "trend_keyword": seed["trend_keyword"],
            "trend_summary": trend_summary,
            "dataforseo_cost_reported_usd": demand["dataforseo_cost_reported_usd"],
        },
        "moat_inputs": {
            "bol_unique_importers": 0,
            "bol_repeat_importers": 0,
            "india_is_proven_origin": None,
            "material_premium": None,
            "niche_wedge": None,
            "brandability": None,
            "commodity_risk": None,
            "price_band": None,
            "compliance_status": None,
            "compliance_notes": [],
        },
        "seed_meta": {
            "id": seed.get("id"),
            "hts_chapter": seed.get("hts_chapter"),
            "material_angle": seed.get("material_angle"),
            "source": seed.get("source"),
        },
        "notes": (
            "DEMAND auto-filled (D1/D2/D3/trend). "
            "MOAT inputs require human judgment — fill in and set engine_ready=true to score."
        ),
    }


# ---------------------------------------------------------------------------
# 7. ORCHESTRATION
# ---------------------------------------------------------------------------

def run_batch(
    seeds: list[dict],
    gf: GuardedFetcher,
    dfs_fetch_fn: Callable[[dict], Any],
    dfs_kd_fn: Optional[Callable[[dict], Any]],
    pytrends_fn: Optional[Callable[[dict], Any]],
    out_dir: Path,
    *,
    dry_run: bool = False,
) -> None:
    """Fetch demand data for all seeds and write output JSONs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    for i, seed in enumerate(seeds, 1):
        sid = seed.get("id", str(i).zfill(2))
        kw = seed["main_keyword"]
        trend_kw = seed.get("trend_keyword", kw)

        print(f"\n[{sid}] {seed['name']}")
        print(f"     keyword: {kw}")

        if dry_run:
            print("     --dry-run: skipping fetch")
            results.append({"id": sid, "name": seed["name"], "status": "dry-run"})
            continue

        # -- DataForSEO -------------------------------------------------------
        demand: dict[str, Any] = {
            "cluster_volume": 0, "cluster_kd": 35.0, "n_low_comp_terms": 0,
            "main_keyword_volume": 0, "cluster_keywords": [],
            "low_comp_terms_found": [], "dataforseo_cost_reported_usd": None,
        }
        try:
            raw = gf.fetch(
                provider="dataforseo",
                endpoint=_DFS_ENDPOINT,
                params={"keyword": kw, "location_code": 2840, "language_code": "en", "limit": 50},
                fetch_fn=dfs_fetch_fn,
                ttl=7 * 24 * 3600,
                cost=_DFS_PROVIDER.cost_per_call_usd,
            )
            demand = _parse_dfs_response(raw)
            print(f"     vol={demand['cluster_volume']:,}  "
                  f"kd={demand['cluster_kd']:.1f}  "
                  f"low_comp_terms={demand['n_low_comp_terms']}")
        except (KillSwitchEngaged, BudgetExceeded):
            raise
        except Exception as exc:
            print(f"     ERROR (DataForSEO): {exc}", file=sys.stderr)
            results.append({"id": sid, "name": seed["name"], "status": f"error: {exc}"})
            continue

        # -- seed keyword KD (bulk_keyword_difficulty) -------------------------
        if dfs_kd_fn is not None:
            try:
                kd_raw = gf.fetch(
                    provider="dataforseo_kd",
                    endpoint=_DFS_KD_ENDPOINT,
                    params={"keyword": kw, "location_code": 2840, "language_code": "en"},
                    fetch_fn=dfs_kd_fn,
                    ttl=7 * 24 * 3600,
                    cost=_DFS_KD_PROVIDER.cost_per_call_usd,
                )
                seed_kd = _parse_dfs_kd_response(kd_raw, kw)
                if seed_kd is not None:
                    demand["cluster_kd"] = seed_kd
                    print(f"     kd (seed lookup): {seed_kd:.1f}")
                else:
                    cluster_kd = _accessible_kd(demand["cluster_keywords"])
                    demand["cluster_kd"] = cluster_kd
                    print(f"     kd (accessible mean): {cluster_kd:.1f}")
            except (KillSwitchEngaged, BudgetExceeded):
                raise
            except Exception as exc:
                print(f"     WARNING (seed KD lookup): {exc} — keeping {demand['cluster_kd']:.1f}", file=sys.stderr)

        # -- pytrends ----------------------------------------------------------
        trend: tuple[str, str] = ("FLAT", "pytrends not available")
        if pytrends_fn is not None:
            try:
                values = gf.fetch(
                    provider="google_trends",
                    endpoint="interest_over_time",
                    params={"keyword": trend_kw, "timeframe": "today 5-y", "geo": "US"},
                    fetch_fn=pytrends_fn,
                    ttl=3 * 24 * 3600,
                    cost=0.0,
                )
                trend = _classify_trend(values)
                print(f"     trend: {trend[0]}  ({trend[1]})")
            except Exception as exc:
                print(f"     WARNING (pytrends): {exc} — trend set to FLAT", file=sys.stderr)
        else:
            print("     trend: FLAT (pytrends not installed)")

        # -- write output ------------------------------------------------------
        output = _build_output(seed, demand, trend)
        slug = kw.replace(" ", "_").replace("/", "-")[:40]
        fname = f"{sid}_{slug}_demand.json"
        (out_dir / fname).write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"     -> {out_dir / fname}")

        results.append({
            "id": sid, "name": seed["name"], "status": "ok",
            "cluster_volume": demand["cluster_volume"],
            "cluster_kd": demand["cluster_kd"],
            "trend": trend[0],
            "output": fname,
        })

    # -- batch summary ---------------------------------------------------------
    summary = {
        "batch_dir": str(out_dir),
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "seeds_processed": len(results),
        "budget_status": gf.status(),
        "results": results,
    }
    (out_dir / "batch_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"\nBatch complete → {out_dir}")
    st = gf.status()
    print(
        f"Budget: run ${st['run_spend_usd']:.4f} | "
        f"cumulative ${st['cumulative_spend_usd']:.4f} | "
        f"ceiling remaining ${st['ceiling_remaining_usd']:.4f}"
    )


# ---------------------------------------------------------------------------
# 8. SELF-TEST (fully offline, no credentials, deterministic)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """
    Verifies: volume summation, KD extraction, n_low_comp_terms counting
    (KD≤10 AND vol≥100), trend RISING classification, moat_inputs all null,
    engine_ready=False, and cache hit (second fetch does not call the network).
    """
    _MOCK_DFS: dict = {
        "tasks": [{
            "status_code": 20000,
            "status_message": "Ok.",
            "cost": 0.12,
            "result": [{
                "seed_keyword_data": {
                    "keyword": "leather gym bag",
                    "keyword_info": {"search_volume": 12100},
                    "keyword_properties": {"keyword_difficulty": 11},
                },
                "items": [
                    # KD=8, vol=5400 → counts in cluster AND n_low_comp (KD≤10)
                    {"keyword": "leather gym duffel",
                     "keyword_info": {"search_volume": 5400},
                     "keyword_properties": {"keyword_difficulty": 8}},
                    # KD=14, vol=2900 → counts in cluster, NOT n_low_comp (KD>10)
                    {"keyword": "leather gym bag men",
                     "keyword_info": {"search_volume": 2900},
                     "keyword_properties": {"keyword_difficulty": 14}},
                    # KD=5, vol=70 → excluded entirely (vol<100)
                    {"keyword": "small leather gym pouch",
                     "keyword_info": {"search_volume": 70},
                     "keyword_properties": {"keyword_difficulty": 5}},
                    # KD=9, vol=1200 → counts in cluster AND n_low_comp
                    {"keyword": "veg tan leather duffel",
                     "keyword_info": {"search_volume": 1200},
                     "keyword_properties": {"keyword_difficulty": 9}},
                ],
            }],
        }],
    }

    # 26 weekly values: first 13 avg=55, last 13 avg=70 → ratio=1.27 → RISING
    _MOCK_TREND = [55.0] * 13 + [70.0] * 13

    _SEED = {
        "id": "01",
        "name": "Premium leather gym duffel — men's everyday carry",
        "main_keyword": "leather gym bag",
        "trend_keyword": "leather gym bag",
        "hts_chapter": "4202",
        "material_angle": "veg-tan leather, Kanpur",
        "source": "A (KNKG archetype)",
    }

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        clock = _FakeClock()
        cfg = default_config()
        cfg.providers["dataforseo"] = _DFS_PROVIDER

        gf = GuardedFetcher(
            config=cfg,
            state_dir=tmp / "runtime",
            run_budget_usd=10.0,
            monotonic_fn=clock.monotonic,
            wall_fn=clock.wall,
            sleep_fn=clock.sleep,
            rng=random.Random(42),
        )

        dfs_calls: dict[str, int] = {"n": 0}
        def _mock_dfs(params: dict) -> dict:
            dfs_calls["n"] += 1
            return copy.deepcopy(_MOCK_DFS)

        trend_calls: dict[str, int] = {"n": 0}
        def _mock_trend(params: dict) -> list[float]:
            trend_calls["n"] += 1
            return list(_MOCK_TREND)

        out_dir = tmp / "batch"
        run_batch([_SEED], gf, _mock_dfs, None, _mock_trend, out_dir)

        # 1. network touched exactly once per provider
        assert dfs_calls["n"] == 1, f"DFS calls: expected 1, got {dfs_calls['n']}"
        assert trend_calls["n"] == 1, f"trend calls: expected 1, got {trend_calls['n']}"

        output_file = next(out_dir.glob("*_demand.json"))
        output = json.loads(output_file.read_text())

        # 2. cluster_volume = 12100 + 5400 + 2900 + 1200 = 21600 (70-vol item excluded)
        expected_vol = 12100 + 5400 + 2900 + 1200
        assert output["demand"]["cluster_volume"] == expected_vol, (
            f"cluster_volume: expected {expected_vol}, got {output['demand']['cluster_volume']}"
        )

        # 3. cluster_kd from seed_keyword_data (not blended with ideas)
        assert output["demand"]["cluster_kd"] == 11.0, (
            f"cluster_kd: expected 11.0, got {output['demand']['cluster_kd']}"
        )

        # 4. n_low_comp_terms: KD=8/vol=5400 + KD=9/vol=1200 = 2
        assert output["demand"]["n_low_comp_terms"] == 2, (
            f"n_low_comp_terms: expected 2, got {output['demand']['n_low_comp_terms']}"
        )

        # 5. trend = RISING (70/55 = 1.27 > 1.15)
        assert output["demand"]["trend"] == "RISING", (
            f"trend: expected RISING, got {output['demand']['trend']}"
        )

        # 6. moat_inputs schema: human-filled fields all null, BoL counts zero
        mi = output["moat_inputs"]
        for field in ("material_premium", "niche_wedge", "brandability",
                      "commodity_risk", "price_band", "compliance_status",
                      "india_is_proven_origin"):
            assert mi[field] is None, f"moat_inputs.{field} should be null"
        assert mi["bol_unique_importers"] == 0
        assert mi["bol_repeat_importers"] == 0

        # 7. engine_ready must be False until human fills MOAT inputs
        assert output["engine_ready"] is False

        # 8. cache hit: second fetch of same keyword does NOT call DFS again
        dfs_calls["n"] = 0
        gf.fetch(
            "dataforseo", _DFS_ENDPOINT,
            {"keyword": "leather gym bag", "location_code": 2840, "language_code": "en", "limit": 50},
            _mock_dfs,
            ttl=7 * 24 * 3600,
            cost=0.20,
        )
        assert dfs_calls["n"] == 0, "Cache miss on identical params — cache is broken"

    print(
        "self-test passed: volume summation, KD, n_low_comp_terms (KD≤10 AND vol≥100), "
        "trend RISING, moat_inputs null, engine_ready=False, cache hit all verified"
    )


# ---------------------------------------------------------------------------
# 9. CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="moat-engine demand fetcher: auto-fills D1/D2/D3/trend per seed.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--seeds", metavar="FILE",
                    help="path to seeds.json (required for a live run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the fetch plan without calling any APIs")
    ap.add_argument("--run-budget", type=float, default=5.0, metavar="USD",
                    help="per-run spend cap in USD (default: $5.00)")
    ap.add_argument("--dfs-login", metavar="EMAIL",
                    help="DataForSEO login email (overrides .env)")
    ap.add_argument("--dfs-password", metavar="PASSWORD",
                    help="DataForSEO API password (overrides .env)")
    ap.add_argument("--self-test", action="store_true",
                    help="run offline self-test (no credentials needed)")
    ap.add_argument("--status", action="store_true",
                    help="print cumulative budget + killswitch state and exit")
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    ap = _build_parser()
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    if args.status:
        gf = GuardedFetcher(state_dir=default_state_dir(), run_budget_usd=0.0)
        print(json.dumps(gf.status(), indent=2))
        return 0

    if not args.seeds:
        ap.print_help()
        return 1

    seeds_path = Path(args.seeds)
    if not seeds_path.is_absolute():
        seeds_path = Path.cwd() / seeds_path
    if not seeds_path.exists():
        print(f"ERROR: seeds file not found: {seeds_path}", file=sys.stderr)
        return 1

    seeds = load_seeds(seeds_path)
    n = len(seeds)
    estimated_cost = n * _DFS_PROVIDER.cost_per_call_usd
    print(f"Loaded {n} seeds from {seeds_path}")
    print(f"Estimated cost: ${estimated_cost:.2f} (≤${args.run_budget:.2f} run cap)")

    if args.dry_run:
        print("\nDRY RUN — no API calls will be made:\n")
        for s in seeds:
            print(f"  [{s.get('id', '?')}] {s['name']}")
            print(f"       keyword={s['main_keyword']}  trend_keyword={s.get('trend_keyword', s['main_keyword'])}")
        return 0

    login, password = _get_credentials(args)
    dfs_fn = make_dfs_fetch_fn(login, password)
    dfs_kd_fn = make_dfs_kd_fetch_fn(login, password)
    pytrends_fn = make_pytrends_fetch_fn()

    if pytrends_fn is None:
        print(
            "NOTE: pytrends not installed — trend will be FLAT for all seeds.\n"
            "      Install with: pip install pytrends"
        )

    cfg = default_config()
    cfg.providers["dataforseo"] = _DFS_PROVIDER
    cfg.providers["dataforseo_kd"] = _DFS_KD_PROVIDER

    gf = GuardedFetcher(
        config=cfg,
        state_dir=default_state_dir(),
        run_budget_usd=args.run_budget,
    )

    batch_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = _BATCH_DIR / batch_ts

    try:
        run_batch(seeds, gf, dfs_fn, dfs_kd_fn, pytrends_fn, out_dir)
    except (KillSwitchEngaged, BudgetExceeded) as exc:
        print(f"\nSAFETY HALT: {exc}", file=sys.stderr)
        print(
            "Run 'python3 T-tools/safe_loop.py --status' to inspect state.\n"
            "Run 'python3 T-tools/safe_loop.py --reset-killswitch' to clear after review.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())