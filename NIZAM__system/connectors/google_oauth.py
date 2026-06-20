"""Google OAuth-backed Calendar, Tasks, and Gmail adapters."""

from __future__ import annotations



import base64

import json

import os

from email.mime.text import MIMEText

from pathlib import Path

from typing import Any



# Write-capable scopes (single token for Calendar, Tasks, Gmail).

ALL_SCOPES: tuple[str, ...] = (

    "https://www.googleapis.com/auth/calendar",

    "https://www.googleapis.com/auth/tasks",

    "https://www.googleapis.com/auth/gmail.modify",

    "https://www.googleapis.com/auth/gmail.compose",

)



# Legacy aliases for read helpers.

CALENDAR_SCOPES = ALL_SCOPES[:1]

TASKS_SCOPES = ALL_SCOPES[1:2]

GMAIL_SCOPES = ALL_SCOPES[2:4]





def _paths() -> tuple[Path | None, Path | None]:

    secrets = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "").strip()

    token = os.environ.get("GOOGLE_OAUTH_TOKEN", "").strip()

    secrets_path = Path(secrets) if secrets else None

    token_path = Path(token) if token else None

    return secrets_path, token_path





def credentials_available() -> bool:

    secrets_path, token_path = _paths()

    return bool(

        secrets_path

        and token_path

        and secrets_path.exists()

        and token_path.exists()

    )





def load_credentials(scopes: tuple[str, ...] | None = None):

    from google.auth.transport.requests import Request

    from google.oauth2.credentials import Credentials



    use_scopes = scopes or ALL_SCOPES

    secrets_path, token_path = _paths()

    if not secrets_path or not token_path or not token_path.exists():

        raise RuntimeError("Google OAuth token files are not configured")

    creds = Credentials.from_authorized_user_file(str(token_path), use_scopes)

    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds





def build_service(api: str, version: str, scopes: tuple[str, ...] | None = None):

    from googleapiclient.discovery import build



    creds = load_credentials(scopes or ALL_SCOPES)

    return build(api, version, credentials=creds, cache_discovery=False)





def token_scopes() -> set[str]:

    _, token_path = _paths()

    if not token_path or not token_path.exists():

        return set()

    try:

        payload = json.loads(token_path.read_text(encoding="utf-8"))

    except (json.JSONDecodeError, OSError):

        return set()

    raw = payload.get("scopes") or []

    if isinstance(raw, str):

        return {raw}

    return {str(item) for item in raw}





def scopes_sufficient_for_write() -> bool:

    present = token_scopes()

    return all(scope in present for scope in ALL_SCOPES)





def refresh_token_if_expired() -> bool:

    """Refresh OAuth token file when expired. Returns True if refresh attempted."""

    scopes = tuple(token_scopes()) or ALL_SCOPES

    try:

        load_credentials(scopes)

        return True

    except Exception:

        return False





def _classify_google_error(exc: Exception) -> str:

    reason = type(exc).__name__

    message = str(exc)

    if "accessNotConfigured" in message or "has not been used in project" in message:

        return "google_apis_not_enabled"

    if "insufficientPermissions" in message or "Insufficient Permission" in message:

        return "insufficient_scope"

    if "HttpError" in reason:

        return "google_api_error"

    return reason





def read_calendar_events(*, max_results: int = 10) -> list[dict[str, Any]]:

    service = build_service("calendar", "v3", CALENDAR_SCOPES)

    payload = (

        service.events()

        .list(calendarId="primary", maxResults=max_results, singleEvents=True, orderBy="startTime")

        .execute()

    )

    rows: list[dict[str, Any]] = []

    for item in payload.get("items", []):

        rows.append(

            {

                "id": item.get("id"),

                "title": item.get("summary"),

                "start": (item.get("start") or {}).get("dateTime")

                or (item.get("start") or {}).get("date"),

                "end": (item.get("end") or {}).get("dateTime")

                or (item.get("end") or {}).get("date"),

                "source": "google_calendar",

            }

        )

    return rows





