"""Read-only context scanners for proactive pulsation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from ..contracts import ContextRefresh, utc_now

REPO = Path(__file__).resolve().parents[3]

FRESHNESS_HOURS: dict[str, int] = {
    "yawmiyat_journal": 72,
    "witness_reflection": 72,
    "pulse_entries": 48,
    "whoop_badan": 48,
    "sukoon_capacity": 24,
    "open_loops": 168,
    "active_decisions": 168,
    "thabat_summary": 24,
    "recent_interactions": 24,
}

ALL_SOURCES = tuple(FRESHNESS_HOURS.keys())

PULSE_STATE = Path.home() / ".hermes" / "nizam" / "last_pulse.json"
RUNTIME_EVENTS = (
    REPO / "NIZAM__system" / "relay" / ".state" / "runtime-events.jsonl"
)
LEDGERS_DIR = REPO / "NIZAM__system" / "ledgers"


@dataclass(frozen=True)
class SourceScan:
    source_key: str
    found: bool
    latest_ts: str | None
    safe_facts: dict[str, Any]


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fresh(ts: datetime | None, *, window_hours: int, now: datetime) -> bool:
    if ts is None:
        return False
    return ts >= now - timedelta(hours=window_hours)


def _latest_json_files(root: Path, pattern: str = "*.json") -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


def _scan_yawmiyat_journal(now: datetime) -> SourceScan:
    roots = (
        REPO / "YAWMIYAT__journaling" / "sessions",
        REPO / "YAWMIYAT__journaling" / "entries",
    )
    latest: datetime | None = None
    title: str | None = None
    entry_date: str | None = None
    for root in roots:
        for path in _latest_json_files(root):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            ts = _parse_ts(payload.get("captured_at") or payload.get("imported_at"))
            if ts and (latest is None or ts > latest):
                latest = ts
                title = payload.get("title")
                entry_date = path.stem[:10] if len(path.stem) >= 10 else path.stem
    window = FRESHNESS_HOURS["yawmiyat_journal"]
    found = _fresh(latest, window_hours=window, now=now)
    return SourceScan(
        "yawmiyat_journal",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {
            "entry_date": entry_date,
            "title_present": bool(title),
        },
    )


def _scan_witness_reflection(now: datetime) -> SourceScan:
    root = REPO / "YAWMIYAT__journaling" / "sessions"
    latest: datetime | None = None
    session_type: str | None = None
    capacity_level: str | None = None
    for path in _latest_json_files(root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ts = _parse_ts(payload.get("captured_at") or payload.get("imported_at"))
        if ts and (latest is None or ts > latest):
            latest = ts
            session_type = payload.get("session_type")
            capacity = payload.get("capacity") or {}
            if isinstance(capacity, dict):
                capacity_level = capacity.get("level")
    window = FRESHNESS_HOURS["witness_reflection"]
    found = _fresh(latest, window_hours=window, now=now)
    return SourceScan(
        "witness_reflection",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {
            "session_type": session_type,
            "capacity_level": capacity_level,
        },
    )


def _scan_pulse_entries(now: datetime) -> SourceScan:
    latest: datetime | None = None
    recovery: float | None = None
    band: str | None = None
    if PULSE_STATE.exists():
        try:
            payload = json.loads(PULSE_STATE.read_text(encoding="utf-8"))
            latest = _parse_ts(payload.get("ts"))
            raw_recovery = payload.get("recovery")
            if raw_recovery is not None:
                recovery = float(raw_recovery)
                if recovery >= 67:
                    band = "HIGH"
                elif recovery >= 34:
                    band = "MEDIUM"
                else:
                    band = "LOW"
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
    window = FRESHNESS_HOURS["pulse_entries"]
    found = _fresh(latest, window_hours=window, now=now)
    return SourceScan(
        "pulse_entries",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"recovery": recovery, "capacity_band": band},
    )


def _scan_whoop_badan(now: datetime) -> SourceScan:
    root = REPO / "BADAN__body_health_system" / "daily_signals"
    latest: datetime | None = None
    metrics: dict[str, float] = {}
    if root.exists():
        files = sorted(root.glob("whoop-*.jsonl"), key=lambda p: p.name, reverse=True)
        for path in files:
            try:
                lines = [
                    line.strip()
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            except OSError:
                continue
            for line in reversed(lines):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _parse_ts(row.get("imported_at") or row.get("observed_at"))
                metric = row.get("metric")
                if ts and (latest is None or ts > latest):
                    latest = ts
                if isinstance(metric, str) and metric not in metrics:
                    try:
                        metrics[metric] = float(row.get("value"))
                    except (TypeError, ValueError):
                        pass
            if latest:
                break
    window = FRESHNESS_HOURS["whoop_badan"]
    found = _fresh(latest, window_hours=window, now=now)
    return SourceScan(
        "whoop_badan",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"metrics": metrics},
    )


def _scan_sukoon_capacity(now: datetime) -> SourceScan:
    from NIZAM__system.relay import sukoon_gate

    flags = sukoon_gate.recent_flags(window_hours=FRESHNESS_HOURS["sukoon_capacity"])
    latest: datetime | None = None
    level: Literal["green", "yellow", "red", "unknown"] = "green"
    for row in flags:
        ts = _parse_ts(row.get("ts") or row.get("timestamp"))
        if ts and (latest is None or ts > latest):
            latest = ts
        severity = str(row.get("severity") or row.get("level") or "").lower()
        if severity in {"red", "crisis"}:
            level = "red"
        elif severity in {"yellow", "amber", "overload"} and level != "red":
            level = "yellow"
    signals_dir = REPO / "SUKOON__recovery_first" / "signals"
    if signals_dir.exists():
        for path in sorted(signals_dir.glob("*.md"), reverse=True):
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if latest is None or mtime > latest:
                latest = mtime
    if flags and level == "green":
        level = "yellow"
    window = FRESHNESS_HOURS["sukoon_capacity"]
    found = _fresh(latest, window_hours=window, now=now) or bool(flags)
    return SourceScan(
        "sukoon_capacity",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"capacity": level, "recent_flag_count": len(flags)},
    )


def _scan_open_loops(now: datetime) -> SourceScan:
    root = REPO / "YAWMIYAT__journaling" / "sessions"
    latest: datetime | None = None
    count = 0
    for path in _latest_json_files(root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ts = _parse_ts(payload.get("captured_at") or payload.get("imported_at"))
        questions = payload.get("open_questions") or []
        if not isinstance(questions, list):
            continue
        if questions:
            count += len(questions)
            if ts and (latest is None or ts > latest):
                latest = ts
    window = FRESHNESS_HOURS["open_loops"]
    found = _fresh(latest, window_hours=window, now=now) and count > 0
    return SourceScan(
        "open_loops",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"open_loop_count": count},
    )


def _tail_ledger(name: str, n: int = 5) -> list[dict[str, Any]]:
    path = LEDGERS_DIR / f"{name}.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except OSError:
        return []
    return rows[-n:]


def _scan_active_decisions(now: datetime) -> SourceScan:
    rows = _tail_ledger("DECISION_LEDGER", 10)
    latest: datetime | None = None
    count = 0
    for row in rows:
        ts = _parse_ts(row.get("ts"))
        if ts and _fresh(ts, window_hours=FRESHNESS_HOURS["active_decisions"], now=now):
            count += 1
            if latest is None or ts > latest:
                latest = ts
    session_root = REPO / "YAWMIYAT__journaling" / "sessions"
    for path in _latest_json_files(session_root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ts = _parse_ts(payload.get("captured_at") or payload.get("imported_at"))
        decisions = payload.get("decisions") or []
        if isinstance(decisions, list) and decisions:
            if ts and _fresh(ts, window_hours=FRESHNESS_HOURS["active_decisions"], now=now):
                count += len(decisions)
                if latest is None or (ts and ts > latest):
                    latest = ts
    window = FRESHNESS_HOURS["active_decisions"]
    found = _fresh(latest, window_hours=window, now=now) and count > 0
    return SourceScan(
        "active_decisions",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"decision_count": count},
    )


def _scan_thabat_summary(now: datetime) -> SourceScan:
    rows = _tail_ledger("EVENT_LEDGER", 5)
    latest: datetime | None = None
    actions: list[str] = []
    for row in rows:
        ts = _parse_ts(row.get("ts"))
        if ts and (latest is None or ts > latest):
            latest = ts
        action = row.get("action")
        if isinstance(action, str):
            actions.append(action)
    window = FRESHNESS_HOURS["thabat_summary"]
    found = _fresh(latest, window_hours=window, now=now) and bool(actions)
    return SourceScan(
        "thabat_summary",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"recent_actions": actions[-5:]},
    )


def _scan_recent_interactions(now: datetime) -> SourceScan:
    latest: datetime | None = None
    count = 0
    if RUNTIME_EVENTS.exists():
        try:
            for line in RUNTIME_EVENTS.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event") not in {"inbound_persisted", "turn_completed"}:
                    continue
                count += 1
        except OSError:
            pass
        try:
            mtime = datetime.fromtimestamp(RUNTIME_EVENTS.stat().st_mtime, tz=timezone.utc)
            latest = mtime
        except OSError:
            pass
    window = FRESHNESS_HOURS["recent_interactions"]
    found = _fresh(latest, window_hours=window, now=now) and count > 0
    return SourceScan(
        "recent_interactions",
        found,
        latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        {"interaction_count": count},
    )


_SCANNERS = {
    "yawmiyat_journal": _scan_yawmiyat_journal,
    "witness_reflection": _scan_witness_reflection,
    "pulse_entries": _scan_pulse_entries,
    "whoop_badan": _scan_whoop_badan,
    "sukoon_capacity": _scan_sukoon_capacity,
    "open_loops": _scan_open_loops,
    "active_decisions": _scan_active_decisions,
    "thabat_summary": _scan_thabat_summary,
    "recent_interactions": _scan_recent_interactions,
}


def _confidence(found: tuple[str, ...]) -> Literal["high", "medium", "low"]:
    n = len(found)
    if n >= 3:
        return "high"
    if n >= 1:
        return "medium"
    return "low"


def refresh_context(*, now: datetime | None = None) -> ContextRefresh:
    current = now or datetime.now(timezone.utc)
    scans = [_SCANNERS[key](current) for key in ALL_SOURCES]
    found = tuple(scan.source_key for scan in scans if scan.found)
    missing = tuple(scan.source_key for scan in scans if not scan.found)
    timestamps = {
        scan.source_key: scan.latest_ts
        for scan in scans
        if scan.latest_ts is not None
    }
    snapshots = {scan.source_key: dict(scan.safe_facts) for scan in scans}
    sukoon = snapshots.get("sukoon_capacity", {}).get("capacity", "unknown")
    if sukoon not in {"green", "yellow", "red"}:
        sukoon = "unknown"
    return ContextRefresh(
        refreshed_at=utc_now(),
        sources_checked=ALL_SOURCES,
        sources_found=found,
        missing_sources=missing,
        latest_entry_timestamps=timestamps,
        confidence=_confidence(found),
        privacy_level="strict_local",
        sukoon_capacity=sukoon,
        source_snapshots=snapshots,
    )
