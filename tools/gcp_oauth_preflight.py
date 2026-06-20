#!/usr/bin/env python3
"""Operator checklist for Google Cloud OAuth before re-auth."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.connectors import google_oauth  # noqa: E402

REQUIRED_APIS = (
    "Google Calendar API",
    "Google Tasks API",
    "Gmail API",
)


def main() -> int:
    print("Google Cloud Console preflight (operator manual steps)")
    print("=" * 60)
    client = REPO / "NIZAM__system" / "connectors" / "oauth-client.json"
    if client.exists():
        payload = json.loads(client.read_text(encoding="utf-8"))
        installed = payload.get("installed") or payload.get("web") or {}
        print(f"OAuth client file: {client}")
        print(f"  project_id: {installed.get('project_id', 'unknown')}")
        print(f"  client_id: {installed.get('client_id', 'unknown')[:20]}...")
    else:
        print(f"MISSING: {client}")
        return 2

    print("\nEnable these APIs in Google Cloud Console:")
    for api in REQUIRED_APIS:
        print(f"  - {api}")

    print("\nOAuth consent screen — add scopes:")
    for scope in google_oauth.ALL_SCOPES:
        print(f"  - {scope}")

    print("\nOAuth client type: Desktop (InstalledAppFlow)")
    print("\nAfter enabling APIs, run:")
    print(f"  {sys.executable} {REPO / 'tools' / 'setup_google_oauth.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
