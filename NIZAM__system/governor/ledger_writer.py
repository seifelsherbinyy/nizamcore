"""ledger_writer.py - sole writer for NIZAM JSONL ledgers.

Implements hash-chained append-only writes. All other code calls
`append(ledger_name, payload, record_id=...)`; no other module opens
`.jsonl` files directly.

Crash semantics: each write is fsynced; partial-row mid-write is detected
on next startup via a tail integrity check (`verify_tail`).

Idempotency and concurrency (owner decision 2026-09-02, authorised by
`.kiro/steering/two-agent-vps.md` section 6a purpose 4 in the sibling
repository). Two correctness defects lived in this module, and every ledger
write in the system passes through it:

  1. No idempotency. `row_id` was a fresh `uuid4()` on every call, so an
     interrupted logical append that was retried produced a SECOND row with
     identical content and a cryptographically VALID chain. Neither
     `verify_tail` nor `verify_chain` could detect it, because a duplicate
     row IS a valid chain, and because the ledger is append-only the
     duplicate could not be removed without breaking the chain.
  2. Silent chain fork. `append` read the tail and then wrote with no lock,
     so two concurrent callers derived the same `prev_hash` and forked the
     chain mid-file. `verify_tail` could not see it because it rehashes only
     the last row in isolation; `verify_chain` then fails forever.

The fix, in the four parts that purpose 4 authorises:

  - `record_id` is a REQUIRED, keyword-only, caller-supplied stable identity.
    It has no default on purpose. A caller that has not been migrated raises
    `TypeError` at once rather than silently writing an un-deduplicated row,
    which is the whole point of making it required.
  - `payload_fingerprint` is a canonical SHA-256 over the record identity,
    the ledger name and the payload. The identity is INSIDE the hashed input
    so two different records can never collide into one another.
  - An existence check on `record_id` returns the already-written row instead
    of appending a second one. Nothing is ever overwritten or deleted; the
    append-only guarantee is absolute.
  - An advisory lock spans read-tail-and-append, so `prev_hash` cannot be
    derived by two writers at once. `poller.py` and `webhook.py` are separate
    entry points writing one ledger, so this is a live risk, not a theoretical
    one.

`row_id` remains a uuid4: it is the PHYSICAL row identifier that `trace.py`
and `relay/coordinator.py` already consume. `record_id` is the new LOGICAL
identity. On a replay the caller receives the original row, original
`row_id` included, because that is the row that actually exists.

Rows written before this change carry no `record_id` and no
`payload_fingerprint`. They still verify, because `_row_hash` hashes each
row's own body; the new fields only affect rows written from now on.

Pure stdlib (except optional `arc-protocol` for STRATEGY_LEDGER STH).
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Iterator

try:  # POSIX: the VPS, and the only platform that serves live traffic.
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    _fcntl = None  # type: ignore[assignment]

try:  # Windows: local verification only.
    import msvcrt as _msvcrt
except ImportError:  # pragma: no cover - exercised on POSIX
    _msvcrt = None  # type: ignore[assignment]

_DEFAULT_REPO = Path(__file__).resolve().parents[2]
_LEDGERS_DIR = _DEFAULT_REPO / "NIZAM__system" / "ledgers"

# Ledgers managed by this module.
KNOWN_LEDGERS = {
    "EVENT_LEDGER",
    "DECISION_LEDGER",
    "LEARNING_LEDGER",
    "DEAD_LETTER",
    "STRATEGY_LEDGER",
    "BATTLE_LEDGER",
    "FINANCE_LEDGER",
    "BODY_LEDGER",
    "FAMILY_LEDGER",
}

# Outcome of an append attempt, reported by `append_with_mode`.
MODE_APPENDED = "APPENDED"
MODE_REPLAYED = "REPLAYED"
MODE_REPLAYED_DIVERGENT = "REPLAYED_DIVERGENT"

# A record identity is an identifier, not a path and not free text. `:` is
# allowed so callers can namespace (`tg-update:1234`). Length is bounded so a
# record_id can never dominate the row it labels.
RECORD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
RECORD_ID_MAX_LEN = 200

# How long to wait for the advisory lock before giving up. A ledger append is
# milliseconds; anything approaching this bound is a stuck holder, and failing
# loudly beats writing without the lock.
LOCK_TIMEOUT_SECONDS = 30.0


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_hash(row: dict) -> str:
    body = {k: v for k, v in row.items() if k != "row_hash"}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _ledger_path(name: str, root: Path = _LEDGERS_DIR) -> Path:
    if name not in KNOWN_LEDGERS:
        raise ValueError(f"unknown ledger {name!r}; not in KNOWN_LEDGERS")
    return root / f"{name}.jsonl"


def _validate_record_id(record_id: str) -> str:
    """A record identity must be usable as a stable key, or refuse the write."""
    if not isinstance(record_id, str):
        raise ValueError(
            f"record_id must be a str, got {type(record_id).__name__}"
        )
    if not record_id:
        raise ValueError("record_id must not be empty")
    if len(record_id) > RECORD_ID_MAX_LEN:
        raise ValueError(
            f"record_id longer than {RECORD_ID_MAX_LEN} chars; "
            "it labels a row, it is not the row"
        )
    if not RECORD_ID_PATTERN.match(record_id):
        raise ValueError(
            f"record_id {record_id!r} is not an identifier; expected "
            f"{RECORD_ID_PATTERN.pattern}"
        )
    return record_id


def payload_fingerprint(name: str, record_id: str, payload: dict) -> str:
    """Canonical hash of what this record claims to say.

    The record identity is part of the hashed input, so two DIFFERENT records
    that happen to carry identical payloads produce different fingerprints and
    can never be mistaken for one another.
    """
    canonical = json.dumps(
        {"ledger": name, "record_id": record_id, "payload": payload},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _msvcrt_lock_blocking(fh: Any) -> None:  # pragma: no cover - Windows only
    """Block until the byte-range lock is ours, or time out.

    `msvcrt.LK_LOCK` gives up after roughly ten seconds of its own accord, so
    the retry loop is written here where the timeout is explicit.
    """
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fh.seek(0)
            _msvcrt.locking(fh.fileno(), _msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "timed out acquiring ledger lock after "
                    f"{LOCK_TIMEOUT_SECONDS}s; refusing to append unlocked"
                )
            time.sleep(0.01)


@contextlib.contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """Hold an exclusive advisory lock across read-tail-and-append.

    The lock lives on a sidecar `<LEDGER>.jsonl.lock` file, so taking it never
    opens, truncates or touches a single byte of the ledger itself. Both
    backends are OS-level locks bound to an open handle, so a crashed holder
    is released by the kernel; there is deliberately no stale-lock recovery
    path, because that is the part everyone gets wrong.
    """
    if _fcntl is None and _msvcrt is None:  # pragma: no cover
        raise RuntimeError(
            "no advisory lock backend on this platform; refusing to append, "
            "because appending unlocked is the defect this lock exists to fix"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    fh = lock_path.open("a+b")  # append mode: never truncates the lock file
    try:
        if _fcntl is not None:
            _fcntl.flock(fh.fileno(), _fcntl.LOCK_EX)
        else:
            _msvcrt_lock_blocking(fh)
        yield
    finally:
        try:
            if _fcntl is not None:
                _fcntl.flock(fh.fileno(), _fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows only
                fh.seek(0)
                _msvcrt.locking(fh.fileno(), _msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        fh.close()


def _last_row(path: Path) -> dict | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    last_line: str | None = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip()
            if line:
                last_line = line
    if last_line is None:
        return None
    return json.loads(last_line)


def _scan_for(path: Path, record_id: str) -> tuple[dict | None, dict | None]:
    """One pass returning (last_row, row_already_bearing_record_id).

    The tail is needed for `prev_hash` and the file has to be read anyway, so
    the existence check costs no extra pass and no extra memory: only the
    first matching row is retained, never a map of every identity seen.
    """
    if not path.exists() or path.stat().st_size == 0:
        return None, None
    last: dict | None = None
    found: dict | None = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip()
            if not line:
                continue
            row = json.loads(line)
            last = row
            if found is None and row.get("record_id") == record_id:
                found = row
    return last, found


def _tail_ok(last: dict | None) -> bool:
    if last is None:
        return True
    return last.get("row_hash") == _row_hash(last)


def verify_tail(name: str, root: Path = _LEDGERS_DIR) -> bool:
    """Verify the last row's hash chain. Returns True if clean."""
    return _tail_ok(_last_row(_ledger_path(name, root)))


