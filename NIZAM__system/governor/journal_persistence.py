"""journal_persistence.py - YAWMIYAT journal entry persistence orchestrator.

Derives every behaviour below from sources already in force in this
repository or the finance repository; it invents no new policy:

  - Path/layout: YAWMIYAT__journaling/_index.json and README.md (this repo).
    Phase 2, matching _index.json's own "phase": 2.
  - THABAT (exactly-once ledger): NIZAM__system/governor/ledger_writer.py is
    the sole writer for NIZAM JSONL ledgers. This module calls
    ledger_writer.append_with_mode() exactly as any other caller must; it
    never opens a ledger file directly. There is no dedicated journal
    ledger in ledger_writer.KNOWN_LEDGERS, so this module reuses
    EVENT_LEDGER (module="YAWMIYAT") rather than inventing a new ledger.
  - HIMAYAH (privacy classification): NIZAM__system/retrieval/himayah.py
    already hard-blocks the "YAWMIYAT__journaling" prefix from leaving this
    host (_HARD_BLOCK_PREFIXES). This module reuses
    himayah.classify_for_ingest() verbatim as the gate in front of any
    external-mirror step. A HimayahViolation there is the CORRECT, EXPECTED
    outcome for journal content - it is not routed around, caught-and-
    retried, or treated as a defect.
  - Host-write boundary: ops/hermes/WORKSPACE_MOUNT.md (finance repo)
    forbids "raw YAWMIYAT / TAFRIGH session bodies into embeddings or
    Drive" - consistent with the HIMAYAH hard block above.

State machine per entry (terminal states in CAPS):

    STAGED -> LOCAL_WRITE_OK -> READBACK_OK -> LEDGERED -> DRIVE_MIRROR_REFUSED

DRIVE_MIRROR_REFUSED is the correct terminal state for strict_local content.
It means HIMAYAH did its job, not that the mirror step is broken.

All writes are atomic (write to a sibling temp file, fsync, os.replace) and
idempotent: re-running persist_journal_entry() for the same filename_stem
overwrites the same two files byte-for-byte (or leaves them unchanged) and
the ledger append for the same record_id replays rather than duplicating
(ledger_writer's own MODE_REPLAYED / MODE_REPLAYED_DIVERGENT contract).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from NIZAM__system.governor import ledger_writer as lw  # noqa: E402

# himayah.py loads classifier.py via importlib.util itself, so a direct
# module-path load here (rather than a package import) avoids any
# dependency on NIZAM__system.retrieval being a fully-initialised package
# in every caller context. This mirrors how himayah.py loads classifier.py.
_HIMAYAH_PATH = _REPO_ROOT / "NIZAM__system" / "retrieval" / "himayah.py"
_himayah_spec = importlib.util.spec_from_file_location("_journal_himayah", _HIMAYAH_PATH)
_himayah = importlib.util.module_from_spec(_himayah_spec)
_himayah_spec.loader.exec_module(_himayah)

HimayahViolation = _himayah.HimayahViolation
classify_for_ingest = _himayah.classify_for_ingest

JOURNAL_LEDGER = "EVENT_LEDGER"
JOURNAL_MODULE = "YAWMIYAT"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    """Write content to path atomically: tmp file in the same dir, fsync, replace.

    Survives a crash mid-write: either the old file or the new file is on
    disk afterwards, never a half-written one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def read_back_verify(path: Path, expected_content: str) -> bool:
    """Independently re-read path and hash-compare against expected_content."""
    if not path.exists():
        return False
    actual = path.read_text(encoding="utf-8")
    return _sha256_text(actual) == _sha256_text(expected_content)


