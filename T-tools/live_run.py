print(">>> [DEBUG] Script started", flush=True)  # VISIBILITY LINE 1 — must be first

# ---------------------------------------------------------------------------
# stdout encoding fix — Windows PowerShell / VS Code terminal safe
# ---------------------------------------------------------------------------
import sys
import io

print(">>> [DEBUG] sys imported", flush=True)

try:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stdout.reconfigure(line_buffering=True)
        print(">>> [DEBUG] stdout rewrapped to UTF-8", flush=True)
    else:
        print(">>> [DEBUG] stdout has no .buffer — skipping rewrap (IDLE/redirect mode)", flush=True)
except Exception as _stdout_err:
    print(f">>> [DEBUG] stdout rewrap FAILED: {_stdout_err}", flush=True)

# ---------------------------------------------------------------------------
# Docstring (after prints — docstrings before code are fine but not first here)
# ---------------------------------------------------------------------------
"""
KritiKaal Leads Hunter — Autonomous Discovery Engine  (Sprint 7 Advanced Discovery)
File: T-tools/live_run.py

Multi-Agent Market Exhaustion Model:
  Runs seven discovery agents sequentially. Each agent targets a distinct
  discovery surface. All agents share one `known_domains` set so no domain
  is classified twice across agents.

  AGENT 1 — LeatherDiscoveryAgent    Core leather vertical (4 queries)
  AGENT 2 — LateralIndustryAgent     5 lateral B2B packs (~39 queries)
  AGENT 3 — ShopifyFootprintAgent    Technology fingerprint (10 queries)
  AGENT 4 — CompetitorLookalikeAgent Two-phase competitor client mining
  AGENT 5 — ProcurementAgent         Two-phase gov procurement portal (7A)
  AGENT 6 — SocialOnlyAgent          Two-phase Facebook page resolver (7B)
  AGENT 7 — PurchaseIntentAgent      Active sourcing / RFQ signals (7C)

  Per-agent Circuit Breaker: MAX_ITERATIONS_PER_RUN batches per agent.
  Per-agent Exhaustion Check: < EXHAUSTION_THRESHOLD new domains → done.
  Cross-agent dedup: known_domains shared — domain processed once globally.

  Phase 1  — Discovery (all 7 agents)
  Phase 2  — NLP Classification + DB upsert
  Phase 2.5— Instagram Signal enrichment (auto-upgrade B/UNCLASSIFIED → A)
  Phase 3  — O-Output Export (3-tab Excel)

Usage:
    cd T-tools && python live_run.py
"""

# ---------------------------------------------------------------------------
# Stdlib imports
# ---------------------------------------------------------------------------
print(">>> [DEBUG] Loading stdlib imports ...", flush=True)

import asyncio
import json
import os
import socket
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

print(">>> [DEBUG] stdlib imports OK", flush=True)

# ---------------------------------------------------------------------------
# Socket-level DNS timeout (critical for preventing hangs on slow DNS)
# ---------------------------------------------------------------------------
# Set default socket timeout to 15s — covers DNS resolution + initial connection.
# This prevents the OS-level socket from hanging indefinitely on unresponsive hosts.
socket.setdefaulttimeout(15.0)
print(">>> [DEBUG] Socket default timeout set to 15s", flush=True)

# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------
print(">>> [DEBUG] Loading dotenv ...", flush=True)

try:
    from dotenv import load_dotenv
    _HERE = Path(__file__).resolve().parent
    _ENV_PATH = _HERE / ".env"
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH)
        print(f">>> [DEBUG] .env found and loaded: {_ENV_PATH}", flush=True)
    else:
        # Try parent directory
        _ENV_PARENT = _HERE.parent / ".env"
        if _ENV_PARENT.exists():
            load_dotenv(dotenv_path=_ENV_PARENT)
            print(f">>> [DEBUG] .env found in parent: {_ENV_PARENT}", flush=True)
        else:
            load_dotenv()  # fallback: search CWD
            print(f">>> [DEBUG] .env not found at {_ENV_PATH} or {_ENV_PARENT} — tried CWD fallback", flush=True)
except Exception as _env_err:
    print(f">>> [DEBUG] dotenv FAILED: {_env_err}", flush=True)

# ---------------------------------------------------------------------------
# Environment key check (masked)
# ---------------------------------------------------------------------------
_openai_raw  = os.environ.get("OPENAI_API_KEY",  "")
_serper_raw  = os.environ.get("SERPER_API_KEY",  "")

def _mask(key: str) -> str:
    if not key:
        return "NOT SET"
    return key[:6] + "..." + key[-3:] if len(key) > 9 else "SET (short)"

print(f">>> [DEBUG] OPENAI_API_KEY  : {_mask(_openai_raw)}", flush=True)
print(f">>> [DEBUG] SERPER_API_KEY  : {_mask(_serper_raw)}", flush=True)

# ---------------------------------------------------------------------------
# sys.path injection (must happen before local imports)
# ---------------------------------------------------------------------------
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
print(f">>> [DEBUG] sys.path[0] = {sys.path[0]}", flush=True)

# ---------------------------------------------------------------------------
# Third-party: aiohttp
# ---------------------------------------------------------------------------
print(">>> [DEBUG] Importing aiohttp ...", flush=True)
try:
    import aiohttp
    print(">>> [DEBUG] aiohttp OK", flush=True)
except ImportError as _e:
    print(f">>> [FATAL] aiohttp not installed: {_e}", flush=True)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
print(">>> [DEBUG] Importing db_init ...", flush=True)
from db_init import (
    get_connection,
    initialize_schema,
    upsert_lead,
    insert_classification,
    flag_stale_leads,
    load_blacklist,
    add_to_blacklist,
    update_contact_fields,
    get_recent_feedback,
)
print(">>> [DEBUG] db_init OK", flush=True)

