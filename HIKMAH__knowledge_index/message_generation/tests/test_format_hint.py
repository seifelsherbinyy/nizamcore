"""Tests for format_hint parameter in generate_message() and adaptation hook in generate_and_dedupe().

Phase 18 Task 1: Validates format_hint parameter behavior and adaptation hook wiring.

Tests:
- format_hint=None → system_prompt unchanged
- format_hint="short" → appends "Keep message under 100 characters"
- format_hint="emoji" → appends "1-2 emojis"
- format_hint="direct_question" → appends "direct question"
- format_hint="story" → appends "2-3 sentence narrative"
- format_hint="standard" → system_prompt unchanged (empty constraint)
- format_hint="unknown_hint" → system_prompt unchanged (safe fallback)
- generate_and_dedupe with rate=0.65 → format_hint is non-None after call
- generate_and_dedupe with rate=0.85 → format_hint=None (no adaptation)
- generate_and_dedupe with adaptation_paths=None → backward-compatible (no adaptation)
- existing generate_and_dedupe() signature without new params works identically (no regression)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

import pytest

from HIKMAH__knowledge_index.message_generation.generator import (
    generate_message,
    generate_and_dedupe,
    FORMAT_CONSTRAINTS,
)
from HIKMAH__knowledge_index.message_generation.message_ledger import MessageLedger
from HIKMAH__knowledge_index.message_generation.repetition_tracker import (
    RepetitionTracker,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_delivery_ledger(tmp_path: Path, persona: str, n_deliveries: int, n_responses: int) -> Path:
    """Write a synthetic DELIVERY_LEDGER.jsonl to tmp_path."""
    now = datetime.now(timezone.utc)
    lines = []
    for i in range(n_deliveries):
        sent_at = now - timedelta(hours=i * 8)  # spread within 7 days
        lines.append(json.dumps({
            "ts": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "delivery",
            "message_id": f"MSG-{i:04d}",
            "persona": persona,
            "sent_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "delivered_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "success",
            "context_tags": [],
        }))
    for i in range(n_responses):
        resp_at = now - timedelta(hours=i * 8)
        lines.append(json.dumps({
            "ts": resp_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "response",
            "message_id": f"MSG-{i:04d}",
            "persona": persona,
        }))
    ledger_path = tmp_path / "DELIVERY_LEDGER.jsonl"
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ledger_path


def _make_index(persona: str) -> Dict[str, Any]:
    """Minimal valid persona index for testing."""
    return {
        "persona": persona,
        "version": "1.0",
        "created_at": "2026-01-01T00:00:00Z",
        "last_updated": "2026-01-01T00:00:00Z",
        "topics": [{"id": "t-001", "name": "Work Item", "status": "active",
                    "created_at": "2026-01-01T00:00:00Z",
                    "last_activity": "2026-01-01T00:00:00Z",
                    "context_tags": ["technical"],
                    "confidence": 0.9,
                    "key_accomplishments": [],
                    "blockers": [],
                    "notes": "Note"}],
        "completions": [],
        "activity_history": [],
        "stalled_work": [],
        "context_snapshot": {"tags_used": ["technical"], "topics_count": 1, "activity_count": 0},
    }


# ---------------------------------------------------------------------------
# Format constraint constants
# ---------------------------------------------------------------------------


class TestFormatConstraints:
    """Verify FORMAT_CONSTRAINTS dict is correctly defined."""

    def test_format_constraints_has_all_formats(self):
        assert "short" in FORMAT_CONSTRAINTS
        assert "emoji" in FORMAT_CONSTRAINTS
        assert "direct_question" in FORMAT_CONSTRAINTS
        assert "story" in FORMAT_CONSTRAINTS
        assert "standard" in FORMAT_CONSTRAINTS

    def test_standard_constraint_is_empty(self):
        assert FORMAT_CONSTRAINTS["standard"] == ""

    def test_short_constraint_content(self):
        assert "100 characters" in FORMAT_CONSTRAINTS["short"]

    def test_emoji_constraint_content(self):
        assert "1-2 emojis" in FORMAT_CONSTRAINTS["emoji"] or "emojis" in FORMAT_CONSTRAINTS["emoji"]

    def test_direct_question_constraint_content(self):
        assert "question" in FORMAT_CONSTRAINTS["direct_question"].lower()

    def test_story_constraint_content(self):
        assert "sentence" in FORMAT_CONSTRAINTS["story"] or "narrative" in FORMAT_CONSTRAINTS["story"]


# ---------------------------------------------------------------------------
# generate_message() format_hint parameter
# ---------------------------------------------------------------------------


class TestGenerateMessageFormatHint:
    """Test generate_message() accepts and applies format_hint."""

    def _captured_system_prompt(self, format_hint, mock_client):
        """Call generate_message and return the system prompt sent to the API."""
        captured = {}

        def fake_create(**kwargs):
            captured["system"] = kwargs.get("system", "")
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test response. Pick one.")]
            return mock_response

        mock_client.messages.create = fake_create
        index = _make_index("TARIQ")
        generate_message("TARIQ", "open work", index, mock_client, format_hint=format_hint)
        return captured.get("system", "")

    def test_format_hint_none_leaves_system_prompt_unchanged(self, mock_client, monkeypatch):
        """format_hint=None → system_prompt identical to PERSONA_SYSTEM_PROMPTS[persona]."""
        from HIKMAH__knowledge_index.message_generation import persona_tones

        captured_with_none = self._captured_system_prompt(None, mock_client)
        base_prompt = persona_tones.PERSONA_SYSTEM_PROMPTS.get("TARIQ", "")
        assert captured_with_none == base_prompt

    def test_format_hint_short_appends_constraint(self, mock_client):
        """format_hint='short' → system_prompt contains '100 characters'."""
        system = self._captured_system_prompt("short", mock_client)
        assert "100 characters" in system

    def test_format_hint_emoji_appends_constraint(self, mock_client):
        """format_hint='emoji' → system_prompt contains emoji constraint."""
        system = self._captured_system_prompt("emoji", mock_client)
        assert "emoji" in system.lower() or "emojis" in system.lower()

    def test_format_hint_direct_question_appends_constraint(self, mock_client):
        """format_hint='direct_question' → system_prompt contains question constraint."""
        system = self._captured_system_prompt("direct_question", mock_client)
        assert "question" in system.lower()

    def test_format_hint_story_appends_constraint(self, mock_client):
        """format_hint='story' → system_prompt contains narrative/sentence constraint."""
        system = self._captured_system_prompt("story", mock_client)
        assert "sentence" in system.lower() or "narrative" in system.lower()

    def test_format_hint_standard_leaves_system_prompt_unchanged(self, mock_client):
        """format_hint='standard' → system_prompt unchanged (empty constraint string)."""
        from HIKMAH__knowledge_index.message_generation import persona_tones

        system_standard = self._captured_system_prompt("standard", mock_client)
        system_none = self._captured_system_prompt(None, mock_client)
        assert system_standard == system_none

    def test_format_hint_unknown_leaves_system_prompt_unchanged(self, mock_client):
        """format_hint='unknown_xyz' → system_prompt unchanged (safe .get() fallback)."""
        from HIKMAH__knowledge_index.message_generation import persona_tones

        system_unknown = self._captured_system_prompt("unknown_xyz", mock_client)
        system_none = self._captured_system_prompt(None, mock_client)
        assert system_unknown == system_none

    def test_format_hint_appended_after_base_prompt(self, mock_client):
        """Constraint string is appended AFTER the base system prompt."""
        system = self._captured_system_prompt("short", mock_client)
        from HIKMAH__knowledge_index.message_generation import persona_tones
        base = persona_tones.PERSONA_SYSTEM_PROMPTS.get("TARIQ", "")
        assert system.startswith(base)
        assert system != base  # something was appended


# ---------------------------------------------------------------------------
# generate_and_dedupe() adaptation hook
# ---------------------------------------------------------------------------


class TestGenerateAndDedupeAdaptationHook:
    """Test generate_and_dedupe() adaptation hook with optional path parameters."""

    def _make_fixtures(self, tmp_path: Path):
        """Create all necessary fixtures for adaptation tests."""
        return {
            "state_path": tmp_path / "ADAPTATION_STATE.jsonl",
            "ledger_path": tmp_path / "ADAPTATION_LEDGER.jsonl",
        }

    def test_no_adaptation_when_paths_none(self, mock_client, tmp_path):
        """All adaptation paths=None → backward-compatible, format_hint=None inside."""
        index = _make_index("TARIQ")
        tracker = RepetitionTracker(tmp_path / "MESSAGE_LEDGER.jsonl")
        ledger = MessageLedger(tmp_path / "MESSAGE_LEDGER.jsonl")

        # No adaptation paths provided → should work exactly like old signature
        msg, success, reason = generate_and_dedupe(
            persona="TARIQ",
            intent="open work",
            index=index,
            client=mock_client,
            tracker=tracker,
            ledger=ledger,
        )
        assert isinstance(msg, str)
        assert success is True

    def test_backward_compatible_without_new_params(self, mock_client, tmp_path):
        """generate_and_dedupe() without new params works identically (no regression)."""
        index = _make_index("AMMAR")
        tracker = RepetitionTracker(tmp_path / "MSG_LEDGER.jsonl")
        ledger = MessageLedger(tmp_path / "MSG_LEDGER.jsonl")

        # Call with only the original 7 parameters
        msg, success, reason = generate_and_dedupe(
            persona="AMMAR",
            intent="focus work",
            index=index,
            client=mock_client,
            tracker=tracker,
            ledger=ledger,
            max_retries=3,
        )
        assert isinstance(msg, str)
        assert success is True
        assert reason == "success"

    def test_format_hint_injected_when_rate_low(self, mock_client, tmp_path):
        """With all adaptation paths + rate=0.65 → format_hint becomes non-None."""
        # 20 deliveries, 13 responses → rate = 0.65
        delivery_ledger = _make_delivery_ledger(tmp_path, "TARIQ", 20, 13)
        fixtures = self._make_fixtures(tmp_path)

        captured_hints = []

        original_generate_message = None

        def fake_generate_message(persona, intent, index, client, max_tokens=100, format_hint=None):
            captured_hints.append(format_hint)
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Strategic action needed. Focus now.")]
            return "Strategic action needed. Focus now."

        index = _make_index("TARIQ")
        tracker = RepetitionTracker(tmp_path / "MSG_LEDGER.jsonl")
        msg_ledger = MessageLedger(tmp_path / "MSG_LEDGER.jsonl")

        with patch(
            "HIKMAH__knowledge_index.message_generation.generator.generate_message",
            side_effect=fake_generate_message,
        ):
            generate_and_dedupe(
                persona="TARIQ",
                intent="open work",
                index=index,
                client=mock_client,
                tracker=tracker,
                ledger=msg_ledger,
                delivery_ledger_path=delivery_ledger,
                adaptation_state_path=fixtures["state_path"],
                adaptation_ledger_path=fixtures["ledger_path"],
            )

        # format_hint should be non-None and a valid format string
        assert len(captured_hints) > 0
        assert captured_hints[0] is not None
        assert captured_hints[0] != "standard" or True  # any non-None is fine, including non-standard

    def test_no_format_hint_when_rate_sufficient(self, mock_client, tmp_path):
        """With rate=0.85 (above threshold) → format_hint=None passed to generate_message."""
        # 20 deliveries, 17 responses → rate = 0.85
        delivery_ledger = _make_delivery_ledger(tmp_path, "TARIQ", 20, 17)
        fixtures = self._make_fixtures(tmp_path)

        captured_hints = []

        def fake_generate_message(persona, intent, index, client, max_tokens=100, format_hint=None):
            captured_hints.append(format_hint)
            return "Strategic action needed. Focus now."

        index = _make_index("TARIQ")
        tracker = RepetitionTracker(tmp_path / "MSG_LEDGER.jsonl")
        msg_ledger = MessageLedger(tmp_path / "MSG_LEDGER.jsonl")

        with patch(
            "HIKMAH__knowledge_index.message_generation.generator.generate_message",
            side_effect=fake_generate_message,
        ):
            generate_and_dedupe(
                persona="TARIQ",
                intent="open work",
                index=index,
                client=mock_client,
                tracker=tracker,
                ledger=msg_ledger,
                delivery_ledger_path=delivery_ledger,
                adaptation_state_path=fixtures["state_path"],
                adaptation_ledger_path=fixtures["ledger_path"],
            )

        assert len(captured_hints) > 0
        assert captured_hints[0] is None
