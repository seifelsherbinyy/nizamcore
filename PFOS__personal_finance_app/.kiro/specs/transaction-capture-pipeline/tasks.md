# Tasks: transaction-capture-pipeline

Owner: `docs/plans/nizam-transaction-capture-pipeline-plan.md` (Revision 2) §11. Phase: Phase 1 / O1.
Requirements: `./requirements.md` · Design: `./design.md`
Alignment context: `docs/plans/nizam-financial-objectives-alignment-plan.md` §3 (this increment set is
**Phase 1** of the O1–O11 roadmap; **Phase 1b** is a separate spec —
`.kiro/specs/financial-snapshot-interface/`).

## Status vocabulary

| Value | Meaning |
|---|---|
| `done` | Performed, with an evidence pointer on the task. |
| `ready` | **No open decision blocks it.** Startable once its `sequenced-after` increments are done. |
| `blocked-on-<letter>` | An **owner decision** is unanswered. Cannot start regardless of sequencing. |

`sequenced-after` is a **schedule** dependency, not a decision block. The two are kept separate
deliberately: per the current decision state, **only Increments 1 and 6 are decision-blocked** (D-C and
D-E). Every other increment is `ready`, and where it also sits behind an earlier increment that is
itself blocked, that is recorded as a schedule consequence in the increment's own row rather than
relabelled as a decision block.

**Decision state loaded (do not re-derive):** **D-A ANSWERED** (server `finance.db` canonical) ·
**D-C ANSWERED 2026-09-20 → (a) strict cutover** · **D-E ANSWERED 2026-09-20 → (b) narrowed: Contract 6 §5 I5.1–I5.6 APPROVED, all other sections stay DRAFT** · **D-G ANSWERED 2026-09-21 via D-5 → (a) WebCrypto AES-GCM + (c) single serialisation-time projection + (e) `drive-db.md` as amended holds — SCOPE-LIMITED: I0 modules buildable, increment 10 still blocked on F6+F12, no key authority (G5/G8 unmarked)** · D-B/D-D/D-I/D-J/D-K per requirements §4 · **D-H OPEN, `None offered`** ⇒
`AC14`/`AC15` fail and **19/21 is the correct baseline**.

**One documented divergence from the plan's §11 prerequisite column.** The plan lists "inc. 1" as the
prerequisite for Increment 2. Increment 2's modules are **channel-agnostic** (they take an
`ExtractionContext`/`ResolutionContext` and know nothing about CSV), so the CSV caller cutover is a
sequencing preference rather than a hard dependency. Increment 2 is therefore `ready` and
`sequenced-after: 0`, which is what keeps D-C's block confined to Increment 1 as the decision state
requires.

---

## Increments

- [x] **0. Authority first — no code.** · status `done` · sequenced-after: —
  - **Files:** `docs/plans/nizam-transaction-capture-pipeline-plan.md`, `docs/plans/nizam-financial-objectives-alignment-plan.md`, `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md`, `contracts/programs/FINANCIAL_NIZAM_OBJECTIVES.md`, `contracts/programs/financial-nizam-objectives/**`, `.kiro/steering/drive-db.md`
  - **Acceptance:** every decision either answered or explicitly open with its blast radius; **D-H, D-M, D-V, D-Q stay `None offered`** with no invented default.
  - **Evidence:**
    - D-A recorded ANSWERED in the pipeline plan §3 decision table.
    - D-L, D-N, D-O, D-P, D-S, D-T, D-U, D-W recorded ANSWERED in the alignment plan §4 decision table; D-M, D-V, D-Q left OPEN / `None offered`.
    - D-N correction written into `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md` §3.1, which also records C-1/C-2 as resolved by D-A + D-S. This is the channel the PFOS contract index names for exactly this conflict class.
    - `FINANCIAL/` tracked per **D-L(a)** as `contracts/programs/FINANCIAL_NIZAM_OBJECTIVES.md` (program record, matching the existing flat-file convention of `SEVEN_CONTRACT_RECOVERY.md`) plus `contracts/programs/financial-nizam-objectives/` holding the eleven objective documents and the governance pack.
    - `.kiro/steering/drive-db.md` amended per **D-S(a)**: Drive is the durable evidence/recovery mirror, the server tier is canonical per `tech.md` D1; `drive.file` scope and the no-keys rule preserved verbatim.
  - **Re-verified 2026-09-20 — do not revert, and do not redo.** A later task asserted that six of the artifacts above "DOES NOT EXIST". **All six were probed individually and all six are present**: `FINANCIAL_NIZAM_OBJECTIVES.md`; `financial-nizam-objectives/` (12 artifacts); `.kiro/specs/financial-snapshot-interface/` (3 files); `.kiro/specs/transaction-capture-pipeline/` (3 files); the D-N correction in `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md` §3.1 (1 match); the `AMENDED` marker in `.kiro/steering/drive-db.md` (1 match). The `ANSWERED` markers in the alignment plan were also counted: **8 present**, consistent with the nine decisions above. **The assertion was stale; acting on it would have destroyed verified work.** Status stays `done`.
  - **D-A and D-S independently corroborated 2026-09-20.** Drive's `BOOTSTRAP.json` — a different domain, a different engine, `llm_contribution: "none"` — assigns `vps: "runtime databases, ingestion, deterministic analytics, caches, cron, secrets"` against `drive: "organized durable knowledge, journals, ledgers, reports, indexes, manifests"`. Same split as `tech.md` D1 and the D-S(a) amendment. See `docs/plans/nizam-drive-truth-inventory.md` §3.1.
  - _Source: plan §11 increment 0; alignment plan §4 D-L/D-N/D-S; requirements §4; `nizam-drive-truth-inventory.md` §4.1._

