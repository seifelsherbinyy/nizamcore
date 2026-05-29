"""utils.py — shared utilities for NIZAM governor.

Refactored from `HIFZ__github_version_control/scripts/nizam_governor_lib.py`
(B1.1). The legacy module re-exports from here to avoid breaking callers.

Pure stdlib.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str, max_len: int = 30) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:max_len] if s else "record").rstrip("-")


def compute_dedupe_key(lane: str, record_type: str, date_str: str, slug: str) -> str:
    return f"{lane}:{record_type}:{date_str}:{slug}"


def date_from_captured_at(captured_at: str) -> str:
    return captured_at[:10]


def normalize_percent(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value > 1:
            return round(value / 100.0, 4)
        return float(value)
    if isinstance(value, str):
        s = value.strip().rstrip("%")
        try:
            n = float(s)
            return round(n / 100.0, 4) if n > 1 else n
        except ValueError:
            return value
    return value


def payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def stage_human_only_fields(
    payload: dict[str, Any], human_only: list[str]
) -> tuple[dict[str, Any], list[str]]:
    staged: list[str] = []
    cleaned = dict(payload)
    for key in list(cleaned.keys()):
        if key in human_only:
            staged.append(key)
            del cleaned[key]
    return cleaned, staged
