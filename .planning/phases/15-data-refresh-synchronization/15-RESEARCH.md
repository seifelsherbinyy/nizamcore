# Phase 15: Data Refresh & Synchronization - Research

**Researched:** 2026-06-20  
**Domain:** Google Drive API integration + index refresh + graceful degradation + audit logging  
**Confidence:** HIGH (Core APIs verified via Context7, project patterns established in Phase 14)

## Summary

Phase 15 must implement a data refresh system that reads conversation logs and activity snapshots from Google Drive, merges new activity into per-persona knowledge indices (Phase 14), and gracefully falls back to cached indices if Drive is unavailable. The system must log all refresh attempts with full audit trail (source, timestamp, success/failure status) to support troubleshooting and compliance.

This phase bridges Phase 14 (index storage) and Phase 16 (message generation), enabling Phase 16 to work with fresh user context pulled from Drive.

**Primary recommendation:** Use `google-api-python-client` with service account credentials (available in secrets) for Drive access; implement retry logic with exponential backoff; always log refresh outcomes to ledger regardless of success/failure; never silently degrade to cached index without audit entry.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `google-api-python-client` | 1.12+ | Google Drive API client (v3) | Official, maintained, discovery-based, 348K code snippets in Context7 |
| `google-auth` | 2.20+ | Service account credentials + token refresh | Official Google auth, built-in RefreshError handling, async support |
| `google-auth-oauthlib` | 1.0+ | OAuth 2.0 flow (future user-facing refresh) | Supports service account + user OAuth flows, integrates with google-api-python-client |
| `python-dateutil` | 2.8+ | ISO 8601 timestamp parsing + timezone handling | Standard in ecosystem, handles timezone-aware comparisons for activity freshness |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `requests` | 2.28+ | HTTP retry logic wrapper (alternative to google-api-python-client built-in) | Already in hermes-venv; use google-api-python-client's built-in retry first |
| `tenacity` | 8.2+ | Advanced retry library (exponential backoff + jitter) | Use if google-api-python-client's retry insufficient; enables custom backoff strategies |

### Already Installed
- `google-api-python-client`: Confirmed in `.venv/Lib/site-packages/googleapiclient/`
- `google-auth`: Available (confirmed by Context7 discovery)
- `python-dateutil`: Standard library supplement (widely available)

**No new installation required for Phase 15 core functionality; tenacity optional for advanced retry strategies.**

---

## Architecture Patterns

### Recommended Project Structure
```
HIKMAH__knowledge_index/
├── refresh/                       # Data refresh pipeline (NEW)
│   ├── __init__.py
│   ├── drive_client.py            # Google Drive API wrapper
│   ├── merge_strategy.py           # Activity merge logic (don't overwrite stalled/completed)
│   ├── ledger_writer.py            # Refresh audit logging
│   └── tests/
│       ├── test_drive_client.py
│       ├── test_merge_strategy.py
│       └── test_refresh_fallback.py
├── indices/                        # Per-persona indices (Phase 14)
├── index/                          # Core schema + initialization
│   ├── schema.py
│   ├── versioning.py
│   └── main.py
└── REFRESH_AUDIT_LEDGER.jsonl     # NEW: Audit trail for refresh operations
```

### Pattern 1: Google Drive API Client with Credentials

**What:** Encapsulate Drive API interactions into a reusable client that handles authentication, querying, and error cases.

**When to use:** Every refresh operation reads from Drive; need centralized credential management and retry logic.

