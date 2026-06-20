from __future__ import annotations

import json
from pathlib import Path

from NIZAM__system.governor import classifier


REPO = Path(__file__).resolve().parents[3]
POLICIES = REPO / "NIZAM__system" / "policies"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dead_letter_contract_is_consistent() -> None:
    temple = _json(REPO / "NIZAM_TEMPLE.json")
    connectors = _json(POLICIES / "CONNECTORS.json")
    dead = temple["ledgers"]["DEAD_LETTER"]

    assert dead["privacy"] == "strict_local"
    assert connectors["retry_policy"]["max_attempts"] == 3
    assert connectors["dead_letter"]["replay_mode"] == "manual_approval_required"
    assert connectors["dead_letter"]["automatic_replay"] is False
    assert classifier.classify(dead["path"]) == "strict_local"


def test_strict_local_maximum_has_no_egress_targets() -> None:
    assert classifier.EGRESS_MATRIX["strict_local_maximum"] == set()
    for target in (
        "github_private",
        "vps_plaintext",
        "vps_encrypted_volume",
        "drive_clear",
        "drive_crypt",
        "notion_sanitized",
        "telegram_operator",
        "zdr_inference",
    ):
        blocked, _ = classifier.is_egress_blocked(
            "HAJR__quarantine/maximum/record.md", target
        )
        assert blocked


def test_local_secret_filenames_are_not_tracked() -> None:
    tracked = {
        line.replace("\\", "/")
        for line in (
            __import__("subprocess")
            .check_output(["git", "ls-files"], cwd=REPO, text=True)
            .splitlines()
        )
    }
    forbidden = {".env", "NIZAM-secrets.json", "nizam-prod-oauthclient.json"}
    assert not (tracked & forbidden)
