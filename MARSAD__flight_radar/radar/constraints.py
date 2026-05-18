"""
ROUTING CONSTRAINT ENGINE — single source of truth for all four pipeline stages.

All four stages (DISCOVER, MONITOR, ALERT, FORECAST) call apply_constraints()
before storing any result. No duplicate constraint logic elsewhere.

Constraints enforced:
- Origin: CAI only
- Destinations: USA major airports only
- Cabins: BUSINESS or PREMIUM_ECONOMY only
- Trip duration: 9–14 nights inclusive
- Max one-way flight time: 30 hours (applied INDEPENDENTLY to outbound and return)
- Travel window: WINDOW_START through WINDOW_END
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from radar.config import (
    CABINS,
    DURATION_MAX_NIGHTS,
    DURATION_MIN_NIGHTS,
    MAX_ONE_WAY_HOURS,
    ORIGIN,
    USA_DESTINATIONS,
    WINDOW_END,
    WINDOW_START,
)


@dataclass
class FlightItinerary:
    """Minimal itinerary representation fed into the constraint engine."""
    origin: str
    destination: str
    cabin: str
    outbound_date: date
    return_date: date
    outbound_duration_hours: float
    return_duration_hours: float
    carrier: str
    price_usd: float


@dataclass
class ConstraintResult:
    passed: bool
    failures: list[str]

    def __bool__(self) -> bool:
        return self.passed


def apply_constraints(itin: FlightItinerary) -> ConstraintResult:
    """
    Apply all routing constraints to a single itinerary.
    Returns ConstraintResult with passed=True only if ALL constraints are met.

    Called by all four pipeline stages before any result is stored.
    Never raises — returns a failure list for logging.
    """
    failures: list[str] = []

    # 1. Origin must be CAI
    if itin.origin.upper() != ORIGIN:
        failures.append(f"origin={itin.origin!r} — must be {ORIGIN!r}")

    # 2. Destination must be a USA major airport
    if itin.destination.upper() not in USA_DESTINATIONS:
        failures.append(
            f"destination={itin.destination!r} — not in USA_DESTINATIONS"
        )

    # 3. Cabin must be BUSINESS or PREMIUM_ECONOMY
    if itin.cabin.upper() not in CABINS:
        failures.append(
            f"cabin={itin.cabin!r} — must be one of {CABINS}"
        )

    # 4. Trip duration must be 9–14 nights inclusive
    nights = (itin.return_date - itin.outbound_date).days
    if not (DURATION_MIN_NIGHTS <= nights <= DURATION_MAX_NIGHTS):
        failures.append(
            f"duration={nights} nights — must be {DURATION_MIN_NIGHTS}–{DURATION_MAX_NIGHTS}"
        )

    # 5. Outbound flight time ≤ 30 hours (INDEPENDENT check — NOT round-trip total)
    if itin.outbound_duration_hours > MAX_ONE_WAY_HOURS:
        failures.append(
            f"outbound_duration={itin.outbound_duration_hours}h — exceeds {MAX_ONE_WAY_HOURS}h limit"
        )

    # 6. Return flight time ≤ 30 hours (INDEPENDENT check — NOT round-trip total)
    if itin.return_duration_hours > MAX_ONE_WAY_HOURS:
        failures.append(
            f"return_duration={itin.return_duration_hours}h — exceeds {MAX_ONE_WAY_HOURS}h limit"
        )

    # 7. Outbound date must fall within travel window
    window_start = date.fromisoformat(WINDOW_START)
    window_end = date.fromisoformat(WINDOW_END)

    if not (window_start <= itin.outbound_date <= window_end):
        failures.append(
            f"outbound_date={itin.outbound_date} — outside window "
            f"{WINDOW_START}–{WINDOW_END}"
        )

    # 8. Return date must also be within window (no return after Sep 30)
    if itin.return_date > window_end:
        failures.append(
            f"return_date={itin.return_date} — after window end {WINDOW_END}"
        )

    return ConstraintResult(passed=len(failures) == 0, failures=failures)


def is_valid_destination(code: str) -> bool:
    return code.upper() in USA_DESTINATIONS


def is_valid_cabin(cabin: str) -> bool:
    return cabin.upper() in CABINS


def is_valid_window(d: date) -> bool:
    return date.fromisoformat(WINDOW_START) <= d <= date.fromisoformat(WINDOW_END)


def generate_search_combinations() -> list[dict]:
    """
    Generate all valid (destination, cabin) search combinations.
    Used by DISCOVER stage to seed the full search matrix.
    Returns list of dicts with origin, destination, cabin, window_start, window_end.
    """
    combos = []
    for dest in USA_DESTINATIONS:
        for cabin in CABINS:
            combos.append({
                "origin": ORIGIN,
                "destination": dest,
                "cabin": cabin,
                "window_start": WINDOW_START,
                "window_end": WINDOW_END,
            })
    return combos


def validate_search_params(
    origin: str,
    destination: str,
    cabin: str,
    outbound_date: Optional[date] = None,
) -> ConstraintResult:
    """
    Lightweight pre-search validation before making any API call.
    Checks origin, destination, cabin, and optionally the outbound date.
    Does not check duration or flight time (not known until results return).
    """
    failures: list[str] = []

    if origin.upper() != ORIGIN:
        failures.append(f"origin={origin!r} must be {ORIGIN!r}")

    if destination.upper() not in USA_DESTINATIONS:
        failures.append(f"destination={destination!r} not in USA_DESTINATIONS")

    if cabin.upper() not in CABINS:
        failures.append(f"cabin={cabin!r} must be one of {CABINS}")

    if outbound_date is not None and not is_valid_window(outbound_date):
        failures.append(f"outbound_date={outbound_date} outside travel window")

    return ConstraintResult(passed=len(failures) == 0, failures=failures)
