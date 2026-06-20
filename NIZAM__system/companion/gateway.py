from __future__ import annotations

from typing import Any

from .contracts import GatewayEnvelope


def envelope_from_update(
    update: dict[str, Any],
    *,
    route: str,
    channel: str = "telegram",
) -> GatewayEnvelope:
    """Build a versioned Hermes-to-worker envelope from a Telegram update."""
    message = update.get("message") or {}
    actor = message.get("from") or {}
    actor_id = str(actor.get("id") or update.get("update_id") or "unknown")
    message_id = str(message.get("message_id") or update.get("update_id") or "unknown")
    return GatewayEnvelope.build(
        message_id=message_id,
        actor_id=actor_id,
        route=route,
        channel=channel,
    )
