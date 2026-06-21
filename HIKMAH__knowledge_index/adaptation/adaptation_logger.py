"""AdaptationLogger — append-only JSONL writer for format rotation events.

Writes one line per rotation event to ADAPTATION_LEDGER.jsonl.
Each line is a JSON object conforming to the schema defined in the Phase 18
research document.

Schema example:
{
  "ts": "2026-06-21T09:30:00Z",
  "adaptation_id": "ADAPT-AMMAR-20260621-001",
  "persona": "AMMAR",
  "event_type": "format_rotation",
  "old_format": "standard",
  "new_format": "short",
  "trigger": "engagement_threshold_breach",
  "response_rate": 0.65,
  "response_rate_threshold": 0.80,
  "calculation_window_days": 7,
  "denominator": 20,
  "numerator": 13,
  "rationale": "AMMAR response rate 65% < 80%, switching from 'standard' to 'short' format",
  "ledger_hash": "a1b2c3d4e5f6a7b8"
}
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class AdaptationLogger:
    """Append-only JSONL writer for format rotation audit events.

    Parameters
    ----------
    ledger_path : Path
        Path to ADAPTATION_LEDGER.jsonl. Created on first write.
    """

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = ledger_path

    def log_rotation(
        self,
        persona: str,
        old_format: str,
        new_format: str,
        response_rate: float,
        numerator: int,
        denominator: int,
        reason: str,
        threshold: float = 0.80,
        window_days: int = 7,
    ) -> str:
        """Append a format_rotation event to the ledger.

        Parameters
        ----------
        persona : str
            Persona identifier.
        old_format : str
            The format that was active before this rotation.
        new_format : str
            The format being switched to.
        response_rate : float
            Calculated response rate that triggered the rotation.
        numerator : int
            Number of responses received.
        denominator : int
            Number of successful deliveries in the window.
        reason : str
            Short trigger label (e.g. "engagement_threshold_breach").
        threshold : float
            Response rate threshold that triggers rotation. Defaults to 0.80.
        window_days : int
            Rolling window used for the rate calculation. Defaults to 7.

        Returns
        -------
        str
            The adaptation_id of the written entry (e.g. "ADAPT-AMMAR-20260621-001").
        """
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y%m%d")

        # Build adaptation_id — count today's entries for this persona first
        count = self._count_today_entries(persona, today_str)
        adaptation_id = f"ADAPT-{persona}-{today_str}-{count + 1:03d}"

        rationale = (
            f"{persona} response rate {response_rate:.0%} < {threshold:.0%}, "
            f"switching from '{old_format}' to '{new_format}' format"
        )

        entry = {
            "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "adaptation_id": adaptation_id,
            "persona": persona,
            "event_type": "format_rotation",
            "old_format": old_format,
            "new_format": new_format,
            "trigger": reason,
            "response_rate": response_rate,
            "response_rate_threshold": threshold,
            "calculation_window_days": window_days,
            "denominator": denominator,
            "numerator": numerator,
            "rationale": rationale,
        }

        # Compute hash from the JSON string (before adding the hash itself)
        json_str = json.dumps(entry, separators=(",", ":"))
        ledger_hash = hashlib.sha256(json_str.encode()).hexdigest()[:16]
        entry["ledger_hash"] = ledger_hash

        self._append_entry(entry)
        return adaptation_id

    # ---- private helpers ----------------------------------------------------

    def _count_today_entries(self, persona: str, today_str: str) -> int:
        """Count existing format_rotation entries for persona today."""
        if not self.ledger_path.exists():
            return 0
        count = 0
        try:
            with self.ledger_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if (
                        entry.get("persona") == persona
                        and entry.get("event_type") == "format_rotation"
                        and entry.get("ts", "").startswith(
                            f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:8]}"
                        )
                    ):
                        count += 1
        except OSError:
            pass
        return count

    def _append_entry(self, entry: dict) -> None:
        """Append a JSON line to the ledger file, creating it if needed."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
