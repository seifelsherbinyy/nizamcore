# Contract: NIZAM-DAILY-ORCHESTRATION-04 daily_dag | Phase: R2_SCHEDULER
"""Governor entrypoint: gate the slot, run the stages that exist, emit a receipt.

Owning contracts: NIZAM Contract 04 `daily_dag`, `schedule`, `reconciliation_1300`
                  NIZAM Contract 01 `required_runtime_receipt`, `autonomy_classes`
Phase:            R2_SCHEDULER

WHY THIS SHIPS BEFORE THE STAGES DO
The timing authority and the receipt are what make every later phase
verifiable, so they go live first. Stages that do not exist yet are recorded as
BLOCKED actions with a named open loop each. That is the contract-honest
position: Contract 01 requires `blocked_actions` and `open_loops` on every
receipt precisely so that an incomplete run cannot present itself as a complete
one. A stage is never silently omitted, and its absence is never reported as
success.

WHAT THIS DELIBERATELY DOES NOT DO
No Drive write, no Calendar write, no GitHub write, no network call, no money.
Contract 01 class_C stays human-only, and `run_record` refuses any manifest
claiming class_C authority. When a stage lands it replaces its own BLOCKED entry
here; nothing else in this file needs to change.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import sys

from .clock import read_utc_now
from .preflight_cli import evaluate_slot
from .run_record import (
    ActionManifest,
    ActionOutcome,
    AutonomyClass,
    Verification,
    VerificationMethod,
    assemble_receipt,
    receipt_to_dict,
)

CONTRACT_VERSIONS = {
    "NIZAM-CONTRACT-01": "1.0.0",
    "NIZAM-DAILY-ORCHESTRATION-04": "1.0.0",
    "NIZAM-CALENDAR-ACTUATION-001": "1.0.0",
}

#: Slots this entrypoint recognises, mapped to their Cairo target and role.
#: Transcribed from Contract 04 `schedule` plus the owner's refresh cadence.
SLOTS = {
    "refresh_1000": (10, 0, "heavier Drive, index and cache refresh"),
    "volatile_1140": (11, 40, "volatile WHOOP, Calendar, location, weather, news"),
    "primary_1200": (12, 0, "primary governor run"),
    "reconcile_1300": (13, 0, "reconciliation and retry only"),
}

#: Stages the deterministic layer can already do, and stages it cannot.
#: Each unbuilt stage names the phase that will land it, so a reader can tell
#: "not yet" from "forgotten".
_BUILT_STAGES = (
    ("slot_gate", "gate the firing against the real Cairo clock",
     "NIZAM-DAILY-ORCHESTRATION-04 schedule"),
    ("run_once_guard", "refuse a second execution for this Cairo day and slot",
     "NIZAM-DAILY-ORCHESTRATION-04 reconciliation_1300"),
    ("assemble_receipt", "emit a THABAT run receipt with a derived status",
     "NIZAM-CONTRACT-01 required_runtime_receipt"),
)

_UNBUILT_STAGES = (
    ("drive_domain_extension", "extend the retrieval entrypoint domains", "R3"),
    ("thabat_drive_persistence", "persist the receipt to Drive with readback", "R3"),
    ("whoop_recovery_read", "read objective recovery from the health MCP", "R4"),
    ("marsad_weather_read", "read Cairo weather and air quality", "R4"),
    ("marsad_news_read", "read world events from a keyless feed", "R4"),
    ("location_intelligence", "resolve current location context", "R4"),
    ("calendar_actuation", "create, update or move calendar events", "R5"),
    ("hikmah_promotion", "promote a belief through the learning stages", "R6"),
    ("github_autonomy", "commit and push a verified change", "R7"),
)


def _blocked_verification(detail: str) -> Verification:
    return Verification(
        method=VerificationMethod.NOT_APPLICABLE_READ_ONLY,
        expected=None,
        observed=None,
        detail=detail,
    )


def build_manifests(run_id: str, slot_record: dict[str, object]) -> list[ActionManifest]:
    """One manifest per stage: what ran, and what could not."""
    manifests: list[ActionManifest] = []
    for action_id, action, owning_contract in _BUILT_STAGES:
        manifests.append(
            ActionManifest(
                run_id=run_id,
                action_id=action_id,
                action=action,
                owning_contract=owning_contract,
                reason="required before any later stage may be trusted",
                evidence=(
                    f"verdict={slot_record['verdict']}",
                    f"guard={slot_record['guard']}",
                    f"cairo_local={slot_record['cairo_local']}",
                ),
                affected_scope="local run state only",
                risk="none: no external effect",
                rollback_or_reversal="not applicable; nothing external was changed",
                verification=_blocked_verification(
                    "deterministic in-process step; asserted by the package suite"
                ),
                privacy_class="strict_local",
                authorization_basis=AutonomyClass.CLASS_A,
                expected_outcome="the slot decision and receipt are recorded",
                outcome=ActionOutcome.VERIFIED,
            )
        )
    for action_id, action, phase in _UNBUILT_STAGES:
        manifests.append(
            ActionManifest(
                run_id=run_id,
                action_id=action_id,
                action=action,
                owning_contract="NIZAM-DAILY-ORCHESTRATION-04 daily_dag",
                reason=f"stage lands in {phase}; refused rather than faked",
                evidence=(f"not_yet_implemented_phase={phase}",),
                affected_scope="none",
                risk="none: refused before execution",
                rollback_or_reversal="not applicable; never attempted",
                verification=_blocked_verification(
                    f"no capability wired yet; scheduled for {phase}"
                ),
                privacy_class="strict_local",
                authorization_basis=AutonomyClass.CLASS_A,
                expected_outcome=f"stage becomes available in {phase}",
                outcome=ActionOutcome.BLOCKED,
            )
        )
    return manifests


def run_slot(
    now_utc: _dt.datetime,
    slot: str,
    state_dir: pathlib.Path,
    *,
    sukoon_state: str = "unknown",
    objective_recovery_percent: int | None = None,
) -> dict[str, object]:
    """Evaluate the slot and, if it is ours to run, emit a receipt."""
    if slot not in SLOTS:
        raise ValueError(f"unknown slot {slot!r}; known: {sorted(SLOTS)}")
    target_hour, target_minute, role = SLOTS[slot]

    slot_record = evaluate_slot(now_utc, target_hour, target_minute, slot, state_dir)
    if not slot_record["executed"]:
        return {"slot_decision": slot_record, "receipt": None, "role": role}

    run_id = str(slot_record["run_id"])
    manifests = build_manifests(run_id, slot_record)
    blocked = [m.action_id for m in manifests if m.outcome is ActionOutcome.BLOCKED]

    receipt = assemble_receipt(
        run_id=run_id,
        timestamp=str(slot_record["utc_instant"]),
        contract_versions=CONTRACT_VERSIONS,
        sukoon_state=sukoon_state,
        # Absence stays absence. A missing recovery reading is NOT zero, and no
        # capacity is inferred from silence.
        objective_recovery_percent=objective_recovery_percent,
        # `strict_local` because the receipt carries `sukoon_state` and
        # `objective_recovery_percent`. The governing schema classifies an
        # artifact by the MOST sensitive field in its payload, and those two are
        # personal health signals. `review_before_commit` would be wrong here
        # even though the receipt is otherwise mundane run metadata.
        himayah_classification="strict_local",
        modules_invoked=("cairo_gate", "preflight_cli", "run_record", "governor_cli"),
        manifests=manifests,
        evidence_summary=(
            f"slot={slot} role={role}",
            f"cairo_local={slot_record['cairo_local']}",
            f"delta_minutes={slot_record['delta_minutes']}",
            f"stages_built={len(_BUILT_STAGES)} stages_blocked={len(blocked)}",
        ),
        open_loops=tuple(f"{action_id} not implemented" for action_id in blocked),
        next_action=(
            "reconcile at 13:00 Africa/Cairo"
            if slot != "reconcile_1300"
            else "no further run today"
        ),
        reconciles_run_id=(
            f"{slot_record['cairo_date']}/primary_1200"
            if slot == "reconcile_1300"
            else None
        ),
    )
    return {
        "slot_decision": slot_record,
        "receipt": receipt_to_dict(receipt, manifests),
        "role": role,
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] not in SLOTS:
        print(f"usage: governor_cli SLOT   (one of {sorted(SLOTS)})", file=sys.stderr)
        return 2
    state_dir = pathlib.Path(
        os.environ.get("NIZAM_GOVERNOR_STATE", "")
        or (pathlib.Path.home() / ".nizam-governor")
    )
    state_dir.mkdir(parents=True, exist_ok=True)

    # One reader for the whole package, shared with the preflight entrypoint, so
    # the governor and its proof cannot drift onto two different instants.
    now_utc = read_utc_now()

    result = run_slot(now_utc, args[0], state_dir)
    print(json.dumps(result, sort_keys=True))
    if result["receipt"] is not None:
        receipts = state_dir / "receipts.jsonl"
        with open(receipts, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(result["receipt"], sort_keys=True) + "\n")
    # Standing down is the designed behaviour of the slot that should not run.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