def create_calendar_event(

    *,

    title: str,

    start: str,

    end: str,

    description: str | None = None,

    calendar_id: str = "primary",

) -> dict[str, Any]:

    service = build_service("calendar", "v3", CALENDAR_SCOPES)

    body: dict[str, Any] = {

        "summary": title,

        "start": {"dateTime": start} if "T" in start else {"date": start},

        "end": {"dateTime": end} if "T" in end else {"date": end},

    }

    if description:

        body["description"] = description

    item = service.events().insert(calendarId=calendar_id, body=body).execute()

    return {

        "id": item.get("id"),

        "title": item.get("summary"),

        "start": (item.get("start") or {}).get("dateTime") or (item.get("start") or {}).get("date"),

        "end": (item.get("end") or {}).get("dateTime") or (item.get("end") or {}).get("date"),

        "source": "google_calendar",

    }





def update_calendar_event(

    *,

    event_id: str,

    calendar_id: str = "primary",

    **fields: Any,

) -> dict[str, Any]:

    service = build_service("calendar", "v3", CALENDAR_SCOPES)

    body: dict[str, Any] = {}

    if "title" in fields:

        body["summary"] = fields["title"]

    if "description" in fields:

        body["description"] = fields["description"]

    if "start" in fields:

        start = fields["start"]

        body["start"] = {"dateTime": start} if "T" in str(start) else {"date": start}

    if "end" in fields:

        end = fields["end"]

        body["end"] = {"dateTime": end} if "T" in str(end) else {"date": end}

    item = (

        service.events()

        .patch(calendarId=calendar_id, eventId=event_id, body=body)

        .execute()

    )

    return {

        "id": item.get("id"),

        "title": item.get("summary"),

        "source": "google_calendar",

    }





def delete_calendar_event(*, event_id: str, calendar_id: str = "primary") -> dict[str, Any]:

    service = build_service("calendar", "v3", CALENDAR_SCOPES)

    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

    return {"id": event_id, "deleted": True, "source": "google_calendar"}





def read_tasks(*, max_results: int = 20) -> list[dict[str, Any]]:

    service = build_service("tasks", "v1", TASKS_SCOPES)

    lists = service.tasklists().list(maxResults=5).execute().get("items", [])

    rows: list[dict[str, Any]] = []

    for task_list in lists:

        tasks = (

            service.tasks()

            .list(tasklist=task_list["id"], maxResults=max_results, showCompleted=False)

            .execute()

            .get("items", [])

        )

        for task in tasks:

            rows.append(

                {

                    "id": task.get("id"),

                    "title": task.get("title"),

                    "due": task.get("due"),

                    "status": task.get("status"),

                    "list": task_list.get("title"),

                    "tasklist_id": task_list.get("id"),

                    "source": "google_tasks",

                }

            )

    return rows





def _default_tasklist_id(service) -> str:

    lists = service.tasklists().list(maxResults=1).execute().get("items", [])

    if not lists:

        raise RuntimeError("No Google Tasks list found")

    return lists[0]["id"]





def create_task(

    *,

    title: str,

    tasklist_id: str | None = None,

    due: str | None = None,

    notes: str | None = None,

) -> dict[str, Any]:

    service = build_service("tasks", "v1", TASKS_SCOPES)

    list_id = tasklist_id or _default_tasklist_id(service)

    body: dict[str, Any] = {"title": title}

    if due:

        body["due"] = due

    if notes:

        body["notes"] = notes

    item = service.tasks().insert(tasklist=list_id, body=body).execute()

    return {

        "id": item.get("id"),

        "title": item.get("title"),

        "tasklist_id": list_id,

        "status": item.get("status"),

        "source": "google_tasks",

    }





def update_task(

    *,

    task_id: str,

    tasklist_id: str,

    **fields: Any,

) -> dict[str, Any]:

    service = build_service("tasks", "v1", TASKS_SCOPES)

    body: dict[str, Any] = {}

    for key in ("title", "due", "notes", "status"):

        if key in fields:

            body[key] = fields[key]

    item = service.tasks().patch(tasklist=tasklist_id, task=task_id, body=body).execute()

    return {

        "id": item.get("id"),

        "title": item.get("title"),

        "status": item.get("status"),

        "tasklist_id": tasklist_id,

        "source": "google_tasks",

    }





def complete_task(*, task_id: str, tasklist_id: str) -> dict[str, Any]:

    return update_task(task_id=task_id, tasklist_id=tasklist_id, status="completed")