print(">>> [DEBUG] Importing exporter ...", flush=True)
from exporter import export_leads, DEFAULT_EXPORT_PATH
print(">>> [DEBUG] exporter OK", flush=True)

print(">>> [DEBUG] Importing scrapers ...", flush=True)
from scrapers import (
    AgentResult,
    SocialFootprintAgent,
    _apply_universal_query_filters,
    is_aggregator_domain,
    is_directory_page,
    enrich_contact_pages,
)
print(">>> [DEBUG] scrapers OK", flush=True)

print(">>> [DEBUG] Importing nlp_classifier ...", flush=True)
from nlp_classifier import (
    TokenUsage,
    classify_lead_full,
    build_feedback_context,
    build_openai_client,
)
print(">>> [DEBUG] nlp_classifier OK", flush=True)

print(">>> [DEBUG] Importing lateral_industry_agent ...", flush=True)
from lateral_industry_agent import LateralIndustryAgent
print(">>> [DEBUG] lateral_industry_agent OK", flush=True)

print(">>> [DEBUG] Importing shopify_agent ...", flush=True)
from shopify_agent import ShopifyFootprintAgent
print(">>> [DEBUG] shopify_agent OK", flush=True)

print(">>> [DEBUG] Importing competitor_agent ...", flush=True)
from competitor_agent import CompetitorLookalikeAgent
print(">>> [DEBUG] competitor_agent OK", flush=True)

print(">>> [DEBUG] Importing procurement_agent ...", flush=True)
from procurement_agent import ProcurementAgent
print(">>> [DEBUG] procurement_agent OK", flush=True)

print(">>> [DEBUG] Importing social_agent ...", flush=True)
from social_agent import SocialOnlyAgent
print(">>> [DEBUG] social_agent OK", flush=True)

print(">>> [DEBUG] Importing purchase_intent_agent ...", flush=True)
from purchase_intent_agent import PurchaseIntentAgent
print(">>> [DEBUG] purchase_intent_agent OK", flush=True)

print(">>> [DEBUG] All imports complete.", flush=True)

# ---------------------------------------------------------------------------
# Run configuration
# ---------------------------------------------------------------------------

MAX_ITERATIONS_PER_RUN: int   = 5      # Circuit Breaker — max Serper batches per agent
EXHAUSTION_THRESHOLD:   float = 0.10   # < 10% new domains → this agent is exhausted
IG_MIN_SCORE:           int   = 2      # min Instagram signals to auto-upgrade lead
MAX_NEW_LEADS_PER_RUN:  int   = 0      # 0 = unlimited; set via agent_overrides.json global

# ---------------------------------------------------------------------------
# HTTP / NLP timeout constants  (Sprint 10.5 — Silent Freeze fix)
# ---------------------------------------------------------------------------
# All aiohttp sessions use _HTTP_TIMEOUT so a single unresponsive .co.il host
# can never hang the pipeline indefinitely.
# NLP_TIMEOUT gives OpenAI calls a hard 45-second ceiling — enough for any
# reasonable completion, but prevents a stalled API connection from freezing
# the classification loop.
_HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=10)
_NLP_TIMEOUT_S: float = 45.0

# ---------------------------------------------------------------------------
# Competitor Lookalike Agent — seed domains
# Add competitor domains here to mine their client / testimonial pages.
# The agent tries known client-page slugs (/לקוחות, /clients, etc.) on each
# domain and extracts company links and Hebrew בע"מ entity names.
# ---------------------------------------------------------------------------
COMPETITOR_SEED_DOMAINS: list[str] = [
    "shugon.co.il",
]

_MODEL      = "gpt-4o-mini"
_DB_PATH    = str(_HERE / "leads.db")
_MEMORY_DIR = _HERE.parent / "M-memory"

# ---------------------------------------------------------------------------
# Agent 1 — Core Leather Discovery
# ---------------------------------------------------------------------------

class LeatherDiscoveryAgent(SocialFootprintAgent):
    """
    Core KritiKaal leather vertical — importers, OEM brands, wholesalers.
    Four focused queries restricted to site:.co.il.
    """
    _EXCLUDED_CO_IL_SITES: list[str] = [
        "d.co.il", "b144.co.il", "easy.co.il", "bizportal.co.il",
        "all.co.il", "hotfrog.co.il", "eniro.co.il",
        "starofservice.co.il", "fixmasters.co.il", "homely.co.il",
        "yad2.co.il", "dunsguide.co.il", "duns100.co.il",
        "ynet.co.il", "walla.co.il", "mako.co.il", "calcalist.co.il",
        "globes.co.il", "haaretz.co.il", "israelhayom.co.il",
        "nevo.co.il", "zap.co.il", "bezeqint.net", "yellow.co.il",
    ]

    async def build_queries(self) -> list[str]:
        excl   = " ".join(f"-site:{s}" for s in self._EXCLUDED_CO_IL_SITES)
        suffix = f"site:.co.il -filetype:pdf {excl}"
        return [
            f"יבואן מוצרי עור ארנקים ישראל {suffix}",
            f"סיטונאי עורות ומוצרי עור ישראל {suffix}",
            f"מותג עור ישראלי קולקציה {suffix}",
            f"אביזרי אופנה עור ישראל {suffix}",
        ]


# ---------------------------------------------------------------------------
# Agent registry — defines execution order and display names
# ---------------------------------------------------------------------------

