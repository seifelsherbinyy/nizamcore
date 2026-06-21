"""
response_monitor.py — Background Engagement Window Monitor for Phase 17

PURPOSE
-------
Monitors the 1-hour engagement window after each message delivery. For every
successfully delivered message, DeliveryOrchestrator spawns a ResponseMonitor
daemon thread that polls the Hermes Telegram relay for user replies within
3600 seconds of delivery.

BACKGROUND MONITORING DESIGN
------------------------------
ResponseMonitor uses Python daemon threads for background polling:

    Why daemon threads?
    - Daemon threads exit automatically when the main process exits.
    - No zombie threads: If the scheduler process is restarted or killed,
      monitor threads die with it (no orphaned polling loops).
    - Non-blocking: Spawning a monitor thread does not block the caller.
      deliver() returns immediately; monitoring happens in the background.

    Thread lifecycle:
    1. monitor() is called after successful delivery
    2. daemon thread spawned, calls _monitor_loop()
    3. _monitor_loop() polls relay every POLL_INTERVAL_SECONDS (30s)
    4a. If reply found: log_response() → thread exits (response captured)
    4b. If deadline exceeded: log_no_response() → thread exits (window closed)
    4c. If error: log warning, sleep, retry (thread never propagates exceptions)

POLLING STRATEGY
----------------
Poll interval: POLL_INTERVAL_SECONDS = 30 seconds

This balance between:
- Latency: 30s max delay between user reply and log entry (acceptable for analytics)
- Resource usage: 2 polls/minute per active monitor (~1 at any time in NIZAM's
  typical load: 11 personas × 2 sends/day = 22 messages/day, 1-hour windows,
  never more than ~1 active monitor at any given time)
- Hermes relay load: Minimal (relay designed for long-polling, 30s timeout)

RESPONSE CORRELATION
--------------------
Telegram's native reply feature: When a user taps "Reply" to a specific message,
Telegram includes a "reply_to_message" field in the update containing the original
message's message_id (integer). This is a first-class Telegram API field (not
a custom convention) and is how NIZAM correlates responses.

Matching logic:
    for update in updates:
        reply_to_id = relay_client.check_reply_to_message_id(update)
        if reply_to_id == telegram_message_id:  # exact integer match
            # User explicitly replied to our message!

This prevents false positives (unrelated messages, new conversations, etc.).
Only explicit Telegram replies trigger response logging.

OFFSET TRACKING
---------------
_global_offset is a shared integer tracking the highest Telegram update_id seen
across all monitor threads. Updates are deduplicated by passing offset+1 to each
get_updates() call, so no update is processed twice.

Shared-state note: _global_offset is read/written from multiple daemon threads.
A threading.Lock is used to prevent race conditions on offset updates. The window
for a race is small (between reading offset and updating it), but correctness
matters for audit trail deduplication.

ERROR HANDLING
--------------
_monitor_loop() catches all exceptions:

1. GatewayPollingConflict (from NIZAM__system.relay.poller):
   Raised when another process (usually Hermes gateway) owns getUpdates.
   Response: Log warning, sleep POLLING_CONFLICT_BACKOFF_SECONDS (60s), retry.
   Rationale: Polling conflict is temporary — Hermes polling windows are typically
   short (25s). After 60s backoff, the conflict is usually resolved.

2. RuntimeError (from tg_get_updates):
   Telegram API returned an error response.
   Response: Log warning, sleep POLL_INTERVAL_SECONDS, retry.

3. Any other Exception (network timeout, connection reset, etc.):
   Response: Log warning, sleep POLL_INTERVAL_SECONDS, retry.

No exception propagates out of _monitor_loop(). Thread NEVER crashes silently —
it either finds a response, reaches the deadline, or hits an error and retries.

ENGAGEMENT WINDOW ENFORCEMENT
------------------------------
Deadline calculation:
    sent_dt = datetime.fromisoformat(sent_at)  # UTC
    deadline = sent_dt + timedelta(seconds=window_seconds)

Poll loop runs while datetime.now(timezone.utc) < deadline.

After deadline:
    ledger.log_no_response(message_id, telegram_message_id, persona)
    del self._monitors[message_id]  # clean up tracking dict

The no_response event enables Phase 18 adaptation:
    response_rate = responses / (responses + no_responses)
    if response_rate < 0.80: trigger format rotation

CONCURRENCY MODEL
-----------------
Multiple monitors may run concurrently (e.g., morning and evening deliveries
both active). The shared _global_offset is protected by _offset_lock:

    with self._offset_lock:
        # read current offset
        # update offset after processing updates

The _monitors dict is accessed from both the main thread (monitor()) and
daemon threads (_monitor_loop()). Dictionary operations (insert/delete) are
GIL-protected in CPython, but for clarity and correctness we rely on the fact
that monitor() only adds entries and _monitor_loop() only deletes its own entry.

USAGE EXAMPLE
--------------
>>> from pathlib import Path
>>> from HIKMAH__knowledge_index.delivery import ResponseMonitor

>>> monitor = ResponseMonitor(
...     telegram_token="bot-token-here",
...     ledger_path=Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"),
... )

>>> # Called by DeliveryOrchestrator after successful delivery
>>> monitor.monitor(
...     message_id="MSG-20260621093045123-A7F2E8CD",
...     telegram_message_id=12345,
...     persona="AMMAR",
...     sent_at="2026-06-21T09:30:45Z",
...     window_seconds=3600,  # 1 hour
... )
>>> # Monitor thread is now running in background
>>> # After 1 hour without reply, logs engagement_window_closed

>>> # To test with short window:
>>> monitor.monitor(
...     message_id="MSG-20260621093045123-B9C0D1E2",
...     telegram_message_id=12346,
...     persona="HIKMAH",
...     sent_at="2026-06-21T09:30:45Z",
...     window_seconds=5,  # 5 seconds for testing
... )

DEPENDENCIES
------------
- datetime: deadline calculation and UTC timestamps
- time: sleep between poll intervals
- threading: daemon thread management and offset lock
- pathlib: ledger path handling
- typing: Optional type annotations
- .delivery_ledger: DeliveryLedger (log response, log no-response)
- .telegram_relay_client: TelegramRelayClient (get_updates, check_reply_to)
- NIZAM__system.relay.poller: GatewayPollingConflict exception type
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from .delivery_ledger import DeliveryLedger
from .telegram_relay_client import TelegramRelayClient
from NIZAM__system.relay.poller import GatewayPollingConflict

# ============================================================================
# Module-level constants
# ============================================================================

POLL_INTERVAL_SECONDS: int = 30
"""Seconds between get_updates() calls during engagement window polling."""

POLLING_CONFLICT_BACKOFF_SECONDS: int = 60
"""Seconds to wait when GatewayPollingConflict is raised (another poller owns channel)."""

logger = logging.getLogger(__name__)


class ResponseMonitor:
    """
    Polls Hermes Telegram relay for user responses within a 1-hour engagement window.

    For each delivered message, spawns a daemon thread that polls get_updates()
    every 30 seconds. If a reply matching the telegram_message_id is found,
    logs the response and exits. If 1 hour passes without a reply, logs
    engagement_window_closed and exits.

    Parameters
    ----------
    telegram_token : str
        Telegram bot token. Passed to TelegramRelayClient.
    ledger_path : Path
        Path to the JSONL delivery ledger file.
    relay_client : Optional[TelegramRelayClient], optional
        Pre-configured relay client (for testing/injection). If None,
        a new TelegramRelayClient is initialized with telegram_token.
    default_window_seconds : int, optional
        Default engagement window duration in seconds. Default 3600 (1 hour).
        Can be overridden per-message in monitor().

    Attributes
    ----------
    _monitors : Dict[str, threading.Thread]
        Mapping of message_id → active monitor thread.
        Threads remove themselves on completion.
    _global_offset : int
        Shared Telegram update offset. Incremented to avoid replaying updates.
    _offset_lock : threading.Lock
        Protects _global_offset from concurrent writes by multiple threads.

    Examples
    --------
    >>> monitor = ResponseMonitor("bot-token", Path("DELIVERY_LEDGER.jsonl"))
    >>> monitor.monitor("MSG-...", 12345, "AMMAR", "2026-06-21T09:00:00Z")
    # Thread running in background
    """

    def __init__(
        self,
        telegram_token: str,
        ledger_path: Path,
        relay_client: Optional[TelegramRelayClient] = None,
        default_window_seconds: int = 3600,
    ) -> None:
        """
        Initialize the response monitor.

        Parameters
        ----------
        telegram_token : str
            Telegram bot token for relay client initialization.
        ledger_path : Path
            Path to JSONL ledger file.
        relay_client : Optional[TelegramRelayClient], optional
            Injected relay client (for testing). If None, creates a new one.
        default_window_seconds : int, optional
            Default engagement window in seconds. Default 3600 (1 hour).
        """
        self._token = telegram_token
        self._ledger_path = Path(ledger_path)
        self._default_window_seconds = default_window_seconds

        # Initialize Wave 1 infrastructure
        self._ledger = DeliveryLedger(self._ledger_path)
        self._relay_client = relay_client or TelegramRelayClient(token=telegram_token)

        # Thread tracking
        self._monitors: Dict[str, threading.Thread] = {}

        # Shared offset for deduplication across all monitor threads
        self._global_offset: int = 0
        self._offset_lock = threading.Lock()

    def monitor(
        self,
        message_id: str,
        telegram_message_id: int,
        persona: str,
        sent_at: str,
        window_seconds: Optional[int] = None,
    ) -> None:
        """
        Spawn a daemon thread to monitor for responses within the engagement window.

        Non-blocking: returns immediately after spawning the thread.
        The background thread handles polling, response correlation, and logging.

        Parameters
        ----------
        message_id : str
            Our unique NIZAM message ID (MSG-{YYYYMMDDHHMMSSMMMM}-{8-HEX}).
        telegram_message_id : int
            Telegram's integer message_id (from sendMessage response).
            Used for reply_to_message_id correlation.
        persona : str
            Persona name (AMMAR, HIKMAH, TARIQ, etc.).
        sent_at : str
            ISO 8601 UTC timestamp when the message was sent.
            Used to calculate the engagement window deadline.
        window_seconds : Optional[int], optional
            Engagement window duration in seconds. Defaults to default_window_seconds
            (3600 by default). Pass a shorter value for testing (e.g., 5 seconds).

        Notes
        -----
        - Thread is daemon=True (exits when main process exits, no zombies)
        - Thread name includes message_id for debugging
        - Thread stored in _monitors dict for lifecycle tracking
        """
        effective_window = window_seconds if window_seconds is not None else self._default_window_seconds

        # Calculate deadline from sent_at + window_seconds
        sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
        deadline = sent_dt + timedelta(seconds=effective_window)

        # Spawn daemon thread for background monitoring
        thread = threading.Thread(
            target=self._monitor_loop,
            args=(message_id, telegram_message_id, persona, sent_at, deadline),
            daemon=True,
            name=f"ResponseMonitor-{message_id}",
        )

        self._monitors[message_id] = thread
        thread.start()

        logger.debug(
            "ResponseMonitor spawned for message_id=%s (telegram_id=%d, window=%ds, deadline=%s)",
            message_id,
            telegram_message_id,
            effective_window,
            deadline.isoformat(),
        )

    def _monitor_loop(
        self,
        message_id: str,
        telegram_message_id: int,
        persona: str,
        sent_at: str,
        deadline: datetime,
    ) -> None:
        """
        Background polling loop for response detection within engagement window.

        Runs in a daemon thread. Polls Hermes relay every POLL_INTERVAL_SECONDS
        for updates matching telegram_message_id via reply_to_message_id.

        On response found:
            - Log to DeliveryLedger with latency_seconds
            - Exit loop (thread terminates)

        On deadline exceeded:
            - Log engagement_window_closed to DeliveryLedger
            - Exit loop (thread terminates)

        On GatewayPollingConflict:
            - Log warning
            - Sleep POLLING_CONFLICT_BACKOFF_SECONDS (60s)
            - Retry

        On other exceptions:
            - Log warning
            - Sleep POLL_INTERVAL_SECONDS
            - Retry

        Parameters
        ----------
        message_id : str
            Our unique NIZAM message ID.
        telegram_message_id : int
            Telegram's integer message_id for reply correlation.
        persona : str
            Persona name for ledger entries.
        sent_at : str
            ISO 8601 UTC timestamp (for latency calculation).
        deadline : datetime
            UTC datetime when the engagement window closes.
        """
        sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))

        logger.debug(
            "_monitor_loop started: message_id=%s, telegram_id=%d, deadline=%s",
            message_id,
            telegram_message_id,
            deadline.isoformat(),
        )

        while datetime.now(timezone.utc) < deadline:
            try:
                # Read current offset (thread-safe)
                with self._offset_lock:
                    current_offset = self._global_offset

                # Poll relay for updates
                updates = self._relay_client.get_updates(
                    offset=current_offset,
                    timeout=25,
                )

                # Process updates: look for reply matching our telegram_message_id
                max_update_id = current_offset
                for update in updates:
                    update_id = update.get("update_id", 0)
                    if update_id >= max_update_id:
                        max_update_id = update_id

                    reply_to_id = self._relay_client.check_reply_to_message_id(update)
                    if reply_to_id == telegram_message_id:
                        # User explicitly replied to our message!
                        response_text = update.get("message", {}).get("text", "")
                        response_time = datetime.now(timezone.utc).isoformat()
                        response_dt = datetime.now(timezone.utc)
                        engagement_latency = (response_dt - sent_dt.replace(tzinfo=timezone.utc) if sent_dt.tzinfo is None else response_dt - sent_dt).total_seconds()

                        self._ledger.log_response(
                            message_id=message_id,
                            telegram_message_id=telegram_message_id,
                            response_text=response_text,
                            response_time=response_time,
                            engagement_latency_seconds=engagement_latency,
                            persona=persona,
                        )

                        logger.info(
                            "Response received: message_id=%s, latency=%.1fs",
                            message_id,
                            engagement_latency,
                        )

                        # Update offset to skip this update on next poll
                        with self._offset_lock:
                            if max_update_id >= self._global_offset:
                                self._global_offset = max_update_id + 1

                        # Clean up tracking and exit
                        self._monitors.pop(message_id, None)
                        return  # Response found — exit monitor loop

                # Update global offset to prevent replaying processed updates
                with self._offset_lock:
                    if max_update_id >= self._global_offset:
                        self._global_offset = max_update_id + 1

            except GatewayPollingConflict:
                logger.warning(
                    "GatewayPollingConflict for message_id=%s: another process owns polling. "
                    "Backing off %ds before retry.",
                    message_id,
                    POLLING_CONFLICT_BACKOFF_SECONDS,
                )
                time.sleep(POLLING_CONFLICT_BACKOFF_SECONDS)
                continue  # Skip the normal sleep; we already slept in backoff

            except Exception as exc:  # noqa: BLE001 — monitor threads must never crash
                logger.warning(
                    "Error in ResponseMonitor for message_id=%s: %s. "
                    "Retrying in %ds.",
                    message_id,
                    exc,
                    POLL_INTERVAL_SECONDS,
                )

            # Sleep between polls (only when no conflict — conflict path already slept)
            time.sleep(POLL_INTERVAL_SECONDS)

        # Deadline exceeded — engagement window closed without a response
        logger.info(
            "Engagement window closed (no response): message_id=%s, persona=%s",
            message_id,
            persona,
        )

        self._ledger.log_no_response(
            message_id=message_id,
            telegram_message_id=telegram_message_id,
            persona=persona,
        )

        # Clean up tracking dict
        self._monitors.pop(message_id, None)
