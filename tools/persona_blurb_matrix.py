#!/usr/bin/env python3
"""Generate 12 agents × 3 persona-fit outbound blurbs for operator review."""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.relay import env_loader  # noqa: E402
from NIZAM__system.relay.persona_runtime import PersonaRuntimeRequest  # noqa: E402
from NIZAM__system.relay.providers import build_provider  # noqa: E402

AGENTS_PATH = REPO / "NIZAM__system" / "agent_personas.json"
OUT_PATH = REPO / "install-audit" / "persona-blurb-matrix.json"
TELEGRAM_MAX_LEN = 4096
TELEGRAM_BLURB_MAX = 220


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _truncate_blurb(text: str, limit: int = TELEGRAM_BLURB_MAX) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    chunk = cleaned[: limit + 1]
    for sep in (". ", "؟ ", "! ", "… ", "\n"):
        idx = chunk.rfind(sep)
        if idx >= int(limit * 0.45):
            return chunk[: idx + len(sep.rstrip())].strip() + "…"
    return cleaned[:limit].rstrip() + "…"


def format_matrix_telegram_html(report: dict[str, Any]) -> list[str]:
    """Build Telegram HTML messages (4096-safe chunks)."""
    results = list(report.get("results") or [])
    header = (
        "<b>Persona blurb matrix</b>\n"
        f"{report.get('total_cases', len(results))} cases\n"
        f"<i>{_html_escape(str(report.get('provider') or 'n/a'))} / "
        f"{_html_escape(str(report.get('model') or 'n/a'))}</i>\n"
        f"<code>{_html_escape(str(report.get('generated_at') or ''))}</code>"
    )
    blocks: list[str] = [header]
    for codename in PROMPTS:
        sample = next(
            (r for r in results if r.get("codename") == codename and r.get("scenario") == 1),
            None,
        )
        if sample is None:
            continue
        blurb = _truncate_blurb(str(sample.get("blurb") or ""))
        blocks.append(
            f"\n\n<b>{_html_escape(codename)}</b>\n{_html_escape(blurb)}"
        )

    messages: list[str] = []
    current = ""
    for block in blocks:
        if not current:
            candidate = block
        else:
            candidate = current + block
        if len(candidate) > TELEGRAM_MAX_LEN - 20 and current:
            messages.append(current)
            current = block.lstrip()
        else:
            current = candidate
    if current:
        messages.append(current)
    return messages or [header]


def send_telegram_html_messages(
    token: str,
    chat_id: int,
    messages: list[str],
) -> int:
    import urllib.request

    sent = 0
    for text in messages:
        payload = json.dumps(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30):
            sent += 1
    return sent