AGENT_REGISTRY: list[dict] = [
    {"name": "Core Leather",         "cls": LeatherDiscoveryAgent},
    {"name": "Lateral Industries",   "cls": LateralIndustryAgent},
    {"name": "Shopify Footprint",    "cls": ShopifyFootprintAgent},
    {
        "name":   "Competitor Lookalike",
        "cls":    CompetitorLookalikeAgent,
        # seed_domains is forwarded to CompetitorLookalikeAgent.__init__()
        # so the seed list lives here in live_run.py, not in the agent file.
        "kwargs": {"seed_domains": COMPETITOR_SEED_DOMAINS},
    },
    # Sprint 7 — Advanced Discovery Agents
    {"name": "Gov Procurement",      "cls": ProcurementAgent},
    {"name": "Social-Only",          "cls": SocialOnlyAgent},
    {"name": "Purchase Intent",      "cls": PurchaseIntentAgent},
]

# ---------------------------------------------------------------------------
# Market Exhaustion helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Agent Overrides — optional operator-controlled tuning
# ---------------------------------------------------------------------------

_OVERRIDES_PATH = _HERE / "agent_overrides.json"

def _load_agent_overrides() -> dict:
    """
    Load T-tools/agent_overrides.json if it exists. Returns an empty dict
    (all defaults) if the file is absent or malformed — the pipeline runs
    identically to pre-Sprint 7.5 behaviour when no overrides file is present.

    Schema:
      {
        "agents": {
          "<agent name>": {
            "enabled":        bool   (default true)
            "max_iterations": int    (default MAX_ITERATIONS_PER_RUN)
            "extra_queries":  [str]  (additional raw Serper query strings)
          }
        },
        "global": {
          "max_iterations_per_run": int   (default MAX_ITERATIONS_PER_RUN)
          "exhaustion_threshold":   float (default EXHAUSTION_THRESHOLD)
        }
      }
    All keys are optional. Unknown keys are silently ignored.
    """
    if not _OVERRIDES_PATH.exists():
        return {}
    try:
        raw = _OVERRIDES_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            print("  [Overrides] agent_overrides.json is not a JSON object — ignoring.")
            return {}
        print(f"  [Overrides] Loaded: {_OVERRIDES_PATH}")
        return data
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [Overrides] Could not parse agent_overrides.json ({exc}) — ignoring.")
        return {}


def _apply_agent_overrides(
    registry: list[dict],
    overrides: dict,
) -> tuple[list[dict], int, float, int]:
    """
    Apply agent_overrides.json to AGENT_REGISTRY and global run params.

    Returns:
        filtered_registry    : copy of registry with disabled agents removed,
                               per-agent _max_iterations and _extra_queries injected.
        max_iterations       : effective global MAX_ITERATIONS_PER_RUN.
        exhaustion           : effective global EXHAUSTION_THRESHOLD.
        max_new_leads_per_run: 0 = unlimited; cap on new domains classified per run.
    """
    global_cfg     = overrides.get("global", {})
    agent_cfg_map  = overrides.get("agents", {})

    eff_max_iter      = int(global_cfg.get("max_iterations_per_run", MAX_ITERATIONS_PER_RUN))
    eff_exhaustion    = float(global_cfg.get("exhaustion_threshold",  EXHAUSTION_THRESHOLD))
    eff_max_new_leads = int(global_cfg.get("max_new_leads_per_run",   MAX_NEW_LEADS_PER_RUN))

    filtered = []
    for cfg in registry:
        name      = cfg["name"]
        acfg      = agent_cfg_map.get(name, {})
        enabled   = bool(acfg.get("enabled", True))

        if not enabled:
            print(f"  [Overrides] {name}: DISABLED by agent_overrides.json")
            continue

        new_cfg = dict(cfg)   # shallow copy — don't mutate the module-level list
        new_cfg["_max_iterations"] = int(
            acfg.get("max_iterations", eff_max_iter)
        )
        new_cfg["_extra_queries"]  = list(acfg.get("extra_queries", []))

        if new_cfg["_max_iterations"] != MAX_ITERATIONS_PER_RUN:
            print(f"  [Overrides] {name}: max_iterations → {new_cfg['_max_iterations']}")
        if new_cfg["_extra_queries"]:
            print(f"  [Overrides] {name}: +{len(new_cfg['_extra_queries'])} extra_queries")

        filtered.append(new_cfg)

    return filtered, eff_max_iter, eff_exhaustion, eff_max_new_leads


def _get_known_domains(db_path: str) -> set[str]:
    """Return set of all domains already in leads.db. Called once at startup."""
    conn = get_connection(db_path)
    rows = conn.execute("SELECT domain FROM leads").fetchall()
    conn.close()
    return {row[0] for row in rows if row[0]}


def _is_market_exhausted(
    new_count: int,
    total_count: int,
    threshold: float = EXHAUSTION_THRESHOLD,
) -> bool:
    """True if new domain ratio < threshold, or nothing returned."""
    if total_count == 0:
        return True
    return (new_count / total_count) < threshold


# ---------------------------------------------------------------------------
# Per-result NLP processing
# ---------------------------------------------------------------------------

