# NIZAM continuity gap report

**Task:** NIZAM-CONTINUITY-010  
**Scope:** Repository evidence from Phase 0 P1–P7. No owner data was opened.  
**Decision boundary:** No migration, schema-version change, new table, column, or enum is authorised.

## Verdict table

| Property | Verdict | Existing evidence | Missing condition | Cheapest change and cost |
|---|---|---|---|---|
| P1 Completeness | **PARTIAL** | `reconcile.ts` computes a three-valued verdict and zero tolerance; `statements.close_state` is the existing period checkpoint. | No persisted account-period assessment can distinguish every covered, gapped, and unexamined period while retaining evidence lineage. | The cheap mapping `no row → unexamined`, `open → gapped`, and closed state → covered costs one shared projection helper, but it is rejected: a known gap has no honest mandatory statement balances, and a statement cannot identify superseded evidence. The minimum honest closure costs a Contract 06/spec decision, a migration for typed versioned coverage evidence, and an account-period scope extension to `reconcile.ts`. |
| P2 Idempotence | **SATISFIED for registered channels** | Structural source-event uniqueness and conflict-ignoring insert/read-back; file and chat branches have tests. | No gap in the current channel semantics. Future readers must use the registry rather than invent another mechanism. | No change. Preserve the existing four idempotency mechanisms. |
| P3 Provenance | **PARTIAL** | Canonical transactions can reference `source_events`; source events retain retrieval time, content hash, and document reference; document pointers reference source events. | `statements` cannot name a source event or indexed document. The transaction foreign key is nullable, so the schema does not guarantee provenance for every stored figure. | Adding an untyped reference to `audit_log.detail` is cheap but rejected because it creates a shadow schema. Honest closure costs typed foreign keys and mandatory provenance rules, which require a migration and contract approval. |
| P4 Monotonic trust | **PARTIAL** | Canonical transactions support supersession and correction links; promotion is explicit, atomic, and separately audited. | The owner grammar cannot yet submit a correction event. A statement cannot identify which evidence justified closure, so tombstoning later evidence cannot reliably invalidate coverage. | Extending `dailyCapture.ts` with a candidate-only correction shape is a small engineering change. Closing statement-evidence supersession still costs the same typed, versioned coverage relationship blocked under P1/P3. |
| P5 Owner input is evidence, not authority | **SATISFIED for the existing movement grammar** | Owner replies append at S2, use a registered candidate-only channel, parse deterministically, create candidates with `approved: false`, and require the separate promotion path. | The new statement-reference, correction, and empty-period shapes are not yet part of the closed grammar. | Extend `dailyCapture.ts` and its consumer additively. Cost: grammar, bilingual closed strings, typed refusals, staging types, and tests. No new prompt, writer, channel, or approval path. |

## P1 — Completeness

**Verdict: PARTIAL.**

Existing computation:

- `src/server/ingest/reconcile.ts:135-174` defines the full report and exact three-valued verdict.
- `src/server/ingest/reconcile.ts:302-419` computes the report and preserves row-count precedence.
- `src/server/ingest/reconcile.ts:420-461` returns the report but performs no write.
- `.kiro/specs/transaction-capture-pipeline/design.md:261-267` identifies `statements.close_state` as the existing period checkpoint.
- `src/server/db/schema.ts:213-228` persists statement period and close state.

The existing tables cannot honestly satisfy the required coverage ledger:

1. `reconcile.ts:223-240` aggregates the whole transaction store, excluding only `superseded`. It does not scope the SQL side to an account and bounded period, and it includes pending and void rows.
2. `reconcile.ts:313-325` gives the per-account side only a lower date bound. There is no upper period bound.
3. `statements` requires opening and closing balances. A period examined and found to have no statement is a known gap, but writing zero would fabricate financial facts.
4. `statements` has no source-event, document, hash, reconciliation-verdict, predecessor, or supersession field.
5. `document_index` can tombstone evidence, but it carries no account-period key and cannot identify the statement that depended on it.

### Rejected cheap representation

A pure projection could map:

- no statement row to `unexamined`;
- `close_state = open` to `gapped`;
- `balanced` or `exception_accepted` to `covered`.

This would make statement-close and coverage derive from one field. It still fails the required known-gap case because an `open` statement needs genuine mandatory balances, and it fails superseded-evidence invalidation because the statement cannot name its evidence. Implementing it would make the report look complete while collapsing cases the contract requires to remain distinct.

### Gap type

- **Engineering absence:** `reconcile.ts` lacks bounded account-period scope and canonical-status filtering.
- **Decision absence:** the minimum typed, versioned coverage/evidence relationship requires a migration, which this task explicitly withholds.

**Item 2 stop result:** Increment 8 cannot satisfy NIZAM-CONTINUITY-010 without a migration. The task instructs the implementation to say so and stop on this item rather than create a shadow schema.

## P2 — Idempotence

**Verdict: SATISFIED for every registered channel.**

Source evidence:

- `src/server/db/repositories/sourceEventsRepository.ts:9-17` states the structural uniqueness and changed-content behavior.
- `src/server/db/repositories/sourceEventsRepository.ts:122-145` makes the insert the decision with `ON CONFLICT ... DO NOTHING`, then reads the winner in the same transaction.
- `src/server/ingest/discovery.ts:109-114` distinguishes file `ref_and_digest` from chat `date_and_sequence` identity.

Test evidence:

