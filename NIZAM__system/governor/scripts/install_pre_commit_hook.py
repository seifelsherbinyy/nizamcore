#!/usr/bin/env python3
"""install_pre_commit_hook.py — write `.git/hooks/pre-commit`.

Idempotent. Writes a small launcher to `.git/hooks/pre-commit` that
invokes `NIZAM__system/governor/scripts/pre_commit_check.py` under the
local Python venv. Works on Windows (Git Bash) and Linux.

USAGE:
    .venv/Scripts/python.exe NIZAM__system/governor/scripts/install_pre_commit_hook.py

Pure stdlib.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_PATH = REPO_ROOT / ".git" / "hooks" / "pre-commit"
CHECK_PATH_REL = "NIZAM__system/governor/scripts/pre_commit_check.py"

HOOK_CONTENT = """#!/usr/bin/env bash
# NIZAM HIMAYAH pre-commit hook (installed by
# NIZAM__system/governor/scripts/install_pre_commit_hook.py).
set -e

# Resolve repo root from the hook location.
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Prefer the local venv interpreter; fallback to system python.
if [ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]; then
    PY="$REPO_ROOT/.venv/Scripts/python.exe"
elif [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PY="$REPO_ROOT/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
    PY="python"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
else
    echo "pre-commit: no python interpreter found" >&2
    exit 2
fi

exec "$PY" "$REPO_ROOT/__CHECK_PATH__" "$@"
""".replace("__CHECK_PATH__", CHECK_PATH_REL)


def main() -> int:
    if not (REPO_ROOT / ".git").exists():
        print(f"install_pre_commit_hook: no .git at {REPO_ROOT}", file=sys.stderr)
        return 2

    HOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    HOOK_PATH.write_text(HOOK_CONTENT, encoding="utf-8", newline="\n")
    try:
        current = HOOK_PATH.stat().st_mode
        HOOK_PATH.chmod(current | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass

    print(f"installed: {HOOK_PATH}")
    print(f"  delegates to: {CHECK_PATH_REL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
