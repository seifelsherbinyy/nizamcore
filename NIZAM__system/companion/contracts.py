from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class GatewayEnvelope:
    message_id: str
    actor_hash: str
    route: str
    timestamp: str
    channel: str
    consent_state: Literal["granted", "denied", "unknown"]
    context_refs: tuple[str, ...] = ()
    schema_version: str = "1.0"

    @classmethod
    def build(
        cls, *, message_id: str, actor_id: str, route: str, channel: str
    ) -> "GatewayEnvelope":
        return cls(
            message_id=message_id,
            actor_hash=hashlib.sha256(actor_id.encode()).hexdigest()[:16],
            route=route,
            timestamp=utc_now(),
            channel=channel,
            consent_state="granted",
        )


@dataclass(frozen=True)
class ContextItem:
    kind: Literal["fact", "user_statement", "inference", "correlation", "action"]
    text: str
    provenance: str
    observed_at: str
    privacy_class: str
    confidence: float
    expires_at: str | None = None


@dataclass(frozen=True)
class ContextPacket:
    trace_id: str
    persona: str
    items: tuple[ContextItem, ...]
    token_budget: int
    privacy_ceiling: str

    def prompt_text(self) -> str:
        max_chars = max(0, self.token_budget * 4)
        lines: list[str] = []
        used = 0
        for item in self.items:
            line = f"[{item.kind}|{item.provenance}] {item.text}"
            if used + len(line) > max_chars:
                break
            lines.append(line)
            used += len(line)
        return "\n".join(lines)


@dataclass(frozen=True)
class ConnectorOperation:
    connector: str
    capability: str
    mode: Literal["read", "propose_write", "execute_write"]
    idempotency_key: str
    approval_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def assert_authorized(self) -> None:
        if self.mode == "execute_write" and not self.approval_id:
            raise PermissionError("connector write requires single-use approval")


@dataclass(frozen=True)
class HealthObservation:
    metric: str
    value: float
    unit: str
    observed_at: str
    source: str
    provenance_hash: str


@dataclass(frozen=True)
class KnowledgeClaim:
    claim_id: str
    claim: str
    source_title: str
    source_url: str
    published_at: str | None
    retrieved_at: str
    reliability: str
    summary: str
    implications: str
    privacy_class: str = "strict_local"
    supersedes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProactiveCandidate:
    persona: str
    trigger: str
    relevance_score: float
    source_refs: tuple[str, ...]
    expires_at: str
    message: str


@dataclass(frozen=True)
class ContextRefresh:
    refreshed_at: str
    sources_checked: tuple[str, ...]
    sources_found: tuple[str, ...]
    missing_sources: tuple[str, ...]
    latest_entry_timestamps: dict[str, str]
    confidence: Literal["high", "medium", "low"]
    privacy_level: Literal["public_safe", "private_ai_ok", "strict_local", "secret"]
    sukoon_capacity: Literal["green", "yellow", "red", "unknown"]
    source_snapshots: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "refreshed_at": self.refreshed_at,
            "sources_checked": list(self.sources_checked),
            "sources_found": list(self.sources_found),
            "missing_sources": list(self.missing_sources),
            "latest_entry_timestamps": dict(self.latest_entry_timestamps),
            "confidence": self.confidence,
            "privacy_level": self.privacy_level,
            "sukoon_capacity": self.sukoon_capacity,
        }


@dataclass(frozen=True)
class PulsationMessage:
    message_type: Literal["companion_checkin", "islamic_reminder"]
    agent_name: str
    agent_role: str
    generated_at: str
    context_refresh: ContextRefresh
    message: str
    focus_trigger: str
    requires_user_reply: bool = False
    council_required: bool = False
    council_motion_candidate: str | None = None
    council_summary_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_type": self.message_type,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "generated_at": self.generated_at,
            "context_refresh": self.context_refresh.to_dict(),
            "message": self.message,
            "focus_trigger": self.focus_trigger,
            "requires_user_reply": self.requires_user_reply,
            "council_required": self.council_required,
            "council_motion_candidate": self.council_motion_candidate,
            "council_summary_hash": self.council_summary_hash,
        }
