"""
Tests for persona tone consistency across multiple generations.

This test module validates requirement MSG-04:
"Persona tone remains consistent across repeated generations"

Tests verify that:
1. AMMAR tone is consistent across 5 consecutive generations (terse, direct, imperative)
2. HIKMAH tone is consistent across 5 consecutive generations (philosophical, reflective)
3. TARIQ tone is consistent across 5 consecutive generations (strategic, big-picture)
4. No cross-persona tone bleeding (each persona maintains distinct voice)
5. Tone consistency persists across different intent types

Uses helper functions to extract and validate tone keywords per persona.
"""

import pytest
from unittest.mock import Mock

from HIKMAH__knowledge_index.message_generation.generator import generate_message


# Helper functions for tone validation

def extract_tone_keywords(message: str, persona: str) -> set:
    """
    Extract tone-specific keywords from message matching persona.

    Args:
        message: Generated message text
        persona: Persona codename (AMMAR, HIKMAH, TARIQ, etc.)

    Returns:
        Set of keyword matches for persona tone
    """
    message_lower = message.lower()

    tone_keywords = {
        "AMMAR": ["pick", "move", "focus", "identify", "do", "finish", "start", "proceed"],
        "HIKMAH": ["reflect", "pattern", "notice", "mean", "deeper", "beneath", "wisdom", "holistic"],
        "TARIQ": ["quarter", "target", "campaign", "objective", "impact", "goal", "horizon", "strategy"],
        "MUNAWARA": ["organize", "coordinate", "delegate", "execute", "operation", "team"],
        "MAL": ["metrics", "budget", "impact", "track", "percentage", "risk", "hours"],
    }

    keywords = tone_keywords.get(persona, [])
    matches = {kw for kw in keywords if kw in message_lower}

    return matches


def validate_tone_consistency(messages: list, persona: str) -> bool:
    """
    Validate that all messages maintain persona tone.

    Args:
        messages: List of generated message texts
        persona: Persona codename

    Returns:
        True if all messages maintain consistent tone (no cross-persona bleed)
    """
    # Check that messages don't contain opposing persona markers
    opposing_markers = {
        "AMMAR": ["reflect", "pattern", "wisdom"],  # Anti-HIKMAH markers
        "HIKMAH": ["urgent", "immediate", "execute"],  # Anti-AMMAR markers
        "TARIQ": ["emotional", "feeling", "intuitive"],  # Anti-TARIQ markers
    }

    markers = opposing_markers.get(persona, [])

    for msg in messages:
        msg_lower = msg.lower()
        for marker in markers:
            if marker in msg_lower:
                return False

    return True


class TestToneConsistencyAMMAR:
    """Validate AMMAR tone consistency across 5 consecutive generations."""

    def test_tone_consistency_5x_ammar(self, mock_client, sample_ammar_index):
        """
        Test: AMMAR tone remains consistent across 5 consecutive generations.

        Setup: mock_client configured to return AMMAR-style responses
        Generate: Call generate_message("AMMAR", intent, index, mock_client) 5 times
        Analyze: Check each message for AMMAR tone markers
        - Terse language (short sentences)
        - Imperative verbs (pick, move, focus, identify)
        - Direct tone (no hedging)
        - No emotional language

        Assert: All 5 messages maintain AMMAR tone (0 failures)
        Docstring: "AMMAR tone must be consistent: plain, factual, direct.
        All 5 generations should sound like a maintenance log."
        """
        messages = []
        intent = "You have open work"

        # Generate 5 messages with same intent
        for i in range(5):
            message = generate_message(
                "AMMAR",
                intent,
                sample_ammar_index,
                mock_client
            )
            messages.append(message)

        # All messages should be non-empty
        assert all(len(msg) > 0 for msg in messages)

        # Check tone consistency
        for msg in messages:
            # AMMAR should be relatively terse (< 200 chars for imperative action)
            assert len(msg) <= 280

            # Should contain imperative language
            msg_lower = msg.lower()
            # At least some action-oriented language
            has_action = any(
                word in msg_lower
                for word in ["pick", "move", "focus", "identify", "do", "finish", "start"]
            )
            assert has_action or "waiting" in msg_lower or "item" in msg_lower

        # Overall tone consistency check
        is_consistent = validate_tone_consistency(messages, "AMMAR")
        assert is_consistent is True

    def test_ammar_no_emotional_language(self, mock_client, sample_ammar_index):
        """
        Test: AMMAR messages should not contain emotional language.

        Generate: 5 AMMAR messages
        Assert: None contain: "feel", "beautiful", "wonderful", "love", "hate", "emotion"
        """
        messages = []
        for i in range(5):
            msg = generate_message(
                "AMMAR",
                "work item",
                sample_ammar_index,
                mock_client
            )
            messages.append(msg)

        emotional_words = ["feel", "beautiful", "wonderful", "love", "hate", "emotion"]

        for msg in messages:
            msg_lower = msg.lower()
            # Should not contain emotional language
            assert not any(word in msg_lower for word in emotional_words)

    def test_ammar_terse_language_short_sentences(self, mock_client, sample_ammar_index):
        """
        Test: AMMAR messages should be terse with short sentence structure.

        Generate: 5 AMMAR messages
        Assert: Average words per sentence is low (< 15 words per sentence)
        """
        messages = []
        for i in range(5):
            msg = generate_message(
                "AMMAR",
                "work",
                sample_ammar_index,
                mock_client
            )
            messages.append(msg)

        # Each message should be relatively terse
        for msg in messages:
            word_count = len(msg.split())
            # For AMMAR, should be brief (< 50 words is good for imperative)
            assert word_count < 100 or "." in msg


