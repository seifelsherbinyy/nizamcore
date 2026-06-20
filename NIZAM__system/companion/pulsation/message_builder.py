"""Rule-based pulsation message templates (no LLM)."""
from __future__ import annotations

import json
from pathlib import Path

from ..contracts import ContextRefresh, PulsationMessage, utc_now

REPO = Path(__file__).resolve().parents[3]
PERSONAS = REPO / "NIZAM__system" / "agent_personas.json"

INSPECTED_LABELS = {
    "yawmiyat_journal": "YAWMIYAT journal",
    "witness_reflection": "Witness reflection",
    "pulse_entries": "pulse log",
    "whoop_badan": "WHOOP/BADAN metrics",
    "sukoon_capacity": "SUKOON capacity",
    "open_loops": "open loops",
    "active_decisions": "active decisions",
    "thabat_summary": "EVENT ledger continuity",
    "recent_interactions": "recent interactions",
}


def _agent_role(codename: str) -> str:
    if not PERSONAS.exists():
        return "NIZAM companion"
    try:
        payload = json.loads(PERSONAS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "NIZAM companion"
    for agent in payload.get("agents", []):
        if agent.get("codename") == codename:
            return str(agent.get("role") or agent.get("function") or "NIZAM companion")
    return "NIZAM companion"


def _inspected_sentence(refresh: ContextRefresh) -> str:
    labels = [INSPECTED_LABELS.get(key, key) for key in refresh.sources_checked]
    return "I checked " + ", ".join(labels) + "."


def _fresh_fact_lines(refresh: ContextRefresh) -> list[str]:
    lines: list[str] = []
    snaps = refresh.source_snapshots

    if "whoop_badan" in refresh.sources_found:
        metrics = snaps.get("whoop_badan", {}).get("metrics") or {}
        parts = []
        for key in ("recovery", "hrv", "strain"):
            if key in metrics:
                parts.append(f"{key} {metrics[key]}")
        if parts:
            lines.append("Fresh WHOOP/BADAN: " + ", ".join(parts) + ".")

    if "pulse_entries" in refresh.sources_found:
        band = snaps.get("pulse_entries", {}).get("capacity_band")
        recovery = snaps.get("pulse_entries", {}).get("recovery")
        if recovery is not None:
            detail = f"recovery {recovery}%"
            if band:
                detail += f" ({band} band)"
            lines.append(f"Fresh pulse log: {detail}.")

    if "yawmiyat_journal" in refresh.sources_found:
        entry_date = snaps.get("yawmiyat_journal", {}).get("entry_date")
        if entry_date:
            lines.append(f"Fresh journal entry dated {entry_date} (title only; body not quoted).")

    if "witness_reflection" in refresh.sources_found:
        session_type = snaps.get("witness_reflection", {}).get("session_type")
        capacity = snaps.get("witness_reflection", {}).get("capacity_level")
        if session_type or capacity:
            parts = [p for p in (session_type, f"capacity {capacity}" if capacity else None) if p]
            lines.append("Fresh Witness reflection: " + ", ".join(parts) + ".")

    if "open_loops" in refresh.sources_found:
        count = snaps.get("open_loops", {}).get("open_loop_count", 0)
        if count:
            lines.append(f"{count} open loop(s) on record.")

    if "active_decisions" in refresh.sources_found:
        count = snaps.get("active_decisions", {}).get("decision_count", 0)
        if count:
            lines.append(f"{count} recent decision(s) logged.")

    if "thabat_summary" in refresh.sources_found:
        actions = snaps.get("thabat_summary", {}).get("recent_actions") or []
        if actions:
            lines.append("Recent continuity actions: " + ", ".join(actions[-3:]) + ".")

    if "recent_interactions" in refresh.sources_found:
        count = snaps.get("recent_interactions", {}).get("interaction_count", 0)
        if count:
            lines.append(f"{count} recent interaction(s) in the local runtime log.")

    if not lines:
        lines.append("No fresh verified context in the current windows.")
    return lines


def _focus_trigger(
    agent: str,
    refresh: ContextRefresh,
    *,
    tiny_mode: bool,
) -> str:
    if tiny_mode:
        return "One small next step only — pick the lightest item you can finish in ten minutes."

    snaps = refresh.source_snapshots
    if agent == "Hayat" and "whoop_badan" in refresh.sources_found:
        return "Notice how recovery and strain line up today before you schedule deep work."
    if agent == "Hayat" and "pulse_entries" in refresh.sources_found:
        return "Align today's plan with the logged capacity band."
    if agent == "Sadiq" and "yawmiyat_journal" in refresh.sources_found:
        return "Continue the thread from your latest journal entry — one sentence is enough."
    if "open_loops" in refresh.sources_found:
        count = snaps.get("open_loops", {}).get("open_loop_count", 0)
        if count:
            return f"Pick one open loop ({count} waiting) and either close it or schedule it."
    if "active_decisions" in refresh.sources_found:
        return "Review one recent decision and confirm it still holds."
    return "Choose one priority for the next block and write it down."


def build_companion_checkin(
    refresh: ContextRefresh,
    *,
    agent_name: str | None = None,
    tiny_mode: bool = False,
) -> PulsationMessage:
    from .routing import pick_agent

    agent = agent_name or pick_agent(refresh)
    role = _agent_role(agent)
    fact_lines = _fresh_fact_lines(refresh)
    focus = _focus_trigger(agent, refresh, tiny_mode=tiny_mode)

    if tiny_mode:
        body = (
            f"I'm {agent}, your {role}.\n"
            f"{_inspected_sentence(refresh)}\n"
            "Capacity looks limited — keeping this tiny.\n"
            f"{fact_lines[0]}\n"
            f"Focus: {focus}"
        )
    else:
        body = (
            f"I'm {agent}, your {role}.\n"
            f"{_inspected_sentence(refresh)}\n"
            + "\n".join(fact_lines)
            + f"\nFocus: {focus}"
        )

    return PulsationMessage(
        message_type="companion_checkin",
        agent_name=agent,
        agent_role=role,
        generated_at=utc_now(),
        context_refresh=refresh,
        message=body,
        focus_trigger=focus,
        requires_user_reply=False,
    )


def build_islamic_reminder_placeholder(refresh: ContextRefresh) -> PulsationMessage:
    """Build Khaldun Islamic reminder or fall back to disabled placeholder."""
    try:
        from NIZAM__system.modes.khaldun.context_linker import summarize_seif_context
        from NIZAM__system.modes.khaldun.reminder_composer import (
            append_dryrun_log,
            compose_khaldun_reminder,
        )
        from NIZAM__system.companion.pulsation.himayah_egress import tiny_mode_for_capacity

        summary = summarize_seif_context(refresh)
        tiny = tiny_mode_for_capacity(refresh)
        message, err = compose_khaldun_reminder(summary, refresh, tiny_mode=tiny)
        if message is not None:
            append_dryrun_log(message, reason="loop_b_compose")
            return message
        if err:
            focus = f"Reminder blocked: {err}"
            return PulsationMessage(
                message_type="islamic_reminder",
                agent_name="Khaldun",
                agent_role=_agent_role("Khaldun"),
                generated_at=utc_now(),
                context_refresh=refresh,
                message=(
                    f"خلدون — تذكير داخلي فقط (لم يُرسل): {err}\n"
                    "Focus: راجع السياق محلياً."
                ),
                focus_trigger=focus,
                requires_user_reply=False,
            )
    except Exception:
        pass

    focus = "Islamic reminder loop is disabled until you configure sources."
    body = (
        "I'm Ammar, your STEWARD — egress firewall.\n"
        f"{_inspected_sentence(refresh)}\n"
        "Islamic reminder content is placeholder-only (enabled: false).\n"
        f"Focus: {focus}"
    )
    return PulsationMessage(
        message_type="islamic_reminder",
        agent_name="Ammar",
        agent_role=_agent_role("Ammar"),
        generated_at=utc_now(),
        context_refresh=refresh,
        message=body,
        focus_trigger=focus,
        requires_user_reply=False,
    )
