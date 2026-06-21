"""
HIKMAH Knowledge Index Module

A comprehensive persona-aware knowledge management system for the NIZAM multi-persona framework.

Provides persona knowledge indices, versioning, data refresh pipeline, message generation,
and delivery infrastructure (Phases 14–17):
- Phase 14 (Index Schema & Storage): Define and store knowledge indices locally
- Phase 15 (Data Refresh): Read Google Drive logs and merge activity into indices
- Phase 16 (Message Generation & Variation): Generate fresh, persona-toned messages via Claude
- Phase 17 (Delivery & Response Tracking): Deliver messages via Hermes relay, track responses

All storage is strict_local (never egressed to Telegram, Drive, or GitHub).

**Public API:**

Initialization (Phase 14):
    from HIKMAH__knowledge_index import initialize_persona_index, initialize_all_personas
    - initialize_persona_index(persona, config): Create per-persona index
    - initialize_all_personas(config): Batch-create all 11 personas

Versioning (Phase 14):
    from HIKMAH__knowledge_index import increment_schema_version, snapshot_indices_to_makhzan
    - increment_schema_version(personas): Bump schema version atomically
    - snapshot_indices_to_makhzan(personas): Archive current indices to MAKHZAN

Refresh (Phase 15):
    from HIKMAH__knowledge_index import refresh_persona_index, load_cached_index, RefreshAuditLogger, load_refresh_config
    - refresh_persona_index(persona, drive_client, index_path, audit_logger): Refresh from Drive
    - load_cached_index(index_path): Load index from disk
    - RefreshAuditLogger: Audit trail logger for refresh operations
    - load_refresh_config(): Load configuration from YAML

Message Generation (Phase 16):
    from HIKMAH__knowledge_index import generate_message, generate_and_dedupe, RepetitionTracker, MessageLedger
    - generate_message(persona, intent, index, client): Generate message via Claude
    - generate_and_dedupe(persona, intent, index, client, tracker, ledger): Generate with repetition checking
    - RepetitionTracker: Track last 5 messages per persona
    - MessageLedger: JSONL audit trail with privacy enforcement

Delivery & Response Tracking (Phase 17):
    from HIKMAH__knowledge_index import MessageIDGenerator, DeliveryLedger, TelegramRelayClient
    - MessageIDGenerator.generate(): Create unique sortable message ID (MSG-{YYYYMMDDHHMMSSMMMM}-{8-HEX})
    - MessageIDGenerator.parse(msg_id): Extract timestamp from message ID
    - DeliveryLedger: JSONL ledger for delivery, response, and engagement window events
    - TelegramRelayClient: Abstraction layer for Hermes relay (send_message, get_updates, reply correlation)

Integration (Phases 16-20):
    from HIKMAH__knowledge_index import refresh_persona_index, generate_and_dedupe
    - Call refresh_persona_index() before message generation to get fresh index
    - Falls back to cached index if Drive unavailable
    - Pass index to generate_and_dedupe() for message generation

Usage (Phases 15-17 combined flow):
    from HIKMAH__knowledge_index import (
        refresh_persona_index, load_refresh_config,
        generate_and_dedupe, RepetitionTracker, MessageLedger,
        MessageIDGenerator, DeliveryLedger, TelegramRelayClient,
    )
    from anthropic import Anthropic
    from pathlib import Path

    # Phase 15: Refresh index
    config = load_refresh_config()
    success, index, reason = refresh_persona_index(
        persona="AMMAR",
        drive_client=drive_client,
        index_path=Path("HIKMAH__knowledge_index/indices/AMMAR_index.json"),
        audit_logger=audit_logger
    )

    # Phase 16: Generate message
    client = Anthropic(api_key="sk-ant-...")
    tracker = RepetitionTracker(Path("HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl"))
    msg_ledger = MessageLedger(Path("HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl"))
    message, gen_success, gen_reason = generate_and_dedupe(
        persona="AMMAR",
        intent="You have open work",
        index=index,
        client=client,
        tracker=tracker,
        ledger=msg_ledger
    )

    # Phase 17: Deliver message with unique ID and audit trail
    msg_id = MessageIDGenerator.generate()
    relay = TelegramRelayClient()  # reads TELEGRAM_BOT_TOKEN from env
    delivery_ledger = DeliveryLedger(Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"))

    response = relay.send_message(chat_id=AMMAR_CHAT_ID, text=message)
    telegram_msg_id = response["result"]["message_id"]

    delivery_ledger.log_delivery(
        message_id=msg_id,
        telegram_message_id=telegram_msg_id,
        persona="AMMAR",
        message_text=message,
        intent="open_work",
        sent_at="2026-06-21T09:30:45Z",
        delivered_at="2026-06-21T09:30:46Z",
        context_tags=["technical"],
        status="success"
    )
"""

__version__ = "1.0"

# Phase 14 imports (index schema & storage)
from HIKMAH__knowledge_index.index.main import (
    initialize_persona_index,
    initialize_all_personas,
)
from HIKMAH__knowledge_index.index.versioning import (
    increment_schema_version,
    snapshot_indices_to_makhzan,
)

# Phase 15 imports (data refresh)
from HIKMAH__knowledge_index.refresh import (
    refresh_persona_index,
    load_cached_index,
    initialize_refresh_logger,
)
from HIKMAH__knowledge_index.refresh.config_loader import (
    RefreshConfig,
    load_refresh_config,
)
from HIKMAH__knowledge_index.refresh.ledger_writer import RefreshAuditLogger

# Phase 16 imports (message generation)
from HIKMAH__knowledge_index.message_generation import (
    generate_message,
    generate_and_dedupe,
    RepetitionTracker,
    MessageLedger,
)

# Phase 17 imports (delivery & response tracking)
from HIKMAH__knowledge_index.delivery import (
    MessageIDGenerator,
    DeliveryLedger,
    TelegramRelayClient,
)

__all__ = [
    # Phase 14: Initialization
    'initialize_persona_index',
    'initialize_all_personas',
    # Phase 14: Versioning
    'increment_schema_version',
    'snapshot_indices_to_makhzan',
    # Phase 15: Refresh
    'refresh_persona_index',
    'load_cached_index',
    'initialize_refresh_logger',
    'RefreshConfig',
    'load_refresh_config',
    'RefreshAuditLogger',
    # Phase 16: Message Generation
    'generate_message',
    'generate_and_dedupe',
    'RepetitionTracker',
    'MessageLedger',
    # Phase 17: Delivery & Response Tracking
    'MessageIDGenerator',
    'DeliveryLedger',
    'TelegramRelayClient',
]
