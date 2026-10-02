# Requirements Document

Spec: `hermes-governed-workflows` · Workflow: design-first · Type: feature
Derived from: `.kiro/specs/hermes-governed-workflows/design.md` (§0–§L, complete). **design.md is the source of truth.** Where this document and design.md disagree, design.md wins; the discrepancies found while deriving are listed in §X.

**Correction pass (source-verified).** Two corrections were applied to this document and to design.md, both grounded in files read directly rather than in an asserted status:

1. **Delivery semantics were overclaimed.** Exactly-once *delivery* is **retracted** and replaced by **at-least-once delivery with an idempotent canonical write** (design **§L.12**; Requirement 22; §X.2 finding 6). New decision **D-11**.
2. **The router-lexicon contradiction was resolved from source, and R-3 was wrong.** `FINANCE` contains `\bsafe to spend\b`, so R-3's fixture routes `mal`/`pfos_read` and reaches no model. R-3 is re-specified and **R-3b** added (design **§D.7.1.1**, **§E.5.1**; Requirement 17; §X.2 finding 1). New decision **D-12**.

Neither correction changed a fixture to make a case pass, weakened an acceptance check, or resolved an owner decision. **D-11 and D-12 carry recommended defaults only.**

## Introduction

This document states, as testable requirements, the governed conversational workflow designed in design.md: an authenticated message arrives, is durably accepted, is classified and governed, reaches **either** a deterministic PFOS read **or** an authorized native capture, the result is verified before it is spoken, and the owner receives an honest reply — including an honest refusal. Everything after that first vertical slice is sequenced behind it as increments **I0–I7**.

**This requirements document is a planning artifact and confers no implementation authorization.** Nothing in it may be read as permission to write code, edit a test, run a gate, touch a host, mint or use a credential, or spend against a provider key. It records what the work must satisfy *if and when* the owner approves the plan. It resolves no owner decision, and it adopts no `[AGREED]` marker found anywhere in the evidence base as an owner choice.

Two standing cautions from design §0.4 apply to every requirement below:

- **A documented status is not fresh verification.** A checked box can mean the check ran and failed.
- **Test success is not live readiness.** A green offline suite establishes composition and refusal behaviour on synthetic fixtures. It establishes nothing about a running host, a bound transport, a loaded MCP surface, or a real ledger.

### Verification vehicles used in this document

| Vehicle | Meaning |
|---|---|
| **automated** | Verifiable by an offline Vitest test or a source-level assertion in this repository. |
| **harness** | Verifiable by one of the twenty-one declared checks in `scripts/verify/all.mjs`. |
| **document review** | Verifiable only by reading an artifact and confirming a statement; no automated check exists or is created. |
| **owner observation** | Verifiable only by the owner, or only against a live system that is INACCESSIBLE from a planning session. |

Each requirement names its vehicle. Requirements whose only vehicle is **document review** or **owner observation** are marked as such rather than dressed up as automatable — see §X.3.

### Evidence labels (design §0.4, used verbatim)

| Label | Meaning |
|---|---|
| **VERIFIED** | Read or run in the session that recorded it. |
| **UNVERIFIED** | Asserted somewhere, not established. |
| **STALE** | A dated receipt, not re-observed. |
| **INACCESSIBLE** | Unreachable from the recording session. |

---

## Glossary

**Approval — Stage 1 (plan approval).** Explicit owner approval of the completed plan (design.md plus this document). Stage 1 unblocks **implementation**, and implementation includes **local and offline code changes and test changes** — a new module under `src/`, a new or extended file under `tests/` or a `*.test.ts` sibling, a widened type signature, an added dependency line at a composition root. There is **no "no approval required" category.**

**Approval — Stage 2 (post-plan approvals).** The separate approvals that still apply, each on its own merits, after Stage 1: **live operation** (a bound transport, a real ingress consumer), **deployment**, **credentials** (minting, rotation, consent, scope), **host mutation** (provisioning, unit edits, service restarts, DNS), **provider spend** (any paid model call), and **the human gates G1–G8** in `ops/DEPLOYMENT_CONTROL.md`. **Plan approval is not live authorization.**

**"Stage 1 only."** The exact phrasing used in this document for an increment or deliverable that requires Stage-1 plan approval and **nothing beyond it**. It never means "no approval".

**Candidate_Exclusion.** The single serialisation-time projection module (`src/lib/drive/candidateExclusion.ts`) that removes `transactionCandidates` from a Drive-bound payload.

**Capture receipt.** A `JournalPersistenceReceipt` from `src/server/process/journalPersistenceAdapter.ts`, carrying `state`, `status`, `mode`, `entryRef`, `canonicalPath`, `readBackConfirmed`, `hashMatch` and `pending`.

**Continuity_Mirror.** The I6 continuity state machine and its Drive mirror leg.

**Deterministic_Alerts.** The I4 deterministic-threshold alert planners.

**DeterministicFinancialFact.** The `hermes/toolBoundary.ts` record carrying `factRef`, `label`, `amountMilliunits: Money`, `currency`, `computedAt` and the literal `deterministicEngine: true`.

**Digit-free.** Containing no character matched by `NO_FIGURE_PATTERN` (`/\d/`).

**Drive_Discovery.** The I3 bounded, `drive.file`-scoped discovery of owner-approved knowledge.

**Effective_Surface_Assessor.** `assessEffectiveToolSurface` and `EffectiveSurfaceReport` in the new `effectiveToolSurface.ts` module.

**Governed_Turn_Path.** The new `src/server/process/governedTurnPath.ts` module and its exported executor, renderer, reply constants and `captureRecordId`.

**Ingress_Router.** `routeIngressText` in `src/server/hermes/ingressRouter.ts`, together with `assertRoutedFinancialResult`.

**Implementation_Program.** The sequenced increments I0–I7 considered as work items.

**Journal_Port.** `GovernedJournalPort`, whose sole method is `appendRecord(JournalAppendRequest): Promise<JournalPersistenceReceipt>`.

**Milliunit.** The integer money unit. 1 EGP = 1000 milliunits; 1 piastre = 10 milliunits.

**Operator_Message_Port.** `src/server/telegram/operatorMessagePort.ts`, owner of the admission decision and the durable queue interface.

**Payload_Envelope.** The new `src/lib/drive/payloadEnvelope.ts` module owning `encrypt`, `decrypt`, `refuse` and `version` for Drive-bound payloads.

**PFOS_Port.** `GovernedPfosPort`, whose methods `readFinancialSnapshot` and `runDeterministicAnalysis` each return `Promise<FinancialAnalysisResult>`.

**Planning_Program.** design.md and this document, considered as artifacts.

**Reachability_Suite.** The offline test suite that carries the six reachability cases of design §E.5 — R-1, R-2, R-3, **R-3b**, R-4, R-5. *(R-3b was added by the correction pass; R-3 was re-specified — see §X.2 finding 1.)*

**Recovery_Rehearsal.** The I7 archive-and-restore exercise on synthetic data in a scratch location.

**Reply_Sender.** `createBindableReplySender`, bound once in `main.ts`; sole outbound send authority.

**Repository_Gate.** `npm run verify:all -- --all` and the twenty-one checks declared in `scripts/verify/all.mjs`.

**Scheduled_Jobs_Registry.** The new `src/server/process/scheduledJobs.ts` registry of named jobs, each a pure planner plus an injected effect.

**Scheduler.** `src/server/process/scheduler.ts`, sole clock, with `SCHEDULER_TARGETS = ['life','finance'] as const`.

**Signal_Bus.** `signalbus.publish_bounded_signal` / `signalbus.read_bounded_signals` and the `signals.db` store.

**Turn_Admission.** The new `src/server/process/turnAdmission.ts` module: `admitTurn`, `ADMISSION_BRANCHES = ['governed_deterministic','tier_path']`, `TurnAdmission`.

**Turn_Classifier.** `classifyTurn` in `src/server/routing/turnClassifier.ts`; the sole mint of a `ModelInvocationGrant`.

**Turn_Dispatch.** `dispatchTurn` in `src/server/routing/turnDispatch.ts`.

**Turn_Worker.** The worker created by `createTurnDispatchWorker` in `src/server/process/turnWorker.ts`.

**Zero effect.** No store read, no store write, no tool call, no model invocation, and no provider spend.

---

## Requirements

The twenty-nine requirements below are organised into four groups — **Group A** cross-cutting, **Group B** increment I0, **Group C** increment I1, **Group D** increments I2 through I7. The grouping is presentational only. **Requirement numbering runs 1–29 continuously across the groups**, and every acceptance criterion is cited elsewhere as `N.M`, so a group boundary never renumbers anything.

### Group A — Cross-cutting requirements

### Requirement 1: Two-stage approval model

