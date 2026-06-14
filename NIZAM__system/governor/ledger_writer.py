"""ledger_writer.py — sole writer for NIZAM JSONL ledgers.

Implements hash-chained append-only writes. All other code calls
`append(ledger_name, payload)`; no other module opens `.jsonl` files
directly.

Crash semantics: each write is fsynced; partial-row mid-write is detected
on next startup via a tail integrity check (`verify_tail`).

STRATEGY_LEDGER additionally publishes an RFC 6962 Signed Tree Head when
`arc-protocol` is importable. Until then, hash-chain only.

Pure stdlib (except optional `arc-protocol` for STRATEGY_LEDGER STH).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

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
    "PULSATION_LEDGER",
    "COUNCIL_LEDGER",
    "CAREER_RADAR_LEDGER",  # TARIQ Career Radar run log
}


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


def verify_tail(name: str, root: Path = _LEDGERS_DIR) -> bool:
    """Verify the last row's hash chain. Returns True if clean."""
    last = _last_row(_ledger_path(name, root))
    if last is None:
        return True
    expected = _row_hash(last)
    return last.get("row_hash") == expected


def append(
    name: str,
    payload: dict,
    *,
    actor: str = "Ammar",
    action: str = "append",
    module: str = "NIZAM__governor",
    privacy_class: str | None = None,
    trace_id: str | None = None,
    root: Path = _LEDGERS_DIR,
) -> dict[str, Any]:
    """Append a new row. Returns the written row dict.

    Pre-conditions:
        - kill switch not armed (NIZAM_KILL_ALL != 1)
        - tail integrity holds (`verify_tail(name)`)

    Caller MUST supply a sensible `privacy_class` for non-EVENT ledgers.
    """
    if os.environ.get("NIZAM_KILL_ALL") == "1":
        raise RuntimeError("NIZAM_KILL_ALL=1 — writer halted (HIMAYAH panic stop)")
    if not verify_tail(name, root):
        raise RuntimeError(f"{name} tail integrity check failed; refusing append")

    if privacy_class is None:
        if name in {"EVENT_LEDGER", "LEARNING_LEDGER", "DECISION_LEDGER",
                    "DEAD_LETTER"}:
            privacy_class = "review_before_commit"
        else:
            privacy_class = "strict_local"

    path = _ledger_path(name, root)
    last = _last_row(path)
    prev_hash = last["row_hash"] if last else "0" * 64

    row = {
        "ts": _utc_now(),
        "ledger": name,
        "row_id": str(uuid.uuid4()),
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            # Windows or non-disk file; best-effort
            pass

    # E4.3 STRATEGY_LEDGER hardening: publish a Signed Tree Head on
    # every append. Failure must NOT block the append — STH publication
    # is a best-effort transparency layer.
    if name == "STRATEGY_LEDGER":
        try:
            from . import strategy_sth
            strategy_sth.publish_sth()
        except Exception:
            pass

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


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: ledger_writer.py verify <LEDGER_NAME>")
        sys.exit(2)
    if sys.argv[1] == "verify" and len(sys.argv) >= 3:
        ok, n, broken = verify_chain(sys.argv[2])
        print(f"{sys.argv[2]}: ok={ok} rows={n} broken_row={broken}")
        sys.exit(0 if ok else 1)
