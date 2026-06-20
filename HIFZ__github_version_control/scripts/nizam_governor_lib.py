"""
Shared utilities for NIZAM dual-write governor scripts.

NOTE (B1.1): generic helpers refactored to
`NIZAM__system/governor/utils.py`. This module re-exports them for
backward compatibility and keeps the Notion/Drive-specific bridge.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "NIZAM__system" / "policies" / "DUAL_WRITE_GOVERNOR.json"
PRIVACY_PATH = REPO_ROOT / "NIZAM__system" / "policies" / "PRIVACY_CLASSIFICATION.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from NIZAM__system.governor.utils import (  # noqa: E402,F401
    compute_dedupe_key,
    date_from_captured_at,
    normalize_percent,
    payload_hash,
    slugify,
    stage_human_only_fields,
    utc_now_iso,
)


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_privacy() -> dict[str, Any]:
    with open(PRIVACY_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_drive_record_filename(
    lane: str, record_type: str, date_str: str, slug: str
) -> str:
    return f"{date_str}_{lane}_{record_type}_{slug}.docx"


def build_drive_record_path(lane: str, filename: str) -> str:
    return f"Records/{lane}/{filename}"


def build_weekly_review_path(year: int, week: int) -> str:
    return f"Records/Reviews/{year}-W{week:02d}_Weekly-Review.docx"


def build_meeting_path(date_str: str, meeting_slug: str) -> str:
    return f"Records/Meetings/{date_str}_{meeting_slug}_MoM.docx"


def check_privacy_gate(
    classification: str | None,
    operator_confirmed: bool,
) -> tuple[bool, str]:
    """Return (allowed, reason)."""
    if classification == "strict_local_maximum" and not operator_confirmed:
        return False, "strict_local_maximum requires operator_confirmed_externalize"
    if classification == "strict_local" and not operator_confirmed:
        return False, "strict_local requires operator_confirmed_externalize"
    return True, "ok"


def emit_receipt(receipt: dict[str, Any]) -> str:
    """Format write-receipt as fenced JSON (spec §7)."""
    return "```json\n" + json.dumps(receipt, indent=2) + "\n```"


def mirror_receipt(
    status: str,
    notes: str,
    *,
    created: int = 0,
    updated: int = 0,
    archived: int = 0,
    needs_confirmation: int = 0,
) -> dict[str, Any]:
    return {
        "status": status,
        "mode": "CREATE" if created and not updated else "UPDATE" if updated else "CREATE",
        "scope": "repo_mirror",
        "dedupe_key": None,
        "notion": {"db": None, "data_source_id": None, "page_id": None},
        "drive": {
            "folder": load_config()["targets"]["drive_root_id"],
            "filename": None,
            "url": load_config()["targets"]["drive_root_url"],
        },
        "drivelink_written_back": False,
        "audit_logged": False,
        "human_only_fields_staged": [],
        "failed_stage": None if status == "OK" else "repo_mirror",
        "notes": notes,
        "stats": {
            "created": created,
            "updated": updated,
            "archived": archived,
            "needs_confirmation": needs_confirmation,
        },
    }


def runtime_receipt(
    status: str,
    mode: str,
    dedupe_key: str | None,
    *,
    notion_db: str | None = None,
    notion_ds: str | None = None,
    notion_page_id: str | None = None,
    drive_folder: str | None = None,
    drive_filename: str | None = None,
    drive_url: str | None = None,
    drivelink_written_back: bool = False,
    audit_logged: bool = False,
    human_only_staged: list[str] | None = None,
    failed_stage: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "mode": mode,
        "scope": "runtime_record",
        "dedupe_key": dedupe_key,
        "notion": {
            "db": notion_db,
            "data_source_id": notion_ds,
            "page_id": notion_page_id,
        },
        "drive": {
            "folder": drive_folder,
            "filename": drive_filename,
            "url": drive_url,
        },
        "drivelink_written_back": drivelink_written_back,
        "audit_logged": audit_logged,
        "human_only_fields_staged": human_only_staged or [],
        "failed_stage": failed_stage,
        "notes": notes,
    }


def get_github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def get_notion_token() -> str | None:
    return os.environ.get("NOTION_TOKEN")


def get_google_credentials_path() -> str | None:
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


MIME_FOLDER = "application/vnd.google-apps.folder"


def build_drive_service():
    cred_path = get_google_credentials_path()
    if not cred_path:
        return None
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_file(cred_path, scopes=scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_drive_children(service, parent_id: str) -> dict[str, dict[str, Any]]:
    children: dict[str, dict[str, Any]] = {}
    page_token = None
    q = f"'{parent_id}' in parents and trashed=false"
    while True:
        resp = (
            service.files()
            .list(
                q=q,
                fields="nextPageToken, files(id, name, mimeType, md5Checksum)",
                pageSize=1000,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        for f in resp.get("files", []):
            children[f["name"]] = {
                "id": f["id"],
                "mimeType": f.get("mimeType"),
                "md5Checksum": f.get("md5Checksum"),
            }
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return children


def ensure_folder(service, parent_id: str, name: str, cache: dict[tuple[str, str], str]) -> str:
    key = (parent_id, name)
    if key in cache:
        return cache[key]
    children = list_drive_children(service, parent_id)
    if name in children and children[name]["mimeType"] == MIME_FOLDER:
        fid = children[name]["id"]
    else:
        meta = {
            "name": name,
            "mimeType": MIME_FOLDER,
            "parents": [parent_id],
        }
        fid = (
            service.files()
            .create(body=meta, fields="id", supportsAllDrives=True)
            .execute()["id"]
        )
    cache[key] = fid
    return fid


def ensure_drive_path_chain(service, root_id: str, rel_path: str) -> tuple[str, str]:
    from pathlib import PurePosixPath

    cache: dict[tuple[str, str], str] = {}
    parts = PurePosixPath(rel_path).parts
    filename = parts[-1]
    parent = root_id
    for part in parts[:-1]:
        parent = ensure_folder(service, parent, part, cache)
    return parent, filename
