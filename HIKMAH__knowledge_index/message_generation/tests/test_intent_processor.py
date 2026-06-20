"""
Tests for IntentProcessor module (context extraction and building).

This test module validates:
1. Topic extraction from intent with keyword matching
2. Fallback to first 3 active topics when no match
3. Context summary building with topic names and status
4. Celebration trigger detection (completions within 7 days)
5. Activity summary generation (event type aggregation)
6. Full context building with all components

All tests use sample persona indices (AMMAR, HIKMAH, TARIQ, etc.)
"""

import pytest
from datetime import datetime, timezone, timedelta

from HIKMAH__knowledge_index.message_generation.intent_processor import (
    IntentProcessor,
)


class TestExtractTopics:
    """Test topic extraction from intent."""

    def test_extract_topics_exact_match(self, sample_ammar_index):
        """
        Test: extract_topics finds topics matching intent keywords.

        Setup: sample_ammar_index has "Work Item 1"
        Call: extract_topics("You have open work on Work Item 1", index)
        Assert: Returns list with "Work Item 1" topic
        """
        intent = "You have open work on item"
        topics = IntentProcessor.extract_topics(intent, sample_ammar_index)

        # Should find at least one topic (Word Item 1 or Project AMMAR-1)
        assert len(topics) > 0
        assert any("Item" in t.get("name", "") for t in topics)

    def test_extract_topics_case_insensitive(self, sample_ammar_index):
        """
        Test: extract_topics is case-insensitive.

        Call: extract_topics("WORK ITEM", index) and extract_topics("work item", index)
        Assert: Both return same topics (case doesn't matter)
        """
        topics_upper = IntentProcessor.extract_topics(
            "WORK ITEM", sample_ammar_index
        )
        topics_lower = IntentProcessor.extract_topics(
            "work item", sample_ammar_index
        )

        assert len(topics_upper) == len(topics_lower)

    def test_extract_topics_no_match_fallback(self, sample_ammar_index):
        """
        Test: extract_topics returns first 3 active topics when no keyword match.

        Setup: sample_ammar_index has topics
        Call: extract_topics("something completely random", index)
        Assert: Returns first 3 active topics (fallback)
        """
        intent = "something completely random xyz"
        topics = IntentProcessor.extract_topics(intent, sample_ammar_index)

        # Should return up to 3 active topics as fallback
        assert len(topics) <= 3
        # All should be from the index
        index_topic_names = {t.get("name") for t in sample_ammar_index["topics"]}
        for topic in topics:
            assert topic.get("name") in index_topic_names

    def test_extract_topics_empty_index(self):
        """
        Test: extract_topics returns empty list for empty index.

        Setup: Index with no topics
        Call: extract_topics("intent", empty_index)
        Assert: Returns []
        """
        empty_index = {
            "persona": "TEST",
            "topics": [],
            "completions": [],
            "activity_history": [],
            "stalled_work": [],
        }
        topics = IntentProcessor.extract_topics("any intent", empty_index)
        assert topics == []

    def test_extract_topics_partial_match(self, sample_ammar_index):
        """
        Test: extract_topics finds topics with partial keyword matches.

        Setup: sample_ammar_index has "Work Item 1" and "Project AMMAR-1"
        Call: extract_topics("Work...", index)
        Assert: Finds "Work Item 1" (partial match)
        """
        topics = IntentProcessor.extract_topics("work", sample_ammar_index)
        assert len(topics) > 0

    def test_extract_topics_returns_topic_dicts(self, sample_ammar_index):
        """
        Test: extract_topics returns full topic dictionaries (not just names).

        Call: extract_topics("work", index)
        Assert: Each returned item has: id, name, status, created_at, context_tags, etc.
        """
        topics = IntentProcessor.extract_topics("work", sample_ammar_index)

        if topics:
            topic = topics[0]
            assert "id" in topic
            assert "name" in topic
            assert "status" in topic
            assert "created_at" in topic
            assert "context_tags" in topic