**Example:**
```python
# Source: google-api-python-client Context7 + Phase 14 writer.py pattern
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from pathlib import Path

class GoogleDriveClient:
    """Wraps Google Drive API v3 with credential management and error handling."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, credentials_path: Path):
        """Initialize with service account credentials."""
        try:
            credentials_info = json.loads(credentials_path.read_text())
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Failed to load credentials: {e}")
    
    def find_folder_by_name(self, folder_name: str, parent_id: str = None) -> str:
        """Find folder ID by name. Returns folder_id or None if not found."""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except HttpError as e:
            raise IOError(f"Drive query failed: {e.resp.status} {e.content}")
    
    def list_files_in_folder(self, folder_id: str, file_type: str = None) -> list:
        """List files in folder, optionally filtered by MIME type."""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            if file_type == 'json':
                query += " and mimeType='application/json'"
            elif file_type == 'text':
                query += " and mimeType='text/plain'"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, modifiedTime, mimeType)',
                pageSize=100
            ).execute()
            
            return results.get('files', [])
        except HttpError as e:
            raise IOError(f"Failed to list folder contents: {e.resp.status}")
    
    def download_file_content(self, file_id: str) -> str:
        """Download file content as string."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            return content.decode('utf-8') if isinstance(content, bytes) else content
        except HttpError as e:
            raise IOError(f"Failed to download file {file_id}: {e.resp.status}")
```

### Pattern 2: Graceful Fallback with Audit Logging

**What:** On Drive unavailability, return cached index AND log the degradation event to audit ledger.

**When to use:** Every refresh attempt must be logged (success AND failure); operator needs visibility into when system is stale.

**Example:**
```python
# Source: Phase 14 ledger writer pattern + error handling best practices
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib

class RefreshAuditLogger:
    """Logs all refresh attempts (success/failure) to REFRESH_AUDIT_LEDGER.jsonl."""
    
    def __init__(self, ledger_path: Path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_refresh_attempt(self, persona: str, status: str, data_sources: list, error: str = None, files_read: int = 0):
        """
        Append refresh attempt record to audit ledger.
        
        Args:
            persona: Persona being refreshed (e.g., "AMMAR")
            status: "success" | "failure" | "partial"
            data_sources: List of Drive folders/files accessed (e.g., ["YAWMIYAT/sessions", "YAWMIYAT/mirrors"])
            error: Exception message if status != "success"
            files_read: Number of files successfully read
        """
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "persona": persona,
            "event_type": "refresh_attempt",
            "status": status,
            "data_sources": data_sources,
            "files_read": files_read,
            "error": error,
        }
        
        # Compute hash for integrity (following Phase 14 pattern)
        entry_json = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        entry['row_hash'] = hashlib.sha256(entry_json.encode()).hexdigest()
        
        # Append to ledger (JSONL format)
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_last_successful_refresh(self, persona: str) -> dict:
        """Retrieve timestamp of last successful refresh for this persona."""
        if not self.ledger_path.exists():
            return None
        
        last_success = None
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                if entry.get('persona') == persona and entry.get('status') == 'success':
                    last_success = entry
        
        return last_success


def refresh_persona_index_with_fallback(persona: str, drive_client, index_path: Path, audit_logger):
    """
    Attempt to refresh index from Drive. On failure, use cached index and log degradation.
    
    Returns: (success: bool, index: dict, degradation_reason: str or None)
    """
    degradation_reason = None
    
    try:
        # Step 1: Query Drive for conversation logs and activity snapshots
        conversation_logs = drive_client.find_folder_by_name("YAWMIYAT/sessions")
        if not conversation_logs:
            raise IOError("YAWMIYAT/sessions folder not found on Drive")
        
        activity_files = drive_client.list_files_in_folder(conversation_logs, file_type='json')
        files_read = len(activity_files)
        
        # Step 2: Merge new activity into index (see Pattern 3)
        index = load_cached_index(index_path)
        for file_info in activity_files:
            content = drive_client.download_file_content(file_info['id'])
            activity_data = json.loads(content)
            index = merge_activity_into_index(index, activity_data, persona)
        
        # Step 3: Log success
        audit_logger.log_refresh_attempt(
            persona=persona,
            status="success",
            data_sources=["YAWMIYAT/sessions"],
            files_read=files_read
        )
        
        return (True, index, None)
    
    except Exception as e:
        # Fallback to cached index + log degradation
        degradation_reason = str(e)
        cached_index = load_cached_index(index_path)
        
        audit_logger.log_refresh_attempt(
            persona=persona,
            status="failure",
            data_sources=["YAWMIYAT/sessions"],
            error=degradation_reason,
            files_read=0
        )
        
        return (False, cached_index, degradation_reason)
```

