from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping


REPO = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO / "NIZAM__system" / "policies" / "CONNECTORS.json"
VALID_STATES = {
    "disabled",
    "blocked",
    "unconfigured",
    "configured",
    "reachable",
    "degraded",
}


def _env_names(raw: list[str]) -> list[str]:
    return [item.split(" ", 1)[0].strip() for item in raw]


def probe_layer(
    connector_id: str,
    layer: Mapping[str, object],
    *,
    environ: Mapping[str, str] | None = None,
) -> dict:
    env = os.environ if environ is None else environ
    enabled = bool(layer.get("enabled", False))
    required = _env_names(list(layer.get("auth_env", [])))
    present = [name for name in required if bool(env.get(name))]
    kind = dict(layer.get("probe", {})).get("kind", "env_all")

    if not enabled:
        state = "disabled"
        reason = "activation requires operator approval"
    elif layer.get("adapter", object()) is None:
        state = "blocked"
        reason = "adapter is not implemented"
    elif not required or connector_id == "github":
        state = "configured"
        reason = "local configuration is present; network not probed"
    elif kind == "env_any" and present:
        state = "configured"
        reason = "at least one required environment variable is present"
    elif kind == "env_all" and len(present) == len(required):
        state = "configured"
        reason = "required environment variables are present"
    else:
        state = "unconfigured"
        reason = "required environment variables are absent"

    return {
        "connector_id": connector_id,
        "state": state,
        "enabled": enabled,
        "configured_env_count": len(present),
        "required_env_count": len(required),
        "network_probed": False,
        "write_attempted": False,
        "reason": reason,
    }


def probe_all(
    registry_path: Path = DEFAULT_REGISTRY,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    results = [
        probe_layer(connector_id, layer, environ=environ)
        for connector_id, layer in registry["layers"].items()
    ]
    return {
        "registry_version": registry["version"],
        "mode": "config_only",
        "network_probed": False,
        "write_attempted": False,
        "connectors": results,
    }


def assert_replay_approved(approved: bool) -> None:
    if not approved:
        raise PermissionError("dead-letter replay requires explicit operator approval")
