# Adaptive Governor R1_FIXTURES — implementation and verification receipt

> Owning authority: `.kiro/steering/two-agent-vps.md` §6/§6a, `AGENTS`, and the five owner-supplied
> NIZAM contracts (01–05, `status: proposed_for_implementation`) plus the three dropzone directives.
> Status: **R0/R1 deterministic slice implemented and verified. NOT committed. NOT activated.**
> This receipt records observed facts. It grants no authority and closes no human gate.

## 1. Authorization basis, stated precisely

The owner instructed, in chat on 2026-09-03, to convert the supplied specifications into a production
Hermes/NIZAM VPS implementation, following Research → Plan → Implement → Verify → Tamper-test →
Smoke-test → Record, using only already-provisioned credentials.

That instruction is the basis for the work below. It does **not** by itself widen two standing limits,
and this receipt does not treat it as if it did:

- `two-agent-vps.md` §6a grants `nizamcore` write/commit/push authority for **four enumerated purposes
  only** and states in terms: *"This is not a licence to restructure that repository."* Standing up a
  daily-governor pipeline is not one of the four.
- `ops/A0_AUTHORIZATION_RECEIPT_2026-09-02.md` scopes its closure to **one** workstream, Hermes journal
  persistence, and excludes "anything outside the named journal-persistence workstream."

The supplied specs are themselves self-limiting on this point. The playbook's `R7_GITHUB_AUTONOMY`
entry requires that the "governing commit/push prohibition has been explicitly reconciled," and the
contracts repeat that "the stricter active rule wins until superseded" and that a higher-priority
prohibition must not be "merely bypassed or ignored." So the specs do **not** supersede §6a.

**Consequence, applied:** the work was confined to a new, additive, pure-logic package that performs no
I/O, holds no credential, opens no socket, and actuates nothing.

**Update, same day:** the owner then explicitly authorized committing across both repositories and the
VPS. Section 7 records that decision and is the scoped §6a reconciliation for this one addition. The
prohibitions on autonomous/standing commit authority, calendar mutation, Drive writes, and G1-G8 are
unchanged.

## 2. What was implemented

New directory only: `NIZAM__system/governor/adaptive/` in the VPS `nizamcore` checkout.
**Zero pre-existing files were modified.** 7 modules + 6 test modules + 2 package files.

| Module | Contract | Enforces |
|---|---|---|
| `evidence` | 01 | FACT/INFERENCE/ASSUMPTION/MISSING labels; 9-level authority order; refuses MISSING-with-a-value (imputation) and model-inference-as-FACT at construction |
| `sukoon_gate` | 01, 04 | recovery thresholds 40 / 67; crisis hard-override outranks any recovery reading; max 3 primary targets; stale/unknown/missing recovery can never elevate mode |
| `sleep_controller` | 03 | 10-minute default shift, 15-minute hard ceiling, 5 states; barrier associations pinned to `correlational_candidate`, never causal |
| `calendar_idempotency` | 04 | key = `nizam-{purpose}-{run_date}-{sha256[:32]}`; retry of an identical intent yields SKIP not CREATE; ambiguity fails closed; 4 human-only fields unwritable by any agent. **No network client exists in this module.** |
| `provenance` | 02 | 13 required + 8 recommended artifact metadata fields; change detection anchored on content hash (mtime alone proves nothing); refuses duplicate-name resolution; absent domain → MISSING, never empty |
| `learning_state` | 03, 05 | 7 stages, 4 causal statuses; counterevidence search mandatory before hypothesis; daily cadence may never promote durable learning (weekly only) |

Scope boundary is declared in `__init__.py`: no I/O, no sockets, no credentials, no actuators.

## 3. Verification actually run, with observed results

All commands run from the repo root on the VPS (`cd /home/<USER>/nizamcore`), python 3.14.4.

| Check | Command | Observed |
|---|---|---|
| New suite | `python3 -m pytest NIZAM__system/governor/adaptive/tests -q` | **131 passed** |
| Pre-existing suites | `python3 -m pytest NIZAM__system/governor/tests NIZAM__system/retrieval/tests -q` | **136 passed, 17 skipped, 14 subtests passed** — identical to the prior baseline, no regression |
| Combined | `python3 -m pytest NIZAM__system/governor NIZAM__system/retrieval -q` | **267 passed, 17 skipped, 14 subtests passed** |
| Composition smoke | 6 modules + 2 guard paths in one pass | **PASS**, exit 0, no I/O performed |

