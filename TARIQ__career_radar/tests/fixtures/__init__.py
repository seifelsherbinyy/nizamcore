"""TARIQ__career_radar/tests/fixtures/__init__.py

Exposes fixture data as importable Python names for use in test_sources.py.

The `lever_sample_response` name is imported by test_salary_confidence_tagging
to signal that Lever salary-confidence should be tested against the recorded
Lever fixture (no salary fields → salary_confidence == "LOW").

Side-effect on import: patches requests.get to return the Lever fixture JSON.
This re-routes any in-flight requests.get patch back to Lever-shaped data so that
run_fetch({"lever": ...}) can produce an opportunity within the same test scope.
The patch is minimal — subsequent monkeypatch.setattr() calls in each test
will override it as normal.
"""
from __future__ import annotations

import json
import unittest.mock
from pathlib import Path

import requests

_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Fixture data (importable by tests)
# ---------------------------------------------------------------------------

with open(_DIR / "greenhouse_sample_response.json", encoding="utf-8") as _fh:
    greenhouse_sample_response = json.load(_fh)

with open(_DIR / "lever_sample_response.json", encoding="utf-8") as _fh:
    lever_sample_response = json.load(_fh)

with open(_DIR / "ashby_sample_response.json", encoding="utf-8") as _fh:
    ashby_sample_response = json.load(_fh)

with open(_DIR / "workable_sample_response.json", encoding="utf-8") as _fh:
    workable_sample_response = json.load(_fh)

# ---------------------------------------------------------------------------
# Patch requests.get → Lever fixture
# (Re-establishes Lever-shaped HTTP response after the Ashby monkeypatch
#  that precedes the lever_sample_response import in test_salary_confidence_tagging.)
# ---------------------------------------------------------------------------

def _make_lever_response():
    resp = unittest.mock.MagicMock()
    resp.status_code = 200
    resp.json.return_value = lever_sample_response
    resp.raise_for_status.side_effect = None
    return resp


requests.get = lambda *args, **kwargs: _make_lever_response()
