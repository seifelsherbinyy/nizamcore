"""
Configuration loader for the Phase 15 data refresh pipeline.

Provides:
- RefreshConfig dataclass with all externally-configurable parameters
- load_refresh_config() to load and validate configuration from YAML
- Environment-specific overrides support (credentials_path, folder paths)

Design:
- Default config path: HIKMAH__knowledge_index/refresh/config.yaml
- Loads YAML using yaml.safe_load()
- Validates fields (credentials_path exists, timeout > 0, max_files > 0)
- Returns RefreshConfig dataclass instance
- Supports runtime overrides via overrides dict

Error handling:
- FileNotFoundError: config file not found
- FileNotFoundError: credentials file not found (with helpful message)
- ValueError: YAML syntax error or validation failure
"""

import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RefreshConfig:
    """Configuration for the Phase 15 data refresh pipeline."""

    # Google Drive folder paths
    conversation_logs_folder: str
    activity_snapshots_folder: str

    # Credential location
    credentials_path: Path

    # Refresh behavior
    max_files_per_refresh: int
    timeout_seconds: int
    enable_partial_refresh: bool

    # Audit logging
    audit_ledger_path: Path

    # Retry policy
    retry_on_transient_error: bool
    max_retries: int
    backoff_base: int


def load_refresh_config(
    config_file: Optional[Path] = None,
    overrides: Optional[Dict[str, Any]] = None
) -> RefreshConfig:
    """
    Load and validate refresh configuration from YAML.

    Args:
        config_file: Path to config YAML file (defaults to refresh/config.yaml)
        overrides: Optional dict to override config values at runtime

    Returns:
        RefreshConfig instance with validated fields

    Raises:
        FileNotFoundError: If config file not found or credentials file missing
        ValueError: If YAML syntax error or validation fails
    """
    # Determine config file path
    if config_file is None:
        config_file = Path(__file__).parent / "config.yaml"
    else:
        config_file = Path(config_file)

    # Load YAML
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML syntax error in {config_file}: {e}")

    if not config_data or 'data_refresh' not in config_data:
        raise ValueError(f"Configuration file missing 'data_refresh' section: {config_file}")

    config_dict = config_data['data_refresh'].copy()

    # Apply overrides
    if overrides:
        config_dict.update(overrides)

    # Convert string paths to Path objects
    credentials_path = Path(config_dict['credentials_path'])

    # Validate credentials file exists
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found at {credentials_path}. "
            f"Set credentials_path in config.yaml or via overrides dict."
        )

    # Validate integer fields
    max_files = config_dict.get('max_files_per_refresh', 100)
    if not isinstance(max_files, int) or max_files <= 0:
        raise ValueError(f"max_files_per_refresh must be a positive integer, got: {max_files}")

    timeout = config_dict.get('timeout_seconds', 30)
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValueError(f"timeout_seconds must be a positive integer, got: {timeout}")

    max_retries = config_dict.get('max_retries', 0)
    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError(f"max_retries must be a non-negative integer, got: {max_retries}")

    backoff_base = config_dict.get('backoff_base', 2)
    if not isinstance(backoff_base, int) or backoff_base < 1:
        raise ValueError(f"backoff_base must be an integer >= 1, got: {backoff_base}")

    # Create RefreshConfig instance
    return RefreshConfig(
        conversation_logs_folder=config_dict.get('conversation_logs_folder', 'YAWMIYAT/sessions'),
        activity_snapshots_folder=config_dict.get('activity_snapshots_folder', 'YAWMIYAT/daily_snapshots'),
        credentials_path=credentials_path,
        max_files_per_refresh=max_files,
        timeout_seconds=timeout,
        enable_partial_refresh=config_dict.get('enable_partial_refresh', False),
        audit_ledger_path=Path(config_dict.get('audit_ledger_path', 'HIKMAH__knowledge_index/REFRESH_AUDIT_LEDGER.jsonl')),
        retry_on_transient_error=config_dict.get('retry_on_transient_error', False),
        max_retries=max_retries,
        backoff_base=backoff_base,
    )


__all__ = [
    'RefreshConfig',
    'load_refresh_config',
]
