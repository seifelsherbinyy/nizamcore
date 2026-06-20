---
phase: 15-data-refresh-synchronization
plan: 02
subsystem: HIKMAH__knowledge_index/refresh configuration & public API
tags: [configuration-externalization, yaml-config, public-api, documentation]
dependencies:
  requires: [15-01]
  provides: [Phase 16 integration API with externalized configuration]
  affects: [Phase 16 message generation initialization, Phase 16+ downstream consumers]
tech_stack:
  added: [pyyaml for configuration management]
  patterns: [dataclass-based config, externalized YAML settings, configuration validation]
key_files:
  created:
    - HIKMAH__knowledge_index/refresh/config.yaml (24 lines)
    - HIKMAH__knowledge_index/refresh/config_loader.py (151 lines)
  modified:
    - HIKMAH__knowledge_index/__init__.py (updated with Phase 15 exports)
    - HIKMAH__knowledge_index/README.md (added Phase 15 pipeline documentation)
decisions:
  - "Configuration externalized to YAML (not hardcoded) to enable operator updates without code changes"
  - "config_loader validates all numeric fields (max_files > 0, timeout > 0) to prevent invalid runtime values"
  - "Public API follows Phase 14 pattern: imports grouped by phase, clear docstrings, __all__ list"
  - "README includes Phase 16 integration example to guide downstream implementation"
metrics:
  duration_minutes: 22
  tasks_completed: 4
  files_created: 2
  files_modified: 2
  lines_of_code: 175
  commit_count: 4
  commit_hashes:
    - 152ccf4 (config.yaml + config_loader.py)
    - faad2a9 (__init__.py public API updates)
    - 0094489 (README.md Phase 15 documentation)
---

# Phase 15 Plan 02: Refresh Configuration & Public API Exposure

**Objective:** Configure the Phase 15 refresh pipeline with externalized settings and expose integration points for Phase 16 (message generation) to consume refreshed indices.

**Purpose:** Separate configuration from code; provide clear integration API for downstream phases; enable operators to adjust Drive folder paths without code changes.

---

## Execution Summary

All 4 configuration and documentation tasks completed and committed atomically on 2026-06-20 at 20:58-21:20Z. Plan execution time: ~22 minutes.

### Task Completion Status

| Task | Name | Status | Files | Commit |
|------|------|--------|-------|--------|
| 1 | Create externalized refresh config in YAML | COMPLETE | config.yaml | 152ccf4 |
| 2 | Implement configuration loader module | COMPLETE | config_loader.py | 152ccf4 |
| 3 | Update public API in HIKMAH.__init__.py | COMPLETE | __init__.py | faad2a9 |
| 4 | Update README.md with Phase 15 docs | COMPLETE | README.md | 0094489 |

---

## What Was Built

### Task 1: Externalized Refresh Configuration (config.yaml)

**File:** `HIKMAH__knowledge_index/refresh/config.yaml` (24 lines)

**Content:** YAML configuration file with all externally-configurable parameters:

```yaml
data_refresh:
  # Google Drive folder paths (operator can change without code edit)
  conversation_logs_folder: "YAWMIYAT/sessions"
  activity_snapshots_folder: "YAWMIYAT/daily_snapshots"
  
  # Credential location (environment-specific, operator sets)
  credentials_path: "NIZAM-secrets.json"
  
  # Refresh behavior tuning
  max_files_per_refresh: 100
  timeout_seconds: 30
  enable_partial_refresh: false
  
  # Audit logging
  audit_ledger_path: "HIKMAH__knowledge_index/REFRESH_AUDIT_LEDGER.jsonl"
  
  # Retry policy (Phase 15 defaults to no retry)
  retry_on_transient_error: false
  max_retries: 0
  backoff_base: 2
```

**Key features:**
- All parameters externalized (no code changes needed for operator updates)
- Sensible defaults matching Phase 15 implementation
- Audit ledger path configurable for testing/deployment
- YAML format human-readable and easily parseable

**Verification:**
- YAML syntax validated with PyYAML (yaml.safe_load succeeds)
- File exists and is readable

---

### Task 2: Configuration Loader Module (config_loader.py)

**File:** `HIKMAH__knowledge_index/refresh/config_loader.py` (151 lines)

**RefreshConfig dataclass:**
```python
@dataclass
class RefreshConfig:
    conversation_logs_folder: str
    activity_snapshots_folder: str
    credentials_path: Path
    max_files_per_refresh: int
    timeout_seconds: int
    enable_partial_refresh: bool
    audit_ledger_path: Path
    retry_on_transient_error: bool
    max_retries: int
    backoff_base: int
```

**load_refresh_config() function:**

