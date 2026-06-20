"""Agent routing from refreshed context."""
from __future__ import annotations

from datetime import datetime

from ..contracts import ContextRefresh


def _freshness_rank(refresh: ContextRefresh, *keys: str) -> datetime | None:
    latest: datetime | None = None
    for key in keys:
        raw = refresh.latest_entry_timestamps.get(key)
        if not raw:
            continue
        try:
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if latest is None or ts > latest:
            latest = ts
    return latest


def pick_agent(refresh: ContextRefresh) -> str:
    """Hayat if body metrics freshest, Sadiq if journal freshest, else Salman."""
    body_ts = _freshness_rank(refresh, "whoop_badan", "pulse_entries")
    journal_ts = _freshness_rank(refresh, "yawmiyat_journal", "witness_reflection")

    body_fresh = "whoop_badan" in refresh.sources_found or "pulse_entries" in refresh.sources_found
    journal_fresh = (
        "yawmiyat_journal" in refresh.sources_found
        or "witness_reflection" in refresh.sources_found
    )

    if body_fresh and journal_fresh:
        if body_ts and journal_ts:
            return "Hayat" if body_ts >= journal_ts else "Sadiq"
        if body_ts:
            return "Hayat"
        if journal_ts:
            return "Sadiq"
    if body_fresh:
        return "Hayat"
    if journal_fresh:
        return "Sadiq"
    return "Salman"
