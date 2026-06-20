from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_PATH = (
    Path(__file__).resolve().parents[2]
    / "TAFRIGH__brain_dumper"
    / "raw"
    / "inbound-capture.jsonl"
)

SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{16,}\b"),
    re.compile(
        r"(?i)\b(?:password|passwd|token|api[_-]?key|secret)\b\s*[:=]\s*\S+"
    ),
)


def redact(text: str) -> tuple[str, int]:
    cleaned = text
    count = 0
    for pattern in SECRET_PATTERNS:
        cleaned, hits = pattern.subn("[REDACTED]", cleaned)
        count += hits
    return cleaned, count


def persist(
    *,
    trace_id: str,
    message_id: str,
    channel: str,
    text: str,
    path: Path = DEFAULT_PATH,
) -> dict[str, Any]:
    cleaned, redactions = redact(text)
    fingerprint = hashlib.sha256(text.encode()).hexdigest()
    record = {
        "schema_version": "1.0",
        "trace_id": trace_id,
        "message_id": message_id,
        "channel": channel,
        "text": cleaned,
        "text_sha256": fingerprint,
        "redactions": redactions,
        "privacy_class": "strict_local",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if path.exists():
        existing = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if any(item.get("message_id") == message_id for item in existing):
            return next(item for item in existing if item.get("message_id") == message_id)
    tmp = path.with_suffix(".tmp")
    lines = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in existing]
    lines.append(json.dumps(record, sort_keys=True, ensure_ascii=False))
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return record
