# Financial NIZAM Objective O1 — Financial Truth

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O1  
**Objective name:** Financial Truth  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 1 — Canonical evidence and transaction ledger  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT]** Financial NIZAM must maintain exactly one authoritative, evidence-backed, current financial state for every downstream calculation and recommendation.

**[FACT]** Financial truth must come from registered evidence and deterministic derivation, never conversational memory, convenience, or an LLM's arithmetic.

**[AGREED]** The practical outcome for the owner is simple: Financial NIZAM should be able to answer **“Where do I stand financially right now, how certain are we, and what evidence proves it?”** before attempting budgeting, spending advice, debt optimization, forecasting, or strategic recommendations.

**[AGREED]** This objective is the foundation underneath the Personal CFO / Wealth Operating System. If O1 is not satisfied, downstream agents may analyze but must not present unreconciled monetary conclusions as verified truth.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** The Financial NIZAM constitution already requires:

- evidence before interpretation;
- durable ledgers rather than conversational memory;
- reconciliation before optimization;
- explicit uncertainty;
- one canonical financial state;
- deterministic monetary truth;
- exactly one authoritative writer per canonical domain;
- freshness as part of truth;
- historical corrections through traceable revision rather than destructive mutation.

**[FACT]** The canonical data contract already defines `Account`, `Transaction`, `FinancialSnapshot`, `EvidenceRecord`, `AuditEvent`, `Merchant`, `Obligation`, `IncomeEvent`, `ForecastItem`, `DecisionRecord`, `Alert`, `FinancialGoal`, and budget objects. O1 must reuse these entities rather than invent parallel definitions.

**[FACT]** The transaction-ingestion contract already specifies the pipeline:

`RAW EVIDENCE → EVIDENCE RECORD → PARSE → NORMALIZE → IDENTITY/DEDUPE → RELATION MATCHING → CLASSIFICATION → LEDGER CANDIDATE → RECONCILIATION → AUDIT`

**[FACT]** Balance concepts such as current balance, available balance, statement balance, reconciled ledger balance, available credit, amount due, minimum due, and pending value are separate fields and must not be collapsed into one number.

### 2.2 New owner directions incorporated into this overhaul

**[AGREED]** The owner's trusted NIZAM operational boundary is VPS + Google Drive, with the VPS acting as replaceable compute/working storage and Google Drive acting as the durable evidence/recovery mirror for permitted artifacts.

**[AGREED]** HIMAYAH v2 will be proposed separately so ordinary NIZAM personal artifacts default to a readable trusted class inside that boundary, while passwords, tokens, API keys, private keys, `.env` values, and similar secrets remain excluded from Drive.

**[AGREED]** Financial statements, SMS transaction exports, merchant descriptions, transaction dates, amounts, balances, and other analytical financial context should remain readable in the approved Drive representation. Only identity/security fields that do not contribute to financial analysis should be sanitized where required by governing policy.

**[FACT]** Until HIMAYAH v2 is implemented and verified, the older runtime privacy contract remains operational; this document records the desired successor behavior rather than claiming that the repository already enforces it.

---

## 3. Scope

O1 governs:

1. financial evidence registration;
2. source provenance and lineage;
3. parsing and normalization;
4. account and transaction identity;
5. duplicate detection and idempotency;
6. pending/posted/reversed lifecycle handling;
7. transfer, card-payment, refund, installment, cash, fee, FX, and reversal relations;
8. account and statement reconciliation;
9. canonical current financial snapshot generation;
10. freshness, confidence, and unresolved-state exposure;
11. versioned corrections and supersession;
12. audit and proof that a downstream calculation used the correct state;
13. Drive evidence mirroring/read-back for permitted artifacts;
14. discovery of new/modified Drive financial evidence even when the owner does not mention it in conversation.

O1 does **not** decide:

- budget allocation;
- protected liquidity policy;
- safe-to-spend recommendations;
- debt prioritization;
- forecasting methodology;
- economic-regime classification;
- purchase approval or challenge behavior;
- long-term capital allocation.

