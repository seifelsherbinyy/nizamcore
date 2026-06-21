"""WeeklyResponseRateCalculator — computes 7-day response rate from delivery ledger.

Reads the DELIVERY_LEDGER.jsonl (written by Phase 17 DeliveryLedger) and
calculates the fraction of successful deliveries within the past N days that
received a response event.

Key contract
------------
- Returns (rate: float, numerator: int, denominator: int)
- denominator=0 (no qualifying deliveries) → returns (1.0, 0, 0) — skip adaptation
- Only counts delivery events with status="success" and sent_at within the window
- Only counts response events whose message_id is in the qualifying delivery set
- Malformed JSONL lines are silently skipped
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Tuple


class WeeklyResponseRateCalculator:
    """Calculate weekly response rate for a persona from the delivery ledger.

    Parameters
    ----------
    ledger_path : Path
        Path to DELIVERY_LEDGER.jsonl (produced by Phase 17 DeliveryLedger).
    """

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = ledger_path

    def calculate(self, persona: str, days: int = 7) -> Tuple[float, int, int]:
        """Compute the response rate for a persona over the past N days.

        Parameters
        ----------
        persona : str
            Persona identifier to filter events by.
        days : int
            Rolling window in days. Defaults to 7.

        Returns
        -------
        Tuple[float, int, int]
            (rate, numerator, denominator) where:
            - rate = numerator / denominator (or 1.0 if denominator == 0)
            - numerator = number of delivered messages that received a response
            - denominator = number of successful deliveries within window
        """
        if not self.ledger_path.exists():
            return (1.0, 0, 0)

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_entries = self._read_all_entries()

        # Collect qualifying delivery message_ids
        qualifying_ids: set[str] = set()
        for entry in all_entries:
            if entry.get("event_type") != "delivery":
                continue
            if entry.get("persona") != persona:
                continue
            if entry.get("status") != "success":
                continue
            sent_at_raw = entry.get("sent_at", "")
            try:
                sent_at = self._parse_iso(sent_at_raw)
            except (ValueError, TypeError):
                continue
            if sent_at >= cutoff:
                msg_id = entry.get("message_id")
                if msg_id:
                    qualifying_ids.add(msg_id)

        denominator = len(qualifying_ids)
        if denominator == 0:
            return (1.0, 0, 0)

        # Count response events whose message_id is in qualifying set
        numerator = 0
        for entry in all_entries:
            if entry.get("event_type") != "response":
                continue
            if entry.get("message_id") in qualifying_ids:
                numerator += 1

        rate = numerator / denominator
        return (rate, numerator, denominator)

    def _read_all_entries(self) -> list[dict]:
        """Read all valid JSONL entries from the ledger, skipping malformed lines."""
        entries: list[dict] = []
        try:
            with self.ledger_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
        return entries

    @staticmethod
    def _parse_iso(ts: str) -> datetime:
        """Parse an ISO 8601 UTC timestamp string to a timezone-aware datetime.

        Handles both 'Z' suffix and '+00:00' offset.
        """
        # Normalize 'Z' suffix to UTC offset
        normalized = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
