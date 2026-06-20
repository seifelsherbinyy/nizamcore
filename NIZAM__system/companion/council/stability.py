from __future__ import annotations

from dataclasses import dataclass

from .contracts import AgentPosition


@dataclass(frozen=True)
class StabilityState:
    round_index: int
    stable_rounds: int
    should_stop: bool
    reason: str


def position_signature(positions: list[AgentPosition]) -> tuple[tuple[str, str, float], ...]:
    return tuple(
        sorted((pos.agent, pos.stance, round(pos.confidence, 2)) for pos in positions)
    )


def update_stability(
    *,
    prior_signature: tuple[tuple[str, str, float], ...] | None,
    current_positions: list[AgentPosition],
    stable_rounds: int,
    round_index: int,
    max_rounds: int,
    stable_target: int = 2,
) -> StabilityState:
    """Adaptive stop after stable_target stable rounds or max_rounds."""
    current = position_signature(current_positions)
    if round_index >= max_rounds:
        return StabilityState(
            round_index=round_index,
            stable_rounds=stable_rounds,
            should_stop=True,
            reason="max_rounds",
        )
    if prior_signature is not None and prior_signature == current:
        stable_rounds += 1
    else:
        stable_rounds = 0
    if stable_rounds >= stable_target:
        return StabilityState(
            round_index=round_index,
            stable_rounds=stable_rounds,
            should_stop=True,
            reason="stable_positions",
        )
    return StabilityState(
        round_index=round_index,
        stable_rounds=stable_rounds,
        should_stop=False,
        reason="continue",
    )
