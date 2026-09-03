# Contract: NIZAM-CONTRACT-01 required_runtime_receipt | Phase: R3_THABAT
"""Acceptance tests for THABAT run records.

Owning contracts: NIZAM Contract 01 `required_runtime_receipt`
                  NIZAM Contract 04 `execution_manifest`, C04-T05
Phase:            R3_THABAT

The two 13-field lists below are TRANSCRIBED from the contract text, not
imported from the module, so a field quietly dropped from the module cannot
also disappear from its own test.
"""
import inspect
import json
import pathlib

import pytest

from scheduler import run_record as rr
from scheduler.run_record import (
    PRIVACY_CLASSES,
    ActionManifest,
    ActionOutcome,
    AutonomyClass,
    ReceiptError,
    ReceiptStatus,
    Verification,
    VerificationMethod,
    assemble_receipt,
    build_run_id,
    cairo_date_of,
    manifest_to_dict,
    receipt_to_dict,
)

# Contract 01 `required_runtime_receipt`, transcribed.
CONTRACT_01_RECEIPT_FIELDS = [
    "run_id",
    "timestamp",
    "contract_versions",
    "sukoon_state",
    "objective_recovery_percent",
    "himayah_classification",
    "modules_invoked",
    "actions_attempted",
    "actions_verified",
    "blocked_actions",
    "evidence_summary",
    "open_loops",
    "next_action",
]

# Contract 04 `execution_manifest.required_fields`, transcribed.
CONTRACT_04_MANIFEST_FIELDS = [
    "run_id",
    "action_id",
    "action",
    "owning_contract",
    "reason",
    "evidence",
    "affected_scope",
    "risk",
    "rollback_or_reversal",
    "verification",
    "privacy_class",
    "authorization_basis",
    "expected_outcome",
]

RUN = "2026-09-03/primary_1200"
STAMP = "2026-09-03T09:00:04Z"
VERSIONS = {"NIZAM-CONTRACT-01": "1.0.0", "NIZAM-DAILY-ORCHESTRATION-04": "1.0.0"}

SHA_A = "a" * 64
SHA_B = "b" * 64


def confirmed_readback(expected=SHA_A, observed=SHA_A):
    return Verification(
        method=VerificationMethod.DRIVE_READBACK_SHA256,
        expected=expected,
        observed=observed,
        detail="readback compared byte digest of the landed artifact",
    )


def read_only_verification():
    return Verification(
        method=VerificationMethod.NOT_APPLICABLE_READ_ONLY,
        expected=None,
        observed=None,
        detail="read-only retrieval leaves no external effect to read back",
    )


def manifest(
    action_id="write_bootstrap_index",
    outcome=ActionOutcome.VERIFIED,
    verification=None,
    run_id=RUN,
    basis=AutonomyClass.CLASS_B,
):
    return ActionManifest(
        run_id=run_id,
        action_id=action_id,
        action="upsert the retrieval entrypoint artifact",
        owning_contract="NIZAM-DAILY-ORCHESTRATION-04 drive_policy",
        reason="the entrypoint is the first element of the retrieval order",
        evidence=("source counts observed at RUN_T0", "prior digest recorded"),
        affected_scope="DRIVE_ROOT/ENTRYPOINT_ARTIFACT",
        risk="low: single artifact, prior digest captured for reversal",
        rollback_or_reversal="re-upsert the prior digest captured before write",
        verification=verification if verification is not None else confirmed_readback(),
        privacy_class="strict_local",
        authorization_basis=basis,
        expected_outcome="entrypoint reflects today's observed source states",
        outcome=outcome,
    )


def receipt(manifests, open_loops=(), **kw):
    params = dict(
        run_id=RUN,
        timestamp=STAMP,
        contract_versions=VERSIONS,
        sukoon_state="yellow",
        objective_recovery_percent=58,
        himayah_classification="strict_local",
        modules_invoked=("cairo_gate", "run_record"),
        manifests=manifests,
        evidence_summary=("1 artifact written and read back",),
        open_loops=open_loops,
        next_action="reconcile at 13:00 Africa/Cairo",
    )
    params.update(kw)
    return assemble_receipt(**params)


