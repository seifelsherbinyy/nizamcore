"""config.py — Configuration and profile seed loader for TARIQ Career Radar.

Loads environment variables, defines path constants, and provides
load_profile_seed() to read the local-only profile cache.

Pure stdlib.
"""
from __future__ import annotations
import json
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
PROFILE_CACHE_PATH = MODULE_ROOT / "data" / "profile_cache.json"


def load_profile_seed() -> dict:
    """Load the local profile seed (strict_local_maximum).

    Raises ValueError if the file is absent or missing required keys.
    Never serialize the returned dict to any egress path (Telegram, Drive, ledger).

    Returns:
        dict with at least: role_keywords, target_roles, constraints
    """
    if not PROFILE_CACHE_PATH.exists():
        raise ValueError(
            f"Profile seed not found at {PROFILE_CACHE_PATH}. "
            "Create it before running (see README.md for shape)."
        )
    with PROFILE_CACHE_PATH.open("r", encoding="utf-8") as fh:
        profile = json.load(fh)
    required = {"role_keywords", "target_roles", "constraints"}
    missing = required - set(profile.keys())
    if missing:
        raise ValueError(f"Profile seed missing required keys: {missing}")
    return profile


if __name__ == "__main__":
    print(load_profile_seed())
