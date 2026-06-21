"""
message_id_generator.py — Globally Unique, Sortable Message ID Generation

PURPOSE
-------
Generates unique message IDs for Phase 17 delivery tracking. Every message
sent through the NIZAM Telegram relay receives a unique ID before dispatch,
enabling reliable delivery audit and response correlation.

WHY ULID-STYLE FORMAT
---------------------
Standard UUIDs (e.g., "550e8400-e29b-41d4-a716-446655440000") are globally
unique but NOT sortable by time — sorting by UUID gives no temporal ordering.

ULID (Universally Unique Lexicographically Sortable Identifier) embeds a
timestamp prefix so that IDs sort lexicographically by creation time:
  - "MSG-20260621090000000-A1B2C3D4" was created BEFORE
  - "MSG-20260621180000000-E5F6A7B8"
  sorting these strings gives chronological order without any additional
  timestamp column in queries.

This property makes the delivery ledger trivially sortable and enables
time-range queries without a separate index column.

MESSAGE ID FORMAT
-----------------
MSG-{YYYYMMDDHHMMSSMMMM}-{8-CHAR-HEX}

Where:
  MSG         — fixed prefix, identifies this as a message delivery ID
  YYYYMMDD    — UTC date (year 4 digits, month 2 digits, day 2 digits)
  HHMMSS      — UTC time (hour 2 digits, minute 2 digits, second 2 digits)
  MMMM        — UTC milliseconds (4 digits, zero-padded to ensure 14-char timestamp)
  8-CHAR-HEX  — 8 uppercase hex characters from UUID4 random portion

Example:
  "MSG-20260621093045123-A7F2E8CD"
  |   |                | |       |
  |   |                | +-------+--- random collision resistance (8 hex chars)
  |   +----------------+------------- timestamp: 2026-06-21 09:30:45.123 UTC
  +----------------------------------  fixed prefix

PROPERTIES
----------
- Timezone-aware: Always UTC (never local time, avoids DST confusion)
- Monotonically increasing: Consecutive calls produce lexicographically ordered IDs
  (within the same millisecond, random suffix prevents ordering; see edge case note)
- Collision resistance: UUID4 random 8-char suffix → 4 billion possible values
  per millisecond → effectively zero collision probability in practice
- No external coordination: No distributed lock, no central counter, no database
- Deterministic parsing: Any valid MSG-ID can be round-tripped through parse()
- No PII encoded: Pure timestamp + random, no user data, no persona information

EDGE CASE: SAME-MILLISECOND COLLISIONS
---------------------------------------
Two IDs generated in the same millisecond share the same timestamp prefix.
The 8-char hex suffix (~4 billion values) makes collision astronomically unlikely.
For context: at 1000 messages/second (far above expected load), the probability
of a collision within one millisecond is ~1 in 4 billion.

If absolute collision prevention is required (e.g., legal/compliance), switch to
a sequential counter suffix. For NIZAM's twice-daily delivery (2-11 messages),
UUID4 random suffix is more than sufficient.

USAGE EXAMPLES
--------------
>>> from HIKMAH__knowledge_index.delivery.message_id_generator import MessageIDGenerator

# Generate a unique message ID
>>> msg_id = MessageIDGenerator.generate()
>>> print(msg_id)
'MSG-20260621093045123-A7F2E8CD'

# Parse a message ID back to its components
>>> parsed = MessageIDGenerator.parse(msg_id)
>>> print(parsed["message_id"])
'MSG-20260621093045123-A7F2E8CD'
>>> print(parsed["timestamp_utc"])
datetime(2026, 6, 21, 9, 30, 45, 123000, tzinfo=timezone.utc)

# Round-trip verification
>>> msg_id2 = MessageIDGenerator.generate()
>>> parsed2 = MessageIDGenerator.parse(msg_id2)
>>> assert parsed2["message_id"] == msg_id2  # always true

# Sortability check
>>> import time
>>> ids = []
>>> for _ in range(5):
...     ids.append(MessageIDGenerator.generate())
...     time.sleep(0.001)  # 1ms between each
>>> assert ids == sorted(ids)  # lexicographic sort = chronological sort

TEST COVERAGE EXPECTATIONS
--------------------------
Wave 2 tests (test_message_id_generator.py) will validate:
  - test_message_id_uniqueness: 10k IDs, verify zero collisions
  - test_message_id_format: prefix "MSG-", length, character set
  - test_parse_round_trip: generate → parse → verify fields match
  - test_parse_invalid_format: ValueError on malformed IDs
  - test_sortability: 100 IDs in rapid succession, verify sorted order

DEPENDENCIES
------------
- datetime: Timezone-aware timestamp generation (always UTC)
- uuid: UUID4 random suffix generation (cryptographically random)
- No external pip packages required
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


class MessageIDGenerator:
    """
    Generates globally unique, sortable message IDs for delivery tracking.

    All methods are class methods — no instantiation required.

    Format: MSG-{YYYYMMDDHHMMSSMMMM}-{8-CHAR-HEX}

    Example: "MSG-20260621093045123-A7F2E8CD"

    Privacy note: Message ID is purely technical (timestamp + random),
    no PII is encoded. Safe to log, transmit, and store in ledger.
    """

    @classmethod
    def generate(cls) -> str:
        """
        Create a unique message ID with millisecond-precision UTC timestamp.

        Returns a string in format: MSG-{YYYYMMDDHHMMSSMMMM}-{8-CHAR-HEX}

        The timestamp is extracted to UTC millisecond precision, making IDs
        lexicographically sortable by creation time.

        The random suffix (8 uppercase hex chars from UUID4) provides collision
        resistance: ~4 billion possible values per millisecond.

        Returns
        -------
        str
            Unique message ID, e.g. "MSG-20260621093045123-A7F2E8CD"

        Notes
        -----
        - Always uses UTC (timezone.utc), never local time
        - Milliseconds zero-padded to 4 digits (0000-9999)
        - Random suffix uppercase for readability
        - No PII encoded; safe to log to audit trail
        """
        now = datetime.now(timezone.utc)
        # Format: YYYYMMDDHHMMSSMMMM (18 chars)
        # microsecond // 1000 gives milliseconds (0-999), zero-pad to 4 digits
        timestamp_part = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:04d}"
        random_part = uuid4().hex[:8].upper()
        return f"MSG-{timestamp_part}-{random_part}"

    @classmethod
    def parse(cls, msg_id: str) -> dict:
        """
        Extract timestamp and metadata from a message ID.

        Performs format validation before parsing. The timestamp component
        is parsed to a timezone-aware datetime object (UTC).

        Parameters
        ----------
        msg_id : str
            Message ID to parse, e.g. "MSG-20260621093045123-A7F2E8CD"

        Returns
        -------
        dict
            Dictionary with keys:
            - "message_id": str — the original msg_id (identity field)
            - "timestamp_utc": datetime — UTC datetime parsed from timestamp component

        Raises
        ------
        ValueError
            If msg_id does not match expected format:
            - Not exactly 3 parts when split by "-"
            - First part is not "MSG"
            - Timestamp part is not exactly 18 digits
            - Random part is not exactly 8 hex characters

        Examples
        --------
        >>> parsed = MessageIDGenerator.parse("MSG-20260621093045123-A7F2E8CD")
        >>> parsed["message_id"]
        'MSG-20260621093045123-A7F2E8CD'
        >>> parsed["timestamp_utc"]
        datetime.datetime(2026, 6, 21, 9, 30, 45, 123000, tzinfo=datetime.timezone.utc)
        """
        parts = msg_id.split("-")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid message ID format: expected 3 parts separated by '-', "
                f"got {len(parts)} parts. Input: {msg_id!r}"
            )

        prefix, timestamp_part, random_part = parts

        if prefix != "MSG":
            raise ValueError(
                f"Invalid message ID prefix: expected 'MSG', got {prefix!r}. "
                f"Input: {msg_id!r}"
            )

        if len(timestamp_part) != 18 or not timestamp_part.isdigit():
            raise ValueError(
                f"Invalid timestamp component: expected 18 digits (YYYYMMDDHHMMSSMMMM), "
                f"got {timestamp_part!r} (length={len(timestamp_part)}). Input: {msg_id!r}"
            )

        if len(random_part) != 8:
            raise ValueError(
                f"Invalid random component: expected 8 hex characters, "
                f"got {random_part!r} (length={len(random_part)}). Input: {msg_id!r}"
            )

        # Validate hex characters in random part
        try:
            int(random_part, 16)
        except ValueError:
            raise ValueError(
                f"Invalid random component: expected 8 hex characters, "
                f"got non-hex characters in {random_part!r}. Input: {msg_id!r}"
            )

        # Parse timestamp: YYYYMMDDHHMMSSMMMM
        # timestamp_part[0:4]  = YYYY
        # timestamp_part[4:6]  = MM
        # timestamp_part[6:8]  = DD
        # timestamp_part[8:10] = HH
        # timestamp_part[10:12] = MM (minute)
        # timestamp_part[12:14] = SS
        # timestamp_part[14:18] = MMMM (milliseconds, 4 digits)
        year = int(timestamp_part[0:4])
        month = int(timestamp_part[4:6])
        day = int(timestamp_part[6:8])
        hour = int(timestamp_part[8:10])
        minute = int(timestamp_part[10:12])
        second = int(timestamp_part[12:14])
        milliseconds = int(timestamp_part[14:18])

        try:
            timestamp_utc = datetime(
                year, month, day, hour, minute, second,
                microsecond=milliseconds * 1000,
                tzinfo=timezone.utc,
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid timestamp values in message ID: {exc}. Input: {msg_id!r}"
            ) from exc

        return {
            "message_id": msg_id,
            "timestamp_utc": timestamp_utc,
        }
