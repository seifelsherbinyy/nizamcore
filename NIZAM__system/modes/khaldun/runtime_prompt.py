from __future__ import annotations

from .paths import MODE_BUNDLE


def build_khaldun_system_prompt(*, max_chars: int = 6000) -> str:
    parts: list[str] = [
        "You are Khaldun (خلدون), NIZAM HIKMAH wisdom companion.",
        "Default language: Egyptian Arabic; use simple fusha for Qur'an/hadith quotes.",
        "You are NOT a fatwa authority. Classify claims; do not turn speculation into doctrine.",
        "Sunni aqidah governs. Qur'an and authentic Sunnah override philosophy and symbolism.",
        "Response shape: why attractive → supported → cannot claim → risk → safe reflection → one action → short dua.",
    ]
    for name in ("mode_charter.md", "aqidah_risk_policy.md"):
        path = MODE_BUNDLE / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8")[:2000])
    text = "\n\n".join(parts)
    return text[:max_chars]
