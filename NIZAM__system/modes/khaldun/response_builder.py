from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import MODE_BUNDLE


TEMPLATES = {
    "deep_research": "template_deep_research.md",
    "debate": "template_debate_mode.md",
    "reminder": "template_islamic_reminder.md",
    "khutbah": "template_khutbah.md",
    "dua": "template_dua.md",
}


def load_template(name: str) -> str:
    filename = TEMPLATES.get(name)
    if not filename:
        raise KeyError(f"Unknown template: {name}")
    path = MODE_BUNDLE / "templates" / filename
    return path.read_text(encoding="utf-8")


def fill_template(name: str, fields: dict[str, str]) -> str:
    text = load_template(name)
    for key, value in fields.items():
        text = text.replace("{" + key + "}", value)
    return text


def default_response_shape(fields: dict[str, str]) -> str:
    """Default Khaldun response shape from spec."""
    return "\n\n".join(
        [
            f"**لماذا جذاب:** {fields.get('why_attractive', '')}",
            f"**يدعمه:** {fields.get('supported_points', '')}",
            f"**لا يُ claimed:** {fields.get('uncertain_points', '')}",
            f"**خطر:** {fields.get('aqidah_or_science_risk', '')}",
            f"**تأمل:** {fields.get('safe_spiritual_lesson', '')}",
            f"**خطوة:** {fields.get('seif_action', '')}",
            f"**دعاء:** {fields.get('short_dua', '')}",
        ]
    )
