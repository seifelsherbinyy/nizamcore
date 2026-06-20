#!/usr/bin/env python3
"""Initialize NIZAM ledger JSONL files with bootstrap rows.

Run once at repo init. Idempotent: if a ledger already has rows, do nothing.

Tasks: G13.2 EVENT_LEDGER, G13.3 LEARNING_LEDGER, G13.4 DEAD_LETTER,
G13.5 STRATEGY_LEDGER (hash-chained pre-Merkle; arc-protocol upgrade at E4.3).

Pure stdlib. No egress.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import uuid
from pathlib import Path

LEDGERS_DIR = Path(__file__).resolve().parents[1] / "NIZAM__system" / "ledgers"


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_row(row: dict) -> str:
    body = {k: v for k, v in row.items() if k != "row_hash"}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _bootstrap_row(ledger: str, payload: dict) -> dict:
    row = {
        "ts": _utc_now(),
        "ledger": ledger,
        "row_id": str(uuid.uuid4()),
        "trace_id": "bootstrap",
        "actor": "Ammar",
        "action": "ledger_bootstrap",
        "module": "NIZAM__governor",
        "privacy_class": "review_before_commit"
        if ledger in {"EVENT_LEDGER", "LEARNING_LEDGER"}
        else "strict_local",
        "prev_hash": "0" * 64,
        "payload": payload,
    }
    row["row_hash"] = _hash_row(row)
    return row


def _init(name: str, payload: dict) -> bool:
    path = LEDGERS_DIR / f"{name}.jsonl"
    if path.exists() and path.stat().st_size > 0:
        print(f"  SKIP (exists, non-empty): {name}.jsonl")
        return False
    LEDGERS_DIR.mkdir(parents=True, exist_ok=True)
    row = _bootstrap_row(name, payload)
    path.write_text(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"  INIT: {name}.jsonl (row_id={row['row_id'][:8]}..., "
          f"row_hash={row['row_hash'][:12]}...)")
    return True


def main() -> int:
    print("[G13] Ledger bootstrap")
    _init("EVENT_LEDGER", {
        "note": "EVENT_LEDGER bootstrap — operational + recovery anchor",
        "spec": "NIZAM__system/ledgers/README.md",
    })
    _init("LEARNING_LEDGER", {
        "note": "LEARNING_LEDGER bootstrap — Salman/Khaldun feedback loop",
        "spec": "NIZAM__system/ledgers/README.md",
    })
    _init("DEAD_LETTER", {
        "note": "DEAD_LETTER bootstrap — failed/dropped messages for replay",
        "spec": "NIZAM__system/ledgers/README.md",
        "schema": {
            "required": ["original_row", "failure_reason",
                          "first_attempted_at", "retry_count"],
            "max_attempts": 3,
            "replay_mode": "manual_approval_required",
            "owner": "Ammar",
        },
    })
    _init("STRATEGY_LEDGER", {
        "note": ("STRATEGY_LEDGER bootstrap — hash-chained; "
                 "Merkle/Ed25519 STH wired at E4.3 via arc-protocol."),
        "spec": "NIZAM__system/ledgers/README.md",
        "merkle_lib_decision": "arc-protocol (default); merkletools fallback",
        "ed25519_decision": "cryptography.hazmat.primitives.asymmetric.ed25519",
        "sth_publication": "every-append + periodic-10min via systemd timer",
    })
    _init("PULSATION_LEDGER", {
        "note": "PULSATION_LEDGER bootstrap — proactive companion + reminder sends",
        "spec": "NIZAM__system/schemas/pulsation_message.schema.json",
    })
    _init("COUNCIL_LEDGER", {
        "note": "COUNCIL_LEDGER bootstrap — council deliberation verdicts",
        "spec": "NIZAM__system/companion/council/",
    })
    print("[G13] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