# --------------------------------------------------------------------------
# 1. Both contracts' required fields are present, under their contract names
# --------------------------------------------------------------------------

def test_R3_T01_receipt_carries_every_contract_01_required_field():
    payload = receipt_to_dict(receipt([manifest()]), [manifest()])
    for name in CONTRACT_01_RECEIPT_FIELDS:
        assert name in payload, f"Contract 01 requires {name}"


def test_R3_T02_manifest_carries_every_contract_04_required_field():
    payload = manifest_to_dict(manifest())
    for name in CONTRACT_04_MANIFEST_FIELDS:
        assert name in payload, f"Contract 04 requires {name}"


def test_R3_T03_the_modules_own_field_lists_match_the_transcribed_contracts():
    """The module publishes the lists for its own preflight. If they drift from
    the contract text this test is the only thing that notices."""
    assert list(rr.REQUIRED_RECEIPT_FIELDS) == CONTRACT_01_RECEIPT_FIELDS
    assert list(rr.REQUIRED_MANIFEST_FIELDS) == CONTRACT_04_MANIFEST_FIELDS


def test_R3_T04_run_id_is_the_only_field_shared_by_both_grains():
    """The non-duplication design: everything else lives at exactly one grain."""
    shared = set(CONTRACT_01_RECEIPT_FIELDS) & set(CONTRACT_04_MANIFEST_FIELDS)
    assert shared == {"run_id"}


def test_R3_T05_manifests_nest_under_the_receipt_rather_than_flatten():
    payload = receipt_to_dict(receipt([manifest()]), [manifest()])
    assert isinstance(payload["execution_manifest"], list)
    assert payload["execution_manifest"][0]["action_id"] == "write_bootstrap_index"


# --------------------------------------------------------------------------
# 2. Run identity is derived so a rerun collides on purpose
# --------------------------------------------------------------------------

def test_R3_T06_the_same_cairo_day_and_slot_yield_the_same_run_id():
    """Duplicate detection is impossible with a random or per-second id."""
    assert build_run_id("2026-09-03", "primary_1200") == RUN
    assert build_run_id("2026-09-03", "primary_1200") == build_run_id(
        "2026-09-03", "primary_1200"
    )


def test_R3_T07_run_id_exposes_the_cairo_day_for_the_run_once_guard():
    assert cairo_date_of(RUN) == "2026-09-03"
    assert receipt([manifest()]).cairo_date == "2026-09-03"


@pytest.mark.parametrize(
    "bad_date", ["2026-9-3", "03-09-2026", "2026/09/03", "", "today"]
)
def test_R3_T08_a_malformed_cairo_date_is_refused(bad_date):
    with pytest.raises(ReceiptError):
        build_run_id(bad_date, "primary_1200")


@pytest.mark.parametrize("bad_slot", ["Primary-1200", "P", "primary 1200", ""])
def test_R3_T09_a_malformed_slot_is_refused(bad_slot):
    with pytest.raises(ReceiptError):
        build_run_id("2026-09-03", bad_slot)


def test_R3_T10_a_manifest_from_another_run_cannot_be_counted_in_this_one():
    stray = manifest(run_id="2026-09-03/reconcile_1300")
    with pytest.raises(ReceiptError, match="belongs to"):
        receipt([stray])


def test_R3_T11_a_duplicate_action_id_is_refused():
    with pytest.raises(ReceiptError, match="duplicate action_id"):
        receipt([manifest(), manifest()])


# --------------------------------------------------------------------------
# 3. C04-T05: a write that did not read back is never OK
# --------------------------------------------------------------------------

def test_R3_T12_C04_T05_write_succeeds_but_readback_fails_is_never_ok():
    """Contract 04 C04-T05, the whole point of the status field."""
    unread = manifest(
        outcome=ActionOutcome.AWAITING_READBACK,
        verification=Verification(
            method=VerificationMethod.DRIVE_READBACK_SHA256,
            expected=SHA_A,
            observed=None,
            detail="write call returned success; readback returned nothing",
        ),
    )
    result = receipt([unread], open_loops=("entrypoint write unconfirmed",))
    assert result.status is ReceiptStatus.SYNC_PENDING
    assert result.status is not ReceiptStatus.OK
    assert result.actions_verified == ()
    assert result.actions_attempted == ("write_bootstrap_index",)


