"""
test_orchestrator.py — DeliveryOrchestrator Test Suite (Wave 2)

Tests for:
- Basic delivery flow (message_id assignment, timestamps, ledger logging)
- Error handling (relay failures, network errors, pre-send crash safety)
- Monitor spawning (called with correct args after successful delivery)
- Integration (full flow: send → ledger → monitor → response)
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from .conftest import (
    SAMPLE_CHAT_ID,
    SAMPLE_PERSONA,
    SAMPLE_INTENT,
    SAMPLE_CONTEXT_TAGS,
    SAMPLE_MESSAGE_TEXT,
    SAMPLE_TELEGRAM_MESSAGE_ID,
    MockTelegramRelay,
)


# ============================================================================
# Basic delivery flow tests
# ============================================================================


class TestDeliverSuccessBasic:
    """Basic delivery flow — happy path."""

    def test_deliver_success_returns_success_status(
        self, delivery_orchestrator, temp_ledger
    ):
        """deliver() with working relay returns DeliveryResult with status='success'."""
        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "success"
        assert result.error is None

    def test_deliver_assigns_unique_message_id(
        self, delivery_orchestrator, temp_ledger
    ):
        """Each deliver() call produces a unique message_id starting with 'MSG-'."""
        result1 = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )
        result2 = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text="Second message.",
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result1.message_id.startswith("MSG-")
        assert result2.message_id.startswith("MSG-")
        assert result1.message_id != result2.message_id

    def test_deliver_logs_sent_at_and_delivered_at(
        self, delivery_orchestrator, temp_ledger
    ):
        """Successful delivery records both sent_at and delivered_at timestamps."""
        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.sent_at is not None
        assert result.delivered_at is not None
        # delivered_at must come after sent_at
        assert result.delivered_at >= result.sent_at

    def test_deliver_maps_telegram_message_id(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """DeliveryResult.telegram_message_id matches relay response message_id."""
        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.telegram_message_id == SAMPLE_TELEGRAM_MESSAGE_ID

    def test_deliver_context_tags_stored_in_ledger(
        self, delivery_orchestrator, temp_ledger
    ):
        """context_tags are stored in the ledger delivery entry."""
        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=["technical", "strategic"],
        )

        # Read the ledger to verify context_tags
        lines = temp_ledger.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines if line]
        success_entries = [e for e in entries if e.get("status") == "success"]
        assert len(success_entries) >= 1
        assert "technical" in success_entries[0]["context_tags"]
        assert "strategic" in success_entries[0]["context_tags"]


# ============================================================================
# Error handling tests
# ============================================================================


class TestDeliverErrorHandling:
    """Tests for relay failures and error logging."""

    def test_deliver_relay_error_returns_failure_result(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """RuntimeError from relay → returns failure DeliveryResult (no exception)."""
        mock_relay_client.send_error = RuntimeError("Telegram API returned ok=False: chat not found")

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "failure"
        assert "chat not found" in result.error
        assert result.telegram_message_id is None
        assert result.delivered_at is None

    def test_deliver_network_timeout_returns_failure(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """ConnectionError from relay → failure result with error message."""
        mock_relay_client.send_error = ConnectionError("Network timeout: relay unreachable")

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "failure"
        assert result.error is not None
        assert "timeout" in result.error.lower()

    def test_deliver_failure_pre_send_log_exists(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """
        Crash-safe: message_id is logged BEFORE relay call.
        Even on relay failure, the ledger contains a pre-send entry.
        """
        mock_relay_client.send_error = RuntimeError("Telegram API error")

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        # Ledger must exist and have entries (pre-send pending + failure)
        assert temp_ledger.exists()
        lines = [l for l in temp_ledger.read_text().strip().split("\n") if l]
        entries = [json.loads(l) for l in lines]

        # Verify our message_id appears in the ledger
        msg_ids = [e.get("message_id") for e in entries]
        assert result.message_id in msg_ids

        # There should be a failure entry with our message_id
        failure_entries = [e for e in entries if e.get("status") == "failure"]
        assert len(failure_entries) >= 1

    def test_deliver_invalid_chat_id_returns_failure(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """Invalid chat_id causes relay to raise → failure result returned."""
        mock_relay_client.send_error = ValueError("Invalid chat_id: must be integer")

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=-1,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "failure"
        assert result.error is not None


# ============================================================================
# Monitor spawning tests
# ============================================================================


class TestMonitorSpawning:
    """Tests verifying ResponseMonitor is called correctly after delivery."""

    def test_deliver_spawns_response_monitor(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """After successful delivery, response_monitor.monitor() is called."""
        mock_monitor = MagicMock()
        delivery_orchestrator.response_monitor = mock_monitor

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "success"
        mock_monitor.monitor.assert_called_once()

    def test_deliver_monitor_receives_correct_message_id(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """ResponseMonitor receives our NIZAM message_id (not Telegram's message_id)."""
        mock_monitor = MagicMock()
        delivery_orchestrator.response_monitor = mock_monitor

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        call_kwargs = mock_monitor.monitor.call_args[1]
        assert call_kwargs["message_id"] == result.message_id
        assert call_kwargs["message_id"].startswith("MSG-")

    def test_deliver_monitor_receives_persona(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """ResponseMonitor receives persona name for ledger logging."""
        mock_monitor = MagicMock()
        delivery_orchestrator.response_monitor = mock_monitor

        delivery_orchestrator.deliver(
            persona="HIKMAH",
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        call_kwargs = mock_monitor.monitor.call_args[1]
        assert call_kwargs["persona"] == "HIKMAH"

    def test_deliver_no_monitor_without_response_monitor_set(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """If response_monitor is None, no monitor is spawned (no error)."""
        delivery_orchestrator.response_monitor = None

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        # Should succeed without error
        assert result.status == "success"

    def test_deliver_monitor_not_spawned_on_failure(
        self, delivery_orchestrator, mock_relay_client, temp_ledger
    ):
        """ResponseMonitor is NOT spawned when delivery fails."""
        mock_monitor = MagicMock()
        delivery_orchestrator.response_monitor = mock_monitor
        mock_relay_client.send_error = RuntimeError("Relay error")

        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "failure"
        mock_monitor.monitor.assert_not_called()


# ============================================================================
# Integration tests
# ============================================================================


class TestDeliveryIntegration:
    """Full flow integration tests."""

    def test_deliver_full_ledger_entries(
        self, delivery_orchestrator, temp_ledger
    ):
        """
        Full flow: deliver() → ledger contains pending + success entries.
        Pre-send entry (pending) + post-send entry (success) both present.
        """
        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.status == "success"

        lines = [l for l in temp_ledger.read_text().strip().split("\n") if l]
        entries = [json.loads(l) for l in lines]

        # Should have both pending and success entries
        statuses = [e.get("status") for e in entries]
        assert "pending" in statuses
        assert "success" in statuses

        # All entries should have the same message_id
        msg_ids = set(e.get("message_id") for e in entries)
        assert result.message_id in msg_ids

    def test_deliver_multiple_messages_have_unique_ids(
        self, delivery_orchestrator, temp_ledger
    ):
        """
        Send 3 messages in sequence — each gets a unique message_id.
        All 3 message_ids must be distinct.
        """
        results = []
        for i in range(3):
            result = delivery_orchestrator.deliver(
                persona=SAMPLE_PERSONA,
                message_text=f"Message {i + 1}",
                intent=SAMPLE_INTENT,
                chat_id=SAMPLE_CHAT_ID,
                context_tags=SAMPLE_CONTEXT_TAGS,
            )
            results.append(result)

        # All successful
        assert all(r.status == "success" for r in results)

        # All unique message_ids
        msg_ids = [r.message_id for r in results]
        assert len(set(msg_ids)) == 3

    def test_deliver_result_fields_complete(
        self, delivery_orchestrator, temp_ledger
    ):
        """DeliveryResult has all expected fields populated on success."""
        result = delivery_orchestrator.deliver(
            persona=SAMPLE_PERSONA,
            message_text=SAMPLE_MESSAGE_TEXT,
            intent=SAMPLE_INTENT,
            chat_id=SAMPLE_CHAT_ID,
            context_tags=SAMPLE_CONTEXT_TAGS,
        )

        assert result.message_id is not None
        assert result.telegram_message_id is not None
        assert result.sent_at is not None
        assert result.delivered_at is not None
        assert result.status == "success"
        assert result.error is None
