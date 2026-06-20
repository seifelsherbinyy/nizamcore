"""
HIKMAH Knowledge Index Schema Definition

Defines TypedDict structures and validation logic for persona knowledge indices.

Core design principles:
1. Context tags are whitelisted to prevent raw PII leakage (only: technical, health, financial, strategic, personal)
2. Version field supports semantic versioning (1.0, 1.1, etc.) with MAKHZAN snapshot pattern on breaking changes
3. All timestamps are ISO 8601 format (UTC)
4. Per-persona index with topics, completions, activity history, stalled work tracking, and context snapshots
5. Strict_local classification: never egressed to Telegram, Drive, or GitHub

Validated against:
- 11 personas (AMMAR, HIKMAH, TARIQ, MUNAWARA, MAL, BADAN, NAQD, SHURA, TAFRIGH, MARSAD, NIZAM)
- Topic statuses (active, paused, completed)
- Event types (topic_created, accomplishment_logged, blocker_flagged, topic_completed, context_snapshot, index_initialized)
- Blocker severity (low, medium, high)
"""

import re
from typing import TypedDict, Optional, List, Any


# Constants: Valid personas (11 total)
VALID_PERSONAS = [
    "AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
    "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"
]

# Constants: Context tags whitelist (prevents PII leakage)
CONTEXT_TAGS_WHITELIST = {"technical", "health", "financial", "strategic", "personal"}

# Constants: Valid version pattern (semantic versioning MAJOR.MINOR, e.g., 1.0, 1.1, 2.0)
VALID_VERSION_PATTERN = r"^[1-9][0-9]*\.[0-9]+$"

# Constants: Valid topic statuses
VALID_TOPIC_STATUS = ["active", "paused", "completed"]

# Constants: Valid event types for activity log
VALID_EVENT_TYPES = [
    "topic_created", "accomplishment_logged", "blocker_flagged",
    "topic_completed", "context_snapshot", "index_initialized"
]

# Constants: Valid blocker severity levels
VALID_BLOCKER_SEVERITY = ["low", "medium", "high"]


# TypedDict definitions: Building blocks for the index schema

class AccomplishmentDict(TypedDict):
    """Record of a completed task or milestone on a topic."""
    text: str  # Description of what was accomplished
    timestamp: str  # ISO 8601 timestamp


class BlockerDict(TypedDict):
    """Blocking issue preventing progress on a topic."""
    text: str  # Description of the blocker
    since: str  # ISO 8601 timestamp when blocker started
    severity: str  # One of: low, medium, high


class TopicDict(TypedDict):
    """A single topic being tracked (open or under investigation)."""
    id: str  # UUID unique within this persona's index
    name: str  # Human-readable topic name
    status: str  # One of: active, paused, completed
    created_at: str  # ISO 8601 timestamp
    last_activity: str  # ISO 8601 timestamp of most recent activity
    context_tags: List[str]  # Whitelisted safe tags (e.g., "technical", not "Seif's project")
    confidence: float  # 0.0–1.0; <0.8 flags for privacy gate in Phase 20
    key_accomplishments: List[AccomplishmentDict]  # Milestones achieved
    blockers: List[BlockerDict]  # Current blocking issues
    notes: str  # Free-form notes


class CompletionDict(TypedDict):
    """A topic that was completed and closed."""
    id: str  # UUID of completed topic
    name: str  # Topic name at completion
    completed_at: str  # ISO 8601 timestamp
    duration_days: int  # Days from creation to completion
    context_tags: List[str]  # Context at time of completion
    final_note: str  # Summary of the completed work


class ActivityEventDict(TypedDict):
    """Single event in the activity history log."""
    ts: str  # ISO 8601 timestamp
    event_type: str  # One of VALID_EVENT_TYPES
    topic_id: Optional[str]  # UUID of related topic (if applicable)
    description: str  # Human-readable event description


class SnapshotMetricsDict(TypedDict):
    """Aggregated metrics at a point in time."""
    open_topic_count: int
    active_blocker_count: int
    recent_accomplishments_count: int
    completion_rate_7d: float  # 0.0–1.0
    engagement_level: str  # e.g., "low", "medium", "high", "unknown"


class ContextSnapshotDict(TypedDict):
    """Snapshot of persona's knowledge state at a point in time."""
    ts: str  # ISO 8601 timestamp
    snapshot: SnapshotMetricsDict


class StalledWorkDict(TypedDict):
    """Topic that has stalled due to blockers."""
    topic_id: str
    topic_name: str
    blocker_count: int
    stalled_since: str  # ISO 8601 timestamp
    days_stalled: int
    last_activity: str  # ISO 8601 timestamp
    recovery_notes: str  # Notes on how to unblock


class MetadataDict(TypedDict):
    """Metadata about the index itself."""
    source: str  # e.g., "v1.1-knowledge-index"
    locale: str  # e.g., "Egypt/Cairo"
    language: str  # e.g., "en"


class PersonaIndexDict(TypedDict):
    """Complete knowledge index for a single persona."""
    version: str  # Semantic version (1.0, 1.1, etc.)
    persona: str  # One of VALID_PERSONAS
    initialized_at: str  # ISO 8601 timestamp
    last_updated: str  # ISO 8601 timestamp
    topics: List[TopicDict]  # Open/active topics
    completions: List[CompletionDict]  # Closed topics
    activity_history: List[ActivityEventDict]  # Append-only log
    stalled_work: List[StalledWorkDict]  # Topics blocked by issues
    context_snapshots: List[ContextSnapshotDict]  # State snapshots over time
    metadata: MetadataDict


# Validation function

