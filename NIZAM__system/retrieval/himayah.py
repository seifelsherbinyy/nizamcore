# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""HIMAYAH gate for retrieval ingestion.

Wraps NIZAM__system/governor/classifier.py with retrieval-specific logic.
Only `private_github` and `review_before_commit` documents may enter the
VPS retrieval database. `strict_local` and `strict_local_maximum` are
hard-blocked. Effective classification is the strictest applicable value.

All logic is pure / side-effect-free. No DB access here.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

# ── load classifier from sibling governor package ────────────────────────────
_GOVERNOR = Path(__file__).resolve().parents[1] / "governor"
_CLASSIFIER_PATH = _GOVERNOR / "classifier.py"

_spec = importlib.util.spec_from_file_location("nizam_classifier", _CLASSIFIER_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
classify_path = _mod.classify  # classify(rel_path: str) -> str


PERMITTED = frozenset({"private_github", "review_before_commit"})
BLOCKED   = frozenset({"strict_local", "strict_local_drive", "strict_local_maximum"})

# Non-negotiable hard-block prefixes (defence-in-depth; classifier is primary)
_HARD_BLOCK_PREFIXES = (
    "AHEL__family_network",
    "BADAN__body_health_system",
    "MAL__financial_engine",
    "YAWMIYAT__journaling",
    "HAJR__quarantine",
    "SUKOON__recovery_first/signals",
    "TAFRIGH__brain_dumper/raw",
    "TAFRIGH__brain_dumper/triaged",
    "SHURA__brainstormer/sessions",
    "NAQD__brain_griller/sessions",
)


class HimayahViolation(RuntimeError):
    """Raised when content classified as prohibited is about to be ingested."""


def classify_for_ingest(rel_path: str) -> str:
    """Return the classification for rel_path.

    Raises HimayahViolation if the path is blocked from VPS ingestion.
    Never catches its own exception — callers handle or propagate.
    """
    p = rel_path.replace("\\", "/").lstrip("/")

    # Defence-in-depth hard block before classifier lookup
    for prefix in _HARD_BLOCK_PREFIXES:
        if p.startswith(prefix):
            raise HimayahViolation(
                f"HIMAYAH hard-block: '{p}' matches protected prefix '{prefix}'. "
                "This content must not enter the VPS retrieval database."
            )

    cls = classify_path(p)

    if cls in BLOCKED:
        raise HimayahViolation(
            f"HIMAYAH gate: '{p}' classified as '{cls}' — prohibited from VPS "
            "retrieval database. Only private_github and review_before_commit permitted."
        )

    if cls not in PERMITTED:
        # Unknown classification → treat as strict_local (fail closed)
        raise HimayahViolation(
            f"HIMAYAH gate: '{p}' has unknown classification '{cls}' — failing closed. "
            "Add to PRIVACY_CLASSIFICATION.json or remove from ingest scope."
        )

    return cls


def filter_permitted(rel_paths: Iterable[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """Partition paths into (permitted, blocked).

    Returns:
        permitted: list of rel_path strings allowed into the DB
        blocked:   list of (rel_path, reason) tuples
    """
    permitted: list[str] = []
    blocked: list[tuple[str, str]] = []
    for p in rel_paths:
        try:
            classify_for_ingest(p)
            permitted.append(p)
        except HimayahViolation as e:
            blocked.append((p, str(e)))
    return permitted, blocked
