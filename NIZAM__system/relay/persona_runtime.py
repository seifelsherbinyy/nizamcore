"""Provider-neutral persona runtime with local-only defaults."""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from NIZAM__system.governor import cost_ceiling
from NIZAM__system.relay.persona_prompt import (
    build_deterministic_reply,
    build_persona_system_prompt,
    is_deterministic_persona,
    is_llm_persona,
)


@dataclass(frozen=True)
class PersonaRuntimeRequest:
    target: str
    input_text: str
    trace_id: str
    timeout_seconds: float = 15.0
    projected_cost_usd: float = 0.0
    system_prompt: str | None = None


@dataclass(frozen=True)
class PersonaRuntimeResult:
    reply: str
    status: str
    provider: str | None
    model: str | None
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    fallback_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PersonaProvider(Protocol):
    name: str
    model: str
    local_only: bool

    def invoke(self, request: PersonaRuntimeRequest) -> dict[str, Any]:
        """Return reply, input_tokens, output_tokens, and cost_usd."""


class PersonaRuntime:
    def __init__(
        self,
        provider: PersonaProvider | None = None,
        *,
        cost_state_path: Path | None = None,
    ) -> None:
        self.provider = provider
        self.cost_state_path = cost_state_path

    def run(self, request: PersonaRuntimeRequest) -> PersonaRuntimeResult:
        started = time.perf_counter()
        target = request.target

        if is_deterministic_persona(target):
            return PersonaRuntimeResult(
                reply=build_deterministic_reply(target, request.input_text),
                status="ok",
                provider=None,
                model=None,
                latency_ms=int((time.perf_counter() - started) * 1000),
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                fallback_reason=None,
            )

        if not is_llm_persona(target):
            return self._fallback(started, "unsupported_persona")
        if self.provider is None:
            return self._fallback(started, "model_not_configured")
        if (
            not self.provider.local_only
            and os.environ.get("NIZAM_LIVE_MODEL_APPROVED") != "1"
        ):
            return self._fallback(started, "external_model_requires_approval")

        state_path = self.cost_state_path or cost_ceiling._STATE_FILE
        try:
            cost_ceiling.check_or_block(state_path)
        except cost_ceiling.CostCeilingExceeded:
            return self._fallback(started, "cost_ceiling_exceeded")

        system_prompt = request.system_prompt or build_persona_system_prompt(target)
        invoke_request = PersonaRuntimeRequest(
            target=request.target,
            input_text=request.input_text,
            trace_id=request.trace_id,
            timeout_seconds=request.timeout_seconds,
            projected_cost_usd=request.projected_cost_usd,
            system_prompt=system_prompt,
        )

        pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="nizam-persona")
        future = pool.submit(self.provider.invoke, invoke_request)
        try:
            payload = future.result(timeout=request.timeout_seconds)
        except FutureTimeout:
            future.cancel()
            return self._fallback(started, "timeout")
        except Exception as exc:
            return self._fallback(started, f"provider_error:{type(exc).__name__}")
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

        reply = str(payload["reply"]).strip()
        if target == "Khaldun":
            from NIZAM__system.modes.khaldun.validator import validate_khaldun_response

            ok, reason = validate_khaldun_response(
                reply, evidence={"tasawwuf_topic": True}
            )
            if not ok:
                reply = (
                    "خلدون: ما قدرت أرد بأمان — "
                    + reason
                    + ". جرّب صياغة أوضح بدون ادعاءات قطعية."
                )

        cost = max(0.0, float(payload.get("cost_usd", 0.0)))
        if cost:
            cost_ceiling.accumulate(
                cost,
                provider=self.provider.name,
                model=self.provider.model,
                agent=request.target,
                state_path=state_path,
            )
        return PersonaRuntimeResult(
            reply=reply,
            status="ok",
            provider=self.provider.name,
            model=self.provider.model,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=max(0, int(payload.get("input_tokens", 0))),
            output_tokens=max(0, int(payload.get("output_tokens", 0))),
            cost_usd=cost,
            fallback_reason=None,
        )

    @staticmethod
    def _fallback(started: float, reason: str) -> PersonaRuntimeResult:
        return PersonaRuntimeResult(
            reply="captured.",
            status="fallback",
            provider=None,
            model=None,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            fallback_reason=reason,
        )


def enabled() -> bool:
    return os.environ.get("NIZAM_REAL_PERSONA_RUNTIME", "0") == "1"


def build_default_runtime() -> "PersonaRuntime | None":
    if not enabled():
        return None
    from NIZAM__system.relay.providers import build_provider

    return PersonaRuntime(build_provider())
