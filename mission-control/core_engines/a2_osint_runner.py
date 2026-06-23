"""
A2 OSINT Brand Researcher — live Claude runner.
KritiKaal CORE, US market, demand-only.

Calls claude-opus-4-8 with the web_search_20260209 server-side tool and
carries out the 3-technique OSINT methodology described in
A2_OSINT_RESEARCHER_SPEC.md.

Signature matches A2Handler in pipeline_runner.py:
    run_a2(a1_validated: dict, consignee_name: str, hs_group: str) -> dict
"""

from __future__ import annotations

import json
import re
import sys
from typing import Optional

import anthropic

# ---------------------------------------------------------------------------
# Section 1: constants
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-8"
MAX_TOKENS = 8000  # headroom for adaptive thinking + full JSON output
MAX_CONTINUATIONS = 5  # max pause_turn re-sends before giving up

TOOLS = [
    {"type": "web_search_20260209", "name": "web_search"},
]

# Verbatim system prompt from A2_OSINT_RESEARCHER_SPEC.md Section 4.
SYSTEM_PROMPT = """You are A2, the OSINT Brand Researcher for KritiKaal's US BoL intent engine. You
receive 1 VALIDATED lead from A1. Your job is to build the minimum verified
context for 1 phone call: who to ask for, what role they hold, how big the
company is, and whether the product line that went silent is still part of their
current business.

You have web search. You do not have memory of company staff, org charts, or
news from before this session. Anything you recall without a fresh source in
front of you is not evidence. Treat your own memory as a hypothesis to check,
never as an answer.

NON-NEGOTIABLE RULES:

1. Run the 3 techniques in order. Decision-maker dorking first, company-page
   dorking second, product-line dorking third. Each technique is 1 search
   query, not a free browse. Stop a technique once you have a qualifying
   result, move to the next.

2. Source every claim. Every populated field carries the exact source_url a
   search result returned. If you cannot point to that URL, the field is
   UNKNOWN. This applies to company size, headquarters, the decision-maker's
   name and title, and the product-line match.

3. Apply the 2-anchor rule to the decision-maker. Write a name and title only
   if 2 independent sources agree, or 1 source carries an explicit date within
   the last 12 months. A single undated snippet is not enough. Record which
   case applied as TWO_SOURCE, ONE_SOURCE_RECENT, or NONE.

4. A name under a different current employer is a departure, not a lead. If any
   source shows the person you found now works somewhere else, do not use that
   name. Either find a current name that clears rule 3, or return UNKNOWN.

5. Never construct a URL. A source_url is copied exactly from a search result.
   Never guess a LinkedIn profile slug, a press page path, or a company domain
   page that you have not seen returned by a query.

6. Product line is a finding either way. If the company's own site still lists
   the product category from the citation, report current_catalog_match true
   with the page URL. If it does not, report false with the page URL that shows
   their current catalog. Either answer is useful. UNKNOWN is only for when no
   page on their domain can be found at all.

7. UNKNOWN over guess, always. A founder will act on every non-UNKNOWN field you
   write. A wrong name costs more than a missing one.

8. Stay inside scope. You do not draft outreach copy. You do not analyze why the
   shipment gap happened. You do not contact anyone. You produce 1 context
   object for A3.

OUTPUT: Return only 1 JSON object in the output schema. No prose outside the
JSON. Every research query you ran goes in research_log, including queries that
returned nothing, so the founder can see what was checked."""


# ---------------------------------------------------------------------------
# Section 2: helpers
# ---------------------------------------------------------------------------

def _build_user_message(
    a1_validated: dict, consignee_name: str, hs_group: str
) -> str:
    """Format the A2 input payload as the user turn string."""
    payload = {
        "consignee_name": consignee_name,
        "hs_group": hs_group,
        "trigger": {
            "status": a1_validated.get("status", ""),
            "score": a1_validated.get("score", 0),
            "band": a1_validated.get("band", ""),
            "citation": a1_validated.get("citation", ""),
            "recomputed_days_since_last": a1_validated.get("recomputed_days_since_last", 0),
            "recomputed_cadence_days": a1_validated.get("recomputed_cadence_days", 0),
        },
    }
    return json.dumps(payload, indent=2)


