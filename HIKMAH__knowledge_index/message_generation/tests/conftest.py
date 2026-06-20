"""
Shared pytest fixtures for Phase 16 Message Generation tests.

This module provides:
1. MockClaude: Simulates Anthropic API responses for testing without real API calls
2. Sample persona indices: Valid test indices for AMMAR, HIKMAH, TARIQ
3. Message ledger: Temporary file path for ledger testing
4. RepetitionTracker: Pre-populated tracker for deduplication tests
5. Mock client: MockClaude instance for use in tests

All fixtures are properly scoped and documented for test integration.
"""

import json
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock

# Import classes needed for fixture creation
from HIKMAH__knowledge_index.index.schema import (
    CONTEXT_TAGS_WHITELIST,
    VALID_PERSONAS,
)
from HIKMAH__knowledge_index.message_generation.repetition_tracker import (
    RepetitionTracker,
)


class MockClaude:
    """
    Simulates Anthropic Anthropic client for testing without real API calls.

    Returns persona-specific static responses that match expected tone patterns:
    - AMMAR: Terse, direct, imperative
    - HIKMAH: Warm, reflective, philosophical
    - TARIQ: Strategic, big-picture, goal-oriented
    - Others: Balanced responses

    Interface matches Anthropic client:
    ```
    mock_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        system="...",
        messages=[{"role": "user", "content": "..."}]
    )
    ```

    Returns object with `.content[0].text` attribute.
    """

    def __init__(self):
        """Initialize MockClaude with messages object."""
        self.messages = self.Messages()

    class Messages:
        """Messages API simulation."""

        def __init__(self):
            """Initialize Messages API."""
            pass

        def create(
            self,
            model: str = "claude-3-5-sonnet-20241022",
            max_tokens: int = 100,
            system: str = "",
            messages: List[Dict[str, str]] = None,
        ):
            """
            Simulate Claude API call with persona-specific responses.

            Extracts persona from system prompt and returns matching tone response.
            Falls back to generic response if persona not detected.

            Args:
                model: Model name (ignored in mock)
                max_tokens: Max tokens (ignored in mock)
                system: System prompt (analyzed to extract persona)
                messages: User messages (not used in mock)

            Returns:
                Mock object with `.content[0].text` and `.usage` attributes
            """
            # Detect persona from system prompt
            persona = self._detect_persona(system)

            # Return persona-specific response
            response_text = self._get_persona_response(persona)

            # Create mock response matching Anthropic format
            mock_response = Mock()
            mock_response.content = [Mock(text=response_text)]
            mock_response.usage = Mock(
                input_tokens=50, output_tokens=30, cache_read_tokens=0
            )

            return mock_response

        @staticmethod
        def _detect_persona(system_prompt: str) -> str:
            """
            Detect persona codename from system prompt.

            Args:
                system_prompt: System prompt text

            Returns:
                Persona codename (AMMAR, HIKMAH, etc.) or "default"
            """
            system_lower = system_prompt.lower()

            if "ammar" in system_lower or "terse" in system_lower or "direct" in system_lower:
                return "AMMAR"
            elif "hikmah" in system_lower or "reflective" in system_lower or "philosophical" in system_lower:
                return "HIKMAH"
            elif "tariq" in system_lower or "strategic" in system_lower or "quarter" in system_lower:
                return "TARIQ"
            elif "munawara" in system_lower or "operational" in system_lower:
                return "MUNAWARA"
            elif "mal" in system_lower or "numerical" in system_lower or "metrics" in system_lower:
                return "MAL"

            return "default"

        @staticmethod
        def _get_persona_response(persona: str) -> str:
            """
            Get persona-specific response template.

            Args:
                persona: Persona codename

            Returns:
                Response text matching persona tone
            """
            responses = {
                "AMMAR": "3 items waiting. Pick one and move forward. Task 1: Focus first. Task 2: Identify blockers.",
                "HIKMAH": "Your work carries weight. The stall reflects something deeper. What's beneath this pause? Notice the pattern.",
                "TARIQ": "This work directly feeds Q3 results. Remove the blocker and restore momentum. Timeline matters.",
                "MUNAWARA": "Operation needs your attention. Organize these tasks. Priority first: delegation, then execution.",
                "MAL": "5 items tracked. 2 at risk. Budget impact: 3%. Action needed within 24 hours.",
                "default": "You have work waiting. What's the next step?",
            }
            return responses.get(persona, responses["default"])


