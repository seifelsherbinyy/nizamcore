"""calendar_idempotency.py — deterministic calendar idempotency, no API calls.

Owning contract: NIZAM-CONTRACT-04 calendar_policy.safeguards v1.0.0
Satisfies:       C04-T04, C01 (calendar), C05 (calendar), playbook C01, C04, C05
Phase:           R1_FIXTURES

DOCTRINE (Contract 04 calendar_policy.safeguards):
  * "Idempotency key required for generated events."
  * "Multiple matching idempotency keys fail closed."
  * "Never claim a human-only Calendar Approved field was personally approved."
  * "Do not infer free time from missing calendar data."

SCOPE BOUNDARY: this module computes keys and detects duplicates. It contains NO
Google Calendar client, no network call and no mutation. Actuation is R5 of the
rollout playbook and is NOT authorized by this module existing.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum

# Fields a human alone may set. The agent may never write these.
HUMAN_ONLY_FIELDS = frozenset({
    "calendar_approved",
    "approved_by_human",
    "human_confirmed",
    "operator_confirmed_externalize",
})


class CalendarIdempotencyError(Exception):
    """Raised when an idempotency or human-only invariant would be violated."""


class DuplicateKeyError(CalendarIdempotencyError):
    """More than one existing event matches one idempotency key: fail closed."""


class HumanOnlyFieldError(CalendarIdempotencyError):
    """The agent attempted to set a human-only truth field."""


def _slug(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(text).strip().lower()).strip("-")
    return s[:limit] or "untitled"


@dataclass(frozen=True)
class EventIntent:
    """A proposed calendar mutation, before any actuation exists."""

    run_date: str          # YYYY-MM-DD, Africa/Cairo civil date of the run
    purpose: str           # e.g. focus_block, recovery_block, workout, sleep_window
    window_start: str      # ISO-8601 instant
    window_end: str        # ISO-8601 instant
    title: str
    calendar_id: str = "primary"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.run_date):
            raise CalendarIdempotencyError("run_date must be YYYY-MM-DD")
        for f in ("purpose", "window_start", "window_end", "title"):
            if not str(getattr(self, f)).strip():
                raise CalendarIdempotencyError(f"{f} is required")

    def idempotency_key(self) -> str:
        """Stable across retries of the same logical intent, and only that.

        Derived from the civil run date, the purpose, the exact window and the
        title slug. Two runs proposing the same block on the same day produce
        the same key, so a retry cannot create a second event.
        """
        material = "|".join([
            "nizam.calendar.v1",
            self.calendar_id,
            self.run_date,
            _slug(self.purpose),
            self.window_start,
            self.window_end,
            _slug(self.title),
        ])
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
        return f"nizam-{_slug(self.purpose, 20)}-{self.run_date}-{digest}"


class Decision(str, Enum):
    CREATE = "create"
    SKIP_ALREADY_PRESENT = "skip_already_verified"
    FAIL_CLOSED_AMBIGUOUS = "fail_closed_ambiguous"


@dataclass(frozen=True)
class Resolution:
    decision: Decision
    idempotency_key: str
    matched_event_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = field(default_factory=tuple)


def resolve(intent: EventIntent, existing_keys: dict[str, list[str]]) -> Resolution:
    """Decide create / skip / fail-closed for one intent.

    `existing_keys` maps an idempotency key to the event ids already carrying it.
    It is supplied by the caller from a real read; this function never reads.

    A missing key means "not present", NOT "free time" — absence of calendar
    data is never treated as availability (Contract 04 safeguard).
    """
    key = intent.idempotency_key()
    matches = tuple(existing_keys.get(key, ()))

    if len(matches) == 0:
        return Resolution(Decision.CREATE, key, (),
                          ("no event carries this idempotency key",))
    if len(matches) == 1:
        return Resolution(Decision.SKIP_ALREADY_PRESENT, key, matches,
                          ("exactly one event already carries this key: this run "
                           "is a retry of an already-satisfied intent",))
    return Resolution(Decision.FAIL_CLOSED_AMBIGUOUS, key, matches,
                      (f"{len(matches)} events carry one idempotency key; "
                       "refusing to guess which is canonical (Contract 04 "
                       "'multiple matching idempotency keys fail closed')",))


def assert_no_human_only_fields(payload: dict) -> None:
    """Refuse any agent-authored payload that sets a human-only truth field."""
    offending = sorted(HUMAN_ONLY_FIELDS.intersection(payload.keys()))
    if offending:
        raise HumanOnlyFieldError(
            "agent may not set human-only truth field(s): "
            + ", ".join(offending)
            + " (Contract 04 calendar_policy safeguard)"
        )