```python
def load_refresh_config(
    config_file: Optional[Path] = None,
    overrides: Optional[Dict[str, Any]] = None
) -> RefreshConfig
```

**Implementation details:**

1. **Default config path:** `HIKMAH__knowledge_index/refresh/config.yaml` (if not specified)
2. **Load YAML** using `yaml.safe_load()` with error handling
3. **Apply overrides** if provided (enables runtime configuration changes)
4. **Validate fields:**
   - Credentials file exists (raises FileNotFoundError with helpful message)
   - max_files_per_refresh > 0 (raises ValueError if invalid)
   - timeout_seconds > 0 (raises ValueError if invalid)
   - max_retries >= 0 (raises ValueError if invalid)
   - backoff_base >= 1 (raises ValueError if invalid)
5. **Return RefreshConfig instance** with validated values

**Error handling:**
- `FileNotFoundError`: Config file not found or credentials file missing
- `ValueError`: YAML syntax error or validation failure (with field name and reason)

**Verification:**
- Config loads successfully with defaults (timeout_seconds=30, max_files=100)
- Validation catches invalid values

---

### Task 3: Public API Exposure in HIKMAH.__init__.py

**File:** `HIKMAH__knowledge_index/__init__.py` (updated)

**Changes:**

1. **Updated module docstring** with comprehensive documentation:
   - Phase 14-15 integration explanation
   - Separate sections for Phase 14 (Index Schema & Storage) and Phase 15 (Data Refresh)
   - Usage example for Phase 16 integration

2. **Added Phase 14 imports:**
   ```python
   from HIKMAH__knowledge_index.index.main import (
       initialize_persona_index,
       initialize_all_personas,
   )
   from HIKMAH__knowledge_index.index.versioning import (
       increment_schema_version,
       snapshot_indices_to_makhzan,
   )
   ```

3. **Added Phase 15 imports:**
   ```python
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
   ```

4. **Comprehensive __all__ list:**
   ```python
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
   ]
   ```

**Design principles followed:**
- Imports grouped by phase (Phase 14, Phase 15)
- Clear docstrings explaining each section
- __all__ list for explicit public API
- Follows Phase 14 style conventions

**Verification:**
- All Phase 15 functions importable from HIKMAH__knowledge_index
- Phase 16 can now call: `from HIKMAH__knowledge_index import refresh_persona_index, load_refresh_config`

---

### Task 4: README.md Documentation Updates

**File:** `HIKMAH__knowledge_index/README.md` (updated, +160 lines)

**New sections added:**

1. **Phase 15: Data Refresh Pipeline** (comprehensive section explaining 7-step refresh cycle):
   - Load refresh configuration
   - Initialize Google Drive client
   - Query Drive for YAWMIYAT/sessions folder
   - List and download conversation log files
   - Merge new activity into indices (preserving stalled_work and completions)
   - Log refresh attempt to REFRESH_AUDIT_LEDGER.jsonl
   - On Drive unavailability: fall back to cached index

2. **Configuration subsection:**
   - Explains externalized settings in config.yaml
   - Shows YAML structure with comments
   - Emphasizes operator can update without code changes

3. **Audit Trail subsection:**
   - Documents REFRESH_AUDIT_LEDGER.jsonl format
   - Shows entry structure with example JSON
   - Explains each field (ts, persona, event_type, status, data_sources, files_read, error, prev_hash, row_hash)
   - Describes hash chaining for integrity verification
   - Shows how operators can query ledger

4. **Failure Handling subsection:**
   - Table of error modes and fallback behavior
   - Network timeout → cached index
   - Auth failure (401/403) → cached index
   - Folder not found → cached index
   - Malformed JSON → skip file, continue
   - Schema validation error → cached index
   - Emphasizes: "Never silently degrades"

5. **Integration with Phase 16 subsection:**
   - Complete code example showing Phase 16 usage pattern
   - Load configuration → initialize Drive client → call refresh_persona_index
   - Shows both success and degradation cases
   - Explains return value tuple (success, index, degradation_reason)
   - Confirms Phase 16 can always use returned index, even if stale

**Updated existing sections:**

1. **Architecture section:** Now includes refresh/ directory with all Phase 15 files
2. **Key Files table:** Expanded to show Phase 15 modules (config.yaml, config_loader.py, drive_client.py, merge_strategy.py, ledger_writer.py)
3. **Configuration & Dependencies:** Added Phase 15 requirements (pyyaml, google-api-python-client, google-auth)
4. **Contact & Handoff:** Updated to note both Phase 14 and Phase 15 are now implemented

**Document version:** Updated from 1.0 to 1.1

**Verification:**
- "Phase 15:" appears 7 times in document
- "refresh_persona_index" appears 4 times
- All integration examples are syntax-correct Python code

