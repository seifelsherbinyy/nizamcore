from __future__ import annotations

from typing import Iterable

from .contracts import Ballot, CouncilVerdict, Outcome, Vote
from .members import MEMBERS, get_member


def _weighted_score(votes: Iterable[Vote]) -> float:
    yes = sum(v.weight for v in votes if v.ballot == "yes")
    no = sum(v.weight for v in votes if v.ballot == "no")
    return yes - no


def _collect_vetoes(votes: Iterable[Vote]) -> list[str]:
    return [vote.agent for vote in votes if vote.ballot == "veto"]


def _dissent(votes: Iterable[Vote], outcome: Outcome) -> tuple[str, ...]:
    if outcome == "approved":
        return tuple(
            f"{vote.agent}: voted {vote.ballot}"
            for vote in votes
            if vote.ballot in {"no", "veto", "defer"}
        )
    if outcome == "rejected":
        return tuple(
            f"{vote.agent}: voted {vote.ballot}"
            for vote in votes
            if vote.ballot == "yes"
        )
    return tuple(f"{vote.agent}: voted {vote.ballot}" for vote in votes if vote.rationale)


def apply_protocol(
    *,
    protocol: str,
    votes: list[Vote],
    judge_synthesis: str | None = None,
) -> tuple[Outcome, str | None]:
    """Resolve a vote set under the requested protocol."""
    vetoes = _collect_vetoes(votes)
    if vetoes:
        return "vetoed", f"Veto by {', '.join(vetoes)}"

    deferrals = [vote.agent for vote in votes if vote.ballot == "defer"]
    if protocol == "defer" or (deferrals and protocol not in {"judge_synthesis"}):
        return "deferred", f"Deferred by {', '.join(deferrals) or 'protocol'}"

    participating = [vote for vote in votes if vote.ballot not in {"abstain", "defer"}]
    if not participating:
        return "no_quorum", "No participating votes"

    if protocol == "unanimity":
        if all(vote.ballot == "yes" for vote in participating):
            return "approved", judge_synthesis
        return "rejected", judge_synthesis

    if protocol == "judge_synthesis":
        return ("approved" if judge_synthesis else "deferred"), judge_synthesis

    if protocol == "weighted":
        score = _weighted_score(participating)
        return ("approved" if score > 0 else "rejected"), judge_synthesis

    yes_count = sum(1 for vote in participating if vote.ballot == "yes")
    total = len(participating)

    if protocol == "supermajority":
        threshold = max(1, int(total * 0.67 + 0.999))
        if yes_count >= threshold:
            return "approved", judge_synthesis
        return "rejected", judge_synthesis

    # majority (default) and veto-only pre-check already handled
    if yes_count > total / 2:
        return "approved", judge_synthesis
    return "rejected", judge_synthesis


def ballots_from_positions(
    positions: list[tuple[str, str, float, str]],
    *,
    protocol: str,
) -> list[Vote]:
    """Convert agent stances into weighted ballots."""
    votes: list[Vote] = []
    for agent, stance, confidence, rationale in positions:
        member = get_member(agent)
        if member.voting_weight <= 0 and stance != "veto":
            continue
        ballot: Ballot
        if stance == "veto":
            ballot = "veto"
        elif stance in {"support", "yes"}:
            ballot = "yes"
        elif stance in {"oppose", "no"}:
            ballot = "no"
        elif stance == "defer":
            ballot = "defer"
        else:
            ballot = "abstain"
        weight = member.voting_weight
        if protocol == "weighted" and ballot == "yes":
            weight *= max(0.25, min(1.0, confidence))
        votes.append(
            Vote(
                agent=agent,
                ballot=ballot,
                weight=weight,
                rationale=rationale,
            )
        )
    return votes


def finalize_verdict(
    *,
    verdict_id: str,
    motion_id: str,
    trace_id: str,
    protocol: str,
    votes: list[Vote],
    decided_at: str,
    judge_synthesis: str | None = None,
    positions: tuple = (),
    rounds_completed: int = 0,
    stability_stopped: bool = False,
) -> CouncilVerdict:
    outcome, synthesis = apply_protocol(
        protocol=protocol,
        votes=votes,
        judge_synthesis=judge_synthesis,
    )
    return CouncilVerdict(
        verdict_id=verdict_id,
        motion_id=motion_id,
        trace_id=trace_id,
        outcome=outcome,
        protocol_used=protocol,
        decided_at=decided_at,
        votes=tuple(votes),
        dissent=_dissent(votes, outcome),
        judge_synthesis=synthesis,
        positions=positions,
        rounds_completed=rounds_completed,
        stability_stopped=stability_stopped,
    )


def member_can_veto(agent: str, veto_kind: str) -> bool:
    member = MEMBERS.get(agent)
    if member is None:
        return False
    return veto_kind in member.veto_rights
