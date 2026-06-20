from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from NIZAM__system.companion import badan_import, scheduler
from NIZAM__system.companion.contracts import ProactiveCandidate
from NIZAM__system.relay import telemetry


class ProductionModuleTests(unittest.TestCase):
    def test_telemetry_exports_when_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "telemetry.jsonl"
            with mock.patch.dict(os.environ, {"NIZAM_REMOTE_TELEMETRY_APPROVED": "1"}, clear=False):
                result = telemetry.export_remote(path=path)
            self.assertTrue(result["ok"])
            self.assertTrue(path.exists())

    def test_scheduler_dry_run_accepts_candidate(self) -> None:
        candidate = ProactiveCandidate(
            persona="Amin",
            trigger="calendar_deadline",
            relevance_score=0.9,
            source_refs=("calendar:event:1",),
            expires_at="2099-01-01T00:00:00Z",
            message="Review is due soon.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "proactive-state.json"
            result = scheduler.run_hourly_evaluation(
                [candidate],
                dry_run=True,
                now=datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc),
                state_path=state_path,
            )
        self.assertEqual(result["accepted"], 1)

    def test_whoop_persist_writes_badan_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "whoop.csv"
            export_path.write_text(
                "date,recovery score,hrv\n2026-06-10,72,48\n",
                encoding="utf-8",
            )
            badan_dir = Path(tmp) / "badan"
            result = badan_import.persist_whoop_export(export_path, badan_dir=badan_dir)
            self.assertEqual(result["observation_count"], 2)
            self.assertTrue(Path(str(result["output"])).exists())
            manifest = badan_dir / "_imports.json"
            self.assertTrue(manifest.exists())

    def test_journal_import_writes_session_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = badan_import.persist_journal_entry(
                title="Check-in",
                body="Feeling steady.",
                session_date="2026-06-13",
                journal_dir=Path(tmp),
            )
            payload = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["title"], "Check-in")


if __name__ == "__main__":
    unittest.main()
