# Contract: NIZAM-DAILY-ORCHESTRATION-04 daily_dag | Phase: R2_SCHEDULER
"""Acceptance tests for the governor entrypoint.

Owning contracts: NIZAM Contract 04 `daily_dag`, `schedule`, `reconciliation_1300`
                  NIZAM Contract 01 `required_runtime_receipt`, `autonomy_classes`
                  NIZAM-CONTRACT-05 regression_protection
Phase:            R2_SCHEDULER

WHAT THESE TESTS ARE FOR
The governor is the file that will eventually be allowed to change the outside
world, so the properties that must hold BEFORE that happens are pinned here
first: it shares one gate with the preflight, it reads the clock once, it cannot
report a stage it did not run, and it cannot close a blocked stage silently.
Every assertion below is traceable to a contract clause named in its docstring.
"""
import ast
import datetime as dt
import inspect
import json
import pathlib

import pytest

from scheduler import clock
from scheduler import governor_cli as gov
from scheduler import preflight_cli as pf
from scheduler.cairo_gate import UTC
from scheduler.run_record import (
    REQUIRED_MANIFEST_FIELDS,
    REQUIRED_RECEIPT_FIELDS,
    ActionOutcome,
    AutonomyClass,
    ReceiptStatus,
)

# ---------------------------------------------------------------------------
# Instants used below, transcribed by hand rather than computed, so a bug in the
# gate cannot also generate the expectation it is checked against.
#   Egypt is EEST (+03:00) from the last Friday of April to the last Thursday of
#   October, and EET (+02:00) otherwise.
# ---------------------------------------------------------------------------
SUMMER_1200 = dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC)   # 12:00 Cairo, +03:00
SUMMER_1200_LATE = dt.datetime(2026, 7, 15, 9, 4, tzinfo=UTC)
SUMMER_1300 = dt.datetime(2026, 7, 15, 10, 0, tzinfo=UTC)  # 13:00 Cairo
SUMMER_1000 = dt.datetime(2026, 7, 15, 7, 0, tzinfo=UTC)   # 10:00 Cairo
SUMMER_1140 = dt.datetime(2026, 7, 15, 8, 40, tzinfo=UTC)  # 11:40 Cairo
WINTER_1200 = dt.datetime(2026, 12, 15, 10, 0, tzinfo=UTC)  # 12:00 Cairo, +02:00
NEXT_DAY_1200 = dt.datetime(2026, 7, 16, 9, 0, tzinfo=UTC)

#: The cadence the owner approved on 2026-09-03, transcribed as literals.
APPROVED_CADENCE = {
    "refresh_1000": (10, 0),
    "volatile_1140": (11, 40),
    "primary_1200": (12, 0),
    "reconcile_1300": (13, 0),
}

GOV_SOURCE = inspect.getsource(gov)


def _run(now, slot, state_dir, **kw):
    return gov.run_slot(now, slot, state_dir, **kw)


# ---------------------------------------------------------------------------
# Slot table: it must be the approved cadence and Contract 04's anchors.
# ---------------------------------------------------------------------------
def test_R2_G01_slot_table_is_the_approved_cadence_exactly():
    """Contract 04 `schedule` + the owner's 2026-09-03 refresh cadence."""
    assert {name: (h, m) for name, (h, m, _role) in gov.SLOTS.items()} == (
        APPROVED_CADENCE
    )


def test_R2_G02_contract_04_anchors_are_present_under_their_own_names():
    """`primary_run` is 12:00 and `reconciliation_run` is 13:00 Africa/Cairo."""
    assert gov.SLOTS["primary_1200"][:2] == (12, 0)
    assert gov.SLOTS["reconcile_1300"][:2] == (13, 0)


def test_R2_G03_every_slot_carries_a_non_empty_role_description():
    for name, (_h, _m, role) in gov.SLOTS.items():
        assert role.strip(), f"{name} has no stated role"


def test_R2_G04_an_unknown_slot_is_refused_and_the_known_ones_are_named():
    with pytest.raises(ValueError) as excinfo:
        _run(SUMMER_1200, "primary_1201", pathlib.Path("."))
    message = str(excinfo.value)
    assert "primary_1201" in message
    for name in gov.SLOTS:
        assert name in message


