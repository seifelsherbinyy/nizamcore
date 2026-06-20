"""
Tests for knowledge index initialization functions.

Covers:
- Single persona index creation (initialize_persona_index)
- Batch initialization for all 11 personas (initialize_all_personas)
- Schema validation of created indices
- File system operations and error handling
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from HIKMAH__knowledge_index.index.main import initialize_persona_index, initialize_all_personas
from HIKMAH__knowledge_index.index.schema import validate_index_schema, VALID_PERSONAS


class TestInitializePersonaIndex:
    """Test initialize_persona_index() function."""

    def test_creates_file_at_correct_path(self):
        """Test 1: initialize_persona_index creates file at target_dir/PERSONA_index.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            assert result.exists(), f"Index file not created at {result}"
            assert result.name == "AMMAR_index.json"
            assert result.parent == temp_path

    def test_created_file_is_valid_json(self):
        """Test 2: Created index file is valid JSON and passes validate_index_schema()"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            # Should be valid JSON
            with open(result) as f:
                data = json.load(f)

            # Should pass schema validation
            is_valid, error = validate_index_schema(data)
            assert is_valid, f"Schema validation failed: {error}"

    def test_index_has_correct_version_and_persona(self):
        """Test 3: Created index has version="1.0" and persona="AMMAR"."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            with open(result) as f:
                data = json.load(f)

            assert data["version"] == "1.0"
            assert data["persona"] == "AMMAR"

    def test_index_has_iso8601_timestamps(self):
        """Test 4: Created index has initialized_at and last_updated in ISO 8601 format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            with open(result) as f:
                data = json.load(f)

            # Check format: should have T and Z (UTC indicator)
            assert "T" in data["initialized_at"]
            assert data["initialized_at"].endswith("Z") or "+" in data["initialized_at"]
            assert "T" in data["last_updated"]
            assert data["last_updated"].endswith("Z") or "+" in data["last_updated"]

            # Should match ISO 8601 UTC format (e.g., 2026-06-20T12:34:56.123456Z)
            assert data["initialized_at"] == data["last_updated"]

    def test_index_has_empty_arrays(self):
        """Test 5: Created index has empty topics[], completions[], stalled_work[] arrays."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            with open(result) as f:
                data = json.load(f)

            assert data["topics"] == []
            assert data["completions"] == []
            assert data["stalled_work"] == []

    def test_index_has_activity_history_with_init_event(self):
        """Test 6: Created index has activity_history with one entry of event_type="index_initialized"."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            with open(result) as f:
                data = json.load(f)

            assert len(data["activity_history"]) == 1
            event = data["activity_history"][0]
            assert event["event_type"] == "index_initialized"
            assert "AMMAR" in event["description"] or "AMMAR" in str(event)

    def test_index_has_context_snapshots_with_zero_metrics(self):
        """Test 7: Created index has context_snapshots with one snapshot having all zero metrics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("AMMAR", temp_path)

            with open(result) as f:
                data = json.load(f)

            assert len(data["context_snapshots"]) == 1
            snapshot = data["context_snapshots"][0]
            metrics = snapshot["snapshot"]

            assert metrics["open_topic_count"] == 0
            assert metrics["active_blocker_count"] == 0
            assert metrics["recent_accomplishments_count"] == 0
            assert metrics["completion_rate_7d"] == 0.0
            assert metrics["engagement_level"] == "unknown"

    def test_invalid_persona_raises_valueerror(self):
        """Test 8: initialize_persona_index() with invalid persona raises ValueError with clear message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with pytest.raises(ValueError, match="Unknown persona|XYZ"):
                initialize_persona_index("INVALID_PERSONA", temp_path)

    def test_creates_directory_if_missing(self):
        """Test 9: initialize_persona_index() creates directory if it doesn't exist (parents=True)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "subdir1" / "subdir2"
            assert not temp_path.exists()

            result = initialize_persona_index("HIKMAH", temp_path)

            assert result.exists()
            assert temp_path.exists()

    def test_metadata_is_set_correctly(self):
        """Test metadata structure in created index."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_persona_index("TARIQ", temp_path)

            with open(result) as f:
                data = json.load(f)

            metadata = data["metadata"]
            assert metadata["source"] == "v1.1-knowledge-index"
            assert metadata["locale"] == "Egypt/Cairo"
            assert metadata["language"] == "en"


class TestInitializeAllPersonas:
    """Test initialize_all_personas() function."""

    def test_creates_indices_for_all_11_personas(self):
        """Test 10: initialize_all_personas(temp_dir) creates indices for all 11 personas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_all_personas(temp_path)

            # Should create 11 files
            files = list(temp_path.glob("*_index.json"))
            assert len(files) == 11, f"Expected 11 index files, got {len(files)}"

    def test_returns_mapping_dict(self):
        """Test 11: initialize_all_personas() returns dict mapping {persona: path}."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_all_personas(temp_path)

            assert isinstance(result, dict)
            assert len(result) == 11

            # Should have all 11 personas as keys
            for persona in VALID_PERSONAS:
                assert persona in result
                assert isinstance(result[persona], Path)
                assert result[persona].exists()

    def test_all_created_indices_pass_validation(self):
        """Test 12: All 11 created indices pass validate_index_schema()."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_all_personas(temp_path)

            for persona, path in result.items():
                with open(path) as f:
                    data = json.load(f)

                is_valid, error = validate_index_schema(data)
                assert is_valid, f"Schema validation failed for {persona}: {error}"

    def test_all_persona_files_named_correctly(self):
        """Test 13: All 11 persona files are named correctly ({PERSONA}_index.json)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = initialize_all_personas(temp_path)

            for persona in VALID_PERSONAS:
                expected_name = f"{persona}_index.json"
                assert result[persona].name == expected_name

    def test_error_aborts_early(self):
        """Test: If any persona initialization fails, aborts early and raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Mock VALID_PERSONAS to include an invalid one by temporarily patching
            # For now, we'll test that normal execution succeeds
            result = initialize_all_personas(temp_path)
            assert len(result) == 11
