"""webhook.py — stdlib HTTP handler for Telegram updates.

B4.1 implementation. Uses Python's `http.server` for local testing; for
production deploy on VPS, swap for FastAPI + uvicorn (I7) and keep
`handle_update()` unchanged.

Security:
  - secret-token header MUST match TELEGRAM_WEBHOOK_SECRET (auth.py).
    Constant-time compare. CVE-2026-32980 mitigation.
  - sender user_id MUST be in NIZAM_TELEGRAM_ALLOWED_IDS whitelist.
  - duplicate update_id is acknowledged but not re-processed.

Pure stdlib.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.relay import auth, coordinator, dedup  # noqa: E402

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def handle_update(update: dict, secret_header: str | None) -> dict:
    """Single entry point used by both stdlib HTTP server and FastAPI.

    Returns a dict that callers may serialize as JSON (200 OK body) or
    use to determine the HTTP status code.

    Output schema:
      {
        "status": "ok"|"duplicate"|"unauthenticated"|"forbidden"|"blocked",
        "trace_id": str | null,
        "decision": dict | null,
        "error": str | null
      }
    """
    try:
        auth.verify_secret_token(secret_header)
    except auth.AuthError as exc:
        return {"status": "unauthenticated", "trace_id": None,
                "decision": None, "error": exc.reason}

    try:
        user_id = auth.verify_user_id(update)
    except auth.AuthError as exc:
        return {"status": "forbidden", "trace_id": None,
                "decision": None, "error": exc.reason}

    update_id = update.get("update_id")
    if isinstance(update_id, int):
        if not dedup.record(update_id):
            return {"status": "duplicate", "trace_id": None,
                    "decision": None, "error": None}

    decision = coordinator.process(update, user_id)
    status = "blocked" if decision.get("blocked") else "ok"
    return {
        "status": status,
        "trace_id": decision.get("trace_id"),
        "decision": decision,
        "error": decision.get("block_reason"),
    }


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != os.environ.get("TELEGRAM_WEBHOOK_PATH", "/telegram"):
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        try:
            update = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
        token = self.headers.get(SECRET_HEADER)
        result = handle_update(update, token)
        if result["status"] == "unauthenticated":
            self.send_response(401)
        elif result["status"] == "forbidden":
            self.send_response(403)
        elif result["status"] == "blocked":
            self.send_response(451)   # Unavailable For Legal Reasons
        else:
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))

    def log_message(self, fmt: str, *args) -> None:
        # Suppress default access log; relay uses EVENT_LEDGER instead.
        pass


def serve(host: str = "127.0.0.1", port: int = 8443) -> None:
    server = HTTPServer((host, port), _Handler)
    server.serve_forever()


if __name__ == "__main__":
    serve(
        host=os.environ.get("RELAY_HOST", "127.0.0.1"),
        port=int(os.environ.get("RELAY_PORT", "8443")),
    )