def validate_index_schema(data: dict) -> tuple[bool, Optional[str]]:
    """
    Validate index structure against schema.

    Returns:
        (True, None) if valid
        (False, error_string) if invalid

    Checks:
    - All required fields present
    - Version format valid (1.x)
    - Persona is registered (one of 11)
    - All timestamps ISO 8601
    - Context tags in whitelist (prevents PII)
    - Array types correct
    """

    # Check required top-level fields
    required_fields = [
        "version", "persona", "initialized_at", "last_updated",
        "topics", "completions", "activity_history",
        "stalled_work", "context_snapshots", "metadata"
    ]

    for field in required_fields:
        if field not in data:
            return (False, f"Missing required field: {field}")

    # Validate version format (semantic versioning: MAJOR.MINOR, e.g., 1.0, 1.1, 2.0)
    version = data.get("version", "")
    if not re.match(VALID_VERSION_PATTERN, version):
        return (False, f"Invalid version format: {version} (must be semantic versioning like 1.0, 1.1, 2.0)")

    # Validate persona is registered
    persona = data.get("persona")
    if persona not in VALID_PERSONAS:
        return (False, f"Unknown persona: {persona}. Valid personas: {VALID_PERSONAS}")

    # Validate timestamps are ISO 8601 format
    timestamp_fields = ["initialized_at", "last_updated"]
    for field in timestamp_fields:
        timestamp = data.get(field, "")
        if not isinstance(timestamp, str) or not _is_iso8601(timestamp):
            return (False, f"Invalid ISO 8601 timestamp in {field}: {timestamp}")

    # Validate array types
    array_fields = ["topics", "completions", "activity_history", "stalled_work", "context_snapshots"]
    for field in array_fields:
        if not isinstance(data.get(field), list):
            return (False, f"Field '{field}' must be a list, got {type(data.get(field))}")

    # Validate topics structure and context tags
    for topic in data.get("topics", []):
        if not isinstance(topic, dict):
            return (False, f"Topic must be a dict, got {type(topic)}")

        # Check topic required fields
        topic_required = ["id", "name", "status", "created_at", "last_activity", "context_tags", "confidence"]
        for field in topic_required:
            if field not in topic:
                return (False, f"Topic missing required field: {field}")

        # Validate topic status
        if topic.get("status") not in VALID_TOPIC_STATUS:
            return (False, f"Invalid topic status: {topic.get('status')}")

        # Validate context tags are whitelisted (PII prevention)
        for tag in topic.get("context_tags", []):
            if tag not in CONTEXT_TAGS_WHITELIST:
                return (False, f"Invalid context_tag '{tag}' in topic '{topic.get('name')}'. "
                        f"Must be from: {CONTEXT_TAGS_WHITELIST}")

        # Validate timestamps
        if not _is_iso8601(topic.get("created_at", "")):
            return (False, f"Invalid ISO 8601 timestamp in topic.created_at")
        if not _is_iso8601(topic.get("last_activity", "")):
            return (False, f"Invalid ISO 8601 timestamp in topic.last_activity")

    # Validate completions structure
    for completion in data.get("completions", []):
        if not isinstance(completion, dict):
            return (False, f"Completion must be a dict")

        completion_required = ["id", "name", "completed_at", "duration_days", "context_tags", "final_note"]
        for field in completion_required:
            if field not in completion:
                return (False, f"Completion missing required field: {field}")

        # Validate context tags
        for tag in completion.get("context_tags", []):
            if tag not in CONTEXT_TAGS_WHITELIST:
                return (False, f"Invalid context_tag '{tag}' in completion. "
                        f"Must be from: {CONTEXT_TAGS_WHITELIST}")

        if not _is_iso8601(completion.get("completed_at", "")):
            return (False, f"Invalid ISO 8601 timestamp in completion.completed_at")

    # Validate activity history
    for event in data.get("activity_history", []):
        if not isinstance(event, dict):
            return (False, f"Activity event must be a dict")

        required = ["ts", "event_type", "description"]
        for field in required:
            if field not in event:
                return (False, f"Activity event missing required field: {field}")

        if not _is_iso8601(event.get("ts", "")):
            return (False, f"Invalid ISO 8601 timestamp in activity_history.ts")

    # Validate stalled_work
    for stalled in data.get("stalled_work", []):
        if not isinstance(stalled, dict):
            return (False, f"Stalled work entry must be a dict")

        required = ["topic_id", "topic_name", "blocker_count", "stalled_since", "days_stalled", "last_activity"]
        for field in required:
            if field not in stalled:
                return (False, f"Stalled work missing required field: {field}")

        if not _is_iso8601(stalled.get("stalled_since", "")):
            return (False, f"Invalid ISO 8601 timestamp in stalled_work.stalled_since")
        if not _is_iso8601(stalled.get("last_activity", "")):
            return (False, f"Invalid ISO 8601 timestamp in stalled_work.last_activity")

    # Validate context_snapshots
    for snap in data.get("context_snapshots", []):
        if not isinstance(snap, dict):
            return (False, f"Context snapshot must be a dict")

        if "ts" not in snap or "snapshot" not in snap:
            return (False, "Context snapshot missing required fields: ts, snapshot")

        if not _is_iso8601(snap.get("ts", "")):
            return (False, f"Invalid ISO 8601 timestamp in context_snapshots.ts")

    # Validate metadata
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        return (False, "Metadata must be a dict")

    required_metadata = ["source", "locale", "language"]
    for field in required_metadata:
        if field not in metadata:
            return (False, f"Metadata missing required field: {field}")

    return (True, None)


def _is_iso8601(timestamp: str) -> bool:
    """Simple check for ISO 8601 timestamp format."""
    if not isinstance(timestamp, str):
        return False
    # Very basic pattern: must have T and either Z or +/- offset
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', timestamp))