### Pattern 3: Activity Merge Strategy (Don't Overwrite Stalled/Completed)

**What:** New activity from Drive is merged into the index carefully to preserve stalled work and completion tracking.

**When to use:** During refresh, need to update `topics[].last_activity`, `activity_history` while preserving `stalled_work[]` and `completions[]`.

**Example:**
```python
# Source: Phase 14 schema.py + merge best practices
from datetime import datetime, timezone
from typing import Optional
import uuid

def merge_activity_into_index(index: dict, activity_data: dict, persona: str) -> dict:
    """
    Merge new activity from Drive into persona index.
    
    Rules:
    1. New topics: Add to topics[] with status "active"
    2. Existing topics: Update last_activity timestamp only if newer
    3. Completed topics: Preserve in completions[]; DO NOT move back to topics[]
    4. Stalled work: Update stalled_work[].days_stalled, but preserve original stalled_since
    5. Activity history: Append new events in chronological order
    
    Args:
        index: Current persona index (from cached file)
        activity_data: New activity from Drive (expected keys: "topics", "accomplishments", "blockers")
        persona: Persona identifier for validation
    
    Returns: Updated index dict with validation
    """
    
    # Step 1: Merge new topics
    existing_topic_ids = {t['id'] for t in index.get('topics', [])}
    for new_topic in activity_data.get('topics', []):
        if new_topic.get('id') not in existing_topic_ids:
            # Add new topic (ensure required fields)
            index['topics'].append({
                'id': new_topic.get('id', str(uuid.uuid4())),
                'name': new_topic['name'],
                'status': 'active',
                'created_at': new_topic.get('created_at', datetime.now(timezone.utc).isoformat()),
                'last_activity': new_topic.get('last_activity', datetime.now(timezone.utc).isoformat()),
                'context_tags': new_topic.get('context_tags', []),
                'confidence': new_topic.get('confidence', 0.5),
                'key_accomplishments': new_topic.get('key_accomplishments', []),
                'blockers': new_topic.get('blockers', []),
                'notes': new_topic.get('notes', '')
            })
    
    # Step 2: Update last_activity for existing topics (only if newer)
    for existing_topic in index.get('topics', []):
        for new_topic in activity_data.get('topics', []):
            if existing_topic['id'] == new_topic.get('id'):
                new_ts = new_topic.get('last_activity', existing_topic['last_activity'])
                if new_ts > existing_topic['last_activity']:
                    existing_topic['last_activity'] = new_ts
    
    # Step 3: Append new activity events (DO NOT overwrite history)
    for event in activity_data.get('accomplishments', []):
        index['activity_history'].append({
            'ts': event.get('ts', datetime.now(timezone.utc).isoformat()),
            'event_type': 'accomplishment_logged',
            'topic_id': event.get('topic_id'),
            'description': event.get('description', '')
        })
    
    # Step 4: Update index timestamp
    index['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Step 5: Validate schema integrity (prevents corrupted merges)
    from schema import validate_index_schema
    valid, error_msg = validate_index_schema(index)
    if not valid:
        raise ValueError(f"Merged index violates schema: {error_msg}")
    
    return index
```

### Anti-Patterns to Avoid

- **Silent degradation without logging:** Never fall back to cached index without appending an audit entry. Operator must know index is stale.
- **Overwriting stalled_work or completions on refresh:** New activity should update last_activity timestamps, not move completed items back to active. Preserve tracker integrity.
- **Blocking message generation on refresh failure:** If Drive is unavailable, Phase 16 should still generate messages using cached index. Degradation is logged; message generation continues.
- **Hardcoding folder names/IDs:** Use configurable paths (e.g., config.yaml) for Drive folder names so operator can adjust without code changes.
- **No retry on transient errors:** Network timeouts or rate-limiting are temporary; retry with exponential backoff (not immediate failure).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Google Drive API authentication | Custom OAuth2 flow | `google-auth` service account credentials | Edge cases (token expiration, refresh, scopes) are complex; google-auth handles them. Custom implementation will leak secrets or fail silently. |
| Parsing JSON from Drive files | Regex or manual parsing | Python's `json` module | JSON parsing has numerous edge cases (Unicode, escape sequences, nested structures). stdlib handles all. |
| Retry logic on network failures | Simple try/except with sleep loop | `google-api-python-client` built-in retry (or `tenacity`) | Exponential backoff with jitter, deadline-aware, idempotency handling — hand-rolled is error-prone. |
| Timestamp comparison across timezones | String comparison or manual parsing | `python-dateutil.parser` + `datetime.timezone.utc` | Timezone offsets are subtle; dateutil handles parsing + comparison correctly. |
| Audit trail integrity | Append events to list in memory | JSONL ledger with hash chaining (Phase 14 pattern) | In-memory logs are lost on crash. Append-only ledger + hash chaining ensures durability + detects tampering. |

