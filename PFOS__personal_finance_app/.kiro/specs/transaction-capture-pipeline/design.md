# Design: transaction-capture-pipeline

Spec: `transaction-capture-pipeline` · Notation: **TypeScript** (the server tier is TS strict; the money
invariant is type-enforced through `Money`, so pseudocode would hide the guarantee this design depends on)
Derived from `docs/plans/nizam-transaction-capture-pipeline-plan.md` (Revision 2) §1–§10 and its annex.
Requirements: `./requirements.md`. Tasks: `./tasks.md`.

**Authorization state.** **D-A ANSWERED — the server `finance.db` tier is canonical. D-C ANSWERED by
owner option (iii), 2026-09-22 — both server and browser CSV surfaces share `parseLedgerCsvStrict`, and
the browser is explicitly non-authoritative. D-E ANSWERED (b), narrowed to Contract 6 §5.**

---

## §A Verified current state

| # | Subject | Finding | Label |
|---|---|---|---|
| A1 | Browser tier | Zustand `db` → Dexie (`nizam_cache`, 7 stores) → Drive `nizam_db.json` + dated snapshots. `SCHEMA_VERSION = 9`, zod-validated. | VERIFIED |
| A2 | Server tier | `finance.db` via `node:sqlite`, WAL + `synchronous=FULL`, 8 checksum-ordered append-only migrations, money asserted at every write. | VERIFIED |
| A3 | No bridge | Nothing in `src/lib/drive/**` knows about SQLite; nothing in `src/server/db/**` reads `nizam_db.json`. No shared ids, no sync, no conflict protocol. | VERIFIED |
| A4 | Divergent corrections | Server supersedes (`supersedes_transaction_id`, `audit_version`, predecessor → `superseded`, second correction refused). Browser appends `reversal` + `replacement` sharing a `correctionGroupId`. Naive merge double-counts. | VERIFIED |
| A5 | Gate | 21 declared checks; `AC14`/`AC15` fail on the 54 dirty entries ⇒ **19/21 is the baseline**. | VERIFIED (declaration) |
| A6 | Host / Drive | No NIZAM host alias reachable; no Drive token in an agent session. | INACCESSIBLE |

### A.1 Input inventory

| Input | Status |
|---|---|
| Manual entry (`addTransaction`/`addTransfer`/`addReconcileAdjustment`) | **IMPLEMENTED, live** — writes canonical directly |
| CSV, 25-column `master_ledger` (`parseLedgerCsvStrict` + `dedupeRows` + `importLedger`, `ImportWizard`) | **OWNER OPTION (iii): strict shared parser; browser is an explicitly non-authoritative projection** — Increment 1 |
| CSV strict boundary (`parseLedgerCsvStrict`, typed refusal codes, derived signed amount) | **IMPLEMENTED and shared by both surfaces under D-C option (iii); browser projection non-authoritative** |
| Conversational capture (`dailyCapture.ts`: deterministic prompt, verbatim capture, 13 refusal codes, `captureContentHash`) | **IMPLEMENTED, UNWIRED** — only its test imports it |
| Per-account tables (`reconcile.ts` `readPerAccountTable`) | **IMPLEMENTED** as a comparator, not an intake path |
| Seed load (`seedLoad.ts`) | **IMPLEMENTED** — the only production caller of `transactionsRepository` |
| Statement files (PDF/XLSX) | **SCHEMA ONLY** (`statements`, `document_index`) — no parser |
| Receipts / images / OCR | **ABSENT** — zero matches repo-wide |
| Bank notifications (SMS/email/push) | **PROPOSED ONLY** — an intent label, no parser |
| Authorized bank APIs | **OUT OF SCOPE** (`product.md` v1 non-goal) |

### A.2 Reusable machinery that already provides a guarantee

