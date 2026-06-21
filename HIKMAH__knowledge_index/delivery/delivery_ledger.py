"""
delivery_ledger.py — Immutable JSONL Audit Trail for Message Delivery & Response Tracking

PURPOSE
-------
Records every message delivery attempt, response received, and engagement window
closure as an append-only audit trail. Phase 17 builds on the established JSONL
ledger pattern from Phase 14 (index writer), Phase 15 (refresh audit), and
Phase 16 (message ledger) — this ledger tracks the outer delivery lifecycle.

WHY JSONL (JSON Lines) FORMAT
------------------------------
JSONL (one JSON object per line) is ideal for this use case:

1. Append-only: New events appended without reading existing content — O(1) writes
2. Atomic writes: Single line appended atomically (no partial record corruption)
3. Concurrent reads: Multiple readers safe (append doesn't corrupt existing lines)
4. Stream processing: Events can be processed line-by-line with minimal memory
5. Debuggable: Human-readable, can be inspected with any text editor
6. Compatible: Standard format for event ledgers (used by Kafka, Fluentd, etc.)

PRIVACY ENFORCEMENT — CONTEXT TAGS WHITELIST
---------------------------------------------
The delivery ledger stores context_tags alongside each delivery to enable
downstream analytics (Phase 18: adaptation). However, raw PII must never
reach the ledger.

Context tags are validated against a strict whitelist before writing:
  - "technical"  → technology/code/tools topics
  - "health"     → wellbeing/fitness topics
  - "financial"  → money/budget/investment topics
  - "strategic"  → planning/goals/milestones topics
  - "personal"   → relationships/growth topics

Any tag outside this whitelist raises ValueError BEFORE the ledger write.
This is a FAIL-SAFE privacy gate: if the caller passes an invalid tag,
the write is blocked (not silently coerced). The caller must fix the tag.

This mirrors the Phase 16 MessageLedger pattern (same whitelist, same
fail-safe semantics).

LEDGER ENTRY TYPES
------------------
Three event types form the delivery lifecycle:

1. "delivery" — Written when a message is sent via Telegram relay
   Fields: message_id, telegram_message_id, persona, message_text, intent,
           sent_at, delivered_at, context_tags, status, error_reason

2. "response" — Written when a user replies to a delivered message
   Fields: message_id, telegram_message_id, persona, response_text,
           response_time, engagement_latency_seconds, engagement_status

3. "engagement_window_closed" — Written when 1-hour window expires with no reply
   Fields: message_id, telegram_message_id, persona, engagement_status

All entries share base fields: ts (write time), event_type, ledger_hash.

INTEGRITY HASHING
-----------------
Each entry includes a "ledger_hash" field: SHA256 of the serialized entry
dict (truncated to 16 chars). This is NOT a chain hash (each entry is
independently hashed) — it provides tamper-evidence for individual entries
without requiring sequential reads to verify the chain.

For full chain integrity (Phase 15 pattern), future phases can add prev_hash
linking. For Phase 17, per-entry SHA256 is sufficient for audit purposes.

LEDGER ENTRY FORMAT
-------------------
Delivery event:
{
  "ts": "2026-06-21T09:30:45.123Z",
  "message_id": "MSG-20260621093045123-A7F2E8CD",
  "telegram_message_id": 12345,
  "persona": "AMMAR",
  "event_type": "delivery",
  "message_text": "Pick one and move forward.",
  "intent": "open_work",
  "sent_at": "2026-06-21T09:30:45.000Z",
  "delivered_at": "2026-06-21T09:30:45.500Z",
  "context_tags": ["technical"],
  "status": "success",
  "error_reason": null,
  "ledger_hash": "a1b2c3d4e5f6a7b8"
}

Response event:
{
  "ts": "2026-06-21T09:45:00.000Z",
  "message_id": "MSG-20260621093045123-A7F2E8CD",
  "telegram_message_id": 12345,
  "persona": "AMMAR",
  "event_type": "response",
  "response_text": "OK noted",
  "response_time": "2026-06-21T09:45:00Z",
  "engagement_latency_seconds": 855.0,
  "engagement_status": "successful",
  "ledger_hash": "b2c3d4e5f6a7b8c9"
}

Engagement window closed:
{
  "ts": "2026-06-21T10:30:45.123Z",
  "message_id": "MSG-20260621093045123-A7F2E8CD",
  "telegram_message_id": 12345,
  "persona": "AMMAR",
  "event_type": "engagement_window_closed",
  "engagement_status": "no_response",
  "ledger_hash": "c3d4e5f6a7b8c9d0"
}

ERROR HANDLING PHILOSOPHY
--------------------------
- File write errors: Propagated to caller (fail-fast, never silently ignored)
- Missing ledger file on read: Treated as empty ledger (returns empty list/None)
- Malformed JSON lines on read: Skipped (old corruption must not crash queries)
- Invalid context_tags: ValueError raised BEFORE write (privacy gate cannot fail)

USAGE EXAMPLES
--------------
>>> from HIKMAH__knowledge_index.delivery.delivery_ledger import DeliveryLedger
>>> from pathlib import Path

# Initialize ledger (creates file on first write)
>>> ledger = DeliveryLedger(Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"))

# Log a delivery
>>> ledger.log_delivery(
...     message_id="MSG-20260621093045123-A7F2E8CD",
...     telegram_message_id=12345,
...     persona="AMMAR",
...     message_text="Pick one and move forward.",
...     intent="open_work",
...     sent_at="2026-06-21T09:30:45Z",
...     delivered_at="2026-06-21T09:30:46Z",
...     context_tags=["technical"],
...     status="success"
... )

# Log a response
>>> ledger.log_response(
...     message_id="MSG-20260621093045123-A7F2E8CD",
...     telegram_message_id=12345,
...     response_text="On it.",
...     response_time="2026-06-21T09:45:00Z",
...     engagement_latency_seconds=855.0,
...     persona="AMMAR"
... )

# Query deliveries for a persona (most recent first)
>>> entries = ledger.get_deliveries_for_persona("AMMAR", limit=5)

# Check if a message got a response
>>> response = ledger.get_responses_for_message("MSG-20260621093045123-A7F2E8CD")
>>> if response:
...     print(f"Response received: {response['response_text']}")

DEPENDENCIES
------------
- json: JSONL serialization
- hashlib: SHA256 ledger entry hashing
- datetime: UTC timestamp generation
- pathlib: Platform-independent path handling
- typing: Optional, List type annotations
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


CONTEXT_TAGS_WHITELIST: List[str] = [
    "technical",
    "health",
    "financial",
    "strategic",
    "personal",
]


class DeliveryLedger:
    """
    Append-only JSONL ledger for message delivery and response tracking.

    Records three event types: delivery, response, engagement_window_closed.

    All writes are append-only (never overwrites existing entries).
    Privacy gate: context_tags validated against CONTEXT_TAGS_WHITELIST.
    Integrity: Each entry includes SHA256 hash of its own content.

    Parameters
    ----------
    ledger_path : Path
        Path to the JSONL ledger file. Created on first write.
        Parent directories created automatically.
    """

    def __init__(self, ledger_path: Path) -> None:
        """
        Initialize the delivery ledger.

        Parameters
        ----------
        ledger_path : Path
            Path to the JSONL ledger file. Created on first write.
            Parent directories are created if they do not exist.
        """
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, entry: dict) -> str:
        """
        Compute SHA256 hash of the entry dict (16-char truncation).

        The entry dict is serialized to JSON (sorted keys for determinism)
        before hashing. The hash is truncated to 16 hex characters for
        compactness while retaining sufficient tamper-evidence.

        Parameters
        ----------
        entry : dict
            Entry dict (without the "ledger_hash" field itself).

        Returns
        -------
        str
            16-character lowercase hex string.
        """
        serialized = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def _append_entry(self, entry: dict) -> None:
        """
        Append a single entry dict to the ledger file as a JSON line.

        Computes and sets "ledger_hash" on the entry before writing.
        Appends to file (creates if not exists).

        Parameters
        ----------
        entry : dict
            Entry dict without "ledger_hash" field.

        Raises
        ------
        OSError
            If the file cannot be written (propagated to caller).
        """
        # Add hash before writing (hash includes all other fields)
        entry["ledger_hash"] = self._compute_hash(entry)

        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _read_entries(self) -> List[dict]:
        """
        Read all entries from the ledger file.

        Returns empty list if file does not exist.
        Skips malformed JSON lines (don't crash on old corruption).

        Returns
        -------
        List[dict]
            All valid parsed entries from the ledger.
        """
        if not self.ledger_path.exists():
            return []

        entries = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines (don't crash on corrupted entries)
                    continue
        return entries

    def log_delivery(
        self,
        message_id: str,
        telegram_message_id: Optional[int],
        persona: str,
        message_text: str,
        intent: str,
        sent_at: str,
        delivered_at: Optional[str],
        context_tags: List[str],
        status: str,
        error_reason: Optional[str] = None,
    ) -> None:
        """
        Log a message delivery event to the ledger.

        Called after sending a message via the Telegram relay. Records
        the unique message_id, Telegram's assigned message_id, delivery
        timestamps, and delivery status for the audit trail.

        Privacy gate: context_tags are validated against CONTEXT_TAGS_WHITELIST
        before any write. Invalid tags raise ValueError (fail-safe: write blocked,
        not silently coerced).

        Parameters
        ----------
        message_id : str
            Unique message ID (MSG-{YYYYMMDDHHMMSSMMMM}-{8-CHAR-HEX}).
        telegram_message_id : Optional[int]
            Telegram API message_id from sendMessage response. None if delivery failed.
        persona : str
            Persona name (AMMAR, HIKMAH, etc.).
        message_text : str
            Full text of the sent message.
        intent : str
            Intent string that prompted the message (e.g., "open_work").
        sent_at : str
            ISO 8601 UTC timestamp when relay send was initiated.
        delivered_at : Optional[str]
            ISO 8601 UTC timestamp when Telegram confirmed delivery. None if failed.
        context_tags : List[str]
            List of context category tags. Must be subset of CONTEXT_TAGS_WHITELIST.
        status : str
            Delivery status: "success" or "failure".
        error_reason : Optional[str]
            Error description if status="failure". None if success.

        Raises
        ------
        ValueError
            If any context_tag is not in CONTEXT_TAGS_WHITELIST.
        OSError
            If ledger file cannot be written.
        """
        # Privacy gate: validate context_tags before any write
        for tag in context_tags:
            if tag not in CONTEXT_TAGS_WHITELIST:
                raise ValueError(
                    f"Invalid context_tag {tag!r}: must be one of "
                    f"{CONTEXT_TAGS_WHITELIST}. Privacy gate: write blocked."
                )

        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        entry = {
            "ts": ts,
            "message_id": message_id,
            "telegram_message_id": telegram_message_id,
            "persona": persona,
            "event_type": "delivery",
            "message_text": message_text,
            "intent": intent,
            "sent_at": sent_at,
            "delivered_at": delivered_at,
            "context_tags": context_tags,
            "status": status,
            "error_reason": error_reason,
        }

        self._append_entry(entry)

    def log_response(
        self,
        message_id: str,
        telegram_message_id: int,
        response_text: str,
        response_time: str,
        engagement_latency_seconds: float,
        persona: str,
    ) -> None:
        """
        Log a user response event to the ledger.

        Called when the response monitor detects a Telegram reply that
        correlates to a previously sent message (matched via reply_to_message_id).

        Response text is truncated to 500 characters for safety (prevents
        very long messages from bloating the ledger).

        Parameters
        ----------
        message_id : str
            Unique message ID of the original sent message.
        telegram_message_id : int
            Telegram API message_id of the original sent message.
        response_text : str
            Text content of the user's reply (truncated to 500 chars).
        response_time : str
            ISO 8601 UTC timestamp when the reply was received.
        engagement_latency_seconds : float
            Seconds between sent_at and response_time (engagement latency).
        persona : str
            Persona name (AMMAR, HIKMAH, etc.).

        Raises
        ------
        OSError
            If ledger file cannot be written.
        """
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        # Truncate response text to 500 chars for safety
        truncated_text = response_text[:500] if len(response_text) > 500 else response_text

        entry = {
            "ts": ts,
            "message_id": message_id,
            "telegram_message_id": telegram_message_id,
            "persona": persona,
            "event_type": "response",
            "response_text": truncated_text,
            "response_time": response_time,
            "engagement_latency_seconds": engagement_latency_seconds,
            "engagement_status": "successful",
        }

        self._append_entry(entry)

    def log_no_response(
        self,
        message_id: str,
        telegram_message_id: int,
        persona: str,
    ) -> None:
        """
        Log a no-response (engagement window closed) event to the ledger.

        Called when the 1-hour engagement window expires without receiving
        a reply from the user. This event enables Phase 18 adaptation
        analytics (response rate calculation).

        Parameters
        ----------
        message_id : str
            Unique message ID of the original sent message.
        telegram_message_id : int
            Telegram API message_id of the original sent message.
        persona : str
            Persona name (AMMAR, HIKMAH, etc.).

        Raises
        ------
        OSError
            If ledger file cannot be written.
        """
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        entry = {
            "ts": ts,
            "message_id": message_id,
            "telegram_message_id": telegram_message_id,
            "persona": persona,
            "event_type": "engagement_window_closed",
            "engagement_status": "no_response",
        }

        self._append_entry(entry)

    def get_deliveries_for_persona(self, persona: str, limit: int = 10) -> List[dict]:
        """
        Retrieve the most recent delivery events for a specific persona.

        Returns delivery events in reverse chronological order (most recent first).
        Skips non-delivery event types (responses, window closures).

        If the ledger file does not exist, returns an empty list.

        Parameters
        ----------
        persona : str
            Persona name to filter by.
        limit : int, optional
            Maximum number of entries to return. Default 10.

        Returns
        -------
        List[dict]
            List of delivery event dicts, most recent first.
            Empty list if no matching entries or file doesn't exist.
        """
        all_entries = self._read_entries()
        deliveries = [
            entry for entry in all_entries
            if entry.get("persona") == persona
            and entry.get("event_type") == "delivery"
        ]
        # Most recent first
        deliveries.reverse()
        return deliveries[:limit]

    def get_responses_for_message(self, message_id: str) -> Optional[dict]:
        """
        Find the response event for a specific message ID.

        Returns the first response entry matching the given message_id,
        or None if no response has been logged yet.

        Parameters
        ----------
        message_id : str
            Unique message ID to look up.

        Returns
        -------
        Optional[dict]
            Response event dict if found, None otherwise.
        """
        all_entries = self._read_entries()
        for entry in all_entries:
            if (
                entry.get("message_id") == message_id
                and entry.get("event_type") == "response"
            ):
                return entry
        return None
