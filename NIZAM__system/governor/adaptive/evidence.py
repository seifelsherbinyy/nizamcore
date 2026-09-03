"""evidence.py — evidence labelling and the no-imputation invariant.

Owning contract: NIZAM-CONTRACT-01 (Constitution and Governance) v1.0.0
Satisfies:       C01-T04, E01, E02, E03, E04
Phase:           R1_FIXTURES

DOCTRINE (Contract 01 evidence_labels, T04_EVIDENCE_BEFORE_INTERPRETATION):
  * Four labels only: FACT, INFERENCE, ASSUMPTION, MISSING.
  * No inference, hypothesis, remembered statement or model-generated
    interpretation may be silently promoted to FACT.
  * Unknown values stay MISSING. Never imputed to complete a record.
  * Conflicting sources stay conflicting until resolved by authority order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Label(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    ASSUMPTION = "ASSUMPTION"
    MISSING = "MISSING"


class EvidenceError(Exception):
    """Raised when an evidence invariant would be violated."""


# Authority order, highest first (Contract 01 authority_order.highest_to_lowest).
AUTHORITY_ORDER = (
    "active_safety_contract",
    "active_privacy_contract",
    "this_constitution",
    "owning_domain_contract",
    "deterministic_engine_output",
    "canonical_source_artifact",
    "promoted_learning",
    "current_hypothesis",
    "model_inference",
)

# Only these authorities may originate a FACT.
FACT_CAPABLE_AUTHORITIES = frozenset(
    {
        "active_safety_contract",
        "active_privacy_contract",
        "this_constitution",
        "owning_domain_contract",
        "deterministic_engine_output",
        "canonical_source_artifact",
    }
)


def authority_rank(authority: str) -> int:
    """Lower number == higher authority. Unknown authorities rank lowest."""
    try:
        return AUTHORITY_ORDER.index(authority)
    except ValueError:
        return len(AUTHORITY_ORDER)


@dataclass(frozen=True)
class Evidence:
    """A single labelled observation with its provenance.

    MISSING carries value=None always. Constructing a MISSING with a non-None
    value is imputation and is refused at construction time.
    """

    label: Label
    value: Any
    source: str
    authority: str
    as_of: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, Label):
            raise EvidenceError(f"label must be a Label, got {self.label!r}")
        if not self.source:
            raise EvidenceError("evidence requires a source pointer")
        if self.label is Label.MISSING and self.value is not None:
            raise EvidenceError(
                "MISSING evidence must carry value=None; assigning a value is "
                "imputation (Contract 01 T04)"
            )
        if self.label is Label.FACT and self.authority not in FACT_CAPABLE_AUTHORITIES:
            raise EvidenceError(
                f"authority {self.authority!r} may not originate a FACT; "
                "model inference and hypotheses cannot be FACT (Contract 01 T08)"
            )

    @property
    def is_known(self) -> bool:
        return self.label is not Label.MISSING


def fact(value: Any, source: str, authority: str = "deterministic_engine_output",
         as_of: str | None = None) -> Evidence:
    return Evidence(Label.FACT, value, source, authority, as_of)


def inference(value: Any, source: str, as_of: str | None = None,
              note: str | None = None) -> Evidence:
    return Evidence(Label.INFERENCE, value, source, "model_inference", as_of, note)


def assumption(value: Any, source: str, as_of: str | None = None,
               note: str | None = None) -> Evidence:
    return Evidence(Label.ASSUMPTION, value, source, "model_inference", as_of, note)


def missing(source: str, note: str | None = None) -> Evidence:
    return Evidence(Label.MISSING, None, source, "model_inference", None, note)


def promote_to_fact(ev: Evidence, deterministic_source: str, authority: str) -> Evidence:
    """Promote an INFERENCE/ASSUMPTION to FACT, but only on real authority.

    Refuses silent promotion (Contract 01 evidence_labels.rule). A MISSING value
    can never be promoted, because there is nothing to promote.
    """
    if ev.label is Label.MISSING:
        raise EvidenceError("MISSING cannot be promoted to FACT; it has no value")
    if authority not in FACT_CAPABLE_AUTHORITIES:
        raise EvidenceError(
            f"cannot promote to FACT on authority {authority!r} (Contract 01 T08)"
        )
    return Evidence(Label.FACT, ev.value, deterministic_source, authority, ev.as_of,
                    note=f"promoted from {ev.label.value}")


@dataclass(frozen=True)
class Conflict:
    """Two sources disagree. Both are preserved; neither is merged away."""

    left: Evidence
    right: Evidence
    field_name: str

    @property
    def winner(self) -> Evidence:
        """The higher-authority side wins for *use*, but both stay recorded."""
        return self.left if authority_rank(self.left.authority) <= authority_rank(
            self.right.authority
        ) else self.right


def resolve_conflict(left: Evidence, right: Evidence, field_name: str) -> Conflict:
    """Never silently merge. Always return a Conflict that keeps both sides.

    E02: a journal inference conflicting with a biometric fact surfaces the
    contradiction rather than overwriting one side.
    C03-T04 / F01: a model-recalled figure loses to a deterministic engine.
    """
    return Conflict(left=left, right=right, field_name=field_name)
