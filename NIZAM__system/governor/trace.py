"""trace.py — trace_id end-to-end logging + chain summary (E1.5).

A `trace_id` is generated at coordinator entry and threaded through every
`agent_message` envelope, every governor decision, and every ledger row
for one operator turn. This module provides:

  * generate_trace_id() — UUID4.
  * chain_summary(trace_id) — reconstructs the chain from EVENT_LEDGER
    rows tagged with that trace_id, returning a compact list of
    (from_agent, to_agent, action, ts) tuples.
  * to_markdown(trace_id) — renders the chain summary as a short
    bullet list, used inside Telegram operator-confirm messages.

Pure stdlib. Reads append-only EVENT_LEDGER from disk; never writes.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

_LEDGER = (
    Path(__file__).resolve().parents[1] / "ledgers" / "EVENT_LEDGER.jsonl"
)


def generate_trace_id() -> str:
    return str(uuid.uuid4())


def _iter_event_rows() -> list[dict[str, Any]]:
    """Yield decoded EVENT_LEDGER rows in append order.

    Skips malformed lines silently — those are surfaced by
    ledger_writer.verify_chain() elsewhere.
    """
    if not _LEDGER.exists():
        return []
    out: list[dict[str, Any]] = []
    with _LEDGER.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def chain_for(trace_id: str) -> list[dict[str, Any]]:
    """Return all EVENT_LEDGER rows that carry this trace_id, in order."""
    return [r for r in _iter_event_rows()
            if r.get("trace_id") == trace_id
            or (isinstance(r.get("payload"), dict)
                and r["payload"].get("trace_id") == trace_id)]


def chain_summary(trace_id: str) -> dict[str, Any]:
    """Compact summary of a trace.

    Output:
        {
          "trace_id": "...",
          "hops": [
            {"ts": "...", "actor": "Operator|Ammar|...",
             "action": "...", "target": "..."},
            ...
          ],
          "first_ts": "...",
          "last_ts": "...",
          "hop_count": N,
          "blocked": bool,
          "block_reasons": [str, ...],
        }
    """
    rows = chain_for(trace_id)
    hops: list[dict[str, Any]] = []
    block_reasons: list[str] = []
    for r in rows:
        payload = r.get("payload") if isinstance(r.get("payload"), dict) else {}
        target = (
            payload.get("target")
            or r.get("module")
            or "unknown"
        )
        hops.append({
            "ts": r.get("ts"),
            "actor": r.get("actor"),
            "action": r.get("action"),
            "target": target,
        })
        if payload.get("blocked") or r.get("action", "").startswith("block_"):
            br = payload.get("block_reason") or r.get("action")
            if br:
                block_reasons.append(br)
    return {
        "trace_id": trace_id,
        "hops": hops,
        "first_ts": hops[0]["ts"] if hops else None,
        "last_ts": hops[-1]["ts"] if hops else None,
        "hop_count": len(hops),
        "blocked": bool(block_reasons),
        "block_reasons": block_reasons,
    }


def to_markdown(trace_id: str, *, max_hops: int = 5) -> str:
    """Render the chain summary as a short bullet list."""
    s = chain_summary(trace_id)
    if not s["hops"]:
        return f"_trace `{trace_id[:8]}` has no recorded hops yet._"
    lines = [f"**trace** `{trace_id[:8]}…`",
             f"hops: {s['hop_count']}  ·  blocked: {s['blocked']}"]
    shown = s["hops"][-max_hops:]
    if len(s["hops"]) > max_hops:
        lines.append(f"_…showing last {max_hops} of {s['hop_count']}_")
    for h in shown:
        lines.append(
            f"- {h['ts']}  ·  **{h['actor']}** → {h['target']}  ·  {h['action']}"
        )
    if s["block_reasons"]:
        lines.append("**block reasons:** " + "; ".join(s["block_reasons"]))
    return "\n".join(lines)
