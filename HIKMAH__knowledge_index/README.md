# HIKMAH Knowledge Index — Persona Knowledge State Tracking

## Overview

The HIKMAH Knowledge Index is a specialized persona-aware knowledge management system that tracks state for each NIZAM persona. It maintains per-persona indices of topics, activity history, blockers, and context snapshots to enable adaptive messaging in Phase 16 and downstream feedback loops in Phases 17–20.

**Codename:** HIKMAH = Weekly Synthesist + Pattern Promoter  
**Phase:** 14 (Foundation)  
**Privacy Classification:** `strict_local` (never egressed)  
**Status:** Active (v1.0)

---

## Purpose

Each persona requires contextual knowledge to generate fresh, actionable nudges twice daily:
- **Topic Tracking:** What has the user been focusing on? What's completed? What's blocked?
- **Activity History:** Recent accomplishments, engagement patterns, response trends
- **Context Snapshots:** Moment-in-time summaries of user state (mood, confidence, blockage)
- **Blockers:** Known obstacles preventing progress on topics

This index serves as the **foundation for adaptive messaging** (Phases 15–20), enabling:
- **Phase 15 (Data Refresh):** Merging Drive logs into per-persona indices
- **Phase 16 (Message Generation):** Fresh, contextual message rephrasing
- **Phase 17 (Delivery & Response Tracking):** Logging engagement metrics
- **Phase 18 (Adaptation & Format Evolution):** Rotating message formats based on response rates
- **Phase 19 (Cross-Pillar Integration):** Signaling MUNAWARA/MAL/TARIQ pillars
- **Phase 20 (Privacy & Safety Validation):** Ensuring no raw PII leakage

---

## Privacy: STRICT LOCAL ENFORCEMENT

### WARNING: SENSITIVE DATA ZONE

**Knowledge indices are STRICTLY LOCAL. They contain sensitive personal context, activity patterns, and user state. Under NO circumstances may these files be:**

- Committed to GitHub (`.gitignore` prevents this)
- Synced to Google Drive via Hermes (SYNC_POLICY blocks this)
- Exposed to Telegram (messages extract only safe context tags)
- Shared across machines or users

**All data remains encrypted on the local laptop/volume only.**

The HIMAYAH privacy gate enforces this classification. Violations trigger immediate sync blockage and audit warnings.

---

## Architecture

```
HIKMAH__knowledge_index/
├── README.md                          # This file
├── _index.json                        # Module self-registration
├── __init__.py                        # Public API (Phase 14-17 exports)
├── indices/                           # Per-persona indices (strict_local)
│   ├── AMMAR_index.json
│   ├── HIKMAH_index.json
│   ├── TARIQ_index.json
│   ├── MUNAWARA_index.json
│   ├── MAL_index.json
│   ├── BADAN_index.json
│   ├── NAQD_index.json
│   ├── SHURA_index.json
│   ├── TAFRIGH_index.json
│   ├── MARSAD_index.json
│   └── NIZAM_index.json
├── data/                              # Snapshot data (transient)
│   └── *.json                         # Per-persona context snapshots
├── index/                             # Phase 14: Index schema & storage
│   ├── schema.py                      # Index schema definition + validation
│   ├── writer.py                      # Ledger writer (append-only mutations)
│   └── main.py                        # Initialization + CLI utilities
├── refresh/                           # Phase 15: Data refresh pipeline
│   ├── __init__.py                    # Refresh API (refresh_persona_index)
│   ├── config.yaml                    # Externalized configuration
│   ├── config_loader.py               # Configuration loader + RefreshConfig
│   ├── drive_client.py                # Google Drive API client
│   ├── merge_strategy.py              # Merge logic for activity data
│   ├── ledger_writer.py               # RefreshAuditLogger for audit trail
│   ├── REFRESH_AUDIT_LEDGER.jsonl    # Audit trail (append-only)
│   └── tests/                         # Refresh tests (63 tests)
├── message_generation/                # Phase 16: Message generation
│   ├── __init__.py                    # Public API (generate_message, generate_and_dedupe)
│   ├── persona_tones.py               # System prompts for all 11 personas
│   ├── generator.py                   # Core generation with Claude API
│   ├── repetition_tracker.py          # Last-5 message deduplication (3-gram phrases)
│   ├── intent_processor.py            # Intent → context pipeline
│   ├── message_ledger.py              # JSONL ledger with privacy gates
│   ├── MESSAGE_LEDGER.jsonl           # Message audit trail (created on first write)
│   └── tests/                         # Message generation tests (81 tests)
│       ├── conftest.py                # Fixtures (MockClaude, sample indices)
│       ├── test_generator.py          # Core generation tests
│       ├── test_repetition_tracker.py # Deduplication tests
│       ├── test_intent_processor.py   # Context building tests
│       └── test_tone_consistency.py   # Tone validation tests
├── delivery/                          # Phase 17 (NEW): Message delivery & response tracking
│   ├── __init__.py                    # Public API (MessageIDGenerator, DeliveryLedger, TelegramRelayClient)
│   ├── message_id_generator.py        # Unique sortable ID generation (ULID-style)
│   ├── delivery_ledger.py             # JSONL ledger (delivery, response, window events)
│   ├── telegram_relay_client.py       # Hermes relay wrapper (send_message, get_updates)
│   └── tests/                         # Test suite (Wave 2 — 30+ tests planned)
│       ├── __init__.py
│       ├── conftest.py                # Shared fixtures (MockTelegramRelay, mock_ledger)
│       ├── test_message_id_generator.py  # ID uniqueness, format, parse round-trip
│       ├── test_delivery_ledger.py    # Write operations, privacy gate, queries
│       └── test_telegram_relay_client.py # Relay integration tests with mocks
├── DELIVERY_LEDGER.jsonl              # Delivery audit trail (created on first write)
└── tests/                             # Phase 14 validation tests
    ├── test_schema_validation.py
    └── test_sample_index.json
```

