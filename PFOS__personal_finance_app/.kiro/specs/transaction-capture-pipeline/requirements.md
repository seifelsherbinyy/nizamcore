# Requirements: transaction-capture-pipeline

Spec: `transaction-capture-pipeline` · Workflow: design-first · Type: feature
Owning authority: PFOS Contract 02 §3/§4/§5 (ingestion strategy, transaction state model, deduplication
and reconciliation), PFOS Contract 06 (store schema and the money persistence boundary), PFOS Contract
15 (daily capture and candidate staging), ADR-0003 AD-4 and AD-6, `money-rules.md`, `drive-db.md`.
Derived from: `docs/plans/nizam-transaction-capture-pipeline-plan.md` (Revision 2) §0–§10 and
`docs/plans/nizam-transaction-capture-pipeline-research-annex.md`. **The plan remains the narrative
source; this file is its normative restatement.** Where the two differ, the plan wins and this file is
corrected in a numbered revision.

**Promotion note.** The plan's own header states it is promoted to
`.kiro/specs/transaction-capture-pipeline/` on approval. **D-A is ANSWERED (server `finance.db`
canonical); D-C is ANSWERED by owner option (iii) on 2026-09-22: browser and server surfaces both call
`parseLedgerCsvStrict`, and the browser is explicitly non-authoritative. D-E is ANSWERED (b), narrowed to
Contract 6 §5.**

---

## 1. Authority and non-negotiables

**1.1** Money is an integer count of milliunits. No floating-point money at any boundary, in any
intermediate. _Source: `money-rules.md` rules 1–2; PFOS 06 §4.2._

**1.2** Deterministic parsers and the authorized single-writer repository control every monetary fact.
The LLM/model tier never computes, sources, estimates, rounds, converts or restates an authoritative
monetary value. _Source: `pfos-current.md`; ADR-0003 AD-4; plan §4.0 rule 1._

**1.3** Hermes orchestrates only. It may ask, deliver deterministic prompt text, present a candidate,
explain a refusal and route a request. It may never compose an amount, choose a currency, infer a
direction, resolve an account, or decide what a malformed line probably meant. _Source: PFOS 15 §2.1;
plan §8.3._

**1.4** The Hermes authority guard is not weakened. `runtimeAdapter.AUTHORITY_KEY` makes a payload or
result key matching `amount|balance|currency|milliunit|money|price|cost|financial` unrepresentable
across the tool boundary; `HERMES_TOOL_NAMES` stays at **10**; no denylist entry is removed and no regex
relaxed. Deterministic legs are added as **worker branches, not tools**. _Source: plan §8.3; PFOS 15
§2.1._

**1.5** Google Drive scope stays `https://www.googleapis.com/auth/drive.file`. Drive holds data only,
never keys or secrets. _Source: `drive-db.md`; AC08._

**1.6** Every file added or changed under `src/` or `tests/` declares its owning contract and phase
within its first twenty lines. _Source: `AGENTS.md`; AC10._

**1.7** No acceptance check in the repository gate (`AC01`–`AC19`, `AC05b`, `AC08b`, `LOOP`) is
invented, weakened, or claimed satisfied without observation. The declared harness count stays 21.
_Source: plan §11, §12; annex §A.1._

---

## 2. Pipeline requirements — the twelve segments

The pipeline is ADR-0003 AD-6's chain with discovery, resolution, staging and derived updates named as
their own segments, because each of those four is where current code has a gap or a defect.

```text
S1 source discovery → S2 immutable evidence capture → S3 deterministic extraction
   → S4 normalization → S5 account/currency resolution → S6 validation → S7 deduplication
   → S8 candidate staging → S9 review/approval → S10 canonical posting
   → S11 reconciliation → S12 derived updates
```

**2.1 (S1)** Adding an intake channel SHALL add a registry entry and an adapter and SHALL change no
later segment. No adapter parses an amount. Pull channels register as consumers of the **existing
`finance` tick**; `SCHEDULER_TARGETS` stays a two-member `const` tuple and `listeningPorts` keeps no
writer. _Source: plan §4/S1; ADR-0003 D7-C (edge relay forwards bytes and a hash, nothing more)._

**2.2 (S2)** Evidence capture SHALL be idempotent by construction: `UNIQUE (channel, idempotency_key)`
with a conflict-ignoring insert, so a re-send is a no-op that cannot be raced. The same key with
**different bytes** SHALL be reported (`contentHashMatches: false`), the stored row left exactly as it
was, and the disagreement surfaced as an exception. `raw_payload` SHALL be byte-identical to what
arrived — not trimmed, re-cased or re-wrapped. Capture durability and parse success SHALL be
independent. _Source: plan §4/S2; PFOS 15 §3.2/§3.3; annex §A.1._

