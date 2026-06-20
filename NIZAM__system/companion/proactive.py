from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .contracts import ProactiveCandidate

REPO = Path(__file__).resolve().parents[2]
CADENCE_RULES = (
    REPO
    / "NIZAM__system"
    / "modes"
    / "khaldun_islamic_cosmic_wisdom"
    / "pulsation_cadence_rules.json"
)


@dataclass(frozen=True)
class ProactivePolicy:
    timezone: str = "Africa/Cairo"
    quiet_start: time = time(22, 30)
    quiet_end: time = time(7, 0)
    max_daily: int = 10
    cooldown_minutes: int = 30
    min_relevance: float = 0.7


def _parse_hhmm(raw: str, default: time) -> time:
    try:
        hour, minute = raw.split(":", 1)
        return time(int(hour), int(minute))
    except (TypeError, ValueError, AttributeError):
        return default


def load_proactive_policy(path: Path = CADENCE_RULES) -> ProactivePolicy:
    defaults = ProactivePolicy()
    if not path.exists():
        return defaults
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return defaults

    quiet = data.get("quiet_hours") or {}
    max_daily = (
        data.get("max_proactive_sends_per_day")
        or data.get("max_islamic_reminders_per_day")
        or defaults.max_daily
    )
    return ProactivePolicy(
        timezone=str(data.get("timezone") or defaults.timezone),
        quiet_start=_parse_hhmm(str(quiet.get("start") or "22:30"), defaults.quiet_start),
        quiet_end=_parse_hhmm(str(quiet.get("end") or "07:00"), defaults.quiet_end),
        max_daily=int(max_daily),
        cooldown_minutes=int(data.get("cooldown_minutes", defaults.cooldown_minutes)),
        min_relevance=float(data.get("min_relevance", defaults.min_relevance)),
    )


def eligible(
    candidate: ProactiveCandidate,
    *,
    now: datetime,
    sent_today: list[datetime],
    paused: bool,
    sukoon_red: bool = False,
    sukoon_capacity: str = "green",
    crisis_suppress: bool = False,
    policy: ProactivePolicy | None = None,
) -> tuple[bool, str, bool]:
    """Return (eligible, reason, tiny_mode).

    Crisis suppress hard-blocks sends. Yellow/red capacity downshifts to tiny mode
    without blocking unless crisis_suppress or legacy sukoon_red is set.
    """
    active_policy = policy or load_proactive_policy()
    local = now.astimezone(ZoneInfo(active_policy.timezone))
    expiry = datetime.fromisoformat(candidate.expires_at.replace("Z", "+00:00"))
    tiny_mode = sukoon_capacity in {"yellow", "red"}

    if paused:
        return False, "paused", tiny_mode
    if crisis_suppress or sukoon_red:
        return False, "crisis_suppress", tiny_mode
    if now >= expiry:
        return False, "expired", tiny_mode
    if (
        candidate.relevance_score < active_policy.min_relevance
        or not candidate.source_refs
    ):
        return False, "insufficient_evidence", tiny_mode
    if local.time() >= active_policy.quiet_start or local.time() < active_policy.quiet_end:
        return False, "quiet_hours", tiny_mode
    local_sent = [item.astimezone(ZoneInfo(active_policy.timezone)) for item in sent_today]
    today = [item for item in local_sent if item.date() == local.date()]
    if len(today) >= active_policy.max_daily:
        return False, "daily_limit", tiny_mode
    if today and local - max(today) < timedelta(minutes=active_policy.cooldown_minutes):
        return False, "cooldown", tiny_mode
    return True, "eligible", tiny_mode
