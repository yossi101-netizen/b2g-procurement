# US BoL SHIPMENT-GAP TRIGGER — TECHNICAL SPECIFICATION
# Phase 1 of the KritiKaal Intent Hunting Plan

**Status:** SPEC (build-ready) | **Date:** 2026-06-14 | **Owner:** Yossi (Founder)
**Scope:** US market only. Bill-of-Lading shipment-gap trigger only.
**Out of scope (do not build here):** UK, Israel, triage dashboard, agents A2 to A5.
**Parent:** KRITIKAAL_INTENT_HUNTING_PLAN.md (Config D, US leg, Phase 1)

> **One sentence:** find US leather-goods importers whose regular China shipments
> have gone silent for longer than their own normal cadence, prove the gap is
> real from the raw records, and rank the survivors by Fit x Timing.

---

## 0. DATA SOURCES AND THEIR LIMITS (read before trusting any field)

US ocean import manifest data (CBP AMS) is surfaced by ImportYeti (free),
ImportGenius, Panjiva, and Volza. Before specifying fields, four hard truths
about this data, because the whole trigger depends on them:

1. **No reliable declared value.** US ocean manifests do NOT carry customs value.
   Any "value" field from a provider is an estimate. We infer scale from weight,
   quantity, and container count, never from a declared dollar value.
2. **HS codes are partial.** Manifest data often carries a free-text product
   description and an incomplete or 6-digit HS code, sometimes none. We must match
   on HS code AND product-description keywords, not HS alone.
3. **Indexing latency.** Providers lag real arrivals by roughly 2 to 4 weeks. The
   trailing 30 days of "silence" may simply be unindexed shipments. The trigger
   must apply a data-latency buffer (see 2.4) or it will fire false gaps.
4. **Consignee masking.** Some importers appear as a freight forwarder or "C/O"
   party, hiding the real buyer. These records need identity resolution and are
   flagged lower-confidence.

These limits are not footnotes. They are the reason for specific rules below.

---

## 1. EXACT DATA FIELDS

### 1.1 Raw BoL fields ingested per shipment record

| Field | Type | Notes |
|---|---|---|
| `bol_number` | string | Unique manifest id. Primary dedupe key. |
| `consignee_name` | string | The US importer. Our prospect. Requires normalization. |
| `consignee_address` | string | City and state used for US-presence confirmation. |
| `consignee_is_forwarder` | bool | True if name matches the forwarder blocklist (see 1.4). |
| `shipper_name` | string | Foreign exporter (the China tannery or factory). |
| `shipper_country` | string | Origin country. China is the target origin. |
| `notify_party` | string | Sometimes reveals the true buyer when consignee is masked. |
| `arrival_date` | date | The event date. The spine of the entire gap calculation. |
| `port_of_lading` | string | Foreign load port (e.g., Yantian, Ningbo, Shanghai). |
| `port_of_unlading` | string | US discharge port (LA, Long Beach, NY/NJ, Savannah). |
| `hs_code` | string | 6 to 10 digit when present. May be null. Match with description. |
| `product_description` | string | Free text. Used for keyword match when HS is weak. |
| `weight_kg` | number | Gross weight. Primary volume proxy. |
| `quantity` | number | Pieces or cartons. Secondary volume proxy. Units vary, treat with care. |
| `container_count` | number | Container or TEU count. Tertiary volume proxy. |
| `carrier_scac` | string | Carrier code. Minor, used for dedupe sanity. |
| `vessel_voyage` | string | Vessel and voyage. Minor, used for dedupe sanity. |
| `source_provider` | string | importyeti / panjiva / volza. Provenance for the audit trace. |
| `source_url` | string | Direct link to the record. Required by anti-fabrication trace. |
| `pulled_at` | datetime | When we fetched it. Latency buffer is measured against this. |

### 1.2 Derived importer-profile fields (computed, per consignee per HS-group)

A "HS-group" is one of the target families in 1.3. We compute the profile per
(`consignee_id`, `hs_group`) because a brand can stop bags while continuing belts.

