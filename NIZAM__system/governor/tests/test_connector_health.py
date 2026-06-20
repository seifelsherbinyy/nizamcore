from __future__ import annotations

import json
from pathlib import Path

import pytest

from NIZAM__system.connectors.health import (
    VALID_STATES,
    assert_replay_approved,
    probe_all,
    probe_layer,
)


REPO = Path(__file__).resolve().parents[3]
REGISTRY = REPO / "NIZAM__system" / "policies" / "CONNECTORS.json"


def test_registry_has_typed_health_contract() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert set(data["health_contract"]["states"]) == VALID_STATES
    for layer in data["layers"].values():
        assert isinstance(layer["enabled"], bool)
        assert layer["status"] in VALID_STATES
        assert layer["approval_required"] is True
        assert layer["probe"]["network"] is False


def test_default_probe_is_local_and_non_writing() -> None:
    result = probe_all(REGISTRY, environ={})
    assert result["network_probed"] is False
    assert result["write_attempted"] is False
    assert {item["state"] for item in result["connectors"]} == {"disabled"}


def test_enabled_missing_adapter_is_blocked() -> None:
    result = probe_layer(
        "gmail",
        {
            "enabled": True,
            "adapter": None,
            "auth_env": ["GMAIL_OAUTH_JSON_PATH", "GMAIL_LABEL_FILTER"],
            "probe": {"kind": "env_all"},
        },
        environ={},
    )
    assert result["state"] == "blocked"


def test_replay_requires_explicit_approval() -> None:
    with pytest.raises(PermissionError):
        assert_replay_approved(False)
    assert_replay_approved(True)
