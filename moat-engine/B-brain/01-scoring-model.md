# Scoring Model — Single-Product Moat Discovery (B-brain)

**Version:** v0.1 (initial, NOT yet calibrated against a real provider pull) |
**Implemented by:** `../T-tools/moat_discovery_engine.py`

> This file is the canonical spec. The constants in the engine ARE these numbers.
> Change one here → change it there → re-run the self-test → bump the version.
> Until v0.1 is calibrated on real candidates, trust the **bands and gate reasons**
> as directional; do not over-read the exact integer score.

---

## 1. Shape of the model

Three axes, two of them scored 0–1, one a gate:

```
FINAL = 100 × DEMAND × MOAT × compliance_factor
```

with **hard gates** evaluated first that collapse a candidate straight to
DISCARD (score 0) regardless of the other axes. This is the same
`score = 100 × A × B` + hard-gate pattern as the validated
`us_bol_scoring_engine.py`, so the two engines read the same way.

Multiplication (not addition) across DEMAND and MOAT is deliberate: a candidate
must be good on **both** axes. A 0.9 demand × 0.2 moat = 0.18 → DISCARD. You
cannot buy your way out of "no moat" with raw demand.

---

## 2. DEMAND axis (0–1)

> "Is anyone searching for it, AND are real US importers already buying it?"

```
DEMAND = (0.25·D1 + 0.30·D2 + 0.15·D3 + 0.30·D4) × trend_mult
```

| Code | Component | Source | Why this weight |
|---|---|---|---|
| **D1** | Cluster search volume | Ahrefs / free KW tool | 0.25 — necessary, not sufficient |
| **D2** | Keyword difficulty (inverse) | Ahrefs KD / free proxy | **0.30 — headline: low KD = winnable discovery** |
| **D3** | Breadth of low-comp long-tails | KW tool | 0.15 — the "fan of zero-comp terms" pattern |
| **D4** | Import validation | **ImportYeti BoL** | **0.30 — hard evidence real money moves** |

**D1 — volume_score(cluster_volume)** (sum of monthly searches across the cluster):

| Cluster volume | Score |
|---|---|
| ≥ 20,000 | 1.00 |
| 10,000–19,999 | 0.85 |
| 5,000–9,999 | 0.65 |
| 2,000–4,999 | 0.45 |
| 500–1,999 | 0.25 |
| < 500 | 0.10 |

**D2 — difficulty_score(cluster_kd)** (0–100 scale; lower is better):

| Cluster KD | Score |
|---|---|
| ≤ 5 | 1.00 |
| ≤ 10 | 0.85 |
| ≤ 15 | 0.65 |
| ≤ 25 | 0.40 |
| ≤ 40 | 0.20 |
| > 40 | 0.05 |

**D3 — breadth_score(n_low_comp_terms)** (count of cluster terms at KD ≤ 10):

| Low-comp terms | Score |
|---|---|
| ≥ 8 | 1.00 |
| 5–7 | 0.80 |
| 3–4 | 0.60 |
| 1–2 | 0.35 |
| 0 | 0.10 |

**D4 — import_validation_score(unique, repeat)** — from US Bill-of-Lading.
The 0.80 tier is **exactly the `bol_pipeline.py` default gate** (≥5 unique, ≥2 repeat):

| Condition | Score |
|---|---|
| repeat ≥ 3 AND unique ≥ 8 | 1.00 |
| repeat ≥ 2 AND unique ≥ 5 (= bol gate) | 0.80 |
| unique ≥ 5 (but < 2 repeat) | 0.50 |
| unique ≥ 2 | 0.30 |
| else (search-only, no import proof) | 0.10 |

**trend_mult** (Google Trends direction): RISING ×1.0 · FLAT ×0.90 · DECLINING ×0.60.

---

## 3. MOAT axis (0–1)

> "Can this be branded / premium-built, or will cheap sellers knock it off?"

```
MOAT = 0.25·M1 + 0.15·M2 + 0.20·M3 + 0.30·M4 + 0.10·M5
```

