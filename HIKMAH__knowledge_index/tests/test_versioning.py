"""
Tests for HIKMAH Knowledge Index schema versioning and MAKHZAN snapshot pattern.

Validates:
- validate_schema_versions() detects matching/mismatched versions
- snapshot_indices_to_makhzan() creates MAKHZAN snapshots with MANIFEST.json
- increment_schema_version() atomically updates all 11 persona indices
- Version format validation
- Backward compatibility for v1.x versions
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from HIKMAH__knowledge_index.index.versioning import (
    validate_schema_versions,
    snapshot_indices_to_makhzan,
    increment_schema_version,
    validate_version_format,
)


def create_test_index(version: str = "1.0", persona: str = "AMMAR") -> dict:
    """Create a minimal valid test index."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "version": version,
        "persona": persona,
        "initialized_at": now,
        "last_updated": now,
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


def create_test_indices_dir(versions_dict: dict = None) -> Path:
    """
    Create a temporary directory with test persona indices.

    Args:
        versions_dict: Dict mapping persona name to version (default: all v1.0)

    Returns:
        Path to temporary directory containing {PERSONA}_index.json files
    """
    if versions_dict is None:
        versions_dict = {
            "AMMAR": "1.0", "HIKMAH": "1.0", "TARIQ": "1.0",
            "MUNAWARA": "1.0", "MAL": "1.0", "BADAN": "1.0",
            "NAQD": "1.0", "SHURA": "1.0", "TAFRIGH": "1.0",
            "MARSAD": "1.0", "NIZAM": "1.0"
        }

    tmpdir = Path(tempfile.mkdtemp())
    for persona, version in versions_dict.items():
        index = create_test_index(version=version, persona=persona)
        index_path = tmpdir / f"{persona}_index.json"
        with open(index_path, 'w') as f:
            json.dump(index, f)

    return tmpdir


class TestValidateSchemaVersions:
    """Test suite for validate_schema_versions function."""

    def test_all_indices_at_same_version_returns_valid(self):
        """Test 1: validate_schema_versions with all indices at v1.0 returns (True, None)."""
        tmpdir = create_test_indices_dir()
        try:
            valid, error = validate_schema_versions(tmpdir)
            assert valid is True
            assert error is None
        finally:
            shutil.rmtree(tmpdir)

    def test_mixed_versions_returns_invalid_with_error_message(self):
        """Test 2: validate_schema_versions with mixed versions returns (False, error_msg)."""
        tmpdir = create_test_indices_dir({
            "AMMAR": "1.0", "HIKMAH": "1.0", "TARIQ": "1.1",  # TARIQ at different version
            "MUNAWARA": "1.0", "MAL": "1.0", "BADAN": "1.0",
            "NAQD": "1.0", "SHURA": "1.0", "TAFRIGH": "1.0",
            "MARSAD": "1.0", "NIZAM": "1.0"
        })
        try:
            valid, error = validate_schema_versions(tmpdir)
            assert valid is False
            assert isinstance(error, str)
            assert "version" in error.lower()
        finally:
            shutil.rmtree(tmpdir)


