"""Proactive Telegram scheduler and sender."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import ProactiveCandidate, PulsationMessage
from .proactive import eligible, load_proactive_policy
from .reminders import validate_sourced_reminder


DEFAULT_STATE = Path(__file__).resolve().parents[1] / "relay" / ".state" / "proactive-state.json"


def _load_state(path: Path = DEFAULT_STATE) -> dict[str, Any]:
    if not path.exists():
        return {"sent_today": [], "paused": False}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(state: dict[str, Any], path: Path = DEFAULT_STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def evaluate_candidates(
    candidates: list[ProactiveCandidate],
    *,
    now: datetime | None = None,
    sukoon_red: bool = False,
    sukoon_capacity: str = "green",
    crisis_suppress: bool = False,
    state_path: Path = DEFAULT_STATE,
) -> list[tuple[ProactiveCandidate, str, bool]]:
    current = now or datetime.now(timezone.utc)
    state = _load_state(state_path)
    sent_raw = state.get("sent_today", [])
    sent = [
        datetime.fromisoformat(item.replace("Z", "+00:00"))
        for item in sent_raw
        if isinstance(item, str)
    ]
    policy = load_proactive_policy()
    accepted: list[tuple[ProactiveCandidate, str, bool]] = []
    for candidate in candidates:
        ok, reason, tiny_mode = eligible(
            candidate,
            now=current,
            sent_today=sent,
            paused=bool(state.get("paused")),
            sukoon_red=sukoon_red,
            sukoon_capacity=sukoon_capacity,
            crisis_suppress=crisis_suppress,
            policy=policy,
        )
        if ok:
            accepted.append((candidate, reason, tiny_mode))
    return accepted


def _pulsation_to_candidate(message: PulsationMessage) -> ProactiveCandidate:
    refresh = message.context_refresh
    refs = tuple(f"pulsation:{key}" for key in refresh.sources_found) or (
        "pulsation:context_refresh",
    )
    return ProactiveCandidate(
        persona=message.agent_name,
        trigger=f"pulsation_{message.message_type}",
        relevance_score=0.85 if refresh.confidence != "low" else 0.75,
        source_refs=refs,
        expires_at="2099-01-01T00:00:00Z",
        message=message.message,
    )


def send_pulsation(
    message: PulsationMessage,
    *,
    token: str | None = None,
    chat_id: int | None = None,
    loop: str = "a",
    dry_run: bool = False,
    state_path: Path = DEFAULT_STATE,
) -> dict[str, Any]:
    from NIZAM__system.companion.pulsation import append_pulsation
    from NIZAM__system.companion.pulsation.himayah_egress import (
        should_suppress_crisis,
        tiny_mode_for_capacity,
    )

    refresh = message.context_refresh
    crisis = should_suppress_crisis(refresh)
    tiny_mode = tiny_mode_for_capacity(refresh)

    if message.message_type == "islamic_reminder" and message.agent_name == "Khaldun":
        from NIZAM__system.modes.khaldun.validator import validate_khaldun_response

        ok, reason = validate_khaldun_response(
            message.message, evidence={"tasawwuf_topic": True}
        )
        if not ok:
            ledger = append_pulsation(
                message, loop=loop, send_status=f"blocked:{reason}", dry_run=True
            )
            return {"ok": False, "reason": reason, "tiny_mode": tiny_mode, "ledger": ledger}

    if dry_run:
        ledger = append_pulsation(
            message, loop=loop, send_status="skipped_dry_run", dry_run=True
        )
        return {
            "ok": True,
            "dry_run": True,
            "tiny_mode": tiny_mode,
            "persona": message.agent_name,
            "ledger": ledger,
        }

    candidate = _pulsation_to_candidate(message)
    accepted = evaluate_candidates(
        [candidate],
        sukoon_capacity=refresh.sukoon_capacity,
        crisis_suppress=crisis,
        state_path=state_path,
    )
    if not accepted:
        reason = "crisis_suppress" if crisis else "policy_blocked"
        ledger = append_pulsation(
            message, loop=loop, send_status=f"blocked:{reason}", dry_run=True
        )
        return {
            "ok": False,
            "reason": reason,
            "tiny_mode": tiny_mode,
            "ledger": ledger,
        }

    _, _, tiny_mode = accepted[0]

    if os.environ.get("NIZAM_LIVE_CONNECTORS_APPROVED") != "1":
        return {"ok": False, "reason": "connectors_not_approved"}

    if message.message_type == "islamic_reminder" and message.agent_name == "Khaldun":
        if os.environ.get("NIZAM_KHALDUN_OUTBOUND_APPROVED") != "1":
            from NIZAM__system.modes.khaldun.reminder_composer import append_dryrun_log

            append_dryrun_log(message, reason="outbound_not_approved")
            ledger = append_pulsation(
                message, loop=loop, send_status="skipped_dry_run", dry_run=True
            )
            return {
                "ok": True,
                "dry_run": True,
                "reason": "khaldun_outbound_not_approved",
                "persona": message.agent_name,
                "ledger": ledger,
            }

    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"ok": False, "reason": "telegram_token_missing"}
    if message.message_type == "islamic_reminder" and message.agent_name != "Khaldun":
        ok, reason = validate_sourced_reminder(message.message, ())
        if not ok and reason != "missing_citation":
            return {"ok": False, "reason": reason}

    from NIZAM__system.relay import auth, poller

    ids = list(auth.whitelisted_ids())
    if chat_id is None:
        if not ids:
            return {"ok": False, "reason": "operator_id_missing"}
        chat_id = ids[0]
    poller.tg_send_message(token, chat_id, message.message)

    state = _load_state(state_path)
    sent = list(state.get("sent_today", []))
    sent.append(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    state["sent_today"] = sent[-10:]
    _save_state(state, state_path)

    ledger = append_pulsation(message, loop=loop, send_status="sent", dry_run=False)
    return {
        "ok": True,
        "chat_id": chat_id,
        "persona": message.agent_name,
        "tiny_mode": tiny_mode,
        "ledger": ledger,
    }


def send_proactive(
    candidate: ProactiveCandidate,
    *,
    token: str | None = None,
    chat_id: int | None = None,
    state_path: Path = DEFAULT_STATE,
) -> dict[str, Any]:
    if os.environ.get("NIZAM_LIVE_CONNECTORS_APPROVED") != "1":
        return {"ok": False, "reason": "connectors_not_approved"}
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"ok": False, "reason": "telegram_token_missing"}
    if candidate.persona.lower() == "reminder":
        ok, reason = validate_sourced_reminder(
            candidate.message, tuple(candidate.source_refs)
        )
        if not ok:
            return {"ok": False, "reason": reason}
    if candidate.persona == "Khaldun":
        from NIZAM__system.modes.khaldun.validator import validate_khaldun_response

        ok, reason = validate_khaldun_response(
            candidate.message, evidence={"tasawwuf_topic": True}
        )
        if not ok:
            return {"ok": False, "reason": reason}
        if os.environ.get("NIZAM_KHALDUN_OUTBOUND_APPROVED") != "1":
            return {"ok": False, "reason": "khaldun_outbound_not_approved"}
    from NIZAM__system.relay import auth, poller

    ids = list(auth.whitelisted_ids())
    if chat_id is None:
        if not ids:
            return {"ok": False, "reason": "operator_id_missing"}
        chat_id = ids[0]
    poller.tg_send_message(token, chat_id, candidate.message)
    state = _load_state(state_path)
    sent = list(state.get("sent_today", []))
    sent.append(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    state["sent_today"] = sent[-10:]
    _save_state(state, state_path)
    return {"ok": True, "chat_id": chat_id, "persona": candidate.persona}


def run_hourly_evaluation(
    candidates: list[ProactiveCandidate],
    *,
    dry_run: bool = False,
    now: datetime | None = None,
    state_path: Path = DEFAULT_STATE,
) -> dict[str, Any]:
    accepted = evaluate_candidates(candidates, now=now, state_path=state_path)
    if not accepted:
        return {"sent": 0, "evaluated": len(candidates), "accepted": 0}
    if dry_run:
        return {
            "sent": 0,
            "evaluated": len(candidates),
            "accepted": len(accepted),
            "dry_run": True,
        }
    sent = 0
    for candidate, _reason, _tiny in accepted[:1]:
        result = send_proactive(candidate, state_path=state_path)
        if result.get("ok"):
            sent += 1
    return {"sent": sent, "evaluated": len(candidates), "accepted": len(accepted)}
