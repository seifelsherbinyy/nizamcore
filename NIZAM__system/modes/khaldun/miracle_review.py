from __future__ import annotations

import json
from typing import Any

from .paths import MODE_BUNDLE


def _load_ladder() -> dict[str, Any]:
    path = MODE_BUNDLE / "miracle_claim_assessment_ladder.json"
    return json.loads(path.read_text(encoding="utf-8"))


def grade_miracle_claim(
    *,
    text_stable: bool,
    meaning_stable: bool,
    scientific_stable: bool,
    non_forced: bool,
    aqidah_risk: bool = False,
) -> str:
    if aqidah_risk:
        return "rejected"
    ladder = _load_ladder()
    dims = {
        "text_stability": text_stable,
        "meaning_stability": meaning_stable,
        "scientific_stability": scientific_stable,
        "non_forced_interpretation": non_forced,
    }
    for grade in ("strong_sign", "moderate_reflection"):
        required = ladder["grades"][grade]["requires"]
        if all(dims.get(r.replace("_stability", "_stability"), False) or dims.get(r, False) for r in required):
            if grade == "strong_sign" and all(
                dims[k] for k in ("text_stability", "meaning_stability", "scientific_stability", "non_forced_interpretation")
            ):
                return grade
            if grade == "moderate_reflection":
                return grade
    if not text_stable or not non_forced:
        return "rejected"
    return "weak_speculative"


def assess_miracle_claim(evidence: dict[str, Any]) -> dict[str, Any]:
    grade = grade_miracle_claim(
        text_stable=bool(evidence.get("text_stable", False)),
        meaning_stable=bool(evidence.get("meaning_stable", False)),
        scientific_stable=bool(evidence.get("scientific_stable", False)),
        non_forced=bool(evidence.get("non_forced", False)),
        aqidah_risk=bool(evidence.get("aqidah_risk", False)),
    )
    ladder = _load_ladder()
    allowed = ladder["grades"].get(grade, {}).get("allowed_output", "G_speculative_unverified")
    return {
        "miracle_ladder_grade": grade,
        "allowed_classification": allowed,
        "confidence": "high" if grade == "rejected" else "low" if grade == "weak_speculative" else "medium",
    }
