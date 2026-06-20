"""
Schema versioning via MAKHZAN snapshot pattern.

Provides functions for managing persona knowledge index schema evolution
while preserving backward compatibility and enabling rollback via
MAKHZAN snapshot archives.

Core features:
- Semantic versioning (1.0, 1.1, 2.0) with format validation
- Atomic updates to all 11 persona indices
- MAKHZAN snapshot creation before version bumps
- Version mismatch detection and validation
- Backward-compatible 1.x changes; breaking 2.x changes

Functions:
    - validate_version_format(version): Check version format validity
    - validate_schema_versions(indices_dir): Verify all indices at same version
    - snapshot_indices_to_makhzan(indices_dir, from_v, to_v, change_desc): Create MAKHZAN snapshot
    - increment_schema_version(indices_dir, old_v, new_v, change_desc): Atomically bump all indices
"""

import json
import shutil
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple
from HIKMAH__knowledge_index.index.schema import validate_index_schema


def validate_version_format(version: str) -> bool:
    r"""
    Validate semantic version format.

    Version must match pattern: "^[1-9][0-9]*\.[0-9]+$"
    Valid examples: 1.0, 1.1, 2.0, 10.5
    Invalid examples: v1.0, 0.5, 1, 1.0.0

    Args:
        version: Version string to validate

    Returns:
        True if version format is valid; False otherwise

    Example:
        >>> validate_version_format("1.0")
        True
        >>> validate_version_format("v1.0")
        False
    """
    pattern = r"^[1-9][0-9]*\.[0-9]+$"
    return bool(re.match(pattern, version))


