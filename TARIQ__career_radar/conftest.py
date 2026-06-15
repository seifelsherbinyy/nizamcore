"""conftest.py — shared pytest fixtures for TARIQ__career_radar test suite.

Wave 0 (TDD scaffold): fixtures are stable contracts; implementation plans
must satisfy them.  These fixtures do NOT import from TARIQ__career_radar.radar
so conftest loads cleanly even before implementation exists.

Wave 1 additions (Phase 2, Plan 02-01):
  - fixtures_dir: path to tests/fixtures/
  - mock_*_response: load recorded ATS JSON fixtures
  - fake_requests_get: factory for injecting fake HTTP (no network)

Wave 4 additions (Phase 4, Plan 04-01):
  - dedup_opp_pairs: loads dedup_test_data.jsonl, returns all records
  - dedup_fresh_record: returns a seen_roles-like row with first_seen 45 days ago
  - cross_source_batch: 4-item list with cross-source duplicate pairs

Wave 4 additions (Phase 4, Plan 04-03):
  - _isolate_dedup_db (autouse, session-scoped): redirects _DEFAULT_DB_PATH to a
    temporary session directory so that tests never write to the production
    seen_roles.sqlite and cross-test dedup contamination is eliminated.
"""
from __future__ import annotations
import datetime
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


# ---------------------------------------------------------------------------
# Phase 4 (Plan 04-03): isolate dedup DB so tests never pollute production
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_dedup_db(tmp_path: Path) -> None:
    """Function-scoped autouse fixture: redirect _DEFAULT_DB_PATH to a per-test temp dir.

    Without this, every call to run_fetch() in test_sources.py would write
    fixture opportunities to the real data/seen_roles.sqlite. Tests that use
    the same mock opportunity (e.g. "AI Operations Manager" at "Acme Corp")
    would suppress each other via the dedup seen-store.

    This fixture patches the module-level _DEFAULT_DB_PATH binding in both
    dedup_engine and stages/fetch so every test gets a clean, isolated SQLite DB.
    """
    test_db_path = tmp_path / "seen_roles_test.sqlite"
    _original_de_path = None
    _original_sf_path = None

    try:
        import radar.dedup_engine as _de
        _original_de_path = _de._DEFAULT_DB_PATH
        _de._DEFAULT_DB_PATH = test_db_path
    except ImportError:
        pass

    try:
        import radar.stages.fetch as _sf
        _original_sf_path = _sf._DEFAULT_DB_PATH
        _sf._DEFAULT_DB_PATH = test_db_path
    except ImportError:
        pass

    yield

    # Restore originals after each test
    try:
        import radar.dedup_engine as _de
        if _original_de_path is not None:
            _de._DEFAULT_DB_PATH = _original_de_path
    except ImportError:
        pass

    try:
        import radar.stages.fetch as _sf
        if _original_sf_path is not None:
            _sf._DEFAULT_DB_PATH = _original_sf_path
    except ImportError:
        pass


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


# ---------------------------------------------------------------------------
# Phase 3 additions — RSS/JSONL fixture loaders (SRC-02, SRC-03, SRC-06)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_remotive_rss(fixtures_dir: Path) -> bytes:
    """Return raw bytes of recorded Remotive RSS feed."""
    return (fixtures_dir / "remotive_sample_rss.xml").read_bytes()


@pytest.fixture
def mock_weworkremotely_rss(fixtures_dir: Path) -> bytes:
    """Return raw bytes of recorded We Work Remotely RSS feed."""
    return (fixtures_dir / "weworkremotely_sample_rss.xml").read_bytes()


@pytest.fixture
def mock_remoteok_response(fixtures_dir: Path) -> list:
    """Return parsed JSON list from recorded RemoteOK API response."""
    return json.loads((fixtures_dir / "remoteok_sample_response.json").read_text())


@pytest.fixture
def manual_import_fixture(tmp_path: Path) -> Path:
    """Create a temporary manual_imports.jsonl for ManualImportSource tests."""
    import_file = tmp_path / "manual_imports.jsonl"
    import_file.write_text(
        '{"title": "AI Evaluator", "company": "Outlier AI", "location": "Remote",'
        ' "salary_usd_low": 30, "salary_usd_high": 60, "salary_per": "hour",'
        ' "source_url": "https://app.outlier.ai/jobs/1"}\n'
        '{"title": "Data Annotator", "company": "DataAnnotation.tech",'
        ' "location": "Remote", "source_url": "https://app.datannotation.tech/work"}\n',
        encoding="utf-8",
    )
    return import_file


