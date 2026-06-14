"""test_sources.py — TDD contract for Phase 2 ATS sourcing (Wave 0 / RED).

All 11 tests are COLLECTIBLE but intentionally FAILING until Wave 1/2 connectors
are implemented.  Uses the _require_module() pattern from Phase 1 Plan 01-01:
each test tries to import the not-yet-existing module, fails with a descriptive
pytest.fail message, and never makes a real network call.

Requirements covered: SRC-01 (fetch), SRC-04 (normalization), SRC-05 (errors).
"""
from __future__ import annotations

import pytest
import requests


# ---------------------------------------------------------------------------
# Helper: collectible import guard
# ---------------------------------------------------------------------------

def _require_module(module_path: str, attr: str = None):
    """Import a module (or attribute) expected to exist in Wave 1/2.

    Returns the module or attribute on success.
    Calls pytest.fail() — test is FAILED (not errored) on ImportError.
    This is the canonical Wave-0 RED pattern: tests are collected, not crashed.
    """
    try:
        import importlib
        mod = importlib.import_module(module_path)
        if attr:
            return getattr(mod, attr)
        return mod
    except (ImportError, ModuleNotFoundError) as exc:
        pytest.fail(
            f"MISSING — implement in Wave 1/2: "
            f"'{module_path}' ({attr or 'module'}) not found. "
            f"Original error: {exc}"
        )


# ---------------------------------------------------------------------------
# SRC-01: Fetch tests (one per ATS platform)
# ---------------------------------------------------------------------------

def test_greenhouse_fetch_mocked(mock_greenhouse_response, fake_requests_get, monkeypatch):
    """SRC-01: GreenhouseSource fetches public endpoint; returns SourceResult with 1 opp."""
    GreenhouseSource = _require_module("radar.sources.greenhouse_source", "GreenhouseSource")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_greenhouse_response))
    src = GreenhouseSource({"board_token": "acme", "enabled": True})
    result = src.fetch({})
    assert result.source_name == "greenhouse"
    assert len(result.opportunities) == 1
    assert result.opportunities[0].title == "AI Operations Manager"
    assert result.errors == []
    assert result.rate_limited is False


def test_lever_fetch_mocked(mock_lever_response, fake_requests_get, monkeypatch):
    """SRC-01: LeverSource fetches public endpoint; returns SourceResult with 1 opp."""
    LeverSource = _require_module("radar.sources.lever_source", "LeverSource")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_lever_response))
    src = LeverSource({"site": "acme", "company_name": "Acme Corp", "enabled": True})
    result = src.fetch({})
    assert result.source_name == "lever"
    assert len(result.opportunities) == 1
    assert result.opportunities[0].title == "Data Analyst"
    assert result.errors == []
    assert result.rate_limited is False


def test_ashby_fetch_mocked(mock_ashby_response, fake_requests_get, monkeypatch):
    """SRC-01: AshbySource fetches public endpoint; returns SourceResult with 1 opp."""
    AshbySource = _require_module("radar.sources.ashby_source", "AshbySource")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_ashby_response))
    src = AshbySource({"board_name": "acme", "enabled": True})
    result = src.fetch({})
    assert result.source_name == "ashby"
    assert len(result.opportunities) == 1
    assert result.opportunities[0].title == "ML Platform Engineer"
    assert result.errors == []
    assert result.rate_limited is False


def test_workable_fetch_mocked(mock_workable_response, fake_requests_get, monkeypatch):
    """SRC-01: WorkableSource fetches public endpoint; returns SourceResult with 1 opp."""
    WorkableSource = _require_module("radar.sources.workable_source", "WorkableSource")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_workable_response))
    src = WorkableSource({"account_subdomain": "acme", "enabled": True})
    result = src.fetch({})
    assert result.source_name == "workable"
    assert len(result.opportunities) == 1
    assert result.opportunities[0].title == "AI Ops Coordinator"
    assert result.errors == []
    assert result.rate_limited is False


# ---------------------------------------------------------------------------
# SRC-04: Normalization tests
# ---------------------------------------------------------------------------

def test_normalization_to_schema(mock_greenhouse_response, fake_requests_get, monkeypatch):
    """SRC-04: Normalized opportunity dict contains all required schema fields."""
    run_fetch = _require_module("radar.stages.fetch", "run_fetch")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_greenhouse_response))
    result = run_fetch({"greenhouse": {"board_token": "acme", "enabled": True}}, "test-run-id")
    opportunities = result["opportunities"]
    assert len(opportunities) >= 1
    opp = opportunities[0]

    required_keys = [
        "opportunity_id",
        "title",
        "company",
        "location",
        "remote_status",
        "source",
        "source_type",
        "source_url",
        "access_date",
        "salary_usd_low",
        "salary_usd_high",
        "salary_evidence_type",
        "salary_confidence",
        "fit_score",
        "growth_score",
        "confidence",
        "tags",
        "lane",
        "observed_at",
    ]
    for key in required_keys:
        assert key in opp, f"Missing required schema field: '{key}'"


def test_required_fields_present(mock_greenhouse_response, fake_requests_get, monkeypatch):
    """SRC-04: Normalized opportunity carries required provenance + access metadata."""
    run_fetch = _require_module("radar.stages.fetch", "run_fetch")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_greenhouse_response))
    result = run_fetch({"greenhouse": {"board_token": "acme", "enabled": True}}, "test-run-id")
    opp = result["opportunities"][0]
    assert opp["source"] == "greenhouse"
    assert opp["source_type"] == "ats"
    assert opp["source_url"].startswith("https://")
    assert opp["access_date"].endswith("Z")


