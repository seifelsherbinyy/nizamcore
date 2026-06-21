"""Unit tests for WeeklyResponseRateCalculator."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from HIKMAH__knowledge_index.adaptation.tests.conftest import make_mock_ledger
from HIKMAH__knowledge_index.adaptation.response_rate_calculator import (
    WeeklyResponseRateCalculator,
)


class TestCalculateBasic:
    """Basic rate calculation tests."""

    def test_calculate_14_deliveries_10_responses(self, tmp_path):
        ledger = make_mock_ledger(14, 10, "AMMAR", tmp_path)
        calc = WeeklyResponseRateCalculator(ledger)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 14
        assert numerator == 10
        assert abs(rate - 10 / 14) < 1e-9

    def test_calculate_20_deliveries_16_responses_at_threshold(self, tmp_path):
        ledger = make_mock_ledger(20, 16, "AMMAR", tmp_path)
        calc = WeeklyResponseRateCalculator(ledger)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 20
        assert numerator == 16
        assert abs(rate - 0.8) < 1e-9

    def test_calculate_20_deliveries_13_responses_below_threshold(self, tmp_path):
        ledger = make_mock_ledger(20, 13, "AMMAR", tmp_path)
        calc = WeeklyResponseRateCalculator(ledger)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 20
        assert numerator == 13
        assert abs(rate - 0.65) < 1e-9

    def test_calculate_all_responded_rate_1(self, tmp_path):
        ledger = make_mock_ledger(10, 10, "AMMAR", tmp_path)
        calc = WeeklyResponseRateCalculator(ledger)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 10
        assert numerator == 10
        assert rate == 1.0

    def test_calculate_no_responses_rate_0(self, tmp_path):
        ledger = make_mock_ledger(10, 0, "AMMAR", tmp_path)
        calc = WeeklyResponseRateCalculator(ledger)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 10
        assert numerator == 0
        assert rate == 0.0


class TestEdgeCases:
    """Edge case tests: zero denominator, missing file."""

    def test_calculate_zero_deliveries_returns_1_0_0(self, tmp_path):
        ledger = make_mock_ledger(0, 0, "AMMAR", tmp_path)
        calc = WeeklyResponseRateCalculator(ledger)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert rate == 1.0
        assert numerator == 0
        assert denominator == 0

    def test_calculate_missing_ledger_returns_1_0_0(self, tmp_path):
        missing = tmp_path / "DELIVERY_LEDGER.jsonl"
        calc = WeeklyResponseRateCalculator(missing)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert rate == 1.0
        assert numerator == 0
        assert denominator == 0

    def test_no_zero_division_error(self, tmp_path):
        """Should never raise ZeroDivisionError even with 0 deliveries."""
        missing = tmp_path / "DELIVERY_LEDGER.jsonl"
        calc = WeeklyResponseRateCalculator(missing)
        # This should not raise
        result = calc.calculate("AMMAR")
        assert result == (1.0, 0, 0)


class TestFilters:
    """Tests that verify correct filtering of events."""

    def test_old_deliveries_excluded(self, tmp_path):
        """Deliveries older than 7 days should be excluded from denominator."""
        now = datetime.now(timezone.utc)
        ledger_path = tmp_path / "DELIVERY_LEDGER.jsonl"
        lines = []
        # 5 deliveries within 7 days
        for i in range(5):
            sent = now - timedelta(days=i)
            lines.append(json.dumps({
                "ts": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "delivery",
                "message_id": f"MSG-{i:04d}",
                "persona": "AMMAR",
                "sent_at": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "success",
            }))
        # 5 deliveries older than 7 days
        for i in range(5, 10):
            sent = now - timedelta(days=8 + i)
            lines.append(json.dumps({
                "ts": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "delivery",
                "message_id": f"MSG-{i:04d}",
                "persona": "AMMAR",
                "sent_at": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "success",
            }))
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        calc = WeeklyResponseRateCalculator(ledger_path)
        rate, numerator, denominator = calc.calculate("AMMAR")
        # Only 5 recent deliveries, no responses
        assert denominator == 5

    def test_failed_deliveries_excluded(self, tmp_path):
        """Deliveries with status='failure' should not count in denominator."""
        now = datetime.now(timezone.utc)
        ledger_path = tmp_path / "DELIVERY_LEDGER.jsonl"
        lines = []
        # 5 successful deliveries
        for i in range(5):
            sent = now - timedelta(hours=i)
            lines.append(json.dumps({
                "ts": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "delivery",
                "message_id": f"MSG-OK-{i:04d}",
                "persona": "AMMAR",
                "sent_at": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "success",
            }))
        # 5 failed deliveries
        for i in range(5):
            sent = now - timedelta(hours=i)
            lines.append(json.dumps({
                "ts": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_type": "delivery",
                "message_id": f"MSG-FAIL-{i:04d}",
                "persona": "AMMAR",
                "sent_at": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "failure",
            }))
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        calc = WeeklyResponseRateCalculator(ledger_path)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 5  # Only successful deliveries

    def test_different_persona_excluded(self, tmp_path):
        """Deliveries for different persona should not affect the calculation."""
        ledger_ammar = make_mock_ledger(10, 5, "AMMAR", tmp_path)
        # Also add HIKMAH deliveries to same file
        now = datetime.now(timezone.utc)
        with ledger_ammar.open("a", encoding="utf-8") as fh:
            for i in range(20):
                sent = now - timedelta(hours=i)
                entry = {
                    "ts": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "event_type": "delivery",
                    "message_id": f"HIKMAH-MSG-{i:04d}",
                    "persona": "HIKMAH",
                    "sent_at": sent.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "status": "success",
                }
                fh.write(json.dumps(entry) + "\n")

        calc = WeeklyResponseRateCalculator(ledger_ammar)
        rate, numerator, denominator = calc.calculate("AMMAR")
        # HIKMAH's 20 deliveries should not affect AMMAR's count
        assert denominator == 10
        assert numerator == 5

    def test_7_day_filter_exact_boundary(self, tmp_path):
        """Delivery exactly at cutoff boundary (days=7)."""
        now = datetime.now(timezone.utc)
        ledger_path = tmp_path / "DELIVERY_LEDGER.jsonl"
        lines = []
        # One delivery exactly 6 days 23 hours ago (within 7 days)
        within = now - timedelta(days=6, hours=23)
        lines.append(json.dumps({
            "ts": within.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "delivery",
            "message_id": "MSG-WITHIN",
            "persona": "AMMAR",
            "sent_at": within.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "success",
        }))
        # One delivery exactly 7 days 1 hour ago (outside 7 days)
        outside = now - timedelta(days=7, hours=1)
        lines.append(json.dumps({
            "ts": outside.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "delivery",
            "message_id": "MSG-OUTSIDE",
            "persona": "AMMAR",
            "sent_at": outside.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "success",
        }))
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        calc = WeeklyResponseRateCalculator(ledger_path)
        rate, numerator, denominator = calc.calculate("AMMAR")
        assert denominator == 1  # Only MSG-WITHIN counts
