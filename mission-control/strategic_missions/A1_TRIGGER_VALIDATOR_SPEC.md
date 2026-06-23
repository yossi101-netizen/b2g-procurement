# A1 TRIGGER VALIDATOR — TECHNICAL SPECIFICATION
# Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only

**Status:** SPEC (build-ready) | **Date:** 2026-06-15 | **Owner:** Yossi (Founder)
**Scope:** US market only. Audits the output of `us_bol_scoring_engine.py`.
**Out of scope (do not build here):** A2 to A5, the triage dashboard, the Phase 4
learning agent (formally deferred until closed-won and closed-lost data exists).
**Parent:** US_BOL_TRIGGER_SPEC.md (Section 4), KRITIKAAL_INTENT_HUNTING_PLAN.md

> **One sentence:** A1 does not find leads. A1 proves, from the raw shipment text
> alone, that the score engine did not invent the gap it scored.

---

## 0. ROLE AND THE ZERO-TRUST PRINCIPLE

`us_bol_scoring_engine.py` is fast and deterministic, but it trusts the metrics
it is handed. If a bad ingestion layer feeds it a wrong `days_since_last`, it
will score a gap that does not exist and rank a calm importer as HOT. A
fabricated gap reaching a real prospect under the founder's name is the single
worst failure mode of this system.

A1 exists to make that failure impossible. A1 is a Claude sub-agent placed
between the engine and the human call list. It assumes the engine is guilty
until the raw text proves it innocent. It has no web access, no outside
knowledge, and no authority to research a company. It has exactly 1 job:
recompute the gap from the raw rows and confirm the engine's number is real.

The contract is binary. A lead either survives A1 with a cited line of raw text
that proves its gap, or it is held. Nothing un-proven is ever contacted.

---

## 1. THE INPUT SCHEMA

A1 receives 2 mandatory inputs in 1 message. Both are required. A missing input
is an immediate REJECTED with reason `MISSING_INPUT`.

### 1.1 Input A: raw shipment rows (the evidence)

The exact text rows for 1 consignee, copied from ImportYeti, each row carrying
at minimum an arrival date and a product description. A1 treats this as the only
source of truth. If the rows carry no parseable dates, A1 cannot prove a gap and
must reject (see rejection taxonomy, Section 5).

```
RAW_ROWS (1 consignee, plain text or line array):
  arrival_date | shipper_country | hs_code | product_description | bol_number
  2026-01-12   | China           | 4202.21 | Cowhide Leather Handbag | BOL...883
  2026-02-26   | China           | 4202.21 | Cowhide Leather Handbag | BOL...901
  ...
```

### 1.2 Input B: the engine ScoreResult (the claim under audit)

The JSON object returned by `score_lead()` in `us_bol_scoring_engine.py`. A1
audits this object. It never assumes any field is correct.

```json
{
  "verdict": "SCORED",
  "reason": "scored 89, gap stage HOT",
  "fit": 0.9625,
  "timing": 0.925,
  "score": 89,
  "band": "HOT",
  "gap": {
    "cadence_days": 45,
    "cadence_mad": 2,
    "sigma_robust": 2.9652,
    "expected_ceiling": 50.93,
    "days_since_last": 85,
    "overdue_ratio": 1.889,
    "anomaly": true,
    "rule_used": "PRIMARY: days_since_last > cadence plus 2 sigma",
    "actionable": true,
    "stage": "HOT"
  },
  "components": { "F1_product": 1.0, "...": "..." }
}
```

A1 also needs the `pulled_at` date (the date the rows were fetched), passed
alongside Input B, because `days_since_last` is measured against it, not against
today. If `pulled_at` is absent, reject with `MISSING_PULLED_AT`.

---

## 2. THE RECOMPUTATION PROCEDURE A1 MUST FOLLOW

A1 performs these 5 steps in order, using only Input A, then compares to Input B.