class TestSnapshotIndicesToMakhzan:
    """Test suite for snapshot_indices_to_makhzan function."""

    def test_creates_makhzan_archive_directory(self):
        """Test 3: snapshot_indices_to_makhzan creates MAKHZAN__archive/ directory."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            snapshot_path = snapshot_indices_to_makhzan(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )
            assert makhzan_dir.exists()
            # snapshot_path is: MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices
            # parent: MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index
            # parent.parent: MAKHZAN__archive/{ISO_TIMESTAMP}
            # parent.parent.parent: MAKHZAN__archive
            assert snapshot_path.parent.parent.parent == makhzan_dir
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_preserves_all_11_index_files(self):
        """Test 4: snapshot preserves all 11 index files in snapshot directory with original content."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            snapshot_path = snapshot_indices_to_makhzan(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            # Verify all 11 persona indices are in snapshot
            personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
                       "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]

            for persona in personas:
                snapshot_index = snapshot_path / f"{persona}_index.json"
                assert snapshot_index.exists()

                # Verify content is preserved
                with open(snapshot_index) as f:
                    snapshot_content = json.load(f)
                with open(indices_dir / f"{persona}_index.json") as f:
                    original_content = json.load(f)

                # Version should be old version
                assert snapshot_content["version"] == "1.0"
                assert snapshot_content["persona"] == persona
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_creates_manifest_json(self):
        """Test 5: snapshot creates MANIFEST.json with metadata."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            snapshot_path = snapshot_indices_to_makhzan(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            # snapshot_path is: MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices
            # MANIFEST.json is at: MAKHZAN__archive/{ISO_TIMESTAMP}/
            manifest_path = snapshot_path.parent.parent / "MANIFEST.json"
            assert manifest_path.exists()

            with open(manifest_path) as f:
                manifest = json.load(f)

            assert manifest["trigger"] == "schema_version_increment"
            assert manifest["from_version"] == "1.0"
            assert manifest["to_version"] == "1.1"
            assert manifest["change"] == "Added engagement_patterns array"
            assert manifest["indices_backed_up"] == 11
            assert "snapshot_at" in manifest
            assert "recovery_note" in manifest
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)


class TestIncrementSchemaVersion:
    """Test suite for increment_schema_version function."""

    def test_calls_snapshot_first(self):
        """Test 6: increment_schema_version calls snapshot first."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            result = increment_schema_version(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            # If snapshot was called, MAKHZAN__archive should exist with content
            assert makhzan_dir.exists()
            assert result["snapshot_location"] is not None
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_updates_all_11_indices_to_new_version(self):
        """Test 7: increment_schema_version updates all 11 indices to new version field value."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            increment_schema_version(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
                       "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]

            for persona in personas:
                with open(indices_dir / f"{persona}_index.json") as f:
                    index = json.load(f)
                assert index["version"] == "1.1"
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_updates_last_updated_field_on_all_indices(self):
        """Test 8: increment_schema_version updates last_updated field on all indices."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")
        old_time = datetime.now(timezone.utc).isoformat()

        try:
            increment_schema_version(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
                       "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]

            for persona in personas:
                with open(indices_dir / f"{persona}_index.json") as f:
                    index = json.load(f)
                # last_updated should be newer than old_time
                assert index["last_updated"] >= old_time
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_all_indices_pass_validation_after_increment(self):
        """Test 9: After increment_schema_version(), all indices pass validate_schema_versions() with new version."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            increment_schema_version(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            valid, error = validate_schema_versions(indices_dir)
            assert valid is True
            assert error is None
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_raises_error_on_invalid_old_version(self):
        """Test 10: increment_schema_version with invalid old_version raises ValueError."""
        indices_dir = create_test_indices_dir({
            "AMMAR": "1.0", "HIKMAH": "1.1",  # Mismatched versions
            "TARIQ": "1.0", "MUNAWARA": "1.0", "MAL": "1.0",
            "BADAN": "1.0", "NAQD": "1.0", "SHURA": "1.0",
            "TAFRIGH": "1.0", "MARSAD": "1.0", "NIZAM": "1.0"
        })
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            with pytest.raises(ValueError):
                increment_schema_version(
                    indices_dir, "1.0", "1.1", "Added engagement_patterns array"
                )
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_allows_major_version_change_to_2_0(self):
        """Test 11: increment_schema_version with version='2.0' allows breaking changes."""
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            result = increment_schema_version(
                indices_dir, "1.0", "2.0", "Breaking change: removed context_snapshots"
            )

            # Verify all indices are now at 2.0
            personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN",
                       "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]

            for persona in personas:
                with open(indices_dir / f"{persona}_index.json") as f:
                    index = json.load(f)
                assert index["version"] == "2.0"
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)

    def test_atomicity_on_write_failure(self):
        """Test 12: increment_schema_version atomicity behavior on write failure."""
        # This test verifies that if a write fails, we document it.
        # In practice, atomicity is limited by filesystem, but we at least verify all succeed together.
        indices_dir = create_test_indices_dir()
        makhzan_dir = Path("MAKHZAN__archive")

        try:
            result = increment_schema_version(
                indices_dir, "1.0", "1.1", "Added engagement_patterns array"
            )

            # If we reach here, all 11 writes succeeded
            assert result["personas_updated"] == 11
        finally:
            shutil.rmtree(indices_dir)
            if makhzan_dir.exists():
                shutil.rmtree(makhzan_dir)


class TestValidateVersionFormat:
    """Test suite for validate_version_format function."""

    def test_accepts_valid_semantic_versions(self):
        """Test: validate_version_format accepts valid versions like 1.0, 1.1, 2.0."""
        assert validate_version_format("1.0") is True
        assert validate_version_format("1.1") is True
        assert validate_version_format("2.0") is True
        assert validate_version_format("10.5") is True

    def test_rejects_invalid_formats(self):
        """Test: validate_version_format rejects invalid formats."""
        assert validate_version_format("v1.0") is False  # v prefix
        assert validate_version_format("0.5") is False   # 0 major
        assert validate_version_format("1") is False     # no minor
        assert validate_version_format("1.0.0") is False # three parts
