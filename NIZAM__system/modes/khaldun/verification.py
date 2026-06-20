from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .classifier import ClassificationResult, classify_claim
from .paths import MODE_BUNDLE


@dataclass
class VerificationBundle:
    claim_text: str
    claim_source: str | None = None
    domain: str | None = None
    initial_risk_level: str = "unknown"
    hadith: dict[str, Any] = field(default_factory=dict)
    tafsir: dict[str, Any] = field(default_factory=dict)
    science: dict[str, Any] = field(default_factory=dict)
    fiqh: dict[str, Any] = field(default_factory=dict)
    classification: ClassificationResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_text": self.claim_text,
            "claim_source": self.claim_source,
            "domain": self.domain,
            "initial_risk_level": self.initial_risk_level,
            "hadith": self.hadith,
            "tafsir": self.tafsir,
            "science": self.science,
            "fiqh": self.fiqh,
            "classification": self.classification.to_dict() if self.classification else None,
        }


def _load_workflow(name: str) -> dict[str, Any]:
    path = MODE_BUNDLE / f"{name}.workflow.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_hadith(
    *,
    hadith_text: str,
    collection: str | None = None,
    claimed_grade: str | None = None,
    scientific_alignment: bool = False,
) -> dict[str, Any]:
    workflow = _load_workflow("hadith_verification")
    grade = (claimed_grade or "unknown").lower()
    rules = workflow.get("grading_rules", {}).get(grade, {})
    usable = list(rules.get("usable_for", []))
    notes: list[str] = []
    if grade in {"daif", "mawdu", "weak", "unknown"}:
        notes.append("Not usable as evidentiary proof.")
        if scientific_alignment:
            notes.append("Scientific alignment does NOT authenticate weak hadith.")
    return {
        "hadith_text": hadith_text,
        "collection": collection,
        "grading": grade,
        "is_usable_as_evidence": bool(usable and grade not in {"daif", "mawdu", "unknown"}),
        "usable_for": usable,
        "notes_on_weakness_if_any": "; ".join(notes) if notes else None,
    }


def verify_tafsir(
    *,
    ayah_ref: str,
    claimed_meaning: str,
    classical_tafsir_checked: bool = False,
    modern_scientific_reading: bool = False,
) -> dict[str, Any]:
    degree = "possible_reflection"
    if modern_scientific_reading and not classical_tafsir_checked:
        degree = "insufficient_for_definitive_tafsir"
    elif classical_tafsir_checked:
        degree = "classical_support_partial"
    return {
        "relevant_ayahs": ayah_ref,
        "tafsir_summary": claimed_meaning,
        "linguistic_notes": "Modern scientific reading labeled reflection only."
        if modern_scientific_reading
        else None,
        "degree_of_scriptural_support": degree,
    }


def run_research_protocol(
    claim_text: str,
    *,
    claim_source: str | None = None,
    domain: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> VerificationBundle:
    evidence = dict(evidence or {})
    bundle = VerificationBundle(
        claim_text=claim_text,
        claim_source=claim_source,
        domain=domain,
    )

    if evidence.get("hadith_text") or evidence.get("hadith_grade"):
        bundle.hadith = verify_hadith(
            hadith_text=str(evidence.get("hadith_text", "")),
            collection=evidence.get("collection"),
            claimed_grade=evidence.get("hadith_grade"),
            scientific_alignment=bool(evidence.get("scientific_alignment")),
        )
        evidence["hadith_grade"] = bundle.hadith.get("grading")

    if evidence.get("ayah_ref"):
        bundle.tafsir = verify_tafsir(
            ayah_ref=str(evidence["ayah_ref"]),
            claimed_meaning=str(evidence.get("claimed_meaning", claim_text)),
            classical_tafsir_checked=bool(evidence.get("classical_tafsir_checked")),
            modern_scientific_reading=bool(evidence.get("modern_scientific_reading")),
        )

    if evidence.get("scientific_claim"):
        bundle.science = {
            "scientific_consensus_summary": evidence.get("scientific_consensus_summary"),
            "uncertainty_level": evidence.get("uncertainty_level", "medium"),
            "source_quality": evidence.get("source_quality", "unknown"),
        }

    if evidence.get("fiqh_relevant"):
        bundle.fiqh = {
            "aqidah_risk": evidence.get("aqidah_risk", False),
            "requires_scholar_escalation": True,
        }

    bundle.classification = classify_claim(claim_text, evidence)
    return bundle
