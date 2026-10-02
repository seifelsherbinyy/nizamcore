# Acceptance / Smoke Checklist: hermes-governed-workflows

Companion to `.kiro/specs/hermes-governed-workflows/tasks.md`. Derived from `design.md` (§0–§L, corrected) and `requirements.md` (29 requirements, corrected). **design.md wins on conflict.**

---

# ⛔ STAGE-1 GATE

> **Every item on this checklist is blocked pending Stage-1 owner approval of the plan.** Running a check is not implementation, but *the work each item verifies* is, and **all implementation — including local and offline code changes and test changes — waits for explicit owner approval of `design.md` plus `requirements.md`** (design §0.5; Requirement 1.1).
>
> **There is no "no approval required" category on this checklist.** Where an item needs nothing beyond Stage 1, it is marked **"Stage 1 only."** That phrase never means "no approval" (Requirement 1.2, 1.3).
>
> **Stage 2 is separate and is never implied by Stage 1:** live operation, deployment, credentials, host mutation, provider spend, and the human gates **G1–G8**. A green run here authorizes **none** of them (Requirement 1.4, 1.5).
>
> **This checklist is a planning artifact and confers no implementation authorization.** It resolves no owner decision.

---

## 0. The headline, before anything else

> ### Passing tests is NOT live readiness.
>
> A green offline suite establishes **composition and refusal behaviour on synthetic fixtures, in this repository, on this machine**. It establishes **nothing** about a running host, a bound transport, a loaded MCP surface, a real ledger, the nizamcore native writer's actual ordering, or Drive at rest.
>
> A green result is **not** a Stage-2 approval and **not** evidence about any running system. `AC04`'s floor (`--min 3009`) measures suite **size**, not coverage of reality. **None of the twenty-one checks observes a host, a credential, a transport or a provider.** _Requirements: 7.6_

Three gates sit outside the twenty-one and are not automatable at all: the **human gates G1–G8**, **D-4** (unique ingress ownership — a live run before it resolves may be consumed by the wrong process), and **Stage-1 plan approval** itself.

---

## 1. Repository gates — unchanged in name, number and weight

Run exactly these. No increment in this program adds, removes, renames or reweights a check. _Requirements: 7.1, 7.2_

```
npm run typecheck
npm run lint
npm test -- --run <pattern>
npm run build
npm run verify:all -- --all
```

The focused three (`typecheck`, `lint`, the targeted test) are the development loop. `build` and `verify:all -- --all` are the handoff gate. The declared check count in `scripts/verify/all.mjs` is **21** and stays 21. **Adding a check is a harness change and therefore an owner decision.** _Requirements: 7.2, 7.9_

**Scope of this section: Stage 1 only.**

---

## 2. Expected baseline — 19 of 21, and why that is correct

> ### Expected result: **19 of 21**, with **`AC14`** (working tree is clean) and **`AC15`** (repository is push ready and unpushed) **failing** on the **54 dirty working-tree entries**.
>
> **A run reporting 19/21 with only those two failing is THE CORRECT BASELINE, NOT A REGRESSION.** Reporting it as a regression is a false alarm. _Requirements: 7.3, 7.4_

- [ ] `npm run verify:all -- --all` reports **19 of 21**.
- [ ] The **only** two failures are `AC14` and `AC15`.
- [ ] Any **third** failure is a genuine regression and is investigated as one.
- [ ] The **54 dirty entries are preserved as found** — 10 tracked modifications, 44 untracked. **No commit and no push was created.** _Requirements: 2.6_

**Evidence labelling, applied honestly.** The **19-of-21 figure is STALE as a measurement** (2026-09-16 receipt, not re-observed). Its **cause — the 54 dirty entries — is VERIFIED**. _Requirements: 7.5_

**Why 21/21 is unreachable.** The untracked set includes `?? .kiro/specs/hermes-governed-workflows/` — **this spec is itself one of the entries that makes the gate fail** — plus all eleven `FINANCIAL/` O-documents and `scripts/verify/all.mjs` itself, which is among the 10 modified files. Disposition of the 54 is **D-6**, which carries **`None offered`** and is **not answered here**. _Requirements: 8.5_

**Scope of this section: Stage 1 only** to run; **Stage 2, owner-only** to change the tree state.

---

## 3. The nineteen git-independent checks that must stay green

Every one of the twenty-one is offline. **Nineteen are offline AND independent of git state** — these are the ones a change to this program can break, and they must all stay green. _Requirements: 7.1, 7.2_