---

## Per-Persona Index Schema

Each persona index (`{PERSONA}_index.json`) follows this structure:

```json
{
  "persona": "AMMAR",
  "version": "1.0",
  "created_at": "2026-06-20T00:00:00Z",
  "updated_at": "2026-06-20T00:00:00Z",
  "topics": [
    {
      "topic_id": "topic_001",
      "title": "Project X Kickoff",
      "status": "open",
      "created_at": "2026-06-15T10:00:00Z",
      "last_activity": "2026-06-19T15:30:00Z",
      "engagement_count": 5,
      "context": "Initial planning phase",
      "blockers": ["Resource allocation pending"],
      "next_action": "Schedule kickoff meeting"
    }
  ],
  "activity_history": [
    {
      "date": "2026-06-19",
      "accomplishments": ["Completed design review", "Sent stakeholder update"],
      "engagement_score": 0.85,
      "mood_indicator": "positive"
    }
  ],
  "context_snapshot": {
    "last_updated": "2026-06-19T18:00:00Z",
    "confidence_level": 0.80,
    "current_focus": "Execution phase",
    "next_expected_action": "Team standup"
  },
  "metadata": {
    "phase": 14,
    "schema_version": "1.0",
    "ledger_offset": 0
  }
}
```

---

## Versioning & Schema Evolution

The index uses semantic versioning (`MAJOR.MINOR`) with support for schema migration via MAKHZAN snapshots:

- **Version 1.0:** Initial release (Phase 14)
- **Schema migrations:** When breaking changes are introduced, MAKHZAN creates a snapshot of the current ledger and index before applying migrations
- **Ledger:** Append-only, hash-chained for audit trail integrity

All schema changes must preserve backward compatibility or explicitly trigger MAKHZAN archival.

---

## Integration Points

### Upstream Producers (Phase 15: Data Refresh)
Phase 15 reads Google Drive conversation logs and merges activity data into indices:
- Extracts topics from conversation threads
- Updates activity_history with daily accomplishments
- Refreshes context_snapshot with latest engagement metrics

### Downstream Consumers (Phases 16–20)
- **Phase 16 (Message Generation):** Reads index to extract context for message rephrasing
- **Phase 17 (Response Tracking):** Logs engagement metrics after message delivery
- **Phase 18 (Adaptation):** Analyzes response patterns to rotate message formats
- **Phase 19 (Integration):** Signals pillar indices (MUNAWARA/MAL/TARIQ) with relevant topics
- **Phase 20 (Validation):** Audits index for raw PII before deployment

---

## Phase 15: Data Refresh Pipeline

Each refresh cycle runs the following steps:

1. **Load refresh configuration** from `refresh/config.yaml` (conversation_logs_folder, credentials_path, timeout)
2. **Initialize Google Drive client** with service account credentials
3. **Query Drive** for YAWMIYAT/sessions folder
4. **List and download** conversation log files (JSON format)
5. **Merge new activity** into per-persona indices (preserving stalled_work and completions)
6. **Log refresh attempt** to REFRESH_AUDIT_LEDGER.jsonl (success or failure)
7. **On Drive unavailability:** fall back to cached index, log degradation

### Configuration

See `refresh/config.yaml` for externalized settings (folder paths, timeouts, credentials):

```yaml
data_refresh:
  conversation_logs_folder: "YAWMIYAT/sessions"      # Google Drive folder path
  activity_snapshots_folder: "YAWMIYAT/daily_snapshots"
  credentials_path: "NIZAM-secrets.json"              # Service account credentials
  max_files_per_refresh: 100
  timeout_seconds: 30
  enable_partial_refresh: false
  audit_ledger_path: "HIKMAH__knowledge_index/REFRESH_AUDIT_LEDGER.jsonl"
  retry_on_transient_error: false
  max_retries: 0
  backoff_base: 2
```

**Operator can update Drive folder location without code changes** by editing config.yaml.

### Audit Trail

All refresh attempts logged to `REFRESH_AUDIT_LEDGER.jsonl`:

