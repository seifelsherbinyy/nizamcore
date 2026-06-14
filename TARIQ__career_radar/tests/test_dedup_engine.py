"""test_dedup_engine.py — DATA-03: SQLite seen-role store round-trip, normalization, persistence.

Wave 0 (TDD): These tests MUST fail because TARIQ__career_radar.radar.dedup_engine
does not yet exist.  Acceptable failure mode: ImportError raised inside tests
(not at module level, so pytest can collect all 12 tests cleanly).
"""
from __future__ import annotations
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import pytest

# Attempt import at module level; capture ImportError for test-time re-raise
try:
    from TARIQ__career_radar.radar.dedup_engine import (
        DedupeEngine as _DedupeEngine,
        compute_dedup_key as _compute_dedup_key,
    )
    _IMPORT_ERROR: ImportError | None = None
except ImportError as exc:
    _DedupeEngine = None  # type: ignore[assignment, misc]
    _compute_dedup_key = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc


def _require_module() -> None:
    """Re-raise ImportError inside a test body so pytest marks it as FAILED."""
    if _IMPORT_ERROR is not None:
        raise ImportError(
            "TARIQ__career_radar.radar.dedup_engine not yet implemented. "
            f"Original error: {_IMPORT_ERROR}"
        )


def test_sqlite_roundtrip(tmp_db_path: Path, sample_opportunity: dict) -> None:
    """DATA-03: First insert returns is_duplicate=False; second call returns is_duplicate=True."""
    _require_module()
    engine = _DedupeEngine(tmp_db_path)  # type: ignore[misc]
    result_1 = engine.check_or_add(sample_opportunity)
    assert result_1["is_duplicate"] is False, "First insert should not be a duplicate"

    result_2 = engine.check_or_add(sample_opportunity)
    assert result_2["is_duplicate"] is True, "Second call with same opportunity should be a duplicate"


def test_normalization_deterministic() -> None:
    """DATA-03: compute_dedup_key produces the same output for identical inputs."""
    _require_module()
    key_1 = _compute_dedup_key("AI Ops Manager", "Acme, Inc.", "Remote")  # type: ignore[misc]
    key_2 = _compute_dedup_key("AI Ops Manager", "Acme, Inc.", "Remote")  # type: ignore[misc]
    assert key_1 == key_2, "Dedup key must be deterministic across calls"
    assert key_1, "Dedup key must be non-empty"


def test_persistence_across_restarts(tmp_db_path: Path, sample_opportunity: dict) -> None:
    """DATA-03: Seen-role store persists across DedupeEngine instantiations (process-restart sim)."""
    _require_module()
    # First instance — insert
    engine_1 = _DedupeEngine(tmp_db_path)  # type: ignore[misc]
    engine_1.check_or_add(sample_opportunity)

    # Second instance — same DB path, should detect duplicate
    engine_2 = _DedupeEngine(tmp_db_path)  # type: ignore[misc]
    result = engine_2.check_or_add(sample_opportunity)
    assert result["is_duplicate"] is True, "Seen-role store must persist across engine restarts"
