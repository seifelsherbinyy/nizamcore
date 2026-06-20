from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class EvidenceRef:
    ref_id: str
    kind: str
    source: str
    summary: str
    hash_excerpt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CouncilMotion:
    motion_id: str
    trace_id: str
    title: str
    question: str
    protocol: str
    urgency: Literal["routine", "normal", "elevated", "crisis"]
    proposed_by: str
    created_at: str
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_refs"] = [ref.to_dict() for ref in self.evidence_refs]
        return data


@dataclass(frozen=True)
class AgentPosition:
    agent: str
    stance: Literal["support", "oppose", "abstain", "defer", "conditional"]
    rationale: str
    confidence: float
    evidence_refs: tuple[str, ...] = ()
    round_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


Ballot = Literal["yes", "no", "abstain", "veto", "defer"]
Outcome = Literal["approved", "rejected", "deferred", "vetoed", "no_quorum"]


@dataclass(frozen=True)
class Vote:
    agent: str
    ballot: Ballot
    weight: float
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CouncilVerdict:
    verdict_id: str
    motion_id: str
    trace_id: str
    outcome: Outcome
    protocol_used: str
    decided_at: str
    votes: tuple[Vote, ...]
    dissent: tuple[str, ...] = ()
    judge_synthesis: str | None = None
    positions: tuple[AgentPosition, ...] = ()
    rounds_completed: int = 0
    stability_stopped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict_id": self.verdict_id,
            "motion_id": self.motion_id,
            "trace_id": self.trace_id,
            "outcome": self.outcome,
            "protocol_used": self.protocol_used,
            "decided_at": self.decided_at,
            "votes": [vote.to_dict() for vote in self.votes],
            "dissent": list(self.dissent),
            "judge_synthesis": self.judge_synthesis,
            "positions": [pos.to_dict() for pos in self.positions],
            "rounds_completed": self.rounds_completed,
            "stability_stopped": self.stability_stopped,
        }


@dataclass(frozen=True)
class CouncilView:
    view_id: str
    verdict_id: str
    motion_title: str
    format: Literal["markdown", "html", "telegram_compact"]
    body: str
    vote_table: tuple[tuple[str, str, float], ...] = ()
    dissent_lines: tuple[str, ...] = ()
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "verdict_id": self.verdict_id,
            "motion_title": self.motion_title,
            "format": self.format,
            "body": self.body,
            "vote_table": [list(row) for row in self.vote_table],
            "dissent_lines": list(self.dissent_lines),
            "created_at": self.created_at,
        }