```json
{
  "ts": "2026-06-20T10:30:00Z",
  "persona": "AMMAR",
  "event_type": "refresh_attempt",
  "status": "success|failure|partial",
  "data_sources": ["YAWMIYAT/sessions"],
  "files_read": 5,
  "error": null,
  "prev_hash": "genesis",
  "row_hash": "SHA256(...)"
}
```

Entry fields:
- **ts:** ISO 8601 UTC timestamp
- **persona:** Persona name (AMMAR, HIKMAH, etc.)
- **event_type:** Always "refresh_attempt" for Phase 15
- **status:** "success" (fresh data merged), "failure" (Drive unavailable), "partial" (some files, some errors)
- **data_sources:** List of Drive folders queried
- **files_read:** Number of files successfully processed
- **error:** Error message (null on success)
- **prev_hash:** SHA256 of previous entry (or "genesis" for first entry)
- **row_hash:** SHA256 of this entry for integrity verification

Operator can query the ledger to answer: "When was AMMAR index last refreshed? Why did it fail?"

### Failure Handling

On Drive unavailability, refresh degrades gracefully:

| Error | Fallback | Logged As |
|-------|----------|-----------|
| Network timeout (>30s) | Return cached index | "failure" with timeout error |
| Auth failure (401/403) | Return cached index | "failure" with auth_failed error |
| Folder not found | Return cached index | "failure" with folder_not_found error |
| Malformed JSON in file | Skip file, continue others | "partial" or "success" if others processed |
| Schema validation error | Return cached index | "failure" with validation_error |

**Never silently degrades:** Always returns degradation reason in audit log and function return value.

### Integration with Phase 16 (Message Generation)

Phase 16 uses the refresh pipeline before generating messages:

```python
from HIKMAH__knowledge_index import refresh_persona_index, load_refresh_config

# Load configuration
config = load_refresh_config()

# Initialize Drive client and audit logger
drive_client = GoogleDriveClient(config.credentials_path)
audit_logger = RefreshAuditLogger(config.audit_ledger_path)

# Refresh index (fresh or cached)
success, index, degradation_reason = refresh_persona_index(
    persona="AMMAR",
    drive_client=drive_client,
    index_path=Path("HIKMAH__knowledge_index/indices/AMMAR_index.json"),
    audit_logger=audit_logger
)

if success:
    print(f"Refreshed AMMAR index from Drive")
    # Use fresh index for message generation
    topics = index.get("topics", [])
else:
    print(f"Using cached AMMAR index (reason: {degradation_reason})")
    # Gracefully degraded to cached index
```

Return value `(success, index, degradation_reason)`:
- **success=True:** Fresh index returned with latest Drive data
- **success=False, degradation_reason=None:** This won't happen (reason always set on degradation)
- **success=False, degradation_reason=str:** Cached index returned, reason explains why refresh failed

Phase 16 can always use the returned index for message generation, even if stale.

---

## Quick Start

### Loading a Persona Index

```python
import json

def load_index(persona: str) -> dict:
    """Load per-persona knowledge index."""
    index_path = f"HIKMAH__knowledge_index/indices/{persona}_index.json"
    with open(index_path, "r") as f:
        return json.load(f)

def get_topics(persona: str) -> list:
    """Get active topics for a persona."""
    index = load_index(persona)
    return [t for t in index.get("topics", []) if t["status"] == "open"]

def update_context_snapshot(persona: str, new_data: dict):
    """Update context snapshot (calls writer.py for ledger)."""
    # Triggers PERSONA_KNOWLEDGE_INDEX.jsonl append
    # See writer.py for mutation tracking
    pass
```

### Accessing Activity History

```python
index = load_index("AMMAR")
today_activity = [a for a in index["activity_history"] if a["date"] == "2026-06-20"]
```

---

## Testing & Validation

Test files are located in `HIKMAH__knowledge_index/tests/`:

- **test_schema_validation.py:** Validates index JSON against schema
- **test_sample_index.json:** Sample valid index for regression testing

Run tests with:
```bash
python -m pytest HIKMAH__knowledge_index/tests/ -v
```

---

## Ledger: PERSONA_KNOWLEDGE_INDEX.jsonl

The PERSONA_KNOWLEDGE_INDEX ledger (stored at `NIZAM__system/ledgers/PERSONA_KNOWLEDGE_INDEX.jsonl`) tracks all mutations to knowledge indices:

- **Format:** JSONL (append-only, one mutation per line)
- **Retention:** Permanent (archived via MAKHZAN on schema migration)
- **Privacy:** `strict_local` (never egressed)
- **Purpose:** Audit trail of all topic creates, updates, completions, blocker changes

Each ledger entry includes:
```json
{
  "timestamp": "2026-06-20T10:30:00Z",
  "persona": "AMMAR",
  "operation": "topic_create|topic_update|topic_complete|blocker_add|snapshot_update",
  "data": { ... },
  "hash": "sha256(previous_hash + entry_json)"
}
```

---

## Phase 16: Message Generation & Variation

### Overview

