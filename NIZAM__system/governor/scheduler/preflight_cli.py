# Contract: NIZAM-DAILY-ORCHESTRATION-04 schedule.preflight_requirement | Phase: R2_SCHEDULER
"""Scheduler preflight CLI: prove the runtime fires at the expected Cairo instant.

Owning contract: NIZAM Contract 04, `schedule.preflight_requirement`
Phase:           R2_SCHEDULER

Contract 04 requires the preflight to prove with a synthetic scheduled job that
the runtime fires at the expected Cairo instant, and to RECORD the scheduler
timezone, the service identity and the working directory. This module is that
job. It emits exactly one JSON line per firing so a real cron run leaves
machine-checkable evidence rather than prose.

IMPURITY IS CONFINED HERE ON PURPOSE
`cairo_gate` and `run_record` read no clock and touch no storage, which is what
makes them testable at the instants that matter. Something must eventually read
the real clock and the real filesystem, and this is the single place that does.
`preflight()` and `scheduler_identity()` both take `now_utc` as an argument, so
the ONE clock read in the whole package is the single annotated line inside
`clock.read_utc_now`, which every entrypoint calls instead of repeating. See
`clock.py` for why that line is a module of its own.
`tests/test_preflight_cli.py` asserts the count rather than trusting this
paragraph.

THE RUN-ONCE GUARD
Two UTC slots are registered for every Cairo target, and on Egypt's autumn
transition a late-evening target can be matched by both on the same Cairo date
(see `cairo_gate.dst_hazards`). The guard therefore keys on the CAIRO date, not
the UTC date, and refuses a second execution for the same (cairo_date, slot).
A refusal is not a failure: the process exits 0, because standing down is the
designed behaviour of the slot that should not run.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import socket
import sys

from .cairo_gate import decide
from .clock import read_utc_now
from .run_record import build_run_id

#: Emitted when the gate said RUN but this Cairo day and slot already ran.
GUARD_ALREADY_RAN = "already_ran_this_cairo_day"
GUARD_FIRST_RUN = "first_run_this_cairo_day"
GUARD_NOT_CONSULTED = "not_consulted_gate_stood_down"


def scheduler_identity(now_utc: _dt.datetime) -> dict[str, str]:
    """The three facts Contract 04's preflight_requirement names.

    Read from the live process rather than declared in a config file, because
    the thing under test is what the RUNTIME actually does, not what a document
    claims it does.

    `now_utc` is passed in rather than read here. The scheduler's local zone
    name is instant-dependent, so resolving it needs a moment in time; taking
    that moment as an argument is what keeps the package to a single clock read.
    """
    return {
        "scheduler_timezone_env_tz": os.environ.get("TZ", "<unset>"),
        "scheduler_timezone_localtime": now_utc.astimezone().strftime("%Z%z"),
        "service_identity_user": _resolve_user(),
        "service_identity_host": socket.gethostname(),
        "service_identity_pid": str(os.getpid()),
        "working_directory": os.getcwd(),
        "python": sys.version.split()[0],
    }


def _resolve_user() -> str:
    try:
        import getpass

        return getpass.getuser()
    except Exception:  # pragma: no cover - depends on host account plumbing
        return os.environ.get("USER", "<unknown>")


def _marker(state_dir: pathlib.Path, cairo_date: str, slot: str) -> pathlib.Path:
    return state_dir / f"{cairo_date}__{slot}.ran"


def preflight(
    now_utc: _dt.datetime,
    target_hour: int,
    target_minute: int,
    slot: str,
    state_dir: pathlib.Path,
    *,
    identity: dict[str, str] | None = None,
    commit_marker: bool = True,
) -> dict[str, object]:
    """Decide, apply the run-once guard, and return the evidence record."""
    decision = decide(now_utc, target_hour, target_minute)

    guard = GUARD_NOT_CONSULTED
    run_id = None
    if decision.should_run:
        assert decision.cairo_date is not None
        run_id = build_run_id(decision.cairo_date, slot)
        marker = _marker(state_dir, decision.cairo_date, slot)
        if marker.exists():
            guard = GUARD_ALREADY_RAN
        else:
            guard = GUARD_FIRST_RUN
            if commit_marker:
                state_dir.mkdir(parents=True, exist_ok=True)
                marker.write_text(
                    f"{decision.utc_instant} {decision.cairo_local}\n",
                    encoding="utf-8",
                )

    executed = decision.should_run and guard == GUARD_FIRST_RUN
    return {
        "record": "scheduler_preflight",
        "contract": "NIZAM-DAILY-ORCHESTRATION-04 schedule.preflight_requirement",
        "slot": slot,
        "target": decision.target,
        "verdict": decision.verdict.value,
        "should_run_per_gate": decision.should_run,
        "guard": guard,
        "executed": executed,
        "delta_minutes": decision.delta_minutes,
        "cairo_local": decision.cairo_local,
        "cairo_date": decision.cairo_date,
        "utc_instant": decision.utc_instant,
        "run_id": run_id,
        "reason": decision.reason,
        "identity": (
            identity if identity is not None else scheduler_identity(now_utc)
        ),
    }


#: The governor uses THIS function, not a copy of it, to decide whether a slot
#: runs. That is deliberate and it is the whole value of the synthetic preflight:
#: a preflight that exercised a parallel implementation would prove only that
#: the parallel implementation works. Contract 04 asks for proof that "the
#: runtime fires at the expected Cairo instant", so the runtime and the proof
#: must share one gate and one guard.
evaluate_slot = preflight


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 3:
        print(
            "usage: preflight_cli TARGET_HOUR TARGET_MINUTE SLOT_NAME",
            file=sys.stderr,
        )
        return 2
    target_hour, target_minute, slot = int(args[0]), int(args[1]), args[2]
    state_dir = pathlib.Path(
        os.environ.get("NIZAM_PREFLIGHT_STATE", "")
        or (pathlib.Path.home() / ".nizam-preflight")
    )

    # The one clock read lives in `clock.read_utc_now`; see that module for why
    # it is not repeated here.
    now_utc = read_utc_now()

    record = preflight(now_utc, target_hour, target_minute, slot, state_dir)
    print(json.dumps(record, sort_keys=True))
    # A slot that correctly stands down is not an error.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