| Field | Type | How computed |
|---|---|---|
| `consignee_id` | string | Stable hash of the normalized consignee name. |
| `hs_group` | enum | LEATHER_BAGS_CASES, LEATHER_SLG, LEATHER_APPAREL_ACCESS, LEATHER_OTHER, LEATHER_FOOTWEAR. |
| `shipment_dates` | date[] | Sorted, deduped `arrival_date` list, lookback 24 months. |
| `n_shipments` | int | Count over lookback. |
| `cadence_days` | number | Median of consecutive inter-arrival intervals. |
| `cadence_mad` | number | Median absolute deviation of those intervals. |
| `last_arrival_date` | date | Max(`shipment_dates`). |
| `days_since_last` | int | `pulled_at` date minus `last_arrival_date`. |
| `overdue_ratio` | number | `days_since_last` / `cadence_days`. |
| `china_share` | number | Fraction of shipments (lookback) with `shipper_country` = China. |
| `supplier_hhi` | number | Herfindahl index of shipper concentration (0 to 1). |
| `origin_shift_flag` | bool | True if China shipments dropped but non-China rose (already diversifying). |
| `est_monthly_volume` | number | Rolling volume proxy from `weight_kg` (median monthly while active). |
| `volume_band` | enum | BELOW_MISSING_MIDDLE, MISSING_MIDDLE, ABOVE_MISSING_MIDDLE (see 3.2 F3). |
| `data_confidence` | enum | HIGH, MEDIUM, LOW. LOW if forwarder-masked or HS inferred from text only. |

### 1.3 Target HS-code reference

| HS-group | HS codes | Description-keyword backup |
|---|---|---|
| LEATHER_BAGS_CASES | 4202.11, 4202.21, 4202.91 | handbag, tote, briefcase, suitcase, leather case |
| LEATHER_SLG | 4202.31, 4202.32 | wallet, cardholder, key fob, pouch, small leather goods |
| LEATHER_APPAREL_ACCESS | 4203.10, 4203.21, 4203.29, 4203.30 | leather belt, leather glove, leather jacket |
| LEATHER_OTHER | 4205 | leather strap, leather goods, leather article |
| LEATHER_FOOTWEAR | 6403 | leather shoe, leather boot (footwear scope, lower priority) |

Match rule: a record joins a HS-group if its `hs_code` prefix matches OR (`hs_code`
is null AND `product_description` contains a backup keyword AND the description
contains "leather" or "genuine leather"). Synthetic, PU, and "vegan leather"
descriptions are excluded (wrong material).

### 1.4 Normalization and exclusion (data hygiene before any math)

- **Consignee normalization:** uppercase, strip punctuation, strip corporate
  suffixes (INC, LLC, LTD, CORP, CO), collapse whitespace, resolve common
  variants. Hash the result to `consignee_id`.
- **Forwarder blocklist:** if the normalized consignee matches a known freight
  forwarder or 3PL (e.g., EXPEDITORS, DHL, KUEHNE NAGEL, FLEXPORT, DSV, OOCL
  LOGISTICS), set `consignee_is_forwarder = True` and `data_confidence = LOW`.
  Try to recover the true buyer from `notify_party` before discarding.
- **Hard excludes:** records that are synthetic-material, samples-only
  (very low weight singletons), or transshipment re-exports.

---

## 2. THE GAP-DETECTION RULE

### 2.1 Preconditions (no history, no trigger)

```
REQUIRE n_shipments >= 4            # at least 3 intervals to trust a cadence
REQUIRE cadence_days is not null
REQUIRE data_confidence in {HIGH, MEDIUM}
ELSE   -> status = INSUFFICIENT_HISTORY   (never scored HOT)
```

### 2.2 Baseline cadence (robust, outlier-resistant)

We use the median and MAD, never the mean, because import schedules are spiky.

```
cadence_days = median(intervals)
cadence_mad  = median(| interval_k - cadence_days |)
sigma_robust = 1.4826 * cadence_mad        # MAD-to-sigma conversion
```

### 2.3 The anomaly test (is the silence statistically real)

```
expected_ceiling = cadence_days + 2 * sigma_robust

PRIMARY  : days_since_last > expected_ceiling
FALLBACK : if sigma_robust == 0 (perfectly regular importer)
           use days_since_last > 1.5 * cadence_days
```

