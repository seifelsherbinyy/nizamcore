"""
HIKMAH Knowledge Index Module

A comprehensive persona-aware knowledge management system for the NIZAM multi-persona framework.

Provides persona knowledge indices, versioning, and data refresh pipeline:
- Phase 14 (Index Schema & Storage): Define and store knowledge indices locally
- Phase 15 (Data Refresh): Read Google Drive logs and merge activity into indices
- Phases 16-20 (Message Generation & Adaptation): Consume fresh/cached indices for messaging

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

Integration (Phases 16-20):
    from HIKMAH__knowledge_index import refresh_persona_index
    - Call refresh_persona_index() before message generation to get fresh index
    - Falls back to cached index if Drive unavailable

Usage:
    from HIKMAH__knowledge_index import refresh_persona_index, load_refresh_config

    # Load configuration
    config = load_refresh_config()

    # Refresh index before message generation
    success, index, reason = refresh_persona_index(
        persona="AMMAR",
        drive_client=drive_client,
        index_path=Path("HIKMAH__knowledge_index/indices/AMMAR_index.json"),
        audit_logger=audit_logger
    )

    if success:
        # Use fresh index for message generation
        topics = index.get("topics", [])
    else:
        # Gracefully degrade to cached index
        print(f"Using cached index (reason: {reason})")
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
