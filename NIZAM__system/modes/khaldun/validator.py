from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from NIZAM__system.companion import reminders

from .classifier import classify_claim
from .paths import MODE_BUNDLE

SHAME_PATTERNS = (
    re.compile(r"(?i)\b(?:spiritual grade|iman score|performance spirituality)\b"),
    re.compile(r"(?:لا\s+إيمان|فاشل\s+روحياً)"),
)

TAWAKKUL_CONFLATION = re.compile(
    r"(?:توك[ّ]?ل\s*و\s*توكل|tawakkul\s+and\s+tawakul\s+(?:are\s+)?the\s+same|same\s+thing)",
    re.I,
)

SYMBOLIC_REQUIRED = re.compile(r"(?:تشابه\s+رمزي|مقارنة\s+تاريخية)", re.I)


def _load_language_policy() -> dict[str, Any]:
    return json.loads((MODE_BUNDLE / "claim_language_policy.json").read_text(encoding="utf-8"))


def validate_khaldun_response(
    message: str,
    *,
    source_ids: tuple[str, ...] = (),
    evidence: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Validate Khaldun output before staging delivery."""
    policy = _load_language_policy()
    for pattern in policy.get("global_forbidden", {}).get("fatwa_patterns", []):
        if re.search(pattern, message, re.I):
            return False, "fatwa_language"

    for pat in SHAME_PATTERNS:
        if pat.search(message):
            return False, "shame_language"

    if TAWAKKUL_CONFLATION.search(message):
        return False, "tawakkul_tawakul_conflated"

    classification = classify_claim(message, evidence)
    if classification.primary_label == "H_reject_aqidah_risk":
        safe_markers = ("قريب", "علم", "near", "knowledge", "ليس داخل")
        if not any(marker in message for marker in safe_markers):
            return False, "aqidah_risk_uncorrected"

    if classification.primary_label == "F_symbolic_comparative":
        if not SYMBOLIC_REQUIRED.search(message):
            return False, "symbolic_framing_missing"

    if source_ids:
        ok, reason = reminders.validate_sourced_reminder(message, source_ids)
        if not ok:
            return False, reason

    miracle_patterns = policy.get("global_forbidden", {}).get("miracle_without_ladder", [])
    for pattern in miracle_patterns:
        if pattern.lower() in message.lower():
            if not evidence or evidence.get("miracle_ladder_grade") not in {
                "strong_sign",
                "moderate_reflection",
            }:
                return False, "miracle_overclaim"

    return True, "valid"