**2.3 (S3)** Extraction SHALL be a deterministic parser, never a model. Every amount goes through
`fromDecimalStrict` / `fromMilliunitsStrict`. **Owner option (iii), 2026-09-22:** the server and browser
CSV surfaces SHALL both call `parseLedgerCsvStrict`; the browser SHALL be labelled non-authoritative in
code and UI, and neither surface may silently redirect to the other. The money unit SHALL be explicitly
declared by the owner and detector disagreement SHALL be reported without overriding that declaration.
Each record yields **a row or a typed refusal, never both
and never a partial**. A refusal SHALL NOT carry the offending value. One fixed clarifying question per
refusal; a model may phrase it, the owner answers, and the answer re-enters at **S2** as new evidence.
_Source: plan §4/S3; PFOS 15 §5.1/§5.3._

**2.4 (S4)** Normalization SHALL retain both raw and normalized payee, SHALL keep upstream vocabulary
tokens verbatim (`transaction_type_raw`, `extraction_method_raw`), and SHALL refuse an unlisted
vocabulary token rather than absorbing it into a default. `extractionMethod` SHALL NEVER be coerced to
`manual` for a machine-extracted row — `unknown` is the honest value and it exists. Normalization SHALL
change no monetary value. _Source: plan §4/S4; PFOS 02 §5.2; `ledger.types.ts` K4/F23._

**2.5 (S5)** Account and currency resolution SHALL refuse an alias matching nothing or more than one.
There is no default account. A currency outside the known set SHALL be refused, **never substituted, and
never defaulted to the account's own currency**. **No FX at ingest, ever.** _Source: plan §4/S5; PFOS 15
§5.2/§5.4._

**2.6 (S6)** Validation SHALL assert: amount is a safe integer in milliunits; `|amount| == outflow +
inflow` with exactly one populated; sign agrees with `direction`; the date is a real calendar date and
not in the future; the account exists and is open; the currency is known; the row carries a source
reference. A non-safe-integer SHALL be refused at the branded type, at the validator **and** at the
persistence schema — three independent guards. _Source: plan §4/S6; PFOS 06 §4.2._

**2.7 (S7)** Deduplication SHALL be fail-closed: `duplicateStatus` starts `ambiguous` and becomes
`unique` only when the comparison has actually run against both the candidate and canonical sets. **No
path deletes a suspected duplicate.** Matching SHALL key on `accountId` (not the display name) and on
the derived signed amount. Scores SHALL be integer basis points end to end. A pending authorization and
its later posted entry SHALL be linked `pending_to_posted`, not deduplicated away. _Source: plan §4/S7;
PFOS 02 §5.1/§5.2; PFOS 15 §7.2._

**2.8 (S8)** Staged candidates SHALL hold these fixed values without exception: `approved = false`;
`cleared = 'uncleared'`; `categoryId = null`; `splits = null`; `transferAccountId` and
`transferTransactionId = null`; `duplicateStatus = 'ambiguous'` unless S7 proved otherwise. Provenance
SHALL be complete and honest (`extractionMethod`, `sourceType`, `confidenceScore`, `confidenceReason`,
`contentHash`, `duplicateKey`, `sourceFile`, `parserVersion`). _Source: plan §4/S8; PFOS 15 §4.4/§7.1._

**2.9 (S8) — engine exclusion must be BUILT, not inherited.** The existing fence is a single test
covering `netWorth` only, with one candidate against an **empty-db baseline**, so all three expected
values are zero. This spec SHALL extend exclusion to **every engine named in §5 of `design.md`, against a
non-empty baseline**, and SHALL add the Drive-payload exclusion assertion that does not exist today.
_Source: plan F17; annex §A.2 (`src/lib/db/migrations.test.ts:343`)._

**2.10 (S9)** Promotion SHALL be an explicit owner action and nothing else. **No schedule, threshold,
confidence score, streak, "obvious" case, or repetition of a previously promoted payee SHALL promote
anything.** No batch promotion. An agent may present and explain a candidate; it may not promote one.
`approved: true` SHALL be set here and nowhere else. _Source: plan §4/S9; PFOS 15 §4.3._

