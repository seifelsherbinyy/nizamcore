from __future__ import annotations

import json
import unittest
from pathlib import Path

from NIZAM__system.skills_registry.router import handle_command, load_registry, resolve_command

REPO = Path(__file__).resolve().parents[3]
INDEX = REPO / "NIZAM__system" / "skills_registry" / "index.json"
SCHEMA = REPO / "NIZAM__system" / "skills_registry" / "registry.schema.json"


class SkillsRegistryTests(unittest.TestCase):
    def test_registry_has_nine_skills(self) -> None:
        reg = load_registry(INDEX)
        self.assertEqual(len(reg["skills"]), 9)
        ids = {s["id"] for s in reg["skills"]}
        self.assertIn("council_review", ids)

    def test_council_review_command_maps(self) -> None:
        skill = resolve_command("/council-review motion: housing focus")
        self.assertIsNotNone(skill)
        assert skill is not None
        self.assertEqual(skill["id"], "council_review")

    def test_handle_command_privacy_safe_stub(self) -> None:
        result = handle_command("/council-review test motion")
        self.assertTrue(result["ok"])
        self.assertTrue(result["council_required"])
        self.assertIn("Council review", result["reply_stub"])
        serialized = json.dumps(result)
        self.assertNotIn("journal", serialized.lower())

    def test_missing_command_returns_none(self) -> None:
        self.assertIsNone(resolve_command("hello world"))

    def test_skill_files_exist(self) -> None:
        reg = load_registry(INDEX)
        for skill in reg["skills"]:
            path = REPO / skill["path"]
            self.assertTrue(path.exists(), msg=str(path))

    def test_schema_file_present(self) -> None:
        self.assertTrue(SCHEMA.exists())


if __name__ == "__main__":
    unittest.main()
