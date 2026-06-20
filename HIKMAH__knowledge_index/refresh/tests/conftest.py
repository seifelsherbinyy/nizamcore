"""
Pytest fixtures for Phase 15 refresh tests.

Provides mocked Drive service, sample indices, and fixtures for all refresh tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
from pathlib import Path


@pytest.fixture
def mock_credentials():
    """Mock service account credentials object."""
    mock_creds = Mock()
    mock_creds.expired = False
    mock_creds.valid = True
    return mock_creds


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive API v3 service."""
    mock_service = Mock()

    # Mock files().list() response
    mock_files_list = Mock()
    mock_files_list.execute.return_value = {
        'files': [
            {
                'id': 'folder-yawmiyat-sessions',
                'name': 'YAWMIYAT/sessions',
                'mimeType': 'application/vnd.google-apps.folder'
            }
        ]
    }
    mock_service.files.return_value.list.return_value = mock_files_list

    # Mock files().get_media() response
    mock_get_media = Mock()
    mock_get_media.execute.return_value = b'{"topics": [], "events": []}'
    mock_service.files.return_value.get_media.return_value = mock_get_media

    return mock_service


@pytest.fixture
def mock_drive_client(mock_drive_service, tmp_path):
    """Mock GoogleDriveClient with service injected."""
    from HIKMAH__knowledge_index.refresh.drive_client import GoogleDriveClient

    # Create a mock client
    client = Mock(spec=GoogleDriveClient)
    client.service = mock_drive_service

    # Implement find_folder_by_name
    def find_folder(name, parent_id=None):
        if name == "YAWMIYAT/sessions":
            return "folder-yawmiyat-sessions"
        return None

    client.find_folder_by_name = find_folder

    # Implement list_files_in_folder
    def list_files(folder_id, file_type=None):
        if folder_id == "folder-yawmiyat-sessions":
            return [
                {
                    'id': 'file-activity-1',
                    'name': 'activity_log_1.json',
                    'modifiedTime': datetime.now(timezone.utc).isoformat(),
                    'mimeType': 'application/json'
                }
            ]
        return []

    client.list_files_in_folder = list_files

    # Implement download_file_content
    def download_content(file_id):
        if file_id == 'file-activity-1':
            return '{"topics": [{"id": "t1", "name": "New Topic"}], "events": []}'
        return '{}'

    client.download_file_content = download_content

    return client


@pytest.fixture
def sample_persona_index():
    """Valid persona index for testing."""
    return {
        "version": "1.0",
        "persona": "AMMAR",
        "initialized_at": "2026-06-20T10:00:00Z",
        "last_updated": "2026-06-20T10:00:00Z",
        "topics": [
            {
                "id": "topic-1",
                "name": "Existing Topic",
                "status": "active",
                "created_at": "2026-06-15T10:00:00Z",
                "last_activity": "2026-06-20T09:00:00Z",
                "context_tags": ["technical"],
                "confidence": 0.8,
                "key_accomplishments": [],
                "blockers": [],
                "notes": ""
            }
        ],
        "completions": [
            {
                "id": "completed-1",
                "name": "Completed Task",
                "completed_at": "2026-06-20T08:00:00Z",
                "duration_days": 5,
                "context_tags": ["technical"],
                "final_note": "Done"
            }
        ],
        "activity_history": [
            {
                "ts": "2026-06-20T10:00:00Z",
                "event_type": "index_initialized",
                "topic_id": None,
                "description": "Index initialized"
            }
        ],
        "stalled_work": [
            {
                "topic_id": "stalled-1",
                "topic_name": "Stalled Task",
                "blocker_count": 1,
                "stalled_since": "2026-06-10T10:00:00Z",
                "days_stalled": 10,
                "last_activity": "2026-06-10T10:00:00Z",
                "recovery_notes": "Waiting for input"
            }
        ],
        "context_snapshots": [],
        "metadata": {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
    }


@pytest.fixture
def sample_activity_data():
    """Sample activity data from Drive."""
    return {
        "topics": [
            {
                "id": "new-topic-1",
                "name": "New Topic from Drive",
                "status": "active",
                "created_at": "2026-06-20T09:00:00Z",
                "last_activity": "2026-06-20T10:30:00Z",
                "context_tags": ["technical"],
                "confidence": 0.75,
                "key_accomplishments": [],
                "blockers": [],
                "notes": "Created from Drive sync"
            }
        ],
        "events": [
            {
                "ts": "2026-06-20T10:30:00Z",
                "event_type": "topic_created",
                "topic_id": "new-topic-1",
                "description": "Topic created from Drive activity"
            }
        ]
    }


@pytest.fixture
def temp_indices_dir(tmp_path):
    """Temporary directory for test indices."""
    return tmp_path / "indices"


@pytest.fixture
def sample_index_file(sample_persona_index, tmp_path):
    """Write sample index to temp file and return path."""
    import json
    index_file = tmp_path / "AMMAR_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(sample_persona_index, f)
    return index_file
