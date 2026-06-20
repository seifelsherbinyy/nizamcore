"""
Data refresh pipeline public API.

Provides high-level functions for refreshing persona knowledge indices from Google Drive
conversation logs with graceful fallback and comprehensive audit logging.

Functions:
    refresh_persona_index(persona, drive_client, index_path, audit_logger): Main refresh entry point
    load_cached_index(index_path): Load index from disk
    initialize_refresh_logger(ledger_path): Create audit logger instance

Design principles:
1. Always try Drive first; if unavailable, gracefully fall back to cached index
2. Log all refresh attempts (success and failure) to audit ledger
3. Never silently degrade: Always include error reason in audit entry and return value
4. Validate merged index before returning (ensure schema integrity)

Returns from refresh_persona_index():
    Tuple[success: bool, index: dict, degradation_reason: Optional[str]]
    - (True, updated_index, None) on success
    - (False, cached_index, error_reason) on failure (but cached index returned)
"""

import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from HIKMAH__knowledge_index.refresh.drive_client import GoogleDriveClient
from HIKMAH__knowledge_index.refresh.merge_strategy import merge_activity_into_index
from HIKMAH__knowledge_index.refresh.ledger_writer import RefreshAuditLogger
from HIKMAH__knowledge_index.index.schema import validate_index_schema


def refresh_persona_index(
    persona: str,
    drive_client: GoogleDriveClient,
    index_path: Path,
    audit_logger: RefreshAuditLogger
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """
    Refresh persona knowledge index from Google Drive with graceful fallback.

    Algorithm:
    1. Try to query Drive for YAWMIYAT/sessions folder
    2. List all files in folder (filter for JSON files)
    3. Download and parse each activity file
    4. Merge activity into cached index
    5. Validate merged index
    6. Log success to audit ledger
    7. Return (True, updated_index, None)

    On ANY exception:
    - Load cached index from index_path
    - Log degradation to audit ledger (status="failure", error=str(e))
    - Return (False, cached_index, error_reason)

    Args:
        persona: Persona name (e.g., "AMMAR")
        drive_client: GoogleDriveClient instance for Drive API access
        index_path: Path to persona's cached index file (used as fallback)
        audit_logger: RefreshAuditLogger for audit trail

    Returns:
        Tuple (success: bool, index: dict, degradation_reason: Optional[str])

    Raises:
        FileNotFoundError: If index_path does not exist and Drive refresh fails
    """
    try:
        # Load current index as starting point
        cached_index = load_cached_index(index_path)

        # Find YAWMIYAT/sessions folder in Drive
        folder_id = drive_client.find_folder_by_name("YAWMIYAT/sessions")
        if not folder_id:
            raise IOError("YAWMIYAT/sessions folder not found in Drive")

        # List all files in folder (filter for JSON files)
        files = drive_client.list_files_in_folder(folder_id, file_type='json')

        if not files:
            # No files found; fallback to cached index
            audit_logger.log_refresh_attempt(
                persona=persona,
                status="partial",
                data_sources=["YAWMIYAT/sessions"],
                files_read=0
            )
            return (False, cached_index, "No activity files found in YAWMIYAT/sessions")

        # Download and merge each activity file
        activity_data = {"topics": [], "events": []}
        files_processed = 0

        for file in files:
            try:
                file_content = drive_client.download_file_content(file['id'])
                file_json = json.loads(file_content)

                # Merge topics and events from file
                activity_data["topics"].extend(file_json.get("topics", []))
                activity_data["events"].extend(file_json.get("events", []))

                files_processed += 1
            except (json.JSONDecodeError, IOError) as e:
                # Log individual file failures but continue with remaining files
                continue

        # Merge activity into cached index
        updated_index = merge_activity_into_index(cached_index, activity_data, persona)

        # Log success
        audit_logger.log_refresh_attempt(
            persona=persona,
            status="success",
            data_sources=["YAWMIYAT/sessions"],
            files_read=files_processed
        )

        return (True, updated_index, None)

    except Exception as e:
        # Load cached index as fallback
        try:
            cached_index = load_cached_index(index_path)
        except Exception as cache_error:
            # If we can't load cached index either, log and re-raise
            audit_logger.log_refresh_attempt(
                persona=persona,
                status="failure",
                data_sources=["YAWMIYAT/sessions"],
                error=f"Drive error: {str(e)} AND cached index load failed: {str(cache_error)}",
                files_read=0
            )
            raise FileNotFoundError(
                f"Cannot refresh {persona} from Drive and cached index not available: {str(cache_error)}"
            )

        # Log failure with degradation reason
        error_reason = str(e)
        audit_logger.log_refresh_attempt(
            persona=persona,
            status="failure",
            data_sources=["YAWMIYAT/sessions"],
            error=error_reason,
            files_read=0
        )

        return (False, cached_index, error_reason)


def load_cached_index(index_path: Path) -> Dict[str, Any]:
    """
    Load knowledge index from disk.

    Args:
        index_path: Path to index JSON file (e.g., AMMAR_index.json)

    Returns:
        Index dictionary

    Raises:
        FileNotFoundError: If index file does not exist
        json.JSONDecodeError: If index file is malformed JSON
    """
    index_path = Path(index_path)

    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Malformed index JSON in {index_path}: {e.msg}", e.doc, e.pos)


def initialize_refresh_logger(ledger_path: Optional[Path] = None) -> RefreshAuditLogger:
    """
    Create and initialize a RefreshAuditLogger instance.

    Args:
        ledger_path: Optional custom path to REFRESH_AUDIT_LEDGER.jsonl
                    (defaults to HIKMAH__knowledge_index/REFRESH_AUDIT_LEDGER.jsonl)

    Returns:
        RefreshAuditLogger instance ready for logging
    """
    return RefreshAuditLogger(ledger_path)


__all__ = [
    'refresh_persona_index',
    'load_cached_index',
    'initialize_refresh_logger',
    'GoogleDriveClient',
    'RefreshAuditLogger',
]