def append_with_mode(
    name: str,
    payload: dict,
    *,
    record_id: str,
    actor: str = "Ammar",
    action: str = "append",
    module: str = "NIZAM__governor",
    privacy_class: str | None = None,
    trace_id: str | None = None,
    on_divergence: str = "replay",
    root: Path = _LEDGERS_DIR,
) -> tuple[dict[str, Any], str]:
    """Append a row idempotently. Returns (row, mode).

    `record_id` is the caller's stable identity for the logical record and is
    REQUIRED. If a row already carries it, that row is returned and NOTHING is
    appended, so a retried interrupted append can no longer produce a second
    row with a valid chain.

    mode is one of:
        MODE_APPENDED           a new row was written
        MODE_REPLAYED           the identity exists and the payload agrees
        MODE_REPLAYED_DIVERGENT the identity exists and the payload does not

    Divergence is reported rather than raised by default. A Telegram replay
    legitimately arrives with a fresh `trace_id` inside its payload, and
    taking the relay down over that would be worse than the duplicate this
    module exists to prevent. The divergence is still visible to the caller
    and, because the ledger is append-only, the FIRST row remains the record
    of what happened. Pass `on_divergence="refuse"` at call sites where
    reusing an identity is a genuine bug.

    Pre-conditions:
        - kill switch not armed (NIZAM_KILL_ALL != 1)
        - tail integrity holds, checked INSIDE the lock

    Caller MUST supply a sensible `privacy_class` for non-EVENT ledgers.
    """
    if os.environ.get("NIZAM_KILL_ALL") == "1":
        raise RuntimeError("NIZAM_KILL_ALL=1 - writer halted (HIMAYAH panic stop)")
    if on_divergence not in {"replay", "refuse"}:
        raise ValueError(
            f"on_divergence must be 'replay' or 'refuse', got {on_divergence!r}"
        )
    _validate_record_id(record_id)
    path = _ledger_path(name, root)

    if privacy_class is None:
        if name in {"EVENT_LEDGER", "LEARNING_LEDGER", "DECISION_LEDGER",
                    "DEAD_LETTER"}:
            privacy_class = "review_before_commit"
        elif name == "FAMILY_LEDGER":
            privacy_class = "strict_local_maximum"
        else:
            privacy_class = "strict_local"

    fingerprint = payload_fingerprint(name, record_id, payload)
    published_row: dict[str, Any] | None = None

    # Everything that reads the tail and everything that writes from it lives
    # inside one lock. This is the whole concurrency fix: two writers can no
    # longer derive the same prev_hash.
    with _exclusive_lock(path):
        last, existing = _scan_for(path, record_id)

        # Tail integrity is checked here, not before the lock. Checked outside,
        # another writer could append between the check and the write and the
        # check would have proved nothing.
        if not _tail_ok(last):
            raise RuntimeError(
                f"{name} tail integrity check failed; refusing append"
            )

        if existing is not None:
            if existing.get("payload_fingerprint") == fingerprint:
                return existing, MODE_REPLAYED
            if on_divergence == "refuse":
                raise RuntimeError(
                    f"record_id {record_id!r} already exists in {name} with a "
                    "different payload; refusing to append a second row under "
                    "one identity (append-only: the first row stands)"
                )
            return existing, MODE_REPLAYED_DIVERGENT

        prev_hash = last["row_hash"] if last else "0" * 64

        row = {
            "ts": _utc_now(),
            "ledger": name,
            "row_id": str(uuid.uuid4()),
            "record_id": record_id,
            "payload_fingerprint": fingerprint,
            "trace_id": trace_id or str(uuid.uuid4()),
            "actor": actor,
            "action": action,
            "module": module,
            "privacy_class": privacy_class,
            "prev_hash": prev_hash,
            "payload": payload,
        }
        row["row_hash"] = _row_hash(row)

        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                # Windows or non-disk file; best-effort
                pass
        published_row = row

    # E4.3 STRATEGY_LEDGER hardening: publish a Signed Tree Head on every
    # append. Failure must NOT block the append - STH publication is a
    # best-effort transparency layer. It runs OUTSIDE the lock: it only reads,
    # and calling into another module while holding the writer lock is how a
    # future change would deadlock this. A replay publishes nothing, because a
    # replay added no row to sign.
    if name == "STRATEGY_LEDGER":
        try:
            from . import strategy_sth
            strategy_sth.publish_sth()
        except Exception:
            pass

    assert published_row is not None  # a new row was written on this path
    return published_row, MODE_APPENDED


