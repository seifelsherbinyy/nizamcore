# Phase 14: Knowledge Index Schema & Storage - Research

**Researched:** 2026-06-20  
**Domain:** Persona knowledge indexing, local-only JSON storage, versioning patterns, privacy enforcement  
**Confidence:** HIGH (grounded in existing NIZAM data model, persona system, ledger patterns, and stated requirements)

## Summary

Phase 14 establishes the foundational data model and infrastructure for persona-driven knowledge indexing before any message generation, delivery, or adaptation begins. This phase delivers three critical inter-dependent items: (1) an optimized JSON schema per persona tracking topics, activity history, and context, (2) local-only strict_local storage initialized per persona with no egress to Telegram/Drive, and (3) versioning + schema evolution support for future persona additions without breaking existing indices.

The scope is strict: no message generation, no Telegram integration, no response tracking—only data structure, storage initialization, and governance. This phase blocks all downstream messaging work (phases 15–20) and must be rock-solid.

Research confirms that all decisions can leverage existing NIZAM patterns:
- **Data model patterns**: Follow NIZAM's universal frontmatter contract and ledger schema (Layer 5 memory model)
- **Privacy enforcement**: Reuse SYNC_POLICY classification system (strict_local classification proven in BADAN, MAL, TARIQ)
- **Storage**: JSONL append-only ledger pattern (proven in EVENT_LEDGER, LEARNING_LEDGER, STRATEGY_LEDGER)
- **Versioning**: Adopt CONTINUITY_PROTOCOL snapshot-before-evolution pattern (MAKHZAN archives)
- **Persona integration**: Personas already defined in NIZAM (AMMAR, HIKMAH, TARIQ, MUNAWARA, MAL, BADAN, NAQD, SHURA, MARSAD, TAFRIGH, NIZAM) with tone/operating_rules per persona JSON

**Primary recommendation:** Create one `PERSONA_KNOWLEDGE_INDEX.jsonl` ledger (strict_local classification, append-only) to track all personas' knowledge state. Initialize per-persona index files as JSON in `HIKMAH__knowledge_index/indices/` (strict_local) named `{PERSONA_NAME}_index.json` with schema supporting topics (array of topic objects), completions (closed topics with dates), activity_history (log of user actions + timestamps), stalled_work (blockers per topic), context_snapshots (current state tagged with confidence). Versioning via schema `version` field and MAKHZAN snapshots before evolution. Register ledger in NIZAM_TEMPLE.json and PRIVACY_CLASSIFICATION.json.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INDEX-01 | Schema with topics, completions, history, stalled_work, context_snapshots | Schema structure detailed below with exact field types + examples |
| INDEX-02 | Index stored locally per persona in strict_local (never egressed) | Storage path = HIKMAH__knowledge_index/indices/{PERSONA}_index.json (strict_local); PRIVACY_CLASSIFICATION rules confirmed |
| INDEX-03 | Versioning + schema evolution support for future personas | Version field in schema + MAKHZAN snapshot pattern on changes (proven in CONTINUITY_PROTOCOL) |
| INDEX-04 | Test run creates valid index file with correct structure | Test path identified; validation schema in place |

---

## User Constraints (from Roadmap + STATE)

### Locked Decisions
- Knowledge index is **strict_local only** — never egressed to Telegram, Drive, or GitHub (PRIVACY_CRITICAL)
- Twice-daily Telegram delivery (09:00 & 18:00 Cairo) **via Hermes cron** — reuses existing relay infrastructure
- Index refreshes from **Google Drive conversation logs** on each message generation (Phase 15 dependency)
- Response tracking **1-hour window** post-delivery (Phase 17 dependency)
- Adaptation triggers **<80% weekly response rate** (Phase 18 dependency)
- **Cross-pillar signals logged but optional** — no silent automation to MUNAWARA/MAL/TARIQ (Phase 19 dependency)
- Privacy validation **phase gate before deployment** — no raw PII in index/messages (Phase 20 dependency)