async def process_agent_result(
    result: AgentResult,
    openai_client,
    conn,
    run_totals: dict,
    feedback_context: str = "",
) -> dict:
    """
    Run NLP classification + DB upsert for one AgentResult.
    Confidence threshold and OEM override are applied inside classify_lead_full().
    feedback_context: optional Calibration Block from build_feedback_context(),
    loaded once per pipeline run and forwarded to every classify_lead_full() call.
    Returns a record dict for console output and M-memory log.
    """
    t0 = time.monotonic()
    record = {
        "entity_name":       result.entity_name,
        "domain":            result.domain,
        "vector":            result.vector,
        "status":            None,
        "confidence":        None,
        "whatsapp":          result.whatsapp,
        "company_id":        result.company_id,
        "model_version":     None,
        "lead_id":           None,
        "tokens_prompt":     0,
        "tokens_completion": 0,
        "error":             None,
        "duration_s":        0.0,
    }

    try:
        print(f"    [NLP-A] raw_text check ({len(result.raw_text or '')} chars)", flush=True)
        if not result.raw_text:
            record["error"] = "EMPTY_TEXT"
            return record

        print("    [NLP-B] aggregator check", flush=True)
        if is_aggregator_domain(result.domain):
            record["error"] = "BLOCKED_L1_DOMAIN"
            return record

        print("    [NLP-C] directory-page check", flush=True)
        if is_directory_page(result.raw_text):
            record["error"] = "BLOCKED_L2_DIRECTORY_PAGE"
            return record

        # Sprint 10.5: hard timeout on GPT call — prevents a stalled API
        # connection from hanging the classification loop indefinitely.
        print("    [NLP-D] entering asyncio.wait_for / classify_lead_full", flush=True)
        _nlp_t0 = time.monotonic()
        try:
            nlp_status, confidence, signals, model_ver, usage = await asyncio.wait_for(
                classify_lead_full(
                    result.raw_text, client=openai_client, model=_MODEL,
                    feedback_context=feedback_context,
                ),
                timeout=_NLP_TIMEOUT_S,
            )
            print(f"    [NLP-E] classify done in {time.monotonic()-_nlp_t0:.1f}s → {nlp_status} ({confidence:.0%})", flush=True)
        except asyncio.TimeoutError:
            print(f"    [NLP-E] classify TIMEOUT after {time.monotonic()-_nlp_t0:.1f}s", flush=True)
            record["error"] = f"NLP_TIMEOUT (>{_NLP_TIMEOUT_S:.0f}s)"
            return record
        record.update({
            "status":            nlp_status,
            "confidence":        confidence,
            "model_version":     model_ver,
            "tokens_prompt":     usage.prompt_tokens,
            "tokens_completion": usage.completion_tokens,
        })
        run_totals["prompt_tokens"]     += usage.prompt_tokens
        run_totals["completion_tokens"] += usage.completion_tokens

        # Auto-blacklist: LLM gave a high-confidence DISQUALIFIED_C verdict
        # based on real page content (not a tier1 technical rejection).
        # These domains are structurally irrelevant — no future run should
        # spend Serper quota, V3 fetch budget, or LLM tokens on them.
        if (
            nlp_status == "DISQUALIFIED_C"
            and confidence >= 0.90
            and model_ver != "tier1"
        ):
            add_to_blacklist(conn, result.domain, reason="AUTO_HIGH_CONF_DISQUALIFY")

        lead_id = upsert_lead(
            conn,
            lead_data={
                "entity_name":      result.entity_name,
                "domain":           result.domain,
                "whatsapp":         result.whatsapp,
                "company_id":       result.company_id,
                "physical_address": result.physical_address,
                "status":           nlp_status,
                "legal_flag":       "PENDING_LEGAL" if nlp_status == "PENDING_LEGAL" else None,
            },
            vector=result.vector,
            source_url=result.source_url,
            raw_snippet=result.raw_text[:500],
        )
        record["lead_id"] = lead_id
        insert_classification(
            conn,
            lead_id=lead_id,
            status=nlp_status,
            confidence=confidence,
            signals=signals,
            model_version=model_ver,
        )

    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        record["duration_s"] = round(time.monotonic() - t0, 2)

    return record


# ---------------------------------------------------------------------------
# Phase 2.5 — Instagram Signal enrichment
# ---------------------------------------------------------------------------

async def _run_instagram_phase(
    records: list[dict],
    conn,
    serper_key: str,
    run_totals: dict,
) -> int:
    """
    Auto-upgrade UNCLASSIFIED/QUALIFIED_B leads that show strong IG signals.
    Returns number of leads upgraded to QUALIFIED_A.
    """
    try:
        from instagram_agent import InstagramSignalAgent
    except ImportError:
        print("  [Phase 2.5] instagram_agent.py not found — skipping.")
        return 0

    candidates = [
        r for r in records
        if r.get("status") in ("UNCLASSIFIED", "QUALIFIED_B_PENDING_VERIFY")
        and r.get("lead_id") is not None
    ]

    if not candidates:
        print("  [Phase 2.5] No upgrade candidates.")
        return 0

    print(f"\n  Phase 2.5 — Instagram Signal enrichment ({len(candidates)} candidate(s)) ...", flush=True)
    agent    = InstagramSignalAgent(api_key=serper_key, proxy_pool=[None])
    upgraded = 0

    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        for rec in candidates:
            score, ig_signals = await agent.enrich_lead(
                session=session,
                entity_name=rec["entity_name"],
                domain=rec["domain"],
            )
            if score >= IG_MIN_SCORE:
                conn.execute(
                    "UPDATE leads SET status='QUALIFIED_A', "
                    "last_updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (rec["lead_id"],),
                )
                insert_classification(
                    conn, lead_id=rec["lead_id"], status="QUALIFIED_A",
                    confidence=0.75, signals=ig_signals,
                    model_version="ig_signal_v1",
                )
                conn.commit()
                rec["status"] = "QUALIFIED_A"
                upgraded += 1
                print(f"  UP UPGRADED: {rec['domain']}  (IG score={score})")
            else:
                print(f"  x {rec['domain']}  (IG score={score})")

    return upgraded


# ---------------------------------------------------------------------------
# Phase 2A — Multi-Page Contact Enrichment
# ---------------------------------------------------------------------------

