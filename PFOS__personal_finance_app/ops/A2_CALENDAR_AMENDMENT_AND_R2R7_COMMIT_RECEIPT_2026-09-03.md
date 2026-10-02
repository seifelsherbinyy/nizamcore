# A2 — Calendar actuation amendment and the R2-R7 commit series

**Date:** 2026-09-03
**Owning authority:** `.kiro/steering/two-agent-vps.md` §6a (cross-repository write authorisation);
NIZAM Contract 01 `autonomy_classes`; NIZAM Contract 04 `calendar_policy` and
`github_policy.current_transition_rule`
**Phase:** R2-R7 preparation
**Status:** commits landed and verified; nothing pushed

---

## 1. Owner direction this receipt discharges

The owner gave six governing decisions in chat on 2026-09-03 and instructed that non-blocking
implementation choices inside those bounds must not be returned for approval:

1. Amend the governing contract to permit autonomous calendar create / update / reschedule and
   bounded delete-replace, preserving idempotency, rollback, conflict checks, HIMAYAH and every
   human-only approval field. R5 must reach real controlled actuation.
2. SUKOON red uses the reduced BOUNDED agenda. Red never becomes FULL from recovery alone.
   Crisis and immediate-safety still override everything.
3. Use the main Hermes profile and implement the three remediations. Do not add the governor to the
   ingress profile as another uncoordinated writer.
4. Start on strong keyless weather and news sources immediately while inspecting already-authorized
   credential and configuration references in parallel. Never print a secret.
5. Telegram is read-only diagnostics only and must not block the governor rollout.
6. Cadence: 10:00 Cairo heavier refresh, about 11:40 volatile refresh, 12:00 full governor,
   13:00 reconciliation only.

Plus: make the seven files classified `REQUIRED_BY_R2_R7` reproducible in Git, commit the
tamper-proven SUKOON and sleep work once the regression gate is green, and correct the stale
open decision about the Drive retrieval entrypoint in the architecture documentation.

---

## 2. The calendar amendment, and why it is a reconciliation rather than a relaxation

Two authorities disagreed, and the disagreement was the whole blocker.

- Contract 01 `autonomy_classes.class_B` (`standing_authorized_execution`) already lists
  `autonomous_calendar_event_create_update_move_delete`, and `class_C` (human-only) lists
  `mark_human_only_fields_as_true`. Actuation and approval were already separated at the
  constitutional layer.
- Contract 04 `calendar_policy` already sets `standing_authorization: true` over ten named
  operations with four safeguards.
- A derived artifact of the health-intelligence layer still asserted that calendar writes require
  explicit human approval. Under Contract 04's transition rule the stricter active rule wins until
  the implementation team amends or supersedes it.

**The governing contract for that layer did not exist.** Its identifier is referenced in code and in
one migration, but no contract document exists anywhere on the host or in either repository. The
correct action was therefore to author the missing NIZAM-derived contract, not to edit a rule with no
parent. That is `NIZAM-CALENDAR-ACTUATION-001 v1.0.0`, committed as
`NIZAM__system/docs/CALENDAR_ACTUATION_CONTRACT.md`.

Everything the owner named as preserved is preserved and given an explicit bound:

- Bounded delete-replace requires **all seven** of: NIZAM idempotency-key ownership; exactly one
  matching event; the replacement validated before the delete is issued; the deleted payload
  captured for rollback; an unexpired window; no human approval field attached; and a per-run
  destructive-operation cap that fails the stage rather than raising itself.
- Idempotency key on every generated event; multiple matching keys fail closed.
- A conflict check precedes every write. When a NIZAM event conflicts with a human event, the NIZAM
  event moves. The human event is never moved, shortened or removed.
- Missing calendar data is never read as free time.
- HIMAYAH classifies before egress, so strict-local content never reaches an event title.
- The four human-only approval fields are never self-set and never reported as personally approved.
- The 13:00 reconciliation run never repeats a calendar action.

Fifteen acceptance criteria, CAL-T01 through CAL-T15, plus a per-action rollback procedure that
requires no canonical file edit.

