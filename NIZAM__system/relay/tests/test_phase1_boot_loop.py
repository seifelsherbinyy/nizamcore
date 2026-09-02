"""Phase-1 boot loop tests (B4.1–B4.10).

Run:
    .venv\\Scripts\\python.exe -m unittest NIZAM__system.relay.tests.test_phase1_boot_loop -v

(From `D:\\NIZAM\\nizamcore`.)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Configure auth + ledgers BEFORE importing relay modules.
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-secret-XYZ")
os.environ.setdefault("NIZAM_TELEGRAM_ALLOWED_IDS", "111222333")

from NIZAM__system.governor import ledger_writer  # noqa: E402
from NIZAM__system.relay import auth, coordinator, dedup, sukoon_gate, webhook  # noqa: E402


def _fresh_update(text: str, user_id: int = 111222333) -> dict:
    """A never-before-seen update, the way a real Telegram update always is."""
    return _telegram_update(text,
                            update_id=900_000_000 + uuid.uuid4().int % 10**8,
                            user_id=user_id)


def _telegram_update(text: str, update_id: int = 1,
                     user_id: int = 111222333) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "from": {"id": user_id, "is_bot": False, "first_name": "Op"},
            "chat": {"id": user_id, "type": "private"},
            "date": 1716926400,
            "text": text,
        },
    }


class B41_AuthSecretToken(unittest.TestCase):
    """B4.1 secret-token verification (CVE-2026-32980)."""

    def test_missing_secret_header_rejected(self) -> None:
        with self.assertRaises(auth.AuthError):
            auth.verify_secret_token(None)

    def test_wrong_secret_rejected(self) -> None:
        with self.assertRaises(auth.TokenMismatch):
            auth.verify_secret_token("wrong-value")

    def test_correct_secret_accepted(self) -> None:
        # No exception means pass
        auth.verify_secret_token("test-secret-XYZ")


class B42_UserWhitelist(unittest.TestCase):
    """B4.2 USER_ID whitelist enforcement."""

    def test_whitelisted_user_accepted(self) -> None:
        update = _telegram_update("hello")
        uid = auth.verify_user_id(update)
        self.assertEqual(uid, 111222333)

    def test_non_whitelisted_user_rejected(self) -> None:
        update = _telegram_update("hello", user_id=99999999)
        with self.assertRaises(auth.UserNotWhitelisted):
            auth.verify_user_id(update)


class B43_DedupTable(unittest.TestCase):
    """B4.3 update_id dedup table."""

    def setUp(self) -> None:
        dedup.reset()

    def tearDown(self) -> None:
        dedup.reset()

    def test_first_seen_records(self) -> None:
        self.assertTrue(dedup.record(42))
        self.assertTrue(dedup.already_seen(42))

    def test_repeat_returns_false(self) -> None:
        self.assertTrue(dedup.record(42))
        self.assertFalse(dedup.record(42))
        self.assertEqual(dedup.max_seen(), 42)


class B44_SukoonPreGate(unittest.TestCase):
    """B4.4 Coordinator SUKOON pre-gate."""

    def test_normal_returns_no_downshift(self) -> None:
        out = sukoon_gate.pre_gate("Just thinking out loud.")
        self.assertFalse(out["downshift"])
        self.assertEqual(out["mode"], "normal")

    def test_crisis_keyword_triggers_protocol(self) -> None:
        out = sukoon_gate.pre_gate("PANIC, overload red")
        self.assertTrue(out["downshift"])
        self.assertEqual(out["mode"], "crisis_protocol")


class B45_CoordinatorRoutes(unittest.TestCase):
    """B4.5 Coordinator -> router -> agent stub."""

    def setUp(self) -> None:
        dedup.reset()

    def test_brainstorm_routes_to_salman(self) -> None:
        update = _telegram_update("/shura-brainstorm wealth options")
        d = coordinator.process(update, user_id=111222333)
        self.assertEqual(d["target"], "Salman")
        self.assertEqual(d["kind"], "COMMAND")
        self.assertFalse(d["blocked"], d.get("block_reason"))

    def test_capture_routes_to_amin(self) -> None:
        update = _telegram_update("Just thinking out loud, no idea where this goes.")
        d = coordinator.process(update, user_id=111222333)
        self.assertEqual(d["target"], "Amin")
        self.assertFalse(d["blocked"], d.get("block_reason"))


class B46_HimayahEgressCheck(unittest.TestCase):
    """B4.6 HIMAYAH classifies the would-be persistence path."""

    def setUp(self) -> None:
        dedup.reset()

    def test_strict_local_allowed_to_telegram_operator(self) -> None:
        update = _telegram_update("/shura-brainstorm wealth options")
        d = coordinator.process(update, user_id=111222333)
        self.assertFalse(d["blocked"], d.get("block_reason"))


class B47_LedgerAppend(unittest.TestCase):
    """B4.7 HIMAYAH-passed -> THABAT (ledger) append."""

    def setUp(self) -> None:
        dedup.reset()

    def test_round_trip_writes_event_ledger_row(self) -> None:
        # A fresh update_id per run, because the writer is now idempotent on it
        # (section 6a purpose 4). Telegram never reuses an update_id, so a
        # hard-coded one only ever worked by relying on the very defect that
        # purpose 4 fixes: with a stable id, the second run of this test would
        # replay the row the first run wrote instead of appending a new one.
        d = coordinator.process(_fresh_update("/shura-brainstorm Q3"),
                                user_id=111222333)
        self.assertIsNotNone(d["ledger_row_id"])
        tail = ledger_writer.tail_rows("EVENT_LEDGER", n=2)
        self.assertTrue(any(r["row_id"] == d["ledger_row_id"] for r in tail))

    def test_a_retried_turn_reuses_its_ledger_row(self) -> None:
        """The ledger half of B4.8.

        The gateway already drops a duplicate update_id, so this covers the
        case the gateway cannot: the turn was processed, the process died
        before the dedup table was saved, and the same update is handed to the
        coordinator again.
        """
        update = _fresh_update("/shura-brainstorm Q3")
        before = len(ledger_writer.tail_rows("EVENT_LEDGER", n=1_000_000))
        first = coordinator.process(update, user_id=111222333)
        second = coordinator.process(update, user_id=111222333)
        after = len(ledger_writer.tail_rows("EVENT_LEDGER", n=1_000_000))
        self.assertEqual(first["ledger_row_id"], second["ledger_row_id"],
                         "a retried turn must land on the row it already wrote")
        self.assertEqual(after - before, 1, "one turn, one row, even on retry")


class B48_IdempotentResume(unittest.TestCase):
    """B4.8 Idempotent resume — replays do not double-fire."""

    def setUp(self) -> None:
        dedup.reset()

    def test_duplicate_update_id_dropped_at_gateway(self) -> None:
        update = _telegram_update("/shura-brainstorm Q3", update_id=999_002)
        r1 = webhook.handle_update(update, "test-secret-XYZ")
        r2 = webhook.handle_update(update, "test-secret-XYZ")
        self.assertEqual(r1["status"], "ok", r1)
        self.assertEqual(r2["status"], "duplicate", r2)


class B49_CaptureFidelitySix(unittest.TestCase):
    """B4.9 6 capture-fidelity tests (Amin/Salman separation)."""

    def setUp(self) -> None:
        dedup.reset()

    def test_amin_artifact_a_zero_themes_tensions_loops(self) -> None:
        update = _telegram_update("Random thought to dump.", update_id=999_010)
        d = coordinator.process(update, user_id=111222333)
        a = d["artifact_a"]
        self.assertNotIn("themes", a)
        self.assertNotIn("tensions", a)
        self.assertNotIn("loops", a)

    def test_amin_preserves_verbatim_capture(self) -> None:
        text = "Q3 plan feels heavy. Five rocks but only three real days a week."
        update = _telegram_update(text, update_id=999_011)
        d = coordinator.process(update, user_id=111222333)
        self.assertEqual(d["artifact_a"]["capture"], text)

    def test_artifact_b_cites_offsets_into_artifact_a(self) -> None:
        update = _telegram_update("/shura-brainstorm Q3", update_id=999_012)
        d = coordinator.process(update, user_id=111222333)
        b = d["artifact_b"]
        self.assertIsNotNone(b)
        for o in b["source_offsets"]:
            self.assertTrue(
                isinstance(o, (list, tuple)) and len(o) == 2,
                f"bad offset {o}"
            )

    def test_artifact_b_no_fabricated_quotes(self) -> None:
        text = "Q3 plan feels heavy."
        update = _telegram_update(text, update_id=999_013)
        d = coordinator.process(update, user_id=111222333)
        for q in (d["artifact_b"] or {}).get("quoted_snippets", []):
            self.assertIn(q, text)

    def test_artifact_b_owner_is_salman_when_target_synthesist(self) -> None:
        update = _telegram_update("/shura-brainstorm Q3", update_id=999_014)
        d = coordinator.process(update, user_id=111222333)
        self.assertEqual(d["artifact_b"]["owner"], "Salman")

    def test_artifact_a_always_has_amin_owner_when_present(self) -> None:
        update = _telegram_update("ad-hoc text", update_id=999_015)
        d = coordinator.process(update, user_id=111222333)
        self.assertEqual(d["artifact_a"]["owner"], "Amin")


class B410_StrictLocalLeakTestBlocked(unittest.TestCase):
    """B4.10 Deliberate strict_local leak test (must BLOCK)."""

    def setUp(self) -> None:
        dedup.reset()

    def test_classifier_blocks_strict_local_to_github(self) -> None:
        from NIZAM__system.governor.classifier import is_egress_blocked
        blocked, reason = is_egress_blocked(
            "SHURA__brainstormer/sessions/2026-05-28.md",
            "github_private",
        )
        self.assertTrue(blocked, reason)

    def test_classifier_blocks_ahel_to_telegram(self) -> None:
        from NIZAM__system.governor.classifier import is_egress_blocked
        blocked, reason = is_egress_blocked(
            "AHEL__family_network/family_tree/dad.md",
            "telegram_operator",
        )
        self.assertTrue(blocked, reason)


if __name__ == "__main__":
    unittest.main()
