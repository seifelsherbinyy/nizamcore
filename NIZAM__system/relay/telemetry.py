"""Export redacted runtime metrics when remote telemetry is approved."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from NIZAM__system.relay import runtime_events


DEFAULT_EXPORT = Path(__file__).resolve().parent / ".state" / "telemetry-export.jsonl"


def approved() -> bool:
    return os.environ.get("NIZAM_REMOTE_TELEMETRY_APPROVED") == "1"


def build_payload() -> dict[str, Any]:
    events = runtime_events.load_events()
    metrics = runtime_events.metrics(events)
    pending = len(runtime_events.pending_inbound(events))
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "service": "nizam-relay",
        "metrics": metrics,
        "pending_inbound": pending,
        "turns_completed": metrics.get("turns", 0),
    }


def export_local(path: Path = DEFAULT_EXPORT) -> dict[str, Any]:
    payload = build_payload()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload


def export_remote(payload: dict[str, Any] | None = None, *, path: Path = DEFAULT_EXPORT) -> dict[str, Any]:
    if not approved():
        return {"ok": False, "reason": "telemetry_not_approved"}
    endpoint = os.environ.get("NIZAM_TELEMETRY_ENDPOINT", "").strip()
    if not endpoint:
        local = export_local(path)
        return {"ok": True, "mode": "local_jsonl", "metrics": local["metrics"]}
    payload = payload or build_payload()
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
    except urllib.error.URLError as exc:
        return {"ok": False, "reason": str(exc)}
    export_local(path)
    return {"ok": True, "mode": "remote_post", "status": status, "metrics": payload["metrics"]}