- [x] **1. Close the live money defect — strict CSV cutover.** · status **`done`** (owner option (iii), 2026-09-22) · sequenced-after: 0
  - **Files:** `src/features/import/ImportWizard.tsx`, `src/features/import/ledgerImport.ts` (caller only)
  - **Work:** wire `parseLedgerCsvStrict` with an owner-declared money unit; surface refusals per row with column and code. **Repairs F1.**
  - **Acceptance:** a whole-amount-decimal file no longer understates by 1000×; an unsigned-magnitude export no longer posts outflows as inflows; then typecheck / lint / build / `verify:all -- --all` → **19/21, `AC14`+`AC15` only**.
  - **Owner answer superseding the earlier D-C shape — option (iii), 2026-09-22.** Both server and browser CSV surfaces call `parseLedgerCsvStrict`; the browser is explicitly labelled a non-authoritative projection in code, UI, requirements and design. Neither surface silently redirects to the other. The strict parser itself was already built and was reused rather than rebuilt.
  - **Delivered:** `parseLedgerCsvForBrowserStrict` projects only after strict money/sign/date/type/provenance validation; `importLedger` requires an explicit `moneyUnit`; `ImportWizard` requires the owner to choose decimal values or integer milliunits before either Drive Picker or local file selection; detector disagreement is visible but never overrides the declaration; row refusals show typed code and column; any row error disables commit. The legacy `parseLedgerCsv` remains for compatibility/contrast tests only and has no production import caller.
  - **F1 resolved:** a whole-amount decimal file declared `decimal` imports 10 as 10,000 milliunits rather than 10; an unsigned outflow derives a negative signed amount from direction rather than posting as an inflow. Both pass through `importLedger`, not only through the parser unit test.
  - **Machine evidence before this board update:** Phase 0 strict baseline 28/28 and repository 19/21; final typecheck exit 0; lint exit 0; focused import tests **47/47**; build 101 modules; full suite **3437/3437**; `verify:all -- --all` **19/21 with only AC14 and AC15**. AC04 floor ratcheted 3433 → 3437 for four regressions. `SCHEMA_VERSION` remains 9; no migration, Drive write, human gate, commit or push.
  - **D-Y bears on this increment's priority, and does not add a second block (2026-09-20).** CORRECTED 2026-09-20 (F-SCOPE-1): a statement corpus **does** exist and was missed by a domain-scoped search — **~30 statement PDFs at the Drive ROOT**, `CIB`→`cib` and `HSBC`→`hsbc`, live-verified, and already extracted into the **1,216-row / 12-month** master ledger. The SMS corpus is **254 messages over one month**. So the true inventory is statements 12 months vs SMS 1 month, and **D-I's statements-first order SURVIVES**; the SMS-first reading is withdrawn. J4 makes statement reconciliation the *matcher*, which is a statement about ROLE, not about corpus availability — a matcher with nothing to match is idle. **Consequence for this increment: it is the FIRST adapter, not a displaced one** — the CSV path carries the only fully-extracted 12-month corpus NIZAM has, so the strict cutover is what turns that corpus into trustworthy intake. **Status: `ready`** (D-C ANSWERED (a), 2026-09-20). See `docs/plans/nizam-drive-truth-inventory.md` §5.3, and note that its D-Y row must be re-derived to match this correction.
  - _Source: plan §11 increment 1; plan F1, D-C; requirements §2.3; alignment plan §4 **D-Y**._

- [x] **2. Shared ingest core.** · status **`done`** (built and gate-green 2026-09-20) · sequenced-after: 0
  - **Files (new):** `src/server/ingest/normalize.ts`, `src/server/ingest/resolve.ts`, `src/server/ingest/validate.ts`, `src/server/ingest/dedupe.ts`, plus the content fingerprint lifted to a shared module · **+ tests**
  - **Work:** channel-agnostic S4–S7. **Repairs F2, F9, F11.**
  - **Acceptance:** property tests — normalization moves no money; currency never inferred from the account; dedup keys on `accountId` and the derived signed amount; the fingerprint excludes `memo`/`categoryId`.
  - **Note:** `AC07` bans a decimal money literal in fixtures unless the line names the invalidity (**F20**).
  - **BUILT 2026-09-20.** The earlier deferral is **withdrawn, and its stated reason was wrong.** It held that the refusal codes and dedup key composition could not be written until the SMS corpus was read at row level. That was over-caution: the refusal *taxonomy pattern* already existed in-repo (`dailyCapture.CAPTURE_REFUSAL_CODES`, 13 codes: a code plus a locator, never the offending value) and the *vocabulary* already existed in `ledger.types.ts` (`TRANSACTION_TYPES`, six tokens). Those are the authoritative sources for a **channel-agnostic** core; the Drive corpus is evidence about ONE channel and could not have changed them. **Increment 2's real blocker was never the Drive evidence.**
  - **Delivered:**
    - `recordIdentity.ts` — identity **LIFTED** from `seedLoad.ts` (`accountIdFor`, `transactionIdFor`, `sourceEventIdFor`, `periodKeyOf`, row hash), with the channel promoted from a module constant to a parameter as the only change, so pre-images are unchanged and ids already in the store still resolve. Also holds **both dedup keys**: `rawPayloadDigest` (layer 1, S2) and `contentFingerprint` (layer 2, S7, lifted from `dailyCapture.captureContentHash`).
    - `pipeline.types.ts` — `ExtractedRow` → `NormalizedRow` → `ResolvedRow` → `ValidatedRow`, the 13-code `INGEST_REFUSAL_CODES` union, and `IngestRefusal` carrying `permanent: true` **structurally** so no caller can justify a retry.
    - `normalize.ts` `resolve.ts` `validate.ts` `dedupe.ts` — S4–S7, pure and channel-agnostic.
    - **`seedLoad.ts` and `dailyCapture.ts` now CONSUME the shared module** rather than holding private copies; both lost their local `sha256` and `createHash` import. `dailyCapture` uses layer 1 for the reply bytes and layer 2 for the parsed record, which makes the two-layer distinction concrete in code rather than only in the design note.
  - **Observed gate, machine numbers:** typecheck clean · lint clean at zero warnings · build succeeded (100 modules) · `src/server/ingest` suite **262 passed** at the point of the two fixture failures below, then green · `verify:all -- --all` = **19 of 21, AC14 and AC15 only**, as expected under **D-H**.
  - **One real defect found by the tests, in the tests.** Two dedupe cases failed because the fixture helper overrode `normalizedPayee` *after* `validateRow` had already computed the fingerprint, leaving a stale fingerprint — so the assertions passed or failed for the wrong reason. Fixed by threading the payee through the real S4→S5→S6 path. The implementation was correct; the fixture was not. Worth recording because a post-hoc override of a hashed field is a fixture bug that looks exactly like an implementation bug.
  - **Deliberately NOT added:** any fifth idempotency mechanism. Four already exist (the DDL's unique `(channel, idempotency_key)`, `enqueueWork`'s conflict-ignoring insert, `claimDelivery` where the insert is the decision, and the content-derived ids just lifted). No migration, no `SCHEMA_VERSION` bump — `suspected_duplicate` and `pending_to_posted` were already in the DDL's `link_type` CHECK.
  - _Source: plan §11 increment 2; design §B/S4–S7 (incl. the S7 two-layer note); requirements §2.4–§2.7._

