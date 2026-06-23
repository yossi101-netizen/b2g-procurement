# Decision Brief: קובץ MASTER Strategy לעסק KritiKaal.com

**Date:** 2026-03-22
**Prepared by:** Strategist, Devil's Advocate, Chief of Staff
**Decision needed by:** Today — this blocks all future sessions.

---

## Decision Required

Create a MASTER strategy reference document for KritiKaal.com — and decide: single comprehensive file or two-layer architecture (Brief + Deep)?

---

## Context

KritiKaal.com is beginning to build structured workflows and recurring AI-assisted processes. Every future research session, content brief, and strategic analysis will need business context. Without a central reference, agents start from scratch each time. The business has sufficient source material to build this document now (C-core files, 3 writing samples, 44KB competitive research document).

---

## Options

### Option A: Single Comprehensive MASTER File

**Pros:**
- One place to look; all agents read the same thing
- Simpler to build and maintain
- Works immediately

**Cons:**
- File grows heavy over time; less efficient for quick tasks
- Any stale information affects all sessions equally
- No natural separation between "always read" and "read for deep work"

**Estimated impact:** Reduces per-session context overhead from 15-30 min to near zero. All future outputs improve in specificity and relevance.
**Confidence:** High

---

### Option B: Two-Layer Architecture (MASTER-BRIEF + MASTER-DEEP)

**Pros:**
- BRIEF stays small, always current, always loaded
- DEEP can grow without penalty; loaded only for strategic tasks
- Separates maintenance burden: BRIEF updated monthly, DEEP quarterly
- Better performance in token-limited contexts

**Cons:**
- Two files to maintain instead of one
- Slight additional complexity for agents (two reads instead of one for deep work)

**Estimated impact:** Same upside as Option A, with better long-term scalability and reduced risk of stale context polluting quick sessions.
**Confidence:** High

---

### Option C: Do Nothing

**What happens:** Every session starts without business context. Estimated 15-30 minutes of setup overhead per session. The 44KB competitive research document (sample-03) never gets encoded. Inconsistent analysis across sessions.

**Cost of inaction:** Unquantifiable cumulative waste. For a business building recurring AI-assisted processes, this is the equivalent of having no CRM — every interaction starts cold.

**Verdict:** Not viable.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| File goes stale without maintenance | High (if no protocol) | High | Build "Last Updated" + "Review When" headers into the document itself |
| Numbers encoded as facts are actually targets | Medium | Medium | Label all projections explicitly as "Target (not current operating reality)" |
| File too long for effective agent use | Medium (over 12 months) | Low-Medium | Use two-layer architecture OR clear section headers for selective reading |
| Wrong sections get outdated first | Medium | Low | Modular structure with section-level review dates |

---

## Where Advisors Agree

- Create the MASTER document now. Source material is sufficient. Every session without it is a degraded session.
- Option C (do nothing) is eliminated. Not viable.
- Numbers and projections must be explicitly labeled as targets vs. current reality.
- A maintenance protocol must be built into the document, not assumed.

## Where Advisors Disagree

**Single file vs. two-layer architecture:** The Strategist recommends one comprehensive file for simplicity. The Devil's Advocate recommends two-layer (BRIEF + DEEP) for maintainability and token efficiency. The core tension: simplicity now vs. scalability over 12 months.

**Chief of Staff resolution:** Start with a single file structured in clearly labeled modular sections. The first section (approx. 400-500 words) functions as the "BRIEF" layer — always-relevant essentials. The remaining sections are the "DEEP" layer. Any agent can read just the first section for quick tasks. This captures the benefit of two layers without creating two maintenance obligations on day one. If the file grows past 3,000 words in 6 months, split it at that point.

---

## Recommendation

**Create the MASTER file now, as a single modular document with a two-layer structure embedded in it.** Confidence: High.

**Why:** We have the source material. The cost of delay is paid in every future session. The two-layer debate is real but premature — a single well-structured file solves it on day one and can be split later if needed.

**Key condition:** The document must include a "Last Updated" date, a "Review When" trigger, and explicit labeling of projections vs. current reality. Without these, the file becomes a liability within 6 months.

---

## What We Don't Know

1. **Which numbers are operating reality vs. targets** — Resolve by: Yossi explicitly confirming or labeling each key metric when reviewing the MASTER file draft.
2. **How frequently the business model will change in year 1** — Resolve by: setting a mandatory 90-day review date in the document header, not a quarterly assumption.

---

## Next Steps

1. Create MASTER file draft — Agent — Today
2. Yossi reviews and labels targets vs. reality — Yossi — Within 48 hours
3. Set 90-day review reminder — Yossi — When reviewing the draft
4. Update CLAUDE.md to instruct all agents to read MASTER file at session start — Agent — After Yossi approves the draft