async def _run_contact_enrichment_phase(
    records: list[dict],
    conn,
) -> int:
    """
    Phase 2A — Multi-Page Contact Enrichment (V3.5).

    For every QUALIFIED_A or QUALIFIED_B_PENDING_VERIFY lead that still has
    no WhatsApp number after classification, probe up to 3 contact/about
    pages per domain looking for a phone number via regex.

    No LLM cost — pure HTML fetch + phone regex.  Jitter is applied between
    each page fetch (Iron Principle 5b) inside enrich_contact_pages().

    COALESCE guard in update_contact_fields() ensures we never overwrite a
    phone already present — safe to run repeatedly.

    Returns the count of leads that received a new phone number this pass.
    """
    candidates = [
        r for r in records
        if r.get("status") in ("QUALIFIED_A", "QUALIFIED_B_PENDING_VERIFY")
        and not r.get("whatsapp")
        and r.get("lead_id") is not None
    ]

    if not candidates:
        print("  [Phase 2A] No contactless qualified leads -- skipping.")
        return 0

    print(f"\n  Phase 2A -- Contact enrichment ({len(candidates)} lead(s) without phone) ...", flush=True)
    enriched_count = 0

    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        for rec in candidates:
            phone = await enrich_contact_pages(session, rec["domain"])
            if phone:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    update_contact_fields(conn, rec["lead_id"], phone)
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                rec["whatsapp"] = phone
                enriched_count += 1
                print(f"  + {rec['domain']:<40}  phone={phone}")
            else:
                print(f"  - {rec['domain']:<40}  no phone found")

    print(f"  [Phase 2A] Enriched {enriched_count}/{len(candidates)} lead(s).")
    return enriched_count


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def _print_token_report(records: list[dict], model: str) -> None:
    p = sum(r["tokens_prompt"]     for r in records)
    c = sum(r["tokens_completion"] for r in records)
    u = TokenUsage(p, c)
    print("\n" + "=" * 60, flush=True)
    print("  OPENAI TOKEN USAGE REPORT", flush=True)
    print("=" * 60, flush=True)
    print(f"  Model    : {model}", flush=True)
    print(f"  Prompt   : {p:,}    Completion: {c:,}    Total: {u.total_tokens:,}", flush=True)
    print(f"  Cost     : ${u.cost_usd(model):.6f} USD", flush=True)
    print("=" * 60, flush=True)


def _print_lead_result(idx: int, total: int, r: dict) -> None:
    status = r.get("status") or "N/A"
    conf   = r.get("confidence")
    conf_s = f"{conf:.2f}" if conf is not None else "--"
    lead   = f"lead_id={r['lead_id']}" if r["lead_id"] else "NOT_SAVED"
    err    = f"  ! {r['error']}" if r["error"] else ""
    print(f"\n  [{idx}/{total}] {r.get('entity_name','')[:60]}  ({r['domain']})", flush=True)
    print(f"    status={status}  conf={conf_s}  via={r.get('model_version','--')}"
          f"  wa={r.get('whatsapp') or '--'}  {lead}  ({r['duration_s']}s){err}", flush=True)


def _save_run_log(
    results: list[dict],
    run_totals: dict,
    elapsed: float,
    agent_summaries: list[dict],
) -> None:
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _MEMORY_DIR / "run_history.json"

    # Sprint 11A — Unit economics
    prompt_tok  = run_totals.get("prompt_tokens", 0)
    comp_tok    = run_totals.get("completion_tokens", 0)
    serper_calls = run_totals.get("serper_calls", 0)
    serper_cost  = serper_calls * 0.001                   # $1.00 / 1K calls
    openai_cost  = (prompt_tok / 1_000_000 * 0.15) + (comp_tok / 1_000_000 * 0.60)
    total_cost   = serper_cost + openai_cost
    qual_a_count = sum(1 for r in results if r.get("status") == "QUALIFIED_A")
    cost_per_a   = round(total_cost / qual_a_count, 4) if qual_a_count else 0.0

    entry = {
        "run_at":              datetime.now(timezone.utc).isoformat(),
        "protocol":            "multi_agent_lateral_v3",
        "agent_summaries":     agent_summaries,
        "targets_processed":   len(results),
        "leads_upserted":      sum(1 for r in results if r["lead_id"] is not None),
        "errors":              sum(1 for r in results if r["error"]),
        "total_prompt_tok":    prompt_tok,
        "total_comp_tok":      comp_tok,
        "total_elapsed_s":     round(elapsed, 2),
        # Sprint 11A — cost fields
        "serper_calls":        serper_calls,
        "serper_cost_usd":     round(serper_cost, 4),
        "openai_cost_usd":     round(openai_cost, 4),
        "total_cost_usd":      round(total_cost, 4),
        "qual_a_new":          qual_a_count,
        "cost_per_qual_a_usd": cost_per_a,
        "results":             results,
    }
    existing: list = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing.append(entry)
    log_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n  Run log -> {log_path}")


# ---------------------------------------------------------------------------
# Single-agent Market Exhaustion loop
# ---------------------------------------------------------------------------

