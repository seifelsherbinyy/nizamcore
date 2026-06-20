#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.connectors.health import probe_all


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report connector configuration without network access or writes."
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    result = probe_all()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["connectors"]:
            print(f"{item['connector_id']}: {item['state']} - {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