**User Story:** As the owner, I want every piece of this program to wait for my approval of the plan first and for a second, separate approval before anything touches a live system, so that no work and no live action is ever taken on inherited or implied authority.

Vehicle: **document review** (criteria 1.1–1.6), **automated** (criterion 1.7).

#### Acceptance Criteria

1. THE Planning_Program SHALL state that Stage-1 plan approval is a precondition of **all** implementation, including local and offline code changes and test changes.
2. WHERE an increment or deliverable requires Stage-1 plan approval and no further approval, THE Planning_Program SHALL describe that increment with the exact phrase **"Stage 1 only."**
3. THE Planning_Program SHALL describe **no** increment, deliverable or requirement as requiring no approval.
4. WHEN Stage-1 plan approval is granted, THE Implementation_Program SHALL treat live operation, deployment, credential work, host mutation, provider spend and the human gates G1–G8 as still requiring separate Stage-2 approval.
5. IF a prior receipt, a green test suite, a green Repository_Gate result or an earlier increment's approval is offered as authorization for a Stage-2 item, THEN THE Implementation_Program SHALL refuse that authorization and require the Stage-2 approval on its own merits.
6. THE Planning_Program SHALL state that this requirements document is a planning artifact conferring no implementation authorization.
7. WHEN a source file under `src/` or `tests/` is added or changed by this program, THE file SHALL declare its owning contract and phase within its first twenty lines, so that `AC10` continues to pass.

---

### Requirement 2: Standing constraints preserved

**User Story:** As the owner, I want the constraints I already set to survive this program untouched, so that a new capability never quietly retires an existing decision.

Vehicle: **automated** (2.1–2.4, 2.7), **document review** (2.5, 2.6, 2.8).

#### Acceptance Criteria

1. THE Implementation_Program SHALL keep Slack Socket Mode as the sole transport, using only the aliases `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` and `SLACK_ALLOWED_USERS`.
2. WHEN a process presents any of the five `REVOKED_TELEGRAM_ALIASES` — `BOT_NIZAM_TOKEN`, `BOT_A_TOKEN`, `BOT_B_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHATS` — THE `assertRevokedTelegramAliasesNotPresent` assertion SHALL refuse that process.
3. THE Implementation_Program SHALL introduce **no** Telegram cutover, and SHALL treat a `telegram*` symbol name in the tree as historical naming rather than a live Telegram binding.
4. THE `OBJECTIVE_REGISTRY` in `src/server/objectives/objectiveRegistry.ts` SHALL remain byte-identical, with `OBJECTIVE_COUNT` equal to 20.
5. THE Planning_Program SHALL describe `src/server/hermes/dailyCompanion.ts` and `channelMemory.ts` as offline references with no live binding, and SHALL NOT describe either as a deployed capability.
6. THE Implementation_Program SHALL preserve the 54 dirty working-tree entries as found, and SHALL create no commit and no push.
7. THE Implementation_Program SHALL represent every monetary magnitude as an integer count of milliunits at 1 EGP = 1000 milliunits, and SHALL introduce no floating-point money at any tier.
8. THE Implementation_Program SHALL leave the authority of the `telegram-window`, `agentic-profile-baseline`, `telegram-daily-companion` and `dual-channel-memory` specs intact, superseding none of them.

---

### Requirement 3: Money provenance and determinism

**User Story:** As the owner, I want every number I am told to come from a deterministic engine, so that I never act on a figure a language model produced.

Vehicle: **automated**, plus **harness** (`AC07`) for the money-integrality half.

#### Acceptance Criteria

1. WHEN a monetary figure reaches the owner, THE figure SHALL originate from a `DeterministicFinancialFact` whose `deterministicEngine` is the literal `true` and whose `amountMilliunits` is a safe integer.
2. WHEN Governed_Turn_Path renders a verified financial result, THE rendered text SHALL copy each `fact.amountMilliunits` verbatim, performing no arithmetic, no formatting, no rounding and no currency conversion.
3. WHEN Governed_Turn_Path renders a verified financial result, THE rendered text SHALL include the deterministic `resultRef`.
4. WHEN Governed_Turn_Path renders a verified financial result, THE module SHALL run `assertRoutedFinancialResult` before `assertDeterministicFinancialResult`, and SHALL run both before composing any character of the reply.
5. IF `assertRoutedFinancialResult` rejects a result, THEN THE Governed_Turn_Path SHALL report the governance failure outcome `pfos_refused` rather than a money failure.
6. IF a PFOS source does not answer, THEN THE Governed_Turn_Path SHALL reply with digit-free text and SHALL offer no substitute figure.
7. IF either assertion rejects a result, THEN THE Governed_Turn_Path SHALL reply with digit-free text and SHALL offer no substitute figure.
8. THE model tier SHALL source, compute, estimate, round and repeat no monetary amount; WHEN a turn is answered on the model tier, THE reply SHALL be digit-free.
9. THE Governed_Turn_Path SHALL import no module from `src/lib/money`, because it performs no computation.
10. WHEN a migration introduced by this program runs, THE migration SHALL leave every monetary field byte-identical, and a test SHALL assert that property.

---

### Requirement 4: Tool boundary and effective tool surface

**User Story:** As the owner, I want the tool boundary to stay exactly as strict as it is today, and I want an honest report about what the live gateway actually loaded, so that a composition guarantee is never mistaken for a runtime one.

Vehicle: **automated** (4.1–4.6), **owner observation** (4.7).

#### Acceptance Criteria

1. THE `HERMES_TOOL_NAMES` array SHALL have length 10 after increment I1, and increment I1 SHALL add zero tools.
2. THE increments I0–I7 SHALL add zero tools, and increment I5 SHALL use only `signalbus.publish_bounded_signal` and `signalbus.read_bounded_signals`, both already members of `HERMES_TOOL_NAMES`.
3. WHEN `denyAuthorityTool` is called with `nizamcore.request_pfos_analysis`, `pfos.read_financial_snapshot` or `pfos.run_deterministic_analysis`, THE predicate SHALL refuse each of the three names.
4. THE Implementation_Program SHALL remove no entry from `DENIED_AUTHORITY_TOOLS`, SHALL relax no part of `AUTHORITY_KEY`, and SHALL carve no exception into either.
5. THE deterministic financial leg SHALL be a Turn_Worker branch and SHALL present no tool name to `runtimeAdapter`.
6. WHEN Effective_Surface_Assessor receives an `ObservedToolSurface` whose `method` is `null`, THE assessor SHALL return verdict `unobserved` and SHALL NOT return verdict `ok`.
7. WHEN Effective_Surface_Assessor produces a report, THE report SHALL carry `authorizesExecution` as the literal `false`, SHALL list `unexpected` and `missing` tools as two separate collections, and SHALL compute `authorityBearing` using the existing `denyAuthorityTool` predicate rather than a re-implementation.
8. WHILE decision D-4 is unresolved, THE Effective_Surface_Assessor SHALL be exercised against synthetic observations only.

---

### Requirement 5: Privacy of observations, logs and thrown values

**User Story:** As the owner, I want my words to stay out of every log, observation and error, so that a diagnostic trail never becomes a disclosure.

Vehicle: **automated**, including one property test.

#### Acceptance Criteria

1. WHEN Governed_Turn_Path emits an observation, THE observation SHALL carry only `turnRef`, a route code, a module, an effect and an outcome.
2. THE observations, log lines and thrown `detail` values produced by this program SHALL contain no turn content.
3. WHEN a component correlates records across tiers, THE component SHALL correlate by `turnRef` or `queuedRef` only.
4. THE observations, log lines, fixtures and ops artifacts produced by this program SHALL record no deployment particular — no host, bot, sender, chat, token, endpoint or monetary figure — so that `AC18` continues to pass.
5. WHEN a capture receipt carries a `recoveryAction` string, THE Governed_Turn_Path SHALL route that string to the redacted observation and SHALL NOT include it in the owner's reply.
6. WHEN a refusal is spoken, THE reply SHALL be the Ingress_Router's own `publicReason` and SHALL leak no reason for the refusal.

---

### Requirement 6: Queue, scheduler and single-writer authority

**User Story:** As the owner, I want exactly one writer for each store, exactly one clock, and an intake path whose behaviour I can reason about after a crash.

Vehicle: **automated**.

#### Acceptance Criteria

