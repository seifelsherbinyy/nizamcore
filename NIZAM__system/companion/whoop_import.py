from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from .contracts import HealthObservation


ALIASES = {
    "recovery score": ("recovery", "percent"),
    "recovery": ("recovery", "percent"),
    "hrv": ("hrv", "ms"),
    "resting heart rate": ("rhr", "bpm"),
    "rhr": ("rhr", "bpm"),
    "strain": ("strain", "score"),
    "sleep performance": ("sleep_performance", "percent"),
}


def _rows(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        return list(data if isinstance(data, list) else data.get("records", []))
    return list(csv.DictReader(io.StringIO(text)))


def import_export(path: Path) -> tuple[str, list[HealthObservation]]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    observations: list[HealthObservation] = []
    seen: set[tuple[str, str]] = set()
    for row in _rows(path):
        observed_at = str(
            row.get("timestamp") or row.get("date") or row.get("Cycle start time") or ""
        )
        if not observed_at:
            continue
        for raw_name, raw_value in row.items():
            mapped = ALIASES.get(str(raw_name).strip().lower())
            if not mapped or raw_value in (None, ""):
                continue
            metric, unit = mapped
            key = (metric, observed_at)
            if key in seen:
                continue
            try:
                value = float(str(raw_value).replace("%", ""))
            except ValueError:
                continue
            seen.add(key)
            provenance = hashlib.sha256(
                f"{digest}:{observed_at}:{metric}:{value}".encode()
            ).hexdigest()
            observations.append(
                HealthObservation(metric, value, unit, observed_at, "whoop_export", provenance)
            )
    return digest, observations


def correlation_notice(sample_count: int) -> str:
    if sample_count < 7:
        return (
            "Insufficient samples for a trend. This is not a diagnosis, "
            "and no causal claim is made."
        )
    return (
        "Association only: this may guide reflection, but it is not a diagnosis "
        "and does not establish causation."
    )
