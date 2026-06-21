"""
HIKMAH Knowledge Index — Delivery Module (Phase 17: Delivery & Response Tracking)

PURPOSE
-------
Provides the public API for Phase 17 message delivery infrastructure. This module
enables twice-daily Telegram message delivery with:
- Unique message ID generation (sortable, collision-resistant)
- Immutable delivery audit trail (JSONL ledger with privacy gates)
- Hermes relay integration (send messages, poll for responses)

Phase 17 is the fourth phase of the NIZAM v1.1 milestone, consuming Phase 16
message generation output and producing delivery metadata for Phase 18 adaptation.

PHASE 17 OVERVIEW: DELIVERY & RESPONSE TRACKING
------------------------------------------------
The NIZAM system delivers twice-daily messages (09:00 & 18:00 Cairo via Hermes
cron) to each persona's Telegram chat. Phase 17 provides:

Wave 1 (This module — Foundation Infrastructure):
  - MessageIDGenerator: Unique, sortable ID for each send attempt
  - DeliveryLedger: JSONL audit trail for delivery, response, and window events
  - TelegramRelayClient: Abstraction layer for Hermes relay (send + poll)

Wave 2 (Delivery Orchestrator & Response Monitor — Phase 17-02):
  - DeliveryOrchestrator: Coordinates ID generation → relay send → ledger logging
  - ResponseMonitor: Polls relay for replies, correlates via reply_to_message_id,
    closes engagement window after 1 hour

ARCHITECTURE
-----------
Message delivery follows this flow:

┌─────────────────────────────────────────────────────────┐
│                     Phase 17 Wave 1                     │
│                                                         │
│  MessageIDGenerator          TelegramRelayClient        │
│     .generate()  ──────────→  .send_message()          │
│         │                          │                   │
│         │           DeliveryLedger │                   │
│         └──────────→ .log_delivery()◄───────────────── │
│                                                         │
│  (Wave 2) DeliveryOrchestrator coordinates all above   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     Phase 17 Wave 2                     │
│                                                         │
│  TelegramRelayClient         DeliveryLedger             │
│     .get_updates() ──────────→ .log_response()         │
│     .check_reply_to_message_id()  or                   │
│                    ──────────→ .log_no_response()      │
│                                                         │
│  (Wave 2) ResponseMonitor coordinates all above        │
└─────────────────────────────────────────────────────────┘

CORE COMPONENTS (Wave 1 — This Package)
----------------------------------------
1. MessageIDGenerator (message_id_generator.py)
   Generates globally unique, sortable message IDs:
   Format: MSG-{YYYYMMDDHHMMSSMMMM}-{8-CHAR-HEX}
   Example: "MSG-20260621093045123-A7F2E8CD"
   Methods: generate() → str, parse(msg_id) → dict

2. DeliveryLedger (delivery_ledger.py)
   JSONL append-only ledger for delivery lifecycle events:
   Events: "delivery", "response", "engagement_window_closed"
   Privacy: context_tags validated against whitelist (fail-safe gate)
   Methods: log_delivery(), log_response(), log_no_response(),
            get_deliveries_for_persona(), get_responses_for_message()

3. TelegramRelayClient (telegram_relay_client.py)
   Abstraction over Hermes relay (NIZAM__system.relay.poller):
   Never calls Telegram API directly — uses battle-tested relay
   Methods: send_message(), get_updates(), check_reply_to_message_id()

PUBLIC API
----------
All three core classes are exported from this module:

    from HIKMAH__knowledge_index.delivery import (
        MessageIDGenerator,
        DeliveryLedger,
        TelegramRelayClient,
    )

Or via the parent module (Phase 17 exports added to HIKMAH__knowledge_index):

    from HIKMAH__knowledge_index import (
        MessageIDGenerator,
        DeliveryLedger,
        TelegramRelayClient,
    )

USAGE EXAMPLE: BASIC DELIVERY FLOW
------------------------------------
>>> from HIKMAH__knowledge_index.delivery import (
...     MessageIDGenerator, DeliveryLedger, TelegramRelayClient
... )
>>> from pathlib import Path
>>> import os
>>>
>>> # Initialize components
>>> ledger = DeliveryLedger(Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"))
>>> relay = TelegramRelayClient()  # reads TELEGRAM_BOT_TOKEN from env
>>>
>>> # Step 1: Generate unique message ID before send
>>> msg_id = MessageIDGenerator.generate()
>>> print(f"Message ID: {msg_id}")
'MSG-20260621093045123-A7F2E8CD'
>>>
>>> # Step 2: Send message via Hermes relay
>>> response = relay.send_message(
...     chat_id=int(os.environ["AMMAR_CHAT_ID"]),
...     text="Your AI work is stalled. Pick one task and move forward."
... )
>>> telegram_msg_id = response["result"]["message_id"]
>>> print(f"Telegram ID: {telegram_msg_id}")
12345
>>>
>>> # Step 3: Log delivery to ledger
>>> ledger.log_delivery(
...     message_id=msg_id,
...     telegram_message_id=telegram_msg_id,
...     persona="AMMAR",
...     message_text="Your AI work is stalled. Pick one task and move forward.",
...     intent="open_work",
...     sent_at="2026-06-21T09:30:45Z",
...     delivered_at="2026-06-21T09:30:46Z",
...     context_tags=["technical"],
...     status="success"
... )
>>>
>>> print(f"Delivery logged: {msg_id} → Telegram {telegram_msg_id}")

USAGE EXAMPLE: RESPONSE POLLING (WAVE 2 PREVIEW)
-------------------------------------------------
>>> # Wave 2 ResponseMonitor polls for replies within 1-hour window
>>> updates = relay.get_updates(offset=last_update_id + 1, timeout=25)
>>> for update in updates:
...     reply_to_id = relay.check_reply_to_message_id(update)
...     if reply_to_id == telegram_msg_id:
...         # User replied to our message!
...         reply_text = update["message"]["text"]
...         ledger.log_response(
...             message_id=msg_id,
...             telegram_message_id=telegram_msg_id,
...             response_text=reply_text,
...             response_time="2026-06-21T09:45:00Z",
...             engagement_latency_seconds=855.0,
...             persona="AMMAR"
...         )

PHASE 17 INTEGRATION POINTS
-----------------------------
Upstream (consumes from Phase 16):
  - generate_and_dedupe() from HIKMAH__knowledge_index.message_generation
    returns (message_text, success, reason)
  - message_text is passed to TelegramRelayClient.send_message()

Downstream (provides to Phase 18):
  - DeliveryLedger entries enable Phase 18 response rate calculation:
    query log for "delivery" + "response" or "engagement_window_closed"
    to compute: response_rate = responses / deliveries
  - response_rate < 80% triggers format rotation (Phase 18)

Query example for Phase 18:
  >>> deliveries = ledger.get_deliveries_for_persona("AMMAR", limit=14)  # last 7 days
  >>> from pathlib import Path
  >>> import json
  >>> entries = json.loads(Path("DELIVERY_LEDGER.jsonl").read_text().splitlines())

ERROR HANDLING PATTERNS
------------------------
send_message() failure:
  - Relay raises RuntimeError (Telegram API returned ok=False)
  - DeliveryOrchestrator (Wave 2) catches, logs delivery with status="failure"
  - error_reason field records the error message

get_updates() conflict:
  - Relay raises GatewayPollingConflict (another process owns polling)
  - ResponseMonitor (Wave 2) catches, waits 60s, retries
  - If conflict persists > 3 retries, skip polling cycle (don't crash)

context_tags validation:
  - DeliveryLedger raises ValueError if invalid tag passed
  - Caller must use only whitelisted tags: technical, health, financial,
    strategic, personal

PERFORMANCE CHARACTERISTICS
----------------------------
- MessageIDGenerator.generate(): <1ms (pure Python, no I/O)
- MessageIDGenerator.parse(): <0.1ms (string operations only)
- DeliveryLedger.log_delivery(): <5ms (single JSON line append)
- TelegramRelayClient.send_message(): 1-5s (network round-trip to Telegram)
- TelegramRelayClient.get_updates(): up to timeout seconds (long-polling)

PRIVACY AND SAFETY NOTES
--------------------------
- Message IDs (MSG-...) encode only timestamp + random: no PII, no persona info
- Delivery ledger stores message_text (for audit), context_tags (privacy-gated)
- context_tags whitelist is the only privacy gate in this module (CONTEXT_TAGS_WHITELIST)
- Raw Telegram update dicts are NOT stored in the ledger (too much metadata)
- Response text truncated to 500 chars in log_response() (prevents bloat)
- All ledger files are strict_local (enforced by HIMAYAH gate + .gitignore)

REQUIREMENTS SATISFIED (WAVE 1 FOUNDATION)
-------------------------------------------
- DELIVERY-01: Foundation for twice-daily delivery (relay client abstraction ready)
- DELIVERY-02: Unique message_id generation (MessageIDGenerator.generate())
- DELIVERY-03: Delivery ledger with sent_at, delivered_at (DeliveryLedger.log_delivery())
- DELIVERY-04: Response polling infrastructure (TelegramRelayClient.get_updates() +
               check_reply_to_message_id())
- DELIVERY-05: Response logging infrastructure (DeliveryLedger.log_response() with
               engagement_latency_seconds)

Wave 2 will complete DELIVERY-01 (actual twice-daily delivery), DELIVERY-04
(1-hour window enforcement), and DELIVERY-05 (full response correlation).

TEST SCAFFOLD (WAVE 2)
-----------------------
Test directory ready at: HIKMAH__knowledge_index/delivery/tests/
Placeholder test files created for Wave 2 implementation:
- tests/conftest.py (shared fixtures and mocks)
- tests/test_message_id_generator.py (ID uniqueness, format, parse round-trip)
- tests/test_delivery_ledger.py (log operations, privacy gate, query methods)
- tests/test_telegram_relay_client.py (relay integration tests with mocks)

Planned test count (Wave 2): 30+ tests covering:
  - 10k ID uniqueness test (no collisions)
  - Ledger write/read operations
  - context_tags validation (reject invalid, accept valid)
  - Response correlation logic (reply_to_message_id matching)
  - Relay mocking (no real Telegram API calls in tests)
"""

from .delivery_ledger import DeliveryLedger
from .message_id_generator import MessageIDGenerator
from .telegram_relay_client import TelegramRelayClient

__all__ = [
    "MessageIDGenerator",
    "DeliveryLedger",
    "TelegramRelayClient",
]
