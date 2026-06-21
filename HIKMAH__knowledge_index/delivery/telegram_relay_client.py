"""
telegram_relay_client.py — Abstraction Layer for Hermes Telegram Relay Integration

PURPOSE
-------
Provides a clean abstraction over the battle-tested Hermes relay infrastructure
(NIZAM__system.relay.poller) for sending Telegram messages and polling for
user responses. Phase 17 never calls Telegram's API directly — all communication
flows through the Hermes relay.

WHY WRAPPER (NOT DIRECT TELEGRAM API CALLS)
--------------------------------------------
The Hermes relay (NIZAM__system.relay.poller) was purpose-built for NIZAM:

1. Token management: Hermes owns the bot token lifecycle; multiple modules
   should not independently manage the same token.

2. Conflict prevention: Telegram only allows ONE process to call getUpdates
   with a given bot token at a time. Hermes coordinates this via dedup.py
   and a polling loop. If Phase 17 called getUpdates directly AND Hermes
   was running, both would get a 409 Conflict (GatewayPollingConflict).

3. Error handling: Hermes has proven error handling (network timeouts,
   HTTP errors, 409 conflicts) in production. Reusing it avoids reinventing
   these edge cases.

4. Future extensibility: If Hermes adds a new feature (rate limiting, logging,
   message queuing), Phase 17 inherits it automatically via this wrapper.

5. No public endpoint required: Hermes relay uses long-polling (outbound),
   so no public HTTPS endpoint, domain, or TLS certificate is needed.

HERMES RELAY FUNCTIONS
-----------------------
This wrapper delegates to two functions from NIZAM__system.relay.poller:

tg_send_message(token, chat_id, text, parse_mode=None) -> dict
  - Sends a message to a Telegram chat
  - Returns the full Telegram API response dict on success
  - Response format: {"ok": True, "result": {"message_id": int, ...}}
  - Raises RuntimeError if the API returns ok=False

tg_get_updates(token, offset, timeout) -> list[dict]
  - Long-polls Telegram for new updates (messages, replies, etc.)
  - Returns list of update dicts (may be empty on timeout)
  - Raises GatewayPollingConflict if another process owns getUpdates
  - Raises RuntimeError on API errors

RESPONSE CORRELATION
--------------------
When a user replies to a specific Telegram message, Telegram includes a
"reply_to_message" field in the update. This is the mechanism Phase 17
uses to correlate user responses to previously sent messages:

Sent message → gets telegram_message_id (e.g., 12345)
User replies → update.message.reply_to_message.message_id == 12345

The check_reply_to_message_id() helper extracts this correlation field
from raw Telegram update dicts.

TOKEN MANAGEMENT
----------------
Token is read from:
1. Constructor parameter token= (explicit, takes priority)
2. TELEGRAM_BOT_TOKEN environment variable (production deployment)

ValueError is raised at construction time if neither is available.
This fail-fast behavior prevents runtime surprises when the bot token
is misconfigured.

USAGE EXAMPLES
--------------
>>> import os
>>> from HIKMAH__knowledge_index.delivery.telegram_relay_client import TelegramRelayClient

# Initialize with explicit token (testing/development)
>>> client = TelegramRelayClient(token="1234567890:AABBCCDDEEFFaabbccddeeff1234567890")

# Initialize from environment (production)
>>> os.environ["TELEGRAM_BOT_TOKEN"] = "1234567890:AABBCCDDEEFFaabbccddeeff1234567890"
>>> client = TelegramRelayClient()

# Send a message
>>> response = client.send_message(
...     chat_id=123456789,
...     text="Your AI work is waiting. Pick one task and start."
... )
>>> telegram_message_id = response["result"]["message_id"]
>>> print(f"Sent with Telegram ID: {telegram_message_id}")

# Poll for updates (called by response monitor in Wave 2)
>>> updates = client.get_updates(offset=0, timeout=25)
>>> for update in updates:
...     reply_to_id = client.check_reply_to_message_id(update)
...     if reply_to_id == telegram_message_id:
...         print(f"User replied to our message!")
...         print(f"Reply text: {update['message']['text']}")

# Check for reply correlation in a raw update
>>> update = {
...     "update_id": 1,
...     "message": {
...         "message_id": 99999,
...         "text": "OK, working on it",
...         "reply_to_message": {"message_id": 12345}
...     }
... }
>>> reply_id = client.check_reply_to_message_id(update)
>>> print(reply_id)  # 12345

EXCEPTIONS
----------
- ValueError: Raised at __init__ if no token available (explicit or environment)
- RuntimeError: Raised by send_message() if Telegram API returns ok=False
- GatewayPollingConflict: Raised by get_updates() if another process owns polling
  (imported from NIZAM__system.relay.poller)

DEPENDENCIES
------------
- os: Environment variable reading for token
- typing: Optional type annotations
- NIZAM__system.relay.poller: tg_send_message, tg_get_updates (Hermes relay)
"""
from __future__ import annotations

