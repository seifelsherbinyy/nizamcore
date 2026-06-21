"""Unit tests for AdaptationState dataclass and file I/O functions."""
import json
import pytest
from pathlib import Path

from HIKMAH__knowledge_index.adaptation.adaptation_state import (
    AdaptationState,
    load_state,
    save_state,
    to_dict,
    FORMATS,
)


class TestAdaptationStateDefaults:
    """Test AdaptationState dataclass default values."""

    def test_default_current_format(self):
        state = AdaptationState(persona="AMMAR")
        assert state.current_format == "standard"

    def test_default_previous_format(self):
        state = AdaptationState(persona="AMMAR")
        assert state.previous_format is None

    def test_default_rotation_index(self):
        state = AdaptationState(persona="AMMAR")
        assert state.rotation_index == 0

    def test_default_last_rotation_at(self):
        state = AdaptationState(persona="AMMAR")
        assert state.last_rotation_at is None

    def test_default_adaptation_id(self):
        state = AdaptationState(persona="AMMAR")
        assert state.adaptation_id is None

    def test_persona_set(self):
        state = AdaptationState(persona="HIKMAH")
        assert state.persona == "HIKMAH"


class TestFormatsConstant:
    """Test FORMATS constant."""

    def test_formats_order(self):
        assert FORMATS == ["standard", "short", "emoji", "direct_question", "story"]

    def test_formats_length(self):
        assert len(FORMATS) == 5


class TestLoadStateMissingFile:
    """Test load_state when file doesn't exist."""

    def test_load_state_missing_file_returns_default(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        state = load_state("AMMAR", state_path)
        assert state.persona == "AMMAR"
        assert state.current_format == "standard"
        assert state.previous_format is None
        assert state.rotation_index == 0

    def test_load_state_any_persona_missing_file(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        state = load_state("TARIQ", state_path)
        assert state.persona == "TARIQ"
        assert state.current_format == "standard"

    def test_load_state_no_matching_persona_returns_default(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        # Write state for a different persona
        existing = AdaptationState(persona="HIKMAH", current_format="short")
        save_state(existing, state_path)
        # Load for AMMAR — should get defaults
        state = load_state("AMMAR", state_path)
        assert state.persona == "AMMAR"
        assert state.current_format == "standard"


class TestSaveAndLoadRoundTrip:
    """Test save_state + load_state round trips."""

    def test_round_trip_basic(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        original = AdaptationState(
            persona="AMMAR",
            current_format="short",
            previous_format="standard",
            rotation_index=1,
            last_rotation_at="2026-06-21T09:30:00Z",
            adaptation_id="ADAPT-AMMAR-20260621-001",
        )
        save_state(original, state_path)
        loaded = load_state("AMMAR", state_path)
        assert loaded.persona == "AMMAR"
        assert loaded.current_format == "short"
        assert loaded.previous_format == "standard"
        assert loaded.rotation_index == 1
        assert loaded.last_rotation_at == "2026-06-21T09:30:00Z"
        assert loaded.adaptation_id == "ADAPT-AMMAR-20260621-001"

    def test_round_trip_all_formats(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        for fmt in FORMATS:
            state = AdaptationState(persona="AMMAR", current_format=fmt)
            save_state(state, state_path)
            loaded = load_state("AMMAR", state_path)
            assert loaded.current_format == fmt

    def test_save_creates_file(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        assert not state_path.exists()
        save_state(AdaptationState(persona="AMMAR"), state_path)
        assert state_path.exists()

    def test_save_creates_parent_dirs(self, tmp_path):
        state_path = tmp_path / "subdir" / "deep" / "ADAPTATION_STATE.jsonl"
        save_state(AdaptationState(persona="AMMAR"), state_path)
        assert state_path.exists()


class TestMultipleSavesLastWins:
    """Test that multiple saves for same persona — last saved wins on load."""

    def test_multiple_saves_last_wins(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        save_state(AdaptationState(persona="AMMAR", current_format="standard"), state_path)
        save_state(AdaptationState(persona="AMMAR", current_format="short"), state_path)
        save_state(AdaptationState(persona="AMMAR", current_format="emoji"), state_path)
        loaded = load_state("AMMAR", state_path)
        assert loaded.current_format == "emoji"

    def test_append_not_overwrite(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        save_state(AdaptationState(persona="AMMAR", current_format="standard"), state_path)
        save_state(AdaptationState(persona="AMMAR", current_format="short"), state_path)
        # File should have 2 lines (append-only)
        lines = state_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_multiple_personas_independent(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        save_state(AdaptationState(persona="AMMAR", current_format="short"), state_path)
        save_state(AdaptationState(persona="HIKMAH", current_format="emoji"), state_path)
        ammar = load_state("AMMAR", state_path)
        hikmah = load_state("HIKMAH", state_path)
        assert ammar.current_format == "short"
        assert hikmah.current_format == "emoji"


class TestToDict:
    """Test to_dict serialization."""

    def test_to_dict_has_ts(self, tmp_path):
        state = AdaptationState(persona="AMMAR")
        d = to_dict(state)
        assert "ts" in d
        assert d["ts"].endswith("Z")

    def test_to_dict_has_all_fields(self, tmp_path):
        state = AdaptationState(
            persona="AMMAR",
            current_format="short",
            previous_format="standard",
            rotation_index=1,
        )
        d = to_dict(state)
        assert d["persona"] == "AMMAR"
        assert d["current_format"] == "short"
        assert d["previous_format"] == "standard"
        assert d["rotation_index"] == 1

    def test_jsonl_line_is_valid_json(self, tmp_path):
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        save_state(AdaptationState(persona="AMMAR"), state_path)
        line = state_path.read_text().strip()
        parsed = json.loads(line)
        assert parsed["persona"] == "AMMAR"
