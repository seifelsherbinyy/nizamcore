"""provenance.py — artifact provenance, freshness and incremental change detection.

Owning contract: NIZAM-CONTRACT-02 (Knowledge Acquisition and Retrieval) v1.0.0
Satisfies:       C02-T02, C02-T03, C02-T05, D01, D02, E03
Phase:           R1_FIXTURES

DOCTRINE (Contract 02):
  * Retrieval starts at BOOTSTRAP -> domain index -> artifact. Blind recursive
    crawling is not a production retrieval path.
  * "Modified time alone is not proof of semantic freshness."
  * A domain absent from BOOTSTRAP is UNINDEXED/MISSING, never "empty".
  * A duplicate canonical display name is never resolved by guessing.
  * strict_local_maximum content never leaves for cloud model context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Contract 02 artifact_metadata.required — all thirteen are mandatory.
REQUIRED_ARTIFACT_FIELDS = (
    "artifact_id", "domain", "artifact_type", "source", "authority",
    "created_at", "updated_at", "event_time", "freshness", "privacy_class",
    "confidence", "content_hash", "schema_version",
)

RECOMMENDED_ARTIFACT_FIELDS = (
    "entities", "topics", "related_artifacts", "supersedes", "superseded_by",
    "retrieval_priority", "temporal_window", "deterministic_source_pointer",
)

# Contract 02 required_domains
REQUIRED_DOMAINS = (
    "personal", "mental_behavioral", "health_fitness", "finance",
    "work_projects", "calendar_behavior", "learning", "system",
)


class Freshness(str, Enum):
    FRESH = "fresh"
    OBSERVED = "observed"
    STALE = "stale"
    UNKNOWN = "unknown"
    MISSING = "missing"
    CONFLICT = "conflict"


class DomainStatus(str, Enum):
    INDEXED = "indexed"
    UNINDEXED = "unindexed"
    MISSING = "missing"


class ChangeKind(str, Enum):
    ADDED = "added"
    CHANGED = "changed"
    SUPERSEDED = "superseded"
    DELETED_OR_MISSING = "deleted_or_missing"
    UNCHANGED = "unchanged"
    CONFLICT = "conflict"


class ProvenanceError(Exception):
    """Raised when required provenance is absent or malformed."""


class AmbiguousIdentityError(ProvenanceError):
    """Two artifacts share a display name; identity cannot be guessed."""


def validate_artifact(meta: dict) -> None:
    """Fail closed on any missing or empty required provenance field."""
    absent = [f for f in REQUIRED_ARTIFACT_FIELDS if f not in meta]
    if absent:
        raise ProvenanceError(
            "artifact metadata missing required field(s): " + ", ".join(absent)
        )
    empty = [f for f in REQUIRED_ARTIFACT_FIELDS
             if meta[f] is None or (isinstance(meta[f], str) and not meta[f].strip())]
    if empty:
        raise ProvenanceError(
            "artifact metadata has empty required field(s): " + ", ".join(empty)
        )
    try:
        Freshness(meta["freshness"])
    except ValueError:
        raise ProvenanceError(
            f"freshness {meta['freshness']!r} is not one of "
            + ", ".join(f.value for f in Freshness)
        ) from None


def usable_as_current_truth(freshness: str | Freshness) -> bool:
    """Only fresh/observed may be treated as current state.

    stale  -> historical evidence only, must be labelled (Contract 02)
    unknown-> must not be promoted to current state
    """
    f = Freshness(freshness) if not isinstance(freshness, Freshness) else freshness
    return f in (Freshness.FRESH, Freshness.OBSERVED)


def detect_change(previous: dict | None, current: dict | None) -> ChangeKind:
    """Incremental change detection with content hash as the trust anchor.

    A new modified time with an unchanged content hash is NOT a semantic change
    (Contract 02 incremental_change_detection.rule, acceptance C02-T03).
    """
    if previous is None and current is None:
        raise ProvenanceError("detect_change requires at least one side")
    if previous is None:
        return ChangeKind.ADDED
    if current is None:
        return ChangeKind.DELETED_OR_MISSING

    if current.get("supersedes") == previous.get("artifact_id") and \
            current.get("artifact_id") != previous.get("artifact_id"):
        return ChangeKind.SUPERSEDED

    prev_hash = previous.get("content_hash")
    curr_hash = current.get("content_hash")
    if not prev_hash or not curr_hash:
        raise ProvenanceError("content_hash is required on both sides to compare")

    if prev_hash == curr_hash:
        # Modified time may well differ. That alone proves nothing.
        return ChangeKind.UNCHANGED

    prev_auth = previous.get("authority")
    curr_auth = current.get("authority")
    if prev_auth and curr_auth and prev_auth != curr_auth:
        return ChangeKind.CONFLICT

    return ChangeKind.CHANGED


def resolve_by_name(display_name: str, candidates: list[dict]) -> dict:
    """Resolve a display name to exactly one artifact, or refuse.

    D02 / C02-T02: two files sharing a display name must never be resolved by a
    name-based guess. Callers must supply an id or an authority discriminator.
    """
    matches = [c for c in candidates if c.get("name") == display_name]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ProvenanceError(f"no artifact named {display_name!r}")
    raise AmbiguousIdentityError(
        f"{len(matches)} artifacts share the display name {display_name!r}; "
        "resolve by artifact_id or authority, never by name (Contract 02 "
        "failure_modes.duplicate_canonical_name)"
    )


@dataclass(frozen=True)
class DomainResolution:
    domain: str
    status: DomainStatus
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def may_be_treated_as_empty(self) -> bool:
        """Only an indexed domain that really holds nothing is empty."""
        return self.status is DomainStatus.INDEXED


def resolve_domains(bootstrap: dict) -> tuple[DomainResolution, ...]:
    """Every required domain gets an explicit status.

    C02-T05: a domain absent from BOOTSTRAP is UNINDEXED/MISSING, and is never
    silently treated as complete or empty.
    """
    registry = bootstrap.get("domain_registry") or {}
    out: list[DomainResolution] = []
    for domain in REQUIRED_DOMAINS:
        if domain not in registry:
            out.append(DomainResolution(
                domain, DomainStatus.MISSING,
                ("absent from BOOTSTRAP.domain_registry; recorded MISSING, not empty",),
            ))
            continue
        pointer = registry[domain] or {}
        if not pointer.get("index_location"):
            out.append(DomainResolution(
                domain, DomainStatus.UNINDEXED,
                ("present in BOOTSTRAP but carries no index_location",),
            ))
            continue
        out.append(DomainResolution(domain, DomainStatus.INDEXED,
                                    ("resolved through BOOTSTRAP domain pointer",)))
    return tuple(out)
