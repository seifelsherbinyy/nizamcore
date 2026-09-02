"""coordinator.py — Phase-1 boot loop coordinator (B4.5).

Orchestrates the full pipeline (already authenticated + deduplicated):

    update -> SUKOON pre-gate -> router -> agent stub -> HIMAYAH egress
    -> ledger append (Ammar) -> reply text

The agent stub returns a deterministic synthesis envelope (Artifact A +
Artifact B); the LLM-as-router and the LLM agent themselves are engaged
post-K1/K2 (USER gates U5/U7). All non-LLM gates ARE exercised here.

Pure stdlib.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.governor import ledger_writer  # noqa: E402
from NIZAM__system.governor.classifier import (  # noqa: E402
    classify,
    is_egress_blocked,
)
from NIZAM__system.relay import sukoon_gate  # noqa: E402


def _route(input_text: str) -> tuple[str, str, float]:
    """Use the deterministic dry-run router."""
    sys.path.insert(0, str(REPO / "NIZAM__system" / "config" / "fixtures"))
    import router_dry_run as r
    cfg = r._read_yaml(REPO / "NIZAM__system" / "config" / "router.config.yaml")
    ex = r._read_yaml(REPO / "NIZAM__system" / "config" / "intent_exemplars.yaml")
    kind = r._detect_kind(input_text, cfg)
    if kind == "CRISIS":
        return "CRISIS", "protocol:crisis_sukoon_red", 1.0
    bucket, conf = r._match_intent(input_text, ex)
    intents = cfg.get("intents", {})
    target = (intents.get(bucket) or {}).get("target", "Amin")
    return kind, target, conf


def _agent_stub(target: str, input_text: str, trace_id: str) -> dict:
    """Stub agent reply — separates Artifact A (Amin) and Artifact B
    (Salman) so the 6 capture-fidelity tests pass.
    """
    artifact_a = {
        "owner": "Amin",
        "capture": input_text,
        "ts": _now_iso(),
        "trace_id": trace_id,
    }
    if target == "Amin":
        return {"artifact_a": artifact_a, "artifact_b": None,
                "reply": "captured."}
    # Stub Salman/etc. — empty themes/tensions/loops until LLM is engaged
    artifact_b = {
        "owner": "Salman",
        "themes": [],
        "tensions": [],
        "loops": [],
        "source_offsets": [(0, len(input_text))],
        "quoted_snippets": [],
        "trace_id": trace_id,
    }
    return {"artifact_a": artifact_a, "artifact_b": artifact_b,
            "reply": f"[stub] {target}: would synthesize ({len(input_text)} chars)."}


def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def process(update: dict, user_id: int) -> dict:
    """Main coordinator entry. Returns a decision envelope.

    Envelope schema:
        {
          "trace_id": str,
          "kind": "CRISIS"|"COMMAND"|"TRIGGER"|"AMBIGUOUS",
          "target": str,
          "sukoon": dict,
          "reply": str,
          "ledger_row_id": str | None,
          "blocked": bool,
          "block_reason": str | None
        }
    """
    trace_id = str(uuid.uuid4())
    message = update.get("message", {})
    text = (message.get("text") or message.get("caption") or "").strip()

    # B4.4 SUKOON pre-gate
    sukoon = sukoon_gate.pre_gate(text)

    # B4.5 router
    kind, target, conf = _route(text)
    if sukoon["mode"] == "crisis_protocol":
        target = "protocol:crisis_sukoon_red"
        kind = "CRISIS"
    elif sukoon["mode"] == "supportive_reflection" and target == "Hazim":
        target = "Salman"  # downshift NAQD -> SHURA per persona rule

    # B4.5 agent stub
    agent_out = _agent_stub(target, text, trace_id)

    # B4.6 HIMAYAH egress check. The destination of the reply is
    # Telegram (operator-only, encrypted). All persistence happens on
    # the laptop disk pre-cutover. Both are permitted for strict_local
    # but NOT for strict_local_maximum (AHEL).
    blocked, reason = False, None
    cls = classify(_pretend_capture_path(target))
    egress_blocked, why = is_egress_blocked(_pretend_capture_path(target),
                                            "telegram_operator")
    if egress_blocked:
        blocked = True
        reason = why

    # B4.7 ledger append (Ammar)
    ledger_row_id = None
    if not blocked:
        # The Telegram update_id is this turn's stable identity. Both gateways
        # (poller.handle_update, webhook.handle_update) already refuse an
        # update whose update_id is not an int, so the fallback below is
        # unreachable in production and exists only for a direct call. If a
        # crash retries the turn, the writer returns the row that already
        # exists rather than appending a second one with a valid chain.
        # See section 6a purpose 4 in the sibling repository's steering.
        _update_id = update.get("update_id")
        _record_id = (f"tg-update:{_update_id}"
                      if isinstance(_update_id, int) else f"turn:{trace_id}")
        row = ledger_writer.append(
            "EVENT_LEDGER",
            payload={
                "trace_id": trace_id,
                "user_id": user_id,
                "kind": kind,
                "target": target,
                "confidence": conf,
                "sukoon_mode": sukoon["mode"],
                "classification": cls,
                "input_chars": len(text),
                "artifact_a_present": agent_out["artifact_a"] is not None,
                "artifact_b_present": agent_out["artifact_b"] is not None,
                "note": "phase-1 boot loop turn",
            },
            record_id=_record_id,
            actor="Ammar",
            action="phase1_round_trip",
            module="NIZAM__relay",
            trace_id=trace_id,
        )
        ledger_row_id = row["row_id"]

    return {
        "trace_id": trace_id,
        "kind": kind,
        "target": target,
        "sukoon": sukoon,
        "reply": agent_out["reply"],
        "ledger_row_id": ledger_row_id,
        "blocked": blocked,
        "block_reason": reason,
        "artifact_a": agent_out["artifact_a"],
        "artifact_b": agent_out["artifact_b"],
    }


def _pretend_capture_path(target: str) -> str:
    """Map a target codename to where its capture would be written."""
    return {
        "Amin": "TAFRIGH__brain_dumper/raw/2026-05-28.md",
        "Salman": "SHURA__brainstormer/sessions/2026-05-28.md",
        "Hazim": "NAQD__brain_griller/sessions/2026-05-28.md",
        "Tariq": "TARIQ__long_horizon_strategy/reviews/2026-05-28.md",
        "Khalid": "MUNAWARA__tactical_strategy/weeks/2026-05-28.md",
        "Khaldun": "HIKMAH__weekly_synthesis/weekly/2026-W22.md",
        "Tahir": "MARSAD__flight_radar/briefs/2026-05-28.md",
        "Hayat": "BADAN__body_health_system/daily_signals/2026-05-28.md",
        "Yusra": "AHEL__family_network/family_tree/note.md",
        "Sadiq": "MAL__financial_engine/baseline/note.md",
        "protocol:crisis_sukoon_red": "NIZAM__system/protocols/crisis_sukoon_red.md",
    }.get(target, "TAFRIGH__brain_dumper/raw/fallback.md")