Phase 16 implements the core message generation engine that creates fresh, contextual, persona-consistent nudges twice daily. It consumes indices from Phase 15 and produces messages for Phase 17 delivery.

**Key Components:**
1. **Intent Rephrasing:** Converts user intents into rich context via IntentProcessor
2. **Tone Injection:** Applies persona-specific system prompts to Claude API calls
3. **Repetition Prevention:** RepetitionTracker detects phrase-level repeats from last 5 messages
4. **Actionability Validation:** Ensures messages contain imperative verbs or clear motivation
5. **Message Ledger:** Audit trail with privacy-gated context tags

### Core API

**Main Functions:**

```python
# Generate a single message (no repetition checking)
message = generate_message(
    persona="AMMAR",
    intent="You have 3 open items",
    index=ammar_index,
    client=anthropic_client,
    max_tokens=100
)
# Returns: "Pick one and move forward" (persona-toned)

# Generate message with repetition detection + ledger logging
message, success, reason = generate_and_dedupe(
    persona="AMMAR",
    intent="open work",
    index=ammar_index,
    client=anthropic_client,
    tracker=repetition_tracker,
    ledger=message_ledger,
    max_retries=3
)
# Returns: (message, True, "success") on first try
# Returns: (fallback, False, "max_retries_exceeded") if all retries repeat
# Returns: (fallback, False, "api_error") if Claude API fails
```

**Classes:**

- **`IntentProcessor`** — Converts intent to rich context
  - `extract_topics(intent, index)` — Find relevant topics via keyword matching
  - `build_context_summary(topics, index)` — Create descriptive summary with status
  - `should_celebrate(index)` — Detect recent completions for celebratory tone
  - `get_activity_summary(index)` — Aggregate activity events (counts by type)
  - `build_full_context(intent, index)` — Combine all context into dict for Claude

- **`RepetitionTracker`** — Last-5 message deduplication
  - `get_last_messages(persona, limit=5)` — Retrieve last N messages
  - `extract_key_phrases(text)` — Extract 3-gram phrases with min 10-char threshold
  - `is_repetition(new_message, persona)` — Check set intersection for phrase overlap
  - `log_message(persona, message_text, intent, success)` — Append to ledger

- **`MessageLedger`** — Audit trail with privacy enforcement
  - `log_generation(persona, message_text, intent, context_tags, ...)` — Write ledger entry
    - Validates context_tags against CONTEXT_TAGS_WHITELIST (technical, health, financial, strategic, personal)
    - Raises ValueError if invalid tag detected (fail-safe privacy gate)
  - `get_messages_for_persona(persona, limit=10)` — Query ledger

### Persona Tones

Each persona gets a distinct system prompt defining voice, constraints, and examples:

**AMMAR (Terse & Direct):**
- Example: "3 items waiting. Pick one and move forward."
- Tone markers: Imperative verbs (pick, move, focus, identify), no emotional language
- Constraint: Keep it factual and actionable

**HIKMAH (Philosophical & Reflective):**
- Example: "Your work carries weight. Notice the pattern. What's beneath this pause?"
- Tone markers: Reflective language (reflect, pattern, notice, mean, deeper), warmth
- Constraint: Deep but honest; no false cheerleading

**TARIQ (Strategic & Big-Picture):**
- Example: "This directly feeds Q3. Remove the blocker and restore momentum."
- Tone markers: Goal/timeline language (quarter, target, impact, horizon), strategic framing
- Constraint: Link to larger objectives

**Others (MUNAWARA, MAL, BADAN, NAQD, SHURA, TAFRIGH, MARSAD, NIZAM):**
- Unique system prompts defined in `persona_tones.py`
- All 11 personas fully supported with distinct voices

### Repetition Prevention Strategy

Why **3-gram phrase-level** over exact string matching?

- **Exact string:** "Your AI work is stalled" vs. "Your work on AI is stalled" → would miss rephrasings
- **3-gram (phrase-level):** Both share "work is stalled" → detected as repetition (correct!)
- **Min 10-char threshold:** Filters trivial phrases like "the" or "you have"
- **Performance:** O(n*m) where n≈20 words, m≈30 phrases → <5ms per check

Example:
```python
tracker = RepetitionTracker(ledger_path)
tracker.log_message("AMMAR", "Your AI workflow could be faster", "optimization")

# Later, check a candidate
is_repeat = tracker.is_repetition("Your AI work might accelerate", "AMMAR")
# True (shared phrase: "your ai")
```

### Message Constraints

- **Length:** <280 chars (fits Telegram limit)
- **PII:** No raw personal data (only safe context_tags)
- **Actionability:** Must contain imperative verbs or clear motivation
- **Repetition:** No exact phrase repeats from last 5 messages per persona

### Privacy & Safety

- **Context Tags:** Ledger stores only safe tags (technical, health, financial, strategic, personal), validated against whitelist
- **Strict Local:** All ledger entries remain on-device (never egressed)
- **Audit Trail:** Every generation (success/failure) logged for Phase 20 validation
- **Fallback Messages:** If Claude API fails, use contextual fallback (e.g., "You have 2 open items. Pick one.")

