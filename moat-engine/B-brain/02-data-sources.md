# Data Sources & Phase-Budget Execution Plan (B-brain)

Every engine input is **gathered by hand** and typed into an `OpportunityInput`.
The engine never touches the network — that is the air-gap contract. This file
maps each input to its source and gives the **sequenced execution plan** for
staying inside the **$300 cumulative budget ceiling**.

**Faire is access-blocked** (B2B retailer verification wall). It does not appear
anywhere in this workflow. The five-lens web below is the definitive replacement.

---

## 1. Field → source map

| Engine field | Lens | Free source | Paid source (burst only) |
|---|---|---|---|
| `cluster_volume` | Search Intent | Google Keyword Planner; Keyword Surfer | Ahrefs |
| `cluster_kd` | Search Intent + Competitive Reality | SERP proxy (§4) | Ahrefs KD |
| `n_low_comp_terms` | Search Intent | autocomplete + SERP sweep | Ahrefs KD≤10 filter |
| `trend` | Trend Velocity | **Google Trends** (free; best tool for this) | Ahrefs trend |
| `bol_unique_importers` | Macro / BoL burst | enter `0` — **UNVALIDATED** pre-burst | **ImportYeti CSV** (burst only) |
| `bol_repeat_importers` | Macro / BoL burst | enter `0` — **UNVALIDATED** pre-burst | **ImportYeti CSV** (burst only) |
| `india_is_proven_origin` | Macro | USITC DataWeb; Census API HTS chapter check | ImportYeti origin filter |
| `material_premium`, `niche_wedge`, `brandability`, `commodity_risk`, `price_band` | Competitive Reality + Transaction Proof | Operator + Amazon/Etsy competitor listings | — |
| `compliance_status`, `compliance_notes` | Compliance | MASTER_CONTEXT_MANIFEST §1.1.2 + gov sources | — |

---

## 2. The five-lens demand-triangulation web (Layer 1 — free)

Work through lenses **in this order**. Trust convergence across all five; no single
lens is authoritative. The order front-loads the cheapest kill criteria: early cuts
mean saved hours on dead ideas.

| # | Lens | Engine inputs it fills | Cut rule — stop here if… |
|---|---|---|---|
| 1 | **Search Intent** | D1, D2, D3, `trend` seed | `cluster_kd > 35` (KD_GATE) or no coherent cluster |
| 2 | **Transaction Proof** | soft D4 proxy; informs moat inputs | zero sold evidence on Terapeak + Amazon |
| 3 | **Trend Velocity** | `trend` (confirm / upgrade / downgrade) | declining curve, no platform tailwind → set DECLINING |
| 4 | **Competitive Reality** | refines `cluster_kd`, `niche_wedge`, `commodity_risk` | commodity wall (30+ clones, no wedge) |
| 5 | **Macro** | `india_is_proven_origin`; census radar corroboration | India absent from HTS chapter — note only, not a killer |

---

## 3. Lens 1 — Search Intent (D1, D2, D3, trend seed)

**Tools (free):**
- **Google Trends** — sets the `trend` direction and surfaces rising related queries
  to seed new clusters. Also use for the 5-year view (needed for Lens 3).
- **Google Keyword Planner** (free with any Google Ads account) — volume ranges.
  Not exact, but enough to distinguish a 2k cluster from a 20k cluster.
- **Keyword Surfer** (free Chrome extension) — volume + rough difficulty overlaid
  directly on the Google results page; good for fast cluster sweeps.
- **Google autocomplete + "People Also Ask" + "related searches"** — the primary
  source for `n_low_comp_terms`. This is how you find the fan of long-tails the
  transcript calls "zero-competition terms."
- **AnswerThePublic / Ubersuggest** — limited free queries/day; useful top-ups.

**Paid (one-month burst, only if free volumes are ambiguous):**
Ahrefs (~$129/mo) — exact volume, exact KD, filter KD≤10 in one click. Single
calibration month; cancel after the first scored batch.

**Decision rule:** if `cluster_kd > 35`, stop now. This is the KD_GATE; further
scoring is pointless regardless of volume.

---

## 4. KD proxy table (when Ahrefs is not available)

Set `cluster_kd` from a SERP read of the main keyword (Google, incognito):

| What the top 10 Google results look like | Proxy KD |
|---|---|
| Forums, thin blogs, no dedicated product pages | ~5 |
| A few small brands, mostly generic content | ~10 |
| Mixed: some focused stores, some established sites | ~15 |
| Mostly established brands + large retailers | ~25 |
| Amazon + national brands wall-to-wall | 40+ → **KD_GATE hit** |

