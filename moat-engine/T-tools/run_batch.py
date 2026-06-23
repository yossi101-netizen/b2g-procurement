"""
run_batch.py -- Score a batch of demand JSON files through moat_discovery_engine.
Usage: python3 T-tools/run_batch.py <batch_dir>
       python3 T-tools/run_batch.py M-memory/batches/20260617_232756
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from moat_discovery_engine import (
    OpportunityInput, rank, Level, PriceBand, TrendDirection, ComplianceStatus,
)


def load_input(path: Path) -> OpportunityInput:
    d = json.loads(path.read_text(encoding="utf-8"))

    if not d.get("engine_ready"):
        raise ValueError(f"{path.name}: engine_ready is not true — fill moat_inputs first")

    dem = d["demand"]
    mi = d["moat_inputs"]

    return OpportunityInput(
        name=d["name"],
        cluster_volume=dem["cluster_volume"],
        cluster_kd=float(dem["cluster_kd"]),
        n_low_comp_terms=int(dem["n_low_comp_terms"]),
        trend=TrendDirection(dem["trend"]),
        bol_unique_importers=int(mi["bol_unique_importers"]),
        bol_repeat_importers=int(mi["bol_repeat_importers"]),
        india_is_proven_origin=bool(mi.get("india_is_proven_origin") or False),
        material_premium=Level(mi["material_premium"]),
        niche_wedge=bool(mi["niche_wedge"]),
        brandability=Level(mi["brandability"]),
        commodity_risk=Level(mi["commodity_risk"]),
        price_band=PriceBand(mi["price_band"]),
        compliance_status=ComplianceStatus(mi["compliance_status"]),
        compliance_notes=mi.get("compliance_notes") or [],
    )


def main() -> int:
    if len(sys.argv) < 2:
        batch_dir = Path(__file__).resolve().parent.parent / "M-memory" / "batches"
        # use most recent batch
        subdirs = sorted(batch_dir.glob("*/"), reverse=True)
        if not subdirs:
            print("No batch directories found. Pass a batch path as argument.", file=sys.stderr)
            return 1
        batch_dir = subdirs[0]
        print(f"No batch specified — using most recent: {batch_dir.name}\n")
    else:
        batch_dir = Path(sys.argv[1])
        if not batch_dir.is_absolute():
            batch_dir = Path.cwd() / batch_dir

    demand_files = sorted(batch_dir.glob("*_demand.json"))
    if not demand_files:
        print(f"No *_demand.json files found in {batch_dir}", file=sys.stderr)
        return 1

    candidates: list[OpportunityInput] = []
    skipped: list[str] = []

    for f in demand_files:
        try:
            candidates.append(load_input(f))
        except ValueError as e:
            skipped.append(str(e))
        except Exception as e:
            skipped.append(f"{f.name}: {e}")

    if skipped:
        print("SKIPPED (not engine_ready or bad data):")
        for s in skipped:
            print(f"  {s}")
        print()

    if not candidates:
        print("No engine-ready candidates to score.")
        return 0

    results = rank(candidates)

    print(f"{'BAND':<8} {'SCORE':>5}  {'NAME'}")
    print("-" * 70)
    for r in results:
        flag = ""
        if r.band.value == "DISCARD":
            flag = "  ← DISCARD"
        print(f"{r.band.value:<8} {str(r.score or 0):>5}  {r.name}{flag}")
        print(f"         {r.reason}")
        if r.components:
            d = r.components
            print(
                f"         D1={d.get('D1_volume','-'):.2f} "
                f"D2={d.get('D2_difficulty','-'):.2f} "
                f"D3={d.get('D3_breadth','-'):.2f} "
                f"D4={d.get('D4_import','-'):.2f} "
                f"trend×{d.get('trend_mult','-')} | "
                f"M1={d.get('M1_material_premium','-'):.2f} "
                f"M2={d.get('M2_niche_wedge','-'):.2f} "
                f"M3={d.get('M3_brandability','-'):.2f} "
                f"M4={d.get('M4_knockoff_resistance','-'):.2f} "
                f"M5={d.get('M5_unit_econ','-'):.2f}"
            )
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