```
1. Parse every arrival_date from the raw rows. Discard any row with no
   parseable date. Count the dates kept as n_dates.
2. If n_dates < 4, stop. Return REJECTED, reason INSUFFICIENT_HISTORY.
3. Sort the dates ascending. Compute the consecutive intervals in days.
   Take the median as recomputed_cadence_days.
4. recomputed_days_since_last = pulled_at minus the latest arrival_date.
5. Identify the single raw row that is the latest China-origin arrival. This
   row is the citation that proves where the silence begins.
```

Tolerances for agreement with Input B:
```
cadence agreement   : abs(recomputed - engine) <= 10 percent of engine cadence
recency agreement   : abs(recomputed - engine) <= 3 days
```

If either tolerance fails, the engine math cannot be proven by the raw text.
A1 returns `FABRICATION_DETECTED` and reports both numbers.

---

## 3. THE ZERO-TRUST SYSTEM PROMPT (verbatim, build-ready)

```
You are A1, the Trigger Validator for KritiKaal's US BoL intent engine. You do
not find leads. You do not research companies. You do not use any outside
knowledge or the web. You audit 1 claim: that the score engine measured a real
shipment gap and did not invent it.

You receive 2 inputs. Input A is the raw shipment rows for 1 importer, copied
from ImportYeti. Input B is the JSON ScoreResult from the scoring engine, plus a
pulled_at date. Input A is the only truth. Input B is the claim under audit.
Treat the engine as guilty until the raw rows prove it innocent.

NON-NEGOTIABLE RULES:

1. Recompute independently. Parse every arrival_date from Input A yourself. Sort
   them ascending. Compute the consecutive intervals in days. Take the median as
   your cadence. Compute days_since_last as pulled_at minus the latest arrival
   date. Do these calculations from the raw rows alone. Never copy a number from
   Input B and never trust it.

2. Cite or stay silent. Every number you report must trace to a specific raw row
   you can quote. Quote the exact text of the latest China-origin arrival row as
   the citation that proves where the silence begins. If you cannot quote a row,
   you may not make the claim.

3. Compare and judge. Set recency agreement when your days_since_last is within
   3 days of the engine value. Set cadence agreement when your cadence is within
   10 percent of the engine value. Both must hold to validate.

4. Halt on fabrication. If either agreement fails, the engine math cannot be
   proven by the raw text. Stop. Return status FABRICATION_DETECTED. Report your
   number and the engine number side by side. Do not attempt to reconcile them
   or to guess which is right.

5. Never invent. If a date is missing, unparseable, or ambiguous, treat that row
   as having no date. Do not estimate a date. Do not fill a gap with a number
   that is not in the rows. Missing data is a valid and required answer.

6. Refuse thin history. If fewer than 4 rows carry a parseable date, return
   REJECTED with reason INSUFFICIENT_HISTORY. 4 dated rows give 3 intervals,
   which is the floor to trust a cadence.

7. Respect the latency buffer. If your days_since_last is 30 or under, return
   REJECTED with reason WITHIN_LATENCY_BUFFER. The silence may be recent
   arrivals the provider has not yet indexed, not a real gap.

8. Stay inside the data. Do not describe the company, its brand, its products
   beyond what the product_description text literally says, or its reasons for
   the gap. Cause analysis belongs to a later agent, not you.

OUTPUT: Return only 1 JSON object in the output schema. No prose outside the
JSON. Use VALIDATED only when you personally recomputed the gap, both agreements
held, and you have a quoted citation row.
```

---

## 4. THE OUTPUT SCHEMA

A1 returns exactly 1 JSON object. 3 statuses are possible. No prose outside JSON.

### 4.1 Validated

```json
{
  "status": "VALIDATED",
  "score": 89,
  "citation": "2026-03-21 | China | 4202.21 | Cowhide Leather Handbag | BOL...992",
  "recomputed_days_since_last": 85,
  "recomputed_cadence_days": 45
}
```

### 4.2 Rejected (business logic, the gap is real but not actionable)

```json
{
  "status": "REJECTED",
  "reason": "WITHIN_LATENCY_BUFFER: recomputed days_since_last 22, at or under the 30 day buffer"
}
```

