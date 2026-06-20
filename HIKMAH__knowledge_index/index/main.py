"""
Index initialization logic for all personas.

Provides entry point functions to create valid, empty knowledge index files
for all 11 personas during Phase 14 setup. These functions are called once
during initialization to create per-persona JSON scaffolds that downstream
phases will populate and modify.

Functions:
    - initialize_persona_index(persona, target_dir): Create index for single persona
    - initialize_all_personas(indices_dir): Create indices for all 11 personas in batch
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from HIKMAH__knowledge_index.index.schema import validate_index_schema, VALID_PERSONAS


def initialize_persona_index(persona: str, target_dir: Path) -> Path:
    """
    Create a valid, empty knowledge index file for a single persona.

    Args:
        persona: Persona name (must be in VALID_PERSONAS)
        target_dir: Directory where index file will be created

    Returns:
        Path to created index file

    Raises:
        ValueError: If persona is not recognized
        FileNotFoundError: If target_dir cannot be created
        IOError: If file write fails

    Example:
        >>> path = initialize_persona_index("AMMAR", Path("indices/"))
        >>> path
        PosixPath('indices/AMMAR_index.json')
    """

    # Validate persona is registered
    if persona not in VALID_PERSONAS:
        raise ValueError(f"Unknown persona: {persona}. Valid personas: {VALID_PERSONAS}")

    # Create target directory if missing (parents=True, exist_ok=True)
    target_dir = Path(target_dir)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise FileNotFoundError(f"Could not create target directory {target_dir}: {e}")

    # Generate current timestamp in ISO 8601 UTC format
    now = datetime.now(timezone.utc).isoformat()

    # Create template index with all required fields
    index = {
        "version": "1.0",
        "persona": persona,
        "initialized_at": now,
        "last_updated": now,
        "topics": [],
        "completions": [],
        "activity_history": [
            {
                "ts": now,
                "event_type": "index_initialized",
                "topic_id": None,
                "description": f"Knowledge index initialized for {persona}"
            }
        ],
        "stalled_work": [],
        "context_snapshots": [
            {
                "ts": now,
                "snapshot": {
                    "open_topic_count": 0,
                    "active_blocker_count": 0,
                    "recent_accomplishments_count": 0,
                    "completion_rate_7d": 0.0,
                    "engagement_level": "unknown"
                }
            }
        ],
        "metadata": {
            "source": "v1.1-knowledge-index",
            "locale": "Egypt/Cairo",
            "language": "en"
        }
    }

    # Validate schema before writing
    is_valid, error = validate_index_schema(index)
    if not is_valid:
        raise ValueError(f"Index schema validation failed: {error}")

    # Write index to file
    target_file = target_dir / f"{persona}_index.json"
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Failed to write index file {target_file}: {e}")

    print(f"[OK] Index initialized for {persona}: {target_file}")
    return target_file


def initialize_all_personas(indices_dir: Path) -> Dict[str, Path]:
    """
    Create valid, empty knowledge indices for all 11 personas in batch.

    Args:
        indices_dir: Target directory for index files

    Returns:
        Mapping of persona name to path of created index file
        Example: {"AMMAR": Path("indices/AMMAR_index.json"), ...}

    Raises:
        ValueError: If any persona initialization fails (aborts early)
        IOError: If file operations fail

    Example:
        >>> result = initialize_all_personas(Path("indices/"))
        >>> len(result)
        11
        >>> result["HIKMAH"]
        PosixPath('indices/HIKMAH_index.json')
    """

    indices_dir = Path(indices_dir)
    result = {}

    for persona in VALID_PERSONAS:
        try:
            path = initialize_persona_index(persona, indices_dir)
            result[persona] = path
        except Exception as e:
            raise ValueError(
                f"Failed to initialize {persona}: {e}. Aborting batch initialization."
            )

    return result
