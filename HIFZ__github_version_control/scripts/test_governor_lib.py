#!/usr/bin/env python3
"""Unit tests for governor lib (no external API calls)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nizam_governor_lib import (
    compute_dedupe_key,
    normalize_percent,
    stage_human_only_fields,
    check_privacy_gate,
    slugify,
)
from nizam_dual_write import dual_write, normalize_record, resolve_drive_path

CONFIG = json.loads(
    (Path(__file__).resolve().parents[2] / "NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json").read_text()
)


def test_dedupe_key():
    k = compute_dedupe_key("Recovery", "CheckIn", "2026-05-21", "morning")
    assert k == "Recovery:CheckIn:2026-05-21:morning"


def test_normalize_percent():
    assert normalize_percent(86) == 0.86
    assert normalize_percent(0.86) == 0.86
    assert normalize_percent("86%") == 0.86


def test_human_only_staging():
    payload = {"energy": 3, "habit completion": True, "note": "ok"}
    human = ["habit completion"]
    cleaned, staged = stage_human_only_fields(payload, human)
    assert "habit completion" not in cleaned
    assert "habit completion" in staged


def test_privacy_gate():
    ok, _ = check_privacy_gate("strict_local", True)
    assert ok
    ok, _ = check_privacy_gate("strict_local", False)
    assert not ok


def test_normalize_record():
    raw = {
        "session_type": "checkin",
        "captured_at": "2026-05-21T08:00:00Z",
        "slug": "am-checkin",
        "drive_narrative": "Test narrative",
        "operator_confirmed_externalize": True,
    }
    rec = normalize_record(raw, CONFIG)
    assert rec["dedupe_key"] == "Recovery:CheckIn:2026-05-21:am-checkin"
    assert rec["type"] == "CheckIn"
    path = resolve_drive_path(rec)
    assert path.startswith("Records/Recovery/")
    assert path.endswith(".docx")


def test_slugify():
    assert slugify("Recovery Trend Assessment") == "recovery-trend-assessment"


def test_dual_write_himayah_blocks():
    receipt = dual_write(
        {
            "session_type": "checkin",
            "captured_at": "2026-05-21T12:00:00Z",
            "drive_narrative": "x",
            "operator_confirmed_externalize": False,
            "privacy_classification": "strict_local",
        },
        dry_run=False,
    )
    assert receipt["status"] == "FAILED"
    assert receipt["failed_stage"] == "himayah_gate"


def main():
    tests = [
        test_dedupe_key,
        test_normalize_percent,
        test_human_only_staging,
        test_privacy_gate,
        test_normalize_record,
        test_slugify,
        test_dual_write_himayah_blocks,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK {t.__name__}")
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