- `src/server/ingest/discovery.test.ts:45-53` proves a second identical file capture returns `already_present` and leaves one source event.
- `src/server/ingest/discovery.test.ts:75-103` proves changed bytes under a content-independent chat key return `EVIDENCE_CONFLICT` and leave the stored row unchanged.
- `src/server/ingest/dailyCaptureConsumer.test.ts:164-184` proves identical owner replies are no-ops and changed bytes at the same date/sequence conflict before parsing.

Changed bytes on the file channel create a new artifact because the digest is part of the key. Changed bytes on the chat channel conflict because date and sequence are content-independent. No fifth idempotency mechanism is needed.

## P3 — Provenance

**Verdict: PARTIAL.**

Existing chain:

- `src/server/db/schema.ts:142-154` stores source-event retrieval time, channel identity, content hash, raw payload policy, parse state, and document reference.
- `src/server/db/schema.ts:152-179` allows a transaction to reference its `source_event_id`.
- `src/server/db/schema.ts:346-357` allows a document pointer to reference a source event and stores content hash plus indexed time.
- `src/server/ingest/promotion.test.ts:172-182` proves promotion preserves candidate provenance into the canonical row.

The chain is not universal. `transactions.source_event_id` is nullable, and `statements` has no evidence relationship. Therefore the repository cannot prove that every stored figure names its artifact, retrieval time, and hash.

### Rejected cheap representation

Encoding account, period, and evidence identifiers in `audit_log.detail`, `document_ref`, a channel name, or a naming convention would avoid DDL. It would also create an untyped secondary schema with no foreign key, uniqueness rule, repository contract, or supersession enforcement. That is not persisted provenance.

### Gap type

- **Engineering absence:** statement and coverage repositories have no provenance contract.
- **Decision absence:** adding typed mandatory relationships requires migration authority.

## P4 — Monotonic trust

**Verdict: PARTIAL.**

Existing safeguards:

- `src/server/db/schema.ts:153-179` records transaction source, verification level, superseded transaction, and audit version.
- `src/server/db/schema.ts:184-198` records a typed `correction` relationship without deleting the original.
- `src/server/ingest/promotion.test.ts:117-153` proves scheduler, confidence, streak, and repetition cannot trigger promotion.
- `src/server/ingest/promotion.test.ts:155-193` proves an owner-reviewed promotion is one atomic transition with an approval audit.
- `src/server/ingest/promotion.test.ts:195-217` proves a repeated promotion is idempotent and does not create another audit or notification.
- `src/server/ingest/promotion.test.ts:349-364` proves `approved: true` exists only in `promotion.ts` and no other production module imports the promotion function.

The current daily-capture grammar cannot submit a correction event. More importantly, statement closure is not linked to the evidence that justified it, so later tombstoning cannot reliably change the one authoritative coverage fact.

### Cheapest change

The transaction side can be advanced without migration by adding a correction reply shape to `dailyCapture.ts`, staging it with `approved: false`, and requiring a separate owner promotion that records a correction link. The statement side remains blocked on the P1/P3 typed evidence relationship.

## P5 — Owner input is evidence, not authority

**Verdict: SATISFIED for the existing movement grammar.**

Source evidence:

- `src/server/ingest/dailyCapture.ts:29-43` defines one owner-capture channel, grammar version, line bound, and explicit declination token.
- `src/server/ingest/dailyCapture.ts:169-181` creates a source event with channel, structural idempotency key, and content hash.
- `src/server/ingest/dailyCapture.ts:286-311` creates an uncleared candidate with `approved: false`.
- `src/server/ingest/dailyCapture.ts:328-349` refuses an over-bound reply whole rather than truncating it.
- `src/server/ingest/sourceRegistry.ts:99-116` registers `owner_daily_capture` as candidate-only.

Test evidence:

- `src/server/ingest/dailyCapture.test.ts:100-104` proves parsed movements are not approved or cleared.
- `src/server/ingest/dailyCapture.test.ts:370-406` proves repeated-looking input never auto-promotes and the module exports no canonical writer.
- `src/server/ingest/dailyCaptureConsumer.test.ts:61-64` proves the channel descriptor is candidate-only.
- `src/server/ingest/dailyCaptureConsumer.test.ts:379-388` proves the consumer cannot set approval or return canonical rows.
- `src/server/ingest/promotion.test.ts:117-153` proves only an explicit owner action can cross the promotion gate.

The requested statement-reference, correction, and closed-empty-period forms should extend this exact path. They do not justify a second prompt, second channel, or shortcut to canonical state.

## Source-shape decision absences

| Decision | Status | Consequence |
|---|---|---|
| D-X: whether the external PDF-to-CSV output becomes the statement adapter | Open | Its output is not an adopted NIZAM source. No engineering work may treat it as S1–S3. |
| D-Y: the real SMS corpus shape and ingestion order | Open | The container is a Google Doc, but message boundaries and adapter input shape are unconfirmed. No SMS reader should be written against an assumed row export. |
| Phase 1b: canonical state-use receipt | Unsigned | A figure cannot yet cite a canonical state version. This is separate from source provenance. |

These are decision absences. More implementation cannot close them.

## Already-built surfaces preserved

- `reconcile.ts` remains the only reconciliation computation.
- `agentReadiness.ts` remains the only readiness/coverage metric.
- `dailyCapture.ts` remains the only owner capture prompt and grammar.
- `document_index` remains the discovery checkpoint.
- `source_events` remains the structural evidence-idempotency boundary.
- `promotion.ts` remains the only path that can set `approved: true`.