- [x] **3. Evidence + discovery.** · status **`done`** (built and gate-green 2026-09-20) · sequenced-after: 2
  - **Files (new):** `src/server/ingest/sourceRegistry.ts`, `buildFileSourceEvent`, the S1 consumer registered on the **existing `finance` tick** · **+ tests** · one `kv` checkpoint key
  - **Unmodified:** `src/server/process/scheduler.ts`
  - **Acceptance:** re-capture appends once; differing bytes reported not overwritten; `SCHEDULER_TARGETS` unchanged; `listeningPorts` still has no writer; a halted deployment discovers nothing and still writes liveness.
  - **BUILT 2026-09-20. Delivered:** `sourceRegistry.ts` (pure channel descriptors; `candidateOnly` declared as DATA per Contract 6 §5 I5.2, failing closed for an unregistered channel) · `channels/fileChannel.ts` (`buildFileSourceEvent`; forwards bytes and a digest, nothing more) · `discovery.ts` (`captureEvent` as the shared S2 path, `captureFile`, `runDiscovery`) · `discovery.test.ts`, **27 tests**. `scheduler.ts` and `sourceEventsRepository.ts` both **untouched**.
  - **Observed gate:** typecheck clean · lint clean at zero warnings · 27/27 own tests · `verify:all -- --all` = **19 of 21, AC14 and AC15 only**.
  - **FINDING F22 — there is no `kv` table, and none was added.** The increment called for "one `kv` checkpoint key". The schema has no such table (`accounts`, `source_events`, `transactions`, `transaction_links`, `obligations`, `statements`, `decisions`, `assets`, `valuations`, `fx_rates`, `spend_ledger`, `model_telemetry`, `update_dedup`, `work_queue`, `document_index`, `audit_log`) and a migration is **not authorized**. It is not needed: **`document_index` already IS the discovery pointer table** — `content_hash` UNIQUE, conflict-ignoring `indexDocument`, carries `source_event_id`, and its own header gives the reason a retired pointer is tombstoned rather than deleted. Correctness does not depend on it either, because S2's idempotency is structural, so the pointer makes discovery cheaper and never more correct. **Zero schema cost.**
  - **FINDING F23 — SQLite silently truncates `raw_payload` at a NUL byte.** Found by this increment's own tests, not predicted. `source_events.raw_payload` is `TEXT` in a STRICT table, so a payload containing `\u0000` round-trips as `''` **while the insert reports success**. Independently reproduced by the owner: **12 chars in, 6 out.**
  - **F23 is a TRADE, and the trade is now on the record (2026-09-20, Track B b1).** The current fix refuses such a payload as `PAYLOAD_NOT_STORABLE`. That **buys** the byte-identical guarantee and **sells** a different acceptance criterion this same increment required: *"capture durability and parse success are independent — an unparseable payload still survives, because the bytes are the owner's."* **A refused payload does not survive.** Refusing beats silent truncation, but it is not free, and it was previously recorded as though it were. Three options, not two:
    - **(a) Refuse — CURRENT.** Never stores bytes the owner did not send. **Cost:** loses durability for NUL-bearing payloads outright. Zero schema cost, shipped, tested.
    - **(b) Lossless encoding (base64 or hex) in the EXISTING `TEXT` column.** Preserves **every** byte AND keeps durability, with **no migration**. **Cost:** a documented indirection on the most load-bearing evidence column in the store — every reader must decode, and a reader that forgets gets plausible-looking garbage rather than an error. That cost is real and is why this is not simply strictly better than (a).
    - **(c) `BLOB` column when a migration is next authorized.** Cleanest: no indirection, no refusal, full durability. **Unavailable now** — Contract 6 §3 (I3.1–I3.5) is DRAFT, so no schema change is authorized.
    - **Assessment:** practical incidence is near zero for bank SMS and CSV, both of which are text by construction, so **(a) is fine to ship and is shipped.** (b) is the right answer if a real NUL-bearing channel ever appears before a migration window. (c) is the right end state. **Owner decides; nothing here is answered.**
  - **Design consequence worth knowing:** because the file key is `documentRef + digest`, changed bytes yield a DIFFERENT key, so a corrected file re-uploaded under the same name is a **new artifact**, not an `EVIDENCE_CONFLICT`. The conflict branch belongs to the chat channel's `date_and_sequence` strategy, where the key is content-independent. Both are tested, so the branch is not dead code.
  - **Scope note, D-Y (2026-09-20) — superseded by the correction below; the increment is now `done`.** `sourceRegistry.ts` and `buildFileSourceEvent` are channel-agnostic, so D-Y does not block them. But settle **one input-format question before building an SMS adapter on top**: the raw SMS corpus on Drive is a **Google Doc**, so its real shape may be document text rather than a message-per-row export. Build the registry against the shape that is actually confirmed; do not assume a row-per-message CSV exists. **Corroboration for keeping S1–S2 immutable:** v1.3 FINAL §5.2 independently names an `Immutable Event Inbox`, and §11.3 requires that *"all imported documents are untrusted data"* which cannot authorize an action merely because text inside them says so.
  - _Source: plan §11 increment 3; design §B/S1–S2; requirements §2.1–§2.2; alignment plan §4 **D-Y**._

- [x] **4. Wire `dailyCapture`.** · status **`done`** (built 2026-09-20) · sequenced-after: 3
  - **Files:** new consumer module + tests. `src/server/ingest/dailyCapture.ts` consumed, not modified.
  - **Work:** the prompt as a scheduled consumer; the reply as an S2 append; the parse as S3 — **as a worker branch, not a Hermes tool.** **Repairs F4.**
  - **Acceptance:** all twelve PFOS 15 §9.1 criteria including 10a; `HERMES_TOOL_NAMES` still 10; `DENIED_AUTHORITY_TOOLS` untouched; tamper test (§9.1 item 12) fails on a default currency, a keyword sign, a lenient parse, or an auto-promotion.
  - **BUILT 2026-09-20.** New: `src/server/ingest/dailyCaptureConsumer.ts` (`promptFor`, `ingestReply`) + `dailyCaptureConsumer.test.ts`, **35 tests** covering all twelve §9.1 criteria including **10a**. `dailyCapture.ts` **consumed, not modified**.
  - **Shape:** two legs in one call. **Leg 1 (S2)** appends the reply as evidence *before* anything parses it. **Leg 2 (S3)** parses deterministically over bytes that are already durable. A refused append returns `parsed: false` and attempts no parse — parsing anyway would produce candidates with no evidence row behind them.
  - **Worker branch, asserted:** `HERMES_TOOL_NAMES` still **10**; no capture symbol registered as a tool; the consumer imports neither `toolBoundary` nor `runtimeAdapter`; and `AUTHORITY_KEY` makes a monetary payload unrepresentable across the tool boundary, so a capture result could not cross it even if someone registered one.
  - **DEFECT FOUND AND FIXED — F24, the channel had TWO names.** Increment 3's registry spelled the chat channel `'chat:daily-capture'` while `dailyCapture.ts` had been writing `CAPTURE_CHANNEL = 'owner_daily_capture'` since Contract 15. Because `captureEvent` refuses an unregistered channel, **every chat reply would have been refused `CHANNEL_UNKNOWN`** — the channel could never have captured at all. Invisible until the two modules were wired together. The channel string is half of `UNIQUE (channel, idempotency_key)`, so it is an **identity, not a label**: a second spelling is a second identity space and rows under one are invisible to the other. Fixed by having `sourceRegistry` **re-export the existing constant** instead of declaring a second one, so there is exactly one declaration. A regression test asserts the registered channel is the one `dailyCapture` writes.
  - **Two scope corrections the tests forced, both recorded rather than worked around:**
    - **`approved` is expected on a candidate.** My first tamper assertion demanded the string be absent; Contract 6 §5 **I5.3** says `approved` *"is a review flag, NOT an isolation boundary"*. The field existing is correct. The assertion is now that this path leaves it **`false`** and contains no code able to set it true.
    - **"No ingest module imports Hermes" is FALSE for this codebase.** `agentReadiness.ts` has a type-only import (erased, harmless) and `driveEvidencePacket.ts` imports `validateEvidenceItem` from `hermes/knowledgeBoundary.ts` — a real runtime import, and a legitimate one for a module whose job is validating against that boundary. The assertion is now scoped to the **eleven modules on the money-origination path**, which is the set the property actually protects, and it fails if any of them is renamed away.
  - **D-D tension pinned, not resolved.** A chat capture carries `sourceType: 'manual'` and `extractionMethod: 'manual'`. I5.4 forbids a **machine-extracted** row claiming `manual`; a daily capture is owner-typed, so `manual` is defensible and `confidenceReason` says *"owner-stated in daily capture"*. But it loses the channel — exactly what **D-D** records as wanted by PFOS 15 §10.1 and deliberately not taken, being a schema change. A test pins the current honest-but-lossy state so a future `chat` value is deliberate.
  - _Source: plan §11 increment 4; requirements §1.4, §2.3; PFOS 15 §9.1; Contract 6 §5 I5.2/I5.3/I5.4/I5.5._

