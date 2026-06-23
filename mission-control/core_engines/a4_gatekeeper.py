"""
A4 Gatekeeper, deterministic thin runner.
Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only.

This is the deterministic encoding of A4_GATEKEEPER_SPEC.md. A4 runs 4 ordered
checks against an A3 draft and the A1/A2 baseline data it was built from. A4
proves the draft is true, on-voice, and correctly priced, or it destroys the
draft and returns every violation with an exact quote and rule citation.

In production the FACT check and VOICE-DNA judgment run inside a Claude
sub-agent driven by the verbatim system prompt in the spec. This runner encodes
the same rules as deterministic regex/string passes so the gatekeeper contract
can be stress-tested before the model is wired in. The model and this runner
must agree by construction.

AIR-GAP CONTRACT: standalone. No imports from kritikaal-hub, no database, no
network.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Section 1: constants
# ---------------------------------------------------------------------------

# VOICE-1: en-dash U+2013 and em-dash U+2014 are both banned.
_DASH_CHARS = "–—"

# VOICE-2: adjective-before-noun-before-number pattern.
# Catches "a small batch of 30 units", "a small starter pack of 30 units".
# The number is pushed to the end instead of leading the noun phrase.
_VOICE2_INVERSION = re.compile(
    r"\b(?:a|an)\s+(?:small|large|big|few|several|many|tiny|substantial|growing)"
    r"\s+(?:\w+(?:\s+\w+)?\s+)?(?:of\s+\d+\b)",
    re.IGNORECASE,
)

# VOICE-2 secondary: "a small starter pack" with no leading number at all.
_VOICE2_PACK_NO_NUMBER = re.compile(
    r"\b(?:a|an)\s+(?:small|large|big|few|tiny)\s+(?:starter\s+pack|starter\s+kit)\b",
    re.IGNORECASE,
)

# VOICE-3: generic AI sales jargon, enforced literally, case-insensitive.
_JARGON: list[str] = [
    "i hope this email finds you well",
    "i hope this finds you well",
    "i wanted to reach out",
    "i came across your company",
    "i noticed that you",
    "i noticed your",
    "in today's fast-paced market",
    "game-changer",
    "game changer",
    "synergy",
    "synergies",
    "circle back",
    "touch base",
    "leverage",
    "unlock your potential",
    "take your business to the next level",
    "seamlessly",
    "seamless",
    "revolutionize",
    "i'd love to connect",
    "no-brainer",
    "move the needle",
    "low-hanging fruit",
    "reaching out because",
    "just wanted to follow up",
]

# BIZ-1: banned commercial "free" equivalents.
_NO_COST_PHRASES = [r"\bno\s+cost\b", r"\bon\s+us\b", r"\bcomplimentary\b"]

# BIZ-2: sample-offer patterns (outside "Golden Sample Trap" context).
_SAMPLE_OFFER_PATTERNS = [
    re.compile(r"\bsend\s+(?:you\s+)?(?:a\s+)?sample\b", re.IGNORECASE),
    re.compile(r"\boffer\s+(?:you\s+)?(?:a\s+)?sample\b", re.IGNORECASE),
    re.compile(r"\bfree\s+sample\b", re.IGNORECASE),
    re.compile(r"\bcomplimentary\s+sample\b", re.IGNORECASE),
    re.compile(r"\bsample\s+at\s+no\s+cost\b", re.IGNORECASE),
    re.compile(r"\bsample\s+kit\b", re.IGNORECASE),
]

# STRUCT-2: 20-minute call CTA.
_CTA_PATTERN = re.compile(r"20.?minute\s+call|20.?min\.?\s+call", re.IGNORECASE)

# STRUCT-3: markdown formatting.
_MARKDOWN_PATTERN = re.compile(
    r"(?:^|\n)\s*#{1,6}\s|(?:^|\n)\s*[-*]\s|\*{2}", re.MULTILINE
)

# Salutation opener — first line to skip in VOICE-4 check.
_SALUTATION = re.compile(r"^(?:hi|hello|dear|good morning|good afternoon)\b", re.IGNORECASE)

# Sentence split on terminal punctuation followed by whitespace.
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


# ---------------------------------------------------------------------------
# Section 2: LineEdit dataclass
# ---------------------------------------------------------------------------

@dataclass
class LineEdit:
    location: str
    quote: str
    rule_broken: str
    requirement: str

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "quote": self.quote,
            "rule_broken": self.rule_broken,
            "requirement": self.requirement,
        }


# ---------------------------------------------------------------------------
# Section 3: Check 1 — Fact Check
# ---------------------------------------------------------------------------

def _check_facts(draft: dict, a1: dict, a2: dict) -> list[LineEdit]:
    edits: list[LineEdit] = []
    body: str = draft.get("email_body", "")
    subject: str = draft.get("subject_line", "")
    full_text: str = subject + "\n" + body

    # FACT-3: both gap numbers from a1_baseline must appear in the draft.
    dsl = a1.get("recomputed_days_since_last")
    cad = a1.get("recomputed_cadence_days")
    for label, val in [("recomputed_days_since_last", dsl), ("recomputed_cadence_days", cad)]:
        if val is not None and str(int(val)) not in full_text:
            edits.append(LineEdit(
                location="email_body",
                quote=body[:60].strip(),
                rule_broken="FACT-3",
                requirement=(
                    f"a1_baseline.{label}={int(val)} must appear as a number in the draft. "
                    "The gap observation is the first sentence and must be numeric."
                ),
            ))

    # FACT-4: addressing must match a2_baseline.overall_status.
    overall_status = a2.get("overall_status", "")
    dm = a2.get("decision_maker", {})
    dm_name = dm.get("name", "UNKNOWN")
    dm_confidence = dm.get("confidence", "UNKNOWN")
    body_lower = body.lower()

    if overall_status == "PARTIAL_CONTEXT":
        if dm_name and dm_name != "UNKNOWN" and dm_name.lower() in body_lower:
            edits.append(LineEdit(
                location="email_body",
                quote=dm_name,
                rule_broken="FACT-4",
                requirement=(
                    "a2_baseline.overall_status is PARTIAL_CONTEXT: decision_maker is UNKNOWN. "
                    "Draft must address a role, not a named individual."
                ),
            ))
    elif overall_status == "READY_FOR_A3":
        if (
            dm_name and dm_name != "UNKNOWN"
            and dm_confidence in ("HIGH", "MEDIUM")
            and dm_name.split()[0].lower() not in body_lower
        ):
            edits.append(LineEdit(
                location="email_body",
                quote="[salutation line]",
                rule_broken="FACT-4",
                requirement=(
                    f"a2_baseline.overall_status is READY_FOR_A3 with decision_maker "
                    f"confidence={dm_confidence}. Draft must address {dm_name} by first name."
                ),
            ))

    return edits


# ---------------------------------------------------------------------------
# Section 4: Check 2 — Voice-DNA Check
# ---------------------------------------------------------------------------

def _check_voicedna(draft: dict, a1: dict) -> list[LineEdit]:
    edits: list[LineEdit] = []
    body: str = draft.get("email_body", "")
    subject: str = draft.get("subject_line", "")
    full_text: str = subject + "\n" + body

    # VOICE-1: em-dash / en-dash scan.
    for char in _DASH_CHARS:
        idx = full_text.find(char)
        if idx != -1:
            snippet = full_text[max(0, idx - 20):idx + 21].replace(char, f"[{char}]")
            edits.append(LineEdit(
                location="subject_line or email_body",
                quote=snippet.strip(),
                rule_broken="VOICE-1",
                requirement=(
                    "No em-dash or en-dash is permitted anywhere. "
                    "Replace with a period, colon, comma, or parentheses."
                ),
            ))
            break

    # VOICE-2: adjective-before-noun-before-number inversion.
    for pattern in (_VOICE2_INVERSION, _VOICE2_PACK_NO_NUMBER):
        for m in pattern.finditer(body):
            edits.append(LineEdit(
                location="email_body",
                quote=m.group(0),
                rule_broken="VOICE-2",
                requirement=(
                    "The number must precede the adjective and noun. "
                    "Write '30-unit starter pack', not 'a small starter pack of 30 units'."
                ),
            ))

    # VOICE-3: jargon scan, verbatim, case-insensitive.
    full_lower = full_text.lower()
    seen: set[str] = set()
    for phrase in _JARGON:
        if phrase in full_lower and phrase not in seen:
            seen.add(phrase)
            edits.append(LineEdit(
                location="email_body",
                quote=f"'{phrase}'",
                rule_broken="VOICE-3",
                requirement=(
                    f"Generic AI sales jargon detected: '{phrase}'. "
                    "Eliminate it. The draft opens with the gap observation, not warm-up phrases."
                ),
            ))

    # VOICE-4: first substantive sentence must be the gap observation.
    dsl = a1.get("recomputed_days_since_last")
    lines = [ln for ln in body.split("\n") if ln.strip()]
    first_substantive: Optional[str] = None
    for ln in lines:
        if _SALUTATION.match(ln.strip()):
            continue
        first_substantive = ln.strip()
        break

    if first_substantive and dsl is not None:
        if str(int(dsl)) not in first_substantive:
            edits.append(LineEdit(
                location="email_body",
                quote=first_substantive[:80],
                rule_broken="VOICE-4",
                requirement=(
                    f"The first substantive sentence must state the gap observation "
                    f"and include the number {int(dsl)}. "
                    "No greeting or self-introduction before it."
                ),
            ))

    # VOICE-5: word count (120-180) and sentence length (<= 30 words).
    words = body.split()
    wc = len(words)
    if wc < 120 or wc > 180:
        edits.append(LineEdit(
            location="email_body",
            quote=f"{wc} words",
            rule_broken="VOICE-5",
            requirement="email_body must be 120 to 180 words.",
        ))

    for sent in _SENT_SPLIT.split(body):
        sw = sent.split()
        if len(sw) > 30:
            edits.append(LineEdit(
                location="email_body",
                quote=" ".join(sw[:12]) + "...",
                rule_broken="VOICE-5",
                requirement=f"Sentence is {len(sw)} words, over the 30-word limit. Break it.",
            ))

    return edits


# ---------------------------------------------------------------------------
# Section 5: Check 3 — Business Model Check
# ---------------------------------------------------------------------------

def _check_business_model(draft: dict) -> list[LineEdit]:
    edits: list[LineEdit] = []
    body: str = draft.get("email_body", "")
    body_lower = body.lower()

    # BIZ-1a: standalone "free" (not part of "risk-free").
    for m in re.finditer(r"\bfree\b", body_lower):
        preceding = body_lower[max(0, m.start() - 5):m.start()]
        if preceding.endswith("risk-") or "risk-" in preceding:
            continue
        snippet = body[max(0, m.start() - 20):m.end() + 20].strip()
        edits.append(LineEdit(
            location="email_body",
            quote=snippet,
            rule_broken="BIZ-1",
            requirement=(
                "The word 'free' is banned in any commercial context. "
                "The starter pack is paid and credited back, not free. "
                "Use 'risk-free starter pack' only if the credit mechanism is also stated."
            ),
        ))
        break  # report first occurrence

    # BIZ-1b: equivalent banned phrases.
    for pattern_str in _NO_COST_PHRASES:
        m = re.search(pattern_str, body_lower)
        if m:
            snippet = body[max(0, m.start() - 10):m.end() + 10].strip()
            edits.append(LineEdit(
                location="email_body",
                quote=snippet,
                rule_broken="BIZ-1",
                requirement=(
                    "'no cost', 'on us', and 'complimentary' are banned equivalents of 'free'. "
                    "The starter pack is a paid, creditable engagement, not a giveaway."
                ),
            ))

    # BIZ-2: sample offered (outside named-mechanism context).
    for pattern in _SAMPLE_OFFER_PATTERNS:
        m = pattern.search(body)
        if m:
            snippet = body[max(0, m.start() - 10):m.end() + 10].strip()
            edits.append(LineEdit(
                location="email_body",
                quote=snippet,
                rule_broken="BIZ-2",
                requirement=(
                    "No sample of any kind may be offered. "
                    "The only permitted commercial mechanism is the risk-free starter pack: "
                    "a paid small production run with 100 percent of the cost credited "
                    "against the first 300-unit-or-more production order."
                ),
            ))
            break

    # BIZ-3/BIZ-4: if "starter pack" is present, both required elements must appear.
    if "starter pack" in body_lower:
        # Unit count: any integer between 20 and 50 within 150 chars of "starter pack".
        sp_idx = body_lower.find("starter pack")
        window = body_lower[max(0, sp_idx - 150):sp_idx + 200]
        count_match = re.search(r"\b([2-4][0-9]|50)\b", window)
        if not count_match:
            edits.append(LineEdit(
                location="email_body",
                quote="starter pack [unit count not found]",
                rule_broken="BIZ-3",
                requirement=(
                    "The starter pack must state a specific unit count between 20 and 50. "
                    "State it as a number before the noun: '30-unit starter pack'."
                ),
            ))

        has_credit = any(
            phrase in body_lower
            for phrase in ["credited", "100 percent", "100%", "full cost credited"]
        )
        if not has_credit:
            edits.append(LineEdit(
                location="email_body",
                quote="starter pack [credit mechanism not found]",
                rule_broken="BIZ-3",
                requirement=(
                    "The starter pack must explicitly state that 100 percent of its cost "
                    "is credited against the first production order of 300 units or more."
                ),
            ))

        # BIZ-4: production threshold must be 300 units or more.
        if "300" not in body_lower:
            edits.append(LineEdit(
                location="email_body",
                quote="starter pack [300-unit threshold not found]",
                rule_broken="BIZ-4",
                requirement=(
                    "The production order threshold must be stated as 300 units or more."
                ),
            ))

    return edits


# ---------------------------------------------------------------------------
# Section 6: Check 4 — Structural Check
# ---------------------------------------------------------------------------

def _check_structural(draft: dict) -> list[LineEdit]:
    edits: list[LineEdit] = []
    body: str = draft.get("email_body", "")
    subject: str = draft.get("subject_line", "")
    body_lower = body.lower()

    # STRUCT-1: negative qualifier must be present.
    neg_patterns = [
        r"\bnot\s+for\s+brands\b",
        r"\bnot\s+for\s+companies\b",
        r"\bnot\s+designed\s+for\b",
        r"\bthis\s+(?:isn.t|is\s+not)\s+for\b",
        r"\bdoes\s+not\s+work\s+for\b",
        r"\bnot\s+yet\s+running\b",
    ]
    if not any(re.search(p, body_lower) for p in neg_patterns):
        edits.append(LineEdit(
            location="email_body",
            quote="[no negative qualifier found]",
            rule_broken="STRUCT-1",
            requirement=(
                "The email must contain 1 sentence stating who this is not for: "
                "brands not yet running production orders of 300 units or more "
                "on this product line."
            ),
        ))

    # STRUCT-2: 20-minute call CTA must be present.
    if not _CTA_PATTERN.search(body):
        edits.append(LineEdit(
            location="email_body",
            quote="[no 20-minute call CTA found]",
            rule_broken="STRUCT-2",
            requirement=(
                "The email must end with a request for a 20-minute call "
                "to discuss whether a starter pack fits."
            ),
        ))

    # STRUCT-3: no markdown formatting.
    md = _MARKDOWN_PATTERN.search(body)
    if md:
        edits.append(LineEdit(
            location="email_body",
            quote=body[md.start():md.start() + 30].strip(),
            rule_broken="STRUCT-3",
            requirement="No markdown (subheadings, bullets, bold). Plain sentences only.",
        ))

    # STRUCT-4: subject line <= 60 characters.
    if len(subject) > 60:
        edits.append(LineEdit(
            location="subject_line",
            quote=subject,
            rule_broken="STRUCT-4",
            requirement=f"subject_line is {len(subject)} characters. Must be 60 or under.",
        ))

    return edits


# ---------------------------------------------------------------------------
# Section 7: Main audit function
# ---------------------------------------------------------------------------

def run_a4(draft: dict, a1_baseline: dict, a2_baseline: dict) -> dict:
    """
    Execute the 4-check A4 audit on 1 draft.

    Returns PASS with an empty line_level_edits list, or FAIL with every
    violation found across all 4 checks. A4 never stops at the first violation.
    """
    if not draft or a1_baseline is None or a2_baseline is None:
        return {
            "status": "FAIL",
            "line_level_edits": [
                LineEdit(
                    location="input",
                    quote="",
                    rule_broken="INPUT-1",
                    requirement=(
                        "All 3 of draft, a1_baseline, and a2_baseline must be present. "
                        "1 or more were missing or empty."
                    ),
                ).to_dict()
            ],
        }

    edits: list[LineEdit] = []
    edits.extend(_check_facts(draft, a1_baseline, a2_baseline))
    edits.extend(_check_voicedna(draft, a1_baseline))
    edits.extend(_check_business_model(draft))
    edits.extend(_check_structural(draft))

    if edits:
        return {"status": "FAIL", "line_level_edits": [e.to_dict() for e in edits]}
    return {"status": "PASS", "line_level_edits": []}


# ---------------------------------------------------------------------------
# Section 8: Self-test — Section 5 worked examples from A4_GATEKEEPER_SPEC.md
# ---------------------------------------------------------------------------

_A1_BASELINE = {
    "status": "VALIDATED",
    "score": 89,
    "citation": "2026-03-22 | China | 4202.21 | Cowhide Leather Handbag | BOL1007",
    "recomputed_days_since_last": 85,
    "recomputed_cadence_days": 45,
}

_A2_BASELINE_PARTIAL = {
    "consignee_name": "Lo & Sons",
    "company_profile": {
        "size_estimate": "11 to 50 employees",
        "headquarters": "Brooklyn, New York, United States",
    },
    "decision_maker": {
        "name": "UNKNOWN",
        "title": "UNKNOWN",
        "confidence": "UNKNOWN",
    },
    "product_line_context": {
        "shipped_product_description": "Cowhide Leather Handbag",
        "current_catalog_match": True,
    },
    "overall_status": "PARTIAL_CONTEXT",
}

# PASS DRAFT: Lo & Sons, Section 5.1 of the spec.
# Voice-DNA compliant, all fact numbers present, starter pack correctly framed.
_PASS_DRAFT = {
    "subject_line": "85-day gap on your cowhide leather handbag line",
    "email_body": (
        "Hi Sourcing Team,\n\n"
        "85 days have passed since your last China-origin shipment of cowhide leather "
        "handbags, against a 45 day average over your recent shipments. That is nearly "
        "twice your normal reorder cycle, inside the window where brands in the Missing "
        "Middle absorb real sourcing friction.\n\n"
        "KritiKaal operates as a Single Point of Accountability for leather goods "
        "production in India. We manage the factory cluster and compliance stack for the "
        "cowhide handbag line your shipment data points to, from prototype through to "
        "AQL 2.5-certified production runs.\n\n"
        "This is not for brands not yet running production orders of 300 units or more "
        "on this category.\n\n"
        "If the scale fits, we offer a 30-unit starter pack of your exact SKU. "
        "100 percent of that cost is credited against your first production order of "
        "300 units or more, placed within 90 days.\n\n"
        "Would a 20-minute call this week to discuss whether a starter pack fits your "
        "current timeline be useful?"
    ),
}

# FAIL DRAFT: planted violations from spec Section 5.2.
# Violations: VOICE-1 (em-dash), VOICE-3 (multiple jargon hits), VOICE-4
# (greeting before gap), FACT-3 (gap numbers absent), BIZ-1 (free + no cost),
# BIZ-2 (sample offered), VOICE-2 (adjective-number inversion), STRUCT-1
# (no negative qualifier), STRUCT-2 (no 20-minute call CTA).
_FAIL_DRAFT = {
    "subject_line": "Quick question about your supply chain",
    "email_body": (
        "Hi Team,\n\n"
        "I hope this finds you well — I wanted to reach out because I noticed your "
        "shipping has slowed down a bit recently. We'd love to send you a free sample "
        "of our cowhide leather handbag work, as we believe this could be a real "
        "game-changer for your sourcing.\n\n"
        "We offer a small batch of 30 brands a complimentary starter kit at no cost, "
        "which will revolutionize how you think about manufacturing accountability. "
        "Our process is seamless, and we help brands like yours leverage our factory "
        "relationships to move the needle on quality and delivery.\n\n"
        "We work with growing brands who want to circle back with reliable production "
        "partnerships. Touch base with us anytime and we can connect on what works.\n\n"
        "Warm regards,\n"
        "The KritiKaal Team"
    ),
}


def _stress_test() -> None:
    print("A4 GATEKEEPER STRESS TEST, Section 5 worked examples")
    print("=" * 72)

    # ---- PASS case ----
    print("\n[CASE 1: Lo & Sons clean draft, expected PASS]")
    result_pass = run_a4(_PASS_DRAFT, _A1_BASELINE, _A2_BASELINE_PARTIAL)
    print(f"  status: {result_pass['status']}")
    if result_pass["line_level_edits"]:
        for e in result_pass["line_level_edits"]:
            print(f"  UNEXPECTED violation: {e['rule_broken']} | {e['quote']}")
    else:
        print("  0 violations found. Draft cleared.")

    assert result_pass["status"] == "PASS", (
        f"PASS case failed: {result_pass['line_level_edits']}"
    )
    assert result_pass["line_level_edits"] == []

    # ---- FAIL case ----
    print("\n[CASE 2: Planted violations draft, expected FAIL]")
    result_fail = run_a4(_FAIL_DRAFT, _A1_BASELINE, _A2_BASELINE_PARTIAL)
    print(f"  status: {result_fail['status']}")
    print(f"  violations found: {len(result_fail['line_level_edits'])}")
    print()

    rules_found = {e["rule_broken"] for e in result_fail["line_level_edits"]}
    for edit in result_fail["line_level_edits"]:
        print(f"  [{edit['rule_broken']}]")
        print(f"    quote      : {edit['quote'][:60]}")
        print(f"    requirement: {edit['requirement'][:80]}")
        print()

    # Assert every planted violation category was caught.
    assert result_fail["status"] == "FAIL"
    assert "VOICE-1" in rules_found, "missed em-dash (VOICE-1)"
    assert "VOICE-2" in rules_found, "missed adjective-number inversion (VOICE-2)"
    assert "VOICE-3" in rules_found, "missed jargon (VOICE-3)"
    assert "VOICE-4" in rules_found, "missed greeting-before-gap (VOICE-4)"
    assert "FACT-3" in rules_found, "missed missing gap numbers (FACT-3)"
    assert "BIZ-1" in rules_found, "missed standalone 'free' (BIZ-1)"
    assert "BIZ-2" in rules_found, "missed sample offer (BIZ-2)"
    assert "STRUCT-1" in rules_found, "missed missing negative qualifier (STRUCT-1)"
    assert "STRUCT-2" in rules_found, "missed missing 20-minute CTA (STRUCT-2)"

    # ---- Full FAIL output JSON ----
    print("=" * 72)
    print("FULL FAIL JSON OUTPUT:")
    print(json.dumps(result_fail, indent=2))

    print("\n" + "=" * 72)
    print("self-test passed: PASS case cleared cleanly, all planted violations caught")


if __name__ == "__main__":
    _stress_test()
