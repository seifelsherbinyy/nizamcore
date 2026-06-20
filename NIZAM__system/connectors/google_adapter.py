"""Google connector adapter implementing CalendarTasksAdapter protocol."""
from __future__ import annotations

from typing import Any

from . import google_oauth


class GoogleConnectorAdapter:
    """Routes connector capabilities to Google API helpers."""

    def _read_handlers(self) -> dict[str, Any]:
        return {
            "read_events": google_oauth.read_calendar_events,
            "read_calendar": google_oauth.read_calendar_events,
            "read_tasks": google_oauth.read_tasks,
            "read_gmail": google_oauth.read_gmail_messages,
        }

    def read(self, capability: str) -> list[dict[str, Any]]:
        handler = self._read_handlers().get(capability)
        if handler is None:
            raise ValueError(f"unsupported read capability: {capability}")
        return handler()

    def write(self, capability: str, payload: dict[str, Any]) -> dict[str, Any]:
        if capability == "create_event":
            return google_oauth.create_calendar_event(
                title=str(payload["title"]),
                start=str(payload["start"]),
                end=str(payload["end"]),
                description=payload.get("description"),
                calendar_id=str(payload.get("calendar_id", "primary")),
            )
        if capability == "update_event":
            fields = {k: v for k, v in payload.items() if k not in {"event_id", "calendar_id"}}
            return google_oauth.update_calendar_event(
                event_id=str(payload["event_id"]),
                calendar_id=str(payload.get("calendar_id", "primary")),
                **fields,
            )
        if capability == "delete_event":
            return google_oauth.delete_calendar_event(
                event_id=str(payload["event_id"]),
                calendar_id=str(payload.get("calendar_id", "primary")),
            )
        if capability == "create_task":
            return google_oauth.create_task(
                title=str(payload["title"]),
                tasklist_id=payload.get("tasklist_id"),
                due=payload.get("due"),
                notes=payload.get("notes"),
            )
        if capability == "update_task":
            task_id = str(payload["task_id"])
            tasklist_id = str(payload["tasklist_id"])
            fields = {
                k: v
                for k, v in payload.items()
                if k not in {"task_id", "tasklist_id"}
            }
            return google_oauth.update_task(
                task_id=task_id,
                tasklist_id=tasklist_id,
                **fields,
            )
        if capability == "complete_task":
            return google_oauth.complete_task(
                task_id=str(payload["task_id"]),
                tasklist_id=str(payload["tasklist_id"]),
            )
        if capability == "delete_task":
            return google_oauth.delete_task(
                task_id=str(payload["task_id"]),
                tasklist_id=str(payload["tasklist_id"]),
            )
        if capability == "send_message":
            return google_oauth.send_message(
                raw=payload.get("raw"),
                to=payload.get("to"),
                subject=payload.get("subject"),
                body=payload.get("body"),
            )
        if capability == "trash_message":
            return google_oauth.trash_message(message_id=str(payload["message_id"]))
        if capability == "untrash_message":
            return google_oauth.untrash_message(message_id=str(payload["message_id"]))
        raise ValueError(f"unsupported write capability: {capability}")


def build_google_adapter() -> GoogleConnectorAdapter:
    return GoogleConnectorAdapter()
