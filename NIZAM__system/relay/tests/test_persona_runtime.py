from __future__ import annotations

import json
import time
from pathlib import Path

from NIZAM__system.relay.persona_runtime import (
    PersonaRuntime,
    PersonaRuntimeRequest,
)


class FakeLocalProvider:
    name = "fake-local"
    model = "fake-amin-1"
    local_only = True

    def invoke(self, request: PersonaRuntimeRequest) -> dict:
        return {
            "reply": f"Captured locally: {request.input_text}",
            "input_tokens": 4,
            "output_tokens": 3,
            "cost_usd": 0.001,
        }


class FakeExternalProvider(FakeLocalProvider):
    local_only = False


class SlowProvider(FakeLocalProvider):
    def invoke(self, request: PersonaRuntimeRequest) -> dict:
        time.sleep(0.2)
        return super().invoke(request)


def _request(**kwargs) -> PersonaRuntimeRequest:
    values = {
        "target": "Amin",
        "input_text": "verbatim capture",
        "trace_id": "trace-1",
    }
    values.update(kwargs)
    return PersonaRuntimeRequest(**values)


def test_mocked_local_runtime_returns_non_stub_result(tmp_path: Path) -> None:
    state = tmp_path / "cost.json"
    result = PersonaRuntime(FakeLocalProvider(), cost_state_path=state).run(_request())
    assert result.status == "ok"
    assert result.reply == "Captured locally: verbatim capture"
    assert result.provider == "fake-local"
    assert result.cost_usd == 0.001
    assert json.loads(state.read_text(encoding="utf-8"))["spend_usd"] == 0.001


def test_missing_model_is_safe_fallback() -> None:
    result = PersonaRuntime().run(_request())
    assert result.status == "fallback"
    assert result.reply == "captured."
    assert result.fallback_reason == "model_not_configured"


def test_external_provider_is_refused_without_approval() -> None:
    result = PersonaRuntime(FakeExternalProvider()).run(_request())
    assert result.status == "fallback"
    assert result.fallback_reason == "external_model_requires_approval"


def test_external_provider_runs_when_live_model_is_approved(monkeypatch) -> None:
    monkeypatch.setenv("NIZAM_LIVE_MODEL_APPROVED", "1")
    result = PersonaRuntime(FakeExternalProvider()).run(_request())
    assert result.status == "ok"
    assert result.reply == "Captured locally: verbatim capture"


def test_timeout_is_safe_fallback(tmp_path: Path) -> None:
    result = PersonaRuntime(SlowProvider(), cost_state_path=tmp_path / "cost.json").run(
        _request(timeout_seconds=0.01)
    )
    assert result.status == "fallback"
    assert result.fallback_reason == "timeout"


def test_hard_cost_ceiling_blocks_before_call(tmp_path: Path) -> None:
    state = tmp_path / "cost.json"
    state.write_text(
        json.dumps({"month": time.strftime("%Y-%m"), "spend_usd": 300, "calls": []}),
        encoding="utf-8",
    )
    result = PersonaRuntime(FakeLocalProvider(), cost_state_path=state).run(_request())
    assert result.status == "fallback"
    assert result.fallback_reason == "cost_ceiling_exceeded"
