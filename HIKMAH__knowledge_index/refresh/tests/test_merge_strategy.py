"""
Tests for activity merge strategy (merge_strategy.py).

Tests merge rules: new topics, timestamp updates, completion preservation,
stalled work preservation, activity appending, and schema validation.
"""

import pytest
from datetime import datetime, timezone
from HIKMAH__knowledge_index.refresh.merge_strategy import merge_activity_into_index


class TestMergeNewTopics:
    """Tests for Rule 1: Adding new topics."""

    def test_merge_new_topic_added(self, sample_persona_index, sample_activity_data):
        """Test that new topics are added to topics[]."""
        initial_count = len(sample_persona_index["topics"])
        result = merge_activity_into_index(sample_persona_index, sample_activity_data, "AMMAR")

        assert len(result["topics"]) == initial_count + 1
        new_topic = next((t for t in result["topics"] if t["id"] == "new-topic-1"), None)
        assert new_topic is not None
        assert new_topic["name"] == "New Topic from Drive"
        assert new_topic["status"] == "active"

    def test_merge_multiple_new_topics(self, sample_persona_index):
        """Test merging multiple new topics."""
        activity_data = {
            "topics": [
                {"id": "new-1", "name": "Topic 1"},
                {"id": "new-2", "name": "Topic 2"},
                {"id": "new-3", "name": "Topic 3"}
            ],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        new_topics = [t for t in result["topics"] if t["id"].startswith("new-")]
        assert len(new_topics) == 3

    def test_merge_topic_with_defaults(self, sample_persona_index):
        """Test that new topics get sensible defaults for missing fields."""
        activity_data = {
            "topics": [{"id": "minimal", "name": "Minimal Topic"}],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        topic = next((t for t in result["topics"] if t["id"] == "minimal"), None)

        assert topic is not None
        assert topic["status"] == "active"
        assert topic["confidence"] == 0.7
        assert topic["context_tags"] == []
        assert isinstance(topic["created_at"], str)


class TestMergeExistingTopics:
    """Tests for Rule 2: Updating existing topics (timestamps only)."""

    def test_merge_updates_newer_timestamp(self, sample_persona_index):
        """Test that last_activity is updated if newer."""
        old_activity = "2026-06-20T09:00:00Z"
        new_activity = "2026-06-20T10:00:00Z"

        activity_data = {
            "topics": [{
                "id": "topic-1",
                "name": "Existing Topic",
                "last_activity": new_activity
            }],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        updated_topic = next((t for t in result["topics"] if t["id"] == "topic-1"), None)

        assert updated_topic["last_activity"] == new_activity

    def test_merge_never_backdates_timestamp(self, sample_persona_index):
        """Test that last_activity is NOT updated if older (never backdate)."""
        current_activity = "2026-06-20T09:00:00Z"
        older_activity = "2026-06-20T08:00:00Z"

        # Set current activity first
        sample_persona_index["topics"][0]["last_activity"] = current_activity

        activity_data = {
            "topics": [{
                "id": "topic-1",
                "name": "Existing Topic",
                "last_activity": older_activity
            }],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        topic = next((t for t in result["topics"] if t["id"] == "topic-1"), None)

        # Should NOT be updated to older timestamp
        assert topic["last_activity"] == current_activity


class TestMergeCompletionPreservation:
    """Tests for Rule 3: Never move completions back to active."""

    def test_merge_preserves_completions(self, sample_persona_index):
        """Test that completed topics are never moved back to active."""
        completed_id = "completed-1"
        initial_completions = len(sample_persona_index["completions"])

        # Try to merge activity for a completed topic
        activity_data = {
            "topics": [{
                "id": completed_id,
                "name": "Completed Task",
                "last_activity": "2026-06-20T10:00:00Z"
            }],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")

        # Verify completed topic stayed in completions
        assert len(result["completions"]) == initial_completions
        assert any(c["id"] == completed_id for c in result["completions"])

        # Verify it's NOT in active topics
        assert not any(t["id"] == completed_id for t in result["topics"])

    def test_merge_completed_not_duplicated(self, sample_persona_index):
        """Test that completed topics don't get duplicated in active."""
        activity_data = {
            "topics": [{"id": "completed-1", "name": "Completed Task"}],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        active_completed = [t for t in result["topics"] if t["id"] == "completed-1"]

        assert len(active_completed) == 0


class TestMergeStalledWorkPreservation:
    """Tests for Rule 4: Update days_stalled, preserve stalled_since."""

    def test_merge_preserves_stalled_since_timestamp(self, sample_persona_index):
        """Test that stalled_since timestamp is never changed."""
        original_stalled_since = sample_persona_index["stalled_work"][0]["stalled_since"]

        activity_data = {
            "topics": [{"id": "stalled-1", "name": "Stalled Task"}],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        stalled = next((s for s in result["stalled_work"] if s["topic_id"] == "stalled-1"), None)

        assert stalled is not None
        assert stalled["stalled_since"] == original_stalled_since

    def test_merge_updates_days_stalled(self, sample_persona_index):
        """Test that days_stalled is recalculated."""
        # Set stalled_since to 20 days ago
        from datetime import datetime, timezone, timedelta
        old_date = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        sample_persona_index["stalled_work"][0]["stalled_since"] = old_date

        activity_data = {"topics": [], "events": []}

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        stalled = result["stalled_work"][0]

        # days_stalled should be approximately 20
        assert stalled["days_stalled"] >= 19
        assert stalled["days_stalled"] <= 21


class TestMergeActivityHistoryAppending:
    """Tests for Rule 5: Append activity events (never overwrite)."""

    def test_merge_appends_new_events(self, sample_persona_index):
        """Test that new activity events are appended."""
        initial_events = len(sample_persona_index["activity_history"])

        activity_data = {
            "topics": [],
            "events": [
                {
                    "ts": "2026-06-20T10:30:00Z",
                    "event_type": "accomplishment_logged",
                    "topic_id": "topic-1",
                    "description": "Accomplished something"
                },
                {
                    "ts": "2026-06-20T11:00:00Z",
                    "event_type": "blocker_flagged",
                    "topic_id": "topic-1",
                    "description": "Found a blocker"
                }
            ]
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")

        assert len(result["activity_history"]) == initial_events + 2

    def test_merge_does_not_duplicate_events(self, sample_persona_index):
        """Test that duplicate events are not added."""
        duplicate_event = {
            "ts": "2026-06-20T10:00:00Z",
            "event_type": "index_initialized",
            "topic_id": None,
            "description": "Index initialized"
        }

        activity_data = {
            "topics": [],
            "events": [duplicate_event]
        }

        initial_count = len(sample_persona_index["activity_history"])
        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")

        # Should not add duplicate
        assert len(result["activity_history"]) == initial_count

    def test_merge_sorts_activity_history_by_timestamp(self, sample_persona_index):
        """Test that activity history is sorted chronologically."""
        activity_data = {
            "topics": [],
            "events": [
                {
                    "ts": "2026-06-20T15:00:00Z",
                    "event_type": "topic_created",
                    "topic_id": None,
                    "description": "Event 3"
                },
                {
                    "ts": "2026-06-20T12:00:00Z",
                    "event_type": "topic_created",
                    "topic_id": None,
                    "description": "Event 1"
                },
                {
                    "ts": "2026-06-20T13:00:00Z",
                    "event_type": "topic_created",
                    "topic_id": None,
                    "description": "Event 2"
                }
            ]
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")

        timestamps = [e["ts"] for e in result["activity_history"]]
        assert timestamps == sorted(timestamps)


class TestMergeValidation:
    """Tests for post-merge schema validation."""

    def test_merge_validates_schema(self, sample_persona_index):
        """Test that merged index passes schema validation."""
        activity_data = {
            "topics": [{"id": "new-1", "name": "New Topic"}],
            "events": []
        }

        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")

        # Should not raise exception if schema is valid
        from HIKMAH__knowledge_index.index.schema import validate_index_schema
        is_valid, error = validate_index_schema(result)
        assert is_valid

    def test_merge_raises_on_invalid_schema(self, sample_persona_index):
        """Test that invalid merged index raises ValueError."""
        # Mock validate_index_schema to fail
        import HIKMAH__knowledge_index.refresh.merge_strategy as merge_module

        original_validate = merge_module.validate_index_schema

        def mock_validate(index):
            return (False, "Test validation failure")

        merge_module.validate_index_schema = mock_validate

        try:
            activity_data = {"topics": [], "events": []}
            with pytest.raises(ValueError, match="Schema validation failed"):
                merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")
        finally:
            merge_module.validate_index_schema = original_validate


class TestMergeEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_merge_with_empty_activity(self, sample_persona_index):
        """Test merge with empty activity data."""
        initial_topics = len(sample_persona_index["topics"])

        result = merge_activity_into_index(sample_persona_index, {}, "AMMAR")

        # Index should be unchanged (except last_updated)
        assert len(result["topics"]) == initial_topics

    def test_merge_with_none_activity(self, sample_persona_index):
        """Test merge with None activity data."""
        result = merge_activity_into_index(sample_persona_index, None, "AMMAR")

        # Should handle gracefully
        assert result is not None

    def test_merge_updates_last_updated_timestamp(self, sample_persona_index):
        """Test that last_updated is updated to current time."""
        old_updated = sample_persona_index["last_updated"]

        import time
        time.sleep(0.1)  # Ensure time advances

        activity_data = {"topics": [], "events": []}
        result = merge_activity_into_index(sample_persona_index, activity_data, "AMMAR")

        assert result["last_updated"] > old_updated
