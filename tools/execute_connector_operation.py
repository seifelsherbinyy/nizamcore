#!/usr/bin/env python3
"""Execute an approved Google connector write operation."""
from __future__ import annotations

import argparse
import json
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
from NIZAM__system.connectors.google_adapter import build_google_adapter  # noqa: E402
from NIZAM__system.relay import env_loader  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute approved connector operation")
    parser.add_argument(
        "--operation",
        type=Path,
        help="JSON file with ConnectorOperation fields",
    )
    parser.add_argument("--approve", action="store_true", help="Grant single-use approval")
    parser.add_argument("--dry-run", action="store_true", help="Use propose_write mode only")
    args = parser.parse_args()

    env_loader.load_all(activate=True)
    if not args.operation or not args.operation.exists():
        print("Provide --operation path to JSON", file=sys.stderr)
        return 2

    raw = json.loads(args.operation.read_text(encoding="utf-8"))
    mode = "propose_write" if args.dry_run else str(raw.get("mode", "execute_write"))
    approval_id = raw.get("approval_id")
    if mode == "execute_write" and args.approve and not approval_id:
        approval_id = str(uuid.uuid4())

    operation = ConnectorOperation(
        connector=str(raw["connector"]),
        capability=str(raw["capability"]),
        mode=mode,  # type: ignore[arg-type]
        idempotency_key=str(raw.get("idempotency_key", uuid.uuid4())),
        approval_id=approval_id,
        payload=dict(raw.get("payload") or {}),
    )

    store = ApprovalStore()
    if mode == "execute_write" and args.approve:
        store.grant(
            Approval(
                str(approval_id),
                operation_hash(operation),
                datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )

    result = execute(operation, adapter=build_google_adapter(), approvals=store)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