Those consume O1 truth and are defined by later objectives.

---

## 4. Truth hierarchy

**[FACT]** O1 uses the following evidence order unless a superior governing contract states otherwise:

1. provider/statement evidence;
2. explicit human correction;
3. explicit user report;
4. deterministic extraction or calculation;
5. model-assisted extraction;
6. model inference.

**[FACT]** Lower-ranked evidence must never silently overwrite higher-ranked evidence.

**[AGREED]** Conflicting evidence creates an exception state. Financial NIZAM must preserve both claims, identify the conflict, request or retrieve additional evidence, and resolve through an auditable correction. It must never average competing balances to manufacture consistency.

---

## 5. Canonical-state lifecycle

### 5.1 Evidence discovery

**[AGREED]** O1 must support both event-driven and scheduled evidence discovery.

Inputs may include:

- bank statements;
- card statements;
- transaction exports;
- SMS transaction evidence;
- uploaded spreadsheets;
- registered account/ledger documents;
- user corrections;
- institution/provider records where an approved connector exists;
- approved Drive artifacts discovered by scheduled inspection.

**[AGREED]** The registered Financial NIZAM Drive scope should be inspected at least twice daily for new or changed evidence. Scheduled scanning is an evidence-discovery function, not permission to treat every discovered file as canonical truth.

### 5.2 Registration

Every source artifact must become an `EvidenceRecord` containing, at minimum:

- stable evidence ID;
- source type;
- source location/reference;
- ingestion timestamp;
- covered period where applicable;
- content hash/fingerprint;
- parser/version metadata;
- sensitivity/trust-boundary classification;
- quality/freshness status;
- relationship to superseded or duplicate evidence where applicable.

### 5.3 Parse and normalize

**[FACT]** Raw/source values must remain recoverable. Normalization may add normalized merchant names, account aliases, dates, direction, categories, relation types, and deterministic currency fields but must not destroy the source representation.

### 5.4 Identity and deduplication

**[FACT]** Provider transaction IDs are preferred when stable within institution/account scope.

**[FACT]** Fallback fingerprints must combine multiple stable fields and must not deduplicate only because two transactions share an amount and date.

**[FACT]** Re-importing identical evidence must be idempotent.

**[AGREED]** Duplicate detection must work across evidence channels where possible—for example, an SMS notification and later bank statement line may represent the same economic event and must not be counted twice.

### 5.5 Relation matching

O1 must explicitly model common financial relations:

- pending → posted;
- original → refund;
- original → reversal/chargeback;
- bank account → card payment;
- internal account → internal account transfer;
- purchase → installment liability/payment schedule;
- withdrawal → cash holding;
- parent transaction → split child transactions;
- foreign-currency purchase → settlement amount/rate/fee.

### 5.6 Reconciliation

For each account/cycle:

1. register authoritative balance or statement evidence with an as-of time;
2. confirm account identity and statement period;
3. match normalized transactions to source records;
4. apply pending/posted/reversal rules;
5. recompute the deterministic ledger balance;
6. compare with authoritative evidence under the currency-specific tolerance policy;
7. open an exception if mismatch remains;
8. close only with evidence and an audit event.

**[FACT]** Optimization from an unreconciled balance is prohibited by the existing contract.

### 5.7 Canonical snapshot

The authoritative writer produces a versioned `FinancialSnapshot` containing the current state references, as-of/freshness, unresolved items, calculation version, and policy version.

**[FACT]** Exactly one current snapshot is canonical for a given snapshot/calculation/policy version.

**[AGREED]** The conversational layer must retrieve this state rather than constructing its own balance from chat history.

---

## 6. Required truth states

O1 must preserve the difference between:

- `PENDING`;
- `POSTED`;
- `REVERSED`;
- `VOID`;
- expected/scheduled evidence not yet realized;
- stale evidence;
- conflicting evidence;
- unknown evidence;
- manually resolved evidence.

