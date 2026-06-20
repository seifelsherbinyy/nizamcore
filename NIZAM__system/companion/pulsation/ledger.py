"""PULSATION_LEDGER + EVENT_LEDGER hash excerpt."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from ..contracts import PulsationMessage

EVENT_EXCERPT_MAX = 400


def _event_excerpt(payload: dict[str, Any]) -> dict[str, Any]:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    excerpt = serialized[:EVENT_EXCERPT_MAX]
    return {
        "payload_hash": digest,
        "payload_excerpt": excerpt,
        "payload_bytes": len(serialized),
    }


def append_pulsation(
    message: PulsationMessage,
    *,
    loop: str,
    send_status: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append full row to PULSATION_LEDGER and hash excerpt to EVENT_LEDGER."""
    from NIZAM__system.governor import ledger_writer

    payload = {
        "loop": loop,
        "message_type": message.message_type,
        "agent_name": message.agent_name,
        "generated_at": message.generated_at,
        "focus_trigger": message.focus_trigger,
        "context_refresh": message.context_refresh.to_dict(),
        "send_status": send_status,
        "dry_run": dry_run,
        "council_required": message.council_required,
        "council_motion_candidate": message.council_motion_candidate,
        "council_summary_hash": message.council_summary_hash,
    }

    if dry_run:
        return {"pulsation_row": None, "event_row": None, "status": "skipped_dry_run"}

    pulsation_row = ledger_writer.append(
        "PULSATION_LEDGER",
        payload,
        actor="Ammar",
        action="pulsation_send",
        module="NIZAM__companion.pulsation",
        privacy_class="strict_local",
    )
    event_row = ledger_writer.append(
        "EVENT_LEDGER",
        {
            "kind": "pulsation",
            "loop": loop,
            "agent": message.agent_name,
            "message_type": message.message_type,
            **_event_excerpt(payload),
        },
        actor="Ammar",
        action="pulsation_excerpt",
        module="NIZAM__companion.pulsation",
        privacy_class="review_before_commit",
        trace_id=pulsation_row.get("trace_id"),
    )
    return {
        "pulsation_row": pulsation_row,
        "event_row": event_row,
        "status": "appended",
    }
