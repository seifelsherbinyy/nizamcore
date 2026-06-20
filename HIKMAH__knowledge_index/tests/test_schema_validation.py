"""
Tests for HIKMAH Knowledge Index schema validation.

Validates:
- TypedDict structure for all index components
- validate_index_schema function behavior
- Context tags whitelist enforcement
- Persona validation
- Version format validation
"""

import pytest
from datetime import datetime, timezone
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


def get_valid_sample_index():
    """Return a minimal valid index structure."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "version": "1.0",
        "persona": "AMMAR",
        "initialized_at": now,
        "last_updated": now,
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


class TestValidateIndexSchema:
    """Test suite for validate_index_schema function."""

    def test_accepts_valid_index_with_all_required_fields(self):
        """Test 1: validate_index_schema accepts valid index and returns (True, None)."""
        index = get_valid_sample_index()
        valid, error = validate_index_schema(index)
        assert valid is True
        assert error is None

    def test_rejects_index_missing_version(self):
        """Test 2: validate_index_schema rejects missing 'version' field."""
        index = get_valid_sample_index()
        del index["version"]
        valid, error = validate_index_schema(index)
        assert valid is False
        assert isinstance(error, str)
        assert "version" in error.lower()

    def test_rejects_invalid_version_format(self):
        """Test 3: validate_index_schema rejects invalid version format."""
        index = get_valid_sample_index()
        index["version"] = "v1.0"  # Invalid: must be semantic without 'v' prefix
        valid, error = validate_index_schema(index)
        assert valid is False
        assert isinstance(error, str)

    def test_rejects_unknown_persona(self):
        """Test 4: validate_index_schema rejects unknown persona."""
        index = get_valid_sample_index()
        index["persona"] = "UNKNOWN_PERSONA"
        valid, error = validate_index_schema(index)
        assert valid is False
        assert isinstance(error, str)
        assert "persona" in error.lower()

    def test_rejects_context_tags_with_invalid_whitelist(self):
        """Test 5: validate_index_schema rejects context_tags not in whitelist."""
        index = get_valid_sample_index()
        index["topics"] = [
            {
                "id": "topic-1",
                "name": "Test Topic",
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "context_tags": ["invalid_tag", "technical"],  # "invalid_tag" not in whitelist
                "confidence": 0.85,
                "key_accomplishments": [],
                "blockers": [],
                "notes": "Test"
            }
        ]
        valid, error = validate_index_schema(index)
        assert valid is False
        assert isinstance(error, str)

    def test_accepts_valid_schema_with_empty_arrays(self):
        """Test 6: validate_index_schema accepts valid schema with empty topics/completions/activity_history."""
        index = get_valid_sample_index()
        index["topics"] = []
        index["completions"] = []
        index["activity_history"] = []
        valid, error = validate_index_schema(index)
        assert valid is True
        assert error is None

    def test_topic_dict_structure(self):
        """Test 7: TopicDict supports full nested structure."""
        now = datetime.now(timezone.utc).isoformat()
        topic: TopicDict = {
            "id": "topic-uuid",
            "name": "AI optimization workflow",
            "status": "active",
            "created_at": now,
            "last_activity": now,
            "context_tags": ["technical", "career"],
            "confidence": 0.85,
            "key_accomplishments": [
                {"text": "Set up pipeline", "timestamp": now}
            ],
            "blockers": [
                {"text": "GPU memory issue", "since": now, "severity": "medium"}
            ],
            "notes": "Core optimization work"
        }
        assert topic["id"] == "topic-uuid"
        assert topic["status"] == "active"
        assert len(topic["key_accomplishments"]) == 1
        assert len(topic["blockers"]) == 1

    def test_completion_dict_structure(self):
        """Test 8: CompletionDict has id, name, completed_at, duration_days, context_tags, final_note."""
        now = datetime.now(timezone.utc).isoformat()
        completion: CompletionDict = {
            "id": "completed-uuid",
            "name": "Q1 financial baseline",
            "completed_at": now,
            "duration_days": 25,
            "context_tags": ["financial", "quarterly"],
            "final_note": "Completed successfully"
        }
        assert completion["id"] == "completed-uuid"
        assert completion["duration_days"] == 25
        assert len(completion["context_tags"]) == 2

    def test_activity_event_dict_structure(self):
        """Test 9: ActivityEventDict has ts, event_type, optional topic_id, description."""
        now = datetime.now(timezone.utc).isoformat()
        event: ActivityEventDict = {
            "ts": now,
            "event_type": "topic_created",
            "topic_id": "topic-uuid",
            "description": "New topic created"
        }
        assert event["ts"] == now
        assert event["event_type"] == "topic_created"
        assert "topic_id" in event

    def test_stalled_work_dict_structure(self):
        """Test 10: StalledWorkDict has topic_id, topic_name, blocker_count, stalled_since, days_stalled, last_activity, recovery_notes."""
        now = datetime.now(timezone.utc).isoformat()
        stalled: StalledWorkDict = {
            "topic_id": "topic-uuid",
            "topic_name": "AI optimization",
            "blocker_count": 1,
            "stalled_since": now,
            "days_stalled": 5,
            "last_activity": now,
            "recovery_notes": "Awaiting GPU decision"
        }
        assert stalled["topic_id"] == "topic-uuid"
        assert stalled["days_stalled"] == 5

    def test_context_snapshot_dict_structure(self):
        """Test 11: ContextSnapshotDict has ts and snapshot with metrics."""
        now = datetime.now(timezone.utc).isoformat()
        snapshot: ContextSnapshotDict = {
            "ts": now,
            "snapshot": {
                "open_topic_count": 3,
                "active_blocker_count": 2,
                "recent_accomplishments_count": 5,
                "completion_rate_7d": 0.40,
                "engagement_level": "medium"
            }
        }
        assert snapshot["ts"] == now
        assert snapshot["snapshot"]["open_topic_count"] == 3

    def test_metadata_dict_structure(self):
        """Test 12: MetadataDict has source, locale, language."""
        metadata: MetadataDict = {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
        assert metadata["source"] == "v1.1-knowledge-index"
        assert metadata["locale"] == "Egypt/Cairo"


class TestConstants:
    """Test constants are properly defined."""

    def test_valid_personas_contains_all_11(self):
        """Test VALID_PERSONAS contains all 11 personas."""
        assert len(VALID_PERSONAS) == 11
        required = {"AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
                   "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"}
        assert set(VALID_PERSONAS) == required

    def test_context_tags_whitelist_defined(self):
        """Test CONTEXT_TAGS_WHITELIST contains safe tags only."""
        assert CONTEXT_TAGS_WHITELIST == {"technical", "health", "financial", "strategic", "personal"}
