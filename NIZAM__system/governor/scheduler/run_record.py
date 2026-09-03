# Contract: NIZAM-CONTRACT-01 required_runtime_receipt | Phase: R3_THABAT
"""THABAT run records: the per-run receipt and the per-action manifest.

Owning contracts: NIZAM Contract 01, `required_runtime_receipt` (13 fields)
                  NIZAM Contract 04, `execution_manifest.required_fields` (13)
                  NIZAM Contract 04, `daily_dag` stage M_THABAT
Phase:            R3_THABAT

WHY TWO RECORDS AND NOT ONE
The two contracts describe different grains. The receipt is per RUN; the
manifest is per ACTION. Merging them would force either a receipt repeated for
every action or a manifest flattened into parallel lists that can silently fall
out of alignment. They are kept separate and joined on `run_id`, which appears
once on the receipt and once per manifest as the join key. Nothing else is
duplicated: the receipt's `actions_attempted`, `actions_verified` and
`blocked_actions` are DERIVED from the manifests at assembly time, never
authored by hand, so they cannot disagree with them.

RUN IDENTITY IS DERIVED, NEVER RANDOM
`run_id` is `<cairo_date>/<slot>`. A second invocation for the same Cairo day
and slot produces the SAME id, which is what makes duplicate detection and the
13:00 reconciliation possible at all: Contract 04 forbids regenerating a full
second daily plan and forbids duplicate calendar, Drive or GitHub writes. A
timestamp-based or random id would make every rerun look like new work.

READBACK IS THE ONLY PROOF A WRITE LANDED
Contract 04 C04-T05: when a write succeeds but readback fails, the receipt is
FAILED or SYNC_PENDING and never OK. A returned success is not evidence. This
module refuses to assemble an OK receipt in that case rather than trusting the
caller to remember.

No clock, no filesystem, no network. Every instant and every observation is
supplied by the caller so a receipt can be replayed and diffed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

MILLIUNITS_PER_EGP = 1000

_CAIRO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLOT = re.compile(r"^[a-z0-9_]{3,40}$")
_ACTION_ID = re.compile(r"^[a-z0-9_]{3,60}$")
_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ReceiptStatus(str, Enum):
    """Terminal state of a run. Never inferred from a lack of errors."""

    OK = "OK"
    SYNC_PENDING = "SYNC_PENDING"
    FAILED = "FAILED"


class ActionOutcome(str, Enum):
    """What became of one action."""

    VERIFIED = "verified"
    #: Executed, the call returned success, readback has NOT confirmed it.
    AWAITING_READBACK = "awaiting_readback"
    FAILED = "failed"
    #: Refused before execution. Never counted as attempted.
    BLOCKED = "blocked"


class AutonomyClass(str, Enum):
    """Contract 01 `autonomy_classes`, transcribed."""

    CLASS_A = "class_A"
    CLASS_B = "class_B"
    CLASS_C = "class_C"


#: Contract 01 class_C is human-only. No autonomous run may carry one.
_FORBIDDEN_AUTONOMY = frozenset({AutonomyClass.CLASS_C})


#: The privacy classification vocabulary, transcribed from the repository's own
#: authority: `NIZAM__system/schemas/agent_message.schema.json`, property
#: `privacy_class`. That schema is enforced elsewhere in this repository by
#: `tests/test_agent_message_schema.py::test_privacy_class_enum_enforced`, which
#: proves the value "public" is rejected.
#:
#: Transcribed rather than imported because this package must import cleanly from
#: two different roots and may not depend on a repository-relative schema path at
#: import time. `test_run_record.py` closes that loop: when the schema file IS
#: reachable it asserts this tuple still matches it, so a transcription that
#: drifts from its source fails the suite rather than rotting quietly.
#:
#: Ordered most sensitive first. The schema's own rule is that an artifact takes
#: the tier of the MOST sensitive field in its payload, so ordering is meaningful
#: and not cosmetic.
PRIVACY_CLASSES = (
    "strict_local_maximum",
    "strict_local",
    "review_before_commit",
    "private_github",
    "mirror_sanitized",
)
_PRIVACY_CLASSES = frozenset(PRIVACY_CLASSES)


class VerificationMethod(str, Enum):
    DRIVE_READBACK_SHA256 = "drive_readback_sha256"
    DRIVE_READBACK_BYTES = "drive_readback_bytes"
    CALENDAR_EVENT_REFETCH = "calendar_event_refetch"
    REPOSITORY_GATE = "repository_gate"
    FOCUSED_TEST = "focused_test"
    #: A read-only action produces no external effect to read back.
    NOT_APPLICABLE_READ_ONLY = "not_applicable_read_only"


_EXACT_MATCH_METHODS = frozenset({
    VerificationMethod.DRIVE_READBACK_SHA256,
    VerificationMethod.DRIVE_READBACK_BYTES,
})


class ReceiptError(ValueError):
    """A record that would misrepresent what happened is refused, not fixed."""


def _reject_floats(value: Any, where: str) -> None:
    """Money is integer milliunits. A float anywhere in a record is a defect.

    Checked structurally rather than by naming convention, because the defect
    this prevents is a rounded monetary value reaching a persisted receipt.
    """
    if isinstance(value, float):
        raise ReceiptError(
            f"float found at {where}; money is integer milliunits "
            f"(1 EGP = {MILLIUNITS_PER_EGP}) and no field may be floating point"
        )
    if isinstance(value, Mapping):
        for key, sub in value.items():
            _reject_floats(sub, f"{where}.{key}")
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, sub in enumerate(value):
            _reject_floats(sub, f"{where}[{index}]")


def build_run_id(cairo_date: str, slot: str) -> str:
    """`<cairo_date>/<slot>`, derived so a rerun collides on purpose."""
    if not _CAIRO_DATE.match(cairo_date):
        raise ReceiptError(f"cairo_date must be YYYY-MM-DD, got {cairo_date!r}")
    if not _SLOT.match(slot):
        raise ReceiptError(f"slot must be lower_snake_case, got {slot!r}")
    return f"{cairo_date}/{slot}"


def cairo_date_of(run_id: str) -> str:
    """The Cairo day a run belongs to. The run-once guard keys on this."""
    head, sep, _tail = run_id.partition("/")
    if not sep or not _CAIRO_DATE.match(head):
        raise ReceiptError(f"malformed run_id: {run_id!r}")
    return head


@dataclass(frozen=True)
class Verification:
    """Contract 04 `execution_manifest.verification`.

    `confirmed` is not a field the caller may simply assert for an exact-match
    method: it is derived from expected vs observed, so 'the API said OK' can
    never be recorded as verified.
    """

    method: VerificationMethod
    expected: str | None
    observed: str | None
    detail: str

    @property
    def confirmed(self) -> bool:
        if self.method is VerificationMethod.NOT_APPLICABLE_READ_ONLY:
            return True
        if self.method in _EXACT_MATCH_METHODS:
            return bool(
                self.expected
                and self.observed
                and self.expected == self.observed
            )
        # Non-exact methods still require an observation to exist. Absence is
        # never read as a positive fact.
        return bool(self.observed)


@dataclass(frozen=True)
class ActionManifest:
    """Contract 04 `execution_manifest`: all 13 required fields, one action."""

    run_id: str
    action_id: str
    action: str
    owning_contract: str
    reason: str
    evidence: tuple[str, ...]
    affected_scope: str
    risk: str
    rollback_or_reversal: str
    verification: Verification
    privacy_class: str
    authorization_basis: AutonomyClass
    expected_outcome: str
    outcome: ActionOutcome

    def __post_init__(self) -> None:
        cairo_date_of(self.run_id)
        if not _ACTION_ID.match(self.action_id):
            raise ReceiptError(
                f"action_id must be lower_snake_case, got {self.action_id!r}"
            )
        for name in (
            "action", "owning_contract", "reason", "affected_scope", "risk",
            "rollback_or_reversal", "privacy_class", "expected_outcome",
        ):
            if not str(getattr(self, name)).strip():
                raise ReceiptError(f"{name} must not be empty on {self.action_id}")
        if self.privacy_class not in _PRIVACY_CLASSES:
            raise ReceiptError(
                f"{self.action_id} declares privacy_class "
                f"{self.privacy_class!r}, which is not in the governing "
                f"vocabulary {list(PRIVACY_CLASSES)}. An invented class cannot "
                "be enforced against an egress class, so it is refused rather "
                "than stored."
            )
        if self.authorization_basis in _FORBIDDEN_AUTONOMY:
            raise ReceiptError(
                f"{self.action_id} claims {self.authorization_basis.value}, "
                "which Contract 01 reserves to a human; an autonomous run may "
                "never record one as its authorization basis"
            )
        if self.outcome is ActionOutcome.VERIFIED and not self.verification.confirmed:
            raise ReceiptError(
                f"{self.action_id} claims VERIFIED but its verification is not "
                f"confirmed (method={self.verification.method.value}); a "
                "returned success is not evidence that a write landed"
            )
        if self.outcome is ActionOutcome.BLOCKED and self.verification.confirmed:
            if self.verification.method is not VerificationMethod.NOT_APPLICABLE_READ_ONLY:
                raise ReceiptError(
                    f"{self.action_id} is BLOCKED yet carries a confirmed "
                    "verification; a refused action cannot have been verified"
                )
        _reject_floats(self.evidence, f"{self.action_id}.evidence")

    @property
    def attempted(self) -> bool:
        """Blocked actions were refused before execution, so never attempted."""
        return self.outcome is not ActionOutcome.BLOCKED


@dataclass(frozen=True)
class RunReceipt:
    """Contract 01 `required_runtime_receipt`: all 13 fields, one run.

    Assemble with `assemble_receipt`; the derived count fields are not meant to
    be authored by hand.
    """

    run_id: str
    timestamp: str
    contract_versions: Mapping[str, str]
    sukoon_state: str
    objective_recovery_percent: int | None
    himayah_classification: str
    modules_invoked: tuple[str, ...]
    actions_attempted: tuple[str, ...]
    actions_verified: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    evidence_summary: tuple[str, ...]
    open_loops: tuple[str, ...]
    next_action: str
    status: ReceiptStatus
    reconciles_run_id: str | None = None

    @property
    def cairo_date(self) -> str:
        return cairo_date_of(self.run_id)


def assemble_receipt(
    *,
    run_id: str,
    timestamp: str,
    contract_versions: Mapping[str, str],
    sukoon_state: str,
    objective_recovery_percent: int | None,
    himayah_classification: str,
    modules_invoked: Sequence[str],
    manifests: Sequence[ActionManifest],
    evidence_summary: Sequence[str],
    open_loops: Sequence[str],
    next_action: str,
    reconciles_run_id: str | None = None,
) -> RunReceipt:
    """Derive the receipt from the manifests, refusing an untruthful one.

    Refusals, each one a contract requirement rather than a style preference:

    * a manifest belonging to a different run cannot be counted in this one;
    * an unverified write forces SYNC_PENDING, a failure forces FAILED, and
      neither may be reported OK (Contract 04 C04-T05);
    * a run that did not fully succeed must carry at least one open loop, so a
      failure cannot be closed silently;
    * `objective_recovery_percent` may be None and None is NOT zero: absence is
      preserved, never imputed;
    * a reconciliation run must name the run it reconciles and must belong to
      the same Cairo day.
    """
    cairo_date_of(run_id)
    if not _UTC_TIMESTAMP.match(timestamp):
        raise ReceiptError(
            f"timestamp must be UTC ...T..:..:..Z, got {timestamp!r}"
        )
    if not contract_versions:
        raise ReceiptError("contract_versions must name every contract relied on")
    if not str(next_action).strip():
        raise ReceiptError("next_action must not be empty; a run always leaves one")
    if objective_recovery_percent is not None:
        if isinstance(objective_recovery_percent, bool) or not isinstance(
            objective_recovery_percent, int
        ):
            raise ReceiptError("objective_recovery_percent must be int or None")
        if not 0 <= objective_recovery_percent <= 100:
            raise ReceiptError(
                f"objective_recovery_percent out of range: "
                f"{objective_recovery_percent}"
            )
    if himayah_classification not in _PRIVACY_CLASSES:
        raise ReceiptError(
            f"himayah_classification {himayah_classification!r} is not in the "
            f"governing vocabulary {list(PRIVACY_CLASSES)}"
        )
    if reconciles_run_id is not None:
        if cairo_date_of(reconciles_run_id) != cairo_date_of(run_id):
            raise ReceiptError(
                "a reconciliation run must reconcile the same Cairo day: "
                f"{reconciles_run_id!r} vs {run_id!r}"
            )
        if reconciles_run_id == run_id:
            raise ReceiptError("a run cannot reconcile itself")

    seen: set[str] = set()
    for manifest in manifests:
        if manifest.run_id != run_id:
            raise ReceiptError(
                f"manifest {manifest.action_id} belongs to {manifest.run_id!r}, "
                f"not {run_id!r}"
            )
        if manifest.action_id in seen:
            raise ReceiptError(f"duplicate action_id: {manifest.action_id}")
        seen.add(manifest.action_id)

    attempted = tuple(m.action_id for m in manifests if m.attempted)
    verified = tuple(
        m.action_id for m in manifests if m.outcome is ActionOutcome.VERIFIED
    )
    blocked = tuple(
        m.action_id for m in manifests if m.outcome is ActionOutcome.BLOCKED
    )
    failed = tuple(
        m.action_id for m in manifests if m.outcome is ActionOutcome.FAILED
    )
    awaiting = tuple(
        m.action_id
        for m in manifests
        if m.outcome is ActionOutcome.AWAITING_READBACK
    )

    if failed:
        status = ReceiptStatus.FAILED
    elif awaiting:
        status = ReceiptStatus.SYNC_PENDING
    else:
        status = ReceiptStatus.OK

    if status is not ReceiptStatus.OK and not open_loops:
        raise ReceiptError(
            f"status {status.value} with no open loop; failed "
            f"{list(failed)} and awaiting readback {list(awaiting)} may not be "
            "closed silently"
        )

    _reject_floats(dict(contract_versions), "contract_versions")
    _reject_floats(list(evidence_summary), "evidence_summary")

    return RunReceipt(
        run_id=run_id,
        timestamp=timestamp,
        contract_versions=MappingProxyType(dict(contract_versions)),
        sukoon_state=sukoon_state,
        objective_recovery_percent=objective_recovery_percent,
        himayah_classification=himayah_classification,
        modules_invoked=tuple(modules_invoked),
        actions_attempted=attempted,
        actions_verified=verified,
        blocked_actions=blocked,
        evidence_summary=tuple(evidence_summary),
        open_loops=tuple(open_loops),
        next_action=next_action,
        status=status,
        reconciles_run_id=reconciles_run_id,
    )


#: Contract 01 `required_runtime_receipt`, transcribed in order. Used to prove
#: the serialised form carries every required field under its contract name.
REQUIRED_RECEIPT_FIELDS = (
    "run_id", "timestamp", "contract_versions", "sukoon_state",
    "objective_recovery_percent", "himayah_classification", "modules_invoked",
    "actions_attempted", "actions_verified", "blocked_actions",
    "evidence_summary", "open_loops", "next_action",
)

#: Contract 04 `execution_manifest.required_fields`, transcribed in order.
REQUIRED_MANIFEST_FIELDS = (
    "run_id", "action_id", "action", "owning_contract", "reason", "evidence",
    "affected_scope", "risk", "rollback_or_reversal", "verification",
    "privacy_class", "authorization_basis", "expected_outcome",
)


def manifest_to_dict(manifest: ActionManifest) -> dict[str, Any]:
    return {
        "run_id": manifest.run_id,
        "action_id": manifest.action_id,
        "action": manifest.action,
        "owning_contract": manifest.owning_contract,
        "reason": manifest.reason,
        "evidence": list(manifest.evidence),
        "affected_scope": manifest.affected_scope,
        "risk": manifest.risk,
        "rollback_or_reversal": manifest.rollback_or_reversal,
        "verification": {
            "method": manifest.verification.method.value,
            "expected": manifest.verification.expected,
            "observed": manifest.verification.observed,
            "confirmed": manifest.verification.confirmed,
            "detail": manifest.verification.detail,
        },
        "privacy_class": manifest.privacy_class,
        "authorization_basis": manifest.authorization_basis.value,
        "expected_outcome": manifest.expected_outcome,
        "outcome": manifest.outcome.value,
    }


def receipt_to_dict(
    receipt: RunReceipt, manifests: Sequence[ActionManifest]
) -> dict[str, Any]:
    """The persisted shape. `manifests` are nested, never flattened into the
    receipt's derived id lists, so the join key stays the only shared field."""
    for manifest in manifests:
        if manifest.run_id != receipt.run_id:
            raise ReceiptError(
                f"manifest {manifest.action_id} does not belong to "
                f"{receipt.run_id!r}"
            )
    payload = {
        "run_id": receipt.run_id,
        "timestamp": receipt.timestamp,
        "contract_versions": dict(receipt.contract_versions),
        "sukoon_state": receipt.sukoon_state,
        "objective_recovery_percent": receipt.objective_recovery_percent,
        "himayah_classification": receipt.himayah_classification,
        "modules_invoked": list(receipt.modules_invoked),
        "actions_attempted": list(receipt.actions_attempted),
        "actions_verified": list(receipt.actions_verified),
        "blocked_actions": list(receipt.blocked_actions),
        "evidence_summary": list(receipt.evidence_summary),
        "open_loops": list(receipt.open_loops),
        "next_action": receipt.next_action,
        "status": receipt.status.value,
        "reconciles_run_id": receipt.reconciles_run_id,
        "execution_manifest": [manifest_to_dict(m) for m in manifests],
    }
    _reject_floats(payload, "receipt")
    return payload