def test_R3_T13_a_digest_mismatch_is_not_a_confirmed_readback():
    """The readback landed, but on different bytes. That is not verification."""
    mismatch = confirmed_readback(expected=SHA_A, observed=SHA_B)
    assert mismatch.confirmed is False
    with pytest.raises(ReceiptError, match="not.*confirmed"):
        manifest(outcome=ActionOutcome.VERIFIED, verification=mismatch)


def test_R3_T14_a_returned_success_alone_cannot_be_recorded_as_verified():
    hollow = Verification(
        method=VerificationMethod.DRIVE_READBACK_SHA256,
        expected=None,
        observed=None,
        detail="API returned 200",
    )
    assert hollow.confirmed is False
    with pytest.raises(ReceiptError):
        manifest(outcome=ActionOutcome.VERIFIED, verification=hollow)


def test_R3_T15_a_failed_action_forces_a_failed_receipt():
    broken = manifest(
        outcome=ActionOutcome.FAILED,
        verification=Verification(
            method=VerificationMethod.DRIVE_READBACK_SHA256,
            expected=SHA_A, observed=None, detail="write raised",
        ),
    )
    result = receipt([broken], open_loops=("entrypoint write failed",))
    assert result.status is ReceiptStatus.FAILED


def test_R3_T16_a_failure_outranks_a_pending_readback():
    broken = manifest(
        action_id="write_a",
        outcome=ActionOutcome.FAILED,
        verification=Verification(
            method=VerificationMethod.DRIVE_READBACK_SHA256,
            expected=SHA_A, observed=None, detail="write raised",
        ),
    )
    pending = manifest(
        action_id="write_b",
        outcome=ActionOutcome.AWAITING_READBACK,
        verification=Verification(
            method=VerificationMethod.DRIVE_READBACK_SHA256,
            expected=SHA_B, observed=None, detail="not yet read back",
        ),
    )
    result = receipt([broken, pending], open_loops=("two writes unresolved",))
    assert result.status is ReceiptStatus.FAILED


def test_R3_T17_a_clean_run_with_a_confirmed_readback_is_ok():
    result = receipt([manifest()])
    assert result.status is ReceiptStatus.OK
    assert result.actions_verified == ("write_bootstrap_index",)


def test_R3_T18_a_read_only_action_needs_no_readback():
    reader = manifest(
        action_id="read_whoop_recovery",
        verification=read_only_verification(),
    )
    assert receipt([reader]).status is ReceiptStatus.OK


# --------------------------------------------------------------------------
# 4. A failure may not be closed silently
# --------------------------------------------------------------------------

def test_R3_T19_a_non_ok_run_must_carry_an_open_loop():
    broken = manifest(
        outcome=ActionOutcome.FAILED,
        verification=Verification(
            method=VerificationMethod.DRIVE_READBACK_SHA256,
            expected=SHA_A, observed=None, detail="write raised",
        ),
    )
    with pytest.raises(ReceiptError, match="closed silently"):
        receipt([broken], open_loops=())


def test_R3_T20_next_action_is_always_present():
    with pytest.raises(ReceiptError, match="next_action"):
        receipt([manifest()], next_action="   ")


# --------------------------------------------------------------------------
# 5. Derived counts, and blocked is not attempted
# --------------------------------------------------------------------------

def test_R3_T21_a_blocked_action_is_never_counted_as_attempted():
    blocked = manifest(
        action_id="mint_credential",
        outcome=ActionOutcome.BLOCKED,
        verification=Verification(
            method=VerificationMethod.NOT_APPLICABLE_READ_ONLY,
            expected=None, observed=None,
            detail="refused before execution: human-only",
        ),
    )
    result = receipt(
        [manifest(), blocked], open_loops=("credential remains owner-only",)
    )
    assert result.blocked_actions == ("mint_credential",)
    assert "mint_credential" not in result.actions_attempted
    assert result.actions_attempted == ("write_bootstrap_index",)
    assert result.status is ReceiptStatus.OK


