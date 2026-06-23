# M-memory — run log & calibration

Append one block per scoring batch. This is where v0.1 → v1.0 calibration happens.

---

## Template

```
### YYYY-MM-DD — batch <n>
- Candidates scored: <n>
- HOT: <names>  | WARM: <names>
- Notable DISCARDs + gate: <name → GATE_NAME (reason)>
- Disagreements with engine (operator overrides): <...>
- Threshold to revisit: <e.g. "vol band felt too generous at 5k">
```

---

## Calibration checklist (close before declaring v1.0)

- [ ] First real batch (10–15 candidates) scored.
- [ ] Bands eyeballed against operator judgement.
- [ ] Any threshold / weight changes mirrored into both
      `B-brain/01-scoring-model.md` and `T-tools/moat_discovery_engine.py`.
- [ ] Self-test updated and passing.
- [ ] Version bumped to v1.0 in the spec and the engine header.

---

## Log

### 2026-06-18 — batch 20260618_065416 (seeds 01–05, canonical)

- Candidates scored: 5
- HOT: [05] wood-framed dog bed (68), [01] leather gym bag (65), [03] leather dog leash (61)
- WARM: none
- DISCARDs:
  - [02] cube pillow → DECLINING trend (trend_mult=0.60 collapses score)
  - [04] block-printed linen journal (re-seeded as "mens leather journal") → DEMAND_GATE:
    zero low-comp long-tails (D3=0.10), low volume band; seed re-key from linen journal
    to mens leather journal produced some improvement in KD but not enough to clear gate
- Accessible KD (fallback — DFS plan returns 0 for seed keyword, using mean sub-100 from cluster):
  [01]=4.5, [02]=11.7, [03]=13.1, [04]=35.0 (saturated cluster fallback), [05]=6.9
- Disagreements with engine: none — operator agrees with all 5 verdicts
- Notes:
  - First real batch; bands feel directionally correct
  - KD_GATE=35 nearly caught [04] (accessible KD hit exactly 35.0 fallback floor);
    if seed keyword produces saturated cluster in future, treat as WATCH not HOT
  - [05] at score 68 is the top candidate: rising trend + real moat (sheesham wood
    frame — cloners can't match the material/finish combination cheaply)
  - Phase 3 (Transaction Proof) now authorised for [01], [03], [05]
