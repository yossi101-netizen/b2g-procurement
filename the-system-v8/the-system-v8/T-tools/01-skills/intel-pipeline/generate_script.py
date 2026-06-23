"""
generate_script.py — KritiKaal Intel Pipeline: Stage 4 Script Generator

Reads approved intel items from intel.db / approved-intel.json and generates
structured YouTube script briefs enriched with real-world evidence: actual
tariff figures, regulatory dates, and documented supply chain failures sourced
from trade journals, regulatory feeds, and Reddit.

PIPELINE POSITION:
    rss_poller.py  →  llm_filter.py  →  hitl_review.py  →  generate_script.py (HERE)

INSTALL:
    pip install anthropic python-dotenv

USAGE:
    cd T-tools/01-skills/intel-pipeline/
    python generate_script.py --list-clusters        # Clusters with approved intel
    python generate_script.py --cluster eudr-compliance
    python generate_script.py --cluster china-plus-one --min-items 3
    python generate_script.py --all-clusters         # Batch all clusters with intel
    python generate_script.py --cluster qc-disaster --format otterly
    python generate_script.py --cluster qc-disaster --no-save  # stdout only

DIFFERENCE FROM script-generation/generate_script.py:
    The script-generation version generates from the pain matrix alone.
    This version enriches every brief with real approved intel:
      - Specific tariff numbers and regulatory dates from trade journals
      - Documented QC failures from Reddit and industry feeds
      - Verifiable case evidence the copywriter can reference by source

OUTPUT:
    O-output/youtube-scripts/script-brief-[cluster]-intel.json
    O-output/youtube-scripts/otterly-[cluster]-intel.json  (--format otterly)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Shared pipeline core (intel_core.py must be in the same directory)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE))
from intel_core import (
    CLUSTER_KEYWORDS,
    QUEUE_DIR,
    export_approved_json,
    get_db,
    init_db,
)

# ---------------------------------------------------------------------------
# .env loading — same candidates as llm_filter.py
# ---------------------------------------------------------------------------
def _load_env() -> None:
    candidates = [
        _HERE / ".env",
        _HERE.parent / "youtube-extraction" / ".env",
        _HERE.parent / "script-generation" / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path, override=False)
                return
            except ImportError:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        os.environ.setdefault(k.strip(), v.strip())
                return

_load_env()

# ---------------------------------------------------------------------------
# Paths — resolved from intel-pipeline/ up to workspace root
# ---------------------------------------------------------------------------
# intel-pipeline/ → 01-skills/ → T-tools/ → workspace root
_WORKSPACE   = _HERE.parent.parent.parent

PAIN_MATRIX_PATH = _WORKSPACE / "C-core" / "04-youtube-pain-matrix.md"
VOICE_DNA_PATH   = _WORKSPACE / "C-core" / "voice-dna.md"
ICP_PATH         = _WORKSPACE / "C-core" / "icp-profile.md"
OUTPUT_DIR       = _WORKSPACE / "O-output" / "youtube-scripts"
APPROVED_JSON    = QUEUE_DIR / "approved-intel.json"

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
# Sonnet tier: intel context can be 4K–8K tokens — haiku truncates reasoning quality.
SCRIPT_MODEL     = "claude-sonnet-4-5"
SCRIPT_MODEL_ALT = "claude-sonnet-4-6"   # try first; fall back if unlisted


def _resolve_model() -> str:
    """Pick best available Sonnet 4 model. Falls back to SCRIPT_MODEL on error."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return SCRIPT_MODEL
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        ids = [m.id for m in client.models.list().data]
        for candidate in (SCRIPT_MODEL_ALT, SCRIPT_MODEL):
            if candidate in ids:
                return candidate
        # Accept any sonnet-4 variant
        sonnet4 = sorted(
            (m for m in ids if "sonnet" in m.lower() and any(
                x in m for x in ("-4-", "sonnet-4")
            )),
            reverse=True,
        )
        if sonnet4:
            return sonnet4[0]
    except Exception:
        pass
    return SCRIPT_MODEL