PROMPTS: dict[str, list[str]] = {
    "Amin": [
        "Dump: meeting ran long, inbox 40, promised Ahmed a reply, low energy, idea for NIZAM router stuck mid-thought.",
        "Worries: falling behind on Q2 plan, guilt about not calling family, scattered notes everywhere.",
        "Open loops: renew domain, fix WHOOP sync, reply to accountant, unclear priority on HIKMAH rollout.",
    ],
    "Salman": [
        "Brainstorm: should I narrow NIZAM to companion-only for 90 days or keep full pillar map?",
        "Co-think: three paths for weekly synthesis — Sunday only, daily tiny, or on-demand /hikmah.",
        "Help me see angles I'm missing before I commit to Khaldun outbound reminders.",
    ],
    "Hazim": [
        "Red-team: I'm launching Khaldun live reminders this week — what's the weakest assumption?",
        "Steelman the case AGAINST expanding proactive send limits to 10/day.",
        "Attack this plan: rely on OpenRouter for all 12 persona blurbs without per-agent ZDR audit.",
    ],
    "Khalid": [
        "Tactical: what are the next 3 battles for June if SUKOON stays green?",
        "Break Q3 into sequenced moves for HIKMAH mode hardening vs Telegram polish.",
        "I have 5 initiatives — force rank for this quarter with time boxes.",
    ],
    "Tariq": [
        "Long war: does daily Telegram pulsation align with a 15-year sovereignty map?",
        "Which strategic pillar does Islamic Cosmic Wisdom mode serve — and which does it risk diluting?",
        "Patience check: am I over-building agents before operator workflow is stable?",
    ],
    "Khaldun": [
        "/hikmah explain tawakkul vs tawakul in Egyptian Arabic, gentle, not fatwa.",
        "Explore how ayat on creation relate to cosmology — classify claims, stay Sunni-safe.",
        "Short reminder for Seif: SUKOON green, one dhikr step, no shame.",
    ],
    "Tahir": [
        "Intel scout: what moved this week in open-source agent frameworks (LangGraph, CrewAI, etc.)?",
        "Signals: any EU MDR or FDA digital-health guidance updates worth a flag?",
        "Brief: competitor pattern — proactive AI companions with religious/cultural modes.",
    ],
    "Hayat": [
        "Biometric witness: recovery 42%, HRV 28ms below baseline, strain 14.2 — report objectively.",
        "Sleep debt 4 nights under 6h, resting HR elevated — facts only, no diagnosis.",
        "WHOOP sync gap 48h — state what is known vs missing from signals.",
    ],
    "Sadiq": [
        "Journal mirror: today felt productive but hollow — hold space, reflect, don't advise.",
        "Weekly reflection: council skipped, Khaldun shipped, operator tired — capture tone.",
        "Ambiguous feeling after live Telegram test — name what happened without fixing.",
    ],
    "Yusra": [
        "[SUKOON yellow] operator capacity downshift — render one soft supportive line.",
        "[SUKOON red supportive_reflection] operator overwhelmed — one minimal recovery line.",
        "[tiny_mode] after long build session — single gentle nudge, never initiate planning.",
    ],
    "Ammar": [
        "[governor-status] report egress gates and connector approval flags.",
        "[cost] soft ceiling check after 36 persona LLM calls.",
        "[ledger-verify] tail integrity OK — state ALLOW/RECORDED format.",
    ],
    "NIZAM": [
        "Check-in: long build day, Khaldun shipped, tired but satisfied — counsel briefly.",
        "Assess: which pillar got attention this week vs which was orphaned?",
        "Consult: should I pause new features and stabilize Telegram + pulsation for 2 weeks?",
    ],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_agents() -> list[dict[str, Any]]:
    payload = json.loads(AGENTS_PATH.read_text(encoding="utf-8"))
    return list(payload.get("agents") or [])


def _load_persona(path: str) -> dict[str, Any]:
    full = REPO / path.replace("/", os.sep)
    if not full.exists():
        return {}
    return json.loads(full.read_text(encoding="utf-8"))


def _build_system_prompt(agent: dict[str, Any], persona: dict[str, Any]) -> str:
    codename = str(agent.get("codename") or "")
    if codename == "Khaldun":
        from NIZAM__system.modes.khaldun.runtime_prompt import build_khaldun_system_prompt

        base = build_khaldun_system_prompt()
        return (
            base
            + "\n\nOutput a single Telegram-ready blurb (under 120 words). "
            "Match Egyptian gentle voice where Arabic is used."
        )

    contract = str(agent.get("contract") or "")
    role = str(agent.get("role") or persona.get("role") or "")
    tone = str(persona.get("tone") or "")
    mode = str(persona.get("mode") or "")
    voice = str(persona.get("voice_constraints") or "")
    extra = f"\nVoice constraints: {voice}" if voice else ""
    return (
        f"You are {codename}, a NIZAM companion.\n"
        f"Role: {role}\n"
        f"Mode: {mode}\n"
        f"Tone: {tone}\n"
        f"Contract: {contract}{extra}\n\n"
        "Write ONE outbound Telegram blurb (2–5 sentences, under 120 words). "
        "Address the operator (Seif), not another agent codename. "
        "Stay strictly in persona. No meta commentary about being an AI."
    )


def _deterministic_blurb(codename: str, prompt: str) -> str:
    if codename == "Ammar":
        if "cost" in prompt.lower():
            return (
                "COST: within soft ceiling. RECORDED. "
                "No kill-switch. strict_local egress unchanged."
            )
        if "ledger" in prompt.lower():
            return "LEDGER: tail_ok=true. ALLOW append. hash chain verified."
        return (
            "GOVERNOR: connectors=config_only unless NIZAM_LIVE_CONNECTORS_APPROVED=1. "
            "Khaldun outbound requires NIZAM_KHALDUN_OUTBOUND_APPROVED=1. BLOCK otherwise."
        )
    if codename == "Yusra":
        if "red" in prompt.lower():
            return "Yusra: بس… ربّنا يوسّع صدرك. خطوة واحدة صغيرة، وكفاية النهارده."
        if "tiny" in prompt.lower():
            return "Yusra: نفس عميق. مفيش استعجال. ربنا معاك."
        return "Yusra: خُذ نفسًا. اليوم مش محكمة على الإنجاز."

    return f"[deterministic] {codename}: {prompt[:80]}"


def _invoke_llm(
    provider: Any,
    *,
    codename: str,
    system: str,
    user_text: str,
) -> dict[str, Any]:
    request = PersonaRuntimeRequest(
        target=codename,
        input_text=user_text,
        trace_id=str(uuid.uuid4()),
        timeout_seconds=45.0,
        system_prompt=system,
    )
    started = datetime.now(timezone.utc)
    payload = provider.invoke(request)
    latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    reply = str(payload.get("reply") or "").strip()
    if codename == "Khaldun":
        from NIZAM__system.modes.khaldun.validator import validate_khaldun_response

        ok, reason = validate_khaldun_response(reply, evidence={"tasawwuf_topic": True})
        if not ok:
            reply = f"خلدون (blocked:{reason}): جرّب صياغة أ safer — {user_text[:60]}"
    return {
        "blurb": reply,
        "provider": provider.name,
        "model": provider.model,
        "latency_ms": latency_ms,
        "input_tokens": int(payload.get("input_tokens", 0)),
        "output_tokens": int(payload.get("output_tokens", 0)),
    }


def run_matrix(*, send_telegram_summary: bool = False) -> dict[str, Any]:
    env_loader.load_all(activate=True)
    os.environ.setdefault("NIZAM_REAL_PERSONA_RUNTIME", "1")
    os.environ.setdefault("NIZAM_LIVE_MODEL_APPROVED", "1")

    provider = build_provider()
    agents = _load_agents()
    by_codename = {a["codename"]: a for a in agents if a.get("codename")}
    by_codename.setdefault(
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

    results: list[dict[str, Any]] = []
    llm_agents = {"Amin", "Khaldun"}
    deterministic_only = {"Ammar", "Yusra"}

    for codename, prompts in PROMPTS.items():
        agent = by_codename.get(codename, {"codename": codename})
        persona = _load_persona(str(agent.get("persona_file") or ""))
        system = _build_system_prompt(agent, persona)

        for idx, prompt in enumerate(prompts, start=1):
            row: dict[str, Any] = {
                "codename": codename,
                "scenario": idx,
                "prompt": prompt,
                "mode": "deterministic",
            }
            if codename in deterministic_only:
                row["blurb"] = _deterministic_blurb(codename, prompt)
            elif provider is None:
                row["blurb"] = f"[stub] {codename}: would reply to ({len(prompt)} chars)."
                row["mode"] = "stub"
                row["reason"] = "no_llm_provider"
            else:
                try:
                    out = _invoke_llm(
                        provider, codename=codename, system=system, user_text=prompt
                    )
                    row.update(out)
                    row["mode"] = "llm"
                except Exception as exc:
                    row["blurb"] = f"[error] {codename}: {type(exc).__name__}"
                    row["mode"] = "error"
                    row["reason"] = str(exc)[:200]

            results.append(row)

    report = {
        "generated_at": _utc_now(),
        "agent_count": len(PROMPTS),
        "scenario_count": 3,
        "total_cases": len(results),
        "provider": getattr(provider, "name", None) if provider else None,
        "model": getattr(provider, "model", None) if provider else None,
        "results": results,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if send_telegram_summary and os.environ.get("NIZAM_LIVE_CONNECTORS_APPROVED") == "1":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if token:
            from NIZAM__system.relay import auth

            ids = list(auth.whitelisted_ids())
            if ids:
                messages = format_matrix_telegram_html(report)
                sent = send_telegram_html_messages(token, ids[0], messages)
                report["telegram_summary_sent"] = True
                report["telegram_messages_sent"] = sent

    return report


def send_report_to_telegram(report_path: Path = OUT_PATH) -> dict[str, Any]:
    env_loader.load_all(activate=True)
    if not report_path.exists():
        raise FileNotFoundError(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")
    from NIZAM__system.relay import auth

    ids = list(auth.whitelisted_ids())
    if not ids:
        raise RuntimeError("NIZAM_TELEGRAM_ALLOWED_IDS missing")
    messages = format_matrix_telegram_html(report)
    sent = send_telegram_html_messages(token, ids[0], messages)
    return {"ok": True, "messages_sent": sent, "chat_id": ids[0]}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="12×3 persona blurb matrix")
    parser.add_argument(
        "--telegram-summary",
        action="store_true",
        help="Send HTML-formatted summary to operator Telegram after matrix run",
    )
    parser.add_argument(
        "--telegram-from-report",
        action="store_true",
        help="Send HTML summary from existing install-audit/persona-blurb-matrix.json",
    )
    args = parser.parse_args()
    if args.telegram_from_report:
        result = send_report_to_telegram()
        print(json.dumps(result, indent=2))
        return 0
    report = run_matrix(send_telegram_summary=args.telegram_summary)
    print(json.dumps({
        "out": str(OUT_PATH),
        "total": report["total_cases"],
        "provider": report.get("provider"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
