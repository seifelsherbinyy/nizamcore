"""
HIKMAH Knowledge Index Module

A comprehensive knowledge management system for the NIZAM multi-persona framework.

This module provides:
- JSON-based persona knowledge indices (per-persona state management)
- TypedDict schema definitions with full type hints
- Validation logic to prevent PII leakage and enforce data integrity
- Append-only activity history logging
- Support for topics, accomplishments, blockers, and context snapshots
- Semantic versioning with MAKHZAN snapshot pattern on breaking changes

All storage is strict_local (never egressed to Telegram, Drive, or GitHub).

Usage:
    from HIKMAH__knowledge_index.index import validate_index_schema, PersonaIndexDict

    # Create a valid index
    index = {
        "version": "1.0",
        "persona": "AMMAR",
        "initialized_at": "2026-06-20T14:30:00Z",
        "last_updated": "2026-06-20T14:30:00Z",
        "topics": [],
        "completions": [],
        "activity_history": [],
        "stalled_work": [],
        "context_snapshots": [],
        "metadata": {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
    }

    # Validate
    valid, error = validate_index_schema(index)
    if not valid:
        raise ValueError(f"Invalid index: {error}")
"""

__version__ = "1.0"