def test_R3_T22_a_blocked_action_cannot_carry_a_confirmed_write_readback():
    with pytest.raises(ReceiptError, match="cannot have been verified"):
        manifest(
            action_id="blocked_but_verified",
            outcome=ActionOutcome.BLOCKED,
            verification=confirmed_readback(),
        )


def test_R3_T23_class_C_is_never_an_autonomous_authorization_basis():
    """Contract 01 reserves class_C to a human."""
    with pytest.raises(ReceiptError, match="reserves to a human"):
        manifest(basis=AutonomyClass.CLASS_C)
    assert manifest(basis=AutonomyClass.CLASS_A).authorization_basis is (
        AutonomyClass.CLASS_A
    )


def test_R3_T24_derived_lists_cannot_be_authored_to_disagree_with_manifests():
    """assemble_receipt takes manifests, not count lists, so there is no
    parameter through which a caller could overstate what was verified."""
    import inspect

    params = inspect.signature(rr.assemble_receipt).parameters
    for forbidden in ("actions_attempted", "actions_verified", "blocked_actions"):
        assert forbidden not in params, (
            f"{forbidden} is derived and must not be an input"
        )
    assert "manifests" in params


# --------------------------------------------------------------------------
# 6. Absence is preserved, never imputed
# --------------------------------------------------------------------------

def test_R3_T25_a_missing_recovery_percent_stays_none_and_is_not_zero():
    result = receipt([manifest()], objective_recovery_percent=None)
    assert result.objective_recovery_percent is None
    assert result.objective_recovery_percent != 0
    payload = receipt_to_dict(result, [manifest()])
    assert payload["objective_recovery_percent"] is None


@pytest.mark.parametrize("bad", [-1, 101, 1000])
def test_R3_T26_an_out_of_range_recovery_percent_is_refused(bad):
    with pytest.raises(ReceiptError, match="objective_recovery_percent"):
        receipt([manifest()], objective_recovery_percent=bad)


def test_R3_T27_a_boolean_is_not_an_acceptable_recovery_percent():
    """True is an int in Python. Accepting it would record a fabricated 1%."""
    with pytest.raises(ReceiptError):
        receipt([manifest()], objective_recovery_percent=True)


def test_R3_T28_contract_versions_must_be_declared():
    with pytest.raises(ReceiptError, match="contract_versions"):
        receipt([manifest()], contract_versions={})


@pytest.mark.parametrize(
    "bad_stamp",
    ["2026-09-03 09:00:04", "2026-09-03T09:00:04+00:00", "2026-09-03T09:00Z", ""],
)
def test_R3_T29_the_timestamp_must_be_an_explicit_utc_instant(bad_stamp):
    with pytest.raises(ReceiptError, match="timestamp"):
        receipt([manifest()], timestamp=bad_stamp)


# --------------------------------------------------------------------------
# 7. Money never appears as a float anywhere in a persisted record
# --------------------------------------------------------------------------

def test_R3_T30_a_float_in_the_evidence_is_refused():
    with pytest.raises(ReceiptError, match="integer milliunits"):
        ActionManifest(
            run_id=RUN, action_id="log_spend", action="record a spend",
            owning_contract="NIZAM-DAILY-ORCHESTRATION-04",
            reason="synthetic", evidence=("amount", 12.5),
            affected_scope="LEDGER_ARTIFACT", risk="low",
            rollback_or_reversal="reverse the entry",
            verification=read_only_verification(),
            privacy_class="strict_local",
            authorization_basis=AutonomyClass.CLASS_A,
            expected_outcome="entry recorded",
            outcome=ActionOutcome.VERIFIED,
        )


def test_R3_T31_a_float_nested_anywhere_in_the_payload_is_refused():
    result = receipt([manifest()])
    good = receipt_to_dict(result, [manifest()])
    assert good["status"] == "OK"
    with pytest.raises(ReceiptError, match="integer milliunits"):
        rr._reject_floats({"balances": [{"egp": 1250.0}]}, "receipt")


