#!/usr/bin/env python3
"""
Verify Notion databases expose governor-required properties.
Run after NOTION_TOKEN is set.
"""
from __future__ import annotations

import json
import sys

import requests

from nizam_governor_lib import load_config, get_notion_token

NOTION_VERSION = "2022-06-28"


def fetch_database(token: str, database_id: str) -> dict:
    resp = requests.get(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def check_db(name: str, database_id: str, required: list[str], token: str) -> dict:
    try:
        db = fetch_database(token, database_id)
    except requests.RequestException as e:
        return {"name": name, "database_id": database_id, "ok": False, "error": str(e)}
    props = set(db.get("properties", {}).keys())
    missing = [p for p in required if p not in props]
    return {
        "name": name,
        "database_id": database_id,
        "ok": len(missing) == 0,
        "missing": missing,
        "present": sorted(props),
    }


def main() -> int:
    token = get_notion_token()
    if not token:
        print(json.dumps({"ok": False, "error": "NOTION_TOKEN not set"}))
        return 1

    config = load_config()
    required = list(config["notion"]["required_properties"].values())
    results = []
    for key, ds in config["notion"]["data_sources"].items():
        results.append(
            check_db(ds["name"], ds["data_source_id"], required, token)
        )

    report = {
        "ok": all(r.get("ok") for r in results),
        "required_properties": required,
        "databases": results,
        "migration_hint": (
            "Add missing properties in Notion UI: dedupe_key (rich_text), "
            "DriveLink (url), captured_at (date with time)."
        ),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