def delete_task(*, task_id: str, tasklist_id: str) -> dict[str, Any]:

    service = build_service("tasks", "v1", TASKS_SCOPES)

    service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()

    return {"id": task_id, "tasklist_id": tasklist_id, "deleted": True, "source": "google_tasks"}





def read_gmail_messages(*, max_results: int = 5, label: str | None = None) -> list[dict[str, Any]]:

    service = build_service("gmail", "v1", GMAIL_SCOPES)

    query = label or os.environ.get("GMAIL_LABEL_FILTER", "").strip()

    kwargs: dict[str, Any] = {"userId": "me", "maxResults": max_results}

    if query:

        kwargs["q"] = f"label:{query}" if ":" not in query else query

    listed = service.users().messages().list(**kwargs).execute()

    rows: list[dict[str, Any]] = []

    for item in listed.get("messages", []):

        msg = (

            service.users()

            .messages()

            .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["Subject", "From"])

            .execute()

        )

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        rows.append(

            {

                "id": item["id"],

                "subject": headers.get("Subject"),

                "from": headers.get("From"),

                "source": "gmail",

            }

        )

    return rows





def _encode_rfc822(*, to: str, subject: str, body: str, sender: str | None = None) -> str:

    message = MIMEText(body)

    message["to"] = to

    message["subject"] = subject

    if sender:

        message["from"] = sender

    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")





def send_message(

    *,

    raw: str | None = None,

    to: str | None = None,

    subject: str | None = None,

    body: str | None = None,

) -> dict[str, Any]:

    service = build_service("gmail", "v1", GMAIL_SCOPES)

    if raw:

        encoded = raw

    elif to and subject is not None and body is not None:

        encoded = _encode_rfc822(to=to, subject=subject, body=body)

    else:

        raise ValueError("send_message requires raw or to/subject/body")

    item = service.users().messages().send(userId="me", body={"raw": encoded}).execute()

    return {"id": item.get("id"), "source": "gmail"}





def trash_message(*, message_id: str) -> dict[str, Any]:

    service = build_service("gmail", "v1", GMAIL_SCOPES)

    item = service.users().messages().trash(userId="me", id=message_id).execute()

    return {"id": item.get("id"), "trashed": True, "source": "gmail"}





def untrash_message(*, message_id: str) -> dict[str, Any]:

    service = build_service("gmail", "v1", GMAIL_SCOPES)

    item = service.users().messages().untrash(userId="me", id=message_id).execute()

    return {"id": item.get("id"), "trashed": False, "source": "gmail"}





def probe_live() -> dict[str, Any]:

    if os.environ.get("NIZAM_LIVE_CONNECTORS_APPROVED") != "1":

        return {"ok": False, "reason": "connectors_not_approved"}

    if not credentials_available():

        return {"ok": False, "reason": "oauth_files_missing"}



    refresh_token_if_expired()

    scopes = token_scopes()

    probes: dict[str, Any] = {

        "scopes": sorted(scopes),

        "write_scopes_ok": scopes_sufficient_for_write(),

    }

    errors: list[str] = []



    if not scopes:

        return {"ok": False, "reason": "oauth_scopes_missing", **probes}



    missing = [s for s in ALL_SCOPES if s not in scopes]

    if missing:

        return {

            "ok": False,

            "reason": "insufficient_scope",

            "missing_scopes": missing,

            **probes,

        }



    calendar_scope = ALL_SCOPES[0]

    tasks_scope = ALL_SCOPES[1]

    gmail_scope = ALL_SCOPES[2]



    if calendar_scope in scopes:

        try:

            probes["calendar_count_sample"] = len(read_calendar_events(max_results=1))

        except Exception as exc:  # noqa: BLE001

            errors.append(_classify_google_error(exc))



    if tasks_scope in scopes:

        try:

            probes["tasks_count_sample"] = len(read_tasks(max_results=1))

        except Exception as exc:  # noqa: BLE001

            errors.append(_classify_google_error(exc))



    if gmail_scope in scopes:

        try:

            probes["gmail_count_sample"] = len(read_gmail_messages(max_results=1))

        except Exception as exc:  # noqa: BLE001

            errors.append(_classify_google_error(exc))



    if errors:

        return {"ok": False, "reason": errors[0], "errors": errors, **probes}

    return {"ok": True, **probes}


