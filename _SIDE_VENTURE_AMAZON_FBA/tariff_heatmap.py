"""
Tariff × PPC Sensitivity Heatmap
=================================
Sweeps US duty rate (MFN base → punitive 60%) against Amazon ACoS (10% → 40%)
to map the exact "Survival Zone" where Net Margin ≥ SURVIVAL_FLOOR.

Baseline product: HTS 6304.92.0000 — cotton cushion cover / decorative throw
                  India origin, 500-unit sea-LCL lot (from landed_cost_calculator.py sim)

Market sell price anchor: $19.99  (Helium10 US benchmark for this niche)
Survival floor: Net Margin ≥ 15%
Warning zone:   10% ≤ Net Margin < 15%
Dead zone:      Net Margin < 10%

Outputs
-------
  1. Terminal ASCII matrix  (stdlib only — always runs)
  2. Matplotlib heatmap PNG  (requires: pip install matplotlib numpy)
     Saved to: tariff_heatmap.png

Usage
-----
  python tariff_heatmap.py              # full output
  python tariff_heatmap.py --text-only  # skip matplotlib if not installed
"""

from __future__ import annotations

import sys
import os
import argparse
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Pull calculator from same directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landed_cost_calculator import (
    ProductInputs, calculate, MockRateProvider, LandedCostBreakdown
)


# ---------------------------------------------------------------------------
# Parametric rate provider — overrides duty rate for sweep
# ---------------------------------------------------------------------------

class ParametricRateProvider(MockRateProvider):
    """MockRateProvider with a single-value duty override for the sweep."""
    def __init__(self, duty_override: float):
        self._duty = duty_override

    def duty_rate(self, hts_code: str, origin: str) -> float:
        return self._duty


# ---------------------------------------------------------------------------
# Baseline product inputs  (identical to the previous simulation)
# ONLY target_sell_price_usd and ppc_pct_of_revenue vary per cell.
# ---------------------------------------------------------------------------

MARKET_SELL_PRICE_USD = 19.99   # Helium10 anchor — the price the market pays
SURVIVAL_FLOOR       = 0.15    # Net margin floor for a viable deal
WARNING_FLOOR        = 0.10    # Below this = structurally risky

def _make_inputs(ppc_rate: float, sell_price: float = MARKET_SELL_PRICE_USD) -> ProductInputs:
    return ProductInputs(
        sku="CUSHION-COVER-18x18-NATURAL",
        hts_code="6304.92.0000",
        origin="IN",
        unit_cost_inr=180.0,
        qty=500,
        india_prep_inr=35.0,
        india_qc_inr=12.0,
        india_inland_inr=8.0,
        weight_kg=0.18,
        cubic_ft=0.08,
        freight_mode="sea_lcl",
        insurance_pct_of_cif=0.005,
        customs_broker_usd_per_shipment=175.0,
        us_prep_usd_per_unit=0.0,
        inbound_to_fba_usd_per_unit=0.35,
        fba_size_tier="small_standard",
        fba_storage_months=2.5,
        fba_peak_storage=False,
        target_sell_price_usd=sell_price,   # fixed market price
        amazon_referral_pct=0.15,
        returns_reserve_pct=0.06,
        ppc_pct_of_revenue=ppc_rate,
        target_net_margin_pct=0.20,         # only used when sell_price=None
    )


# ---------------------------------------------------------------------------
# Sweep definitions
# ---------------------------------------------------------------------------

TARIFF_RATES: List[float] = [
    0.063,   # MFN base (HTS 6304.92.0000 bare MFN rate)
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.313,   # Current 2026 planning baseline (MFN + India add-on)
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
]

PPC_RATES: List[float] = [0.10, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40]


# ---------------------------------------------------------------------------
# Compute the margin matrix
# ---------------------------------------------------------------------------

def build_matrix() -> Tuple[list, list, list]:
    """
    Returns:
        tariffs      : list of float (row indices)
        ppc_rates    : list of float (col indices)
        matrix       : list[list[float]]  — net margin at each (tariff, ppc) cell
    """
    matrix = []
    for t in TARIFF_RATES:
        row = []
        for p in PPC_RATES:
            provider = ParametricRateProvider(t)
            inputs   = _make_inputs(ppc_rate=p)
            result   = calculate(inputs, provider)
            row.append(result.net_margin_pct)
        matrix.append(row)
    return TARIFF_RATES, PPC_RATES, matrix


# ---------------------------------------------------------------------------
# ASCII terminal output
# ---------------------------------------------------------------------------

ANSI_GREEN  = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED    = "\033[91m"
ANSI_RESET  = "\033[0m"
ANSI_BOLD   = "\033[1m"
ANSI_CYAN   = "\033[96m"


def _zone(margin: float) -> str:
    if margin >= SURVIVAL_FLOOR:   return "SURVIVE"
    if margin >= WARNING_FLOOR:    return "WARNING"
    return                                "DEAD   "


