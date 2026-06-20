"""
Tests for refresh audit logging (ledger_writer.py).

Tests audit ledger format, persistence, hash chaining, and query operations.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from HIKMAH__knowledge_index.refresh.ledger_writer import RefreshAuditLogger


class TestAuditLoggerInit:
    """Tests for RefreshAuditLogger initialization."""

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        logger = RefreshAuditLogger()
        assert logger.ledger_path is not None

    def test_init_with_custom_path(self, tmp_path):
        """Test initialization with custom ledger path."""
        custom_path = tmp_path / "custom.jsonl"
        logger = RefreshAuditLogger(custom_path)
        assert logger.ledger_path == custom_path

    def test_init_creates_parent_directories(self, tmp_path):
        """Test that initialization creates parent directories."""
        nested_path = tmp_path / "a" / "b" / "c" / "ledger.jsonl"
        logger = RefreshAuditLogger(nested_path)

        # Parent should be created
        assert logger.ledger_path.parent.exists()


class TestAuditLogEntry:
    """Tests for audit log entry format and writing."""

    def test_log_refresh_attempt_success(self, tmp_path):
        """Test logging a successful refresh attempt."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        hash_result = logger.log_refresh_attempt(
            persona="AMMAR",
            status="success",
            data_sources=["YAWMIYAT/sessions"],
            files_read=5
        )

        # Check file was created and contains entry
        assert ledger_path.exists()
        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["persona"] == "AMMAR"
        assert entry["status"] == "success"
        assert entry["files_read"] == 5
        assert entry["ts"] is not None
        assert entry["row_hash"] == hash_result

    def test_log_refresh_attempt_failure(self, tmp_path):
        """Test logging a failed refresh attempt."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt(
            persona="HIKMAH",
            status="failure",
            data_sources=["YAWMIYAT/sessions"],
            error="Connection timeout",
            files_read=0
        )

        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["status"] == "failure"
        assert entry["error"] == "Connection timeout"
        assert entry["files_read"] == 0

    def test_log_refresh_attempt_partial(self, tmp_path):
        """Test logging a partial refresh."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt(
            persona="TARIQ",
            status="partial",
            data_sources=["YAWMIYAT/sessions"],
            files_read=2
        )

        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["status"] == "partial"


class TestAuditLedgerFormat:
    """Tests for audit ledger JSONL format and structure."""

    def test_audit_ledger_entry_has_required_fields(self, tmp_path):
        """Test that audit entries have all required fields."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt(
            persona="AMMAR",
            status="success",
            data_sources=["source1", "source2"],
            files_read=3
        )

        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        required_fields = ["ts", "persona", "event_type", "status", "data_sources", "files_read", "error", "row_hash", "prev_hash"]
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"

    def test_audit_ledger_is_jsonl_format(self, tmp_path):
        """Test that ledger is valid JSONL (one JSON per line)."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        # Log multiple entries
        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)
        logger.log_refresh_attempt("HIKMAH", "failure", ["source"], error="test", files_read=0)
        logger.log_refresh_attempt("TARIQ", "success", ["source"], files_read=2)

        # Verify each line is valid JSON
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            for line in lines:
                obj = json.loads(line)
                assert isinstance(obj, dict)

    def test_audit_ledger_timestamps_are_iso8601(self, tmp_path):
        """Test that timestamps are ISO 8601 format."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)

        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        ts = entry["ts"]
        # Should contain T and either Z or +/- offset
        assert "T" in ts
        assert "Z" in ts or "+" in ts or ts.count("-") >= 3  # ISO 8601 format

    def test_audit_ledger_event_type_is_fixed(self, tmp_path):
        """Test that event_type is always 'refresh_attempt'."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)

        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["event_type"] == "refresh_attempt"


