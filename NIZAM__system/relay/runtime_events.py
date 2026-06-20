"""Privacy-safe local runtime events and aggregate metrics."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from statistics import median
from typing import Any, Iterable


DEFAULT_PATH = Path(__file__).resolve().parent / ".state" / "runtime-events.jsonl"


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def persist_inbound(
    *,
    trace_id: str,
    update_id: int | None,
    user_id: int,
    text: str,
    path: Path = DEFAULT_PATH,
) -> dict[str, Any]:
    event = {
        "event": "inbound_persisted",
        "trace_id": trace_id,
        "update_id": update_id,
        "user_id_hash": hashlib.sha256(str(user_id).encode()).hexdigest()[:12],
        "input_chars": len(text),
        "input_sha256_16": text_fingerprint(text),
    }
    append_event(event, path)
    return event


def append_event(event: dict[str, Any], path: Path = DEFAULT_PATH) -> None:
    forbidden = {"input_text", "prompt", "response", "message_text"}
    if forbidden & event.keys():
        raise ValueError("runtime event contains sensitive payload fields")
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(".tmp")
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    tmp.write_text(existing + line, encoding="utf-8")
    os.replace(tmp, path)


def load_events(path: Path = DEFAULT_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def pending_inbound(events: Iterable[dict[str, Any]]) -> set[str]:
    persisted: set[str] = set()
    completed: set[str] = set()
    for event in events:
        trace_id = str(event.get("trace_id", ""))
        if event.get("event") == "inbound_persisted":
            persisted.add(trace_id)
        elif event.get("event") == "turn_completed":
            completed.add(trace_id)
    return persisted - completed


def metrics(events: Iterable[dict[str, Any]]) -> dict[str, float | int]:
    completed = [event for event in events if event.get("event") == "turn_completed"]
    latencies = sorted(
        int(event["latency_ms"]) for event in completed if "latency_ms" in event
    )
    errors = sum(event.get("outcome") != "ok" for event in completed)
    total_cost = sum(float(event.get("cost_usd", 0.0)) for event in completed)
    if not latencies:
        return {
            "turns": 0,
            "p50_latency_ms": 0,
            "p95_latency_ms": 0,
            "error_rate": 0.0,
            "cost_usd": 0.0,
        }
    p95_index = max(0, int((len(latencies) - 1) * 0.95))
    return {
        "turns": len(completed),
        "p50_latency_ms": int(median(latencies)),
        "p95_latency_ms": latencies[p95_index],
        "error_rate": errors / len(completed),
        "cost_usd": round(total_cost, 6),
    }