def append(
    name: str,
    payload: dict,
    *,
    record_id: str,
    actor: str = "Ammar",
    action: str = "append",
    module: str = "NIZAM__governor",
    privacy_class: str | None = None,
    trace_id: str | None = None,
    on_divergence: str = "replay",
    root: Path = _LEDGERS_DIR,
) -> dict[str, Any]:
    """Append a new row idempotently. Returns the row dict.

    Thin wrapper over `append_with_mode` for callers that only need the row.
    On a replay the row returned is the one already on disk, so
    `row["row_id"]` is stable across retries.
    """
    row, _mode = append_with_mode(
        name,
        payload,
        record_id=record_id,
        actor=actor,
        action=action,
        module=module,
        privacy_class=privacy_class,
        trace_id=trace_id,
        on_divergence=on_divergence,
        root=root,
    )
    return row


def tail_rows(name: str, n: int = 10, root: Path = _LEDGERS_DIR) -> list[dict]:
    """Return the last n rows for inspection / Khaldun synthesis."""
    path = _ledger_path(name, root)
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip()
            if line:
                rows.append(json.loads(line))
    return rows[-n:]


def verify_chain(name: str, root: Path = _LEDGERS_DIR) -> tuple[bool, int, str | None]:
    """Verify the full hash chain of a ledger.

    Returns (ok, rows_checked, broken_row_id-or-None).
    """
    path = _ledger_path(name, root)
    if not path.exists():
        return True, 0, None
    prev_hash = "0" * 64
    n = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("prev_hash") != prev_hash:
                return False, n, row.get("row_id")
            expected = _row_hash(row)
            if row.get("row_hash") != expected:
                return False, n, row.get("row_id")
            prev_hash = row["row_hash"]
            n += 1
    return True, n, None


def duplicate_record_ids(name: str, root: Path = _LEDGERS_DIR) -> list[str]:
    """Report record_ids appearing on more than one row.

    A duplicate is a VALID chain, so `verify_chain` cannot surface one. This
    is the detector that was missing. Rows predating the idempotency change
    carry no `record_id` and are skipped rather than reported, because their
    absence of an identity is history, not a fault.
    """
    path = _ledger_path(name, root)
    if not path.exists():
        return []
    seen: set[str] = set()
    dupes: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip()
            if not line:
                continue
            rid = json.loads(line).get("record_id")
            if not rid:
                continue
            if rid in seen and rid not in dupes:
                dupes.append(rid)
            seen.add(rid)
    return dupes


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: ledger_writer.py verify <LEDGER_NAME>")
        sys.exit(2)
    if sys.argv[1] == "verify" and len(sys.argv) >= 3:
        name = sys.argv[2]
        ok, n, broken = verify_chain(name)
        dupes = duplicate_record_ids(name)
        print(f"{name}: ok={ok} rows={n} broken_row={broken} "
              f"duplicate_record_ids={dupes or None}")
        sys.exit(0 if (ok and not dupes) else 1)
