"""Fixture-based tests for governor.classifier.

10-file fixture covering every classification tier and a fallthrough path.
Run with:

    .venv\\Scripts\\python.exe -m unittest NIZAM__system.governor.tests.test_classifier_fixture

(from `D:\\NIZAM\\nizamcore`)

Pure stdlib (unittest).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import classifier  # noqa: E402
from NIZAM__system.governor.sync_arbiter import (  # noqa: E402
    Plane,
    decide,
    pre_commit_check,
)


FIXTURE = [
    # (rel_path, expected_classification)
    ("TAFRIGH__brain_dumper/raw/2026-05-28.md",           "strict_local"),
    ("SHURA__brainstormer/sessions/2026-05-28.md",        "strict_local"),
    ("NAQD__brain_griller/sessions/2026-05-28.md",        "strict_local"),
    ("AHEL__family_network/records/dad.md",               "strict_local_maximum"),
    ("BADAN__body_health_system/biometrics.jsonl",        "strict_local"),
    ("MAL__financial_engine/budget_2026.md",              "strict_local"),
    ("NIZAM__system/ledgers/EVENT_LEDGER.jsonl",          "review_before_commit"),
    ("NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl",       "strict_local"),
    ("NIZAM__system/policies/PRIVACY_CLASSIFICATION.json", "private_github"),
    ("README.md",                                          "private_github"),
]


class ClassifierFixtureTests(unittest.TestCase):
    def test_each_fixture_matches_expected_class(self) -> None:
        for path, expected in FIXTURE:
            with self.subTest(path=path):
                got = classifier.classify(path)
                self.assertEqual(got, expected, f"{path}: got {got}, want {expected}")

    def test_default_strict_local_for_unknown(self) -> None:
        self.assertEqual(
            classifier.classify("some/random/unmapped/path.md"),
            "strict_local",
        )

    def test_egress_matrix_blocks_strict_local_to_github(self) -> None:
        blocked, reason = classifier.is_egress_blocked(
            "TAFRIGH__brain_dumper/raw/2026-05-28.md", "github_private")
        self.assertTrue(blocked, f"should be blocked: {reason}")

    def test_egress_matrix_blocks_ahel_everywhere_outbound(self) -> None:
        for tgt in ("github_private", "vps_plaintext", "drive_clear",
                    "notion_sanitized"):
            with self.subTest(target=tgt):
                blocked, reason = classifier.is_egress_blocked(
                    "AHEL__family_network/records/dad.md", tgt)
                self.assertTrue(blocked, f"AHEL must be blocked from {tgt}: {reason}")

    def test_egress_matrix_allows_private_github_to_github(self) -> None:
        blocked, _ = classifier.is_egress_blocked(
            "NIZAM__system/policies/PRIVACY_CLASSIFICATION.json",
            "github_private",
        )
        self.assertFalse(blocked)

    def test_sync_arbiter_decide_strict_local_to_drive_crypt_allowed(self) -> None:
        d = decide("SHURA__brainstormer/sessions/2026-05-28.md", Plane.DRIVE_CRYPT)
        self.assertTrue(d.allowed, d.reason)

    def test_sync_arbiter_decide_strict_local_to_drive_clear_blocked(self) -> None:
        d = decide("SHURA__brainstormer/sessions/2026-05-28.md", Plane.DRIVE_CLEAR)
        self.assertFalse(d.allowed, d.reason)

    def test_pre_commit_blocks_mixed_batch(self) -> None:
        # 4 framework + 2 strict_local + 1 AHEL — 3 expected blocks
        batch = [
            "README.md",
            "NIZAM__system/policies/PRIVACY_CLASSIFICATION.json",
            "NIZAM__system/schemas/persona.schema.json",
            "NIZAM__system/templates/persona_v1.1_template.json",
            "SHURA__brainstormer/sessions/2026-05-28.md",
            "NAQD__brain_griller/sessions/2026-05-28.md",
            "AHEL__family_network/records/dad.md",
        ]
        ok, blocked = pre_commit_check(batch)
        self.assertFalse(ok)
        self.assertEqual(len(blocked), 3, blocked)


if __name__ == "__main__":
    unittest.main()
