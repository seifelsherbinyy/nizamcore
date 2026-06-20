"""
Shared pytest fixtures for HIKMAH Knowledge Index tests.

Provides:
- temp_indices_dir: Temporary directory for test indices
- valid_personas: List of all 11 valid personas
- sample_index_dict: Sample valid index for testing
- context_tags_whitelist: Allowed context tags
"""

import pytest
from pathlib import Path
import tempfile
import json
from datetime import datetime, timezone


@pytest.fixture
def temp_indices_dir():
    """Temporary directory for test indices."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_personas():
    """List of all 11 valid personas."""
    return ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
            "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]


@pytest.fixture
def sample_index_dict(valid_personas):
    """Sample valid index for first persona."""
    return {
        "version": "1.0",
        "persona": valid_personas[0],
        "initialized_at": "2026-06-20T14:30:00Z",
        "last_updated": "2026-06-20T14:30:00Z",
        "topics": [],
        "completions": [],
        "activity_history": [
            {
                "ts": "2026-06-20T14:30:00Z",
                "event_type": "index_initialized",
                "description": "Knowledge index initialized"
            }
        ],
        "stalled_work": [],
        "context_snapshots": [
            {
                "ts": "2026-06-20T14:30:00Z",
                "snapshot": {
                    "open_topic_count": 0,
                    "active_blocker_count": 0,
                    "recent_accomplishments_count": 0,
                    "completion_rate_7d": 0.0,
                    "engagement_level": "unknown"
                }
            }
        ],
        "metadata": {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
    }


@pytest.fixture
def context_tags_whitelist():
    """Allowed context tags."""
    return {"technical", "health", "financial", "strategic", "personal"}