| # | Id | Label | Must stay green |
|---|---|---|---|
| 1 | `AC16` | toolchain pin, lockfile and launch path | [ ] |
| 2 | `AC10` | source files declare their contract and phase | [ ] |
| 3 | `AC01` | no placeholders remain in src | [ ] |
| 4 | `AC07` | money stays integral | [ ] |
| 5 | `AC19` | protected repository invariants are fail closed | [ ] |
| 6 | `AC08` | drive scope is per file only | [ ] |
| 7 | `AC09` | no secrets or real ledgers tracked | [ ] |
| 8 | `AC11` | no organization specific terms | [ ] |
| 9 | `AC18` | no deployment particular in ops or any fixture | [ ] |
| 10 | `AC02` | typescript reports zero errors | [ ] |
| 11 | `AC03` | linter is clean at zero warnings | [ ] |
| 12 | `AC04` | test suite passes and meets its size floor (`--min 3009`) | [ ] |
| 13 | `AC13` | verification ledger is intact and covering | [ ] |
| 14 | `LOOP` | loop refusal paths hold | [ ] |
| 15 | `AC05` | production build emits a static application (**produces** `dist`) | [ ] |
| 16 | `AC05b` | built output shape is valid (**needs** `dist`) | [ ] |
| 17 | `AC06` | built output has no remote asset reference (**needs** `dist`) | [ ] |
| 18 | `AC08b` | ingestion tooling and server tier stay isolated (**needs** `dist`) | [ ] |
| 19 | `AC12` | contract index and build log agree — **see §4 for its real scope** | [ ] |

The remaining two are offline but **git-state-dependent** and are the two that fail: `AC14`, `AC15`.

**Ordering note:** `AC05` produces `dist`; `AC05b`, `AC06` and `AC08b` need it. Run them in the declared order.

**Scope of this section: Stage 1 only.**

---

## 4. Two recorded coverage gaps — neither is filled, and no new check is invented

### 4.1 The `AC12` gap

`scripts/verify/contract-ledger.mjs`, read in full:

| It **does** check | It does **NOT** check |
|---|---|
| `contracts/_CONTRACT_INDEX.md` and `contracts/_BUILD_LOG.md` — **these two files only** | **PFOS contracts 01–15.** `contracts/pfos/_PFOS_CONTRACT_INDEX.md` and `contracts/pfos/_PFOS_BUILD_LOG.md` appear **nowhere** in the script |
| That the index has **exactly five** contract rows | **Amendments.** No supersession, amendment, date or heading logic **of any kind** |
| Index rows, matched positionally by a single digit | `contracts/CONTRACT_6`, which exists as a file but is not indexed |
| Build-log phases, collected only as passing gate lines | Any PFOS phase, gate or record |
| Both directions — done-without-phase and phase-without-contract | Whether any PFOS contract's claims are true |

> **Consequence, stated plainly: a PFOS-contract record or an amendment record added by this program is covered by NO acceptance check.** The **inline build-log amendment channel** every increment in `tasks.md` relies on as its recording channel is **unverified by the harness**. `AC12` going green says the five *repository* build contracts agree with `contracts/_BUILD_LOG.md`, and says **nothing** about PFOS 01–15 or about any amendment. _Requirements: 7.7, 7.8_

- [ ] Recorded in the amendment section. **No new check invented.** Extending `AC12`, or adding an `AC22`, changes the declared count that `all.mjs` asserts — **a harness change and therefore an owner decision.** _Requirements: 7.9_

### 4.2 The Drive-encryption gap

> **No check among the twenty-one enforces the Drive encryption requirement. `AC08` enforces SCOPE ONLY** (`drive.file`). _Requirements: 7.10_

- [ ] The I0 no-plaintext assertion is implemented **as a test**, in the spirit of `AC08`, and **not** as a twenty-second harness check. _Requirements: 10.1, 7.9_
- [ ] Recorded that a green `AC08` says nothing about whether Drive data is encrypted at rest.

**Scope of this section: document review.**

---

## 5. Delivery semantics — at-least-once, and no item may say otherwise

> ### The delivery semantics on this checklist are **AT-LEAST-ONCE**.
>
> **No item on this checklist asserts exactly-once delivery.** Exactly-once is asserted of the **canonical journal write** only. _Requirements: 22.9, 22.13_

The three guarantees, separated and never to be merged again:

