"""Persist imported health observations into BADAN daily signals."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .contracts import HealthObservation
from .whoop_import import import_export


REPO = Path(__file__).resolve().parents[2]
DEFAULT_BADAN_DIR = REPO / "BADAN__body_health_system" / "daily_signals"


def persist_whoop_export(
    export_path: Path,
    *,
    badan_dir: Path = DEFAULT_BADAN_DIR,
) -> dict[str, object]:
    digest, observations = import_export(export_path)
    badan_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = badan_dir / f"whoop-{stamp}.jsonl"
    for item in observations:
        row = {
            "metric": item.metric,
            "value": item.value,
            "unit": item.unit,
            "observed_at": item.observed_at,
            "source": item.source,
            "provenance_hash": item.provenance_hash,
            "export_digest": digest,
            "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    manifest = badan_dir / "_imports.json"
    history = []
    if manifest.exists():
        history = json.loads(manifest.read_text(encoding="utf-8"))
    history.append(
        {
            "source_file": str(export_path),
            "digest": digest,
            "observation_count": len(observations),
            "output": str(out),
            "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    manifest.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return {
        "digest": digest,
        "observation_count": len(observations),
        "output": str(out),
    }


def persist_journal_entry(
    *,
    title: str,
    body: str,
    session_date: str | None = None,
    journal_dir: Path | None = None,
) -> dict[str, str]:
    journal_root = journal_dir or (REPO / "YAWMIYAT__journaling" / "sessions")
    journal_root.mkdir(parents=True, exist_ok=True)
    stamp = session_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = journal_root / f"{stamp}.json"
    payload = {
        "title": title,
        "body": body,
        "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "privacy_class": "strict_local",
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(path), "date": stamp}
