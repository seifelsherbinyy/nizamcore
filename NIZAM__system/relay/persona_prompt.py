"""Build system prompts and deterministic replies for NIZAM companion codenames."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPO / "NIZAM__system" / "agent_personas.json"

DETERMINISTIC_ONLY = frozenset({"Ammar", "Yusra"})
LLM_PERSONAS = frozenset(
    {
        "Amin",
        "Salman",
        "Hazim",
        "Khalid",
        "Tariq",
        "Khaldun",
        "Tahir",
        "Hayat",
        "Sadiq",
        "NIZAM",
    }
)

GUARDRAILS: dict[str, str] = {
    "Khalid": (
        "Context: NIZAM operator tactical planning for Seif (software/life pillars). "
        "Never use military, war, battalion, sector, or combat metaphors."
    ),
    "Tariq": (
        "Context: long-horizon strategy for Seif's NIZAM system and life pillars — "
        "not literal warfare."
    ),
    "Hayat": (
        "Report biometrics objectively. Never diagnose. Never claim subjective feelings."
    ),
    "Ammar": "Governance only — ALLOW/BLOCK/RECORDED format.",
    "Yusra": "Recovery voice only — one gentle line in Arabic or English, never initiate planning.",
}


@lru_cache(maxsize=1)
def _agents_by_codename() -> dict[str, dict[str, Any]]:
    payload = json.loads(AGENTS_PATH.read_text(encoding="utf-8"))
    agents = list(payload.get("agents") or [])
    by_name = {str(a["codename"]): a for a in agents if a.get("codename")}
    by_name.setdefault(
        "NIZAM",
        {
            "codename": "NIZAM",
            "persona_file": "NIZAM__system/personas/NIZAM.json",
            "role": "Conversational layer — counseling-grade front-end",
            "contract": (
                "Warm, direct, unhurried. Honesty over comfort. "
                "No shame language. Not therapist or clergy."
            ),
        },
    )
    return by_name


def _load_persona(path: str) -> dict[str, Any]:
    full = REPO / path.replace("/", os.sep)
    if not full.exists():
        return {}
    return json.loads(full.read_text(encoding="utf-8"))


def is_llm_persona(codename: str) -> bool:
    return codename in LLM_PERSONAS


def is_deterministic_persona(codename: str) -> bool:
    return codename in DETERMINISTIC_ONLY


def build_persona_system_prompt(codename: str) -> str | None:
    if codename == "Khaldun":
        from NIZAM__system.modes.khaldun.runtime_prompt import build_khaldun_system_prompt

        return build_khaldun_system_prompt()

    if is_deterministic_persona(codename):
        return None

    agent = _agents_by_codename().get(codename)
    if not agent:
        return None

    persona = _load_persona(str(agent.get("persona_file") or ""))
    contract = str(agent.get("contract") or "")
    role = str(agent.get("role") or persona.get("role") or "")
    tone = str(persona.get("tone") or "")
    mode = str(persona.get("mode") or "")
    voice = str(persona.get("voice_constraints") or "")
    guard = GUARDRAILS.get(codename, "")

    parts = [
        f"You are {codename}, a NIZAM companion speaking to operator Seif.",
        f"Role: {role}",
        f"Mode: {mode}",
        f"Tone: {tone}",
        f"Contract: {contract}",
    ]
    if voice:
        parts.append(f"Voice constraints: {voice}")
    if guard:
        parts.append(guard)
    parts.append(
        "Reply in 2–5 sentences for Telegram. Stay in persona. "
        "Do not mention being an AI model."
    )
    return "\n".join(parts)


def build_deterministic_reply(codename: str, input_text: str) -> str:
    text = input_text.strip()
    if codename == "Ammar":
        if "cost" in text.lower():
            return "COST: within soft ceiling. RECORDED. No kill-switch."
        if "ledger" in text.lower():
            return "LEDGER: tail_ok=true. ALLOW append."
        return (
            "GOVERNOR: egress gated by HIMAYAH. "
            "Khaldun outbound requires NIZAM_KHALDUN_OUTBOUND_APPROVED=1."
        )
    if codename == "Yusra":
        if "red" in text.lower():
            return "Yusra: بس… ربّنا يوسّع صدرك. خطوة واحدة صغيرة، وكفاية النهارده."
        return "Yusra: خُذ نفسًا. اليوم مش محكمة على الإنجاز."
    return f"{codename}: acknowledged."
