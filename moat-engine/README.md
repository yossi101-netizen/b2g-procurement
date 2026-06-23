# moat-engine

An **ABC-TOM** project. One job: **find single-product opportunities with a
defensible moat** — made in India, sold to the West — and prove demand is real
*before* committing. Demand-only; it never touches supplier sourcing.

This is a clean, isolated workspace seeded with only the essential logic. It does
not inherit the sprawl of the older systems (`the-system-v8`, `mission-control`,
`kritikaal-hub`); it references them where it needs their knowledge and stays
small on purpose.

```
moat-engine/
├─ C-core/        business DNA — what counts as a good opportunity, system limits
│   └─ 01-business-context.md
├─ B-brain/       the knowledge — scoring model + data sources
│   ├─ 01-scoring-model.md      ← canonical spec (the detailed logic)
│   └─ 02-data-sources.md
├─ T-tools/       the executable
│   └─ moat_discovery_engine.py ← air-gapped scoring engine + self-test
├─ A-agents/      who runs each step (human-driven for now)
├─ O-output/      ranked shortlists land here
└─ M-memory/      run log + calibration notes
```

**ABC = the foundation, set up once. TOM = the loop, run on each batch.**

---

## Quickstart

```powershell
cd C:\Users\mygre\Documents\yossi-workspace\moat-engine
python3 T-tools/moat_discovery_engine.py
```

Expected:

```
self-test passed: HOT=86, WARM=45, and 3 hard-gate DISCARDs reproduced exactly
```

---

## The TOM loop (run this per batch of ideas)

The engine is air-gapped: you gather numbers, you type them in, it scores. The
loop is the workflow around it. Full data-gathering detail is in
`B-brain/02-data-sources.md`.

### Step 1 — Generate candidate clusters
Seed ideas from: Google Trends rising queries, "best X for [subset]" gaps you
notice, categories the sibling `census_pipeline` flags, or KritiKaal's own
leather/SLG strengths. Each candidate = **one product + one keyword cluster**.

### Step 2 — Pull keyword metrics (per candidate)
With Ahrefs or the free stack, record for the cluster:
`cluster_volume` (sum), `cluster_kd` (main term, or proxy via SERP read),
`n_low_comp_terms` (how many sit at KD ≤ 10), and `trend` from Google Trends.

### Step 3 — Demand triangulation (Layer 1 free → Layer 2 burst)

Work through the five lenses in order. Trust convergence across all five; each is
orthogonal. Full tool detail is in `B-brain/02-data-sources.md`.

**Lens 1 — Search Intent:** already done in Step 2 (D1, D2, D3, trend seed).

**Lens 2 — Transaction Proof (required before advancing; the Faire substitute):**
eBay Terapeak (free, in Seller Hub) for sold-through volume. Amazon "bought in past
month" + review velocity. Etsy sales counts for gifting sub-niches. Zero sold
evidence on all three → stop; do not score.

**Lens 3 — Trend Velocity (confirm/adjust trend):**
Google Trends 5-year view + Pinterest Trends + TikTok Creative Center. Two sources
declining → set `trend=DECLINING` (0.60× multiplier is punishing).

**Lens 4 — Competitive Reality (tightens cluster_kd, sets moat inputs):**
SERP read refines KD proxy. Scan 10–20 competitor listings: 30+ near-identical
listings → `commodity_risk=HIGH`; a clear unowned subset → `niche_wedge=True`.

**Lens 5 — Macro (india_is_proven_origin; census corroboration):**
```powershell
# in INDIA-STOCKS
cd C:\Users\mygre\Documents\INDIA-STOCKS
python3 src/census_pipeline.py
```
Cross-check India's share of the HTS chapter at USITC DataWeb (free, no account).

**D4 at this stage — enter 0, mark UNVALIDATED:**
Set `bol_unique_importers=0, bol_repeat_importers=0`. Score the ceiling without BoL
proof. Label any HOT/WARM result **SHORTLIST — D4 UNVALIDATED**. Do not promote to
HuntList until D4 is confirmed.

**Layer 2 — ImportYeti BoL burst (trigger: ≥3 shortlist candidates, capital imminent):**
```powershell
# in INDIA-STOCKS — see its OPERATING_MANUAL.md Steps 2–3
cd C:\Users\mygre\Documents\INDIA-STOCKS
python3 src/bol_pipeline.py --dry-run
```
Read off `unique consignees` and `repeat (≥2 shipments)`. Use `--origin India`
to confirm `india_is_proven_origin`. Re-score with real D4. Any HOT after
re-score is now actionable.

### Step 4 — Judge moat + compliance
Set `material_premium`, `niche_wedge`, `brandability`, `commodity_risk`,
`price_band` from your read of the product and competitor listings. Set
`compliance_status` from `MASTER_CONTEXT_MANIFEST` §1.1.2 (CLEAR /
DOCUMENTED_LOAD / HARD_BLOCK).

### Step 5 — Score the batch
Build an `OpportunityInput` per candidate and rank them. Minimal script
(save as `T-tools/run_batch.py`, edit the list, run it):

