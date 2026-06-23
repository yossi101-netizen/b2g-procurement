# moat-engine — Business Context (C-core)

**Project:** moat-engine | **Framework:** ABC-TOM (new isolated workspace) |
**Created:** 2026-06-17 | **Mode:** Demand-only

> C-core is the business DNA. It defines *what counts as a good opportunity* and
> *what this system is and is not allowed to do*. B-brain encodes the math;
> C-core encodes the intent. If they ever disagree, C-core wins and B-brain is
> wrong.

---

## 1. Mission

Find and validate **single-product opportunities** — one hero product aimed at
one low-competition demand pocket — that can be **manufactured in India** and
sold into the **West (US primary; UK/EU secondary)**, and that have a
**defensible moat** so they survive contact with cheap algorithmic knock-offs.

This is the operationalisation of the "one-product store" playbook (PillowCube,
BikeTowLeash, MindJournals, BigBarker, KNKG, Nutr, BigFig, Vessi — see
`../README.md` appendix): pick one product, own one keyword cluster nobody is
seriously contesting, and validate that real money is already moving before
committing.

## 2. Hard boundary — DEMAND ONLY

This system **discovers and validates demand. It does not find suppliers.**

| In scope | Out of scope (permanently) |
|---|---|
| Keyword-cluster demand discovery | Supplier / manufacturer discovery |
| US import-demand validation (BoL) | Factory vetting, RFQs, sourcing |
| Moat / brandability scoring | Outreach, negotiation, CRM |
| Regulatory import-viability screen | Order placement / logistics |
| Ranked opportunity shortlist | Anything downstream of "what to sell" |

The operator already knows how to source and manufacture in India. The single
question this engine answers is: **"of all the things we *could* make, which ones
have proven Western demand AND a moat AND a clear regulatory path?"**

This is consistent with — and a clean extension of — the 2026-06-12 demand-only
pivot in the sibling project INDIA-STOCKS (`census → bol_pipeline → digest`).
Never reintroduce supply-side logic here.

## 3. The thesis (what a "good opportunity" looks like)

A candidate is worth pursuing only when **all three** hold at once:

1. **DEMAND is proven, not imagined.** A keyword cluster with real aggregate
   search volume AND low competition (low Ahrefs-style KD), *cross-referenced
   with hard US Bill-of-Lading data showing real importers — ideally repeat
   importers — already buying the category.* Search interest alone is a
   hypothesis; import records are evidence.
2. **There is a MOAT.** The product must allow **premium material utilisation**
   (full-grain leather, real finishing) or **elevated B2B / corporate
   positioning** — something that lets it compete on quality and brand equity,
   not price. If a cheap seller can list an identical item next week, it fails.
3. **It can legally land.** No hard regulatory blocker for India → target
   market. Documentation load (REACH Cr(VI), EUDR due-diligence, Prop 65
   labelling) is acceptable and is often a *selling point* for the CORE
   business; a true block (CITES-restricted material, banned input) is not.

## 4. Why "moat" is the headline word

The failure mode of the one-product playbook is that a winning product gets
cloned by dozens of cheap algorithmic sellers within weeks, collapsing margin to
zero. The defence is **not secrecy — it is build quality the cloners can't cheaply
match.** India's leather/full-grain capability (the KritiKaal network: Kanpur
SLG, Agra footwear, Kolkata bags) is exactly that kind of moat: a full-grain
leather product with real finishing is structurally expensive to knock off,
unlike a PU/plastic gadget. The MOAT axis exists to **reject high-demand cheap
commodities on purpose**, even when the demand numbers look great.

## 5. Relationship to the rest of the estate

- **INDIA-STOCKS** (sibling project) owns the live demand stack: `census_pipeline`
  (macro radar), `bol_pipeline` (ImportYeti CSV → HuntList signals),
  `huntlist.py` (the ledger), `confidence_digest`. **moat-engine sits one step
  upstream of HuntList**: it decides *which* single-product bets are worth
  opening as HuntList items in the first place. A HOT result here becomes a
  `huntlist.py add` there.
- **KritiKaal CORE / MASTER_CONTEXT_MANIFEST** supplies the regulatory knowledge
  (Prop 65, REACH Cr(VI) ≤3mg/kg, EUDR, CPSIA, Section 301, post-Brexit customs)
  that the COMPLIANCE axis encodes. moat-engine does not duplicate that doc; it
  references it.

## 6. Output contract

The engine produces a **ranked shortlist with auditable reasons**, not a verdict
to act blindly on. For every candidate it returns the DEMAND / MOAT axes, the
final score and band (HOT / WARM / WATCH / DISCARD), and — critically — *which
gate it failed and why*. The gate reasons are the real product: knowing that a
tempting idea is a "MOAT_GATE: cheap-knock-off risk" or a "COMPLIANCE_HARD_BLOCK:
CITES" is worth more than any single number.