**Key insight:** Drive integration is deceptively complex — rate limiting, partial failures, stale tokens, transient network errors all require robust handling. Lean on official libraries.

---

## Common Pitfalls

### Pitfall 1: Uncaught Credential Errors Blocking Entire Message Generation

**What goes wrong:** `google-auth` raises `RefreshError` when token can't be refreshed. If not caught, message generation (Phase 16) hangs or crashes.

**Why it happens:** Service account key may be rotated, Drive permissions revoked, or network unavailable during token refresh. Code doesn't expect this.

**How to avoid:** Always wrap Drive API calls in try/except, catching `google.auth.exceptions.RefreshError`, `google.auth.exceptions.TransportError`, and `googleapiclient.errors.HttpError`. On any error, log to audit ledger and return cached index.

**Warning signs:** Test with revoked service account key; verify message generation still works (uses cached index). Phase 17 delivery should not hang.

### Pitfall 2: Overwriting Stalled Work During Merge

**What goes wrong:** New activity from Drive shows a topic is "active" again (user working on it). Merge naively updates `topics[].status` from "paused" to "active", losing the fact that this topic was blocked for 2 weeks.

**Why it happens:** Developer assumes "latest activity = current status" without checking if the topic is in stalled_work[].

**How to avoid:** When merging, check if topic_id exists in stalled_work[]. If it does, only update `last_activity` timestamp; DO NOT change `status`. stalled_work[] is a separate audit trail.

**Warning signs:** Phase 18 (adaptation) shows stalled_work[] being reset incorrectly. Manual index inspection shows topics with "active" status but stalled_since timestamps months old.

### Pitfall 3: No Audit Trail for Successful Refreshes

**What goes wrong:** Operator can't tell if index is 1 hour stale or 1 week stale. No refresh_audit ledger, so troubleshooting is blind.

**Why it happens:** Developer logs failures but skips success logging ("it's just cache validation, not important").

**How to avoid:** ALWAYS log refresh attempts, success or failure, with timestamp and data sources. Operator queries ledger to find: "Last successful refresh: 2026-06-20T10:30:00Z. Last attempt: 2026-06-20T18:00:00Z (failed: network timeout)."

**Warning signs:** Operator asks "when was the index last updated?" and code has no answer.

### Pitfall 4: Partial Failures Silently Dropped

**What goes wrong:** Drive has 5 conversation log files. First 4 read successfully, but file #5 fails (corrupted JSON). Code returns "failure" status but has already written files 1-4 into the index. Merge is half-done, index is inconsistent.

**Why it happens:** No transactional semantics; file writes are not atomic.

**How to avoid:** Validate ALL files from Drive before merging any. If any file fails validation, return error WITHOUT modifying index. On success, merge all at once. For large batches, consider staging to a temp index, validate, then swap.

**Warning signs:** Index has gaps (activity history jumps from 2026-06-19 to 2026-06-21). Test with a malformed JSON file in Drive; verify entire refresh is rejected.

### Pitfall 5: Hardcoded Drive Folder Paths

**What goes wrong:** Code says `find_folder_by_name("YAWMIYAT/sessions")`. Operator wants to reorganize Drive (rename folder to "2026-conversations"). Code breaks.

**Why it happens:** Developer put folder path in code instead of config.

