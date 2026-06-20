"""NIZAM companion council — multi-agent deliberation."""

from .contracts import (
    AgentPosition,
    CouncilMotion,
    CouncilVerdict,
    CouncilView,
    EvidenceRef,
    Vote,
)
from .decision_protocols import apply_protocol, finalize_verdict, member_can_veto
from .deliberation import deliberate, inject_veto
from .evidence import build_evidence_pack, contains_journal_egress
from .ledger import append_council_verdict
from .members import MEMBERS, get_member, members_for_context
from .stability import update_stability
from .triggers import minimal_pulse_note, should_convene_council, trigger_reason
from .view_renderer import render_view

__all__ = [
    "AgentPosition",
    "CouncilMotion",
    "CouncilVerdict",
    "CouncilView",
    "EvidenceRef",
    "Vote",
    "MEMBERS",
    "apply_protocol",
    "append_council_verdict",
    "build_evidence_pack",
    "contains_journal_egress",
    "deliberate",
    "finalize_verdict",
    "get_member",
    "inject_veto",
    "member_can_veto",
    "members_for_context",
    "minimal_pulse_note",
    "render_view",
    "should_convene_council",
    "trigger_reason",
    "update_stability",
]
