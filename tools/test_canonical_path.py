from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EXPECTED = Path(r"D:\NIZAM")


def test_repo_is_canonical_root() -> None:
    assert (REPO / ".git").exists()
    assert (REPO / "NIZAM_TEMPLE.json").exists()


def test_pointer_matches_repo() -> None:
    pointer = (REPO / "NIZAMCORE_PATH.txt").read_text(encoding="utf-8").strip()
    assert Path(pointer) == EXPECTED
    if REPO == EXPECTED:
        assert Path(pointer) == REPO


def test_machine_readable_contracts_match_repo() -> None:
    temple = json.loads((REPO / "NIZAM_TEMPLE.json").read_text(encoding="utf-8"))
    sync = json.loads(
        (REPO / "NIZAM__system" / "policies" / "SYNC_POLICY.json").read_text(
            encoding="utf-8"
        )
    )
    expected = f"local working tree at {EXPECTED}"
    assert temple["canonical_source_of_truth"] == expected
    assert sync["canonical_source_of_truth"] == expected
