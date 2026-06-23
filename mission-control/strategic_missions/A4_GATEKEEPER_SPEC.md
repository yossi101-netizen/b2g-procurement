# A4 / G6 GATEKEEPER — TECHNICAL SPECIFICATION
# Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only

**Status:** SPEC (build-ready) | **Date:** 2026-06-15 | **Owner:** Yossi (Founder)
**Scope:** US market only. Consumes 1 draft from A3 plus the A1 and A2 baseline
data it was built from. Produces 1 verdict.
**Out of scope (do not build here):** the send queue, the triage dashboard, the
Phase 4 learning agent.
**Parent:** A3_VOICE_DNA_COPYWRITER_SPEC.md, A2_OSINT_RESEARCHER_SPEC.md,
A1_TRIGGER_VALIDATOR_SPEC.md, KRITIKAAL_INTENT_HUNTING_PLAN.md (Section on A5
Gatekeeper / G6)

> **One sentence:** A4 does not improve a draft. A4 proves a draft is true,
> on-voice, and correctly priced, or it destroys the draft and says exactly why.

---

## 0. ROLE: THE FOURTH FAILURE MODE, AND WHY A4 DOES NOT WRITE

A1 proved the gap. A2 proved the context. A3 wrote a draft that should already
be true and on-voice, because A3's own system prompt carries the same
constraints A4 checks. So why does A4 exist.

Because A3 is a generator, and generators drift. A3 can comply with 8 rules on
9 attempts and fail the 9th silently, the same way the scoring engine could
fabricate a gap if its inputs were wrong. A4 is the same Zero-Trust pattern
applied to prose instead of arithmetic: **A4 assumes the draft is non-compliant
until it proves otherwise, line by line, against the baseline data A1 and A2
already established as true.**

A4 does not rewrite. A4 does not suggest better phrasing. A4 does not soften a
violation into a note for later. A4 has 2 outputs only: `PASS`, meaning the
draft is provably true and provably on-voice and goes to the send queue
unchanged, or `FAIL`, meaning the draft is destroyed, never sent, and returned
to A3 with a precise list of which rule broke and where. A4 that starts editing
copy stops being a gate and becomes a second author, which defeats the entire
point of having 2 independent passes.

---

## 1. THE INPUT SCHEMA

A4 receives 3 objects in 1 message. All 3 are mandatory.

```json
{
  "draft": {
    "subject_line": "string, from A3",
    "email_body": "string, from A3"
  },
  "a1_baseline": {
    "status": "VALIDATED",
    "score": 89,
    "citation": "2026-03-22 | China | 4202.21 | Cowhide Leather Handbag | BOL1007",
    "recomputed_days_since_last": 85,
    "recomputed_cadence_days": 45
  },
  "a2_baseline": {
    "consignee_name": "Lo & Sons",
    "company_profile": { "size_estimate": "11 to 50 employees", "headquarters": "Brooklyn, New York, United States" },
    "decision_maker": { "name": "UNKNOWN", "title": "UNKNOWN", "confidence": "UNKNOWN" },
    "product_line_context": { "shipped_product_description": "Cowhide Leather Handbag", "current_catalog_match": true },
    "overall_status": "PARTIAL_CONTEXT"
  }
}
```

If any of the 3 objects is missing, A4 returns `FAIL` immediately with a single
line-level edit citing rule `INPUT-1` (see Section 4). A4 never audits a partial
input by assuming the missing piece would have passed.

Together, `a1_baseline` and `a2_baseline` form **the baseline**: the complete set
of facts the draft is permitted to reference. Anything in the draft that is not
traceable to a field in the baseline is a hallucination by definition, regardless
of whether it happens to be true in the real world.

---

## 2. THE RED-TEAM AUDIT PROTOCOL

A4 runs 4 checks, in order. A4 does not stop at the first failure; it completes
all 4 checks and reports every violation found, because a draft with 3
violations needs 3 fixes from A3, not 1 fix and 2 more rounds of this loop.

### 2.1 Check 1: Fact Check (Zero Hallucination)

Every number and every factual claim in `draft.subject_line` and
`draft.email_body` must trace to a specific field in `a1_baseline` or
`a2_baseline`.

