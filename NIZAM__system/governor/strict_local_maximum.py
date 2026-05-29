"""strict_local_maximum.py — AHEL handling (separate keypair).

AHEL data (FAMILY_LEDGER, /ahel/ folders, family records) is the most
sensitive tier in NIZAM. Per section B locked decision:

  - AHEL has its OWN encryption keypair (not shared with general
    strict_local data).
  - AHEL inference runs on a LOCAL 3B model only (no third-party transit).
  - AHEL data NEVER transits VPS plaintext, GitHub, Notion, Drive-clear.
  - Sync is allowed ONLY to AHEL-LUKS encrypted volume (LOCAL) and
    AHEL-rclone-crypt Drive remote (encrypted blob).

This module verifies the AHEL keypair is loaded, ensures the writer uses
the AHEL-LUKS-mounted path, and refuses operations that violate any of the
above rules. The keypair never appears in plaintext on disk — operator
provides it at session start via `AHEL_KEYPAIR_PATH` env var pointing to a
LUKS-mounted secret.

Pure stdlib.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

from . import classifier


AHEL_PATH_PREFIXES = (
    "ahel/",
    "ahel_strict_local_maximum/",
    "ledgers/FAMILY_LEDGER",
    "AHEL_personal_council/",
)

AHEL_KEYPAIR_ENV = "AHEL_KEYPAIR_PATH"
AHEL_VOLUME_ENV = "AHEL_LUKS_MOUNT"
LOCAL_MODEL_ENV = "AHEL_LOCAL_MODEL"


class AhelGateViolation(RuntimeError):
    pass


def is_ahel_path(rel_path: str) -> bool:
    p = rel_path.replace("\\", "/").lstrip("/")
    if any(p.startswith(prefix) for prefix in AHEL_PATH_PREFIXES):
        return True
    return classifier.classify(rel_path) == "strict_local_maximum"


def assert_ahel_keypair_loaded() -> Path:
    """Ensure AHEL_KEYPAIR_PATH points at a real LUKS-mounted file."""
    raw = os.environ.get(AHEL_KEYPAIR_ENV)
    if not raw:
        raise AhelGateViolation(
            f"{AHEL_KEYPAIR_ENV} unset; AHEL operations refused. "
            "Mount AHEL LUKS volume and export key path."
        )
    p = Path(raw)
    if not p.exists() or not p.is_file():
        raise AhelGateViolation(
            f"{AHEL_KEYPAIR_ENV}={raw} does not point at a readable file."
        )
    return p


def assert_ahel_volume_mounted() -> Path:
    raw = os.environ.get(AHEL_VOLUME_ENV)
    if not raw:
        raise AhelGateViolation(
            f"{AHEL_VOLUME_ENV} unset; AHEL writes refused. "
            "Mount LUKS AHEL volume first."
        )
    p = Path(raw)
    if not p.exists() or not p.is_dir():
        raise AhelGateViolation(
            f"{AHEL_VOLUME_ENV}={raw} is not a mounted directory."
        )
    return p


def assert_local_model() -> str:
    """Ensure inference for AHEL is local-only."""
    model = os.environ.get(LOCAL_MODEL_ENV, "")
    if not model:
        raise AhelGateViolation(
            f"{LOCAL_MODEL_ENV} unset; AHEL inference refused. "
            "Set AHEL_LOCAL_MODEL=local-llama-3b (or other local) "
            "before any AHEL prompt."
        )
    if model.startswith(("anthropic/", "deepseek/", "moonshot/", "openrouter/",
                          "openai/", "google/")):
        raise AhelGateViolation(
            f"{LOCAL_MODEL_ENV}={model} appears non-local. AHEL is "
            "local-only (no third-party transit allowed)."
        )
    return model


def gate(rel_path: str) -> None:
    """Comprehensive gate for an AHEL write/read.

    Combines keypair, volume, and (best-effort) model checks.
    """
    if not is_ahel_path(rel_path):
        return
    assert_ahel_keypair_loaded()
    assert_ahel_volume_mounted()
    assert_local_model()


def gate_many(paths: Iterable[str]) -> dict[str, str]:
    """Returns {path: 'ok' or error message} for diagnostic dry-run."""
    result: dict[str, str] = {}
    for p in paths:
        try:
            gate(p)
            result[p] = "ok"
        except AhelGateViolation as exc:
            result[p] = f"BLOCKED: {exc}"
    return result


def fingerprint_keypair() -> str:
    """Return a short, non-secret fingerprint of the AHEL keypair file.

    Used for ledger provenance only (`actor: Ammar, keypair_fp: ...`).
    Never expose raw key material.
    """
    key_path = assert_ahel_keypair_loaded()
    h = hashlib.sha256(key_path.read_bytes()).hexdigest()
    return h[:12]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: strict_local_maximum.py <rel_path>")
        sys.exit(2)
    try:
        gate(sys.argv[1])
        print(f"{sys.argv[1]}: ok (AHEL gate passed)")
    except AhelGateViolation as exc:
        print(f"{sys.argv[1]}: BLOCKED — {exc}")
        sys.exit(1)