async def _run_agent_loop(
    agent_cfg: dict,
    serper_key: str,
    openai_client,
    conn,
    skip_domains: set[str],
    run_totals: dict,
    all_records: list[dict],
    feedback_context: str = "",
    exhaustion_threshold: float = EXHAUSTION_THRESHOLD,
    max_new_leads: int = 0,
) -> dict:
    """
    Run one agent through its Market Exhaustion loop.

    Per-agent max_iterations and extra_queries are read from agent_cfg
    keys _max_iterations / _extra_queries (injected by _apply_agent_overrides()).
    Fall back to module-level MAX_ITERATIONS_PER_RUN / [] if absent.

    skip_domains is the combined gate of known_domains (leads already in DB)
    AND blacklisted_domains (permanently disqualified). Any domain in this set
    is skipped before V3 enrichment or NLP — zero Serper re-spend, zero API cost.

    feedback_context: Calibration Block from build_feedback_context(), loaded
    once per pipeline run and forwarded to every classify_lead_full() call.

    Mutates skip_domains and all_records in place.
    Returns a summary dict for the run log.
    """
    agent_name      = agent_cfg["name"]
    extra_kwargs    = agent_cfg.get("kwargs", {})
    max_iterations  = agent_cfg.get("_max_iterations", MAX_ITERATIONS_PER_RUN)
    extra_queries   = agent_cfg.get("_extra_queries", [])
    agent           = agent_cfg["cls"](
        api_key=serper_key, proxy_pool=[None], **extra_kwargs
    )
    stop_reason      = "circuit_breaker"
    total_new        = 0
    total_raw        = 0
    total_known      = 0   # domains blocked by skip gate (corroborated, not re-processed)
    iterations_used  = 0

    print(f"\n{'=' * 60}", flush=True)
    print(f"  AGENT: {agent_name}", flush=True)
    print(f"{'=' * 60}", flush=True)

    for iteration in range(1, max_iterations + 1):
        iterations_used = iteration
        print(f"\n  -- Iteration {iteration}/{max_iterations} --", flush=True)

        # Sprint 10.5: _HTTP_TIMEOUT prevents any single slow host from blocking
        # the session indefinitely (30s total, 10s connect).
        # force_close=True: never pool connections — each response immediately
        # closes its socket.  This prevents stalled/cancelled V3 connections
        # from poisoning the pool and causing session.close() to hang.
        # enable_cleanup_closed=True: background task actively purges any
        # already-closed sockets that aiohttp hasn't yet removed from the pool.
        print(f"  [SESSION] opening fresh session (iteration {iteration})", flush=True)
        async with aiohttp.ClientSession(
            timeout=_HTTP_TIMEOUT,
            connector=aiohttp.TCPConnector(
                force_close=True,
                enable_cleanup_closed=True,
            ),
        ) as session:
            raw_results: list[AgentResult] = await agent.run(session)

            # Extra queries from agent_overrides.json — run through the same
            # SocialFootprintAgent Serper pipeline as the agent's own queries.
            if extra_queries and iteration == 1:
                print(f"  [Overrides] Running {len(extra_queries)} extra_queries ...", flush=True)
                for eq in extra_queries:
                    try:
                        filtered_q = _apply_universal_query_filters(eq)
                        raw_eq = await agent._safe_request(session, filtered_q)
                        if raw_eq:
                            extra_results = await agent.parse_response(raw_eq, filtered_q)
                            enriched = await asyncio.gather(
                                *[agent._enrich_with_direct_html(session, r)
                                  for r in extra_results],
                                return_exceptions=True,
                            )
                            for item in enriched:
                                if isinstance(item, AgentResult):
                                    raw_results.append(item)
                    except Exception as _eq_err:
                        print(f"  [Overrides] extra_query failed: {_eq_err}", flush=True)

            # ── session.close() fires on 'async with' __aexit__ immediately below ──
            print(f"  [SESSION] work done — {len(raw_results)} raw results — closing session ...", flush=True)

        # session.__aexit__ (session.close()) completed to reach here
        print("  [SESSION] session closed OK", flush=True)

        # Tally Serper API calls: each Serper request returns ~10 results.
        # ceil(raw / 10) gives a tight estimate without modifying every agent.
        import math
        run_totals["serper_calls"] = run_totals.get("serper_calls", 0) + max(1, math.ceil(len(raw_results) / 10))

        total_raw += len(raw_results)
        new_unique:    list[AgentResult] = []
        blocked = 0
        iter_known = 0

        for r in raw_results:
            if not r.domain or r.domain.startswith("maps::"):
                continue
            if is_aggregator_domain(r.domain):
                blocked += 1
                continue
            if r.domain in skip_domains:        # known in DB or blacklisted — skip NLP
                iter_known += 1
                continue
            skip_domains.add(r.domain)          # intra-run dedup: prevent cross-agent reprocessing
            new_unique.append(r)

        total_known += iter_known
        print(f"  Raw={len(raw_results)}  Blocked={blocked}  Known={iter_known}  New={len(new_unique)}", flush=True)
        print("  [GAP-1] total_new accumulate", flush=True)
        total_new += len(new_unique)

        print("  [GAP-2] exhaustion check", flush=True)
        if _is_market_exhausted(len(new_unique), len(raw_results), exhaustion_threshold):
            pct = f"{len(new_unique)/len(raw_results):.0%}" if raw_results else "0%"
            print(f"  [EXHAUSTED] {agent_name} ({pct} new < {exhaustion_threshold:.0%})", flush=True)
            stop_reason = "market_exhausted"
            break

        print("  [GAP-3] empty-unique check", flush=True)
        if not new_unique:
            stop_reason = "market_exhausted"
            break

        print("  [GAP-4] cap check", flush=True)
        # Sprint 10.5: max_new_leads_per_run cap — operator can limit how many
        # new domains are classified per run to control cost and run time.
        if max_new_leads > 0:
            remaining = max_new_leads - len(all_records)
            if remaining <= 0:
                print(f"  [CAP] max_new_leads_per_run={max_new_leads} reached — stopping agent.", flush=True)
                stop_reason = "max_new_leads_cap"
                break
            if len(new_unique) > remaining:
                print(f"  [CAP] Trimming {len(new_unique)} → {remaining} domain(s) (cap={max_new_leads}).", flush=True)
                new_unique = new_unique[:remaining]

        print(f"  [GAP-5] printing {len(new_unique)} entity names", flush=True)
        for r in new_unique:
            print(f"    + {r.entity_name[:55]}  ({r.domain})", flush=True)

        print("  [GAP-6] about to enter NLP classify loop", flush=True)
        print(f"\n  Classifying {len(new_unique)} domain(s) ...", flush=True)
        print("  [GAP-7] NLP loop entered — first domain in 1 line", flush=True)
        batch_start = len(all_records)
        for idx, result in enumerate(new_unique, start=1):
            # Sprint 10.5: per-domain progress line — always visible even during
            # a slow GPT call so the terminal never looks frozen.
            print(f"  [NLP {idx}/{len(new_unique)}] {result.domain} ...", flush=True)
            # Sprint 11B: structured progress token for dashboard progress bar
            print(f"PROGRESS:{agent_name}:{iteration}:{idx}:{len(new_unique)}", flush=True)

            # CRITICAL DEBUG: Record exact timestamp before classification to catch hangs
            _t_start = time.monotonic()
            _domain_debug = result.domain

            try:
                rec = await process_agent_result(
                    result, openai_client, conn, run_totals,
                    feedback_context=feedback_context,
                )
                _elapsed = time.monotonic() - _t_start
                if _elapsed > 10:  # Warn if domain takes > 10s (usually 2-5s)
                    print(f"    ⚠️  SLOW: {_domain_debug} took {_elapsed:.1f}s", flush=True)
            except asyncio.TimeoutError:
                print(f"    ❌ TIMEOUT: {_domain_debug} exceeded 45s NLP limit — skipping", flush=True)
                rec = {
                    "entity_name": result.entity_name,
                    "domain": result.domain,
                    "vector": result.vector,
                    "status": None,
                    "confidence": None,
                    "whatsapp": result.whatsapp,
                    "company_id": result.company_id,
                    "model_version": None,
                    "lead_id": None,
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "error": "CLASSIFICATION_TIMEOUT (45s)",
                    "duration_s": 45.0,
                }
            except Exception as e:
                print(f"    ❌ ERROR: {_domain_debug} — {type(e).__name__}: {str(e)[:80]}", flush=True)
                rec = {
                    "entity_name": result.entity_name,
                    "domain": result.domain,
                    "vector": result.vector,
                    "status": None,
                    "confidence": None,
                    "whatsapp": result.whatsapp,
                    "company_id": result.company_id,
                    "model_version": None,
                    "lead_id": None,
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "error": f"{type(e).__name__}: {str(e)[:80]}",
                    "duration_s": time.monotonic() - _t_start,
                }

            all_records.append(rec)
            _print_lead_result(batch_start + idx, batch_start + len(new_unique), rec)

        conn.commit()

    # Write dedup counters back to the agent's run log so they appear in
    # run_summary.json alongside HTTP-level stats.
    agent._run_log.domains_new           = total_new
    agent._run_log.domains_already_known = total_known
    agent._flush_run_log()   # re-flush with updated counters

    return {
        "agent":                agent_name,
        "iterations":           iterations_used,
        "stop_reason":          stop_reason,
        "new_domains":          total_new,
        "already_known":        total_known,
        "raw_results":          total_raw,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    # ── Load operator overrides (agent_overrides.json) ────────────────────────
    # Must happen before the header print so we can report effective settings.
    overrides = _load_agent_overrides()
    active_registry, eff_max_iter, eff_exhaustion, eff_max_new_leads = _apply_agent_overrides(
        AGENT_REGISTRY, overrides
    )

    print("=" * 60, flush=True)
    print("  KritiKaal Leads Hunter -- Phase 1 Lateral Expansion", flush=True)
    print(f"  Agents          : {', '.join(a['name'] for a in active_registry)}", flush=True)
    print(f"  Max iterations  : {eff_max_iter} per agent", flush=True)
    print(f"  Exhaustion      : {eff_exhaustion:.0%} new-domain threshold", flush=True)
    print(f"  DB              : {_DB_PATH}", flush=True)
    print(f"  Model           : {_MODEL}", flush=True)
    if eff_max_new_leads > 0:
        print(f"  New leads cap   : {eff_max_new_leads} (max_new_leads_per_run)", flush=True)
    if len(active_registry) < len(AGENT_REGISTRY):
        _active_names = {r["name"] for r in active_registry}
        disabled = [a["name"] for a in AGENT_REGISTRY if a["name"] not in _active_names]
        print(f"  Disabled agents : {', '.join(disabled)}", flush=True)
    print("=" * 60, flush=True)

    api_key    = os.environ.get("OPENAI_API_KEY", "").strip()
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key or api_key == "paste_your_key_here_without_quotes":
        print("\n  FATAL: OPENAI_API_KEY not set"); sys.exit(1)
    if not serper_key:
        print("\n  FATAL: SERPER_API_KEY not set"); sys.exit(1)

    openai_client = build_openai_client(api_key)
    conn          = get_connection(_DB_PATH)
    initialize_schema(conn)

    stale = flag_stale_leads(conn, days_threshold=90)
    if stale:
        print(f"\n  TTL: {stale} stale lead(s) flagged.", flush=True)

    # ── Global State: build combined skip gate ────────────────────────────────
    known_domains:  set[str]       = _get_known_domains(_DB_PATH)
    blacklisted:    frozenset[str] = load_blacklist(conn)
    skip_domains:   set[str]       = known_domains | set(blacklisted)

    print(f"\n  Known domains in DB : {len(known_domains)}", flush=True)
    print(f"  Blacklisted domains : {len(blacklisted)}", flush=True)
    print(f"  Total skip gate     : {len(skip_domains)}", flush=True)

    # ── HITL Feedback ─────────────────────────────────────────────────────────
    _feedback_list    = get_recent_feedback(conn, n=10)
    feedback_context  = build_feedback_context(_feedback_list)
    if _feedback_list:
        print(f"\n  HITL Feedback   : {len(_feedback_list)} rejection reason(s) injected into NLP prompt.", flush=True)
    else:
        print("\n  HITL Feedback   : none recorded yet (skipping injection).", flush=True)

    run_totals:     dict       = {"prompt_tokens": 0, "completion_tokens": 0, "serper_calls": 0}
    all_records:    list[dict] = []
    agent_summaries: list[dict] = []
    t_start = time.monotonic()

    for agent_cfg in active_registry:
        summary = await _run_agent_loop(
            agent_cfg=agent_cfg,
            serper_key=serper_key,
            openai_client=openai_client,
            conn=conn,
            skip_domains=skip_domains,
            run_totals=run_totals,
            all_records=all_records,
            feedback_context=feedback_context,
            exhaustion_threshold=eff_exhaustion,
            max_new_leads=eff_max_new_leads,
        )
        agent_summaries.append(summary)

    elapsed = time.monotonic() - t_start

    upgraded = await _run_instagram_phase(all_records, conn, serper_key, run_totals)
    if upgraded:
        print(f"\n  Phase 2.5 complete -- {upgraded} lead(s) upgraded to Class A.")

    enriched = await _run_contact_enrichment_phase(all_records, conn)
    if enriched:
        print(f"\n  Phase 2A complete -- {enriched} lead(s) enriched with contact phone.")

    _print_token_report(all_records, _MODEL)

    # Sprint 11A — cost summary
    _p   = run_totals.get("prompt_tokens", 0)
    _c   = run_totals.get("completion_tokens", 0)
    _sc  = run_totals.get("serper_calls", 0)
    _oai = (_p / 1_000_000 * 0.15) + (_c / 1_000_000 * 0.60)
    _ser = _sc * 0.001
    _tot = _oai + _ser
    _qa  = sum(1 for r in all_records if r.get("status") == "QUALIFIED_A")
    _cpa = _tot / _qa if _qa else 0.0
    print("\n" + "=" * 60, flush=True)
    print("  UNIT ECONOMICS", flush=True)
    print("=" * 60, flush=True)
    print(f"  Serper calls  : {_sc}  (est. ${_ser:.4f})", flush=True)
    print(f"  OpenAI cost   : ${_oai:.4f}  (prompt={_p:,} / comp={_c:,} tok)", flush=True)
    print(f"  Total run cost: ${_tot:.4f} USD", flush=True)
    print(f"  New QUALIFIED_A: {_qa}  →  ${_cpa:.4f} / Class A lead", flush=True)
    print("=" * 60, flush=True)

    print("\n  -- Agent Summaries --", flush=True)
    for s in agent_summaries:
        print(f"  {s['agent']:<22}  new={s['new_domains']:>3}  "
              f"known={s.get('already_known', 0):>3}  "
              f"raw={s['raw_results']:>4}  iter={s['iterations']}  stop={s['stop_reason']}", flush=True)

    cur = conn.execute("SELECT COUNT(*) FROM leads")
    print(f"\n  Total DB rows : {cur.fetchone()[0]}", flush=True)

    _save_run_log(all_records, run_totals, elapsed, agent_summaries)
    conn.close()

    print("\n  Phase 3 -- O-Output Export ...", flush=True)
    counts = export_leads(db_path=_DB_PATH, output_path=DEFAULT_EXPORT_PATH)
    print(f"  Class A : {counts['class_a']} leads", flush=True)
    print(f"  Class B : {counts['class_b']} leads", flush=True)
    print(f"  Class C : {counts['class_c']} leads  (AI rejections -- human review)", flush=True)
    print(f"  File    : {DEFAULT_EXPORT_PATH}", flush=True)

    # Sprint 6 — post-run delta report
    try:
        from delta_reporter import generate_delta_report
        report_path = generate_delta_report()
        print(f"  Delta   : {report_path}", flush=True)
    except Exception as _dr_err:
        print(f"  Delta   : skipped ({_dr_err})", flush=True)

    print(f"\n  Done in {elapsed:.1f}s.\n", flush=True)


# ---------------------------------------------------------------------------
# Entry point — full traceback on any crash
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(">>> [DEBUG] Entering __main__ block", flush=True)

    # ── Windows: force SelectorEventLoop (Sprint 10.5 — Silent Freeze fix, root cause) ──
    # On Windows, Python 3.8+ defaults to ProactorEventLoop (IOCP-based).
    # ProactorEventLoop blocks the event loop thread during TLS/SSL handshakes when
    # httpx (used by the OpenAI AsyncOpenAI client) opens its first HTTPS connection to
    # api.openai.com.  While the loop is blocked, ALL asyncio timer callbacks stop
    # firing — including the asyncio.wait_for(timeout=45) guard around classify_lead_full.
    # This causes a silent, indefinite hang that no application-level timeout can cancel.
    #
    # WindowsSelectorEventLoopPolicy switches to SelectorEventLoop, which uses Python's
    # own select()-based IO multiplexing for SSL and is fully compatible with httpx /
    # anyio / openai.AsyncOpenAI.  All asyncio.wait_for guards then work correctly.
    #
    # Downside of SelectorEventLoop on Windows: no subprocess.PIPE for asyncio.subprocess
    # — but live_run.py uses only synchronous subprocess (subprocess.Popen via the
    # dashboard) and blocking SQLite, so this trade-off is harmless here.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print(">>> [DEBUG] Windows: event loop → WindowsSelectorEventLoopPolicy (SelectorEventLoop)", flush=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n>>> [DEBUG] Interrupted by user (Ctrl+C)", flush=True)
    except SystemExit as _se:
        print(f">>> [DEBUG] SystemExit({_se.code})", flush=True)
        sys.exit(_se.code)
    except Exception:
        print("\n>>> [FATAL] Unhandled exception in main():", flush=True)
        traceback.print_exc()
        sys.exit(1)
    print(">>> [DEBUG] Script finished cleanly", flush=True)