| # | Guarantee | Status | Mechanism |
|---|---|---|---|
| (i) | **Canonical-write exactly-once** | **GUARANTEED** | `recordId = captureRecordId(item.queuedRef)`, caller-frozen and payload-independent; a replay returns `IDEMPOTENT_REPLAY` with the same `entryRef` and writes nothing. VERIFIED against the local adapter; **UNVERIFIED against the native writer (D-7)**. |
| (ii) | **Settlement idempotence** | **GUARANTEED** | the `state = 'running'` predicate on the settle; a second call matches no row and reports `settled: false`. |
| (iii) | **External delivery exactly-once** | **NOT GUARANTEED** | **No mechanism exists.** `sendMessage` takes no idempotency key, `TelegramOutboundMessage` carries no correlation ref, the receipt is discarded, and a crashed row is deliberately returned to `queued` for a re-send. |

Two interruption points duplicate a delivery, and both are modelled rather than left as "a crash":

- **Case D-A** — send accepted, acknowledgement lost. The bounded retry re-sends; the owner may receive the reply twice. Bounded by `maxAttempts`, not eliminated.
- **Case D-B** — send succeeded, crash before settle. The row is reclaimed and re-processed; the canonical write is suppressed by `recordId`, but the reply is re-issued. Unbounded across repeated crashes.

**What is not at risk in either case:** no second canonical entry, no double settlement, and no figure from a non-deterministic source — a re-sent reply is re-composed from the same observed receipt or the same `DeterministicFinancialFact`, so a duplicate is a **repetition, never a divergence**.

### 5.1 Planned failure-injection items — FI-1 … FI-5

**Planned, not run.** Every one is **offline**, on synthetic fixtures, with injected ports and a **fake transport**: no host, no credential, no provider spend. Shape blocked on **D-11**. **Not optional — this is the honest-delivery gate (AC-I1-18).**

| # | Injection | Expected observation |
|---|---|---|
| [ ] **FI-1** | Send resolves, then the process is killed **before** `settle`. | Exactly **one** canonical entry. The reply **is** re-sent on the re-claim — asserted **as a fact, not as a defect**. The row settles `done` exactly once. |
| [ ] **FI-2** | Send rejects with a `TelegramRateLimitRefusal` carrying `retryAfterSeconds` **after** the provider actually accepted. | Duplicate delivery is **observable and reported** — surfaced in the redacted observation and in the test's own assertion — and **never silently swallowed**. |
| [ ] **FI-3** | `reclaimStalledWork` returns a `running` row whose send already succeeded. | `recordId` suppresses the second **canonical write**. Under **D-11(b)** the reconciliation record suppresses the second **send**, and the assertion is a **narrowing, not a closure** — a crash between provider-accept and receipt-persist still duplicates. Under **D-11(a)** the second send occurs and the test asserts it is **reported**. |
| [ ] **FI-4** | `settleWork(done)` called repeatedly on the same `queuedRef`. | The second and every later call reports `settled: false` and writes nothing (guarantee (ii)). |
| [ ] **FI-5** | Crash between the canonical write and the read-back. | The reply is `captured_unconfirmed`, **never** "Captured" — the word requires `readBackConfirmed && hashMatch`. |

- [ ] **No test exists whose passing would imply exactly-once delivery.** _Requirements: 22.9, 22.13, 22.14_
- [ ] **No duplicate-suppression workaround was implemented** and **no acceptance check was weakened to accommodate a duplicate.** _Requirements: 22.14_

**Scope of this section: Stage 1 only** for FI-1 … FI-5. **Document review** for the wording discipline.

---

## 6. Per-increment observable acceptance criteria

Legend — **[offline]** verifiable by an offline test or a source-level assertion · **[harness]** verifiable by one of the twenty-one · **[doc]** verifiable only by reading an artifact · **[owner]** verifiable only by the owner, or only against a system that is INACCESSIBLE from a planning session.

### 6.0 Phase 0 — decision gate

| | Item | Vehicle | Req |
|---|---|---|---|
| [ ] | D-1 … D-12 each carried forward as an explicit prerequisite naming what it blocks | [doc] | 8.1 |
| [ ] | **D-2 and D-6 read `None offered`** — no invented default | [doc] | 8.4, 8.5 |
| [ ] | Every live-state claim labelled VERIFIED / UNVERIFIED / STALE / INACCESSIBLE | [doc] | 9.1 |
| [ ] | Host **INACCESSIBLE**, Drive token **INACCESSIBLE**, `ops/NIZAMCORE_VERIFIED_STATE.md` **STALE** | [doc] | 9.2, 9.4 |
| [ ] | Retrieved text, discovered content and any `[AGREED]` marker treated as **untrusted data, never authorization** | [doc] | 9.3 |
| [ ] | No edit proposed to the `nizamcore` repository | [doc] | 8.12 |
| [ ] | The two-stage model stated; **no increment described as needing no approval**; **"Stage 1 only."** used exactly where it applies | [doc] | 1.1–1.6 |