### 4.3 Fabrication detected (the engine claim cannot be proven)

```json
{
  "status": "FABRICATION_DETECTED",
  "reason": "recency disagreement: A1 recomputed days_since_last 41, engine claimed 85, gap of 44 days exceeds the 3 day tolerance",
  "a1_value": 41,
  "engine_value": 85
}
```

The minimum contract the parent task fixed is honored exactly: A1 returns either
`{"status": "VALIDATED", "score": Int, "citation": "exact raw text"}` or
`{"status": "REJECTED", "reason": "explanation"}`. FABRICATION_DETECTED is the
third, most severe outcome and is treated downstream as a hard REJECTED that also
raises an engine alarm (Section 5).

---

## 5. HOW THE LOOP HANDLES A REJECTED LEAD

A1 produces 1 of 3 dispositions. Each routes differently.

| Status | Meaning | Routing |
|---|---|---|
| VALIDATED | gap proven from raw text, all tolerances held | advance to A2 (OSINT), a later mission |
| REJECTED | gap real or absent, but not actionable now | logged with reason, held, never contacted |
| FABRICATION_DETECTED | engine number cannot be proven by raw rows | held AND the engine run is flagged for review |

The REJECTED reason taxonomy:
```
INSUFFICIENT_HISTORY   : fewer than 4 dated rows
WITHIN_LATENCY_BUFFER  : days_since_last 30 or under
UNVERIFIABLE_DATES     : rows carry no parseable arrival dates
MISSING_INPUT          : Input A or Input B absent
MISSING_PULLED_AT      : no fetch date to measure recency against
NOT_ACTIONABLE         : gap stale or on schedule per the engine, A1 confirms
```

A rejected lead is never deleted. It is written to a hold log with its full A1
output and its reason, so a later pull can reconsider it once more shipments
arrive or once the latency buffer clears. A rejection is a not yet, not a no.

A FABRICATION_DETECTED disposition is the important one. It does 2 things. First
it holds the lead exactly like a rejection, so no un-proven gap reaches a human.
Second it raises an alarm against the engine run itself, because a fabrication
means the ingestion or normalization layer produced a metric the raw rows do not
support. 1 fabrication is a data bug to fix before the next pull, not a lead to
discard quietly. This is the self-auditing property that lets the founder trust
the HOT list without re-checking every row by hand.

---

## 6. PASS CRITERIA TO A2

A lead advances to A2 only when all 4 hold:
```
status == VALIDATED
AND recomputed agreement on cadence and recency both held
AND a citation row was quoted
AND the engine band was HOT
```
Everything else is held with its reason. The planted bad cases from the approved
2026-06-15 validation must come out correctly: Modern Picnic rejects on
WITHIN_LATENCY_BUFFER, Staud rejects on NOT_ACTIONABLE (stale), and any row set
stripped of its dates rejects on UNVERIFIABLE_DATES.

---

## 7. WORKED EXAMPLES

### 7.1 A clean VALIDATED (Lo & Sons, the approved top lead)

A1 parses 8 dated China-origin rows, sorts them, finds a median cadence near 45
days, and computes days_since_last as 85 from the latest arrival to pulled_at.
Engine claimed cadence 45 and days_since_last 85. Both agreements hold. A1 quotes
the latest China row as the citation and returns VALIDATED with score 89.

### 7.2 A FABRICATION_DETECTED (planted bad ingestion)

The ingestion layer mis-parsed a 2026 row as 2025 and handed the engine a
days_since_last of 85. A1 reparses the raw rows, finds the true latest arrival is
41 days before pulled_at, and the 44 day disagreement exceeds the 3 day
tolerance. A1 halts, returns FABRICATION_DETECTED with both numbers, the lead is
held, and the engine run is flagged so the date parser is fixed before scaling.

---

*A1 Trigger Validator Spec v1.0 | 2026-06-15 | CORE-side, demand-only*
*A1 audits the engine. A1 never trusts it. Zero un-proven gap reaches a human.*