def validate_schema_versions(indices_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that all persona indices are at the same schema version.

    Lists all {PERSONA}_index.json files in indices_dir, reads each,
    extracts version field, and confirms all versions are identical.

    Args:
        indices_dir: Path to directory containing persona index files

    Returns:
        Tuple[bool, Optional[str]]:
            - (True, None) if all indices are at same version
            - (False, error_msg) if versions mismatch
            - Raises FileNotFoundError if indices_dir doesn't exist
            - Raises error if any file is unreadable

    Example:
        >>> valid, error = validate_schema_versions(Path("HIKMAH__knowledge_index/indices"))
        >>> if valid:
        ...     print("All indices synchronized")
        >>> else:
        ...     print(f"Version mismatch: {error}")
    """
    indices_dir = Path(indices_dir)

    if not indices_dir.exists():
        raise FileNotFoundError(f"Indices directory not found: {indices_dir}")

    # Find all {PERSONA}_index.json files
    index_files = sorted(indices_dir.glob("*_index.json"))

    if not index_files:
        raise FileNotFoundError(f"No index files found in {indices_dir}")

    versions = {}
    for index_file in index_files:
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            version = index.get("version")
            if version is None:
                return False, f"Missing version field in {index_file.name}"
            versions[index_file.name] = version
        except Exception as e:
            raise IOError(f"Failed to read {index_file}: {e}")

    # Check all versions are identical
    unique_versions = set(versions.values())
    if len(unique_versions) == 1:
        return True, None
    else:
        version_summary = "; ".join(f"{k}={v}" for k, v in sorted(versions.items()))
        return False, f"Version mismatch detected: {version_summary}"


def snapshot_indices_to_makhzan(
    indices_dir: Path,
    from_version: str,
    to_version: str,
    change_description: str
) -> Path:
    """
    Create MAKHZAN snapshot of all persona indices before version bump.

    Creates directory structure:
        MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices/

    Copies all {PERSONA}_index.json files to snapshot location, preserving
    content exactly. Creates MANIFEST.json with change metadata, versions,
    timestamp, and recovery notes.

    Args:
        indices_dir: Path to directory containing persona indices
        from_version: Old schema version (e.g., "1.0")
        to_version: New schema version (e.g., "1.1")
        change_description: Description of change (e.g., "Added engagement_patterns array")

    Returns:
        Path to snapshot indices directory (MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices/)

    Raises:
        IOError: If any copy fails
        FileNotFoundError: If indices_dir doesn't exist

    Example:
        >>> snapshot_path = snapshot_indices_to_makhzan(
        ...     Path("HIKMAH__knowledge_index/indices"),
        ...     "1.0", "1.1",
        ...     "Added engagement_patterns array"
        ... )
        >>> snapshot_path.exists()
        True
    """
    indices_dir = Path(indices_dir)

    if not indices_dir.exists():
        raise FileNotFoundError(f"Indices directory not found: {indices_dir}")

    # Create MAKHZAN base directory
    makhzan_base = Path("MAKHZAN__archive")
    makhzan_base.mkdir(parents=True, exist_ok=True)

    # Create timestamp-based subdirectory (ISO 8601 format, safe for filesystem)
    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace("+", "Z")
    makhzan_snapshot = makhzan_base / timestamp / "HIKMAH__knowledge_index" / "indices"
    makhzan_snapshot.mkdir(parents=True, exist_ok=True)

    # Copy all {PERSONA}_index.json files
    try:
        for index_file in indices_dir.glob("*_index.json"):
            dest_file = makhzan_snapshot / index_file.name
            shutil.copy2(index_file, dest_file)
    except Exception as e:
        raise IOError(f"Failed to copy indices to MAKHZAN snapshot: {e}")

    # Create MANIFEST.json in parent directory (MAKHZAN__archive/{ISO_TIMESTAMP}/)
    manifest_path = makhzan_snapshot.parent.parent / "MANIFEST.json"
    manifest = {
        "trigger": "schema_version_increment",
        "from_version": from_version,
        "to_version": to_version,
        "change": change_description,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "indices_backed_up": len(list(makhzan_snapshot.glob("*_index.json"))),
        "operator": "auto_system",
        "recovery_note": "If rollback needed, restore indices from this snapshot and revert schema_version field"
    }

    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Failed to write MANIFEST.json: {e}")

    return makhzan_snapshot


def increment_schema_version(
    indices_dir: Path,
    old_version: str,
    new_version: str,
    change_description: str
) -> Dict:
    """
    Atomically increment schema version across all 11 persona indices.

    Procedure:
    1. Validate old_version matches all indices using validate_schema_versions()
    2. Create MAKHZAN snapshot of current indices
    3. For each {PERSONA}_index.json:
        - Read file to dict
        - Update version field to new_version
        - Update last_updated field to current UTC timestamp
        - Validate updated dict using validate_index_schema()
        - Write updated dict back to file
    4. Return summary dict with personas_updated, snapshot_location, manifest_location

    Args:
        indices_dir: Path to directory containing persona indices
        old_version: Current schema version (e.g., "1.0")
        new_version: Target schema version (e.g., "1.1")
        change_description: Description of change (e.g., "Added engagement_patterns array")

    Returns:
        Dict with keys:
            - personas_updated (int): Number of indices successfully updated (should be 11)
            - snapshot_location (Path): Path to MAKHZAN snapshot directory
            - manifest_location (Path): Path to MANIFEST.json

    Raises:
        ValueError: If old_version doesn't match all indices or version format invalid
        IOError: If any file write fails
        FileNotFoundError: If indices_dir doesn't exist

    Example:
        >>> result = increment_schema_version(
        ...     Path("HIKMAH__knowledge_index/indices"),
        ...     "1.0", "1.1",
        ...     "Added engagement_patterns array"
        ... )
        >>> result["personas_updated"]
        11
    """
    indices_dir = Path(indices_dir)

    if not indices_dir.exists():
        raise FileNotFoundError(f"Indices directory not found: {indices_dir}")

    # Validate version formats
    if not validate_version_format(old_version):
        raise ValueError(f"Invalid old_version format: {old_version}")
    if not validate_version_format(new_version):
        raise ValueError(f"Invalid new_version format: {new_version}")

    # Validate old_version matches all indices
    valid, error = validate_schema_versions(indices_dir)
    if not valid:
        raise ValueError(f"Version mismatch in indices: {error}")

    # Additional check: the detected version must match old_version
    # Read first index to get current version
    first_index_file = next(indices_dir.glob("*_index.json"), None)
    if first_index_file:
        with open(first_index_file, 'r', encoding='utf-8') as f:
            first_index = json.load(f)
        current_version = first_index.get("version")
        if current_version != old_version:
            raise ValueError(
                f"Mismatch: indices at version {current_version}, "
                f"but old_version specified as {old_version}"
            )

    # Create MAKHZAN snapshot
    snapshot_path = snapshot_indices_to_makhzan(
        indices_dir, old_version, new_version, change_description
    )
    manifest_path = snapshot_path.parent.parent / "MANIFEST.json"

    # Update all indices
    now_utc = datetime.now(timezone.utc).isoformat()
    personas_updated = 0

    try:
        for index_file in sorted(indices_dir.glob("*_index.json")):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)

            # Update version and last_updated
            index["version"] = new_version
            index["last_updated"] = now_utc

            # Validate updated index
            valid, error = validate_index_schema(index)
            if not valid:
                raise ValueError(f"Index validation failed for {index_file.name}: {error}")

            # Write updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)

            personas_updated += 1
    except Exception as e:
        raise IOError(f"Failed to update index files: {e}")

    return {
        "personas_updated": personas_updated,
        "snapshot_location": snapshot_path,
        "manifest_location": manifest_path
    }