| Code | Component | Scale → score |
|---|---|---|
| **M1** | Material-premium potential (full-grain / real finishing can elevate it) | HIGH 1.0 · MED 0.60 · LOW 0.25 |
| **M2** | Niche wedge ("best X for [subset]") | yes 1.0 · no 0.40 |
| **M3** | Brandability (giftable / story / B2B vs price-only) | HIGH 1.0 · MED 0.60 · LOW 0.25 |
| **M4** | **Knock-off resistance** (inverse of commodity risk) | commodity LOW→1.0 · MED→0.55 · HIGH→0.15 |
| **M5** | Unit economics (high-ticket / giftable) | HIGH_TICKET 1.0 · MID 0.70 · LOW 0.40 |

M4 carries the most weight (0.30) because knock-off resistance is the whole
point of the "defensible moat" mandate.

---

## 4. COMPLIANCE axis (gate + haircut)

Encodes the per-market regulatory knowledge from the KritiKaal
`MASTER_CONTEXT_MANIFEST` (§1.1.2): Prop 65 / CPSIA / FTC (US), UK REACH Cr(VI)
≤3mg/kg / GPSR / EUDR (UK/EU), Section 301 non-exposure for India-origin.

| Status | Meaning | Effect |
|---|---|---|
| **CLEAR** | No material friction India → target market | ×1.00 |
| **DOCUMENTED_LOAD** | Passable with certs/test reports (REACH Cr(VI), EUDR DD, Prop 65 labels) | ×0.85 |
| **HARD_BLOCK** | CITES-restricted material, banned input, named restriction | **VETO → DISCARD** |

DOCUMENTED_LOAD is only a mild haircut on purpose: for the CORE business,
absorbing compliance documentation is a *value-add to sell*, not a reason to walk.

---

## 5. Hard gates (evaluated in this order, cheapest veto first)

1. **COMPLIANCE_HARD_BLOCK** → DISCARD. Cannot legally land it.
2. **KD_GATE**: `cluster_kd > 35` → DISCARD. Cannot win discovery.
3. **DEMAND_GATE**: `DEMAND < 0.40` → DISCARD. Nobody is searching/buying enough.
4. **MOAT_GATE**: `MOAT < 0.40` → DISCARD. Cheap-knock-off target. *(The core filter.)*

A gated candidate returns score 0, band DISCARD, and the gate name in
`gates_tripped` with a human-readable reason.

## 6. Bands (shared with us_bol_scoring_engine.py)

| Score | Band | Meaning |
|---|---|---|
| ≥ 55 | **HOT** | Open a HuntList item now |
| ≥ 35 | **WARM** | Worth a deeper look / close one gap and re-score |
| ≥ 20 | **WATCH** | Park it; revisit if data improves |
| < 20 | **DISCARD** | Drop |

---

## 7. Frozen reference cases (the self-test)

| Case | Candidate | DEMAND | MOAT | Compl. | Score | Band | Why |
|---|---|---|---|---|---|---|---|
| A | Full-grain leather valet/EDC tray (men) | 0.8875 | 0.97 | 1.00 | **86** | HOT | low KD + repeat importers + real moat |
| E | Waxed-canvas + leather dopp kit | 0.6875 | 0.655 | 1.00 | **45** | WARM | solid but mid material/brand |
| B | Generic PU/plastic phone stand | 0.865 | 0.2575 | — | 0 | DISCARD | **MOAT_GATE** — high demand, cheap commodity |
| C | Exotic python-leather wallet | — | — | — | 0 | DISCARD | **COMPLIANCE_HARD_BLOCK** — CITES |
| D | Leather laptop bag (saturated) | — | — | — | 0 | DISCARD | **KD_GATE** — KD 45, unwinnable |

Cases B/C/D are the three ways a tempting idea gets correctly rejected:
*cheap to clone*, *illegal to land*, *impossible to rank*.

## 8. Calibration to-do (before scaling)

- [ ] Run the first 10–15 real ImportYeti + Ahrefs candidates through the engine.
- [ ] Eyeball the bands against operator judgement (same "eyeball test" that
      validated `us_bol_scoring_engine.py` on 2026-06-15).
- [ ] Adjust band floors / KD_GATE / volume bands to fit reality, then bump to v1.0.
