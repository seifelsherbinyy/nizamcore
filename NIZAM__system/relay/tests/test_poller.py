"""test_poller.py — HERMES long-poll runner orchestration tests.

Mocks Telegram transport, auth, dedup, and coordinator so no network call
and no ledger write happens. Verifies: dedup skip, non-operator rejection,
happy-path reply, blocked-content safety, and getUpdates offset.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.relay import poller  # noqa: E402


def _update(uid: int = 8001780136, upd_id: int = 10, text: str = "hi") -> dict:
    return {
        "update_id": upd_id,
        "message": {
            "message_id": 1,
            "from": {"id": uid, "is_bot": False},
            "chat": {"id": uid, "type": "private"},
            "text": text,
        },
    }


class TestPollerHandleUpdate(unittest.TestCase):
    def test_duplicate_is_skipped(self):
        with mock.patch.object(poller.dedup, "record", return_value=False), \
             mock.patch.object(poller.coordinator, "process") as proc, \
             mock.patch.object(poller, "tg_send_message") as send:
            out = poller.handle_update(_update(), token="T")
        self.assertIsNone(out)
        proc.assert_not_called()
        send.assert_not_called()

    def test_non_whitelisted_is_rejected(self):
        with mock.patch.object(poller.dedup, "record", return_value=True), \
             mock.patch.object(poller.auth, "verify_user_id",
                               side_effect=poller.auth.UserNotWhitelisted("nope")), \
             mock.patch.object(poller.coordinator, "process") as proc, \
             mock.patch.object(poller, "tg_send_message") as send:
            out = poller.handle_update(_update(uid=999), token="T")
        self.assertIsNone(out)
        proc.assert_not_called()
        send.assert_not_called()

    def test_malformed_update_id_skipped(self):
        with mock.patch.object(poller.coordinator, "process") as proc:
            out = poller.handle_update({"message": {}}, token="T")
        self.assertIsNone(out)
        proc.assert_not_called()

    def test_happy_path_sends_reply(self):
        env = {"reply": "captured.", "blocked": False,
               "target": "Amin", "trace_id": "x"}
        with mock.patch.object(poller.dedup, "record", return_value=True), \
             mock.patch.object(poller.auth, "verify_user_id",
                               return_value=8001780136), \
             mock.patch.object(poller.coordinator, "process", return_value=env), \
             mock.patch.object(poller, "tg_send_message") as send:
            out = poller.handle_update(_update(), token="T")
        self.assertEqual(out, env)
        send.assert_called_once()
        args = send.call_args.args
        self.assertEqual(args[0], "T")
        self.assertEqual(args[1], 8001780136)
        self.assertEqual(args[2], "captured.")

    def test_blocked_sends_safe_notice_not_content(self):
        env = {"reply": "SENSITIVE FAMILY CONTENT", "blocked": True,
               "block_reason": "AHEL strict_local_maximum",
               "target": "Yusra", "trace_id": "x"}
        with mock.patch.object(poller.dedup, "record", return_value=True), \
             mock.patch.object(poller.auth, "verify_user_id",
                               return_value=8001780136), \
             mock.patch.object(poller.coordinator, "process", return_value=env), \
             mock.patch.object(poller, "tg_send_message") as send:
            poller.handle_update(_update(), token="T")
        sent_text = send.call_args.args[2]
        self.assertNotIn("SENSITIVE FAMILY CONTENT", sent_text)
        self.assertIn("HIMAYAH", sent_text)

    def test_send_failure_does_not_raise(self):
        env = {"reply": "captured.", "blocked": False,
               "target": "Amin", "trace_id": "x"}
        with mock.patch.object(poller.dedup, "record", return_value=True), \
             mock.patch.object(poller.auth, "verify_user_id",
                               return_value=8001780136), \
             mock.patch.object(poller.coordinator, "process", return_value=env), \
             mock.patch.object(poller, "tg_send_message",
                               side_effect=RuntimeError("network down")):
            # must not raise
            out = poller.handle_update(_update(), token="T")
        self.assertEqual(out, env)


class TestPollerOffset(unittest.TestCase):
    def test_poll_once_uses_max_seen_plus_one(self):
        with mock.patch.object(poller.dedup, "max_seen", return_value=41), \
             mock.patch.object(poller, "tg_get_updates", return_value=[]) as gu:
            poller.poll_once("T", 25, send=True)
        gu.assert_called_once_with("T", 42, 25)


if __name__ == "__main__":
    unittest.main()