def test_R3_T32_integer_milliunits_are_accepted_unchanged():
    """1 EGP = 1000 milliunits, transcribed. 12 EGP 500 piastres = 12500."""
    assert rr.MILLIUNITS_PER_EGP == 1000
    rr._reject_floats({"amount_milliunits": 12500}, "receipt")


# --------------------------------------------------------------------------
# 8. The 13:00 reconciliation run
# --------------------------------------------------------------------------

def test_R3_T33_a_reconciliation_names_the_run_it_reconciles():
    result = assemble_receipt(
        run_id="2026-09-03/reconcile_1300",
        timestamp="2026-09-03T10:00:02Z",
        contract_versions=VERSIONS,
        sukoon_state="yellow",
        objective_recovery_percent=58,
        himayah_classification="strict_local",
        modules_invoked=("cairo_gate", "run_record"),
        manifests=(),
        evidence_summary=("primary run verified; nothing to retry",),
        open_loops=(),
        next_action="no action; primary run already verified",
        reconciles_run_id=RUN,
    )
    assert result.reconciles_run_id == RUN
    assert result.status is ReceiptStatus.OK
    assert result.actions_attempted == ()


def test_R3_T34_a_reconciliation_cannot_cross_cairo_days():
    with pytest.raises(ReceiptError, match="same Cairo day"):
        receipt([manifest()], reconciles_run_id="2026-09-02/primary_1200")


def test_R3_T35_a_run_cannot_reconcile_itself():
    with pytest.raises(ReceiptError, match="cannot reconcile itself"):
        receipt([manifest()], reconciles_run_id=RUN)


# --------------------------------------------------------------------------
# 9. Records are immutable and carry their contract header
# --------------------------------------------------------------------------

def test_R3_T36_a_receipt_cannot_be_edited_after_assembly():
    result = receipt([manifest()])
    with pytest.raises(Exception):
        result.status = ReceiptStatus.OK  # type: ignore[misc]
    with pytest.raises(Exception):
        result.contract_versions["NIZAM-CONTRACT-01"] = "9.9.9"  # type: ignore[index]


def test_R3_T37_receipt_to_dict_refuses_a_manifest_from_another_run():
    result = receipt([manifest()])
    stray = manifest(run_id="2026-09-03/reconcile_1300")
    with pytest.raises(ReceiptError, match="does not belong to"):
        receipt_to_dict(result, [stray])


def test_R3_T38_the_module_names_its_contract_and_phase_in_its_header():
    import inspect
    import pathlib

    head = "\n".join(
        pathlib.Path(inspect.getsourcefile(rr))
        .read_text(encoding="utf-8")
        .splitlines()[:20]
    )
    assert "NIZAM-CONTRACT-01" in head
    assert "R3_THABAT" in head


def test_R3_T39_the_module_reads_no_clock_and_touches_no_storage():
    """A receipt must be replayable. A module that stamped its own time or
    wrote its own file could not be tested at the instant that matters."""
    import inspect
    import pathlib

    source = pathlib.Path(inspect.getsourcefile(rr)).read_text(encoding="utf-8")
    for forbidden in (
        "datetime.now", "utcnow", "time.time", "open(", "requests",
        "urllib", "subprocess", "Path(",
    ):
        assert forbidden not in source, f"impure construct found: {forbidden}"


# --------------------------------------------------------------------------
# The privacy classification vocabulary
# --------------------------------------------------------------------------

def test_R3_T40_an_invented_privacy_class_is_refused():
    """The field is enforced against an egress class downstream.

    2026-09-03: this test exists because an invented value, `private_personal`,
    reached three call sites unchallenged. The field was declared `str` and never
    checked, so nothing could catch it. An unenforceable classification is worse
    than a missing one, because it reads as a decision that was made.
    """
    with pytest.raises(ReceiptError, match="governing vocabulary"):
        ActionManifest(
            run_id=RUN, action_id="invented_class", action="do a thing",
            owning_contract="NIZAM-DAILY-ORCHESTRATION-04",
            reason="synthetic", evidence=("none",),
            affected_scope="local", risk="none",
            rollback_or_reversal="none",
            verification=read_only_verification(),
            privacy_class="private_personal",
            authorization_basis=AutonomyClass.CLASS_A,
            expected_outcome="nothing",
            outcome=ActionOutcome.VERIFIED,
        )


