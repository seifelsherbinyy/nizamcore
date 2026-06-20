from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from NIZAM__system.governor import ledger_writer

from .contracts import CouncilMotion, CouncilVerdict, CouncilView


def _hash_excerpt(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def append_council_verdict(
    verdict: CouncilVerdict,
    *,
    motion: CouncilMotion,
    view: CouncilView | None = None,
    actor: str = "Ammar",
    trace_id: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Append council verdict to COUNCIL_LEDGER and EVENT_LEDGER hash excerpt."""
    payload = {
        "motion_id": motion.motion_id,
        "motion_title": motion.title,
        "verdict_id": verdict.verdict_id,
        "outcome": verdict.outcome,
        "protocol_used": verdict.protocol_used,
        "rounds_completed": verdict.rounds_completed,
        "stability_stopped": verdict.stability_stopped,
        "dissent": list(verdict.dissent),
        "vote_count": len(verdict.votes),
        "verdict_hash": _hash_excerpt(verdict.to_dict()),
    }
    if view is not None:
        payload["view_format"] = view.format
        payload["view_hash"] = _hash_excerpt(view.to_dict())

    kwargs: dict[str, Any] = {
        "actor": actor,
        "module": "NIZAM__companion.council",
        "privacy_class": "strict_local",
        "trace_id": trace_id or verdict.trace_id,
    }
    if root is not None:
        kwargs["root"] = root

    council_row = ledger_writer.append(
        "COUNCIL_LEDGER",
        payload=payload,
        action="council_verdict",
        **kwargs,
    )

    event_payload = {
        "event": "council_verdict_recorded",
        "trace_id": verdict.trace_id,
        "motion_id": motion.motion_id,
        "verdict_id": verdict.verdict_id,
        "outcome": verdict.outcome,
        "council_row_id": council_row["row_id"],
        "hash_excerpt": payload["verdict_hash"],
        "note": f"Council verdict for {motion.title}",
    }
    event_row = ledger_writer.append(
        "EVENT_LEDGER",
        payload=event_payload,
        action="council_verdict_excerpt",
        **kwargs,
    )
    return {"council_row": council_row, "event_row": event_row}
