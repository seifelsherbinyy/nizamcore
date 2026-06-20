from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .contracts import AgentPosition, CouncilMotion, CouncilVerdict, Vote
from .decision_protocols import ballots_from_positions, finalize_verdict
from .members import full_council_roster, lead_speakers
from .stability import update_stability


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _confidence_spread(positions: list[AgentPosition]) -> float:
    if not positions:
        return 0.0
    confidences = [pos.confidence for pos in positions]
    return max(confidences) - min(confidences)


def _default_positions(
    motion: CouncilMotion,
    *,
    round_index: int,
    phase: str,
) -> list[AgentPosition]:
    positions: list[AgentPosition] = []
    if phase == "two_positions":
        speakers = lead_speakers()[:2]
        stances = ("support", "conditional")
        for agent, stance in zip(speakers, stances):
            positions.append(
                AgentPosition(
                    agent=agent,
                    stance=stance,
                    rationale=f"{agent} initial position on {motion.title}",
                    confidence=0.62 if stance == "support" else 0.48,
                    round_index=round_index,
                )
            )
        return positions

    if phase == "rebuttal":
        return [
            AgentPosition(
                agent="Hazim",
                stance="oppose",
                rationale=f"Counter-case for weakest assumption in {motion.title}",
                confidence=0.55,
                round_index=round_index,
            )
        ]

    roster = full_council_roster()
    for index, agent in enumerate(roster):
        stance = "support" if index % 2 == 0 else "oppose"
        positions.append(
            AgentPosition(
                agent=agent,
                stance=stance,
                rationale=f"{agent} full-council view on {motion.title}",
                confidence=0.5 + (index % 3) * 0.1,
                round_index=round_index,
            )
        )
    return positions


def deliberate(
    motion: CouncilMotion,
    *,
    max_rounds: int = 5,
    conflict_threshold: float = 0.15,
) -> CouncilVerdict:
    """Progressive deliberation: two positions → rebuttal → full council if conflict."""
    all_positions: list[AgentPosition] = []
    prior_signature = None
    stable_rounds = 0
    round_index = 0
    phase = "two_positions"
    expanded = False

    while round_index < max_rounds:
        round_index += 1
        if phase == "two_positions":
            round_positions = _default_positions(motion, round_index=round_index, phase=phase)
            all_positions.extend(round_positions)
            spread = _confidence_spread(round_positions)
            phase = "rebuttal" if spread >= conflict_threshold else "stable_check"
        elif phase == "rebuttal":
            round_positions = _default_positions(motion, round_index=round_index, phase=phase)
            all_positions.extend(round_positions)
            spread = _confidence_spread(all_positions)
            if spread >= conflict_threshold and not expanded:
                phase = "full_council"
                expanded = True
            else:
                phase = "stable_check"
            round_positions = all_positions[-len(round_positions) :]
        elif phase == "full_council":
            round_positions = _default_positions(motion, round_index=round_index, phase=phase)
            all_positions = round_positions
            phase = "stable_check"
        else:
            round_positions = all_positions

        stability = update_stability(
            prior_signature=prior_signature,
            current_positions=round_positions,
            stable_rounds=stable_rounds,
            round_index=round_index,
            max_rounds=max_rounds,
        )
        stable_rounds = stability.stable_rounds
        prior_signature = tuple(
            sorted((pos.agent, pos.stance, round(pos.confidence, 2)) for pos in round_positions)
        )
        if stability.should_stop:
            break

    latest_by_agent: dict[str, AgentPosition] = {}
    for pos in all_positions:
        latest_by_agent[pos.agent] = pos

    vote_inputs = [
        (pos.agent, pos.stance, pos.confidence, pos.rationale)
        for pos in latest_by_agent.values()
    ]
    votes = ballots_from_positions(vote_inputs, protocol=motion.protocol)
    judge_synthesis = None
    if motion.protocol == "judge_synthesis":
        judge_synthesis = f"Khaldun synthesis for {motion.title}"

    return finalize_verdict(
        verdict_id=str(uuid.uuid4()),
        motion_id=motion.motion_id,
        trace_id=motion.trace_id,
        protocol=motion.protocol,
        votes=votes,
        decided_at=_utc_now(),
        judge_synthesis=judge_synthesis,
        positions=tuple(latest_by_agent.values()),
        rounds_completed=round_index,
        stability_stopped=stability.should_stop,
    )


def inject_veto(verdict: CouncilVerdict, *, agent: str, rationale: str) -> CouncilVerdict:
    votes = list(verdict.votes)
    votes.append(
        Vote(agent=agent, ballot="veto", weight=0.0, rationale=rationale)
    )
    return finalize_verdict(
        verdict_id=verdict.verdict_id,
        motion_id=verdict.motion_id,
        trace_id=verdict.trace_id,
        protocol=verdict.protocol_used,
        votes=votes,
        decided_at=verdict.decided_at,
        judge_synthesis=verdict.judge_synthesis,
        positions=verdict.positions,
        rounds_completed=verdict.rounds_completed,
        stability_stopped=verdict.stability_stopped,
    )