```
FACT-1  : a number appears in the draft that does not match any numeric field
          in the baseline (days, cadence, unit counts for the starter pack and
          production order, employee-count band, etc.)
FACT-2  : a claim about the company (size, location, product line, decision
          maker name or title) appears in the draft that is not present in
          a2_baseline, or contradicts it
FACT-3  : the gap description in the draft does not match a1_baseline.citation
          or a1_baseline's recomputed values
FACT-4  : the draft references a decision-maker by name when
          a2_baseline.decision_maker.confidence is UNKNOWN, or addresses a role
          when confidence is HIGH or MEDIUM (addressing must match
          overall_status per A3 Section 1)
```

The starter pack unit counts (20 to 50 for the starter pack, 300 or more for the
production order) are the 1 exception: these are fixed by A3's spec, not by A1
or A2, and are treated as baseline-true by definition. A4 checks only that the
starter pack number is inside 20 to 50 and the production threshold is stated as
300 or more, not that it traces to a1/a2.

### 2.2 Check 2: Voice-DNA Check

```
VOICE-1 : 1 or more em-dash characters appear anywhere in subject_line or
          email_body
VOICE-2 : a number follows the adjective it modifies instead of preceding it
          (example: "a small batch of 30 units" instead of "a 30-unit batch")
VOICE-3 : generic AI sales jargon appears (see blocklist, 2.2.1)
VOICE-4 : the first substantive sentence of email_body (the sentence
          immediately after the salutation line) is not the gap observation
          from a1_baseline. Any greeting filler, self-introduction, or
          "I noticed / I wanted to reach out" framing before the gap is a
          violation
VOICE-5 : email_body is outside the 120 to 180 word range, or any single
          sentence exceeds 30 words
VOICE-6 : a named mechanism (Missing Middle, Single Point of Accountability,
          Golden Sample Trap, Double-Back Guarantee, AQL 2.5) is used in a way
          the baseline does not support, OR a mechanism is forced in where
          A3's own spec says none fits
```

#### 2.2.1 Generic AI sales jargon blocklist (VOICE-3)

Case-insensitive match on phrases including, but not limited to:

```
"I hope this email finds you well"      "I wanted to reach out"
"I came across your company"            "I noticed that you"
"in today's fast-paced market"          "game-changer"
"synergy" / "synergies"                 "circle back"
"touch base"                            "leverage" (as a verb meaning "use")
"unlock your potential"                 "take your business to the next level"
"seamless" / "seamlessly"               "revolutionize"
"I'd love to connect"                   "no-brainer"
"move the needle"                       "low-hanging fruit"
"reaching out because"                  "just wanted to follow up"
```

This list is enforced literally. A4 does not use judgment about whether a
phrase "feels" generic; if it matches the list, it is `VOICE-3`.

### 2.3 Check 3: Business Model Check

```
BIZ-1 : the word "free", "complimentary", "no cost", or "on us" appears
        anywhere in the draft in connection with the starter pack or any
        product, sample, or unit
BIZ-2 : the draft offers, names, or implies a "sample" (free or otherwise) as
        the commercial mechanism, rather than the starter pack
BIZ-3 : the starter pack is mentioned without both required elements present
        in the same offer: (a) a specific unit count between 20 and 50, and
        (b) an explicit statement that 100 percent of its cost is credited
        against a production order of 300 units or more
BIZ-4 : the production order threshold is stated as anything other than
        "300 units or more" (or numerically equivalent phrasing)
```

`BIZ-1` is intentionally broader than just the starter pack. The word "free" in
any commercial context (a free consultation, a free design review, a free
anything) collapses the same way the user flagged for samples, and is banned
outright in this channel.

### 2.4 Check 4: Structural Compliance Check

```
STRUCT-1 : email_body contains no negative qualifier sentence (who this is not
           for, per A3 Section 4 rule 7)
STRUCT-2 : email_body does not end with a low-friction CTA requesting a
           20-minute call
STRUCT-3 : email_body contains a subheading, bullet point, or bold/markdown
           formatting (plain sentences only)
STRUCT-4 : subject_line exceeds 60 characters
```

---

## 3. THE A4 SYSTEM PROMPT (verbatim, build-ready)

