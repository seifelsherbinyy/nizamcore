"""
conftest.py — Shared fixtures and mocks for Phase 17 delivery tests (Wave 2)

Provides:
- MockTelegramRelay: Simulates tg_send_message / tg_get_updates
- mock_relay_client: Fixture returning pre-configured MockTelegramRelay
- temp_ledger: Temporary JSONL ledger path (test isolation)
- delivery_orchestrator: Pre-configured DeliveryOrchestrator with mocked relay
- response_monitor: Pre-configured ResponseMonitor with mocked relay
- SAMPLE_* constants for consistent test values
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import List, Optional

# ============================================================================
# Constants
# ============================================================================

SAMPLE_CHAT_ID: int = 987654321
SAMPLE_PERSONA: str = "AMMAR"
SAMPLE_MESSAGE_ID: str = "MSG-20260621093045123-A7F2E8CD"
SAMPLE_TELEGRAM_MESSAGE_ID: int = 12345
SAMPLE_INTENT: str = "open_work"
SAMPLE_CONTEXT_TAGS: List[str] = ["technical"]
SAMPLE_MESSAGE_TEXT: str = "Your AI work is stalled. Pick one task and move forward."
# Note: Use fresh_sent_at() in tests that need an active window.
# SAMPLE_SENT_AT is a historical timestamp used for non-timing-sensitive tests.
SAMPLE_SENT_AT: str = "2026-06-21T09:30:45+00:00"


# ============================================================================
# Mock classes
# ============================================================================


class MockTelegramRelay:
    """
    Simulates TelegramRelayClient behavior for tests.

    Configurable responses:
    - send_message: Returns success response by default, or raises on send_error
    - get_updates: Returns empty list by default, or configured updates
    - Tracks call history for verification

    Attributes
    ----------
    send_message_response : dict
        Response returned by send_message(). Defaults to success with
        message_id=SAMPLE_TELEGRAM_MESSAGE_ID.
    send_error : Optional[Exception]
        If set, send_message() raises this exception instead of returning.
    updates_to_return : List[List[dict]]
        Queue of update lists returned by successive get_updates() calls.
        Each call pops the first list. Empty if exhausted.
    send_calls : list
        Recorded calls to send_message() for assertion.
    get_updates_calls : list
        Recorded calls to get_updates() for assertion.
    """

    def __init__(self) -> None:
        self.send_message_response: dict = {
            "ok": True,
            "result": {
                "message_id": SAMPLE_TELEGRAM_MESSAGE_ID,
                "chat": {"id": SAMPLE_CHAT_ID},
                "text": SAMPLE_MESSAGE_TEXT,
                "date": 1750502245,
            },
        }
        self.send_error: Optional[Exception] = None
        self.updates_to_return: List[List[dict]] = []
        self.send_calls: list = []
        self.get_updates_calls: list = []
        self.check_reply_calls: list = []

    def send_message(self, chat_id: int, text: str, parse_mode=None) -> dict:
        """Simulate send_message — returns configured response or raises."""
        self.send_calls.append({"chat_id": chat_id, "text": text, "parse_mode": parse_mode})
        if self.send_error is not None:
            raise self.send_error
        return self.send_message_response

    def get_updates(self, offset: int, timeout: int = 25) -> List[dict]:
        """Simulate get_updates — returns next configured updates batch."""
        self.get_updates_calls.append({"offset": offset, "timeout": timeout})
        if self.updates_to_return:
            return self.updates_to_return.pop(0)
        return []

    def check_reply_to_message_id(self, update: dict) -> Optional[int]:
        """Simulate check_reply_to_message_id — delegates to real logic."""
        self.check_reply_calls.append(update)
        return (
            update.get("message", {})
            .get("reply_to_message", {})
            .get("message_id")
        )


def make_reply_update(
    update_id: int,
    reply_to_message_id: int,
    text: str = "OK, on it",
    message_id: int = 99999,
) -> dict:
    """
    Factory: Create a Telegram update dict representing a reply to a message.

    Parameters
    ----------
    update_id : int
        Telegram update_id.
    reply_to_message_id : int
        The message_id being replied to.
    text : str
        Reply text content.
    message_id : int
        The reply message's own message_id.
    """
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "text": text,
            "date": 1750502300,
            "reply_to_message": {
                "message_id": reply_to_message_id,
            },
        },
    }


def fresh_sent_at() -> str:
    """
    Return current UTC time as ISO 8601 string for tests needing an active window.

    Tests that set window_seconds=N need sent_at to be NOW so that the deadline
    is N seconds in the future (not in the past like SAMPLE_SENT_AT).
    """
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def make_non_reply_update(update_id: int, text: str = "Hello", message_id: int = 77777) -> dict:
    """
    Factory: Create a Telegram update dict with no reply_to_message field.

    Used to simulate unrelated messages.
    """
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "text": text,
            "date": 1750502300,
        },
    }


# ============================================================================
# Pytest fixtures
# ============================================================================


@pytest.fixture
def mock_relay_client() -> MockTelegramRelay:
    """Pre-configured MockTelegramRelay instance."""
    return MockTelegramRelay()


@pytest.fixture
def temp_ledger(tmp_path: Path) -> Path:
    """
    Temporary ledger file path for test isolation.

    Returns a Path in a temporary directory. Each test gets its own
    isolated ledger file — no shared state between tests.
    """
    return tmp_path / "test_delivery_ledger.jsonl"


@pytest.fixture
def delivery_orchestrator(mock_relay_client: MockTelegramRelay, temp_ledger: Path):
    """
    Pre-configured DeliveryOrchestrator with mocked relay client.

    Patches TelegramRelayClient to use MockTelegramRelay.
    response_monitor is None (not set) — configure per test if needed.
    """
    from HIKMAH__knowledge_index.delivery.delivery_orchestrator import DeliveryOrchestrator

    with patch(
        "HIKMAH__knowledge_index.delivery.delivery_orchestrator.TelegramRelayClient",
        return_value=mock_relay_client,
    ):
        orch = DeliveryOrchestrator(
            telegram_token="test-token-12345",
            ledger_path=temp_ledger,
        )
        # Store mock for assertions in tests
        orch._relay_client = mock_relay_client
    return orch


@pytest.fixture
def response_monitor(mock_relay_client: MockTelegramRelay, temp_ledger: Path):
    """
    Pre-configured ResponseMonitor with mocked relay client.

    Passes relay_client directly (injection path — no patch needed).
    """
    from HIKMAH__knowledge_index.delivery.response_monitor import ResponseMonitor

    return ResponseMonitor(
        telegram_token="test-token-12345",
        ledger_path=temp_ledger,
        relay_client=mock_relay_client,
        default_window_seconds=3600,
    )
