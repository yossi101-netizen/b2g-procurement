# Devil's Advocate Review: יצירת קובץ MASTER Strategy

**Date:** 2026-03-22
**Reviewing:** Strategist's analysis — MASTER strategy document for KritiKaal.com

---

## Assumption Stress-Test

| # | Assumption | Risk If Wrong | Confidence |
|---|-----------|---------------|-----------|
| 1 | We have enough information to build a comprehensive MASTER now | If key business model decisions are still open (pricing structure, exact service tiers, operational capacity), the MASTER file encodes guesses as facts — and agents will act on them | Medium |
| 2 | The file will be maintained as the business evolves | If nobody updates it, stale context is actively harmful. Agents citing last year's MOQ minimums or a discontinued Starter Pack pricing is worse than no file. | Low — most files don't get updated without a named owner and trigger |
| 3 | One comprehensive file serves all agent needs | A 3,000-word document is fine for strategic context but may be too heavy for quick queries. Agents asked to write a social post don't need the full LWG compliance section. | Medium |
| 4 | The numbers in sample-03 ($35K/client, 28 clients, AQL 2.5) are current operational targets, not aspirational projections | If these are stretch goals rather than actual operating reality, the MASTER file will make every agent analysis over-confident | Medium |

---

## Risks the Strategist Underweighted

1. **The "frozen assumptions" problem.** The Strategist frames the MASTER file as a one-time build. But KritiKaal is an early-stage business. Pricing, MOQs, target geographies, and even the service model will shift in the next 6-12 months. A comprehensive file that isn't updated doesn't just become useless — it actively misleads. Every agent reading stale context will produce analysis that feels right but is built on outdated foundations. The Strategist's solution ("quarterly review") is necessary but not sufficient — there's no named owner or trigger for updates.

2. **Token bloat in context windows.** As the MASTER file grows, it becomes expensive to load in full. If the file reaches 5,000+ words, agents will either truncate it or the most important sections will get buried below the fold. The Strategist recommended "comprehensive" without addressing the practical constraint of how AI agents actually consume long documents.

3. **False confidence in specificity.** The Strategist listed specific numbers: 28 clients, $35K per client, AQL 2.5. These came from sample-03 (a research document), not from actual operational data. If these are planning assumptions rather than verified reality, encoding them in the MASTER file creates a confidence illusion. Future agents will cite them as facts.

---

## The Missing Option

**Option D: Two-layer architecture.**

Instead of one file, create two:

- **MASTER-BRIEF.md** (max 600 words): The always-current essentials — who we are, who we serve, 5 key numbers, what we're not. Read by every agent every session. Maintained monthly.

- **MASTER-DEEP.md** (full strategic depth): The comprehensive competitive analysis, operational model, compliance details, financial mechanics. Read only for strategic or research tasks. Reviewed quarterly.

**Why this is worth considering:** The Brief stays small and easy to maintain. The Deep file can grow without penalty because it's only loaded for the right tasks. The Brief gets updated when anything material changes. The Deep gets updated when strategy shifts.

This avoids the single-file trade-off between "always relevant but shallow" and "comprehensive but heavy."

---

## Pre-Mortem: If This Fails

Imagine it's September 2026. The MASTER file is harming more than helping. Here's what went wrong:

1. The MASTER file was built with current assumptions in March 2026. By June, the UK market strategy changed and the $300 Starter Pack was replaced with a different entry model.
2. Nobody updated the MASTER file. Sessions continued loading it.
3. Agents started producing analysis based on the old model — recommending the Starter Pack, quoting the $35K/client number, targeting UK as Tier 1 — all of which had been revised.
4. Yossi noticed the mismatch only after several sessions produced off-base recommendations.
5. Root cause: comprehensive file with no maintenance protocol and no expiry signal.

**The fix that should have been built in from day 1:** A "VALID UNTIL" date in the header, and a named trigger for review (e.g., "review this file whenever a core service offering changes").

---

## The Hard Question

**Are the numbers in the MASTER file (28 clients, $35K, AQL 2.5) current operating reality, or are they the target state you're building toward?**

If they're targets, the MASTER file needs to say so explicitly. Otherwise, every agent that reads "we serve 28 core clients" will treat KritiKaal as an established operation rather than a business being built — and the analysis will be wrong.

---

## Summary

**Where I agree with the Strategist:**
- Create the MASTER file now. Waiting has a real cost. We have sufficient source material.
- Option C (do nothing) is clearly unacceptable.

**Where I see more risk:**
- "Comprehensive" must be paired with "maintainable." A large file without a maintenance protocol is a liability, not an asset.
- The two-layer architecture (MASTER-BRIEF + MASTER-DEEP) is worth considering over a single monolithic document.
- Numbers must be explicitly labeled as targets vs. operating reality.

**My biggest concern:** The MASTER file becomes the business's version of "The Document Everyone Cites But Nobody Updates" — a confident-sounding reference that drifts from reality within 90 days.
