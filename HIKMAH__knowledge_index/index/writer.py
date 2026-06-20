"""
Ledger writer for knowledge index initialization and updates.

Provides functions to persist index files and ledger entries with hash chaining
and immutable audit trail. Ledger entries follow NIZAM pattern: JSONL format,
append-only, SHA256 hash chaining for integrity.

Functions:
    - write_index_to_file(index, target_path): Serialize and write index to JSON file
    - write_initialization_event_to_ledger(persona, file_path, ledger_path): Append JSONL ledger entry
    - compute_row_hash(row_dict): Compute SHA256 of ledger row
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def write_index_to_file(index: Dict, target_path: Path) -> Path:
    """
    Serialize index to JSON and write to file.

    Args:
        index: Index dictionary to write
        target_path: Path where file will be written

    Returns:
        target_path (as Path object)

    Raises:
        IOError: If file write fails
        TypeError: If index is not serializable to JSON

    Example:
        >>> index = {"version": "1.0", "persona": "AMMAR", ...}
        >>> path = write_index_to_file(index, Path("AMMAR_index.json"))
        >>> path.exists()
        True
    """
    target_path = Path(target_path)

    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Failed to write index file {target_path}: {e}")
    except TypeError as e:
        raise TypeError(f"Index contains non-serializable data: {e}")

    return target_path


def compute_row_hash(row_dict: Dict) -> str:
    """
    Compute SHA256 hash of ledger row.

    Args:
        row_dict: Row dictionary to hash (excludes row_hash field itself)

    Returns:
        SHA256 hex digest

    Note:
        row_dict should NOT include 'row_hash' field when calling this function.
    """
    # Create a copy and exclude row_hash if present
    row_copy = {k: v for k, v in row_dict.items() if k != 'row_hash'}

    # Serialize to JSON with sorted keys for deterministic output
    serialized = json.dumps(row_copy, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

    # Compute SHA256
    hash_obj = hashlib.sha256(serialized.encode('utf-8'))
    return hash_obj.hexdigest()


def write_initialization_event_to_ledger(
    persona: str,
    file_path: Path,
    ledger_path: Path
) -> str:
    """
    Append initialization event to PERSONA_KNOWLEDGE_INDEX ledger.

    Ledger is JSONL format (one JSON object per line), append-only, with hash chaining
    for integrity verification. Entry includes all metadata needed for audit trail.

    Args:
        persona: Persona name (e.g., "AMMAR")
        file_path: Path to created index file
        ledger_path: Path to ledger file (JSONL)

    Returns:
        row_id (UUID string) for tracing

    Raises:
        IOError: If ledger write fails
        ValueError: If row validation fails

    Example:
        >>> row_id = write_initialization_event_to_ledger(
        ...     "AMMAR",
        ...     Path("AMMAR_index.json"),
        ...     Path("PERSONA_KNOWLEDGE_INDEX.jsonl")
        ... )
        >>> print(row_id)
        a1b2c3d4-...
    """

    ledger_path = Path(ledger_path)
    file_path = Path(file_path)

    # Create ledger directory if missing
    try:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise IOError(f"Could not create ledger directory {ledger_path.parent}: {e}")

    # Read last row hash if ledger exists
    prev_hash = "genesis"
    if ledger_path.exists():
        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        last_row = json.loads(last_line)
                        prev_hash = last_row.get('row_hash', 'genesis')
        except Exception as e:
            raise IOError(f"Failed to read last hash from ledger {ledger_path}: {e}")

    # Create ledger entry
    row_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    row = {
        "ts": now,
        "ledger": "PERSONA_KNOWLEDGE_INDEX",
        "row_id": row_id,
        "trace_id": trace_id,
        "actor": "auto_system",
        "action": "index_initialized",
        "persona": persona,
        "module": "HIKMAH__knowledge_index",
        "privacy_class": "strict_local",
        "prev_hash": prev_hash,
        "payload": {
            "file_path": str(file_path),
            "event": "initialization"
        }
    }

    # Compute row hash (excluding row_hash field itself)
    row["row_hash"] = compute_row_hash(row)

    # Validate row before writing
    if not row.get("row_hash"):
        raise ValueError("Failed to compute row_hash")

    # Append to ledger as JSONL
    try:
        with open(ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
    except IOError as e:
        raise IOError(f"Failed to append to ledger {ledger_path}: {e}")

    print(f"[OK] Logged initialization event for {persona}: {ledger_path}")
    return row_id