- [x] **5. Staging + record identity + the exclusion fence.** · status **`done`** — candidate repository, F17/F5/F19 and the preventive read-boundary rider are BUILT and gate-green · sequenced-after: 4
  - **THE F17 FENCE EXISTS, 2026-09-21.** `src/lib/db/candidateFence.test.ts`, **14 tests, all passing**, typecheck clean. Evidence pointer, not an assertion: run `npm test -- --run src/lib/db/candidateFence.test.ts`.
  - **What it replaced, and why the old guarantee was not one.** The entire prior guarantee was one test in `migrations.test.ts`: **netWorth only**, against `createEmptyDb`, so the baseline had no accounts and no transactions and all three compared values were **zero**. Zero-equals-zero passes whatever the engine does with a list it never reads — it would catch an engine summing candidates into an empty ledger, and would **not** catch one merging them into real rows. And **nothing anywhere** asserted the Drive-payload exclusion; that lived only as a comment at `sync.ts` ~line 193.
  - **Coverage now — every engine design §E enumerates, against a NON-EMPTY baseline** (2 accounts, 2 category groups, 3 categories, 4 posted transactions, so every engine returns non-zero): `netWorth` · `realNetWorth` · `computeMonth` · `safeToSpendAllHorizons` · `forecastAll` · `spendingByCategory` · `netWorthSeries` · `ageOfMoney` · `cardUtilization` · `debtServiceRatio` · `liquidityRunway` · `controlPanel` · cached `balance`/`clearedBalance`. The candidate carries an absurd magnitude so any leak moves a number that was already moving. **A guard on the guard** asserts the baseline is non-zero, so the identity tests cannot pass vacuously.
  - **The Drive-payload exclusion is now asserted, not commented.** Three tests: no candidate id, payee or `transactionCandidates` key survives the projection; the projection keeps every canonical row so exclusion is not achieved by dropping the payload; and a candidate-free db still projects cleanly.
  - **The boundary is now RESOLVED. D-G was ANSWERED 2026-09-21 via D-5 → (c) single serialisation-time projection.** The projection helper was deliberately kept **in the test** while D-G was open, because writing the production module then would have been building in an ungoverned area (`two-agent-vps.md` §5). That constraint is lifted: the production `candidateExclusion.ts` now replaces the helper, and **the three Drive-payload assertions must point at it unchanged** — condition 3 of the owner's answer requires the refactor be proven by the tests that already exist, not by tests reshaped to fit it. If an assertion has to change shape, STOP and report.
  - **F5 RESOLVED 2026-09-21 — the single serialisation-time projection is in production.** Owner decision **D-5 part 2 = (c)**. Module: `src/lib/drive/candidateExclusion.ts`. Evidence pointers, not claims — run `npm test -- --run src/lib/drive src/lib/db/candidateFence.test.ts` → **41 passed (41)**: `sync.test.ts` 13, `driveDb.test.ts` 6, `candidateFence.test.ts` 22. Full gate re-run to completion: **19 of 21, AC14 + AC15 only**, 80 entries.
    - **The exclusion is a property of the TYPE, not a step a caller performs.** `DriveBoundPayload` carries an unforgeable brand that only `projectForDrive` attaches, and `serialiseForDrive` accepts nothing else — so a new upload path cannot leak a candidate, because the alternative does not typecheck. That is (c); a caller-performed strip would have been (d).
    - **THREE serialisation sites, not two.** `driveDb.ts` has the `ensureDb` fresh-create plus `saveDb`, where **one `json` variable feeds both** the snapshot upload and the canonical media update — so the snapshot cannot diverge from the canonical file by construction. All three now call `serialiseDbForDrive`.
    - **The three pre-existing Drive assertions were NOT reshaped** (owner binding condition 3). Only the import changed; the helper moved out of the test into production. Had an assertion needed to change shape, the module would have been wrong.
    - **`sync.ts` comment fixed.** It claimed candidates were *"not synced to Drive"* while the line two below it put them in the serialised object — the comment was contradicted by the code it annotated. It now states merge semantics only and names where the property actually lives.
  - **DEFECT I INTRODUCED AND FIXED — the boundary was asymmetric (F25).** `projectForDrive` removed `transactionCandidates`, but `zNizamDb` declares it **required with no `.default()`** (`schema.ts:478`) and the only code that ever filled it is the **v5→v6** migration step (`migrations.ts:281`). A projected artifact is stamped `schemaVersion: 9`, so no migration step runs and `validateDb` threw on every read of an artifact this module had written — **2 failing tests in `driveDb.test.ts`, caught by AC04 at 3296/3298, not by the focused run.** Writing a required field out without putting it back is a bug with two halves.
    - **Fix: `rehydrateFromDrive` in the same module**, called in `loadDb` before `migrate`. `loadDb` is the single read choke point — `ensureDb`, `saveDb`'s conflict branch and `sync.pullDb` all arrive there — mirroring `serialiseDbForDrive` as the single write choke point. **No schema change, no `SCHEMA_VERSION` bump** (still `9`), no migration.
    - **Absence is injected; presence is left alone, even when malformed**, so `validateDb` still rejects a corrupt artifact. Coercing a present-but-wrong value would convert a corruption signal into silence.
    - **Rejected alternatives, recorded:** `.default([])` on the zod field — wrong blast radius, it would weaken validation for `localCache` too, silencing a real corruption signal on the device-local path to fix a Drive-path problem. Filling it in `migrate()` — no step runs at v9, so it would need a repair pass outside the version chain. Writing `transactionCandidates: []` into the projection instead of stripping the key — breaks three existing assertions, and key **absence** is the better property: it says *"staging is not a Drive concept"*, where an empty array is indistinguishable from *"this device happened to have none."* `downgradeV6toV5` already treats key-absence as legitimate (`migrations.ts:299`).
  - **INCREMENT 5 COMPLETED 2026-09-21 under NIZAM-INC5-TAIL-008 + NIZAM-FINAL-009.** `src/server/db/repositories/candidatesRepository.ts` now stages the already-modelled `pending` + `unverified` row with no migration, pins both values in a caller-unsettable type, keeps candidate/canonical collections structurally separate, preserves provenance verbatim on read-back and cannot approve. `candidatesRepository.test.ts` is **30 tests**: same candidate twice = one row; interrupted retry returns the existing row; same-id/different-content refuses `READBACK_MISMATCH` and writes no second audit; manual machine provenance rolls back; every exclusion assertion runs against a six-row non-empty baseline; ordinary transaction lists and duplicate-key reads also exclude candidates.
  - **F19 RESOLVED, including all three instances the probe found rather than only the transaction instance the prompt named.** `seedLoad` account, transaction and statement-period paths now make the conflict-ignoring INSERT the decision, then verify the read-back in the same transaction. Interleaved stale-read tests prove one winner and a loser receiving the existing row; statement unique-period collision and all same-id/different-content collisions refuse `READBACK_MISMATCH`. A same-key/different-bytes source event remains `EVIDENCE_CONFLICT` and derives nothing from the competing payload. **Rejected fixes:** (1) lock/mutex/semaphore — a fifth idempotency mechanism and caller-coordination guarantee instead of a database guarantee; (2) retry loop — converts determinism into timing and hides the race; (3) widening the preceding read transaction — only shrinks the window, which is dangerous because it stops reproducing without closing.
  - **Preventive read-boundary rider completed, explicitly not a live-hole fix.** `src/lib/drive/readBoundaryGuard.test.ts` has 8 tests and enumerates every `downloadText` caller. A synthetic database caller that parses without `rehydrateFromDrive` fails; wrong-order validation fails; the real nested `migrate(rehydrateFromDrive(raw))` path passes. `ImportWizard.tsx` remains unchanged and exempt because it hands a Picker-selected ledger CSV to `loadCsv`, never constructs `NizamDb`; the two other exemptions are test-only raw-byte/type assertions. No harness check was added; the count remains 21.
  - **Machine evidence, observed before this board update:** focused item-A typecheck exit 0 and 58/58; rider typecheck exit 0 and 49/49; final suite **3407/3407**; `verify:all -- --all` **19/21 with only AC14 and AC15**; `SCHEMA_VERSION` still 9; no DDL or migration. AC04 strictness chain is recorded at its only changed line in `scripts/verify/all.mjs`: committed 2301 → prior working 3009 → 3346 → 3374 → 3382 → 3405 → 3407. Only the floor rose; no check, order or label changed.
  - **Files (new):** `src/server/db/repositories/candidatesRepository.ts`, shared record-identity module · **+ tests**
  - **Work:** record identity **lifted from `seedLoad.ts`**, not written fresh; conflict-ignoring post-or-return; **build the F17 fence** — exclusion across every engine in design §E against a **non-empty** baseline, plus the Drive-payload assertion that does not exist. **Repairs F3 (producer half), F8, F17, F19.**
  - **Acceptance:** candidates leave every engine in design §E unchanged against a non-empty baseline; no candidate appears in any Drive-bound payload; the same promotion twice yields one row; a retried interrupted write returns the existing row without a primary-key error.
  - _Source: plan §11 increment 5; requirements §2.8–§2.9, §3.1; annex §A.2, §A.3, §A.5._