def test_R3_T41_the_public_class_is_refused_like_the_rest_of_the_repository():
    """`public` is rejected by the repository's own schema test; so here."""
    with pytest.raises(ReceiptError, match="governing vocabulary"):
        ActionManifest(
            run_id=RUN, action_id="public_class", action="do a thing",
            owning_contract="NIZAM-DAILY-ORCHESTRATION-04",
            reason="synthetic", evidence=("none",),
            affected_scope="local", risk="none",
            rollback_or_reversal="none",
            verification=read_only_verification(),
            privacy_class="public",
            authorization_basis=AutonomyClass.CLASS_A,
            expected_outcome="nothing",
            outcome=ActionOutcome.VERIFIED,
        )


@pytest.mark.parametrize("privacy_class", PRIVACY_CLASSES)
def test_R3_T42_every_governing_class_is_accepted(privacy_class):
    """The vocabulary must be usable in full, or it is not the vocabulary."""
    built = ActionManifest(
        run_id=RUN, action_id="allowed_class", action="do a thing",
        owning_contract="NIZAM-DAILY-ORCHESTRATION-04",
        reason="synthetic", evidence=("none",),
        affected_scope="local", risk="none",
        rollback_or_reversal="none",
        verification=read_only_verification(),
        privacy_class=privacy_class,
        authorization_basis=AutonomyClass.CLASS_A,
        expected_outcome="nothing",
        outcome=ActionOutcome.VERIFIED,
    )
    assert built.privacy_class == privacy_class


def test_R3_T43_an_invented_receipt_classification_is_refused():
    with pytest.raises(ReceiptError, match="governing vocabulary"):
        assemble_receipt(
            run_id=RUN, timestamp=STAMP, contract_versions=VERSIONS,
            sukoon_state="green", objective_recovery_percent=None,
            himayah_classification="private_personal",
            modules_invoked=("x",), manifests=[],
            evidence_summary=("none",), open_loops=(), next_action="stop",
        )


def test_R3_T44_the_vocabulary_is_ordered_most_sensitive_first():
    """Ordering is load bearing: an artifact takes its most sensitive field."""
    assert PRIVACY_CLASSES[0] == "strict_local_maximum"
    assert PRIVACY_CLASSES[-1] == "mirror_sanitized"
    assert len(set(PRIVACY_CLASSES)) == len(PRIVACY_CLASSES)


def test_R3_T45_the_transcribed_vocabulary_still_matches_its_schema():
    """Close the loop on the transcription when the schema is reachable.

    The package cannot import the schema at runtime, because it must load from
    two different roots. So the transcription is checked against the real file
    whenever the test happens to run inside the repository, and skipped with a
    stated reason when it does not. A silent pass would defeat the point.
    """
    here = pathlib.Path(__file__).resolve()
    schema = None
    for parent in here.parents:
        candidate = parent / "schemas" / "agent_message.schema.json"
        if candidate.exists():
            schema = candidate
            break
    if schema is None:
        pytest.skip(
            "agent_message.schema.json not reachable from this checkout root; "
            "the transcription is unverified here and is verified in the "
            "repository checkout"
        )
    loaded = json.loads(schema.read_text(encoding="utf-8"))
    enum = loaded["properties"]["privacy_class"]["enum"]
    assert set(enum) == set(PRIVACY_CLASSES), (
        f"transcription drifted from {schema.name}: "
        f"schema={sorted(enum)} code={sorted(PRIVACY_CLASSES)}"
    )


def test_R3_T46_the_module_names_the_schema_that_governs_the_vocabulary():
    """Closes tamper case R-W.

    A transcribed enum with no stated source is indistinguishable from a guess.
    The pointer to `agent_message.schema.json` is what lets the next reader --
    and T45 -- find the authority, so removing it must fail the suite.
    """
    source = inspect.getsource(rr)
    assert "agent_message.schema.json" in source
    assert "test_privacy_class_enum_enforced" in source
