"""test_ledger_writer_idempotency.py - proof tests for the two ledger defects.

Covers the fix authorised by `.kiro/steering/two-agent-vps.md` section 6a
purpose 4 (owner decision 2026-09-02):

  1. A retried logical append produced a SECOND row with identical content and
     a cryptographically VALID chain, which neither `verify_tail` nor
     `verify_chain` could detect.
  2. `append` read the tail and wrote with no lock, so two concurrent writers
     derived the same `prev_hash` and forked the chain. `poller.py` and
     `webhook.py` are separate entry points writing one ledger, so this was a
     live risk.

Every test writes to a temporary `root=`; the real ledgers directory is never
touched.

Run with:
    .venv\\Scripts\\python.exe -m unittest NIZAM__system.governor.tests.test_ledger_writer_idempotency
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import ledger_writer as lw  # noqa: E402


LEDGER = "EVENT_LEDGER"


def _rows(root: Path, name: str = LEDGER) -> list[dict]:
    path = root / f"{name}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _legacy_append(root: Path, payload: dict, name: str = LEDGER) -> dict:
    """The writer as it behaved BEFORE the fix, reproduced exactly.

    Fresh uuid4 row_id per call, no record identity, no existence check, no
    lock. Kept in the test rather than in git history so the defect this
    module fixes stays legible.
    """
    path = root / f"{name}.jsonl"
    last = lw._last_row(path)
    row = {
        "ts": lw._utc_now(),
        "ledger": name,
        "row_id": str(uuid.uuid4()),
        "trace_id": str(uuid.uuid4()),
        "actor": "Ammar",
        "action": "append",
        "module": "NIZAM__governor",
        "privacy_class": "review_before_commit",
        "prev_hash": last["row_hash"] if last else "0" * 64,
        "payload": payload,
    }
    row["row_hash"] = lw._row_hash(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


class LedgerTempRoot(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="nizam-ledger-"))
        self.addCleanup(shutil.rmtree, self.root, True)


class TheDefectBeingFixed(LedgerTempRoot):
    """Side-by-side: the old writer forks, the new writer does not."""

    def test_legacy_retry_writes_two_rows_and_the_chain_still_verifies(self) -> None:
        payload = {"kind": "turn", "note": "one logical event"}
        _legacy_append(self.root, payload)
        _legacy_append(self.root, payload)   # the interrupted append, retried

        self.assertEqual(len(_rows(self.root)), 2,
                         "legacy behaviour: one logical event, two rows")
        ok, n, broken = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok, "the duplicate IS a valid chain")
        self.assertEqual(n, 2)
        self.assertIsNone(broken)
        self.assertTrue(lw.verify_tail(LEDGER, root=self.root),
                        "verify_tail cannot see a duplicate either")

    def test_fixed_retry_writes_one_row(self) -> None:
        payload = {"kind": "turn", "note": "one logical event"}
        first, mode1 = lw.append_with_mode(
            LEDGER, payload, record_id="tg-update:9001", root=self.root)
        second, mode2 = lw.append_with_mode(
            LEDGER, payload, record_id="tg-update:9001", root=self.root)

        self.assertEqual(mode1, lw.MODE_APPENDED)
        self.assertEqual(mode2, lw.MODE_REPLAYED)
        self.assertEqual(len(_rows(self.root)), 1,
                         "one logical event, exactly one row")
        self.assertEqual(first["row_id"], second["row_id"],
                         "a replay returns the row that already exists")
        ok, n, _ = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok)
        self.assertEqual(n, 1)


class IdempotencyOnRecordId(LedgerTempRoot):

    def test_identity_not_content_is_what_deduplicates(self) -> None:
        payload = {"same": "content"}
        lw.append(LEDGER, payload, record_id="a-1", root=self.root)
        lw.append(LEDGER, payload, record_id="a-2", root=self.root)
        self.assertEqual(len(_rows(self.root)), 2,
                         "two distinct records may legitimately agree in full")

    def test_distinct_records_are_all_kept(self) -> None:
        for i in range(5):
            lw.append(LEDGER, {"i": i}, record_id=f"r-{i}", root=self.root)
        self.assertEqual(len(_rows(self.root)), 5)
        ok, n, _ = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok)
        self.assertEqual(n, 5)

    def test_replay_is_stable_across_many_retries(self) -> None:
        row = lw.append(LEDGER, {"k": 1}, record_id="stable", root=self.root)
        for _ in range(4):
            again = lw.append(LEDGER, {"k": 1}, record_id="stable",
                              root=self.root)
            self.assertEqual(again["row_id"], row["row_id"])
            self.assertEqual(again["ts"], row["ts"],
                             "the original timestamp is what happened")
        self.assertEqual(len(_rows(self.root)), 1)

    def test_fingerprint_binds_the_payload_to_its_identity(self) -> None:
        payload = {"same": "content"}
        self.assertNotEqual(
            lw.payload_fingerprint(LEDGER, "a-1", payload),
            lw.payload_fingerprint(LEDGER, "a-2", payload),
            "identity is inside the hash so two records cannot merge")

    def test_fingerprint_is_stored_on_the_row(self) -> None:
        row = lw.append(LEDGER, {"k": 1}, record_id="fp", root=self.root)
        self.assertEqual(row["payload_fingerprint"],
                         lw.payload_fingerprint(LEDGER, "fp", {"k": 1}))
        self.assertEqual(len(row["payload_fingerprint"]), 64)


class DivergenceUnderOneIdentity(LedgerTempRoot):

    def test_divergent_payload_still_appends_nothing(self) -> None:
        first, _ = lw.append_with_mode(LEDGER, {"trace": "attempt-1"},
                                       record_id="d-1", root=self.root)
        second, mode = lw.append_with_mode(LEDGER, {"trace": "attempt-2"},
                                           record_id="d-1", root=self.root)
        self.assertEqual(mode, lw.MODE_REPLAYED_DIVERGENT)
        self.assertEqual(len(_rows(self.root)), 1)
        self.assertEqual(second["row_id"], first["row_id"])
        self.assertEqual(second["payload"], {"trace": "attempt-1"},
                         "append-only: the first row remains the record")

    def test_divergence_can_be_refused_where_reuse_is_a_bug(self) -> None:
        lw.append(LEDGER, {"v": 1}, record_id="d-2", root=self.root)
        with self.assertRaises(RuntimeError) as ctx:
            lw.append(LEDGER, {"v": 2}, record_id="d-2",
                      on_divergence="refuse", root=self.root)
        self.assertIn("already exists", str(ctx.exception))
        self.assertEqual(len(_rows(self.root)), 1)

    def test_unknown_divergence_policy_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lw.append(LEDGER, {"v": 1}, record_id="d-3",
                      on_divergence="overwrite", root=self.root)


class RecordIdIsRequiredAndValidated(LedgerTempRoot):

    def test_omitting_record_id_is_a_loud_failure(self) -> None:
        with self.assertRaises(TypeError):
            lw.append(LEDGER, {"k": 1}, root=self.root)  # type: ignore[call-arg]
        self.assertEqual(_rows(self.root), [],
                         "an unmigrated caller writes nothing at all")

    def test_empty_and_oversized_and_wrong_type_are_refused(self) -> None:
        for bad in ["", "x" * (lw.RECORD_ID_MAX_LEN + 1)]:
            with self.assertRaises(ValueError):
                lw.append(LEDGER, {"k": 1}, record_id=bad, root=self.root)
        for bad_type in [None, 17, {"a": 1}]:
            with self.assertRaises(ValueError):
                lw.append(LEDGER, {"k": 1}, record_id=bad_type,  # type: ignore[arg-type]
                          root=self.root)

    def test_path_shaped_identities_are_refused(self) -> None:
        for bad in ["../escape", "a/b", "a\\b", ".hidden", "has space",
                    "new\nline"]:
            with self.assertRaises(ValueError):
                lw.append(LEDGER, {"k": 1}, record_id=bad, root=self.root)
        self.assertEqual(_rows(self.root), [])

    def test_namespaced_identities_are_accepted(self) -> None:
        for good in ["tg-update:1234", "sess_1.2", "A-b.C:9"]:
            lw.append(LEDGER, {"k": good}, record_id=good, root=self.root)
        self.assertEqual(len(_rows(self.root)), 3)


class ConcurrencyDoesNotForkTheChain(LedgerTempRoot):

    def test_critical_sections_do_not_overlap(self) -> None:
        """Mutual exclusion, proved directly rather than raced for."""
        path = self.root / f"{LEDGER}.jsonl"
        spans: list[tuple[float, float]] = []
        guard = threading.Lock()

        def hold() -> None:
            with lw._exclusive_lock(path):
                t0 = time.monotonic()
                time.sleep(0.02)
                t1 = time.monotonic()
                with guard:
                    spans.append((t0, t1))

        threads = [threading.Thread(target=hold) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(spans), 4)
        spans.sort()
        for (_, end), (start, _) in zip(spans, spans[1:]):
            self.assertLessEqual(end, start + 1e-6,
                                 "two writers held the ledger lock at once")

    def test_concurrent_appends_keep_one_valid_chain(self) -> None:
        n = 12
        errors: list[BaseException] = []

        def writer(i: int) -> None:
            try:
                lw.append(LEDGER, {"i": i}, record_id=f"c-{i}", root=self.root)
            except BaseException as exc:  # noqa: BLE001 - reported, not hidden
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        rows = _rows(self.root)
        self.assertEqual(len(rows), n, "every distinct record landed")
        ok, checked, broken = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok, f"chain forked at {broken}")
        self.assertEqual(checked, n)
        self.assertEqual(len({r["prev_hash"] for r in rows}), n,
                         "no two rows derived the same prev_hash")

    def test_concurrent_retries_of_one_identity_still_write_one_row(self) -> None:
        payload = {"one": "event"}
        seen: list[str] = []
        guard = threading.Lock()

        def retry() -> None:
            row = lw.append(LEDGER, payload, record_id="race-1", root=self.root)
            with guard:
                seen.append(row["row_id"])

        threads = [threading.Thread(target=retry) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(_rows(self.root)), 1,
                         "eight simultaneous retries, one row")
        self.assertEqual(len(set(seen)), 1,
                         "every caller was told about the same row")

    def test_a_lock_backend_is_present(self) -> None:
        self.assertTrue(lw._fcntl is not None or lw._msvcrt is not None,
                        "appending unlocked is the defect; there is no "
                        "no-op fallback")


class DuplicateDetection(LedgerTempRoot):

    def _write_valid_chain_with_a_duplicate(self) -> None:
        """Hand-build two rows sharing one record_id and a VALID chain."""
        path = self.root / f"{LEDGER}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        prev = "0" * 64
        with path.open("w", encoding="utf-8") as fh:
            for _ in range(2):
                row = {
                    "ts": lw._utc_now(),
                    "ledger": LEDGER,
                    "row_id": str(uuid.uuid4()),
                    "record_id": "dupe-1",
                    "payload_fingerprint": lw.payload_fingerprint(
                        LEDGER, "dupe-1", {"k": 1}),
                    "trace_id": str(uuid.uuid4()),
                    "actor": "Ammar",
                    "action": "append",
                    "module": "NIZAM__governor",
                    "privacy_class": "review_before_commit",
                    "prev_hash": prev,
                    "payload": {"k": 1},
                }
                row["row_hash"] = lw._row_hash(row)
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True)
                         + "\n")
                prev = row["row_hash"]

    def test_verify_chain_cannot_see_a_duplicate_but_the_detector_can(self) -> None:
        self._write_valid_chain_with_a_duplicate()
        ok, n, _ = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok, "a duplicate is a cryptographically valid chain")
        self.assertEqual(n, 2)
        self.assertEqual(lw.duplicate_record_ids(LEDGER, root=self.root),
                         ["dupe-1"],
                         "this is the detector verify_chain cannot be")

    def test_clean_ledger_reports_no_duplicates(self) -> None:
        for i in range(3):
            lw.append(LEDGER, {"i": i}, record_id=f"u-{i}", root=self.root)
        self.assertEqual(lw.duplicate_record_ids(LEDGER, root=self.root), [])

    def test_missing_ledger_file_is_not_an_error(self) -> None:
        self.assertEqual(lw.duplicate_record_ids(LEDGER, root=self.root), [])


class BackwardCompatibility(LedgerTempRoot):
    """Rows written before the fix carry no identity. They must still work."""

    def test_legacy_rows_verify_and_accept_a_new_row_after_them(self) -> None:
        _legacy_append(self.root, {"old": 1})
        _legacy_append(self.root, {"old": 2})
        ok, n, _ = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok)
        self.assertEqual(n, 2)

        lw.append(LEDGER, {"new": 3}, record_id="new-3", root=self.root)
        ok, n, broken = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok, f"chain broke at {broken} across the schema change")
        self.assertEqual(n, 3)

    def test_legacy_rows_are_not_reported_as_duplicates(self) -> None:
        _legacy_append(self.root, {"old": 1})
        _legacy_append(self.root, {"old": 1})
        self.assertEqual(lw.duplicate_record_ids(LEDGER, root=self.root), [],
                         "no identity is history, not a fault")

    def test_a_legacy_identity_free_row_does_not_satisfy_a_new_record_id(self) -> None:
        _legacy_append(self.root, {"k": 1})
        row, mode = lw.append_with_mode(LEDGER, {"k": 1}, record_id="k-1",
                                        root=self.root)
        self.assertEqual(mode, lw.MODE_APPENDED)
        self.assertEqual(len(_rows(self.root)), 2)
        self.assertEqual(row["record_id"], "k-1")


class PreconditionsStillHold(LedgerTempRoot):

    def test_kill_switch_halts_the_writer(self) -> None:
        import os
        os.environ["NIZAM_KILL_ALL"] = "1"
        try:
            with self.assertRaises(RuntimeError) as ctx:
                lw.append(LEDGER, {"k": 1}, record_id="ks-1", root=self.root)
            self.assertIn("NIZAM_KILL_ALL", str(ctx.exception))
        finally:
            del os.environ["NIZAM_KILL_ALL"]
        self.assertEqual(_rows(self.root), [])

    def test_unknown_ledger_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            lw.append("NOT_A_LEDGER", {"k": 1}, record_id="x-1",
                      root=self.root)

    def test_broken_tail_refuses_the_append(self) -> None:
        lw.append(LEDGER, {"k": 1}, record_id="t-1", root=self.root)
        path = self.root / f"{LEDGER}.jsonl"
        rows = _rows(self.root)
        rows[-1]["payload"] = {"k": "tampered"}
        path.write_text(
            json.dumps(rows[-1], ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8")
        with self.assertRaises(RuntimeError) as ctx:
            lw.append(LEDGER, {"k": 2}, record_id="t-2", root=self.root)
        self.assertIn("tail integrity", str(ctx.exception))

    def test_privacy_class_defaults_are_unchanged(self) -> None:
        row = lw.append(LEDGER, {"k": 1}, record_id="p-1", root=self.root)
        self.assertEqual(row["privacy_class"], "review_before_commit")
        row = lw.append("FAMILY_LEDGER", {"k": 1}, record_id="p-2",
                        root=self.root)
        self.assertEqual(row["privacy_class"], "strict_local_maximum")
        row = lw.append("BODY_LEDGER", {"k": 1}, record_id="p-3",
                        root=self.root)
        self.assertEqual(row["privacy_class"], "strict_local")

    def test_the_lock_file_never_becomes_a_ledger_row(self) -> None:
        lw.append(LEDGER, {"k": 1}, record_id="l-1", root=self.root)
        self.assertTrue((self.root / f"{LEDGER}.jsonl.lock").exists())
        self.assertEqual(len(_rows(self.root)), 1)
        ok, _, _ = lw.verify_chain(LEDGER, root=self.root)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
