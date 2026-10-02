# NIZAM Transaction Capture, Processing, Posting and Derived-Update Pipeline — Plan

Status: **PLAN ONLY. No implementation authorized by this document.**
**Revision 2** (2026-09-20) — every claim revision 1 left unverified has been read from source or
researched. Companion evidence: `docs/plans/nizam-transaction-capture-pipeline-research-annex.md`.
Revision 2 corrects one over-claim (F17), demotes one "new" mechanism to "already exists" (§5.1), adds
findings F17–F21 and decisions D-J/D-K, and sharpens S11 and D-I. Changelog: §14.
Prepared against local working tree at HEAD `5652edf`, `master` 4 ahead of `origin/master`, working tree **dirty: 54 entries** (verified this session).
Author role: Kiro IDE engineer, financial ingestion and agentic workflows.
Skills activated: `nizam-investigate`, `nizam-docs-research`.

On approval, this document is promoted to `.kiro/specs/transaction-capture-pipeline/{requirements,design,tasks}.md`. It lives in `docs/plans/` until then, because a spec directory asserts a sanctioned work item and this is a proposal.

---

## §0 Scope and authority

### 0.1 What is being planned

One pipeline, twelve segments, from a movement happening in the owner's life to every derived
financial answer reflecting it:

```text
S1 source discovery → S2 immutable evidence capture → S3 deterministic extraction
   → S4 normalization → S5 account/currency resolution → S6 validation → S7 deduplication
   → S8 candidate staging → S9 review/approval → S10 canonical posting
   → S11 reconciliation → S12 derived updates
```