# ---------------------------------------------------------------------------
# The gate and the guard are the preflight's, not a copy.
# ---------------------------------------------------------------------------
def test_R2_G05_the_governor_evaluates_slots_with_the_preflight_function_itself():
    """Contract 04 `schedule.preflight_requirement`.

    The preflight only proves the runtime if the runtime uses it. Identity, not
    similarity, is the property that makes the synthetic proof transfer.
    """
    assert gov.evaluate_slot is pf.evaluate_slot
    assert gov.evaluate_slot is pf.preflight


def test_R2_G06_the_governor_does_not_import_the_raw_gate_decision():
    """A second call site for `decide` would be a second, unproven gate."""
    tree = ast.parse(GOV_SOURCE)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.name)
    assert "decide" not in imported
    assert "decide(" not in GOV_SOURCE


def test_R2_G07_the_governor_makes_no_network_or_subprocess_import():
    """Contract 04 T02_HIMAYAH_BEFORE_EGRESS: no egress may originate here."""
    forbidden = {
        "socket", "http", "http.client", "urllib", "urllib.request",
        "requests", "httpx", "subprocess", "smtplib", "ftplib",
    }
    tree = ast.parse(GOV_SOURCE)
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            seen.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.add(node.module)
    assert not (seen & forbidden), f"forbidden imports: {sorted(seen & forbidden)}"


def test_R2_G08_the_governor_keeps_no_clock_read_of_its_own():
    """The impure boundary is `clock.read_utc_now`, shared with the preflight.

    A private `datetime.now()` here would let the governor and the proof that
    the governor fires correctly sit on two different instants.
    """
    code = [
        line for line in GOV_SOURCE.splitlines()
        if not line.lstrip().startswith("#")
    ]
    assert not any("datetime.now(" in line for line in code)
    assert gov.read_utc_now is clock.read_utc_now
    assert "read_utc_now()" in inspect.getsource(gov.main)


# ---------------------------------------------------------------------------
# Firing behaviour.
# ---------------------------------------------------------------------------
def test_R2_G09_the_matching_instant_produces_a_receipt(tmp_path):
    result = _run(SUMMER_1200, "primary_1200", tmp_path)
    assert result["receipt"] is not None
    assert result["slot_decision"]["executed"] is True
    assert result["receipt"]["run_id"] == "2026-07-15/primary_1200"


def test_R2_G10_a_slot_that_is_not_due_stands_down_without_a_receipt(tmp_path):
    """Both UTC candidates fire daily; the one that is not due must do nothing."""
    result = _run(SUMMER_1300, "primary_1200", tmp_path)
    assert result["receipt"] is None
    assert result["slot_decision"]["executed"] is False
    assert result["slot_decision"]["guard"] == pf.GUARD_NOT_CONSULTED
    assert list(tmp_path.iterdir()) == []


def test_R2_G11_a_second_firing_on_the_same_cairo_day_is_refused(tmp_path):
    """Contract 04 `reconciliation_1300`: no duplicate run for one Cairo day."""
    first = _run(SUMMER_1200, "primary_1200", tmp_path)
    assert first["receipt"] is not None
    second = _run(SUMMER_1200_LATE, "primary_1200", tmp_path)
    assert second["receipt"] is None
    assert second["slot_decision"]["guard"] == pf.GUARD_ALREADY_RAN


def test_R2_G12_the_guard_releases_on_the_next_cairo_day(tmp_path):
    assert _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"] is not None
    later = _run(NEXT_DAY_1200, "primary_1200", tmp_path)
    assert later["receipt"] is not None
    assert later["receipt"]["run_id"] == "2026-07-16/primary_1200"


def test_R2_G13_the_guard_is_per_slot_not_a_global_latch(tmp_path):
    assert _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"] is not None
    assert _run(SUMMER_1300, "reconcile_1300", tmp_path)["receipt"] is not None


