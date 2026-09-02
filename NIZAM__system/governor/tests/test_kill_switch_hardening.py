"""test_kill_switch_hardening.py - proof tests for the file-based kill switch.

Covers the hardening added alongside the host-native migration work: the
kill switch now has two independent signals (env var + file existence),
OR'd together, so an ordinary Hermes turn editing its own profile .env
cannot silently clear a stop that was set via the file path outside any
Hermes-profile-writable directory.

Every test uses a temporary file path via the `kill_switch_file=` /
`NIZAM_KILL_SWITCH_FILE` override; the real /etc/nizam file is never
touched or even stat'd unless the default is used explicitly.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import kill_switch as ks  # noqa: E402
from NIZAM__system.governor import ledger_writer as lw  # noqa: E402


class TestKillSwitchOrLogic(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fake_file = Path(self._tmp.name) / "HALT"
        self._prev_env = os.environ.get("NIZAM_KILL_ALL")
        if "NIZAM_KILL_ALL" in os.environ:
            del os.environ["NIZAM_KILL_ALL"]

    def tearDown(self):
        self._tmp.cleanup()
        if self._prev_env is not None:
            os.environ["NIZAM_KILL_ALL"] = self._prev_env
        elif "NIZAM_KILL_ALL" in os.environ:
            del os.environ["NIZAM_KILL_ALL"]

    def test_alive_when_neither_signal_set(self):
        self.assertTrue(ks.is_alive(self.fake_file))

    def test_dead_when_file_exists_even_with_empty_env(self):
        self.fake_file.write_text("")
        self.assertFalse(ks.is_alive(self.fake_file))
        with self.assertRaises(ks.KillSwitchActive):
            ks.assert_alive("test", self.fake_file)

    def test_dead_when_env_set_even_without_file(self):
        os.environ["NIZAM_KILL_ALL"] = "1"
        self.assertFalse(ks.is_alive(self.fake_file))

    def test_file_signal_survives_env_being_cleared(self):
        # Simulates the scenario this hardening exists for: a Hermes turn
        # edits its own .env to clear NIZAM_KILL_ALL, but the file-based
        # signal (set outside any profile-writable path) still wins.
        self.fake_file.write_text("")
        os.environ["NIZAM_KILL_ALL"] = "1"
        del os.environ["NIZAM_KILL_ALL"]  # the "Hermes cleared its own .env" step
        self.assertFalse(ks.is_alive(self.fake_file), "file signal must survive an env clear")

    def test_status_reports_both_signals(self):
        self.fake_file.write_text("")
        report = ks.status(self.fake_file)
        self.assertTrue(report["kill_switch_file_present"])
        self.assertFalse(report["alive"])


class TestLedgerWriterUsesHardenedSwitch(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self._prev_env = os.environ.pop("NIZAM_KILL_ALL", None)

    def tearDown(self):
        self._tmp.cleanup()
        if self._prev_env is not None:
            os.environ["NIZAM_KILL_ALL"] = self._prev_env

    def test_ledger_append_halts_when_env_killed(self):
        os.environ["NIZAM_KILL_ALL"] = "1"
        try:
            with self.assertRaises(RuntimeError):
                lw.append(
                    "EVENT_LEDGER", {"k": "v"}, record_id="killswitch-test-1",
                    module="TEST", root=self.tmp_path,
                )
        finally:
            del os.environ["NIZAM_KILL_ALL"]

    def test_ledger_append_works_when_alive(self):
        row = lw.append(
            "EVENT_LEDGER", {"k": "v"}, record_id="killswitch-test-2",
            module="TEST", root=self.tmp_path,
        )
        self.assertEqual(row["record_id"], "killswitch-test-2")


if __name__ == "__main__":
    unittest.main()