- [x] **6. Review and promotion.** · status **`done`** (Contract 6 §5 I5.1–I5.6, narrowed approval) · sequenced-after: 5
  - **Files:** `src/server/ingest/promotion.ts`, `promotion.test.ts`; single-writer transition in `transactionsRepository.ts`.
  - **Delivered 2026-09-21:** explicit owner action is the only accepted trigger; deterministic parse and validation are required; dedupe uses the existing `duplicateKey`; unresolved/deferred/confirmed duplicates refuse while an explicitly rejected suspicion is linked and resolved; original payee, cleaned payee and provenance remain separately readable; one outer `withTransaction` contains review, transition, read-back and approval audit; `pending/unverified → posted/parser` is performed by the existing transactions repository and no second writer exists. The server table has no `approved` column and migrations are forbidden, so the durable review fact is `candidate.approved` in `audit_log`; the result carries the one server-side `approved: true` projection marker.
  - **Tamper and delivery proof:** 23 tests. Non-owner triggers refuse `AUTOMATIC_PROMOTION_FORBIDDEN` and leave the candidate byte-identical. An after-update trigger mutates a consequential field; read-back raises `READBACK_MISMATCH`, the outer transaction rolls back to the exact candidate and notification is never called. Notification runs only after commit: failed send leaves posting intact; failed posting never sends. A second promotion is idempotent, adds no audit and sends no second notification. A typed refusal is permanent; owner clarification enters through an injected S2 port as `NEW_EVIDENCE` and is never retried.
  - **Automation/source guard:** exactly one non-test server module sets the `approved: true` result marker; no other production module imports `promoteCandidate`; the promotion module imports no Hermes/model surface and uses durable-intent language without a stronger delivery promise.
  - **Machine evidence, observed before this board update:** promotion-focused typecheck exit 0 and 61/61; full pre-board gate **19/21, AC14+AC15 only**, 3407/3407 suite, build 101 modules, validators 0/0, citation/retrieval tests 41/41. No migration, DDL, schema-version change, scheduler edit, transport binding, credential, Drive write, commit or push.

