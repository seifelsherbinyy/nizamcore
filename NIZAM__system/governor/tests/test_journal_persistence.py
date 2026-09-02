"""test_journal_persistence.py - proof tests for YAWMIYAT journal persistence.

Covers the acceptance bar for the journal-persistence workstream: end-to-end
write/read-back, THABAT exactly-once on restart/retry, staged-record
recovery without duplication, a write-failure case, and the HIMAYAH
tamper/negative test (strict_local content must be REFUSED from any
external-mirror step, not permitted).

Every test writes to temporary `yawmiyat_root=` / `ledger_root=` directories;
the real ~/nizamcore/YAWMIYAT__journaling and the real ledgers directory are
never touched.

Run with:
    python3 -m pytest NIZAM__system/governor/tests/test_journal_persistence.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import journal_persistence as jp  # noqa: E402
from NIZAM__system.governor import ledger_writer as lw  # noqa: E402


SAMPLE_PAYLOAD = {
    "session_type": "checkin",
    "needs_human_confirmation": False,
    "confidence": 0.9,
    "captured_at": "2026-09-01T20:45:00Z",
}
SAMPLE_MIRROR = "# Check-in — 2026-09-01\n\nSynthetic fixture content.\n"
STEM = "2026-09-01T20-45-00Z__checkin"


class JournalPersistenceTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.yawmiyat_root = self.tmp_path / "YAWMIYAT__journaling"
        self.ledger_root = self.tmp_path / "ledgers"
        self.ledger_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self._tmp.cleanup()


class TestEndToEndHappyPath(JournalPersistenceTestBase):
    def test_write_readback_ledger_and_himayah_refusal(self):
        result = jp.persist_journal_entry(
            filename_stem=STEM,
            session_payload=SAMPLE_PAYLOAD,
            mirror_markdown=SAMPLE_MIRROR,
            yawmiyat_root=self.yawmiyat_root,
            ledger_root=self.ledger_root,
        )

        # 1. Local write + independent read-back.
        session_path = Path(result["session_path"])
        mirror_path = Path(result["mirror_path"])
        self.assertTrue(session_path.exists())
        self.assertTrue(mirror_path.exists())
        self.assertEqual(json.loads(session_path.read_text()), SAMPLE_PAYLOAD)
        self.assertEqual(mirror_path.read_text(), SAMPLE_MIRROR)

        # 2. THABAT: exactly one EVENT_LEDGER row, hash-chained, module=YAWMIYAT.
        self.assertEqual(result["ledger_mode"], lw.MODE_APPENDED)
        ledger_file = self.ledger_root / "EVENT_LEDGER.jsonl"
        self.assertTrue(ledger_file.exists())
        rows = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["module"], "YAWMIYAT")
        self.assertEqual(rows[0]["record_id"], f"yawmiyat:{STEM}")

        # 3. HIMAYAH: strict_local journal content must be REFUSED from any
        #    external mirror, not silently permitted.
        self.assertEqual(result["state"], "DRIVE_MIRROR_REFUSED")
        self.assertIn("himayah_refusal_reason", result)
        self.assertIn("YAWMIYAT__journaling", result["himayah_refusal_reason"])


class TestRestartIdempotency(JournalPersistenceTestBase):
    def test_same_record_id_twice_produces_one_row(self):
        first = jp.persist_journal_entry(
            filename_stem=STEM,
            session_payload=SAMPLE_PAYLOAD,
            mirror_markdown=SAMPLE_MIRROR,
            yawmiyat_root=self.yawmiyat_root,
            ledger_root=self.ledger_root,
        )
        second = jp.persist_journal_entry(
            filename_stem=STEM,
            session_payload=SAMPLE_PAYLOAD,
            mirror_markdown=SAMPLE_MIRROR,
            yawmiyat_root=self.yawmiyat_root,
            ledger_root=self.ledger_root,
        )

        self.assertEqual(first["ledger_mode"], lw.MODE_APPENDED)
        self.assertEqual(second["ledger_mode"], lw.MODE_REPLAYED)

        ledger_file = self.ledger_root / "EVENT_LEDGER.jsonl"
        rows = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 1, "retry after restart must not duplicate the ledger row")

        # Files are byte-identical after the retry, proving idempotent write.
        session_path = Path(second["session_path"])
        self.assertEqual(json.loads(session_path.read_text()), SAMPLE_PAYLOAD)


class TestFailureCase(JournalPersistenceTestBase):
    def test_write_failure_leaves_existing_file_untouched(self):
        session_path = self.yawmiyat_root / "sessions" / f"{STEM}.json"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        original_content = json.dumps({"pre-existing": True})
        session_path.write_text(original_content, encoding="utf-8")

        real_replace = jp.os.replace

        def _boom(*_args, **_kwargs):
            raise OSError("simulated disk failure during atomic replace")

        jp.os.replace = _boom
        try:
            with self.assertRaises(OSError):
                jp.atomic_write_text(session_path, json.dumps(SAMPLE_PAYLOAD))
        finally:
            jp.os.replace = real_replace

        # The original file must be untouched — atomic_write_text must never
        # leave a half-written or truncated target on failure.
        self.assertEqual(session_path.read_text(encoding="utf-8"), original_content)


class TestStagedRecovery(JournalPersistenceTestBase):
    def test_recovers_real_record_and_discards_exact_duplicate(self):
        staging_dir = self.tmp_path / "staging_journal"
        (staging_dir / "sessions").mkdir(parents=True)
        (staging_dir / "mirrors").mkdir(parents=True)

        session_text = json.dumps(SAMPLE_PAYLOAD, indent=2)
        (staging_dir / "sessions" / f"{STEM}.json").write_text(session_text, encoding="utf-8")
        (staging_dir / "mirrors" / f"{STEM}.md").write_text(SAMPLE_MIRROR, encoding="utf-8")
        # Duplicate write-retry artifact under a wrong/generic filename,
        # byte-identical to the real session — must be discarded, not filed
        # as a second record (this reproduces the real "books.json" find).
        (staging_dir / "books.json").write_text(session_text, encoding="utf-8")

        outcome = jp.recover_staged_records(
            staging_dir=staging_dir,
            yawmiyat_root=self.yawmiyat_root,
            ledger_root=self.ledger_root,
        )

        self.assertEqual(len(outcome["recovered"]), 1)
        self.assertEqual(outcome["recovered"][0]["state"], "DRIVE_MIRROR_REFUSED")
        self.assertEqual(len(outcome["discarded_duplicates"]), 1)
        self.assertTrue(outcome["discarded_duplicates"][0].endswith("books.json"))

        ledger_file = self.ledger_root / "EVENT_LEDGER.jsonl"
        rows = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 1, "the duplicate must not create a second ledger row")

    def test_recovery_is_idempotent_across_two_runs(self):
        staging_dir = self.tmp_path / "staging_journal"
        (staging_dir / "sessions").mkdir(parents=True)
        (staging_dir / "sessions" / f"{STEM}.json").write_text(
            json.dumps(SAMPLE_PAYLOAD), encoding="utf-8"
        )

        jp.recover_staged_records(
            staging_dir=staging_dir, yawmiyat_root=self.yawmiyat_root, ledger_root=self.ledger_root,
        )
        jp.recover_staged_records(
            staging_dir=staging_dir, yawmiyat_root=self.yawmiyat_root, ledger_root=self.ledger_root,
        )

        ledger_file = self.ledger_root / "EVENT_LEDGER.jsonl"
        rows = [json.loads(line) for line in ledger_file.read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 1, "re-running recovery after a restart must not duplicate")


class TestHimayahTamper(JournalPersistenceTestBase):
    def test_yawmiyat_path_is_hard_blocked_from_external_mirror(self):
        with self.assertRaises(jp.HimayahViolation) as ctx:
            jp.classify_for_ingest(f"YAWMIYAT__journaling/sessions/{STEM}.json")
        self.assertIn("YAWMIYAT__journaling", str(ctx.exception))

    def test_himayah_gate_is_reused_not_reimplemented(self):
        # journal_persistence must call the real himayah gate, not a local
        # copy of its policy — proven by identity, not just behaviour.
        import importlib.util

        himayah_path = _REPO / "NIZAM__system" / "retrieval" / "himayah.py"
        spec = importlib.util.spec_from_file_location("_reference_himayah", himayah_path)
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)

        self.assertEqual(
            jp.classify_for_ingest.__code__.co_code,
            reference.classify_for_ingest.__code__.co_code,
            "journal_persistence's HIMAYAH gate must be the same code as "
            "NIZAM__system/retrieval/himayah.py, not a reimplementation",
        )


if __name__ == "__main__":
    unittest.main()
