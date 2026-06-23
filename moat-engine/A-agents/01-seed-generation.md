# Cluster Scout — Seed Generation Method

One job: produce 15–20 product candidates for a moat-engine scoring batch.
Each candidate = **one product + one keyword cluster**.

**Core strategic rule:** a novel invention is not required — and in practice is
harder to validate. An **existing product with proven demand** is the preferred
starting point, provided we can demonstrably upgrade it using premium India-native
capabilities. This is the KNKG / BigBarker pattern: known demand, engineered moat.
It also means BoL data (D4) will already exist for the category — the import trail
is pre-established. Novel ideas score zero on D4 by definition.

---

## The four seed sources

Run all four. Combine and de-duplicate outputs. Target 15–20 survivors.

---

### Source A — Transcript archetype × India material matrix

Cross the eight transcript archetypes against India's premium capabilities. Every
intersection where incumbents use commodity materials and we can make something
demonstrably better is a candidate.

**India premium capability index:**

| Material / craft | Cluster | Moat potential |
|---|---|---|
| Full-grain / veg-tan leather | Kanpur, Kolkata | HIGH — provenance + hand-stitch |
| Handloom cotton / linen | Jaipur, Ahmedabad | MED-HIGH — block-print makes it proprietary |
| Silk / Chanderi fabric | Varanasi, Bhopal | HIGH for gifting / accessories |
| Brass / bronze metalwork | Moradabad, Rajasthan | HIGH — distinctive finish, tactile weight |
| Sheesham / mango wood | Jodhpur, Saharanpur | MED — artisan grain, non-commodity feel |
| Ceramics / blue pottery | Jaipur, Khurja | MED for home goods / kitchenware |
| Jute / natural fiber | West Bengal | MED — strong sustainable narrative |
| Pashmina / wool | Kashmir, Himachal | HIGH — geographic origin IS the moat |
| Hand-knotted / hand-tufted textiles | Bhadohi, Kashmir | HIGH — labour moat, low KD sub-niches |

**Archetype × material matrix (8 immediate seed candidates):**

| Archetype (proven demand) | Incumbent weakness | India material upgrade | Seed candidate |
|---|---|---|---|
| PillowCube — side-sleeper cube pillow; "best pillow for side sleepers" 30k KD5 | foam + polyester = commodity | Handloom cotton shell + kapok fill | Handloom-covered cube pillow for side sleepers |
| BikeTowLeash — dog leash ($183); fan of KD0 long-tails | nylon + plastic hardware | Full-grain leather + cast brass hardware | Premium leather dog leash + collar set |
| MindJournals — men's journal ($50); "men's journal" 3.5k KD5, giftable | generic faux-leather cover | Hand-block-print linen cover + handmade paper | Block-printed linen journal, gift-boxed |
| BigBarker — orthopedic large-dog bed ($239-400); "large dog bed" easy-med | MDF frame + mass fabric | Sheesham wood frame + handloom cotton ticking | Artisan wood-framed large-dog orthopedic bed |
| KNKG — men's gym duffel; "gym bag" 33k KD11, ranks #2 | ballistic nylon = commodity | Full-grain leather weekend/gym duffel | Premium leather gym duffel — India craft |
| Nutr — nut-milk maker ($189); "nut milk maker" low-comp + TikTok | plastic body | Brass + teak slow-pour milk jug set | Hand-turned brass + teak beverage set |
| BigFig — mattress for heavy sleepers; "mattress for heavy people" KD1 | foam/springs | Handloom wool-filled zafu/zabuton floor set | Wool meditation floor cushion set, heavy-duty |
| Vessi — waterproof shoes ($100M); "waterproof shoes" 28k KD14 | synthetic upper | Waxed cotton + full-grain leather Chelsea boot | Waxed-cotton waterproof boot, India-craft |

---

### Source B — "Best X for [subset]" gap hunt (free, ~30 min)

Search Google autocomplete for high-volume categories + underserved modifier
combinations. Record any suggestion that returns < 5 dedicated DTC brand results
on the first SERP page — that blank space is the `niche_wedge`.

Starter sweeps:

```
"best desk organizer for ___"    → home office / minimalist / men / standing desk
"best gym bag for ___"           → minimalist / carry-on travel / leather / men's
"best dog leash for ___"         → large breeds / hiking / hands-free / running
"best journal for ___"           → men / grief / anxiety / new dads / couples
"best pillow for ___"            → side sleepers / neck pain / pregnancy / hot sleepers
"best tote bag for ___"          → work / farmers market / leather / minimalist
"best dog collar for ___"        → large breeds / training / leather / no-pull
"best laptop bag for ___"        → minimalist / men's leather / standing desk workers
```

For each gap found: check that (a) India-native material can be applied, and (b) price
point above $60 is plausible. Below $60 → margin is too thin for premium handcraft.

---

### Source C — Census radar flags (one command, already built)

```powershell
cd C:\Users\mygre\Documents\INDIA-STOCKS
python3 src/census_pipeline.py
```

The radar flags HTS chapters with growing US import value. Each flagged chapter is
a live category signal; drill to a specific product within it.

Common chapters to watch for India-native output:
- HTS 4202 — trunks, cases, handbags, leather goods (bags, wallets, organizers)
- HTS 4205 — other leather articles (leashes, belts, straps)
- HTS 6301–6307 — home textiles (throws, cushion covers, table runners)
- HTS 6912 — ceramic tableware (mugs, bowls, plates)
- HTS 7418 — brass / copper table / kitchen articles
- HTS 9404 — pillows, mattress supports (cushions, meditation sets)

Run the pipeline, read the flagged chapters, add 2–4 product seeds from live HTS
growth data. These seeds carry a built-in `india_is_proven_origin = True` head start.

---

### Source D — eBay Terapeak category sweep (free, ~20 min)

Open Terapeak (eBay Seller Hub → Research → Terapeak Product Research). Sort sold
listings by category. Flag categories where:
- Average sold price > $60 (premium-viable margin)
- Sell-through rate > 40% (active buyer demand, not stagnant inventory)
- No dominant single brand in the top 20 results (fragmented = enterable)

Each flagged category from Terapeak provides independent transaction proof before
you build a keyword cluster — you are confirming buyers first, then searching for
the keyword signal, not the other way around. This inverts the usual process and
dramatically reduces wasted scoring cycles.

---

## Combining and pre-filtering

After running all four sources:

1. List every candidate.
2. Remove near-duplicates (e.g. "leather dog leash" and "leather dog collar" → merge into one "leather dog leash + collar set").
3. **Fast pre-filter** — drop any candidate where:
   - You already know cluster_kd > 35 (KD_GATE, no point scoring).
   - India-origin is structurally impossible for the product.
   - Price point below $60 (margin incompatible with handcraft cost structure).
4. Target 15–20 survivors.

---

## Output format

Write each seed as a one-liner before entering Phase 1:

```
[##] <Product + niche descriptor>
     Material angle: <India capability + cluster>
     Category: HTS <chapter>
     Source: <A / B / C / D>
```

Example:
```
[01] Premium leather gym duffel — men's everyday carry
     Material angle: veg-tan leather, Kanpur
     Category: HTS 4202
     Source: A (KNKG archetype)

[02] Handloom cube pillow — side sleeper
     Material angle: block-print cotton shell, Jaipur
     Category: HTS 9404
     Source: A (PillowCube archetype)
```

This list feeds directly into Phase 1 of the phase-budget execution plan
(`B-brain/02-data-sources.md §11`).