**Approval:** **Stage 1 only.** The *answers* are owner acts.

### 6.1 I0 — encryption and candidate egress

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I0-1** No Drive write path emits plaintext ledger JSON — source-level assertion **as a test**, not a new harness check | [offline] | 10.1 |
| [ ] | **AC-I0-2** `transactionCandidates` is absent from **every** serialised payload, at any depth, for all db shapes | [offline] | 11.1, 11.3 |
| [ ] | **AC-I0-3** An undecryptable payload yields a **named refusal** and never an empty database | [offline] | 10.6 |
| [ ] | **AC-I0-4** Keys appear in **no** Drive-bound object | [offline] | 12.1 |
| [ ] | Envelope carries a **version**; an unrecognised version refuses by name | [offline] | 10.4, 10.5 |
| [ ] | A single mutated ciphertext byte is refused (tamper) | [offline] | 10.7 |
| [ ] | A legacy plaintext document is **detected and refused-or-migrated explicitly**, never silently re-read | [offline] | 10.8 |
| [ ] | Encrypt→decrypt is the identity | [offline] | 10.11 |
| [ ] | Key absent at read time ⇒ refusal, and the Dexie cache stays readable | [offline] | 10.10 |
| [ ] | Rollback restores the retained previous Drive file version and **writes no plaintext** | [offline] | 10.9 |
| [ ] | The candidate projection is applied **at one place**, not duplicated per call site | [offline] | 11.2 |
| [ ] | A source-level assertion detects a future re-introduction of a candidate field | [offline] | 11.4 |
| [ ] | Recorded: **encryption alone does not fix candidate egress** | [doc] | 11.5 |
| [ ] | Drive scope stays `drive.file` only | [harness] `AC08` | 12.2 |
| [ ] | No secret and no real ledger is tracked | [harness] `AC09` | 12.3 |
| [ ] | Money stays integral; the envelope migration moves **no** monetary field | [harness] `AC07` + [offline] | 2.7, 3.10 |
| [ ] | **No key generated, rotated; no consent renewed; no scope broadened** | [owner] | 12.4 |
| [ ] | **G5 and G8 recorded `BLOCKED - awaiting human` ⇒ no real-data Drive sync enabled** | [owner] | 12.5 |

**Approval:** **Stage 1 once D-5 is answered** for every [offline] item. **Stage 2** for real-data sync, G5, G8, and all key work.

### 6.2 I1 — the governed vertical slice

The ten baseline criteria:

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I1-1** A `mal` + `pfos_read` turn replies with the deterministic `resultRef` and integer-milliunit values copied **verbatim** | [offline] | 3.1, 3.2, 3.3 |
| [ ] | **AC-I1-2** An unavailable source yields a **digit-free** reply and **no** substitute figure | [offline] | 3.6, 13.4 |
| [ ] | **AC-I1-3** An assertion-failing result yields a digit-free reply and **no** substitute figure | [offline] | 3.7, 13.5 |
| [ ] | **AC-I1-4** A `local_write` turn reports the **writer's own** `entryRef` | [offline] | 21.7 |
| [ ] | **AC-I1-5** `REFUSED_SECRET` / `REFUSED_UNKNOWN_WRITE` yield the router's `publicReason` with **zero effect** | [offline] | 13.1, 18.1 |
| [ ] | **AC-I1-6** `HERMES_TOOL_NAMES.length === 10` | [offline] | 4.1 |
| [ ] | **AC-I1-7** All three `DENIED_AUTHORITY_TOOLS` still refuse; `AUTHORITY_KEY` unrelaxed; no exception carved | [offline] | 4.3, 4.4 |
| [ ] | **AC-I1-8** No observation and no thrown `detail` contains turn text | [offline] | 5.2 |
| [ ] | **AC-I1-9** `settle done` occurs **only** after a delivered send | [offline] | 6.5 |
| [ ] | **AC-I1-10** `assessEffectiveToolSurface` returns `unobserved` (**never** `ok`) when `method === null` | [offline] | 4.6 |

The reachability gate — **six** cases. **The slice is NOT claimed successful until all six pass**, even if every criterion above is green. A failing case fails **loudly with the case identified** and never degrades to a passing weaker assertion. _Requirements: 20.1, 20.3_