- [x] **7. Posting integrity.** · status `done` · sequenced-after: 6
  - **Files:** the server posting path (or `src/state/store.ts` if D-A were revisited — it is not), tests
  - **Work:** read-back before acknowledge; transfer pairs in one transaction; posting decoupled from notification. **Repairs F10, F14.**
  - **Acceptance:** `READBACK_MISMATCH` never acknowledges; no one-legged transfer; a failed send never rolls back a posting; **no artifact claims exactly-once delivery.**
  - **Delivered 2026-09-22:** read-back-before-acknowledgement and notification independence were already built by Increment 6 and reused. The only missing item was the server single-writer transfer pair. `transactionsRepository.insertTransferPair` now validates two distinct accounts, transfer type, posted state, same currency, opposite equal signed amounts and coherent inflow/outflow magnitudes; inserts both legs and the existing `transfer_pair` link inside one `withTransaction`; reuses identical retries; and raises `READBACK_MISMATCH` if only one leg resolves as new.
  - **No one-legged proof:** an injected SQLite trigger aborts the second leg; the test asserts both transaction ids remain absent and no link exists, proving rollback rather than reasoning about it. Additional tests prove equal opposite legs, idempotent retry and pre-write refusal of unequal legs.
  - **Already-built items not rebuilt:** promotion tamper test proves `READBACK_MISMATCH` never acknowledges; promotion commits before notification; failed notification leaves posting intact; failed posting never calls notification; durable-intent wording remains and no stronger delivery claim was introduced.
  - **Machine evidence before board update:** Phase 0 focused 33/33 and gate 19/21; final typecheck exit 0; focused posting tests 37/37; full suite 3441/3441; `verify:all -- --all` **19/21 with only AC14 and AC15**. AC04 floor 3437 → 3441. `SCHEMA_VERSION` remains 9; no migration, Drive write, gate action, commit or push.
  - _Source: plan §11 increment 7; requirements §3.4–§3.5; design §C.4–§C.5._

- [ ] **8. Reconciliation + statement close.** · status `ready` · sequenced-after: 7 — **partially pre-delivered: `reconcile.ts` population repair landed 2026-09-22; `statementClose.ts` NOT started**
  - **Files (new):** `src/server/ingest/statementClose.ts` + tests. ~~`src/server/ingest/reconcile.ts` consumed, not modified.~~ **AMENDED 2026-09-22 — see the repair below.** `reconcile.ts` **was** modified, ahead of this increment and under separate authority (requirement **2.12a**, owner decision **R2**), because its population was unbounded. The original line assumed `reconcile.ts` was correct to consume as-is. It was not. `statementClose.ts` still does not exist and this increment is still open.
  - **Acceptance:** zero-milliunit tolerance; three distinct verdicts, never collapsed; close only on a passing equation or an **explicit** exception acceptance; all five `statements` money columns mentioned including an explicit-null `minimum_due`.
  - **Preserve, do not "fix":** the verdict precedence and the sign-residual identity (design §B/S11).
  - **`reconcile.ts` population repair — delivered 2026-09-22 (master-plan Increment B, authorized by R1 + R2).** The defect: `ReconciliationInput` carried only a window **start**, and the store-side totals query was bounded by neither an end date, a status filter, nor the mapped-account set. A comparison was therefore drawn between a bounded per-account side and an effectively open-ended whole-table store side, so a passing verdict could be produced by two populations that were never the same population. That is a wrong-answer defect in a money comparison, not a tidiness issue.
  - **Repaired by stating the population instead of inheriting it:** `windowEndInclusive` is now **required**, not optional — an optional end defaulting to open-ended is the defect itself, so it was not offered. `CANONICAL_RECONCILIATION_STATUSES` is `['posted', 'reconciled']`, applied to both the totals query and `storeRowCount`, which was previously a whole-table count. The store side is scoped to mapped accounts only, returning an empty map rather than a silent full-table read when no account is mapped. `duplicateGroupsInWindow` is bounded at both ends. A new `ReconciliationWindow` is returned on every report, declaring both bounds, the canonical statuses, the mapped accounts and — explicitly, rather than silently unifying them — that the store side is bounded on `transaction_date` while the per-account side is bounded on `posted_date`. `rowCounts.perAccountAfterWindow` was added so rows beyond the window are visible instead of absorbed.
  - **Candidate-safe, and that is the point of the status filter.** `status='pending' AND verification_level='unverified'` rows share the `transactions` table as staging (Contract 6 **§5.7**, owner decision **R1**). Narrowing the reconciliation universe to canonical statuses is what keeps an unreviewed candidate out of a money comparison on **every read**, per I5.7.1–I5.7.5.
  - **Deliberately unchanged:** zero tolerance; the three verdicts; verdict precedence with row-count precedence ahead of the sign-residual identity; the identity itself. Identical recomputation must stay identical, and a test asserts it.
  - **Machine evidence before this board update:** focused `reconcile.test.ts` **27/27** (16 pre-existing, 11 new regressions); `typecheck` clean; `lint` clean at zero warnings; no editor diagnostics on the three changed files; `verify:all -- --all` = **19 of 21, `AC14` and `AC15` only**, with `AC04`, `AC13`, `LOOP`, `AC05`, `AC05b`, `AC06`, `AC08b` and `AC12` all observed `PASS` after the change. `AC04 --min` ratcheted **3441 → 3452** in the same change that added the tests. `SCHEMA_VERSION` remains 9; no migration, no Drive write, no gate action, no commit, no push.
  - **FINDING F25 — `liveSeedLoad.test.ts` teardown is not tolerant of a transient Windows file lock. Observed 2026-09-22, **REPAIRED the same day** (see the closing note on this bullet), NOT caused by this change.** Immediately after a passing gate, an identical standalone `node scripts/verify/testcount.mjs --min 3452` reported **3452 total, 3434 passed, 18 failed**, every failure in that one file and every one the same error: `EPERM, Permission denied` from `rmSync` on `data/store` at `liveSeedLoad.test.ts:150`. No vitest or NIZAM process was holding it — the only live `node` processes were two unrelated MCP connectors and a language server — so the handle was a residual OS-level lock on the freshly closed SQLite file. **Re-running the identical command with nothing else touching the tree gave `3452 total, 3452 passed, 0 failed, PASS`.** The suite is healthy; the teardown is flaky. The `rmSync` is deliberately there so K1/K2 measure this run rather than a leftover store, so the fix is a bounded retry that still throws if the directory cannot be emptied — **not** dropping the clean-start requirement, which would make working idempotence look like failure. **Repaired 2026-09-22 under the owner's standing authority to diagnose and repair test failures with bounded retries.** `performRun` now calls `removeStoreDirectory`, which retries the removal up to five times with a 200 ms synchronous pause and then **throws `STORE_NOT_CLEARED`** if the directory survives. The clean-start requirement is not softened — that is the whole point of the named throw, because a silently reused store would make working idempotence look like a failure. Observed after the repair: `liveSeedLoad.test.ts` **24 passed (24)**; full gate **19 of 21 with only `AC14` and `AC15`**; `AC04` still met at 3452 (the repair adds no test, so the floor did not move). **Consequence for anyone reading a red suite: if every failure is this file with an `EPERM` on `data/store`, that was this flake, and it should now surface as `STORE_NOT_CLEARED` instead.**
  - **Observation on the floor's slack, not introduced here.** `AC04 --min 3452` now equals the observed total exactly, and 18 of those tests are `describe.skipIf(!cachePresent)` — they run only where the tier-1 live cache exists. On a machine without it the suite reports 3434 and `AC04` fails at a floor nothing regressed to cause. This is a property of the existing ratchet rule (set the floor at the observed count), visible at 3441 before this change too, not a new defect. Flagged rather than "fixed", because lowering a floor is forbidden and excluding the live tests from the count is an owner's call.
  - **Not done, and not startable here:** `statementClose.ts`. This repair makes the comparison it will consume trustworthy; it does not deliver the close.
  - _Source: plan §11 increment 8; requirements §2.12 and **§2.12a**; Contract 6 **§5.7**; annex §A.6, §A.7._