A gap passes the anomaly test if PRIMARY (or FALLBACK when variance is zero) holds.

### 2.4 The actionability window (is the gap worth a call now)

A statistically real gap is only useful if the brand is still in pain and still
winnable. Apply both a data-latency floor and a staleness ceiling.

```
DATA_LATENCY_BUFFER = 30 days     # provider indexing lag; ignore silence inside it
ABS_FLOOR           = 45 days     # nothing under 45 days is "pain" yet
ABS_CEILING         = 180 days    # beyond 6 months they likely re-sourced or churned
REL_CEILING         = 2.5         # overdue_ratio above this is probably resolved/dead

actionable IF:
    days_since_last >= max(ABS_FLOOR, DATA_LATENCY_BUFFER)
AND days_since_last <= ABS_CEILING
AND overdue_ratio  <= REL_CEILING
```

### 2.5 Gap staging

```
overdue_ratio R = days_since_last / cadence_days

STALE  : R > 2.5  OR days_since_last > 180        -> deprioritize
HOT    : 1.5 <= R <= 2.5  AND actionable          -> the sweet spot
WATCH  : 1.25 <= R < 1.5  AND days_since_last>=45  -> monitor, do not contact yet
NONE   : R < 1.25                                  -> on schedule, no gap
```

### 2.6 Seasonality filter (suppress false distress)

Leather and fashion importers buy seasonally. A 65-day winter gap after a Q4 bulk
load can be normal, not distress. A gap is DOWNGRADED from HOT to WATCH if either
test fires:

1. **Year-over-year self-comparison.** If a silence of comparable length covered
   the same calendar window in a prior year for this same importer, the gap is
   seasonal. `seasonal_self = True`.
2. **Cohort co-silence.** If more than 40% of the fit-cohort (other importers in
   the same HS-group and China origin) are simultaneously silent in the same
   rolling 30-day window, the lull is category-wide, not importer-specific.
   `seasonal_cohort = True`.

```
seasonal_confidence = max(seasonal_self_score, seasonal_cohort_score)   # 0 to 1
IF seasonal_confidence >= 0.5  -> downgrade HOT to WATCH
```

The cohort test is the stronger of the two: an importer-specific gap while peers
keep shipping is the cleanest distress signal in the whole system.

### 2.7 Origin specificity

The gap we care about is a drop in CHINA-origin shipments (the China-Plus-One
pain). Compute the gap on the China-origin subset.

```
IF china shipments stopped AND non-china shipments rose in the same window:
    origin_shift_flag = True     # already diversifying, different pitch, lower timing
```

---

## 3. THE FIT x TIMING SCORING FORMULA

Both factors are scaled 0 to 1, then multiplied. Multiplication enforces the rule
that BOTH are required: a perfect-fit brand with no gap, or a gap on a non-fit
brand, must not rank high.

### 3.1 Hard gate (applied first)

```
IF FIT < 0.40  OR TIMING < 0.30  -> DISCARD (regardless of the other factor)
IF status in {INSUFFICIENT_HISTORY, INSUFFICIENT_DATA} -> not scored
```

### 3.2 FIT score (0 to 1)

```
FIT = 0.35*F1 + 0.25*F2 + 0.25*F3 + 0.15*F4
```

| Comp | Meaning | Scoring |
|---|---|---|
| F1 | Product fit | 1.0 for LEATHER_BAGS_CASES or LEATHER_SLG; 0.7 LEATHER_APPAREL_ACCESS; 0.5 LEATHER_OTHER; 0.4 LEATHER_FOOTWEAR |
| F2 | Origin fit | `china_share` directly (0 to 1). High China dependency is the target. |
| F3 | Volume fit (Missing Middle) | 1.0 if `volume_band` = MISSING_MIDDLE; 0.5 if BELOW; 0.3 if ABOVE |
| F4 | Importer maturity | scaled by `n_shipments` and `data_confidence`: 1.0 if n>=8 and HIGH; 0.7 if n 4-7; 0.4 if MEDIUM confidence |

