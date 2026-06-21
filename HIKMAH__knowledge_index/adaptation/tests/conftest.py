"""Shared pytest fixtures for adaptation module tests."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import pytest


@pytest.fixture
def tmp_state_path(tmp_path):
    """Path to a temporary ADAPTATION_STATE.jsonl (file not created)."""
    return tmp_path / "ADAPTATION_STATE.jsonl"


@pytest.fixture
def tmp_ledger_path(tmp_path):
    """Path to a temporary ADAPTATION_LEDGER.jsonl (file not created)."""
    return tmp_path / "ADAPTATION_LEDGER.jsonl"


def make_mock_ledger(
    n_deliveries: int,
    n_responses: int,
    persona: str,
    tmp_path: Path,
    ledger_filename: str = "DELIVERY_LEDGER.jsonl",
    days_spread: int = 6,
) -> Path:
    """Write a synthetic DELIVERY_LEDGER.jsonl for testing.

    Creates n_deliveries "delivery" events (all within past 7 days by default)
    and n_responses "response" events for the first n_responses delivery
    message IDs.

    Parameters
    ----------
    n_deliveries : int
        Number of delivery events to create.
    n_responses : int
        Number of response events to create (first n_responses deliveries
        receive a matching response).
    persona : str
        Persona name for all events.
    tmp_path : Path
        Temporary directory from pytest.
    ledger_filename : str
        Filename for the ledger file.
    days_spread : int
        Spread deliveries over this many days (all within past 7 days).

    Returns
    -------
    Path
        Path to the created DELIVERY_LEDGER.jsonl file.
    """
    now = datetime.now(timezone.utc)
    ledger_path = tmp_path / ledger_filename
    lines: List[str] = []

    for i in range(n_deliveries):
        sent_at = now - timedelta(days=i % days_spread)
        entry = {
            "ts": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "delivery",
            "message_id": f"MSG-{i:04d}",
            "persona": persona,
            "sent_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "delivered_at": sent_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "success",
            "context_tags": [],
        }
        lines.append(json.dumps(entry))

    for i in range(n_responses):
        resp_at = now - timedelta(days=i % days_spread)
        entry = {
            "ts": resp_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_type": "response",
            "message_id": f"MSG-{i:04d}",
            "persona": persona,
        }
        lines.append(json.dumps(entry))

    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ledger_path