import os
from typing import List, Optional

from NIZAM__system.relay.poller import GatewayPollingConflict, tg_get_updates, tg_send_message


class TelegramRelayClient:
    """
    Abstraction layer for Hermes Telegram relay (send messages, poll updates).

    Wraps NIZAM__system.relay.poller functions with token management,
    clean method signatures, and response correlation helpers.

    Never calls Telegram API directly — all communication flows through
    the Hermes relay infrastructure (tg_send_message, tg_get_updates).

    Parameters
    ----------
    token : Optional[str]
        Telegram bot token. If not provided, read from TELEGRAM_BOT_TOKEN env var.

    Raises
    ------
    ValueError
        If no token provided and TELEGRAM_BOT_TOKEN environment variable not set.

    Examples
    --------
    >>> client = TelegramRelayClient(token="bot-token-here")
    >>> response = client.send_message(chat_id=123456789, text="Hello!")
    >>> telegram_msg_id = response["result"]["message_id"]
    """

    def __init__(self, token: Optional[str] = None) -> None:
        """
        Initialize the Telegram relay client.

        Parameters
        ----------
        token : Optional[str]
            Telegram bot token. Takes priority over environment variable.
            If None, reads from TELEGRAM_BOT_TOKEN environment variable.

        Raises
        ------
        ValueError
            If neither token parameter nor TELEGRAM_BOT_TOKEN env var is set.
        """
        if token is not None:
            self.token = token
        else:
            env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            if not env_token:
                raise ValueError(
                    "No Telegram bot token provided. Either pass token= parameter "
                    "or set the TELEGRAM_BOT_TOKEN environment variable."
                )
            self.token = env_token

    def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
    ) -> dict:
        """
        Send a text message to a Telegram chat via the Hermes relay.

        Delegates to tg_send_message() from NIZAM__system.relay.poller.
        The relay handles HTTP transport, error detection, and returns
        the full Telegram API response dict on success.

        Parameters
        ----------
        chat_id : int
            Telegram chat ID to send the message to.
        text : str
            Message text content (plain text or HTML/Markdown depending on parse_mode).
        parse_mode : Optional[str]
            Telegram parse mode: "HTML", "Markdown", or None for plain text.
            Defaults to None (plain text).

        Returns
        -------
        dict
            Full Telegram API response dict on success:
            {
                "ok": True,
                "result": {
                    "message_id": int,       # Telegram's message ID (use for response correlation)
                    "from": {...},           # Bot info
                    "chat": {...},           # Chat info
                    "date": int,             # Unix timestamp
                    "text": str              # Sent text
                }
            }

        Raises
        ------
        RuntimeError
            If Telegram API returns ok=False (message not sent).
            Propagated from tg_send_message() in relay.poller.

        Notes
        -----
        - The returned message_id (response["result"]["message_id"]) is the
          Telegram-assigned integer ID. Store this alongside message_id
          in DeliveryLedger for response correlation.
        - Phase 17 Wave 2 delivery orchestrator extracts message_id from this
          response after successful send.

        Examples
        --------
        >>> response = client.send_message(chat_id=123456789, text="Hello!")
        >>> telegram_id = response["result"]["message_id"]
        """
        return tg_send_message(self.token, chat_id, text, parse_mode=parse_mode)

    def get_updates(self, offset: int, timeout: int = 25) -> List[dict]:
        """
        Long-poll Telegram for new updates via the Hermes relay.

        Delegates to tg_get_updates() from NIZAM__system.relay.poller.
        Blocks for up to `timeout` seconds waiting for new messages.
        Returns immediately when updates arrive or timeout elapses.

        Parameters
        ----------
        offset : int
            Update ID offset — only updates with update_id >= offset are returned.
            Pass 0 for all pending updates; pass (last_seen_update_id + 1) to
            skip already-processed updates.
        timeout : int, optional
            Long-poll timeout in seconds. Default 25 (Telegram's recommended default).
            Set to 0 for non-blocking poll (returns immediately).

        Returns
        -------
        List[dict]
            List of Telegram update dicts. May be empty if no new updates
            within the timeout period. Each update contains:
            {
                "update_id": int,
                "message": {
                    "message_id": int,
                    "from": {...},
                    "chat": {...},
                    "date": int,
                    "text": str,
                    "reply_to_message": {...}  # Present only if user replied to a message
                }
            }

        Raises
        ------
        GatewayPollingConflict
            If another process (e.g., the Hermes gateway long-poll runner) is
            already calling getUpdates with the same bot token. Raised by
            tg_get_updates() in relay.poller. Phase 17 Wave 2 response monitor
            must handle this exception gracefully (wait and retry, or skip polling).
        RuntimeError
            If Telegram API returns an error response.

        Notes
        -----
        - GatewayPollingConflict is imported from NIZAM__system.relay.poller
          and re-raised to the caller. Phase 17 Wave 2 response_monitor.py
          should catch this and wait before retrying.
        - Use check_reply_to_message_id() on each update to find replies.

        Examples
        --------
        >>> updates = client.get_updates(offset=0, timeout=10)
        >>> for update in updates:
        ...     reply_id = client.check_reply_to_message_id(update)
        ...     if reply_id:
        ...         print(f"Reply to message {reply_id}")
        """
        return tg_get_updates(self.token, offset, timeout)

    def check_reply_to_message_id(self, update: dict) -> Optional[int]:
        """
        Extract the reply_to_message_id from a Telegram update dict.

        When a Telegram user replies to a specific message, the update contains
        a nested "reply_to_message" object with the original message_id. This
        helper extracts that ID for response correlation.

        Used by Phase 17 Wave 2 response monitor to match user replies to
        previously sent messages:
          sent telegram_message_id = 12345
          user replies → update has reply_to_message.message_id == 12345
          → matched! record response in DeliveryLedger

        Parameters
        ----------
        update : dict
            Raw Telegram update dict from get_updates().

        Returns
        -------
        Optional[int]
            The message_id of the message being replied to, or None if:
            - The update has no "message" field
            - The message has no "reply_to_message" field (not a reply)
            - The reply_to_message has no "message_id" field

        Examples
        --------
        >>> update = {
        ...     "update_id": 1,
        ...     "message": {
        ...         "message_id": 99999,
        ...         "text": "On it",
        ...         "reply_to_message": {"message_id": 12345}
        ...     }
        ... }
        >>> client.check_reply_to_message_id(update)
        12345

        >>> non_reply_update = {"update_id": 2, "message": {"message_id": 1, "text": "hello"}}
        >>> client.check_reply_to_message_id(non_reply_update) is None
        True
        """
        return (
            update.get("message", {})
            .get("reply_to_message", {})
            .get("message_id")
        )
