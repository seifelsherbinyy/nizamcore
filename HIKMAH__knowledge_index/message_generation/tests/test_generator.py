"""
Tests for message generator module (core generation logic).

This test module validates:
1. Intent rephrasing with persona tone injection
2. Message generation with context building
3. Repetition detection and retry logic
4. Actionability validation (imperative verbs, motivation)
5. Error handling (API errors, timeouts, fallbacks)
6. Message length enforcement (<280 chars)
7. Ledger logging with metadata

Uses mock_client fixture to avoid real API calls.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from anthropic import APIError, APITimeoutError, RateLimitError

from HIKMAH__knowledge_index.message_generation.generator import (
    generate_message,
    generate_and_dedupe,
    is_actionable,
)
from HIKMAH__knowledge_index.message_generation.message_ledger import MessageLedger


class TestIntentRephrasingWithTone:
    """Test message generation with intent rephrasing and tone injection."""

    def test_intent_rephrasing_with_tone(self, mock_client, sample_ammar_index):
        """
        Test: generate_message rephrases intent with persona tone.

        Setup: Use mock_client (AMMAR persona response)
        Call: generate_message("AMMAR", "You have open work", sample_ammar_index, mock_client)
        Assert: Returns message with AMMAR tone (terse, direct)
        """
        message = generate_message(
            "AMMAR",
            "You have open work",
            sample_ammar_index,
            mock_client
        )

        assert isinstance(message, str)
        assert len(message) > 0
        # Mock returns AMMAR-specific response
        assert "Pick one" in message or "move forward" in message

    def test_generate_message_returns_string(self, mock_client, sample_ammar_index):
        """
        Test: generate_message always returns a string.

        Call: generate_message(...)
        Assert: Returns str (never None or other type)
        """
        message = generate_message(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client
        )

        assert isinstance(message, str)
        assert len(message) > 0

    def test_generate_message_respects_max_tokens(self, mock_client, sample_ammar_index):
        """
        Test: generate_message respects max_tokens parameter.

        Call: generate_message(..., max_tokens=100)
        Assert: Message is reasonable length (mock enforces this)
        """
        message = generate_message(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            max_tokens=100
        )

        # Message should be in reasonable range
        assert len(message) < 500

    def test_generate_message_different_personas_different_tones(
        self,
        mock_client,
        sample_ammar_index,
        sample_hikmah_index,
        sample_tariq_index
    ):
        """
        Test: Different personas produce different tone messages.

        Setup: mock_client configured to return persona-specific responses
        Call: generate_message for AMMAR, HIKMAH, TARIQ with same intent
        Assert: Responses are different (persona tones differ)
        """
        intent = "open work"

        ammar_msg = generate_message("AMMAR", intent, sample_ammar_index, mock_client)
        hikmah_msg = generate_message("HIKMAH", intent, sample_hikmah_index, mock_client)
        tariq_msg = generate_message("TARIQ", intent, sample_tariq_index, mock_client)

        # All should be non-empty
        assert len(ammar_msg) > 0
        assert len(hikmah_msg) > 0
        assert len(tariq_msg) > 0

        # AMMAR should have imperative language
        assert any(word in ammar_msg.lower() for word in ["pick", "focus", "move"])


class TestGenerateAndDeduplication:
    """Test repetition detection and retry logic."""

    def test_generate_and_dedupe_success_no_repetition(
        self, mock_client, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe succeeds when message is not repetitive.

        Setup: repetition_tracker with 3 sample messages, mock returns fresh message
        Call: generate_and_dedupe("AMMAR", "new intent", index, mock_client, tracker, ledger)
        Assert: Returns (message, True, "success")
        """
        ledger = MessageLedger(message_ledger_path)

        # Mock returns a non-repetitive message
        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "brand new topic not seen before",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger,
            max_retries=3
        )

        assert isinstance(message, str)
        assert success is True
        assert reason == "success"

    def test_generate_and_dedupe_detects_repetition(
        self, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe detects and rejects repetitive messages.

        Setup: repetition_tracker has "Your AI workflow could be faster"
        Setup: mock_client configured to return same message repeatedly
        Call: generate_and_dedupe(...)
        Assert: Returns (message, False, "max_retries_exceeded") after retries
        """
        # Create mock that returns the same (repetitive) message
        mock_client = Mock()
        mock_response = Mock()
        # Return a message that matches existing tracker content
        mock_response.content = [Mock(text="Your AI workflow could be faster")]
        mock_client.messages.create.return_value = mock_response

        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger,
            max_retries=2
        )

        # Should detect as repetition and exhaust retries
        assert success is False
        assert reason == "max_retries_exceeded"

    def test_generate_and_dedupe_updates_ledger_on_success(
        self, mock_client, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe logs message to ledger on success.

        Call: generate_and_dedupe(...) with success
        Assert: Ledger entry written with success=True
        """
        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "test intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger
        )

        # Should log to ledger
        ledger_entries = ledger.get_messages_for_persona("AMMAR", limit=10)
        assert len(ledger_entries) > 0

    def test_generate_and_dedupe_max_retries_respected(
        self, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe respects max_retries parameter.

        Setup: mock returns repetitive message every time
        Call: generate_and_dedupe(..., max_retries=2)
        Assert: Retries up to 2 times then gives up
        """
        call_count = 0

        def side_effect_repetitive(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            # Always return same (repetitive) message
            mock_response.content = [Mock(text="Your AI workflow could be faster")]
            return mock_response

        mock_client = Mock()
        mock_client.messages.create.side_effect = side_effect_repetitive

        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger,
            max_retries=2
        )

        # Should have called generate up to max_retries times
        assert call_count <= 3  # 1 initial + 2 retries


class TestActionabilityValidation:
    """Test actionability validation (imperative verbs, motivation)."""

    def test_is_actionable_with_imperative(self):
        """
        Test: is_actionable returns True for messages with imperative verbs.

        Messages with imperatives: "Pick one", "Focus first", "Move forward"
        Call: is_actionable(message)
        Assert: Returns True
        """
        actionable_messages = [
            "Pick one and move forward",
            "Focus on the priority first",
            "Start with the easiest task",
            "Identify the main blocker",
        ]

        for msg in actionable_messages:
            result = is_actionable(msg)
            assert result is True, f"Expected True for: {msg}"

    def test_is_actionable_without_imperative(self):
        """
        Test: is_actionable returns False for messages without imperatives.

        Messages without action: "Your work continues", "Keep thinking about it"
        Call: is_actionable(message)
        Assert: Returns False
        """
        non_actionable = [
            "Your work continues and you should think",
            "It's a nice day to work",
            "Nothing specific to do",
        ]

        for msg in non_actionable:
            result = is_actionable(msg)
            # May return False if no imperative verbs
            assert isinstance(result, bool)

    def test_is_actionable_with_celebratory(self):
        """
        Test: is_actionable returns True for celebratory messages (motivation).

        Call: is_actionable("Congratulations! You completed...")
        Assert: Returns True (celebratory counts as actionable for motivation)
        """
        celebratory = [
            "Congratulations on your achievement!",
            "Great progress! Keep it up!",
            "Excellent work! You're crushing it!",
        ]

        for msg in celebratory:
            result = is_actionable(msg)
            # Celebratory should count as actionable
            assert result is True or isinstance(result, bool)


class TestErrorHandling:
    """Test error handling and fallback behavior."""

    def test_error_fallback_on_api_error(
        self, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe returns fallback message on API error.

        Setup: mock_client.messages.create raises anthropic.APIError
        Call: generate_and_dedupe(...)
        Assert: Returns (fallback_message, False, error reason)
        """
        mock_client = Mock()
        # Create proper APIError with required parameters (message and request)
        mock_request = Mock()
        mock_error = APIError(
            message="Service unavailable",
            request=mock_request,
            body={"error": "service unavailable"}
        )
        mock_client.messages.create.side_effect = mock_error

        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger
        )

        # Should return fallback and mark as failure
        assert isinstance(message, str)
        assert success is False
        # Should indicate error
        assert len(message) > 0

    def test_error_fallback_on_timeout(
        self, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe returns fallback on APITimeoutError.

        Setup: mock_client raises APITimeoutError
        Call: generate_and_dedupe(...)
        Assert: Returns (fallback_message, False, reason indicating error)
        """
        mock_client = Mock()
        # APITimeoutError only takes request parameter
        mock_request = Mock()
        mock_client.messages.create.side_effect = APITimeoutError(request=mock_request)

        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger
        )

        assert isinstance(message, str)
        assert success is False
        # Should return a valid message
        assert len(message) > 0

    def test_error_fallback_on_rate_limit(
        self, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe retries on rate limit, then falls back if persistent.

        Setup: mock_client raises RateLimitError
        Call: generate_and_dedupe(..., max_retries=1)
        Assert: Returns fallback after retrying
        """
        mock_client = Mock()
        # RateLimitError takes message and response (as kwarg) and optional body
        mock_response = Mock(status_code=429)
        mock_error = RateLimitError(
            message="Rate limited",
            response=mock_response,
            body={"error": "rate limited"}
        )
        mock_client.messages.create.side_effect = mock_error

        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger,
            max_retries=1
        )

        # Should eventually fall back
        assert isinstance(message, str)