### Error Handling

Graceful degradation on API errors:
- **RateLimitError:** Retry with exponential backoff (1s, 2s, 4s)
- **APITimeoutError:** Retry up to max_retries, then fallback message
- **APIError:** Log error, return fallback, mark success=False in ledger
- **Fallback:** Generic contextual message when Claude unavailable

### Phase 17 Integration Example

```python
from HIKMAH__knowledge_index import (
    refresh_persona_index, load_refresh_config,
    generate_and_dedupe, RepetitionTracker, MessageLedger
)
from pathlib import Path
from anthropic import Anthropic
import os

# Phase 15: Load fresh index
config = load_refresh_config()
drive_client = GoogleDriveClient(config.credentials_path)
audit_logger = RefreshAuditLogger(config.audit_ledger_path)

success, index, reason = refresh_persona_index(
    persona="AMMAR",
    drive_client=drive_client,
    index_path=Path("HIKMAH__knowledge_index/indices/AMMAR_index.json"),
    audit_logger=audit_logger
)

# Phase 16: Generate message
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
tracker = RepetitionTracker(Path("HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl"))
ledger = MessageLedger(Path("HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl"))

message, success, reason = generate_and_dedupe(
    persona="AMMAR",
    intent="You have 3 open items on AI optimization",
    index=index,
    client=client,
    tracker=tracker,
    ledger=ledger,
    max_retries=3
)

# Returns: ("Pick one and move forward", True, "success")
# Ledger entry appended with: ts, persona, message_text, intent, context_tags, success

# Phase 17: Deliver to Telegram (next phase)
# hermes_relay.send_telegram(message, persona=persona, message_id=generate_message_id())
```

### Test Suite

Phase 16 includes comprehensive test coverage:
- **81 total tests** across 5 test modules
- **test_repetition_tracker.py:** 19 tests for phrase extraction, deduplication, ledger persistence
- **test_intent_processor.py:** 24 tests for topic extraction, context building, activity summarization
- **test_generator.py:** 20 tests for generation flow, error handling, ledger logging
- **test_tone_consistency.py:** 18 tests for tone validation across 5 consecutive generations per persona

**Run tests:**
```bash
# Quick run (unit tests only)
pytest HIKMAH__knowledge_index/message_generation/tests/ -v -k "not api"

# Full suite (all tests including mocked LLM)
pytest HIKMAH__knowledge_index/message_generation/tests/ -v

# Coverage check
pytest HIKMAH__knowledge_index/message_generation/tests/ --cov=HIKMAH__knowledge_index.message_generation --cov-report=term-missing
```

All tests use MockClaude fixture to avoid real API calls. Sample persona indices provided for AMMAR, HIKMAH, TARIQ, etc.

---

## Privacy Classification & Enforcement

### SYNC_POLICY Integration
The SYNC_POLICY blocks egress of `strict_local` files via:
- **HIMAYAH gate:** Checks classification before any sync/export operation
- **Trigger:** Prevents indices/ and ledger from being pushed to GitHub, Drive, or Telegram

### .gitignore Integration
```
HIKMAH__knowledge_index/indices/
NIZAM__system/ledgers/PERSONA_KNOWLEDGE_INDEX.jsonl
```

### PRIVACY_CLASSIFICATION.json Rules
Two rules enforce strict_local on this module:
1. **Per-persona indices:** `HIKMAH__knowledge_index/indices/*.json` → `strict_local`
2. **Ledger:** `NIZAM__system/ledgers/PERSONA_KNOWLEDGE_INDEX.jsonl` → `strict_local`

---

## Configuration & Dependencies

**Phase 14 (Index Schema & Storage):**
- No external dependencies beyond Python stdlib
- Uses only `json`, `datetime`, `hashlib` (for ledger hash chaining)

**Phase 15 (Data Refresh):**
- Requires `pyyaml` (for config.yaml parsing)
- Requires `google-api-python-client` and `google-auth` (for Drive API)
- **Configuration:** See `refresh/config.yaml` for all externalized settings
- **Credentials:** Set `credentials_path` in config.yaml (defaults to NIZAM-secrets.json)

**Python Version:** 3.8+

---

## Key Files