**How to avoid:** Store Drive folder names in a config file (e.g., `refresh_config.yaml`):
```yaml
data_refresh:
  conversation_logs_folder: "YAWMIYAT/sessions"
  activity_snapshots_folder: "YAWMIYAT/daily_snapshots"
  max_files_per_refresh: 100
  timeout_seconds: 30
```

Then load config at runtime. Operator can change without code edit.

**Warning signs:** Folder renames cause immediate failures. Test by moving folder on Drive; verify code detects and handles gracefully (with error message pointing to config).

---

## Code Examples

Verified patterns from official sources:

### Google Drive Query Syntax
```python
# Source: google-api-python-client Context7 docs
# Find a folder by name in Drive root
service.files().list(
    q="name='YAWMIYAT/sessions' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    spaces='drive',
    fields='files(id, name)',
    pageSize=10
).execute()

# Find files in a specific folder, modified after a date
service.files().list(
    q="'<folder_id>' in parents and modifiedTime > '2026-06-19T00:00:00Z' and trashed=false",
    spaces='drive',
    fields='files(id, name, modifiedTime, size)',
    pageSize=100,
    orderBy='modifiedTime desc'  # Newest first
).execute()

# Find JSON files only
service.files().list(
    q="name contains '.json' and mimeType='application/json'",
    spaces='drive',
    fields='files(id, name)',
).execute()
```

### Service Account Credential Loading
```python
# Source: google-auth Context7 + Phase 14 writer.py pattern
from google.oauth2 import service_account
import json
from pathlib import Path

credentials_path = Path('NIZAM-secrets.json')
try:
    credentials_info = json.loads(credentials_path.read_text())
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    raise RuntimeError(f"Failed to load credentials: {e}")
```

### Error Handling with Retry
```python
# Source: google-auth + google-api-python-client Context7
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError, TransportError
from datetime import datetime, timezone
import time

def query_drive_with_retry(service, query_fn, max_retries=3, backoff_base=2):
    """Execute Drive query with exponential backoff retry logic."""
    attempt = 0
    
    while attempt < max_retries:
        try:
            return query_fn(service), True, None
        except (RefreshError, TransportError) as e:
            # Transient error: auth or network issue
            attempt += 1
            if attempt < max_retries:
                wait_time = backoff_base ** attempt
                print(f"Transient error on attempt {attempt}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return None, False, f"Transient error after {max_retries} retries: {e}"
        except HttpError as e:
            # HTTP 4xx/5xx error
            if e.resp.status in [429, 500, 503]:  # Rate limit, server error
                attempt += 1
                if attempt < max_retries:
                    wait_time = backoff_base ** attempt
                    print(f"HTTP {e.resp.status} on attempt {attempt}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return None, False, f"HTTP {e.resp.status} after {max_retries} retries"
            else:
                # Permanent error (auth failure, not found, etc.)
                return None, False, f"HTTP {e.resp.status}: {e.content}"
        except Exception as e:
            # Unexpected error
            return None, False, f"Unexpected error: {type(e).__name__}: {e}"
    
    return None, False, "Unknown failure"
```

