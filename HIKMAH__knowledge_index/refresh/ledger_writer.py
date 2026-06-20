"""
Refresh audit logging to REFRESH_AUDIT_LEDGER.jsonl.

Provides RefreshAuditLogger class following Phase 14 ledger writer pattern.
Logs all refresh attempts (success, failure, partial) with full audit trail:
timestamps, data sources, files read, error details, and SHA256 hash chaining.

Design principles:
1. JSONL format (one JSON object per line, append-only)
2. Hash chaining for integrity verification (SHA256 computed per row)
3. All timestamps ISO 8601 UTC format
4. Deterministic JSON serialization for hashing (sorted keys, no spaces)
5. Follows Phase 14 writer.py pattern for consistency

Classes:
    RefreshAuditLogger: Audit trail logger with append and query methods
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


class RefreshAuditLogger:
    """
    Audit trail logger for all refresh operations.

    Logs every refresh attempt (success or failure) to an append-only JSONL ledger.
    Supports hash chaining for integrity and querying for the last successful refresh.

    Attributes:
        ledger_path: Path to REFRESH_AUDIT_LEDGER.jsonl file
    """

    def __init__(self, ledger_path: Optional[Path] = None):
        """
        Initialize audit logger with ledger path.

        Args:
            ledger_path: Path to REFRESH_AUDIT_LEDGER.jsonl (defaults to HIKMAH__knowledge_index/REFRESH_AUDIT_LEDGER.jsonl)

        Raises:
            FileNotFoundError: If ledger_path parent directory cannot be created
        """
        if ledger_path is None:
            ledger_path = Path("HIKMAH__knowledge_index") / "REFRESH_AUDIT_LEDGER.jsonl"

        self.ledger_path = Path(ledger_path)

        # Create parent directories if needed
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileNotFoundError(f"Could not create ledger directory {self.ledger_path.parent}: {e}")

    def log_refresh_attempt(
        self,
        persona: str,
        status: str,
        data_sources: List[str],
        error: Optional[str] = None,
        files_read: int = 0
    ) -> str:
        """
        Log a refresh attempt to the audit ledger.

        Args:
            persona: Persona name (e.g., "AMMAR")
            status: One of "success", "failure", "partial"
            data_sources: List of data sources queried (e.g., ["YAWMIYAT/sessions"])
            error: Optional error message (if status != "success")
            files_read: Number of files processed

        Returns:
            row_hash: SHA256 hash of the logged entry

        Raises:
            IOError: If ledger write fails
        """
        # Create ledger entry
        now = datetime.now(timezone.utc).isoformat()

        # Get previous row hash for chaining
        prev_hash = "genesis"
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if last_line:
                            last_row = json.loads(last_line)
                            prev_hash = last_row.get('row_hash', 'genesis')
            except Exception as e:
                # If we can't read the last hash, just use genesis
                prev_hash = "genesis"

        row = {
            "ts": now,
            "persona": persona,
            "event_type": "refresh_attempt",
            "status": status,
            "data_sources": data_sources,
            "files_read": files_read,
            "error": error,
            "prev_hash": prev_hash
        }

        # Compute row hash (excluding row_hash field itself)
        row["row_hash"] = self._compute_row_hash(row)

        # Append to ledger as JSONL
        try:
            with open(self.ledger_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
        except IOError as e:
            raise IOError(f"Failed to append to audit ledger {self.ledger_path}: {e}")

        return row["row_hash"]

    def get_last_successful_refresh(self, persona: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent successful refresh for a persona.

        Args:
            persona: Persona name (e.g., "AMMAR")

        Returns:
            Ledger entry dict if found, None if no successful refresh found

        Raises:
            IOError: If ledger read fails
        """
        if not self.ledger_path.exists():
            return None

        try:
            with open(self.ledger_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            last_success = None
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    if (entry.get("persona") == persona and
                        entry.get("event_type") == "refresh_attempt" and
                        entry.get("status") == "success"):
                        last_success = entry
                        break
                except json.JSONDecodeError:
                    continue

            return last_success

        except IOError as e:
            raise IOError(f"Failed to read audit ledger {self.ledger_path}: {e}")

    @staticmethod
    def _compute_row_hash(row_dict: Dict) -> str:
        """
        Compute SHA256 hash of ledger row.

        Args:
            row_dict: Row dictionary to hash (excludes row_hash field if present)

        Returns:
            SHA256 hex digest
        """
        # Create a copy and exclude row_hash if present
        row_copy = {k: v for k, v in row_dict.items() if k != 'row_hash'}

        # Serialize to JSON with sorted keys for deterministic output
        serialized = json.dumps(row_copy, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

        # Compute SHA256
        hash_obj = hashlib.sha256(serialized.encode('utf-8'))
        return hash_obj.hexdigest()