class TestAuditHashChaining:
    """Tests for SHA256 hash chaining."""

    def test_row_hash_computed_deterministically(self, tmp_path):
        """Test that row_hash is computed consistently."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        hash1 = logger.log_refresh_attempt(
            persona="AMMAR",
            status="success",
            data_sources=["source"],
            files_read=1
        )

        # Read the entry and verify hash
        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["row_hash"] == hash1

    def test_hash_chain_prev_hash_genesis_first_entry(self, tmp_path):
        """Test that first entry has prev_hash='genesis'."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)

        with open(ledger_path, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["prev_hash"] == "genesis"

    def test_hash_chain_links_entries(self, tmp_path):
        """Test that subsequent entries link to previous hash."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)
        logger.log_refresh_attempt("HIKMAH", "success", ["source"], files_read=2)

        with open(ledger_path, 'r') as f:
            line1 = json.loads(f.readline())
            line2 = json.loads(f.readline())

        # Second entry's prev_hash should match first entry's row_hash
        assert line2["prev_hash"] == line1["row_hash"]


class TestAuditPersistence:
    """Tests for ledger persistence across restarts."""

    def test_audit_ledger_appends_on_reopen(self, tmp_path):
        """Test that ledger entries persist and append correctly."""
        ledger_path = tmp_path / "audit.jsonl"

        # First session
        logger1 = RefreshAuditLogger(ledger_path)
        logger1.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)

        # Second session (reopen)
        logger2 = RefreshAuditLogger(ledger_path)
        logger2.log_refresh_attempt("HIKMAH", "success", ["source"], files_read=2)

        # Verify both entries exist
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2

    def test_audit_ledger_does_not_overwrite(self, tmp_path):
        """Test that reopening ledger does not overwrite existing entries."""
        ledger_path = tmp_path / "audit.jsonl"

        logger1 = RefreshAuditLogger(ledger_path)
        logger1.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)

        logger2 = RefreshAuditLogger(ledger_path)
        logger2.log_refresh_attempt("HIKMAH", "failure", ["source"], error="test", files_read=0)

        with open(ledger_path, 'r') as f:
            entries = [json.loads(line) for line in f.readlines()]

        assert len(entries) == 2
        assert entries[0]["persona"] == "AMMAR"
        assert entries[1]["persona"] == "HIKMAH"


class TestAuditQueryOperations:
    """Tests for querying the audit ledger."""

    def test_get_last_successful_refresh(self, tmp_path):
        """Test retrieving last successful refresh for a persona."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        # Log success, then failure
        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)
        logger.log_refresh_attempt("AMMAR", "failure", ["source"], error="test", files_read=0)

        # Query should return the success entry
        last_success = logger.get_last_successful_refresh("AMMAR")
        assert last_success is not None
        assert last_success["status"] == "success"
        assert last_success["files_read"] == 1

    def test_get_last_successful_refresh_returns_most_recent(self, tmp_path):
        """Test that query returns MOST recent success, not first."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        # Log multiple successes
        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)
        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=5)
        logger.log_refresh_attempt("AMMAR", "failure", ["source"], error="test", files_read=0)
        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=10)

        last_success = logger.get_last_successful_refresh("AMMAR")
        assert last_success["files_read"] == 10

    def test_get_last_successful_refresh_filters_by_persona(self, tmp_path):
        """Test that query filters by persona."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=1)
        logger.log_refresh_attempt("HIKMAH", "success", ["source"], files_read=2)
        logger.log_refresh_attempt("AMMAR", "success", ["source"], files_read=3)

        ammar_last = logger.get_last_successful_refresh("AMMAR")
        hikmah_last = logger.get_last_successful_refresh("HIKMAH")

        assert ammar_last["files_read"] == 3
        assert hikmah_last["files_read"] == 2

    def test_get_last_successful_refresh_returns_none_if_not_found(self, tmp_path):
        """Test that query returns None if no success found."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        logger.log_refresh_attempt("AMMAR", "failure", ["source"], error="test", files_read=0)

        last_success = logger.get_last_successful_refresh("AMMAR")
        assert last_success is None

    def test_get_last_successful_refresh_on_empty_ledger(self, tmp_path):
        """Test query on empty ledger."""
        ledger_path = tmp_path / "empty.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        result = logger.get_last_successful_refresh("AMMAR")
        assert result is None


class TestAuditMultiplePersonas:
    """Tests for multi-persona audit logging."""

    def test_audit_entries_for_multiple_personas(self, tmp_path):
        """Test logging entries for all 11 personas."""
        ledger_path = tmp_path / "audit.jsonl"
        logger = RefreshAuditLogger(ledger_path)

        personas = ["AMMAR", "HIKMAH", "TARIQ", "MUNAWARA", "MAL", "BADAN", "NAQD", "SHURA", "TAFRIGH", "MARSAD", "NIZAM"]

        for persona in personas:
            logger.log_refresh_attempt(persona, "success", ["source"], files_read=1)

        with open(ledger_path, 'r') as f:
            entries = [json.loads(line) for line in f.readlines()]

        assert len(entries) == len(personas)
        logged_personas = {e["persona"] for e in entries}
        assert logged_personas == set(personas)
