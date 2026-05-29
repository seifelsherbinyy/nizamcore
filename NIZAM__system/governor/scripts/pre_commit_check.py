#!/usr/bin/env python3
"""pre_commit_check.py — HIMAYAH egress firewall pre-commit hook.

Invoked by `.git/hooks/pre-commit`. Reads staged files via `git diff
--cached --name-only` and refuses the commit if any path is classified
`strict_local` or `strict_local_maximum` (which must never reach GitHub).

Exit codes:
    0 — clean, allow commit
    1 — blocked, list of offending paths printed
    2 — environment error (no git, no classifier)

Pure stdlib.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _staged_paths() -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"pre_commit_check: git failed: {exc}", file=sys.stderr)
        sys.exit(2)
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    try:
        from NIZAM__system.governor.sync_arbiter import pre_commit_check
    except ImportError as exc:
        print(f"pre_commit_check: cannot import governor: {exc}",
              file=sys.stderr)
        sys.exit(2)

    if os.environ.get("NIZAM_PRE_COMMIT_BYPASS") == "I_KNOW_WHAT_IM_DOING":
        print("pre_commit_check: BYPASS env var active — letting commit through.",
              file=sys.stderr)
        return 0

    paths = _staged_paths()
    if not paths:
        return 0

    ok, blocked = pre_commit_check(paths)
    if ok:
        return 0

    print("\nHIMAYAH PRE-COMMIT BLOCK", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(
        "The following staged files are classified as private and must NOT "
        "be pushed to GitHub:", file=sys.stderr,
    )
    for d in blocked:
        print(f"  - [{d.classification}] {d.rel_path}", file=sys.stderr)
    print(
        "\nResolutions:\n"
        "  1. `git restore --staged <path>` to unstage the offending file.\n"
        "  2. Move/rename if the path was misclassified, then verify via:\n"
        "       python -m NIZAM__system.governor.classifier <path>\n"
        "  3. Emergency bypass (DOCUMENT in EVENT_LEDGER FIRST):\n"
        "       NIZAM_PRE_COMMIT_BYPASS=I_KNOW_WHAT_IM_DOING git commit ...\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
