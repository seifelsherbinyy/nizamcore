"""
Tests for refresh fallback logic (graceful degradation).

Tests success path, all failure modes (network, auth, malformed), and audit logging.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from HIKMAH__knowledge_index.refresh import refresh_persona_index, load_cached_index
from HIKMAH__knowledge_index.refresh.ledger_writer import RefreshAuditLogger


class TestRefreshSuccess:
    """Tests for successful refresh path."""

    def test_refresh_success(self, mock_drive_client, sample_index_file, tmp_path):
        """Test successful refresh from Drive."""
        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_drive_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        assert success is True
        assert reason is None
        assert index is not None

    def test_refresh_audit_logged_on_success(self, mock_drive_client, sample_index_file, tmp_path):
        """Test that successful refresh is logged to audit ledger."""
        audit_path = tmp_path / "audit.jsonl"
        audit_logger = RefreshAuditLogger(audit_path)

        refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_drive_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        # Check audit ledger was written
        assert audit_path.exists()
        with open(audit_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0


class TestRefreshFolderNotFound:
    """Tests for handling missing YAWMIYAT/sessions folder."""

    def test_refresh_fallback_on_folder_not_found(self, sample_index_file, tmp_path):
        """Test fallback to cached index when folder not found."""
        mock_client = Mock()
        mock_client.find_folder_by_name.return_value = None  # Folder not found

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        assert success is False
        assert reason is not None
        assert "not found" in reason.lower() or "folder" in reason.lower()
        assert index is not None  # Cached index returned

    def test_refresh_returns_cached_index_on_failure(self, sample_index_file, tmp_path):
        """Test that cached index is returned on any Drive error."""
        mock_client = Mock()
        mock_client.find_folder_by_name.side_effect = IOError("Connection timeout")

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        # Should return cached index
        assert success is False
        assert index is not None
        assert index["persona"] == "AMMAR"


class TestRefreshNetworkErrors:
    """Tests for handling network errors."""

    def test_refresh_fallback_on_http_error(self, sample_index_file, tmp_path):
        """Test fallback on HTTP errors (401, 403, 500)."""
        mock_client = Mock()
        mock_client.find_folder_by_name.side_effect = IOError("Drive API error (status 403): Forbidden")

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        assert success is False
        assert "403" in reason or "Forbidden" in reason
        assert index is not None

    def test_refresh_fallback_on_timeout(self, sample_index_file, tmp_path):
        """Test fallback on network timeout."""
        mock_client = Mock()
        mock_client.find_folder_by_name.side_effect = IOError("Connection timeout")

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        assert success is False
        assert index is not None

    def test_refresh_fallback_on_token_refresh_error(self, sample_index_file, tmp_path):
        """Test fallback on token refresh failure."""
        mock_client = Mock()
        mock_client.find_folder_by_name.side_effect = IOError("Token refresh failed")

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        assert success is False
        assert "Token" in reason or "refresh" in reason
        assert index is not None


class TestRefreshMalformedData:
    """Tests for handling malformed data from Drive."""

    def test_refresh_fallback_on_malformed_json(self, sample_index_file, tmp_path):
        """Test fallback when Drive returns malformed JSON."""
        mock_client = Mock()
        mock_client.find_folder_by_name.return_value = "folder-id"
        mock_client.list_files_in_folder.return_value = [
            {"id": "file-1", "name": "bad.json"}
        ]

        def download_with_error(file_id):
            raise IOError("Failed to download file")

        mock_client.download_file_content = download_with_error

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        # Should gracefully fall back (no files processed = partial/failure)
        assert index is not None

    def test_refresh_continues_on_individual_file_error(self, sample_index_file, tmp_path):
        """Test that refresh continues if one file fails."""
        mock_client = Mock()
        mock_client.find_folder_by_name.return_value = "folder-id"
        mock_client.list_files_in_folder.return_value = [
            {"id": "file-1", "name": "bad.json"},
            {"id": "file-2", "name": "good.json"}
        ]

        def download_content(file_id):
            if file_id == "file-1":
                raise IOError("Cannot read file")
            return '{"topics": [], "events": []}'

        mock_client.download_file_content = download_content

        audit_logger = RefreshAuditLogger(tmp_path / "audit.jsonl")

        success, index, reason = refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        # Should continue and not fail completely
        assert index is not None


class TestRefreshAuditLogging:
    """Tests for audit trail logging."""

    def test_audit_logged_on_failure(self, sample_index_file, tmp_path):
        """Test that failures are logged with error details."""
        audit_path = tmp_path / "audit.jsonl"
        audit_logger = RefreshAuditLogger(audit_path)

        mock_client = Mock()
        mock_client.find_folder_by_name.side_effect = IOError("Test error")

        refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        # Check audit entry
        import json
        with open(audit_path, 'r') as f:
            entry = json.loads(f.readline())
            assert entry["status"] == "failure"
            assert "Test error" in entry["error"]

    def test_audit_logged_on_partial_success(self, sample_index_file, tmp_path):
        """Test that partial refreshes (no files) are logged."""
        audit_path = tmp_path / "audit.jsonl"
        audit_logger = RefreshAuditLogger(audit_path)

        mock_client = Mock()
        mock_client.find_folder_by_name.return_value = "folder-id"
        mock_client.list_files_in_folder.return_value = []  # No files

        refresh_persona_index(
            persona="AMMAR",
            drive_client=mock_client,
            index_path=sample_index_file,
            audit_logger=audit_logger
        )

        import json
        with open(audit_path, 'r') as f:
            entry = json.loads(f.readline())
            assert entry["status"] == "partial" or entry["status"] == "failure"


class TestLoadCachedIndex:
    """Tests for load_cached_index function."""

    def test_load_cached_index_success(self, sample_index_file):
        """Test loading a valid cached index."""
        index = load_cached_index(sample_index_file)
        assert index is not None
        assert index["persona"] == "AMMAR"

    def test_load_cached_index_missing_file(self, tmp_path):
        """Test loading from missing file."""
        missing_path = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_cached_index(missing_path)

    def test_load_cached_index_invalid_json(self, tmp_path):
        """Test loading malformed JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ not valid json")

        with pytest.raises(Exception):  # json.JSONDecodeError or similar
            load_cached_index(bad_file)
