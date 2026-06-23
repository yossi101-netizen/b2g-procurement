"""
generate_script.py — KritiKaal YouTube Script-Generation Module
Phase 2 of the YouTube Authority Engine.

Reads the Pain Matrix (C-core/04-youtube-pain-matrix.md) and Voice DNA,
then generates a structured script brief (Hook, Body, CTA) for a given
pain-point cluster using the KritiKaal Copywriter persona.

OUTPUT MODES:
  --format raw      Full structured JSON brief (default)
  --format otterly  Otterly.ai API payload for GEO/AI Overview tracking

USAGE:
  python generate_script.py --list-clusters
  python generate_script.py --cluster "EUDR Compliance Panic"
  python generate_script.py --cluster "China Plus One Pivot" --format otterly
  python generate_script.py --cluster "QC Disaster" --output briefs/qc.json

INTEGRATION:
  Reads from:  C-core/04-youtube-pain-matrix.md
               C-core/voice-dna.md
               T-tools/01-skills/youtube-extraction/extract_insight.py (optional context)
  Writes to:   O-output/youtube-scripts/script-brief-[cluster-slug].json
               O-output/youtube-scripts/otterly-[cluster-slug].json (--format otterly)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import anthropic
except ImportError:
    print(
        "ERROR: anthropic package not installed.\n"
        "Run: pip install anthropic",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; ANTHROPIC_API_KEY can be set directly in environment

# ---------------------------------------------------------------------------
# Paths — resolved relative to workspace root
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).parent.resolve()
_WORKSPACE = _THIS_DIR.parent.parent.parent  # T-tools/01-skills/script-generation -> workspace root

PAIN_MATRIX_PATH = _WORKSPACE / "C-core" / "04-youtube-pain-matrix.md"
VOICE_DNA_PATH   = _WORKSPACE / "C-core" / "voice-dna.md"
ICP_PATH         = _WORKSPACE / "C-core" / "icp-profile.md"
OUTPUT_DIR       = _WORKSPACE / "O-output" / "youtube-scripts"

# Model — Sonnet with prompt caching (system prompt cached across multi-cluster runs)
SCRIPT_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Copywriter Persona — KritiKaal B2B YouTube Voice
# ---------------------------------------------------------------------------

_COPYWRITER_SYSTEM = """\
You are KritiKaal's B2B YouTube Script Copywriter. KritiKaal is a Managed \
Manufacturing service based in India, specialising in leather goods for \
UK/EU/US small and medium brands (300-3,000 units/run).

PERSONA: Senior supply chain operator. 40+ years of European export experience \
in Chennai and Kolkata clusters. You have seen every failure mode. You do not \
sell dreams. You solve operational problems with specific mechanisms and \
verifiable numbers.

VOICE RULES (non-negotiable):
1. Open with a concrete failure moment — never a question, never a statistic.
   The cold open is a scene or a sentence that happened. Example:
   "The factory said: Sir, you approved the sample. They were not wrong."
2. Use specific numbers every time. Not "significant savings" — "2,000 pounds
   kept on a 20,000-pound order." Not "high quality" — "AQL 2.5, the same
   standard used by LVMH and Hermes supply chains."
3. Name the mechanism. Do not describe it vaguely. Named mechanisms:
   - Single Point of Accountability (one contact, owns every outcome)
   - Double-Back Guarantee (defective units replaced before shipment, our cost)
   - AQL 2.5 (premium inspection standard, 8 criteria, in-line at 30% of run)
   - The Missing Middle (300-3,000 unit bracket no platform serves)
   - The Golden Sample Trap (sample approval creates false production confidence)
4. Disqualify wrong-fit viewers explicitly. End every CTA with who this is NOT for.
5. No creator conventions. No "smash the like button". No "in today's video".
   No "I hope this helps". No hedging. No filler transitions.
6. Structure: Problem -> Mechanism -> Solution -> Proof. Every section.
7. No em dashes (—). Use a period and a new sentence instead.

OUTPUT FORMAT:
Return ONLY a valid JSON object. No prose. No markdown fences. No explanation.
Any deviation from valid JSON causes a pipeline failure.

