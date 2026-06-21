"""Integration tests for end-to-end Phase 18 adaptation flow.

Tests the full feedback loop:
  DELIVERY_LEDGER → WeeklyResponseRateCalculator → FormatRotationManager → format_hint → generate_message()

Test inventory (8 tests):
1. test_rate_calc_counts_responses: 20 deliveries + 13 responses → rate=0.65
2. test_rate_calc_within_7_days: old deliveries excluded from denominator
3. test_no_format_hint_when_rate_sufficient: rate >= 80% → format_hint=None
4. test_format_hint_injected_when_rate_low: rate=0.65 → format_hint is not None
5. test_ten_consecutive_no_repeats: 10 rotations → zero adjacent identical formats (ADAPT-04)
6. test_adaptation_ledger_written_before_format_applied: ADAPTATION_LEDGER written after rotate_format()
7. test_rationale_string_format: rationale matches expected pattern
8. test_no_repeat_validated_against_state: 2nd rotation avoids previous format
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from HIKMAH__knowledge_index.adaptation import (
    WeeklyResponseRateCalculator,
    FormatRotationManager,
    AdaptationLogger,
    AdaptationState,
)
from HIKMAH__knowledge_index.adaptation.adaptation_state import (
    FORMATS,
    load_state,
    save_state,
)
from HIKMAH__knowledge_index.message_generation.generator import generate_and_dedupe
from HIKMAH__knowledge_index.message_generation.message_ledger import MessageLedger
from HIKMAH__knowledge_index.message_generation.repetition_tracker import (
    RepetitionTracker,
)

# Re-export make_mock_ledger from conftest for direct use
from HIKMAH__knowledge_index.adaptation.tests.conftest import make_mock_ledger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_index(persona: str) -> Dict[str, Any]:
    """Minimal valid persona index for integration testing."""
    return {
        "persona": persona,
        "version": "1.0",
        "created_at": "2026-01-01T00:00:00Z",
        "last_updated": "2026-01-01T00:00:00Z",
        "topics": [
            {
                "id": "t-001",
                "name": "Work Item",
                "status": "active",
                "created_at": "2026-01-01T00:00:00Z",
                "last_activity": "2026-01-01T00:00:00Z",
                "context_tags": ["technical"],
                "confidence": 0.9,
                "key_accomplishments": [],
                "blockers": [],
                "notes": "Test note",
            }
        ],
        "completions": [],
        "activity_history": [],
        "stalled_work": [],
        "context_snapshot": {
            "tags_used": ["technical"],
            "topics_count": 1,
            "activity_count": 0,
        },
    }


def _set_last_rotation_n_days_ago(persona: str, state_path: Path, days: int) -> None:
    """Backdating helper — sets last_rotation_at to N days ago to bypass rate-limit guard."""
    state = load_state(persona, state_path)
    n_days_ago = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    state.last_rotation_at = n_days_ago
    save_state(state, state_path)


# ---------------------------------------------------------------------------
# Test 1: rate_calc_counts_responses
# ---------------------------------------------------------------------------


class TestRateCalculation:
    """Integration: WeeklyResponseRateCalculator reads DELIVERY_LEDGER correctly."""

    def test_rate_calc_counts_responses(self, tmp_path):
        """20 deliveries + 13 responses within 7 days → rate=0.65, num=13, den=20."""
        ledger_path = make_mock_ledger(
            n_deliveries=20,
            n_responses=13,
            persona="TARIQ",
            tmp_path=tmp_path,
        )
        calc = WeeklyResponseRateCalculator(ledger_path)
        rate, numerator, denominator = calc.calculate("TARIQ", days=7)

        assert denominator == 20
        assert numerator == 13
        assert abs(rate - 0.65) < 0.01

    def test_rate_calc_within_7_days(self, tmp_path):
        """Deliveries older than 7 days are excluded from denominator."""
        now = datetime.now(timezone.utc)
        lines = []

        # 5 recent deliveries (within 7 days)
        for i in range(5):
            sent_at = now - timedelta(days=i)
            lines.append(json.dumps({
                "ts": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "delivery",
                "message_id": f"MSG-RECENT-{i:04d}",
                "persona": "TARIQ",
                "sent_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "delivered_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "success",
                "context_tags": [],
            }))

        # 10 old deliveries (8-17 days ago — outside 7-day window)
        for i in range(10):
            sent_at = now - timedelta(days=8 + i)
            lines.append(json.dumps({
                "ts": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "delivery",
                "message_id": f"MSG-OLD-{i:04d}",
                "persona": "TARIQ",
                "sent_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "delivered_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "success",
                "context_tags": [],
            }))

        # 3 responses for recent messages
        for i in range(3):
            lines.append(json.dumps({
                "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "response",
                "message_id": f"MSG-RECENT-{i:04d}",
                "persona": "TARIQ",
            }))

        ledger_path = tmp_path / "DELIVERY_LEDGER.jsonl"
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        calc = WeeklyResponseRateCalculator(ledger_path)
        rate, numerator, denominator = calc.calculate("TARIQ", days=7)

        # Only 5 recent deliveries counted
        assert denominator == 5
        assert numerator == 3
        assert abs(rate - 0.60) < 0.01


# ---------------------------------------------------------------------------
# Test 3 & 4: format_hint integration via generate_and_dedupe
# ---------------------------------------------------------------------------


class TestAdaptationHookIntegration:
    """Integration: generate_and_dedupe adaptation hook triggers format_hint correctly."""

    def test_no_format_hint_when_rate_sufficient(self, tmp_path):
        """With rate >= 80% → format_hint=None passed to generate_message (no adaptation)."""
        # 20 deliveries, 18 responses → rate = 0.90
        ledger_path = make_mock_ledger(
            n_deliveries=20,
            n_responses=18,
            persona="TARIQ",
            tmp_path=tmp_path,
        )
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        adapt_ledger_path = tmp_path / "ADAPTATION_LEDGER.jsonl"

        captured_hints = []

        def fake_generate_message(persona, intent, index, client, max_tokens=100, format_hint=None):
            captured_hints.append(format_hint)
            return "Strategic action required. Focus now."

        index = _make_index("TARIQ")
        tracker = RepetitionTracker(tmp_path / "MSG_LEDGER.jsonl")
        msg_ledger = MessageLedger(tmp_path / "MSG_LEDGER.jsonl")
        mock_client = _make_mock_client()

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
                delivery_ledger_path=ledger_path,
                adaptation_state_path=state_path,
                adaptation_ledger_path=adapt_ledger_path,
            )

        assert len(captured_hints) > 0
        # Rate was 0.90 >= 0.80 → no adaptation, format_hint stays None
        assert captured_hints[0] is None
        # ADAPTATION_LEDGER should NOT be written (no rotation triggered)
        assert not adapt_ledger_path.exists()

    def test_format_hint_injected_when_rate_low(self, tmp_path):
        """With rate=0.65 < 80% → format_hint is not None (adaptation triggered)."""
        # 20 deliveries, 13 responses → rate = 0.65
        ledger_path = make_mock_ledger(
            n_deliveries=20,
            n_responses=13,
            persona="TARIQ",
            tmp_path=tmp_path,
        )
        state_path = tmp_path / "ADAPTATION_STATE.jsonl"
        adapt_ledger_path = tmp_path / "ADAPTATION_LEDGER.jsonl"

        captured_hints = []

        def fake_generate_message(persona, intent, index, client, max_tokens=100, format_hint=None):
            captured_hints.append(format_hint)
            return "Strategic action required. Focus now."

        index = _make_index("TARIQ")
        tracker = RepetitionTracker(tmp_path / "MSG_LEDGER.jsonl")
        msg_ledger = MessageLedger(tmp_path / "MSG_LEDGER.jsonl")
        mock_client = _make_mock_client()

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
                delivery_ledger_path=ledger_path,
                adaptation_state_path=state_path,
                adaptation_ledger_path=adapt_ledger_path,
            )

        assert len(captured_hints) > 0
        # Rate was 0.65 < 0.80 → adaptation triggered, format_hint is not None
        assert captured_hints[0] is not None
        assert captured_hints[0] in FORMATS


# ---------------------------------------------------------------------------
# Test 5: ten consecutive no repeats (ADAPT-04)
# ---------------------------------------------------------------------------


class TestTenConsecutiveNoRepeats:
    """ADAPT-04: No two adjacent formats in a 10-rotation sequence are identical."""

    def test_ten_consecutive_no_repeats(self, tmp_state_path, tmp_ledger_path):
        """Simulate 10 consecutive rotate_format() calls; verify no adjacent repeats."""
        manager = FormatRotationManager(tmp_state_path, tmp_ledger_path)
        formats_returned = []

        for i in range(10):
            fmt = manager.rotate_format(
                persona="TARIQ",
                reason="test low engagement",
                response_rate=0.40,
                numerator=4,
                denominator=10,
            )
            formats_returned.append(fmt)
            # Bypass 1-rotation-per-week guard: set last_rotation_at to 8 days ago
            _set_last_rotation_n_days_ago("TARIQ", tmp_state_path, days=8)

        assert len(formats_returned) == 10, "Expected 10 rotation results"

        # Assert no consecutive repeats
        for i in range(len(formats_returned) - 1):
            assert formats_returned[i] != formats_returned[i + 1], (
                f"Consecutive repeat at index {i}: "
                f"'{formats_returned[i]}' == '{formats_returned[i + 1]}'"
            )


# ---------------------------------------------------------------------------
# Test 6: ADAPTATION_LEDGER written before format applied
# ---------------------------------------------------------------------------


class TestAdaptationLedgerWrittenBeforeFormatApplied:
    """ADAPTATION_LEDGER.jsonl entry exists immediately after rotate_format()."""

    def test_adaptation_ledger_written_before_format_applied(
        self, tmp_state_path, tmp_ledger_path
    ):
        """Calling rotate_format() writes ledger entry with correct fields."""
        manager = FormatRotationManager(tmp_state_path, tmp_ledger_path)
        manager.rotate_format(
            persona="TARIQ",
            reason="engagement_threshold_breach",
            response_rate=0.65,
            numerator=13,
            denominator=20,
        )

        # Ledger must exist immediately after rotate_format()
        assert tmp_ledger_path.exists(), "ADAPTATION_LEDGER.jsonl not created"

        # Read and parse the entry
        lines = [l for l in tmp_ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) >= 1, "Expected at least one ledger entry"

        entry = json.loads(lines[-1])
        assert entry["persona"] == "TARIQ"
        assert entry["old_format"] == "standard"
        assert entry["new_format"] in FORMATS
        assert entry["new_format"] != entry["old_format"]
        assert "adaptation_id" in entry
        assert entry["event_type"] == "format_rotation"


# ---------------------------------------------------------------------------
# Test 7: rationale string format
# ---------------------------------------------------------------------------


class TestRationaleStringFormat:
    """The rationale field in ADAPTATION_LEDGER matches the expected pattern."""

    def test_rationale_string_format(self, tmp_state_path, tmp_ledger_path):
        """Rotate from 'standard' at rate=0.65; verify rationale string format."""
        manager = FormatRotationManager(tmp_state_path, tmp_ledger_path)
        new_fmt = manager.rotate_format(
            persona="TARIQ",
            reason="engagement_threshold_breach",
            response_rate=0.65,
            numerator=13,
            denominator=20,
        )

        lines = [l for l in tmp_ledger_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        entry = json.loads(lines[-1])

        expected_rationale = (
            f"TARIQ response rate 65% < 80%, "
            f"switching from 'standard' to '{new_fmt}' format"
        )
        assert entry["rationale"] == expected_rationale, (
            f"Rationale mismatch.\nExpected: {expected_rationale!r}\nGot:      {entry['rationale']!r}"
        )


# ---------------------------------------------------------------------------
# Test 8: no-repeat validated against state
# ---------------------------------------------------------------------------


class TestNoRepeatValidatedAgainstState:
    """After rotating from 'standard' to X, next rotation skips 'standard' (previous_format guard)."""

    def test_no_repeat_validated_against_state(self, tmp_state_path, tmp_ledger_path):
        """After standard→short, next rotation should NOT return 'standard' (previous_format guard)."""
        manager = FormatRotationManager(tmp_state_path, tmp_ledger_path)

        # First rotation: standard → short
        first_fmt = manager.rotate_format(
            persona="TARIQ",
            reason="test",
            response_rate=0.50,
            numerator=5,
            denominator=10,
        )
        assert first_fmt == "short", f"Expected 'short', got '{first_fmt}'"

        # Bypass weekly rate-limit guard
        _set_last_rotation_n_days_ago("TARIQ", tmp_state_path, days=8)

        # Second rotation: short → emoji (skips over 'standard' via no-repeat guard if needed)
        second_fmt = manager.rotate_format(
            persona="TARIQ",
            reason="test",
            response_rate=0.50,
            numerator=5,
            denominator=10,
        )

        # previous_format is "standard" after 1st rotation, so 2nd rotation must not return "standard"
        assert second_fmt != "standard", (
            f"Second rotation returned 'standard' (previous_format), which violates no-consecutive-repeat guard"
        )
        assert second_fmt in FORMATS


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------


def _make_mock_client():
    """Create a minimal mock Anthropic client for integration testing."""
    from unittest.mock import MagicMock

    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Strategic action required. Focus now.")]
    client.messages.create.return_value = mock_response
    return client