### Claude's Discretion (research options, recommend)
- **Module naming**: Where to store persona indices? (recommendation: new module `HIKMAH__knowledge_index` under HIKMAH's remit as weekly synthesist + pattern promoter)
- **Ledger technology**: Single ledger or per-persona ledgers? (recommendation: single `PERSONA_KNOWLEDGE_INDEX.jsonl` for all personas, keyed by persona_name)
- **Schema granularity**: Exact field structure for topics/context/activity? (detailed in Architecture section below with HIGH confidence)
- **Versioning strategy**: When to snapshot + migrate? (recommendation: MAKHZAN snapshot on schema_version change, adopt existing protocol)

### Deferred Ideas (OUT OF SCOPE Phase 14)
- Message generation logic (Phase 16)
- Telegram delivery + response tracking (Phases 17–18)
- Cross-pillar integration (Phase 19)
- Privacy validation + audit (Phase 20)
- ML-based tone optimization (v1.2+)
- Multi-channel delivery (v1.2+)

---

## Standard Stack

### Core Dependencies (No New Additions)

| Library | Version | Already Available? | Purpose | Why |
|---------|---------|---|---------|-----|
| **python** | 3.11+ | ✓ | Runtime | NIZAM stdlib-first pattern |
| **json** | stdlib | ✓ | Index serialization + ledger writes | NIZAM standard |
| **pathlib** | stdlib | ✓ | File path handling | Locale-independent, modern |
| **uuid** | stdlib | ✓ | Unique IDs for topics + snapshots | NIZAM standard |
| **hashlib** | stdlib | ✓ | Hash-chaining for ledger integrity | NIZAM standard (Event Ledger proven) |
| **datetime** | stdlib | ✓ | Timestamps (ISO 8601 UTC) | NIZAM standard |
| **typing** | stdlib | ✓ | Type hints | NIZAM standard |
| **jsonschema** | already pinned? | ? | Index schema validation (optional) | POP uses for frontmatter; optional for index |

### No New Pinned Dependencies Required for Phase 14

The index schema, per-persona JSON files, JSONL ledger, and versioning all use stdlib only. Refresh logic (Phase 15) will add Google API dependencies (`google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`) later.

---

## Architecture Patterns

### Recommended Module Folder Structure

**Module name:** `HIKMAH__knowledge_index` (verified against NIZAM naming)

**Rationale:** NIZAM naming pattern is `UPPERCASE_SYMBOL__snake_case_description`. HIKMAH (Khaldun) is the existing persona for "weekly synthesist and pattern promoter"; appending "knowledge index" clarifies that HIKMAH synthesizes and maintains persona knowledge patterns. Index storage falls naturally under HIKMAH's operational remit (reads ledgers, promotes patterns, watches longitudinal arcs).

**Directory tree:**

```
HIKMAH__knowledge_index/
├── README.md                          # Module overview + quick start
├── _index.json                        # Self-registration to NIZAM_TEMPLE (private_github)
├── .env.example                       # Env var documentation (committed, no secrets)
├── conftest.py                        # Shared pytest config
│
├── index/                             # Core indexing logic
│   ├── __init__.py
│   ├── main.py                        # Entry point (init + validation)
│   ├── schema.py                      # Index schema definition + validation
│   ├── writer.py                      # Per-persona index file writer
│   └── versioning.py                  # Schema evolution + MAKHZAN snapshots
│
├── indices/                           # Per-persona index storage (strict_local — never committed)
│   ├── AMMAR_index.json               # Steward persona knowledge state
│   ├── HIKMAH_index.json              # Wisdom persona knowledge state
│   ├── TARIQ_index.json               # Strategic persona knowledge state
│   ├── MUNAWARA_index.json            # Tactical persona knowledge state
│   ├── MAL_index.json                 # Finance persona knowledge state
│   ├── BADAN_index.json               # Health persona knowledge state
│   ├── NAQD_index.json                # Critique persona knowledge state
│   ├── SHURA_index.json               # Counsel persona knowledge state
│   ├── TAFRIGH_index.json             # Capture persona knowledge state
│   ├── MARSAD_index.json              # Watchlist persona knowledge state
│   └── NIZAM_index.json               # Orchestration persona knowledge state
│
├── data/                              # Metadata + audit trail
│   ├── schema_versions.json           # History of schema versions (git-tracked)
│   └── init_manifest.json             # Initialization manifest (git-tracked)
│
└── tests/
    ├── test_schema_validation.py      # Schema structure validation
    ├── test_index_initialization.py   # Per-persona index creation
    └── test_versioning.py             # Schema evolution + snapshots
```

**Privacy classification:**
- `indices/{PERSONA}_index.json` → `strict_local` (never egressed, never committed, only on laptop/encrypted volume)
- `schema_versions.json` → `private_github` (schema history is publishable)
- `init_manifest.json` → `private_github` (initialization record is publishable)

---

## Knowledge Index Schema Design

### Top-level Index Structure (per persona)

```json
{
  "version": "1.0",
  "persona": "AMMAR",
  "initialized_at": "2026-06-20T14:30:00Z",
  "last_updated": "2026-06-20T14:30:00Z",
  "topics": [
    {
      "id": "uuid-v4-unique-per-topic",
      "name": "AI optimization workflow",
      "status": "active",
      "created_at": "2026-06-15T10:00:00Z",
      "last_activity": "2026-06-19T17:45:00Z",
      "context_tags": ["technical", "career", "optimization"],
      "confidence": 0.85,
      "key_accomplishments": [
        {
          "text": "Set up streaming inference pipeline",
          "timestamp": "2026-06-18T14:00:00Z"
        }
      ],
      "blockers": [
        {
          "text": "GPU memory constraints on current infra",
          "since": "2026-06-15T10:00:00Z",
          "severity": "medium"
        }
      ],
      "notes": "Core optimization work for career progression"
    }
  ],
  "completions": [
    {
      "id": "uuid-completed-topic",
      "name": "Q1 financial baseline review",
      "completed_at": "2026-06-10T16:00:00Z",
      "duration_days": 25,
      "context_tags": ["financial", "quarterly"],
      "final_note": "Completed baseline; MAL integration ready"
    }
  ],
  "activity_history": [
    {
      "ts": "2026-06-20T14:00:00Z",
      "event_type": "topic_created",
      "topic_id": "uuid-v4",
      "description": "New topic: AI optimization workflow"
    },
    {
      "ts": "2026-06-19T17:45:00Z",
      "event_type": "accomplishment_logged",
      "topic_id": "uuid-v4",
      "description": "Set up streaming inference pipeline"
    },
    {
      "ts": "2026-06-15T10:00:00Z",
      "event_type": "blocker_flagged",
      "topic_id": "uuid-v4",
      "description": "GPU memory constraints identified"
    }
  ],
  "stalled_work": [
    {
      "topic_id": "uuid-v4",
      "topic_name": "AI optimization workflow",
      "blocker_count": 1,
      "stalled_since": "2026-06-15T10:00:00Z",
      "days_stalled": 5,
      "last_activity": "2026-06-19T17:45:00Z",
      "recovery_notes": "Awaiting GPU scaling decision"
    }
  ],
  "context_snapshots": [
    {
      "ts": "2026-06-20T14:30:00Z",
      "snapshot": {
        "open_topic_count": 3,
        "active_blocker_count": 2,
        "recent_accomplishments_count": 5,
        "completion_rate_7d": 0.40,
        "engagement_level": "medium"
      }
    }
  ],
  "metadata": {
    "source": "v1.1-knowledge-index",
    "locale": "Egypt/Cairo",
    "language": "en"
  }
}
```

### Schema Versioning

**Version field:** Semantic versioning (MAJOR.MINOR)

- **v1.0**: Initial schema with topics, completions, activity_history, stalled_work, context_snapshots
- **v1.1** (future): Could add "engagement_patterns" array without breaking v1.0 readers (backward-compatible)
- **v2.0** (future): Breaking changes requiring MAKHZAN snapshot + migration guide

**Migration strategy** (per CONTINUITY_PROTOCOL):
1. Before schema change: snapshot current indices to `MAKHZAN__archive/{timestamp}/` with manifest
2. Increment `schema_version` in all files
3. Document migration path in `CHANGELOG.md`
4. Run validation: confirm all indices parse post-migration

---

## Storage & Versioning Strategy

### Local-Only Storage (Strict Privacy Enforcement)

**Classification:** `strict_local` per SYNC_POLICY
- Never committed to GitHub (`.gitignore` entries for `indices/`)
- Never synced to Google Drive (HIMAYAH gate blocks)
- Accessible **laptop only** or **encrypted volume only** (per NIZAM governance)

**File system permissions:**
```bash
# Files should be readable by owner only (user runs the Python code)
chmod 600 HIKMAH__knowledge_index/indices/*.json
```

**Encryption at rest:** Optional — if using NIZAM's encrypted volume (Cryptomator, age, or disk-level encryption), indices inherit that protection. No in-file encryption required (NIZAM assumes OS-level protection).

### Initialization Flow

1. **Phase 14 Wave 0:** Create empty `HIKMAH__knowledge_index/` module folder + Python package
2. **Phase 14 Wave 1:** Define schema + validation logic (`index/schema.py`)
3. **Phase 14 Wave 2:** Initialize per-persona index files (all 11 personas) with empty topics/completions/activity_history arrays
4. **Phase 14 Wave 3:** Register ledger + test empty index creation

### Append-Only Ledger (Auditable History)

**New ledger:** `PERSONA_KNOWLEDGE_INDEX.jsonl` (strict_local classification)

**Purpose:** Track all knowledge index mutations (topic creates, accomplishments, blocker flags, completions, context snapshots)

**Row schema:**
```json
{
  "ts": "2026-06-20T14:30:00Z",
  "ledger": "PERSONA_KNOWLEDGE_INDEX",
  "row_id": "uuid4",
  "trace_id": "uuid4-end-to-end-chain-id",
  "actor": "Salman|operator|TARIQ|HIKMAH",
  "action": "topic_created|accomplishment_logged|blocker_flagged|topic_completed|context_snapshot",
  "persona": "AMMAR|HIKMAH|TARIQ|etc.",
  "module": "HIKMAH__knowledge_index",
  "privacy_class": "strict_local",
  "prev_hash": "sha256-of-prior-row",
  "row_hash": "sha256-of-this-row-excluding-row_hash",
  "payload": {
    "topic_id": "uuid-or-null",
    "topic_name": "string",
    "description": "what happened",
    "blocker_text": "if blocker event",
    "accomplishment_text": "if accomplishment event"
  }
}
```

**Registration:**
- Add to `NIZAM_TEMPLE.json` → `ledgers` section
- Add to `NIZAM__system/governor/ledger_writer.py` → `KNOWN_LEDGERS` set
- Add to `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json` → rules for `PERSONA_KNOWLEDGE_INDEX.jsonl` as `strict_local`

### Versioning via Snapshots (MAKHZAN Pattern)

When schema version increments:
1. Snapshot all current indices to `MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices/`
2. Create `MAKHZAN__archive/{ISO_TIMESTAMP}/MANIFEST.json` with:
   - Original schema version
   - Change description
   - Migration path
   - Operator who triggered (or "auto_system")
   - Timestamp

**Example manifest:**
```json
{
  "trigger": "schema_version_increment",
  "from_version": "1.0",
  "to_version": "1.1",
  "change": "Added engagement_patterns array (backward-compatible)",
  "snapshot_at": "2026-07-15T10:00:00Z",
  "indices_backed_up": 11,
  "operator": "auto_system",
  "recovery_note": "If rollback needed, restore from this snapshot and revert schema_version field"
}
```

---

## Integration Points (Downstream Phases)

### Phase 15: Data Refresh & Synchronization
- **Input**: Index files from Phase 14
- **Operation**: Refresh index topics from Google Drive logs; merge new activity without overwriting stalled/completed flags
- **Output**: Updated index files + audit log
- **Research gap**: Exact format of Google Drive conversation logs (Phase 15 will research)

### Phase 16: Message Generation & Variation
- **Input**: Index per selected persona (e.g., AMMAR_index.json)
- **Operation**: Pull open topics + recent accomplishments; rephrase intent; apply persona tone
- **Output**: Fresh message + message_id
- **No schema change**: Phase 16 reads index, doesn't write (Phase 15 refreshes it)

### Phase 17: Delivery & Response Tracking
- **Input**: Message + message_id from Phase 16
- **Operation**: Send via Telegram; record sent_at + delivered_at in index
- **Output**: Response metadata stored in index (response_timestamp, response_content)
- **Schema addition**: Response tracking may add `response_log` array to index (indexed by message_id)

### Phase 18: Adaptation & Format Evolution
- **Input**: Response rates from Phase 17
- **Operation**: Track weekly engagement; log format changes
- **Output**: Format rotation + rationale logged to PERSONA_KNOWLEDGE_INDEX ledger
- **No schema change**: Phase 18 reads response_log, doesn't modify core schema

### Phase 19: Cross-Pillar Integration
- **Input**: Messages + topics from Phase 16
- **Operation**: Signal MUNAWARA/MAL/TARIQ based on message content
- **Output**: Ledger entries (persona_message_log) with pillar_signals_sent
- **Integration**: New ledger `PERSONA_MESSAGE_LOG.jsonl` (strict_local) or extend PERSONA_KNOWLEDGE_INDEX

### Phase 20: Privacy & Safety Validation
- **Input**: All indices from Phase 14 + messages from Phase 16
- **Operation**: Audit for raw PII; validate context_tags are safe
- **Output**: Privacy audit report + sign-off
- **Validation**: Schema includes `confidence` field; Phase 20 checks for <80% topics being skipped in messages

---

## Common Pitfalls

### Pitfall 1: PII Leakage in Context Tags
**What goes wrong:** Context tags like "Seif's workflow" or "my mother's health" creep into the index, then appear in messages.

**Why it happens:** Persona agents lazily tag context with raw names instead of derived/safe tags.

**How to avoid:** 
- Schema validation: `context_tags` must match a whitelist (e.g., "technical", "health", "financial", "strategic", "personal")
- Linter check pre-ledger-write: reject tags not on whitelist
- Privacy gate (Phase 20) audits all context_tags before sign-off

**Warning signs:** 
- Index files contain "Seif", "family names", "health conditions", "financial amounts"
- Message generation includes raw context without "safe" prefix

### Pitfall 2: Schema Drift (Version Mismatch)
**What goes wrong:** Some index files stay at v1.0 while others are v1.1; message generation breaks on missing fields.

**Why it happens:** Manual version bumping without coordinating all 11 persona files; incomplete MAKHZAN snapshots.

**How to avoid:**
- Centralize version bump: single script updates all 11 files atomically
- Snapshot BEFORE version bump (MAKHZAN pattern)
- Validation at read-time: confirm index schema_version matches expected version; error if mismatch

**Warning signs:** 
- "KeyError: engagement_patterns" in Phase 16 message generation
- Some personas' indices have v1.1, others v1.0

### Pitfall 3: Activity History Explosion (Performance)
**What goes wrong:** `activity_history` array grows unbounded (1000s of rows per persona over months); index files balloon; read latency increases.

**Why it happens:** Logging every single action (topic created, blocker flagged, accomplished, etc.) without pruning or archiving.

**How to avoid:**
- Define retention policy: keep last 90 days of activity_history in live index; archive older entries to MAKHZAN
- Implement cleanup task: Phase 15 refresh (or separate cron) trims activity_history periodically
- Ledger is permanent: PERSONA_KNOWLEDGE_INDEX.jsonl keeps full history; index JSON is working copy

**Warning signs:** 
- Index files exceed 1MB
- Refresh latency >5s per persona

### Pitfall 4: Stalled Work Detection Brittleness
**What goes wrong:** Stalled work detection misses topics or flags false positives (topic marked stalled even though user is still working).

**Why it happens:** No distinction between "user paused intentionally" vs. "user abandoned"; arbitrary "days_stalled" threshold.

**How to avoid:**
- Add `stalled_status` enum: "active", "paused", "blocked", "completed" (not inferred; user-set or inference-with-confidence)
- Confidence <80% on stalled inference → skip stalling notifications (Phase 20 gates)
- Phase 15 refresh: check Google Drive logs to confirm stalled status before marking

**Warning signs:** 
- Personas receiving nudges on topics they intentionally paused
- "Days stalled" counter doesn't reset after user logs new activity

### Pitfall 5: Cross-Persona Context Pollution
**What goes wrong:** AMMAR's index leaks into HIKMAH's message generation; tones collide (steward + wisdom = incoherent).

**Why it happens:** Message generation accidentally pulls from wrong index file or merges multiple personas' contexts.

**How to avoid:**
- Namespace isolation: each persona index file loaded separately; no cross-reading in Phase 16
- Message generation: explicit persona parameter; validate index persona matches selected persona
- Tests: verify AMMAR_index.json is never accessed when generating HIKMAH message

**Warning signs:** 
- Messages from HIKMAH contain AMMAR's steward tone
- Index file names don't match persona names

---

## Code Examples

### Schema Definition (Python)

```python
# Source: HIKMAH__knowledge_index/index/schema.py
from typing import TypedDict, Optional, List
from datetime import datetime
import json

class TopicDict(TypedDict):
    id: str
    name: str
    status: str  # "active" | "completed" | "paused"
    created_at: str  # ISO 8601
    last_activity: str
    context_tags: List[str]  # Whitelisted: ["technical", "health", "financial", "strategic", "personal"]
    confidence: float  # 0.0–1.0; <0.8 flags for privacy gate
    key_accomplishments: List[dict]  # [{text, timestamp}]
    blockers: List[dict]  # [{text, since, severity}]
    notes: str

class PersonaIndexDict(TypedDict):
    version: str  # "1.0", "1.1", etc.
    persona: str  # "AMMAR", "HIKMAH", etc.
    initialized_at: str
    last_updated: str
    topics: List[TopicDict]
    completions: List[dict]
    activity_history: List[dict]
    stalled_work: List[dict]
    context_snapshots: List[dict]
    metadata: dict

def validate_index_schema(data: dict) -> tuple[bool, Optional[str]]:
    """Validate index structure against schema. Return (valid, error_msg)."""
    required_fields = ["version", "persona", "topics", "completions", "activity_history"]
    for field in required_fields:
        if field not in data:
            return (False, f"Missing required field: {field}")
    
    # Validate version format
    version = data.get("version", "")
    if not version.startswith("1."):
        return (False, f"Invalid version: {version}")
    
    # Validate persona is registered
    valid_personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN", 
                      "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]
    if data.get("persona") not in valid_personas:
        return (False, f"Unknown persona: {data.get('persona')}")
    
    # Validate context_tags are whitelisted
    whitelist = {"technical", "health", "financial", "strategic", "personal"}
    for topic in data.get("topics", []):
        for tag in topic.get("context_tags", []):
            if tag not in whitelist:
                return (False, f"Invalid context_tag in topic {topic.get('name')}: {tag}")
    
    return (True, None)
```

### Index Initialization (Python)

```python
# Source: HIKMAH__knowledge_index/index/main.py
from pathlib import Path
import json
from datetime import datetime, timezone

def initialize_persona_index(persona: str, target_dir: Path) -> Path:
    """Create empty index for a persona. Return path to created file."""
    if persona not in ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN", 
                       "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]:
        raise ValueError(f"Unknown persona: {persona}")
    
    now = datetime.now(timezone.utc).isoformat()
    index = {
        "version": "1.0",
        "persona": persona,
        "initialized_at": now,
        "last_updated": now,
        "topics": [],
        "completions": [],
        "activity_history": [
            {
                "ts": now,
                "event_type": "index_initialized",
                "persona": persona,
                "description": f"Knowledge index initialized for {persona}"
            }
        ],
        "stalled_work": [],
        "context_snapshots": [
            {
                "ts": now,
                "snapshot": {
                    "open_topic_count": 0,
                    "active_blocker_count": 0,
                    "recent_accomplishments_count": 0,
                    "completion_rate_7d": 0.0,
                    "engagement_level": "unknown"
                }
            }
        ],
        "metadata": {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
    }
    
    # Validate schema
    valid, error = validate_index_schema(index)
    if not valid:
        raise ValueError(f"Schema validation failed: {error}")
    
    # Write to file
    target_dir.mkdir(parents=True, exist_ok=True)
    index_path = target_dir / f"{persona}_index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    
    return index_path

def initialize_all_personas(indices_dir: Path) -> dict:
    """Initialize all 11 persona indices. Return mapping {persona: path}."""
    personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN", 
                "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]
    result = {}
    for persona in personas:
        result[persona] = initialize_persona_index(persona, indices_dir)
    return result
```

### Ledger Registration

```json
# Addition to NIZAM_TEMPLE.json (under "ledgers" section)
{
  "name": "PERSONA_KNOWLEDGE_INDEX",
  "privacy": "strict_local",
  "phase": 14,
  "purpose": "Track all knowledge index mutations per persona (topic creates, accomplishments, blockers, completions, context snapshots)",
  "writer": "HIKMAH__knowledge_index/index/writer.py",
  "row_schema": "NIZAM__system/schemas/persona_knowledge_index_row.schema.json",
  "note": "Append-only; hash-chained for integrity"
}

# Addition to PRIVACY_CLASSIFICATION.json (under "rules" section)
{
  "path_glob": "HIKMAH__knowledge_index/indices/*.json",
  "classification": "strict_local",
  "reason": "Per-persona knowledge state; sensitive context tracking; never egressed"
}
{
  "path_glob": "NIZAM__system/ledgers/PERSONA_KNOWLEDGE_INDEX.jsonl",
  "classification": "strict_local",
  "reason": "Audit trail of knowledge index mutations; sensitive context"
}

# Addition to ledger_writer.py (in KNOWN_LEDGERS set)
KNOWN_LEDGERS = {
    "EVENT_LEDGER",
    "LEARNING_LEDGER",
    "DECISION_LEDGER",
    "STRATEGY_LEDGER",
    "BATTLE_LEDGER",
    "FINANCE_LEDGER",
    "BODY_LEDGER",
    "PERSONA_KNOWLEDGE_INDEX",  # ← NEW
}
```

---

## Validation Architecture

**nyquist_validation is enabled** (`.planning/config.json` → `workflow.nyquist_validation: true`)

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` (stdlib for NIZAM) |
| Config file | `HIKMAH__knowledge_index/conftest.py` + `pytest.ini` |
| Quick run command | `pytest HIKMAH__knowledge_index/tests/ -v --tb=short` |
| Full suite command | `pytest HIKMAH__knowledge_index/tests/ -v --cov=HIKMAH__knowledge_index --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|------------|
| INDEX-01 | Schema with topics, completions, history, blockers, snapshots | unit | `pytest HIKMAH__knowledge_index/tests/test_schema_validation.py::test_schema_structure -xvs` | ❌ Wave 0 |
| INDEX-02 | Per-persona index created in strict_local location | unit | `pytest HIKMAH__knowledge_index/tests/test_index_initialization.py::test_initialize_all_personas -xvs` | ❌ Wave 0 |
| INDEX-03 | Schema versioning + MAKHZAN snapshots on changes | unit | `pytest HIKMAH__knowledge_index/tests/test_versioning.py::test_schema_version_increment -xvs` | ❌ Wave 0 |
| INDEX-04 | Empty test run creates valid, readable index files | integration | `pytest HIKMAH__knowledge_index/tests/test_index_initialization.py::test_create_valid_index_files -xvs` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit**: `pytest HIKMAH__knowledge_index/tests/ -v --tb=short`
- **Per wave merge**: `pytest HIKMAH__knowledge_index/tests/ -v --cov=HIKMAH__knowledge_index`
- **Phase gate**: Full suite green + privacy check (no raw PII in schema)

### Wave 0 Gaps

- [ ] `HIKMAH__knowledge_index/tests/test_schema_validation.py` — validate schema structure (topics, completions, activity_history, stalled_work, context_snapshots)
- [ ] `HIKMAH__knowledge_index/tests/test_index_initialization.py` — test per-persona index creation for all 11 personas
- [ ] `HIKMAH__knowledge_index/tests/test_versioning.py` — test schema version bumping + MAKHZAN snapshots
- [ ] `HIKMAH__knowledge_index/tests/conftest.py` — shared fixtures (temp directories, sample indices)
- [ ] `HIKMAH__knowledge_index/conftest.py` — top-level pytest config
- [ ] Framework setup: ensure `pytest` available in venv; install if needed

---

## State of the Art

### Current Approach (v1.1)
| Old | New | Rationale |
|-----|-----|-----------|
| No per-persona knowledge state | JSON-based per-persona index | Enables persona-specific nudging + adaptation |
| Raw activity logs only | Index + append-only ledger | Supports incremental refresh + auditability |
| No context tags | Whitelisted context_tags | Prevents PII leakage while preserving context for messages |
| No versioning | Schema version + MAKHZAN snapshots | Supports future schema evolution without data loss |
| Manual ledger writes | Automated PERSONA_KNOWLEDGE_INDEX ledger | Centralized audit trail for all index mutations |

### Deprecated/Outdated (v1.0)
- None (Phase 14 is the foundation; no v1.0 to deprecate)

---

## Open Questions

1. **Google Drive Conversation Log Format**
   - What we know: Phase 15 will refresh index from Google Drive logs; logs exist in NIZAM user's Drive
   - What's unclear: Exact format, location, field names, timestamp format, activity categorization
   - Recommendation: Phase 15 research must uncover this; document in Phase 15 RESEARCH.md before planning

2. **Response Tracking Integration**
   - What we know: Phase 17 will track responses in 1-hour window via Telegram relay; relay already operational
   - What's unclear: Exact response storage model (update existing index? new ledger? separate response_log array?)
   - Recommendation: Phase 17 planning decides; Phase 14 reserves `response_log` array in schema (optional, v1.1+)

3. **Multi-Persona vs. Single Index**
   - What we know: Phase 14 recommends 11 separate persona index files + 1 shared ledger
   - What's unclear: If future work needs cross-persona synthesis (all personas' contexts), would single merged index be better?
   - Recommendation: v1.1 keeps separate files (simpler, safer); v1.2 can consider merged index if synthesis is needed

