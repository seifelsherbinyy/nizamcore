# Contract: NIZAM-CONTRACT-05 regression_protection | Phase: R2_SCHEDULER
"""conftest.py — make the scheduler package importable from either checkout root.

Owning contract: NIZAM-CONTRACT-05 regression_protection v1.0.0
Phase:           R2_SCHEDULER
"""
import pathlib
import sys

# parents[0]=tests, [1]=scheduler, [2]=the directory holding the package.
_PKG_PARENT = pathlib.Path(__file__).resolve().parents[2]
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))
