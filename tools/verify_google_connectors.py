#!/usr/bin/env python3
"""Verify Google Calendar, Tasks, and Gmail connectors (read + optional write smoke)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.companion.calendar_tasks import (  # noqa: E402
    Approval,
    ApprovalStore,
    execute,
    operation_hash,
)
from NIZAM__system.companion.contracts import ConnectorOperation  # noqa: E402
from NIZAM__system.connectors import google_oauth  # noqa: E402
from NIZAM__system.connectors.google_adapter import build_google_adapter  # noqa: E402
from NIZAM__system.relay import env_loader  # noqa: E402


def utc_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_write_smoke() -> dict:
    adapter = build_google_adapter()
    store = ApprovalStore()
    results: dict[str, object] = {}
    tag = f"NIZAM_SMOKE_{utc_tag()}"

    # Calendar create + delete
    cal_start = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cal_end = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cal_op = ConnectorOperation(
        connector="google_calendar",
        capability="create_event",
        mode="execute_write",
        idempotency_key=f"smoke-cal-{tag}",
        approval_id=str(uuid.uuid4()),
        payload={"title": tag, "start": cal_start, "end": cal_end},
    )
    store.grant(
        Approval(
            str(cal_op.approval_id),
            operation_hash(cal_op),
            datetime.now(timezone.utc) + timedelta(minutes=5),
        )
    )
    cal_created = execute(cal_op, adapter=adapter, approvals=store)
    event_id = cal_created["written"]["id"]
    del_op = ConnectorOperation(
        connector="google_calendar",
        capability="delete_event",
        mode="execute_write",
        idempotency_key=f"smoke-cal-del-{tag}",
        approval_id=str(uuid.uuid4()),
        payload={"event_id": event_id},
    )
    store.grant(
        Approval(
            str(del_op.approval_id),
            operation_hash(del_op),
            datetime.now(timezone.utc) + timedelta(minutes=5),
        )
    )
    execute(del_op, adapter=adapter, approvals=store)
    results["calendar"] = {"ok": True, "event_id": event_id}

    # Tasks create + delete
    task_op = ConnectorOperation(
        connector="google_tasks",
        capability="create_task",
        mode="execute_write",
        idempotency_key=f"smoke-task-{tag}",
        approval_id=str(uuid.uuid4()),
        payload={"title": tag},
    )
    store.grant(
        Approval(
            str(task_op.approval_id),
            operation_hash(task_op),
            datetime.now(timezone.utc) + timedelta(minutes=5),
        )
    )
    task_created = execute(task_op, adapter=adapter, approvals=store)
    task_id = task_created["written"]["id"]
    tasklist_id = task_created["written"]["tasklist_id"]
    task_del = ConnectorOperation(
        connector="google_tasks",
        capability="delete_task",
        mode="execute_write",
        idempotency_key=f"smoke-task-del-{tag}",
        approval_id=str(uuid.uuid4()),
        payload={"task_id": task_id, "tasklist_id": tasklist_id},
    )
    store.grant(
        Approval(
            str(task_del.approval_id),
            operation_hash(task_del),
            datetime.now(timezone.utc) + timedelta(minutes=5),
        )
    )
    execute(task_del, adapter=adapter, approvals=store)
    results["tasks"] = {"ok": True, "task_id": task_id}

    # Gmail trash/untrash optional
    smoke_msg = os.environ.get("NIZAM_GMAIL_SMOKE_MESSAGE_ID", "").strip()
    if smoke_msg:
        trash_op = ConnectorOperation(
            connector="gmail",
            capability="trash_message",
            mode="execute_write",
            idempotency_key=f"smoke-gmail-trash-{tag}",
            approval_id=str(uuid.uuid4()),
            payload={"message_id": smoke_msg},
        )
        store.grant(
            Approval(
                str(trash_op.approval_id),
                operation_hash(trash_op),
                datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        execute(trash_op, adapter=adapter, approvals=store)
        untrash_op = ConnectorOperation(
            connector="gmail",
            capability="untrash_message",
            mode="execute_write",
            idempotency_key=f"smoke-gmail-untrash-{tag}",
            approval_id=str(uuid.uuid4()),
            payload={"message_id": smoke_msg},
        )
        store.grant(
            Approval(
                str(untrash_op.approval_id),
                operation_hash(untrash_op),
                datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        execute(untrash_op, adapter=adapter, approvals=store)
        results["gmail"] = {"ok": True, "message_id": smoke_msg}
    else:
        results["gmail"] = {"ok": True, "skipped": "NIZAM_GMAIL_SMOKE_MESSAGE_ID not set"}

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Google connectors")
    parser.add_argument("--write-smoke", action="store_true", help="Create then delete test resources")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    env_loader.load_all(activate=True)
    report: dict[str, object] = {
        "probe": google_oauth.probe_live(),
        "write_scopes_ok": google_oauth.scopes_sufficient_for_write(),
    }
    if args.write_smoke:
        try:
            report["write_smoke"] = run_write_smoke()
            report["write_smoke_ok"] = True
        except Exception as exc:  # noqa: BLE001
            report["write_smoke_ok"] = False
            report["write_smoke_error"] = type(exc).__name__ + ": " + str(exc)

    ok = bool(report.get("probe", {}).get("ok"))  # type: ignore[union-attr]
    if args.write_smoke:
        ok = ok and bool(report.get("write_smoke_ok"))

    report["ok"] = ok
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
