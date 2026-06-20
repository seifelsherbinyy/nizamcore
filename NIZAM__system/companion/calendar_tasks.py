from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from .contracts import ConnectorOperation


class CalendarTasksAdapter(Protocol):
    def read(self, capability: str) -> list[dict[str, Any]]: ...
    def write(self, capability: str, payload: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class Approval:
    approval_id: str
    operation_hash: str
    expires_at: datetime
    consumed: bool = False


def operation_hash(operation: ConnectorOperation) -> str:
    body = {
        "connector": operation.connector,
        "capability": operation.capability,
        "idempotency_key": operation.idempotency_key,
        "payload": operation.payload,
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class ApprovalStore:
    def __init__(self) -> None:
        self._approvals: dict[str, Approval] = {}

    def grant(self, approval: Approval) -> None:
        self._approvals[approval.approval_id] = approval

    def consume(self, operation: ConnectorOperation) -> None:
        operation.assert_authorized()
        approval = self._approvals.get(str(operation.approval_id))
        if approval is None or approval.consumed:
            raise PermissionError("approval missing or already consumed")
        if approval.expires_at <= datetime.now(timezone.utc):
            raise PermissionError("approval expired")
        if approval.operation_hash != operation_hash(operation):
            raise PermissionError("approval does not match operation")
        approval.consumed = True


def execute(
    operation: ConnectorOperation,
    *,
    adapter: CalendarTasksAdapter,
    approvals: ApprovalStore,
) -> Any:
    if operation.mode == "read":
        return adapter.read(operation.capability)
    if operation.mode == "propose_write":
        return {"operation": operation.payload, "diff": operation.payload}
    approvals.consume(operation)
    result = adapter.write(operation.capability, operation.payload)
    read_capability = _read_capability_for(operation.capability)
    return {"written": result, "verified": adapter.read(read_capability)}


_READ_CAPABILITY_MAP = {
    "create_event": "read_calendar",
    "update_event": "read_calendar",
    "delete_event": "read_calendar",
    "create_task": "read_tasks",
    "update_task": "read_tasks",
    "complete_task": "read_tasks",
    "delete_task": "read_tasks",
    "send_message": "read_gmail",
    "trash_message": "read_gmail",
    "untrash_message": "read_gmail",
}


def _read_capability_for(capability: str) -> str:
    return _READ_CAPABILITY_MAP.get(capability, capability)