## 4. Tamper test — including a real defect it caught

Harness ran against a throwaway copy under `/tmp`; the real tree was never mutated, and a
post-run recursive source diff confirmed **IDENTICAL — real tree provably untouched**.

**Result: 12 of 12 gates proven real.** Each case verifies the mutation actually applied *before*
drawing a conclusion, and reports DETECTED / NOT DETECTED / INCONCLUSIVE as three distinct outcomes.

| # | Invariant broken | Suite result |
|---|---|---|
| T1 | SUKOON bounded threshold 40→20 | 3 failed — DETECTED |
| T2 | SUKOON full threshold 67→50 | 2 failed — DETECTED |
| T3 | sleep ceiling 15→30 min | 1 failed — DETECTED |
| T4 | calendar duplicate suppression → CREATE | 1 failed — DETECTED |
| T5 | rename `artifact_id` in required list | 16 failed — DETECTED |
| T6 | `model_inference` allowed to be FACT | 2 failed — DETECTED |
| T7 | daily cadence allowed to promote learning | 5 failed — DETECTED |
| T8 | drop `schema_version` from required list | 3 failed — DETECTED |
| T9 | shrink `HUMAN_ONLY_FIELDS` | 2 failed — DETECTED |
| T10 | empty-required-value check disabled | 13 failed — DETECTED |
| T11 | crisis hard-override disabled | 1 failed — DETECTED |
| T12 | `missing()` constructor removed | error — DETECTED |

### 4a. Defect found and fixed — two tautological gates

The first harness reported "all tampers detected." That claim was **false**, for two compounding
reasons, and is corrected here rather than left in the record:

1. The harness captured `$?` from a shell pipeline rather than from `pytest`, so its PASS/FAIL label
   was inverted.
2. Four of its `sed` mutations silently never matched (a trailing comment defeated a `$` anchor; one
   file had CRLF line endings; two patterns assumed type annotations that were not present). A suite
   that "passed" was therefore reported as a detected tamper when nothing had been tampered at all.

Once corrected, a genuine defect surfaced: **`test_provenance` and `test_calendar_idempotency`
were tautological.** Both built fixtures from — and parametrised over — the very constants they were
meant to police (`REQUIRED_ARTIFACT_FIELDS`, `HUMAN_ONLY_FIELDS`). Renaming or deleting a required
field shrank the test in lockstep and all 46 provenance tests still passed. Those 26 parametrised
cases proved only "the validator enforces whatever list it was handed," never "the list matches the
contract."

Fix: both test modules now restate the field lists **literally, from the contract text** (Contract 02
lines 86–108; Contract 04 `calendar_policy.safeguards`), assert set-equality and length against the
implementation, and parametrise over the literal. Four new pinning tests were added (131 vs 127).
`sleep_controller` line endings were normalised to LF for consistency.

**Generalisable lesson:** a test that derives its expectation from the subject under test is not a
gate. Tamper-testing is the only thing that distinguishes the two, and a tamper harness must prove its
mutation landed before it is allowed to report a result.

## 5. What was NOT done

- **No push, in any repository.** Two commits were made, under the owner authorization recorded in
  section 7 and scoped exactly as stated there: `nizamfinancialapp` `ba43912` (four ops documents)
  and `nizamcore` `c3a4e65` (the adaptive package only, 15 files). Neither was pushed.
- No calendar event created, updated, moved, or deleted.
- No Drive write. the `47_NIZAM` BOOTSTRAP manifest was **not** authored (Contract 02's mandatory
  `retrieval_entrypoint` remains absent — see §6).
- No scheduler, cron entry, systemd unit, or timer created. The 12:00/13:00 governor does not exist.
- No credential read, printed, copied, relocated, or minted. No `.env`, `.env.mcp`, or token file touched.
- No LLM, weather, or news API call. No network egress from the new package — it has none.
- Nothing in `ops/DEPLOYMENT_CONTROL.md` executed, tested, substituted into, or marked complete.
- No G1–G8 gate performed. No existing user file reset, reverted, or overwritten.

### 5a. Pre-existing working-tree state that is NOT from this work