**2.11 (S10)** Canonical posting SHALL go through the single writer. Correction is by **superseding
row**; there is no delete and no in-place edit of a posted row. `verification_level` advances
`unverified → parser → reconciled → statement` and never regresses. Transfers post as a **linked pair in
the same transaction**. The insert SHALL be **conflict-ignoring with a read-back** rather than
check-then-insert, so the insert *is* the decision. _Source: plan §4/S10; plan F19; annex §A.5._

**2.12 (S11)** Reconciliation tolerance SHALL be **zero milliunits**, derived: both sources state
amounts as decimal text with at most three fractional digits, a milliunit *is* the third decimal place,
so every conversion is exact and summing exact integers is exact. The verdict SHALL be one of
`RECONCILED | RECONCILED_WITH_REPORTED_DISAGREEMENT | UNEXPLAINED_RESIDUAL` — **never collapsed to a
pass/fail**. A disagreement is a finding; neither side is adopted silently and the two are never
averaged. A period closes only after the balance equation passes or an exception is **explicitly**
accepted. _Source: plan §4/S11; PFOS 02 §5.3; annex §A.6._

**2.12a (S11) — the reconciliation universe. Owner decision R2, recorded 2026-09-22.** The owner approved
the consolidated master plan and directed execution with R2's recommended option unamended. Reconciliation
SHALL compare like with like, which requires the population to be **stated rather than inherited from
whatever the table happens to hold**:

- Only rows whose `status` is `posted` or `reconciled` participate. A staged candidate (`pending` +
  `unverified`, Contract 6 §5.7), a `void` row and a `superseded` row are each excluded. Excluding a
  candidate here is not a preference; it is Contract 6 I5.2 applied to a report.
- The period SHALL be bounded at **both** ends. An open-ended upper bound silently admits rows the other
  rendering was never asked about, and that appears as an unexplained residual when it is really a scope
  error.
- Only accounts named by a supplied mapping participate on the store side, so an unmapped account cannot
  contribute to a total whose counterpart does not exist.
- The two renderings use **different date bases** — the store's `transaction_date` and the per-account
  rendering's `posted_date`. That difference SHALL be declared in the report rather than hidden inside the
  comparison.
- The zero tolerance, the three-verdict vocabulary, the row-count precedence and the sign-residual identity
  of §2.12 are unchanged. A narrower population is not a weaker check: it makes the residual mean what it
  claims to mean.

Two identical computations over one unchanged store SHALL return an identical report, so a reconciliation
answer is a function of persisted state and never of what a reader happened to have open.

**2.13 (S12)** A posted transaction SHALL correctly move every target named in `design.md` §5.
`Account.balance` and `Account.clearedBalance` are the only **stored** derived money and SHALL be
refreshed; everything else recomputes from the ledger. `MonthBudget.activity`/`.available` SHALL NOT be
read or written — they are persisted, stale, and read by nobody. Recorded decisions SHALL NOT be
mutated. _Source: plan §4/S12, §9; plan F16._

---

## 3. Cross-cutting requirements

**3.1 Identity.** Four identities, each with one job: evidence identity `(channel, idempotency_key)`;
a content fingerprint over date, direction, integer magnitude, currency, accountId and normalizedPayee
— **excluding `memo` and `categoryId`** so a later edit cannot change it; a **caller-supplied,
content-derived record identity**; and `queuedRef` for correlation. The record identity SHALL be lifted
from `seedLoad.ts`, which already implements it, rather than written fresh. _Source: plan §5.1; annex
§A.3._

**3.2 Atomic writes.** One store transaction per logical step through `withTransaction`, which already
uses **`BEGIN IMMEDIATE`** and joins an open transaction rather than nesting. `recordAudit` runs inside
the mutation's own transaction, so an audit gap is not a reachable state. _Source: plan §5.3; annex
§A.5, §C.3._

**3.3 Retry discipline.** **A typed refusal is permanent and SHALL NEVER be retried** — it needs a
clarifying question, not a backoff. Only transient failures use the existing bounded retries (tick 3
attempts, work 5, send 4, Drive push 1). No new retry policy is invented. _Source: plan §5.4; annex
§C.2._

**3.4 Posting success is separate from notification delivery.** Three guarantees, never merged:
canonical write **exactly once** (record identity); settlement **idempotent** (the `state = 'running'`
predicate); outbound notification **at-least-once and nothing more**. **No artifact, reply or document
SHALL claim exactly-once delivery.** A posting commits before any message is composed, and a failed send
never rolls back a posting. _Source: plan §5.5._

**3.5 Canonical read-back before acknowledging.** Write → commit → `get(recordId)` → compare the
financially consequential fields → **only then** acknowledge. A mismatch or absent read-back is an
exception (`READBACK_MISMATCH`), never a silent success. _Source: plan §5.6._

