"""
HIKMAH Knowledge Index Module

Core indexing logic for persona-driven knowledge management.

This module provides:
- schema: TypedDict definitions for the persona knowledge index (topics, completions, activity history, context snapshots)
- validate_index_schema: Validation function to ensure index structure and prevent PII leakage via context_tags whitelist
- Writer: Per-persona index file management with append-only ledger support

All index storage is strict_local (never egressed to Telegram, Drive, or GitHub).
Context tags are whitelisted to prevent raw PII leakage.
Versioning supports semantic evolution with MAKHZAN snapshot pattern on breaking changes.
"""

from HIKMAH__knowledge_index.index.schema import (
    validate_index_schema,
    PersonaIndexDict,
    TopicDict,
    CompletionDict,
    ActivityEventDict,
    StalledWorkDict,
    ContextSnapshotDict,
    MetadataDict,
    VALID_PERSONAS,
    CONTEXT_TAGS_WHITELIST,
)

__all__ = [
    "validate_index_schema",
    "PersonaIndexDict",
    "TopicDict",
    "CompletionDict",
    "ActivityEventDict",
    "StalledWorkDict",
    "ContextSnapshotDict",
    "MetadataDict",
    "VALID_PERSONAS",
    "CONTEXT_TAGS_WHITELIST",
]