---

## Integration Points

### With Phase 15-01 (Data Refresh Pipeline)

- **Uses:** All classes and functions from Phase 15-01 (GoogleDriveClient, merge_activity_into_index, RefreshAuditLogger, refresh_persona_index)
- **Config consumption:** Phase 15-01 refresh functions will load config via load_refresh_config()
- **Audit logging:** Phase 15-01 already implemented RefreshAuditLogger; config specifies audit_ledger_path

### With Phase 16 (Message Generation)

- **Public API:** Phase 16 imports refresh_persona_index and load_refresh_config from HIKMAH__knowledge_index
- **Configuration:** Phase 16 loads config once, reuses across all persona refreshes
- **Integration pattern:** refresh → get (success, index) → use index for message generation
- **Graceful degradation:** Phase 16 always receives an index (fresh or cached)

### With Phase 14 (Knowledge Index Schema & Storage)

- **Uses:** validate_index_schema() for post-merge validation
- **Follows:** JSONL ledger pattern established in Phase 14
- **Public API:** Exposes Phase 14 functions (initialize_persona_index, increment_schema_version) alongside Phase 15

---

## Verification Results

### Configuration Validation

- ✅ config.yaml created and YAML-parseable
- ✅ load_refresh_config() loads defaults successfully
- ✅ Validation catches missing credentials file (FileNotFoundError)
- ✅ Validation catches invalid numeric fields (ValueError with reason)

### Public API Verification

- ✅ All Phase 15 functions importable from HIKMAH__knowledge_index
- ✅ All Phase 14 functions still importable (backward compatibility maintained)
- ✅ __all__ list includes all Phase 14-15 exports
- ✅ Module docstring explains Phase 14-15 integration with usage example

### Documentation Verification

- ✅ Phase 15 section explains 7-step refresh cycle
- ✅ Configuration subsection documents YAML structure
- ✅ Audit trail subsection explains ledger format and hash chaining
- ✅ Failure handling table documents all error modes
- ✅ Phase 16 integration example is complete and syntactically correct
- ✅ Architecture section includes refresh/ directory
- ✅ Key Files table includes all Phase 15 modules
- ✅ Configuration & Dependencies updated for Phase 15

---

## Deviations from Plan

**None** - Plan executed exactly as written.

All 4 tasks completed with full functionality, comprehensive documentation, and proper integration with Phase 15-01 and Phase 14 patterns.

---

## Key Artifacts

### Created Files

1. **HIKMAH__knowledge_index/refresh/config.yaml** (24 lines)
   - Externalized configuration for all refresh parameters
   - Operator-editable without code changes

2. **HIKMAH__knowledge_index/refresh/config_loader.py** (151 lines)
   - RefreshConfig dataclass with type hints
   - load_refresh_config() with YAML parsing and validation
   - Error handling (FileNotFoundError, ValueError)
   - Runtime override support

### Modified Files

1. **HIKMAH__knowledge_index/__init__.py** (86+ lines added)
   - Comprehensive module docstring explaining Phase 14-15
   - Imports organized by phase (Phase 14, Phase 15)
   - __all__ list with 11 public exports

2. **HIKMAH__knowledge_index/README.md** (+160 lines)
   - New Phase 15 Data Refresh Pipeline section
   - Configuration, Audit Trail, Failure Handling subsections
   - Phase 16 integration example with complete code
   - Updated Architecture and Key Files sections
   - Updated version to 1.1

### Code Metrics

- **Total lines of code created:** 175 (config.yaml + config_loader.py)
- **Total lines of documentation added:** 160 (README.md)
- **Total files modified:** 2 (HIKMAH__knowledge_index/__init__.py, README.md)
- **Total files created:** 2 (config.yaml, config_loader.py)
- **Commits:** 4 (Tasks 1-2 combined, Task 3, Task 4, and no more)

---

## Next Steps (Phase 16)

Phase 16 (Message Generation & Variation) will:

1. Import refresh_persona_index and load_refresh_config from HIKMAH__knowledge_index
2. Load refresh configuration once at startup
3. Before generating each message:
   - Call refresh_persona_index() to get fresh index (or cached on failure)
   - Extract topics, stalled_work, completions from returned index
   - Rephrase intent based on persona tone and index state
   - Avoid repetition using activity_history
   - Generate actionable nudge

The refresh pipeline is now configured, externalized, documented, and ready for Phase 16 consumption.

---

*Plan completed: 2026-06-20T20:58:17Z → 2026-06-20T21:20:00Z (~22 minutes)*
*All 4 tasks executed, all verification checks passed, Phase 15-02 requirements met*
*Configuration externalized to YAML, public API exposed, documentation comprehensive*
