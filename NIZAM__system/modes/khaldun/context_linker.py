from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from NIZAM__system.companion.context import build_context_packet
from NIZAM__system.companion.contracts import ContextItem, ContextRefresh

from .paths import REPO

HOME = Path(os.path.expanduser("~"))
PULSE_STATE = HOME / ".hermes" / "nizam" / "last_pulse.json"
YAWMIYAT_SESSIONS = REPO / "YAWMIYAT__journaling" / "sessions"
BADAN_SIGNALS = REPO / "BADAN__body_health_system" / "daily_signals"


@dataclass
class SeifContextSummary:
    journal_themes: list[str] = field(default_factory=list)
    witness_summary: dict[str, Any] = field(default_factory=dict)
    badan_whoop_summary: dict[str, Any] = field(default_factory=dict)
    pulse_summary: dict[str, Any] = field(default_factory=dict)
    open_loops_count: int = 0
    active_decisions_count: int = 0
    spiritual_intent: str = ""
    missing_data: list[str] = field(default_factory=list)
    sukoon_capacity: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "journal_themes": self.journal_themes,
            "witness_summary": self.witness_summary,
            "badan_whoop_summary": self.badan_whoop_summary,
            "pulse_summary": self.pulse_summary,
            "open_loops_count": self.open_loops_count,
            "active_decisions_count": self.active_decisions_count,
            "spiritual_intent": self.spiritual_intent,
            "missing_data": self.missing_data,
            "sukoon_capacity": self.sukoon_capacity,
        }


def _latest_json_files(folder: Path, limit: int = 3) -> list[Path]:
    if not folder.exists():
        return []
    files = sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def _read_pulse() -> dict[str, Any]:
    if not PULSE_STATE.exists():
        return {}
    try:
        return json.loads(PULSE_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_witness_themes() -> tuple[dict[str, Any], list[str]]:
    themes: list[str] = []
    summary: dict[str, Any] = {}
    for path in _latest_json_files(YAWMIYAT_SESSIONS, 1):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        summary = {
            "session_type": payload.get("session_type") or payload.get("type"),
            "capacity_level": payload.get("capacity_level"),
            "theme": payload.get("theme") or payload.get("felt_state"),
        }
        if summary.get("theme"):
            themes.append(str(summary["theme"]))
        break
    return summary, themes


def _read_badan_metrics() -> dict[str, Any]:
    for path in _latest_json_files(BADAN_SIGNALS, 1):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        metrics = payload.get("metrics") or payload
        return {
            "recovery_band": metrics.get("recovery_band") or metrics.get("band"),
            "recovery_pct": metrics.get("recovery"),
            "hrv": metrics.get("hrv"),
            "strain": metrics.get("strain"),
        }
    return {}


def summarize_seif_context(refresh: ContextRefresh | None = None) -> SeifContextSummary:
    summary = SeifContextSummary()
    snaps = refresh.source_snapshots if refresh else {}

    if refresh:
        summary.sukoon_capacity = refresh.sukoon_capacity
        if "open_loops" in refresh.sources_found:
            summary.open_loops_count = int(
                snaps.get("open_loops", {}).get("open_loop_count", 0)
            )
        if "whoop_badan" in refresh.sources_found:
            summary.badan_whoop_summary = dict(
                snaps.get("whoop_badan", {}).get("metrics") or {}
            )
        if "pulse_entries" in refresh.sources_found:
            summary.pulse_summary = {
                "capacity_band": snaps.get("pulse_entries", {}).get("capacity_band"),
                "recovery": snaps.get("pulse_entries", {}).get("recovery"),
            }
        if "witness_reflection" in refresh.sources_found:
            summary.witness_summary = dict(snaps.get("witness_reflection") or {})
        if "yawmiyat_journal" in refresh.sources_found:
            entry_date = snaps.get("yawmiyat_journal", {}).get("entry_date")
            if entry_date:
                summary.journal_themes.append(f"entry_{entry_date}")
    else:
        witness, themes = _read_witness_themes()
        summary.witness_summary = witness
        summary.journal_themes = themes
        summary.badan_whoop_summary = _read_badan_metrics()
        pulse = _read_pulse()
        if pulse:
            summary.pulse_summary = {
                "capacity_band": pulse.get("band") or pulse.get("capacity_band"),
                "recovery": pulse.get("recovery"),
            }
        else:
            summary.missing_data.append("pulse_entries")

    if not summary.journal_themes and not summary.witness_summary:
        summary.missing_data.append("yawmiyat_journal")
    if not summary.badan_whoop_summary:
        summary.missing_data.append("whoop_badan")

    return summary


def refresh_context_link(
    *, trace_id: str = "khaldun"
) -> tuple[SeifContextSummary, ContextRefresh | None]:
    try:
        from NIZAM__system.companion.pulsation.context_refresh import refresh_context

        refresh = refresh_context()
        summary = summarize_seif_context(refresh)
        return summary, refresh
    except Exception:
        return summarize_seif_context(None), None


def build_khaldun_context_packet(
    summary: SeifContextSummary,
    *,
    trace_id: str = "khaldun",
):
    items: list[ContextItem] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if summary.journal_themes:
        items.append(
            ContextItem(
                kind="correlation",
                text="Journal themes: " + ", ".join(summary.journal_themes),
                provenance="yawmiyat_theme_summary",
                observed_at=now,
                privacy_class="strict_local",
                confidence=0.8,
            )
        )
    if summary.pulse_summary:
        band = summary.pulse_summary.get("capacity_band")
        rec = summary.pulse_summary.get("recovery")
        items.append(
            ContextItem(
                kind="fact",
                text=f"Pulse capacity band {band}, recovery {rec}",
                provenance="pulse_summary",
                observed_at=now,
                privacy_class="strict_local",
                confidence=0.9,
            )
        )
    if summary.missing_data:
        items.append(
            ContextItem(
                kind="fact",
                text="Missing: " + ", ".join(summary.missing_data),
                provenance="context_linker",
                observed_at=now,
                privacy_class="strict_local",
                confidence=1.0,
            )
        )
    return build_context_packet(trace_id=trace_id, persona="Khaldun", items=items)