@pytest.fixture
def fake_rss_bytes_get():
    """Factory for mocking requests.get to return raw RSS/JSON bytes.

    Usage:
        monkeypatch.setattr(requests, "get", fake_rss_bytes_get(xml_bytes))
    """
    def make_fake_rss_get(content_bytes: bytes, status_code: int = 200, raise_exc=None):
        def fake_get(*args, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            resp = unittest.mock.MagicMock()
            resp.status_code = status_code
            resp.content = content_bytes
            if status_code < 400:
                resp.raise_for_status.side_effect = None
            else:
                resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                    f"{status_code}"
                )
            return resp
        return fake_get
    return make_fake_rss_get


@pytest.fixture
def synthetic_profile_seed() -> dict:
    """Synthetic profile seed with role_keywords as group-dict (SRC-06 tests).

    Structure mirrors data/profile_cache.json but contains NO real personal data.
    role_keywords is dict[group_name, list[keyword]] — exact substring match.
    """
    return {
        "role_keywords": {
            "AI_OPERATIONS": ["ai operations", "ai ops", "ml ops", "llm ops"],
            "DATA_SCIENCE": ["data science", "data scientist", "ml engineer", "machine learning"],
            "COORDINATION": ["program manager", "project coordinator", "operations manager"],
            "LLM_EVALUATION": ["ai evaluator", "data annotator", "content reviewer"],
        },
        "target_roles": ["AI Ops Manager", "ML Engineering Manager", "Data Scientist"],
        "constraints": {
            "min_salary_usd": 80000,
            "remote_only": True,
        },
    }


# ---------------------------------------------------------------------------
# Phase 4 additions — deduplication fixtures (DEDUP-01, DEDUP-02, DEDUP-03)
# ---------------------------------------------------------------------------

@pytest.fixture
def dedup_opp_pairs(fixtures_dir: Path) -> list:
    """Load all records from dedup_test_data.jsonl and return as list[dict].

    Records come in pairs: same underlying role, different title wording.
    Includes cross-source pairs and records with >30-day access_date gaps.
    """
    jsonl_path = fixtures_dir / "dedup_test_data.jsonl"
    records = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


@pytest.fixture
def dedup_fresh_record() -> dict:
    """Return a dict mimicking a SQLite seen_roles row with first_seen 45 days ago.

    Used in freshness rule tests (DEDUP-03): a role first seen >=30 days ago
    should be treated as a fresh repost — return it as if new.
    """
    now = datetime.datetime.utcnow()
    first_seen = now - datetime.timedelta(days=45)
    return {
        "first_seen_date": first_seen.isoformat() + "Z",
        "last_seen_date": now.isoformat() + "Z",
        "hit_count": 1,
    }


@pytest.fixture
def cross_source_batch() -> list:
    """Return a hardcoded list of 4 opportunities for cross-source duplicate tests.

    Layout:
      [0] "AI Ops Manager"    at "Acme Corp"   from "greenhouse"   — duplicate pair A
      [1] "Finance Manager"   at "Acme Corp"   from "greenhouse"   — distinct role
      [2] "AI Ops Manager"    at "Acme Corp"   from "remotive"     — duplicate pair A (cross-source)
      [3] "Data Annotator"    at "Beta Inc"    from "weworkremotely" — distinct role

    Pair A (opps[0] and opps[2]) should be detected as cross-source duplicates.
    """
    return [
        {
            "title": "AI Ops Manager",
            "company": "Acme Corp",
            "location": "Remote",
            "source": "greenhouse",
            "access_date": "2026-06-15T10:00:00Z",
        },
        {
            "title": "Finance Manager",
            "company": "Acme Corp",
            "location": "Remote",
            "source": "greenhouse",
            "access_date": "2026-06-15T10:00:00Z",
        },
        {
            "title": "AI Ops Manager",
            "company": "Acme Corp",
            "location": "Remote",
            "source": "remotive",
            "access_date": "2026-06-15T10:00:00Z",
        },
        {
            "title": "Data Annotator",
            "company": "Beta Inc",
            "location": "Remote",
            "source": "weworkremotely",
            "access_date": "2026-06-15T10:00:00Z",
        },
    ]