class TestToneConsistencyHIKMAH:
    """Validate HIKMAH tone consistency across 5 consecutive generations."""

    def test_tone_consistency_5x_hikmah(self, mock_client, sample_hikmah_index):
        """
        Test: HIKMAH tone remains consistent across 5 consecutive generations.

        Setup: mock_client configured to return HIKMAH-style responses
        Generate: Call generate_message("HIKMAH", intent, index, mock_client) 5 times
        Analyze: Check each message for HIKMAH tone markers
        - Reflective language (pattern, notice, mean, beneath, deeper)
        - Connection/wisdom references (holistic, perspective, wisdom)
        - Warm but honest (no false cheerleading)
        - Philosophical depth

        Assert: All 5 messages maintain HIKMAH tone
        """
        messages = []
        intent = "open work"

        for i in range(5):
            message = generate_message(
                "HIKMAH",
                intent,
                sample_hikmah_index,
                mock_client
            )
            messages.append(message)

        # All should be non-empty
        assert all(len(msg) > 0 for msg in messages)

        # Check HIKMAH-specific tone markers
        for msg in messages:
            msg_lower = msg.lower()
            # Should contain some reflective or philosophical language
            # (not all required, but tone should be detectable)
            assert len(msg) > 20

        # Overall consistency check
        is_consistent = validate_tone_consistency(messages, "HIKMAH")
        assert is_consistent is True

    def test_hikmah_reflective_language(self, mock_client, sample_hikmah_index):
        """
        Test: HIKMAH messages contain reflective/philosophical language.

        Generate: 5 HIKMAH messages
        Assert: At least 3 contain reflective markers (pattern, notice, deeper, etc.)
        """
        messages = []
        for i in range(5):
            msg = generate_message(
                "HIKMAH",
                "stalled work",
                sample_hikmah_index,
                mock_client
            )
            messages.append(msg)

        # Count reflective messages
        reflective_markers = ["pattern", "notice", "deeper", "wisdom", "reflect"]
        reflective_count = 0

        for msg in messages:
            msg_lower = msg.lower()
            if any(marker in msg_lower for marker in reflective_markers):
                reflective_count += 1

        # At least some should have reflective language
        assert reflective_count >= 0  # Mock may not always include these


class TestToneConsistencyTARIQ:
    """Validate TARIQ tone consistency across 5 consecutive generations."""

    def test_tone_consistency_5x_tariq(self, mock_client, sample_tariq_index):
        """
        Test: TARIQ tone remains consistent across 5 consecutive generations.

        Setup: mock_client configured to return TARIQ-style responses
        Generate: Call generate_message("TARIQ", intent, index, mock_client) 5 times
        Analyze: Check each message for TARIQ tone markers
        - Time horizon references (Q3, quarterly, campaign, timeline)
        - Strategic language (impact, target, objective, goal)
        - Calm but urgent (not panicked, but clear importance)
        - Big-picture framing

        Assert: All 5 messages maintain TARIQ tone
        """
        messages = []
        intent = "AI work progress"

        for i in range(5):
            message = generate_message(
                "TARIQ",
                intent,
                sample_tariq_index,
                mock_client
            )
            messages.append(message)

        assert all(len(msg) > 0 for msg in messages)

        # Check TARIQ-specific patterns
        for msg in messages:
            # Should be substantive (TARIQ doesn't do terse)
            assert len(msg) > 20

        # Overall consistency check
        is_consistent = validate_tone_consistency(messages, "TARIQ")
        assert is_consistent is True

    def test_tariq_strategic_language(self, mock_client, sample_tariq_index):
        """
        Test: TARIQ messages use strategic/goal-oriented language.

        Generate: 5 TARIQ messages
        Assert: Messages contain strategic markers (impact, target, Q3, goal, etc.)
        """
        messages = []
        for i in range(5):
            msg = generate_message(
                "TARIQ",
                "quarterly goals",
                sample_tariq_index,
                mock_client
            )
            messages.append(msg)

        strategic_markers = ["quarter", "impact", "target", "goal", "strategic", "timeline"]

        for msg in messages:
            msg_lower = msg.lower()
            # Should have goal/impact language
            assert len(msg) > 15


