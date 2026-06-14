"""test_config.py — DATA-02: Profile seed loads and contains required keys.

Wave 0 (TDD): These tests MUST fail because TARIQ__career_radar.radar.config
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
    from TARIQ__career_radar.radar.config import load_profile_seed as _load_profile_seed
    _IMPORT_ERROR: ImportError | None = None
except ImportError as exc:
    _load_profile_seed = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc


def _require_module() -> None:
    """Re-raise ImportError inside a test body so pytest marks it as FAILED."""
    if _IMPORT_ERROR is not None:
        raise ImportError(
            "TARIQ__career_radar.radar.config not yet implemented. "
            f"Original error: {_IMPORT_ERROR}"
        )


def test_profile_seed_load() -> None:
    """DATA-02: load_profile_seed() returns dict with required top-level keys."""
    _require_module()
    result = _load_profile_seed()  # type: ignore[misc]
    required_keys = {"role_keywords", "target_roles", "constraints"}
    missing = required_keys - set(result.keys())
    assert not missing, f"Profile seed missing keys: {missing}"


def test_profile_seed_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DATA-02: load_profile_seed() raises ValueError when profile file is absent."""
    _require_module()
    import TARIQ__career_radar.radar.config as _cfg
    monkeypatch.setattr(_cfg, "_PROFILE_PATH", tmp_path / "nonexistent_profile.json")
    with pytest.raises(ValueError, match="[Pp]rofile"):
        _load_profile_seed()
