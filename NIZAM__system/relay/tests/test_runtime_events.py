from __future__ import annotations

from pathlib import Path

import pytest

from NIZAM__system.relay import runtime_events


def test_inbound_persistence_contains_hash_not_text(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    runtime_events.persist_inbound(
        trace_id="t1",
        update_id=1,
        user_id=123,
        text="private message",
        path=path,
    )
    raw = path.read_text(encoding="utf-8")
    assert "private message" not in raw
    assert runtime_events.pending_inbound(runtime_events.load_events(path)) == {"t1"}


def test_completed_turn_is_not_recovered_twice(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    runtime_events.persist_inbound(
        trace_id="t1", update_id=1, user_id=123, text="x", path=path
    )
    runtime_events.append_event(
        {
            "event": "turn_completed",
            "trace_id": "t1",
            "outcome": "ok",
            "latency_ms": 10,
            "cost_usd": 0,
        },
        path,
    )
    assert runtime_events.pending_inbound(runtime_events.load_events(path)) == set()


def test_metrics_calculate_latency_error_and_cost() -> None:
    events = [
        {"event": "turn_completed", "latency_ms": 10, "outcome": "ok", "cost_usd": 0.1},
        {"event": "turn_completed", "latency_ms": 30, "outcome": "ok", "cost_usd": 0.2},
        {"event": "turn_completed", "latency_ms": 100, "outcome": "error", "cost_usd": 0},
    ]
    result = runtime_events.metrics(events)
    assert result["turns"] == 3
    assert result["p50_latency_ms"] == 30
    assert result["p95_latency_ms"] == 30
    assert result["error_rate"] == pytest.approx(1 / 3)
    assert result["cost_usd"] == 0.3


def test_sensitive_event_fields_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        runtime_events.append_event(
            {"event": "bad", "trace_id": "t", "prompt": "secret"},
            tmp_path / "events.jsonl",
        )