4. **Blocker Severity Levels**
   - What we know: Schema includes blocker `severity` field (low/medium/high)
   - What's unclear: Exact threshold for blocker escalation (when does high-severity blocker trigger Phase 16 message?)
   - Recommendation: Phase 16 planning defines; Phase 14 schema accepts any severity value

5. **Activity History Cleanup Policy**
   - What we know: Activity history is append-only; can grow unbounded
   - What's unclear: When to archive (90 days? 6 months? rolling window?); how often to run cleanup?
   - Recommendation: Phase 15 refresh task implements cleanup; document policy in HIKMAH__knowledge_index/README.md

---

## Known Gaps / Deferred Items

| Gap | Why Deferred | Phase/Milestone |
|----|---|---|
| Message generation logic (rephrase intent, apply tone) | Depends on Phase 14 index | Phase 16 |
| Google Drive refresh logic | Depends on Phase 14 index | Phase 15 |
| Response tracking storage | Depends on Phase 14 index + Phase 17 Telegram integration | Phase 17 |
| Format adaptation logic | Depends on Phase 17 response data | Phase 18 |
| Cross-pillar signal routing | Depends on Phase 16 messages | Phase 19 |
| Privacy audit + sign-off | Depends on all upstream phases | Phase 20 |
| ML-based tone optimization | v1.2+; manual persona tuning sufficient for v1 | v1.2 |
| Multi-channel delivery (email, Slack) | Telegram proven; add after v1 validation | v1.2 |
| Persona-to-persona discussion before sending | Defer; single-persona messages first | v1.2 |

