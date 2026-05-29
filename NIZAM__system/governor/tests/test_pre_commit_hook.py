"""test_pre_commit_hook.py — sanity tests for the pre-commit block path.

Exercises `sync_arbiter.pre_commit_check` directly (the same function the
real hook invokes) on a mixed batch and asserts blocking behavior.

Run with:
    .venv\\Scripts\\python.exe -m unittest NIZAM__system.governor.tests.test_pre_commit_hook
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor.sync_arbiter import pre_commit_check  # noqa: E402


CLEAN_BATCH = [
    "README.md",
    "NIZAM__system/policies/PRIVACY_CLASSIFICATION.json",
    "NIZAM__system/schemas/persona.schema.json",
    "NIZAM__system/governor/classifier.py",
]

LEAKY_BATCH = CLEAN_BATCH + [
    "SHURA__brainstormer/sessions/2026-05-28.md",
    "AHEL__family_network/records/dad.md",
]


class PreCommitHookTests(unittest.TestCase):
    def test_clean_batch_allowed(self) -> None:
        ok, blocked = pre_commit_check(CLEAN_BATCH)
        self.assertTrue(ok, blocked)
        self.assertEqual(blocked, [])

    def test_leaky_batch_blocked(self) -> None:
        ok, blocked = pre_commit_check(LEAKY_BATCH)
        self.assertFalse(ok)
        rel_paths = {d.rel_path for d in blocked}
        self.assertIn("SHURA__brainstormer/sessions/2026-05-28.md", rel_paths)
        self.assertIn("AHEL__family_network/records/dad.md", rel_paths)

    def test_blocked_decisions_carry_reason(self) -> None:
        _, blocked = pre_commit_check(LEAKY_BATCH)
        for d in blocked:
            self.assertTrue(d.reason.startswith("HIMAYAH refuses"))


if __name__ == "__main__":
    unittest.main()