The `nizamcore` working tree also carries modifications and untracked files from earlier sessions:
health-system documentation, a relay coordinator module, recovery-system documentation, the retrieval
package, relay adapter and owner-memory modules with their tests, a knowledge-retrieval contract
document, and several timestamped pre-change backup copies. **None of those were created, modified,
staged, reverted, or cleaned by this work.** They are recorded here only so a later reader does not
attribute them to the adaptive-governor workstream. `nizamcore` HEAD advanced by exactly one commit,
`c3a4e65`, whose staged set was guarded to 15 files all under `governor/adaptive/`; every item listed
above was left uncommitted and unmodified.

Likewise in this workspace, `ops/A0_AUTHORIZATION_RECEIPT_2026-09-02` predates this session.

## 6. Blockers that are not mine to clear

| Blocker | Nature | Needs |
|---|---|---|
| `nizamcore` commit/push of a new pipeline exceeds §6a's four purposes | governance | explicit owner reconciliation, per playbook R7 |
| No GitHub push credential on the VPS | credential | owner; push is impossible regardless of §6a |
| the `47_NIZAM` BOOTSTRAP manifest does not exist | external mutation (Drive write, class B) | owner authorization; R4 is read-only |
| Deterministic finance engine API absent | implementation | blocks D03, C02-T04, C03-T04 |
| SUKOON `full` mode: 40-only vs `>=67` independent trigger | **spec-vs-spec conflict** | owner adjudication. Contracts 01/04 define `full` as green-only with 40 as an override; the dropzone Cross-Domain contract adds `objective_recovery >= 67` as an independent trigger, which would permit full-strength work under a RED state. No acceptance test isolates it. This implementation follows the dropzone contract (67) and pins both thresholds under tamper T1/T2, so a change of policy fails loudly rather than silently. |
| Playbook `S05` crisis detection | underspecified | no field name, type, or trigger defined in any contract. Only the *override-given-a-flag* is implemented; detection from free text is deliberately not built. |
| Playbook bare IDs `C01`–`C05` collide with Contract 01's `C01-T0x` | spec hygiene | rename before either appears in a real run receipt |

## 7. Owner decision — RESOLVED 2026-09-03

The owner, in chat on 2026-09-03, explicitly authorized committing across `nizamcore`,
`nizamfinancialapp`, and the VPS. That selects **option 1** of the three that were offered: the
adaptive package is committed to `nizamcore` in place.

**This is the §6a reconciliation record for this one addition.** It widens §6a's four enumerated
purposes to admit a fifth, narrowly: *committing the additive, non-actuating `governor/adaptive`
package and its tests*. It does not authorize restructuring `nizamcore`, and it does not grant the
governor autonomous commit authority on any cadence — Contract 04's
`github_policy.desired_standing_authorization` remains **unreconciled and blocked**, and playbook
R7_GITHUB_AUTONOMY remains **not entered**.

Scope actually committed, deliberately narrow:

- `nizamfinancialapp`: the four `ops/` documents of this workstream.
- `nizamcore`: `NIZAM__system/governor/adaptive/` only.

**Not committed, and not mine to bundle:** the modifications and untracked files already present in
the `nizamcore` working tree from earlier sessions (see section 5a). Folding unrelated prior work into
this commit would misattribute it and widen the blast radius, so each was left exactly as found.

**Push was NOT performed.** The owner authorized commit. Push remains a separate external action, and
no GitHub push credential exists on the VPS in any case.

## 8. Rollback

Both changes are now committed, so rollback is a revert rather than a file deletion. Neither commit
has been pushed, so nothing has to be coordinated with a remote.

`nizamcore` (removes the adaptive package):

```
cd /home/<USER>/nizamcore && git revert --no-edit c3a4e65
```

`nizamfinancialapp` (removes the four ops documents):

```
git revert --no-edit ba43912
```

Because both commits are additive and each is the tip of its branch, `git reset --hard` onto the parent commit would
also work while they remain unpushed — `d71a0b6` and `109ca67` respectively — but revert is preferred
because it preserves the record of what was done and why.

After reverting `nizamcore`, its pre-existing suites return to 136 passed / 17 skipped / 14 subtests.
No config, service, schema, policy, cron entry, scheduler unit, or credential requires reversal in
either repository, because none was ever changed.

## 9. Honest production readiness

**Not production ready, and not close.** R0/R1 (`synthetic_only`, `autonomy: none`) is implemented and
tamper-proven. R2–R7 are **not started**: there is no scheduler, no retrieval entrypoint, no actuation
path, no run-record persistence, no reconciliation job, and no promotion pipeline. Nothing here has
been observed to run against live data, and no autonomous action has been enabled.