```python
from moat_discovery_engine import (
    OpportunityInput, rank, Level, PriceBand, TrendDirection, ComplianceStatus,
)

batch = [
    OpportunityInput(
        name="<product + niche>",
        cluster_volume=14000, cluster_kd=6, n_low_comp_terms=6,
        trend=TrendDirection.RISING,
        bol_unique_importers=9, bol_repeat_importers=3, india_is_proven_origin=True,
        material_premium=Level.HIGH, niche_wedge=True, brandability=Level.HIGH,
        commodity_risk=Level.LOW, price_band=PriceBand.MID,
        compliance_status=ComplianceStatus.CLEAR,
    ),
    # ... more candidates ...
]

for r in rank(batch):
    print(f"{r.band.value:8} {str(r.score):>3}  {r.name}")
    print(f"           {r.reason}")
```

```powershell
cd C:\Users\mygre\Documents\yossi-workspace\moat-engine\T-tools
python3 run_batch.py
```

### Step 6 — Act on survivors
- **HOT** → promote to a real HuntList item in INDIA-STOCKS (see bridge below).
- **WARM** → close the weakest gap (often `bol_repeat_importers` or a real visual
  ref) and re-score.
- **WATCH / DISCARD** → log the reason in `M-memory/run-log.md` and move on. The
  *reasons* are the accumulating asset.

---

## Bridge to INDIA-STOCKS (where a HOT result goes to live)

moat-engine decides *what to open*; INDIA-STOCKS' HuntList tracks it from there.
A HOT result maps onto a `huntlist.py add` like this:

| moat-engine | → | HuntList field |
|---|---|---|
| candidate name | → | `--name` |
| price_band → your conservative $ | → | `--sell-price`, `--max-landed` |
| BoL unique/repeat importers | → | `--signal-source-tier tier_a`, `--signal-desc`, `--signal-scope product` |
| the search term | → | also add to `data\huntlist\bol_keyword_map.json` |
| a real competitor listing | → | `--benchmark-ref`, `--visual` |

```powershell
cd C:\Users\mygre\Documents\INDIA-STOCKS
python3 src/huntlist.py add --name "<HOT candidate>" --category "<cat>" --hts-chapter <NN> ^
  --benchmark-channel amazon_listing --benchmark-ref "<real listing URL>" ^
  --reasoning "moat-engine HOT (score NN): <one line>" ^
  --sell-price <NN> --max-landed <NN> ^
  --signal-type marketplace_observation --signal-source-tier tier_a ^
  --signal-desc "BoL: <U> unique, <R> repeat importers; cluster KD <kd>, vol <vol>" ^
  --signal-source "US Customs BoL (ImportYeti) + Ahrefs cluster" ^
  --signal-scope product --visual "<real url>::<what to match>"
```

(`^` is PowerShell line continuation. See `INDIA-STOCKS/OPERATING_MANUAL.md` for
the full HuntList workflow.)

---

## Appendix — what the transcript actually teaches

Source: *"This 'One-Product' Website Makes $600,000/Month"*. Eight one-product
businesses, reverse-engineered into the heuristics this engine encodes.

| # | Business | Product | Keyword signal | Pattern |
|---|---|---|---|---|
| 1 | PillowCube | cube pillow for side sleepers | "best pillow for side sleepers" 30k/KD5; "neck pain" 47k/KD9 | one product, one niche cluster |
| 2 | BikeTowLeash | bike-mounted dog leash ($183) | many terms at KD 0 | **fan of zero-comp long-tails** |
| 3 | MindJournals | men's journal ($50) | "men's journal" 3.5k/KD5; low CPC $0.70 | underserved subset + giftable |
| 4 | BigBarker | orthopedic beds for big dogs ($239–400) | "orthopedic/large dog bed" easy–med | high-ticket + becomes default rec |
| 5 | KNKG | men's gym duffel | "gym bag" 33k/KD11 (ranks #2 → 6k visits/mo) | **even popular terms can be underserved** |
| 6 | Nutr | nut-milk maker ($189) | "nut milk maker / almond milk machine" low-comp + TikTok | trend tailwind + long-tails |
| 7 | BigFig | mattress for plus-size sleepers | "mattress for heavy people" KD1 | **own a subset → become the default** |
| 8 | Vessi | 100% waterproof shoes ($100M/yr) | "waterproof shoes" 28k/KD14; "...for men" 7.8k/KD0 | real product moat + huge under-served search |

**Extracted heuristics → engine mapping:**

1. *One product, one cluster* → the unit of analysis is a single `OpportunityInput`.
2. *High aggregate volume* (one big term **or** a fan of small ones) → `D1` + `D3`.
3. *Low keyword difficulty* (KD 0–15) → `D2`, the heaviest demand weight, + `KD_GATE`.
4. *Underserved even when popular* → judged into `commodity_risk` / `niche_wedge`.
5. *"Best X for [subset]" wedge* → `M2 niche_wedge`.
6. *High-ticket / giftable* → `M5 price_band`.
7. *Becomes the default recommendation* → a brandability outcome → `M3`.
8. *Trend tailwind* (alt-milk, waterproof fashion) → `trend` multiplier.

**What the transcript leaves out, and this engine adds:**
- **Hard import validation** (`D4`, BoL) — the video stops at search interest; we
  demand evidence that real importers are already buying.
- **A moat axis** — the video's businesses had moats (Vessi's tech, BigFig's
  engineering) but never named the risk; we make "will cheap sellers clone it?"
  an explicit, weighted, gating question.
- **A regulatory screen** — irrelevant to a US dropshipper, essential for
  India → West physical-goods export.
