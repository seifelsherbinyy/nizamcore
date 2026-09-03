# Contract: NIZAM-DAILY-ORCHESTRATION-04 schedule.preflight_requirement | Phase: R2_SCHEDULER
"""Acceptance tests for the scheduler preflight and its run-once guard.

Owning contract: NIZAM Contract 04, `schedule.preflight_requirement`
Phase:           R2_SCHEDULER

`preflight()` takes both the instant and the state directory as arguments, so
everything except the single clock read inside `main()` is testable at the
exact instants that matter, including Egypt's DST transition.
"""
import datetime as dt
import inspect
import json
import pathlib

import pytest

from scheduler import clock
from scheduler import preflight_cli as pf
from scheduler.cairo_gate import UTC, Verdict
from scheduler.preflight_cli import (
    GUARD_ALREADY_RAN,
    GUARD_FIRST_RUN,
    GUARD_NOT_CONSULTED,
    preflight,
)
from scheduler.run_record import build_run_id

# Contract 04 preflight_requirement names these three facts, transcribed.
REQUIRED_PREFLIGHT_FACTS = ["scheduler_timezone", "service_identity", "working_directory"]

# The concrete keys that constitute each required fact. A prefix match is NOT
# enough: dropping `service_identity_user` while keeping the host and pid still
# satisfies a prefix check but loses WHICH ACCOUNT ran the job, which is the
# part of "service identity" that matters when two accounts share a host.
REQUIRED_IDENTITY_KEYS = {
    "scheduler_timezone": (
        "scheduler_timezone_env_tz",
        "scheduler_timezone_localtime",
    ),
    "service_identity": (
        "service_identity_user",
        "service_identity_host",
        "service_identity_pid",
    ),
    "working_directory": ("working_directory",),
}

FAKE_IDENTITY = {
    "scheduler_timezone_env_tz": "<unset>",
    "scheduler_timezone_localtime": "UTC+0000",
    "service_identity_user": "SERVICE_USER",
    "service_identity_host": "SERVICE_HOST",
    "service_identity_pid": "1",
    "working_directory": "WORKING_DIR",
    "python": "3.14.4",
}


def run(now, hour, minute, slot, state, **kw):
    return preflight(now, hour, minute, slot, state, identity=FAKE_IDENTITY, **kw)


# --------------------------------------------------------------------------
# 1. The guard: once per Cairo day, per slot
# --------------------------------------------------------------------------

def test_R2_P01_a_correct_slot_executes_and_leaves_a_marker(tmp_path):
    now = dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC)
    record = run(now, 12, 0, "primary_1200", tmp_path)
    assert record["verdict"] == Verdict.RUN.value
    assert record["guard"] == GUARD_FIRST_RUN
    assert record["executed"] is True
    assert record["cairo_date"] == "2026-07-15"
    assert record["run_id"] == build_run_id("2026-07-15", "primary_1200")
    assert (tmp_path / "2026-07-15__primary_1200.ran").exists()


