#!/usr/bin/env python3
"""MAKHZAN snapshot anchor for NIZAM Core.

Writes:
  MAKHZAN__archive/<ISO_TS>/manifest.sha256  (one line per file: <sha256>  <relpath>)
  MAKHZAN__archive/<ISO_TS>/MANIFEST.json    (metadata: count, root_sha256, ts)

Source set: `git ls-files` (tracked working tree only).
Pure stdlib. No egress.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_ls_files(repo_root: Path) -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=repo_root, text=True, encoding="utf-8"
    )
    return [line for line in out.splitlines() if line.strip()]


def _verify_clean(repo_root: Path) -> None:
    out = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=repo_root, text=True, encoding="utf-8"
    )
    if out.strip():
        sys.stderr.write("ERROR: git working tree not clean:\n" + out)
        sys.exit(2)


def main(argv: list[str]) -> int:
    repo_root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd().resolve()
    _verify_clean(repo_root)

    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = repo_root / "MAKHZAN__archive" / ts
    out_dir.mkdir(parents=True, exist_ok=False)

    files = _git_ls_files(repo_root)
    files.sort()

    manifest_lines: list[str] = []
    for rel in files:
        abs_p = repo_root / rel
        if not abs_p.is_file():
            continue
        digest = _sha256_file(abs_p)
        manifest_lines.append(f"{digest}  {rel}")

    manifest_path = out_dir / "manifest.sha256"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    root = hashlib.sha256("\n".join(manifest_lines).encode("utf-8")).hexdigest()

    meta = {
        "timestamp_utc": ts,
        "file_count": len(manifest_lines),
        "root_sha256": root,
        "source": "git ls-files",
        "repo_root": str(repo_root),
        "tool": "scripts/makhzan_snapshot.py",
        "purpose": "MAKHZAN anchor (NIZAM Next Plan v2 G0)",
    }
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps({"ok": True, **meta}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
