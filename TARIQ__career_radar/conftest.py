"""conftest.py — shared pytest fixtures for TARIQ__career_radar test suite.

Wave 0 (TDD scaffold): fixtures are stable contracts; implementation plans
must satisfy them.  These fixtures do NOT import from TARIQ__career_radar.radar
so conftest loads cleanly even before implementation exists.

Wave 1 additions (Phase 2, Plan 02-01):
  - fixtures_dir: path to tests/fixtures/
  - mock_*_response: load recorded ATS JSON fixtures
  - fake_requests_get: factory for injecting fake HTTP (no network)
"""
from __future__ import annotations
import json
import sys
import unittest.mock
import uuid
from pathlib import Path

import requests

# Ensure repo root is on sys.path for cross-module imports
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Ensure TARIQ__career_radar/ is on sys.path so that `radar.*` short imports
# work inside test_sources.py (Wave 1/2 connectors use `radar.sources.*` paths).
_TARIQ_PKG = Path(__file__).resolve().parent
if str(_TARIQ_PKG) not in sys.path:
    sys.path.insert(0, str(_TARIQ_PKG))

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return absolute path to the NIZAM repository root."""
    return _REPO


@pytest.fixture
def schema_path(repo_root: Path) -> Path:
    """Return path to the career opportunity JSON Schema file.

    The file may not exist yet (created in Wave 1, Plan 01-02).
    The fixture just returns the expected path so tests can assert
    existence or load it once created.
    """
    return repo_root / "NIZAM__system" / "schemas" / "career_opportunity_record.schema.json"


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Yield a Path to a temporary SQLite file, cleaned up after the test."""
    db = tmp_path / "seen_roles.sqlite"
    yield db
    # Cleanup is handled automatically by pytest's tmp_path


@pytest.fixture
def sample_opportunity() -> dict:
    """Return a minimal valid opportunity dict satisfying all 20 required schema fields.

    Values are synthetic — no real personal data.  Scores are intentionally
    mid-range so tests can assert boundary conditions without special casing.
    """
    return {
        "opportunity_id": str(uuid.uuid4()),
        "title": "Senior AI Operations Manager",
        "company": "Acme Corp",
        "location": "Remote",
        "remote_status": "fully_remote",
        "source": "Greenhouse",
        "source_type": "manual",
        "source_url": "https://boards.greenhouse.io/acme/jobs/12345",
        "access_date": "2026-06-14T12:00:00Z",
        "fit_score": 50,
        "growth_score": 40,
        "confidence": "LOW",
        "tags": [],
        "salary_usd_low": None,
        "salary_usd_high": None,
        "salary_evidence_type": "not_disclosed",
        "salary_confidence": "LOW",
        "observed_at": "2026-06-14T12:00:00Z",
        "lane": "Remote USD",
        "data_quality": "partial",
    }


@pytest.fixture
def sample_profile() -> dict:
    """Return a minimal synthetic profile dict with required top-level keys.

    Never contains real personal data.  Used in tests that verify the
    profile structure without triggering privacy-egress rules.
    """
    return {
        "role_keywords": ["AI operations", "ML platform", "LLM tooling"],
        "target_roles": ["AI Ops Manager", "ML Engineering Manager"],
        "constraints": {
            "min_salary_usd": 120000,
            "remote_only": True,
            "preferred_timezones": ["UTC-5", "UTC-8"],
        },
    }


# ---------------------------------------------------------------------------
# Phase 2 additions — fake-HTTP transport + ATS fixture loaders
# ---------------------------------------------------------------------------

@pytest.fixture
def fixtures_dir() -> Path:
    """Return the absolute path to TARIQ__career_radar/tests/fixtures/."""
    return Path(__file__).parent / "tests" / "fixtures"


@pytest.fixture
def mock_greenhouse_response(fixtures_dir: Path) -> dict:
    """Load the recorded Greenhouse API response from disk."""
    with open(fixtures_dir / "greenhouse_sample_response.json") as fh:
        return json.load(fh)


@pytest.fixture
def mock_lever_response(fixtures_dir: Path) -> list:
    """Load the recorded Lever API response from disk."""
    with open(fixtures_dir / "lever_sample_response.json") as fh:
        return json.load(fh)


@pytest.fixture
def mock_ashby_response(fixtures_dir: Path) -> dict:
    """Load the recorded Ashby API response from disk."""
    with open(fixtures_dir / "ashby_sample_response.json") as fh:
        return json.load(fh)


@pytest.fixture
def mock_workable_response(fixtures_dir: Path) -> dict:
    """Load the recorded Workable API response from disk."""
    with open(fixtures_dir / "workable_sample_response.json") as fh:
        return json.load(fh)


@pytest.fixture
def fake_requests_get():
    """Return a factory that creates fake requests.get callables.

    Usage in tests:
        monkeypatch.setattr(requests, "get", fake_requests_get(200, my_data))
        monkeypatch.setattr(requests, "get",
                            fake_requests_get(raise_exc=requests.Timeout()))

    The factory never makes a real network call — all responses are
    constructed from the provided status_code and json_data arguments.
    """
    def make_fake_get(status_code: int = 200, json_data=None, raise_exc=None):
        def fake_get(*args, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            resp = unittest.mock.MagicMock()
            resp.status_code = status_code
            resp.json.return_value = json_data if json_data is not None else {}
            if status_code < 400:
                resp.raise_for_status.side_effect = None
            else:
                resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                    f"{status_code}"
                )
            return resp
        return fake_get

    return make_fake_get