**3.6 Preservation.** Original evidence verbatim; provenance on every canonical row (a row with no
source reference is refused); parser version per row; **confidence as two separate fields — an integer
bps score and an ordinal band, neither derived from the other**; refusal reasons without the offending
value; superseded state append-only. _Source: plan §6._

**3.7 Exception handling.** Twelve classes — `AMOUNT_AMBIGUOUS`, `DATE_AMBIGUOUS`, `SIGN_AMBIGUOUS`,
`CURRENCY_AMBIGUOUS`, `ACCOUNT_AMBIGUOUS`, `TRANSFER_AMBIGUOUS`, `REFUND_AMBIGUOUS`, `SPLIT_AMBIGUOUS`,
`DUPLICATE_AMBIGUOUS`, `EVIDENCE_CONFLICT`, `READBACK_MISMATCH`, `VOCABULARY_UNKNOWN`. Each SHALL
produce zero canonical rows, an intact source event, a typed code, and exactly one clarifying question
whose text is fixed in code. **Ambiguity SHALL NEVER become a ledger write.** _Source: plan §7._

**3.8 Automation boundary.** Automated: discovery, capture, parsing, normalization, resolution,
validation, staging, dedup *analysis* and link recording, candidate presentation, reconciliation checks,
derived recompute. **Never automated:** promotion, approval, statement-close exception acceptance,
duplicate-link disposition, category assignment at capture, transfer pairing, refund netting, ingest FX,
schema migration, any credential/host/transport act. _Source: plan §8.1/§8.2._

**3.9 Automatic posting is out of scope.** Explicit owner promotion is preserved without exception. Any
automatic-posting policy is a **separate contract requiring its own approval** and is not bundled with
this spec. _Source: plan §8.4 (**D-F**)._

---

## 4. Decision state

Inherited from the plan §3. **This spec does not re-litigate any of them.**

| # | Status | Effect on this spec |
|---|---|---|
| **D-A** | **ANSWERED — server `finance.db` canonical** | Sets every segment's persistence. The browser becomes a read model. Recorded 2026-09-20. |
| **D-C** | **ANSWERED — option (iii), 2026-09-22: both CSV surfaces share `parseLedgerCsvStrict`; browser explicitly non-authoritative** | Unblocks Increment 1 without redirecting the wiring. |
| **D-E** | **OPEN** | **Blocks Increment 6 only** (review/promotion needs an approved governing contract; `two-agent-vps.md` §5 forbids building an ungoverned area). |
| D-B | OPEN, deferred by design | Offline build proceeds behind injected ports with deterministic mocks. No transport bound. |
| D-D | OPEN | Not a blocker; `manual` works for `sourceType`. |
| D-G | OPEN (shared with `hermes-governed-workflows` D-5) | Blocks the Drive-mirror half of Increment 10. Answer once, there. |
| D-H | **OPEN, `None offered`** | `AC14`/`AC15` fail; **19/21 is the correct baseline**, not a regression. |
| D-I | ANSWERED on format order (OFX/QFX → CSV → PDF); sequencing still deferred | Statement/notification parsers stay out of scope; they are an S1–S3 adapter. |
| D-J | OPEN | Outbox is a migration. Until answered, commit-then-compose stands **with the loss disclosed**. |
| D-K | OPEN | `audit_log` append-only triggers are a migration; the trail is populated either way. |
| **D-H** | **ANSWERED 2026-09-22 — reviewed partition. `docs/adr/ADR-0004-production-release-decisions.md`** | Project material commits in atomic groups; personal/non-project material moves to a private quarantine outside this public repository; ambiguous material is held unopened. A local exclude is **prohibited** as a substitute. Unblocks `AC14`/`AC15`. |
| **D-J** | **ANSWERED 2026-09-22 — transactional outbox. ADR-0004** | Migration **version 9**. Posting and notification intent commit in one transaction. At-least-once with deduplication; **exactly-once may never be claimed**. |
| **D-K** | **ANSWERED 2026-09-22 — append-only triggers. ADR-0004** | Migration **version 10**. `UPDATE`/`DELETE` on the audit trail refused by the engine, matching the existing signal-store trigger precedent that `AC19` already asserts. |
| **D-Z** | **ANSWERED 2026-09-22 — source payload plus derived read. ADR-0004** | No migration. **No FX conversion at ingest**; a rate is evidence about its source event and is read through a derived accessor. |
| **D-8** | **ANSWERED 2026-09-22 — pre-tier admission. ADR-0004** | Local capture, deterministic financial reads, clarifications and refusals never reach model classification or model spend. |
| **D-SLACK-1** | **ANSWERED 2026-09-22 — ADR-0004 + `ops/SLACK_V2_RELEASE_RECORD.md`** | One consumer per Slack envelope; the `nizamfinancialapp` Socket Mode process is the sole live owner ingress. |
| **D-SLACK-2** | **ANSWERED 2026-09-22 — ADR-0004** | Deterministic engines are the only source of a financial number. A model may explain; it may never source or modify money. |
| **D-INGEST-1** | **ANSWERED 2026-09-22 — ADR-0004** | Evidence → candidate → **explicit** promotion. Enforced by Contract 6 §5.7 and §2.12a, not re-invented. |
| **D-RELEASE-1** | **ANSWERED 2026-09-22 — audit passed, include. ADR-0004** | `ba43912`, `2702235`, `5a5b882`, `5652edf`: six `ops/` docs, 1,665 insertions, zero deletions, zero scan hits. No history rewrite. |
| **R1** | **ANSWERED — recorded 2026-09-22 as Contract 6 §5.7 (I5.7.1–I5.7.5)** | Server-tier staging MAY be the disjoint `status='pending' AND verification_level='unverified'` subset of `transactions`; "distinct from canonical" becomes a requirement on **every read**, not a table boundary. No migration, no physical `transaction_candidates` table. |
| **R2** | **ANSWERED — recorded 2026-09-22 as requirement §2.12a** | Fixes the reconciliation universe: canonical statuses only, both window bounds required, mapped accounts only, date bases declared rather than unified. Repaired `reconcile.ts` ahead of Increment 8. |