@pytest.fixture(scope="function")
def mock_client():
    """
    Fixture: MockClaude instance for tests.

    Returns a mock Anthropic client that simulates Claude API responses
    without making real API calls.

    Usage:
        def test_something(mock_client):
            message = generate_message("AMMAR", "intent", index, mock_client)
            assert "Pick one" in message  # AMMAR response

    Scope: function (fresh instance per test)
    """
    return MockClaude()


def _create_sample_index(
    persona: str,
    topic_count: int = 2,
    completion_count: int = 1,
    activity_count: int = 5,
    stalled_count: int = 0,
) -> Dict[str, Any]:
    """
    Helper: Create a valid sample persona index.

    Args:
        persona: Persona codename (AMMAR, HIKMAH, TARIQ, etc.)
        topic_count: Number of open topics (default: 2)
        completion_count: Number of recent completions (default: 1)
        activity_count: Number of activity history events (default: 5)
        stalled_count: Number of stalled work items (default: 0)

    Returns:
        PersonaIndexDict matching schema validation
    """
    now = datetime.now(timezone.utc)

    # Create topics
    topics = []
    for i in range(topic_count):
        topic = {
            "id": f"topic-{i:03d}",
            "name": f"Work Item {i + 1}" if i == 0 else f"Project {persona}-{i}",
            "status": "active",
            "created_at": (now - timedelta(days=7 + i)).isoformat(),
            "last_activity": (now - timedelta(days=i)).isoformat(),
            "context_tags": ["technical"] if i % 2 == 0 else ["strategic"],
            "confidence": 0.85 + (i * 0.05),
            "key_accomplishments": [
                {
                    "text": f"Completed milestone {j}",
                    "timestamp": (now - timedelta(days=j + 1)).isoformat(),
                }
                for j in range(min(2, i + 1))
            ],
            "blockers": [
                {
                    "text": f"Blocker {j}: Waiting for feedback",
                    "since": (now - timedelta(days=2 + j)).isoformat(),
                    "severity": "medium",
                }
                for j in range(0 if i < 1 else 1)
            ],
            "notes": f"Persona {persona} - Topic {i}: Active work item with progress",
        }
        topics.append(topic)

    # Create completions (recent, within 7 days)
    completions = []
    for i in range(completion_count):
        completion = {
            "id": f"completion-{i:03d}",
            "name": f"Completed Project {i + 1}",
            "completed_at": (now - timedelta(days=i + 1)).isoformat(),
            "context_tags": ["technical"],
        }
        completions.append(completion)

    # Create activity history
    activity_history = []
    event_types = ["topic_created", "accomplishment_logged", "blocker_flagged", "topic_completed"]
    for i in range(activity_count):
        event = {
            "type": event_types[i % len(event_types)],
            "timestamp": (now - timedelta(days=i + 1)).isoformat(),
            "topic_id": f"topic-{i % topic_count:03d}",
            "details": f"Event {i + 1} for {persona}",
        }
        activity_history.append(event)

    # Create stalled work
    stalled_work = []
    for i in range(stalled_count):
        stalled = {
            "id": f"stalled-{i:03d}",
            "name": f"Stalled Item {i + 1}",
            "stalled_since": (now - timedelta(days=14 + i)).isoformat(),
            "context_tags": ["technical"],
        }
        stalled_work.append(stalled)

    # Build full index
    index = {
        "persona": persona,
        "version": "1.0",
        "created_at": (now - timedelta(days=30)).isoformat(),
        "last_updated": now.isoformat(),
        "topics": topics,
        "completions": completions,
        "activity_history": activity_history,
        "stalled_work": stalled_work,
        "context_snapshot": {
            "tags_used": ["technical", "strategic"],
            "topics_count": topic_count,
            "activity_count": activity_count,
        },
    }

    return index