1. THE Operator_Message_Port SHALL perform the dedup claim and the enqueue in one transaction, and returning from `accept` SHALL be the acknowledgement.
2. THE Implementation_Program SHALL introduce no separate acknowledgement step after `accept` returns.
3. WHEN a delivery arrives, THE Operator_Message_Port SHALL check the bot namespace before performing dedup, and SHALL then check the owner allowlist before enqueueing.
4. WHEN a delivery is refused, THE Operator_Message_Port SHALL emit exactly the one generic code `OPERATOR_DELIVERY_REFUSED`, and a `duplicate` decision SHALL carry no refusal code.
5. WHEN the Turn_Worker settles an item as `done`, THE settle SHALL occur only after the Reply_Sender reports a delivered send.
6. WHEN the Reply_Sender is unbound, THE Reply_Sender SHALL throw `TELEGRAM_SEND_REFUSED`; WHEN the reply target is `null`, THE Turn_Worker SHALL settle the item as `abandoned` with code `TELEGRAM_SEND_REFUSED`.
7. THE increment I2 SHALL add a consumer behind the existing `finance` internal endpoint only, and SHALL add no `SCHEDULER_TARGETS` member, no timer, no cron and no `listeningPorts` writer.
8. THE Scheduler SHALL remain the sole timing source in the tree, and a source-level assertion SHALL confirm that no second timing source exists.
9. THE Turn_Classifier SHALL remain the sole mint of a `ModelInvocationGrant`, and `isMintedGrant` SHALL continue to be re-checked independently at the planner, at the channel and at the router.
10. WHEN a `ModelInvocationGrant` is forged by a type cast, THE planner, THE channel and THE router SHALL each refuse it.
11. THE single writer per store — Operator_Message_Port for admission, `workQueueRepo` for durable queue state, Turn_Classifier for grants, Scheduler for the clock, the nizamcore native writer for journal content, Reply_Sender for outbound sends, `createModelChannel` for provider reach — SHALL be preserved by every increment.
12. THE Governed_Turn_Path SHALL call `appendRecord` only, and SHALL NOT call the legacy `appendWithReceipt`.

---

### Requirement 7: Repository gates and the measured baseline

**User Story:** As the owner, I want the verification surface to stay exactly as it is and the expected result to be stated honestly, so that a known-failing check is never mistaken for a regression and a green run is never mistaken for readiness.

Vehicle: **harness** (7.1–7.4), **document review** (7.5–7.9).

#### Acceptance Criteria

1. THE Repository_Gate commands SHALL remain `npm run typecheck`, `npm run lint`, `npm test -- --run <pattern>`, `npm run build` and `npm run verify:all -- --all`, unchanged in name, number and weight.
2. THE Implementation_Program SHALL add, remove, rename and reweight no check in `scripts/verify/all.mjs`, whose declared count is 21.
3. WHEN the Repository_Gate runs while the working tree carries the 54 dirty entries, THE expected result SHALL be **19 of 21**, with `AC14` (working tree is clean) and `AC15` (repository is push ready and unpushed) failing.
4. WHEN a smoke run reports 19 of 21 with only `AC14` and `AC15` failing, THE Implementation_Program SHALL treat that result as the correct baseline and SHALL NOT report it as a regression.
5. THE Planning_Program SHALL label the 19-of-21 figure as **STALE** as a measurement, dated 2026-09-16, while labelling its cause — the 54 dirty entries — as **VERIFIED**.
6. THE Planning_Program SHALL state that passing tests is not live readiness, is not a Stage-2 approval, and is not evidence about any running system.
7. THE Planning_Program SHALL record that `scripts/verify/contract-ledger.mjs` (`AC12`) opens only `contracts/_CONTRACT_INDEX.md` and `contracts/_BUILD_LOG.md`, hard-requires exactly five contract rows, and contains no supersession, amendment, date or heading logic.
8. THE Planning_Program SHALL record that `AC12` checks neither PFOS contracts 01–15 nor any amendment, and therefore that the inline build-log amendment channel every increment relies on is **unverified by the harness**.
9. THE Implementation_Program SHALL invent no new acceptance check to fill the `AC12` gap, because changing the declared check count is a harness change and therefore an owner decision.
10. THE Planning_Program SHALL record that no check in the twenty-one enforces the Drive **encryption** requirement, `AC08` enforcing scope only.

---

### Requirement 8: Blocking decisions as prerequisites

**User Story:** As the owner, I want every open decision named with what it blocks, and I want the places where no default was offered left empty, so that no choice is made on my behalf.

Vehicle: **document review**.

#### Acceptance Criteria