### 2a. Reconciling the derived layer

Seven superseded statements were found in the health-intelligence sync layer, not one. All seven were
reconciled by a fail-closed patcher that refuses to write unless every pattern matches exactly once,
and that backs up each touched file first using the host's existing pre-change convention:

| Site | Was | Now |
|---|---|---|
| hard rules list | calendar writes require explicit human approval | three precise rules: autonomous actuation under the new contract; approval fields never self-set; missing data never read as free time |
| daily-intelligence index write policy | proposal only until human approval | autonomous within scheduling policy, approval fields human-only, plus the contract identifier |
| source registry access mode | read; writes require human approval | read-write autonomous under the new contract |
| artifact module doctrine line | calendar writes are proposal-only | autonomous actuation, but nothing there can mark an approval field approved |
| daily-plan builder docstring | fields stay unwritten and no step can advance them | the human-only approval fields stay false because no step can advance one |
| plan artifact reason | human approval required | actuation not yet run |
| the test pinning that reason | asserted the old literal | asserts the new literal |

**Not changed, deliberately.** The LLM boundary still forbids the model from approving a calendar
write. The human-only gates list still names the Calendar Approved field and final calendar approval.
The plan artifact still starts unwritten with approval false. Autonomy of actuation did not become
autonomy of approval.

### 2b. Verification of the amendment

| Check | Result |
|---|---|
| Health-stack baseline before | 223 passed |
| Health-stack after amendment | **239 passed** (+16 new tests, net coverage up) |
| Tamper harness, 12 cases | **12 DETECTED, 0 NOT DETECTED, 0 INCONCLUSIVE** |
| Baseline green before and after every tamper case | yes, and every file restored byte-identically |

The retired test was not weakened. Its human-only-gate assertions were kept verbatim, its policy
literal was updated, and two stronger tests now cover the same ground plus the contract identifier.
Tamper cases include reverting each of the seven edits, deleting each new rule, pre-approving the
plan artifact, and letting the model approve a write. All are caught.

---

## 3. A finding that changed the commit plan: the other repository is public

Before staging, `two-agent-vps.md` §6a was re-read in full. It states that R24 is untouched by the
authorisation and that both repositories are public. That was verified independently through the
GitHub API rather than assumed: the repository reports `private: false` and `visibility: public`.

A value-suppressing scan was therefore run over every candidate file. It reports pattern name, file,
line and match **length** only, so running the scan cannot itself leak a secret. It found real
deployment particulars, which forced three redactions and two exclusions.

**Redacted, behaviour preserved:**

- The embedding port module's model-cache constant was a hardcoded absolute host path, and was
  referenced nowhere in the tree. It now reads from an environment variable and otherwise stays
  unset.
- The backfill module inserted a hardcoded absolute home path onto the import path. It now derives
  the repository root from its own location, which is exactly equivalent when run from the tree.
- The retrieval contract named a container, a volume, a network, a bind address and port mapping, a
  database name, an MCP server name and an MCP host path. Each is now a named placeholder. The
  architecture, the role separation and the rollback steps are unchanged.

**Excluded and now ignored so they cannot be added by accident:**

- Two deployment receipts. A receipt whose particulars are removed is no longer a receipt, so these
  stay local operational records.
- Two benchmark result files. Their per-query records quote real query text and real corpus document
  paths from the owner's private corpus. The benchmark harness is committed; its outputs are not.

The host's pre-change backup convention is now ignored too, because those files hold the text as it
was **before** redaction.

No secret, no credential, no address, no container name, no host path and no private corpus content
is present in any committed file. Re-scanning all 35 committed files afterwards returns zero hits in
every particulars category; the residual hits are long identifiers, one synthetic money fixture in
integer milliunits, a bytes-to-megabytes divisor, and one public upstream project URL, each inspected
individually.

---

## 4. Commits landed

Five narrow commits on the other repository, on top of the prior tip:

| # | Subject | Files |
|---|---|---|
| 1 | make the SUKOON capacity state a ceiling recovery cannot lift | 2 |
| 2 | add the wake-obligation half of the sleep model | 2 |
| 3 | author NIZAM-CALENDAR-ACTUATION-001 | 1 |
| 4 | track the retrieval layer, redacted for a public repository | 25 |
| 5 | replace the agent stub with the Hermes adapter | 5 |

**Nothing was pushed.** Push remains a separate external act, and no push credential exists on the
host in any case.

### 4a. Section 6a reconciliation for this series

- Commit 5 is **already inside** §6a purpose 1. That purpose exists precisely because the relay
  coordinator ran the full pipeline and then called a stub returning a canned string; this commit
  replaces that stub with a real client. No widening is needed. The runtime standby gate is
  untouched, and the new path is gated on a protected live flag whose absence preserves the existing
  deterministic behaviour exactly.
- Commits 1 and 2 are inside the **fifth** purpose recorded in the A1 receipt §7, which admits the
  additive non-actuating adaptive package and its tests.
- Commit 3 requires a **sixth** purpose: authoring a missing NIZAM-derived governing contract into
  the docs tree when a requested area has none. Owner direction 1 of 2026-09-03 supplies it in
  writing.
- Commit 4 requires a **seventh** purpose: making an already-deployed subsystem reproducible in Git,
  redacted to R24. Owner direction of 2026-09-03 supplies it in writing.

Both new purposes are narrow. Neither authorizes restructuring that repository, and neither grants
the governor autonomous commit authority on any cadence. Contract 04
`github_policy.desired_standing_authorization` stays unreconciled for autonomous push.

### 4b. Preserved untouched

Three working-tree items were left exactly as found, because they are not this work:

- A health-system README modification and an infrastructure note, both in the strictest-privacy
  health tree. They embed a wearable account identifier, the owner's real name and a public webhook
  hostname, so they are ineligible for a public repository regardless of authorisation.
- An unrelated recovery-system README modification.
- Five pre-change backup files, which are protected local rollback anchors.

### 4c. Floors that must not regress

`two-agent-vps.md` §6a records a floor of 143 test functions, of which 29 are relay tests. Measured
after this series: **295 total, 41 relay**. Both rose.

---

## 5. Corrections to my own earlier claims

Recorded because an uncorrected false finding is worse than an open question.

1. **The Drive retrieval entrypoint artifact exists.** It was reported absent across two sessions.
   The probe used a command that takes a file identifier and was handed a path string, so it
   returned not-found for any input; the overview command then appeared to confirm the absence
   because it folds loose files into a size total and never lists them. The artifact is present, is
   first in the retrieval order, and is refreshed daily by the existing pre-noon job. R3 extends it
   and must not recreate it. **An absence proven only by a tool used outside its contract is not a
   proven absence.**
2. **A scheduler already exists.** Hermes ships a cron subsystem with its own job store. The earlier
   claim that none existed was wrong.
3. **A full read-write Calendar credential already exists.** The earlier claim that none existed was
   wrong.
4. **The retrieval layer was never a committed asset.** It was entirely untracked until commit 4.
5. **The ingress writer concern was about a profile, not a directory.** The absence of a directory
   with that name did not mean the profile did not exist; it is the only profile whose gateway runs.

The architecture document's open-decision section has been rewritten as a resolved register of
eleven decisions with an authority column, and its retrieval-entrypoint step now states the proven
position instead of the unproven one.

---

## 6. What is still not done

- **R2 activation has not happened.** The main profile still has an empty timezone value, no MCP
  wiring, and a job that has not ticked since 2026-08-31. The no-daemon tick model is a decision, not
  yet an observation.
- **R5 actuation has not run.** The contract now permits it and the derived layer no longer forbids
  it. No calendar write has been attempted.
- **Weather, news and location intelligence do not exist yet.** Greenfield.
- **Telegram delivery is still broken.** Read-only diagnostics only.
- **No push.** Seven commits are unpushed on the other repository.
- The five NIZAM governor contracts are still tracked in neither repository.