@pytest.mark.parametrize(
    "now,slot",
    [
        (SUMMER_1000, "refresh_1000"),
        (SUMMER_1140, "volatile_1140"),
        (SUMMER_1200, "primary_1200"),
        (SUMMER_1300, "reconcile_1300"),
        (WINTER_1200, "primary_1200"),
    ],
)
def test_R2_G14_every_slot_runs_at_its_own_cairo_target_in_both_offsets(
    now, slot, tmp_path
):
    result = _run(now, slot, tmp_path)
    assert result["receipt"] is not None, result["slot_decision"]
    assert result["slot_decision"]["delta_minutes"] == 0


# ---------------------------------------------------------------------------
# Receipt shape: Contract 01 `required_runtime_receipt`.
# ---------------------------------------------------------------------------
def test_R2_G15_the_receipt_carries_all_thirteen_required_fields(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    for field in REQUIRED_RECEIPT_FIELDS:
        assert field in receipt, f"missing Contract 01 field {field}"


def test_R2_G16_every_manifest_carries_all_thirteen_required_fields(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    manifests = receipt["execution_manifest"]
    assert manifests
    for manifest in manifests:
        for field in REQUIRED_MANIFEST_FIELDS:
            assert field in manifest, f"missing Contract 04 field {field}"


def test_R2_G17_contract_versions_name_every_contract_relied_on(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert "NIZAM-CONTRACT-01" in receipt["contract_versions"]
    assert "NIZAM-DAILY-ORCHESTRATION-04" in receipt["contract_versions"]
    assert "NIZAM-CALENDAR-ACTUATION-001" in receipt["contract_versions"]


def test_R2_G18_modules_invoked_names_the_modules_that_actually_ran(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert set(receipt["modules_invoked"]) == {
        "cairo_gate", "preflight_cli", "run_record", "governor_cli"
    }


def test_R2_G19_the_receipt_is_a_single_json_line_with_no_float(tmp_path):
    """Money is integer milliunits; a float anywhere is a determinism defect."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    line = json.dumps(receipt, sort_keys=True)
    assert "\n" not in line
    reloaded = json.loads(line)

    def walk(value, path="receipt"):
        if isinstance(value, float):
            raise AssertionError(f"float at {path}: {value!r}")
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")

    walk(reloaded)


# ---------------------------------------------------------------------------
# Stage honesty: an unbuilt stage is BLOCKED with a named open loop.
# ---------------------------------------------------------------------------
def test_R2_G20_built_and_unbuilt_stage_ids_do_not_overlap():
    built = {action_id for action_id, _a, _c in gov._BUILT_STAGES}
    unbuilt = {action_id for action_id, _a, _p in gov._UNBUILT_STAGES}
    assert built and unbuilt
    assert not (built & unbuilt)


def test_R2_G21_every_unbuilt_stage_names_the_phase_that_will_land_it():
    """'Not yet' must be distinguishable from 'forgotten'."""
    for action_id, _action, phase in gov._UNBUILT_STAGES:
        assert phase in {"R3", "R4", "R5", "R6", "R7"}, (action_id, phase)


def test_R2_G22_the_receipt_verifies_exactly_the_built_stages(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    built = [action_id for action_id, _a, _c in gov._BUILT_STAGES]
    assert receipt["actions_verified"] == built


def test_R2_G23_the_receipt_blocks_exactly_the_unbuilt_stages(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    unbuilt = [action_id for action_id, _a, _p in gov._UNBUILT_STAGES]
    assert receipt["blocked_actions"] == unbuilt


def test_R2_G24_a_blocked_stage_is_never_counted_as_attempted(tmp_path):
    """Contract 01 `actions_attempted`: a refused action was never attempted."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert not set(receipt["actions_attempted"]) & set(receipt["blocked_actions"])


def test_R2_G25_every_blocked_stage_leaves_an_open_loop(tmp_path):
    """Contract 01 `open_loops`: an incomplete run cannot look complete."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert len(receipt["open_loops"]) == len(receipt["blocked_actions"])
    for action_id in receipt["blocked_actions"]:
        assert any(action_id in loop for loop in receipt["open_loops"])


def test_R2_G26_a_blocked_stage_carries_no_confirmed_write_verification(tmp_path):
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    for manifest in receipt["execution_manifest"]:
        if manifest["outcome"] != ActionOutcome.BLOCKED.value:
            continue
        assert manifest["verification"]["method"] == "not_applicable_read_only"
        assert manifest["verification"]["expected"] is None
        assert manifest["verification"]["observed"] is None


def test_R2_G27_no_manifest_claims_a_human_only_authorization_basis(tmp_path):
    """Contract 01 class_C is human-only; an autonomous run may not claim it."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    for manifest in receipt["execution_manifest"]:
        assert manifest["authorization_basis"] != AutonomyClass.CLASS_C.value


def test_R2_G28_no_stage_declares_an_external_effect_in_this_phase(tmp_path):
    """R2 ships timing and receipts only: no Drive, Calendar or GitHub write."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    for manifest in receipt["execution_manifest"]:
        if manifest["outcome"] == ActionOutcome.VERIFIED.value:
            assert manifest["affected_scope"] == "local run state only"


def test_R2_G29_the_status_is_ok_only_because_nothing_failed(tmp_path):
    """C04-T05: OK requires no FAILED and no AWAITING_READBACK manifest."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    outcomes = {m["outcome"] for m in receipt["execution_manifest"]}
    assert ActionOutcome.FAILED.value not in outcomes
    assert ActionOutcome.AWAITING_READBACK.value not in outcomes
    assert receipt["status"] == ReceiptStatus.OK.value


def test_R2_G30_built_manifest_evidence_quotes_the_real_slot_decision(tmp_path):
    result = _run(SUMMER_1200, "primary_1200", tmp_path)
    cairo_local = result["slot_decision"]["cairo_local"]
    for manifest in result["receipt"]["execution_manifest"]:
        if manifest["outcome"] != ActionOutcome.VERIFIED.value:
            continue
        assert any(cairo_local in item for item in manifest["evidence"])


# ---------------------------------------------------------------------------
# Absence, recovery and reconciliation.
# ---------------------------------------------------------------------------
def test_R2_G31_a_missing_recovery_reading_stays_absent(tmp_path):
    """Contract 01: None is not zero; no capacity is inferred from silence."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert receipt["objective_recovery_percent"] is None


def test_R2_G32_a_supplied_recovery_reading_is_carried_unchanged(tmp_path):
    receipt = _run(
        SUMMER_1200, "primary_1200", tmp_path,
        sukoon_state="yellow", objective_recovery_percent=41,
    )["receipt"]
    assert receipt["objective_recovery_percent"] == 41
    assert receipt["sukoon_state"] == "yellow"


def test_R2_G33_the_reconciliation_run_names_the_run_it_reconciles(tmp_path):
    """Contract 04 `reconciliation_1300`: retry or reconcile, never a new plan."""
    receipt = _run(SUMMER_1300, "reconcile_1300", tmp_path)["receipt"]
    assert receipt["reconciles_run_id"] == "2026-07-15/primary_1200"
    assert receipt["run_id"] == "2026-07-15/reconcile_1300"


def test_R2_G34_a_non_reconciliation_run_reconciles_nothing(tmp_path):
    for slot, now in (
        ("refresh_1000", SUMMER_1000),
        ("volatile_1140", SUMMER_1140),
        ("primary_1200", SUMMER_1200),
    ):
        receipt = _run(now, slot, tmp_path)["receipt"]
        assert receipt["reconciles_run_id"] is None


def test_R2_G35_the_reconciliation_run_is_the_last_run_of_the_day(tmp_path):
    earlier = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert "13:00" in earlier["next_action"]
    final = _run(SUMMER_1300, "reconcile_1300", tmp_path)["receipt"]
    assert final["next_action"] == "no further run today"


def test_R2_G36_a_run_always_leaves_a_next_action(tmp_path):
    for slot, now in (
        ("refresh_1000", SUMMER_1000),
        ("volatile_1140", SUMMER_1140),
        ("primary_1200", SUMMER_1200),
        ("reconcile_1300", SUMMER_1300),
    ):
        receipt = _run(now, slot, tmp_path)["receipt"]
        assert receipt["next_action"].strip()


# ---------------------------------------------------------------------------
# CLI behaviour.
# ---------------------------------------------------------------------------
def test_R2_G37_the_cli_refuses_a_missing_or_unknown_slot(capsys):
    assert gov.main([]) == 2
    assert gov.main(["primary_1200", "extra"]) == 2
    assert gov.main(["not_a_slot"]) == 2
    assert "usage" in capsys.readouterr().err


def test_R2_G38_a_standing_down_slot_exits_zero_and_writes_no_receipt(
    tmp_path, monkeypatch, capsys
):
    """Standing down is the designed behaviour of the slot that is not due."""
    monkeypatch.setenv("NIZAM_GOVERNOR_STATE", str(tmp_path))

    monkeypatch.setattr(gov, "read_utc_now", lambda: SUMMER_1300)
    assert gov.main(["primary_1200"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["receipt"] is None
    assert not (tmp_path / "receipts.jsonl").exists()


def test_R2_G39_a_firing_appends_exactly_one_receipt_line(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("NIZAM_GOVERNOR_STATE", str(tmp_path))

    monkeypatch.setattr(gov, "read_utc_now", lambda: SUMMER_1200)
    assert gov.main(["primary_1200"]) == 0
    capsys.readouterr()
    lines = (tmp_path / "receipts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["run_id"] == "2026-07-15/primary_1200"

    # A second firing on the same Cairo day must append nothing.
    assert gov.main(["primary_1200"]) == 0
    capsys.readouterr()
    lines = (tmp_path / "receipts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_R2_G40_the_state_directory_is_configurable_and_created(
    tmp_path, monkeypatch, capsys
):
    target = tmp_path / "nested" / "state"
    monkeypatch.setenv("NIZAM_GOVERNOR_STATE", str(target))

    monkeypatch.setattr(gov, "read_utc_now", lambda: SUMMER_1200)
    assert gov.main(["primary_1200"]) == 0
    capsys.readouterr()
    assert target.is_dir()


def test_R2_G41_the_module_declares_its_owning_contract_in_the_first_20_lines():
    """NIZAM repository rule: provenance in the header, not in a wiki."""
    head = GOV_SOURCE.splitlines()[:20]
    joined = "\n".join(head)
    assert "NIZAM-DAILY-ORCHESTRATION-04" in joined
    assert "R2_SCHEDULER" in joined


def test_R2_G42_the_run_is_classified_private_personal_not_public(tmp_path):
    """Contract 04 `D_HIMAYAH` / `T02_HIMAYAH_BEFORE_EGRESS`.

    An autonomous run may not reclassify the owner's data downward. This
    classification is what every later egress decision is taken against, so a
    silent widening here would authorise disclosure everywhere downstream.
    """
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    assert receipt["himayah_classification"] == "strict_local"


def test_R2_G43_every_manifest_declares_the_same_private_privacy_class(tmp_path):
    """Contract 04 `execution_manifest.privacy_class`, per action."""
    receipt = _run(SUMMER_1200, "primary_1200", tmp_path)["receipt"]
    classes = {m["privacy_class"] for m in receipt["execution_manifest"]}
    assert classes == {"strict_local"}, classes


def test_R2_G44_the_rationale_against_imputing_absence_is_still_stated():
    """Closes tamper case V-O.

    Imputing zero for a missing recovery reading is caught behaviourally by
    G31, but the only thing stopping a future editor from writing `or 0` in the
    first place is the comment that says not to. The tamper harness deleted that
    comment and nothing failed, which is the same gap P15 and the clock module
    already close for the clock read: rationale that prevents a defect is part
    of the guard, so the suite asserts it rather than hoping it survives.
    """
    assert "Absence stays absence" in GOV_SOURCE
    assert "NOT zero" in GOV_SOURCE
    assert "inferred from silence" in GOV_SOURCE


def test_R2_G45_the_classification_choice_is_justified_where_it_is_made():
    """A bare `strict_local` would look arbitrary to the next reader."""
    assert "most sensitive field" in GOV_SOURCE.lower()
    assert "review_before_commit" in GOV_SOURCE
