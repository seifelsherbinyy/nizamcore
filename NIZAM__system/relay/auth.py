"""auth.py — Telegram webhook authentication.

Implements:
  - B4.1 secret-token verification (CVE-2026-32980 mitigation: ALWAYS
    constant-time compare the X-Telegram-Bot-Api-Secret-Token header
    against the configured secret. Reject if header missing.).
  - B4.2 USER_ID whitelist enforcement (only operator's numeric Telegram
    user_id may interact with the relay; all others -> 403).

Reads config from environment variables:
  TELEGRAM_WEBHOOK_SECRET    secret-token configured at setWebhook time
  NIZAM_TELEGRAM_ALLOWED_IDS comma-separated list of operator user_ids

Pure stdlib.
"""
from __future__ import annotations

import hmac
import os
from typing import Iterable

SECRET_ENV = "TELEGRAM_WEBHOOK_SECRET"
WHITELIST_ENV = "NIZAM_TELEGRAM_ALLOWED_IDS"


class AuthError(Exception):
    code: int = 401
    reason: str = "unauthenticated"


class TokenMissing(AuthError):
    code = 401
    reason = "missing_secret_token_header"


class TokenMismatch(AuthError):
    code = 403
    reason = "invalid_secret_token"


class UserNotWhitelisted(AuthError):
    code = 403
    reason = "user_id_not_whitelisted"


def verify_secret_token(header_value: str | None) -> None:
    """CVE-2026-32980 mitigation: constant-time compare the header.

    A missing header is treated as failure — never as 'no secret expected'.
    """
    expected = os.environ.get(SECRET_ENV, "")
    if not expected:
        raise AuthError(
            f"{SECRET_ENV} not set — relay refuses webhooks until configured"
        )
    if header_value is None:
        raise TokenMissing("X-Telegram-Bot-Api-Secret-Token header missing")
    a = expected.encode("utf-8")
    b = header_value.encode("utf-8")
    if not hmac.compare_digest(a, b):
        raise TokenMismatch("secret token mismatch")


def _parse_allowed_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            ids.add(int(tok))
        except ValueError:
            continue
    return ids


def verify_user_id(update: dict) -> int:
    """Extract the sender's user_id and ensure it is whitelisted.

    Returns the user_id on success. Raises UserNotWhitelisted otherwise.
    """
    raw = os.environ.get(WHITELIST_ENV, "").strip()
    if not raw:
        raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    allowed = _parse_allowed_ids(raw)
    if not allowed:
        raise AuthError(
            f"{WHITELIST_ENV} not set — relay refuses traffic until "
            "operator user_id is whitelisted"
        )
    candidate = _extract_user_id(update)
    if candidate is None:
        raise UserNotWhitelisted("no user_id in update payload")
    if candidate not in allowed:
        raise UserNotWhitelisted(
            f"user_id {candidate} not in whitelist {sorted(allowed)}"
        )
    return candidate


def _extract_user_id(update: dict) -> int | None:
    for branch in ("message", "edited_message", "callback_query",
                   "channel_post", "edited_channel_post"):
        node = update.get(branch)
        if isinstance(node, dict):
            sender = node.get("from") or node.get("sender")
            if isinstance(sender, dict):
                uid = sender.get("id")
                if isinstance(uid, int):
                    return uid
    return None


def whitelisted_ids() -> Iterable[int]:
    raw = os.environ.get(WHITELIST_ENV, "").strip()
    if not raw:
        raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    return sorted(_parse_allowed_ids(raw))
