"""test_registration.py — DATA-04/05: _index.json, KNOWN_LEDGERS, PRIVACY_CLASSIFICATION registration.

Wave 0 (TDD):
- test_index_json_valid: MUST fail (TARIQ__career_radar/_index.json not yet created)
- test_ledger_registered: MUST fail (CAREER_RADAR_LEDGER not yet in KNOWN_LEDGERS)
Acceptable failure modes: FileNotFoundError, AssertionError.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import pytest

# This import is stable — ledger_writer.py exists; KNOWN_LEDGERS just won't contain the new key yet
from NIZAM__system.governor.ledger_writer import KNOWN_LEDGERS


def test_index_json_valid(repo_root: Path) -> None:
    """DATA-04: TARIQ__career_radar/_index.json must exist and contain required keys."""
    index_path = repo_root / "TARIQ__career_radar" / "_index.json"
    if not index_path.exists():
        pytest.fail(f"_index.json not found: {index_path}")

    data = json.loads(index_path.read_text(encoding="utf-8"))
    required_keys = {"module", "privacy_level", "phase"}
    missing = required_keys - set(data.keys())
    assert not missing, f"_index.json missing keys: {sorted(missing)}"


def test_ledger_registered() -> None:
    """DATA-05: CAREER_RADAR_LEDGER must be present in KNOWN_LEDGERS (added in Plan 01-06)."""
    assert "CAREER_RADAR_LEDGER" in KNOWN_LEDGERS, (
        "CAREER_RADAR_LEDGER not found in KNOWN_LEDGERS. "
        "This will be added in Plan 01-06 when the ledger is registered."
    )
