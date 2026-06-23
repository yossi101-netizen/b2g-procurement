# A2 OSINT BRAND RESEARCHER — TECHNICAL SPECIFICATION
# Phase 1 of the KritiKaal Intent Hunting Plan, US market, demand-only

**Status:** SPEC (build-ready) | **Date:** 2026-06-15 | **Owner:** Yossi (Founder)
**Scope:** US market only. Consumes 1 VALIDATED lead from A1. Produces 1 context
object for A3 (Voice-DNA Copywriter).
**Out of scope (do not build here):** A4, A5, the triage dashboard, the Phase 4
learning agent.
**Parent:** A1_TRIGGER_VALIDATOR_SPEC.md, KRITIKAAL_INTENT_HUNTING_PLAN.md

> **One sentence:** A2 turns 1 proven shipment gap into 1 named person, 1 sized
> company, and 1 confirmed product line, or it returns UNKNOWN for any piece it
> cannot prove with a live source.

---

## 0. ROLE AND THE SECOND ZERO-TRUST LAYER

A1 proved the gap is real from raw shipment text. A2 is a different kind of
risk. A2 is the first agent in the chain with web access, and web access carries
2 specific failure modes that the gap math never faced.

1. **Anti-bot walls.** LinkedIn, Instagram, and most company "Team" pages actively
   block direct browsing by automated agents. An agent that cannot reach a page
   will be tempted to answer from training-data memory instead. That memory can
   be a year old or more.
2. **Stale decision-makers.** A named buyer found through memory or a single old
   snippet may have left the company, changed roles, or never held the title
   claimed. A founder who calls and asks for the wrong person by name burns the
   only first impression this engine exists to create.

A2's job is not research in the open-ended sense. A2's job is to apply 3 fixed
OSINT techniques, in order, and to refuse to assert anything that those
techniques did not return with a working source and a recency signal. 1 piece of
context with a source beats 5 pieces of context from memory.

---

## 1. THE INPUT SCHEMA

A2 receives exactly 1 object, the VALIDATED output of A1, plus the original
consignee name and HS group carried from the scoring engine.

```json
{
  "consignee_name": "Lo & Sons",
  "hs_group": "LEATHER_BAGS_CASES",
  "trigger": {
    "status": "VALIDATED",
    "score": 89,
    "band": "HOT",
    "citation": "2026-03-22 | China | 4202.21 | Cowhide Leather Handbag | BOL1007",
    "recomputed_days_since_last": 85,
    "recomputed_cadence_days": 45
  }
}
```

If `trigger.status` is not `VALIDATED`, A2 does not run. This is enforced by the
caller, not by A2, but A2 must still check it on input and return `REJECTED` with
reason `TRIGGER_NOT_VALIDATED` if it somehow receives anything else.

---

## 2. THE OSINT METHODOLOGY CONSTRAINTS

A2 does not browse freely. A2 runs a fixed sequence of 3 search techniques,
in this order, and stops as soon as a field is filled with a corroborated
source. Each technique is a search-engine query, not a direct page visit, which
is how A2 routes around anti-bot walls: search engines index pages that block
live agent traffic, and the indexed snippet is itself a citable source.

### 2.1 Technique 1, decision-maker dorking (LinkedIn via search index)

```
site:linkedin.com/in "<Company Name>" AND ("Sourcing" OR "Supply Chain" OR
  "Procurement" OR "Production" OR "Founder" OR "Owner" OR "CEO" OR "Operations")
```

Run this query first. The goal is 1 name plus 1 title plus 1 indexed snippet
that shows the person's current employer as the target company. A profile that
the search index shows under a different current employer is evidence the
person has left, not evidence to use.

### 2.2 Technique 2, company-page dorking (size and headquarters)

```
site:linkedin.com/company/<company-slug>
"<Company Name>" "employees" OR "headquarters"
```

The goal is an employee-count range and a headquarters location, both with a
source URL. LinkedIn company pages show an employee-count band even when the
page itself cannot be fully rendered, because the band appears in the indexed
snippet.

### 2.3 Technique 3, product-line dorking (catalog confirmation)

```
"<Company Name>" "<key product term from the citation>" site:<company-domain>
```

The key product term comes directly from A1's cited `product_description`, for
example "leather handbag" or "cowhide". The goal is 1 current page on the
company's own domain that still lists this product category, confirming the
silenced shipment line is still part of their active business, not a
discontinued one.

### 2.4 What A2 may never do

- Never answer a field from memory because a search returned nothing useful.
- Never visit a URL that was not itself returned by a search result.
- Never substitute a company's general "Contact Us" page for a named
  decision-maker. That is a fallback for A3, not a finding for A2.
- Never carry forward a name found in Technique 1 if Technique 2 or any other
  result shows the person under a different current company.

---

## 3. THE ZERO-TRUST PROOF STANDARD

Every populated field in the output carries its own `source_url`. A field with
no qualifying source is `"UNKNOWN"`, written as the literal string, never null
and never omitted.

### 3.1 The two-anchor rule for the decision-maker

A name and title are written into the output only if 1 of these 2 conditions
holds:

```
TWO_SOURCE      : the same name and a consistent title appear in 2
                  independent indexed sources (for example, a LinkedIn
                  snippet and a press mention, or a LinkedIn snippet and the
                  company's own team page).

ONE_SOURCE_RECENT : exactly 1 source, but that source carries an explicit
                  recency signal dated within the last 12 months (a dated
                  press release, a dated interview, a LinkedIn snippet whose
                  indexed date is within the window).
```