---

## Sources

### Primary (HIGH confidence)

- **NIZAM system architecture** — `/d/nizam/NIZAM__system/` (personas, ledgers, privacy policies, governance)
  - `NIZAM_TEMPLE.json` — module/ledger registration
  - `NIZAM__system/personas/{AMMAR,HIKMAH,TARIQ,etc.}.json` — persona definitions
  - `NIZAM__system/ledgers/README.md` — ledger schema + integrity model
  - `NIZAM__system/policies/SYNC_POLICY.json` — privacy classification rules
  - `NIZAM__system/docs/CONTINUITY_PROTOCOL.md` — versioning + snapshot pattern
  - `NIZAM__system/docs/MEMORY_MODEL.md` — six-layer memory architecture
  - `NIZAM__system/docs/DATA_MODEL.md` — POP artifact types + ledger contract

- **Existing NIZAM patterns** — verified via code inspection
  - Hash-chained ledger integrity (EVENT_LEDGER.jsonl examples)
  - JSONL append-only format (proven in STRATEGY_LEDGER, FINANCE_LEDGER, BODY_LEDGER)
  - Persona JSON structure (`HIKMAH.json`, `TARIQ.json` define tone/operating_rules)
  - Privacy enforcement via SYNC_POLICY + HIMAYAH gate (proven in BADAN, MAL, TARIQ modules)
  - MAKHZAN snapshot pattern for schema evolution (CONTINUITY_PROTOCOL §)

