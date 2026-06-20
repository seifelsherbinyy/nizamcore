from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from NIZAM__system.companion.contracts import ContextRefresh, PulsationMessage
from NIZAM__system.companion.proactive import eligible
from NIZAM__system.companion.contracts import ProactiveCandidate
from NIZAM__system.companion.pulsation import (
    collision,
    context_refresh,
    himayah_egress,
    loops,
    message_builder,
    routing,
    state,
)
from NIZAM__system.companion.pulsation.ledger import append_pulsation


class PulsationContractTests(unittest.TestCase):
    def test_context_refresh_to_dict(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=("yawmiyat_journal",),
            sources_found=("yawmiyat_journal",),
            missing_sources=(),
            latest_entry_timestamps={"yawmiyat_journal": "2026-06-14T09:00:00Z"},
            confidence="medium",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        payload = refresh.to_dict()
        self.assertEqual(payload["confidence"], "medium")
        self.assertNotIn("source_snapshots", payload)

    def test_pulsation_message_to_dict_includes_council_fields(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=(),
            sources_found=(),
            missing_sources=("yawmiyat_journal",),
            latest_entry_timestamps={},
            confidence="low",
            privacy_level="public_safe",
            sukoon_capacity="green",
        )
        message = PulsationMessage(
            message_type="companion_checkin",
            agent_name="Salman",
            agent_role="Brainstormer",
            generated_at="2026-06-14T10:00:00Z",
            context_refresh=refresh,
            message="I'm Salman, your Brainstormer.",
            focus_trigger="Pick one priority.",
            council_required=True,
            council_motion_candidate="weekly_review",
            council_summary_hash="abc123",
        )
        payload = message.to_dict()
        self.assertTrue(payload["council_required"])
        self.assertEqual(payload["council_motion_candidate"], "weekly_review")
        self.assertEqual(payload["council_summary_hash"], "abc123")


class ContextRefreshTests(unittest.TestCase):
    def test_refresh_never_includes_journal_body(self) -> None:
        refresh = context_refresh.refresh_context(
            now=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc)
        )
        serialized = json.dumps(refresh.source_snapshots)
        self.assertNotIn("Imported via tools", serialized)
        self.assertNotIn("body", serialized.lower())

    def test_confidence_high_with_multiple_sources(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=context_refresh.ALL_SOURCES,
            sources_found=("yawmiyat_journal", "whoop_badan", "thabat_summary"),
            missing_sources=(),
            latest_entry_timestamps={},
            confidence="high",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        self.assertEqual(refresh.confidence, "high")

    def test_missing_sources_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            journal = repo / "YAWMIYAT__journaling" / "entries"
            journal.mkdir(parents=True)
            with mock.patch.object(context_refresh, "REPO", repo):
                refresh = context_refresh.refresh_context(
                    now=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc)
                )
        self.assertIn("yawmiyat_journal", refresh.missing_sources)