- [x] **8b. Notification outbox — migration 9.** · status **`done`** (built and gate-green 2026-09-22) · owner decision **D-J**, `docs/adr/ADR-0004-production-release-decisions.md`
  - **Files:** `src/server/db/schema.ts` (`MIGRATION_009`, `notification_outbox` added to `TABLES`), `src/server/db/migrations.ts` (version 9 registered), `src/server/db/repositories/notificationOutboxRepository.ts` + tests (**18**).
  - **The defect it closes.** Commit-then-compose loses a notification silently: a process that commits a posting and dies before its send has produced a financial fact the owner is never told about, with nothing in the store recording that a message was owed. The loss had been disclosed rather than fixed. `enqueue` is designed to be called **inside the posting's own transaction**, so the intent survives exactly whatever the posting survives, and a crash leaves a recoverable `pending` row instead of nothing.
  - **The guarantee, stated honestly:** at-least-once with deduplication. **Exactly-once is never claimed** (D-J). `dedup_key` is UNIQUE, so a replay is absorbed by a constraint rather than by a read-then-write check two concurrent callers could both pass.
  - **The table holds no money and no prose.** Not an amount, a currency, a balance or a formatted figure — a test enumerates `pragma_table_info` and asserts every one of those column names is absent. `body_ref` is a reference, so the message is composed from canonical state at send time; storing the prose would freeze a figure at compose time and let a stale number be delivered after the state moved. `target_ref` is an opaque runtime reference, so no deployment particular is a literal (R24).
  - **Four states, not two.** `pending`, `sent`, `failed`, `abandoned`. `failed` is retryable and `abandoned` terminal; collapsing them would make a permanently undeliverable row indistinguishable from one waiting on a transient error, so a relay would retry forever or give up too early. Two schema `CHECK`s make an incoherent row unrepresentable: `sent` requires both `sent_at` and `receipt_ref`, and anything else requires neither. Both are proved by direct SQL that the engine refuses.
  - **The central test is the transaction property.** A failure after the enqueue and before the commit leaves **neither** the intent nor the posting, observed absent by both lookups rather than reasoned about. Also proved: a duplicated settle does not count a second attempt; an abandoned row cannot be revived; settling a row that does not exist refuses rather than creating one; and an absorbed replay writes **no** audit row, because nothing happened.
  - **One defect found, and it was in the test.** The audit assertion first used `/\d{3,}/` as a stand-in for "no amount" and failed on the cause reference `txn-synthetic-0001` — a reference that is supposed to be there. A fuzzy ban on digits cannot tell an identifier from a figure, so the detail is now pinned to its exact literal content, with the monetary property asserted separately. Recorded because a proxy assertion that fails for the right reason is luckier than one that passes for the wrong one.
  - **Machine evidence:** focused **18/18**; `migrations.test.ts` + `connection.test.ts` **2 files passed** with a ninth migration in the series; `AC19` and `AC07` pass (the repository does **not** import the money boundary, whose importer set `AC19` pins exactly); `AC04` floor **3452 → 3470** in the same change. No `SCHEMA_VERSION` change — that constant is the browser Drive document version and is unrelated to this series.
  - _Source: ADR-0004 D-J; plan §11 increment 8's notification half; Contract 06 §5.1 (an applied migration is frozen)._

- [ ] **9. Derived-update seam.** · status `ready` · sequenced-after: 7
  - **Files:** thin seam + tests
  - **Acceptance:** a posting moves every target in design §E; the ledger recompute and the cached balance agree; `forecastStartReconciles` holds; recorded decisions unchanged; `MonthBudget.activity`/`.available` untouched.
  - _Source: plan §11 increment 9; requirements §2.13; design §E._

- [ ] **10. Coherence and Drive mirroring.** · status **`blocked-on-F6+F12`** — **D-G is no longer the blocker (ANSWERED 2026-09-21 via D-5)**, but F6 (`If-Match`) and F12 (tombstones) are independent preconditions and remain open · sequenced-after: 9
  - **Files:** projection module + tests
  - **Work:** `mirrorOf` stamp + the supersede-projection test. **Repairs F7.**
  - **Acceptance:** the mirror is labelled as a mirror; candidates absent from every Drive-bound payload; a supersede projection does not double-count; `drive.file` unchanged so `AC08` keeps passing.
  - **Blocked because:** ~~the candidate-egress fix (F5) is **D-G**~~ — **D-G ANSWERED 2026-09-21 via D-5 → (c), so F5's fix is now authorized and lands in increment 5 as `candidateExclusion.ts`.** What still blocks THIS increment: **F6 (`If-Match`) and F12 (tombstones)**, both independent preconditions, both open. The owner's condition 4 is explicit that answering D-G does **not** authorize this increment's coherence-and-mirroring work.
  - _Source: plan §11 increment 10; design §F; requirements §4._

- [ ] **11. Failure injection.** · status `ready` · sequenced-after: 9
  - **Files:** tests only
  - **Cases:** crash between commit and read-back; crash between send and settle; duplicate tick; evidence conflict; store unavailable mid-post.
  - **Acceptance:** each case leaves the canonical store consistent and produces a **named exception, never a silent success**.
  - _Source: plan §11 increment 11._

---

## Board summary

