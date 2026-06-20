"""
Shared pytest configuration for HIKMAH Knowledge Index tests.

Provides fixtures and configuration for all test modules in the package.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path


@pytest.fixture
def temp_indices_dir(tmp_path):
    """Provide a temporary directory for index files during tests."""
    indices_dir = tmp_path / "indices"
    indices_dir.mkdir(exist_ok=True)
    return indices_dir


@pytest.fixture
def sample_timestamp():
    """Provide an ISO 8601 timestamp for consistent test data."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_valid_index(sample_timestamp):
    """Provide a minimal valid index structure."""
    return {
        "version": "1.0",
        "persona": "AMMAR",
        "initialized_at": sample_timestamp,
        "last_updated": sample_timestamp,
        "topics": [],
        "completions": [],
        "activity_history": [],
        "stalled_work": [],
        "context_snapshots": [],
        "metadata": {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
    }
