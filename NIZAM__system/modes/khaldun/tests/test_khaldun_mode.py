from __future__ import annotations

import json
import unittest
from pathlib import Path

from NIZAM__system.modes.khaldun.classifier import classify_claim
from NIZAM__system.modes.khaldun.miracle_review import assess_miracle_claim
from NIZAM__system.modes.khaldun.paths import MODE_BUNDLE
from NIZAM__system.modes.khaldun.validator import validate_khaldun_response
from NIZAM__system.modes.khaldun.verification import run_research_protocol


class KhaldunClassifierTests(unittest.TestCase):
    def test_tc06_allah_inside(self):
        result = classify_claim("Allah is inside us physically")
        self.assertEqual(result.primary_label, "H_reject_aqidah_risk")

    def test_tc03_weak_hadith_science(self):
        result = classify_claim(
            "Weak hadith proves science",
            {"hadith_grade": "daif", "scientific_alignment": True},
        )
        self.assertEqual(result.primary_label, "G_speculative_unverified")

    def test_tc04_chakras(self):
        result = classify_claim("Chakras map to qalb in Islam")
        self.assertEqual(result.primary_label, "F_symbolic_comparative")


class KhaldunValidatorTests(unittest.TestCase):
    def test_blocks_fatwa(self):
        ok, reason = validate_khaldun_response("This is haram for you")
        self.assertFalse(ok)
        self.assertEqual(reason, "fatwa_language")

    def test_allows_gentle_reminder(self):
        msg = "تفويض ومراقبة — خطوة صغيرة\n*ليس فتوى.*"
        ok, _ = validate_khaldun_response(msg, evidence={"tasawwuf_topic": True})
        self.assertTrue(ok)


class KhaldunBundleTests(unittest.TestCase):
    def test_mode_bundle_files_exist(self):
        required = [
            "mode_charter.md",
            "source_registry.json",
            "claim_classification.schema.json",
            "spiritual_reminder_mapping.json",
        ]
        for name in required:
            self.assertTrue((MODE_BUNDLE / name).exists(), name)

    def test_test_cases_load(self):
        cases = json.loads(
            (MODE_BUNDLE / "khaldun_test_cases.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(cases["cases"]), 8)


class KhaldunMiracleTests(unittest.TestCase):
    def test_rejected_forced(self):
        out = assess_miracle_claim({"text_stable": True, "non_forced": False})
        self.assertEqual(out["miracle_ladder_grade"], "rejected")


class KhaldunProtocolTests(unittest.TestCase):
    def test_research_protocol_runs(self):
        bundle = run_research_protocol(
            "Allah is inside us",
            evidence={"fiqh_relevant": True},
        )
        self.assertIsNotNone(bundle.classification)
        self.assertEqual(bundle.classification.primary_label, "H_reject_aqidah_risk")


if __name__ == "__main__":
    unittest.main()
