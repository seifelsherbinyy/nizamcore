"""test_opportunity_schema.py — DATA-01: Opportunity record validates against JSON Schema.

Wave 0 (TDD): These tests MUST fail because the schema file does not yet exist.
Acceptable failure mode: FileNotFoundError or jsonschema.ValidationError on missing schema.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import pytest

jsonschema = pytest.importorskip("jsonschema", reason="jsonschema not installed")

# --------------------------------------------------------------------------
# Required fields per research (20 fields)
# --------------------------------------------------------------------------
_REQUIRED_FIELDS = [
    "opportunity_id",
    "title",
    "company",
    "location",
    "remote_status",
    "source",
    "source_type",
    "source_url",
    "access_date",
    "fit_score",
    "growth_score",
    "confidence",
    "tags",
    "salary_usd_low",
    "salary_usd_high",
    "salary_evidence_type",
    "salary_confidence",
    "observed_at",
    "lane",
    "data_quality",
]


def _load_schema(schema_path: Path) -> dict:
    """Load and return the JSON Schema.  Raises FileNotFoundError if absent."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_schema_validate(schema_path: Path, sample_opportunity: dict) -> None:
    """DATA-01: sample_opportunity must validate against the JSON Schema."""
    schema = _load_schema(schema_path)
    # Will raise jsonschema.ValidationError if invalid
    jsonschema.validate(instance=sample_opportunity, schema=schema)


def test_schema_required_fields(schema_path: Path) -> None:
    """DATA-01: Schema must declare all 20 required fields."""
    schema = _load_schema(schema_path)
    schema_required = set(schema.get("required", []))
    missing = set(_REQUIRED_FIELDS) - schema_required
    assert not missing, f"Schema missing required fields: {sorted(missing)}"


def test_schema_rejects_missing_title(schema_path: Path, sample_opportunity: dict) -> None:
    """DATA-01: Opportunity without 'title' must fail schema validation."""
    schema = _load_schema(schema_path)
    bad_opp = {k: v for k, v in sample_opportunity.items() if k != "title"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad_opp, schema=schema)