def test_R2_P02_a_second_firing_for_the_same_day_and_slot_is_refused(tmp_path):
    """The dual-slot pattern means a second firing is normal, not exceptional."""
    first = run(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    second = run(dt.datetime(2026, 7, 15, 9, 4, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    assert first["executed"] is True
    assert second["verdict"] == Verdict.RUN.value, "the gate still says run"
    assert second["delta_minutes"] == 4, "inside the tolerance window"
    assert second["guard"] == GUARD_ALREADY_RAN
    assert second["executed"] is False, "the guard, not the gate, stopped it"


def test_R2_P03_the_guard_is_per_slot_not_a_global_latch(tmp_path):
    run(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    other = run(dt.datetime(2026, 7, 15, 10, 0, tzinfo=UTC), 13, 0, "reconcile_1300", tmp_path)
    assert other["guard"] == GUARD_FIRST_RUN
    assert other["executed"] is True


def test_R2_P04_the_guard_releases_on_the_next_cairo_day(tmp_path):
    run(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    tomorrow = run(dt.datetime(2026, 7, 16, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    assert tomorrow["cairo_date"] == "2026-07-16"
    assert tomorrow["guard"] == GUARD_FIRST_RUN
    assert tomorrow["executed"] is True


def test_R2_P05_the_dst_double_fire_is_contained_by_the_guard(tmp_path):
    """The case `cairo_gate.dst_hazards` reports for a late-evening target.

    On Egypt's autumn transition both candidate UTC slots land on the same
    Cairo date at the same wall time. The gate cannot tell them apart, so the
    guard is the only thing standing between one run and two.
    """
    first = run(dt.datetime(2026, 10, 29, 20, 0, tzinfo=UTC), 23, 0, "late_2300", tmp_path)
    second = run(dt.datetime(2026, 10, 29, 21, 0, tzinfo=UTC), 23, 0, "late_2300", tmp_path)
    assert first["verdict"] == Verdict.RUN.value
    assert second["verdict"] == Verdict.RUN.value, "both slots genuinely match"
    assert first["cairo_date"] == second["cairo_date"] == "2026-10-29"
    assert first["executed"] is True
    assert second["executed"] is False
    assert second["guard"] == GUARD_ALREADY_RAN


def test_R2_P06_the_marker_is_named_by_the_cairo_date_not_the_utc_date(tmp_path):
    """22:00 UTC is already the next day in Cairo. A UTC-keyed marker would
    guard the wrong day."""
    record = run(dt.datetime(2026, 7, 15, 22, 0, tzinfo=UTC), 1, 0, "late_0100", tmp_path)
    assert record["utc_instant"].startswith("2026-07-15")
    assert record["cairo_date"] == "2026-07-16"
    assert (tmp_path / "2026-07-16__late_0100.ran").exists()
    assert not (tmp_path / "2026-07-15__late_0100.ran").exists()


# --------------------------------------------------------------------------
# 2. Standing down writes nothing
# --------------------------------------------------------------------------

def test_R2_P07_a_stood_down_slot_writes_no_marker_and_claims_no_run(tmp_path):
    record = run(dt.datetime(2026, 7, 15, 10, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    assert record["verdict"] == Verdict.SKIP_WRONG_CAIRO_TIME.value
    assert record["guard"] == GUARD_NOT_CONSULTED
    assert record["executed"] is False
    assert record["run_id"] is None
    assert list(tmp_path.iterdir()) == []


def test_R2_P08_a_naive_instant_stands_down_without_touching_state(tmp_path):
    record = run(dt.datetime(2026, 7, 15, 9, 0), 12, 0, "primary_1200", tmp_path)
    assert record["verdict"] == Verdict.SKIP_NOT_TZ_AWARE.value
    assert record["executed"] is False
    assert record["cairo_date"] is None
    assert list(tmp_path.iterdir()) == []


def test_R2_P09_a_dry_run_consults_the_guard_without_committing(tmp_path):
    record = run(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200",
                 tmp_path, commit_marker=False)
    assert record["guard"] == GUARD_FIRST_RUN
    assert list(tmp_path.iterdir()) == [], "a dry run must leave no trace"
    again = run(dt.datetime(2026, 7, 15, 9, 1, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    assert again["guard"] == GUARD_FIRST_RUN, "the dry run must not have latched"


# --------------------------------------------------------------------------
# 3. The three facts Contract 04 requires the preflight to record
# --------------------------------------------------------------------------

def test_R2_P10_the_record_carries_all_three_required_preflight_facts():
    identity = pf.scheduler_identity(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC))
    for fact, keys in REQUIRED_IDENTITY_KEYS.items():
        for key in keys:
            assert key in identity, (
                f"Contract 04 preflight_requirement requires {fact}, "
                f"and {key} is part of it"
            )
            assert str(identity[key]).strip(), f"{key} is present but empty"
    assert set(REQUIRED_IDENTITY_KEYS) == set(REQUIRED_PREFLIGHT_FACTS)


def test_R2_P10b_a_firing_record_carries_the_same_required_keys(tmp_path):
    """The identity helper and the emitted record must not drift apart."""
    record = preflight(
        dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path
    )
    identity = record["identity"]
    for keys in REQUIRED_IDENTITY_KEYS.values():
        for key in keys:
            assert key in identity, f"the emitted record dropped {key}"


def test_R2_P11_identity_is_read_from_the_live_process_not_declared(tmp_path):
    """The claim under test is what the runtime does, so the facts must come
    from the running process rather than from a config file."""
    identity = pf.scheduler_identity(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC))
    assert identity["working_directory"] == str(pathlib.Path.cwd())
    assert identity["service_identity_pid"].isdigit()
    assert int(identity["service_identity_pid"]) > 0


def test_R2_P12_the_record_names_its_governing_contract(tmp_path):
    record = run(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    assert record["record"] == "scheduler_preflight"
    assert "NIZAM-DAILY-ORCHESTRATION-04" in record["contract"]
    assert "preflight_requirement" in record["contract"]


def test_R2_P13_the_record_serialises_to_one_json_line(tmp_path):
    """Evidence has to be machine-checkable, so one firing is one JSON object."""
    record = run(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0, "primary_1200", tmp_path)
    line = json.dumps(record, sort_keys=True)
    assert "\n" not in line
    assert json.loads(line)["executed"] is True


# --------------------------------------------------------------------------
# 4. Purity boundary: exactly one clock read in the whole package
# --------------------------------------------------------------------------

def test_R2_P14_the_package_reads_the_clock_in_exactly_one_place():
    """The confinement claim, checked rather than trusted.

    2026-09-03: this test earned its keep. Adding `governor_cli` introduced a
    SECOND clock read and this assertion failed, which is what forced the read
    into `clock.py` where it is the only thing a module does. The assertion is
    now stricter than it was, because the one permitted location is a file with
    no other purpose: any drift is visible in the filename alone.
    """
    package = pathlib.Path(inspect.getsourcefile(pf)).parent
    reads = []
    for path in sorted(package.glob("*.py")):
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.lstrip().startswith("#"):
                continue
            if "datetime.now(" in line or "utcnow(" in line:
                reads.append(f"{path.name}:{number}")
    assert reads == ["clock.py:" + str(_clock_line())], reads


def _clock_line() -> int:
    source = pathlib.Path(inspect.getsourcefile(clock)).read_text(encoding="utf-8")
    for number, line in enumerate(source.splitlines(), start=1):
        if "datetime.now(" in line and not line.lstrip().startswith("#"):
            return number
    raise AssertionError("no clock read found in clock.py")


def test_R2_P15_the_clock_read_is_annotated_as_the_only_one():
    """A future reader must be told, not left to infer, that this line is load
    bearing."""
    lines = pathlib.Path(inspect.getsourcefile(clock)).read_text(
        encoding="utf-8"
    ).splitlines()
    preceding = lines[_clock_line() - 2]
    assert "ONLY CLOCK READ" in preceding.upper()


def test_R2_P14b_no_entrypoint_keeps_a_private_clock_read():
    """Every entrypoint must go through the shared reader, not around it."""
    package = pathlib.Path(inspect.getsourcefile(pf)).parent
    for name in ("preflight_cli.py", "governor_cli.py"):
        source = (package / name).read_text(encoding="utf-8")
        assert "read_utc_now" in source, f"{name} does not use the shared reader"
        code = [
            line for line in source.splitlines()
            if not line.lstrip().startswith("#")
        ]
        assert not any("datetime.now(" in line for line in code), name


def test_R2_P16_the_cli_refuses_the_wrong_number_of_arguments():
    assert pf.main([]) == 2
    assert pf.main(["12"]) == 2
    assert pf.main(["12", "0", "slot", "extra"]) == 2


def test_R2_P17_standing_down_is_not_an_error_exit(tmp_path, monkeypatch, capsys):
    """cron must not see a stood-down slot as a failure, or the wrong slot
    would page the owner every single day."""
    monkeypatch.setenv("NIZAM_PREFLIGHT_STATE", str(tmp_path))
    code = pf.main(["3", "0", "impossible_hour_now"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["record"] == "scheduler_preflight"


# --------------------------------------------------------------------------
# 5. The preflight proves the production path, not a parallel copy
# --------------------------------------------------------------------------

def test_R2_P18_the_governor_slot_evaluator_is_the_preflight_function_itself():
    """If these ever became two implementations, the synthetic preflight would
    prove nothing about what the governor actually does at noon."""
    assert pf.evaluate_slot is pf.preflight


def test_R2_P19_no_second_gate_or_guard_implementation_exists_in_the_package():
    """A second call site for `decide` outside the shared evaluator would be a
    parallel gate. Only the shared evaluator and the gate's own module may
    reference it."""
    package = pathlib.Path(inspect.getsourcefile(pf)).parent
    callers = []
    for path in sorted(package.glob("*.py")):
        if path.name == "cairo_gate.py":
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("*"):
                continue
            if "decide(" in stripped and "def decide" not in stripped:
                callers.append(f"{path.name}:{number}")
    assert callers == ["preflight_cli.py:" + str(_decide_call_line())], callers


def _decide_call_line() -> int:
    source = pathlib.Path(inspect.getsourcefile(pf)).read_text(encoding="utf-8")
    for number, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if "decide(" in stripped and "import" not in stripped:
            return number
    raise AssertionError("no call to decide() found in preflight_cli")
