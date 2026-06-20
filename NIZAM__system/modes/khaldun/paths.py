from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MODE_BUNDLE = REPO / "NIZAM__system" / "modes" / "khaldun_islamic_cosmic_wisdom"
DRYRUN_LOG = REPO / "NIZAM__system" / "relay" / ".state" / "khaldun-reminders-dryrun.jsonl"