| File | Purpose | Phase | Status |
|------|---------|-------|--------|
| README.md | Module documentation | 14-16 | ✓ |
| __init__.py | Public API (Phase 14-16 exports) | 16 | ✓ |
| _index.json | Self-registration metadata | 14 | ✓ |
| index/schema.py | Schema definition + validation | 14 | ✓ |
| index/writer.py | Ledger writer (mutations) | 14 | ✓ |
| index/main.py | Initialization + versioning | 14 | ✓ |
| refresh/config.yaml | Externalized configuration | 15 | ✓ |
| refresh/config_loader.py | Configuration loader + RefreshConfig | 15 | ✓ |
| refresh/drive_client.py | Google Drive API client | 15 | ✓ |
| refresh/merge_strategy.py | Merge logic for activity data | 15 | ✓ |
| refresh/ledger_writer.py | RefreshAuditLogger for audit trail | 15 | ✓ |
| refresh/__init__.py | Refresh API (refresh_persona_index) | 15 | ✓ |
| message_generation/persona_tones.py | System prompts for all 11 personas | 16 | ✓ |
| message_generation/generator.py | Core generation + Claude API integration | 16 | ✓ |
| message_generation/repetition_tracker.py | Last-5 message deduplication (3-gram phrases) | 16 | ✓ |
| message_generation/intent_processor.py | Intent → context conversion pipeline | 16 | ✓ |
| message_generation/message_ledger.py | JSONL ledger with privacy enforcement | 16 | ✓ |
| message_generation/__init__.py | Message generation public API | 16 | ✓ |
| message_generation/tests/conftest.py | Shared pytest fixtures (MockClaude, indices) | 16 | ✓ |
| message_generation/tests/test_generator.py | Core generation tests (20 tests) | 16 | ✓ |
| message_generation/tests/test_repetition_tracker.py | Deduplication tests (19 tests) | 16 | ✓ |
| message_generation/tests/test_intent_processor.py | Context building tests (24 tests) | 16 | ✓ |
| message_generation/tests/test_tone_consistency.py | Tone validation tests (18 tests) | 16 | ✓ |
| delivery/__init__.py | Delivery public API (Phase 17 exports) | 17 | ✓ |
| delivery/message_id_generator.py | Unique sortable ID generation (MSG-YYYYMMDDHHMMSSMMMM-8HEX) | 17 | ✓ |
| delivery/delivery_ledger.py | JSONL ledger (delivery/response/window events, privacy gate) | 17 | ✓ |
| delivery/telegram_relay_client.py | Hermes relay wrapper (send_message, get_updates, reply correlation) | 17 | ✓ |
| delivery/tests/ | Wave 2 test scaffold (34 test cases specified) | 17 | Wave 2 |
| DELIVERY_LEDGER.jsonl | Delivery audit trail (created on first write) | 17 | created at runtime |

---

## Contact & Handoff

- **Module Owner:** Seif ElSherbiny (seif.elsherbiny13@gmail.com)
- **Phases Implemented:** 14 (Schema & Storage) + 15 (Data Refresh) + 16 (Message Generation)
- **Next Phase:** 18 (Adaptation & Format Evolution)
- **Privacy Compliance:** HIMAYAH gate + SYNC_POLICY
- **Last Updated:** 2026-06-21
- **Test Coverage:** 43+ Phase 14 tests + 63 Phase 15 tests + 81 Phase 16 tests = 187+ total (Wave 2 adds 30+ delivery tests)

---

## Phase 17: Delivery & Response Tracking

### Overview

Phase 17 implements the message delivery infrastructure for NIZAM's twice-daily Telegram messaging
(09:00 & 18:00 Cairo via Hermes cron). Every message sent receives a unique, sortable message ID
before dispatch, and all delivery events (sent, responded, no-response) are recorded in an
immutable JSONL audit trail.

**Wave 1 (Foundation — Phase 17-01):** Message ID generator, delivery ledger, relay client abstraction
**Wave 2 (Execution — Phase 17-02):** Delivery orchestrator, response monitor, 1-hour engagement window

**Requirements Satisfied:**
- DELIVERY-01: Twice-daily delivery via Hermes relay (relay client ready; Wave 2 adds scheduler)
- DELIVERY-02: Unique message_id per send (MessageIDGenerator.generate())
- DELIVERY-03: Delivery audit trail with sent_at/delivered_at (DeliveryLedger.log_delivery())
- DELIVERY-04: Response polling and correlation (TelegramRelayClient.get_updates() + reply matching)
- DELIVERY-05: Response logging with engagement latency (DeliveryLedger.log_response())

### Architecture

Message delivery follows this pipeline:

```
Phase 16 Output        Phase 17 Wave 1              Phase 17 Wave 2
─────────────────────  ──────────────────────────   ──────────────────────────────────
generate_and_dedupe()  MessageIDGenerator           DeliveryOrchestrator
  → message_text       .generate() → msg_id    ──→ coordinates ID + send + log
                                │
                       TelegramRelayClient         ResponseMonitor
                       .send_message(text)    ──→ polls get_updates() every 60s
                                │                 matches reply_to_message_id
                       DeliveryLedger              logs response or window close
                       .log_delivery()
```

**Directory structure:**
```
HIKMAH__knowledge_index/delivery/
├── __init__.py                           # Public API (NEW - Phase 17)
├── message_id_generator.py               # ULID-style ID generation (NEW)
├── delivery_ledger.py                    # JSONL ledger (NEW)
├── telegram_relay_client.py              # Hermes relay wrapper (NEW)
└── tests/
    ├── __init__.py
    ├── conftest.py                       # Shared fixtures (Wave 2)
    ├── test_message_id_generator.py      # 8 test cases (Wave 2)
    ├── test_delivery_ledger.py           # 14 test cases (Wave 2)
    └── test_telegram_relay_client.py     # 12 test cases (Wave 2)
```

