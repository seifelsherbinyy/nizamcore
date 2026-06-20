"""Load NIZAM environment files and normalize relay aliases."""
from __future__ import annotations

import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
ROOT_ENV = REPO / ".env"
RELAY_ENV = Path(__file__).resolve().parent / ".env"

ACTIVATION_VARS = (
    "NIZAM_LIVE_MODEL_APPROVED",
    "NIZAM_LIVE_CONNECTORS_APPROVED",
    "NIZAM_DEPLOYMENT_APPROVED",
    "NIZAM_REMOTE_TELEMETRY_APPROVED",
)


def _parse_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    elif value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return key, value


def load_file(path: Path, *, override: bool = False) -> int:
    if not path.exists():
        return 0
    loaded = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


def normalize_aliases() -> None:
    chat_ids = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if chat_ids and not os.environ.get("NIZAM_TELEGRAM_ALLOWED_IDS", "").strip():
        os.environ["NIZAM_TELEGRAM_ALLOWED_IDS"] = chat_ids
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        claude = os.environ.get("CLAUDE_API_KEY", "").strip()
        if claude:
            os.environ["ANTHROPIC_API_KEY"] = claude


def apply_activation_bundle() -> None:
    for name in ACTIVATION_VARS:
        os.environ[name] = "1"
    os.environ.setdefault("RELAY_MODE", "live")
    os.environ.setdefault("NIZAM_REAL_PERSONA_RUNTIME", "1")


def configured(name: str) -> bool:
    value = os.environ.get(name, "").strip()
    if not value:
        return False
    placeholders = {
        "changeme",
        "your-token-here",
        "sk-...",
        "123456789:abcdef-your-botfather-token",
    }
    lowered = value.lower()
    if value in placeholders:
        return False
    if lowered.startswith("your_") or "your-botfather" in lowered:
        return False
    return True


def load_all(*, activate: bool = False) -> dict[str, int | bool]:
    counts = {
        "root_env": load_file(ROOT_ENV),
        "relay_env": load_file(RELAY_ENV, override=True),
    }
    normalize_aliases()
    if activate:
        apply_activation_bundle()
    return {
        **counts,
        "telegram_ready": configured("TELEGRAM_BOT_TOKEN")
        and configured("NIZAM_TELEGRAM_ALLOWED_IDS"),
        "model_ready": configured("OPENAI_API_KEY")
        or configured("ANTHROPIC_API_KEY")
        or configured("DEEPSEEK_API_KEY"),
    }