1. THE Planning_Program SHALL carry decisions D-1 through D-12 forward as explicit prerequisites, each naming the requirements it blocks.
2. WHILE decision **D-8** (reachability approach; recommended default: pre-tier governed admission) is unanswered, THE Implementation_Program SHALL treat Requirements 13 through 23 as blocked, because the two options produce different files.
3. WHILE decision **D-5** (Drive encryption scheme, candidate-egress fix, and the O1 §2.2 readable-mirror conflict; recommended default: a WebCrypto-based scheme, a single serialisation-time projection, and `drive-db.md` holding) is unanswered, THE Implementation_Program SHALL treat Requirements 10, 11 and 12 as blocked, and transitively Requirements 25, 28 and 29 and the real-data path of Requirements 13 through 23.
4. WHILE decision **D-2** (whether O6's cadence of three proactive daily briefs and twice-daily Drive discovery gets a contract) is unanswered, THE Planning_Program SHALL record **None offered** as the recommendation and SHALL treat only O6 §6 as blocked, leaving Requirement 24 unblocked.
5. WHILE decision **D-6** (disposition of the 54 dirty entries) is unanswered, THE Planning_Program SHALL record **None offered** as the recommendation, and SHALL treat `AC14`, `AC15`, any commit and any push as blocked.
6. WHILE decision **D-1** (registration of objectives O1–O11; recommended default: an additive sub-registry keyed by parent `id: 10`) is unanswered, THE Implementation_Program SHALL create no tracked authority for O1–O11 and SHALL treat Requirements 10 through 29 as unblocked by it.
7. WHILE decision **D-3** (systemd hardening; recommended default: harden the live unit, as a Stage-2 host mutation) is unanswered, THE Planning_Program SHALL make no claim that the gateway runs hardened.
8. WHILE decision **D-4** (ingress ownership; recommended default: a disambiguation observation before choosing) is unresolved, THE Implementation_Program SHALL run no live turn, SHALL run no real-host scheduled job, SHALL produce no real effective-surface observation, and SHALL terminate no ingress candidate for appearing redundant.
9. WHILE decision **D-7** (the nizamcore verified-state contradiction; recommended default: mark `ops/NIZAMCORE_VERIFIED_STATE.md` STALE now and re-observe when authorized) is unresolved, THE Governed_Turn_Path SHALL treat a remote capture as `captured_unconfirmed` by default and SHALL NOT say "Captured" on the strength of a remote call alone.
10. WHILE decision **D-9** (deterministic seam shape; recommended default: instantiate the existing generic as `Answer = Promise<string>`) is unanswered, THE Implementation_Program SHALL treat the two changed lines of `turnWorker.ts` named in Requirement 23 as unfixed in shape.
11. WHILE decision **D-10** (disposition of `singleWindowFlow.ts`; recommended default: keep it as the offline reference for I1 and decide retirement later) is unanswered, THE Implementation_Program SHALL leave `singleWindowFlow.ts` intact and SHALL consume its types only.
12. THE Planning_Program SHALL propose no edit to the `nizamcore` repository, which is separate and owner-gated.
13. WHILE decision **D-11** (duplicate outbound delivery; recommended default: a delivery-reconciliation record persisting `queuedRef → TelegramSendReceipt` before the settle, **with** the at-least-once disclosure retained regardless) is unanswered, THE Implementation_Program SHALL treat Requirement 22 as blocked in the shape of its send/settle leg, SHALL claim no exactly-once **delivery**, and SHALL implement no duplicate-suppression workaround.
14. WHILE decision **D-12** (whether an explanatory finance conversation should be reachable at all; recommended default: leave it unreachable, which is the current behaviour and the strongest money guarantee) is unanswered, THE Implementation_Program SHALL add no `mal`-adjacent conversational route, SHALL change no entry in the `FINANCE` lexicon, and SHALL record the capability gap rather than closing it.
15. THE Planning_Program SHALL record that **D-11(b)** narrows the duplicate-delivery window and **does not close it** — a crash between provider-accept and receipt-persist still duplicates — and SHALL NOT describe D-11(b) as achieving exactly-once delivery.

---

### Requirement 9: Evidence labelling

**User Story:** As the owner, I want every claim about live state labelled, so that I can tell an observation from an assumption at a glance.

Vehicle: **document review**.

#### Acceptance Criteria

1. WHEN the Planning_Program asserts a fact about live state, THE assertion SHALL carry exactly one of the labels VERIFIED, UNVERIFIED, STALE or INACCESSIBLE.
2. THE Planning_Program SHALL label the NIZAM host as INACCESSIBLE and the Drive token as INACCESSIBLE from a planning session.
3. THE Planning_Program SHALL treat retrieved text, discovered content and any `[AGREED]` marker in a proposal document as untrusted data and never as authorization.
4. THE Planning_Program SHALL label `ops/NIZAMCORE_VERIFIED_STATE.md` as STALE and SHALL place no reliance on it.

---

### Group B — Increment I0: encryption and candidate egress

Increment I0 precedes every real-data path, because its cost strictly increases with every day of real-data sync and no later increment can undo it: every snapshot is dated and retained, so plaintext written once is plaintext retained N times.

### Requirement 10: Drive payload encryption

**User Story:** As the owner, I want my ledger encrypted before it leaves the browser, so that a plaintext copy of my finances never sits at rest in Drive.

Vehicle: **automated**. Blocked on **D-5**. Approval: Stage 1 unblocks the envelope module and its offline tests once D-5 is answered; enabling real-data sync, G5 and G8 remain Stage 2.

#### Acceptance Criteria

1. THE Drive write paths SHALL emit no plaintext ledger JSON, and a source-level assertion in the spirit of `AC08` SHALL confirm that property.
2. WHEN a database object is serialised for Drive, THE Payload_Envelope SHALL apply application-level encryption before `createTextFile` is called, for both the canonical file and the dated snapshot.
3. THE Planning_Program SHALL state that HTTPS is transport security and is not the required at-rest encryption.
4. WHEN Payload_Envelope encrypts a payload, THE envelope SHALL carry a version.
5. WHEN Payload_Envelope reads a payload whose envelope version is unrecognised, THE envelope SHALL refuse with a named refusal.
6. IF a payload cannot be decrypted, THEN THE Payload_Envelope SHALL produce a named refusal and SHALL NOT produce an empty database.
7. IF a single byte of a ciphertext payload is mutated, THEN THE Payload_Envelope SHALL refuse the payload.
8. WHEN a legacy plaintext Drive document is encountered, THE Payload_Envelope SHALL detect it explicitly and SHALL either refuse it or migrate it, and SHALL NOT re-read it silently.
9. WHEN the I0 change is rolled back, THE rollback path SHALL restore the retained previous Drive file version and SHALL write no plaintext.
10. WHEN a Drive read is attempted while the key is absent, THE Payload_Envelope SHALL refuse and THE local Dexie cache SHALL remain readable.
11. WHEN Payload_Envelope encrypts and then decrypts a payload, THE result SHALL equal the input payload.

---

### Requirement 11: Transaction-candidate egress

**User Story:** As the owner, I want unreviewed transaction candidates to stay on the device that created them, so that unconfirmed guesses about my spending never reach Drive.

Vehicle: **automated**, including one property test. Blocked on **D-5**. Approval: once D-5 is answered, **Stage 1 only.**

#### Acceptance Criteria

1. WHEN a database object is serialised for Drive, THE Candidate_Exclusion projection SHALL remove `transactionCandidates`, and `transactionCandidates` SHALL be absent from every serialised payload.
2. THE Candidate_Exclusion projection SHALL be applied at the one place the payload is built, and SHALL NOT be duplicated per call site.
3. FOR ALL database shapes, THE serialised Drive payload SHALL contain no candidate field.
4. THE Implementation_Program SHALL include a source-level assertion that detects a future re-introduction of a candidate field into a Drive-bound payload.
5. THE Planning_Program SHALL state that encryption alone does not fix candidate egress, because an encrypted payload still contains the candidates.

---

### Requirement 12: Key custody and Drive scope

**User Story:** As the owner, I want to hold the keys myself and the app to see only the files I gave it, so that the encryption is real and the blast radius stays small.

Vehicle: **automated** (12.1–12.3), **harness** (`AC08`, `AC09`), **owner observation** (12.4–12.5). Approval: Stage 2 for all key operations.

#### Acceptance Criteria

1. THE keys used by Payload_Envelope SHALL appear in no Drive-bound object.
2. THE Drive scope SHALL remain `https://www.googleapis.com/auth/drive.file` only, so that `AC08` continues to pass.
3. THE repository SHALL track no secret and no real ledger, so that `AC09` continues to pass.
4. THE Implementation_Program SHALL generate no key, SHALL rotate no key, SHALL renew no consent and SHALL broaden no scope.
5. WHILE gate **G5** (storage consent) or gate **G8** (backup keypair, private half off-host) is recorded as `BLOCKED - awaiting human`, THE Implementation_Program SHALL enable no real-data Drive sync.

---

### Group C — Increment I1: the governed vertical slice

### Requirement 13: Governed deterministic path composition

**User Story:** As the owner, I want the deterministic legs that already exist to be composed into the path that actually runs, so that a financial question gets an answer instead of a redirect.

Vehicle: **automated**. Blocked on **D-8**. Approval: for the offline half, **Stage 1 only.** A bound transport, a real `finance.db` read and a real native capture remain Stage 2.

#### Acceptance Criteria

1. WHEN the Ingress_Router returns `effect: 'none'`, THE Governed_Turn_Path SHALL reply with `route.publicReason`, SHALL record outcome `clarified` for code `CLARIFY` or `refused` for a `REFUSED_*` code, and SHALL produce zero effect.
2. WHEN the Ingress_Router returns `effect: 'local_write'`, THE Governed_Turn_Path SHALL call `Journal_Port.appendRecord` and SHALL derive the reply from the returned capture receipt as specified in Requirement 21.
3. WHEN the Ingress_Router returns `effect: 'pfos_read'`, THE Governed_Turn_Path SHALL select the PFOS method named by `route.tool`, calling `PFOS_Port.runDeterministicAnalysis` for the value `pfos.run_deterministic_analysis` and `PFOS_Port.readFinancialSnapshot` for every other value.
4. IF the PFOS call throws, THEN THE Governed_Turn_Path SHALL record outcome `pfos_unavailable` and reply with the digit-free unavailable text.
5. IF `renderVerifiedFinance` throws, THEN THE Governed_Turn_Path SHALL record outcome `pfos_refused` and reply with the digit-free refused text.
6. WHEN the Ingress_Router returns any other effect, THE Governed_Turn_Path SHALL record outcome `sentence` and reply from the existing digit-free answer table.
7. WHEN the raw body cannot be read as a turn, THE `readTurnText` helper SHALL return `null` and THE Governed_Turn_Path SHALL proceed without throwing.
8. THE Governed_Turn_Path SHALL own no store, no socket and no clock, and SHALL receive its PFOS port, journal port and clock by injection.
9. THE increment I1 SHALL modify none of `turnDispatch.ts`, `turnClassifier.ts`, any module under `src/server/hermes/`, `operatorMessagePort.ts`, `scheduler.ts` or `singleWindowFlow.ts`.
10. THE increment I1 SHALL introduce no schema migration.

---

### Requirement 14: Pre-tier governed admission

**User Story:** As the owner, I want the routing decision taken before the tier decision, so that a turn needing no model never reaches the model tier at all.

Vehicle: **automated**. Governed by **D-8**; under option (b) this requirement is replaced by classifier-vocabulary criteria and Requirements 15–19 still apply unchanged.

#### Acceptance Criteria

1. WHEN Turn_Admission receives turn text, THE module SHALL call the Ingress_Router and SHALL return the router's verdict unmodified alongside a branch.
2. WHEN the router's effect is `local_write`, `pfos_read` or `none`, THE Turn_Admission SHALL return branch `governed_deterministic`.
3. WHEN the router's effect is `read` or any other value, THE Turn_Admission SHALL return branch `tier_path`.
4. WHEN Turn_Admission returns branch `governed_deterministic`, THE Turn_Worker SHALL call neither the Turn_Classifier nor Turn_Dispatch, and no `ModelInvocationGrant` SHALL exist for that turn.
5. WHEN Turn_Admission returns branch `tier_path`, THE Turn_Worker SHALL follow the existing Turn_Classifier and Turn_Dispatch path unchanged.
6. THE Turn_Admission SHALL re-implement no routing policy, and SHALL consume `routeIngressText` verbatim.
7. THE increment I1 SHALL modify none of `TURN_INTENT_TRIGGER`, `INTENT_FAMILY`, `PROSE_INTENTS` or `DEFAULT_PROSE_INTENT`.

---

### Requirement 15: Reachability R-1 — journal capture

**User Story:** As the owner, I want "write this down: …" to be captured by the writer, so that a thought I dictate is recorded rather than discussed.

Vehicle: **automated**. Acceptance criterion in design: **AC-I1-11**.

**Confirmed from source (this pass).** `JOURNAL` matches `write this down`, the text carries no `FINANCE` token and no read verb (`read`/`show`/`what did i`), so the router selects `nizamcore.append_journal_entry` with effect `local_write`. **VERIFIED**; the pattern is quoted in design §D.7.1.1. R-1 holds as designed.

#### Acceptance Criteria

1. WHEN the Reachability_Suite submits the representative text `write this down: the fridge broke`, THE Ingress_Router SHALL return code `ROUTED`, module `yawmiyat` and effect `local_write`.
2. WHEN that turn is admitted, THE Turn_Admission SHALL return branch `governed_deterministic`.
3. WHEN that turn is processed, THE Reachability_Suite SHALL observe that the Turn_Classifier was never called and that no model channel was invoked.
4. WHEN that turn is answered, THE reply SHALL be a writer-receipt reply derived from observed `JournalPersistenceReceipt` fields, and SHALL NOT be a model-composed sentence.

---

### Requirement 16: Reachability R-2 — balance and PFOS read

**User Story:** As the owner, I want "what is my balance" answered from the deterministic engine, so that the number I read is the number the engine computed.

Vehicle: **automated**. Acceptance criterion in design: **AC-I1-12**.

**Confirmed from source (this pass).** `FINANCE` matches `balance`, `JOURNAL` does not match, so the router takes the `finance` branch; `deriveIntent` returns `recalculate_balances` (the `PROSE_INTENTS` entry `['balance', 'recalculate_balances']`), which is not `evaluate_financial_decision`, so the tool is `pfos.read_financial_snapshot` and the effect is `pfos_read`. **VERIFIED.** R-2 holds as designed. The same branch is what R-3 takes — see Requirement 17.

#### Acceptance Criteria

1. WHEN the Reachability_Suite submits the representative text `what is my balance`, THE Ingress_Router SHALL return code `ROUTED`, module `mal` and effect `pfos_read`.
2. WHEN that turn is admitted, THE Turn_Admission SHALL return branch `governed_deterministic`.
3. WHEN that turn is processed, THE Reachability_Suite SHALL observe that the Turn_Classifier was never called and that no model channel was invoked.
4. WHEN that turn is answered, THE reply SHALL contain the deterministic `resultRef` and SHALL contain digits byte-identical to each `fact.amountMilliunits`, stated as integer milliunits.
5. WHEN that turn is answered, THE Governed_Turn_Path SHALL have run both financial assertions in the order of Requirement 3.4 before composing the reply.

---

### Requirement 17: Reachability R-3 and R-3b — explanatory finance wording is deterministic, and the tier path is guarded separately

**User Story:** As the owner, I want an explanatory money question answered by the engine rather than discussed by a model, and I want the model tier's survival proved on a turn that actually reaches it, so that a regression guard is not pointed at a path that does not exist.

Vehicle: **automated**. Acceptance criteria in design: **AC-I1-13** (R-3), **AC-I1-13b** (R-3b).

**Correction (this pass).** §X.2 finding 1 flagged that design.md never quoted the router's money lexicon, and criterion 17.5 existed to make an R-2/R-3 conflict fail loudly. **The conflict was real and R-3 was wrong.** `FINANCE` in `src/server/hermes/ingressRouter.ts` explicitly contains `\bsafe to spend\b` (**VERIFIED** by direct reading; now quoted verbatim in design **§D.7.1.1**), so `how much is safe to spend` routes `ROUTED` · `mal` · `pfos_read` and is admitted `governed_deterministic` — **no model**. R-3 is re-specified below from source, and **R-3b** is added inside this requirement as the tier-path guard, using a `SHURA` phrase that carries no `FINANCE` token. **No fixture text was changed to preserve the old expectation, and no lexicon was edited.** Criterion 17.5 is retained. Requirement numbering is unchanged; R-3b lives here rather than as a new requirement number.

#### Acceptance Criteria

**R-3 — explanatory finance wording (re-specified from source):**

1. WHEN the Reachability_Suite submits the representative text `how much is safe to spend`, THE Ingress_Router SHALL return code `ROUTED`, module `mal` and effect `pfos_read`, and THE Turn_Admission SHALL return branch `governed_deterministic`.
2. WHEN that turn is processed, THE Reachability_Suite SHALL observe that the Turn_Classifier was never called, that no `ModelInvocationGrant` exists for the turn, and that no model channel was invoked.
3. WHEN that turn is answered, THE reply SHALL be either the verified-deterministic reply of Requirement 16.4 or a digit-free unavailable/refused reply, and SHALL NOT be a model-composed sentence.

**R-3b — the tier-path regression guard:**

3a. WHEN the Reachability_Suite submits a representative `SHURA` text containing no `FINANCE` token — for example `plan with me the week ahead` — THE Ingress_Router SHALL return code `ROUTED`, module `shura` and effect `read`, and THE Turn_Admission SHALL return branch `tier_path`.
3b. WHEN that turn is processed, THE Turn_Classifier SHALL be called, a `ModelInvocationGrant` SHALL be minted, and a fake model channel SHALL record that the minted grant reached it.
3c. WHEN that turn is answered, THE reply SHALL be digit-free, and THE model tier SHALL source no figure.
3d. WHILE any representative text for R-3b contains a `FINANCE` token, THE Reachability_Suite SHALL fail, because such a text routes `pfos_read` and cannot exercise the tier path.

**Both cases:**

4. WHEN the Reachability_Suite runs, THE suite SHALL use a fake model channel and SHALL cause no real provider invocation and no provider spend.
5. IF the Ingress_Router's lexicon and a reachability case's expected route disagree, THEN THE Reachability_Suite SHALL fail and report a lexicon conflict naming both cases, and SHALL NOT reclassify a case or edit a fixture to make the suite pass. *(Retained. It is now satisfied by an actual resolution — the R-2/R-3 conflict it guarded was resolved from source, not by editing a fixture — and it continues to govern any future conflict.)*
6. THE Planning_Program SHALL quote the `FINANCE` and `JOURNAL` patterns verbatim, so that no reachability case rests on an unquoted lexicon. *(Satisfied by design §D.7.1.1.)*

---

### Requirement 18: Reachability R-4 — secret-seeking text

**User Story:** As the owner, I want a request for a secret refused at zero cost, so that a refusal never becomes a bill.

Vehicle: **automated**. Acceptance criterion in design: **AC-I1-14**.

#### Acceptance Criteria

1. WHEN the Reachability_Suite submits secret-seeking text, THE Ingress_Router SHALL return code `REFUSED_SECRET`, module `refuse` and effect `none`.
2. WHEN that turn is admitted, THE Turn_Admission SHALL return branch `governed_deterministic` and THE turn SHALL be settled from `route.publicReason`.
3. WHEN that turn is processed, THE turn SHALL produce zero effect, THE Reachability_Suite SHALL observe that no port was touched, and THE fake model channel SHALL record no invocation.
4. WHEN that turn is answered, THE reply SHALL leak no reason for the refusal.

---

### Requirement 19: Reachability R-5 — ambiguous text

**User Story:** As the owner, I want an unclear message answered with a question, so that ambiguity never silently turns into a paid conversation.

Vehicle: **automated**. Acceptance criterion in design: **AC-I1-15**.

#### Acceptance Criteria

1. WHEN the Reachability_Suite submits text matching nothing in the Ingress_Router, THE router SHALL return code `CLARIFY`, module `clarify` and effect `none`.
2. WHEN that turn is admitted, THE Turn_Admission SHALL return branch `governed_deterministic` and THE turn SHALL produce zero effect.
3. WHEN that turn is answered, THE reply SHALL ask the owner to clarify.
4. WHEN that turn is processed, THE turn SHALL NOT become a paid conversational turn by way of `DEFAULT_PROSE_INTENT`, and THE fake model channel SHALL record no invocation.

---

### Requirement 20: Reachability gate on the vertical slice

**User Story:** As the owner, I want the slice declared successful only when it is actually reachable, so that dead code is never reported as a delivered capability.

Vehicle: **automated** (the suite), **document review** (the claim).

**Correction (this pass).** The gate now covers **six** cases — R-1, R-2, R-3, R-3b, R-4, R-5 — carried by Requirements 15, 16, 17 (which holds both R-3 and R-3b), 18 and 19. The requirement count is unchanged at five; the case count moved from five to six.

#### Acceptance Criteria

1. WHILE any of Requirements 15, 16, 17, 18 and 19 is unsatisfied, THE Implementation_Program SHALL NOT claim the vertical slice successful, even WHERE every other I1 acceptance criterion passes.
2. WHEN all six reachability cases pass, THE Implementation_Program SHALL record that the slice's two halves — deterministic PFOS read and authorized native capture — are both reachable.
3. WHEN a reachability case fails, THE Reachability_Suite SHALL fail loudly with the failing case identified, and SHALL NOT degrade to a passing weaker assertion.
4. THE Reachability_Suite SHALL carry R-3 and R-3b as **two distinct cases**, and SHALL NOT treat R-3 as the tier-path guard, because R-3 no longer reaches the model tier.
5. WHEN the reachability matrix is read, THE Implementation_Program SHALL record that under **D-8** option (a) the model tier is reachable **only** from effect `read` — the journal-read variant of module `yawmiyat`, plus `shura`, `naqd`, `qarar` and `thabat` — and therefore that **no finance wording of any kind reaches a model**. That is a stronger money guarantee than design §D.7.2's table claimed, and simultaneously the capability gap recorded as **D-12**.

---

### Requirement 21: Capture receipt honesty

**User Story:** As the owner, I want "Captured" to mean an independent read-back agreed, so that the word carries evidence rather than a returned string.

Vehicle: **automated**. Acceptance criterion in design: **AC-I1-16**.

#### Acceptance Criteria

1. WHEN a capture receipt reports `readBackConfirmed` true and `hashMatch` true, THE Governed_Turn_Path SHALL record outcome `captured` and SHALL reply with the word "Captured", the writer's own `entryRef`, and a statement that read-back is confirmed.
2. WHERE `readBackConfirmed` and `hashMatch` are not both true, THE reply SHALL omit the word "Captured", and a returned `entryRef` alone SHALL NOT satisfy the condition for that word.
3. WHEN a capture receipt reports state `LOCAL_WRITTEN` without both confirmations, THE Governed_Turn_Path SHALL record outcome `captured_unconfirmed` and SHALL reply that the entry is recorded locally and not yet confirmed.
4. WHEN a capture receipt reports state `STAGED_RETRY`, THE Governed_Turn_Path SHALL record outcome `captured_unconfirmed` and SHALL reply with the same weaker wording.
5. IF a capture receipt reports state `FAILED`, or `record` is `null`, or the `appendRecord` call throws, THEN THE Governed_Turn_Path SHALL record outcome `capture_refused` and SHALL reply that nothing durable exists, without the word "Captured".
6. WHEN a read-back disagrees with the expected payload hash, THE journal adapter SHALL report state `FAILED`, and THE Governed_Turn_Path SHALL treat that as `capture_refused`.
7. WHEN the Governed_Turn_Path reports a capture, THE reported `entryRef` SHALL be the writer's own value and SHALL NOT be locally invented.
8. WHILE the native writer is not established to satisfy the `JournalPersistenceReceipt` shape with independent read-back, THE Governed_Turn_Path SHALL treat a remote capture as `captured_unconfirmed`.

---

### Requirement 22: Capture ordering, idempotence, and honest delivery semantics

**User Story:** As the owner, I want a network hiccup to re-send my confirmation, not re-record my thought, so that one message never becomes two journal entries — and I want to be told plainly that a re-sent confirmation may reach me twice, rather than being promised a guarantee the transport cannot give.

Vehicle: **automated** (22.1–22.12), **document review** (22.13, 22.14). Acceptance criteria in design: **AC-I1-17**, **AC-I1-18**, **AC-I1-19**. Blocked on **D-11**.

**Correction (this pass).** Criterion 22.5 previously read *"WHEN a process restarts after a canonical write and before a send, THE system SHALL contain exactly one canonical entry and SHALL deliver exactly one reply."* The delivery half is **retracted**. Three guarantees were conflated and are now stated separately: **(i)** canonical-write exactly-once — **guaranteed** by `recordId`; **(ii)** settlement idempotence — **guaranteed** by the `state = 'running'` predicate; **(iii)** external delivery exactly-once — **NOT guaranteed**, and not achievable with the transport as it stands. See design **§L.12**, which is the authority for this requirement. The five-step ordering of 22.1 is unchanged.

#### Acceptance Criteria

1. WHEN a capture turn is processed, THE Governed_Turn_Path and THE Turn_Worker SHALL perform, in this order: the canonical write, the verified read-back, the reply composition from observed receipt fields, the send, and the settle as `done`.
2. IF a crash or a send failure occurs between the canonical write and the settle, THEN THE queue SHALL re-deliver the item and THE Governed_Turn_Path SHALL NOT re-write the canonical entry.
3. WHEN a capture turn is replayed, THE `recordId` SHALL be `captureRecordId(item.queuedRef)`, a pure function of the queue ref, and SHALL be byte-identical to the first attempt's value.
4. WHEN a capture turn is replayed with an identical payload, THE journal adapter SHALL report mode `IDEMPOTENT_REPLAY` and SHALL return the same `entryRef`, and THE writer SHALL perform no second canonical write.
5. WHEN a process restarts after a canonical write and before a send, THE system SHALL contain exactly one canonical entry, and THE reply SHALL be delivered at least once.
6. THE `captureRecordId` function SHALL derive the record identity from the queue ref and SHALL NOT derive it from the payload.
7. THE `updatePolicy` SHALL remain at its default `REFUSE`; IF a replay carries a different text under the same `recordId`, THEN THE journal adapter SHALL refuse with `JOURNAL_UPDATE_NOT_PERMITTED` and THE Governed_Turn_Path SHALL record `capture_refused`.
8. WHEN an item is claimed and left unsettled beyond its lease, THE `reclaimExpired` call — which delegates to `workQueueRepo.reclaimStalledWork` — SHALL return it to `queued` and THE Turn_Worker SHALL re-process it as a later attempt.
9. THE delivery semantics of the reply leg SHALL be **at-least-once**, and THE Implementation_Program SHALL NOT represent them as exactly-once; exactly-once SHALL be claimed of the canonical journal write only.
10. WHEN a send is accepted by the provider and its acknowledgement is lost (**Case D-A**), THE bounded outbound retry SHALL re-send, THE owner MAY receive the reply twice, and THE duplicate SHALL be reported in the redacted observation rather than silently swallowed.
11. WHEN a send succeeds and the process crashes before the settle (**Case D-B**), THE row SHALL be reclaimed to `queued` and re-processed; THE canonical write SHALL be suppressed by `recordId` dedup so that exactly one canonical entry exists; and THE reply SHALL be re-issued, so THE owner MAY receive it twice.
12. WHEN `settleWork` is called more than once for one `queuedRef` with outcome `done`, THE second and every later call SHALL report `settled: false` and SHALL write nothing.
13. THE Planning_Program SHALL NOT claim exactly-once **delivery** without either verified transport-level idempotency or a delivery-reconciliation record; and WHERE neither exists, THE Planning_Program SHALL state the at-least-once semantics plainly to the owner.
14. WHILE decision **D-11** is unanswered, THE Implementation_Program SHALL treat the shape of the send/settle leg as unfixed, SHALL implement no duplicate-suppression workaround, and SHALL weaken no acceptance check to accommodate a duplicate.

---

### Requirement 23: Seam shape, worker wiring and rollback

**User Story:** As the owner, I want an asynchronous deterministic read to fit the existing seam without weakening the argument that protects it, so that a convenience does not cost an invariant.

Vehicle: **automated**. Governed by **D-9**.

#### Acceptance Criteria

1. THE Turn_Worker SHALL instantiate the dispatch generic as `Answer = Promise<string>`, and THE `renderAnswer` dependency SHALL remain the identity function.
2. THE `renderAnswer` dependency SHALL declare the return type `string | Promise<string>`, and THE Turn_Worker SHALL await its result on the `code_only` route.
3. THE `turnDispatch.ts` module SHALL receive no edit, so that its deterministic branch still returns before any `await`.
4. THE Turn_Worker SHALL accept an optional `executeTurnDeterministically` dependency that overrides `executeDeterministically` for one item only, and SHALL use the supplied dependencies unchanged WHEN that override is absent.
5. WHEN the `executeTurnDeterministically` override is supplied, THE override SHALL hold no `ModelInvocationGrant` and SHALL be unable to reach `channel.invoke`.
6. THE `main.ts` composition SHALL build the governed executor once and SHALL take a per-item closure per turn.
7. THE `main.ts` composition SHALL retain `answerDeterministically` as the fallback deterministic executor on the dispatch path.
8. WHEN increment I1 is rolled back by removing the `executeTurnDeterministically` line from `main.ts` and the admission branch from `turnWorker.ts`, THE system SHALL revert to the current behaviour, SHALL require no data change and no migration, and THE Planning_Program SHALL record that the rollback restores the reachability defect.
9. THE widened `renderAnswer` return type SHALL remain backward compatible, because `string` is assignable to `string | Promise<string>`.

---

### Group D — Increments I2 through I7

### Requirement 24: I2 — scheduled jobs as a consumer

**User Story:** As the owner, I want scheduled work to ride the clock that already exists, so that nothing in the system has two opinions about when.

Vehicle: **automated**. Depends on I1. Approval: for the offline half, **Stage 1 only.** A real-host run remains Stage 2 and is blocked by A14 and D-4.

#### Acceptance Criteria

1. THE `SCHEDULER_TARGETS` tuple SHALL remain `['life','finance']`.
2. THE `listeningPorts` value SHALL remain an empty constant with no writer.
3. WHEN a registered job throws, THE tick SHALL not throw and `isTicking()` SHALL remain true.
4. THE tree SHALL contain no second timing source, and a source-level assertion SHALL confirm that property.
5. WHEN a job needs a last-run timestamp, THE Scheduled_Jobs_Registry SHALL use the existing `kv` table rather than a new table.
6. WHEN a job's planner runs, THE planner SHALL be pure and deterministic, and its effect SHALL be injected.
7. WHEN a long job would overlap the next tick, THE Scheduled_Jobs_Registry SHALL guard the job with a claim-style lease reusing the queue's mechanism.
8. WHEN a process restarts, THE last-run state SHALL survive and no job SHALL run twice for one due period.
9. WHEN an endpoint outside the internal range is addressed, THE existing internal-endpoint refusals SHALL reject it.
10. THE increment I2 SHALL implement no part of O6's cadence, which is blocked on **D-2**.

---

### Requirement 25: I3 — Drive discovery

**User Story:** As the owner, I want discovery limited to files I approved and treated as untrusted, so that a document can inform an answer without ever instructing the system.

Vehicle: **automated**. Depends on I0 and I2. Approval: for the offline half, **Stage 1 only.** Any Drive token operation, any real-data discovery run, and any enumeration beyond app-created or explicitly-picked files remain Stage 2, the last additionally requiring owner authorisation **and** a policy amendment.

#### Acceptance Criteria

1. THE Drive_Discovery SHALL operate under `drive.file` scope only, and SHALL enumerate only app-created files and files the owner explicitly picked.
2. WHEN discovered content enters a request boundary, THE content SHALL be labelled untrusted data, never an instruction, never a tool request, and never authority over policy or deterministic financial facts.
3. WHEN an instruction-shaped payload appears in discovered content, THE system behaviour SHALL be unchanged.
4. WHEN a discovery packet is composed, THE packet size SHALL be bounded.
5. IF a discovery packet is modified, THEN THE packet's own integrity check SHALL fail.
6. WHEN the discovery job is disabled, THE discovery index SHALL become inert and SHALL require no data change.

---

### Requirement 26: I4 — deterministic alerts

**User Story:** As the owner, I want an alert to be a deterministic threshold crossing, so that the system never wakes me with a guess.

Vehicle: **automated**. Depends on I2. Approval: for the offline half, **Stage 1 only.** Live delivery remains Stage 2.

#### Acceptance Criteria

1. WHEN an alert carries a figure, THE figure SHALL trace to a `DeterministicFinancialFact`.
2. THE Deterministic_Alerts SHALL compose no figure from a model result.
3. WHEN the same threshold condition persists, THE Deterministic_Alerts SHALL deduplicate the alert, and THE deduplication state SHALL survive a restart.
4. WHEN alerts would exceed the configured per-window cap, THE Deterministic_Alerts SHALL withhold the excess.
5. WHILE the model channel is shut, THE deterministic alert route SHALL still answer.

---

### Requirement 27: I5 — cross-agent handoffs over bounded signals

**User Story:** As the owner, I want agents to exchange bounded state and never raw ledger rows, so that a handoff cannot become a data leak or an authority channel.

Vehicle: **automated**. Depends on I1. Approval: for the offline half, **Stage 1 only.** Live cross-agent operation remains Stage 2 and is blocked by A14.

#### Acceptance Criteria

1. THE signal payload keys and result keys SHALL match no part of `AUTHORITY_KEY`.
2. THE `nizam` and `pfos` profiles SHALL share no OpenRouter key, no weekly cap and no store entry, as asserted by `assertIngressKeepsInternalIsolation`.
3. WHEN a signal is published, THE payload SHALL be bounded state and SHALL carry no grant.
4. IF a cross-profile signal is attempted, THEN THE system SHALL refuse it rather than downgrade it.
5. THE Signal_Bus SHALL write to `signals.db` only, preserving store separation by ownership.
6. WHEN publishing stops, THE readers SHALL see no new signals and SHALL require no data change.

---

### Requirement 28: I6 — continuity

**User Story:** As the owner, I want a mirror to claim success only after it reads itself back, so that continuity is verified rather than assumed.

Vehicle: **automated**. Depends on I0, I3 and I5. Approval: for the offline half on synthetic data, **Stage 1 only.** Any Drive write of real data remains Stage 2 and is blocked by G5 and G8.

#### Acceptance Criteria

1. WHEN a continuity record reaches state `DRIVE_MIRRORED`, THE state SHALL imply a verified read-back.
2. IF a mirror attempt fails, THEN THE continuity state SHALL NOT report `DRIVE_MIRRORED`.
3. WHEN a continuity payload is written to Drive, THE payload SHALL be encrypted by Payload_Envelope.
4. IF a mirrored file is altered, THEN THE read-back SHALL fail.
5. WHEN a process restarts while a record is in state `STAGED_RETRY`, THE continuity process SHALL resume that record.
6. THE continuity migration SHALL be versioned, and THE migration SHALL move no monetary field.
7. WHERE the `mirrorApproved` dependency returns false, THE journal adapter SHALL attempt no mirror call and SHALL still reach state `LOCAL_WRITTEN`.
8. IF the `permitted` consent guard throws, THEN THE system SHALL treat the throw as a denial.

---

### Requirement 29: I7 — recovery

**User Story:** As the owner, I want a restore I have actually watched succeed, so that the backup is a backup rather than a hope.

Vehicle: **automated** (29.1–29.4 on synthetic data), **owner observation** (29.5–29.7). Depends on I6. Hard-blocked on **G8**.

#### Acceptance Criteria

1. WHEN an encrypted archive is created and then restored to a scratch location, THE restored data SHALL equal the source synthetic data.
2. IF a restore is attempted with the wrong key, THEN THE Recovery_Rehearsal SHALL refuse.
3. IF an archive is mutated, THEN THE Recovery_Rehearsal SHALL refuse it.
4. WHEN a restore is interrupted, THE Recovery_Rehearsal SHALL either resume the restore or refuse cleanly.
5. THE restore SHALL be independently observed, and a rehearsal that is never exercised SHALL NOT be recorded as a backup.
6. WHILE gate **G8** is not satisfied, THE Implementation_Program SHALL produce no archive of real data, because an archive produced before G8 voids the ciphertext-only guarantee retroactively for every archive.
7. WHEN a rehearsal fails, THE Implementation_Program SHALL record the failure as a finding, because recovery is exercised rather than deployed.

---

## §Y Deliberately out of scope

Recorded so that absence is a decision rather than an oversight.

| Item | Why it is out of scope | Where it is recorded |
|---|---|---|
| **FX history storage shape** (design §H.5) | The stored collection is keyed by currency in `NetWorthView.tsx` and in `sync.ts`, so a rate history cannot be retained even though `fx.ts` can order one. Fixing it touches the browser schema and UI, which this program does not otherwise open, and it interacts with the I0 envelope version. **Owner-facing consequence: historical net-worth valuations are currently unreliable by storage shape, not by arithmetic.** | design §H.5; no requirement in this document |
| **Registering O1–O11 as top-level objectives** | Mechanically refused by `objectiveRegistry.ts` and blocked on **D-1**. | Requirement 2.4, Requirement 8.6 |
| **O6's three-briefs-and-twice-daily cadence** | No contract grants it; blocked on **D-2**. | Requirement 8.4, Requirement 24.10 |
| **Unifying the four stores into one ledger** | Contract 06 separates stores by ownership deliberately; unification is a larger program than the one commissioned. | design §H.4; Requirements 27 and 28 carry the narrower additive positions |
| **Any edit to `nizamcore`** | Separate, owner-gated repository. | Requirement 8.12 |
| **A new acceptance check for the `AC12` gap or the Drive-encryption gap** | Changing the declared check count is a harness change and therefore an owner decision. | Requirement 7.9, Requirement 7.10 |

---

## §X Discrepancies and gaps found while deriving

design.md wins on every point below; each is recorded rather than reconciled.

### X.1 Prompt-versus-design discrepancies

| # | Prompt statement | design.md | Resolution |
|---|---|---|---|
| 1 | R-1 and R-2 route to the "deterministic branch". | §D.7.2 and §E.5: both route to branch **`governed_deterministic`**, taken **before** `classifyTurn` and `dispatchTurn` are consulted. The T0 "deterministic branch" of `dispatchTurn` is a different thing and is not the one taken. | Requirements 15.2 and 16.2 use `governed_deterministic`; Requirements 15.3 and 16.3 assert the classifier was never called. |
| 2 | Capture ordering is "canonical write → verified read-back → send → settle done". | §D.4.5 has **five** steps, with **compose reply from observed receipt fields** between read-back and send. | Requirement 22.1 states all five. |
| 3 | Baseline is 19/21. | §J.2 agrees on the number, but labels the **measurement** STALE (2026-09-16 receipt) while labelling the **cause** VERIFIED. | Requirement 7.5 carries both labels. |
| 4 | design.md is 1890 lines. | The file read this session ends at §K.3 at approximately line 1917. | Immaterial to content; recorded for accuracy. |

### X.2 Gaps inside design.md

1. **The Ingress_Router money lexicon was never quoted — ~~UNRESOLVED~~ → RESOLVED (this pass), and R-3 was wrong.**

   *The finding, as originally recorded:* design §A.3 and §D.7.1 quoted the `JOURNAL` pattern verbatim, but no section quoted the `mal` / money pattern. R-2 asserted `what is my balance` routes to `mal`/`pfos_read` and R-3 asserted `how much is safe to spend` does **not**, yet both claims rested on an unquoted lexicon, and both texts contain money-adjacent words. **If one pattern matched both, R-2 and R-3 could not both hold.**

   *The resolution, from source.* `src/server/hermes/ingressRouter.ts` was read directly. **VERIFIED:**

   ```ts
   const FINANCE =
     /(?:\bbalance\b|\bbudget\b|\bdebt\b|\bforecast\b|\bsafe to spend\b|\bmilliunit\b|\bcard bill\b|\bnet worth\b|\bmal\b|\bpfos\b)/iu;
   ```

   `FINANCE` **explicitly contains `\bsafe to spend\b`.** Both fixtures match `FINANCE`, neither matches `JOURNAL`, so both take the same `finance` branch. `deriveIntent` then selects the tool, and only `evaluate_financial_decision` selects `pfos.run_deterministic_analysis`; `PROSE_INTENTS` maps `safe to spend` → `explain_safe_to_spend` and `balance` → `recalculate_balances`, so **both fixtures yield `ROUTED` · module `mal` · effect `pfos_read`**. Therefore:

   - **R-2 holds.** Requirement 16.1 is confirmed.
   - **R-3's premise is false.** Under **D-8** option (a), `pfos_read` ⇒ `governed_deterministic` ⇒ **no model**. design §E.5's original R-3 ("conversational ⇒ tier path ⇒ model permitted") contradicted the router.
   - **design.md already contained the correct answer.** §D.7.3's comparison table asks *"Fixes the `'safe to spend'` case?"* and answers **"Yes, because the router's `mal`/`pfos_read` verdict decides, not the prose lexicon."* So §D.7.3 and §E.5 R-3 contradicted each other; §D.7.3 wins.

   *What changed.* Both patterns are now quoted verbatim in design **§D.7.1.1**. R-3 is re-specified in §E.5 as *"explanatory finance wording is deterministic, not conversational"*, and **R-3b** was added inside Requirement 17 as the tier-path guard using a `SHURA` phrase carrying no `FINANCE` token. **No fixture was edited to preserve the old expectation and no lexicon was changed.** Requirement 17.5 is retained and is now satisfied by an actual resolution.

   *The larger consequence, recorded as **D-12**.* `IngressRoute['effect']` is `'none' | 'read' | 'local_write' | 'pfos_read'` — **there is no conversational or model effect at all**. Under `admitTurn` mapping only `read` to `tier_path`, a model is reachable only from effect `read`: the journal-**read** variant of `yawmiyat`, plus `shura`, `naqd`, `qarar` and `thabat`. **No finance wording of any kind reaches a model**, and anything matching nothing falls to `CLARIFY` (effect `none`), which is also not the model. That is a *stronger* money guarantee than design claimed, and simultaneously a **capability gap**: the explanatory finance conversation R-3 was written to exercise is not a reachable behaviour. Recommended default **(a) leave it unreachable**; **not decided**.

   *One precision on the prompt's framing of this consequence.* The commissioning note said the model tier is reachable "only via `shura` / `naqd` / `qarar` / `thabat`". The journal branch also yields effect `read` when the text carries a read verb (`read`/`show`/`what did i`), so `yawmiyat` reaches `tier_path` too. It is still finance-free, so the money invariant is unaffected — but the model-reachable set is five routes, not four.
2. **New-file count is internally inconsistent.** §D.5's diff table lists four new files and the prose says "four new files"; §G.1's Files/symbols row additionally names `effectiveToolSurface.ts` and its test, making **six**. Requirement 4 keeps the effective-surface module in scope; the count itself is left to design.md to correct.
3. **`governedTurnPath` step 4 is unreachable under D-8 option (a).** `admitTurn` sends `effect: 'read'` and every other effect to `tier_path`, so a turn admitted as `governed_deterministic` can only carry `none`, `local_write` or `pfos_read`. The executor's fallback to `answerDeterministically` is therefore dead on that branch, and is reachable only through the retained `dispatch.executeDeterministically`. Requirement 13.6 keeps the branch specified; Requirement 23.7 keeps the retained fallback. Whether the dead branch stays as a guard is a design.md matter.
4. **AC-I0-1's verification vehicle is ambiguous.** §G.0 asks for "a source-level check, in the spirit of `AC08`", while §J.1 and §K.2 forbid adding a check to the declared twenty-one without an owner decision. Requirement 10.1 therefore specifies a source-level assertion **as a test**, not as a new harness check.
5. **"Journal content is written only by the native writer" is convention, not mechanism.** design §I.3 says so outright: the local adapter demonstrably can write a local file. Requirement 6.12 captures the part that *is* mechanical — `appendRecord` only, never `appendWithReceipt`.

6. **Exactly-once *delivery* was overclaimed — RESOLVED (this pass) by retraction.** design §D.4.5, §G.1's Tests row and §L.5 Property 22 each promised *"exactly one canonical entry, exactly one delivered reply"*, §L.5 generalising it to **any** interruption point. The `recordId` journal dedup guarantees **one canonical entry**, not **one external delivery**; the two were conflated. Verified from source this pass:

   - `TelegramTransportClient.sendMessage(message: TelegramOutboundMessage): Promise<TelegramSendReceipt>` — **no idempotency key of any kind**; `TelegramOutboundMessage` is `{ botId, chatRef, … }` with **no correlation ref**. **VERIFIED** (`liveTransport.ts`, `ports/telegram.ts`).
   - The outbound leg retries a `TelegramRateLimitRefusal` using `sendRetryDelayMs` up to `send.maxAttempts`, with **nothing to suppress a duplicate**. **VERIFIED.**
   - `TelegramSendReceipt` is returned and then **discarded**: `turnWorker` awaits `sendReply` and returns `{ outcome: 'done' }` without persisting it, so it is never reconciled against a prior send for the same `queuedRef`. **VERIFIED.**
   - `RECLAIM_STALLED_SQL` returns a crashed `running` row to `queued` and `CLAIM_SQL` increments `attempts`, so **re-sending is the designed recovery**. **VERIFIED.**
   - `SETTLE_DONE_SQL`'s `AND state = 'running'` predicate makes settlement idempotent — which is about **the row**, not the send. The module's own note (*"cannot be made to double-count by the retry that follows"*) is a claim about the settlement, not about the delivery. **VERIFIED.**

   *What changed.* design **§L.12** now states the honest semantics — **at-least-once delivery, with an idempotent canonical write** — separates the three guarantees (canonical-write exactly-once: guaranteed; settlement idempotence: guaranteed; external delivery exactly-once: **not** guaranteed), models the two interruption points **Case D-A** (send accepted, acknowledgement lost) and **Case D-B** (send succeeded, crash before settle), and lists five proposed failure-injection cases **FI-1 … FI-5** as planned tests. Requirement 22 is reconciled and criteria 22.9–22.14 were added. The decision is **D-11**; recommended default **(b)** a delivery-reconciliation record, which **narrows the window and does not close it**. **Not decided.** No workaround was implemented, no acceptance check was weakened, and no fixture was changed.

### X.3 Requirements that are not automatically testable

Stated plainly rather than disguised as automatable.

| Requirement | Why | Vehicle |
|---|---|---|
| 1.1–1.6 | Approval is a human act. No test can observe that an owner approved a plan. | document review |
| 2.5, 2.6, 2.8 | Assertions about how artifacts describe things, and about the deliberate absence of a commit. `AC14`/`AC15` observe tree state but do not encode intent. | document review |
| 7.5–7.10 | Statements about labels, scope and coverage of the harness — verifiable by reading `all.mjs` and `contract-ledger.mjs`, not by running them. | document review |
| 8.1–8.12 | Decision state is owner state. | document review |
| 9.1–9.4 | Label discipline in prose. | document review |
| 12.4, 12.5 | Credential and gate state is owner-held and INACCESSIBLE from a planning session. | owner observation |
| 20.1–20.2, 20.5 | The *claim* about slice success and the record of the reachability consequence are human statements; the six underlying cases are fully automated. | document review over automated evidence |
| 22.13, 17.6 | Statements about how artifacts word a claim — that no artifact claims exactly-once delivery, and that both lexicons are quoted. Verifiable by reading design.md, and partially mechanisable as a text assertion over the spec files (design §L.5 Property 22b). | document review |
| 29.5–29.7 | An independently observed restore, and gate G8, are owner acts. | owner observation |

