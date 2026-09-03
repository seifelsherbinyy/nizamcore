"""test_provenance.py — provenance, freshness and change-detection tests.

Owning contract: NIZAM-CONTRACT-02 v1.0.0
Covers:          C02-T02, C02-T03, C02-T05, D02, E03
Phase:           R1_FIXTURES
"""
import pytest

from adaptive.provenance import (
    AmbiguousIdentityError, ChangeKind, DomainStatus, Freshness,
    ProvenanceError, RECOMMENDED_ARTIFACT_FIELDS, REQUIRED_ARTIFACT_FIELDS,
    detect_change, resolve_by_name, resolve_domains, usable_as_current_truth,
    validate_artifact,
)

# ---------------------------------------------------------------------------
# Independent restatement of NIZAM-CONTRACT-02 `artifact_metadata` (lines
# 86-108 of the contract). These literals are deliberately NOT derived from
# the module under test: a test that parametrises over the very constant it
# is meant to police is tautological, because shrinking or renaming the
# source constant shrinks the test with it and the suite still passes.
# Tamper case T5 proved exactly that defect. Any drift between the contract
# and the implementation must fail here.
# ---------------------------------------------------------------------------
CONTRACT_02_REQUIRED = (
    "artifact_id", "domain", "artifact_type", "source", "authority",
    "created_at", "updated_at", "event_time", "freshness", "privacy_class",
    "confidence", "content_hash", "schema_version",
)
CONTRACT_02_RECOMMENDED = (
    "entities", "topics", "related_artifacts", "supersedes", "superseded_by",
    "retrieval_priority", "temporal_window", "deterministic_source_pointer",
)


def test_required_field_list_matches_contract_02_exactly():
    """Pins the implementation to the contract, not to itself."""
    assert set(REQUIRED_ARTIFACT_FIELDS) == set(CONTRACT_02_REQUIRED)
    assert len(REQUIRED_ARTIFACT_FIELDS) == len(CONTRACT_02_REQUIRED) == 13


def test_recommended_field_list_matches_contract_02_exactly():
    assert set(RECOMMENDED_ARTIFACT_FIELDS) == set(CONTRACT_02_RECOMMENDED)
    assert len(RECOMMENDED_ARTIFACT_FIELDS) == len(CONTRACT_02_RECOMMENDED) == 8


def test_no_required_field_is_also_recommended():
    assert not set(CONTRACT_02_REQUIRED) & set(CONTRACT_02_RECOMMENDED)


def _meta(**over):
    m = {f: "x" for f in CONTRACT_02_REQUIRED}
    m["freshness"] = "fresh"
    m.update(over)
    return m


def test_a_complete_artifact_validates():
    validate_artifact(_meta())


@pytest.mark.parametrize("field_name", CONTRACT_02_REQUIRED)
def test_every_required_provenance_field_is_enforced(field_name):
    m = _meta()
    del m[field_name]
    with pytest.raises(ProvenanceError, match="missing required field"):
        validate_artifact(m)


@pytest.mark.parametrize("field_name", CONTRACT_02_REQUIRED)
def test_an_empty_required_field_is_refused(field_name):
    with pytest.raises(ProvenanceError, match="empty required field"):
        validate_artifact(_meta(**{field_name: "   "}))


def test_an_unknown_freshness_value_is_refused():
    with pytest.raises(ProvenanceError, match="freshness"):
        validate_artifact(_meta(freshness="probably_ok"))


def test_C02_T03_new_modified_time_with_same_hash_is_not_a_semantic_change():
    prev = {"artifact_id": "a", "content_hash": "h1", "updated_at": "2026-09-01"}
    curr = {"artifact_id": "a", "content_hash": "h1", "updated_at": "2026-09-03"}
    assert detect_change(prev, curr) is ChangeKind.UNCHANGED


def test_a_changed_hash_is_a_real_change():
    prev = {"artifact_id": "a", "content_hash": "h1"}
    curr = {"artifact_id": "a", "content_hash": "h2"}
    assert detect_change(prev, curr) is ChangeKind.CHANGED


def test_supersession_is_detected():
    prev = {"artifact_id": "a", "content_hash": "h1"}
    curr = {"artifact_id": "b", "content_hash": "h2", "supersedes": "a"}
    assert detect_change(prev, curr) is ChangeKind.SUPERSEDED


def test_conflicting_authority_on_changed_content_is_a_conflict():
    prev = {"artifact_id": "a", "content_hash": "h1", "authority": "engine"}
    curr = {"artifact_id": "a", "content_hash": "h2", "authority": "narrative"}
    assert detect_change(prev, curr) is ChangeKind.CONFLICT


def test_absent_side_is_added_or_deleted():
    curr = {"artifact_id": "a", "content_hash": "h1"}
    assert detect_change(None, curr) is ChangeKind.ADDED
    assert detect_change(curr, None) is ChangeKind.DELETED_OR_MISSING


def test_comparison_without_a_content_hash_is_refused():
    with pytest.raises(ProvenanceError, match="content_hash"):
        detect_change({"artifact_id": "a"}, {"artifact_id": "a"})


def test_D02_duplicate_display_name_is_never_resolved_by_guessing():
    candidates = [{"name": "MASTER_INDEX.md", "artifact_id": "1"},
                  {"name": "MASTER_INDEX.md", "artifact_id": "2"}]
    with pytest.raises(AmbiguousIdentityError, match="share the display name"):
        resolve_by_name("MASTER_INDEX.md", candidates)


def test_a_unique_display_name_resolves():
    got = resolve_by_name("A.md", [{"name": "A.md", "artifact_id": "1"}])
    assert got["artifact_id"] == "1"


def test_C02_T05_domain_absent_from_bootstrap_is_missing_not_empty():
    res = {d.domain: d for d in resolve_domains({"domain_registry": {}})}
    personal = res["personal"]
    assert personal.status is DomainStatus.MISSING
    assert personal.may_be_treated_as_empty is False


def test_domain_present_without_an_index_location_is_unindexed():
    res = {d.domain: d for d in
           resolve_domains({"domain_registry": {"finance": {}}})}
    assert res["finance"].status is DomainStatus.UNINDEXED
    assert res["finance"].may_be_treated_as_empty is False


def test_domain_with_an_index_location_is_indexed():
    res = {d.domain: d for d in resolve_domains(
        {"domain_registry": {"finance": {"index_location": "FIN_INDEX.json"}}})}
    assert res["finance"].status is DomainStatus.INDEXED


def test_every_required_domain_gets_an_explicit_status():
    res = resolve_domains({})
    assert len(res) == 8
    assert all(r.status in DomainStatus for r in res)


@pytest.mark.parametrize("f,expected", [
    (Freshness.FRESH, True), (Freshness.OBSERVED, True),
    (Freshness.STALE, False), (Freshness.UNKNOWN, False),
    (Freshness.MISSING, False), (Freshness.CONFLICT, False),
])
def test_E03_only_fresh_or_observed_counts_as_current_truth(f, expected):
    assert usable_as_current_truth(f) is expected