| # | Increment | Status |
|---|---|---|
| 0 | Authority first | **`done`** — re-verified 2026-09-20; a later "does not exist" claim was **stale**, all six artifacts present, nothing reverted |
| 1 | Strict CSV cutover | **`done`** — owner option (iii), shared strict parser on server/browser, browser non-authoritative; 47 focused tests; gate 19/21 |
| 2 | Shared ingest core | **`done`** — built and gate-green at 19/21 on 2026-09-20 |
| 3 | Evidence + discovery | **`done`** — gate-green at 19/21 on 2026-09-20; 27 tests in `discovery.test.ts` |
| 4 | Wire `dailyCapture` | **`done`** — 35 tests, all twelve §9.1 criteria incl. 10a; found and fixed **F24** (channel had two names) |
| 5 | Staging + identity + fence | **`done`** — candidate repository + F17/F5/F19 + preventive read rider; 30 candidate tests, 8 rider tests; gate 19/21 after floor 3407 |
| 6 | Review and promotion | **`done`** — explicit-owner promotion, tamper rollback, duplicate resolution, independent notification; 23 tests; gate 19/21 |
| 7 | Posting integrity | **`done`** — read-back/notification reused; atomic server transfer pair added with rollback proof; gate 19/21 |
| 8 | Reconciliation + close | `ready` (behind 7) — **`reconcile.ts` population repair delivered 2026-09-22** under R1+R2 (bounded window, canonical statuses, mapped accounts, declared date bases); 27 reconcile tests; gate 19/21 after floor 3452. **`statementClose.ts` not started.** |
| 8b | Notification outbox — migration 9 (D-J) | **`done`** — 18 tests; at-least-once with dedup and no exactly-once claim; no money and no prose in the table; the rollback property proved rather than reasoned; floor 3452 → 3470 |
| 9 | Derived-update seam | `ready` (behind 7) |
| 10 | Coherence + mirroring | **`blocked-on-F6+F12`** — D-G ANSWERED 2026-09-21 via D-5 → (c); F6 and F12 remain independent preconditions |
| 11 | Failure injection | `ready` (behind 9) |

**Next startable work, revised 2026-09-20.** Increment 2 is **`done`**. The next startable increment is
**3 (evidence + discovery)**, `ready`, sequenced-after 2. Increments 4 and 5 follow it in order, and none
of the three is blocked by an open decision.

**Superseded 2026-09-20 (later the same day): increment 3 is now `done` and gate-green at 19/21.** The next
startable increment is **4 (wire `dailyCapture`)**, sequenced-after 3. Two findings came out of 3 and are
recorded on its entry above: **F22** — there is no `kv` table and none was added, because `document_index`
already is the discovery pointer table (zero schema cost); and **F23** — SQLite silently truncates
`raw_payload` at a NUL byte, so a NUL-bearing payload is now refused as `PAYLOAD_NOT_STORABLE` rather than
stored truncated, with a BLOB column proposed for whenever a migration is next authorized.

**The ladder no longer stops. UNBLOCKED 2026-09-20.** D-E is **ANSWERED (b) narrowed** — Contract 6 §5
(I5.1–I5.6) is APPROVED and is now the governing authority for staging and promotion, so **Gap 1 is
CLOSED** and increment 6 is `ready`. Increments 7, 8, 9 and 11 sit behind 6 on sequencing only, not on any
decision. D-C is **ANSWERED (a)**, so increment 1 is `ready` too. **As of 2026-09-21 NO increment in this pipeline is
decision-blocked.** D-G was the last one and it is **ANSWERED via D-5 → (a)+(c)+(e)**. Increment 10 is
still blocked, but on **F6 and F12** — engineering preconditions, not owner decisions. Runway now: **1, 3, 4, 5, 6, 7, 8, 9, 11 — nine increments, all `ready` or sequencing-gated, zero
owner decisions in the way.** The binding constraint has moved off the pipeline and onto **D-H** (dirty
tree ⇒ AC14/AC15 ⇒ no push ⇒ no deploy) and, for anything that ships a real figure, **F7/RG-5**.

**Decision couplings worth answering together rather than separately:**

- **D-C + D-X** — D-X(a) routes ~1,216 already-extracted statement rows in through the CSV boundary, which
  is D-C's subject. Answering one without the other leaves the statement channel half-decided.
- **D-Y is CORRECTED** — its original premise ("SMS is the only corpus") was false, and on the true
  inventory **D-I's statements-first order survives**. The earlier SMS-first recommendation is withdrawn.
  See the alignment plan §4 D-Y row.

## PROPOSAL — the `AC04` floor now trails the suite · **SUPERSEDED BY OBSERVATION 2026-09-22**

**Read the status line before the body.** The body below is the original 2026-09-20 text and its two
factual premises are both now stale: `AC04 --min` is **no longer 3009**, and `scripts/verify/all.mjs`
**has** since been edited. The observed floor history is **3009 → 3433 → 3437 (increment 1) → 3441
(increment 7) → 3452 (the `reconcile.ts` population repair, 2026-09-22)**, each raise made in the same
change that added the tests — which is the rule the proposal asked for, now in force. The body is kept
rather than deleted so the reasoning stays traceable. **The two exclusions still hold and are not
superseded: no floor is ever lowered, and `AC19`'s `PROTECTED_TEST_FLOOR` is not touched.**

**Original text, 2026-09-20 (premises now stale):**

**Raised 2026-09-20 under Track B b2. `scripts/verify/all.mjs` has NOT been edited. Owner's call.**

`AC04` reads `--min 3009`. Increments 2 and 3 added **104 tests** (77 + 27), so the suite now clears that
floor by roughly a hundred. `AC19` holds its own separate `PROTECTED_TEST_FLOOR = 2301`, which trails
further still.

**Why that is a problem rather than just slack.** A floor is a ratchet: it exists to fail when coverage
goes *down*. A floor the suite has already cleared by ~100 would not notice the deletion of an entire test
file — `discovery.test.ts` (27), `validate.test.ts` (19) and `normalize.test.ts` (19) could all be removed
and `AC04` would still pass. At that distance it has stopped being a ratchet and become a historical
marker of where the suite once was.

**Proposed:** raise `AC04 --min` to the observed count at the moment of the raise, and adopt the rule that
it is raised in the same change that adds the tests — so the floor never trails by more than one increment.

**Two things deliberately NOT proposed.** Lowering either floor, ever. And touching `AC19`'s
`PROTECTED_TEST_FLOOR` — it guards a different, narrower set and its distance from the total is expected,
not drift.

**Not actioned because** editing the harness to change its own threshold is exactly the class of act the
standing constraints forbid an agent from performing unilaterally, even in the safe direction. Raising a
floor is still rewriting a check.

---

## Standing constraints on every increment

Every new/changed `src/` or `tests/` file declares its contract and phase in the first twenty lines
(`AC10`). A decimal money literal in a fixture needs a line that names the invalidity (`AC07`, **F20**).
Tests ratchet **up only**, against **both** floors (`AC04 --min` — **3452 as of 2026-09-22**, raised in the
same change that adds the tests; and `AC19`'s 2301, which is a separate narrower floor and is not touched). The declared
harness count stays **21**; **no check is invented, weakened, or claimed satisfied without observation.**
Expected gate result while **D-H** is unanswered: **19 of 21, `AC14` and `AC15` only.**