### Audit Ledger Structure (JSONL)
```json
{"ts": "2026-06-20T10:30:00Z", "persona": "AMMAR", "event_type": "refresh_attempt", "status": "success", "data_sources": ["YAWMIYAT/sessions"], "files_read": 5, "error": null, "row_hash": "abc123..."}
{"ts": "2026-06-20T11:00:00Z", "persona": "HIKMAH", "event_type": "refresh_attempt", "status": "failure", "data_sources": ["YAWMIYAT/sessions"], "files_read": 0, "error": "HTTP 401: Unauthorized", "row_hash": "def456..."}
{"ts": "2026-06-20T12:30:00Z", "persona": "TARIQ", "event_type": "refresh_attempt", "status": "partial", "data_sources": ["YAWMIYAT/sessions"], "files_read": 3, "error": "Stopped after 3 files due to rate limit", "row_hash": "ghi789..."}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual Drive folder exploration to find logs | Query Drive API with `q` parameter filtering by folder name + mimeType | REST API standardized (2012+) | Automated refresh possible; no manual folder navigation |
| OAuth 2.0 user flow (requires user browser login) | Service account credentials with .json key | Service accounts standardized (2010+) | Unattended refresh possible; no interactive auth |
| Synchronous blocking API calls | google-api-python-client with built-in async support (optional) | Context7 confirms async patterns available | Phase 16+ can implement non-blocking message generation if Drive is slow |
| Generic error messages ("API call failed") | Specific error types (RefreshError, HttpError with status code) | google-auth library design (2016+) | Operator can distinguish transient vs. permanent failures; retry logic can be precise |

**Deprecated/outdated:**
- **Using user OAuth flow for unattended refresh:** Service account credentials now standard for server-to-server integrations. User OAuth is for user-facing (interactive) features only.
- **Hardcoding folder IDs:** Query by folder name now preferred (survives folder moves). IDs only used when folder name is ambiguous.
- **Synchronous-only Drive access:** google-api-python-client supports async patterns (Hermes agent can use this for non-blocking operations in Phase 17+).

---

## Open Questions

1. **Google service account credentials location and format**
   - What we know: Project secrets stored in `D:\NIZAM\NIZAM-secrets.json` (free-text register, not structured JSON). rclone-crypt uses this for Drive access.
   - What's unclear: Does a Google service account JSON key exist? Is it in NIZAM-secrets.json or separate file? Who has permission to generate a new key if needed?
   - Recommendation: Operator confirms: (a) service account email (e.g., `nizam-refresh@nizam-prod.iam.gserviceaccount.com`), (b) key JSON location, (c) Drive folder IDs for YAWMIYAT/sessions and YAWMIYAT/daily_snapshots. Phase planning will extract to config.yaml.

2. **Drive folder structure for conversation logs**
   - What we know: Phase 14 README mentions "Phase 15 will read Drive logs and merge activity" but doesn't specify folder path or file format.
   - What's unclear: Are conversation logs in YAWMIYAT/sessions/? Are they Markdown, JSON, or Google Docs? What's the schema (topics, timestamps, accomplishments)?
   - Recommendation: Phase 15 planning includes sample file fetch from Drive to document exact format. Task 15-01 (Drive client setup) should succeed with real folder access before 15-02 (merge logic).

3. **Activity snapshot schema from Drive**
   - What we know: Index schema defines expected fields (topics[], activity_history[], stalled_work[]). Drive files must be mapped to these.
   - What's unclear: Do Drive files have a fixed format (e.g., YAWMIYAT conversation session schema from Phase 2)? Or free-form? How does refresher know which fields to extract?
   - Recommendation: Document mapping during planning: "Drive conversation log field 'accomplishment' → index activity_history event with event_type='accomplishment_logged'". Create a dedicated schema converter function if mapping is complex.

4. **Network timeout and rate-limiting thresholds**
   - What we know: Phase 16 needs fresh index before message generation; Phase 16 has Hermes cron schedule (09:00 & 18:00 Cairo). Refresh must complete before message generation starts.
   - What's unclear: How long can refresh take? If Drive is rate-limiting, should refresh timeout (e.g., 30 seconds) and fall back to cache? Or retry indefinitely?
   - Recommendation: Set refresh_timeout in config (e.g., 30 seconds). If Drive query exceeds timeout, log to audit trail and fall back to cached index. Phase 16 can proceed with potentially stale data.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (v7.0+) with google-api-python-client mocking (unittest.mock + Mock Drive service) |
| Config file | `.planning/phases/15-data-refresh-synchronization/conftest.py` (Phase 15 shared fixtures) |
| Quick run command | `pytest HIKMAH__knowledge_index/refresh/tests/ -v -k "not integration"` |
| Full suite command | `pytest HIKMAH__knowledge_index/refresh/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REFRESH-01 | Refresh reads conversation logs and activity snapshots from Google Drive (correct folder, correct file types) | integration | `pytest HIKMAH__knowledge_index/refresh/tests/test_drive_client.py::test_find_folder_by_name -v` | ❌ Wave 0 |
| REFRESH-02 | New activity from Drive is merged into local index without overwriting stalled/completed tracking | unit | `pytest HIKMAH__knowledge_index/refresh/tests/test_merge_strategy.py::test_merge_preserves_stalled_work -v` | ❌ Wave 0 |
| REFRESH-03 | If Drive unavailable, system falls back to cached index and logs degradation (audit entry with timestamp) | unit | `pytest HIKMAH__knowledge_index/refresh/tests/test_refresh_fallback.py::test_fallback_on_network_error -v` | ❌ Wave 0 |
| (Implicit) | Every refresh logs data sources read, timestamps, and success/failure status (audit trail) | unit | `pytest HIKMAH__knowledge_index/refresh/tests/test_audit_logging.py::test_audit_ledger_appended -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest HIKMAH__knowledge_index/refresh/tests/ -v -k "not integration"` (unit tests only, < 5 sec)
- **Per wave merge:** `pytest HIKMAH__knowledge_index/refresh/tests/ -v` (includes mocked integration tests, ~15 sec)
- **Phase gate:** Full suite green + manual spot-check: operator runs `pytest ... -v --tb=short` and verifies audit ledger entries before mark-done

