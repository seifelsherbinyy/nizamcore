# Implementation Plan: hermes-governed-workflows

Spec: `hermes-governed-workflows` · Workflow: design-first · Type: feature
Derived from `design.md` (§0–§L, corrected) and `requirements.md` (29 requirements, corrected). **design.md wins on conflict.**

---

# ⛔ STAGE-1 GATE — READ BEFORE ANY TASK BELOW

> ## EVERY TASK IN THIS FILE IS BLOCKED PENDING STAGE-1 OWNER APPROVAL OF THE PLAN.
>
> **No task below may begin.** Not the first one. Not a "small" one. Not a test file. Not a type widening. Not a one-line dependency at a composition root. Stage-1 plan approval — explicit owner approval of `design.md` plus `requirements.md` — is a **precondition of all implementation**, and implementation includes **local and offline code changes and test changes** (design §0.5; Requirement 1.1).
>
> **There is no "no approval required" category in this file.** Where a task requires Stage-1 plan approval and nothing beyond it, its Approval boundary reads exactly **"Stage 1 only."** That phrase never means "no approval" (Requirement 1.2, 1.3).
>
> **Stage 2 is separate and is never implied by Stage 1.** Live operation (a bound transport, a real ingress consumer), deployment, credentials (minting, rotation, consent, scope), host mutation (provisioning, unit edits, service restarts, DNS), provider spend (any paid model call), and the human gates **G1–G8** in `ops/DEPLOYMENT_CONTROL.md` each require their own Stage-2 approval on its own merits. A green test suite, a green repository gate, an old receipt, or an earlier increment's approval authorizes **none** of them (Requirement 1.4, 1.5).
>
> **This tasks.md is a planning artifact and confers no implementation authorization.** It records what the work must satisfy *if and when* the owner approves the plan. It resolves no owner decision. It adopts no `[AGREED]` marker found anywhere in the evidence base as an owner choice (Requirement 1.6, 9.3).

**Second gate, upstream of Stage 1 in practice.** Phase 0 answers must exist before Phase 1 and Phase 2 code can be written coherently, because the open decisions change *which files get written*. **D-8** decides I1's file list. **D-5** decides whether `payloadEnvelope.ts` exists at all and what it contains. **D-11** decides whether the send leg carries a persisted reconciliation record. **D-2 and D-6 carry `None offered` and must not receive an invented default.**

**Two standing cautions apply to every task (design §0.4).**

- A documented status is not fresh verification. A checked box can mean the check ran and failed.
- **Test success is not live readiness.** A green offline suite establishes composition and refusal behaviour on synthetic fixtures. It establishes nothing about a running host, a bound transport, a loaded MCP surface, or a real ledger.

---

## Overview

*Placed **after** the Stage-1 gate deliberately: the gate stays the first content block in this file, and the `## Task Dependency Graph` JSON block stays the final section.*

This plan sequences the governed conversational workflow of `design.md` into **19 top-level tasks and 59 leaf sub-tasks** across **nine phases** — a Phase 0 decision gate that writes no code, then increments **I0 → I7** in dependency order.

| Phase | Increment | Tasks | Scope in one line |
|---|---|---|---|
| **0** | Decision gate | 1–3 | Surface **D-1 … D-12** as briefs, author the amendment and honest-claims register. **No code.** |
| **1** | **I0** Drive envelope + candidate egress | 4–5 | Application-level encryption before every `createTextFile`, one serialisation-time candidate projection. **First, because it is retroactive.** |
| **2** | **I1** the governed vertical slice | 6–12 | Pre-tier admission, the governed deterministic path, the worker seam, the **six**-case reachability gate, the effective-surface assessor, the invariant net. |
| **3** | **I2** scheduled jobs | 13 | A **consumer** behind the existing `finance` tick. No second clock. |
| **4** | **I3** Drive discovery | 14 | Bounded, `drive.file`-scoped, untrusted-by-construction. |
| **5** | **I4** deterministic alerts | 15 | Threshold crossings only; every figure traces to a `DeterministicFinancialFact`. |
| **6** | **I5** cross-agent handoffs | 16 | Bounded signals, zero tools added. |
| **7** | **I6** continuity | 17 | Verified read-back before `DRIVE_MIRRORED`; encrypted mirror. |
| **8** | **I7** recovery | 18–19 | Archive-and-restore rehearsal on **synthetic** data. Hard-blocked on **G8**. |

**Four things to carry into every task below.**

- **Nothing here is authorization.** Every task is blocked pending **Stage-1** plan approval, and every Stage-2 item — live operation, deployment, credentials, host mutation, provider spend, **G1–G8** — remains separate. Where a task needs nothing beyond Stage 1, its Approval boundary reads exactly **"Stage 1 only."**
- **Phase 0 is the real blocker.** **D-8** decides I1's file list, **D-5** decides whether I0 has a module to write, **D-11** decides the shape of the send leg. **D-2 and D-6 carry `None offered` and must not receive an invented default.**
- **Delivery is at-least-once.** Exactly-once is claimed of the **canonical journal write** only.
- **Two coverage gaps are recorded and not filled**, and the declared harness count stays **21**. The expected gate result is **19 of 21**.

The per-increment observable acceptance criteria, the baseline detail, the two coverage gaps and the five failure-injection items live in the companion checklist — see the next section for why it is a separate file.

---

## Where the acceptance / smoke checklist lives

**Chosen: a separate file — `.kiro/specs/hermes-governed-workflows/acceptance-checklist.md`.**

Reason: this workflow's `tasks.md` format requires the machine-parsed `## Task Dependency Graph` JSON block to be **appended after the task list and notes**, i.e. to be the final section. The checklist is a multi-section gate artifact (repository gates, the 19-of-21 baseline, the git-independent green set, two named coverage gaps, five failure-injection items, and per-increment observable acceptance criteria). Embedding it would either displace the parsed graph from the end of the file or bury the graph mid-document. It is also referenced *per increment* rather than executed once, so it reads better as a standing companion artifact than as a tail section of a task list.

---

## How to read a task

Each **top-level task** carries: **Owning contract / amendment** · **Prerequisites** (including which of **D-1 … D-12** must be answered first) · **Requirements covered** · **Rollback** · **Approval boundary** (the Stage-1 / Stage-2 split).

Each **sub-task** carries the concrete **files and symbols**, its own `_Requirements: N.M_` citations, and the **tests** it must produce.

- Sub-tasks postfixed with `*` are optional supplementary tests and may be skipped for a faster path. **Sub-tasks that constitute a design gate are never marked `*`** — the six reachability cases and the five failure-injection cases are gates, not extras.
- Amendment-record tasks author a **dated inline section** in `contracts/pfos/_PFOS_BUILD_LOG.md`. **There is no `contracts/amendments/` directory** (design §A.4), and **no acceptance check covers that channel** (design §A.4.1, §J.3).
- **Every file added or changed under `src/` or `tests/` must declare its owning contract and phase within its first twenty lines**, so `AC10` keeps passing. _Requirements: 1.7_

---

## Tasks

## Phase 0 — Decision gate (no code)

These are the true blockers. Nothing in Phase 1 or Phase 2 can be written coherently until they are answered. **No task in this phase writes, modifies or tests code.**

