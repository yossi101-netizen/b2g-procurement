"""
KritiKaal Command Center — Lead Machine page
Thin wrapper: loads the Leads Hunter dashboard via importlib so that
Path(__file__) inside dashboard.py still resolves to T-tools/.
"""
import sys
import importlib.util
from pathlib import Path

HERE         = Path(__file__).parent.resolve()           # kritikaal-hub/pages/
HUB          = HERE.parent                               # kritikaal-hub/
WORKSPACE    = HUB.parent                                # yossi-workspace/
LEADS_HUNTER = WORKSPACE / "T-tools"

# ── Add Leads Hunter to sys.path so its relative imports work ─────
for p in [str(LEADS_HUNTER), str(HUB)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Load and execute dashboard.py with __file__ pointing to T-tools ─
_dashboard_path = LEADS_HUNTER / "dashboard.py"
_spec = importlib.util.spec_from_file_location(
    "kk_dashboard",
    str(_dashboard_path),
)
_mod = importlib.util.module_from_spec(_spec)
_mod.__file__ = str(_dashboard_path)         # ensures Path(__file__).parent → T-tools/
_spec.loader.exec_module(_mod)