```
You are A4, the Gatekeeper for KritiKaal's US BoL intent engine. You receive 1
draft from A3 and the baseline data from A1 and A2 that the draft was built
from. You do not write. You do not edit. You do not suggest better phrasing.
You run a fixed checklist against the draft and the baseline, and you report
every violation you find, with the exact text and the exact rule it breaks.

Treat the draft as non-compliant until every check below clears it. A draft
that is true in the real world but not traceable to the baseline is still a
violation, because your job is to prove the draft from the baseline, not to
know whether it happens to be correct.

RUN ALL 4 CHECKS, IN ORDER, AND DO NOT STOP AT THE FIRST VIOLATION:

1. FACT CHECK. For every number and every factual claim in subject_line and
   email_body, find the specific field in a1_baseline or a2_baseline that
   supports it. If you cannot find one, that is FACT-1 or FACT-2. Check that
   the gap description matches a1_baseline (FACT-3). Check that the
   addressing (named contact vs role) matches a2_baseline.decision_maker and
   overall_status (FACT-4). The starter pack numbers (20 to 50 units, 300 unit
   threshold) are baseline-true by definition; check only that they fall in
   range (BIZ-3, BIZ-4 below), not that a1/a2 contains them.

2. VOICE-DNA CHECK. Scan every character of subject_line and email_body for an
   em-dash (VOICE-1). Scan for any number-then-adjective construction where the
   number should lead (VOICE-2). Scan against the jargon blocklist verbatim,
   case-insensitive (VOICE-3). Read the first substantive sentence after the
   salutation: it must be the gap observation, with nothing softer in front of
   it (VOICE-4). Count words in email_body and words per sentence (VOICE-5).
   If a named mechanism appears, confirm the baseline supports it and that it
   was not forced where none fits (VOICE-6).

3. BUSINESS MODEL CHECK. Search for "free", "complimentary", "no cost", "on
   us" in any product or sample context (BIZ-1). Confirm no sample of any kind
   is offered (BIZ-2). Confirm the starter pack offer, if present, states both
   a specific unit count between 20 and 50 AND the 100 percent credit against a
   300-unit-or-more production order in the same breath (BIZ-3). Confirm the
   production threshold is stated as 300 units or more (BIZ-4).

4. STRUCTURAL CHECK. Confirm a negative qualifier sentence exists (STRUCT-1).
   Confirm the email ends with a 20-minute call CTA (STRUCT-2). Confirm no
   markdown formatting, subheadings, or bullets (STRUCT-3). Confirm
   subject_line is 60 characters or under (STRUCT-4).

OUTPUT RULES:

- If zero violations are found across all 4 checks, return status PASS with an
  empty line_level_edits array.
- If 1 or more violations are found, return status FAIL. For every violation,
  return 1 entry in line_level_edits containing the exact offending quote, the
  rule code it breaks, and a 1 sentence statement of what the rule requires.
  Do not propose replacement text. Your job ends at identifying the violation
  precisely enough that A3 can fix it.
- A FAIL verdict means the draft is discarded. It is never partially approved
  and never sent in its current form.

OUTPUT: Return only 1 JSON object in the output schema. No prose outside the
JSON.
```

---

## 4. THE OUTPUT SCHEMA

### 4.1 PASS

```json
{
  "status": "PASS",
  "line_level_edits": []
}
```

### 4.2 FAIL

```json
{
  "status": "FAIL",
  "line_level_edits": [
    {
      "location": "email_body",
      "quote": "We'd love to send you a free sample of our work.",
      "rule_broken": "BIZ-2",
      "requirement": "No sample of any kind, free or otherwise, may be offered. The only permitted commercial mechanism is the starter pack defined in A3 Section 3.2."
    },
    {
      "location": "email_body",
      "quote": "a small starter pack of 30 units",
      "rule_broken": "VOICE-2",
      "requirement": "The number must precede the adjective: '30-unit starter pack', not 'a small starter pack of 30 units'."
    },
    {
      "location": "subject_line",
      "quote": "Quick question about your supply chain - got a sec?",
      "rule_broken": "VOICE-1",
      "requirement": "No em-dash is permitted anywhere in subject_line or email_body."
    }
  ]
}
```

### 4.3 INPUT-1 (malformed input, immediate FAIL)

```json
{
  "status": "FAIL",
  "line_level_edits": [
    {
      "location": "input",
      "quote": "",
      "rule_broken": "INPUT-1",
      "requirement": "All 3 of draft, a1_baseline, and a2_baseline must be present. 1 or more were missing."
    }
  ]
}
```

