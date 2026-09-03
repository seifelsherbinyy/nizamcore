"""Safe owner memory for the Hermes relay.

Only explicit operator memory requests are written. Ordinary conversation is not
promoted into memory. Entries are append-only, bounded, and never sent to the
cloud when they contain journal or health material.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_MEMORY_CHARS = 600
MEMORY_PREFIXES = ("remember:", "remember that ", "save preference:", "my preference is ")
SECRET_PATTERN = re.compile(r"sk-or-|begin .*private key|(?:api[_-]?key|token|secret)\s*=|bot[_-]?token", re.IGNORECASE)
PRIVATE_TOPIC_PATTERN = re.compile(r"journal|health|whoop|therapy|medical|diagnos", re.IGNORECASE)

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def extract_explicit_memory(text: str) -> str | None:
    clean = text.strip()
    lowered = clean.lower()
    for prefix in MEMORY_PREFIXES:
        if lowered.startswith(prefix):
            value = clean[len(prefix):].strip()
            if value:
                return value[:MAX_MEMORY_CHARS]
    return None

def append_explicit_memory(path_value: str, text: str, *, trace_id: str) -> dict[str, Any] | None:
    value = extract_explicit_memory(text)
    if value is None or SECRET_PATTERN.search(value):
        return None
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"schema":"nizam.owner.memory.v1","memory_id":hashlib.sha256((trace_id + value).encode("utf-8")).hexdigest(),"created_at":_now(),"confirmed_by":"Operator","status":"confirmed","kind":"preference_or_instruction","content":value,"trace_id":trace_id}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n")
    path.chmod(0o600)
    return record

def render_memory(path_value: str, *, max_chars: int = 5000) -> str:
    if not path_value:
        return ""
    path = Path(path_value).expanduser()
    if not path.is_absolute() or not path.is_file():
        return ""
    blocks: list[str] = []
    used = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("status") != "confirmed" or item.get("confirmed_by") != "Operator":
            continue
        value = str(item.get("content", "")).strip()
        if not value or PRIVATE_TOPIC_PATTERN.search(value) or SECRET_PATTERN.search(value):
            continue
        block = "OWNER_MEMORY: " + value
        source_ref = str(item.get("source_ref", "")).strip()
        if source_ref:
            block += "\nOWNER_MEMORY_SOURCE: " + source_ref
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n".join(blocks)

__all__ = ["append_explicit_memory", "extract_explicit_memory", "render_memory"]