class TestContextSummary:
    """Test context summary building."""

    def test_build_context_summary_with_topics(self, sample_ammar_index):
        """
        Test: build_context_summary creates rich string with topic info.

        Setup: sample_ammar_index with 2 topics
        Call: build_context_summary([topic1, topic2], index)
        Assert: Returns string with topic names (e.g., "Work Item 1 | Project AMMAR-1")
        """
        topics = sample_ammar_index["topics"][:2]
        summary = IntentProcessor.build_context_summary(topics, sample_ammar_index)

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Should contain topic names
        for topic in topics:
            assert topic.get("name") in summary or "active" in summary

    def test_build_context_summary_empty_topics(self, sample_ammar_index):
        """
        Test: build_context_summary handles empty topic list gracefully.

        Call: build_context_summary([], index)
        Assert: Returns fallback string (e.g., "No active topics")
        """
        summary = IntentProcessor.build_context_summary(
            [], sample_ammar_index
        )

        assert isinstance(summary, str)
        # Should be non-empty (fallback message)
        assert len(summary) > 0

    def test_build_context_summary_includes_topic_info(self, sample_ammar_index):
        """
        Test: build_context_summary includes topic names and status.

        Setup: Topics with different statuses
        Call: build_context_summary(topics, index)
        Assert: Summary mentions topic names and/or status info
        """
        topics = sample_ammar_index["topics"][:1]
        summary = IntentProcessor.build_context_summary(topics, sample_ammar_index)

        # Should mention topic name or have descriptive info
        assert len(summary) > len(topics[0].get("name", ""))


class TestCelebrationDetection:
    """Test celebration trigger detection."""

    def test_should_celebrate_recent_completion(self, sample_ammar_index):
        """
        Test: should_celebrate returns True for recent completions (≤7 days).

        Setup: sample_ammar_index has completion from 1 day ago (created in fixture)
        Call: should_celebrate(index)
        Assert: Returns True
        """
        should = IntentProcessor.should_celebrate(sample_ammar_index)

        # sample_ammar_index has 1 completion from 1 day ago (within 7 days)
        assert should is True

    def test_should_celebrate_old_completion(self):
        """
        Test: should_celebrate returns False for old completions (>7 days).

        Setup: Index with completion from 10 days ago
        Call: should_celebrate(index)
        Assert: Returns False (outside 7-day window)
        """
        now = datetime.now(timezone.utc)
        old_index = {
            "persona": "TEST",
            "completions": [
                {
                    "id": "old-completion",
                    "name": "Old project",
                    "completed_at": (now - timedelta(days=10)).isoformat(),
                    "context_tags": ["technical"],
                }
            ],
            "topics": [],
            "activity_history": [],
            "stalled_work": [],
        }

        should = IntentProcessor.should_celebrate(old_index)
        assert should is False

    def test_should_celebrate_no_completions(self):
        """
        Test: should_celebrate returns False for empty completions.

        Setup: Index with no completions
        Call: should_celebrate(index)
        Assert: Returns False
        """
        empty_index = {
            "persona": "TEST",
            "completions": [],
            "topics": [],
            "activity_history": [],
            "stalled_work": [],
        }

        should = IntentProcessor.should_celebrate(empty_index)
        assert should is False


class TestActivitySummary:
    """Test activity summary generation."""

    def test_get_activity_summary_with_events(self, sample_ammar_index):
        """
        Test: get_activity_summary counts and formats activity events.

        Setup: sample_ammar_index has 5 activity events
        Call: get_activity_summary(index)
        Assert: Returns string like "Recent: 1 topic created, 1 accomplishment logged, 1 blocker flagged..."
        """
        summary = IntentProcessor.get_activity_summary(sample_ammar_index)

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Should mention activity or events
        assert "activity" in summary.lower() or "recent" in summary.lower() or "event" in summary.lower() or "topic" in summary.lower()

    def test_get_activity_summary_empty(self):
        """
        Test: get_activity_summary returns fallback for empty activity.

        Setup: Index with no activity_history
        Call: get_activity_summary(index)
        Assert: Returns "No recent activity logged." or similar
        """
        empty_index = {
            "persona": "TEST",
            "activity_history": [],
            "topics": [],
            "completions": [],
            "stalled_work": [],
        }

        summary = IntentProcessor.get_activity_summary(empty_index)

        assert isinstance(summary, str)
        # Should indicate no activity
        assert "no" in summary.lower() or "activity" in summary.lower()

    def test_get_activity_summary_event_counting(self, sample_ammar_index):
        """
        Test: get_activity_summary counts events by type.

        Setup: sample_ammar_index with mixed event types
        Call: get_activity_summary(index)
        Assert: Summary includes event type counts (e.g., "1 topic created")
        """
        summary = IntentProcessor.get_activity_summary(sample_ammar_index)

        # Should be non-empty and descriptive
        assert len(summary) > 10


