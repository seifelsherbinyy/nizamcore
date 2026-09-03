# NIZAM Calendar Actuation Contract

**Contract ID:** NIZAM-CALENDAR-ACTUATION-001
**Version:** 1.0.0
**Owning contract:** NIZAM Contract 01 (Constitution & Governance) `autonomy_classes`; NIZAM Contract 04 (Daily Autonomous Orchestration & Actuation) `calendar_policy`
**Phase:** R5 — controlled calendar actuation
**Status:** Active
**Classification:** private_github
**Generated:** 2026-09-03


## Purpose

Calendar actuation had no governing contract of its own. Two authorities said different things:

- Contract 01 `autonomy_classes.class_B` (`standing_authorized_execution`) lists
  `autonomous_calendar_event_create_update_move_delete`, and Contract 04 `calendar_policy`
  sets `standing_authorization: true` over ten named operations.
- A derived artifact of the health-intelligence layer still asserted
  `"Calendar writes require explicit human approval."` and
  `calendar_write_policy == "proposal_only_until_human_approval"`.

Contract 04 `github_policy.current_transition_rule` prescribes the resolution: while an older
stricter active rule stands, the stricter rule wins, and the implementation team must amend or
supersede it before enabling autonomous action. This contract is that amendment. It is a
reconciliation of a derived artifact to its governing contracts, not a relaxation of an invariant:
every human-only field named in Contract 01 `class_C` remains human-only here, and every
Contract 04 safeguard is carried forward and tightened with explicit bounds.


## Supersession

This contract supersedes, in the health-intelligence sync layer:

| Superseded statement | Site | Replaced by |
|---|---|---|
| `"Calendar writes require explicit human approval."` | `sync/index_builder.py` `hard_rules` | Rules 1–3 below |
| `calendar_write_policy = "proposal_only_until_human_approval"` | `sync/index_builder.py` `build_daily_intelligence_index` | `autonomous_within_scheduling_policy_approval_fields_human_only` |
| `"Calendar writes are proposal-only."` | `sync/artifact_builder.py` module docstring | Rule 1 below; the second clause of that docstring ("nothing here can mark one approved") remains in force |

Nothing else about the calendar boundary changes. In particular the LLM boundary
(`approve a calendar write` remains in `llm_boundary.may_not`) and the `human_only_gates`
list (`Calendar Approved`, `final calendar approval`) are unchanged and remain enforced.


## Non-Negotiable Rules

1. **Actuation is autonomous; approval is not.** NIZAM may create, update, move/reschedule,
   add a reminder, resolve an overlap, create a focus block, create a recovery block, protect a
   sleep window, schedule a workout, and perform a bounded delete-replace, without asking.
   NIZAM may never approve a calendar write, and may never claim it did.
2. **Human-only fields stay human-only.** `calendar_approved`, `approved_by_human`,
   `human_confirmed`, `operator_confirmed_externalize` are Contract 01 `class_C`. NIZAM never
   sets one true, never reads its own write as an approval, and never reports a human-only field
   as personally approved.
3. **Standing authorization is not unlimited authority.** Every actuation is Contract 01
   `class_B` and therefore requires a complete Contract 04 execution manifest, including
   `rollback_or_reversal`, before the write is attempted.
4. **Idempotency key required for every generated event.** The key is deterministic in the
   material identity of the intent, not in wall-clock time.
5. **Multiple matching idempotency keys fail closed.** Two or more events matching one key is
   an unresolved-identity condition: read no further conclusion, write nothing, delete nothing,
   record the ambiguity.
6. **Missing calendar data is never free time.** A failed, partial, unauthorized, or stale read of
   the target window blocks the write. Absence of events is only free time when the read
   succeeded and was fresh.
7. **A conflict check precedes every write.** The target window is read and evaluated first.
   When a NIZAM event conflicts with a human-authored or human-approved event, the NIZAM
   event moves. The human event is never moved, shortened, or removed to make room.
8. **Past events are the record, not the plan.** Actuation is confined to the active planning
   horizon. NIZAM never mutates or deletes an event whose window has already ended.
9. **HIMAYAH classifies before egress.** Event titles, descriptions, and locations are egress.
   `strict_local` and `strict_local_maximum` content must not be written into a calendar event;
   a neutral placeholder title is used instead.
10. **The 13:00 reconciliation run never duplicates an action.** Contract 04
    `reconciliation_1300.forbidden` includes `duplicate_calendar_actions`. Reconciliation may
    only retry a stage that failed, and retry resolves through the idempotency key.


## Autonomous Operations and Their Bounds