If neither condition holds, for example a single LinkedIn snippet with no
visible date and no corroboration, the decision-maker fields are `"UNKNOWN"`
and the corroboration field records `"NONE"`. A name that cannot clear this bar
is worse than no name, because a founder will use it on a phone call.

### 3.2 Company size and product line

Company size requires 1 source with an explicit employee-count band or a
stated figure. A vague description such as "a growing brand" with no number is
`"UNKNOWN"`.

Product line confirmation requires 1 live page on the company's own domain
listing the product category from the citation. If the company's site no
longer sells that category, A2 still reports the finding, with
`current_catalog_match: false` and the source URL of the page that shows the
current catalog. This is itself useful signal for A3, not a failure.

### 3.3 No fabricated URLs

A `source_url` is always a URL that a search query in Section 2 actually
returned. A2 never constructs a plausible-looking URL (for example guessing a
LinkedIn slug pattern) and never presents a search-results page itself as if it
were the target page. If the only evidence is a search snippet, the
`source_url` is the URL of the indexed page the snippet describes, exactly as
returned by the search result, not the search-engine query URL.

---

## 4. THE A2 SYSTEM PROMPT (verbatim, build-ready)

```
You are A2, the OSINT Brand Researcher for KritiKaal's US BoL intent engine. You
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
returned nothing, so the founder can see what was checked.
```

---

## 5. THE OUTPUT SCHEMA

```json
{
  "consignee_name": "Lo & Sons",
  "trigger_context": {
    "citation": "2026-03-22 | China | 4202.21 | Cowhide Leather Handbag | BOL1007",
    "score": 89,
    "gap_summary": "85 days silent on a 45 day cadence, China-origin cowhide leather handbag line"
  },
  "company_profile": {
    "size_estimate": "11 to 50 employees",
    "size_source_url": "UNKNOWN or exact URL",
    "headquarters": "Brooklyn, New York, United States",
    "hq_source_url": "UNKNOWN or exact URL"
  },
  "decision_maker": {
    "name": "UNKNOWN",
    "title": "UNKNOWN",
    "profile_url": "UNKNOWN",
    "recency_evidence": "UNKNOWN",
    "corroboration": "NONE",
    "confidence": "UNKNOWN"
  },
  "product_line_context": {
    "shipped_product_description": "Cowhide Leather Handbag",
    "current_catalog_match": true,
    "catalog_source_url": "UNKNOWN or exact URL"
  },
  "research_log": [
    {"query": "site:linkedin.com/in \"Lo & Sons\" AND (\"Sourcing\" OR \"Supply Chain\" OR \"Founder\")",
     "result_summary": "1 result, no visible date, single source only",
     "used": false},
    {"query": "site:linkedin.com/company/lo-and-sons \"employees\"",
     "result_summary": "found employee-count band and headquarters",
     "used": true},
    {"query": "\"Lo & Sons\" \"leather handbag\" site:loandsons.com",
     "result_summary": "found current product category page",
     "used": true}
  ],
  "overall_status": "PARTIAL_CONTEXT"
}
```

### 5.1 overall_status values

```
READY_FOR_A3     : decision_maker.confidence is HIGH or MEDIUM, meaning the
                   2-anchor rule cleared. A3 can draft a named, addressed message.

PARTIAL_CONTEXT  : decision_maker is UNKNOWN but company_profile and
                   product_line_context have at least 1 populated field each.
                   A3 drafts to a role or department, not a name.

NO_USABLE_CONTEXT : every field is UNKNOWN. The lead stays in the hold log with
                   its A1 proof intact. It is not discarded, because the gap is
                   still real. It is simply not yet ready for outreach drafting.
```

---

## 6. WORKED EXAMPLE (Lo & Sons, the lead that cleared A1)

Input: the VALIDATED object from Section 1, score 89, citation a March 2026
China cowhide leather handbag arrival.

A2 runs Technique 1. The query returns 1 LinkedIn result for a "Supply Chain
Manager" with no visible date and no second source. Rule 3 is not cleared.
`decision_maker` stays UNKNOWN, `corroboration: "NONE"`.

A2 runs Technique 2. The query returns the company LinkedIn page showing "11 to
50 employees" and a Brooklyn, New York headquarters, both with a source URL.
Both fields populate.

A2 runs Technique 3. The query returns a current category page on the company's
own domain listing leather handbags. `current_catalog_match: true` with that
URL.

Result: `overall_status: "PARTIAL_CONTEXT"`. A3 receives a sized, located company
with a confirmed live product line and a proven 85-day China gap, addressed to a
role (Supply Chain or Sourcing) rather than a name. This is a usable outcome. It
is not a failure of A2, it is A2 correctly refusing to hand a founder a stale
name.

---

## 7. PASS CRITERIA TO A3

A lead reaches A3 if `overall_status` is `READY_FOR_A3` or `PARTIAL_CONTEXT`.
Only `NO_USABLE_CONTEXT` holds the lead, and even then the A1 proof remains
valid, so the lead can be re-run through A2 later if new public information
appears.

A3 must read `decision_maker.confidence` and `overall_status` before drafting,
and must address the message to the named person only when `confidence` is
`HIGH` or `MEDIUM`. Anything else is addressed to a role, per voice-dna's
existing low-friction CTA pattern.

---

*A2 OSINT Brand Researcher Spec v1.0 | 2026-06-15 | CORE-side, demand-only*
*A2 trades completeness for proof. UNKNOWN is a correct answer, not a gap.*
