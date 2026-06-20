from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from NIZAM__system.companion.contracts import ContextRefresh, PulsationMessage, utc_now
from NIZAM__system.companion import scheduler
from NIZAM__system.modes.khaldun.reminder_composer import (
    append_dryrun_log,
    compose_khaldun_reminder,
)
from NIZAM__system.modes.khaldun.context_linker import SeifContextSummary
from NIZAM__system.modes.khaldun.validator import validate_khaldun_response
from NIZAM__system.modes.khaldun.paths import DRYRUN_LOG


def _refresh(*, capacity: str = "green") -> ContextRefresh:
    return ContextRefresh(
        refreshed_at=utc_now(),
        sources_checked=("pulse_entries", "sukoon_capacity"),
        sources_found=("pulse_entries",),
        missing_sources=("whoop_badan",),
        latest_entry_timestamps={"pulse_entries": utc_now()},
        confidence="medium",
        privacy_level="strict_local",
        sukoon_capacity=capacity,
        source_snapshots={
            "pulse_entries": {"capacity_band": "LOW", "recovery": 42},
        },
    )


class KhaldunReminderComposerTests(unittest.TestCase):
    def test_compose_valid_reminder(self) -> None:
        summary = SeifContextSummary(
            pulse_summary={"capacity_band": "LOW", "recovery": 42},
            sukoon_capacity="yellow",
            missing_data=["whoop_badan"],
        )
        message, err = compose_khaldun_reminder(
            summary, _refresh(capacity="yellow"), tiny_mode=True
        )
        self.assertIsNone(err)
        self.assertIsNotNone(message)
        assert message is not None
        self.assertEqual(message.agent_name, "Khaldun")
        self.assertEqual(message.message_type, "islamic_reminder")
        ok, reason = validate_khaldun_response(
            message.message, evidence={"tasawwuf_topic": True}
        )
        self.assertTrue(ok, reason)
        self.assertIn("ليس فتوى", message.message)

    def test_blocks_aqidah_risk_in_validator(self) -> None:
        ok, reason = validate_khaldun_response("Allah is inside us physically")
        self.assertFalse(ok)
        self.assertEqual(reason, "aqidah_risk_uncorrected")


class KhaldunTelegramSchedulerTests(unittest.TestCase):
    def test_send_pulsation_khaldun_dry_run_without_outbound_approval(self) -> None:
        summary = SeifContextSummary(
            pulse_summary={"capacity_band": "MEDIUM", "recovery": 55},
            sukoon_capacity="green",
        )
        message, err = compose_khaldun_reminder(summary, _refresh(), tiny_mode=False)
        self.assertIsNone(err)
        assert message is not None

        with tempfile.TemporaryDirectory() as tmp:
            dry_log = Path(tmp) / "dryrun.jsonl"
            state = Path(tmp) / "proactive-state.json"
            with mock.patch.dict(os.environ, {"NIZAM_LIVE_CONNECTORS_APPROVED": "1"}, clear=False), \
                 mock.patch.dict(os.environ, {}, clear=False), \
                 mock.patch("NIZAM__system.modes.khaldun.paths.DRYRUN_LOG", dry_log), \
                 mock.patch(
                     "NIZAM__system.companion.scheduler.evaluate_candidates",
                     return_value=[(mock.Mock(), "eligible", False)],
                 ):
                os.environ.pop("NIZAM_KHALDUN_OUTBOUND_APPROVED", None)
                result = scheduler.send_pulsation(
                    message,
                    loop="b",
                    dry_run=False,
                    state_path=state,
                )
            self.assertTrue(result.get("ok"))
            self.assertTrue(result.get("dry_run"))
            self.assertEqual(result.get("reason"), "khaldun_outbound_not_approved")
            self.assertTrue(dry_log.exists())

    def test_send_pulsation_khaldun_telegram_when_outbound_approved(self) -> None:
        summary = SeifContextSummary(
            pulse_summary={"capacity_band": "MEDIUM", "recovery": 55},
            sukoon_capacity="green",
        )
        message, err = compose_khaldun_reminder(summary, _refresh(), tiny_mode=False)
        self.assertIsNone(err)
        assert message is not None

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "proactive-state.json"
            env = {
                "NIZAM_LIVE_CONNECTORS_APPROVED": "1",
                "NIZAM_KHALDUN_OUTBOUND_APPROVED": "1",
                "TELEGRAM_BOT_TOKEN": "test-token",
            }
            with mock.patch.dict(os.environ, env, clear=False), \
                 mock.patch(
                     "NIZAM__system.companion.scheduler.evaluate_candidates",
                     return_value=[(mock.Mock(), "eligible", False)],
                 ), \
                 mock.patch(
                     "NIZAM__system.relay.auth.whitelisted_ids",
                     return_value=[8001780136],
                 ), \
                 mock.patch(
                     "NIZAM__system.relay.poller.tg_send_message"
                 ) as send:
                result = scheduler.send_pulsation(
                    message,
                    loop="b",
                    dry_run=False,
                    state_path=state,
                )
            self.assertTrue(result.get("ok"))
            self.assertFalse(result.get("dry_run"))
            self.assertEqual(result.get("chat_id"), 8001780136)
            send.assert_called_once()
            args = send.call_args.args
            self.assertEqual(args[0], "test-token")
            self.assertEqual(args[1], 8001780136)
            self.assertIn("ليس فتوى", args[2])

    def test_send_pulsation_khaldun_blocked_by_validator(self) -> None:
        bad = PulsationMessage(
            message_type="islamic_reminder",
            agent_name="Khaldun",
            agent_role="test",
            generated_at=utc_now(),
            context_refresh=_refresh(),
            message="This is haram for you definitely",
            focus_trigger="n/a",
        )
        result = scheduler.send_pulsation(bad, loop="b", dry_run=False)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason"), "fatwa_language")


class KhaldunDryrunLogTests(unittest.TestCase):
    def test_append_dryrun_log_writes_jsonl(self) -> None:
        summary = SeifContextSummary(sukoon_capacity="green")
        message, _ = compose_khaldun_reminder(summary, _refresh(), tiny_mode=False)
        assert message is not None
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dryrun.jsonl"
            with mock.patch("NIZAM__system.modes.khaldun.paths.DRYRUN_LOG", path):
                append_dryrun_log(message, reason="test")
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            row = json.loads(lines[0])
            self.assertEqual(row["reason"], "test")
            self.assertEqual(row["message"]["agent_name"], "Khaldun")


if __name__ == "__main__":
    unittest.main()
