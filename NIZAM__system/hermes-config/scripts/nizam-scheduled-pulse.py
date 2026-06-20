#!/usr/bin/env python3
"""Scheduled pulse text for Hermes cron (--no-agent) delivery to Telegram."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


def _google_counts() -> dict[str, int | str]:
    secrets = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "").strip()
    token = os.environ.get("GOOGLE_OAUTH_TOKEN", "").strip()
    if not secrets or not token or not os.path.exists(token):
        return {}
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            token,
            [
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
        )
        cal = build("calendar", "v3", credentials=creds, cache_discovery=False)
        events = (
            cal.events()
            .list(calendarId="primary", maxResults=5, singleEvents=True, orderBy="startTime")
            .execute()
            .get("items", [])
        )
        gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
        unread = (
            gmail.users()
            .messages()
            .list(userId="me", maxResults=5, q="is:unread")
            .execute()
            .get("resultSizeEstimate", 0)
        )
        return {"calendar_events": len(events), "gmail_unread": int(unread or 0)}
    except Exception:
        return {}


def main() -> None:
    tz = ZoneInfo(os.environ.get("NIZAM_TIMEZONE", "Africa/Cairo"))
    now = datetime.now(tz)
    counts = _google_counts()
    parts = [
        f"NIZAM scheduled pulse · {now.strftime('%a %d %b %H:%M %Z')}",
        "Hermes gateway cron delivery OK.",
    ]
    if counts:
        parts.append(
            f"Calendar sample: {counts.get('calendar_events', 0)} · "
            f"Gmail unread est.: {counts.get('gmail_unread', 0)}"
        )
    parts.append("Reply /status or /digest for more.")
    print("\n".join(parts))


if __name__ == "__main__":
    main()