### Secondary (MEDIUM confidence)

- **Roadmap + State** — `/d/nizam/.planning/ROADMAP.md`, `STATE.md`, `REQUIREMENTS_v1.1.md`
  - Phase 14–20 dependencies clearly sequenced
  - Success criteria explicit for Phase 14 (schema defined, local storage, versioning, valid test index)
  - Integration points documented (Phase 15 refresh, Phase 16 message generation, Phase 17 delivery)

- **Existing research** — `/d/nizam/.planning/phases/01-foundation-data-model/01-RESEARCH.md`
  - Phase 1 research pattern shows successful use of NIZAM naming convention, module structure, PRIVACY_CLASSIFICATION registration
  - Demonstrates stdlib-only approach (no new dependencies)

### Tertiary (validation opportunities)

- **Google Drive conversation logs format** — NOT researched yet; flagged as Phase 15 research gap
- **Telegram relay response polling API** — exists (Hermes plugin active); exact schema deferred to Phase 17
- **Cross-pillar signal schemas (MUNAWARA/MAL/TARIQ)** — sketched in REQUIREMENTS_v1.1.md; details in Phase 19 research

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| **Standard stack** | HIGH | All dependencies are NIZAM stdlib-proven (json, pathlib, uuid, hashlib, datetime); no new packages required |
| **Architecture** | HIGH | Module structure mirrors MARSAD/TARIQ pattern; ledger schema mirrors EVENT_LEDGER; privacy enforcement proven in BADAN/MAL/TARIQ |
| **Schema design** | HIGH | Grounded in Phase 15–20 requirements; context_tags whitelist prevents PII; version field enables evolution |
| **Versioning** | HIGH | MAKHZAN snapshot pattern proven in CONTINUITY_PROTOCOL; schema versioning standard practice |
| **Storage & privacy** | HIGH | SYNC_POLICY classification tested in 3+ modules; strict_local enforcement via HIMAYAH gate; .gitignore patterns proven |
| **Integration points** | MEDIUM | Phases 15–20 clearly defined; specific data formats (Drive logs, message_id storage) flagged for downstream research |
| **Pitfalls** | MEDIUM | Grounded in NIZAM data governance (PII leakage, schema drift, cross-module pollution); activity history growth inferred from NIZAM scale |

**Research date:** 2026-06-20  
**Valid until:** 2026-07-20 (30 days; NIZAM system is stable, schema is foundational and unlikely to change)

---

## Recommendations for Planner

1. **Module naming is HIKMAH__knowledge_index** — aligns with NIZAM pattern, puts index under Khaldun's (synthesist) remit
2. **Single shared PERSONA_KNOWLEDGE_INDEX ledger** — simpler than per-persona ledgers; keyed by persona_name for flexibility
3. **Per-persona JSON files in `indices/` directory** — separate files prevent cross-contamination; enable per-persona versioning if needed later
4. **Context tags whitelist enforced at write-time** — prevents PII creep; validation in Phase 14 Wave 1
5. **Activity history cleanup task deferred to Phase 15** — keep current indices lean; archive to MAKHZAN; Phase 15 refresh can clean up during data sync
6. **No breaking schema changes in v1.1** — keep version at "1.0" for Phase 14; future v1.1+ can add optional fields (backward-compatible)
7. **Test all 11 personas in Wave 3** — verify initialization works for every persona; prevent persona-specific bugs in Phase 16
8. **Privacy audit in Phase 20** — Phase 14 creates schema; Phase 20 audits instances (no raw PII in created files)