def persist_journal_entry(
    *,
    filename_stem: str,
    session_payload: dict[str, Any],
    mirror_markdown: str | None,
    yawmiyat_root: Path,
    ledger_root: Path = lw._LEDGERS_DIR,
    actor: str = "Ammar",
) -> dict[str, Any]:
    """Persist one YAWMIYAT session record end-to-end.

    filename_stem must already be in the "{YYYY-MM-DD}T{HH-MM-SS}Z__{type}"
    shape from YAWMIYAT__journaling/README.md; this function does not
    invent or reformat it.

    Idempotent: calling this twice with the same filename_stem and the same
    session_payload/mirror_markdown produces the same files and a single
    ledger row (mode MODE_REPLAYED on the second call).
    """
    result: dict[str, Any] = {"filename_stem": filename_stem, "state": "STAGED"}

    sessions_dir = yawmiyat_root / "sessions"
    mirrors_dir = yawmiyat_root / "mirrors"

    session_path = sessions_dir / f"{filename_stem}.json"
    session_text = json.dumps(session_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    atomic_write_text(session_path, session_text)
    if not read_back_verify(session_path, session_text):
        result["state"] = "READBACK_FAILED"
        result["failed_path"] = str(session_path)
        return result
    result["session_path"] = str(session_path)

    if mirror_markdown is not None:
        mirror_path = mirrors_dir / f"{filename_stem}.md"
        atomic_write_text(mirror_path, mirror_markdown)
        if not read_back_verify(mirror_path, mirror_markdown):
            result["state"] = "READBACK_FAILED"
            result["failed_path"] = str(mirror_path)
            return result
        result["mirror_path"] = str(mirror_path)

    result["state"] = "READBACK_OK"

    record_id = f"yawmiyat:{filename_stem}"
    payload = {
        "kind": "journal_entry_persisted",
        "filename_stem": filename_stem,
        "session_sha256": _sha256_text(session_text),
    }
    row, mode = lw.append_with_mode(
        JOURNAL_LEDGER,
        payload,
        record_id=record_id,
        actor=actor,
        action="journal_entry_persisted",
        module=JOURNAL_MODULE,
        privacy_class="strict_local",
        root=ledger_root,
    )
    result["ledger_mode"] = mode
    result["ledger_row"] = row
    result["state"] = "LEDGERED"

    rel_path = f"YAWMIYAT__journaling/sessions/{filename_stem}.json"
    try:
        cls = classify_for_ingest(rel_path)
        # Reaching here for YAWMIYAT content would mean HIMAYAH's hard block
        # regressed. Surface it loudly rather than proceeding to a mirror.
        result["state"] = "HIMAYAH_UNEXPECTEDLY_PERMITTED"
        result["classification"] = cls
    except HimayahViolation as e:
        result["state"] = "DRIVE_MIRROR_REFUSED"
        result["himayah_refusal_reason"] = str(e)

    return result


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recover_staged_records(
    *,
    staging_dir: Path,
    yawmiyat_root: Path,
    ledger_root: Path = lw._LEDGERS_DIR,
    actor: str = "Ammar",
) -> dict[str, Any]:
    """Recover journal records staged outside the real host path (for
    example while nizamcore was mounted read-only) without duplication.

    Any staged file whose content is byte-identical (sha256) to a session
    file already being recovered is treated as a duplicate write-retry
    artifact and discarded, not filed as a second record.
    """
    sessions_src = staging_dir / "sessions"
    mirrors_src = staging_dir / "mirrors"

    recovered: list[dict[str, Any]] = []
    discarded_duplicates: list[str] = []
    seen_hashes: dict[str, str] = {}

    session_files = sorted(sessions_src.glob("*.json")) if sessions_src.exists() else []

    for session_file in session_files:
        digest = sha256_file(session_file)
        if digest in seen_hashes:
            discarded_duplicates.append(str(session_file))
            continue
        seen_hashes[digest] = str(session_file)

        filename_stem = session_file.stem
        session_payload = json.loads(session_file.read_text(encoding="utf-8"))

        mirror_file = mirrors_src / f"{filename_stem}.md"
        mirror_markdown = mirror_file.read_text(encoding="utf-8") if mirror_file.exists() else None

        outcome = persist_journal_entry(
            filename_stem=filename_stem,
            session_payload=session_payload,
            mirror_markdown=mirror_markdown,
            yawmiyat_root=yawmiyat_root,
            ledger_root=ledger_root,
            actor=actor,
        )
        recovered.append(outcome)

    # Any other file directly under staging_dir (e.g. a mis-filed duplicate
    # like a stray "books.json") that matches an already-recovered session's
    # hash is a duplicate artifact too, even though it never lived in
    # sessions/. Report it; do not file it as a new record.
    for stray in sorted(staging_dir.glob("*.json")):
        digest = sha256_file(stray)
        if digest in seen_hashes:
            discarded_duplicates.append(str(stray))

    return {"recovered": recovered, "discarded_duplicates": discarded_duplicates}