| | Case | Observable AC | Vehicle | Req |
|---|---|---|---|---|
| [ ] | **R-1** | **AC-I1-11** `write this down: the fridge broke` ⇒ `ROUTED` · `yawmiyat` · `local_write` · branch `governed_deterministic`; `classifyTurn` **never called**, no channel invoked; reply is a **writer receipt** | [offline] | 15.1–15.4 |
| [ ] | **R-2** | **AC-I1-12** `what is my balance` ⇒ `ROUTED` · `mal` · `pfos_read` · `governed_deterministic`; no model; reply carries `resultRef` + digits **byte-identical** to each `fact.amountMilliunits`; both assertions ran in order first | [offline] | 16.1–16.5 |
| [ ] | **R-3** *(re-specified)* | **AC-I1-13** `how much is safe to spend` ⇒ `ROUTED` · `mal` · `pfos_read` · `governed_deterministic` — **because `FINANCE` contains `\bsafe to spend\b`**; **no model, no grant**; reply is the verified-deterministic shape **or** a digit-free refusal | [offline] | 17.1–17.3 |
| [ ] | **R-3b** *(new)* | **AC-I1-13b** a `SHURA` phrase carrying **no `FINANCE` token** ⇒ `ROUTED` · `shura` · `read` · branch **`tier_path`**; `classifyTurn` called, a grant **minted**, a **fake** channel records it reached; reply **digit-free** | [offline] | 17.3a–17.3d, 3.8 |
| [ ] | **R-4** | **AC-I1-14** secret-seeking text ⇒ `REFUSED_SECRET` · `refuse` · `none`; **zero effect**, no port touched, **no model invocation**; reply **leaks no reason** | [offline] | 18.1–18.4 |
| [ ] | **R-5** | **AC-I1-15** unmatched text ⇒ `CLARIFY` · `clarify` · `none`; zero effect; **does not** become a paid conversational turn via `DEFAULT_PROSE_INTENT` | [offline] | 19.1–19.4 |
| [ ] | gate | R-3 and R-3b carried as **two distinct cases**; **R-3 is not the tier-path guard**; case count is **six** | [offline] | 20.4 |
| [ ] | gate | A lexicon/expectation disagreement **fails the suite and names both cases** — it must **not** be resolved by editing a fixture or reclassifying a case | [offline] | 17.5 |
| [ ] | gate | Both ingress lexicons quoted verbatim, so no case rests on an unquoted lexicon | [doc] | 17.6 |
| [ ] | gate | Recorded: under D-8 option (a) the model tier is reachable **only** from effect `read`, so **no finance wording of any kind reaches a model** — a stronger money guarantee, and the capability gap **D-12** | [doc] | 20.5 |
| [ ] | gate | The **fake** model channel is used throughout; **no real provider invocation and no provider spend** | [offline] | 17.4 |

Capture receipt, ordering and delivery:

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I1-16** The word **"Captured"** appears **only** when `readBackConfirmed && hashMatch`; `LOCAL_WRITTEN` alone yields the weaker honest reply; `STAGED_RETRY` yields the same weaker wording; `FAILED` / `null` record / a thrown call yields `capture_refused` | [offline] | 21.1–21.5 |
| [ ] | A read-back disagreeing with the expected payload hash ⇒ state `FAILED` ⇒ `capture_refused` | [offline] | 21.6 |
| [ ] | A **remote** capture is treated as `captured_unconfirmed` by default while **D-7** is unresolved | [offline] | 21.8 |
| [ ] | A `recoveryAction` string reaches the **redacted observation** and **not** the owner's reply | [offline] | 5.5 |
| [ ] | **AC-I1-17** A replayed turn returns the **same** `entryRef` and performs **no** second canonical write | [offline] | 22.4 |
| [ ] | `captureRecordId` derives identity from the **queue ref**, not the payload; byte-identical across replays | [offline] | 22.3, 22.6 |
| [ ] | `updatePolicy` stays `REFUSE`; a replay with different text under the same `recordId` ⇒ `JOURNAL_UPDATE_NOT_PERMITTED` ⇒ `capture_refused`, never a silent revision | [offline] | 22.7 |
| [ ] | The **five-step** ordering holds: canonical write → verified read-back → **compose reply from observed receipt fields** → send → settle `done` | [offline] | 22.1 |
| [ ] | A crash or send failure between the write and the settle **re-delivers, never re-writes** | [offline] | 22.2 |
| [ ] | A restart after a canonical write and before a send leaves **exactly one** canonical entry, and the reply is delivered **at least once** | [offline] | 22.5 |
| [ ] | An item left unsettled beyond its lease is reclaimed to `queued` and re-processed as a later attempt | [offline] | 22.8 |
| [ ] | **AC-I1-18** The plan and the implementation claim **at-least-once** delivery and claim exactly-once **nowhere**; a duplicate reply is **reported, never silently swallowed** | [offline] + [doc] | 22.9, 22.10, 22.13 |
| [ ] | **AC-I1-19** A repeated `settleWork(done)` on one `queuedRef` reports `settled: false` and writes nothing | [offline] | 22.11, 22.12 |
| [ ] | Recorded: **D-11(b) narrows the duplicate window and does not close it** | [doc] | 8.15 |