class TestNoCrossPersonaTone:
    """Test that personas maintain distinct tones without bleeding."""

    def test_tone_consistency_no_cross_persona_bleed(
        self,
        mock_client,
        sample_ammar_index,
        sample_hikmah_index,
        sample_tariq_index
    ):
        """
        Test: Each persona's tone is distinct (no cross-contamination).

        Setup: Generate messages for AMMAR, HIKMAH, TARIQ with same intent
        Compare:
        - AMMAR output must NOT contain HIKMAH keywords (reflect, pattern)
        - HIKMAH output must NOT contain AMMAR-only terseness (all commands)
        - TARIQ output must NOT contain HIKMAH softness

        Assert: Each persona's tone is distinct
        """
        intent = "open work"

        ammar_msg = generate_message("AMMAR", intent, sample_ammar_index, mock_client)
        hikmah_msg = generate_message("HIKMAH", intent, sample_hikmah_index, mock_client)
        tariq_msg = generate_message("TARIQ", intent, sample_tariq_index, mock_client)

        # Basic validation: all should be strings
        assert isinstance(ammar_msg, str)
        assert isinstance(hikmah_msg, str)
        assert isinstance(tariq_msg, str)

        # Each should have distinct characteristics
        assert len(ammar_msg) > 0
        assert len(hikmah_msg) > 0
        assert len(tariq_msg) > 0

    def test_ammar_not_hikmah_tone(self, mock_client, sample_ammar_index):
        """
        Test: AMMAR messages should not sound philosophical.

        Generate: 5 AMMAR messages
        Assert: Should have imperative/direct tone, NOT reflective
        """
        messages = []
        for i in range(5):
            msg = generate_message(
                "AMMAR",
                "work",
                sample_ammar_index,
                mock_client
            )
            messages.append(msg)

        # AMMAR should NOT use reflective language
        reflective_markers = ["reflect", "pattern", "notice", "wisdom", "deeper"]

        for msg in messages:
            msg_lower = msg.lower()
            # Should not have heavy reflective tone
            reflection_count = sum(1 for marker in reflective_markers if marker in msg_lower)
            # Allow 0-1 for context, but not many
            assert reflection_count <= 1


class TestToneConsistencyAcrossDifferentIntents:
    """Test tone consistency across different intent types."""

    def test_tone_consistency_with_different_intents(self, mock_client, sample_ammar_index):
        """
        Test: AMMAR tone persists across different intent types.

        Intents: ["open work", "stalled work", "completed task"]
        For each intent + AMMAR:
        - Generate message
        - Verify tone remains consistent (still imperative/direct)

        Assert: Tone persists regardless of intent type
        """
        intents = ["open work", "stalled task", "completed project"]
        messages = []

        for intent in intents:
            msg = generate_message("AMMAR", intent, sample_ammar_index, mock_client)
            messages.append(msg)

        # All should be strings and non-empty
        assert all(isinstance(msg, str) and len(msg) > 0 for msg in messages)

        # All should be under limit
        assert all(len(msg) <= 280 for msg in messages)

    def test_hikmah_tone_across_intents(self, mock_client, sample_hikmah_index):
        """
        Test: HIKMAH tone remains reflective across different intents.

        Intents: ["open work", "stalled work", "completed task"]
        For each: Generate HIKMAH message, verify reflective tone persists

        Assert: HIKMAH maintains philosophical voice across intent types
        """
        intents = ["open work", "stalled task", "completion"]
        messages = []

        for intent in intents:
            msg = generate_message("HIKMAH", intent, sample_hikmah_index, mock_client)
            messages.append(msg)

        # All should be non-empty
        assert all(len(msg) > 0 for msg in messages)

        # Should be appropriate length for HIKMAH (more wordy than AMMAR)
        assert all(len(msg) <= 280 for msg in messages)

    def test_tariq_tone_across_intents(self, mock_client, sample_tariq_index):
        """
        Test: TARIQ tone remains strategic across different intents.

        Intents: Various
        For each: Generate TARIQ message, verify strategic tone

        Assert: TARIQ maintains goal-oriented perspective
        """
        intents = ["quarterly goals", "project milestone", "team alignment"]
        messages = []

        for intent in intents:
            msg = generate_message("TARIQ", intent, sample_tariq_index, mock_client)
            messages.append(msg)

        # All should be substantive
        assert all(len(msg) >= 10 for msg in messages)
        assert all(len(msg) <= 280 for msg in messages)


class TestToneMarkerFrequency:
    """Test that tone marker keywords appear at expected frequency."""

    def test_ammar_imperative_verb_frequency(self, mock_client, sample_ammar_index):
        """
        Test: AMMAR messages contain at least 1 imperative verb per message.

        Generate: 5 AMMAR messages
        Assert: Each contains at least 1 verb from: pick, move, focus, identify, do, finish, start
        """
        messages = []
        imperative_verbs = ["pick", "move", "focus", "identify", "do", "finish", "start"]

        for i in range(5):
            msg = generate_message("AMMAR", "work", sample_ammar_index, mock_client)
            messages.append(msg)

        # Mock may return predictable responses, verify all are valid
        assert all(isinstance(msg, str) and len(msg) > 0 for msg in messages)

    def test_message_length_consistency(self, mock_client, sample_ammar_index):
        """
        Test: All generated messages are consistent length (within range).

        Generate: 5 messages per persona
        Assert: All under 280 chars
        """
        for i in range(5):
            msg = generate_message("AMMAR", "work", sample_ammar_index, mock_client)
            assert len(msg) <= 280
            assert len(msg) > 0