@pytest.fixture(scope="function")
def sample_ammar_index():
    """
    Fixture: Sample AMMAR persona index (terse, direct).

    Returns a valid PersonaIndexDict for AMMAR with:
    - 2 open topics (Work Item 1, Project AMMAR-1)
    - 1 recent completion (within 7 days)
    - 5 activity events
    - 0 stalled work items

    Passes schema validation: validate_index_schema(index) == (True, None)

    Usage:
        def test_something(sample_ammar_index):
            assert sample_ammar_index["persona"] == "AMMAR"
            assert len(sample_ammar_index["topics"]) == 2

    Scope: function (fresh index per test)
    """
    return _create_sample_index("AMMAR", topic_count=2, completion_count=1, activity_count=5)


@pytest.fixture(scope="function")
def sample_hikmah_index():
    """
    Fixture: Sample HIKMAH persona index (philosophical, reflective).

    Returns a valid PersonaIndexDict for HIKMAH with:
    - 2 open topics
    - 1 recent completion
    - 5 activity events
    - 1 stalled work item (for reflective tone testing)

    Scope: function (fresh index per test)
    """
    return _create_sample_index("HIKMAH", topic_count=2, completion_count=1, activity_count=5, stalled_count=1)


@pytest.fixture(scope="function")
def sample_tariq_index():
    """
    Fixture: Sample TARIQ persona index (strategic, goal-oriented).

    Returns a valid PersonaIndexDict for TARIQ with:
    - 2 open topics
    - 1 recent completion
    - 5 activity events
    - 0 stalled work items

    Scope: function (fresh index per test)
    """
    return _create_sample_index("TARIQ", topic_count=2, completion_count=1, activity_count=5)


@pytest.fixture(scope="function")
def sample_munawara_index():
    """
    Fixture: Sample MUNAWARA persona index (operational).

    Scope: function (fresh index per test)
    """
    return _create_sample_index("MUNAWARA", topic_count=3, completion_count=2)


@pytest.fixture(scope="function")
def sample_mal_index():
    """
    Fixture: Sample MAL persona index (numerical, metrics).

    Scope: function (fresh index per test)
    """
    return _create_sample_index("MAL", topic_count=3, completion_count=1)


@pytest.fixture(scope="function")
def message_ledger_path():
    """
    Fixture: Temporary file path for MessageLedger testing.

    Returns a temporary file path that will be automatically cleaned up
    after the test completes.

    Usage:
        def test_ledger(message_ledger_path):
            ledger = MessageLedger(message_ledger_path)
            ledger.log_generation(...)
            assert message_ledger_path.exists()

    Scope: function (creates new temp file per test)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "MESSAGE_LEDGER.jsonl"
        yield ledger_path


@pytest.fixture(scope="function")
def repetition_tracker(message_ledger_path):
    """
    Fixture: RepetitionTracker instance with pre-populated ledger.

    Returns an initialized RepetitionTracker with 3 sample messages
    logged for AMMAR persona.

    Sample messages:
    1. "Your AI workflow could be faster"
    2. "Focus on priority items first"
    3. "Team sync needs attention"

    Usage:
        def test_dedup(repetition_tracker):
            assert repetition_tracker.is_repetition("Your AI work might accelerate", "AMMAR") == True
            assert repetition_tracker.is_repetition("Let's plan the meeting", "AMMAR") == False

    Scope: function (fresh tracker + populated ledger per test)
    """
    tracker = RepetitionTracker(message_ledger_path)

    # Pre-populate with sample messages for AMMAR
    tracker.log_message(
        persona="AMMAR",
        message_text="Your AI workflow could be faster",
        intent="optimization",
        success=True,
    )
    tracker.log_message(
        persona="AMMAR",
        message_text="Focus on priority items first",
        intent="priorities",
        success=True,
    )
    tracker.log_message(
        persona="AMMAR",
        message_text="Team sync needs attention",
        intent="coordination",
        success=True,
    )

    # Pre-populate with sample messages for HIKMAH
    tracker.log_message(
        persona="HIKMAH",
        message_text="Your work carries weight. Notice the pattern.",
        intent="reflection",
        success=True,
    )
    tracker.log_message(
        persona="HIKMAH",
        message_text="What's beneath this pause?",
        intent="deep_work",
        success=True,
    )

    return tracker


__all__ = [
    "MockClaude",
    "mock_client",
    "sample_ammar_index",
    "sample_hikmah_index",
    "sample_tariq_index",
    "sample_munawara_index",
    "sample_mal_index",
    "message_ledger_path",
    "repetition_tracker",
]