def _extract_json(text: str) -> Optional[dict]:
    """
    Pull the first JSON object out of a text block.
    Tries bare parse, then a fenced code block, then a raw brace-delimited
    scan, in that order.
    """
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Last resort: find the outermost {...} block.
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(stripped[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _no_usable_context(
    consignee_name: str,
    hs_group: str,
    a1_validated: dict,
    reason: str,
) -> dict:
    """Return a NO_USABLE_CONTEXT shell so the pipeline holds the lead cleanly."""
    dsl = a1_validated.get("recomputed_days_since_last", 0)
    cad = a1_validated.get("recomputed_cadence_days", 0)
    return {
        "consignee_name": consignee_name,
        "hs_group": hs_group,
        "trigger_context": {
            "citation": a1_validated.get("citation", ""),
            "score": a1_validated.get("score", 0),
            "gap_summary": (
                f"{dsl} days silent on a {cad} day cadence, "
                f"China-origin {hs_group.lower().replace('_', ' ')} line"
            ),
        },
        "company_profile": {
            "size_estimate": "UNKNOWN",
            "size_source_url": "UNKNOWN",
            "headquarters": "UNKNOWN",
            "hq_source_url": "UNKNOWN",
        },
        "decision_maker": {
            "name": "UNKNOWN",
            "title": "UNKNOWN",
            "profile_url": "UNKNOWN",
            "recency_evidence": "UNKNOWN",
            "corroboration": "NONE",
            "confidence": "UNKNOWN",
        },
        "product_line_context": {
            "shipped_product_description": "UNKNOWN",
            "current_catalog_match": "UNKNOWN",
            "catalog_source_url": "UNKNOWN",
        },
        "research_log": [
            {"query": "RUNNER_ERROR", "result_summary": reason, "used": False}
        ],
        "overall_status": "NO_USABLE_CONTEXT",
    }


# ---------------------------------------------------------------------------
# Section 3: main runner
# ---------------------------------------------------------------------------

def run_a2(a1_validated: dict, consignee_name: str, hs_group: str) -> dict:
    """
    Live A2 runner. Calls claude-opus-4-8 with web_search_20260209 and returns
    the A2 context object shaped per A2_OSINT_RESEARCHER_SPEC.md Section 5.

    Signature matches A2Handler in pipeline_runner.py.
    """
    if a1_validated.get("status") != "VALIDATED":
        return {
            "consignee_name": consignee_name,
            "hs_group": hs_group,
            "overall_status": "REJECTED",
            "reason": "TRIGGER_NOT_VALIDATED",
        }

    client = anthropic.Anthropic()
    user_message = _build_user_message(a1_validated, consignee_name, hs_group)
    messages: list = [{"role": "user", "content": user_message}]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Handle pause_turn: server-side search loop hit its 10-iteration limit.
        # Re-send with the trailing server_tool_use block intact; the API resumes
        # automatically without an extra user message.
        continuations = 0
        while response.stop_reason == "pause_turn" and continuations < MAX_CONTINUATIONS:
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response.content},
            ]
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            continuations += 1

    except anthropic.APIError as exc:
        return _no_usable_context(
            consignee_name, hs_group, a1_validated,
            f"Anthropic API error: {exc}",
        )
    except Exception as exc:  # noqa: BLE001
        return _no_usable_context(
            consignee_name, hs_group, a1_validated,
            f"Unexpected error: {exc}",
        )

    # Extract the text blocks from the final response. Thinking blocks are
    # present when adaptive thinking fires but are not JSON — skip them.
    text_blocks = [b.text for b in response.content if b.type == "text"]
    if not text_blocks:
        return _no_usable_context(
            consignee_name, hs_group, a1_validated,
            "A2 produced no text output",
        )

    raw_text = "\n".join(text_blocks)
    result = _extract_json(raw_text)

    if result is None:
        return _no_usable_context(
            consignee_name, hs_group, a1_validated,
            f"A2 output could not be parsed as JSON. Raw (first 500 chars): {raw_text[:500]}",
        )

    # Inject pass-through fields that the pipeline expects but the LLM may omit.
    result.setdefault("consignee_name", consignee_name)
    result.setdefault("hs_group", hs_group)
    result.setdefault("overall_status", "NO_USABLE_CONTEXT")

    return result


# ---------------------------------------------------------------------------
# Section 4: standalone smoke test
# ---------------------------------------------------------------------------

def _smoke_test() -> None:
    """
    Quick end-to-end call against the real API using the Lo & Sons worked
    example from the spec. Prints the A2 context object and exits.

    Usage:
        python a2_osint_runner.py --smoke-test
        python a2_osint_runner.py --smoke-test --consignee "Brand Name" --hs-group HS_GROUP
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="A2 OSINT Brand Researcher — live Claude runner."
    )
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run the built-in smoke test and exit.")
    parser.add_argument("--consignee", default="Lo & Sons",
                        help="Consignee name (default: 'Lo & Sons')")
    parser.add_argument("--hs-group", default="LEATHER_BAGS_CASES",
                        help="HS group string (default: LEATHER_BAGS_CASES)")
    args = parser.parse_args()

    if not args.smoke_test:
        parser.print_help()
        sys.exit(0)

    mock_a1 = {
        "status": "VALIDATED",
        "score": 89,
        "band": "HOT",
        "citation": "2026-03-22 | China | 4202.21 | Cowhide Leather Handbag | BOL1007",
        "recomputed_days_since_last": 85,
        "recomputed_cadence_days": 45,
    }

    print(f"A2 OSINT smoke test: {args.consignee} / {args.hs_group}")
    print("=" * 72)
    result = run_a2(mock_a1, args.consignee, args.hs_group)
    print(json.dumps(result, indent=2))

    status = result.get("overall_status", "MISSING")
    dm_conf = result.get("decision_maker", {}).get("confidence", "UNKNOWN")
    print(f"\noverall_status   : {status}")
    print(f"decision_maker   : {result.get('decision_maker', {}).get('name', 'UNKNOWN')} ({dm_conf})")
    cp = result.get("company_profile", {})
    print(f"company_profile  : {cp.get('size_estimate', 'UNKNOWN')} | {cp.get('headquarters', 'UNKNOWN')}")
    pl = result.get("product_line_context", {})
    print(f"catalog_match    : {pl.get('current_catalog_match', 'UNKNOWN')}")
    rlog = result.get("research_log", [])
    print(f"research_log     : {len(rlog)} entr{'y' if len(rlog) == 1 else 'ies'}")


if __name__ == "__main__":
    _smoke_test()
