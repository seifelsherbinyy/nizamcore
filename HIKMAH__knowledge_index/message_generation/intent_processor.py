"""
HIKMAH Message Generation: Intent Processor

Phase 16: Extract context from knowledge index and build rich message context.

This module implements intent-to-context conversion, transforming user intents
("You have open work on AI optimization") into rich context summaries that feed
message generation with topical specificity and emotional calibration.

Key Design Principles:
1. Intent matching: Extract keywords from intent, match against index topics (case-insensitive)
2. Fallback: If no match, return first 3 active topics (assume relevant baseline)
3. Context summary: Rich string with topic name, status, days active, blockers
4. Activity awareness: Summarize last 10 activity events (count event types)
5. Celebration detection: Flag if recent completions exist (last 7 days) → celebratory tone enabled
6. Privacy: Only use safe context_tags (already whitelisted in index); no raw names

Integration Points:
- Called by generator.generate_message() to build context user message for Claude
- Supports message generation with contextually-aware intent rephrasing
- Enables Phase 17 delivery with personalized nudges per persona

"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class IntentProcessor:
    """
    Convert user intent into rich context for message generation.

    Extracts topics from intent, builds context summaries, detects celebration
    triggers, and aggregates activity history into summaries.

    Static methods (no state): can be called directly without instantiation.
    Example: IntentProcessor.extract_topics(intent, index)
    """

    @staticmethod
    def extract_topics(intent: str, index: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract relevant topics from intent and index.

        Matches intent keywords (lowercased) against topic names. If no exact match,
        returns first 3 active topics as fallback (assumes relevance).

        Args:
            intent: User intent string (e.g., "You have open work on AI optimization")
            index: PersonaIndexDict from Phase 15 refresh (has 'topics' field)

        Returns:
            List of matching topic dicts (subset of index['topics'])
            Empty list if index has no topics
        """
        topics = index.get("topics", [])
        if not topics:
            return []

        # Simple heuristic: extract lowercase intent keywords, match against topic names
        intent_lower = intent.lower()
        intent_words = set(intent_lower.split())

        # Find topics whose names contain any intent words
        matching = []
        for topic in topics:
            topic_name_lower = topic.get("name", "").lower()
            # Check if any words from intent appear in topic name
            if any(word in topic_name_lower for word in intent_words):
                matching.append(topic)

        # If no exact match, return first 3 active topics
        if not matching:
            active = [t for t in topics if t.get("status") == "active"]
            matching = active[:3]

        return matching

    @staticmethod
    def build_context_summary(
        topics: List[Dict[str, Any]], index: Dict[str, Any]
    ) -> str:
        """
        Build rich context string from topics.

        Creates human-readable summary: "Topic X (active 3d, blockers: blocked on auth; unknown blockers) | Topic Y (active 1d, no blockers)"

        If no topics, summarizes recent completions as fallback (e.g., "Recent completions: 2 items closed").

        Args:
            topics: List of topic dicts (from extract_topics)
            index: PersonaIndexDict (has 'completions' field)

        Returns:
            Rich context summary string, safe for message generation user message
        """
        if not topics:
            # Fallback: summarize recent completions
            completions = index.get("completions", [])
            if completions:
                recent_count = len(completions[-5:])  # Last 5 completions
                completion_names = [c.get("name", "") for c in completions[-3:]]
                return f"Recent completions: {recent_count} items closed. Latest: {', '.join(completion_names)}"
            return "No open topics; no recent completions. Ready for new work?"

        summaries = []
        now = datetime.now(timezone.utc)

        for topic in topics:
            name = topic.get("name", "unnamed")
            status = topic.get("status", "unknown")

            # Calculate days active
            try:
                last_activity_str = topic.get("last_activity", "")
                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str.replace("Z", "+00:00"))
                    days_active = (now - last_activity).days
                else:
                    days_active = 0
            except (ValueError, TypeError):
                days_active = 0

            # Summarize blockers
            blockers = topic.get("blockers", [])
            if blockers:
                blocker_descriptions = [b.get("text", "") for b in blockers[:2]]
                blockers_text = "; ".join(blocker_descriptions)
            else:
                blockers_text = "no blockers"

            # Build topic summary
            summary = f"{name} ({status} {days_active}d, blockers: {blockers_text})"
            summaries.append(summary)

        return " | ".join(summaries)

    @staticmethod
    def should_celebrate(index: Dict[str, Any]) -> bool:
        """
        Check if index shows recent completions (triggers celebratory tone).

        Looks for completions completed within last 7 days. If found, recommends
        celebratory or acknowledgment tone for next message.

        Args:
            index: PersonaIndexDict (has 'completions' field)

        Returns:
            True if recent completion found (within 7 days)
            False if no completions or all are >7 days old
        """
        completions = index.get("completions", [])
        if not completions:
            return False

        # Get most recent completion
        latest_completion = completions[-1]
        try:
            completed_at_str = latest_completion.get("completed_at", "")
            if not completed_at_str:
                return False
            completed_at = datetime.fromisoformat(
                completed_at_str.replace("Z", "+00:00")
            )
            now = datetime.now(timezone.utc)
            days_since = (now - completed_at).days
            return days_since <= 7  # Recent completion in last 7 days
        except (ValueError, TypeError):
            return False

    @staticmethod
    def get_activity_summary(index: Dict[str, Any]) -> str:
        """
        Summarize recent activity from activity_history.

        Extracts last 10 events, counts event types, returns human-readable summary.
        Example output: "Recent: 3 topic_created, 2 accomplishment_logged, 1 blocker_flagged."

        Args:
            index: PersonaIndexDict (has 'activity_history' field)

        Returns:
            Human-readable activity summary string
            "No recent activity logged." if activity_history is empty or missing
        """
        history = index.get("activity_history", [])
        if not history:
            return "No recent activity logged."

        # Count event types in last 10 events
        recent_events = history[-10:]
        event_types: Dict[str, int] = {}
        for event in recent_events:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Build human-readable summary
        summary_parts = []
        for event_type, count in sorted(event_types.items()):
            # Convert snake_case to readable form: topic_created → topic created
            readable_type = event_type.replace("_", " ")
            summary_parts.append(f"{count} {readable_type}")

        if summary_parts:
            return "Recent: " + ", ".join(summary_parts) + "."
        return "No recent activity logged."

    @staticmethod
    def build_full_context(intent: str, index: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build complete context dict for message generation.

        Combines topic extraction, context summary, celebration detection, and activity
        summary into single context object. Used by generator.py to build rich user message.

        Args:
            intent: User intent string
            index: PersonaIndexDict

        Returns:
            Dict with keys:
            - topics: list of extracted topic dicts
            - context_summary: rich string describing current state
            - should_celebrate: bool flag for celebratory tone
            - activity_summary: string summarizing recent activity
            - stalled_count: number of topics in stalled_work
            - topic_count: total number of open topics
            - completion_count: total number of completions

        Example return value:
        {
            "topics": [
                {"name": "AI optimization", "status": "active", ...}
            ],
            "context_summary": "AI optimization (active 3d, blockers: auth integration) | ...",
            "should_celebrate": True,
            "activity_summary": "Recent: 2 accomplishment_logged, 1 topic_created.",
            "stalled_count": 1,
            "topic_count": 5,
            "completion_count": 12
        }
        """
        topics = IntentProcessor.extract_topics(intent, index)
        context_summary = IntentProcessor.build_context_summary(topics, index)
        should_celebrate = IntentProcessor.should_celebrate(index)
        activity_summary = IntentProcessor.get_activity_summary(index)

        stalled_work = index.get("stalled_work", [])
        all_topics = index.get("topics", [])
        completions = index.get("completions", [])

        return {
            "topics": topics,
            "context_summary": context_summary,
            "should_celebrate": should_celebrate,
            "activity_summary": activity_summary,
            "stalled_count": len(stalled_work),
            "topic_count": len(all_topics),
            "completion_count": len(completions),
        }


__all__ = ["IntentProcessor"]