Reconciliation state must remain explicit using the existing lifecycle:

`UNSEEN → INGESTED → NORMALIZED → MATCHED → RECONCILED`

with exception branches:

`EXCEPTION` and `MANUALLY_RESOLVED`.

**[AGREED]** No user-facing financial number may be presented as current verified truth without an attached freshness and reconciliation state.

---

## 7. Single-writer and agent responsibilities

### Authoritative writer

**[FACT]** Exactly one component may mutate the canonical transaction/account/snapshot state for its domain.

### Evidence Ingestion Agent

May:

- discover evidence;
- register it;
- parse/normalize it;
- propose identities/categories/relations;
- open exceptions.

May not:

- overwrite canonical balances directly;
- decide unresolved conflicts by inference;
- perform financial actions.

### Reconciliation Agent

May:

- compare evidence and deterministic ledger results;
- resolve deterministic matches;
- open/close reconciliation exceptions when evidence satisfies policy;
- request human correction where required.

May not:

- average conflicts;
- hide stale evidence;
- optimize spending from unreconciled state.

### Audit Agent

Must independently verify:

- writer identity;
- evidence references;
- before/after state linkage;
- version metadata;
- approval reference when applicable;
- persistence receipt/read-back where an external mirror is expected.

### Conversational CFO

May explain O1 outputs.

Must not:

- calculate authoritative money independently;
- replace canonical state with conversational memory;
- hide uncertainty to give a faster answer.

---

## 8. Drive evidence/recovery behavior

**[AGREED]** Google Drive is the durable financial evidence/recovery mirror inside the owner-approved Trusted NIZAM Boundary, while the canonical computational writer remains governed by the NIZAM runtime architecture.

**[AGREED]** A Drive edit or newly uploaded statement is **evidence**, not an automatic canonical-state mutation.

Required flow:

`Drive discovery → EvidenceRecord → parse/normalize → dedupe/reconcile → canonical writer → approved derived record/mirror → Drive read-back receipt`

**[AGREED]** Readable financial context should be preserved in Drive-safe representations. Secrets such as credentials, passwords, tokens, API keys, private keys, OTPs/PINs, and `.env` values must never be stored there.

**[AGREED]** A persistence health check must detect important permitted records that exist only on VPS/local working storage and have not successfully landed in the durable mirror.

---

## 9. Correction and supersession model

**[FACT]** Historical financial truth must not be rewritten invisibly.

A correction must append an event that captures:

- previous record/event reference;
- new record/event reference;
- reason;
- actor;
- supporting evidence;
- timestamp;
- policy/schema version;
- approval reference when applicable.

**[FACT]** Model inference must be recorded separately from deterministic state.

**[AGREED]** If a later statement proves an earlier SMS extraction or categorization wrong, the system should retain the earlier observation and its correction rather than deleting the history.

---

## 10. Required proof on downstream use

**[AGREED]** A downstream Financial NIZAM recommendation must be able to prove that it used the correct truth state instead of merely claiming that it did.

At minimum, material outputs should carry references to:

- canonical snapshot ID/version;
- as-of time/freshness;
- reconciliation status;
- calculation/policy version;
- unresolved material exceptions;
- evidence references needed to reproduce the state;
- engine/run receipt for deterministic outputs.

**[INFERENCE]** This proof contract should later become a shared `calculation_receipt` or `state_use_receipt` schema consumed by O2+ objectives.

---

## 11. Failure behavior

### Missing source

**[FACT]** Mark state provisional or unknown; do not fabricate.

### Stale source

**[FACT]** Preserve the last known state but expose staleness and narrow any downstream claim accordingly.

### Conflicting balances

**[FACT]** Open an exception; never average.

### Unknown transaction

**[FACT]** Preserve transaction and evidence; classification remains UNKNOWN/REVIEW until resolved.

### Ambiguous transfer/card payment

**[FACT]** Hold unresolved rather than creating false spending or income.

### Drive mirror failure