{
  "cluster": "<exact pain cluster name from the Pain Matrix>",
  "cluster_id": "<snake_case cluster id>",
  "hook": {
    "cold_open": "<Opening line. Concrete failure moment. Max 30 words. No question.>",
    "problem_statement": "<The specific operational pain this video addresses. 2-3 sentences. Unhedged.>",
    "credibility_anchor": "<Why Yossi Daniel can speak to this. One specific experience, not a credential list.>",
    "viewer_promise": "<What the viewer will be able to DO after watching. Operational, not inspirational.>",
    "estimated_duration_sec": <integer, 30-45>
  },
  "body": {
    "sections": [
      {
        "title": "<Section heading — declarative claim, not a question>",
        "key_claim": "<The assertive, unhedged claim of this section>",
        "evidence": "<Specific number, named mechanism, or verified example>",
        "estimated_duration_sec": <integer>
      }
    ],
    "mechanism_name": "<The primary named KritiKaal mechanism introduced in this video>",
    "mechanism_definition": "<One precise sentence defining the mechanism>",
    "estimated_total_duration_sec": <integer, target 300-480>
  },
  "cta": {
    "primary_ask": "<The specific, low-friction action. 20-minute call language. Remove every barrier.>",
    "disqualification": "<Who this is NOT for. The explicit filter. Required.>",
    "link_description": "<Text for the link in the video description>",
    "estimated_duration_sec": <integer, 15-30>
  },
  "metadata": {
    "target_icp": "<Specific viewer persona — job title, context, pain state>",
    "primary_keyword": "<Main search term this video targets>",
    "secondary_keywords": ["<keyword 2>", "<keyword 3>"],
    "content_type": "<educational|case-study|comparison|explainer>",
    "estimated_total_runtime_min": <float, one decimal place>,
    "geo_authority_claim": "<The single most citable factual claim in this video for AI search>",
    "regulation_check": "<CLEAR — no regulatory figures / FLAG: [exact figure] — verify before publish>"
  }
}
"""


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_file(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"{label} not found at:\n  {path}\n"
            "Run migration and file creation steps first."
        )
    return path.read_text(encoding="utf-8")


def _load_pain_matrix() -> str:
    return _load_file(PAIN_MATRIX_PATH, "Pain Matrix")


def _load_voice_dna() -> str:
    try:
        return _load_file(VOICE_DNA_PATH, "Voice DNA")
    except FileNotFoundError:
        return ""  # Optional — copywriter persona above covers the essentials


def _load_icp() -> str:
    try:
        return _load_file(ICP_PATH, "ICP Profile")
    except FileNotFoundError:
        return ""


# ---------------------------------------------------------------------------
# Cluster utilities
# ---------------------------------------------------------------------------

def list_clusters(pain_matrix: str) -> list[dict]:
    """
    Parse cluster names and IDs from the Pain Matrix markdown.
    Returns list of dicts: {"name": ..., "id": ..., "priority": ...}
    """
    clusters = []
    current: dict = {}
    for line in pain_matrix.splitlines():
        if line.startswith("## Cluster "):
            # Format: "## Cluster N: Name"
            match = re.match(r"## Cluster \d+: (.+)", line)
            if match:
                if current:
                    clusters.append(current)
                current = {"name": match.group(1).strip(), "id": "", "priority": ""}
        elif line.startswith("**ID:**") and current:
            current["id"] = line.replace("**ID:**", "").strip()
        elif line.startswith("**Priority:**") and current:
            current["priority"] = line.replace("**Priority:**", "").strip()
    if current:
        clusters.append(current)
    return clusters


def find_cluster_section(cluster_name: str, pain_matrix: str) -> str:
    """
    Extract the full markdown section for a specific cluster.
    Matches by name (case-insensitive, partial match allowed).
    """
    name_lower = cluster_name.lower()
    lines = pain_matrix.splitlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.startswith("## Cluster") and name_lower in line.lower():
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

def generate_script_brief(
    cluster_name: str,
    pain_matrix: str,
    voice_dna: str,
    icp: str,
    client: anthropic.Anthropic,
    extra_context: Optional[str] = None,
) -> dict:
    """
    Generate a structured script brief for a given pain-point cluster.

    Uses Claude Sonnet with prompt caching on the system prompt.
    Multiple clusters can be generated in one session at ~10% system prompt cost
    after the first call.
    """
    # Narrow the pain matrix to just the target cluster section for focus
    cluster_section = find_cluster_section(cluster_name, pain_matrix)
    if not cluster_section:
        raise ValueError(
            f"Cluster '{cluster_name}' not found in Pain Matrix.\n"
            f"Run --list-clusters to see available clusters."
        )

    user_parts = [
        "TARGET CLUSTER (from Pain Matrix):",
        cluster_section,
        "",
        "FULL PAIN MATRIX (for cross-cluster mechanism consistency):",
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
        "Return ONLY the JSON object. No markdown. No explanation.",
    ]

    response = client.messages.create(
        model=SCRIPT_MODEL,
        max_tokens=2500,
        system=[{
            "type": "text",
            "text": _COPYWRITER_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": "\n".join(user_parts)}],
    )

    raw = "".join(b.text for b in response.content if hasattr(b, "text")).strip()

    # Strip markdown fences if model included them despite instruction
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON for cluster '{cluster_name}'.\n"
            f"JSON error: {exc}\n\n"
            f"Raw output (first 500 chars):\n{raw[:500]}"
        ) from exc


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_for_otterly(brief: dict) -> dict:
    """
    Format the script brief as an Otterly.ai API payload.

    Otterly.ai (https://otterly.ai) monitors AI Overview presence and GEO signals.
    This payload submits the video's primary GEO authority claim as a tracked query,
    enabling measurement of whether KritiKaal content surfaces in AI-generated answers
    for this cluster's search terms.

    API endpoint: https://app.otterly.ai/api/v1/queries  (update when confirmed)
    Authentication: Bearer token via OTTERLY_API_KEY environment variable.

    To submit:
        import requests, os
        headers = {"Authorization": f"Bearer {os.getenv('OTTERLY_API_KEY')}"}
        response = requests.post(
            "https://app.otterly.ai/api/v1/queries",
            headers=headers,
            json=otterly_payload,
        )
    """
    meta = brief.get("metadata", {})
    hook = brief.get("hook", {})
    body = brief.get("body", {})
    cta  = brief.get("cta", {})

    return {
        "query": meta.get("geo_authority_claim", ""),
        "keywords": [meta.get("primary_keyword", "")] + meta.get("secondary_keywords", []),
        "brand": "KritiKaal",
        "content_snapshot": {
            "title":     f"{brief.get('cluster', '')} — KritiKaal Managed Manufacturing",
            "cold_open": hook.get("cold_open", ""),
            "mechanism": body.get("mechanism_name", ""),
            "cta":       cta.get("primary_ask", ""),
            "runtime_min": meta.get("estimated_total_runtime_min"),
        },
        "tracking_metadata": {
            "content_type": "youtube_script_brief",
            "cluster_id":   brief.get("cluster_id", ""),
            "icp":          meta.get("target_icp", ""),
            "regulation_check": meta.get("regulation_check", ""),
        },
    }


# ---------------------------------------------------------------------------
# Output persistence
# ---------------------------------------------------------------------------

def save_brief(brief: dict, cluster_name: str, suffix: str = "") -> Path:
    """
    Save the brief JSON to O-output/youtube-scripts/.
    Returns the path written.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", cluster_name.lower()).strip("-")
    filename = f"script-brief-{slug}{suffix}.json"
    out_path = OUTPUT_DIR / filename
    out_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal YouTube Script Brief Generator — Phase 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_script.py --list-clusters
  python generate_script.py --cluster "EUDR Compliance Panic"
  python generate_script.py --cluster "China Plus One Pivot" --format otterly
  python generate_script.py --cluster "QC Disaster" --output briefs/qc.json
  python generate_script.py --cluster "Sourcing Agent Betrayal" --context "Focus on UK brands"
        """,
    )
    parser.add_argument(
        "--cluster", "-c",
        help="Pain-point cluster name to generate a brief for",
    )
    parser.add_argument(
        "--list-clusters", "-l", action="store_true",
        help="List all available clusters from the Pain Matrix",
    )
    parser.add_argument(
        "--format", "-f", choices=["raw", "otterly"], default="raw",
        help="Output format: 'raw' (full script brief JSON) or 'otterly' (Otterly.ai payload)",
    )
    parser.add_argument(
        "--output", "-o", metavar="PATH",
        help="Write output to this file path instead of auto-saving to O-output/",
    )
    parser.add_argument(
        "--context",
        help="Additional context string from the YouTube Analyst to append to the prompt",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Print to stdout only. Do not auto-save to O-output/youtube-scripts/",
    )
    args = parser.parse_args()

    # Load files
    try:
        pain_matrix = _load_pain_matrix()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    voice_dna = _load_voice_dna()
    icp       = _load_icp()

    # List clusters mode
    if args.list_clusters:
        clusters = list_clusters(pain_matrix)
        if not clusters:
            print(
                "Could not parse clusters from Pain Matrix.\n"
                "Check format of C-core/04-youtube-pain-matrix.md"
            )
            sys.exit(1)
        print("Available pain-point clusters:\n")
        for c in clusters:
            print(f"  [{c.get('priority', '?')}] {c['name']}")
            if c.get("id"):
                print(f"        id: {c['id']}")
        print(f"\n{len(clusters)} clusters total.")
        print(
            '\nUsage: python generate_script.py --cluster "Cluster Name Here"'
        )
        return

    if not args.cluster:
        parser.print_help()
        sys.exit(0)

    # Resolve API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it in your .env file or export it in your shell.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Generating script brief for: '{args.cluster}' ...", file=sys.stderr)

    try:
        brief = generate_script_brief(
            cluster_name=args.cluster,
            pain_matrix=pain_matrix,
            voice_dna=voice_dna,
            icp=icp,
            client=client,
            extra_context=args.context,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Apply output format
    if args.format == "otterly":
        output_data = format_for_otterly(brief)
        suffix = "-otterly"
    else:
        output_data = brief
        suffix = ""

    json_out = json.dumps(output_data, indent=2, ensure_ascii=False)

    # Write to specified path
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json_out, encoding="utf-8")
        print(f"Written to: {args.output}", file=sys.stderr)
        print(json_out)
        return

    # Auto-save + print
    if not args.no_save:
        saved = save_brief(output_data, args.cluster, suffix=suffix)
        print(f"Auto-saved to: {saved}", file=sys.stderr)

    print(json_out)


if __name__ == "__main__":
    main()
