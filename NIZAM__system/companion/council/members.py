from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SpeakingRight = Literal["lead", "rebuttal", "full", "observe", "none"]
ContextScope = Literal[
    "strategic",
    "tactical",
    "body",
    "journal_meta",
    "governance",
    "recovery",
    "synthesis",
    "all",
]


@dataclass(frozen=True)
class CouncilMember:
    codename: str
    role: str
    voting_weight: float
    veto_rights: tuple[str, ...]
    speaking_rights: SpeakingRight
    allowed_contexts: tuple[ContextScope, ...]


MEMBERS: dict[str, CouncilMember] = {
    "Salman": CouncilMember(
        codename="Salman",
        role="consulting_companion",
        voting_weight=1.0,
        veto_rights=(),
        speaking_rights="lead",
        allowed_contexts=("strategic", "tactical", "synthesis", "all"),
    ),
    "Hazim": CouncilMember(
        codename="Hazim",
        role="resolute_critic",
        voting_weight=1.0,
        veto_rights=("value_conflict", "weak_assumption"),
        speaking_rights="rebuttal",
        allowed_contexts=("strategic", "tactical", "synthesis", "all"),
    ),
    "Khaldun": CouncilMember(
        codename="Khaldun",
        role="weekly_synthesizer",
        voting_weight=1.2,
        veto_rights=(),
        speaking_rights="full",
        allowed_contexts=("synthesis", "strategic", "all"),
    ),
    "Hayat": CouncilMember(
        codename="Hayat",
        role="biometric_witness",
        voting_weight=0.8,
        veto_rights=("body_red_flag",),
        speaking_rights="full",
        allowed_contexts=("body", "all"),
    ),
    "Sadiq": CouncilMember(
        codename="Sadiq",
        role="journal_witness",
        voting_weight=0.6,
        veto_rights=(),
        speaking_rights="observe",
        allowed_contexts=("journal_meta", "all"),
    ),
    "Khalid": CouncilMember(
        codename="Khalid",
        role="tactical_commander",
        voting_weight=1.0,
        veto_rights=(),
        speaking_rights="lead",
        allowed_contexts=("tactical", "strategic", "all"),
    ),
    "Ammar": CouncilMember(
        codename="Ammar",
        role="egress_guardian",
        voting_weight=0.0,
        veto_rights=("egress", "privacy", "cost_ceiling"),
        speaking_rights="observe",
        allowed_contexts=("governance", "all"),
    ),
    "Yusra": CouncilMember(
        codename="Yusra",
        role="recovery_voice",
        voting_weight=0.0,
        veto_rights=(),
        speaking_rights="none",
        allowed_contexts=("recovery",),
    ),
}


def get_member(codename: str) -> CouncilMember:
    try:
        return MEMBERS[codename]
    except KeyError as exc:
        raise KeyError(f"unknown council member {codename!r}") from exc


def members_for_context(scope: ContextScope) -> list[CouncilMember]:
    return [
        member
        for member in MEMBERS.values()
        if scope in member.allowed_contexts or "all" in member.allowed_contexts
    ]


def lead_speakers() -> list[str]:
    return [m.codename for m in MEMBERS.values() if m.speaking_rights == "lead"]


def full_council_roster() -> list[str]:
    return [
        m.codename
        for m in MEMBERS.values()
        if m.speaking_rights in {"lead", "rebuttal", "full"}
    ]
