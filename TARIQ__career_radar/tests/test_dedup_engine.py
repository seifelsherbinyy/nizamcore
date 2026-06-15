"""test_dedup_engine.py — DATA-03: SQLite seen-role store round-trip, normalization, persistence.
Phase 4 additions (Plan 04-01): 6 failing RED tests for DEDUP-01/02/03 contracts.

Wave 0 (TDD): These tests MUST fail because TARIQ__career_radar.radar.dedup_engine
does not yet exist.  Acceptable failure mode: ImportError raised inside tests
(not at module level, so pytest can collect all 12 tests cleanly).
"""
from __future__ import annotations
import datetime
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

# Phase 4 — attempt import of new symbols (absent until Wave 1/2 implementation)
try:
    from TARIQ__career_radar.radar.dedup_engine import (
        fuzzy_match_opportunities as _fuzzy_match_opportunities,
        is_fresh_repost as _is_fresh_repost,
        run_dedup_pass as _run_dedup_pass,
    )
    _PHASE4_IMPORT_ERROR: ImportError | None = None
except ImportError as exc:
    _fuzzy_match_opportunities = None  # type: ignore[assignment]
    _is_fresh_repost = None  # type: ignore[assignment]
    _run_dedup_pass = None  # type: ignore[assignment]
    _PHASE4_IMPORT_ERROR = exc


def _require_module() -> None:
    """Re-raise ImportError inside a test body so pytest marks it as FAILED."""
    if _IMPORT_ERROR is not None:
        raise ImportError(
            "TARIQ__career_radar.radar.dedup_engine not yet implemented. "
            f"Original error: {_IMPORT_ERROR}"
        )


def _require_phase4() -> None:
    """Re-raise ImportError for Phase-4 symbols — MISSING until Wave 1 implementation."""
    if _PHASE4_IMPORT_ERROR is not None:
        raise ImportError(
            "MISSING — implement in Wave 1: fuzzy_match_opportunities, is_fresh_repost, "
            "run_dedup_pass not yet present in TARIQ__career_radar.radar.dedup_engine. "
            f"Original error: {_PHASE4_IMPORT_ERROR}"
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


# ---------------------------------------------------------------------------
# Phase 4 — Wave 0 RED tests (DEDUP-02, DEDUP-03)
# These MUST fail until Wave 1/2 adds fuzzy_match_opportunities, is_fresh_repost,
# and run_dedup_pass to TARIQ__career_radar.radar.dedup_engine.
# ---------------------------------------------------------------------------

def test_fuzzy_match_title_variants() -> None:
    """DEDUP-02: fuzzy_match_opportunities detects title variants as duplicates (score >=0.88).

    "AI Operations Manager" and "AI Ops Manager" are the same role with different wording.
    The function must return (is_match=True, score>=0.88) for this canonical variant pair.
    """
    _require_phase4()
    candidate = {"title": "AI Operations Manager"}
    seen_list = [{"title": "AI Ops Manager"}]
    is_match, score = _fuzzy_match_opportunities(candidate, seen_list)  # type: ignore[misc]
    assert is_match is True, f"Title variants should match: got is_match={is_match}, score={score}"
    assert score >= 0.88, f"Similarity score must be >=0.88 for title variants; got score={score}"


def test_fuzzy_match_no_false_positive() -> None:
    """DEDUP-02: fuzzy_match_opportunities does NOT match clearly different roles.

    "Finance Manager" and "AI Ops Manager" are unrelated roles; must return is_match=False.
    """
    _require_phase4()
    candidate = {"title": "Finance Manager"}
    seen_list = [{"title": "AI Ops Manager"}]
    is_match, score = _fuzzy_match_opportunities(candidate, seen_list)  # type: ignore[misc]
    assert is_match is False, (
        f"Unrelated roles must not match: got is_match={is_match}, score={score}"
    )


def test_fuzzy_match_same_company_exact_location(cross_source_batch: list) -> None:
    """DEDUP-02: fuzzy_match_opportunities detects cross-source duplicates.

    cross_source_batch[0] = "AI Ops Manager" at "Acme Corp" from "greenhouse"
    cross_source_batch[2] = "AI Ops Manager" at "Acme Corp" from "remotive"
    Same role posted on two sources — must be detected as duplicate.
    """
    _require_phase4()
    candidate = cross_source_batch[2]  # remotive copy
    seen_list = [cross_source_batch[0]]  # greenhouse copy
    is_match, score = _fuzzy_match_opportunities(candidate, seen_list)  # type: ignore[misc]
    assert is_match is True, (
        f"Cross-source duplicate must match: got is_match={is_match}, score={score}"
    )


def test_is_fresh_repost_old_role_surfaces(dedup_fresh_record: dict) -> None:
    """DEDUP-03: is_fresh_repost returns True when first_seen is >=30 days ago.

    dedup_fresh_record has first_seen 45 days ago — qualifies as a fresh repost
    (re-surface it as a new opportunity for the user to review).
    """
    _require_phase4()
    result = _is_fresh_repost(  # type: ignore[misc]
        dedup_fresh_record["first_seen_date"],
        dedup_fresh_record["last_seen_date"],
    )
    assert result is True, (
        "Role first seen 45 days ago (>=30-day threshold) must be treated as fresh repost"
    )


def test_is_fresh_repost_recent_stays_hidden() -> None:
    """DEDUP-03: is_fresh_repost returns False when first_seen is <30 days ago.

    A role first seen 10 days ago is still a recent duplicate — keep it hidden.
    """
    _require_phase4()
    now = datetime.datetime.utcnow()
    first_seen = (now - datetime.timedelta(days=10)).isoformat() + "Z"
    last_seen = now.isoformat() + "Z"
    result = _is_fresh_repost(first_seen, last_seen)  # type: ignore[misc]
    assert result is False, (
        "Role first seen 10 days ago (<30-day threshold) must stay hidden as duplicate"
    )


def test_run_dedup_pass_removes_within_run_dups(
    tmp_db_path: Path, cross_source_batch: list
) -> None:
    """DEDUP-02 + DEDUP-03: run_dedup_pass deduplicates a batch, returning only unique roles.

    cross_source_batch has 4 opportunities:
      [0] "AI Ops Manager"  @ Acme Corp (greenhouse)  — duplicate pair A
      [1] "Finance Manager" @ Acme Corp (greenhouse)  — distinct
      [2] "AI Ops Manager"  @ Acme Corp (remotive)    — duplicate pair A (cross-source)
      [3] "Data Annotator"  @ Beta Inc  (weworkremotely) — distinct

    After run_dedup_pass, only 2 unique roles should remain ([0] or [2], [1], [3]).
    Actually [0], [1], [3] — the first occurrence of each unique role is kept.
    run_dedup_pass(opportunities, db_path) instantiates DedupeEngine internally.
    """
    _require_phase4()
    result = _run_dedup_pass(cross_source_batch, db_path=tmp_db_path)  # type: ignore[misc]
    assert isinstance(result, list), f"run_dedup_pass must return list; got {type(result)}"
    assert len(result) == 3, (
        f"Expected 3 unique roles (1 cross-source dup removed); got {len(result)}"
    )
    assert all("title" in opp for opp in result), "Each result item must have a 'title' key"