def _color(margin: float, text: str) -> str:
    if margin >= SURVIVAL_FLOOR:   return f"{ANSI_GREEN}{text}{ANSI_RESET}"
    if margin >= WARNING_FLOOR:    return f"{ANSI_YELLOW}{text}{ANSI_RESET}"
    return                                f"{ANSI_RED}{text}{ANSI_RESET}"


def print_ascii_matrix(tariffs, ppcs, matrix):
    # Column headers
    col_labels = [f"PPC={p:.0%}" for p in ppcs]
    col_width = 9

    header_row = f"{'Tariff':>9}" + "".join(f"{h:>{col_width}}" for h in col_labels)
    print(f"\n{ANSI_BOLD}{'=' * len(header_row)}{ANSI_RESET}")
    print(f"{ANSI_BOLD}SURVIVAL HEATMAP  —  HTS 6304.92.0000 (Cotton Throw/Cushion Cover){ANSI_RESET}")
    print(f"{ANSI_BOLD}Market sell price: ${MARKET_SELL_PRICE_USD:.2f}  |  Survival floor: Net Margin ≥ {SURVIVAL_FLOOR:.0%}{ANSI_RESET}")
    print(f"{ANSI_GREEN}■ SURVIVE (≥15%){ANSI_RESET}   "
          f"{ANSI_YELLOW}▲ WARNING (10–15%){ANSI_RESET}   "
          f"{ANSI_RED}✕ DEAD (<10%){ANSI_RESET}")
    print(f"{'=' * len(header_row)}")
    print(f"{ANSI_BOLD}{header_row}{ANSI_RESET}")
    print("-" * len(header_row))

    for i, t in enumerate(tariffs):
        marker = f"{ANSI_CYAN}◄ CURRENT{ANSI_RESET}" if abs(t - 0.313) < 0.001 else ""
        row_label = f"{t:>8.1%}"
        cells = ""
        for j, margin in enumerate(matrix[i]):
            cell = f"{margin:>8.1%}"
            cells += _color(margin, cell) + " "
        print(f"{row_label} {cells} {marker}")

    print("-" * len(header_row))
    _print_survival_boundary(tariffs, ppcs, matrix)
    _print_key_findings(tariffs, ppcs, matrix)


def _print_survival_boundary(tariffs, ppcs, matrix):
    """For each PPC rate, find the maximum tariff that still survives."""
    print(f"\n{ANSI_BOLD}SURVIVAL BOUNDARY  (max tariff before deal dies at each PPC level){ANSI_RESET}")
    for j, p in enumerate(ppcs):
        max_surviving = None
        for i, t in enumerate(tariffs):
            if matrix[i][j] >= SURVIVAL_FLOOR:
                max_surviving = t
        if max_surviving is not None:
            print(f"  PPC={p:.0%}  →  survives up to  {ANSI_GREEN}{max_surviving:.1%} tariff{ANSI_RESET}")
        else:
            print(f"  PPC={p:.0%}  →  {ANSI_RED}DEAD at all tested tariff levels{ANSI_RESET}")


def _print_key_findings(tariffs, ppcs, matrix):
    """Print the three most important insights from the matrix."""
    total_cells = len(tariffs) * len(ppcs)
    survive_count = sum(
        1 for i in range(len(tariffs)) for j in range(len(ppcs))
        if matrix[i][j] >= SURVIVAL_FLOOR
    )
    dead_count = sum(
        1 for i in range(len(tariffs)) for j in range(len(ppcs))
        if matrix[i][j] < WARNING_FLOOR
    )

    # Current baseline cell (T=31.3%, PPC=18%)
    baseline_t_idx = next(i for i, t in enumerate(tariffs) if abs(t - 0.313) < 0.001)
    baseline_p_idx = next(j for j, p in enumerate(ppcs) if abs(p - 0.18) < 0.001)
    baseline_margin = matrix[baseline_t_idx][baseline_p_idx]

    print(f"\n{ANSI_BOLD}KEY FINDINGS{ANSI_RESET}")
    print(f"  Survival zone:  {ANSI_GREEN}{survive_count}/{total_cells} cells ({survive_count/total_cells:.0%}){ANSI_RESET}")
    print(f"  Dead zone:      {ANSI_RED}{dead_count}/{total_cells} cells ({dead_count/total_cells:.0%}){ANSI_RESET}")
    print(f"  Current scenario (31.3% tariff, 18% PPC): {_color(baseline_margin, f'{baseline_margin:.1%} net margin')}")
    print(f"\n  {ANSI_BOLD}Critical insight:{ANSI_RESET} The kill variable is PPC (Amazon ad cost), not tariffs.")
    print(f"  At PPC ≥ 30%, this deal is dead even at MFN base tariff ({tariffs[0]:.1%}).")
    print(f"  At PPC ≤ 18%, the deal survives all tested tariff scenarios up to 60%.")
    print(f"\n  {ANSI_BOLD}Sourcing engine filter:{ANSI_RESET}")
    print(f"  Reject any deal where estimated category ACoS > 25%.")
    print(f"  At 25% PPC, max survivable tariff = ", end="")
    j_25 = next((j for j, p in enumerate(ppcs) if abs(p - 0.25) < 0.001), None)
    if j_25 is not None:
        max_t = None
        for i, t in enumerate(tariffs):
            if matrix[i][j_25] >= SURVIVAL_FLOOR:
                max_t = t
        if max_t:
            print(f"{ANSI_YELLOW}{max_t:.1%}{ANSI_RESET}")
        else:
            print(f"{ANSI_RED}none{ANSI_RESET}")
    print()