class RoutingTests(unittest.TestCase):
    def test_hayat_when_body_freshest(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=context_refresh.ALL_SOURCES,
            sources_found=("whoop_badan", "yawmiyat_journal"),
            missing_sources=(),
            latest_entry_timestamps={
                "whoop_badan": "2026-06-14T09:00:00Z",
                "yawmiyat_journal": "2026-06-13T09:00:00Z",
            },
            confidence="high",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        self.assertEqual(routing.pick_agent(refresh), "Hayat")

    def test_sadiq_when_journal_freshest(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=context_refresh.ALL_SOURCES,
            sources_found=("yawmiyat_journal", "whoop_badan"),
            missing_sources=(),
            latest_entry_timestamps={
                "yawmiyat_journal": "2026-06-14T09:30:00Z",
                "whoop_badan": "2026-06-13T09:00:00Z",
            },
            confidence="high",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        self.assertEqual(routing.pick_agent(refresh), "Sadiq")

    def test_salman_fallback(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=context_refresh.ALL_SOURCES,
            sources_found=(),
            missing_sources=context_refresh.ALL_SOURCES,
            latest_entry_timestamps={},
            confidence="low",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        self.assertEqual(routing.pick_agent(refresh), "Salman")


class MessageBuilderTests(unittest.TestCase):
    def test_companion_message_has_identity_and_focus(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=context_refresh.ALL_SOURCES,
            sources_found=(),
            missing_sources=context_refresh.ALL_SOURCES,
            latest_entry_timestamps={},
            confidence="low",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        message = message_builder.build_companion_checkin(refresh, agent_name="Salman")
        self.assertTrue(message.message.startswith("I'm Salman,"))
        self.assertIn("I checked", message.message)
        self.assertTrue(message.focus_trigger)

    def test_tiny_mode_shortens_message(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=context_refresh.ALL_SOURCES,
            sources_found=(),
            missing_sources=context_refresh.ALL_SOURCES,
            latest_entry_timestamps={},
            confidence="low",
            privacy_level="strict_local",
            sukoon_capacity="yellow",
        )
        message = message_builder.build_companion_checkin(refresh, tiny_mode=True)
        self.assertIn("tiny", message.message.lower())


class HimayahTests(unittest.TestCase):
    def test_redacts_snapshots_on_egress(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=("yawmiyat_journal",),
            sources_found=("yawmiyat_journal",),
            missing_sources=(),
            latest_entry_timestamps={"yawmiyat_journal": "2026-06-14T09:00:00Z"},
            confidence="medium",
            privacy_level="strict_local",
            sukoon_capacity="green",
            source_snapshots={"yawmiyat_journal": {"entry_date": "2026-06-14"}},
        )
        message = PulsationMessage(
            message_type="companion_checkin",
            agent_name="Sadiq",
            agent_role="Journaling steward",
            generated_at="2026-06-14T10:00:00Z",
            context_refresh=refresh,
            message="I'm Sadiq, your journaling steward.",
            focus_trigger="Continue your thread.",
        )
        safe, result = himayah_egress.apply_egress(message)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(safe.context_refresh.privacy_level, "public_safe")
        self.assertEqual(safe.context_refresh.source_snapshots, {})

    def test_refuses_journal_body_marker(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=(),
            sources_found=(),
            missing_sources=(),
            latest_entry_timestamps={},
            confidence="low",
            privacy_level="strict_local",
            sukoon_capacity="green",
        )
        message = PulsationMessage(
            message_type="companion_checkin",
            agent_name="Sadiq",
            agent_role="Journaling steward",
            generated_at="2026-06-14T10:00:00Z",
            context_refresh=refresh,
            message="felt_state: anxious",
            focus_trigger="n/a",
        )
        safe, result = himayah_egress.apply_egress(message)
        self.assertEqual(result["status"], "refused")
        self.assertIn("HIMAYAH blocked", safe.message)


class CollisionTests(unittest.TestCase):
    def test_loop_a_wins_when_both_due(self) -> None:
        now = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc)
        winner, reason = collision.resolve_collision(
            loop_a_due=True,
            loop_b_due=True,
            last_loop_a_at=now - timedelta(minutes=5),
            last_loop_b_at=now - timedelta(minutes=5),
            now=now,
        )
        self.assertEqual(winner, "a")
        self.assertIsNotNone(reason)


class LoopTests(unittest.TestCase):
    def test_waking_hours(self) -> None:
        morning = datetime(2026, 6, 14, 7, 30, tzinfo=timezone.utc)
        night = datetime(2026, 6, 14, 21, 0, tzinfo=timezone.utc)
        self.assertTrue(loops.in_waking_hours(morning))
        self.assertFalse(loops.in_waking_hours(night))

    def test_islamic_loop_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "islamic_reminder_config.json"
            config.write_text(json.dumps({"enabled": False}), encoding="utf-8")
            with mock.patch.object(loops, "ISLAMIC_CONFIG", config):
                result = loops.evaluate_loops(
                    now=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
                    loop="b",
                    dry_run=True,
                )
        self.assertTrue(result.get("skipped"))
        self.assertEqual(result.get("reason"), "islamic_reminder_disabled")


class StateTests(unittest.TestCase):
    def test_state_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulsation-state.json"
            state.save_state({"last_loop_a_at": "2026-06-14T07:00:00Z"}, path)
            loaded = state.load_state(path)
            self.assertEqual(loaded["last_loop_a_at"], "2026-06-14T07:00:00Z")


class ProactivePolicyTests(unittest.TestCase):
    def test_crisis_suppress_blocks(self) -> None:
        candidate = ProactiveCandidate(
            persona="Salman",
            trigger="pulsation",
            relevance_score=0.9,
            source_refs=("pulsation:context_refresh",),
            expires_at="2099-01-01T00:00:00Z",
            message="check-in",
        )
        ok, reason, tiny = eligible(
            candidate,
            now=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
            sent_today=[],
            paused=False,
            crisis_suppress=True,
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "crisis_suppress")

    def test_yellow_allows_tiny_mode(self) -> None:
        candidate = ProactiveCandidate(
            persona="Salman",
            trigger="pulsation",
            relevance_score=0.9,
            source_refs=("pulsation:context_refresh",),
            expires_at="2099-01-01T00:00:00Z",
            message="check-in",
        )
        ok, reason, tiny = eligible(
            candidate,
            now=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
            sent_today=[],
            paused=False,
            sukoon_capacity="yellow",
        )
        self.assertTrue(ok, reason)
        self.assertTrue(tiny)


class LedgerTests(unittest.TestCase):
    def test_dry_run_skips_ledger(self) -> None:
        refresh = ContextRefresh(
            refreshed_at="2026-06-14T10:00:00Z",
            sources_checked=(),
            sources_found=(),
            missing_sources=(),
            latest_entry_timestamps={},
            confidence="low",
            privacy_level="public_safe",
            sukoon_capacity="green",
        )
        message = PulsationMessage(
            message_type="companion_checkin",
            agent_name="Salman",
            agent_role="Brainstormer",
            generated_at="2026-06-14T10:00:00Z",
            context_refresh=refresh,
            message="I'm Salman, your Brainstormer.",
            focus_trigger="One step.",
        )
        result = append_pulsation(message, loop="a", send_status="skipped_dry_run", dry_run=True)
        self.assertEqual(result["status"], "skipped_dry_run")


class IntegrationTests(unittest.TestCase):
    def test_forced_loop_a_dry_run(self) -> None:
        result = loops.evaluate_loops(
            now=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
            loop="a",
            dry_run=True,
        )
        self.assertFalse(result.get("skipped"))
        message = result.get("message")
        self.assertIsNotNone(message)
        assert hasattr(message, "message")
        self.assertIn("I'm", message.message)


if __name__ == "__main__":
    unittest.main()
