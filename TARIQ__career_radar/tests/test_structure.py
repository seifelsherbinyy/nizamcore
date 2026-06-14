"""test_structure.py — DATA-04: Module folder structure mirrors MARSAD pattern.

Wave 0 (TDD): test_module_layout MUST fail because radar/ modules don't exist yet.
Acceptable failure mode: AssertionError (paths missing).
"""
from __future__ import annotations
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import pytest


def test_module_layout(repo_root: Path) -> None:
    """DATA-04: Required files and directories exist under TARIQ__career_radar/."""
    base = repo_root / "TARIQ__career_radar"

    required_paths = [
        ("TARIQ__career_radar/radar/__init__.py", base / "radar" / "__init__.py"),
        ("TARIQ__career_radar/radar/config.py", base / "radar" / "config.py"),
        ("TARIQ__career_radar/radar/dedup_engine.py", base / "radar" / "dedup_engine.py"),
        ("TARIQ__career_radar/data/ (directory)", base / "data"),
        ("TARIQ__career_radar/tests/__init__.py", base / "tests" / "__init__.py"),
    ]

    missing = []
    for label, path in required_paths:
        if path.suffix:
            # File check
            if not path.is_file():
                missing.append(label)
        else:
            # Directory check
            if not path.is_dir():
                missing.append(label)

    assert not missing, "Missing required paths:\n  " + "\n  ".join(missing)