# ---------------------------------------------------------------------------
# Copywriter persona — KritiKaal B2B YouTube Voice
# (Identical to script-generation/generate_script.py — single source of truth
#  in voice-dna.md; this string is the compiled prompt form.)
# ---------------------------------------------------------------------------
_COPYWRITER_SYSTEM = """\
ENTITY DEFINITIONS (hold both simultaneously throughout generation):

KRITIKAAL — the operating firm. A Managed Manufacturing service headquartered in
India, providing end-to-end production management for leather goods on behalf of
UK, EU, and US brands. Operates in the 300-3,000 unit bracket. Does NOT sell
product. Sells operational certainty: on-spec, on-time, fully accountable.

THE INTEL AGENTS — the intelligence and content division of KritiKaal. The Intel
Agents monitor macro events (regulatory changes, tariff shifts, supply chain
disruptions, trade policy) and translate them into data-driven video content aimed
at B2B decision-makers. The Intel Agents speak as analysts, not as salespeople.
Their mandate: educate business owners on how macro forces affect their sourcing
decisions, then position KritiKaal as the operational solution. The audience is
never the general consumer. The audience is always the business.

YOUR ROLE: You are writing on behalf of The Intel Agents. Every script you generate
is an intelligence briefing delivered as a YouTube video. The viewer is a business
operator. The framing is always: "Here is what is happening in the macro environment.
Here is how it affects your business specifically. Here is the operational mechanism
that resolves it."

THE TARGET VIEWER (ICP):
Brand founders, heads of product, procurement leads, or operations directors at
UK/EU/US leather goods brands, accessories labels, or fashion businesses with
300-3,000 unit production runs. They are sourcing from China (and trying to diversify),
navigating EUDR compliance, dealing with QC failures from opaque supply chains, or
being held hostage by sourcing intermediaries they can no longer trust.
This is NOT for: hobbyists, consumers, retail buyers, Etsy sellers, or anyone who
does not manage a business with real P&L exposure to supply chain decisions.

MACRO-TO-BUSINESS TRANSLATION MANDATE:
Every script must follow this logic chain:
  MACRO EVENT (tariff change, regulation, supply chain disruption, trade policy)
  → BUSINESS IMPACT (what this costs the viewer's business in pounds, units, or risk)
  → OPERATIONAL GAP (the failure mode that exists without a solution)
  → KRITIKAAL MECHANISM (the named, specific solution KritiKaal provides)
  → PROOF (verified data, documented case, or verifiable number from the intel)

VOICE RULES (non-negotiable):
1. Open with a concrete failure moment or macro event consequence — not a question,
   not a statistic. The cold open is a scene, a policy clause, or a sentence that
   happened. Example: "On 1 January 2026, the EU began requiring farm-level
   geolocation data for every leather product crossing its border. Most India-sourced
   brands had zero documentation."
2. Use specific numbers every time. Not "significant savings" — "2,000 pounds
   kept on a 20,000-pound order." Not "high quality" — "AQL 2.5, the same
   standard used by LVMH and Hermes supply chains."
3. Name the mechanism. Do not describe it vaguely. Named KritiKaal mechanisms:
   - Single Point of Accountability (one contact owns every outcome end-to-end)
   - Double-Back Guarantee (defective units replaced before shipment, KritiKaal cost)
   - AQL 2.5 (premium inspection standard, 8 criteria, in-line at 30% of run)
   - The Missing Middle (300-3,000 unit bracket no platform serves at managed quality)
   - The Golden Sample Trap (sample approval creates false confidence in bulk production)
   - DCTS Zero-Duty Window (0% UK import duty for India-origin leather goods under DCTS)
4. Disqualify wrong-fit viewers explicitly. End every CTA with who this is NOT for.
5. No creator conventions. No "smash the like button". No "in today's video".
   No "I hope this helps". No hedging. No filler transitions.
6. Structure every section: Macro Event -> Business Impact -> Mechanism -> Proof.
7. No em dashes (—). Use a period and a new sentence instead.

USING INTEL EVIDENCE:
You will receive REAL APPROVED INTELLIGENCE: actual articles, regulatory updates,
and documented supply chain failures reviewed and approved by a human analyst.
These are the raw material. Use them directly:
- Lead with the most specific, verifiable number or date from the intel.
- Prefer verified data from the intel over invented numbers.
- Do not cite the source URL in the script. Weave the information naturally.
- If intel contains a figure that contradicts the Pain Matrix, flag it in
  "metadata.regulation_check" for human verification before publishing.

OUTPUT FORMAT:
Return ONLY a valid JSON object. No prose. No markdown fences. No explanation.
Any deviation from valid JSON causes a pipeline failure.

{
  "cluster": "<exact pain cluster name>",
  "cluster_id": "<snake_case cluster id matching CLUSTER_KEYWORDS>",
  "intel_items_used": <integer — how many intel items informed this brief>,
  "hook": {
    "cold_open": "<Opening line. Macro event consequence or concrete failure. Max 35 words. No question.>",
    "macro_event": "<The specific regulatory, tariff, or market event this video addresses>",
    "business_impact": "<What this macro event costs the viewer's business — in pounds, units, or operational risk>",
    "credibility_anchor": "<Why The Intel Agents and KritiKaal can speak to this. One specific operational fact, not a credential list.>",
    "viewer_promise": "<What the viewer will be able to DO after watching. Operational, not inspirational.>",
    "estimated_duration_sec": <integer, 30-45>
  },
  "body": {
    "sections": [
      {
        "title": "<Section heading — declarative claim about the macro event's business consequence>",
        "macro_context": "<The external event or data driving this section>",
        "key_claim": "<The assertive, unhedged business impact claim>",
        "evidence": "<Specific number, named mechanism, or verified example — cite intel where possible>",
        "intel_source": "<Publication name or 'Pain Matrix' — where the evidence originated>",
        "kritikaal_response": "<The specific KritiKaal mechanism that addresses this section's problem>",
        "estimated_duration_sec": <integer>
      }
    ],
    "mechanism_name": "<The primary named KritiKaal mechanism introduced in this video>",
    "mechanism_definition": "<One precise sentence defining the mechanism and its measurable outcome>",
    "estimated_total_duration_sec": <integer, target 300-480>
  },
  "cta": {
    "primary_ask": "<The specific, low-friction action. 20-minute call language. Remove every barrier.>",
    "disqualification": "<Who this is NOT for. Explicit. Required. Must name wrong-fit viewer types.>",
    "link_description": "<Text for the link in the video description>",
    "estimated_duration_sec": <integer, 15-30>
  },
  "metadata": {
    "target_icp": "<Specific B2B viewer persona — job title, company stage, active pain state>",
    "primary_keyword": "<Main B2B search term this video targets>",
    "secondary_keywords": ["<keyword 2>", "<keyword 3>"],
    "content_type": "<regulatory-briefing|tariff-analysis|case-study|comparison|explainer>",
    "estimated_total_runtime_min": <float, one decimal place>,
    "geo_authority_claim": "<The single most citable factual claim in this video for AI search>",
    "regulation_check": "<CLEAR — no regulatory figures / FLAG: [exact figure] — verify before publish>"
  }
}
"""


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_optional(path: Path, label: str) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_required(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"{label} not found at:\n  {path}\n"
            "This file is required. Check workspace structure."
        )
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Intel loading
# ---------------------------------------------------------------------------