The transcript's winners sit in the top two rows (KD 0–15).

---

## 5. Lens 2 — Transaction Proof (soft D4 proxy; informs moat inputs)

This is the **definitive Faire replacement** — and actually more direct demand
evidence, because it shows real end-buyer transactions rather than retailer orders.

**Tools (free):**
- **eBay Terapeak** (free in Seller Hub → Research → Terapeak Product Research) —
  real sold-through volume, average sale price, sell-through rate. Shows that
  *buyers paid money* for this category, not just searched for it.
- **Amazon "Bought in past month"** — visible on product listing pages; a direct
  sold-unit signal. Also check **review velocity**: use Keepa (free tier) to see
  whether review count is climbing (active sales) or flat.
- **Etsy sales count + eRank** — most useful for gifting / handcraft sub-niches
  where the buyer skews toward premium and bespoke.

**What to record (not an engine field — qualitative gate):**
- Is there active sold volume on Terapeak in this category?
- Does at least one comparable Amazon listing show "X+ bought in past month"?
- What's the review-count range of the top 5 competitors? (Indicates market maturity.)

**D4 at this stage:** enter `bol_unique_importers=0, bol_repeat_importers=0`. The
engine will score the ceiling achievable without BoL proof. Mark any HOT/WARM result
with the label **SHORTLIST — D4 UNVALIDATED**. Do not promote to a HuntList item
until D4 is confirmed with real BoL data (§9).

**Cut rule:** zero Terapeak sales + zero Amazon "bought in past month" → stop. No
volume of search traffic compensates for absent purchase evidence.

---

## 6. Lens 3 — Trend Velocity (confirms / adjusts trend field)

**Tools (free):**
- **Google Trends** — 5-year view + regional interest breakdown. The definitive
  source for the `trend` enum. Compare the past 12 months to the prior 12 months.
- **Pinterest Trends** — especially strong for home goods, gifting, lifestyle.
  A Pinterest trend rising 2–3 seasons in a row is a real consumer signal.
- **TikTok Creative Center** — surfaces viral demand surges that search tools catch
  later. Use for awareness, not confirmation.
- **Reddit** (niche subs) — a sub with 100k+ members and active product threads is
  a real, sustained cluster.

**Decision:**
- Two or more sources agree trend is rising → `RISING` (×1.0 multiplier).
- Mixed signals / flat → `FLAT` (×0.90).
- Two or more sources show declining or stagnant → `DECLINING` (×0.60; punishing).

---

## 7. Lens 4 — Competitive Reality (cluster_kd, niche_wedge, commodity_risk)

**Tools (free):**
- **SERP read** (Google, incognito) — confirms or refines the KD proxy from §4.
  Look at who ranks: if it's Amazon, Walmart, and REI, that is a KD 35+ situation.
- **Similarweb free** — rough traffic estimate on competitor DTC sites; shows whether
  one brand owns the category or the market is fragmented.
- **Competitor listing scan** — read 10–20 Amazon/Etsy listings:
  - 30+ near-identical listings (same materials, same price point, interchangeable
    photography) → `commodity_risk = HIGH` regardless of volume.
  - A clear subset nobody names explicitly ("for new dads", "corporate desk corner") →
    `niche_wedge = True`.
  - Competitors with a memorable name, distinctive visual identity, and appearances
    in editorial/gift roundups → `brandability = HIGH`.

---

## 8. Lens 5 — Macro (india_is_proven_origin; census radar)

**Tools (free):**

```powershell
# in INDIA-STOCKS — the Census API radar is already built
cd C:\Users\mygre\Documents\INDIA-STOCKS
python3 src/census_pipeline.py
```

The census radar flags HTS chapters growing in US imports. Cross-check India's
share of that chapter at **USITC DataWeb** (dataweb.usitc.gov — free, no account):
filter by HTS chapter, select India as partner, read the import value trend.

**Setting `india_is_proven_origin`:**
- India in top-5 origin countries for this HTS chapter → `True`.
- India absent or < 1% share → `False`. This is not a veto — but it raises
  execution risk (you may be first-mover into an untested lane for India).

---

## 9. ImportYeti BoL burst — Layer 2 (D4 definitive; gated)

This is the **only planned paid spike** for D4 data. It is confirmatory, not
generative — it runs after the free stack has already produced a shortlist.

