"""Tests for Google connector adapter and OAuth helpers."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from NIZAM__system.connectors import google_oauth
from NIZAM__system.connectors.google_adapter import GoogleConnectorAdapter, build_google_adapter


class GoogleAdapterTests(unittest.TestCase):
    def test_build_google_adapter(self) -> None:
        adapter = build_google_adapter()
        self.assertIsInstance(adapter, GoogleConnectorAdapter)

    @patch("NIZAM__system.connectors.google_oauth.create_calendar_event")
    def test_write_create_event(self, mock_create: MagicMock) -> None:
        mock_create.return_value = {"id": "evt1", "title": "Test"}
        adapter = GoogleConnectorAdapter()
        result = adapter.write(
            "create_event",
            {"title": "Test", "start": "2026-06-14T10:00:00Z", "end": "2026-06-14T11:00:00Z"},
        )
        self.assertEqual(result["id"], "evt1")
        mock_create.assert_called_once()

    @patch("NIZAM__system.connectors.google_oauth.delete_calendar_event")
    def test_write_delete_event(self, mock_delete: MagicMock) -> None:
        mock_delete.return_value = {"id": "evt1", "deleted": True}
        adapter = GoogleConnectorAdapter()
        result = adapter.write("delete_event", {"event_id": "evt1"})
        self.assertTrue(result["deleted"])

    @patch("NIZAM__system.connectors.google_oauth.create_task")
    @patch("NIZAM__system.connectors.google_oauth.delete_task")
    def test_write_task_lifecycle(self, mock_delete: MagicMock, mock_create: MagicMock) -> None:
        mock_create.return_value = {"id": "t1", "tasklist_id": "list1"}
        mock_delete.return_value = {"id": "t1", "deleted": True}
        adapter = GoogleConnectorAdapter()
        created = adapter.write("create_task", {"title": "Smoke"})
        self.assertEqual(created["id"], "t1")
        deleted = adapter.write(
            "delete_task", {"task_id": "t1", "tasklist_id": "list1"}
        )
        self.assertTrue(deleted["deleted"])

    @patch("NIZAM__system.connectors.google_oauth.trash_message")
    def test_write_trash_message(self, mock_trash: MagicMock) -> None:
        mock_trash.return_value = {"id": "m1", "trashed": True}
        adapter = GoogleConnectorAdapter()
        result = adapter.write("trash_message", {"message_id": "m1"})
        self.assertTrue(result["trashed"])

    @patch("NIZAM__system.connectors.google_oauth.read_calendar_events")
    def test_read_calendar(self, mock_read: MagicMock) -> None:
        mock_read.return_value = [{"id": "1"}]
        adapter = GoogleConnectorAdapter()
        rows = adapter.read("read_calendar")
        self.assertEqual(len(rows), 1)

    def test_scopes_sufficient_for_write_empty(self) -> None:
        with patch.object(google_oauth, "token_scopes", return_value=set()):
            self.assertFalse(google_oauth.scopes_sufficient_for_write())

    def test_scopes_sufficient_for_write_full(self) -> None:
        with patch.object(google_oauth, "token_scopes", return_value=set(google_oauth.ALL_SCOPES)):
            self.assertTrue(google_oauth.scopes_sufficient_for_write())

    @patch.dict("os.environ", {"NIZAM_LIVE_CONNECTORS_APPROVED": "1"}, clear=False)
    @patch.object(google_oauth, "credentials_available", return_value=True)
    @patch.object(google_oauth, "token_scopes")
    @patch.object(google_oauth, "refresh_token_if_expired", return_value=True)
    def test_probe_live_insufficient_scope(
        self,
        _refresh: MagicMock,
        mock_scopes: MagicMock,
        _creds: MagicMock,
    ) -> None:
        mock_scopes.return_value = {"https://www.googleapis.com/auth/calendar.readonly"}
        result = google_oauth.probe_live()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "insufficient_scope")


if __name__ == "__main__":
    unittest.main()
