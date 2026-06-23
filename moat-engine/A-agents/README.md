# A-agents

The roles that run the TOM loop. Human-driven for now; each maps to a future
automation slot, but nothing here scrapes or calls the network today.

| Role | Does | Feeds engine field(s) |
|---|---|---|
| **Cluster Scout** | generates 15–20 seed candidates using the four-source method in `01-seed-generation.md` (archetype matrix, gap hunt, census radar, Terapeak sweep) | the candidate list |
| **Keyword Analyst** | pulls volume / KD / breadth / trend | `cluster_volume`, `cluster_kd`, `n_low_comp_terms`, `trend` |
| **Import Validator** | runs ImportYeti CSV → `bol_pipeline.py`, reads off importer counts | `bol_unique_importers`, `bol_repeat_importers`, `india_is_proven_origin` |
| **Moat Judge** | scores material / wedge / brand / commodity-risk / price | the MOAT inputs |
| **Compliance Checker** | screens against `MASTER_CONTEXT_MANIFEST` §1.1.2 | `compliance_status`, `compliance_notes` |
| **Scorer** | builds the batch, runs `rank()`, writes the shortlist to `O-output/` | — |

Automate later, in this order of payoff: Keyword Analyst (API) → Import
Validator (CSV parse) → Cluster Scout (Trends API). Moat Judge and Compliance
Checker stay human — they are judgement, not data.