def test_salary_confidence_tagging(
    mock_greenhouse_response, mock_ashby_response, fake_requests_get, monkeypatch
):
    """SRC-04: salary_confidence HIGH for employer-posted salary; LOW when absent."""
    GreenhouseSource = _require_module("radar.sources.greenhouse_source", "GreenhouseSource")
    AshbySource = _require_module("radar.sources.ashby_source", "AshbySource")
    LeverSource = _require_module("radar.sources.lever_source", "LeverSource")

    # --- RED: import fails above; assertions below are the GREEN contract ---

    # Greenhouse has salary_min/salary_max → HIGH confidence
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_greenhouse_response))
    gh_src = GreenhouseSource({"board_token": "acme", "enabled": True})
    gh_result = gh_src.fetch({})
    assert gh_result.opportunities[0].salary_usd_low is not None
    # salary_confidence assessed at normalization stage; check via run_fetch
    from radar.stages.fetch import run_fetch  # noqa: F811 — available at GREEN time
    run_fetch_result = run_fetch(
        {"greenhouse": {"board_token": "acme", "enabled": True}}, "test-run-id"
    )
    gh_opp = run_fetch_result["opportunities"][0]
    assert gh_opp["salary_confidence"] == "HIGH", "Greenhouse salary should be HIGH confidence"

    # Ashby has compensation.salary → HIGH confidence
    monkeypatch.setattr(requests, "get", fake_requests_get(200, mock_ashby_response))
    ashby_src = AshbySource({"board_name": "acme", "enabled": True})
    ashby_result = ashby_src.fetch({})
    assert ashby_result.opportunities[0].salary_usd_low is not None

    # Lever has no salary fields → LOW confidence
    from TARIQ__career_radar.tests.fixtures import lever_sample_response  # noqa — not real import
    # Lever fixture has no salary fields; after normalization salary_confidence should be LOW
    lever_run_result = run_fetch(
        {"lever": {"site": "acme", "company_name": "Acme Corp", "enabled": True}}, "test-run-id"
    )
    lever_opp = lever_run_result["opportunities"][0]
    assert lever_opp["salary_confidence"] == "LOW", "Lever salary should be LOW confidence"


# ---------------------------------------------------------------------------
# SRC-05: Error-handling tests
# ---------------------------------------------------------------------------

def test_fetch_network_error_graceful(fake_requests_get, monkeypatch):
    """SRC-05: Network timeout is caught; source returns error, no exception propagated."""
    GreenhouseSource = _require_module("radar.sources.greenhouse_source", "GreenhouseSource")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(
        requests, "get", fake_requests_get(raise_exc=requests.Timeout("Connection timeout"))
    )
    src = GreenhouseSource({"board_token": "acme", "enabled": True})
    result = src.fetch({})
    assert result.opportunities == []
    assert len(result.errors) > 0
    assert "timeout" in result.errors[0].lower()


def test_429_rate_limit_handled(fake_requests_get, monkeypatch):
    """SRC-05: 429 response sets rate_limited=True; no retry; empty opportunities."""
    GreenhouseSource = _require_module("radar.sources.greenhouse_source", "GreenhouseSource")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    monkeypatch.setattr(requests, "get", fake_requests_get(429, {}))
    src = GreenhouseSource({"board_token": "acme", "enabled": True})
    result = src.fetch({})
    assert result.rate_limited is True
    assert result.opportunities == []
    assert len(result.errors) > 0


def test_blocked_sources_manifest(fake_requests_get, monkeypatch):
    """SRC-05: run_fetch returns blocked_sources list when a source fails; others continue."""
    run_fetch = _require_module("radar.stages.fetch", "run_fetch")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    # Inject a timeout so GreenhouseSource fails; other sources may be disabled/absent
    monkeypatch.setattr(
        requests, "get", fake_requests_get(raise_exc=requests.Timeout("Connection timeout"))
    )
    config = {
        "greenhouse": {"board_token": "acme", "enabled": True},
        "lever": {"site": "acme", "company_name": "Acme Corp", "enabled": False},
        "ashby": {"board_name": "acme", "enabled": False},
        "workable": {"account_subdomain": "acme", "enabled": False},
    }
    result = run_fetch(config, "test-run-id")
    assert "blocked_sources" in result, "run_fetch must return 'blocked_sources' key"
    blocked = result["blocked_sources"]
    # At least greenhouse should appear in blocked_sources
    blocked_names = [b["source"] for b in blocked]
    assert "greenhouse" in blocked_names
    for b in blocked:
        assert "source" in b
        assert "errors" in b


def test_zero_results_graceful(fake_requests_get, monkeypatch):
    """SRC-05: run_fetch with all sources disabled returns canonical structure without raising."""
    run_fetch = _require_module("radar.stages.fetch", "run_fetch")

    # --- RED: import fails above; assertions below are the GREEN contract ---
    config = {
        "greenhouse": {"board_token": "", "enabled": False},
        "lever": {"site": "", "company_name": "", "enabled": False},
        "ashby": {"board_name": "", "enabled": False},
        "workable": {"account_subdomain": "", "enabled": False},
    }
    result = run_fetch(config, "test-run-id")
    assert "opportunities" in result
    assert result["opportunities"] == []
    assert "blocked_sources" in result
    assert "fetch_summary" in result
    # Run must complete without raising