Seam, composition, invariants and rollback:

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | `Answer = Promise<string>`; `renderAnswer` stays the identity, return type widened to `string \| Promise<string>`, awaited on `code_only` | [offline] | 23.1, 23.2, 23.9 |
| [ ] | **`turnDispatch.ts` receives no edit** — its deterministic branch still returns before any `await` | [offline] | 23.3 |
| [ ] | The optional `executeTurnDeterministically` override applies to **one item only**, holds **no grant**, and **cannot reach `channel.invoke`** | [offline] | 23.4, 23.5 |
| [ ] | `main.ts` builds the executor **once** and takes the per-item closure per turn; `answerDeterministically` **retained** as the fallback | [offline] | 23.6, 23.7 |
| [ ] | Rollback = remove one `main.ts` line + the worker's admission branch ⇒ current behaviour, **no data change, no migration**; recorded that it **restores the reachability defect** | [offline] + [doc] | 23.8 |
| [ ] | Unmodified: `turnDispatch.ts`, `turnClassifier.ts`, every `src/server/hermes/*`, `operatorMessagePort.ts`, `scheduler.ts`, `singleWindowFlow.ts`; **no schema migration** | [offline] | 13.9, 13.10 |
| [ ] | Unmodified: `TURN_INTENT_TRIGGER`, `INTENT_FAMILY`, `PROSE_INTENTS`, `DEFAULT_PROSE_INTENT` | [offline] | 14.7 |
| [ ] | The governed path owns **no** store, socket or clock; ports and clock injected; **no import from `src/lib/money`** | [offline] | 13.8, 3.9 |
| [ ] | The governed path calls **`appendRecord` only**, never the legacy `appendWithReceipt` | [offline] | 6.12 |
| [ ] | An unreadable raw body yields `null` and the path proceeds **without throwing** | [offline] | 13.7 |
| [ ] | Slack Socket Mode is the sole transport, three aliases only; the five `REVOKED_TELEGRAM_ALIASES` refused; **no Telegram cutover** | [offline] | 2.1, 2.2, 2.3 |
| [ ] | `OBJECTIVE_REGISTRY` **byte-identical**, `OBJECTIVE_COUNT === 20` | [offline] | 2.4 |
| [ ] | Every added or changed file under `src/` or `tests/` declares its contract and phase in the first twenty lines | [harness] `AC10` | 1.7 |
| [ ] | No deployment particular in `ops/` or any fixture | [harness] `AC18` | 5.4 |
| [ ] | `classifyTurn` remains the **sole** mint; `isMintedGrant` re-checked at planner, channel and router; a forged cast grant refused at all three | [offline] | 6.9, 6.10 |
| [ ] | Every single-writer authority preserved | [offline] | 6.11 |
| [ ] | Dedup claim + enqueue in **one transaction**; returning **is** the ack; **no separate ack step introduced** | [offline] | 6.1, 6.2 |
| [ ] | Bot namespace checked **before** dedup, allowlist **before** enqueue | [offline] | 6.3 |
| [ ] | Exactly one refusal code `OPERATOR_DELIVERY_REFUSED`; a `duplicate` decision carries **no** code | [offline] | 6.4 |
| [ ] | Unbound sender throws `TELEGRAM_SEND_REFUSED`; `target === null` ⇒ `abandoned` with that code | [offline] | 6.6 |
| [ ] | `EffectiveSurfaceReport` carries `authorizesExecution` as the literal `false`, lists `unexpected` and `missing` **separately**, and computes `authorityBearing` with the **existing** `denyAuthorityTool` | [offline] | 4.7 |
| [ ] | While **D-4** is unresolved, the assessor is exercised against **synthetic observations only** | [offline] | 4.8 |
| [ ] | I1 adds **zero** tools; the deterministic leg presents **no** tool name to `runtimeAdapter` | [offline] | 4.1, 4.5 |
| [ ] | Recorded: `dailyCompanion.ts` and `channelMemory.ts` are **offline references with no live binding** | [doc] | 2.5 |
| [ ] | Recorded: the four neighbouring specs keep their authority; **none is superseded** | [doc] | 2.8 |
| [ ] | Smoke: **19 of 21**, only `AC14` / `AC15` failing | [harness] | 7.3, 7.4 |

