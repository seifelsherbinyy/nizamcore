"""HIMAYAH egress gate for pulsation messages."""
from __future__ import annotations

import re
from dataclasses import replace
from typing import Literal

from ..contracts import ContextRefresh, PulsationMessage

JOURNAL_BODY_MARKERS = re.compile(
    r"\b(body|felt_state|open_questions|decisions)\s*[:=]",
    re.I,
)


def _capacity_level(refresh: ContextRefresh) -> str:
    return refresh.sukoon_capacity


def apply_egress(
    message: PulsationMessage,
    *,
    allow_private_ai: bool = False,
) -> tuple[PulsationMessage, dict[str, str]]:
    """Redact journal bodies, set privacy_level, refuse raw strict_local egress."""
    result: dict[str, str] = {"status": "pass", "reason": "public_safe"}

    if JOURNAL_BODY_MARKERS.search(message.message):
        result = {"status": "refused", "reason": "journal_body_marker_detected"}
        safe = replace(
            message,
            message=(
                f"I'm {message.agent_name}, your {message.agent_role}.\n"
                "HIMAYAH blocked raw journal egress.\n"
                "Focus: Reply when ready — no private content was sent."
            ),
            focus_trigger="Reply when ready — no private content was sent.",
        )
        safe_refresh = replace(
            safe.context_refresh,
            privacy_level="public_safe",
            source_snapshots={},
        )
        return replace(safe, context_refresh=safe_refresh), result

    privacy: Literal["public_safe", "private_ai_ok", "strict_local", "secret"]
    if allow_private_ai:
        privacy = "private_ai_ok"
    else:
        privacy = "public_safe"

    redacted_refresh = replace(
        message.context_refresh,
        privacy_level=privacy,
        source_snapshots={},
    )
    return replace(message, context_refresh=redacted_refresh), result


def should_suppress_crisis(refresh: ContextRefresh) -> bool:
    flags = refresh.source_snapshots.get("sukoon_capacity", {})
    if refresh.sukoon_capacity == "red" and flags.get("recent_flag_count", 0) >= 2:
        return True
    return False


def tiny_mode_for_capacity(refresh: ContextRefresh) -> bool:
    return refresh.sukoon_capacity in {"yellow", "red"}