`sourceEventsRepository.append` (immutable inbox, conflict-ignoring, reports
`contentHashMatches`) · `transactionsRepository` (single writer, no delete, `supersede`) ·
`transaction_links` (4 link types, integer bps, resolution enum) · `workQueueRepo` (claim/settle
predicates, **`reclaimStalledWork`** for crash recovery, explicit prune) · `updateDedupRepo.claimDelivery`
(the insert *is* the decision) · `scheduler.ts` (single clock, payload-free tick, per-tick halt re-read,
bounded retry, never crashes) · `liveness.ts` · `migrations.ts` (checksum-verified, `BEGIN IMMEDIATE`) ·
`withTransaction` (**`BEGIN IMMEDIATE`** + join-not-nest) · `connection.ts` (WAL/`foreign_keys`/
`synchronous=FULL`/`busy_timeout` set **and read back**, store refused on mismatch) · `recordAudit`
(inside the mutation's transaction) · `assertMonetaryCoverage` (**bidirectional** drift guard) ·
`store.mutate` (the browser's only invalidation mechanism) · `recomputeAccountBalances` · the Hermes
authority guard.

### A.3 Findings this design must address

F1 lenient CSV path is live (money-unit guess + sign inferred from an unsigned-magnitude column ⇒ every
row reads as an inflow) · F2 CSV `currency` parsed then discarded · F3 no promotion path anywhere ·
F4 `dailyCapture` unwired · F5 candidates serialized to Drive despite the "device-local" comment ·
F6 `saveDb` has no `If-Match` · F7 two canonical stores, no bridge, divergent corrections ·
F8 ids are clock+counter, not reproducible · F9 fuzzy dedup keys on display name and on the sign F1
breaks · F10 `persistLocal` errors unobserved, acknowledged before read-back · F11 eight provenance
fields declared, never written · F12 no tombstones · F13 server vocabulary diverges from PFOS 02 §4 with
no amendment record · F14 imported transfers are one-sided · F15 transport policy says Slack-only while
the wired path is Telegram-shaped · F16 `MonthBudget.activity`/`.available` are dead fields ·
**F17 the candidate exclusion fence is one netWorth test against an empty baseline** · F18 `audit_log`
has no append-only trigger · F19 `seedLoad`'s `get`-then-`insert` is not atomic · F20 `AC07` bans a
decimal money literal **in fixtures** unless the line names the invalidity · F21 `node:sqlite` is
Stability 1.1 under a pinned runtime.

_Full text: plan §1.4 and §14._

---

## §B Segment design

Per segment: **Owner** · **Input → Output** · **Persistence** · **State** · **Trigger** · **Failure** ·
**Acceptance**. Written to **D-A = server canonical**.

### S1 Source discovery
**Owner** NEW `src/server/ingest/sourceRegistry.ts` + one adapter per channel under
`src/server/ingest/channels/`. **In** a payload-free tick (pull), an authorized inbound message (push),
an owner file selection (pick). **Out** `DiscoveredSource { channel, idempotencyKey, rawBytes,
discoveredAt, declaredMoneyUnit? }` — **bytes only, nothing parsed**. **Persistence** none; stateless by
construction. **Trigger** a consumer on the **existing `finance` tick**; `acceptHandler` after allowlist
+ `claimDelivery`; `pickLedgerFile()`. **Failure** a raising channel is a failed discovery for that tick
only, bounded by the scheduler's existing `{1000ms, 15000ms, 3}` and abandoned; never costs another
channel its tick; never crashes the clock. **Acceptance** adding a channel changes no later segment;
`SCHEDULER_TARGETS` unchanged; `listeningPorts` still has no writer; a halted deployment discovers
nothing and still writes liveness; a source-level test asserts no adapter parses an amount.

### S2 Immutable evidence capture
**Owner** EXISTING `sourceEventsRepository.append`; `buildCapturedSourceEvent` (chat) + NEW
`buildFileSourceEvent` (CSV/statement) producing the same `SourceEventAppend`. **Out** `{ row, appended,
contentHashMatches }`. **Persistence** `source_events` (STRICT): `UNIQUE (channel, idempotency_key)`,
`content_hash`, `raw_payload`, `raw_payload_pruned_at`, `parse_state`, `document_ref`; large files hold a
`document_index` reference (`content_hash UNIQUE`) rather than bytes. **State** `parse_state`:
`pending → parsed | rejected | replayed`; nothing else mutates a row. **Failure** structural idempotency
— the insert is the decision; same key + different bytes is **reported, never overwritten**.
**Acceptance** capture twice appends once; differing bytes append nothing and report; `raw_payload`
byte-identical; capture durability independent of parse success; a pruned payload leaves hash, keys and
parsed record intact.

### S3 Deterministic extraction
**Owner** chat → EXISTING `parseDailyCaptureReply`; CSV → EXISTING `parseLedgerCsvStrict` (**Increment 1,
blocked on D-C**); statements deferred. All amounts through the money core's strict parsers. **Out**
`{ extracted: ExtractedRow[], refusals: ExtractionRefusal[] }` — a row **or** a refusal per record, never
both, never partial. **Persistence** none; writes `parse_state` and `parser_version`. **Trigger** S2
`appended: true`, or an explicit owner replay at a newer parser version (→ `replayed`). **Failure** typed
refusal carrying the code and the column/line at fault and **never the offending value**; one fixed
clarifying question; the answer re-enters at S2. **Acceptance** float, grouping separator and
four-fractional-digit amounts each **refused, not rounded**; sign from `direction` only; currency omission
refused and **not** defaulted to the account's; over-bound reply refused **whole**; every refusal code
provoked by a purpose-built input yielding **zero** rows; tamper test — a default currency, a
keyword-inferred sign or a lenient parse each make a test fail.

### S4 Normalization
**Owner** NEW `src/server/ingest/normalize.ts`, pure. **Out** `NormalizedRow` = `ExtractedRow` +
`normalizedPayee`, `merchantRaw` (verbatim), `occurredAt`, `postedAt`, `transactionType`, `direction`.
**Depends** the existing `normalizePayee` rule (lowercase, non-alphanumeric → single space, **Arabic
range `\u0600-\u06ff` preserved**) lifted into this shared module so there is one implementation;
`TRANSACTION_TYPE_VOCABULARY` / `DIRECTION_VOCABULARY` as declared maps. **Failure** an unlisted token is
refused (`TRANSACTION_TYPE_UNRECOGNISED`), never absorbed into `charge`; upstream tokens kept verbatim so
nothing the map decides is irreversible. **Acceptance** both payee forms retained; `extractionMethod`
never coerced to `manual`; a property test asserts byte-identical amounts in and out.

### S5 Account and currency resolution
**Owner** NEW `src/server/ingest/resolve.ts`. **In** + `ResolutionContext { accountAliases: readonly
{alias, accountId}[], knownCurrencies }` — an **array, not a map**, so a duplicated alias is
representable and therefore refusable. **Persistence** none; the alias set is a **caller input, not a
stored registry** (PFOS 15 §10.3), so a stale map yields a refusal rather than a wrong account. **Reuse**
`reconcile.resolveAccountMappings` already implements the right shape: two stages, `hits.length === 1`
required to claim, ambiguity left **unresolved rather than guessed**. **Failure** alias matching nothing
or more than one → `CAPTURE_ACCOUNT_UNKNOWN`; currency outside the known set → `CAPTURE_CURRENCY_UNKNOWN`.
Case-folding a currency is permitted (it cannot produce a *different* currency); defaulting one is not.
**Acceptance** ambiguous alias refused not chosen; currency never inferred from the account; **no FX at
ingest**; **repairs F2** for every channel routing through it.

### S6 Validation
**Owner** NEW `src/server/ingest/validate.ts` + EXISTING `moneyBoundary.assertMoneyField` /
`assertMonetaryCoverage`. **Failure** typed refusal. **Acceptance** three independent integrality guards;
`assertMonetaryCoverage` proves every money column was asserted before a statement was prepared; a
future-dated row refused, a validly back-dated one accepted at the stated date.

### S7 Deduplication
**Owner** NEW `src/server/ingest/dedupe.ts` composing EXISTING `captureContentHash` and
`transactionsRepository.findByDuplicateKey` / `recordLink`. **Persistence** `transaction_links` with
`link_type = 'suspected_duplicate'`, `confidence_bps` (integer basis points — **no float score**),
`resolution` initially `NULL`. **State** `duplicateStatus` starts `ambiguous`, becomes `unique` only when
the comparison ran; `resolution: NULL → confirmed | rejected | deferred` (owner act, S9). **Note**
`duplicate_key` is **indexed but NOT unique**; uniqueness comes solely from the content-derived primary
key. **Failure** **never auto-delete** — a same-day, same-amount, same-payee repeat is legitimate (two
coffees), so a collision is surfaced, linked, and the original source retained. **Acceptance** fail-closed
on an un-run comparison; no path deletes a row; integer bps end to end; keys on `accountId` and the
derived signed amount (**repairs F9**); pending↔posted linked not deduplicated.

#### S7 note — there are TWO dedup layers, and only one of them is S7 (added 2026-09-20)

PFOS v1.3 FINAL §27.6 **J2** orders the per-transaction journey as
`raw event → parse → exact duplicate check → normalize → ledger candidate`, i.e. an **exact duplicate
check before normalization**. S7 runs *after* S4–S6 and cannot move, because its fingerprint reads
`normalizedPayee`, which does not exist until S4 has run.

**This is not a conflict — the two checks are different checks, at different layers, on different keys:**

| Layer | Question | Key | Stage | Status |
|---|---|---|---|---|
| **Raw exact duplicate** (J2's) | Was this *same source message* already captured? | `(channel, idempotency_key)` over the captured bytes | **S2 evidence append** | key **EXISTS**; S1–S2 acceptance already reads "re-capture appends once" |
| **Content near-duplicate** (S7's) | Do two *different* source events describe the same economic transaction? | content fingerprint over date, direction, integer magnitude, currency, `accountId`, `normalizedPayee` | **S7** | new module |

**Why this note exists rather than a design change.** The raw layer was already specified, but only as an
evidence-idempotency property in §C.1 — it is never *named* as a duplicate check. A reader who looks for
"deduplication" finds S7, concludes dedup happens after normalization, and can then build an S2 path that
appends the same message twice while waiting for S7 to sort it out. That would push a raw duplicate
through parse, normalize, resolve and validate before catching it, and would make the evidence ledger
itself non-idempotent — which S8's record identity then cannot repair, because two evidence rows are two
legitimate parents.

**The Drive evidence confirms this layer fires, at a measurable rate.** The 30-day SMS reconstruction
(`docs/plans/nizam-drive-truth-inventory.md` §3.6) reports **3 exact duplicate SMS out of 254 scanned**.
Raw exact duplicates are real, roughly 1 in 85 messages, and they are cheap to catch at S2. The same
corpus also carries **20 declines**, **8 OTP/pre-auth** and **7 reversal notices** — all of which S3/S6
must refuse or route rather than post, and none of which are duplicates.

**Acceptance to add when S2 is built:** capturing a byte-identical message twice appends **one** evidence
row and reports the second as already-seen; and no raw duplicate reaches S4.

### S8 Candidate staging
**Owner** EXISTING `TransactionCandidate` shape; NEW `candidatesRepository`. **Persistence** server
`transactions` with `status = 'pending'`, `verification_level = 'unverified'` — the schema already models
this, so **a `pending` row is a candidate**. (Note `seedLoad` hardcodes `status: 'posted'`; nothing in the
tree writes `'pending'` today, so this is design, not existing behaviour.) **State** the six fixed values
of requirements §2.8, non-negotiable. **Failure** a candidate that cannot be written is a failed stage for
that record; the source event stays `pending` so a retry re-derives rather than half-commits.
**Acceptance** requirements §2.9 — the fence is **built here**, across every engine in §5, against a
non-empty baseline, plus the Drive-payload assertion that does not exist today.

### S9 Review and approval
**Owner** NEW promotion module + review UI. **BLOCKED on D-E** — `two-agent-vps.md` §5 forbids building an
ungoverned area, and the only document specifying promotion (draft Contract 6 I5.3) is unapproved.
**Out** `PromotionRequest { candidateId, edits?, resolvedLinks, reason? }` or a discard. **Persistence**
`audit_log` per review act; link `resolution` set; discarded candidates **superseded, not deleted**.
**Trigger** an explicit owner action and nothing else. **Acceptance** requirements §2.10, plus a tamper
test that adding an auto-promotion path makes a test fail.

### S10 Canonical posting
**Owner** EXISTING `transactionsRepository` — the single writer, in either tier, with no second writer
introduced. **Persistence** server `transactions`. **State** `pending → posted` on promotion;
`posted → reconciled` at statement close; correction by `supersede`; **no delete, no in-place edit**.
**Failure** one `withTransaction` (`BEGIN IMMEDIATE`) so a crash leaves nothing or everything; duplicate
promotion suppressed by the record identity; **conflict-ignoring insert + read-back rather than
check-then-insert** (repairs F19 — `enqueueWork` and `claimDelivery` already show the idiom).
**Acceptance** promoting twice yields one row; a reconciled row never mutated in place; no one-legged
transfer; split legs sum exactly via `allocate()` with superseded sets retained; the acknowledgement
follows the §C.4 read-back; `assertMonetaryCoverage` passes.

### S11 Reconciliation
**Owner** EXISTING `reconcile.ts` (verified to **write nothing** — three `SELECT`s, no transaction, and it
never touches `statements`) + NEW `src/server/ingest/statementClose.ts`, which is the writer and the only
thing that persists a report. **In** `ReconciliationInput { ctx, perAccount, mappings,
windowStartInclusive, thirdOpinion }` — the window boundary **stated, never inferred**. **Out**
`ReconciliationReport` with `verdict: 'RECONCILED' | 'RECONCILED_WITH_REPORTED_DISAGREEMENT' |
'UNEXPLAINED_RESIDUAL'` and `tolerance.milliunits` typed literal `0`. **Persistence** `statements`
(`close_state`, `UNIQUE (account_id, statement_month)`); `transaction_links` for `pending_to_posted` and
`correction`. **State** `open → balanced | exception_accepted` (the latter an **explicit owner act**);
transactions in a closed period → `reconciled`.
**Two verified gotchas to preserve rather than "fix":** ① verdict precedence puts a row-count mismatch
above everything, and `RECONCILED` requires `findings.length === 0`, so **any** finding — including an
unmapped account token unrelated to money — correctly downgrades a matching load. Do not suppress
findings to reach `RECONCILED`. ② `disagreementIsSignOnly` is trusted only alongside
`signResidualIdentityHolds`: flipping a sign moves a total by exactly twice the magnitude, so if the
residual is not the difference of the unmatched populations, something other than a sign moved.
**New write constraint** `assertMonetaryCoverage` is bidirectional, so `statementClose.ts` must mention
**all five** `statements` money columns including `minimum_due`, passing an explicit null.
**Acceptance** PFOS 02 §5.3 in full; the two comparison paths share no arithmetic.

### S12 Derived updates
**Owner** EXISTING engines, unmodified, plus a NEW thin invalidation seam. **Persistence** only
`Account.balance` and `Account.clearedBalance` are stored derived money; both must be refreshed.
**Browser path** the mutation must go through `store.mutate` so a **new `db` object** is produced — that
identity change is the *only* invalidation mechanism — and must call `recomputeAccountBalances(draft)`.
Skipping the second step leaves `liquidNow` → safe-to-spend, forecast, obligations and net worth on the
**old** cash figure while the register shows the new one. **Failure** posting success is independent of
notification delivery; a failed recompute is a failed *read*, never a rollback of a committed posting.
**Acceptance** §5 below.

---

## §C Cross-cutting mechanics

### C.1 Identity — four, each with one job
| Identity | Definition | Status |
|---|---|---|
| Evidence | `(channel, idempotency_key)` | **EXISTS** |
| Content fingerprint | `sha256` over date, direction, **integer magnitude**, currency, accountId, normalizedPayee, `\u0000`-joined; **excludes `memo` and `categoryId`** | **EXISTS** (`captureContentHash`) — lift to a shared module |
| Record identity | caller-supplied, content-derived, reproducible on retry | **ALREADY EXISTS in `seedLoad.ts`** — `transactionIdFor(key) = 'txn_' + sha256(channel \0 key).slice(0,32)` plus `accountIdFor`, `sourceEventIdFor`, `periodKeyOf`, a 26-field `rowContentHash`. **Lift and share; do not invent.** |
| Correlation | `queuedRef` | **EXISTS** |

The record identity is the direct answer to the `nizamcore` `ledger_writer.py` defect recorded in
`two-agent-vps.md` §6a purpose 4: a fresh `uuid4()` per call gives a retried write a **second valid row**
that no chain verification can detect. Browser `newId()` (clock + module counter) is unsuitable — F8.

### C.2 Checkpoints
Schema `schema_migrations` (checksum) · Evidence `source_events.parse_state` · Work `work_queue.state` ·
Job run the **existing `kv` table** (`lastRunAt`; **no new table** — this reuses what
`hermes-governed-workflows` I2 proposes, so the two do not create competing registries) · Liveness the
file record · Period `statements.close_state`.

### C.3 Fencing and bounds
Claim-is-the-fence (`state = 'queued'` predicate) · double-settle refused (`state = 'running'`) ·
duplicate arrival conflict-ignoring · read-then-append races avoided by `BEGIN IMMEDIATE` or, preferably,
by a unique constraint that makes the fork impossible · **a typed refusal is permanent and never
retried** · tick 3 / work 5 / send 4 / Drive push 1 — all already declared, none invented.

### C.4 Read-back before acknowledging
Write → commit → `get(recordId)` → compare `amount`, `currency`, `accountId`, `date`, `direction`,
`status`, `duplicateKey` → **then** compose the acknowledgement. In the browser tier this additionally
requires `persistLocal` to be **awaited with errors observed** (repairs F10).

### C.5 Outbound delivery
Three guarantees, never merged: canonical write exactly once · settlement idempotent · **outbound
at-least-once only**. Commit-then-compose stands, with the honest disclosure that a crash between the two
loses the notification. The **transactional outbox** (write the notification intent in the same
transaction, drain by relay) closes that durability gap and **not** the cardinality one; it needs a new
table, hence **D-J**. `work_queue` already proves the mechanics; column names must avoid
`TELEMETRY_FORBIDDEN_COLUMNS` (`payload` is admissible).

---

## §D Exception taxonomy

Twelve classes per requirements §3.7. Each produces zero canonical rows, an intact source event, a typed
code, and one clarifying question fixed in code. Notable dispositions: `TRANSFER_AMBIGUOUS` stages a
**one-sided candidate flagged for review**, never a half-transfer and never auto-paired;
`REFUND_AMBIGUOUS` records a candidate `correction` link with a bps score and **never nets against the
original automatically**; `SPLIT_AMBIGUOUS` refuses the allocation set **whole** (a tolerance here is how
drift starts); `EVIDENCE_CONFLICT` keeps the existing row exactly and surfaces the disagreement.

---

## §E Downstream mapping (S12 targets)

One canonical ledger, read-only mirrors, no competing ledger (ADR-0003 AD-2).

| Target | How | Guard |
|---|---|---|
| Transactional store | single writer inserts; supersede-not-edit; no delete | `assertMonetaryCoverage` before any statement is prepared |
| Linked transfers | both legs in one transaction + `transfer_pair` link | a group with one live leg, or three legs, is a defect and a test |
| Balances | `Account.balance`/`clearedBalance` recomputed from the ledger | **two sources for one figure is the coherence risk**: `rescue.ts` and the register use the ledger recompute while `liquidNow` uses the cached field. Both must agree after every posting — asserted by a test |
| Budgets | `computeBudget`/`computeMonth` recompute; split legs expand per category | transfers excluded via `transferAccountId`; correction rows deliberately **keep** it so a reversal is not counted as spending |
| Obligations | `obligationFundingReport`, `confidentInflowsBy`, `pendingOutflowsBy` at the injected `asOf` | reads cached `clearedBalance` via `liquidNow`, so §C.4 and the balance recompute must precede it |
| Safe-to-spend | `safeToSpendAllHorizons` | calls `computeMonth` per horizon — known cost, not a defect |
| Forecast | `forecastAll` | `forecastStartReconciles` must still hold |
| Reports | `spendingByCategory/ByGroup`, `netWorthSeries`, `ageOfMoney`, `cardUtilization`, `debtServiceRatio`, `liquidityRunway`, `controlPanel` | pure recompute |
| Net worth | `netWorth`, `realNetWorth` | balances + assets + obligations + fxRates + macro |
| **Decisions** | **not recomputed** — `forecast`/`confidenceBps` frozen at decision time; `reviewDecision` enforces byte-identity of core keys | a posting must not mutate a recorded decision |
| Audit history | `audit_log`, `supersedes_transaction_id`, `audit_version`, `supersededAllocations`, `meta.conflicts` | append-only everywhere |
| **Not written** | `MonthBudget.activity`/`.available` (F16) | dead fields; this pipeline does not start reading them |

---

## §F Browser / server coherence, under D-A = server canonical

1. **One canonical writer** — server `finance.db` via `transactionsRepository`. The browser stops posting
   and becomes a **review and presentation surface**.
2. **One direction of flow** — server → browser. The browser never writes a transaction back.
3. **The mirror is derived, not authoritative** — `nizam_db.json` becomes a **projection** carrying a
   `mirrorOf { storeRef, schemaVersion, projectedAt, sourceAuditVersion }` stamp so a reader can tell a
   mirror from a source. Drive stays `drive.file`, data only, atomic writes, dated snapshots, retention,
   and `meta.conflicts` as the audit channel.
4. **Candidates never leave the device** until D-G's single serialisation-time projection lands (F5). The
   mirror must not be enabled for real data before then.
5. **Identity is shared** via the fingerprint and the record identity of §C.1, not via `newId()` (F8).
6. **Correction semantics unified at the mirror boundary** — the canonical supersede chain projects into
   browser-shaped rows in exactly one declared way, and a test asserts the projection of a supersede does
   **not** double-count against a reversal+replacement reading (A4).

**Preconditions for trusting the mirror:** F5 (via D-G), F6 (`If-Match`), F12 (tombstones).

---

## §G Harness constraints on how this work may be written

- **`AC10`** — contract + phase tokens bearing a digit within the first twenty lines of every new/changed
  `src/` or `tests/` file.
- **`AC07`** — a decimal literal on a money-named field is banned **in test fixtures too**, unless the
  line matches `must fail|must be integer|float|invalid|rejects?|should throw`. Every S3/S6 refusal
  fixture must be authored on a line that names the invalidity (**F20**).
- **Two test floors** — `AC04` reads `--min 3009`; `AC19` holds its own `PROTECTED_TEST_FLOOR = 2301`.
  Tests ratchet **up only**; consider both.
- **`AC05b`/`AC06`/`AC08b` need `dist`** — the harness enforces this with a `produces`/`needs` preflight
  that refuses to run if the order contradicts itself. Do not reorder checks.
- The declared harness count stays **21**; no check is invented here.
