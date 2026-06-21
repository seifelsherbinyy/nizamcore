"""
delivery_orchestrator.py — Delivery Lifecycle Orchestration for Phase 17

PURPOSE
-------
Orchestrates the complete message delivery lifecycle for the NIZAM twice-daily
Telegram nudge system. DeliveryOrchestrator coordinates four interdependent
steps that must run in strict order:

    1. Generate a unique message_id (before any relay call — crash safety)
    2. Log a pre-send "pending" entry to the DeliveryLedger (crash-safe record)
    3. Send the message via TelegramRelayClient (Hermes relay abstraction)
    4a. On success: update ledger with delivered_at and telegram_message_id
    4b. On failure: update ledger with status="failure" and error_reason
    5. Spawn ResponseMonitor background thread (if configured) for 1-hour polling

DELIVERY LIFECYCLE
------------------
The delivery lifecycle is designed around crash safety and audit completeness.
Every step has a clear failure mode:

    Step 1 (ID generation): Pure Python, infallible. No external calls.
    Step 2 (Pre-send log):  Writes one JSONL line. If disk is full, caller sees
                            OSError and no relay call is made (safe failure).
    Step 3 (Relay send):    Network call. May fail with RuntimeError, timeout,
                            network error. Any exception is caught and logged.
    Step 4 (Post-send log): Updates ledger with final status. Always executes
                            (whether step 3 succeeded or failed).
    Step 5 (Monitor spawn): Non-blocking daemon thread. Only spawned after
                            successful delivery (step 3 succeeded).

WHY PRE-SEND LOGGING
--------------------
The message_id is generated and logged BEFORE the relay send. This design choice
prevents the "lost message" failure mode:

Without pre-send logging:
    1. Generate message_id
    2. Send via relay → SUCCESS
    3. Process crashes before logging → message_id is LOST
    4. Operator has no record that this message_id was sent
    5. Cannot correlate any user responses

With pre-send logging (this implementation):
    1. Generate message_id
    2. Log message_id with status="pending" → DURABLE
    3. Send via relay → SUCCESS
    4. Update ledger with status="success" and delivered_at
    5. If crash occurs between steps 2 and 4, operator sees status="pending"
       and can investigate manually (message may or may not have been sent)

The "pending" status in the ledger serves as an explicit "unknown state" marker,
enabling operator awareness of messages that may have been delivered but not
confirmed. This is a best-effort audit trail (not two-phase commit), appropriate
for NIZAM's twice-daily delivery volume.

PHASE 16 INTEGRATION
--------------------
Phase 16 (Message Generation) produces (message_text, success, reason) from
generate_and_dedupe(). DeliveryOrchestrator receives message_text and wraps
it with delivery metadata:

    # Phase 16: Generate
    message_text, ok, reason = generate_and_dedupe(
        persona="AMMAR", intent="open_work", index=index, ...
    )

    # Phase 17: Deliver (this class)
    result = orchestrator.deliver(
        persona="AMMAR",
        message_text=message_text,
        intent="open_work",
        chat_id=AMMAR_CHAT_ID,
        context_tags=["technical"],
    )

RESPONSE MONITOR INTEGRATION
------------------------------
After successful delivery, the orchestrator spawns a ResponseMonitor daemon
thread to poll for user replies within the 1-hour engagement window:

    result = orchestrator.deliver(...)
    # ResponseMonitor is now polling in background for reply_to_message_id == result.telegram_message_id
    # After 1 hour without reply → logs engagement_window_closed event
    # On reply → logs response event with engagement_latency_seconds

ResponseMonitor can be injected at construction time (default) or set later:
    orchestrator = DeliveryOrchestrator(token, ledger_path)
    orchestrator.response_monitor = ResponseMonitor(token, ledger_path)

ERROR HANDLING
--------------
All exceptions from TelegramRelayClient.send_message() are caught and handled:
- RuntimeError: Telegram API returned ok=False (relay propagates this)
- ConnectionError: Network unreachable
- TimeoutError: Relay timeout
- Exception: Any other unexpected error

On exception:
    - delivered_at = None
    - status = "failure"
    - error_reason = str(exc)
    - Ledger is updated with failure entry
    - DeliveryResult.status = "failure" is returned (no exception raised to caller)
    - ResponseMonitor is NOT spawned (nothing to monitor for failed delivery)

The caller (scheduler, cron job) decides how to handle failure results.
Common patterns: retry after delay, alert operator, skip to next persona.

PHASE 18 DOWNSTREAM INTEGRATION
---------------------------------
DeliveryLedger entries written by this orchestrator are the primary data source
for Phase 18 (Adaptation & Format Evolution). Phase 18 queries:

    deliveries = ledger.get_deliveries_for_persona("AMMAR", limit=14)
    responses = [ledger.get_responses_for_message(d["message_id"]) for d in deliveries]
    response_rate = len([r for r in responses if r]) / len(deliveries)
    if response_rate < 0.80:
        # trigger format rotation

USAGE EXAMPLE
--------------
>>> from pathlib import Path
>>> from HIKMAH__knowledge_index.delivery import DeliveryOrchestrator, ResponseMonitor
>>> import os

>>> # Initialize orchestrator and monitor
>>> ledger_path = Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl")
>>> orchestrator = DeliveryOrchestrator(
...     telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
...     ledger_path=ledger_path,
... )
>>> monitor = ResponseMonitor(
...     telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
...     ledger_path=ledger_path,
... )
>>> orchestrator.response_monitor = monitor

>>> # Deliver a message (Phase 16 output → Phase 17 delivery)
>>> result = orchestrator.deliver(
...     persona="AMMAR",
...     message_text="Your AI work is stalled. Pick one task and move forward.",
...     intent="open_work",
...     chat_id=int(os.environ["AMMAR_CHAT_ID"]),
...     context_tags=["technical"],
... )

>>> if result.status == "success":
...     print(f"Sent: {result.message_id} → Telegram {result.telegram_message_id}")
...     # ResponseMonitor running in background for 1 hour
... else:
...     print(f"Failed: {result.error}")

DEPENDENCIES
------------
- dataclasses: DeliveryResult dataclass definition
- datetime: UTC timestamp generation for sent_at and delivered_at
- pathlib: ledger_path handling
- typing: Literal, Optional type annotations
- .message_id_generator: MessageIDGenerator (unique ID per send)
- .delivery_ledger: DeliveryLedger (JSONL audit trail)
- .telegram_relay_client: TelegramRelayClient (Hermes relay abstraction)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from .delivery_ledger import DeliveryLedger
from .message_id_generator import MessageIDGenerator
from .telegram_relay_client import TelegramRelayClient

if TYPE_CHECKING:
    from .response_monitor import ResponseMonitor


@dataclass
class DeliveryResult:
    """
    Result of a message delivery attempt via DeliveryOrchestrator.

    Contains all metadata needed to correlate the delivery in the ledger,
    track the Telegram message for response monitoring, and report to the
    caller whether delivery succeeded or failed.

    Attributes
    ----------
    message_id : str
        Our unique NIZAM message ID (MSG-{YYYYMMDDHHMMSSMMMM}-{8-HEX}).
        Generated by MessageIDGenerator.generate() before relay call.
        Always present (generated even on failure).
    telegram_message_id : Optional[int]
        Telegram's integer message_id from sendMessage response.
        Present only on successful delivery (status="success").
        None on failure (relay call failed or API returned ok=False).
    sent_at : str
        ISO 8601 UTC timestamp when delivery was initiated.
        Recorded before the relay call (even if relay fails).
    delivered_at : Optional[str]
        ISO 8601 UTC timestamp when Telegram confirmed delivery.
        Present only on successful delivery. None on failure.
    status : Literal["success", "failure"]
        Delivery outcome. "success" means Telegram API accepted the message.
        "failure" means the relay call threw an exception.
    error : Optional[str]
        Human-readable error description if status="failure".
        None on success.

    Examples
    --------
    Successful delivery:
        DeliveryResult(
            message_id="MSG-20260621093045123-A7F2E8CD",
            telegram_message_id=12345,
            sent_at="2026-06-21T09:30:45.000Z",
            delivered_at="2026-06-21T09:30:45.500Z",
            status="success",
            error=None
        )

    Failed delivery:
        DeliveryResult(
            message_id="MSG-20260621093045123-B8C9D0E1",
            telegram_message_id=None,
            sent_at="2026-06-21T09:30:45.000Z",
            delivered_at=None,
            status="failure",
            error="Telegram API returned ok=False: chat not found"
        )
    """

    message_id: str
    telegram_message_id: Optional[int]
    sent_at: str
    delivered_at: Optional[str]
    status: Literal["success", "failure"]
    error: Optional[str]


class DeliveryOrchestrator:
    """
    Orchestrates the complete NIZAM message delivery lifecycle.

    Coordinates message ID generation, fail-safe ledger logging,
    Telegram relay sending, and response monitor spawning in a single
    atomic workflow.

    Parameters
    ----------
    telegram_token : str
        Telegram bot token passed to TelegramRelayClient.
    ledger_path : Path
        Path to the JSONL delivery ledger file.
        Created on first write if it does not exist.
    monitor_window_seconds : int, optional
        Duration of the engagement window in seconds.
        Default 3600 (1 hour). Passed to ResponseMonitor.monitor().
    response_monitor : Optional[ResponseMonitor], optional
        Pre-configured ResponseMonitor instance. Can be None for testing
        or set after construction via orchestrator.response_monitor = ...

    Attributes
    ----------
    response_monitor : Optional[ResponseMonitor]
        ResponseMonitor instance. If set, spawned after each successful
        delivery. If None, response monitoring is disabled.
    last_offset : int
        Last Telegram update offset seen (for polling; updated by monitor).

    Examples
    --------
    >>> orchestrator = DeliveryOrchestrator(
    ...     telegram_token="bot-token",
    ...     ledger_path=Path("DELIVERY_LEDGER.jsonl"),
    ... )
    >>> result = orchestrator.deliver(
    ...     persona="AMMAR",
    ...     message_text="Take action now.",
    ...     intent="open_work",
    ...     chat_id=12345,
    ...     context_tags=["technical"],
    ... )
    """

    def __init__(
        self,
        telegram_token: str,
        ledger_path: Path,
        monitor_window_seconds: int = 3600,
        response_monitor: Optional["ResponseMonitor"] = None,
    ) -> None:
        """
        Initialize the delivery orchestrator with relay and ledger.

        Parameters
        ----------
        telegram_token : str
            Telegram bot token for TelegramRelayClient.
        ledger_path : Path
            Path to the JSONL delivery ledger file.
        monitor_window_seconds : int, optional
            Engagement window duration in seconds. Default 3600 (1 hour).
        response_monitor : Optional[ResponseMonitor], optional
            Pre-configured response monitor. Set to None to disable monitoring.
        """
        self._token = telegram_token
        self._ledger_path = Path(ledger_path)
        self._monitor_window_seconds = monitor_window_seconds
        self.response_monitor = response_monitor

        # Initialize Wave 1 infrastructure
        self._ledger = DeliveryLedger(self._ledger_path)
        self._relay_client = TelegramRelayClient(token=telegram_token)

        # Polling offset (updated by monitor as updates are consumed)
        self.last_offset: int = 0

    def deliver(
        self,
        persona: str,
        message_text: str,
        intent: str,
        chat_id: int,
        context_tags: list,
    ) -> DeliveryResult:
        """
        Execute the complete message delivery lifecycle.

        Orchestrates five steps in strict sequence:
            1. Generate unique message_id (pre-relay, crash safe)
            2. Log pending entry to ledger (durable before relay call)
            3. Send via TelegramRelayClient (Hermes relay)
            4a. Success: update ledger with delivered_at + telegram_message_id
            4b. Failure: update ledger with error_reason, status="failure"
            5. Spawn ResponseMonitor thread (success only)

        All relay exceptions are caught. Caller receives DeliveryResult
        regardless of outcome — no exceptions propagated.

        Parameters
        ----------
        persona : str
            Persona name (AMMAR, HIKMAH, TARIQ, etc.).
        message_text : str
            Full text of the message to send (from Phase 16 generator).
        intent : str
            Intent string that prompted this message (e.g., "open_work").
        chat_id : int
            Telegram chat ID for the persona's private chat.
        context_tags : list
            List of context category tags. Validated against whitelist by
            DeliveryLedger (technical, health, financial, strategic, personal).

        Returns
        -------
        DeliveryResult
            Contains message_id, telegram_message_id (or None on failure),
            sent_at, delivered_at (or None on failure), status, error.

        Raises
        ------
        ValueError
            If context_tags contains invalid tags (from DeliveryLedger privacy gate).
            This is NOT caught — invalid context_tags are a caller error.
        OSError
            If ledger file cannot be written (from DeliveryLedger).
            This is NOT caught — disk write failures need operator attention.

        Notes
        -----
        - message_id is assigned before relay call (crash safety)
        - Pre-send "pending" entry uses status="pending" (interim state)
        - Post-send entry overwrites with status="success" or "failure"
        - ResponseMonitor is only spawned on status="success"
        - context_tags ValueError is propagated (not a runtime error; fix the code)
        """
        # Step 1: Generate unique message_id and record sent_at
        msg_id = MessageIDGenerator.generate()
        sent_at = datetime.now(timezone.utc).isoformat()

        # Step 2: Log pre-send pending entry (crash-safe: message_id recorded before relay)
        self._ledger.log_delivery(
            message_id=msg_id,
            telegram_message_id=None,
            persona=persona,
            message_text=message_text,
            intent=intent,
            sent_at=sent_at,
            delivered_at=None,
            context_tags=context_tags,
            status="pending",
        )

        # Step 3: Send via relay — catch ALL exceptions to ensure ledger consistency
        try:
            response = self._relay_client.send_message(chat_id, message_text)
            tg_message_id = response.get("result", {}).get("message_id")
            delivered_at = datetime.now(timezone.utc).isoformat()

            # Step 4a: Log success entry with telegram_message_id and delivered_at
            self._ledger.log_delivery(
                message_id=msg_id,
                telegram_message_id=tg_message_id,
                persona=persona,
                message_text=message_text,
                intent=intent,
                sent_at=sent_at,
                delivered_at=delivered_at,
                context_tags=context_tags,
                status="success",
            )

            # Step 5: Spawn ResponseMonitor if configured
            if self.response_monitor is not None:
                self.response_monitor.monitor(
                    message_id=msg_id,
                    telegram_message_id=tg_message_id,
                    persona=persona,
                    sent_at=sent_at,
                    window_seconds=self._monitor_window_seconds,
                )

            # Step 6: Return success result
            return DeliveryResult(
                message_id=msg_id,
                telegram_message_id=tg_message_id,
                sent_at=sent_at,
                delivered_at=delivered_at,
                status="success",
                error=None,
            )

        except Exception as exc:  # noqa: BLE001 — intentional catch-all for relay errors
            # Step 4b: Log failure entry with error reason
            error_msg = str(exc)
            self._ledger.log_delivery(
                message_id=msg_id,
                telegram_message_id=None,
                persona=persona,
                message_text=message_text,
                intent=intent,
                sent_at=sent_at,
                delivered_at=None,
                context_tags=context_tags,
                status="failure",
                error_reason=error_msg,
            )

            # Return failure result — do NOT raise (caller decides how to handle failures)
            return DeliveryResult(
                message_id=msg_id,
                telegram_message_id=None,
                sent_at=sent_at,
                delivered_at=None,
                status="failure",
                error=error_msg,
            )