**Gate: do not buy until all three conditions are true:**
1. ≥ 3 candidates carry the label **SHORTLIST — D4 UNVALIDATED**.
2. Every shortlist candidate has survived all five free lenses.
3. A capital decision (sampling PO, inventory order) is about to be made.

**Cost:** $130/mo. Buy one month, extract everything, cancel.

**Workflow:**
```
ImportYeti.com → search product category → export CSV
→ INDIA-STOCKS/data/bol/<keyword>.csv (manual file placement)
```

```powershell
# in INDIA-STOCKS — see OPERATING_MANUAL.md Steps 2–3
cd C:\Users\mygre\Documents\INDIA-STOCKS
python3 src/bol_pipeline.py --dry-run
```

Read off `unique consignees` and `repeat (≥2 shipments)`. Use the `--origin India`
filter to confirm `india_is_proven_origin`. Enter the numbers into
`bol_unique_importers` / `bol_repeat_importers` and **re-score the shortlist**.
Any HOT after re-score is now **actionable** and can be promoted to a HuntList item.

**D4 soft gates applied by the scoring engine:**
- `bol_unique_importers < 5` → import validation score = 0 (no meaningful market).
- `bol_repeat_importers < 2` → no repeat-buyer bonus (one-off shipment pattern).

---

## 10. Compliance sources

Primary: **`mission-control/MASTER_CONTEXT_MANIFEST.md` §1.1.2** holds the
per-market regulatory map. For anything not covered there:

- **EUDR** — EU Deforestation Regulation (leather/cattle is a named commodity).
  *Enforcement dates have shifted more than once — verify the current effective
  date before asserting it; never state a date as fact in client-facing copy.*
- **REACH (UK/EU)** — Chromium VI in leather capped at **3 mg/kg**.
- **US** — Prop 65 (heavy metals/dyes), CPSIA (lead in hardware), FTC labelling.
  India-origin is **not** subject to Section 301 China tariffs (a talking point,
  not a compliance blocker).
- **CITES** — exotic or reptile-derived leathers → export permits required →
  treat as `HARD_BLOCK` unless documented otherwise.

---

## 11. Phase-budget execution plan

**Phase 0 — Candidate generation ($0, ~1 hr):**
Generate 10–20 ideas from: Google Trends rising queries, "best X for [subset]"
gap spotting, census radar flags from `census_pipeline.py`, or the eight
transcript archetypes in `../README.md → Appendix`.

**Phase 1 — Search Intent sweep ($0, ~30 min/candidate):**
Pull D1, D2, D3, trend for each candidate (§3). Kill anything where
`cluster_kd > 35` immediately (KD_GATE). Target: cut to 8–12 survivors.

**Phase 2 — Transaction Proof check ($0, ~20 min/candidate):**
Terapeak + Amazon "bought in past month" for each survivor (§5). Kill any
candidate with zero sold evidence. Target: cut to 5–8 survivors.

**Phase 3 — Trend Velocity + Competitive Reality ($0, ~20 min/candidate):**
Google Trends 5-year + Pinterest + TikTok confirm `trend` (§6). SERP read +
competitor scan sets moat inputs (§7). Target: cut to 3–5 survivors.

**Phase 4 — Macro + Compliance + score ($0, ~30 min/candidate):**
Census pipeline + USITC DataWeb (§8). Compliance check (§10). Score each
survivor with `bol_unique_importers=0, bol_repeat_importers=0`. Label any
HOT/WARM result **SHORTLIST — D4 UNVALIDATED**. Write shortlist to `../O-output/`.

**Phase 5 — ImportYeti BoL burst ($130; trigger after Phase 4 gate):**
Pull BoL CSVs for all shortlist items (§9). Re-score with real D4 numbers.
Any HOT after re-score → promote to INDIA-STOCKS HuntList. Cancel ImportYeti.

**Phase 6 — Ahrefs burst (~$129; optional):**
Only if free-stack keyword volumes were ambiguous for multiple survivors. Exact
KD + volume for the shortlist only. Re-score if inputs change materially.

**Budget ceiling check:**

| Phase | Spend | Running total |
|---|---|---|
| 0 – 4 | $0 | $0 |
| 5 — ImportYeti (one month) | $130 | $130 |
| 6 — Ahrefs (one month, optional) | $129 | $259 |
| Buffer | — | $41 remaining ✓ |

The $300 ceiling holds even with both paid bursts active simultaneously.
