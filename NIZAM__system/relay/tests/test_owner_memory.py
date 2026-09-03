"""Tests for explicit, append-only owner memory."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from NIZAM__system.relay.owner_memory import (
    append_explicit_memory,
    extract_explicit_memory,
    render_memory,
)


class TestOwnerMemory(unittest.TestCase):
    def test_ordinary_text_is_not_memory(self):
        self.assertIsNone(extract_explicit_memory("I prefer concise replies"))

    def test_explicit_preference_is_append_only_and_confirmed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "memory.jsonl")
            record = append_explicit_memory(path, "remember: use concise replies", trace_id="trace-1")
            self.assertEqual(record["status"], "confirmed")
            rows = Path(path).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 1)
            self.assertEqual(json.loads(rows[0])["content"], "use concise replies")
            self.assertIn("use concise replies", render_memory(path))

    def test_health_and_journal_content_is_not_rendered_to_cloud_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "status": "confirmed",
                        "confirmed_by": "Operator",
                        "content": "remember my health recovery history",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(render_memory(str(path)), "")

    def test_secret_like_memory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "memory.jsonl")
            self.assertIsNone(append_explicit_memory(path, "remember: api_key=secret", trace_id="trace-2"))
            self.assertFalse(Path(path).exists())


if __name__ == "__main__":
    unittest.main()