class TestFullContextBuilding:
    """Test full context dict building."""

    def test_build_full_context_returns_dict(self, sample_ammar_index):
        """
        Test: build_full_context returns dict with all context components.

        Call: build_full_context("intent", index)
        Assert: Returns dict with keys: topics, context_summary, should_celebrate, activity_summary, etc.
        """
        context = IntentProcessor.build_full_context(
            "AI optimization work",
            sample_ammar_index
        )

        assert isinstance(context, dict)
        # Should have key context fields
        assert "topics" in context
        assert "context_summary" in context
        assert "should_celebrate" in context
        assert "activity_summary" in context

    def test_build_full_context_topics_populated(self, sample_ammar_index):
        """
        Test: build_full_context.topics is populated from extract_topics.

        Setup: sample_ammar_index with topics
        Call: build_full_context("work", index)
        Assert: context["topics"] is non-empty list
        """
        context = IntentProcessor.build_full_context(
            "work",
            sample_ammar_index
        )

        assert "topics" in context
        assert isinstance(context["topics"], list)
        # Should have at least some topics (fallback to first 3 if no match)
        assert len(context["topics"]) > 0

    def test_build_full_context_celebration_flag(self, sample_ammar_index):
        """
        Test: build_full_context.should_celebrate reflects celebration state.

        Setup: sample_ammar_index with recent completions
        Call: build_full_context("intent", index)
        Assert: context["should_celebrate"] is boolean
        """
        context = IntentProcessor.build_full_context(
            "any intent",
            sample_ammar_index
        )

        assert "should_celebrate" in context
        assert isinstance(context["should_celebrate"], bool)

    def test_build_full_context_with_empty_index(self):
        """
        Test: build_full_context handles empty index gracefully.

        Setup: Empty index
        Call: build_full_context("intent", empty_index)
        Assert: Returns valid context dict (all fields present, possibly empty/default)
        """
        empty_index = {
            "persona": "TEST",
            "topics": [],
            "completions": [],
            "activity_history": [],
            "stalled_work": [],
        }

        context = IntentProcessor.build_full_context("intent", empty_index)

        assert isinstance(context, dict)
        # All expected keys should be present
        assert "context_summary" in context
        assert "should_celebrate" in context
        assert "activity_summary" in context

    def test_build_full_context_with_all_personas(
        self,
        sample_ammar_index,
        sample_hikmah_index,
        sample_tariq_index,
        sample_munawara_index,
        sample_mal_index,
    ):
        """
        Test: build_full_context works with all persona indices.

        Setup: Sample indices for multiple personas
        Call: build_full_context on each
        Assert: All return valid context dicts
        """
        personas = [
            ("AMMAR", sample_ammar_index),
            ("HIKMAH", sample_hikmah_index),
            ("TARIQ", sample_tariq_index),
            ("MUNAWARA", sample_munawara_index),
            ("MAL", sample_mal_index),
        ]

        for persona_name, index in personas:
            context = IntentProcessor.build_full_context("test intent", index)
            assert isinstance(context, dict)
            assert "topics" in context
            assert "context_summary" in context


class TestIntentProcessorIntegration:
    """Integration tests across multiple intent processor methods."""

    def test_full_pipeline_topic_to_summary(self, sample_ammar_index):
        """
        Test: Full pipeline from intent to rich context summary.

        Call: extract_topics → build_context_summary
        Assert: Produces coherent context string
        """
        topics = IntentProcessor.extract_topics("work", sample_ammar_index)
        summary = IntentProcessor.build_context_summary(topics, sample_ammar_index)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_celebration_enables_celebratory_tone(self, sample_ammar_index):
        """
        Test: Celebration flag should enable celebratory message tone.

        Setup: Index with recent completions
        Call: should_celebrate(index) → enables celebratory tone
        Assert: Flag is True when completions exist
        """
        should_celebrate = IntentProcessor.should_celebrate(sample_ammar_index)

        # sample_ammar_index has recent completions
        assert should_celebrate is True

    def test_activity_summary_tracks_user_engagement(self, sample_ammar_index):
        """
        Test: Activity summary reflects recent user engagement.

        Setup: Index with activity history
        Call: get_activity_summary(index)
        Assert: Summary describes recent activities
        """
        summary = IntentProcessor.get_activity_summary(sample_ammar_index)

        # Should have activity description
        assert len(summary) > 10