Volume bands for F3 (proxy thresholds, calibrate after first real pull):
```
BELOW_MISSING_MIDDLE   : est_monthly_volume below the 300-unit-equivalent floor
MISSING_MIDDLE         : 300 to 3,000 unit-equivalent per style band
ABOVE_MISSING_MIDDLE   : large enough to run their own factory relationship
```

### 3.3 TIMING score (0 to 1)

```
TIMING = (0.45*T1 + 0.25*T2 + 0.30*T3) * (1 - seasonal_confidence) * origin_factor
```

| Comp | Meaning | Scoring |
|---|---|---|
| T1 | Gap severity | plateau on overdue_ratio R: 0 below 1.25; linear ramp 1.25 to 1.5; 1.0 across 1.5 to 2.5; linear decay 2.5 to 3.5; 0 above |
| T2 | Freshness | 1.0 when days_since_last in [45,120]; linear decay to 0 by 180; 0 below 45 |
| T3 | Concentration shock | `supplier_hhi` (single-supplier dependency hurts more); 1.0 near monopoly, lower when diversified |
| origin_factor | China specificity | 1.0 if the silenced line was China-origin; 0.5 if `origin_shift_flag` (already moving) |

### 3.4 Combine and band

```
RAW   = FIT * TIMING                 # 0 to 1
SCORE = round(100 * RAW)             # 0 to 100

HOT     : SCORE >= 55
WARM    : 35 <= SCORE <= 54
WATCH   : 20 <= SCORE <= 34
DISCARD : SCORE < 20
```

### 3.5 Worked example (the founder's case)

A handbag importer, ships from one Chinese supplier every 30 days, now silent 65
days, mid-band volume, 10 shipments of history, not seasonal.

```
cadence_days = 30, days_since_last = 65, R = 2.17
FIT:  F1=1.0, F2(china_share)=1.0, F3=1.0, F4=1.0  -> FIT = 1.00
TIMING: T1=1.0 (R in plateau), T2=1.0 (65 in [45,120]),
        T3=1.0 (single supplier), seasonal=0, origin_factor=1.0 -> TIMING = 1.00
RAW = 1.00 * 1.00 = 1.00  ->  SCORE = 100  ->  HOT
```

A realistic partial case: handbag importer, China_share 0.6, mid-band, n=5,
silent 95 days on a 50-day cadence (R=1.9), mild cohort seasonality 0.3.

```
FIT  = 0.35*1.0 + 0.25*0.6 + 0.25*1.0 + 0.15*0.7 = 0.855
TIMING = (0.45*1.0 + 0.25*0.84 + 0.30*0.7) * (1-0.3) * 1.0
       = (0.45 + 0.21 + 0.21) * 0.7 = 0.87 * 0.7 = 0.609
RAW = 0.855 * 0.609 = 0.521  ->  SCORE = 52  ->  WARM
```

---

## 4. THE A1 TRIGGER VALIDATOR SPEC (ANTI-FABRICATION)

A1 is the first Claude sub-agent. It receives the raw shipment rows plus the
computed gap metrics and must PROVE the gap is real from the rows before any lead
moves to A2 (OSINT). A1 has no web access and no outside knowledge. It only
validates the math against the data it was given.

### 4.1 Inputs

```json
{
  "consignee_id": "string",
  "consignee_name": "string",
  "hs_group": "enum",
  "computed_metrics": {
     "n_shipments": 0, "cadence_days": 0.0, "cadence_mad": 0.0,
     "last_arrival_date": "YYYY-MM-DD", "days_since_last": 0,
     "overdue_ratio": 0.0, "china_share": 0.0, "supplier_hhi": 0.0,
     "seasonal_confidence": 0.0, "origin_shift_flag": false,
     "data_confidence": "HIGH|MEDIUM|LOW", "pulled_at": "YYYY-MM-DD"
  },
  "raw_shipments": [
     {"bol_number":"", "arrival_date":"YYYY-MM-DD", "shipper_country":"",
      "hs_code":"", "product_description":"", "weight_kg":0,
      "source_url":""}
  ]
}
```

### 4.2 System prompt (verbatim, build-ready)

