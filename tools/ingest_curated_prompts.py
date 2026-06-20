#!/usr/bin/env python3
"""License-aware curated prompt ingestion stub (no unlicensed bulk copy)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_LICENSES = frozenset({"MIT", "Apache-2.0", "BSD-3-Clause", "CC0-1.0"})


def ingest(source_dir: Path, *, dry_run: bool = True) -> dict:
    rows = []
    for path in sorted(source_dir.rglob("*.md")):
        license_hint = "UNKNOWN"
        if "MIT" in path.read_text(encoding="utf-8", errors="ignore")[:500]:
            license_hint = "MIT"
        allowed = license_hint in ALLOWED_LICENSES
        rows.append({"path": str(path), "license_hint": license_hint, "allowed": allowed})
    blocked = [r for r in rows if not r["allowed"]]
    if blocked and not dry_run:
        raise SystemExit("Blocked unlicensed sources; use dry_run or curate manually")
    return {"dry_run": dry_run, "scanned": len(rows), "blocked": len(blocked), "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", nargs="?", default="Research_docs/vendor_research")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = ingest(Path(args.source_dir), dry_run=not args.apply)
    print(json.dumps(result, indent=2))
    return 0 if result["blocked"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