**R3–R12 remain OPEN, and the reason is an evidence gap rather than a disagreement (recorded 2026-09-22).**
The owner subsequently directed that R3–R12 be executed by adopting "the single recommended option already
documented for each", and in the same instruction required that an item **without exactly one documented
recommendation must not be decided on the owner's behalf**. Those two clauses resolve against execution
here, on the following observation: **the master plan that carried the R3–R12 recommendations was delivered
in conversation and was never written to this repository.** `docs/kiro/prompts/` contains no `011` artifact,
`docs/plans/` contains no master-plan file, and a repository-wide search for the R3–R12 decision package
returns only unrelated identifier spaces — the `06-two-agent-vps` spec's requirements R1–R34, and the
governor readiness stages R3–R7 in `ops/NIZAM_GOVERNOR_ACCEPTANCE_MATRIX.md`. Neither is a decision package
with one recommendation per item, and mapping the owner's R-numbers onto either would be a guess about
which decision was meant. R1 and R2 survived because their full text was transcribed into Contract 6 §5.7
and §2.12a above before the session record was compacted; R3–R12 were not transcribed, so no durable
statement of their recommended options exists to adopt. **Re-supplying the R3–R12 text, or naming each
decision directly, re-opens execution immediately and reopens nothing already settled.**

**Drift to flag, not to resolve here (noted 2026-09-22).** This table lists **D-E** as `OPEN`, while
`tasks.md` records it as **ANSWERED (b) narrowed, 2026-09-20 — Contract 6 §5 (I5.1–I5.6) APPROVED and
governing**, and unblocks Increment 6 on that basis. Increment 6 is recorded `done`. Both statements are in
the repository and they disagree; the newer, more specific one is in `tasks.md`. **This row was not
rewritten**, because changing a decision's status is recording an owner answer, and no owner answer
naming D-E was given in this session. R1's §5.7 extends the same §5 that the `tasks.md` record says is
approved, so the two are consistent with each other under that reading.

---

## 5. Definition of done

This spec is DONE when every increment in `tasks.md` is `done`, and:

1. Every requirement in §2 and §3 has a passing test whose failure mode was observed at least once
   (tamper discipline — a guard that cannot be made to fail is not a guard).
2. `npm run typecheck`, `npm run lint`, focused tests and `npm run build` pass.
3. `npm run verify:all -- --all` reports **19 of 21 with only `AC14` and `AC15` failing** while **D-H**
   is unanswered. That is the correct baseline. **21/21 is unreachable until D-H is answered and no gate
   is weakened to reach it.**
4. The three recorded coverage gaps remain **recorded, not silently filled**: `AC12`'s single-digit
   five-row contract-ledger parse, Drive encryption (`AC08` enforces scope only), and the candidate
   exclusion fence (closed here **as tests**, not as a new harness check).

_Source: plan §12; annex §A.1._
