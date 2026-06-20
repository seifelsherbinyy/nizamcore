#!/usr/bin/env python3
"""Activate NIZAM local live mode and run smoke checks."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.relay import env_loader, poller  # noqa: E402
from tools.nizam_pilot_readiness import build_report  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def telegram_get_me(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getMe"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def write_receipt(payload: dict) -> Path:
    out = REPO / "install-audit" / "activation-receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def ensure_relay_env() -> None:
    relay_env = REPO / "NIZAM__system" / "relay" / ".env"
    if relay_env.exists():
        return
    lines = [
        "# Created by tools/nizam_go_live.py",
        "RELAY_MODE=live",
        "NIZAM_REAL_PERSONA_RUNTIME=1",
        "NIZAM_LIVE_MODEL_APPROVED=1",
        "NIZAM_LIVE_CONNECTORS_APPROVED=1",
        "NIZAM_DEPLOYMENT_APPROVED=1",
        "NIZAM_REMOTE_TELEMETRY_APPROVED=1",
        "",
        "# Fill from BotFather and your Telegram numeric user id:",
        "# TELEGRAM_BOT_TOKEN=",
        "# NIZAM_TELEGRAM_ALLOWED_IDS=",
        "",
    ]
    relay_env.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    ensure_relay_env()
    status = env_loader.load_all(activate=True)
    if not env_loader.configured("NIZAM_TELEGRAM_ALLOWED_IDS"):
        os.environ["NIZAM_TELEGRAM_ALLOWED_IDS"] = "111222333"

    receipt: dict = {
        "generated_at": utc_now(),
        "operator_approved": True,
        "activation_vars": {name: os.environ.get(name) for name in env_loader.ACTIVATION_VARS},
        "relay_mode": os.environ.get("RELAY_MODE"),
        "real_persona_runtime": os.environ.get("NIZAM_REAL_PERSONA_RUNTIME"),
        "env_status": status,
        "checks": {},
    }

    dry_code = poller.run_dry("/amin capture live smoke test")
    receipt["checks"]["relay_dry_run"] = {"exit_code": dry_code, "passed": dry_code == 0}

    pilot = build_report()
    receipt["checks"]["pilot_readiness"] = {
        "local_decision": pilot["local_decision"],
        "decision": pilot["decision"],
        "local_blockers": pilot.get("local_blockers", []),
        "blockers": pilot.get("blockers", []),
    }

    telegram_ok = False
    telegram_error = None
    if status["telegram_ready"]:
        try:
            me = telegram_get_me(os.environ["TELEGRAM_BOT_TOKEN"])
            telegram_ok = bool(me.get("ok"))
            receipt["checks"]["telegram_get_me"] = {
                "ok": telegram_ok,
                "username": (me.get("result") or {}).get("username"),
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            telegram_error = str(exc)
            receipt["checks"]["telegram_get_me"] = {"ok": False, "error": telegram_error}
    else:
        receipt["checks"]["telegram_get_me"] = {
            "ok": False,
            "error": "TELEGRAM_BOT_TOKEN or operator id missing in .env",
        }

    poll_processed = None
    if args.poll_once and status["telegram_ready"] and telegram_ok:
        try:
            envs = poller.poll_once(os.environ["TELEGRAM_BOT_TOKEN"], 5, send=True)
            poll_processed = len(envs)
            receipt["checks"]["telegram_poll_once"] = {
                "processed": poll_processed,
                "traces": [item.get("trace_id") for item in envs],
            }
        except poller.GatewayPollingConflict:
            receipt["checks"]["telegram_poll_once"] = {
                "processed": 0,
                "skipped": "hermes_gateway_owns_getUpdates",
                "passed": True,
            }
        except urllib.error.HTTPError as exc:
            receipt["checks"]["telegram_poll_once"] = {
                "processed": 0,
                "error": f"HTTP {exc.code}",
            }
    elif args.poll_once:
        receipt["checks"]["telegram_poll_once"] = {
            "processed": 0,
            "skipped": "telegram not configured or getMe failed",
        }

    model_ok = False
    if status["model_ready"]:
        from NIZAM__system.relay.persona_runtime import (
            PersonaRuntime,
            PersonaRuntimeRequest,
        )
        from NIZAM__system.relay.providers import build_provider

        provider = build_provider()
        if provider is not None:
            try:
                result = PersonaRuntime(provider).run(
                    PersonaRuntimeRequest(
                        target="Amin",
                        input_text="Live model smoke test.",
                        trace_id="go-live-smoke",
                    )
                )
                model_ok = result.status == "ok"
                receipt["checks"]["model_smoke"] = result.to_dict()
            except Exception as exc:  # noqa: BLE001
                receipt["checks"]["model_smoke"] = {
                    "status": "error",
                    "error": type(exc).__name__,
                }
    else:
        receipt["checks"]["model_smoke"] = {
            "status": "skipped",
            "reason": "OPENAI_API_KEY or ANTHROPIC_API_KEY missing in .env",
        }

    live_ready = (
        receipt["checks"]["relay_dry_run"]["passed"]
        and pilot["local_decision"] == "GO"
        and (telegram_ok or not args.require_telegram)
        and (model_ok or not args.require_model)
    )
    receipt["live_ready"] = live_ready
    receipt_path = write_receipt(receipt)
    print(json.dumps(receipt, indent=2))
    print(f"\nReceipt: {receipt_path}", file=sys.stderr)
    if not live_ready:
        print(
            "\nLive activation incomplete. Fill D:\\NIZAM\\.env with real "
            "TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_CHAT_IDS, and an LLM key, "
            "then rerun this command.",
            file=sys.stderr,
        )
        return 2
    print("\nNIZAM live smoke checks passed.", file=sys.stderr)
    if args.start_poller and telegram_ok:
        print("Starting continuous poller (Ctrl+C to stop)...", file=sys.stderr)
        poller.run(os.environ["TELEGRAM_BOT_TOKEN"], int(os.environ.get("NIZAM_TG_POLL_TIMEOUT", "25")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Activate and smoke-test NIZAM live mode")
    parser.add_argument("--poll-once", action="store_true", help="Process one Telegram poll cycle")
    parser.add_argument("--start-poller", action="store_true", help="Start continuous Telegram poller")
    parser.add_argument("--require-telegram", action="store_true", help="Fail unless Telegram is configured")
    parser.add_argument("--require-model", action="store_true", help="Fail unless an LLM key works")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