### Core API

#### MessageIDGenerator

Generates globally unique, lexicographically sortable message IDs.

**Format:** `MSG-{YYYYMMDDHHMMSSMMMM}-{8-CHAR-HEX}`
**Example:** `"MSG-20260621093045123-A7F2E8CD"`

```python
from HIKMAH__knowledge_index import MessageIDGenerator

# Generate unique ID (called BEFORE sending to relay)
msg_id = MessageIDGenerator.generate()
print(msg_id)   # "MSG-20260621093045123-A7F2E8CD"

# Parse message ID (returns timestamp + original ID)
parsed = MessageIDGenerator.parse(msg_id)
print(parsed["timestamp_utc"])   # datetime(2026, 6, 21, 9, 30, 45, 123000, tzinfo=UTC)
print(parsed["message_id"])      # "MSG-20260621093045123-A7F2E8CD"

# Sortability: IDs generated in sequence sort chronologically
id1 = MessageIDGenerator.generate()
id2 = MessageIDGenerator.generate()
assert id1 < id2   # True (lexicographic == chronological order)
```

**Properties:**
- Always UTC (never local time, avoids DST confusion)
- Random 8-char hex suffix: ~4 billion values/millisecond (no collisions in practice)
- No PII encoded: timestamp + random only
- Parse raises ValueError on malformed input

#### DeliveryLedger

JSONL append-only audit trail for message delivery lifecycle events.

**Privacy gate:** context_tags validated against CONTEXT_TAGS_WHITELIST before writing.
**File:** `HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl` (created on first write)

```python
from HIKMAH__knowledge_index import DeliveryLedger
from pathlib import Path

ledger = DeliveryLedger(Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"))

# Log a delivery event (called after successful relay send)
ledger.log_delivery(
    message_id="MSG-20260621093045123-A7F2E8CD",
    telegram_message_id=12345,
    persona="AMMAR",
    message_text="Pick one and move forward.",
    intent="open_work",
    sent_at="2026-06-21T09:30:45Z",
    delivered_at="2026-06-21T09:30:46Z",
    context_tags=["technical"],   # must be whitelisted
    status="success"
)

# Log a response event (called when user replies within 1-hour window)
ledger.log_response(
    message_id="MSG-20260621093045123-A7F2E8CD",
    telegram_message_id=12345,
    response_text="On it.",
    response_time="2026-06-21T09:45:00Z",
    engagement_latency_seconds=855.0,
    persona="AMMAR"
)

# Log no-response (called when 1-hour window expires without reply)
ledger.log_no_response(
    message_id="MSG-20260621093045123-A7F2E8CD",
    telegram_message_id=12345,
    persona="AMMAR"
)

# Query deliveries for a persona (most recent first)
entries = ledger.get_deliveries_for_persona("AMMAR", limit=10)

# Check if a message got a response
response = ledger.get_responses_for_message("MSG-20260621093045123-A7F2E8CD")
if response:
    print(f"Response: {response['response_text']} (latency: {response['engagement_latency_seconds']}s)")
```

**Ledger Entry Format:**

Delivery event:
```json
{
  "ts": "2026-06-21T09:30:45.123Z",
  "message_id": "MSG-20260621093045123-A7F2E8CD",
  "telegram_message_id": 12345,
  "persona": "AMMAR",
  "event_type": "delivery",
  "message_text": "Pick one and move forward.",
  "intent": "open_work",
  "sent_at": "2026-06-21T09:30:45.000Z",
  "delivered_at": "2026-06-21T09:30:46.000Z",
  "context_tags": ["technical"],
  "status": "success",
  "error_reason": null,
  "ledger_hash": "a1b2c3d4e5f6a7b8"
}
```

**context_tags whitelist:** `["technical", "health", "financial", "strategic", "personal"]`
Invalid tags raise ValueError BEFORE write (fail-safe privacy gate).

#### TelegramRelayClient

Abstraction layer for NIZAM's Hermes relay. Never calls Telegram API directly.

```python
import os
from HIKMAH__knowledge_index import TelegramRelayClient
from NIZAM__system.relay.poller import GatewayPollingConflict

# Initialize (reads TELEGRAM_BOT_TOKEN env var automatically)
relay = TelegramRelayClient()
# Or with explicit token:
relay = TelegramRelayClient(token="1234567890:AABBCCDDEEFFaabbccddeeff1234567890")

# Send a message
response = relay.send_message(
    chat_id=int(os.environ["AMMAR_CHAT_ID"]),
    text="Your AI work is stalled. Pick one task and move forward."
)
telegram_msg_id = response["result"]["message_id"]
print(f"Sent: Telegram message ID = {telegram_msg_id}")

# Poll for updates (response monitor pattern)
try:
    updates = relay.get_updates(offset=last_update_id + 1, timeout=25)
    for update in updates:
        reply_to_id = relay.check_reply_to_message_id(update)
        if reply_to_id == telegram_msg_id:
            print(f"Reply received: {update['message']['text']}")
except GatewayPollingConflict:
    print("Another process is polling; waiting before retry...")

# Response correlation
update = {"update_id": 1, "message": {"reply_to_message": {"message_id": 12345}}}
reply_to = relay.check_reply_to_message_id(update)
print(reply_to)  # 12345
```

