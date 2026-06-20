"""Skill activation router for operator commands and capability packs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
INDEX = Path(__file__).resolve().parent / "index.json"


def load_registry(path: Path = INDEX) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_command(text: str, *, registry: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Map a Telegram command to a skill entry."""
    reg = registry or load_registry()
    cmd = (text or "").strip().split()[0].lower()
    for skill in reg.get("skills", []):
        skill_cmd = skill.get("command")
        if skill_cmd and cmd == skill_cmd.lower():
            return skill
    return None


def handle_command(text: str) -> dict[str, Any]:
    """Return a dry-run envelope for operator commands (no LLM)."""
    skill = resolve_command(text)
    if skill is None:
        return {"ok": False, "reason": "unknown_command", "text": text}

    if skill["id"] == "council_review":
        from NIZAM__system.companion.council.triggers import should_convene_council
        from NIZAM__system.companion.pulsation.context_refresh import refresh_context

        refresh = refresh_context()
        return {
            "ok": True,
            "skill_id": skill["id"],
            "command": skill["command"],
            "council_required": True,
            "convene": should_convene_council(
                refresh, pulse_kind="operator_request", operator_requested=True
            ),
            "reply_stub": (
                "Council review requested. Full deliberation runs on operator command only; "
                "reply with your motion question to proceed."
            ),
            "privacy_ceiling": skill["privacy_ceiling"],
        }

    return {
        "ok": True,
        "skill_id": skill["id"],
        "reply_stub": f"Skill {skill['name']} acknowledged (stub).",
    }
