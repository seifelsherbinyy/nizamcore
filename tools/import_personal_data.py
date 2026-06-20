#!/usr/bin/env python3
"""Import WHOOP export and a journal entry into local BADAN/YAWMIYAT paths."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.companion import badan_import  # noqa: E402

DEFAULT_WHOOP = REPO / "NIZAM__system" / "companion" / "tests" / "fixtures" / "whoop-sample.csv"
DEFAULT_JOURNAL = REPO / "YAWMIYAT__journaling" / "entries"


def run(whoop: Path, journal_dir: Path) -> dict:
    whoop_result = badan_import.persist_whoop_export(whoop)
    journal_result = badan_import.persist_journal_entry(
        title="NIZAM production import",
        body="Imported via tools/import_personal_data.py",
        session_date="2026-06-13",
        journal_dir=journal_dir,
    )
    return {"whoop": whoop_result, "journal": journal_result}


def main() -> int:
    parser = argparse.ArgumentParser(description="Import personal health/journal data")
    parser.add_argument("--whoop", type=Path, default=DEFAULT_WHOOP)
    parser.add_argument("--journal-dir", type=Path, default=DEFAULT_JOURNAL)
    args = parser.parse_args()
    if not args.whoop.exists():
        print(f"WHOOP export not found: {args.whoop}", file=sys.stderr)
        return 2
    result = run(args.whoop, args.journal_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