**Token precedence:** explicit token= > TELEGRAM_BOT_TOKEN env var > ValueError

### Delivery Ledger Event Types

| Event Type | When Written | Key Fields |
|-----------|-------------|-----------|
| `delivery` | After relay send (success or failure) | message_id, telegram_message_id, status, sent_at, delivered_at |
| `response` | When user replies within 1-hour window | message_id, response_text, engagement_latency_seconds |
| `engagement_window_closed` | After 1 hour with no reply | message_id, engagement_status="no_response" |

### Hermes Relay Integration

Phase 17 uses NIZAM's existing Hermes relay (NIZAM__system.relay.poller) rather than
calling Telegram's API directly. This is intentional:

**Why use Hermes relay:**
1. **No polling conflicts:** Telegram only allows ONE getUpdates caller per token. Hermes
   coordinates this via dedup.py. Phase 17 calling directly would cause 409 conflicts.
2. **Proven infrastructure:** Hermes relay has been in production since Phase 1 with
   battle-tested error handling (network timeouts, retries, auth).
3. **Token centralization:** Hermes owns the bot token lifecycle; multiple modules
   sharing a token creates coordination issues.
4. **No public endpoint:** Hermes uses outbound long-polling, so no domain/TLS needed.

**Conflict handling:**
```python
from NIZAM__system.relay.poller import GatewayPollingConflict
try:
    updates = relay.get_updates(offset=0, timeout=25)
except GatewayPollingConflict:
    # Another process (Hermes gateway) is polling; back off and retry
    time.sleep(60)
```

### Phase 18+ Integration Example

Phase 18 (Adaptation & Format Evolution) queries the delivery ledger to calculate
response rates and trigger format rotation:

```python
from HIKMAH__knowledge_index import DeliveryLedger
from pathlib import Path
import json

ledger = DeliveryLedger(Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"))

# Get last 14 deliveries (7 days × 2 per day)
deliveries = ledger.get_deliveries_for_persona("AMMAR", limit=14)

# Count responses
responses = 0
for delivery in deliveries:
    msg_id = delivery["message_id"]
    if ledger.get_responses_for_message(msg_id) is not None:
        responses += 1

# Calculate response rate
response_rate = responses / len(deliveries) if deliveries else 0
print(f"AMMAR response rate: {response_rate:.0%}")  # e.g., "71%"

if response_rate < 0.80:
    print("Response rate < 80% — trigger format rotation (Phase 18)")
```

### Common Pitfalls

**1. Timezone confusion in timestamps**
Always use UTC. Cairo time offset varies with DST. The scheduler converts
09:00/18:00 Cairo to UTC internally; Phase 17 ledger always stores UTC.
```python
from datetime import datetime, timezone
sent_at = datetime.now(timezone.utc).isoformat()  # Correct: UTC
# NOT: datetime.now().isoformat()  # Wrong: local time (Cairo)
```

**2. Response matching uses reply_to_message_id (not text matching)**
Users must explicitly reply to the message (not just send any message) for
the correlation to work. This is enforced by check_reply_to_message_id().
```python
# Correct: use Telegram's reply_to_message mechanism
reply_id = relay.check_reply_to_message_id(update)
if reply_id == sent_telegram_message_id:
    # This is a reply to our message
```

**3. GatewayPollingConflict requires backoff, not crash**
If Hermes gateway is running alongside the response monitor, conflicts will
occur. The response monitor (Wave 2) must catch and wait, not crash.
```python
try:
    updates = relay.get_updates(offset=0)
except GatewayPollingConflict:
    time.sleep(60)  # Wait for Hermes gateway polling cycle to release
```

**4. context_tags must match whitelist exactly**
Pass only whitelisted tags to log_delivery(). Invalid tags are rejected
before write (privacy gate). Check your intent mapping against the whitelist.
```python
CONTEXT_TAGS_WHITELIST = ["technical", "health", "financial", "strategic", "personal"]
```

### Error Handling Patterns

| Error | Source | Handler |
|-------|--------|---------|
| RuntimeError | relay.send_message() (Telegram API error) | Log delivery with status="failure", error_reason=str(e) |
| GatewayPollingConflict | relay.get_updates() (polling conflict) | Sleep 60s, retry; if >3 retries, skip cycle |
| ValueError | ledger.log_delivery() (invalid context_tag) | Fix tag mapping in delivery orchestrator |
| ValueError | TelegramRelayClient.__init__() (no token) | Set TELEGRAM_BOT_TOKEN env var |
| FileNotFoundError | ledger queries on missing file | Returns [] or None (handled gracefully) |

---