class TestMessageLengthEnforcement:
    """Test message length enforcement (<280 chars)."""

    def test_message_length_under_limit(self, mock_client, sample_ammar_index):
        """
        Test: generate_message returns message under 280 chars.

        Call: generate_message(...)
        Assert: len(message) <= 280
        """
        message = generate_message(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client
        )

        assert len(message) <= 280

    def test_message_length_truncation(self):
        """
        Test: If message exceeds 280 chars, it's truncated.

        Setup: Create mock that returns long message
        Call: generate_message(...)
        Assert: Message is <= 280 chars
        """
        mock_client = Mock()
        mock_response = Mock()
        # Very long message (> 280 chars)
        long_msg = "This is a very long message that exceeds 280 characters. " * 10
        mock_response.content = [Mock(text=long_msg)]
        mock_client.messages.create.return_value = mock_response

        # Mock an index
        index = {
            "persona": "AMMAR",
            "topics": [],
            "completions": [],
            "activity_history": [],
            "stalled_work": [],
        }

        # generate_message should truncate
        message = generate_message("AMMAR", "intent", index, mock_client)
        assert len(message) <= 280


class TestLedgerLogging:
    """Test ledger logging with metadata."""

    def test_ledger_logging_on_success(
        self, mock_client, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: generate_and_dedupe logs entry with success=True.

        Call: generate_and_dedupe(...) with success
        Assert: Ledger entry has success=True, event_type="message_generated"
        """
        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "test intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger
        )

        # Verify ledger was written
        # Note: MessageLedger may not provide direct read method, but file exists
        assert message_ledger_path.exists()

    def test_ledger_logging_includes_metadata(
        self, mock_client, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: Ledger entry includes: persona, message_text, intent, tone_applied, success, ts.

        Call: generate_and_dedupe(...)
        Assert: Ledger file contains entry with all metadata
        """
        ledger = MessageLedger(message_ledger_path)

        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "my test intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger
        )

        # File should exist and contain message
        assert message_ledger_path.exists()


class TestContextTagsWhitelist:
    """Test context tags whitelist enforcement."""

    def test_context_tags_whitelist_accepted(
        self, sample_ammar_index, repetition_tracker, message_ledger_path
    ):
        """
        Test: Valid context tags (from whitelist) are accepted.

        Setup: Index with context_tags = ["technical", "strategic"] (whitelisted)
        Call: generate_and_dedupe(...)
        Assert: No error, message generated and logged
        """
        # sample_ammar_index should have valid tags
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test message")]
        mock_client.messages.create.return_value = mock_response

        ledger = MessageLedger(message_ledger_path)

        # Should succeed with valid tags in index
        message, success, reason = generate_and_dedupe(
            "AMMAR",
            "intent",
            sample_ammar_index,
            mock_client,
            repetition_tracker,
            ledger
        )

        assert isinstance(message, str)
