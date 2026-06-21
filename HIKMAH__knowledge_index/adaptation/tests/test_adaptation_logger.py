"""Unit tests for AdaptationLogger JSONL writer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from HIKMAH__knowledge_index.adaptation.adaptation_logger import AdaptationLogger


class TestLogRotationWritesEntry:
    """Test that log_rotation writes a valid JSONL entry."""

    def test_log_rotation_creates_file(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation(
            persona="AMMAR",
            old_format="standard",
            new_format="short",
            response_rate=0.65,
            numerator=13,
            denominator=20,
            reason="engagement_threshold_breach",
        )
        assert tmp_ledger_path.exists()

    def test_log_rotation_writes_valid_json(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        line = tmp_ledger_path.read_text().strip()
        parsed = json.loads(line)
        assert isinstance(parsed, dict)

    def test_log_rotation_includes_required_fields(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "engagement_threshold_breach")
        parsed = json.loads(tmp_ledger_path.read_text().strip())
        required_fields = [
            "ts", "adaptation_id", "persona", "event_type", "old_format",
            "new_format", "trigger", "response_rate", "response_rate_threshold",
            "calculation_window_days", "denominator", "numerator",
            "rationale", "ledger_hash",
        ]
        for field in required_fields:
            assert field in parsed, f"Missing field: {field}"

    def test_log_rotation_field_values(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test_reason")
        parsed = json.loads(tmp_ledger_path.read_text().strip())
        assert parsed["persona"] == "AMMAR"
        assert parsed["old_format"] == "standard"
        assert parsed["new_format"] == "short"
        assert abs(parsed["response_rate"] - 0.65) < 1e-9
        assert parsed["numerator"] == 13
        assert parsed["denominator"] == 20
        assert parsed["trigger"] == "test_reason"
        assert parsed["event_type"] == "format_rotation"
        assert parsed["response_rate_threshold"] == 0.80
        assert parsed["calculation_window_days"] == 7


class TestAdaptationId:
    """Test adaptation_id generation and incrementing."""

    def test_adaptation_id_format(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        aid = logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        # Format: ADAPT-AMMAR-YYYYMMDD-NNN
        parts = aid.split("-")
        assert parts[0] == "ADAPT"
        assert parts[1] == "AMMAR"
        assert len(parts[2]) == 8  # YYYYMMDD
        assert parts[3].isdigit() and len(parts[3]) == 3  # zero-padded

    def test_adaptation_id_starts_at_001(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        aid = logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        assert aid.endswith("-001")

    def test_adaptation_id_increments_per_persona_per_day(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        aid1 = logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        aid2 = logger.log_rotation("AMMAR", "short", "emoji", 0.60, 12, 20, "test")
        assert aid1.endswith("-001")
        assert aid2.endswith("-002")

    def test_adaptation_id_independent_per_persona(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        aid_ammar = logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        aid_hikmah = logger.log_rotation("HIKMAH", "standard", "short", 0.70, 14, 20, "test")
        assert aid_ammar.endswith("-001")
        assert aid_hikmah.endswith("-001")


class TestRationale:
    """Test rationale auto-generation."""

    def test_rationale_format(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        parsed = json.loads(tmp_ledger_path.read_text().strip())
        expected = "AMMAR response rate 65% < 80%, switching from 'standard' to 'short' format"
        assert parsed["rationale"] == expected

    def test_rationale_with_different_rate(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("HIKMAH", "short", "emoji", 0.70, 14, 20, "test")
        parsed = json.loads(tmp_ledger_path.read_text().strip())
        expected = "HIKMAH response rate 70% < 80%, switching from 'short' to 'emoji' format"
        assert parsed["rationale"] == expected


class TestLedgerHash:
    """Test ledger_hash field."""

    def test_ledger_hash_is_16_chars(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        parsed = json.loads(tmp_ledger_path.read_text().strip())
        assert len(parsed["ledger_hash"]) == 16

    def test_ledger_hash_is_hex(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        parsed = json.loads(tmp_ledger_path.read_text().strip())
        int(parsed["ledger_hash"], 16)  # Should not raise ValueError


class TestAppendBehavior:
    """Test append-only behavior."""

    def test_two_calls_two_lines(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        logger.log_rotation("AMMAR", "short", "emoji", 0.60, 12, 20, "test")
        lines = tmp_ledger_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_append_not_overwrite(self, tmp_ledger_path):
        logger = AdaptationLogger(tmp_ledger_path)
        logger.log_rotation("AMMAR", "standard", "short", 0.65, 13, 20, "test")
        first_content = tmp_ledger_path.read_text()
        logger.log_rotation("AMMAR", "short", "emoji", 0.60, 12, 20, "test")
        second_content = tmp_ledger_path.read_text()
        assert second_content.startswith(first_content.rstrip("\n"))
