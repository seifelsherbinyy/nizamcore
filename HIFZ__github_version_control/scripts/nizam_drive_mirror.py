#!/usr/bin/env python3
"""
Stage 0: Mirror nizamcore main branch to Google Drive root (1:1 repo tree).
Runtime-only folders (Records, Projects, etc.) are preserved; off-repo clutter → _Archive.
"""
from __future__ import annotations

import argparse
import io
import json
import mimetypes
import sys
from pathlib import PurePosixPath
from typing import Any

import requests

from nizam_governor_lib import (
    MIME_FOLDER,
    build_drive_service,
    emit_receipt,
    ensure_folder,
    list_drive_children,
    load_config,
    mirror_receipt,
    utc_now_iso,
    get_github_token,
)


def fetch_github_tree(repo: str, branch: str, token: str | None) -> dict[str, dict[str, Any]]:
    """Return {posix_path: {sha, size}} for all blobs."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(url, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    index: dict[str, dict[str, Any]] = {}
    for item in data.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item["path"].replace("\\", "/")
        index[path] = {"sha": item["sha"], "size": item.get("size", 0)}
    return index


def fetch_blob_content(repo: str, sha: str, token: str | None) -> bytes:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo}/git/blobs/{sha}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    import base64

    return base64.b64decode(resp.json()["content"])


def resolve_parent_folders(
    service, root_id: str, rel_path: str, cache: dict[tuple[str, str], str]
) -> str:
    """Ensure folder chain exists; return parent id for file."""
    parts = PurePosixPath(rel_path).parts[:-1]
    parent = root_id
    for part in parts:
        parent = ensure_folder(service, parent, part, cache)
    return parent


def upload_or_update_file(
    service,
    parent_id: str,
    name: str,
    content: bytes,
    existing_id: str | None,
    dry_run: bool,
) -> str | None:
    mime, _ = mimetypes.guess_type(name)
    if not mime:
        mime = "application/octet-stream"
    media_body = None
    if not dry_run:
        from googleapiclient.http import MediaIoBaseUpload

        media_body = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime, resumable=False)
    if existing_id:
        if dry_run:
            return existing_id
        service.files().update(
            fileId=existing_id,
            media_body=media_body,
            supportsAllDrives=True,
        ).execute()
        return existing_id
    if dry_run:
        return "dry-run-new-id"
    meta = {"name": name, "parents": [parent_id]}
    return (
        service.files()
        .create(body=meta, media_body=media_body, fields="id", supportsAllDrives=True)
        .execute()["id"]
    )


def repo_paths_set(repo_index: dict[str, dict[str, Any]]) -> set[str]:
    paths = set(repo_index.keys())
    for p in list(repo_index.keys()):
        parts = PurePosixPath(p).parts
        for i in range(1, len(parts)):
            paths.add("/".join(parts[:i]))
    return paths


def mirror_apply(
    service,
    root_id: str,
    repo_index: dict[str, dict[str, Any]],
    repo: str,
    token: str | None,
    *,
    dry_run: bool,
    confirm_overwrite: bool,
) -> dict[str, int]:
    config = load_config()
    reserved = set(config.get("drive_runtime_reserved", []))
    cache: dict[tuple[str, str], str] = {}
    stats = {"created": 0, "updated": 0, "archived": 0, "needs_confirmation": 0}

    # Upload blobs
    for path, meta in sorted(repo_index.items()):
        parent_id = resolve_parent_folders(service, root_id, path, cache)
        name = PurePosixPath(path).name
        children = list_drive_children(service, parent_id)
        existing = children.get(name)
        content = fetch_blob_content(repo, meta["sha"], token)
        if existing and existing.get("md5Checksum"):
            # Drive md5 may not match git; always treat content fetch as source
            pass
        if existing:
            if not confirm_overwrite and not dry_run:
                stats["needs_confirmation"] += 1
                continue
            upload_or_update_file(service, parent_id, name, content, existing["id"], dry_run)
            stats["updated"] += 1
        else:
            upload_or_update_file(service, parent_id, name, content, None, dry_run)
            stats["created"] += 1

    # Archive off-repo root items
    archive_name = config["drive_runtime_paths"]["archive"]
    root_children = list_drive_children(service, root_id)
    repo_top = {PurePosixPath(p).parts[0] for p in repo_index.keys()}
    repo_top.update(
        {
            ".github",
            ".gitignore",
            "CHANGELOG.md",
            "CRITICAL_FACTS.md",
            "LICENSE",
            "POP_MASTER_REGISTER.json",
            "POP_TEMPLE.json",
            "README.md",
            "index.md",
            "log.md",
        }
    )
    for name, info in root_children.items():
        if name in repo_top or name in reserved or name == archive_name:
            continue
        if info["mimeType"] == MIME_FOLDER and name.endswith("__"):
            pass  # still module folders
        if name in repo_top:
            continue
        stats["archived"] += 1
        if dry_run:
            continue
        archive_id = ensure_folder(service, root_id, archive_name, cache)
        service.files().update(
            fileId=info["id"],
            addParents=archive_id,
            removeParents=root_id,
            supportsAllDrives=True,
            fields="id",
        ).execute()

    return stats


def save_mirror_state(service, root_id: str, repo: str, branch: str, stats: dict[str, int], dry_run: bool):
    if dry_run or not service:
        return
    config = load_config()
    archive = config["drive_runtime_paths"]["archive"]
    cache: dict[tuple[str, str], str] = {}
    archive_id = ensure_folder(service, root_id, archive, cache)
    state = {
        "synced_at": utc_now_iso(),
        "repo": repo,
        "branch": branch,
        "stats": stats,
    }
    content = json.dumps(state, indent=2).encode()
    children = list_drive_children(service, archive_id)
    existing = children.get(".mirror_state.json")
    upload_or_update_file(
        service,
        archive_id,
        ".mirror_state.json",
        content,
        existing["id"] if existing else None,
        dry_run=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror nizamcore to Google Drive")
    parser.add_argument("--dry-run", action="store_true", help="Report actions only")
    parser.add_argument("--apply", action="store_true", help="Apply changes to Drive")
    parser.add_argument(
        "--confirm-overwrite",
        action="store_true",
        help="Allow overwriting existing Drive files",
    )
    args = parser.parse_args()
    if not args.dry_run and not args.apply:
        parser.error("Specify --dry-run or --apply")

    config = load_config()
    targets = config["targets"]
    repo = targets["github_repo"]
    branch = targets["github_branch"]
    root_id = targets["drive_root_id"]
    token = get_github_token()

    try:
        repo_index = fetch_github_tree(repo, branch, token)
    except requests.RequestException as e:
        receipt = mirror_receipt("FAILED", f"GitHub unreachable: {e}")
        print(emit_receipt(receipt))
        return 1

    service = build_drive_service()
    if args.apply and not service:
        receipt = mirror_receipt(
            "FAILED",
            "GOOGLE_APPLICATION_CREDENTIALS not set; cannot apply mirror",
        )
        print(emit_receipt(receipt))
        return 1

    dry_run = args.dry_run or not args.apply
    if dry_run and not service:
        receipt = mirror_receipt(
            "OK",
            f"Dry-run: {len(repo_index)} repo files would be synced (no Drive credentials)",
            created=len(repo_index),
        )
        print(emit_receipt(receipt))
        return 0

    stats = mirror_apply(
        service,
        root_id,
        repo_index,
        repo,
        token,
        dry_run=dry_run,
        confirm_overwrite=args.confirm_overwrite,
    )

    if not dry_run and service:
        save_mirror_state(service, root_id, repo, branch, stats, dry_run=False)

    status = "OK"
    notes = (
        f"Mirror {'dry-run' if dry_run else 'applied'}: "
        f"{stats['created']} created, {stats['updated']} updated, "
        f"{stats['archived']} archived, {stats['needs_confirmation']} need confirmation"
    )
    if stats["needs_confirmation"] and not args.confirm_overwrite:
        status = "NEEDS_CONFIRMATION"
    receipt = mirror_receipt(
        status,
        notes,
        created=stats["created"],
        updated=stats["updated"],
        archived=stats["archived"],
        needs_confirmation=stats["needs_confirmation"],
    )
    print(emit_receipt(receipt))
    return 0 if status == "OK" else 2


if __name__ == "__main__":
    sys.exit(main())