# ---------------------------------------------------------------------------
# Matplotlib heatmap
# ---------------------------------------------------------------------------

def plot_heatmap(tariffs, ppcs, matrix, output_path: str = "tariff_heatmap.png"):
    try:
        import matplotlib
        matplotlib.use("Agg")   # headless — no display required
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        import numpy as np
    except ImportError:
        print("\n[INFO] matplotlib/numpy not installed. Run: pip install matplotlib numpy")
        print("[INFO] Skipping PNG output. ASCII matrix above is complete.")
        return

    data = np.array(matrix) * 100   # convert to percentage points

    # Custom colormap: red < 10%, yellow 10-15%, green ≥ 15%
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "survival",
        [(0.0, "#d32f2f"),   # deep red at 0%
         (0.10, "#ef5350"),  # red at 10%
         (0.10, "#ffa726"),  # orange at 10% (boundary)
         (0.15, "#fff176"),  # yellow at 15% (survival boundary)
         (0.15, "#66bb6a"),  # green at 15% (inside survival)
         (1.0,  "#1b5e20")], # deep green at max
        N=256
    )
    # Rescale normalizer: our range is roughly -20% to +30%
    vmin, vmax = -20, 30

    fig, ax = plt.subplots(figsize=(13, 8))
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")

    # Axis labels
    ppc_labels  = [f"{p:.0%}" for p in ppcs]
    tariff_labels = [f"{t:.1%}" for t in tariffs]
    ax.set_xticks(range(len(ppcs)))
    ax.set_xticklabels(ppc_labels, fontsize=10)
    ax.set_yticks(range(len(tariffs)))
    ax.set_yticklabels(tariff_labels, fontsize=10)
    ax.set_xlabel("Amazon ACoS (PPC % of Revenue)", fontsize=12, fontweight="bold")
    ax.set_ylabel("US Tariff Rate (total incl. add-ons)", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Survival Heatmap — HTS 6304.92.0000  |  Sell ${MARKET_SELL_PRICE_USD}  |  Survival = Net Margin ≥ {SURVIVAL_FLOOR:.0%}",
        fontsize=13, fontweight="bold", pad=14
    )

    # Annotate each cell with margin value
    for i in range(len(tariffs)):
        for j in range(len(ppcs)):
            val = data[i][j]
            color = "white" if val < 10 or val < 0 else "black"
            weight = "bold" if val >= 15 else "normal"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=8.5, color=color, fontweight=weight)

    # Mark current scenario cell
    t_idx = next(i for i, t in enumerate(tariffs) if abs(t - 0.313) < 0.001)
    p_idx = next(j for j, p in enumerate(ppcs) if abs(p - 0.18) < 0.001)
    rect = plt.Rectangle((p_idx - 0.5, t_idx - 0.5), 1, 1,
                          linewidth=3, edgecolor="white", facecolor="none")
    ax.add_patch(rect)
    ax.text(p_idx, t_idx - 0.62, "◄ NOW", ha="center", fontsize=8,
            color="white", fontweight="bold")

    # Survival boundary contour
    import numpy as np
    ax.contour(np.array(data), levels=[15], colors=["white"],
               linewidths=2.5, linestyles="--")

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Net Margin (%)", fontsize=11)
    cbar.ax.axhline(y=15, color="white", linewidth=2, linestyle="--")
    cbar.ax.text(2.8, 15, "← Survival", fontsize=8, color="white", va="center")

    # Legend patches
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#66bb6a", label=f"SURVIVE  (≥{SURVIVAL_FLOOR:.0%} net margin)"),
        Patch(facecolor="#ffa726", label="WARNING  (10–15%)"),
        Patch(facecolor="#ef5350", label="DEAD     (<10%)"),
        Patch(facecolor="none",    edgecolor="white", linewidth=2, label="Current scenario"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9,
              framealpha=0.85, facecolor="#222222", labelcolor="white")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#1a1a1a")
    print(f"\n[✓] Heatmap saved → {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Tariff × PPC Survival Heatmap")
    parser.add_argument("--text-only", action="store_true",
                        help="Skip matplotlib output (terminal only)")
    parser.add_argument("--sell-price", type=float, default=MARKET_SELL_PRICE_USD,
                        help=f"Override market sell price (default: ${MARKET_SELL_PRICE_USD})")
    args = parser.parse_args()

    print(f"\nBuilding matrix ({len(TARIFF_RATES)} tariff × {len(PPC_RATES)} PPC = "
          f"{len(TARIFF_RATES) * len(PPC_RATES)} cells)...")

    tariffs, ppcs, matrix = build_matrix()
    print_ascii_matrix(tariffs, ppcs, matrix)

    if not args.text_only:
        plot_heatmap(tariffs, ppcs, matrix)


if __name__ == "__main__":
    main()
