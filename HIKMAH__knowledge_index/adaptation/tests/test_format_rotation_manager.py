"""Unit tests for FormatRotationManager state machine."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from HIKMAH__knowledge_index.adaptation.adaptation_state import FORMATS, AdaptationState, save_state
from HIKMAH__knowledge_index.adaptation.format_rotation_manager import FormatRotationManager


# ---- helpers ----------------------------------------------------------------

def make_manager(tmp_state_path, tmp_ledger_path) -> FormatRotationManager:
    return FormatRotationManager(tmp_state_path, tmp_ledger_path)


def do_rotate(mgr, persona="AMMAR", reason="test", rate=0.65, n=13, d=20):
    return mgr.rotate_format(persona, reason, rate, n, d)


# ---- tests ------------------------------------------------------------------

class TestGetCurrentFormat:
    """Test get_current_format."""

    def test_new_persona_returns_standard(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        assert mgr.get_current_format("AMMAR") == "standard"

    def test_after_rotate_returns_new_format(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        new_fmt = do_rotate(mgr)
        assert mgr.get_current_format("AMMAR") == new_fmt

    def test_different_personas_independent(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        do_rotate(mgr, persona="AMMAR")
        assert mgr.get_current_format("HIKMAH") == "standard"


class TestRotateAdvancesFormat:
    """Test that rotate_format advances the format cycle."""

    def test_standard_to_short(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        result = do_rotate(mgr)
        assert result == "short"

    def test_short_to_emoji(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        do_rotate(mgr)  # standard → short
        # Force reset last_rotation_at to allow second rotation
        state = _load_state_from_path(tmp_state_path, "AMMAR")
        state.last_rotation_at = None
        from HIKMAH__knowledge_index.adaptation.adaptation_state import save_state
        save_state(state, tmp_state_path)
        result = do_rotate(mgr)
        assert result == "emoji"

    def test_wraps_around_story_to_standard(self, tmp_state_path, tmp_ledger_path):
        """After 'story', next should be 'standard' (wraps around)."""
        from HIKMAH__knowledge_index.adaptation.adaptation_state import save_state, AdaptationState
        # Set state to "story" (index 4)
        state = AdaptationState(
            persona="AMMAR",
            current_format="story",
            previous_format="direct_question",
            rotation_index=4,
        )
        save_state(state, tmp_state_path)
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        result = do_rotate(mgr)
        assert result == "standard"

    def test_full_cycle_5_rotations(self, tmp_state_path, tmp_ledger_path):
        """5 rotations should complete the full cycle."""
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        formats_seen = []
        for _ in range(5):
            fmt = _force_rotate(mgr, tmp_state_path)
            formats_seen.append(fmt)
        # Should have seen all 5 formats (in order, possibly some skipped due to no-repeat)
        assert len(set(formats_seen)) >= 4  # At least 4 unique formats in 5 rotations


class TestNoConsecutiveRepeat:
    """Test that rotate_format never returns the same format twice consecutively."""

    def test_no_consecutive_repeat_in_10_rotations(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        results = []
        for _ in range(10):
            fmt = _force_rotate(mgr, tmp_state_path)
            results.append(fmt)
        for i in range(len(results) - 1):
            assert results[i] != results[i + 1], (
                f"Consecutive repeat at index {i}: {results[i]!r} → {results[i+1]!r}"
            )

    def test_skip_when_previous_equals_next(self, tmp_state_path, tmp_ledger_path):
        """If advancing would land on previous_format, skip to the next one."""
        from HIKMAH__knowledge_index.adaptation.adaptation_state import save_state, AdaptationState
        # Set state: current="standard" (idx 0), previous="short" (idx 1)
        # Next would be "short" (idx 1), but that == previous → should skip to "emoji" (idx 2)
        state = AdaptationState(
            persona="AMMAR",
            current_format="standard",
            previous_format="short",
            rotation_index=0,
        )
        save_state(state, tmp_state_path)
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        result = do_rotate(mgr)
        assert result == "emoji"


class TestStatePersistence:
    """Test that state is persisted to disk, not just in memory."""

    def test_new_instance_reads_correct_state(self, tmp_state_path, tmp_ledger_path):
        """A new FormatRotationManager instance should read the persisted state."""
        mgr1 = make_manager(tmp_state_path, tmp_ledger_path)
        do_rotate(mgr1)  # Rotates to "short"
        # Create a completely new instance
        mgr2 = make_manager(tmp_state_path, tmp_ledger_path)
        assert mgr2.get_current_format("AMMAR") == "short"

    def test_rotation_index_persisted(self, tmp_state_path, tmp_ledger_path):
        from HIKMAH__knowledge_index.adaptation.adaptation_state import load_state
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        do_rotate(mgr)
        state = load_state("AMMAR", tmp_state_path)
        assert state.rotation_index == 1  # Moved from index 0 to 1


class TestAuditLogging:
    """Test that rotate_format logs to ADAPTATION_LEDGER.jsonl."""

    def test_rotate_writes_to_ledger(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        do_rotate(mgr)
        assert tmp_ledger_path.exists()

    def test_rotate_logs_before_state_update(self, tmp_state_path, tmp_ledger_path):
        """ADAPTATION_LEDGER entry should have old_format as the state before rotation."""
        import json
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        do_rotate(mgr)
        entry = json.loads(tmp_ledger_path.read_text().strip().splitlines()[0])
        assert entry["old_format"] == "standard"
        assert entry["new_format"] == "short"

    def test_10_rotations_write_10_ledger_entries(self, tmp_state_path, tmp_ledger_path):
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        for _ in range(10):
            _force_rotate(mgr, tmp_state_path)
        lines = tmp_ledger_path.read_text().strip().splitlines()
        assert len(lines) == 10


class TestRateLimit:
    """Test the 1-rotation-per-week guard."""

    def test_recent_rotation_returns_current_unchanged(self, tmp_state_path, tmp_ledger_path):
        """If last_rotation_at is within 7 days, rotate_format returns current format."""
        from HIKMAH__knowledge_index.adaptation.adaptation_state import save_state, AdaptationState
        recent = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = AdaptationState(
            persona="AMMAR",
            current_format="short",
            previous_format="standard",
            rotation_index=1,
            last_rotation_at=recent,
        )
        save_state(state, tmp_state_path)
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        result = do_rotate(mgr)
        assert result == "short"  # Unchanged

    def test_old_rotation_allows_new_rotation(self, tmp_state_path, tmp_ledger_path):
        """If last_rotation_at is >7 days ago, rotation should proceed."""
        from HIKMAH__knowledge_index.adaptation.adaptation_state import save_state, AdaptationState
        old = (datetime.now(timezone.utc) - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = AdaptationState(
            persona="AMMAR",
            current_format="short",
            previous_format="standard",
            rotation_index=1,
            last_rotation_at=old,
        )
        save_state(state, tmp_state_path)
        mgr = make_manager(tmp_state_path, tmp_ledger_path)
        result = do_rotate(mgr)
        assert result != "short"  # Should have advanced


# ---- private helpers --------------------------------------------------------

def _force_rotate(mgr: FormatRotationManager, tmp_state_path, persona="AMMAR"):
    """Rotate format by clearing last_rotation_at to bypass the weekly guard."""
    from HIKMAH__knowledge_index.adaptation.adaptation_state import load_state, save_state
    state = load_state(persona, tmp_state_path)
    state.last_rotation_at = None
    save_state(state, tmp_state_path)
    return mgr.rotate_format(persona, "force", 0.60, 12, 20)


def _load_state_from_path(state_path, persona):
    from HIKMAH__knowledge_index.adaptation.adaptation_state import load_state
    return load_state(persona, state_path)