```
You are A1, the Trigger Validator for KritiKaal's US BoL intent engine. Your only
job is to PROVE or DISPROVE that a shipment gap is real, using ONLY the shipment
rows provided in this message. You do not research companies. You do not use any
outside knowledge. You do not guess.

NON-NEGOTIABLE RULES:
1. Every factual claim you make must cite a specific bol_number and arrival_date
   from raw_shipments. If you cannot cite a row, you may not make the claim.
2. Never invent, estimate, or "fill in" a shipment, date, HS code, country, or
   name. If a field is missing or null, write "UNKNOWN". Missing data is a valid
   and required answer.
3. Recompute the gap yourself from raw_shipments. Sort arrival_date ascending,
   compute the consecutive intervals, take the median as cadence, and compute
   days_since_last as pulled_at minus the latest arrival_date. Compare your
   numbers to computed_metrics. If they disagree by more than 10 percent on
   cadence_days or by more than 3 days on days_since_last, set verdict to
   REJECTED with reason "METRIC_MISMATCH" and report both numbers.
4. Apply the preconditions. If fewer than 4 shipments, or data_confidence is LOW,
   return INSUFFICIENT_DATA. Do not attempt to validate a gap you cannot support.
5. Apply the data-latency rule. If days_since_last is at or below 30, return
   REJECTED with reason "WITHIN_LATENCY_BUFFER" (the silence may be unindexed
   recent arrivals, not a real gap).
6. State the seasonality position. You are given seasonal_confidence; if it is
   0.5 or higher, note that the gap is likely seasonal and recommend WATCH, not
   HOT. Do not override the number with a guess.
7. You may not describe the company, its brand, its products beyond what the
   product_description fields literally say, or its reasons for the gap. Cause
   analysis is A2's job, not yours. Stay inside the shipment data.
8. If the China-origin subset is what went silent, say so and cite the last
   China-origin bol_number and date. If non-China shipments continued, say so and
   cite them. This distinction matters and must be evidence-backed.

OUTPUT: return only the JSON object defined in the output schema. No prose
outside the JSON. Confidence must reflect evidence strength: HIGH only when you
personally recomputed the gap and it cleared every rule with cited rows.
```

### 4.3 Output schema

```json
{
  "consignee_id": "string",
  "verdict": "VALIDATED | REJECTED | INSUFFICIENT_DATA",
  "verdict_reason": "string",
  "evidence": {
     "recomputed_cadence_days": 0.0,
     "recomputed_days_since_last": 0,
     "last_arrival_cited": {"bol_number":"", "arrival_date":""},
     "last_china_arrival_cited": {"bol_number":"", "arrival_date":""},
     "n_shipments_seen": 0,
     "metric_agreement": "MATCH | MISMATCH"
  },
  "seasonality_position": "NOT_SEASONAL | LIKELY_SEASONAL | UNKNOWN",
  "recommended_stage": "HOT | WATCH | REJECT",
  "confidence": "HIGH | MEDIUM | LOW",
  "unknowns": ["list of fields marked UNKNOWN"]
}
```

### 4.4 Pass criteria to A2

A lead advances to A2 (OSINT) only if:
```
verdict == VALIDATED
AND recommended_stage == HOT
AND confidence in {HIGH, MEDIUM}
AND metric_agreement == MATCH
```
Everything else is logged with its reason and held. Nothing un-validated is ever
contacted. A fabricated gap reaching a real prospect under the founder's name is
the single worst failure mode of this system, which is why A1 exists before A2.

---

## 5. BUILD ORDER (within this one trigger)

1. Ingest and normalize one real pull (HS 4202, China origin, US consignees).
2. Implement the derived profile and the gap rule (section 2). Eyeball the HOT list.
3. Implement Fit x Timing scoring (section 3). Check the ranking is sane.
4. Wire A1 (section 4) and confirm it rejects the planted bad cases.
5. Only then, hand the validated HOT list to A2 (a later mission).

---

*US BoL Shipment-Gap Trigger Spec v1.0 | 2026-06-14 | CORE-side, demand-only*
*Thresholds are initial values. Calibrate against the first real pull before scale.*