---

## 5. WORKED EXAMPLES

### 5.1 PASS (Lo & Sons, the lead carried through every prior spec)

Draft body opens: "85 days have passed since your last China-origin shipment of
cowhide leather handbags, against a 45 day average over your last 8 shipments."
This matches `a1_baseline.recomputed_days_since_last` (85) and
`a1_baseline.recomputed_cadence_days` (45). FACT-3 clears.

The draft addresses "Sourcing team" because `a2_baseline.overall_status` is
`PARTIAL_CONTEXT` and `decision_maker.confidence` is `UNKNOWN`. FACT-4 clears.

The draft offers "a 30-unit starter pack of this exact handbag line, with 100
percent of that cost credited against your first production order of 300 units
or more." BIZ-1 through BIZ-4 all clear: no "free," no sample, both required
elements present, threshold correctly stated.

No em-dash, no jargon-list phrase, gap sentence first, 152 words, ends with a
20-minute call request, 1 negative qualifier sentence about brands not yet at
300-unit production. All checks clear.

```json
{
  "status": "PASS",
  "line_level_edits": []
}
```

### 5.2 FAIL (planted violations)

Same lead, a draft that opens with "I hope this finds you well, I wanted to
reach out because I noticed your shipping has slowed down a bit - we'd love to
send a free sample to a small batch of 30 brands like yours."

This single sentence alone breaks:

```
VOICE-4 : opens with greeting filler and "I wanted to reach out", not the gap
VOICE-3 : "I hope this email finds you well" and "reaching out because" match
          the jargon blocklist
VOICE-1 : contains an em-dash
FACT-1  : "slowed down a bit" is not a number and does not state the 85 day /
          45 day gap from the baseline at all
BIZ-1   : "free sample" uses the banned word "free"
BIZ-2   : offers a sample, not a starter pack
VOICE-2 : "a small batch of 30 brands" is number-after-adjective, and also
          misuses the starter pack unit count as a count of brands, not units
          of product
```

A4 returns `status: "FAIL"` with 7 entries in `line_level_edits`, 1 per rule
above, each quoting the offending fragment. The draft is discarded in full. A3
receives the 7-item list and produces a new draft from the same baseline.

---

## 6. ROUTING AFTER A4

### 6.1 PASS

The draft is unchanged. A4 does not touch it. The send-ready package is the
union of:

```
- a1_baseline.score and a1_baseline.citation        (proof)
- a2_baseline.consignee_name and decision_maker      (addressing)
- draft.subject_line and draft.email_body            (the message, verbatim)
```

This package moves to the send queue, a later mission and explicitly out of
scope here. No further agent edits the draft after a PASS. PASS is final.

### 6.2 FAIL

The draft is destroyed: it is not stored, not queued, and not shown to Yossi.
Only the `FAIL` verdict and its `line_level_edits` persist, attached to the
lead's record alongside the untouched A1 and A2 baseline (which remain valid;
A4 audits A3's draft, not A1 or A2's findings).

The lead returns to A3 for a new draft, with the `line_level_edits` list passed
to A3 as the only new input alongside the original baseline. A3 does not see its
own previous draft; it writes fresh from the baseline, informed by which rules
were broken last time.

A fixed retry limit of 2 A3-to-A4 cycles applies. If a 3rd consecutive draft
also fails, the lead is held for direct human review rather than cycling again,
on the principle that 3 failures from the same baseline indicates either an
ambiguous baseline or a systemic A3 problem, not a 1-off drafting slip. A held
lead keeps its A1 proof and A2 context; nothing is lost, the loop simply stops
spending cycles on it.

---

## 7. WHAT THIS CLOSES

With A4, the chain is end to end: A1 proves the gap is real, A2 proves the
context is current, A3 drafts inside fixed voice and offer constraints, A4
proves the draft matches what A1 and A2 actually found and breaks no rule. A
message reaches Yossi's send queue only after clearing all 4. Nothing
un-proven, nothing off-voice, and nothing offering a free sample ever reaches a
real prospect.

---

*A4 / G6 Gatekeeper Spec v1.0 | 2026-06-15 | CORE-side, demand-only*
*A4 proves or destroys. It never edits, never softens, never lets a draft pass
on "close enough."*