This is ADR-0003 AD-6's pipeline (`capture -> parser -> normalized candidate -> deterministic
validation -> dedupe -> review -> canonical ledger -> reconciliation`) with discovery, resolution,
staging and derived updates named as their own segments, because each of those four is where the
current code either has a gap or has a defect.

### 0.2 Authority order used throughout

1. **Domain steering.** `two-agent-vps.md` governs server, agent, bot, ingestion and deployment.
   `pfos-current.md` governs PFOS. `money-rules.md` and `drive-db.md` are preserved everywhere and
   are never traded for convenience.
2. **Contracts.** PFOS 01–15; repository build contracts 1–6; `contracts/programs/*`.
3. **Specs.** `.kiro/specs/<spec>/{requirements,design,tasks}.md`.
4. **Supporting docs and dated receipts.** Evidence, never authority.

Where authority conflicts, the conflict is **named and left open** in §3 with a recommendation. This
document resolves no owner decision and adopts no default where none was offered.

### 0.3 Evidence labels

| Label | Meaning |
|---|---|
| **VERIFIED** | Read or run in this session. |
| **UNVERIFIED** | Asserted somewhere, not established. |
| **STALE** | A dated receipt, not re-observed. |
| **INACCESSIBLE** | Unreachable from this session. |

Two standing cautions. A documented status is not fresh verification — a checked task box can mean
the check ran and failed. Passing tests are not live readiness: they establish composition and
refusal behaviour on synthetic fixtures and nothing about a running host, a bound transport or a real
ledger. Prior reports in `ops/` and `docs/` were treated as hypotheses and re-checked against source.

### 0.4 Ten things this plan is not

| Not | Because |
|---|---|
| An implementation | No source file is edited by this document. |
| An authorization | Writing code, editing a test, running a gate, touching a host or spending against a key each need explicit owner approval. |
| An automatic-posting policy | Deliberately excluded. §8.4 proposes it **separately**, for its own approval. |
| A transport cutover | `ingressPolicy.ts` v2 makes Slack Socket Mode the sole transport and revokes five Telegram aliases. Nothing here changes that. |
| A schema migration | No `SCHEMA_VERSION`, table, column or enum is changed without the owner decision that governs it (§3 D-D, D-E). |
| A second ledger | ADR-0003 AD-2 confirms one canonical ledger with read-only mirrors. §10 is written to honour that, not to add a third store. |
| A human-gate action | G1–G8 in `ops/DEPLOYMENT_CONTROL.md` are owner-only. Nothing here executes, tests, substitutes into or marks any of them. |
| A claim about the host or Drive | Both are **INACCESSIBLE** from this session. No host was probed; no Drive token exists here. |
| A disposition of the 54 dirty entries | Recorded as an open decision. Preserved, untouched. |
| A supersession of any spec | `hermes-governed-workflows`, `telegram-window`, `dual-channel-memory`, `seven-contract-recovery` keep their authority. This plan composes with them. |

### 0.5 Data discipline

Every example below is synthetic. No real amount, balance, account identifier, payee, hostname,
Drive identifier, channel identifier or ledger excerpt appears, per `two-agent-vps.md` §0b R24 and
`ops/DEPLOYMENT_CONTROL.md`.

---

## §1 Verified current state

### 1.1 The two tiers, and the fact that they do not meet

| # | Subject | Finding | Label |
|---|---|---|---|
| A1 | **Browser tier** | Zustand `db` in memory → Dexie mirror (`nizam_cache`, 7 stores) → Drive `nizam_db.json` + dated snapshots. `SCHEMA_VERSION = 9`, zod-validated. | VERIFIED (`src/state/store.ts`, `src/lib/db/*`, `src/lib/drive/*`) |
| A2 | **Server tier** | `finance.db` via `node:sqlite`, WAL + `synchronous=FULL`, 8 checksum-ordered append-only migrations, money asserted at every write by `moneyBoundary.ts`. | VERIFIED (`src/server/db/*`) |
| A3 | **No bridge** | Nothing in `src/lib/drive/**` knows about SQLite. Nothing in `src/server/db/**` reads or writes `nizam_db.json`. No shared ids, no sync, no conflict protocol. | VERIFIED |
| A4 | **Divergent correction semantics** | Server corrects by superseding row (`supersede()`, `supersedes_transaction_id`, `audit_version`, predecessor → `superseded`, second correction refused). Browser corrects by appending a `reversal` + `replacement` pair sharing a `correctionGroupId`. Naively merging the two double-counts. | VERIFIED (`transactionsRepository.ts`, `state/actions.ts`) |
| A5 | **Repository gate** | `npm run verify:all -- --all` declares 21 checks. `AC14` (clean tree) and `AC15` (push-ready) fail on the 54 dirty entries, so **19/21 is the correct baseline**, not a regression. | VERIFIED (declaration + `git status`) |
| A6 | **Host / Drive** | No NIZAM host alias reachable; no Drive token in an agent session. | INACCESSIBLE |

### 1.2 Input inventory — implemented vs proposed

| Input | Where | Status |
|---|---|---|
| **Manual entry** (typed in the app) | `addTransaction` / `addTransfer` / `addReconcileAdjustment` in `src/state/actions.ts`; `TransactionForm.tsx` | **IMPLEMENTED, live.** Writes canonical `transactions[]` directly. `approved: true`, `cleared: 'uncleared'`. |
| **CSV — 25-column `master_ledger`** | `parseLedgerCsv` + `dedupeRows` + `importLedger` in `src/features/import/ledgerImport.ts`; `ImportWizard.tsx` (Drive Picker or local file) | **IMPLEMENTED, live — on the lenient path.** See F1/F2. |
| **CSV — strict ingestion boundary** | `parseLedgerCsvStrict`, 14 `StrictRefusalCode`s, derived signed amount, declared money unit | **IMPLEMENTED, UNWIRED.** Only `ledgerImportStrict.test.ts` calls it. |
| **Conversational capture** ("what moved today?") | `src/server/ingest/dailyCapture.ts` — deterministic prompt, verbatim capture, positional grammar, 13 refusal codes, `captureContentHash`, `dailyCaptureIdempotencyKey` | **IMPLEMENTED, UNWIRED.** Only its own test imports it. No scheduler consumer, no ingress handler, nothing appends its `CapturedSourceEvent`. |
| **Per-account tables (15-column)** | `src/server/ingest/reconcile.ts` `readPerAccountTable` | **IMPLEMENTED** as a reconciliation comparator, not as an intake path. |
| **Seed / one-time load** | `src/server/ingest/seedLoad.ts` | **IMPLEMENTED.** The only production caller of `transactionsRepository`. |
| **Statement files (PDF/XLSX)** | `statements` table, `document_index` (`content_hash UNIQUE`), `statementsRepository` | **SCHEMA ONLY.** No parser exists. |
| **Receipts / images / OCR** | — | **ABSENT.** A repo-wide grep over `src/server/**` for receipt/photo/image/OCR returns zero matches. `readTurnText` reads a photo *caption*, never an attachment. |
| **Bank notifications (SMS / email / push)** | `TURN_INTENT_TRIGGER.parse_bank_message = 'parse'` is an intent *label* only; `ImportInfo.sourceType` names `telegram|sms|email` | **PROPOSED ONLY.** No parser module. |
| **Authorized bank APIs** | — | **OUT OF SCOPE** (`product.md` v1 non-goal; ADR-0003 AD-6 puts them last). |

### 1.3 Orchestration surface that already exists

| Mechanism | Guarantee it already provides | Path |
|---|---|---|
| `sourceEventsRepository.append` | Immutable inbox. `UNIQUE (channel, idempotency_key)`, conflict-ignoring insert, returns `{row, appended, contentHashMatches}`. Same key + different bytes is **reported, never overwritten**. `parse_state` moves `pending → parsed \| rejected \| replayed`. | `src/server/db/repositories/sourceEventsRepository.ts` |
| `transactionsRepository` | The **single writer** for monetary facts. `insert`, `get`, `listForAccount`, `findByDuplicateKey`, `supersede`, `recordLink`, `listLinks`, `resolveLink`. **No delete.** | `src/server/db/repositories/transactionsRepository.ts` |
| `transaction_links` | `suspected_duplicate \| pending_to_posted \| transfer_pair \| correction`, `confidence_bps` 0–10000, `resolution ∈ {confirmed, rejected, deferred}`, `UNIQUE (from, to, link_type)`. | `src/server/db/schema.ts` |
| `workQueueRepo` | Durable queue. `enqueueWork` = `INSERT OR IGNORE` on a unique delivery key; `claimNextWork` `queued→running` **with a state predicate**; `settleWork` `running→done\|queued\|failed` — a re-settle writes nothing and reports false. **Crash recovery already exists:** `reclaimStalledWork(ctx, stallAfterMs)` returns rows stuck in `running` to the claimable set, with the stall window injected because how long a legitimate item may run is an operational fact. `pruneSettledWork` never runs implicitly and touches only `done`/`failed`. | `src/server/telegram/workQueueRepo.ts` |
| `withTransaction` | **`BEGIN IMMEDIATE`**, plus a `WeakSet` of in-flight databases so a repository method called from inside another **joins** the open transaction rather than starting a second. This is exactly the remedy the SQLite literature prescribes for the read-to-write upgrade (annex §C.3) — already in place. | `src/server/db/repositories/support.ts` |
| `connection.ts` pragmas | `journal_mode=WAL`, `foreign_keys=ON`, `synchronous=FULL` and an injected `busy_timeout` are set **and read back**, with the store refused on mismatch — because a pragma that was set but did not take is indistinguishable from one never set. | `src/server/db/connection.ts` |
| `recordAudit` | An `audit_log` row is written **inside the same transaction as the mutation it describes**, so an audit gap is not a reachable state. `transactionsRepository` already emits `transaction.insert`, `transaction.supersede`, `transaction.insert.correction` and `transactionLink.record`. | `src/server/db/repositories/support.ts` |
| `assertMonetaryCoverage` | **Bidirectional** drift guard reading `MONETARY_COLUMNS` beside the DDL: it refuses a field the DDL does not call monetary, **and** refuses a declared monetary column the write path omits — "pass an explicit null where the column is nullable; an omitted amount is never read as zero". | `src/server/db/moneyBoundary.ts` |
| `updateDedupRepo.claimDelivery` | The insert **is** the decision. No check-then-insert, so it cannot be raced. | `src/server/telegram/updateDedupRepo.ts` |
| `scheduler.ts` | The single clock. `SCHEDULER_TARGETS = ['life','finance']` as a `const` tuple (a third target is a compile error). Tick carries **no payload**. Halt sentinel re-read **per tick**. Retry `{base 1000ms, max 15000ms, maxAttempts 3}`, abandoned for that tick only. Never crashes on a failed tick. | `src/server/process/scheduler.ts` |
| `liveness.ts` | Cross-process heartbeat + derived staleness window; the basis of every exec readiness check. | `src/server/process/liveness.ts` |
| `migrations.ts` | Ordered, append-only, **checksum-verified**, one transaction per migration; a changed checksum is a hard failure. | `src/server/db/migrations.ts` |
| `store.mutate` | The browser's only invalidation mechanism: `structuredClone` → apply → bump `meta.revision` → `set({db})`, which changes object identity and therefore misses the `WeakMap` ledger index and re-runs every view `useMemo`. | `src/state/store.ts` |
| `recomputeAccountBalances` | The only refresh of *stored* derived money (`Account.balance`, `Account.clearedBalance`). | `src/state/actions.ts` |
| Hermes tool boundary | `runtimeAdapter.AUTHORITY_KEY` makes any payload/result key matching `amount\|balance\|currency\|milliunit\|money\|price\|cost\|financial` **unrepresentable** across the tool boundary. `HERMES_TOOL_NAMES` = exactly 10. Three would-be carriers are in `DENIED_AUTHORITY_TOOLS`. | `src/server/hermes/{runtimeAdapter,toolBoundary}.ts` |
| Governed turn path | `main.ts` → `readInboundTurn` (wired; `conservativeTurnFacts` survives as an unused export). `classifyTurn` is the **sole** mint of a `ModelInvocationGrant`. The deterministic branch is a sentence table with `NO_FIGURE_PATTERN = /\d/`. | `src/server/process/{main,turnIntake}.ts`, `src/server/routing/*` |

### 1.4 Findings — defects and gaps this plan must address

Each is a claim about code read this session, not a restatement of a prior report.

| # | Finding | Consequence | Evidence |
|---|---|---|---|
| **F1** | The **lenient** CSV path is the live one. `detectMoneyFormat` *guesses* the money unit per file (a file of whole-amount decimals carries no `.` and reads as milliunits, understating by 1000×), and direction is inferred from the sign of `amount` — which on the canonical export is an **unsigned magnitude**, so every row reads as an inflow. | Outflows post as inflows; magnitudes can be off by 1000×. The strict parser that fixes both exists and is not called. | `ledgerImport.ts` `detectMoneyFormat`, `buildIngestRow` lenient branch, and the module's own F22/F23 comments |
| **F2** | The CSV `currency` column is parsed onto `LedgerRow` and then **discarded**. `importLedger` sets a new account's currency to `db.meta.currency` and each transaction's to the account's. | Contradicts the stated intent that `Transaction.currency` is "never inferred from the account" (draft C6 I1.2). A foreign purchase on a domestic card is silently mis-denominated. | `ledgerImport.ts` `ensureAccount` / the `Transaction` literal |
| **F3** | **No promotion path exists anywhere.** `transactionCandidates` has a type, a collection, a Dexie KV slot, a v5→v6 migration and a downgrade refusal — and no producer in the browser and no consumer at all. | The staging tier is inert. Every implemented intake path writes straight to canonical. | Repo-wide grep for `promote`/`promotion` outside tests returns only comments and `downgradeV6toV5`'s refusal |
| **F4** | `dailyCapture.ts` is complete and **unwired**. | The capability the owner asked for (D7: "Hermes asks and captures the latest daily transactional information") does not run. | Only importer is `dailyCapture.test.ts` |
| **F5** | `sync.ts merge3` takes `local.transactionCandidates` unconditionally and comments "device-local (not synced to Drive)" — but `saveDb` serialises the **whole** `NizamDb`, so candidates *are* written to `nizam_db.json` and into every retained snapshot. | Unreviewed candidates leave the device and are clobbered by another device's next push. Both a data-loss path and an egress the comment denies. Overlaps `hermes-governed-workflows` **D-5**; must not receive a second, competing answer. | `sync.ts` merge block vs `driveDb.ts` `saveDb` |
| **F6** | `saveDb`'s concurrency guard is read-then-write on an integer `version`, with **no `If-Match`/etag** on the media PATCH. | A remote write landing between `getFileMeta` and `updateTextFile` is overwritten silently. | `driveDb.ts` |
| **F7** | Two canonical stores, no shared identity, no sync, divergent correction semantics (A4). | ADR-0003 AD-2's "one canonical ledger + read-only mirrors" is **not realised in code**. This is the pipeline's largest open question (§3 D-A). | A3, A4 |
| **F8** | Browser ids are `newId()` = `prefix_<Date.now base36>_<module counter base36>`. Not content-addressed, not deterministic across processes. Only `duplicateKey` is stable. | Re-importing the same file into a fresh db yields different transaction ids, so no cross-tier or cross-device identity can be built on them. | `ledgerImport.ts`, `state/actions.ts` |
| **F9** | Fuzzy dedup compares the **account display name** (not `accountId`) and the **signed** `amount` — which F1 makes positive on every row — within ±3 days on a normalised payee. O(existing × batch), no index. | Weak matching, and systematically weakened further by F1. | `dedupeRows` |
| **F10** | `store.mutate` calls `void persistLocal(draft)` — fire and forget, **errors unobserved** — and the UI reflects the mutation immediately. No canonical read-back precedes the acknowledgement. | A user can be shown "saved" for a write that never reached Dexie or Drive. | `store.ts` |
| **F11** | `ImportInfo.contentHash`, `batchId`, `parserVersion`, `sourceType`, `sourceTransactionId`, `sourceAccountId`, `statementReference`, `normalizedPayee` are declared, schema-validated and **never written or read** by any browser code. | The provenance fields the pipeline needs already exist in the type and carry no data. | `transaction.types.ts`, `schema.ts` |
| **F12** | No tombstones and no per-entity `version`. `sync.ts` documents the limit: without a base, a deletion is indistinguishable from a row never held and may resurrect. | Draft C6 I3.1–I3.3 unimplemented; deletions are not safely replicable. | `sync.ts noCommonAncestorBase` |
| **F13** | The server's vocabulary (`status ∈ {pending, posted, reconciled, superseded, void}`, `verification_level ∈ {unverified, parser, reconciled, statement}`, with `transaction_type` split out) is **narrower and differently named** than Contract 02 §4's five verification levels (`observed, provisional, matched, posted, reconciled`) and its 13-item status list. The schema header claims it "deliberately mirrors contract 02 §4/§6". | A real divergence between contract and code with no amendment record. Neither side may be silently adopted. | `src/server/db/schema.ts` vs `contracts/pfos/02_*.md` §4 |
| **F14** | `importLedger` turns a `transaction_type: 'transfer'` row into a **single one-sided** transaction with `categoryId: null`; it never builds the linked pair that `addTransfer` builds and that every engine detects via `transferAccountId`. | Imported transfers are invisible to transfer-aware logic. | `ledgerImport.ts` vs `state/actions.ts` |
| **F15** | `ingressPolicy.ts` v2 names Slack Socket Mode the sole transport and refuses five Telegram aliases — but the **wired** path is entirely Telegram-shaped (secret-token header, `(bot_id, update_id)` dedup, long-poll), and **no Slack transport module exists in the tree**. | Any live conversational-capture channel is blocked on a transport decision that is not this plan's to make. | `ingressPolicy.ts` vs `main.ts`, `providerRequest.ts` |
| **F16** | `MonthBudget.categories[].activity` / `.available` are persisted, written stale by `setAssigned`, and read by nobody (`computeBudget` recomputes from transactions). | Harmless today; a trap for any new consumer. The pipeline must not start reading them. | `budget.logic.ts` |
| **F17** | **The candidate exclusion fence is one narrow test.** `src/lib/db/migrations.test.ts:343` asserts `netWorth()` is unchanged by one synthetic candidate against an **empty-db baseline** (so all three expected values are zero). There is no assertion for balances, budgets, forecasts, obligations or reports, and **none** for the Drive-bound payload. Contract 15 §4.2 calls this "the existing exclusion test" and treats it as broader than it is. | Increment 5 must **build** the fence, not inherit it. Revision 1's S8 acceptance criterion was an over-claim and is corrected below. | Annex §A.2 |
| **F18** | `audit_log` has **no** append-only trigger, unlike `decisions` (migration 004), `spend_ledger` (005) and `model_telemetry` (007), each of which raises ABORT on UPDATE and DELETE. | The trail is populated correctly; only its immutability rests on convention. New decision **D-K**. | `src/server/db/schema.ts` |
| **F19** | `seedLoad`'s `txnRepo.get(txnId)` sits **outside** any transaction and `insert` then opens its own, so the check and the write are not one atomic decision. Harmless under one loader; under two the loser gets a primary-key error rather than a clean "already present". | S10 must make the insert **conflict-ignoring and read back**, so the insert *is* the decision — the idiom `enqueueWork` and `claimDelivery` already use. | Annex §A.5 |
| **F20** | `AC07` (`money-invariant.mjs`) bans a decimal literal assigned to a money-named field **including in test fixtures**, unless the same line matches `must fail\|must be integer\|float\|invalid\|rejects?\|should throw`. | A negative fixture written as `amount: 12.34` **fails the harness**. Every S3/S6 refusal fixture must be authored on a line that names the invalidity. An authoring constraint, not a style note. | `scripts/verify/money-invariant.mjs` |
| **F21** | `node:sqlite` is documented **Stability 1.1 — Active development** for Node 24, and `package.json` pins `"node": ">=24 <25"`. | A maintenance assumption worth naming: the API may change within the major line. Containment via `sqliteBinding.ts` is already the right shape. | Annex §C.3 |

---

## §2 Authority map — what governs each segment

| Segment | Governing authority | State |
|---|---|---|
| S1 source discovery | PFOS 02 §3 (ingestion strategy); ADR-0003 **AD-6** (priority order: manual → snapshot → CSV/XLSX → statements → SMS/email → chat → APIs); **D7-C** (Workers permitted as a *stateless verbatim relay only* — no parse, no amount, no currency, no rounding) | **APPROVED** |
| S2 immutable evidence capture | PFOS 06 §3.1/§8.2 (`source_events`, verbatim `raw_payload`, prunable); PFOS 15 §3 (one row per reply, verbatim, `parse_state = pending`) | **APPROVED** |
| S3 deterministic extraction | PFOS 15 §5 (money origination boundary; strict parse or refuse, no third outcome); `money-rules.md`; ADR-0003 **AD-4** (deterministic core is the sole source of monetary truth) | **APPROVED** for the chat channel. **CSV strict path: governed by draft C6 §5 (I5.1–I5.6), UNAPPROVED.** |
| S4 normalization | PFOS 02 §4 (field set), §5.2 (merchant similarity as a dedup input) | **APPROVED** |
| S5 account / currency resolution | PFOS 15 §5.2 (`acct:` alias resolved against a caller-supplied map; unknown or ambiguous is **refused**; currency never defaulted, **not even to the account's**); §10.3 (no stored alias registry) | **APPROVED** for chat. Draft C6 I1.2 for the general rule: **UNAPPROVED**. |
| S6 validation | PFOS 02 §4; PFOS 06 money persistence boundary (`moneyBoundary.ts`) | **APPROVED** |
| S7 deduplication | PFOS 02 §5.1 (exact idempotency), §5.2 (probabilistic score; **never auto-delete a suspected duplicate — link and retain**); PFOS 15 §7.2 (fail closed: `ambiguous` until dedup has actually run) | **APPROVED** |
| S8 candidate staging | PFOS 15 §4 (`transactionCandidates` only, never canonical; structural exclusion; fixed field values at capture) | **APPROVED** |
| S9 review / approval | PFOS 02 §8 Phase C ("Review queue") and §8 Phase E ("Document and exception review"); PFOS 15 §4.3 (**promotion is the owner's and only the owner's** — no schedule, threshold, confidence, streak or "obvious case" may promote) | **APPROVED as an obligation. The mechanism is unspecified.** |
| S10 canonical posting | PFOS 02 §4 + PFOS 06 (server `transactions` table, single writer, supersede-not-edit) | **APPROVED for the server tier.** **For the browser tier, promotion into `transactions[]` is governed only by draft C6 I5.3 — UNAPPROVED.** |
| S11 reconciliation | PFOS 02 §5.3 (pending→posted matching, FX/tip/fee/settlement differences, card payment as transfer, cash withdrawal as movement, refund linkage, installments as schedule + components, close only after the balance equation passes or an exception is accepted); PFOS 06 `statements.close_state` | **APPROVED** |
| S12 derived updates | PFOS 03 (deterministic engines); repository contracts 3 (budget) and 5 (reports); PFOS Stage 1–4 engines | **APPROVED** |

### 2.1 The two authority gaps, stated plainly

**Gap 1 — browser-tier promotion has no approved contract.** PFOS 15 §8 is explicit: it authorizes
*no canonical write, no promotion, no approval, no schema migration*. PFOS 02 §8 Phase C names a
"review queue" as a phase but specifies no mechanism. The only document that specifies promotion
(draft C6 I5.3) is **DRAFT — "No implementation authorized by this document"** and is deliberately
held out of `contracts/_CONTRACT_INDEX.md`. So S9 and the browser half of S10 are **ungoverned**, and
`two-agent-vps.md` §5 forbids building an ungoverned area.

**Gap 2 — the vocabulary divergence (F13) has no amendment record.** The implemented server
vocabulary is defensible (it separates status from type, which Contract 02's list conflates) but it is
not what Contract 02 §4 says, and nothing records the decision.

**Consequence: two artifacts precede code.** Either (a) the owner approves draft Contract 6 —
which also closes D-E, giving tombstones, per-entity versions and required currency — or (b) a new
NIZAM-derived contract is authored for promotion and canonical posting, in the same form as
Contract 15. Plus a dated amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md` for F13.

**And `AC12` is narrower than it first appears** (verified, annex §A.1). `contract-ledger.mjs` parses
index rows with `^\|\s*(\d)\s*\|` — a **single digit** — and hard-requires **exactly five** rows. So:
no acceptance check covers the build-log amendment channel; promoting C6 to row 6 requires editing the
script's expected count in the same change; and a **two-digit contract (PFOS 15, Contract 06) can never
parse as a row at all**. The amendment record is therefore unverifiable by the harness by construction,
not by omission. Recorded, not filled — changing the declared check count is an owner decision.

---

## §3 Blocking owner decisions

No default is invented. Where none can be recommended without choosing for the owner, the entry reads
`None offered`.

| # | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| **D-A** [ANSWERED 2026-09-20: (a) server `finance.db` canonical] | **Which tier owns the canonical ledger for this pipeline?** | (a) Server `finance.db` is canonical; the browser becomes a read model + review UI fed from it. (b) Browser Drive-JSON stays canonical; the server stays an inbox and never posts. (c) Both, with a defined bridge. | **(a)**, on three grounds: `tech.md`/`pfos-current.md` **D1** says the server tier is the final database and Drive-JSON is the Profile-A build; ADR-0003 **AD-2** confirms one canonical ledger with read-only mirrors; and the server tier already has the single writer, the immutable inbox, the links table, checksum-verified migrations and the money boundary. **(c) is the status quo and is the defect (F7), not a design.** But (a) means the browser stops being authoritative, which is a product decision. | **Everything.** Every segment's persistence and every acceptance criterion depends on this. |
| **D-B** | Transport for conversational capture | (a) Build the Slack Socket Mode gateway that policy v2 requires. (b) Keep the wired Telegram-shaped path and amend policy v2. (c) Defer: build S1–S12 behind the existing injected ports with deterministic mocks, bind no transport. | **(c) for this plan's offline scope.** It needs no transport decision, honours `two-agent-vps.md` §2's "build behind an injected port with a deterministic mock", and leaves (a)/(b) as a Stage-2 item. | The *live* half of S1/S2 only. Not the offline build. |
| **D-C** — **ANSWERED 2026-09-20 → (a) flip to `parseLedgerCsvStrict`** | CSV strict-parser cutover | (a) Flip `ImportWizard` to `parseLedgerCsvStrict` with an owner-declared money unit. (b) Keep lenient. (c) Offer both with strict as default. | **(a).** F1 is a silent-wrong-money defect on the live path and the fix is already written and tested. It needs one UI control (declare the money unit) and it turns silent corruption into a named refusal. | S3 for the CSV channel. |
| **D-D** | Widen `ImportInfo.sourceType` to add `chat` | (a) Widen (schema change, `SCHEMA_VERSION` bump). (b) Keep using `manual`. | **(a)**, recorded as wanted by PFOS 15 §10.1 and deliberately not taken there. A chat capture labelled `manual` is defensible but loses the channel. Schema migration is owner-only. | Honest provenance on S2/S8. Not a blocker: `manual` works. |
| **D-E** — **ANSWERED 2026-09-20 → (b) narrowed: Contract 6 §5 (I5.1–I5.6) APPROVED, all other sections stay DRAFT** | Approve draft **Contract 6** | (a) Approve as row 6. (b) Approve a narrowed version (ingestion boundary + promotion only). (c) Author a separate promotion contract instead. | **(b)**, then (a) later. The multi-currency and tombstone work is large; the ingestion boundary and promotion clauses (I5.1–I5.6, I3.1–I3.3) are what this pipeline actually needs. C6 §10 also carries four of its own unanswered items (uncleared balance derive-or-store, base-currency derive-or-cache, `FxRate.asOf` widening — **already landed at v8**, and per-currency display formatting). | **Gap 1.** S9 and browser-tier S10. |
| **D-F** | Automatic posting policy | See **§8.4**, proposed separately. | **Not bundled.** Explicit owner promotion is preserved by this plan without exception. | Nothing here. It is an additive later policy. |
| **D-G** | Candidate Drive egress (F5) and Drive encryption | **ANSWERED 2026-09-21 via `hermes-governed-workflows` D-5: (a) WebCrypto AES-GCM + (c) single serialisation-time projection + (e) `drive-db.md` as amended holds.** | **Consumed, not re-decided.** The projection this pipeline needs is the option chosen. **SCOPE LIMIT:** this answers the decision only — it makes the I0 modules buildable and moves the projection helper out of `candidateFence.test.ts` into production. It does **NOT** unblock increment 10, which still has **F6 and F12** as independent preconditions, and it grants **no** key authority (G5/G8 stay owner-only and unmarked). | S8 persistence, if D-A resolves to (b) or (c). |
| **D-H** | The 54 dirty working-tree entries | Commit / push are owner acts. | **`None offered`.** Blocks `AC14`, `AC15`, any commit and any push. **21/21 is unreachable; 19/21 is the correct baseline.** Same as `hermes-governed-workflows` D-6. | Every gate claim. |
| **D-I** | Statement-file and notification parsers, **and which format to target** | (a) In scope now. (b) Deferred behind CSV + chat. Format order: OFX/QFX, CSV, PDF. | **(b) for sequencing, with the format order settled now: OFX/QFX → CSV → PDF.** Prefer OFX wherever the bank offers it, for one structural reason — an OFX transaction carries a **source-supplied unique transaction id**, which is a stronger evidence identity than a fingerprint NIZAM derives, because it is stable across re-downloads and across changes the bank makes to its own description fields. Where present it should **become** the evidence identity, with the derived fingerprint retained as a secondary check. PDF is last: easy to archive, largely unparseable. Conditional on availability — whether the owner's banks offer OFX is **unverified and unverifiable from this session**, so CSV remains the guaranteed path. Evidence: annex §C.4. | Nothing. It is the extension point. |
| **D-J** | **New.** Adopt a **transactional outbox** for owner notifications — a table written in the same transaction as the posting, drained by a relay — or keep commit-then-compose ordering? | (a) Outbox (new table ⇒ migration 009). (b) Commit first, then compose. | **(a).** It removes the lost-notification failure mode by making the intent to notify exactly as durable as the posting, and `work_queue` already proves the mechanics in this codebase — same claim/settle predicates, same bounded retry, same stall reclaim, pointed outward instead of inward. It does **not** achieve exactly-once delivery and must never be described as doing so (§5.5 is unchanged). It is a schema change, therefore owner-only. The fallback (b) is honest and acceptable for a single user who can re-read the register. Column names must avoid `TELEMETRY_FORBIDDEN_COLUMNS`; `payload` is admissible. Evidence: annex §C.1. | §5.5's durability, not its cardinality. |
| **D-K** | **New.** Add append-only triggers to `audit_log` (F18)? | (a) Add. (b) Leave as convention. | **(a)**, for consistency with the three tables that already put the rule in the engine rather than in a repository's manners. Schema change, owner-only. | Nothing. Additive hardening. |

---

## §4 The pipeline

### 4.0 How to read a segment

Each segment states: **Owner** (the module that owns it, existing or new) · **Input** → **Output**
schema · **Persistence** · **State transitions** · **Trigger** · **Depends on** · **Failure
handling** · **Acceptance**.

Two rules hold across all twelve, and they are the spine of the design:

1. **Deterministic parsers and the authorized single-writer repository control every monetary fact.**
   Hermes orchestrates — it may ask, deliver a prompt, present a candidate, explain a refusal and
   route a request. It may never compose an amount, choose a currency, infer a direction, resolve an
   account, or decide what a malformed line "probably meant". This is already mechanical:
   `runtimeAdapter.AUTHORITY_KEY` makes a monetary payload key unrepresentable across the tool
   boundary, and **that guard is not weakened** — the deterministic legs are added as **worker
   branches, not tools**, so `HERMES_TOOL_NAMES` stays at 10.
2. **Every segment either produces a typed result or a typed refusal. There is no third outcome and
   no partial.** A refusal is first-class: it names a code, the record it concerns, and nothing about
   the offending value.

The segment table assumes **D-A = (a)** (server canonical). Where the choice changes a segment
materially, the alternative is noted.

---

### S1 — Source discovery

| | |
|---|---|
| **Owner** | **NEW** `src/server/ingest/sourceRegistry.ts` — a pure registry of channel descriptors. Plus one adapter per channel under `src/server/ingest/channels/`. |
| **Input** | A tick (no payload) for pull channels; an authenticated inbound message for push channels; an owner file selection for pick channels. |
| **Output** | `DiscoveredSource { channel, idempotencyKey, rawBytes, discoveredAt, declaredMoneyUnit? }`. Bytes only — **nothing is parsed here**. |
| **Persistence** | None. S1 is stateless by construction; its only durable effect is handing bytes to S2. |
| **State transitions** | None. |
| **Trigger** | **Pull:** a consumer registered on the **existing `finance` tick** of `scheduler.ts`. **No second clock** — `SCHEDULER_TARGETS` stays a two-member `const` tuple, and a third member is a compile error. **Push:** the accept path (`acceptHandler`) after allowlist + `claimDelivery`. **Pick:** `pickLedgerFile()` (browser, `drive.file` one-time grant). |
| **Depends on** | `scheduler.ts` (unmodified), `haltGate` (sentinel honoured per tick), D-B for any live transport. |
| **Failure handling** | A channel that raises is a failed discovery for **that tick only**, bounded by the scheduler's existing `{1000ms, 15000ms, 3 attempts}` and then abandoned; the next tick starts clean. A failed channel never costs another channel its tick (the existing per-target independence). Never crashes the clock. |
| **Acceptance** | (1) Adding a channel adds a registry entry and an adapter and changes no later segment. (2) `SCHEDULER_TARGETS` is unchanged and `listeningPorts` still has no writer. (3) A halted deployment discovers nothing and still writes liveness. (4) No adapter parses an amount — asserted by a source-level test over the adapter directory. |

**Discovery is not authority.** Per ADR-0003 **D7-C**, an edge relay may forward bytes and a content
hash and nothing more. An adapter that computes, rounds, or interprets a figure is a contract
violation, not a convenience.

---

### S2 — Immutable evidence capture

| | |
|---|---|
| **Owner** | **EXISTING** `sourceEventsRepository.append`. Plus `buildCapturedSourceEvent` (chat) and a **NEW** `buildFileSourceEvent` (CSV/statement) that produce the same `SourceEventAppend` shape. |
| **Input** | `DiscoveredSource`. |
| **Output** | `{ row: SourceEventRow, appended: boolean, contentHashMatches: boolean }`. |
| **Persistence** | `source_events` (STRICT): `id`, `received_at`, `channel`, `idempotency_key`, `content_hash`, `raw_payload`, `raw_payload_pruned_at`, `parse_state`, `document_ref`, `UNIQUE (channel, idempotency_key)`. For large files, `raw_payload` holds a `document_index` reference (`content_hash UNIQUE`) rather than the bytes. |
| **State transitions** | `parse_state`: `pending` on arrival → `parsed` (S3 produced ≥1 candidate) \| `rejected` (S3 produced only refusals) \| `replayed` (re-parsed at a newer parser version). **Nothing else mutates a row.** |
| **Trigger** | S1 output. |
| **Depends on** | Store open through `openFinanceStore` (containment guard, WAL, `synchronous=FULL`). |
| **Failure handling** | **Idempotency is structural, not procedural:** `append` is a conflict-ignoring insert, so a re-send is a no-op that **cannot be raced** — no check-then-insert is added. Same key with **different bytes** returns `contentHashMatches: false`, the stored row is left exactly as it was, and the disagreement is surfaced to the owner as an exception (§7 `EVIDENCE_CONFLICT`). Silently keeping either version is a decision this layer has no standing to make. |
| **Acceptance** | (1) The same evidence captured twice appends once; the second call reports `appended: false`. (2) The same key with different bytes appends nothing and reports the disagreement. (3) `raw_payload` is byte-identical to what arrived — not trimmed, re-cased or re-wrapped. (4) Capture durability and parse success are **independent**: a reply that cannot be parsed still survives, because the bytes are the owner's and a future parser may read them. (5) A pruned payload leaves `content_hash`, keys and the parsed record intact. |

---

### S3 — Deterministic extraction

| | |
|---|---|
| **Owner** | Per channel, and **always a deterministic parser, never a model**: chat → **EXISTING** `parseDailyCaptureReply` / `parseCaptureLine`; CSV → **EXISTING** `parseLedgerCsvStrict` (subject to D-C); statements → deferred (D-I). All amounts through `fromDecimalStrict` / `fromMilliunitsStrict` in `src/lib/money/money.ts`. |
| **Input** | `SourceEventRow` + a per-channel `ExtractionContext` (known currencies, account aliases, declared money unit, capture date, source-event ref). |
| **Output** | `{ extracted: ExtractedRow[], refusals: ExtractionRefusal[] }`. Per record: a row **or** a refusal, never both, never partial. |
| **Persistence** | None directly. Writes `parse_state` on the source event, and `parser_version` onto each produced row. |
| **State transitions** | Source event `pending → parsed \| rejected`. |
| **Trigger** | S2 `appended: true`, or an explicit owner replay of a `parsed`/`rejected` row at a newer parser version (→ `replayed`). |
| **Depends on** | The money core's strict parsers. **One implementation of money** — no second digit-by-digit conversion is written beside a caller. |
| **Failure handling** | Typed refusal per record. Chat: the 13 `CAPTURE_REFUSAL_CODES`, each with `lineNumber` and, for `CAPTURE_AMOUNT_UNPARSEABLE`, the strict parser's own code carried through **unflattened**. CSV: the 14 `StrictRefusalCode`s with the column at fault. **A refusal never carries the offending value**, so it can be logged and surfaced without echoing a figure onto a model path. One fixed clarifying question per refusal (`clarifyingQuestionFor`) — a model may phrase it; the owner answers; the answer re-enters at **S2** as new evidence. |
| **Acceptance** | (1) A float money value, a grouping separator and a four-fractional-digit amount are each **refused — not rounded, not stripped, not accepted**. (2) Sign comes from `direction` and only from `direction`; a non-positive magnitude is refused. (3) A currency omission is refused and is **not** defaulted to the account's currency. (4) An over-bound reply is refused **whole** rather than truncated. (5) Every refusal code is provoked by a purpose-built input and produces **zero** rows. (6) **Tamper test:** introducing a default currency, a keyword-inferred sign, or a lenient amount parse must each make a test fail. A guard that cannot be made to fail is not a guard. |

---

### S4 — Normalization

| | |
|---|---|
| **Owner** | **NEW** `src/server/ingest/normalize.ts` — pure, no clock, no store. |
| **Input** | `ExtractedRow`. |
| **Output** | `NormalizedRow` = `ExtractedRow` + `normalizedPayee`, `merchantRaw` (verbatim), `occurredAt`, `postedAt`, `transactionType`, `direction`. |
| **Persistence** | None. |
| **State transitions** | None. |
| **Trigger** | S3 output. |
| **Depends on** | The existing `normalizePayee` rule (lowercase, non-alphanumeric → single space, **Arabic range `\u0600-\u06ff` preserved**) lifted from `ledgerImport.ts` into this shared module so there is one implementation. `TRANSACTION_TYPE_VOCABULARY` and `DIRECTION_VOCABULARY` as **declared maps**. |
| **Failure handling** | An unlisted vocabulary token is **refused** (`TRANSACTION_TYPE_UNRECOGNISED`), never absorbed into `charge` — so an upstream vocabulary change surfaces as a failure instead of a silent reclassification. The upstream token is kept verbatim (`transaction_type_raw`, `extraction_method_raw`) so nothing the map decides is irreversible. |
| **Acceptance** | (1) Both raw and normalized payee are retained (PFOS 02 §5.2 needs both; draft C6 I5.6 requires it). (2) `extractionMethod` is **never** coerced to `manual` for a machine-extracted row — `unknown` is the honest value and it exists (`INGEST_EXTRACTION_METHODS`). (3) Normalization changes no monetary value — a property test asserts byte-identical amounts in and out. |

---

### S5 — Account and currency resolution

| | |
|---|---|
| **Owner** | **NEW** `src/server/ingest/resolve.ts`. |
| **Input** | `NormalizedRow` + `ResolutionContext { accountAliases: readonly {alias, accountId}[], knownCurrencies: readonly CurrencyCode[] }` — an **array, not a map**, so a duplicated alias is representable and therefore refusable. |
| **Output** | `ResolvedRow` = `NormalizedRow` + `accountId`, `currency` (explicit). |
| **Persistence** | None. The alias set is a **caller input, not a stored registry** (PFOS 15 §10.3): the accounts collection already exists, and a stale map yields a refusal rather than a wrong account. |
| **State transitions** | None. |
| **Trigger** | S4 output. |
| **Depends on** | `accountsRepository` supplies the alias set to the caller; `CURRENCY_CODE_PATTERN`. |
| **Failure handling** | An alias matching **nothing or more than one** account is refused (`CAPTURE_ACCOUNT_UNKNOWN`). There is no "the usual account", no default account, and no inference from a previous line, a previous day or a frequent pattern. A currency outside the known set is refused (`CAPTURE_CURRENCY_UNKNOWN`) — **never substituted**. Case-folding a currency code is permitted because it cannot produce a *different* currency; defaulting one can. |
| **Acceptance** | (1) An ambiguous alias is refused, not chosen. (2) Currency is never inferred from the account. (3) **No FX at ingest, ever** (PFOS 15 §5.4): a foreign amount is stored in its own stated currency and converted only by the deterministic engine at read time. (4) This segment **repairs F2** for every channel that routes through it. |

---

### S6 — Validation

| | |
|---|---|
| **Owner** | **NEW** `src/server/ingest/validate.ts` + **EXISTING** `moneyBoundary.assertMoneyField` / `assertMonetaryCoverage`. |
| **Input** | `ResolvedRow`. |
| **Output** | `ValidatedRow` or `ValidationRefusal[]`. |
| **Persistence** | None. |
| **State transitions** | None. |
| **Trigger** | S5 output. |
| **Depends on** | `zMoney` at the browser boundary; `moneyBoundary.ts` at the server boundary; the CHECK constraints (`outflow >= 0`, `inflow >= 0`, `confidence_bps BETWEEN 0 AND 10000`) as the last line of defence. |
| **Failure handling** | Typed refusal. Checks: amount is a safe integer in milliunits; `|amount| == outflow + inflow` with exactly one of the two populated and the other zero; sign agrees with `direction`; date is a **real calendar date** (`2026-02-30` is well-shaped and is not a day) and is not in the future; account exists and is open; currency is known; the row carries a source reference (`PROVENANCE_SOURCE_ABSENT` — a row with no provenance is refused rather than stored as though it had one). |
| **Acceptance** | (1) A non-safe-integer is refused at the branded type, at this validator **and** at the persistence schema — three independent guards, so defeating one is not enough. (2) `assertMonetaryCoverage` proves every money column on the target table was asserted before any statement was prepared. (3) A future-dated row is refused; a validly back-dated one is accepted at the stated date. |

---

### S7 — Deduplication

| | |
|---|---|
| **Owner** | **NEW** `src/server/ingest/dedupe.ts`, composing **EXISTING** `captureContentHash` and `transactionsRepository.findByDuplicateKey` / `recordLink`. |
| **Input** | `ValidatedRow` + the existing candidate and canonical sets. |
| **Output** | `{ row, duplicateStatus: 'unique' \| 'duplicate' \| 'ambiguous', links: SuspectedDuplicateLink[] }`. |
| **Persistence** | `transaction_links` rows with `link_type = 'suspected_duplicate'`, `confidence_bps` (integer basis points — **no float score**), `resolution` initially `NULL`. |
| **State transitions** | `duplicateStatus`: starts `ambiguous` and becomes `unique` **only when the comparison has actually run** against both sets and found no match. `resolution`: `NULL → confirmed \| rejected \| deferred` (owner act, S9). |
| **Trigger** | S6 output. |
| **Depends on** | **Identity, §5.1.** The content hash must be computed over the financially consequential fields only. |
| **Failure handling** | **Never delete a suspected duplicate automatically** (PFOS 02 §5.2, PFOS 15 §7.2). A same-day, same-amount, same-payee repeat is genuinely possible — two coffees — so a hash collision is **surfaced for owner review**, linked, and the original source retained. Probabilistic inputs per PFOS 02 §5.2: amount, currency, account, time distance, merchant similarity, direction/type, card last-four, reference number, pending-to-posted relationship. |
| **Acceptance** | (1) Fail closed: an un-run comparison leaves `ambiguous`. (2) No path deletes a row. (3) The score is integer bps end to end. (4) Matching keys on **`accountId`, not the display name**, and on the **derived signed amount** — this **repairs F9**. (5) A pending authorization and its later posted entry are linked `pending_to_posted`, not deduplicated away. |

---

### S8 — Candidate staging

| | |
|---|---|
| **Owner** | **EXISTING** `TransactionCandidate` (browser `schema.ts`) as the shape; **NEW** `src/server/db/repositories/candidatesRepository.ts` if D-A = (a), or the existing `db.transactionCandidates` collection if D-A = (b). |
| **Input** | S7 output. |
| **Output** | Zero or more staged candidates. |
| **Persistence** | **If D-A = (a):** server `transactions` with `status = 'pending'` and `verification_level = 'unverified'`, which the schema already models — a `pending` row is a candidate. **If D-A = (b):** `db.transactionCandidates`, and **F5 must be fixed first** via D-G. |
| **State transitions** | On creation, the fixed field values are **not negotiable** (PFOS 15 §4.4): `approved = false` always; `cleared = 'uncleared'` always (a conversational report is not a bank confirmation); `categoryId = null` always (categorization is a budgeting decision, not a reading of the owner's words); `splits = null` always (a split must sum exactly; deriving legs from prose invents the arithmetic); `transferAccountId`/`transferTransactionId = null` always (capturing one leg as a transfer creates a half-transfer, worse than an uncategorized outflow); `duplicateStatus = 'ambiguous'` unless S7 proved otherwise. |
| **Trigger** | S7 output. |
| **Depends on** | The structural engine-exclusion fence. |
| **Failure handling** | A candidate that cannot be written is a failed stage for that record, retried under §5.4's bounds; the source event stays `pending` so a retry re-derives rather than half-commits. |
| **Acceptance** | (1) **Engine exclusion must be BUILT, not inherited — see F17.** The existing fence is a single test covering `netWorth` only, with one candidate against an empty-db baseline, so all three expected values are zero; nothing covers balances, budgets, forecasts, obligations, reports, or the Drive payload. This segment must extend it to **every engine named in §9, against a non-empty baseline**, and add the Drive-payload exclusion assertion that does not exist today. No engine's input is widened. (2) No second staging tier is created. (3) Every field in the table above holds its stated value on every produced candidate. (4) Provenance is complete and honest: `extractionMethod` (`manual` for owner-typed, `parser` for a machine-read artifact, **`unknown` when unknown**), `sourceType`, `confidenceScore` (a statement about *provenance*, not correctness — it authorizes no promotion), `confidenceReason` as fixed text naming the contract and the parse, `contentHash`, `duplicateKey`, `sourceFile` (the source-event ref), `parserVersion`. This **repairs F11**. |

---

### S9 — Review and approval

| | |
|---|---|
| **Owner** | **NEW** promotion module + review UI. **Blocked on Gap 1 (D-E).** |
| **Input** | Staged candidates + their suspected-duplicate links. |
| **Output** | A `PromotionRequest { candidateId, edits?, resolvedLinks, reason? }` — or a discard. |
| **Persistence** | `audit_log` entry per review act. Link `resolution` set. Discarded candidates are **superseded, not deleted**. |
| **State transitions** | Candidate → `promoted` \| `discarded` \| `deferred`. Links → `confirmed \| rejected \| deferred`. |
| **Trigger** | **An explicit owner action, and nothing else.** |
| **Depends on** | D-E. |
| **Failure handling** | A promotion that fails validation at S10 leaves the candidate exactly as it was and returns a typed refusal. Never a partial promotion. |
| **Acceptance** | (1) **No schedule, threshold, confidence score, streak, "obvious" case, or repetition of a previously promoted payee promotes anything** (PFOS 15 §4.3). (2) No batch promotion. (3) An agent may **present** and **explain** a candidate; it may not promote one. (4) `approved: true` is set **here and nowhere else**. (5) A tamper test: adding an auto-promotion path makes a test fail. |

---

### S10 — Canonical posting

| | |
|---|---|
| **Owner** | **EXISTING** `transactionsRepository` — the single writer. No second writer is introduced, in either tier. |
| **Input** | `PromotionRequest`. |
| **Output** | `PostedTransaction` **read back from the canonical store** (§5.6). |
| **Persistence** | Server `transactions`: `status`, `verification_level`, `amount` + `outflow`/`inflow`, `currency`, `duplicate_key`, `source_event_id`, `supersedes_transaction_id`, `audit_version`, `transaction_type`. |
| **State transitions** | `pending → posted` on promotion. `posted → reconciled` at S11 statement close. Correction is **`supersede`**: insert the replacement, set `supersedes_transaction_id`, bump `audit_version`, flip the predecessor to `superseded`; a second correction of a superseded row is **refused**. There is **no delete** and no in-place edit of a posted row. `verification_level` advances `unverified → parser → reconciled → statement` and **never regresses**. |
| **Trigger** | S9 only. |
| **Depends on** | One transaction per logical posting. Transfers are posted as a **linked pair** in the **same** transaction, with `transaction_links.link_type = 'transfer_pair'` — this **repairs F14** for the imported case. |
| **Failure handling** | The whole posting is one `withTransaction` (`BEGIN IMMEDIATE`) store transaction, so a crash leaves either nothing or everything (§5.3). A duplicate promotion is suppressed by the stable record identity (§5.1). **Make the insert conflict-ignoring and read back, rather than checking first — F19.** `seedLoad`'s `get`-then-`insert` leaves the check outside the transaction, so under two writers the loser gets a primary-key error instead of a clean "already present". `enqueueWork` and `claimDelivery` already show the right idiom: the insert *is* the decision, and no check-then-insert exists to race. |
| **Acceptance** | (1) Promoting the same candidate twice produces **one** row and the second call reports the existing one. (2) A reconciled row is never mutated in place. (3) A transfer never exists with one live leg. (4) Split legs sum **exactly** to the parent via `allocate()`; a superseded allocation set is retained, never destroyed. (5) The acknowledgement is emitted only after the read-back of §5.6 succeeds. (6) `assertMonetaryCoverage` passes for the write. |

**If D-A = (b)**, S10 is `store.mutate` + `recomputeAccountBalances`, and three additional repairs
become mandatory in the same increment: content-addressed ids (F8), an awaited and error-observed
`persistLocal` (F10), and an `If-Match` on the Drive PATCH (F6).

---

### S11 — Reconciliation

| | |
|---|---|
| **Owner** | **EXISTING** `src/server/ingest/reconcile.ts` (the independent-path comparator — verified to **write nothing**: three `SELECT`s, no INSERT, no transaction, and it never touches `statements`) + **NEW** `src/server/ingest/statementClose.ts`, which is the writer and the only thing that persists a report. |
| **Input** | **`ReconciliationInput`** (not `ReconcileInput`): `{ ctx, perAccount, mappings, windowStartInclusive, thirdOpinion }`. The caller resolves mappings and supplies the pre-computed third opinion; the window boundary is **stated, never inferred**. |
| **Output** | A `ReconciliationReport` whose `verdict` is the literal `'RECONCILED' \| 'RECONCILED_WITH_REPORTED_DISAGREEMENT' \| 'UNEXPLAINED_RESIDUAL'`, and whose `tolerance.milliunits` is the literal type `0`. |
| **Persistence** | `statements` (`opening_balance`, `closing_balance`, `total_outflow`, `total_inflow`, `close_state`, `UNIQUE (account_id, statement_month)`); `transaction_links` for `pending_to_posted` and `correction`. |
| **State transitions** | `close_state`: `open → balanced` (the balance equation passes) \| `open → exception_accepted` (**an explicit owner act, never implicit**). Transactions in a closed period → `reconciled`. |
| **Trigger** | A statement arriving through S1–S3, or an owner-initiated reconciliation. |
| **Depends on** | **Zero tolerance, derived not chosen:** both renderings state amounts as decimal text with at most three fractional digits, a milliunit *is* the third decimal place, so every conversion is exact and summing exact integers is exact. There is no operation that loses precision, therefore no rounding error for a tolerance to accommodate, therefore the bound is **zero milliunits**. A fourth fractional digit would be refused by the strict parser, so this derivation cannot quietly stop being true. |
| **Failure handling** | A disagreement is a **finding**. Neither side is adopted silently and the two are **never averaged**. Collapsing the three verdicts into a pass/fail is how a real finding disappears. **Two verified gotchas to preserve rather than "fix":** (1) verdict precedence puts a row-count mismatch above everything (`!allRowsEqual → UNEXPLAINED_RESIDUAL`), and `RECONCILED` requires `findings.length === 0` — so **any** finding, including an unmapped account token that has nothing to do with money, correctly downgrades a matching load to `RECONCILED_WITH_REPORTED_DISAGREEMENT`. Do not suppress findings to reach `RECONCILED`. (2) `disagreementIsSignOnly` is trusted only alongside `signResidualIdentityHolds`: flipping a sign moves a total by exactly twice the magnitude, so the residual must equal the difference of the two unmatched populations and nothing else — if it does not, something other than a sign moved. |
| **New write-path constraint** | `assertMonetaryCoverage` is **bidirectional**, so `statementClose.ts` must mention **all five** `statements` money columns — `opening_balance`, `closing_balance`, `total_outflow`, `total_inflow` and `minimum_due` — passing an **explicit null** for the one it has no value for. An omitted amount is never read as zero. |
| **Acceptance** | PFOS 02 §5.3 in full: pending authorization matched to posted entry; FX / tip / fee / settlement-date differences handled explicitly; **credit-card payment treated as a transfer, not an expense**; cash withdrawal treated as movement to a cash account with later cash spending as the expense; refund linked to the original expense where possible; installments as a liability schedule plus principal/fee components; a period closes only after the balance equation passes or an exception is **explicitly** accepted. Plus: the two comparison paths share no arithmetic, so a write-path corruption appears in one and not the other. |

---

### S12 — Derived updates

| | |
|---|---|
| **Owner** | **EXISTING** deterministic engines, unmodified. A **NEW** thin invalidation seam. |
| **Input** | A posted (or superseded) transaction. |
| **Output** | Every derived answer reflecting it. |
| **Persistence** | Only two derived values are **stored**, and both must be refreshed: `Account.balance` and `Account.clearedBalance`. Everything else recomputes from the ledger on demand. |
| **State transitions** | None of its own. |
| **Trigger** | A successful S10 or S11 write. |
| **Depends on** | **Browser:** the mutation must go through `store.mutate` so a **new `db` object** is produced — that identity change is the *only* invalidation mechanism (it misses the `WeakMap` ledger index and re-runs every view `useMemo`) — and must call `recomputeAccountBalances(draft)`. Skipping the second step leaves `liquidNow` → safe-to-spend, forecast, obligations and net worth reading the **old** cash figure while the register and rescue reports show the new one. **Server:** balances are recomputed from the ledger; no cached figure is trusted. |
| **Failure handling** | **Posting success is independent of notification delivery (§5.5).** A failed recompute is a failed *read*, never a rollback of a committed posting; it is reported and retried. |
| **Acceptance** | Posting one transaction correctly moves: the register and running balances (`transactionsForAccount`, `runningBalances`); `Account.balance`/`clearedBalance`; the linked transfer peer; `computeBudget` category activity and available (including split legs expanded per category, and the credit-card attribution pass); `obligationFundingReport`; `safeToSpendAllHorizons` (which calls `computeMonth` per horizon — up to six budget recomputes per render, a known cost); `forecastAll` (and `forecastStartReconciles` must still hold: forecast starting cash equals safe-to-spend's `liquidAvailableNow`); `spendingByCategory`/`ByGroup`; `netWorthSeries` and `netWorth`; `ageOfMoney`; `cardUtilization`, `debtServiceRatio`, `liquidityRunway`, `controlPanel`. **Not touched:** `DecisionRecord.forecast`/`confidenceBps` are frozen at decision time on purpose and `reviewDecision` enforces byte-identity of the core keys. **Not written:** `MonthBudget.activity`/`.available` (F16) — dead fields; nothing reads them and this pipeline does not start.

---

## §5 Cross-cutting mechanics

### 5.1 Stable identities

Four identities, each with one job. Two of the four already exist and are reused verbatim.

| Identity | Definition | Purpose | Status |
|---|---|---|---|
| **Evidence identity** | `(channel, idempotency_key)` | Suppresses duplicate *arrival*. The insert is the decision. | **EXISTS** (`source_events UNIQUE`) |
| **Content fingerprint** | `sha256` over the financially consequential fields **only**: date, direction, **magnitude as an integer** (no decimal form ever enters the hash input), currency, accountId, normalizedPayee — joined with `\u0000`. **Excludes `memo` and `categoryId`**, so a later edit cannot change the fingerprint. Uses the magnitude with direction as its own field, so `out 5` and `in 5` hash differently by construction. | Suppresses duplicate *content* independently of arrival order. | **EXISTS** (`captureContentHash`); must be lifted to a shared module and used by every channel |
| **Record identity** | A **caller-supplied stable id**, content-derived and therefore reproducible on a retry. | Makes posting idempotent: an interrupted post that is retried returns the already-written row instead of appending a second one. | **ALREADY EXISTS — lift and share, do not invent.** `seedLoad.ts` implements exactly this: `transactionIdFor(key) = 'txn_' + sha256(channel \0 key).slice(0,32)`, plus `accountIdFor`, `sourceEventIdFor`, `periodKeyOf` and a 26-field `rowContentHash`, none of which reads a clock or a counter. It is the direct answer to the `nizamcore` `ledger_writer.py` defect recorded in `two-agent-vps.md` §6a purpose 4, where a fresh `uuid4()` per call gives a retried write a *second valid row* that no chain verification can detect. **Do not repeat that mistake, and do not re-solve it either.** |
| **Correlation ref** | `queuedRef` end to end | Observability. It is the **only** thing about a turn that reaches an observer. | **EXISTS** |

**F8 consequence.** Browser `newId()` (clock + module counter) is unsuitable as a record identity: it
is not reproducible across processes. If D-A = (b), record identity must be derived, not minted.

### 5.2 Checkpoints

| Checkpoint | Where | Meaning |
|---|---|---|
| Schema | `schema_migrations` (checksum-verified) | Which migrations this store has applied. |
| Evidence | `source_events.parse_state` | How far this evidence got. |
| Work | `work_queue.state` (`queued \| running \| done \| failed`) | Which unit of work is in flight. |
| Job run | The **existing `kv` table** | `lastRunAt` per scheduled consumer. **No new table** — this reuses what `hermes-governed-workflows` I2 already proposes, so the two do not create competing registries. |
| Liveness | `liveness.ts` file record | The loop is turning. |
| Period | `statements.close_state` | Which period is settled. |

### 5.3 Atomic writes

- **Server.** One store transaction per logical step, through `withTransaction`, which uses
  **`BEGIN IMMEDIATE`** and joins an already-open transaction rather than nesting. A posting writes the
  transaction row, its transfer peer, its links and its audit entry **together or not at all** —
  `recordAudit` runs inside the mutation's own transaction, so an audit gap is not a reachable state.
  WAL, `foreign_keys=ON`, `synchronous=FULL` and an injected `busy_timeout` are set **and read back**
  by `connection.ts`, with the store refused on mismatch. The dedup claim and the queue row already
  land in one transaction. **This is already the arrangement the SQLite literature prescribes**
  (annex §C.3): the read-to-write upgrade under a `DEFERRED` transaction is the most common source of
  `SQLITE_BUSY` in production, and `BEGIN IMMEDIATE` is the remedy. Nothing new is needed here — but
  see F19 for the one place a read still sits outside the transaction.
- **Browser.** `writeDbToCache` is already a single Dexie `rw` transaction over all six tables plus
  `kv`. Drive is a single media PATCH preceded by a dated snapshot upload, so the snapshot is the
  rollback artifact. **F6 stands:** the version guard is read-then-write with no `If-Match`. The plan's
  position is that the browser must not be the canonical writer while F6 is open.

### 5.4 Concurrency fencing and retry limits

| Concern | Mechanism | Bound |
|---|---|---|
| Two consumers, one unit of work | `claimNextWork` updates `queued→running` **with `state = 'queued'` in the predicate** — the claim is the fence. | — |
| Double settle | `settleWork` requires `state = 'running'`; a re-settle writes nothing and reports false. | — |
| Duplicate arrival | Conflict-ignoring insert. | — |
| Read-tail-then-append race | **The lesson from `two-agent-vps.md` §6a purpose 4:** two callers deriving the same predecessor silently fork a chain. Any append-ordered write here runs inside `withTransaction`'s `BEGIN IMMEDIATE`, or uses a unique constraint that makes the fork impossible. Prefer the constraint: a conflict-ignoring insert needs no lock reasoning at all. | — |
| Retryable vs permanent failure | **A typed refusal is permanent and must never be retried.** S3–S7 refusals need a clarifying question, not a backoff — retrying one would re-ask the owner the same question on a timer. Only transient failures (store unavailable, send failed, provider unreachable) go on the bounded retries below. The distinction mirrors standard practice: retry timeouts and 5xx, never a 4xx-class validation failure (annex §C.2). | — |
| Tick delivery | Existing scheduler backoff. | base 1000ms, max 15000ms, **3 attempts**, then abandoned **for that tick only** |
| Work retry | Existing `WORK_RETRY_POLICY`. | base 5000ms, max 300000ms, **5 attempts** |
| Outbound send | Existing `SEND_RETRY_POLICY`. | base 1000ms, max 60000ms, **4 attempts** |
| Drive push | Existing: conflict → 3-way merge → **one** retry; a second conflict surfaces. | 1 retry |

No new retry policy is invented. Every bound above is already declared in `main.ts` or `scheduler.ts`.

### 5.5 Posting success is separate from notification delivery

Three guarantees, never to be merged again:

1. **Canonical write: exactly once.** Guaranteed by the stable record identity of §5.1.
2. **Settlement: idempotent.** Guaranteed by the `state = 'running'` predicate.
3. **Outbound notification: at-least-once, and that is all.** Two unavoidable cases — send accepted
   but the acknowledgement is lost; send succeeded but the process crashed before settling. The
   transport carries no idempotency key, so **exactly-once delivery is not achievable and must never
   be claimed.** A delivery-reconciliation record narrows the window; it does not close it. This is
   the same finding as `hermes-governed-workflows` **D-11** and takes its answer from there.

Operationally: **a posting is committed before any message is composed**, and a failed send never
rolls back a posting. The owner may receive a duplicate confirmation; they may never receive a
confirmation for a posting that did not happen.

**The named pattern, and the residual gap in the ordering above.** Committing first and composing
second is correct about *ordering* and still loses the notification if the process dies between the
two: the posting is durable, the intent to tell the owner is not. The established remedy is the
**transactional outbox** — write the notification intent into a table **inside the same transaction as
the posting**, so one COMMIT lands both or neither, and let a separate relay drain it (annex §C.1). This
codebase already contains the inbound half of that shape: `work_queue` is a durable queue with a
claim predicate, a settle predicate, bounded retry, a stall reclaim and an explicit prune. An outbox is
the same mechanics pointed outward, and `withTransaction` composes it with the posting for free.

It buys **durability of the intent**, not exactly-once delivery — the relay still delivers
at-least-once and guarantee 3 above is unchanged. It costs a new table, hence a migration, hence an
owner decision: **D-J**. Until D-J is answered, commit-then-compose stands, with the loss disclosed.

### 5.6 Canonical read-back before acknowledging

**A saved transaction is acknowledged only after it has been read back out of the canonical store and
compared field-by-field on the financially consequential fields.** Concretely:

1. Write inside the store transaction.
2. Commit.
3. `get(recordId)` from the canonical store.
4. Compare `amount`, `currency`, `accountId`, `date`, `direction`, `status`, `duplicateKey` against
   what was intended.
5. Only then compose the acknowledgement.

A mismatch or an absent read-back is an **exception**, never a silent success. In the browser tier
this means `persistLocal` must be **awaited and its errors observed**, and the acknowledgement must
follow the Dexie read-back — repairing **F10**.

---

## §6 Preserving evidence, provenance, versions, confidence and refusals

| Preserved | Where | Rule |
|---|---|---|
| **Original evidence** | `source_events.raw_payload`, or `document_index` for large artifacts | Verbatim bytes. Not normalized, trimmed, re-cased or re-wrapped. Prunable on its own schedule; the parsed record and its keys stay forever. |
| **Provenance** | `importInfo` / `source_event_id` | Every canonical row traces to the evidence it came from. A row with no source reference is **refused**, not stored as though it had one. |
| **Parser version** | `parserVersion` (per row), `CAPTURE_GRAMMAR_VERSION` | So a re-parse at a newer version is **detectable rather than silent**, and a `replayed` source event is distinguishable from a first parse. |
| **Confidence** | `confidence_bps` (integer basis points) and `confidence_band` (ordinal) — **as two separate fields, neither derived from the other** | A band is not a score. Converting one into the other invents precision that was never measured. Confidence is a statement about **provenance**, not correctness, and it **authorizes no promotion**. |
| **Refusal reasons** | Typed refusal codes with the record and column at fault | **Never the offending value**, so a refusal can be logged, surfaced and shown to a model-phrased question without echoing a figure. |
| **Superseded state** | `supersedes_transaction_id` + `audit_version`; `supersededAllocations`; `meta.conflicts` | Append-only. A duplicate already committed is superseded, never removed. |
| **Vocabulary rawness** | `transaction_type_raw`, `extraction_method_raw` | The upstream token is kept verbatim, so nothing a declared map decides is irreversible. |

---

## §7 Exception handling — ambiguity never becomes a ledger write

**The rule.** An ambiguous amount, date, sign, currency, account, transfer, refund or split enters
explicit exception handling. It is never guessed into a ledger write, and it is never partially
accepted.

| Exception class | Trigger | Disposition |
|---|---|---|
| `AMOUNT_AMBIGUOUS` | Undeclared money unit; grouping separator; a fourth fractional digit; a magnitude that disagrees with the declared one | Refuse the record. Clarifying question. **Never round, never strip, never accept.** |
| `DATE_AMBIGUOUS` | Unparseable, non-calendar (`2026-02-30`), or future-dated | Refuse. Back-dating is the owner's own `@YYYY-MM-DD` mechanism and nothing else. |
| `SIGN_AMBIGUOUS` | Direction absent or contradicting which of outflow/inflow is populated | Refuse. A wrong sign is a **double-magnitude** error. Direction is never inferred from an amount's sign. |
| `CURRENCY_AMBIGUOUS` | Missing or outside the known set | Refuse. **Never default, including not to the account's own currency.** |
| `ACCOUNT_AMBIGUOUS` | Alias matches nothing, or matches more than one | Refuse. No default account, no "the usual". |
| `TRANSFER_AMBIGUOUS` | One side seen with no identifiable peer | Stage as a **one-sided candidate flagged for review**, never as a half-transfer and never auto-paired. Pairing is an owner act producing both legs in one transaction. |
| `REFUND_AMBIGUOUS` | An inflow that may reverse a prior outflow | Stage; record a candidate `correction` link with a bps score; **never net against the original automatically** (PFOS 02 §5.3 says "where possible"). |
| `SPLIT_AMBIGUOUS` | Legs supplied that do not sum exactly to the parent | Refuse the allocation set whole. `allocate()` guarantees exactness; a tolerance here is how drift starts. |
| `DUPLICATE_AMBIGUOUS` | Fingerprint or fuzzy match against an existing row | Stage, link `suspected_duplicate`, leave `resolution` NULL. **Never auto-discard** — two coffees. |
| `EVIDENCE_CONFLICT` | Same idempotency key, different bytes | Store nothing new, keep the existing row exactly, surface the disagreement. |
| `READBACK_MISMATCH` | §5.6 comparison fails | Do **not** acknowledge. Raise as an integrity exception. |
| `VOCABULARY_UNKNOWN` | A type or extraction token with no declared translation | Refuse. A vocabulary change upstream must surface, not silently reclassify. |

Every class produces: zero canonical rows, an intact source event, a typed code, and exactly one
clarifying question whose text is **fixed in code**. A model may phrase a question; the owner answers;
the answer re-enters at **S2** as new evidence. A model never disambiguates a figure.

---

## §8 Automation boundary

### 8.1 Automated where the contracts already permit it

| Automated | Authority |
|---|---|
| **Discovery** — polling registered channels on the existing `finance` tick | PFOS 02 §3; scheduler already exists, no second clock |
| **Capture** — appending evidence to the immutable inbox | PFOS 15 §3.2 (structural idempotency) |
| **Parsing** — deterministic extraction, normalization, resolution, validation | PFOS 15 §5; ADR-0003 AD-4 |
| **Staging** — writing candidates | PFOS 15 §4 |
| **Routing** — presenting candidates, asking clarifying questions, delivering the daily prompt | PFOS 14 §5 |
| **Dedup analysis and link recording** | PFOS 02 §5.2 (analysis is automated; **disposition is not**) |
| **Reconciliation checks** — the two independent comparison paths, the balance equation, disagreement reporting | PFOS 02 §5.3; `reconcile.ts` exists |
| **Derived recompute** after a committed posting | PFOS 03 |

### 8.2 Never automated

Promotion. Approval (`approved: true`). Statement-close exception acceptance. Duplicate-link
disposition. Category assignment at capture. Transfer pairing. Refund netting. Any FX at ingest. Any
schema migration. Any credential, host or transport act.

### 8.3 Hermes's role, stated as a boundary

Hermes **orchestrates**: it asks, delivers deterministic prompt text, presents candidates, explains
refusals, and routes a request to a deterministic branch. It **never** holds monetary authority. The
enforcement is structural and stays structural:

- `runtimeAdapter.AUTHORITY_KEY` makes a monetary payload/result key unrepresentable across the tool
  boundary. **The guard is not weakened** — no denylist entry removed, no regex relaxed, no exception
  carved.
- Therefore the deterministic legs are **worker branches, not Hermes tools**. `HERMES_TOOL_NAMES`
  stays at **10**. This is the same structural rule `hermes-governed-workflows` I1 adopted, reused
  rather than re-decided.
- `classifyTurn` remains the sole mint of a `ModelInvocationGrant`, and the system framing already
  forbids the model to state, compute, estimate, round or repeat any monetary amount.

### 8.4 Automatic-posting policy — proposed separately, for its own approval

**Not part of this plan and not bundled with its approval.** Recorded here so it is a visible option
rather than an inferred permission.

A later policy *could* permit automatic posting for a narrowly defined class, and if it does, it
should require **all** of: two independent evidence sources agreeing byte-for-byte on the financially
consequential fields; `duplicateStatus = 'unique'` from a comparison that actually ran; an exact
merchant and account match against a rule the owner explicitly created; an amount at or under an
owner-set ceiling; a reversible window during which the posting can be withdrawn by one owner action;
and a per-period cap on how many rows may post this way. It should be a separate contract, and
**PFOS 15 §4.3's list of forbidden triggers — schedule, threshold, confidence score, streak, "obvious"
case, repetition of a previously promoted payee — would each still be forbidden as the *sole* basis.**

Until such a contract exists and is approved, **explicit owner promotion is preserved without
exception.**

---

## §9 Mapping an approved posting into the rest of the system

One canonical ledger, read-only mirrors, no competing ledger (ADR-0003 AD-2).

| Target | How it is updated | Guard |
|---|---|---|
| **Transactional store** | The single writer inserts; supersede-not-edit; no delete | `assertMonetaryCoverage` before any statement is prepared |
| **Linked transfers** | Both legs in one transaction + `transaction_links.transfer_pair` | A group with one live leg, or with three legs, is a defect and a test |
| **Balances** | `Account.balance` / `clearedBalance` recomputed from the ledger (`recomputeAccountBalances` in the browser) | Two sources for one figure is the coherence risk: `rescue.ts` and the register use the ledger recompute while `liquidNow` uses the cached field. Both must agree after every posting — asserted by a test |
| **Budgets** | `computeBudget` / `computeMonth` recompute from transactions; split legs expand per category | Transfers excluded via `transferAccountId`; correction rows deliberately **keep** `transferAccountId` so a reversal is not counted as spending |
| **Obligations** | `obligationFundingReport`, `confidentInflowsBy`, `pendingOutflowsBy` recompute at the injected `asOf` | Reads cached `clearedBalance` via `liquidNow` — so §5.6 and the balance recompute must precede it |
| **Safe-to-spend** | `safeToSpendAllHorizons` | Calls `computeMonth` per horizon; known cost, not a defect |
| **Forecast** | `forecastAll` | `forecastStartReconciles` must still hold: forecast starting cash equals safe-to-spend's `liquidAvailableNow` |
| **Reports** | `spendingByCategory/ByGroup`, `netWorthSeries`, `ageOfMoney`, `cardUtilization`, `debtServiceRatio`, `liquidityRunway`, `controlPanel` | Pure recompute; nothing cached |
| **Net worth** | `netWorth`, `realNetWorth` | Reads balances + assets + obligations + fxRates + macro |
| **Decisions** | **Not recomputed.** `forecast`/`confidenceBps` are frozen at decision time and `reviewDecision` enforces byte-identity of the core keys | A posting must not mutate a recorded decision |
| **Audit history** | `audit_log`, `supersedes_transaction_id`, `audit_version`, `supersededAllocations`, `meta.conflicts` | Append-only everywhere |

---

## §10 Browser / server coherence and Drive mirroring

**The problem, restated.** Four stores are in play (browser IndexedDB, Drive `nizam_db.json` +
snapshots, server `finance.db`, and the nizamcore-side life store, plus `signals.db` in design), two
of them model the same ledger, and **nothing reconciles them** (F7). Divergent correction semantics
(A4) mean a naive merge double-counts.

**The proposed resolution, contingent on D-A = (a):**

1. **One canonical writer.** Server `finance.db`, via `transactionsRepository`. The browser stops
   posting and becomes a **review and presentation surface**.
2. **One direction of flow.** Server → browser. The browser never writes a transaction back.
3. **The mirror is derived, not authoritative.** `nizam_db.json` becomes a **projection** of the
   canonical ledger, carrying a `mirrorOf { storeRef, schemaVersion, projectedAt, sourceAuditVersion }`
   stamp so a reader can tell a mirror from a source. Drive stays `drive.file` only, holds **data
   only, never keys**, keeps atomic writes, dated snapshots and retention, and `meta.conflicts`
   remains the audit channel.
4. **Candidates never leave the device** until D-G's single serialisation-time projection lands
   (F5). Until then, the mirror must not be enabled for real data.
5. **Identity is shared** via the content fingerprint and the record identity of §5.1 — not via
   `newId()` (F8).
6. **Correction semantics are unified** at the mirror boundary: the canonical supersede chain
   projects into browser-shaped rows in exactly one declared way, and a test asserts the projection
   of a supersede does **not** double-count against a reversal+replacement reading.

**Interim posture, and it matters.** Until D-A is answered, the browser Drive-JSON tier remains the
only live ledger and the server tier remains an inbox with a seed loader. Nothing in this plan should
be built that *assumes* the bridge exists, and nothing should be built that makes the divergence
worse. The offline work in §11 increments 1–4 is valid under either answer.

**F6 and F12 are preconditions of trusting the mirror**: without `If-Match` the Drive write can
overwrite a concurrent one, and without tombstones a deletion can resurrect.

---

## §11 Increment sequence

Every increment is **blocked pending explicit owner approval of this plan**. That includes local and
offline code and test changes. Approval of the plan is not authorization for live operation,
deployment, credentials, host mutation, provider spend, or **G1–G8** — each of those remains separate
and is never implied.

| # | Increment | Prerequisite | Files (new / changed) | Gate |
|---|---|---|---|---|
| **0** | **Authority first.** Answer D-A, D-C, D-E. Author the promotion contract or approve narrowed C6. Author the dated amendment section in `contracts/pfos/_PFOS_BUILD_LOG.md` for F13. Record D-B, D-D, D-G, D-H, D-I, **D-J, D-K** as open with what each blocks. | none | `contracts/**`, `docs/plans/**` | No code. Every decision either answered or explicitly open with its blast radius. **D-H stays `None offered`.** |
| **1** | **Close the live money defect.** Wire `parseLedgerCsvStrict` into `ImportWizard` with an owner-declared money unit; surface refusals per row with column and code. **Repairs F1.** | D-C | `ImportWizard.tsx`, `ledgerImport.ts` (caller only) | Focused tests; a whole-amount-decimal file no longer understates by 1000×; an unsigned-magnitude export no longer posts outflows as inflows; then typecheck / lint / build / `verify:all -- --all` → **19/21, AC14+AC15 only.** |
| **2** | **Shared ingest core.** `normalize.ts`, `resolve.ts`, `validate.ts`, `dedupe.ts`, plus the content fingerprint lifted to a shared module. Pure, channel-agnostic. **Repairs F2, F9, F11.** | inc. 1 | 4 new modules + tests | Property tests: normalization moves no money; currency never inferred from the account; dedup keys on `accountId` and the derived signed amount; fingerprint excludes `memo`/`categoryId`. |
| **3** | **Evidence + discovery.** `sourceRegistry.ts`, `buildFileSourceEvent`, and the S1 consumer registered on the **existing `finance` tick**. `scheduler.ts` **unmodified**. | inc. 2, D-B(c) | 2–3 new modules + tests; one `kv` checkpoint key | Re-capture appends once; differing bytes reported not overwritten; `SCHEDULER_TARGETS` unchanged; `listeningPorts` still has no writer; halted deployment discovers nothing and still writes liveness. |
| **4** | **Wire `dailyCapture`.** The prompt as a scheduled consumer; the reply as an S2 append; the parse as S3. **As a worker branch, not a Hermes tool.** **Repairs F4.** | inc. 3 | consumer module + tests | All twelve PFOS 15 §9.1 criteria including 10a; `HERMES_TOOL_NAMES` still 10; `DENIED_AUTHORITY_TOOLS` untouched; tamper test (§9.1 item 12) fails on a default currency, a keyword sign, a lenient parse, or an auto-promotion. |
| **5** | **Staging + record identity + the exclusion fence.** `candidatesRepository`; the record identity **lifted from `seedLoad` into a shared module** rather than written fresh; conflict-ignoring post-or-return. **Build the F17 fence:** extend exclusion to every engine in §9 against a **non-empty** baseline, and add the Drive-payload exclusion assertion that does not exist. **Repairs F3 (producer half), F8, F17, F19.** | inc. 4, D-A | repository + shared identity module + tests | Candidates leave every engine in §9 unchanged against a non-empty baseline; no candidate appears in any Drive-bound payload; the same promotion twice yields one row; a retried interrupted write returns the existing row without a primary-key error. |
| **6** | **Review and promotion.** The promotion module + review UI. **Repairs F3 (consumer half).** | **D-E — hard block** | promotion module, review UI, tests | No automatic promotion path exists (tamper test); `approved: true` set only here; a failed promotion leaves the candidate untouched. |
| **7** | **Posting integrity.** Read-back before acknowledge; transfer pairs in one transaction; posting decoupled from notification. **Repairs F10, F14.** | inc. 6 | `state/store.ts` (awaited + observed) or server posting path; tests | `READBACK_MISMATCH` never acknowledges; no one-legged transfer; a failed send never rolls back a posting; no artifact claims exactly-once **delivery**. |
| **8** | **Reconciliation + statement close.** `statementClose.ts`; `pending_to_posted` linking; the seven PFOS 02 §5.3 rules. | inc. 7 | 1 new module + tests | Zero-milliunit tolerance; three distinct verdicts, never collapsed; close only on a passing equation or an explicit exception acceptance. |
| **9** | **Derived-update seam.** The invalidation contract, asserted. | inc. 7 | thin seam + tests | A posting moves every target in §9; the ledger recompute and the cached balance agree; `forecastStartReconciles` holds; decisions unchanged; `MonthBudget.activity`/`.available` untouched. |
| **10** | **Coherence and mirroring.** Only if D-A = (a). Projection + `mirrorOf` stamp + the supersede-projection test. Preconditions: **F5 (via D-G), F6, F12.** | D-A, D-G | projection module + tests | Mirror is labelled as a mirror; candidates absent from every Drive-bound payload; a supersede projection does not double-count; `drive.file` scope unchanged so `AC08` keeps passing. |
| **11** | **Failure injection.** Crash between commit and read-back; crash between send and settle; duplicate tick; evidence-conflict; store unavailable mid-post. | inc. 9 | tests only | Each case leaves the canonical store consistent and produces a named exception, never a silent success. |

**Four harness constraints on how this work may be written** (all verified — annex §A.1):

- **`AC10`** — every file added or changed under `src/` or `tests/` must carry both a contract and a
  phase token bearing a digit within its **first twenty lines**.
- **`AC07`** — a decimal literal on a money-named field is banned **in test fixtures too**, unless the
  same line matches `must fail|must be integer|float|invalid|rejects?|should throw`. Every S3/S6
  refusal fixture must be authored on a line that names the invalidity (**F20**).
- **Two test floors, not one** — `AC04` reads `--min 3009`; `AC19` holds its own hard-coded
  `PROTECTED_TEST_FLOOR = 2301`. Tests **ratchet up only**; consider both.
- **`AC08b`, `AC05b` and `AC06` need `dist`** — the harness enforces this with a `produces`/`needs`
  preflight that refuses to run at all if the order contradicts itself. Do not reorder checks.

**The declared harness count stays 21** and no acceptance check is invented here; changing the count is
an owner decision.

---

## §12 Verification

Focused first, then the repository gate:

```text
npm run typecheck
npm run lint
npm test -- --run <relevant-test-file-or-pattern>
npm run build
npm run verify:all -- --all
```

**Expected result: 19 of 21, with `AC14` (clean tree) and `AC15` (push-ready) failing** on the 54
dirty entries. That is the correct baseline under **D-H**, not a regression. 21/21 is unreachable until
D-H is answered, and no gate is weakened to reach it.

**Three coverage gaps are recorded and not filled**, because each would change the declared check
count, which is an owner decision:

1. **`AC12`** opens only the two repository ledger files, parses index rows with a **single-digit**
   contract number, and hard-requires exactly five rows, with no amendment, supersession or date
   logic. The build-log amendment channel this plan depends on is therefore unverifiable by the
   harness **by construction** — a two-digit contract cannot even parse as a row.
2. **Drive encryption** — `AC08` enforces **scope only** (`drive.file`), not encryption, and no other
   check covers it.
3. **The candidate exclusion fence (F17)** — one netWorth test against an empty baseline is the whole
   of it, and nothing covers the Drive payload. Increment 5 closes this **as tests**, not as a new
   harness check.

For the record, the checks this plan actually leans on are `AC10`, `AC07`, `AC04`, `AC19`, `AC08`,
`AC09`, `AC18`, `AC12`, `AC14`, `AC15` — and the real ID set is not `AC01..AC21`: there is no `AC17`
entry (`AC17` *is* `all.mjs`), no `AC20`, no `AC21`, and the list includes `AC05b`, `AC08b` and `LOOP`.

---

## §13 What this plan does not authorize

No code is written. No test is edited. No gate is run. No host is touched. No credential is created,
rotated, read or echoed. No OAuth consent is completed. No webhook is registered. No DNS is mutated.
No provider key is spent against. No commit and no push. `G1–G8` in `ops/DEPLOYMENT_CONTROL.md` are
untouched, uncompleted, untested and unsubstituted. The 54 dirty working-tree entries are preserved
exactly as found. `money-rules.md` and `drive-db.md` are preserved without amendment. The Drive scope
stays `drive.file`. `HERMES_TOOL_NAMES` stays at 10 and no authority guard is weakened. No acceptance
check is weakened, removed or added. No owner decision is resolved and no default is adopted where
none was offered. The two schema changes this revision proposes (**D-J** outbox, **D-K** audit
triggers) are proposed and **not taken**.

---

## §14 Revision 2 changelog

What the second research pass changed, and why. Full evidence in the annex.

| Change | Was | Now | Source |
|---|---|---|---|
| **Corrected an over-claim** | "Engine exclusion holds with candidates present — the existing test is the fence." | The fence is **one** test: netWorth only, one candidate, empty-db baseline. Increment 5 must **build** it and add the Drive-payload assertion that does not exist. New finding **F17**. | Annex §A.2 |
| **Demoted "new" to "already exists"** | The stable record identity was marked **NEW**. | `seedLoad.ts` already implements it — content-derived, no clock, no counter, four independent idempotency mechanisms. Lift and share; do not invent. | Annex §A.3 |
| **Resolved a researched risk as already handled** | §5.4 reasoned about a read-tail-then-append lock in the abstract. | `withTransaction` already uses **`BEGIN IMMEDIATE`** and joins an open transaction; pragmas are set **and read back**. This is the remedy the literature prescribes, in place. It also **strengthens D-A(a)**. | Annex §A.5, §C.3 |
| **Found the residual concurrency gap** | — | **F19**: `seedLoad`'s `get`-then-`insert` is not atomic. S10 must make the insert conflict-ignoring and read back. | Annex §A.5 |
| **Named the mechanism §5.5 needed** | "Commit before composing the message." | Correct about ordering, and still loses the notification on a crash between the two. The **transactional outbox** fixes durability (not cardinality), and `work_queue` already proves the mechanics here. New decision **D-J**. | Annex §C.1 |
| **Sharpened the retry rule** | One retry table. | **A typed refusal is permanent and must never be retried** — it needs a clarifying question, not a backoff. Only transient failures retry. | Annex §C.2 |
| **Corrected the harness facts** | Implied `AC01..AC21`. | The real ID set has no `AC17`/`AC20`/`AC21` and includes `AC05b`, `AC08b`, `LOOP`. Added `AC07` (the money-float check **does** exist), `AC18`, `AC19`'s **second** floor of 2301, and `AC12`'s **single-digit** row regex. | Annex §A.1 |
| **Added an authoring constraint** | — | **F20**: `AC07` bans a decimal money literal **in fixtures**, so every refusal fixture must be written on a line naming the invalidity. This would have failed the harness during increment 1. | Annex §A.1 |
| **Made S11 literal** | "A `ReconciliationReport` distinguishing three outcomes." | `ReconciliationInput` (not `ReconcileInput`); literal verdict identifiers; `reconcile.ts` **writes nothing and never touches `statements`**, so the new module is the writer; two verdict gotchas preserved rather than "fixed". | Annex §A.6 |
| **Added a write-path constraint** | — | `assertMonetaryCoverage` is **bidirectional**: the statement-close path must mention all five `statements` money columns, explicit null included. | Annex §A.7 |
| **Settled the D-I format order** | Deferred, no target named. | **OFX/QFX → CSV → PDF**, because an OFX transaction carries a **source-supplied unique id** that is a stronger evidence identity than a derived fingerprint. Conditional on availability, which is unverifiable here. | Annex §C.4 |
| **Two new findings, two new decisions** | — | **F18** `audit_log` has no append-only trigger (**D-K**); **F21** `node:sqlite` is Stability 1.1 under a pinned runtime. | Annex §A.8, §C.3 |

**Net effect on scope.** Increment 5 grows (it now owns the exclusion fence) and increment 2 shrinks
(the identity is lifted, not authored). Nothing in §0's prohibitions, §7's exception taxonomy or §8's
automation boundary changed. The recommendation on **D-A(a)** is stronger than it was, on evidence
rather than on preference.

**Approval requested: this plan, for Stage-1 (offline implementation) only.** D-J and D-K are schema
changes and need their own answers; they are not bundled into that request.