**Owner-observation-only for I1:** a bound Slack transport · a real `finance.db` read on a confirmed host (**A14 INACCESSIBLE**) · a real native capture (**D-7**) · any paid model turn (**provider spend**) · **D-4** resolution before a live run · any **real** effective-surface observation.

**Approval:** **Stage 1 only** for every [offline] item. **Stage 2** for every [owner] item. **Commit and push are separately authorized and not granted.**

### 6.3 I2 — scheduled jobs

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I2-1** `SCHEDULER_TARGETS` unchanged at `['life','finance']` | [offline] | 24.1 |
| [ ] | **AC-I2-2** `listeningPorts` still an empty constant **with no writer** | [offline] | 24.2 |
| [ ] | **AC-I2-3** A job failure leaves `isTicking() === true` and the tick does not throw | [offline] | 24.3 |
| [ ] | **AC-I2-4** **No second timing source** exists in the tree — source-level assertion | [offline] | 6.8, 24.4 |
| [ ] | A consumer behind the existing `finance` internal endpoint only; **no target, no timer, no cron, no `listeningPorts` writer** | [offline] | 6.7 |
| [ ] | `lastRunAt` uses the **existing `kv`** table, not a new one | [offline] | 24.5 |
| [ ] | Planners are **pure and deterministic**; effects injected | [offline] | 24.6 |
| [ ] | Overlap guarded by a **claim-style lease reusing the queue's mechanism** | [offline] | 24.7 |
| [ ] | Last-run state survives a restart; **no job runs twice for one due period** | [offline] | 24.8 |
| [ ] | An out-of-range endpoint is rejected by the **existing** internal-endpoint refusals | [offline] | 24.9 |
| [ ] | **No part of O6's cadence implemented** — blocked on **D-2**, which reads `None offered` | [doc] | 24.10, 8.4 |

**Owner-observation-only:** a real-host run (**A14**, **D-4**) and any live delivery from a tick.
**Approval:** **Stage 1 only** for the offline items. **Stage 2** for a real-host run.

### 6.4 I3 — Drive discovery

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I3-1** `drive.file` only; enumerate **only** app-created and explicitly-picked files | [offline] + [harness] `AC08` | 25.1 |
| [ ] | **AC-I3-2** Every discovered item labelled **untrusted data** at the request boundary — never an instruction, never a tool request, never authority over policy or deterministic financial facts | [offline] | 25.2 |
| [ ] | An instruction-shaped payload in discovered content leaves route, branch and effect **identical** | [offline] | 25.3 |
| [ ] | **AC-I3-3** The discovery packet is **bounded** | [offline] | 25.4 |
| [ ] | A modified packet fails its own integrity check | [offline] | 25.5 |
| [ ] | Disabling the job leaves the index **inert**, requiring no data change | [offline] | 25.6 |

**Owner-observation-only:** any Drive token operation (**A15 INACCESSIBLE**) · any real-data discovery run · **anything beyond app-created or explicitly-picked files, which needs owner authorisation AND a policy amendment.**
**Approval:** **Stage 1 only** for the offline items. **Stage 2** for the rest. **Neither stage authorises a scope broadening.**

### 6.5 I4 — deterministic alerts

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I4-1** Every alert figure traces to a `DeterministicFinancialFact` | [offline] | 26.1 |
| [ ] | No alert composes a figure from a model result | [offline] | 26.2 |
| [ ] | **AC-I4-2** Deduplication holds **across a restart** | [offline] | 26.3 |
| [ ] | Alerts beyond the per-window cap are **withheld** | [offline] | 26.4 |
| [ ] | While the model channel is shut, the deterministic alert route **still answers** | [offline] | 26.5 |

**Owner-observation-only:** live delivery of any alert to the owner's channel.
**Approval:** **Stage 1 only** for the offline items. **Stage 2** for live delivery.

