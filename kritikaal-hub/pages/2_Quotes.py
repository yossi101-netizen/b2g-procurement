"""
KritiKaal Command Center — Quote Engine page
Thin wrapper: loads the Quote Engine app via importlib so that
Path(__file__) inside app.py still resolves to quote-engine/.
"""
import sys
import importlib.util
from pathlib import Path

HERE         = Path(__file__).parent.resolve()
HUB          = HERE.parent
WORKSPACE    = HUB.parent
QUOTE_ENGINE = (
    WORKSPACE
    / "the-system-v8"
    / "the-system-v8"
    / "T-tools"
    / "quote-engine"
)

# ── Add Quote Engine to sys.path so its relative imports work ─────
for p in [str(QUOTE_ENGINE), str(HUB)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Load and execute app.py with __file__ pointing to quote-engine/ ─
_app_path = QUOTE_ENGINE / "app.py"
_spec = importlib.util.spec_from_file_location(
    "kk_quote_app",
    str(_app_path),
)
_mod = importlib.util.module_from_spec(_spec)
_mod.__file__ = str(_app_path)               # ensures HERE in app.py → quote-engine/
_spec.loader.exec_module(_mod)
