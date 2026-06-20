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
├── __init__.py                        # Public API (Phase 14-15 exports)
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
| README.md | Module documentation | 14-15 | ✓ |
| __init__.py | Public API (Phase 14-15 exports) | 15 | ✓ |
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

---

## Contact & Handoff

- **Module Owner:** Seif ElSherbiny (seif.elsherbiny13@gmail.com)
- **Phases Implemented:** 14 (Schema & Storage) + 15 (Data Refresh)
- **Next Phase:** 16 (Message Generation)
- **Privacy Compliance:** HIMAYAH gate + SYNC_POLICY
- **Last Updated:** 2026-06-20

---

*Document Version: 1.1*  
*Phases: 14 (Knowledge Index Schema & Storage) + 15 (Data Refresh & Synchronization)*  
*Classification: NIZAM Internal*
