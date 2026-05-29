"""poller.py — HERMES long-poll runner for the NIZAM relay.

The LONG-POLL alternative to webhook.py: instead of Telegram POSTing to a
public HTTPS endpoint, this process pulls updates *outbound* via
getUpdates and feeds each authorized update into the Phase-1 coordinator.
No public endpoint, no setWebhook, no domain/TLS required.

Pipeline per update:

    getUpdates --> dedup.record() --> auth.verify_user_id()
        --> coordinator.process() --> tg_send_message(reply)

Auth for long-poll is the USER_ID whitelist (auth.verify_user_id). The
webhook secret-token (CVE-2026-32980) does NOT apply to long-poll — there
is no inbound request to forge.

NOTE: the coordinator's agent is still a deterministic STUB. Replies are
canned ("captured." / "[stub] <Agent>: would synthesize ...") until the
LLM layer is engaged in the next phase. This runner proves the TRANSPORT
end-to-end; it does not yet call any model.

Modes (env RELAY_MODE):
  standby (default) — refuse to poll (Q8: standby until G4).
  live              — allow --once and the continuous loop.

CLI:
  python -m NIZAM__system.relay.poller --dry-run   # synthetic update, NO network
  python -m NIZAM__system.relay.poller --once      # one real getUpdates cycle (needs live)
  python -m NIZAM__system.relay.poller             # continuous loop (needs live)

Env:
  TELEGRAM_BOT_TOKEN          bot token from BotFather
  NIZAM_TELEGRAM_ALLOWED_IDS  comma-separated operator user_ids
  RELAY_MODE                  standby | live
  NIZAM_TG_POLL_TIMEOUT       long-poll timeout seconds (default 25)

Pure stdlib (urllib). No pip deps.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.relay import auth, coordinator, dedup  # noqa: E402

API = "https://api.telegram.org"
BLOCKED_NOTICE = "⛔ Blocked by HIMAYAH (privacy tier). Nothing was stored."


# ─── Telegram transport (monkeypatched in tests) ─────────────────
def _post(url: str, payload: dict, timeout: float) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tg_get_updates(token: str, offset: int, timeout: int) -> list[dict]:
    """Long-poll getUpdates. urlopen timeout must exceed the poll timeout."""
    url = f"{API}/bot{token}/getUpdates"
    payload = {"offset": offset, "timeout": timeout,
               "allowed_updates": ["message"]}
    resp = _post(url, payload, timeout + 10)
    if not resp.get("ok"):
        raise RuntimeError(f"getUpdates not ok: {resp}")
    return resp.get("result", [])


def tg_send_message(token: str, chat_id: int, text: str) -> dict:
    url = f"{API}/bot{token}/sendMessage"
    resp = _post(url, {"chat_id": chat_id, "text": text}, 30)
    if not resp.get("ok"):
        raise RuntimeError(f"sendMessage not ok: {resp}")
    return resp


# ─── Core handling ───────────────────────────────────────────────
def handle_update(update: dict, token: str | None, send: bool = True) -> dict | None:
    """dedup -> auth -> coordinator -> reply. Returns the envelope or None
    (None = skipped: malformed / duplicate / not whitelisted)."""
    upd_id = update.get("update_id")
    if not isinstance(upd_id, int):
        return None
    if not dedup.record(upd_id):          # duplicate / replay
        return None
    try:
        uid = auth.verify_user_id(update)
    except auth.AuthError:                # non-operator: ignore silently
        return None

    env = coordinator.process(update, uid)

    if send and token:
        chat_id = (update.get("message") or {}).get("chat", {}).get("id")
        if chat_id is not None:
            reply = BLOCKED_NOTICE if env.get("blocked") else (
                env.get("reply") or "(no reply)")
            try:
                tg_send_message(token, chat_id, reply)
            except Exception as exc:      # noqa: BLE001 — never crash the loop
                print(f"hermes: send failed: {exc}", file=sys.stderr)
    return env


def poll_once(token: str, timeout: int, send: bool = True) -> list[dict]:
    offset = dedup.max_seen() + 1
    updates = tg_get_updates(token, offset, timeout)
    out: list[dict] = []
    for u in updates:
        env = handle_update(u, token, send=send)
        if env is not None:
            out.append(env)
    return out


# ─── Continuous loop ─────────────────────────────────────────────
_STOP = False


def _install_signal_handlers() -> None:
    import signal

    def _stop(signum, frame):            # noqa: ARG001
        global _STOP
        _STOP = True

    for name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, _stop)
            except (ValueError, OSError):
                pass


def run(token: str, timeout: int) -> None:
    _install_signal_handlers()
    backoff = 1
    print(f"hermes: poller LIVE; resume offset={dedup.max_seen() + 1}",
          file=sys.stderr)
    while not _STOP:
        try:
            poll_once(token, timeout, send=True)
            backoff = 1
        except (urllib.error.URLError, RuntimeError, OSError) as exc:
            print(f"hermes: poll error: {exc}; backoff {backoff}s",
                  file=sys.stderr)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
    print("hermes: poller stopped.", file=sys.stderr)


# ─── Dry run (no network) ────────────────────────────────────────
def build_update(uid: int, text: str, update_id: int = 999_999) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": 1,
            "from": {"id": uid, "is_bot": False},
            "chat": {"id": uid, "type": "private"},
            "text": text,
        },
    }


def run_dry(text: str = "/shura-brainstorm dry-run probe") -> int:
    ids = list(auth.whitelisted_ids())
    if not ids:
        print("DRY-RUN ERROR: set NIZAM_TELEGRAM_ALLOWED_IDS first.",
              file=sys.stderr)
        return 2
    uid = ids[0]
    update = build_update(uid, text)
    checked = auth.verify_user_id(update)     # exercises whitelist
    env = coordinator.process(update, checked)  # exercises full pipeline + ledger
    summary = {k: env.get(k) for k in (
        "trace_id", "kind", "target", "reply", "blocked",
        "block_reason", "ledger_row_id")}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nDRY-RUN OK (no network; one EVENT_LEDGER row appended locally).",
          file=sys.stderr)
    return 0


# ─── CLI ─────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="NIZAM HERMES long-poll runner")
    p.add_argument("--dry-run", action="store_true",
                   help="process one synthetic update, no network")
    p.add_argument("--once", action="store_true",
                   help="one real getUpdates cycle then exit (needs RELAY_MODE=live)")
    p.add_argument("--timeout", type=int,
                   default=int(os.environ.get("NIZAM_TG_POLL_TIMEOUT", "25")))
    a = p.parse_args(argv)

    if a.dry_run:
        return run_dry()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set.", file=sys.stderr)
        return 2
    if not list(auth.whitelisted_ids()):
        print("NIZAM_TELEGRAM_ALLOWED_IDS not set.", file=sys.stderr)
        return 2

    mode = os.environ.get("RELAY_MODE", "standby").strip().lower()
    if mode != "live":
        print(f"RELAY_MODE={mode!r}; refusing to poll. "
              "Set RELAY_MODE=live (G4) to go live.", file=sys.stderr)
        return 3

    if a.once:
        envs = poll_once(token, a.timeout, send=True)
        print(f"once: processed {len(envs)} update(s)")
        for e in envs:
            print(f"  trace={e['trace_id']} target={e['target']} "
                  f"blocked={e['blocked']}")
        return 0

    run(token, a.timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