**[AGREED]** Canonical processing may remain valid locally, but persistence status must show that the durable mirror has not landed. The system must retry under policy and surface unresolved recovery risk.

### Authoritative writer unavailable

**[FACT]** No alternate agent may silently become the writer. Processing may produce read-only analysis/proposals until the authoritative path is restored.

---

## 12. Acceptance criteria

O1 is **not complete** until all of the following are demonstrated with observed output:

1. exactly one canonical current-state writer exists;
2. authoritative money fields use integer milliunits and explicit currency;
3. re-importing the same evidence is idempotent;
4. legitimate same-amount/date transactions are not incorrectly collapsed;
5. SMS + statement representations of one transaction resolve to one economic event where evidence supports the match;
6. pending + posted states count once;
7. card payments and internal transfers do not create false expenses/income;
8. refunds/reversals retain linkage;
9. installment economics do not double count purchase and repayment;
10. FX retains original/settlement values, relevant rate/date, and fees when provided;
11. statement/account reconciliation can close exactly or within the explicit policy tolerance;
12. unresolved mismatches remain exceptions rather than being averaged or hidden;
13. current-state responses expose freshness and reconciliation status;
14. a stale historically correct balance is not represented as current;
15. manual corrections outrank model inference and remain auditable;
16. historical corrections are superseding/append-only;
17. downstream agents cannot bypass canonical state by using chat memory;
18. Drive-discovered evidence does not directly mutate canonical state without reconciliation;
19. approved Drive persistence produces a write receipt and read-back confirmation;
20. a failed Drive mirror is detectable and does not masquerade as successful persistence;
21. secret material is absent from Drive-safe financial artifacts;
22. a deliberate tamper test proves that verification detects a broken truth invariant.

---

## 13. Minimum test matrix

| Test family | Required proof |
|---|---|
| Evidence registration | same source receives stable identity/hash behavior |
| Idempotency | second identical import creates no duplicate economic transaction |
| Duplicate discrimination | legitimate same-value transactions remain separate |
| Pending/posted | one economic event counted once |
| Transfer | internal movement does not become income/expense |
| Card payment | payment reduces liability without duplicate spending |
| Refund/reversal | source relation retained and state corrected |
| Statement reconciliation | deterministic ledger agrees with authoritative statement or opens exception |
| Staleness | expired evidence cannot produce falsely current state |
| Manual correction | explicit user correction supersedes inference with audit trail |
| Single writer | unauthorized writer attempt fails |
| Drive discovery | new approved artifact becomes evidence without automatic canonical mutation |
| Drive persistence | mirror is accepted only after read-back |
| Privacy | secrets are rejected from Drive-safe artifacts |
| Tamper | changed invariant causes verification failure |

---

## 14. Migration strategy

**[FACT]** The existing roadmap requires new writers to run shadow/read-only until reconciliation and idempotency gates pass.

**[PROPOSED]** O1 migration sequence:

1. inventory existing evidence sources, transaction ledgers, account records, statements, Drive financial directories, and current writers;
2. identify the current authoritative path and all shadow/duplicate stores;
3. map existing records to canonical entities without deleting originals;
4. establish EvidenceRecord registration and content fingerprinting;
5. run ingestion/dedupe/relation logic in shadow mode;
6. reconcile historical periods against statement/provider evidence;
7. resolve material exceptions or explicitly carry them forward;
8. produce canonical snapshots in shadow mode;
9. run deterministic, integration, privacy-egress, failure-injection, and tamper tests;
10. compare new snapshot outputs with the prior authoritative path;
11. authorize cutover only after the owner-approved acceptance gate;
12. retain rollback to the previous writer without rewriting ledger history.

---

## 15. Required implementation artifacts

**[PROPOSED]** Exact paths must be chosen only after repository inspection; this design does not invent unverified paths.

The implementation phase should locate or create, under the correct owning contracts:

- canonical evidence registry/schema;
- transaction identity/dedupe engine;
- relation matcher;
- reconciliation engine;
- canonical snapshot builder;
- exception queue;
- correction/supersession event schema;
- state-use/calculation receipt;
- Drive discovery manifest;
- Drive mirror/read-back receipt;
- deterministic fixtures covering the O1 acceptance matrix;
- tamper test proving invalid state cannot pass verification.

---

## 16. Dependencies on later objectives

O1 provides truth to:

- O2 Financial Protection;
- O3 Decision Intelligence;
- O4 Capital Optimization;
- O5 Wealth Growth;
- O7 Regime Management;
- O8 Longitudinal Financial Intelligence;
- O9 Merchant & Behavioral Intelligence;
- O11 Evidence-Based Reasoning;
- O12 Forecast Accountability;
- O13 Income-Cycle Orchestration;
- O14 Credit & Liquidity Optimization;
- O15 Dynamic Resilience;
- O19 Adversarial Decision Protection;
- O28 Dynamic Materiality;
- O29 Computation Proof;
- O30/O32 Continuous Drive Discovery and Mirroring;
- O33+ HIMAYAH v2 / Trusted NIZAM Boundary.

**[FACT]** These objectives may enrich or consume O1 state, but none may silently redefine O1 monetary truth.

---

## 17. Explicit non-goals

O1 will not:

- decide whether a purchase is wise;
- calculate safe-to-spend policy;
- rank debts;
- create investment recommendations;
- infer causation from behavioral/recovery correlations;
- execute payments, transfers, borrowing, investing, account closures, credential actions, host/DNS mutations, commits, or pushes;
- mark a human-only decision field as complete;
- convert uncertain evidence into a convenient definite number.

---

## 18. Definition of done

**[FACT]** Architecture documentation alone does not satisfy O1.

O1 is done only when repository implementation has been inspected, the owning contracts are identified, the single-writer path is implemented or verified, the deterministic fixture suite passes, failure/tamper checks fail when deliberately broken, Drive persistence/read-back works under the approved HIMAYAH policy, and observed runtime output proves that a conversational Financial NIZAM answer can cite the exact canonical snapshot and evidence lineage it used.

Until then, status remains **DESIGNED / NOT RUNTIME-VERIFIED**.

---

## 19. Decision register entries opened by this document

### O1-D001 — Financial Truth remains the prerequisite

**[AGREED]** No optimization/recommendation engine may claim authoritative monetary output before current truth/freshness/reconciliation has been established.

### O1-D002 — Drive is durable evidence/recovery, not an alternate writer

**[AGREED]** Files discovered or edited in Drive enter through evidence ingestion and reconciliation; they do not directly overwrite canonical state.

### O1-D003 — Readable financial context is preserved

**[AGREED]** Approved Drive representations preserve merchant, transaction narrative, dates, values, balances, and relevant source context; only security/identity fields unnecessary for analysis are sanitized under policy.

### O1-D004 — New HIMAYAH v2 behavior requires governed supersession

**[AGREED]** `trusted_private` / trusted-boundary behavior is an approved design direction but must be implemented through formal privacy-policy change control rather than silent reinterpretation of the older strict-local contract.

---

## 20. Open items before implementation

**[MISSING]** Exact existing repository implementation paths and current writer components have not been inspected in this artifact-creation step.

**[MISSING]** PFOS v1.3 FINAL and the canonical LOCAL_FULL sibling are referenced by the governance pack but were not separately supplied in this turn; implementation must read them before changing runtime policy.

**[MISSING]** The exact Drive folder taxonomy and financial evidence root to govern O1 must be resolved from the configured NIZAM Drive structure rather than invented here.

**[MISSING]** HIMAYAH v2 schemas/enums are not yet implemented; O1 references the owner-approved target policy and must remain compatible with the currently verified runtime until that change is completed.

---

## 21. Next objective

The next document in the owner-approved overhaul sequence is:

**O2 — Financial Protection**  
Define how Financial NIZAM protects obligations, detects errors, prevents avoidable financial damage, manages exception severity, and responds when verified truth indicates emerging risk.