| Operation | Class | Bound |
|---|---|---|
| `create` | B | Idempotency key required; conflict check first; horizon-bounded |
| `update` | B | Only fields NIZAM owns; never a human-only approval field |
| `move` / reschedule | B | NIZAM events freely; a human event is never moved |
| `add_reminder` | B | Additive only |
| `resolve_overlap` | B | Resolve by moving the NIZAM side |
| `create_focus_block` | B | Horizon-bounded; must not overlap a protected sleep window |
| `create_recovery_block` | B | Permitted in every SUKOON mode, including RECOVERY |
| `protect_sleep_window` | B | May block, never shorten, an existing human event |
| `schedule_workout` | B | Requires a deterministic engine recommendation as evidence |
| `delete` | B, bounded | Only under Bounded Delete-Replace below |
| set a human-only approval field | C | Prohibited without an explicit human act |


## Bounded Delete-Replace

`delete` is the only destructive calendar operation, and it is permitted only as the first half of
a replace. All seven conditions must hold; any one failing blocks the delete.

1. **Ownership.** The event carries a NIZAM idempotency key recorded in THABAT. NIZAM
   deletes only what NIZAM created. An event with no NIZAM key is human-authored or
   third-party and is out of scope entirely.
2. **Unambiguous identity.** Exactly one event matches the key. Zero means nothing to delete;
   two or more fails closed under Rule 5.
3. **Replacement first.** The replacement intent is computed and validated *before* the delete
   is issued. A delete is never issued speculatively.
4. **Rollback captured.** The full payload of the event to be deleted is captured and persisted
   before deletion, so the original can be recreated verbatim.
5. **Horizon.** The event window has not yet ended.
6. **No human approval attached.** The event carries no human-only approval field set true.
7. **Per-run cap.** A configured maximum number of destructive operations per run. Exceeding
   the cap fails the stage; it never proceeds partially and never raises its own cap.

If the replacement write fails after a successful delete, the captured payload is restored and the
run receipt records `FAILED`, never `OK`.


## Rollback

Rollback is per-action and does not require editing any canonical file.

1. Read the THABAT run receipt for the run being rolled back.
2. For each created event, delete by idempotency key (single match only).
3. For each updated or moved event, restore the captured prior payload.
4. For each deleted-and-replaced event, delete the replacement and recreate the captured original.
5. Read back every reverted event and confirm the observed state matches the intended state.
6. Record the rollback as its own run with its own receipt. A rollback that cannot be verified is
   reported as an open loop, not as a completed rollback.


## Acceptance Criteria

| ID | Given | Expect |
|---|---|---|
| CAL-T01 | The same event intent is generated twice | One event exists; the second attempt reports skip-already-verified |
| CAL-T02 | Two events match one idempotency key | Fail closed; no create, no update, no delete |
| CAL-T03 | The target-window read fails | No write; absence is not treated as free time |
| CAL-T04 | The target-window read is stale | No write; staleness is recorded |
| CAL-T05 | A NIZAM event conflicts with a human event | The NIZAM event moves; the human event is byte-identical afterwards |
| CAL-T06 | A delete is requested for an event with no NIZAM key | Blocked as `class_C` |
| CAL-T07 | A delete is requested for an event whose window has ended | Blocked by the horizon rule |
| CAL-T08 | A delete is requested and the replacement intent is invalid | Nothing is deleted |
| CAL-T09 | The replacement write fails after a successful delete | The original is restored; the receipt is `FAILED` |
| CAL-T10 | Destructive operations exceed the per-run cap | The stage fails; the cap is not raised |
| CAL-T11 | An execution manifest omits `rollback_or_reversal` | The write is refused |
| CAL-T12 | Any code path attempts to set a human-only approval field | Refused, and the attempt is recorded |
| CAL-T13 | An event title would carry `strict_local` content | A neutral placeholder title is written instead |
| CAL-T14 | The primary run succeeded and 13:00 reconciliation runs | No calendar action is repeated |
| CAL-T15 | SUKOON RECOVERY mode is active | Recovery-block creation is permitted; optimization actuation is not |


## References

- NIZAM Contract 01 — Constitution & Governance: `autonomy_classes`, `T02_HIMAYAH_BEFORE_EGRESS`, `required_runtime_receipt`
- NIZAM Contract 04 — Daily Autonomous Orchestration & Actuation: `calendar_policy`, `execution_manifest`, `reconciliation_1300`, `github_policy.current_transition_rule`, acceptance tests C04-T04
- NIZAM Contract 05 — Verification, Promotion & Self-Evolution: `P4_CLASS_B` promotion gate, `class_B_idempotency_passes`, `rollback_or_recovery_test_passes`
- `NIZAM__system/governor/adaptive/calendar_idempotency.py` — deterministic key derivation and `HUMAN_ONLY_FIELDS`
- `NIZAM__system/docs/KNOWLEDGE_RETRIEVAL_CONTRACT.md` — HIMAYAH classification gate
