#!/usr/bin/env python3
"""NIZAM startup verifier — §2 of NIZAM_ORCHESTRATION_LAYER.md.

Stdlib only. Runs in any sandbox with a Python 3.8+ interpreter.

Performs the six-step §2 startup sequence and emits a §7 STARTUP RECEIPT
to stdout as a fenced JSON block. Exits non-zero if a gate is missing or
the repo version cannot be read (HALT condition per §2.4).

Usage:
    python tools/nizam_startup.py            # full check + receipt
    python tools/nizam_startup.py --no-net   # skip network probes
    python tools/nizam_startup.py --json     # raw JSON only (no fences)

What it does NOT do:
- Install dependencies. It reports what is declared in requirements.txt,
  not what is installed. Operator installs per §2.5.
- Touch any durable layer. Network probes are HEAD-style only.
- Write to disk (the receipt goes to stdout per §1.1).
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# REPO_ROOT = tools/.. (assuming this script stays at tools/nizam_startup.py)
REPO_ROOT = Path(__file__).resolve().parent.parent
NIZAM_TEMPLE = REPO_ROOT / "NIZAM_TEMPLE.json"
LOG_MD = REPO_ROOT / "log.md"
CONTRACT_DOC = REPO_ROOT / "NIZAM__system" / "docs" / "NIZAM_ORCHESTRATION_LAYER.md"
AGENT_MAPPING = REPO_ROOT / "NIZAM__system" / "AGENT_MAPPING.json"
CONNECTORS = REPO_ROOT / "NIZAM__system" / "policies" / "CONNECTORS.json"
DUAL_WRITE = REPO_ROOT / "NIZAM__system" / "policies" / "DUAL_WRITE_GOVERNOR.json"

REQUIRED_GATES = ("HIMAYAH", "SUKOON", "THABAT")

NETWORK_TARGETS = {
    "github": "https://github.com/seifelsherbinyy/nizamcore",
    "drive":  "https://drive.google.com/",
    "notion": "https://api.notion.com/v1/",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def have_git() -> bool:
    return shutil.which("git") is not None


def have_pip() -> bool:
    return shutil.which("pip") is not None or shutil.which("pip3") is not None


def probe_url(url: str, timeout: float = 4.0) -> str:
    """Return 'up' if URL is reachable (any non-network-error response), else 'down'."""
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # Any HTTP response (even 401/403/404) proves the host is up.
            _ = resp.status
            return "up"
    except urllib.error.HTTPError:
        return "up"
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError):
        return "down"


def have_net() -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2).close()
        return True
    except OSError:
        return False


def read_repo_version() -> tuple[str | None, list[str], dict | None]:
    """Returns (version, missing_orientation_files, temple_dict)."""
    missing: list[str] = []
    if not NIZAM_TEMPLE.exists():
        missing.append("NIZAM_TEMPLE.json")
    if not LOG_MD.exists():
        missing.append("log.md")
    if not NIZAM_TEMPLE.exists():
        return None, missing, None
    try:
        temple = json.loads(NIZAM_TEMPLE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, missing, None
    return temple.get("platform_version"), missing, temple


def verify_gates(temple: dict | None) -> tuple[bool, list[str]]:
    """Verifies HIMAYAH/SUKOON/THABAT are all present in NIZAM_TEMPLE.json#gates."""
    if not temple:
        return False, list(REQUIRED_GATES)
    gates = temple.get("gates", {})
    missing = [g for g in REQUIRED_GATES if g not in gates]
    return (not missing), missing


def declared_requirements() -> list[dict]:
    """Walk the repo for requirements*.txt files; report pinned vs floating."""
    found = []
    for req_file in sorted(REPO_ROOT.rglob("requirements*.txt")):
        # Skip anything inside .git/ or node_modules/.
        if any(part in {".git", "node_modules"} for part in req_file.parts):
            continue
        try:
            text = req_file.read_text(encoding="utf-8")
        except OSError:
            continue
        pinned: list[str] = []
        floating: list[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pinned.append(line)
            else:
                floating.append(line)
        found.append({
            "path": str(req_file.relative_to(REPO_ROOT)),
            "pinned_count": len(pinned),
            "floating_count": len(floating),
            "policy_note": (
                "All pinned — \u00a72.5 compliant."
                if not floating
                else "Floating versions present — \u00a72.5 says pin them."
            ),
        })
    return found


def companion_artifacts_present() -> dict[str, bool]:
    return {
        "contract_doc":   CONTRACT_DOC.exists(),
        "agent_mapping":  AGENT_MAPPING.exists(),
        "connectors":     CONNECTORS.exists(),
        "dual_write_cfg": DUAL_WRITE.exists(),
    }


def build_receipt(skip_net: bool) -> tuple[dict, list[str]]:
    """Build the §7 STARTUP RECEIPT dict and a list of HALT reasons (empty = OK)."""
    halt_reasons: list[str] = []

    version, missing_files, temple = read_repo_version()
    gates_ok, missing_gates = verify_gates(temple)
    artifacts = companion_artifacts_present()
    reqs = declared_requirements()

    if missing_files:
        halt_reasons.append(f"orientation files missing: {missing_files}")
    if not gates_ok:
        halt_reasons.append(f"gates missing in NIZAM_TEMPLE.json: {missing_gates}")
    if version is None:
        halt_reasons.append("NIZAM_TEMPLE.json#platform_version unreadable")

    durable = {k: "skipped" for k in NETWORK_TARGETS} if skip_net else (
        {k: probe_url(v) for k, v in NETWORK_TARGETS.items()} if have_net() else
        {k: "down" for k in NETWORK_TARGETS}
    )

    receipt = {
        "generated_at": utc_now(),
        "sandbox": {
            "python": python_version(),
            "git":    have_git(),
            "pip":    have_pip(),
            "net":    have_net() if not skip_net else None,
        },
        "repo": {
            "version":             version,
            "gates_ok":            gates_ok,
            "missing_gates":       missing_gates,
            "missing_orientation": missing_files,
            "companion_artifacts": artifacts,
        },
        "durable_layers": durable,
        "requirements_declared": reqs,
        "halt_reasons": halt_reasons,
        "ready": not halt_reasons,
    }
    return receipt, halt_reasons


def emit(receipt: dict, raw_json: bool) -> None:
    body = json.dumps(receipt, indent=2, ensure_ascii=False)
    if raw_json:
        print(body)
    else:
        print("```json")
        print(body)
        print("```")


def main() -> int:
    p = argparse.ArgumentParser(description="NIZAM \u00a72 startup verifier.")
    p.add_argument(
        "--no-net", action="store_true",
        help="Skip network probes (faster, offline-safe).",
    )
    p.add_argument(
        "--json", action="store_true",
        help="Emit raw JSON only (no fenced code block).",
    )
    args = p.parse_args()

    receipt, halt_reasons = build_receipt(skip_net=args.no_net)
    emit(receipt, raw_json=args.json)

    # Exit code policy: 0 if ready, 2 on gate/version HALT (§2.4).
    return 0 if not halt_reasons else 2


if __name__ == "__main__":
    raise SystemExit(main())
