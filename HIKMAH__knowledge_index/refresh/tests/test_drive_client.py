"""
Tests for Google Drive API client (drive_client.py).

Tests credential loading, folder/file queries, downloads, and error handling.
"""

import pytest
import json
from unittest.mock import Mock, patch
from pathlib import Path
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from HIKMAH__knowledge_index.refresh.drive_client import GoogleDriveClient


class TestGoogleDriveClientInit:
    """Tests for GoogleDriveClient initialization."""

    def test_init_with_valid_credentials(self, tmp_path):
        """Test initialization with valid service account credentials."""
        credentials_file = tmp_path / "credentials.json"
        credentials_file.write_text(json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key-id",
            "private_key": "fake-key",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123456789",
        }))

        with patch('HIKMAH__knowledge_index.refresh.drive_client.service_account') as mock_sa:
            with patch('HIKMAH__knowledge_index.refresh.drive_client.build') as mock_build:
                mock_creds = Mock()
                mock_sa.Credentials.from_service_account_info.return_value = mock_creds
                mock_build.return_value = Mock()

                client = GoogleDriveClient(credentials_file)
                assert client is not None
                assert client.service is not None
                mock_sa.Credentials.from_service_account_info.assert_called_once()

    def test_init_with_missing_file(self, tmp_path):
        """Test initialization fails with missing credentials file."""
        missing_file = tmp_path / "missing.json"
        with pytest.raises(RuntimeError, match="Credentials file not found"):
            GoogleDriveClient(missing_file)

    def test_init_with_invalid_json(self, tmp_path):
        """Test initialization fails with malformed JSON."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("not valid json {")
        with pytest.raises(RuntimeError, match="Invalid JSON"):
            GoogleDriveClient(bad_json)


class TestGoogleDriveClientFolderQueries:
    """Tests for folder finding and file listing."""

    def test_find_folder_by_name_success(self, mock_drive_client):
        """Test finding a folder by name."""
        result = mock_drive_client.find_folder_by_name("YAWMIYAT/sessions")
        assert result == "folder-yawmiyat-sessions"

    def test_find_folder_by_name_not_found(self, mock_drive_client):
        """Test finding a folder that doesn't exist."""
        result = mock_drive_client.find_folder_by_name("NonExistent")
        assert result is None

    def test_list_files_in_folder(self, mock_drive_client):
        """Test listing files in a folder."""
        files = mock_drive_client.list_files_in_folder("folder-yawmiyat-sessions", file_type='json')
        assert len(files) > 0
        assert files[0]['id'] == 'file-activity-1'
        assert files[0]['mimeType'] == 'application/json'

    def test_list_files_empty_folder(self, mock_drive_client):
        """Test listing files in empty folder."""
        files = mock_drive_client.list_files_in_folder("nonexistent-folder")
        assert files == []


class TestGoogleDriveClientDownload:
    """Tests for file download operations."""

    def test_download_file_content(self, mock_drive_client):
        """Test downloading and decoding file content."""
        content = mock_drive_client.download_file_content("file-activity-1")
        assert isinstance(content, str)
        assert "topics" in content

    def test_download_file_invalid(self, mock_drive_client):
        """Test downloading non-existent file."""
        content = mock_drive_client.download_file_content("nonexistent-file")
        assert content == "{}"


class TestGoogleDriveClientErrorHandling:
    """Tests for error handling."""

    def test_refresh_error_handling(self):
        """Test handling of RefreshError (token expiration)."""
        with patch('HIKMAH__knowledge_index.refresh.drive_client.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service

            # Create a real client
            with patch('HIKMAH__knowledge_index.refresh.drive_client.service_account') as mock_sa:
                mock_creds = Mock()
                mock_sa.Credentials.from_service_account_info.return_value = mock_creds

                credentials_file = Path("test.json")
                with patch.object(Path, 'read_text', return_value='{}'):
                    with patch('json.loads', return_value={}):
                        client = GoogleDriveClient(credentials_file)

                        # Setup service to raise RefreshError
                        mock_service.files.return_value.list.return_value.execute.side_effect = RefreshError("Token expired")

                        with pytest.raises(IOError, match="Token refresh failed"):
                            client.find_folder_by_name("test")

    def test_http_error_handling(self):
        """Test handling of HttpError (API errors)."""
        with patch('HIKMAH__knowledge_index.refresh.drive_client.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service

            with patch('HIKMAH__knowledge_index.refresh.drive_client.service_account') as mock_sa:
                mock_creds = Mock()
                mock_sa.Credentials.from_service_account_info.return_value = mock_creds

                credentials_file = Path("test.json")
                with patch.object(Path, 'read_text', return_value='{}'):
                    with patch('json.loads', return_value={}):
                        client = GoogleDriveClient(credentials_file)

                        # Setup service to raise HttpError
                        mock_resp = Mock()
                        mock_resp.status = 403
                        http_error = HttpError(mock_resp, b"Forbidden")
                        mock_service.files.return_value.list.return_value.execute.side_effect = http_error

                        with pytest.raises(IOError, match="Drive API error"):
                            client.find_folder_by_name("test")
