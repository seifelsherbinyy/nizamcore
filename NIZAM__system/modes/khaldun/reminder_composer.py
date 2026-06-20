from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from NIZAM__system.companion.contracts import ContextRefresh, PulsationMessage, utc_now

from .context_linker import SeifContextSummary
from .paths import MODE_BUNDLE
from .response_builder import fill_template
from .validator import validate_khaldun_response


def _load_mapping() -> dict[str, Any]:
    path = MODE_BUNDLE / "spiritual_reminder_mapping.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_mapping(summary: SeifContextSummary, *, tiny_mode: bool) -> dict[str, Any]:
    mappings = _load_mapping().get("mappings", [])
    haystack = " ".join(
        [
            " ".join(summary.journal_themes),
            str(summary.witness_summary.get("theme", "")),
            str(summary.pulse_summary.get("capacity_band", "")),
            summary.sukoon_capacity,
        ]
    ).lower()

    if tiny_mode or summary.sukoon_capacity in {"red", "yellow"}:
        for row in mappings:
            if row.get("signal") == "low_energy":
                return row

    for row in mappings:
        for trigger in row.get("triggers", []):
            if str(trigger).lower() in haystack:
                return row

    if summary.open_loops_count > 0:
        for row in mappings:
            if row.get("signal") == "productivity_drift":
                return row

    return mappings[0] if mappings else {}


def compose_khaldun_reminder(
    summary: SeifContextSummary,
    refresh: ContextRefresh,
    *,
    tiny_mode: bool = False,
) -> tuple[PulsationMessage | None, str | None]:
    mapping = _pick_mapping(summary, tiny_mode=tiny_mode)
    missing_note = ""
    if summary.missing_data:
        missing_note = " (بعض المصادر غ unavailable: " + ", ".join(summary.missing_data) + ")"

    context_line = "حالة اليوم: "
    if summary.pulse_summary.get("capacity_band"):
        context_line += f"سعة {summary.pulse_summary.get('capacity_band')}. "
    elif summary.sukoon_capacity != "unknown":
        context_line += f"SUKOON {summary.sukoon_capacity}. "
    else:
        context_line += "بدون بيانات حيوية حديثة."
    context_line += missing_note

    fields = {
        "greeting": "يا سيف، أنا خلدون — رفيق حكمة.",
        "context_one_liner": context_line,
        "islamic_meaning": mapping.get("islamic_meaning", "تفويض ومراقبة."),
        "one_action": mapping.get("action", "خطوة صغيرة واحدة."),
        "short_dua": mapping.get("dua_hint", "اللهم أعني على ذكرك وشكرك."),
    }

    body = fill_template("reminder", fields)
    if tiny_mode:
        body = (
            "يا سيف — تذكير خفيف.\n"
            + mapping.get("islamic_meaning", "")
            + "\n**خطوة:** "
            + mapping.get("action", "")
            + "\n**دعاء:** "
            + mapping.get("dua_hint", "")
            + "\n*ليس فتوى.*"
        )

    evidence = {"tasawwuf_topic": True}
    if summary.sukoon_capacity in {"red", "yellow"}:
        evidence["recovery_low"] = True

    ok, reason = validate_khaldun_response(body, evidence=evidence)
    if not ok:
        return None, reason

    message = PulsationMessage(
        message_type="islamic_reminder",
        agent_name="Khaldun",
        agent_role="Islamic Cosmic Wisdom companion",
        generated_at=utc_now(),
        context_refresh=refresh,
        message=body,
        focus_trigger=mapping.get("action", ""),
        requires_user_reply=False,
    )
    return message, None


def append_dryrun_log(message: PulsationMessage, *, reason: str = "composed") -> None:
    from .paths import DRYRUN_LOG

    DRYRUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "message": message.to_dict(),
    }
    with DRYRUN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
