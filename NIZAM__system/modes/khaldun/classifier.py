from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import MODE_BUNDLE

AQIDAH_RISK_PATTERNS = (
    re.compile(r"(?i)\ballah\s+(?:is\s+)?(?:in|inside|within)\s+(?:us|me|you|creation)\b"),
    re.compile(r"(?i)\b(?:hulul|ittihad|pantheism|أ(?:نا\s+)?(?:ال)?(?:له|الحق))\b"),
    re.compile(r"(?i)\b(?:law\s+of\s+attraction\s+(?:always|guarantees))\b"),
    re.compile(r"(?:الله\s+(?:في|داخل)\s+(?:نا|قلوبنا|الخلق))"),
)

SYMBOLIC_KEYWORDS = re.compile(
    r"(?i)\b(?:chakra|chakras|kundalini|ancient\s+egypt|pharaoh\s+soul|energy\s+body)\b"
)
MIRACLE_KEYWORDS = re.compile(
    r"(?i)\b(?:scientific\s+miracle|miracle\s+of\s+quran|معجزة\s+علمية|يثبت\s+القرآن)\b"
)


@dataclass(frozen=True)
class ClassificationResult:
    primary_label: str
    secondary_labels: tuple[str, ...]
    confidence: str
    explanation: str
    allowed_language: tuple[str, ...]
    requires_scholar_escalation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_label": self.primary_label,
            "secondary_labels": list(self.secondary_labels),
            "confidence": self.confidence,
            "explanation": self.explanation,
            "allowed_language": list(self.allowed_language),
            "requires_scholar_escalation": self.requires_scholar_escalation,
        }


def _load_language_policy() -> dict[str, Any]:
    path = MODE_BUNDLE / "claim_language_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _rules_for(label: str, policy: dict[str, Any]) -> dict[str, Any]:
    return policy.get("rules", {}).get(label, {})


def classify_claim(
    claim_text: str,
    evidence_bundle: dict[str, Any] | None = None,
) -> ClassificationResult:
    """Rule-based claim classifier (deterministic pre-check)."""
    evidence = evidence_bundle or {}
    text = claim_text.strip()
    lower = text.lower()
    policy = _load_language_policy()
    secondary: list[str] = []

    for pat in AQIDAH_RISK_PATTERNS:
        if pat.search(text):
            rules = _rules_for("H_reject_aqidah_risk", policy)
            return ClassificationResult(
                primary_label="H_reject_aqidah_risk",
                secondary_labels=tuple(secondary),
                confidence="high",
                explanation="Claim matches aqidah-risk patterns.",
                allowed_language=tuple(
                    [rules.get("required_tone", "compassionate_correction")]
                ),
                requires_scholar_escalation=bool(evidence.get("fiqh_relevant")),
            )

    if evidence.get("hadith_grade") in {"daif", "mawdu", "weak", "unknown"}:
        if evidence.get("scientific_alignment"):
            return ClassificationResult(
                primary_label="G_speculative_unverified",
                secondary_labels=tuple(secondary),
                confidence="high",
                explanation="Weak hadith cannot be authenticated by scientific alignment.",
                allowed_language=("احتمال", "تأمل"),
            )

    if SYMBOLIC_KEYWORDS.search(text):
        rules = _rules_for("F_symbolic_comparative", policy)
        return ClassificationResult(
            primary_label="F_symbolic_comparative",
            secondary_labels=tuple(secondary),
            confidence="medium",
            explanation="Comparative or symbolic framing required.",
            allowed_language=tuple(rules.get("required_phrases_ar", ["تشابه رمزي"])),
        )

    if MIRACLE_KEYWORDS.search(text) or evidence.get("miracle_claim"):
        ladder = evidence.get("miracle_ladder_grade")
        if ladder in {"strong_sign", "moderate_reflection"}:
            secondary.append("C_linguistic_or_tafsir_possibility")
            if evidence.get("scientific_consensus"):
                secondary.append("B_scientifically_supported")
            return ClassificationResult(
                primary_label="C_linguistic_or_tafsir_possibility",
                secondary_labels=tuple(dict.fromkeys(secondary)),
                confidence="low" if ladder == "moderate_reflection" else "medium",
                explanation="Miracle-adjacent claim requires tafsir caution.",
                allowed_language=("احتمال", "يحتمل في التفسير", "تأمل"),
            )
        return ClassificationResult(
            primary_label="G_speculative_unverified",
            secondary_labels=tuple(secondary),
            confidence="low",
            explanation="Miracle claim lacks ladder verification.",
            allowed_language=("احتمال", "تأمل", "فرضية"),
        )

    if evidence.get("quran_or_sunnah") and evidence.get("authentic_hadith"):
        rules = _rules_for("A_shari_established", policy)
        return ClassificationResult(
            primary_label="A_shari_established",
            secondary_labels=tuple(secondary),
            confidence="high",
            explanation="Supported by cited Qur'an or authentic Sunnah.",
            allowed_language=tuple(rules.get("allowed_phrases_ar", ["يدل عليه"])),
        )

    if evidence.get("scientific_consensus") and not evidence.get("miracle_claim"):
        rules = _rules_for("B_scientifically_supported", policy)
        return ClassificationResult(
            primary_label="B_scientifically_supported",
            secondary_labels=tuple(secondary),
            confidence="medium",
            explanation="Supported by scientific consensus; reflection only.",
            allowed_language=tuple(rules.get("allowed_phrases_ar", ["يدعمه العلم الحالي"])),
        )

    if evidence.get("tasawwuf_topic"):
        return ClassificationResult(
            primary_label="E_sunni_tasawwuf_tazkiyah",
            secondary_labels=tuple(secondary),
            confidence="medium",
            explanation="Sober tazkiyah framing.",
            allowed_language=("تزكية", "محاسبة", "مراقبة"),
        )

    if evidence.get("philosophy_topic"):
        return ClassificationResult(
            primary_label="D_philosophical_reflection",
            secondary_labels=tuple(secondary),
            confidence="low",
            explanation="Philosophical reflection; not binding doctrine.",
            allowed_language=("تأمل", "reflection"),
        )

    if "ibn arabi" in lower or "ibn al-arabi" in lower:
        secondary.append("D_philosophical_reflection")
        return ClassificationResult(
            primary_label="G_speculative_unverified",
            secondary_labels=tuple(secondary),
            confidence="low",
            explanation="Contested metaphysical material — reflection only.",
            allowed_language=("تأمل", "محل خلاف", "احتمال"),
        )

    return ClassificationResult(
        primary_label="G_speculative_unverified",
        secondary_labels=tuple(secondary),
        confidence="low",
        explanation="Insufficient evidence; treat as hypothesis.",
        allowed_language=("احتمال", "تأمل"),
    )


def map_reliability_to_knowledge_claim(label: str) -> str:
    mapping = {
        "A_shari_established": "primary_religious",
        "B_scientifically_supported": "peer_reviewed_science",
        "C_linguistic_or_tafsir_possibility": "classical_reference",
        "D_philosophical_reflection": "speculative",
        "E_sunni_tasawwuf_tazkiyah": "classical_reference",
        "F_symbolic_comparative": "speculative",
        "G_speculative_unverified": "speculative",
        "H_reject_aqidah_risk": "rejected",
    }
    return mapping.get(label, "speculative")