### 6.6 I5 — cross-agent handoffs

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I5-1** No signal payload key and no result key matches `AUTHORITY_KEY` | [offline] | 27.1 |
| [ ] | **AC-I5-2** `nizam` and `pfos` share **no** OpenRouter key, weekly cap or store entry | [offline] | 27.2 |
| [ ] | A published signal is **bounded state and carries no grant** | [offline] | 27.3 |
| [ ] | A cross-profile signal is **refused, not downgraded** | [offline] | 27.4 |
| [ ] | The signal bus writes to `signals.db` **only** | [offline] | 27.5 |
| [ ] | When publishing stops, readers see no new signals and no data change is required | [offline] | 27.6 |
| [ ] | I5 adds **zero** tools — both signal-bus names are already among the 10 | [offline] | 4.2 |

**Owner-observation-only:** cross-agent **live** operation (**A14 INACCESSIBLE**).
**Approval:** **Stage 1 only** for the offline items. **Stage 2** for live operation.

### 6.7 I6 — continuity

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I6-1** `DRIVE_MIRRORED` **implies a verified read-back** | [offline] | 28.1 |
| [ ] | A failed mirror **never** reports `DRIVE_MIRRORED` | [offline] | 28.2 |
| [ ] | **AC-I6-2** Every continuity payload written to Drive is **encrypted by the Payload_Envelope** (I0 landed first) | [offline] | 28.3 |
| [ ] | An altered mirrored file **fails read-back** | [offline] | 28.4 |
| [ ] | A restart with a record in `STAGED_RETRY` **resumes** that record | [offline] | 28.5 |
| [ ] | The continuity migration is **versioned** and **moves no monetary field** | [offline] | 28.6, 3.10 |
| [ ] | `mirrorApproved` false ⇒ **no** mirror call attempted, and `LOCAL_WRITTEN` still reached | [offline] | 28.7 |
| [ ] | A **throwing** `permitted` consent guard is treated as a **denial** | [offline] | 28.8 |

**Owner-observation-only:** any Drive write of **real** data · **G5** · **G8**.
**Approval:** **Stage 1 only** on synthetic data. **Stage 2** for real data, G5, G8.

### 6.8 I7 — recovery

| | Observable AC | Vehicle | Req |
|---|---|---|---|
| [ ] | **AC-I7-1** An archive of **synthetic** data restored to a **scratch location** equals the source | [offline] | 29.1 |
| [ ] | **AC-I7-2** A wrong-key restore **refuses** | [offline] | 29.2 |
| [ ] | A mutated archive **refuses** | [offline] | 29.3 |
| [ ] | An interrupted restore **resumes or refuses cleanly**, never presenting a partial dataset as complete | [offline] | 29.4 |
| [ ] | The restore is **independently observed**; a rehearsal never exercised is **not** recorded as a backup | [owner] | 29.5 |
| [ ] | **AC-I7-3** While **G8** is unsatisfied, **no archive of real data is produced** — one early archive voids the ciphertext-only guarantee **retroactively for every archive** | [owner] | 29.6 |
| [ ] | A failed rehearsal is recorded as a **finding** — recovery is exercised, not deployed | [doc] | 29.7 |

**Approval:** **Stage 1 only** for the offline round trip on synthetic data in a scratch location. **Stage 2: G8 is owner-only and a hard blocker.**

---

## 7. Closing confirmations

- [ ] **19 of 21**, only `AC14` and `AC15` failing. Not a regression. _Requirements: 7.3, 7.4_
- [ ] **No artifact, test, comment, observation or reply claims exactly-once delivery.** _Requirements: 22.13_
- [ ] All **six** reachability cases present and passing — R-1, R-2, R-3, R-3b, R-4, R-5. _Requirements: 20.1, 20.4_
- [ ] All **five** failure-injection items present — FI-1 … FI-5. _Requirements: 22.9_
- [ ] **`HERMES_TOOL_NAMES` is 10.** Zero tools added across I0–I7. _Requirements: 4.1, 4.2_
- [ ] The **54 dirty entries** are preserved as found; **no commit, no push**. _Requirements: 2.6_
- [ ] The **UPOI 20-entry registry** is untouched and byte-identical. _Requirements: 2.4_
- [ ] **No acceptance check was weakened, added, removed, renamed or reweighted.** _Requirements: 7.2_
- [ ] Both coverage gaps recorded and **not filled**: `AC12` (PFOS 01–15 and amendments unchecked) and Drive encryption (`AC08` is scope only). _Requirements: 7.7, 7.8, 7.10_
- [ ] **No owner decision was invented.** D-2 and D-6 still read `None offered`. _Requirements: 8.4, 8.5_
- [ ] **Passing tests is not live readiness.** _Requirements: 7.6_