def _load_approved_json() -> dict:
    """Load approved-intel.json. Re-exports from DB if file is missing or stale."""
    if not APPROVED_JSON.exists():
        # Auto-export if we have approved items in the DB
        init_db()
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM intel_items WHERE status = 'approved'"
        ).fetchone()[0]
        conn.close()
        if count > 0:
            export_approved_json()
        else:
            return {"total_approved": 0, "by_cluster": {}, "items": []}

    try:
        return json.loads(APPROVED_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Could not parse approved-intel.json: {exc}", file=sys.stderr)
        return {"total_approved": 0, "by_cluster": {}, "items": []}


def get_intel_for_cluster(cluster_id: str, data: dict, max_items: int = 10) -> list[dict]:
    """
    Return up to max_items approved intel items for a cluster.
    Higher-scored items first (already sorted in approved-intel.json).
    """
    by_cluster = data.get("by_cluster", {})
    items = by_cluster.get(cluster_id, [])
    return items[:max_items]


def list_clusters_with_intel(data: dict) -> list[dict]:
    """
    Return clusters that have at least one approved intel item,
    sorted by item count descending.
    """
    by_cluster = data.get("by_cluster", {})
    result = []
    for cid, items in by_cluster.items():
        # Map cluster_id to a human-readable name via CLUSTER_KEYWORDS
        name = cid.replace("-", " ").title()
        result.append({
            "cluster_id":   cid,
            "cluster_name": name,
            "item_count":   len(items),
            "top_score":    max((i.get("raw_score", 0) for i in items), default=0),
        })
    return sorted(result, key=lambda x: x["item_count"], reverse=True)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _format_intel_block(items: list[dict]) -> str:
    """
    Format approved intel items into a structured prompt block.
    Each item: source, title, score, publication date, excerpt.
    """
    if not items:
        return "(No approved intel for this cluster — brief will draw from Pain Matrix only.)"

    lines = [
        f"APPROVED INTELLIGENCE — {len(items)} items reviewed by human analyst:",
        "=" * 60,
    ]
    for i, item in enumerate(items, 1):
        source   = item.get("source", "?").upper()
        title    = item.get("title", "(no title)")
        excerpt  = (item.get("body_excerpt") or "")[:400].strip()
        pub_date = (item.get("published_at") or "")[:10]
        score    = item.get("raw_score", 0.0)
        notes    = item.get("user_notes", "")

        lines.append(f"\n[{i}] [{source}] {title}")
        if pub_date:
            lines.append(f"    Published: {pub_date}  |  Signal score: {score:.1f}")
        if notes:
            lines.append(f"    Analyst note: {notes}")
        if excerpt:
            lines.append(f"    Excerpt: {excerpt}")
        if len(item.get("body_excerpt", "")) > 400:
            lines.append("    [...]")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def _find_cluster_section(cluster_id_or_name: str, pain_matrix: str) -> str:
    """Extract the full markdown section for a specific cluster."""
    search_term = cluster_id_or_name.replace("-", " ").lower()
    lines  = pain_matrix.splitlines()
    start  = None
    end    = None
    for i, line in enumerate(lines):
        if line.startswith("## Cluster") and search_term in line.lower():
            start = i
        elif start is not None and line.startswith("## ") and i > start:
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end] if end else lines[start:])


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def generate_intel_brief(
    cluster_id: str,
    intel_items: list[dict],
    pain_matrix: str,
    voice_dna: str,
    icp: str,
    model_id: str,
    extra_context: Optional[str] = None,
) -> dict:
    """
    Generate a script brief enriched with real approved intel.

    The intel block is injected before the pain matrix so the model
    reads actual evidence before reading the theoretical framework.
    """
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    cluster_section = _find_cluster_section(cluster_id, pain_matrix)
    intel_block     = _format_intel_block(intel_items)

    # Human-readable cluster name for the prompt
    cluster_name = cluster_id.replace("-", " ").title()

    user_parts = [
        f"TARGET PAIN CLUSTER: {cluster_name} (id: {cluster_id})",
        "",
        # Intel first — model reads evidence before theory
        intel_block,
        "",
        "CLUSTER DEFINITION (from Pain Matrix):",
        cluster_section if cluster_section else "(section not found in Pain Matrix — use cluster_id as guide)",
        "",
        "FULL PAIN MATRIX (cross-cluster mechanism consistency):",
        pain_matrix,
    ]

    if voice_dna:
        user_parts += ["", "VOICE DNA (calibration):", voice_dna]
    if icp:
        user_parts += ["", "ICP PROFILE (know the viewer):", icp]
    if extra_context:
        user_parts += ["", "ADDITIONAL CONTEXT FROM ANALYST:", extra_context]

    user_parts += [
        "",
        "Generate the structured script brief for this cluster.",
        "Prioritise concrete figures and documented failures from the APPROVED INTELLIGENCE block.",
        "Return ONLY the JSON object. No markdown. No explanation.",
    ]

    response = client.messages.create(
        model=model_id,
        max_tokens=3000,
        system=[{
            "type":          "text",
            "text":          _COPYWRITER_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": "\n".join(user_parts)}],
    )

    raw = "".join(b.text for b in response.content if hasattr(b, "text")).strip()

    # Strip markdown fences if model included them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        brief = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON for cluster '{cluster_id}'.\n"
            f"JSON error: {exc}\n\n"
            f"Raw output (first 600 chars):\n{raw[:600]}"
        ) from exc

    # Ensure cluster_id is set correctly
    brief.setdefault("cluster_id", cluster_id)
    brief.setdefault("intel_items_used", len(intel_items))
    return brief


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_for_otterly(brief: dict) -> dict:
    """Format as Otterly.ai API payload for GEO / AI Overview tracking."""
    meta = brief.get("metadata", {})
    hook = brief.get("hook", {})
    body = brief.get("body", {})
    cta  = brief.get("cta", {})

    return {
        "query":    meta.get("geo_authority_claim", ""),
        "keywords": [meta.get("primary_keyword", "")] + meta.get("secondary_keywords", []),
        "brand":    "KritiKaal",
        "content_snapshot": {
            "title":       f"{brief.get('cluster', '')} — KritiKaal Managed Manufacturing",
            "cold_open":   hook.get("cold_open", ""),
            "mechanism":   body.get("mechanism_name", ""),
            "cta":         cta.get("primary_ask", ""),
            "runtime_min": meta.get("estimated_total_runtime_min"),
        },
        "tracking_metadata": {
            "content_type":      "youtube_script_brief",
            "cluster_id":        brief.get("cluster_id", ""),
            "intel_items_used":  brief.get("intel_items_used", 0),
            "icp":               meta.get("target_icp", ""),
            "regulation_check":  meta.get("regulation_check", ""),
            "generated_at":      datetime.now(timezone.utc).isoformat(),
        },
    }


# ---------------------------------------------------------------------------
# Output persistence
# ---------------------------------------------------------------------------

def save_brief(brief: dict, cluster_id: str, suffix: str = "") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug     = re.sub(r"[^a-z0-9]+", "-", cluster_id.lower()).strip("-")
    filename = f"script-brief-{slug}-intel{suffix}.json"
    out_path = OUTPUT_DIR / filename
    out_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal Intel Pipeline — Stage 4: Intel-Enriched Script Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_script.py --list-clusters
  python generate_script.py --cluster eudr-compliance
  python generate_script.py --cluster china-plus-one --min-items 3
  python generate_script.py --all-clusters
  python generate_script.py --cluster qc-disaster --format otterly
  python generate_script.py --cluster qc-disaster --no-save
  python generate_script.py --cluster uk-import-duty --context "Focus on post-Brexit DCTS rates"

Cluster IDs (from intel_core.py CLUSTER_KEYWORDS):
  eudr-compliance      china-plus-one       qc-disaster
  sourcing-agent-betrayal  golden-sample-trap  uk-import-duty
  missing-middle-moq   managed-vs-alternatives
        """,
    )
    parser.add_argument(
        "--cluster", "-c", metavar="CLUSTER_ID",
        help="Cluster ID to generate a brief for (e.g. eudr-compliance)",
    )
    parser.add_argument(
        "--all-clusters", "-a", action="store_true",
        help="Generate briefs for ALL clusters that have approved intel",
    )
    parser.add_argument(
        "--list-clusters", "-l", action="store_true",
        help="List clusters with approved intel and exit",
    )
    parser.add_argument(
        "--min-items", type=int, default=1, metavar="N",
        help="Skip clusters with fewer than N approved items (default: 1)",
    )
    parser.add_argument(
        "--max-items", type=int, default=10, metavar="N",
        help="Max intel items per cluster injected into prompt (default: 10)",
    )
    parser.add_argument(
        "--format", "-f", choices=["raw", "otterly"], default="raw",
        help="Output format: raw (full JSON brief) or otterly (Otterly.ai payload)",
    )
    parser.add_argument(
        "--output", "-o", metavar="PATH",
        help="Write output to this path instead of auto-saving to O-output/",
    )
    parser.add_argument(
        "--context",
        help="Additional context to append to the prompt (analyst notes)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Print to stdout only, do not write to O-output/",
    )
    parser.add_argument(
        "--sleep", type=float, default=3.0, metavar="SEC",
        help="Seconds to sleep between cluster generations in --all-clusters (default: 3)",
    )
    args = parser.parse_args()

    # Load intel data
    print("Loading approved intel ...", file=sys.stderr)
    intel_data     = _load_approved_json()
    total_approved = intel_data.get("total_approved", 0)
    print(f"  {total_approved} approved item(s) in intel queue.", file=sys.stderr)

    # List clusters mode
    if args.list_clusters:
        clusters = list_clusters_with_intel(intel_data)
        if not clusters:
            print(
                "\nNo approved intel found.\n"
                "Run: python hitl_review.py --run   to approve items first."
            )
            sys.exit(0)
        print(f"\nClusters with approved intel ({len(clusters)} total):\n")
        print(f"  {'Cluster ID':<30} {'Items':>6}  {'Top Score':>9}")
        print("  " + "-" * 50)
        for c in clusters:
            flag = "" if c["item_count"] >= 1 else "  [skip]"
            print(
                f"  {c['cluster_id']:<30} {c['item_count']:>6}  {c['top_score']:>9.1f}{flag}"
            )
        print(
            f"\nUsage: python generate_script.py --cluster <cluster_id>"
        )
        return

    # Determine which clusters to process
    if args.all_clusters:
        all_with_intel = list_clusters_with_intel(intel_data)
        targets = [
            c["cluster_id"]
            for c in all_with_intel
            if c["item_count"] >= args.min_items
        ]
        if not targets:
            print(
                f"No clusters with >= {args.min_items} approved item(s). "
                "Lower --min-items or approve more items.",
                file=sys.stderr,
            )
            sys.exit(0)
        print(f"Batch mode: {len(targets)} cluster(s) to process.", file=sys.stderr)

    elif args.cluster:
        targets = [args.cluster]
        intel_count = len(get_intel_for_cluster(args.cluster, intel_data))
        if intel_count < args.min_items:
            print(
                f"[WARN] Cluster '{args.cluster}' has only {intel_count} approved item(s) "
                f"(--min-items {args.min_items}). Continuing with available intel.",
                file=sys.stderr,
            )

    else:
        parser.print_help()
        sys.exit(0)

    # Load C-core context
    try:
        pain_matrix = _load_required(PAIN_MATRIX_PATH, "Pain Matrix")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    voice_dna = _load_optional(VOICE_DNA_PATH, "Voice DNA")
    icp       = _load_optional(ICP_PATH, "ICP Profile")

    if not voice_dna:
        print("[WARN] voice-dna.md not found — copywriter persona embedded in system prompt will be used.", file=sys.stderr)
    if not icp:
        print("[WARN] icp-profile.md not found — target ICP will be inferred from Pain Matrix.", file=sys.stderr)

    # Resolve model once
    model_id = _resolve_model()
    print(f"Model: {model_id}", file=sys.stderr)

    # Generate
    results: list[dict] = []
    for idx, cluster_id in enumerate(targets):
        if idx > 0:
            print(f"\n  Sleeping {args.sleep}s before next cluster ...", file=sys.stderr)
            time.sleep(args.sleep)

        intel_items = get_intel_for_cluster(cluster_id, intel_data, max_items=args.max_items)
        print(
            f"\n[{idx+1}/{len(targets)}] Generating: {cluster_id} "
            f"({len(intel_items)} intel item(s)) ...",
            file=sys.stderr,
        )

        try:
            brief = generate_intel_brief(
                cluster_id=cluster_id,
                intel_items=intel_items,
                pain_matrix=pain_matrix,
                voice_dna=voice_dna,
                icp=icp,
                model_id=model_id,
                extra_context=args.context,
            )
        except Exception as exc:
            print(f"  ERROR on cluster '{cluster_id}': {exc}", file=sys.stderr)
            if len(targets) > 1:
                print("  Skipping — continuing batch.", file=sys.stderr)
                continue
            sys.exit(1)

        # Apply output format
        if args.format == "otterly":
            output_data = format_for_otterly(brief)
            suffix = "-otterly"
        else:
            output_data = brief
            suffix = ""

        json_out = json.dumps(output_data, indent=2, ensure_ascii=False)

        # Single-cluster: honour --output and --no-save
        if len(targets) == 1:
            if args.output:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text(json_out, encoding="utf-8")
                print(f"  Written to: {args.output}", file=sys.stderr)
            elif not args.no_save:
                saved = save_brief(output_data, cluster_id, suffix=suffix)
                print(f"  Saved: {saved}", file=sys.stderr)
            print(json_out)

        else:
            # Batch mode — always save, print summary
            saved = save_brief(output_data, cluster_id, suffix=suffix)
            n_sections = len(brief.get("body", {}).get("sections", []))
            runtime    = brief.get("body", {}).get("estimated_total_duration_sec", 0)
            print(
                f"  Saved: {saved.name}  "
                f"({n_sections} body sections, ~{runtime//60}:{runtime%60:02d})",
                file=sys.stderr,
            )
            results.append({"cluster_id": cluster_id, "path": str(saved)})

    # Batch summary
    if len(targets) > 1:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Batch complete — {len(results)}/{len(targets)} brief(s) generated.", file=sys.stderr)
        for r in results:
            print(f"  {r['cluster_id']:<30} → {Path(r['path']).name}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
