from __future__ import annotations

from datetime import datetime, timezone

from .contracts import ContextItem, ContextPacket


PRIVACY_RANK = {
    "private_github": 0,
    "review_before_commit": 1,
    "strict_local": 2,
    "strict_local_maximum": 3,
}


def build_context_packet(
    *,
    trace_id: str,
    persona: str,
    items: list[ContextItem],
    token_budget: int = 1800,
    privacy_ceiling: str = "strict_local",
    now: datetime | None = None,
) -> ContextPacket:
    current = now or datetime.now(timezone.utc)
    ceiling = PRIVACY_RANK[privacy_ceiling]
    accepted: list[ContextItem] = []
    for item in items:
        if PRIVACY_RANK.get(item.privacy_class, 99) > ceiling:
            continue
        if item.expires_at:
            expiry = datetime.fromisoformat(item.expires_at.replace("Z", "+00:00"))
            if expiry <= current:
                continue
        accepted.append(item)
    return ContextPacket(
        trace_id=trace_id,
        persona=persona,
        items=tuple(accepted),
        token_budget=token_budget,
        privacy_ceiling=privacy_ceiling,
    )