### Wave 0 Gaps
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_drive_client.py` — mocked Drive API queries, credential loading, error handling
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_merge_strategy.py` — activity merge logic, stalled_work preservation, validation
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_refresh_fallback.py` — graceful degradation on Drive errors, cached index fallback
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_audit_logging.py` — audit ledger JSONL append, success/failure logging
- [ ] `HIKMAH__knowledge_index/refresh/__init__.py` — public API (refresh_persona_index, load_cached_index, etc.)
- [ ] `HIKMAH__knowledge_index/refresh/drive_client.py` — Google Drive API wrapper with retry logic
- [ ] `HIKMAH__knowledge_index/refresh/merge_strategy.py` — Activity merge with stalled_work preservation
- [ ] `HIKMAH__knowledge_index/refresh/ledger_writer.py` — Audit trail JSONL appender
- [ ] `HIKMAH__knowledge_index/tests/conftest.py` — Shared pytest fixtures (MockDriveService, sample indices, mock credentials)

---

## Sources

### Primary (HIGH confidence)
- `/googleapis/google-api-python-client` - Google Drive API v3 file listing, querying, content retrieval (Context7)
- `/googleapis/google-auth-library-python` - Service account credentials, token refresh, error handling (Context7)
- `D:\NIZAM\HIKMAH__knowledge_index\index\schema.py` - PersonaIndexDict schema + validation (Phase 14 verified code)
- `D:\NIZAM\HIKMAH__knowledge_index\index\writer.py` - Ledger JSONL append-only pattern with hash chaining (Phase 14 verified code)
- `D:\NIZAM\.planning\ROADMAP.md` - Phase 15 requirements and success criteria (project specification)

### Secondary (MEDIUM confidence)
- `D:\NIZAM\NIZAM__system\docs\DATA_MODEL.md` - NIZAM artifact types, ledger structure, privacy classifications
- `D:\NIZAM\NIZAM__system\docs\CONTINUITY_PROTOCOL.md` - MAKHZAN snapshot pattern, cross-session ledger consistency

### Tertiary (LOW confidence)
- Project memory `nizam-hermes-deployment-env.md` (20 days old, credentials/paths may have changed)

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - google-api-python-client and google-auth are official, mature, verified via Context7 with 348K+ code examples
- Architecture: **HIGH** - Patterns derived from Phase 14 verified code (writer.py ledger structure) + official Google docs
- Pitfalls: **MEDIUM** - Identified from Context7 API docs + common Drive integration issues; not validated against this specific codebase yet
- Error handling: **HIGH** - google-auth exception types and retry patterns verified via Context7

**Research date:** 2026-06-20  
**Valid until:** 2026-07-04 (14 days; Google APIs stable, low change risk)  
**Revisit if:** Service account credentials format differs from assumption, or Drive folder structure is different than Phase 15 discovery reveals

---

*Document Version: 1.0*  
*Phase: 15 (Data Refresh & Synchronization)*  
*Classification: NIZAM Internal — Planning artifact*
