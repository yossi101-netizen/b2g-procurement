"""
safe_loop.py -- Foundational Execution Loop: SAFETY INFRASTRUCTURE ONLY
moat-engine (ABC-TOM, T-tools). Demand-only.

WHAT THIS IS / WHAT IT IS NOT
-----------------------------
This module is the protective runtime that EVERY data-ingestion agent must call
*through*. It contains ZERO ingestion logic -- no ImportYeti, no Ahrefs, no HTTP,
no scraping, no parsing. It exists to make an automated fetch loop safe to run
unattended, by solving the two dilemmas that kill such loops:

  1. BILL SHOCK / INFINITE LOOP
     -> BudgetLedger: per-run budget + a persistent cumulative $300 hard ceiling.
     -> hard pagination caps (max_pages_per_query) so a paginated pull cannot run away.
     -> a latching KillSwitch that halts the WHOLE loop on first breach and writes
        its tripped state to disk, so a process restart cannot resume a runaway.

  2. IP BAN / THROTTLING
     -> Throttle: per-provider minimum interval + randomized jitter + a rolling
        rate window + Retry-After penalty honouring.
     -> RequestCache: a persistent on-disk cache so we never pay for, or re-fetch,
        the same query twice. A cache hit costs nothing and touches no network.

THE CONTRACT (how ingestion plugs in later)
-------------------------------------------
Ingestion code -- written separately, AFTER this is approved -- supplies a
`fetch_fn(params) -> payload` callable and a request descriptor. GuardedFetcher
decides everything else:

    cache hit?            -> return it, FREE (no throttle, no charge, no network)
    killswitch tripped?   -> raise, refuse the call
    budget / page cap ok? -> no -> trip killswitch, raise
    otherwise             -> throttle -> call fetch_fn -> cache + charge + return

fetch_fn is the ONLY place the network is ever touched, and it lives outside this
file. This module never decides what to fetch or how to parse it.

TESTABILITY
-----------
All time, sleep, and randomness are injectable (monotonic_fn, wall_fn, sleep_fn,
rng). The self-test runs fully offline, deterministically, and WITHOUT real
sleeping, by injecting a fake clock whose sleep() just advances virtual time.
Real ingestion uses the real clock by default.

    python3 safe_loop.py --self-test       # offline, no network, no real sleep
    python3 safe_loop.py --status          # show cumulative budget + killswitch state
    python3 safe_loop.py --reset-killswitch # deliberately clear a halt

CALIBRATION STATUS
------------------
v0.1 -- provider limits and costs below are conservative initial guesses, NOT yet
tuned against real provider behaviour. Tighten min_interval / costs against the
first real pull before unattended use, then version this file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# 0. ERRORS
# ---------------------------------------------------------------------------

class SafeLoopError(Exception):
    """Base for everything this module raises."""


class KillSwitchEngaged(SafeLoopError):
    """The loop is halted. No further calls will be attempted until reset."""


class BudgetExceeded(SafeLoopError):
    """A charge would breach the per-run budget or the cumulative ceiling."""


class RateLimited(SafeLoopError):
    """
    Ingestion code raises this when a provider signals throttling (HTTP 429,
    a Cloudflare challenge, a 'slow down' body, etc.). Optionally carries the
    provider's Retry-After in seconds. This module never raises it -- it only
    reacts to it (penalise + back off + count toward the ban-detection trip).
    """
    def __init__(self, message: str = "", retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


# ---------------------------------------------------------------------------
# 1. CONFIG (provider limits + global caps)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderConfig:
    name: str
    cost_per_call_usd: float = 0.0     # 0.0 for free tools; >0 for metered/credit APIs
    min_interval_seconds: float = 5.0  # hard floor between two calls to this provider
    jitter_seconds: float = 2.0        # random 0..jitter added on top, to look non-robotic
    rate_window_seconds: float = 60.0  # rolling window for the burst cap
    max_calls_per_window: int = 10     # no more than this many calls inside the window
    max_calls_per_run: int = 50        # hard cap on calls to this provider in one run
    max_pages_per_query: int = 5       # the anti-infinite-loop pagination cap
    default_ttl_seconds: float = 7 * 24 * 3600   # cache lifetime (customs/SEO data is slow)
    max_retries: int = 3               # retries on RateLimited before tripping
    backoff_seconds: float = 30.0      # base backoff when no Retry-After is given


@dataclass
class RunConfig:
    global_ceiling_usd: float = 300.0  # ABSOLUTE cumulative spend ceiling (demand-only memo)
    max_consecutive_errors: int = 5    # ban-detection: this many in a row trips the switch
    providers: dict[str, ProviderConfig] = field(default_factory=dict)

    # A deliberately conservative fallback. An unknown provider is NEVER unlimited.
    _fallback: ProviderConfig = field(
        default_factory=lambda: ProviderConfig(name="_unknown_"),
    )

    def provider(self, name: str) -> ProviderConfig:
        return self.providers.get(name, self._fallback)


def default_config() -> RunConfig:
    """
    Initial, conservative limits for the providers the discovery funnel will use.
    Costs are operator-set estimates; subscription tools (Ahrefs) carry 0 per-call
    and are tracked against the cumulative ceiling via the operator logging the
    subscription charge once. Metered/credit APIs carry a real per-call cost.
    """
    return RunConfig(
        global_ceiling_usd=300.0,
        max_consecutive_errors=5,
        providers={
            # Customs / Bill-of-Lading. Free tier, but extremely ban-sensitive
            # (Cloudflare). Slow and patient on purpose; long cache (data is stable).
            "importyeti": ProviderConfig(
                name="importyeti", cost_per_call_usd=0.0,
                min_interval_seconds=20.0, jitter_seconds=10.0,
                rate_window_seconds=300.0, max_calls_per_window=15,
                max_calls_per_run=40, max_pages_per_query=5,
                default_ttl_seconds=30 * 24 * 3600, max_retries=2, backoff_seconds=60.0,
            ),
            # SEO keyword data. Subscription (per-call cost 0); credit-metered plans
            # should set cost_per_call_usd to the real credit price.
            "ahrefs": ProviderConfig(
                name="ahrefs", cost_per_call_usd=0.0,
                min_interval_seconds=2.0, jitter_seconds=1.5,
                rate_window_seconds=60.0, max_calls_per_window=30,
                max_calls_per_run=200, max_pages_per_query=10,
                default_ttl_seconds=14 * 24 * 3600, max_retries=3, backoff_seconds=15.0,
            ),
            # Google Trends (unofficial). Free but rate-limits hard; treat like a scrape.
            "google_trends": ProviderConfig(
                name="google_trends", cost_per_call_usd=0.0,
                min_interval_seconds=10.0, jitter_seconds=5.0,
                rate_window_seconds=120.0, max_calls_per_window=20,
                max_calls_per_run=60, max_pages_per_query=3,
                default_ttl_seconds=3 * 24 * 3600, max_retries=2, backoff_seconds=30.0,
            ),
            # Google Custom Search JSON API (official, authenticated).
            # Cost: $5/1000 queries = $0.005/call after 100 free/day.
            # GuardedFetcher NEVER caches the API key (fetch_fn closes over it;
            # params passed to .fetch() contain only {q, start} — no auth).
            # 7-day TTL: SERP results for artisan brand queries are stable.
            "google_cse": ProviderConfig(
                name="google_cse", cost_per_call_usd=0.005,
                min_interval_seconds=1.0, jitter_seconds=0.5,
                rate_window_seconds=60.0, max_calls_per_window=30,
                max_calls_per_run=50, max_pages_per_query=5,
                default_ttl_seconds=7 * 24 * 3600, max_retries=2, backoff_seconds=30.0,
            ),
            # Shopify /products.json public storefront endpoint.
            # No auth needed; 3.0s floor + 60s backoff avoids Cloudflare bot trips.
            # 3-day TTL: inventory shifts daily but not minute-to-minute.
            "shopify": ProviderConfig(
                name="shopify", cost_per_call_usd=0.0,
                min_interval_seconds=3.0, jitter_seconds=1.5,
                rate_window_seconds=60.0, max_calls_per_window=20,
                max_calls_per_run=150, max_pages_per_query=3,
                default_ttl_seconds=3 * 24 * 3600, max_retries=2, backoff_seconds=60.0,
            ),
            # Example metered API, to make the budget machinery concrete/visible.
            "metered_api": ProviderConfig(
                name="metered_api", cost_per_call_usd=0.01,
                min_interval_seconds=1.0, jitter_seconds=0.5,
                rate_window_seconds=60.0, max_calls_per_window=60,
                max_calls_per_run=1000, max_pages_per_query=20,
                default_ttl_seconds=7 * 24 * 3600, max_retries=3, backoff_seconds=10.0,
            ),
        },
    )


def default_state_dir() -> Path:
    """Runtime state lives in M-memory (logs/insights/runtime per ABC-TOM)."""
    return Path(__file__).resolve().parent.parent / "M-memory" / "runtime"


# ---------------------------------------------------------------------------
# 2. CACHE -- never query (or pay for) the same thing twice
# ---------------------------------------------------------------------------

class RequestCache:
    def __init__(self, cache_dir: Path, wall_fn: Callable[[], float]):
        self.dir = cache_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.wall_fn = wall_fn
        self.hits = 0
        self.misses = 0

    @staticmethod
    def make_key(provider: str, endpoint: str, params: dict) -> str:
        canon = json.dumps(
            {"provider": provider, "endpoint": endpoint, "params": params},
            sort_keys=True, default=str,
        )
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if not path.exists():
            self.misses += 1
            return None
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            self.misses += 1
            return None
        ttl = rec.get("ttl_seconds")
        if ttl is not None and (self.wall_fn() - rec.get("created_at", 0)) > ttl:
            self.misses += 1  # expired -> treat as miss, will be refetched + overwritten
            return None
        self.hits += 1
        return rec.get("payload")

    def set(self, key: str, payload: Any, meta: dict, ttl: float) -> None:
        rec = {
            "created_at": self.wall_fn(),
            "ttl_seconds": ttl,
            "meta": meta,
            "payload": payload,
        }
        self._path(key).write_text(json.dumps(rec, default=str), encoding="utf-8")


# ---------------------------------------------------------------------------
# 3. THROTTLE -- look human, respect rate limits, honour Retry-After
# ---------------------------------------------------------------------------

class Throttle:
    def __init__(
        self,
        config: RunConfig,
        monotonic_fn: Callable[[], float],
        sleep_fn: Callable[[float], None],
        rng: random.Random,
    ):
        self.config = config
        self.monotonic_fn = monotonic_fn
        self.sleep_fn = sleep_fn
        self.rng = rng
        self._last: dict[str, float] = {}
        self._next_allowed: dict[str, float] = {}
        self._window: dict[str, deque] = {}

    def wait(self, provider: str) -> float:
        """Block until it is safe to call `provider`. Returns the delay applied."""
        cfg = self.config.provider(provider)
        now = self.monotonic_fn()

        # Rolling burst window: drop timestamps older than the window.
        dq = self._window.setdefault(provider, deque())
        while dq and (now - dq[0]) >= cfg.rate_window_seconds:
            dq.popleft()
        window_wait_until = 0.0
        if cfg.max_calls_per_window and len(dq) >= cfg.max_calls_per_window:
            window_wait_until = dq[0] + cfg.rate_window_seconds

        target = max(now, self._next_allowed.get(provider, 0.0), window_wait_until)
        last = self._last.get(provider)
        if last is not None:
            target = max(target, last + cfg.min_interval_seconds)
        if cfg.jitter_seconds:
            target += self.rng.uniform(0.0, cfg.jitter_seconds)

        delay = max(0.0, target - now)
        if delay > 0:
            self.sleep_fn(delay)

        stamp = self.monotonic_fn()
        self._last[provider] = stamp
        self._window[provider].append(stamp)
        return delay

    def penalize(self, provider: str, seconds: float) -> None:
        """Push back the next-allowed time after a Retry-After / 429 / challenge."""
        now = self.monotonic_fn()
        self._next_allowed[provider] = max(
            self._next_allowed.get(provider, 0.0), now + max(0.0, seconds)
        )


# ---------------------------------------------------------------------------
# 4. BUDGET LEDGER -- per-run budget + persistent cumulative ceiling
# ---------------------------------------------------------------------------

class BudgetLedger:
    def __init__(
        self,
        state_dir: Path,
        run_budget_usd: float,
        global_ceiling_usd: float,
        wall_fn: Callable[[], float],
    ):
        state_dir.mkdir(parents=True, exist_ok=True)
        self.path = state_dir / "budget_ledger.json"
        self.global_ceiling = global_ceiling_usd
        # A run can never authorise more than the absolute ceiling.
        self.run_budget = min(run_budget_usd, global_ceiling_usd)
        self.wall_fn = wall_fn
        self.run_spend = 0.0
        self.run_calls: dict[str, int] = {}
        self._cum = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                pass
        return {"cumulative_spend_usd": 0.0, "total_calls": 0, "providers": {}, "updated_at": None}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._cum, indent=2, default=str), encoding="utf-8")

    def cumulative_spend(self) -> float:
        return self._cum["cumulative_spend_usd"]

    def remaining_run(self) -> float:
        return round(self.run_budget - self.run_spend, 6)

    def remaining_ceiling(self) -> float:
        return round(self.global_ceiling - self._cum["cumulative_spend_usd"], 6)

    def calls_for(self, provider: str) -> int:
        return self.run_calls.get(provider, 0)

    def can_afford(self, provider: str, cost: float) -> bool:
        eps = 1e-9
        return (
            (self.run_spend + cost) <= (self.run_budget + eps)
            and (self._cum["cumulative_spend_usd"] + cost) <= (self.global_ceiling + eps)
        )

    def charge(self, provider: str, cost: float) -> None:
        if not self.can_afford(provider, cost):
            raise BudgetExceeded(
                f"charge ${cost:.4f} to '{provider}' would breach "
                f"run budget (left ${self.remaining_run():.4f}) or "
                f"ceiling (left ${self.remaining_ceiling():.4f})"
            )
        self.run_spend = round(self.run_spend + cost, 6)
        self.run_calls[provider] = self.run_calls.get(provider, 0) + 1
        self._cum["cumulative_spend_usd"] = round(self._cum["cumulative_spend_usd"] + cost, 6)
        self._cum["total_calls"] += 1
        p = self._cum["providers"].setdefault(provider, {"spend_usd": 0.0, "calls": 0})
        p["spend_usd"] = round(p["spend_usd"] + cost, 6)
        p["calls"] += 1
        self._cum["updated_at"] = self.wall_fn()
        self._save()


# ---------------------------------------------------------------------------
# 5. KILL SWITCH -- latching halt, persisted across restarts
# ---------------------------------------------------------------------------

class KillSwitch:
    def __init__(self, state_dir: Path, max_consecutive_errors: int, wall_fn: Callable[[], float]):
        state_dir.mkdir(parents=True, exist_ok=True)
        self.path = state_dir / "killswitch.json"
        self.kill_file = state_dir / "KILL"   # operator can create this to halt everything
        self.max_consecutive_errors = max_consecutive_errors
        self.wall_fn = wall_fn
        self._consecutive = 0
        self._state = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                pass
        return {"tripped": False, "reason": None, "tripped_at": None}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._state, indent=2, default=str), encoding="utf-8")

    def is_tripped(self) -> bool:
        return bool(self._state.get("tripped"))

    def reason(self) -> Optional[str]:
        return self._state.get("reason")

    def trip(self, reason: str) -> None:
        if not self._state.get("tripped"):
            self._state = {"tripped": True, "reason": reason, "tripped_at": self.wall_fn()}
            self._save()

    def check(self) -> None:
        """Raise if halted. Also trips on the presence of a manual KILL file."""
        if self.kill_file.exists() and not self.is_tripped():
            self.trip("manual KILL file present")
        if self.is_tripped():
            raise KillSwitchEngaged(self._state.get("reason") or "killswitch tripped")

    def record_success(self) -> None:
        self._consecutive = 0

    def record_error(self, ban_signal: bool = False) -> None:
        self._consecutive += 1
        if self._consecutive >= self.max_consecutive_errors:
            self.trip(f"{self._consecutive} consecutive errors (ban_signal={ban_signal})")

    def reset(self) -> None:
        self._state = {"tripped": False, "reason": None, "tripped_at": None}
        self._save()
        if self.kill_file.exists():
            self.kill_file.unlink()
        self._consecutive = 0


# ---------------------------------------------------------------------------
# 6. GUARDED FETCHER -- the foundational execution loop
# ---------------------------------------------------------------------------

class GuardedFetcher:
    """
    The single chokepoint all ingestion calls pass through. Order of operations
    on every fetch (each guard is a veto, cheapest first):

        1. killswitch.check()                 -> refuse if halted
        2. cache.get()                        -> hit returns FREE (no throttle/charge/net)
        3. budget.can_afford() / call cap     -> breach trips killswitch + raises
        4. throttle.wait()                    -> enforce delay + jitter + rate window
        5. fetch_fn(params)                   -> the ONLY network touch (injected, external)
              RateLimited -> penalise + back off + count; trip after max_retries
              other error -> count toward ban-detection; re-raise
           success        -> cache.set() + budget.charge() + record_success()
    """

    def __init__(
        self,
        config: Optional[RunConfig] = None,
        state_dir: Optional[Path] = None,
        run_budget_usd: float = 0.0,
        *,
        monotonic_fn: Callable[[], float] = time.monotonic,
        wall_fn: Callable[[], float] = time.time,
        sleep_fn: Callable[[float], None] = time.sleep,
        rng: Optional[random.Random] = None,
    ):
        self.config = config or default_config()
        self.state_dir = state_dir or default_state_dir()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.monotonic_fn = monotonic_fn
        self.wall_fn = wall_fn
        self.rng = rng or random.Random()

        self.cache = RequestCache(self.state_dir / "cache", wall_fn)
        self.throttle = Throttle(self.config, monotonic_fn, sleep_fn, self.rng)
        self.budget = BudgetLedger(
            self.state_dir, run_budget_usd, self.config.global_ceiling_usd, wall_fn
        )
        self.killswitch = KillSwitch(self.state_dir, self.config.max_consecutive_errors, wall_fn)

    # -- single guarded fetch -------------------------------------------------
    def fetch(
        self,
        provider: str,
        endpoint: str,
        params: dict,
        fetch_fn: Callable[[dict], Any],
        *,
        ttl: Optional[float] = None,
        cost: Optional[float] = None,
    ) -> Any:
        self.killswitch.check()
        cfg = self.config.provider(provider)

        key = RequestCache.make_key(provider, endpoint, params)
        cached = self.cache.get(key)
        if cached is not None:
            return cached  # FREE: served from cache, no throttle, no charge, no network

        call_cost = cfg.cost_per_call_usd if cost is None else cost

        # Budget pre-check -- a breach is a hard stop for the whole loop.
        if not self.budget.can_afford(provider, call_cost):
            self.killswitch.trip(
                f"budget: '{provider}' call (${call_cost:.4f}) would breach "
                f"run/ceiling (run left ${self.budget.remaining_run():.4f}, "
                f"ceiling left ${self.budget.remaining_ceiling():.4f})"
            )
            self.killswitch.check()  # raises KillSwitchEngaged

        # Per-provider call cap for this run.
        if self.budget.calls_for(provider) >= cfg.max_calls_per_run:
            self.killswitch.trip(
                f"max_calls_per_run={cfg.max_calls_per_run} reached for '{provider}'"
            )
            self.killswitch.check()

        attempts = 0
        while True:
            self.killswitch.check()
            self.throttle.wait(provider)
            try:
                payload = fetch_fn(params)
            except RateLimited as e:
                attempts += 1
                backoff = e.retry_after if e.retry_after is not None else cfg.backoff_seconds * attempts
                self.throttle.penalize(provider, backoff)
                self.killswitch.record_error(ban_signal=True)
                if attempts > cfg.max_retries:
                    self.killswitch.trip(
                        f"rate-limited {attempts}x on '{provider}' -- backing all the way off"
                    )
                    self.killswitch.check()
                continue  # retry after the penalty (killswitch may already have tripped)
            except Exception:
                self.killswitch.record_error(ban_signal=False)
                raise

            # success
            self.budget.charge(provider, call_cost)
            self.cache.set(
                key, payload,
                meta={"provider": provider, "endpoint": endpoint, "params": params},
                ttl=ttl if ttl is not None else cfg.default_ttl_seconds,
            )
            self.killswitch.record_success()
            return payload

    # -- bounded pagination ---------------------------------------------------
    def run_query(
        self,
        provider: str,
        endpoint: str,
        page_params_fn: Callable[[int], dict],
        fetch_page_fn: Callable[[dict], Any],
        *,
        max_pages: Optional[int] = None,
        is_empty: Callable[[Any], bool] = lambda payload: not payload,
    ) -> list[Any]:
        """
        Page through a query under a HARD cap. Stops at the first of:
          - the provider's max_pages_per_query (or the caller's lower max_pages),
          - an empty page (per `is_empty`),
          - a killswitch trip.
        There is no code path here that can loop forever.
        """
        cfg = self.config.provider(provider)
        cap = cfg.max_pages_per_query if max_pages is None else min(max_pages, cfg.max_pages_per_query)
        pages: list[Any] = []
        for page in range(1, cap + 1):
            self.killswitch.check()
            payload = self.fetch(provider, endpoint, page_params_fn(page), fetch_page_fn)
            pages.append(payload)
            if is_empty(payload):
                break
        return pages

    # -- human-readable status ------------------------------------------------
    def status(self) -> dict:
        return {
            "killswitch_tripped": self.killswitch.is_tripped(),
            "killswitch_reason": self.killswitch.reason(),
            "cumulative_spend_usd": self.budget.cumulative_spend(),
            "ceiling_usd": self.config.global_ceiling_usd,
            "ceiling_remaining_usd": self.budget.remaining_ceiling(),
            "run_budget_usd": self.budget.run_budget,
            "run_spend_usd": self.budget.run_spend,
            "cache_hits": self.cache.hits,
            "cache_misses": self.cache.misses,
        }


# ---------------------------------------------------------------------------
# 7. SELF-TEST (fully offline, deterministic, no real sleeping)
# ---------------------------------------------------------------------------

class _FakeClock:
    """A virtual clock. sleep() advances time instead of blocking."""
    def __init__(self, start: float = 1000.0):
        self.t = start

    def monotonic(self) -> float:
        return self.t

    def wall(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0, seconds
        self.t += seconds


def _fetcher(tmp: Path, clock: _FakeClock, run_budget: float, config: Optional[RunConfig] = None) -> GuardedFetcher:
    return GuardedFetcher(
        config=config or default_config(),
        state_dir=tmp,
        run_budget_usd=run_budget,
        monotonic_fn=clock.monotonic,
        wall_fn=clock.wall,
        sleep_fn=clock.sleep,
        rng=random.Random(0),
    )


def _self_test() -> None:
    import tempfile

    cfg = default_config()

    # --- 1. CACHE: the same query is fetched once; the second call is a free hit.
    with tempfile.TemporaryDirectory() as d:
        clock = _FakeClock()
        gf = _fetcher(Path(d), clock, run_budget=10.0)
        calls = {"n": 0}

        def fake_fetch(params):
            calls["n"] += 1
            return {"echo": params, "served_call": calls["n"]}

        p1 = gf.fetch("metered_api", "search", {"q": "wood serving board"}, fake_fetch)
        p2 = gf.fetch("metered_api", "search", {"q": "wood serving board"}, fake_fetch)
        assert calls["n"] == 1, calls           # network touched exactly once
        assert p1 == p2                          # identical payload returned
        assert gf.cache.hits == 1 and gf.cache.misses == 1, gf.status()
        # charged exactly once (one real call): 1 x $0.01
        assert abs(gf.budget.run_spend - cfg.providers["metered_api"].cost_per_call_usd) < 1e-9

    # --- 2. THROTTLE: a second un-cached call waits at least min_interval.
    with tempfile.TemporaryDirectory() as d:
        clock = _FakeClock()
        gf = _fetcher(Path(d), clock, run_budget=10.0)
        mi = cfg.providers["metered_api"].min_interval_seconds
        gf.fetch("metered_api", "search", {"q": "a"}, lambda p: {"ok": 1})
        t_after_first = clock.t
        gf.fetch("metered_api", "search", {"q": "b"}, lambda p: {"ok": 1})
        assert (clock.t - t_after_first) >= mi, (clock.t, t_after_first, mi)

    # --- 3. BUDGET + KILL SWITCH: spend to the run budget, then halt and latch.
    with tempfile.TemporaryDirectory() as d:
        clock = _FakeClock()
        # run budget 0.025 at $0.01/call -> exactly 2 calls affordable, 3rd trips.
        gf = _fetcher(Path(d), clock, run_budget=0.025)
        gf.fetch("metered_api", "s", {"q": 1}, lambda p: {"ok": 1})
        gf.fetch("metered_api", "s", {"q": 2}, lambda p: {"ok": 1})
        try:
            gf.fetch("metered_api", "s", {"q": 3}, lambda p: {"ok": 1})
            raise AssertionError("expected KillSwitchEngaged on budget breach")
        except KillSwitchEngaged as e:
            assert "budget" in str(e).lower(), e
        assert gf.killswitch.is_tripped()
        # Latches across a restart: a brand-new fetcher on the same dir stays halted.
        gf2 = _fetcher(Path(d), _FakeClock(), run_budget=100.0)
        assert gf2.killswitch.is_tripped()
        try:
            gf2.fetch("metered_api", "s", {"q": 99}, lambda p: {"ok": 1})
            raise AssertionError("restart must not resume a tripped loop")
        except KillSwitchEngaged:
            pass

    # --- 4. PAGINATION CAP: a never-empty source still stops at the hard cap.
    with tempfile.TemporaryDirectory() as d:
        clock = _FakeClock()
        gf = _fetcher(Path(d), clock, run_budget=100.0)
        cap = cfg.providers["metered_api"].max_pages_per_query
        seen = {"pages": 0}

        def always_full(params):
            seen["pages"] += 1
            return {"rows": list(range(50)), "page": params["page"]}  # never "empty"

        pages = gf.run_query(
            "metered_api", "search",
            page_params_fn=lambda page: {"q": "x", "page": page},
            fetch_page_fn=always_full,
        )
        assert len(pages) == cap and seen["pages"] == cap, (len(pages), cap, seen)

    # --- 5. BAN DETECTION: repeated RateLimited backs off and finally trips.
    with tempfile.TemporaryDirectory() as d:
        clock = _FakeClock()
        gf = _fetcher(Path(d), clock, run_budget=100.0)

        def always_429(params):
            raise RateLimited("429 Too Many Requests", retry_after=5.0)

        try:
            gf.fetch("metered_api", "search", {"q": "banme"}, always_429)
            raise AssertionError("expected KillSwitchEngaged after retries exhausted")
        except KillSwitchEngaged as e:
            assert "rate-limited" in str(e).lower() or "consecutive" in str(e).lower(), e
        assert gf.killswitch.is_tripped()

    # --- 6. MANUAL KILL FILE: operator drops a KILL file -> everything halts.
    with tempfile.TemporaryDirectory() as d:
        clock = _FakeClock()
        gf = _fetcher(Path(d), clock, run_budget=100.0)
        (Path(d) / "KILL").write_text("stop", encoding="utf-8")
        try:
            gf.fetch("metered_api", "search", {"q": "anything"}, lambda p: {"ok": 1})
            raise AssertionError("manual KILL file must halt the loop")
        except KillSwitchEngaged as e:
            assert "manual" in str(e).lower(), e

    print("self-test passed: cache, throttle, budget+killswitch latch, "
          "pagination cap, ban-detection, and manual KILL all hold")


# ---------------------------------------------------------------------------
# 8. CLI (operational helpers only -- no ingestion)
# ---------------------------------------------------------------------------

def _main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="moat-engine safety runtime (no ingestion).")
    ap.add_argument("--self-test", action="store_true", help="run the offline safety self-test")
    ap.add_argument("--status", action="store_true", help="print cumulative budget + killswitch state")
    ap.add_argument("--reset-killswitch", action="store_true", help="deliberately clear a halt")
    ap.add_argument("--no-color", action="store_true", help="(accepted for consistency; output is plain)")
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    state_dir = default_state_dir()

    if args.reset_killswitch:
        ks = KillSwitch(state_dir, default_config().max_consecutive_errors, time.time)
        was = ks.is_tripped()
        ks.reset()
        print(f"killswitch reset (was tripped: {was}) at {state_dir}")
        return 0

    if args.status:
        gf = GuardedFetcher(state_dir=state_dir, run_budget_usd=0.0)
        st = gf.status()
        print(json.dumps(st, indent=2, default=str))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
