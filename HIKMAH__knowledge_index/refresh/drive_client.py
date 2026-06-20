"""
Google Drive API client for data refresh pipeline.

Provides GoogleDriveClient class wrapping google-api-python-client for Drive API v3 interactions.
Handles credential management, folder/file queries, and error cases with graceful degradation.

Design principles:
1. Service account credentials from NIZAM-secrets.json or environment
2. Folder/file queries use MIME type filtering (folders, JSON, text files)
3. Error handling catches RefreshError (token expiration), HttpError, and file I/O errors
4. Follows Phase 14 writer.py pattern for consistency (JSONL, error logging)

Classes:
    GoogleDriveClient: Main Drive API wrapper
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.oauth2 import service_account
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleDriveClient:
    """
    Wrapper for Google Drive API v3 with credential management and error handling.

    Attributes:
        credentials: service_account.Credentials object
        service: googleapiclient drive service (v3)
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, credentials_path: Path):
        """
        Initialize with service account credentials.

        Args:
            credentials_path: Path to NIZAM-secrets.json or service account JSON file

        Raises:
            RuntimeError: If credential loading fails (file not found, invalid JSON, missing fields)
        """
        try:
            credentials_path = Path(credentials_path)
            credentials_info = json.loads(credentials_path.read_text(encoding='utf-8'))
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
        except FileNotFoundError as e:
            raise RuntimeError(f"Credentials file not found: {credentials_path}: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in credentials file: {credentials_path}: {e}")
        except (ValueError, KeyError) as e:
            raise RuntimeError(f"Invalid service account credentials: {e}")

    def find_folder_by_name(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find folder ID by name.

        Args:
            folder_name: Name of folder to find (e.g., "YAWMIYAT/sessions")
            parent_id: Optional parent folder ID to search within

        Returns:
            Folder ID (string) if found, None if not found

        Raises:
            IOError: On API errors (token expiration, network, etc.)
        """
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()

            files = results.get('files', [])
            if files:
                return files[0]['id']
            return None

        except RefreshError as e:
            raise IOError(f"Token refresh failed: {e}")
        except HttpError as e:
            raise IOError(f"Drive API error (status {e.resp.status}): {e.content}")

    def list_files_in_folder(self, folder_id: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in a folder with metadata.

        Args:
            folder_id: Drive folder ID
            file_type: Optional filter (None = all files, 'json' = JSON files only, 'text' = text files)

        Returns:
            List of dicts with {id, name, modifiedTime, mimeType}

        Raises:
            IOError: On API errors
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"

            if file_type == 'json':
                query += " and mimeType='application/json'"
            elif file_type == 'text':
                query += " and mimeType='text/plain'"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, modifiedTime, mimeType)',
                pageSize=100
            ).execute()

            return results.get('files', [])

        except RefreshError as e:
            raise IOError(f"Token refresh failed: {e}")
        except HttpError as e:
            raise IOError(f"Drive API error (status {e.resp.status}): {e.content}")

    def download_file_content(self, file_id: str) -> str:
        """
        Download file content and decode as UTF-8 string.

        Args:
            file_id: Drive file ID

        Returns:
            File content as UTF-8 string

        Raises:
            IOError: On API errors (token, network, file not found)
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()

            if isinstance(content, bytes):
                return content.decode('utf-8')
            return str(content)

        except RefreshError as e:
            raise IOError(f"Token refresh failed: {e}")
        except HttpError as e:
            raise IOError(f"Drive API error (status {e.resp.status}): {e.content}")