- [ ] 1. Surface D-1 … D-12 for owner answer as decision briefs
  - **Owning contract / amendment:** none required — this is a spec-local planning artifact. It authors no code and amends no contract.
  - **Prerequisites:** none. This task is what unblocks the rest.
  - **Requirements covered:** Requirement 8 in full (8.1–8.15), Requirement 9 (9.1–9.4).
  - **Files:** one file per decision under `.kiro/specs/hermes-governed-workflows/decisions/` — `D-01.md` … `D-12.md`. One file per decision so the owner can answer them independently and so no two briefs contend for the same file.
  - **Rollback:** delete the brief. No code, no data, no contract state is touched.
  - **Approval boundary:** **Stage 1 only.** Authoring a decision brief is planning, not implementation. The *answers* are owner acts and are not solicited by any Stage-2 mechanism here.
  - **Hard rule for every sub-task below: never invent an owner choice.** A recommended default is recorded as a recommendation. `None offered` is recorded as `None offered` and left empty.

  - [ ] 1.1 Write the **D-8** brief — reachability approach
    - Present option (a) pre-tier governed admission (design §D.7.2) against option (b) classifier vocabulary change (design §D.7.3), with the full comparison table and the recommended default (a).
    - State plainly that the two options **produce different files**: (a) writes `src/server/process/turnAdmission.ts` + test; (b) edits `turnClassifier.ts`, `turnIntake.ts`, `TURN_INTENT_TRIGGER`, `INTENT_FAMILY`, `PROSE_INTENTS` and every exhaustive `Record<TurnIntent, …>` corpus in the tree.
    - Record that under (a) the model tier is reachable **only** from effect `read` — the journal-read variant of `yawmiyat`, plus `shura`, `naqd`, `qarar`, `thabat` — so **no finance wording of any kind reaches a model** (design §D.7.1.1, §E.5.1).
    - _Requirements: 8.2, 20.5_

  - [ ] 1.2 Write the **D-5** brief — Drive encryption scheme, candidate-egress fix, and the O1 §2.2 conflict
    - Present scheme (a) WebCrypto-based / (b) library-based; egress (c) single serialisation-time projection / (d) per-call-site exclusion; conflict (e) `drive-db.md` holds / (f) amend toward a readable mirror. Recommended default **(a) + (c) + (e)**.
    - State that a readable evidence mirror and application-level encryption are **two answers to one question** and cannot both be chosen, which is why they are one decision (design §B.5, §K.1).
    - Record the corollary: even if the owner later amends toward O1 §2.2, **I0 does not become unnecessary** — the retroactivity argument covers everything written before the amendment, and a readable mirror still needs the candidate egress fixed.
    - Record that O1 §2.2's `[AGREED]` marker is the proposal's own claim about a conversation and is **not** a policy amendment; steering outranks a proposal document.
    - _Requirements: 8.3, 9.3, 11.5_

  - [ ] 1.3 Write the **D-11** brief — duplicate outbound delivery
    - Present (a) accept at-least-once with plain disclosure / (b) a delivery-reconciliation record persisting `queuedRef → TelegramSendReceipt` before the settle / (c) require verified transport-level idempotency. Recommended default **(b), with (a)'s disclosure retained regardless**.
    - State that **(c) is not available**: `sendMessage` takes no idempotency key and `TelegramOutboundMessage` carries no correlation ref (design §L.12.1).
    - State that **(b) narrows the duplicate window and does not close it** — a crash between provider-accept and receipt-persist still duplicates — and must never be described as achieving exactly-once delivery.
    - _Requirements: 8.13, 8.15, 22.9, 22.13, 22.14_

  - [ ] 1.4 Write the **D-9** and **D-12** briefs — seam shape, and whether explanatory finance conversation should be reachable
    - **D-9:** (a) instantiate the existing generic as `Answer = Promise<string>` / (b) widen `executeDeterministically` to `=> Answer | Promise<Answer>` and await inside `dispatchTurn`. Recommended default (a), because it leaves `dispatchTurn` unedited so its own R16 sentence stays literally true.
    - **D-12:** (a) leave an explanatory finance conversation unreachable — the current behaviour and the strongest money guarantee / (b) add a `mal`-adjacent conversational route. Recommended default (a) for this slice. Record that (b) requires a new effect member or a new route, both of which touch the router this program otherwise consumes verbatim.
    - Record the capability gap honestly: the behaviour R-3 was originally written to exercise **does not exist**, and that is a gap, not a defect.
    - _Requirements: 8.10, 8.14, 20.5, 23.1_

  - [ ] 1.5 Write the **D-2** and **D-6** entries — both `None offered`
    - **D-2** (O6's three daily briefs + twice-daily Drive discovery): record **`None offered`**. It is a scope decision; recommending one would invent an owner choice. Record the three facts that make O6 §6 unbuildable by policy: no contract grants it, `two-agent-vps.md` §5 requires a contract before its area is built, and a third `SCHEDULER_TARGETS` member is a compile error. Record that D-2 blocks **O6 §6 only** and **does not block I2** or Requirement 24.
    - **D-6** (disposition of the 54 dirty working-tree entries): record **`None offered`**. Commit and push are owner-authorized actions. Record that D-6 blocks `AC14`, `AC15`, any commit and any push, permanently until answered — so **21/21 is unreachable and 19/21 is the correct baseline**.
    - Attach the `AC12` coverage note to D-6's neighbourhood: extending `AC12`, or adding an `AC22`, changes the declared check count that `all.mjs` asserts and is therefore a **harness change and an owner decision**. **Invent no new check here.**
    - _Requirements: 8.4, 8.5, 7.9, 24.10_

  - [ ] 1.6 Write the **D-1, D-3, D-4, D-7, D-10** briefs
    - **D-1** (registration of O1–O11; recommended default: an additive sub-registry keyed by parent `id: 10`, leaving `OBJECTIVE_REGISTRY` byte-identical). Record that D-1 does **not** block I0–I7.
    - **D-3** (systemd hardening; recommended default: harden the live unit — a Stage-2 host mutation). Record that until answered, **no claim may be made that the gateway runs hardened**.
    - **D-4** (ingress ownership; recommended default: a disambiguation observation before choosing). Record the standing rule: **never kill a candidate for appearing redundant** — an UNRESOLVED purpose is not a known-idle process. Record that until resolved there is no live turn, no real-host scheduled job and no real effective-surface observation.
    - **D-7** (nizamcore verified-state contradiction; recommended default: mark `ops/NIZAMCORE_VERIFIED_STATE.md` STALE now, re-observe when authorized). Record the mechanical consequence already designed in: a remote capture is `captured_unconfirmed` by default and the governed path may not say "Captured" on a remote call alone.
    - **D-10** (`singleWindowFlow.ts`; recommended default: keep as the offline reference, consume types only).
    - Record that **no edit to the `nizamcore` repository is proposed** — it is separate and owner-gated.
    - _Requirements: 8.6, 8.7, 8.8, 8.9, 8.11, 8.12_

- [ ] 2. Author the program amendment record and the honest-claims register
  - **Owning contract / amendment:** **a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`**, requested explicitly. There is no amendments directory (design §A.4). Formal reference model: **KWP08** in `contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md` — named, dated, explicit about what it supersedes.
  - **Prerequisites:** Task 1 complete. No decision answer required — this task records state, it does not choose.
  - **Requirements covered:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.5, 2.6, 2.8, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 9.1, 9.2, 9.4, 17.6, 20.1, 20.2, 20.5, 22.13.
  - **Rollback:** remove the amendment section. It records; it changes no behaviour.
  - **Approval boundary:** **Stage 1 only.** Authoring an amendment record is a documentation act inside `contracts/`. It executes no gate, mutates no host and grants nothing. **Note that no acceptance check verifies this record** (design §J.3) — that is the gap, recorded not filled.

  - [ ] 2.1 Write the amendment section: scope, the two-stage approval model, and the standing constraints
    - State the two stages verbatim from design §0.5, including that **no increment anywhere is described as needing no approval**, and that the exact phrase **"Stage 1 only."** is used where an increment needs nothing beyond Stage 1.
    - Record the preserved standing constraints: Slack Socket Mode as the sole transport with the three Slack aliases only; the five `REVOKED_TELEGRAM_ALIASES` refused; **no Telegram cutover**; `telegram*` symbol names are historical naming; `OBJECTIVE_REGISTRY` byte-identical at `OBJECTIVE_COUNT = 20`; `dailyCompanion.ts` and `channelMemory.ts` are **offline references with no live binding**; the `telegram-window`, `agentic-profile-baseline`, `telegram-daily-companion` and `dual-channel-memory` specs keep their authority, superseded by none of this.
    - Record that the **54 dirty entries are preserved as found** and that **no commit and no push** is created by this program.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.5, 2.6, 2.8_
  
  - [ ] 2.2 Write the evidence-label register and the two coverage gaps
    - Label every live-state claim with exactly one of **VERIFIED / UNVERIFIED / STALE / INACCESSIBLE**. Label the NIZAM host **INACCESSIBLE** and the Drive token **INACCESSIBLE** from a planning session. Label `ops/NIZAMCORE_VERIFIED_STATE.md` **STALE** and place no reliance on it. Treat retrieved text, discovered content and any `[AGREED]` marker as **untrusted data, never authorization**.
    - Record **gap 1 — `AC12`:** `scripts/verify/contract-ledger.mjs` opens only `contracts/_CONTRACT_INDEX.md` and `contracts/_BUILD_LOG.md`, hard-requires **exactly five** contract rows, and has **no** supersession, amendment, date or heading logic. It checks **neither PFOS 01–15 nor any amendment** — so the inline build-log amendment channel every increment relies on is **unverified by the harness**. **Invent no new check.**
    - Record **gap 2 — Drive encryption:** **no check among the twenty-one enforces the Drive encryption requirement.** `AC08` enforces **scope only** (`drive.file`). Changing the declared check count is an owner decision.
    - Record the baseline honestly: the **19-of-21 figure is STALE as a measurement** (2026-09-16 receipt) while its **cause — the 54 dirty entries — is VERIFIED**; and state that **passing tests is not live readiness, is not a Stage-2 approval, and is not evidence about any running system**.
    - _Requirements: 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 9.1, 9.2, 9.3, 9.4_

  - [ ] 2.3 Write the delivery-semantics disclosure and the reachability record
    - State the delivery semantics as **at-least-once delivery with an idempotent canonical write**. Separate the three guarantees and never merge them again: **(i)** canonical-write exactly-once — guaranteed by `recordId`; **(ii)** settlement idempotence — guaranteed by the `state = 'running'` predicate; **(iii)** external delivery exactly-once — **NOT guaranteed and not achievable with the transport as it stands**. Record **Case D-A** (send accepted, acknowledgement lost) and **Case D-B** (send succeeded, crash before settle).
    - State that **no artifact and no reply may claim exactly-once delivery**; exactly-once is claimed of the canonical journal write only. Record that **D-11(b) narrows the window and does not close it**.
    - Record the reachability consequence: the gate is **six** cases — R-1, R-2, **R-3 (re-specified: `mal`/`pfos_read` ⇒ `governed_deterministic` ⇒ no model)**, **R-3b (new: a `shura` phrase ⇒ `read` ⇒ `tier_path` ⇒ model permitted, reply digit-free)**, R-4, R-5 — and that **R-3 is no longer the tier-path guard**. Record that both ingress lexicons are quoted verbatim in design §D.7.1.1, so no reachability case rests on an unquoted lexicon.
    - Record that the slice is **not claimed successful** until all six cases pass, even if every other I1 criterion is green.
    - _Requirements: 8.15, 17.6, 20.1, 20.2, 20.4, 20.5, 22.9, 22.13_

- [ ] 3. Checkpoint — decision gate closed
  - Confirm each of D-1 … D-12 is either **answered by the owner** or **explicitly recorded as open with what it blocks**, and that **D-2 and D-6 still read `None offered`** with no invented default. Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 8.1, 8.4, 8.5_

---

## Phase 1 — I0 · Drive payload encryption and candidate egress

**Why this phase is first.** Its cost strictly increases with every day of real-data sync and **no later increment can undo it**: every snapshot is dated and retained, so plaintext written once is plaintext retained N times (design §F.2). **I0 precedes every real-data path**, including I1's live half, and I3, I6, I7 by definition.

**Recorded gap that bears directly on this phase: no check among the twenty-one enforces Drive encryption.** `AC08` enforces **scope only**. The encryption assertions below are therefore **tests**, not new harness checks (design §X.2 finding 4, §I.5).

- [ ] 4. I0 — application-level Drive payload envelope and candidate exclusion
  - **Owning contract / amendment:** `drive-db.md` (active steering, preserved) + **repository build Contract 2** (Drive data layer) + **PFOS 02** (data architecture & security). **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`** — requested explicitly, since there is no amendments directory.
  - **Prerequisites:** **D-5 must be answered first** — the scheme choice determines what `payloadEnvelope.ts` contains, so Stage-1 approval alone is necessary but not sufficient. Task 1.2 and Task 2 complete. `drive-db.md` holds unless the owner amends it; **do not design to O1 §2.2**, which is PROPOSED / CONFLICTED and not authority.
  - **Requirements covered:** 10.1–10.11, 11.1–11.5, 12.1, 12.2, 12.3, 2.7, 3.10, 1.7.
  - **Rollback:** restore the retained previous Drive file version (already retained by design) and revert the envelope module. **The rollback path must refuse rather than downgrade — no plaintext is re-written on rollback.** _Requirements: 10.9_
  - **Approval boundary:** **Stage 1, once D-5 is answered,** unblocks `payloadEnvelope.ts`, `candidateExclusion.ts`, the legacy-detection/migration path, the source-level assertions and every offline test below. **Stage 2 still required for:** enabling real-data Drive sync (owner), **G5** storage consent, **G8** backup keypair, and **all** key generation, custody and rotation — owner only. This program **generates no key, rotates no key, renews no consent and broadens no scope.** _Requirements: 12.4, 12.5_

  - [ ] 4.1 Create `payloadEnvelope.ts` with encrypt / decrypt / refuse / version — **AC-I0-3, AC-I0-4**
    - New file `src/lib/drive/payloadEnvelope.ts` exporting `encrypt`, `decrypt`, a named refusal set, and an envelope `version`. Header declares owning contract and phase.
    - Insert it between the database object and **every** `createTextFile` call in `src/lib/drive/driveDb.ts` — both the dated snapshot write (~L111) and the canonical write (~L76), and the whole-db serialisation at ~L108. Leave `src/lib/drive/driveClient.ts` `createTextFile` (~L150–183) unmodified; it receives ciphertext.
    - An unrecognised envelope version **refuses by name** and does not attempt a read. An undecryptable payload produces a **named refusal and never an empty database**. A key absent at read time refuses while the Dexie mirror stays readable.
    - Record in the module header that **HTTPS is transport security and is not the required at-rest encryption**.
    - Tests: focused encrypt→decrypt round trip; envelope-version refusal; negative — undecryptable payload yields a named refusal, never a silent empty db; restart — reopen with the key absent refuses and the local cache stays intact.
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6, 10.10, 1.7_

  - [ ]* 4.2 Write property tests for the envelope
    - **Property 37: Encrypt then decrypt is the identity** — **Validates: Requirements 10.11**
    - **Property 39: An unrecognised envelope version is refused by name** — **Validates: Requirements 10.4, 10.5**
    - **Property 40: An undecryptable payload never yields a database** — **Validates: Requirements 10.6**
    - **Property 41: A single mutated ciphertext byte is refused** (tamper) — **Validates: Requirements 10.7**
    - **Property 44: No key appears in a Drive-bound payload** — **Validates: Requirements 12.1**
    - Minimum 100 iterations each; tag `Feature: hermes-governed-workflows, Property {n}: {text}`.
    - _Requirements: 10.4, 10.5, 10.6, 10.7, 10.11, 12.1_

  - [ ] 4.3 Create `candidateExclusion.ts` as a single serialisation-time projection — **AC-I0-2**
    - New file `src/lib/drive/candidateExclusion.ts`. Applied at **the one place the payload is built** in `driveDb.ts` (~L108), **not** duplicated per call site.
    - Leave `src/lib/drive/sync.ts` (~L192–196) unmodified: its merge comment is accurate about merge; the defect is in persistence, and the fix belongs at serialisation.
    - Record that **encryption alone does not fix candidate egress** — an encrypted payload still contains the candidates, the owner's key decrypts them, and a future readable mirror would expose them.
    - Tests: focused — `transactionCandidates` is absent from both the snapshot payload and the canonical payload.
    - _Requirements: 11.1, 11.2, 11.5, 1.7_

  - [ ] 4.4 Add the candidate-egress property test and the re-introduction source assertion
    - **Property 43: No serialised payload contains a candidate field** — for any database shape, no `transactionCandidates` field at any depth. **Validates: Requirements 11.1, 11.3**
    - Add a **source-level assertion as a test** (not a new harness check) that detects a future re-introduction of a candidate field into a Drive-bound payload — a property test proves today's code excludes them; a source check catches tomorrow's regression.
    - _Requirements: 11.3, 11.4_

  - [ ] 4.5 Add the no-plaintext source assertion and explicit legacy-plaintext handling — **AC-I0-1**
    - Add a **source-level assertion in the spirit of `AC08`, implemented as a test**, that no Drive write path emits plaintext ledger JSON. **Add no check to `scripts/verify/all.mjs`** — the declared count of 21 is untouched.
    - Implement explicit legacy handling: a plaintext legacy Drive document is **detected and refused-or-migrated explicitly**, never silently re-read, and the path taken is recorded.
    - **Property 38: Every Drive-bound write receives ciphertext** — both the dated snapshot write and the canonical write receive an encrypted envelope, and the value passed to `createTextFile` is not parseable as ledger JSON. **Validates: Requirements 10.1, 10.2**
    - **Property 42: A legacy plaintext document is never silently re-read** — **Validates: Requirements 10.8**
    - _Requirements: 10.1, 10.8, 7.2, 7.9_

  - [ ]* 4.6 Write the migration money-invariance property test
    - **Property 14: A migration moves no money** — for any generated database shape, every monetary field is byte-identical before and after any migration introduced by this program. Guards `migrations.ts` (~L31–32, 60–62, 75–78) against coercion.
    - **Property 13: Money stays an integer everywhere it is typed** — a non-safe-integer is refused at the branded type, at `assertDeterministicFinancialResult` and at the zod schema boundary.
    - The Drive change is a **payload envelope version bump, not a SQLite migration**; browser `SCHEMA_VERSION` stays at 9.
    - _Requirements: 2.7, 3.10_

  - [ ] 4.7 Confirm the scope and secret guarantees still hold
    - Assert the Drive scope remains `https://www.googleapis.com/auth/drive.file` only so `AC08` keeps passing, and that no secret and no real ledger is tracked so `AC09` keeps passing.
    - **Property 45: No secret and no real ledger is tracked** — **Validates: Requirements 12.3**
    - Record that keys used by the envelope appear in **no** Drive-bound object — the failure mode `AC09` cannot see, because `AC09` scans the repository, not a runtime payload.
    - _Requirements: 12.1, 12.2, 12.3_

- [ ] 5. Checkpoint — I0 offline half complete
  - Run the focused tests, then `npm run typecheck`, `npm run lint`, `npm run build`, then `npm run verify:all -- --all`. **Expect 19 of 21 with only `AC14` and `AC15` failing** — that is the correct baseline, not a regression. Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

---

## Phase 2 — I1 · The governed vertical slice

**The slice:** authenticated intake → durable queue → governed Hermes turn → **deterministic PFOS read OR authorized native capture** → verified result → honest reply.

**Two structural rules that hold across every task in this phase.**

1. **The deterministic leg is a worker branch, not a tool.** `runtimeAdapter.AUTHORITY_KEY` matches `amount`, `currency`, `milliunit` and `financial` on grant-scope, payload **and** result keys, so a `DeterministicFinancialFact` is **unrepresentable** across the Hermes tool boundary — and all three tools that would carry one are in `DENIED_AUTHORITY_TOOLS`. **I1 adds zero tools. `HERMES_TOOL_NAMES` stays at 10.** The guard is preserved: no denylist entry removed, no regex relaxed, no exception carved.
2. **The diff surface is closed.** **Six** new files — `governedTurnPath.ts` + test (Task 7), `turnAdmission.ts` + test (Task 6), `effectiveToolSurface.ts` + test (Task 10) — plus roughly thirty changed lines across `turnWorker.ts` and `main.ts`. **Unmodified:** `turnDispatch.ts`, `turnClassifier.ts`, every module under `src/server/hermes/`, `operatorMessagePort.ts`, `scheduler.ts`, `singleWindowFlow.ts`. **No new schema, no new clock, no new port binding, no new transport.** _Requirements: 13.9, 13.10, 14.7_

- [ ] 6. I1a — pre-tier governed admission (`turnAdmission.ts`)
  - **Owning contract / amendment:** PFOS **Contract 14** (single-window composition) + **Contract 12** (worker/queue). The ingress-router policy is **consumed verbatim, never re-implemented**. Recorded in the I1 amendment section authored in Task 12.
  - **Prerequisites:** **D-8 answered** — under option (b) this task is replaced by classifier-vocabulary work and Tasks 8–9 still apply unchanged. Task 3 complete.
  - **Requirements covered:** 14.1–14.7.
  - **Rollback:** remove the admission branch from `turnWorker.ts`; every turn returns to `classifyTurn` → `dispatchTurn`. The module becomes dead but harmless. **Note what the rollback restores: the reachability defect.** It is a safe revert, not a neutral one.
  - **Approval boundary:** **Stage 1 only.**

  - [ ] 6.1 Create `turnAdmission.ts`
    - New file `src/server/process/turnAdmission.ts` exporting `admitTurn`, `ADMISSION_BRANCHES = ['governed_deterministic','tier_path'] as const`, and `TurnAdmission { branch, route }`.
    - `admitTurn` calls `routeIngressText` and returns the router's verdict **unmodified** alongside a branch: effect `local_write`, `pfos_read` or `none` ⇒ `governed_deterministic`; effect `read` or any other value ⇒ `tier_path`.
    - Re-implement **no** routing policy. Modify **none** of `TURN_INTENT_TRIGGER`, `INTENT_FAMILY`, `PROSE_INTENTS`, `DEFAULT_PROSE_INTENT`.
    - Tests: focused — one case per effect value; the returned `route` deep-equals the router's own verdict.
    - _Requirements: 14.1, 14.2, 14.3, 14.6, 14.7, 1.7_

  - [ ]* 6.2 Write property tests for admission
    - **Property 2: Admission partitions the four effects exactly** — **Validates: Requirements 14.2, 14.3**
    - **Property 3: Admission reproduces the router's verdict without modification** — **Validates: Requirements 14.1, 14.6**
    - _Requirements: 14.1, 14.2, 14.3, 14.6_

- [ ] 7. I1b — the governed deterministic path (`governedTurnPath.ts`)
  - **Owning contract / amendment:** PFOS **Contract 14** + **Contract 12** + **Contract 06** (store isolation); `money-rules.md`. Recorded in the I1 amendment section (Task 12).
  - **Prerequisites:** **D-8 answered** (branch shape), **D-7 open is acceptable** — its consequence is designed in as `captured_unconfirmed` by default. Task 6 complete. For any **real** `finance.db` read or **real** native capture, Phase 1 must have landed and Stage-2 approvals apply.
  - **Requirements covered:** 3.1–3.10, 5.1–5.6, 6.12, 13.1–13.10, 21.1–21.8, 22.3, 22.4, 22.6, 22.7.
  - **Rollback:** remove the `executeTurnDeterministically` line from `main.ts`; the deterministic path reverts to `answerDeterministically` exactly as today. **No data change, no migration.** The new files become dead but harmless.
  - **Approval boundary:** **Stage 1 only** for the offline half — the module, its tests, and injected fake ports. **Stage 2 still required for:** a real `finance.db` read on a confirmed host (**A14 INACCESSIBLE**), a real native capture (**D-7**), a bound transport, and **D-4** resolution before any live run.

  - [ ] 7.1 Create the module surface: outcomes, replies, observation, dependencies
    - New file `src/server/process/governedTurnPath.ts` exporting `GovernedPfosPort` (`readFinancialSnapshot`, `runDeterministicAnalysis`, both `Promise<FinancialAnalysisResult>`), `GovernedJournalPort` (`appendRecord` only), `GOVERNED_DETERMINISTIC_OUTCOMES`, `GovernedDeterministicObservation`, `GovernedDeterministicDependencies`, `createGovernedDeterministicExecutor`.
    - Own **no** store, socket or clock: PFOS port, journal port and clock are injected. Import **no** module from `src/lib/money` — nothing here computes.
    - Call `appendRecord` **only**; never the legacy `appendWithReceipt`, which derives `recordId` from the payload and is the duplicate-entry hazard.
    - `readTurnText` returns `null` on an unreadable body and the path proceeds **without throwing**. Introduce **no** schema migration.
    - Observation carries only `{turnRef, code, module, effect, outcome}`.
    - Tests: focused — one test per effect branch (`none`, `local_write`, `pfos_read`, fallback) and one per `IngressCode`; hostile-body cases (unparseable body, non-envelope, absent message, non-string text) each return without throwing.
    - _Requirements: 13.1, 13.6, 13.7, 13.8, 13.9, 13.10, 3.9, 5.1, 6.12, 1.7_

  - [ ] 7.2 Implement `renderVerifiedFinance` with the assertion ordering
    - Run `assertRoutedFinancialResult` **before** `assertDeterministicFinancialResult`, and run **both before composing any character** of the reply — so a rejected result produces no text at all.
    - Copy each `fact.amountMilliunits` **verbatim**: no arithmetic, no formatting, no rounding, no currency conversion. Include the deterministic `resultRef`.
    - A governance rejection reports `pfos_refused`, not a money failure.
    - Tests: focused — a `mal` result on a non-`mal` route yields the **governance** rejection, not the money one; a fact with a non-safe-integer amount yields `PFOS_FACT_MILLIUNITS_INVALID` ⇒ `pfos_refused`.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.3_

  - [ ] 7.3 Implement the honest non-answers — digit-free, no substitute figure
    - Export `PFOS_UNAVAILABLE_REPLY`, `PFOS_REFUSED_REPLY`, `CAPTURE_REFUSED_REPLY`, `CAPTURE_UNCONFIRMED_REPLY`. A PFOS throw ⇒ outcome `pfos_unavailable`; a `renderVerifiedFinance` throw ⇒ outcome `pfos_refused`. Both replies **digit-free**, neither offering a substitute figure.
    - Tests: negative — assert each reply against `NO_FIGURE_PATTERN`.
    - _Requirements: 3.6, 3.7, 13.4, 13.5_

  - [ ] 7.4 Implement the capture leg: `captureRecordId` and the receipt-honesty mapping — **AC-I1-4, AC-I1-16**
    - `captureRecordId(queuedRef)` is a **pure function of the queue ref**, byte-identical across replays, and **not** derived from the payload.
    - Exhaustive reply mapping from the observed `JournalPersistenceReceipt`: `readBackConfirmed && hashMatch` ⇒ outcome `captured`, reply carries the word **"Captured"**, the **writer's own** `entryRef`, and a read-back-confirmed statement. `LOCAL_WRITTEN` without both confirmations ⇒ `captured_unconfirmed`. `STAGED_RETRY` ⇒ `captured_unconfirmed` with the same weaker wording. `FAILED`, `record === null`, or a thrown call ⇒ `capture_refused`, **never** the word "Captured".
    - `LOCAL_WRITTEN` alone never earns "Captured": branch on `readBackConfirmed && hashMatch`, **not** on the state name. A returned `entryRef` alone never satisfies the condition. Never invent an `entryRef` locally.
    - Route any `recoveryAction` string to the **redacted observation** and never into the owner's reply.
    - Keep `updatePolicy` at its default `REFUSE`: a replay carrying different text under the same `recordId` ⇒ `JOURNAL_UPDATE_NOT_PERMITTED` ⇒ `capture_refused`, never a silent revision.
    - Treat a **remote** capture as `captured_unconfirmed` by default while **D-7** is unresolved and the native writer is not established to satisfy the receipt shape with independent read-back.
    - Tests: focused — one case per receipt row of the mapping. Negative — a read-back disagreeing with the expected payload hash yields state `FAILED` ⇒ `capture_refused`. Tamper — a replay with different text under the same `recordId` refuses.
    - _Requirements: 13.2, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8, 22.3, 22.6, 22.7_

  - [ ] 7.5 Add the capture idempotence and receipt property tests — **AC-I1-16, AC-I1-17**
    - **Property 19: The reply is a total function of the observed receipt, and "Captured" requires both confirmations** — **Validates: Requirements 21.1, 21.2, 21.3, 21.4, 21.5, 21.7, 21.8, 13.2**
    - **Property 20: Capture identity depends on the queue ref alone** — **Validates: Requirements 22.3, 22.6**
    - **Property 21: A replayed capture writes once and returns the same reference** — replay under the same `recordId` returns mode `IDEMPOTENT_REPLAY` with the same `entryRef`, and the fake writer records **exactly one** canonical write. **Validates: Requirements 22.4**
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.7, 21.8, 22.3, 22.4, 22.6_

  - [ ]* 7.6 Write the money-provenance and digit-free property tests
    - **Property 9: Every digit an owner reads traces to a deterministic fact or a reference** — **Validates: Requirements 3.1, 3.2, 3.3, 16.4**
    - **Property 10: A non-answer is digit-free and offers no substitute** — **Validates: Requirements 3.6, 3.7, 13.4, 13.5**
    - **Property 12: The deterministic answer table is digit-free for every intent** — **Validates: Requirements 13.6**
    - _Requirements: 3.1, 3.2, 3.3, 3.6, 3.7, 13.4, 13.5, 13.6_

  - [ ]* 7.7 Write the privacy property tests
    - **Property 15: An observation carries only a reference and four enums** — exact key set `{turnRef, code, module, effect, outcome}`. **Validates: Requirements 5.1, 5.3**
    - **Property 16: No turn content reaches an observation, a log line or a thrown detail** — a unique marker in the turn text appears nowhere; a receipt `recoveryAction` appears in the observation and **not** in the reply. **Validates: Requirements 5.2, 5.5**
    - **Property 17: No artifact records a deployment particular** — no host, bot, sender, chat, token, endpoint or monetary figure under `ops/` or in any fixture, so `AC18` keeps passing. **Validates: Requirements 5.4**
    - **Property 8: A refusal reply is exactly the router's public reason** — **Validates: Requirements 5.6**
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 8. I1c — worker seam widening, composition, and the send/settle leg
  - **Owning contract / amendment:** PFOS **Contract 12** (worker/queue/transport) + **Contract 14**. Recorded in the I1 amendment section (Task 12).
  - **Prerequisites:** **D-9 answered** (seam shape — until then the two changed lines of `turnWorker.ts` are unfixed in shape) and **D-11 answered** (the send/settle leg's shape — option (b) adds a persisted reconciliation record and a pre-send consult that option (a) does not). Tasks 6 and 7 complete.
  - **Requirements covered:** 6.1–6.6, 6.9, 6.10, 6.11, 22.1, 22.2, 22.5, 22.8–22.14, 23.1–23.9.
  - **Rollback:** two subtractive edits — remove the `executeTurnDeterministically` line from `main.ts`, and remove the admission branch from `turnWorker.ts`. The widened `renderAnswer` return type is backward compatible (`string` is assignable to `string | Promise<string>`) and may be left in place. **No data change and no migration.** The rollback restores the reachability defect. _Requirements: 23.8, 23.9_
  - **Approval boundary:** **Stage 1 only** for the signature widening, the composition lines and every offline test. **Stage 2 still required for:** a bound Slack transport (live operation), any paid model turn on the conversational branch (provider spend), and **D-4** resolution before a live run. **Commit and push are separately authorized and are not granted here** (the tree is dirty — **D-6**).

  - [ ] 8.1 Widen the `turnWorker.ts` seam without editing `turnDispatch.ts`
    - Instantiate the dispatch generic as `Answer = Promise<string>`; `renderAnswer` stays the identity function and its declared return type widens to `string | Promise<string>`; the worker `await`s its result on the `code_only` route.
    - **`src/server/routing/turnDispatch.ts` receives no edit**, so its deterministic branch still returns before any `await` and its R16 sentence stays literally true.
    - Add the optional `executeTurnDeterministically?: (item) => TurnDispatchDependencies<Answer>['executeDeterministically']` dependency, overriding `dispatch.executeDeterministically` **for one item only**; absent, the supplied dependencies are used unchanged. Extend the existing one-line dispatch composition with one spread.
    - The override holds **no** `ModelInvocationGrant` and cannot reach `channel.invoke`.
    - Tests: focused — `turnWorker.test.ts` extended for the `Promise<string>` wiring; an unbound sender still throws `TELEGRAM_SEND_REFUSED`; `target === null` still settles `abandoned` with that code.
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.9, 6.6, 1.7_

  - [ ] 8.2 Add the admission branch to the worker
    - Call `admitTurn(readTurnText(item.rawBody))`. On branch `governed_deterministic`, call **neither** `classifyTurn` **nor** `dispatchTurn`, so **no `ModelInvocationGrant` can exist** for that turn. On branch `tier_path`, follow the existing `classifyTurn` → `dispatchTurn` path unchanged.
    - Preserve `settle done` **only after** the Reply_Sender reports a delivered send.
    - Tests: focused — spies assert zero `classifyTurn` and zero `dispatchTurn` calls on the governed branch, and exactly one `classifyTurn` call on the tier path.
    - _Requirements: 14.4, 14.5, 6.5_

  - [ ] 8.3 Wire the composition in `main.ts`
    - Build `createGovernedDeterministicExecutor` **once** (it holds ports, not per-turn state) and take the per-item closure **per turn**. Add one generic argument, one factory call, one dependency line.
    - **Retain `answerDeterministically`** as the fallback deterministic executor on the dispatch path.
    - Bind the Reply_Sender once, as today; preserve every single-writer authority: `operatorMessagePort` for admission, `workQueueRepo` for durable queue state, `classifyTurn` for grants, `scheduler.ts` for the clock, the nizamcore native writer for journal content, `createBindableReplySender` for outbound sends, `createModelChannel` for provider reach.
    - Route `onOutcome` to the redacted logger only.
    - Tests: focused — composition-shape test asserting the executor is constructed once and the closure per item.
    - _Requirements: 23.6, 23.7, 6.11, 13.8, 1.7_

  - [ ] 8.4 Implement the send/settle leg under the answered D-11 — **AC-I1-9, AC-I1-18, AC-I1-19**
    - Perform, in this order: **(1)** the canonical write, **(2)** the verified read-back, **(3)** the reply composition from observed receipt fields, **(4)** the send, **(5)** the settle as `done`. Five steps — the compose step sits **between** read-back and send.
    - A crash or send failure between (1) and (5) **re-delivers** and must **not** re-write the canonical entry. An item left unsettled beyond its lease is returned to `queued` by `reclaimExpired` → `workQueueRepo.reclaimStalledWork` and re-processed as a later attempt.
    - **Delivery semantics are at-least-once.** Do **not** represent them as exactly-once anywhere — in code, in a comment, in an observation or in a reply. Exactly-once is claimed of the **canonical journal write** only.
    - A duplicate reply is **reported in the redacted observation, never silently swallowed**.
    - Under **D-11(b)**: persist `queuedRef → TelegramSendReceipt` **before** the settle and consult it on re-claim before re-sending. Record in the module header that this **narrows the window and does not close it** — a crash between provider-accept and receipt-persist still duplicates. Under **D-11(a)**: the second send occurs and is reported.
    - **Implement no duplicate-suppression workaround and weaken no acceptance check to accommodate a duplicate.**
    - Tests: focused — the five-step ordering; `settleWork` called more than once for one `queuedRef` with outcome `done` reports `settled: false` and writes nothing.
    - _Requirements: 22.1, 22.2, 22.5, 22.8, 22.9, 22.10, 22.11, 22.12, 22.14_

  - [ ] 8.5 Write the failure-injection suite FI-1 … FI-5
    - Offline only: synthetic fixtures, injected ports, a **fake transport**, injected crash points. No host, no credential, no provider spend. **Not optional — this suite is the honest-delivery gate (AC-I1-18).**
    - **FI-1** — the send resolves, then the process is killed **before** `settle`: assert exactly one canonical entry, that the reply **is** re-sent on the re-claim (asserted as a fact, not as a defect), and that the row settles `done` exactly once.
    - **FI-2** — the send rejects with a `TelegramRateLimitRefusal` carrying `retryAfterSeconds` **after** the provider actually accepted: assert the duplicate delivery is **observable and reported**, never silently swallowed.
    - **FI-3** — `reclaimStalledWork` returns a `running` row whose send already succeeded: assert `recordId` suppresses the second **canonical write**; under **D-11(b)** assert the reconciliation record suppresses the second **send** and that the assertion is a **narrowing, not a closure**; under **D-11(a)** assert the second send occurs and is reported.
    - **FI-4** — `settleWork(done)` called repeatedly on the same `queuedRef`: assert `settled: false` and nothing written from the second call on.
    - **FI-5** — a crash between the canonical write and the read-back: assert the reply is `captured_unconfirmed` and **never** "Captured".
    - **No test may be written whose passing would imply exactly-once delivery.**
    - _Requirements: 21.3, 22.2, 22.5, 22.9, 22.10, 22.11, 22.12, 22.14_

  - [ ]* 8.6 Write the seam, queue and grant property tests
    - **Property 35: The renderer treats a string and a promised string identically** — **Validates: Requirements 23.2, 23.9**
    - **Property 36: A per-item override cannot reach the model channel** — **Validates: Requirements 23.5**
    - **Property 22: Exactly one canonical entry survives any interruption before settle — delivery is at-least-once** — asserts a lower bound of one delivered reply and **does not** assert an upper bound of one. **Validates: Requirements 22.1, 22.2, 22.5, 22.8, 22.9, 22.10, 22.12**
    - **Property 22a: Settlement is idempotent** — **Validates: Requirements 22.11**
    - **Property 23: A settle as done implies a delivered send** — **Validates: Requirements 6.5**
    - **Property 24: A foreign namespace consumes no dedup slot** — **Validates: Requirements 6.3**
    - **Property 25: A rejection is always the one opaque code** — `OPERATOR_DELIVERY_REFUSED`; a `duplicate` decision carries no code. **Validates: Requirements 6.4**
    - **Property 26: A forged grant is refused at all three checkpoints** — planner, channel, router. **Validates: Requirements 6.10**
    - Also assert as one-shot tests: `accept` performs dedup claim and enqueue in **one transaction** and returning **is** the acknowledgement, with **no separate acknowledgement step introduced**; and `classifyTurn` remains the **sole** mint of a grant with `isMintedGrant` re-checked independently at planner, channel and router.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.9, 6.10, 22.1, 22.11, 23.2, 23.5, 23.9_

- [ ] 9. I1d — the reachability suite: six cases, and the gate on the slice
  - **Owning contract / amendment:** PFOS **Contract 14**; recorded in the I1 amendment section (Task 12). The suite lives in `src/server/process/turnAdmission.test.ts`.
  - **Prerequisites:** **D-8 answered**; Tasks 6, 7, 8 complete. Uses a **fake** model channel throughout — **no real provider invocation and no provider spend.**
  - **Requirements covered:** 15.1–15.4, 16.1–16.5, 17.1–17.3, 17.3a–17.3d, 17.4, 17.5, 17.6, 18.1–18.4, 19.1–19.4, 20.1–20.5, 3.8.
  - **Rollback:** the suite is additive test code; deleting it removes the gate and is therefore **not** a neutral rollback — it removes the only thing that makes the reachability defect impossible to ship silently.
  - **Approval boundary:** **Stage 1 only.** Every case is offline with injected ports and a stub channel.
  - **The gate, stated as a rule for this task: the vertical slice is NOT claimed successful until all six cases pass.** `AC-I1-1 … AC-I1-10` can all be green while journal capture is dead code. These six make that impossible. A failing case must **fail loudly with the failing case identified** and must **never degrade to a passing weaker assertion.** _Requirements: 20.1, 20.3_

  - [ ] 9.1 **R-1** — journal capture reaches the capture leg (**AC-I1-11**)
    - Representative text `write this down: the fridge broke` ⇒ code `ROUTED`, module `yawmiyat`, effect `local_write`, branch `governed_deterministic`.
    - Assert via spies that `classifyTurn` was **never called** and **no** model channel was invoked. Assert the reply is a **writer-receipt** reply derived from observed `JournalPersistenceReceipt` fields, not a model-composed sentence.
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [ ] 9.2 **R-2** — balance reaches the PFOS leg (**AC-I1-12**)
    - Representative text `what is my balance` ⇒ `ROUTED`, module `mal`, effect `pfos_read`, branch `governed_deterministic`.
    - Assert `classifyTurn` never called and no channel invoked. Assert the reply contains the deterministic `resultRef` and digits **byte-identical** to each `fact.amountMilliunits`, stated as integer milliunits. Assert both financial assertions ran in the Requirement 3.4 order before the reply was composed.
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 9.3 **R-3 (re-specified)** — explanatory finance wording is deterministic (**AC-I1-13**)
    - Representative text `how much is safe to spend` ⇒ `ROUTED`, module `mal`, effect `pfos_read`, branch `governed_deterministic`, **because `FINANCE` explicitly contains `\bsafe to spend\b`** (design §D.7.1.1, quoted verbatim).
    - Assert `classifyTurn` never called, **no `ModelInvocationGrant` exists** for the turn, and no model channel invoked. Assert the reply is either the verified-deterministic reply of R-2 or a **digit-free** unavailable/refused reply — **never** a model-composed sentence.
    - **Do not change this fixture** to restore the superseded expectation, and **do not edit the `FINANCE` lexicon.**
    - _Requirements: 17.1, 17.2, 17.3_

  - [ ] 9.4 **R-3b (new)** — the tier-path regression guard (**AC-I1-13b**)
    - A representative `SHURA` text carrying **no `FINANCE` token** — for example `plan with me the week ahead` ⇒ `ROUTED`, module `shura`, effect `read`, branch `tier_path`.
    - Assert `classifyTurn` **is** called, a `ModelInvocationGrant` **is** minted, and a **fake** model channel records that the minted grant reached it. Assert the reply is **digit-free** and that the model tier sources no figure.
    - Assert the negative guard: **while any representative text for R-3b contains a `FINANCE` token, the suite fails**, because such a text routes `pfos_read` and cannot exercise the tier path.
    - _Requirements: 17.3a, 17.3b, 17.3c, 17.3d, 17.4, 3.8_

  - [ ] 9.5 **R-4** and **R-5** — the cost-and-honesty guards (**AC-I1-14**, **AC-I1-15**)
    - **R-4:** secret-seeking text ⇒ `REFUSED_SECRET`, module `refuse`, effect `none`, branch `governed_deterministic`, settled from `route.publicReason`. Assert **zero effect** — no port touched, no store read, no store write, no tool call — and that the fake channel records **no** invocation. Assert the reply **leaks no reason** for the refusal.
    - **R-5:** text matching nothing ⇒ `CLARIFY`, module `clarify`, effect `none`, branch `governed_deterministic`, zero effect. Assert the reply asks the owner to clarify and that the turn **does not** become a paid conversational turn by way of `DEFAULT_PROSE_INTENT`, with the fake channel recording no invocation.
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 19.1, 19.2, 19.3, 19.4_

  - [ ] 9.6 Add the lexicon-conflict guard and the six-case gate assertion
    - If the Ingress_Router's lexicon and a case's expected route disagree, the suite **fails and reports a lexicon conflict naming both cases**. It must **not** reclassify a case or edit a fixture to make itself pass.
    - Carry **R-3 and R-3b as two distinct cases**; the suite must not treat R-3 as the tier-path guard.
    - Assert the case count is **six** and that the suite fails loudly with the failing case identified.
    - _Requirements: 17.5, 20.3, 20.4_

  - [ ]* 9.7 Write the reachability property tests
    - **Property 1: Journal-shaped text always routes to local capture** — **Validates: Requirements 15.1**
    - **Property 2a: Finance-shaped text never reaches the model tier** — for any text containing a `FINANCE` token, module `mal` + effect `pfos_read`, branch `governed_deterministic`, and zero calls on `classifyTurn`, `dispatchTurn` and the channel. **Validates: Requirements 3.8, 16.1, 17.1, 17.2, 17.3**
    - **Property 4: The governed branch never reaches the classifier, the dispatcher or a channel** — **Validates: Requirements 4.5, 14.4, 15.3, 16.3, 18.3, 19.4**
    - **Property 5: The tier path is unchanged for conversational turns** — **Validates: Requirements 14.5, 23.4**
    - **Property 6: A hostile raw body never throws** — **Validates: Requirements 13.7**
    - **Property 7: Zero-effect verdicts touch nothing** — **Validates: Requirements 13.1, 18.1, 18.3, 19.1, 19.2**
    - **Property 11: Model-tier replies are digit-free** — **Validates: Requirements 3.8, 17.3**
    - _Requirements: 3.8, 4.5, 13.1, 13.7, 14.4, 14.5, 15.1, 15.3, 16.1, 16.3, 17.1, 17.2, 17.3, 18.1, 18.3, 19.1, 19.2, 19.4, 23.4_

- [ ] 10. I1e — the effective tool surface assessor
  - **Owning contract / amendment:** PFOS **Contract 05** §8.1 (tool set) + **Contract 12** (operations) + **Contract 13**. Recorded in the I1 amendment section (Task 12).
  - **Prerequisites:** Task 6 complete. **While D-4 is unresolved, exercise the assessor against synthetic observations only** — a surface report about the wrong process is worse than none.
  - **Requirements covered:** 4.6, 4.7, 4.8.
  - **Rollback:** delete the module and its test. It is an assertion over an observation and nothing depends on it.
  - **Approval boundary:** **Stage 1 only** for the module and synthetic-observation tests. **Stage 2 still required for:** producing any **real** observation, which needs **D-4** resolved and a reachable host (**A14 INACCESSIBLE**). The assessor performs no host mutation, starts no gateway, kills nothing and edits no configuration.

  - [ ] 10.1 Create `effectiveToolSurface.ts`
    - New file exporting `EFFECTIVE_SURFACE_VERDICTS`, `ObservedToolSurface`, `EffectiveSurfaceReport`, `assessEffectiveToolSurface`.
    - `method === null` ⇒ verdict `unobserved`, **never** `ok`. Report `unexpected` (observed ∖ declared — a containment finding) and `missing` (declared ∖ observed — a capability finding) as **two separate collections**. Compute `authorityBearing` with the **existing** `denyAuthorityTool` predicate, not a re-implementation. Carry `authorizesExecution` as the **literal `false`** so no caller can read the report as permission.
    - Tests: focused — synthetic observations including `method: null`.
    - _Requirements: 4.6, 4.7, 4.8, 1.7_

  - [ ]* 10.2 Write the effective-surface property test
    - **Property 33: An unobserved surface is never reported as healthy, and the two differences are set differences** — **Validates: Requirements 4.6, 4.7**
    - _Requirements: 4.6, 4.7_

- [ ] 11. I1f — the invariant regression net
  - **Owning contract / amendment:** PFOS **Contract 05** (tool set) + **Contract 06** (store isolation) + **Contract 12**; `money-rules.md`. Recorded in the I1 amendment section (Task 12).
  - **Prerequisites:** Tasks 6–10 complete.
  - **Requirements covered:** 2.1, 2.2, 2.3, 2.4, 2.7, 4.1, 4.2, 4.3, 4.4, 4.5, 1.7, 23.8.
  - **Rollback:** these are assertions; removing one removes a guard rather than a behaviour. Do not remove any.
  - **Approval boundary:** **Stage 1 only.**

  - [ ] 11.1 Assert the tool boundary and the transport policy did not move
    - `expect(HERMES_TOOL_NAMES).toHaveLength(10)` after I1; I1 adds **zero** tools and so do I0–I7. `denyAuthorityTool` still refuses all three of `nizamcore.request_pfos_analysis`, `pfos.read_financial_snapshot`, `pfos.run_deterministic_analysis`. **No entry removed from `DENIED_AUTHORITY_TOOLS`, no part of `AUTHORITY_KEY` relaxed, no exception carved.**
    - The deterministic financial leg presents **no tool name** to `runtimeAdapter`.
    - Slack Socket Mode remains the sole transport, using only `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_ALLOWED_USERS`. `assertRevokedTelegramAliasesNotPresent` still refuses any process presenting any of the five `REVOKED_TELEGRAM_ALIASES`. **No Telegram cutover is introduced**; a `telegram*` symbol name is historical naming, not a live binding.
    - **Property 32: The authority-tool predicate refuses the whole family** — **Validates: Requirements 4.3**
    - **Property 34: A revoked transport alias is always refused** — **Validates: Requirements 2.2**
    - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 11.2 Assert the objective registry and the header discipline
    - `OBJECTIVE_REGISTRY` in `src/server/objectives/objectiveRegistry.ts` remains **byte-identical**, with `OBJECTIVE_COUNT === 20`. **Do not touch the UPOI 20-entry registry.**
    - **Property 18: Every source file declares its owning contract and phase** — for all files under `src/` and `tests/`, the first twenty lines declare an owning contract and a phase, so `AC10` keeps passing. **Validates: Requirements 1.7**
    - **Property 13: Money stays an integer everywhere it is typed** — re-asserted at the I1 boundary; no floating-point money at any tier. **Validates: Requirements 2.7**
    - _Requirements: 1.7, 2.4, 2.7_

  - [ ] 11.3 Rehearse the I1 rollback
    - Verify that removing the `executeTurnDeterministically` line from `main.ts` and the admission branch from `turnWorker.ts` reverts the system to current behaviour, requires **no data change and no migration**, and leaves the widened `renderAnswer` return type in place safely.
    - Record in the test's own comment that **the rollback restores the reachability defect** — a safe revert, not a neutral one.
    - _Requirements: 23.8, 23.9_

- [ ] 12. Checkpoint — I1 complete, and author the I1 amendment record
  - Run the focused tests, then `npm run typecheck`, `npm run lint`, `npm run build`, then `npm run verify:all -- --all`. **Expect 19 of 21 with only `AC14` and `AC15` failing.**
  - Author a dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md` recording the I1 composition, the six reachability cases and their result, the capture-receipt discipline, the at-least-once delivery semantics, and the two coverage gaps. **Record that this amendment channel is itself unverified by the harness.**
  - Do **not** claim the slice successful unless all six reachability cases passed. Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.8, 20.1, 20.2_

---

## Phase 3 — I2 · Scheduled jobs as a consumer

**The rule, stated as a constraint and not as advice: add a consumer behind the existing `finance` internal endpoint. Add no `SCHEDULER_TARGETS` member, no timer, no cron, no `listeningPorts` writer, and no second clock.** `scheduler.ts` already owns cadence, retry, staleness, halt and liveness, and `SCHEDULER_TARGETS` is a `const` tuple so a third target is a **compile error**.

- [ ] 13. I2 — scheduled jobs registry behind the existing finance tick
  - **Owning contract / amendment:** PFOS **Contract 12** §"scheduler". **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`.** It **does not** carry O6's cadence — that is **D-2**.
  - **Prerequisites:** I1 (Tasks 6–12) complete. **D-2 is `None offered` and must not be answered on the owner's behalf**; I2 is deliberately scoped so D-2 does not block it.
  - **Requirements covered:** 6.7, 6.8, 24.1–24.10.
  - **Rollback:** unregister the job. The tick continues delivering to an endpoint that does nothing extra.
  - **Approval boundary:** **Stage 1 only** for `scheduledJobs.ts`, the finance internal-endpoint handler change, the `kv` usage and their offline tests. **Stage 2 still required for:** running any job against a real host (**A14 INACCESSIBLE**, and **D-4** unresolved) and any live delivery arising from a tick. **O6's cadence is unblocked by neither stage** — it needs **D-2** and a contract amendment.

  - [ ] 13.1 Create `scheduledJobs.ts` as a registry of pure planners plus injected effects — **AC-I2-3**
    - New file `src/server/process/scheduledJobs.ts`. Each job is a **pure, deterministic planner** with its effect **injected**. Attach behind the finance agent's existing internal endpoint handler; **`src/server/process/scheduler.ts` is not modified**.
    - Use the **existing `kv` table** for any `lastRunAt`, rather than a new table, matching the precedent set when obligations reused `kv`.
    - Guard a job that could overlap the next tick with a **claim-style lease reusing the queue's mechanism**, not a new one.
    - A throwing job must not throw the tick: `tickOnce` already never throws and the handler must preserve that, with `isTicking()` remaining true.
    - Tests: focused — each planner is pure and deterministic. Negative — a throwing job does not fail the tick. Restart — `lastRunAt` survives and no job runs twice for one due period.
    - _Requirements: 24.3, 24.5, 24.6, 24.7, 24.8, 1.7_

  - [ ] 13.2 Assert the clock invariants and the endpoint refusals — **AC-I2-1, AC-I2-2, AC-I2-4**
    - Assert `SCHEDULER_TARGETS` remains `['life','finance']` and `listeningPorts` remains an empty constant **with no writer**.
    - Add a **source-level assertion** that the tree contains **no second timing source** — no timing primitive constructed outside `scheduler.ts`.
    - Assert an endpoint outside the internal range is rejected by the **existing** internal-endpoint refusals; add no new refusal shape.
    - Record that I2 implements **no part of O6's cadence**.
    - _Requirements: 6.7, 6.8, 24.1, 24.2, 24.4, 24.9, 24.10_

  - [ ]* 13.3 Write the scheduler-consumer property tests
    - **Property 27: The tree contains exactly one timing source** — **Validates: Requirements 6.8, 24.4**
    - **Property 28: A throwing job never breaks the tick** — **Validates: Requirements 24.3**
    - **Property 29: Job planners are pure** — **Validates: Requirements 24.6**
    - **Property 30: A job runs at most once per due period across a restart** — **Validates: Requirements 24.8**
    - **Property 31: An out-of-range endpoint is refused** — **Validates: Requirements 24.9**
    - _Requirements: 6.8, 24.3, 24.4, 24.6, 24.8, 24.9_

---

## Phase 4 — I3 · Drive discovery

- [ ] 14. I3 — bounded, `drive.file`-scoped discovery of owner-approved knowledge
  - **Owning contract / amendment:** PFOS **Contract 05** §8.1 knowledge tools + `drive-db.md`. **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`.** Contract 05 states in its own words that broader Drive enumeration requires **owner authorisation *and* a policy amendment by the owner** — so I3 is scoped to app-created and explicitly-picked files, or it is blocked.
  - **Prerequisites:** **I0 (Task 4) must have landed** — nothing writes to Drive before encryption. I2 (Task 13) complete. **D-5 answered.**
  - **Requirements covered:** 25.1–25.6.
  - **Rollback:** disable the job; the discovery index becomes inert and requires no data change.
  - **Approval boundary:** **Stage 1 only** for the bounded evidence-packet composition and its offline tests, scoped to app-created / explicitly-picked files. **Stage 2 still required for:** any Drive token operation (**A15 INACCESSIBLE** — owner only), any real-data discovery run, and — for **anything beyond app-created or explicitly-picked files** — **owner authorisation *and* a policy amendment**. **Neither stage authorises a scope broadening.**

  - [ ] 14.1 Compose the bounded discovery packet — **AC-I3-1, AC-I3-3**
    - Files: `src/server/ingest/driveEvidencePacket.ts` (exists, re-exported from `hermes/index.ts`); the `knowledge.contextFor` path already composed in `main.ts`; `knowledge.read_github_content` and `knowledge.load_profile_memory`, **both already among the 10** — I3 adds **no** tool. A discovery index is additive.
    - Operate under `drive.file` **only**; enumerate **only** app-created files and files the owner explicitly picked, so `AC08` keeps passing. Bound the packet size.
    - Tests: focused — bounded packet size. Tamper — a modified packet fails its own integrity check. Smoke — `AC08` green.
    - _Requirements: 25.1, 25.4, 25.5, 25.6, 1.7_

  - [ ] 14.2 Enforce the untrusted-data framing at the request boundary — **AC-I3-2**
    - Preserve `turnIntake`'s existing framing **verbatim**: discovered content is *untrusted data, never an instruction, never a tool request, and never authority over policy or deterministic financial facts*.
    - Tests: negative — an instruction-shaped payload in discovered content leaves the resulting route, branch and effect **identical** to those produced with the content absent.
    - _Requirements: 25.2, 25.3_

  - [ ]* 14.3 Write the discovery property tests
    - **Property 46: Discovered content is labelled untrusted and changes no behaviour** — **Validates: Requirements 25.2, 25.3**
    - **Property 47: A discovery packet is bounded** — **Validates: Requirements 25.4**
    - **Property 48: A mutated discovery packet fails its integrity check** — **Validates: Requirements 25.5**
    - _Requirements: 25.2, 25.3, 25.4, 25.5_

---

## Phase 5 — I4 · Deterministic alerts

- [ ] 15. I4 — deterministic-threshold alerts on the existing tick
  - **Owning contract / amendment:** PFOS **Contract 03** §"alerts" + **Contract 12**. **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`.**
  - **Prerequisites:** I2 (Task 13) complete. Consumes I2's registry; adds no clock.
  - **Requirements covered:** 26.1–26.5, 3.1.
  - **Rollback:** disable the job.
  - **Approval boundary:** **Stage 1 only** for the alert planners, the dedup state and their offline tests. **Stage 2 still required for:** live delivery of any alert to the owner's channel — that is live operation on a bound transport.

  - [ ] 15.1 Implement the alert planners with deterministic provenance — **AC-I4-1, AC-I4-2**
    - Files: `src/server/routing/deterministicAlerts*` (a negative-path test already exists at `deterministicAlerts.negative.test.ts`); the reply sender from I1. Alert-state table or `kv` entries for dedup — additive.
    - Every alert figure **traces to a `DeterministicFinancialFact`**. The alerts compose **no** figure from a model result. While the model channel is shut, the deterministic alert route **still answers**.
    - Deduplicate a persisting threshold condition, with dedup state surviving a restart; withhold alerts exceeding the configured per-window cap.
    - Tests: focused — threshold crossings. Negative — no alert composes a figure from a model result; `deterministicAlerts.negative.test.ts` stays green. Restart — dedup survives.
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 3.1, 1.7_

  - [ ]* 15.2 Write the alert property tests
    - **Property 49: No alert digit originates from a model result** — **Validates: Requirements 26.2**
    - **Property 50: Alert deduplication and the window cap hold across a restart** — **Validates: Requirements 26.3, 26.4**
    - _Requirements: 26.2, 26.3, 26.4_

---

## Phase 6 — I5 · Cross-agent handoffs over bounded signals

- [ ] 16. I5 — bounded-signal handoffs, adding zero tools
  - **Owning contract / amendment:** PFOS **Contract 12** §"consent-controlled signal bus" + **Contract 06** (store isolation). **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`.**
  - **Prerequisites:** I1 (Tasks 6–12) complete.
  - **Requirements covered:** 27.1–27.6, 4.2.
  - **Rollback:** stop publishing; readers see no new signals and no data change is required.
  - **Approval boundary:** **Stage 1 only** for the bounded-signal publish/read composition, the `signals.db` usage and their offline tests. **Stage 2 still required for:** cross-agent **live** operation — two running agents exchanging real signals is live operation on a host, and **A14 is INACCESSIBLE**.

  - [ ] 16.1 Compose the bounded-signal publish and read legs — **AC-I5-1**
    - Use **only** `signalbus.publish_bounded_signal` and `signalbus.read_bounded_signals`, **both already members of `HERMES_TOOL_NAMES`** — I5 adds **no** tool. Existing files: `busServer.ts`, `busMain.ts`, `busStart.ts`. Write to `signals.db` **only**, preserving store separation by ownership.
    - A signal payload is **bounded state and carries no grant**; no payload key and no result key matches `AUTHORITY_KEY`. A cross-profile signal is **refused, never downgraded**.
    - Tests: focused — bounded shape. Negative — a monetary key is refused by the existing adapter guard. Tamper — a cross-profile signal is refused. Smoke — the isolation assertions stay green.
    - _Requirements: 4.2, 27.1, 27.3, 27.4, 27.5, 27.6, 1.7_

  - [ ] 16.2 Assert profile isolation holds under two-agent exchange — **AC-I5-2**
    - `assertIngressKeepsInternalIsolation` refuses a shared OpenRouter key, a shared weekly cap and any shared store entry between the `nizam` and `pfos` profiles.
    - **Property 51: A signal is bounded state and never authority-bearing** — **Validates: Requirements 27.1, 27.3**
    - **Property 52: The two profiles share nothing** — **Validates: Requirements 27.2**
    - _Requirements: 27.1, 27.2, 27.3_

---

## Phase 7 — I6 · Continuity

- [ ] 17. I6 — continuity state machine with verified read-back and an encrypted Drive mirror
  - **Owning contract / amendment:** PFOS **Contract 12** §"backup/recovery" + the `dual-channel-memory` spec as an **offline reference authority, not a live cutover**. **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`.**
  - **Prerequisites:** **I0 (Task 4)** — it writes to Drive; I3 (Task 14); I5 (Task 16). **D-5 answered.**
  - **Requirements covered:** 28.1–28.8, 3.10.
  - **Rollback:** continuity is additive and read-only to the rest of the system — disable the job and the mirror.
  - **Approval boundary:** **Stage 1 only** for the continuity state machine, its versioned migration and their offline tests **on synthetic data**. **Stage 2 still required for:** any Drive write of **real** data, plus **G5** (storage consent) and **G8** (backup keypair, private half off-host), both currently `BLOCKED - awaiting human`. **I0 must have landed first.**

  - [ ] 17.1 Implement the continuity state machine and the versioned migration — **AC-I6-1**
    - Files: `src/server/process/journalPersistenceAdapter.ts` (states `LOCAL_WRITTEN | DRIVE_MIRRORED | STAGED_RETRY | FAILED`); `memoryReceipt.ts` and `channelMemory.ts` as **offline references with no live binding** — do **not** describe either as a deployed capability. **This is the first real migration in the program**: continuity state, **versioned**.
    - `DRIVE_MIRRORED` **implies a verified read-back**; a failed mirror **never** reports that state. A process restarting while a record is `STAGED_RETRY` **resumes** that record. The migration **moves no monetary field**.
    - Tests: focused — the state transitions. Negative — a failed mirror never reports `DRIVE_MIRRORED`. Tamper — an altered mirrored file fails read-back. Restart — `STAGED_RETRY` resumes. Smoke — the full harness.
    - _Requirements: 28.1, 28.2, 28.4, 28.5, 28.6, 3.10, 1.7_

  - [ ] 17.2 Route the continuity mirror through the Payload_Envelope and the consent guard — **AC-I6-2**
    - Every continuity payload written to Drive is **encrypted by `payloadEnvelope.ts`** (I0).
    - Where the `mirrorApproved` dependency returns false, the journal adapter attempts **no** mirror call and still reaches `LOCAL_WRITTEN` — the consent gate constrains **egress**, never the owner's own local record. If the `permitted` consent guard **throws**, treat the throw as a **denial**.
    - Tests: focused — a `mirrorApproved` of false yields zero mirror calls and `LOCAL_WRITTEN`; a throwing `permitted()` denies and produces no egress.
    - _Requirements: 28.3, 28.7, 28.8_

  - [ ]* 17.3 Write the continuity property tests
    - **Property 53: DRIVE_MIRRORED implies a verified read-back** — **Validates: Requirements 28.1, 28.2**
    - **Property 54: A mutated mirrored file fails read-back** — **Validates: Requirements 28.4**
    - **Property 55: The consent gate constrains egress and never local truth** — **Validates: Requirements 28.7, 28.8**
    - **Property 38** extended to the continuity mirror path — every Drive-bound continuity write receives ciphertext. **Validates: Requirements 28.3**
    - **Property 14: A migration moves no money** — re-asserted for the continuity migration. **Validates: Requirements 28.6, 3.10**
    - _Requirements: 3.10, 28.1, 28.2, 28.3, 28.4, 28.6, 28.7, 28.8_

---

## Phase 8 — I7 · Recovery

**Hard-blocked on G8.** An archive produced **before G8** voids the ciphertext-only guarantee **retroactively for every archive**. A gate whose breach cannot be undone is a hard blocker, not a checklist item.

- [ ] 18. I7 — archive-and-restore rehearsal on synthetic data in a scratch location
  - **Owning contract / amendment:** PFOS **Contract 12** §"backup/recovery"; `ops/DEPLOYMENT_CONTROL.md` for the gates. **Requires a new dated inline amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md`.** This program **never executes, tests, populates or marks complete** any part of the control record.
  - **Prerequisites:** I6 (Task 17) complete. **G8 is `BLOCKED - awaiting human` and is a hard blocker** on any archive of real data. **G5** also applies.
  - **Requirements covered:** 29.1–29.7, 12.4, 12.5.
  - **Rollback:** not applicable — **recovery is exercised, not deployed. A failed rehearsal is a finding**, recorded as one.
  - **Approval boundary:** **Stage 1 only** for the archive/restore round-trip code and its offline tests **on synthetic data in a scratch location only**. **Stage 2 still required for: G8 — owner-only and a hard blocker.** No archive of real data may be produced before G8. This program **generates no key, produces no archive of real data and writes to no host.**

  - [ ] 18.1 Implement the archive-and-restore round trip on synthetic data — **AC-I7-1, AC-I7-2**
    - Files: `backupMain.ts`, `backupStart.ts`, `backupUploader.ts` (all exist with tests). No schema beyond I6.
    - Restoring an archive of a synthetic dataset to a **scratch location** produces an equal dataset. A restore with the **wrong key refuses**. A **mutated archive refuses**. An **interrupted restore** either resumes to equality or refuses cleanly, and **never presents a partial dataset as complete**.
    - Tests: focused — round trip on synthetic data. Negative — wrong-key restore refuses. Tamper — a mutated archive refuses. Restart — a partial restore resumes or refuses cleanly. Smoke — the full harness.
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 1.7_

  - [ ] 18.2 Record the G8 ordering constraint and the observation requirement — **AC-I7-3**
    - Record in the amendment section that **while G8 is unsatisfied, no archive of real data is produced**, and why: one archive produced early voids the ciphertext-only guarantee retroactively for **every** archive.
    - Record that the restore must be **independently observed by the owner**, that a rehearsal never exercised **is not** recorded as a backup, and that a failed rehearsal is recorded as a **finding**. These three are **owner-observation** items and are marked as such — no test can substitute for them.
    - Record that this program generates no key, rotates no key, renews no consent and broadens no scope.
    - _Requirements: 12.4, 12.5, 29.5, 29.6, 29.7_

  - [ ]* 18.3 Write the recovery property tests
    - **Property 56: Archive then restore is the identity on synthetic data** — **Validates: Requirements 29.1**
    - **Property 57: A wrong-key restore is refused** — **Validates: Requirements 29.2**
    - **Property 58: A mutated archive is refused** — **Validates: Requirements 29.3**
    - **Property 59: An interrupted restore never presents a partial dataset as complete** — **Validates: Requirements 29.4**
    - _Requirements: 29.1, 29.2, 29.3, 29.4_

- [ ] 19. Final checkpoint — program-level verification
  - Run the focused tests, then `npm run typecheck`, `npm run lint`, `npm run build`, then `npm run verify:all -- --all`. **Expect 19 of 21 with only `AC14` and `AC15` failing on the 54 dirty entries — the correct baseline, not a regression.**
  - Walk the acceptance/smoke checklist in `acceptance-checklist.md` and record, per increment, which items are **offline-only** and which are **owner-observation-only**. Confirm **no artifact anywhere claims exactly-once delivery**.
  - Confirm the 54 dirty entries are still preserved as found and that **no commit and no push** was created. Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 2.6, 7.1, 7.2, 7.3, 7.4, 22.13_

---

## Requirements coverage map

Every requirement 1–29 maps to at least one task. Criteria whose only vehicle is **document review** or **owner observation** are covered by an amendment-record task (Tasks 2, 12, 18.2) rather than by a test, and are marked so rather than dressed up as automatable.

| Req | Subject | Covering tasks |
|---|---|---|
| 1 | Two-stage approval model | 2.1 (1.1–1.6, document review) · 11.2 (1.7) · every code sub-task cites 1.7 |
| 2 | Standing constraints preserved | 11.1 (2.1–2.3) · 11.2 (2.4, 2.7) · 2.1 (2.5, 2.6, 2.8) · 4.6 (2.7) · 19 (2.6) |
| 3 | Money provenance and determinism | 7.2 (3.1–3.5) · 7.3 (3.6, 3.7) · 9.4 / 9.7 (3.8) · 7.1 (3.9) · 4.6, 17.1, 17.3 (3.10) · 15.1 (3.1) |
| 4 | Tool boundary and effective surface | 11.1 (4.1–4.5) · 10.1, 10.2 (4.6–4.8) · 16.1 (4.2) · 9.7 (4.5) |
| 5 | Privacy of observations and thrown values | 7.1 (5.1) · 7.7 (5.1–5.6) · 7.4 (5.5) |
| 6 | Queue, scheduler, single-writer authority | 8.6 (6.1–6.5, 6.9, 6.10) · 8.1 (6.6) · 8.2 (6.5) · 13.2 (6.7, 6.8) · 13.3 (6.8) · 8.3 (6.11) · 7.1 (6.12) |
| 7 | Repository gates and the measured baseline | 2.2 (7.5–7.10) · 1.5 (7.9) · 4.5 (7.2, 7.9) · 5, 12, 19 (7.1–7.4) |
| 8 | Blocking decisions as prerequisites | 1.1–1.6 (8.1–8.14) · 2.3 (8.15) · 3 (8.1, 8.4, 8.5) |
| 9 | Evidence labelling | 2.2 (9.1–9.4) · 1.2 (9.3) |
| 10 | Drive payload encryption | 4.1 (10.2–10.6, 10.10) · 4.2 (10.4–10.7, 10.11) · 4.5 (10.1, 10.8) · Task 4 Rollback (10.9) |
| 11 | Transaction-candidate egress | 4.3 (11.1, 11.2, 11.5) · 4.4 (11.3, 11.4) · 1.2 (11.5) |
| 12 | Key custody and Drive scope | 4.7 (12.1–12.3) · 4.2 (12.1) · Task 4 Approval boundary (12.4, 12.5) · 18.2 (12.4, 12.5) |
| 13 | Governed deterministic path composition | 7.1 (13.1, 13.6–13.10) · 7.4 (13.2) · 7.2 (13.3) · 7.3 (13.4, 13.5) · 8.3 (13.8) · 9.7 (13.1, 13.7) |
| 14 | Pre-tier governed admission | 6.1 (14.1–14.3, 14.6, 14.7) · 6.2 (14.1–14.3, 14.6) · 8.2 (14.4, 14.5) · 9.7 (14.4, 14.5) |
| 15 | Reachability R-1 | 9.1 (15.1–15.4) · 9.7 (15.1, 15.3) |
| 16 | Reachability R-2 | 9.2 (16.1–16.5) · 9.7 (16.1, 16.3) · 7.6 (16.4) |
| 17 | Reachability R-3 and R-3b | 9.3 (17.1–17.3) · 9.4 (17.3a–17.3d, 17.4) · 9.6 (17.5) · 2.3 (17.6) · 9.7 (17.1–17.3) |
| 18 | Reachability R-4 | 9.5 (18.1–18.4) · 9.7 (18.1, 18.3) |
| 19 | Reachability R-5 | 9.5 (19.1–19.4) · 9.7 (19.1, 19.2, 19.4) |
| 20 | Reachability gate on the slice | 9.6 (20.3, 20.4) · 2.3 (20.1, 20.2, 20.4, 20.5) · 1.1, 1.4 (20.5) · 12 (20.1, 20.2) |
| 21 | Capture receipt honesty | 7.4 (21.1–21.8) · 7.5 (21.1–21.5, 21.7, 21.8) · 8.5 (21.3) |
| 22 | Capture ordering, idempotence, honest delivery | 7.4 (22.3, 22.6, 22.7) · 7.5 (22.3, 22.4, 22.6) · 8.4 (22.1, 22.2, 22.5, 22.8–22.12, 22.14) · 8.5 (22.2, 22.5, 22.9–22.12, 22.14) · 8.6 (22.1, 22.11) · 2.3 / 19 (22.13) · 1.3 (22.9, 22.13, 22.14) |
| 23 | Seam shape, worker wiring, rollback | 8.1 (23.1–23.5, 23.9) · 8.3 (23.6, 23.7) · 11.3 (23.8, 23.9) · 8.6 (23.2, 23.5, 23.9) · 1.4 (23.1) · 9.7 (23.4) |
| 24 | I2 scheduled jobs as a consumer | 13.1 (24.3, 24.5–24.8) · 13.2 (24.1, 24.2, 24.4, 24.9, 24.10) · 13.3 (24.3, 24.4, 24.6, 24.8, 24.9) · 1.5 (24.10) |
| 25 | I3 Drive discovery | 14.1 (25.1, 25.4–25.6) · 14.2 (25.2, 25.3) · 14.3 (25.2–25.5) |
| 26 | I4 deterministic alerts | 15.1 (26.1–26.5) · 15.2 (26.2–26.4) |
| 27 | I5 cross-agent handoffs | 16.1 (27.1, 27.3–27.6) · 16.2 (27.1–27.3) |
| 28 | I6 continuity | 17.1 (28.1, 28.2, 28.4–28.6) · 17.2 (28.3, 28.7, 28.8) · 17.3 (28.1–28.4, 28.6–28.8) |
| 29 | I7 recovery | 18.1 (29.1–29.4) · 18.2 (29.5–29.7) · 18.3 (29.1–29.4) |

---

## Notes

- **Every task above is blocked pending Stage-1 owner approval of the plan.** Nothing in this file is authorization. Where a task needs nothing beyond Stage 1, its Approval boundary reads **"Stage 1 only."**
- **Phase 0 is the real blocker.** D-8 decides I1's file list; D-5 decides whether I0 has a module to write; D-11 decides the shape of the send leg. **D-2 and D-6 carry `None offered` and must not receive an invented default.**
- Sub-tasks marked `*` are optional supplementary tests. **The six reachability cases (Task 9.1–9.6) and the five failure-injection cases (Task 8.5) are gates and are not optional.**
- **Delivery is at-least-once.** No task, test, comment, observation, reply or artifact may claim exactly-once **delivery**. Exactly-once is claimed of the **canonical journal write** only.
- **I1 adds zero tools.** `HERMES_TOOL_NAMES` stays at 10, and the deterministic leg is a **worker branch, not a tool**.
- **Two coverage gaps are recorded and not filled.** `AC12` checks neither PFOS 01–15 nor any amendment, so every amendment record this plan authors is **unverified by the harness**. And **no check among the twenty-one enforces Drive encryption** — `AC08` is scope only. **Invent no new check for either**; changing the declared count of 21 is an owner decision.
- **The expected baseline is 19 of 21**, with `AC14` and `AC15` failing on the 54 dirty entries. Treating that as a regression would be a false alarm. The full checklist lives in `acceptance-checklist.md`.
- The 54 dirty working-tree entries are **preserved as found**. No task creates a commit or a push. The UPOI 20-entry registry is **untouched**.

## Task Dependency Graph

Waves are separated so that **no two sub-tasks in one wave write the same file**. `driveDb.ts` is touched by 4.1, 4.3 and 4.5; `governedTurnPath.ts` by 7.1–7.4; `turnWorker.ts` by 8.1, 8.2 and 8.4; and `turnAdmission.test.ts` by 6.2 and 9.1–9.6 — each of those groups is therefore serialised. Checkpoint tasks (3, 5, 12, 19) and top-level parents are not in the graph.

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["4.1", "6.1", "10.1"] },
    { "id": 5, "tasks": ["4.2", "4.3", "6.2", "7.1", "10.2"] },
    { "id": 6, "tasks": ["4.4", "7.2"] },
    { "id": 7, "tasks": ["4.5", "7.3"] },
    { "id": 8, "tasks": ["4.6", "4.7", "7.4"] },
    { "id": 9, "tasks": ["7.5", "8.1"] },
    { "id": 10, "tasks": ["7.6", "8.2"] },
    { "id": 11, "tasks": ["7.7", "8.3"] },
    { "id": 12, "tasks": ["8.4", "11.1", "11.2"] },
    { "id": 13, "tasks": ["8.5", "11.3"] },
    { "id": 14, "tasks": ["8.6", "9.1"] },
    { "id": 15, "tasks": ["9.2"] },
    { "id": 16, "tasks": ["9.3"] },
    { "id": 17, "tasks": ["9.4"] },
    { "id": 18, "tasks": ["9.5"] },
    { "id": 19, "tasks": ["9.6"] },
    { "id": 20, "tasks": ["9.7", "13.1"] },
    { "id": 21, "tasks": ["13.2", "16.1"] },
    { "id": 22, "tasks": ["13.3", "14.1", "15.1", "16.2"] },
    { "id": 23, "tasks": ["14.2", "15.2"] },
    { "id": 24, "tasks": ["14.3"] },
    { "id": 25, "tasks": ["17.1"] },
    { "id": 26, "tasks": ["17.2"] },
    { "id": 27, "tasks": ["17.3"] },
    { "id": 28, "tasks": ["18.1"] },
    { "id": 29, "tasks": ["18.2", "18.3"] }
  ]
}
```
