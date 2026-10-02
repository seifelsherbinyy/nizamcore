# Requirements Document

Spec: `financial-snapshot-interface` · Workflow: design-first · Type: feature
Controller: `NIZAM-HERMES-FINANCIAL-CONSULTANT-013`
Selected journey: **“Are my financial facts current enough to use?”**

**Status: REQUIREMENTS_ACYCLIC_IDENTITY_ALIGNED_FOR_OWNER_REVIEW; NOT OWNER-ACCEPTED.**
`design.md` and `requirements.md` are both current review artifacts. Neither artifact is owner-accepted,
superseded, or pending re-derivation. The current review artifacts grant no implementation, migration,
execution, delivery, or live authority. `tasks.md` remains **SUPERSEDED_NON_EXECUTABLE** and is not modified
by this revision. No existing task may run. Task regeneration may occur only after the owner accepts both
current review artifacts.

This revision changes only `requirements.md` and appends one immutable planning-ledger event. This revision
does not edit `design.md` or `tasks.md`, allocate or apply a migration, implement behavior, run a test or
build, access a host or network, use real data, bind a transport, register a scheduler, call a model, commit,
push, deploy, or spend.

## Introduction

The Financial Snapshot Interface answers one bounded question: whether candidate-excluded canonical
financial facts are current enough for downstream use. The interface reads `finance.db` once into one
immutable bundle, derives stable canonical-state identity, constructs exactly five ordered identity-free
version payloads, hashes only those payloads into a Version_Set_Content_Digest, derives the version-set and
entry references from that digest, and then derives the time-relative Evaluation_Key. The interface runs
exactly three deterministic checks and persists one append-only graph through one repository unit of work.
The graph owns its status, version entries, digest-only canonical manifest, engine runs, output sets, facts,
Financial Snapshot, and shared State Use Receipt. Historical evidence resolves inside the graph rather than
against mutable live canonical rows.

The interface returns `CURRENT`, `LIMITED`, `STALE`, `UNKNOWN`, or one typed refusal. The interface does not
calculate a recommendation, invent money or policy, promote a candidate, add another canonical writer, call
a model, activate a transport, register a timer, write to Drive, or perform a live action. Missing evidence
remains missing. Stale evidence remains stale. A failed required check refuses the request and persists no
new graph.

### Governing clauses

- Financial NIZAM Objective O1 §§5.7, 6, 9, 10, and 11: canonical snapshot, truth states,
  supersession, downstream proof, and failure behavior.
- PFOS Contract 03 §§1 and 11: calculations before language and evidence-backed deterministic outputs.
- PFOS Contract 06 §§2–5 and 8: store isolation, exact integer-milliunit persistence, append-only
  migrations, and retention-policy boundaries.
- Repository Contract 6 §5.7, specifically I5.7.1–I5.7.5: the server candidate subset, mandatory
  candidate/canonical read separation, and promotion as the only transition to canonical state.
- PFOS Contract 12 §7.4: forward-only migrations and separately authorized pre-migration snapshot restore.
- PFOS Contract 14 §§5 and 11: deterministic-first routing, PFOS-only monetary authority, and unavailable
  financial state represented as unavailable rather than zero.
- PFOS Contract 15 §§2, 4, and 8: candidates remain engine-excluded and cannot be promoted by this path.
- `money-rules.md`: one safe-integer milliunit representation and no floating-point money.
- `drive-db.md`: `finance.db` is canonical; Drive remains a separately gated evidence and recovery mirror.

## Glossary

- **Financial_Snapshot_Interface**: The bounded feature specified by this document.
- **Authorized_Local_Caller**: A caller admitted by the Enclosing_Composition to request the
  `FINANCIAL_TRUTH_STATUS` Purpose. Admission grants no transport, host, or live authority.
- **Purpose**: The closed request classification. This feature accepts only `FINANCIAL_TRUTH_STATUS`.
- **Financial_Truth_Request**: A closed object containing exactly `asOf`, `generatedAt`, and `purpose`.
- **UTC_Instant**: A valid ISO 8601 instant with an explicit `Z` UTC designator.
- **Generated_At**: The caller-supplied UTC_Instant recording graph generation time.
- **Result**: The generic closed union `OK<T> | Refused` returned by every fallible boundary.
- **Refused**: The `REFUSED` branch containing exactly one Refusal_Code and no successful value.
- **Refusal_Code**: One member of the current design's closed refusal-code set.
- **Reason_Code**: One member of the current design's closed reason-code set.
- **Financial_Truth_Coordinator**: The component that parses a request, obtains one Canonical_Read_Bundle,
  resolves one Evaluation_Version_Set, derives an Evaluation_Key, runs Required_Engines, derives status,
  and delegates graph persistence or historical lookup to the Financial_Truth_Repository.
- **Financial_Truth_Status**: One of `CURRENT`, `LIMITED`, `STALE`, or `UNKNOWN`.
- **Canonical_Store**: The server-tier `finance.db` governed by PFOS Contract 06.
- **Canonical_Row**: A financial row admitted by the existing canonical predicate.
- **Candidate_Row**: The server subset defined by Repository Contract 6 I5.7.1 as
  `status = 'pending'` and `verification_level = 'unverified'`.
- **Canonical_State_Reader**: The read-only fallible adapter that materializes one candidate-excluded
  Canonical_Read_Bundle in one consistent Canonical_Store read transaction.
- **Canonical_Read_Bundle**: One immutable object containing materialized candidate-excluded values and one
  Canonical_Input_Manifest_Draft produced by the same read transaction.
- **Canonical_Input_Manifest_Draft**: The canonically ordered, typed digest-only description of the exact
  candidate-excluded rows used by a Canonical_Read_Bundle, together with schema head and candidate count.
- **Approved_Manifest_Schema**: The reviewed table, field, normalization, and ordering policy for
  financially consequential canonical content. This document does not select that policy.
- **Canonical_State_Version**: The exact lowercase SHA-256 content identity of approved, canonically encoded,
  candidate-excluded canonical content. Request times and candidate observations are excluded.
- **Canonical_Manifest**: The immutable graph-owned copy of the accepted manifest identity and metadata.
- **Canonical_Manifest_Entry**: A graph-owned immutable evidence row containing only evidence class,
  deterministic ordinal, source-row digest, and canonical-content digest.
- **Canonical_Evidence_Reference**: An Opaque_Reference that resolves to one Canonical_Manifest_Entry in the
  same Derived_Graph and never to a mutable live canonical row.
- **Required_Engine**: One member of `CANONICAL_ACCOUNT_STATE`, `STATEMENT_STATE`, or
  `RECONCILIATION_EVIDENCE`.
- **Required_Policy_Artifact**: One of exactly `MANIFEST_SCHEMA_POLICY` or `FRESHNESS_POLICY`, the two
  closed policy roles required by the current design.
- **Version_Artifact_Key**: One of exactly five closed roles: `ENGINE:CANONICAL_ACCOUNT_STATE`,
  `ENGINE:STATEMENT_STATE`, `ENGINE:RECONCILIATION_EVIDENCE`, `POLICY:MANIFEST_SCHEMA_POLICY`, or
  `POLICY:FRESHNESS_POLICY`.
- **Closed_Entry_Role**: The fixed identity tag `EVALUATION_VERSION_ENTRY` used only when deriving an
  Evaluation_Version_Entry reference.
- **Calculation_Version**: A closed version reference for one Required_Engine implementation.
- **Policy_Version**: A closed version reference for one Required_Policy_Artifact.
- **Version_Entry_State**: Either `KNOWN` with one resolvable Calculation_Version or Policy_Version reference,
  or `MISSING` with a null version reference.
- **Evaluation_Version_Entry_Payload**: One identity-free value containing only ordinal,
  Version_Artifact_Key, artifact class, and Version_Entry_State with the associated version reference.
  Evaluation_Version_Entry_Payload contains no Evaluation_Version_Set reference, Evaluation_Version_Entry
  reference, Evaluation_Key, or graph-local identity.
- **Version_Set_Content_Digest**: The exact lowercase SHA-256 digest of the canonical encoding of exactly five
  ordered Evaluation_Version_Entry_Payload values and no derived references or graph-local identities.
- **Evaluation_Version_Entry**: One immutable ordered Evaluation_Version_Entry_Payload plus an entry
  Opaque_Reference and the owning Evaluation_Version_Set Opaque_Reference. The two references are derived
  after Version_Set_Content_Digest and do not participate in payload hashing.
- **Evaluation_Version_Set**: One immutable content-addressed canonical ordered set containing exactly five
  Evaluation_Version_Entry_Payload values and five matching Evaluation_Version_Entries for the three fixed
  Required_Engine roles followed by `MANIFEST_SCHEMA_POLICY` and `FRESHNESS_POLICY`.
- **Evaluation_Version_Set_Registry**: The fallible component that resolves and validates the complete
  Evaluation_Version_Set before required-engine execution.
- **Evaluation_Key**: The exact lowercase SHA-256 identity derived only from Canonical_State_Version,
  Version_Set_Content_Digest, Purpose, caller-supplied `asOf`, and caller-supplied `generatedAt`. The
  Evaluation_Key excludes Evaluation_Version_Set and Evaluation_Version_Entry references.
- **Opaque_Reference**: A structurally closed pair containing one Reference_Target and one exact lowercase
  SHA-256 digest.
- **Reference_Target**: One member of the current design's closed reference-target set.
- **Required_Engine_Registry**: The fallible registry that runs exactly the three Required_Engines over one
  Canonical_Read_Bundle.
- **Engine_Run**: A graph-owned record containing Required_Engine identity, matching version-set entry,
  Evaluation_Key, Canonical_State_Version, status, evidence, output ownership, and closed reason.
- **Engine_Run_Status**: One of `PASS`, `DEGRADED`, `FAILED`, or `MISSING`.
- **Output_Set**: The zero-or-one ordered collection of fact references owned by one Engine_Run.
- **Deterministic_Output_Fact**: A fact owned by one Output_Set and Engine_Run, with a closed fact kind,
  deterministic ordinal, exact safe-integer milliunit amount where monetary, currency, and injected time.
- **Financial_Snapshot**: The append-only, versioned, reference-only state record defined by the final
  corrected design.
- **State_Use_Receipt**: The shared amount-free proof record naming stored status, snapshot, manifest,
  version set, engine runs, evidence, freshness, reconciliation, and unresolved items.
- **Freshness_Policy_Port**: The fallible injected policy boundary that classifies account evidence using
  the matching policy entry from the Evaluation_Version_Set.
- **Freshness_State**: One of `FRESH`, `LIMITED`, `STALE`, or `UNKNOWN`.
- **Reconciliation_State**: One of `RECONCILED`, `RECONCILED_WITH_REPORTED_DISAGREEMENT`,
  `UNEXPLAINED_RESIDUAL`, `NOT_RECONCILED`, or `UNKNOWN`.
- **Materiality_State**: One of `MATERIAL`, `NON_MATERIAL`, or `UNKNOWN`.
- **Completion_Status**: One of `COMPLETE` or `PARTIAL`.
- **Derived_Graph**: The append-only graph containing immutable stored status, Evaluation_Version_Set,
  Canonical_Manifest, Engine_Runs, Output_Sets, Deterministic_Output_Facts, one Financial_Snapshot, one
  State_Use_Receipt, and all child rows for one Evaluation_Key.
- **Verified_Derived_Graph**: A complete Derived_Graph that passed independent value-for-value read-back.
- **Financial_Truth_Repository**: The sole fallible unit-of-work owner for every Derived_Graph write,
  validation, commit, read-back, replay, and historical lookup.
- **Historical_Graph_Lookup**: A lookup that returns a prior Verified_Derived_Graph and immutable stored
  Financial_Truth_Status without re-deriving currentness.
- **Synthetic_Fixture_Capability**: An unforgeable test-profile capability constructible only by the
  Synthetic_Fixture_Factory.
- **Synthetic_Fixture_Factory**: The test-only factory and build profile that creates
  Synthetic_Fixture_Capability and synthetic stores.
- **Synthetic_Shape_Guard**: A defense-in-depth scanner for prohibited content shapes and deployment
  particulars. A passing scan does not prove synthetic provenance.
- **Synthetic_Verification_Profile**: The test build profile that omits production canonical-store,
  transport, provider, Drive, model, and host adapters.
- **Enclosing_Composition**: The separately governed local runtime composition that admits callers and may
  leave the Financial_Snapshot_Interface unbound.
- **Migration_Planner**: The implementation-time component that reads the actual migration frontier before
  selecting an additive migration number.
- **Derived_Persistence_Migration**: The additive migration for reviewed Derived_Graph tables and guards.
- **Migrator**: The existing PFOS Contract 06 migration executor and checksum verifier.
- **Downstream_Adapter**: A separately approved consumer that reads a Verified_Derived_Graph by reference.
- **Task_Board**: `.kiro/specs/financial-snapshot-interface/tasks.md`.

## Requirements

### Requirement 1: Validate the closed request and return one result

**User Story:** As the owner, I want one evidence-backed currentness result, so that downstream use starts
from an explicit and auditable decision.

#### Acceptance Criteria

1. WHEN an Authorized_Local_Caller submits a currentness request, THE Financial_Snapshot_Interface SHALL
   require caller-supplied `asOf`, `generatedAt`, and `purpose` fields.
2. THE Financial_Truth_Request parser SHALL accept exactly the keys `asOf`, `generatedAt`, and `purpose`.
3. IF request parsing finds an unknown key, including an effect, tool, action, or transport key, THEN THE
   Financial_Truth_Request parser SHALL return `Refused(INVALID_REQUEST)` before any canonical read.
4. IF request parsing finds a missing field, invalid UTC_Instant, or malformed structure, THEN THE
   Financial_Truth_Request parser SHALL return `Refused(INVALID_REQUEST)` before any canonical read.
5. WHEN the Financial_Truth_Coordinator returns `OK`, THE Financial_Truth_Coordinator SHALL bind one
   Financial_Truth_Status and one Verified_Derived_Graph to the request `asOf`, `generatedAt`, Purpose, and
   Evaluation_Key.
6. WHEN the Financial_Truth_Coordinator returns `OK`, THE Verified_Derived_Graph SHALL contain exactly one
   Financial_Snapshot and exactly one State_Use_Receipt.
7. THE Financial_Snapshot_Interface SHALL accept only the `FINANCIAL_TRUTH_STATUS` Purpose.
8. IF the request Purpose is outside `FINANCIAL_TRUTH_STATUS`, THEN THE Financial_Truth_Request parser SHALL
   return `Refused(UNSUPPORTED_PURPOSE)` before any canonical read.
9. IF the Enclosing_Composition does not admit the caller, THEN THE Financial_Snapshot_Interface SHALL
   return `Refused(UNAUTHORIZED_CALLER)` before any canonical read.
10. IF any fallible boundary returns Refused, THEN THE Financial_Truth_Coordinator SHALL propagate the same
    closed Refusal_Code without a successful fallback value.
11. WHEN Historical_Graph_Lookup returns a Verified_Derived_Graph, THE Financial_Truth_Repository SHALL
    return the original Graph identity, Evaluation_Key, Canonical_State_Version, Evaluation_Version_Set
    reference, Purpose, `asOf`, `generatedAt`, stored Financial_Truth_Status, Financial_Snapshot,
    State_Use_Receipt, and `READ_BACK_VERIFIED` verification state.
12. WHEN Historical_Graph_Lookup returns a Verified_Derived_Graph, THE Financial_Truth_Coordinator SHALL
    identify the result as historical evidence without re-deriving or relabelling Financial_Truth_Status.
13. WHEN an Authorized_Local_Caller requests currentness with a changed Canonical_State_Version,
    Version_Set_Content_Digest, Purpose, `asOf`, or `generatedAt`, THE Financial_Truth_Coordinator SHALL
    rerun the required policy and engine path.
14. WHEN Historical_Graph_Lookup finds no Verified_Derived_Graph, THE Financial_Truth_Repository SHALL return
    `OK(null)`.
15. IF no Verified_Derived_Graph exists, THEN THE Financial_Truth_Coordinator SHALL return no substitute
    from conversation, Drive, cache, mutable live-row inference, prior status, or unverified graph.
16. IF complete graph verification fails, THEN THE Financial_Truth_Coordinator SHALL return one Refused
    result and no built result.
17. IF the Financial_Truth_Coordinator returns Refused, THEN THE Financial_Truth_Coordinator SHALL return no
    fallback Financial_Truth_Status, Financial_Snapshot, State_Use_Receipt, or Derived_Graph.
18. WHEN the Financial_Truth_Request parser returns OK, THE Financial_Truth_Request parser SHALL return
    `asOf` and `generatedAt` as valid UTC_Instants ending in `Z` and Purpose as
    `FINANCIAL_TRUTH_STATUS`.
19. WHEN any Financial_Snapshot_Interface call completes, THE Financial_Snapshot_Interface SHALL return
    exactly one Result branch containing either one successful value or one Refused value.
20. WHEN the Enclosing_Composition receives a currentness call, THE Enclosing_Composition SHALL complete
    caller admission before invoking the Financial_Truth_Request parser.
21. WHEN caller admission succeeds, THE Financial_Truth_Request parser SHALL complete exact-key, structure,
    UTC_Instant, and Purpose validation before the Financial_Truth_Coordinator invokes the
    Canonical_State_Reader.
22. IF caller admission fails, THEN THE Enclosing_Composition SHALL return
    `Refused(UNAUTHORIZED_CALLER)` without invoking the Financial_Truth_Request parser or any downstream
    boundary.
23. WHEN Historical_Graph_Lookup returns a Verified_Derived_Graph, THE Financial_Truth_Repository SHALL
    return every graph-owned child and collection in stored canonical order together with the complete
    identity and immutable Financial_Truth_Status named in criterion 1.11.
24. WHEN any member of the complete evaluation identity differs from a prior evaluation, THE
    Financial_Truth_Coordinator SHALL treat the request as a new evaluation rather than an exact retry.

### Requirement 2: Materialize one candidate-excluded canonical bundle

**User Story:** As a deterministic financial component, I want one immutable canonical bundle and stable
state identity, so that candidates, request time, and read order cannot alter the facts used.

#### Acceptance Criteria

1. WHEN the Canonical_State_Reader reads the Canonical_Store, THE Canonical_State_Reader SHALL materialize
   one immutable Canonical_Read_Bundle in one consistent read transaction.
2. WHILE the consistent read transaction remains open, THE Canonical_State_Reader SHALL materialize every
   required candidate-excluded value and the complete Canonical_Input_Manifest_Draft.
3. THE Canonical_State_Reader SHALL finalize the Canonical_Read_Bundle and Canonical_State_Version before the
   consistent read transaction closes.
4. THE Canonical_State_Reader SHALL encode Approved_Manifest_Schema content using the schema-defined total
   order across evidence classes, source rows, fields, and normalized values.
5. THE Canonical_State_Reader SHALL derive Canonical_State_Version without repository return order,
   `asOf`, `generatedAt`, Candidate_Row content, candidate count, or candidate observation metadata.
6. WHEN two candidate-excluded read sets contain identical Approved_Manifest_Schema content, THE
   Canonical_State_Reader SHALL produce the same Canonical_State_Version.
7. WHEN any financially consequential Approved_Manifest_Schema field changes, THE Canonical_State_Reader
   SHALL produce a different Canonical_State_Version.
8. WHEN Candidate_Row additions, removals, or content changes occur without a Canonical_Row change, THE
   Financial_Snapshot_Interface SHALL preserve canonical references, Canonical_State_Version, engine inputs,
   deterministic outputs, Financial_Snapshot, and State_Use_Receipt.
9. WHEN Candidate_Row additions, removals, or content changes occur without a Canonical_Row change, THE
   Canonical_State_Reader SHALL permit only candidate observation metadata to differ.
10. WHEN the Canonical_State_Reader observes Candidate_Rows, THE Canonical_State_Reader SHALL record the exact
    candidate count and candidate rows included equal to zero.
11. THE Canonical_State_Reader SHALL apply Repository Contract 6 I5.7.1–I5.7.5 to every canonical read
    without a caller-configurable bypass.
12. IF a Candidate_Row reaches a canonical reference, materialized value, or engine input, THEN THE
    Financial_Truth_Coordinator SHALL return `Refused(CANDIDATE_FENCE_FAILED)` before calculation or write.
13. IF Approved_Manifest_Schema is unavailable, THEN THE Canonical_State_Reader SHALL return
    `Refused(MANIFEST_POLICY_MISSING)` without creating a derived artifact.
14. IF the Canonical_Store read fails, THEN THE Canonical_State_Reader SHALL return
    `Refused(CANONICAL_READ_FAILED)` without creating a derived artifact.
15. IF the Canonical_Store read fails, THEN THE Financial_Truth_Coordinator SHALL return no substitute from
    Drive, cache, prior snapshot data, or an unverified graph.
16. THE Canonical_State_Reader SHALL perform zero canonical insert, update, delete, promotion, or
    reconciliation mutation operations.
17. THE Required_Engine_Registry SHALL consume only the immutable Canonical_Read_Bundle without an ambient
    repository reread.
18. WHEN an adapter requires a canonical reread, THE adapter SHALL reread every required row in one new
    consistent transaction and recompute the complete digest and ordered reference collections.
19. WHEN the adapter completes the canonical reread, THE adapter SHALL compare the recomputed digest and
    ordered reference collections with the original Canonical_Read_Bundle before calculation.
20. IF the recomputed digest or ordered reference collections differ, THEN THE adapter SHALL return
    `Refused(CANONICAL_REREAD_CONFLICT)` before calculation or persistence.
21. IF the Canonical_State_Reader cannot materialize every required candidate-excluded value and the complete
    Canonical_Input_Manifest_Draft before the consistent read transaction closes, THEN THE
    Canonical_State_Reader SHALL return Refused without returning a partial Canonical_Read_Bundle.
22. WHEN an adapter performs a canonical reread, THE adapter SHALL reread the complete schema-defined row
    set and compare the full Canonical_State_Version and every canonically ordered reference collection.
23. WHILE the consistent read transaction remains open, THE Canonical_State_Reader SHALL derive the exact
    Candidate_Row count from the same transaction and set candidate rows included to zero.
24. IF Canonical_State_Version, candidate count, any required value, or any
    Canonical_Input_Manifest_Draft entry cannot be finalized before the consistent read transaction closes,
    THEN THE Canonical_State_Reader SHALL return Refused without returning a partial or mutable
    Canonical_Read_Bundle.
25. IF an adapter reread fails, returns a partial row set, closes before comparison completes, or cannot
    reproduce every ordered reference collection, THEN THE adapter SHALL return
    `Refused(CANONICAL_REREAD_CONFLICT)` before calculation or persistence.
26. WHEN the Canonical_State_Reader returns OK, THE Canonical_Read_Bundle SHALL contain the finalized
    Canonical_State_Version, exact candidate count, zero included candidate rows, complete manifest draft,
    and every required candidate-excluded value from the same closed transaction.

### Requirement 3: Resolve one version set and record exact deterministic outputs

**User Story:** As an auditor, I want each relied-on fact to resolve through one required engine and one
version-set entry, so that missing versions and ambiguous facts cannot appear complete.

#### Acceptance Criteria

1. WHEN the Required_Engine_Registry evaluates a request, THE Required_Engine_Registry SHALL build every
   engine input from the same Canonical_Read_Bundle.
2. THE Evaluation_Version_Set_Registry SHALL resolve one immutable canonically ordered
   Evaluation_Version_Set containing exactly five identity-free Evaluation_Version_Entry_Payload values and
   exactly five matching Evaluation_Version_Entries: the three Required_Engine roles in canonical
   Required_Engine order, followed by `MANIFEST_SCHEMA_POLICY` and `FRESHNESS_POLICY` in canonical policy
   order.
3. THE Evaluation_Version_Set SHALL represent each Evaluation_Version_Entry_Payload Version_Entry_State as
   either `KNOWN` with exactly one class-matching resolvable Calculation_Version or Policy_Version reference,
   or `MISSING` with a null version reference and the artifact class required by the Version_Artifact_Key.
4. IF the Evaluation_Version_Set contains a duplicate, omission, extra or runtime-added role, wrong class,
   wrong order, malformed payload or entry, payload-entry mismatch, or unresolved `KNOWN` reference, THEN THE
   Evaluation_Version_Set_Registry SHALL return `Refused(VERSION_SET_VALIDATION_FAILED)` before engine
   execution.
5. THE Financial_Truth_Repository SHALL persist or exactly reuse the Evaluation_Version_Set and every
   Evaluation_Version_Entry as immutable content-addressed rows within the Derived_Graph transaction.
6. WHEN the Required_Engine_Registry evaluates `FINANCIAL_TRUTH_STATUS`, THE Required_Engine_Registry SHALL
   record exactly one Engine_Run for each Required_Engine in canonical Required_Engine order.
7. THE Financial_Truth_Repository SHALL resolve each Engine_Run version-entry reference to the unique
   matching engine entry in the same Evaluation_Version_Set.
8. THE Financial_Truth_Repository SHALL require each Engine_Run version state to equal the resolved
   Evaluation_Version_Entry field-for-field.
9. IF a Required_Engine lacks canonical inputs or an approved adapter, THEN THE Required_Engine_Registry
   SHALL record `MISSING`, one closed Reason_Code, a null Output_Set reference, and zero facts.
10. WHEN the Financial_Truth_Repository reads a valid monetary fact, THE Financial_Truth_Repository SHALL
    return the exact signed safe-integer milliunit amount submitted for persistence.
11. WHEN the Financial_Truth_Repository reads a valid monetary fact, THE Financial_Truth_Repository SHALL
    return the exact submitted three-uppercase-ASCII-letter currency.
12. IF a monetary fact contains an amount outside the existing safe-integer money boundary, THEN THE
    Financial_Truth_Repository SHALL return `Refused(REFERENCE_VALIDATION_FAILED)` before preparing SQL.
13. IF a monetary fact contains an invalid currency, THEN THE Financial_Truth_Repository SHALL return
    `Refused(REFERENCE_VALIDATION_FAILED)` before preparing SQL.
14. IF a monetary fact is rejected, THEN THE Financial_Truth_Repository SHALL preserve every previously
    persisted row unchanged.
15. THE Required_Engine_Registry and Financial_Truth_Repository SHALL use the existing money implementation
    as the exclusive monetary representation and arithmetic path.
16. IF reconciliation inputs or mappings are absent, THEN THE Required_Engine_Registry SHALL record
    `RECONCILIATION_EVIDENCE` as `MISSING` without producing a clean reconciliation result.
17. IF any Required_Engine has status `FAILED`, THEN THE Financial_Truth_Coordinator SHALL return
    `Refused(REQUIRED_ENGINE_FAILED)` without persisting a Derived_Graph.
18. IF any Required_Engine boundary returns Refused, THEN THE Financial_Truth_Coordinator SHALL propagate the
    same closed Refusal_Code without persisting a Derived_Graph.
19. WHEN an Engine_Run has zero facts, THE Financial_Truth_Repository SHALL persist zero Output_Sets for the
    Engine_Run.
20. WHEN an Engine_Run has one or more facts, THE Financial_Truth_Repository SHALL persist exactly one
    Output_Set owned by the Engine_Run.
21. WHEN an Output_Set contains fact references, THE Financial_Truth_Repository SHALL persist the references
    in a gap-free deterministic ordinal sequence using the canonical ordinal base defined by the closed
    Output_Set schema.
22. WHEN an Output_Set declares a fact reference, THE Financial_Truth_Repository SHALL persist exactly one
    matching fact owned by the same Output_Set and Engine_Run at the declared ordinal.
23. WHEN the Required_Engine_Registry evaluates `FINANCIAL_TRUTH_STATUS`, THE Required_Engine_Registry SHALL
    create zero Engine_Runs for safe-to-spend, forecast, budget, obligation protection, net worth, or any
    other downstream engine.
24. IF an Engine_Run is `MISSING`, `DEGRADED`, or `FAILED`, THEN THE Financial_Snapshot_Interface SHALL
    preserve the Engine_Run_Status without substituting zero, a prior fact, or a model estimate.
25. IF any Evaluation_Version_Entry_Payload, Evaluation_Version_Entry, Engine_Run, Output_Set, or
    Deterministic_Output_Fact fails structural, ownership, ordinal, money, currency, or reference validation,
    THEN THE Financial_Truth_Repository SHALL reject the complete attempted Derived_Graph before preparing
    SQL and preserve every previously persisted row unchanged.
26. THE Evaluation_Version_Entry_Payload SHALL contain only ordinal, Version_Artifact_Key, artifact class,
    and Version_Entry_State with the associated Calculation_Version or Policy_Version reference.
27. THE Evaluation_Version_Set_Registry SHALL canonically encode and hash exactly the five ordered
    Evaluation_Version_Entry_Payload values to produce Version_Set_Content_Digest.
28. THE Version_Set_Content_Digest input SHALL exclude every Evaluation_Version_Entry reference,
    Evaluation_Version_Set reference, Evaluation_Key, Derived_Graph identity, and graph-local reference.
29. THE Evaluation_Version_Set Opaque_Reference digest SHALL equal Version_Set_Content_Digest.
30. THE Evaluation_Version_Set_Registry SHALL derive each Evaluation_Version_Entry Opaque_Reference digest
    only from Version_Set_Content_Digest, the payload ordinal, Closed_Entry_Role, and Version_Artifact_Key.
31. THE Evaluation_Version_Set_Registry SHALL require each Evaluation_Version_Entry to match the
    Evaluation_Version_Entry_Payload at the same ordinal field-for-field.
32. IF any runtime path attempts to add, remove, replace, or reorder a Version_Artifact_Key, THEN THE
    Evaluation_Version_Set_Registry SHALL return `Refused(VERSION_SET_VALIDATION_FAILED)` before engine
    execution.
33. WHEN a change to the five-role Version_Artifact_Key set is proposed, THE planning workflow SHALL require
    reviewed revisions to both `design.md` and `requirements.md` before the changed set enters a runtime or
    persisted schema.
34. IF an approved artifact record or digest for a fixed Version_Artifact_Key is unavailable, THEN THE
    Evaluation_Version_Set_Registry SHALL preserve the corresponding Version_Entry_State as `MISSING`
    without inventing artifact content, a digest, a policy value, or a version reference.
35. WHEN the Evaluation_Version_Set_Registry resolves a version set, THE
    Evaluation_Version_Set_Registry SHALL complete derivation in this order: construct exactly five
    identity-free payloads, derive Version_Set_Content_Digest from those payloads, derive the
    Evaluation_Version_Set reference, derive exactly five Evaluation_Version_Entry references, and only then
    permit Evaluation_Key or graph-local identity derivation.
36. THE Evaluation_Version_Set_Registry SHALL derive exactly one payload and exactly one entry for each fixed
    Version_Artifact_Key and zero payloads or entries for any other role.
37. WHEN an Engine_Run has one or more facts, THE Financial_Truth_Repository SHALL require the Engine_Run
    fact references, Output_Set fact references, and persisted Deterministic_Output_Facts to have equal
    cardinality and identical gap-free ordinal order.
38. WHEN the Financial_Truth_Repository persists a monetary Deterministic_Output_Fact, THE
    Financial_Truth_Repository SHALL bind the validated safe-integer milliunit amount directly as an integer
    and the validated currency directly as three uppercase ASCII letters without floating-point, textual
    numeric, or lossy conversion.
39. THE Financial_Truth_Coordinator SHALL derive Evaluation_Key only after validating that every
    Evaluation_Key input is independent of Evaluation_Key, every graph-local identity, every
    Evaluation_Version_Set reference, and every Evaluation_Version_Entry reference.
40. IF Version_Set_Content_Digest changes while Canonical_State_Version, Purpose, `asOf`, and `generatedAt`
    remain unchanged, THEN THE Financial_Truth_Coordinator SHALL derive a different Evaluation_Key.

### Requirement 4: Persist graph-owned evidence and a reference-only snapshot

**User Story:** As a downstream consumer, I want immutable historical evidence and a partial-capable snapshot,
so that later canonical corrections cannot break or rewrite prior proof.

#### Acceptance Criteria

1. WHEN the Financial_Truth_Coordinator constructs a Derived_Graph, THE Financial_Truth_Coordinator SHALL
   copy the Canonical_Input_Manifest_Draft into one graph-owned Canonical_Manifest.
2. THE Canonical_Manifest SHALL contain Canonical_State_Version, schema migration head, candidate observation
   metadata, and canonically ordered Canonical_Manifest_Entries.
3. THE Financial_Truth_Repository SHALL resolve every Canonical_Evidence_Reference to exactly one
   Canonical_Manifest_Entry in the same Derived_Graph.
4. THE Financial_Truth_Repository SHALL resolve historical Canonical_Evidence_References without reading a
   mutable live canonical row.
5. THE Canonical_Manifest_Entry SHALL contain only evidence class, deterministic ordinal, source-row digest,
   and canonical-content digest.
6. THE Canonical_Manifest and Canonical_Manifest_Entry SHALL contain zero raw canonical values, account
   names, payees, source text, personal identifiers, or sensitive text.
7. WHEN a live canonical row changes, is superseded, or is removed after graph commit, THE
   Financial_Truth_Repository SHALL preserve historical Canonical_Evidence_Reference resolution unchanged.
8. WHEN the Financial_Truth_Coordinator builds a Financial_Snapshot, THE Financial_Snapshot SHALL populate
   each field from the design-defined closed domain, nullable reference, or permitted empty collection.
9. THE Financial_Snapshot SHALL represent every monetary field as a Deterministic_Output_Fact reference or
   null.
10. IF a downstream monetary field lacks a deterministic fact in this feature, THEN THE Financial_Snapshot
    SHALL use null without creating a downstream Engine_Run.
11. WHEN the Financial_Snapshot contains unresolved items, THE Financial_Snapshot SHALL deduplicate and order
    the items canonically by closed kind and Opaque_Reference.
12. IF no approved policy classifies an unresolved item, THEN THE Financial_Snapshot SHALL assign
    Materiality_State `UNKNOWN`.
13. WHEN a prior Verified_Derived_Graph exists at Financial_Snapshot construction time, THE
    Financial_Snapshot SHALL reference the latest prior verified Financial_Snapshot as predecessor.
14. IF a Financial_Snapshot reference is missing, ambiguous, wrong-target, cross-graph, version-mismatched,
    or identity-mismatched, THEN THE Financial_Truth_Repository SHALL return
    `Refused(REFERENCE_VALIDATION_FAILED)` before acknowledging success.
15. WHEN no prior Verified_Derived_Graph exists, THE Financial_Snapshot SHALL use null as predecessor.
16. WHEN a successor Financial_Snapshot is persisted, THE Financial_Truth_Repository SHALL preserve every
    prior Financial_Snapshot unchanged.
17. THE Financial_Snapshot SHALL record Evaluation_Key, `asOf`, Canonical_State_Version,
    Evaluation_Version_Set reference, and Canonical_Manifest reference from the same Derived_Graph.
18. IF the Financial_Truth_Coordinator constructs other than exactly one graph-owned Canonical_Manifest,
    THEN THE Financial_Truth_Repository SHALL reject the complete attempted Derived_Graph.
19. IF the graph-owned Canonical_Manifest_Entries differ in value, cardinality, or order from the complete
    Canonical_Input_Manifest_Draft entries, THEN THE Financial_Truth_Repository SHALL reject the complete
    attempted Derived_Graph.
20. IF any Financial_Snapshot field or reference fails closed-domain, ownership, identity, cardinality, or
    order validation, THEN THE Financial_Truth_Repository SHALL reject the complete attempted Derived_Graph
    without acknowledging partial success.
21. WHEN the Financial_Truth_Coordinator copies a Canonical_Input_Manifest_Draft, THE
    Financial_Truth_Coordinator SHALL create exactly one Canonical_Manifest_Entry for each draft entry at
    the same ordinal with zero additional Canonical_Manifest_Entries.
22. WHEN more than one prior Verified_Derived_Graph is eligible as a predecessor, THE
    Financial_Truth_Repository SHALL select the graph with the greatest lexicographic tuple of `generatedAt`,
    `asOf`, and Evaluation_Key after excluding the current Evaluation_Key and requiring the same Purpose.
23. WHEN exactly one prior Verified_Derived_Graph is eligible as a predecessor, THE Financial_Snapshot SHALL
    reference that graph's Financial_Snapshot.
24. IF no prior Verified_Derived_Graph with the same Purpose and a different Evaluation_Key exists at
    Financial_Snapshot construction time, THEN THE Financial_Snapshot SHALL use null as predecessor.
25. IF predecessor selection returns more than one graph for the selected ordering tuple or a graph without
    `READ_BACK_VERIFIED` verification state, THEN THE Financial_Truth_Repository SHALL return
    `Refused(REFERENCE_VALIDATION_FAILED)` before persistence.

### Requirement 5: Produce one shared structurally closed receipt

**User Story:** As a downstream consumer, I want one amount-free proof of the exact state used, so that later
objectives extend one receipt base instead of inventing parallel evidence.

#### Acceptance Criteria

1. WHEN the Financial_Truth_Coordinator builds or replays a Derived_Graph, THE
   Financial_Truth_Coordinator SHALL derive exactly one State_Use_Receipt identity from Evaluation_Key and
   the closed receipt role.
2. THE State_Use_Receipt SHALL contain the stored Financial_Truth_Status, `generatedAt`, Financial_Snapshot
   reference, Canonical_Manifest reference, Evaluation_Version_Set reference, Evaluation_Key,
   Canonical_State_Version, `asOf`, Purpose, freshness, reconciliation, exactly three Engine_Run references,
   evidence references, unresolved items, and Completion_Status.
3. THE State_Use_Receipt SHALL contain exactly three Engine_Run references in Required_Engine order.
4. THE State_Use_Receipt SHALL deduplicate and canonically order each reference collection.
5. THE State_Use_Receipt SHALL contain one canonically ordered evidence-reference collection, one
   canonically ordered unresolved-`MATERIAL` collection, and one canonically ordered
   unresolved-`UNKNOWN`-materiality collection.
6. THE State_Use_Receipt SHALL contain zero unresolved `NON_MATERIAL` items.
7. THE Financial_Truth_Repository SHALL resolve the State_Use_Receipt Financial_Snapshot reference to exactly
   one Financial_Snapshot in the same Derived_Graph.
8. THE Financial_Truth_Repository SHALL resolve each State_Use_Receipt Engine_Run reference to exactly one
   Engine_Run in the same Derived_Graph.
9. THE Financial_Truth_Repository SHALL resolve each State_Use_Receipt Canonical_Evidence_Reference to exactly
   one Canonical_Manifest_Entry in the same Derived_Graph.
10. THE Financial_Truth_Repository SHALL resolve every receipt engine and policy version reference through
    the receipt's Evaluation_Version_Set and require field-for-field equality with the resolved entry.
11. IF a receipt reference is malformed, duplicated, missing, ambiguous, wrong-target, cross-graph,
    out-of-order, over-bound, or identity-mismatched, THEN THE Financial_Truth_Repository SHALL return
    `Refused(REFERENCE_VALIDATION_FAILED)` before preparing SQL.
12. THE State_Use_Receipt SHALL use only target-typed Opaque_References, exact lowercase SHA-256 digests,
    validated UTC_Instants, closed enums, and canonically ordered bounded collections.
13. THE State_Use_Receipt SHALL contain zero monetary magnitudes, monetary fact copies, account names,
    payees, source text, chat text, secrets, credentials, unknown keys, or arbitrary free-form text.
14. IF any Required_Engine has status `FAILED`, THEN THE Financial_Truth_Coordinator SHALL return Refused
    without creating a State_Use_Receipt.
15. IF any Required_Engine boundary returns Refused, THEN THE Financial_Truth_Coordinator SHALL propagate the
    same Refusal_Code without creating a State_Use_Receipt.
16. WHEN no Required_Engine has status `FAILED` and at least one Required_Engine is `MISSING` or `DEGRADED`,
    THE State_Use_Receipt SHALL use Completion_Status `PARTIAL`.
17. WHEN any required Evaluation_Version_Entry is `MISSING`, THE State_Use_Receipt SHALL use Completion_Status
    `PARTIAL`.
18. WHEN all three Required_Engines are `PASS`, every required Evaluation_Version_Entry is `KNOWN` and
    resolvable, and every graph reference resolves exactly once, THE State_Use_Receipt SHALL use
    Completion_Status `COMPLETE`.
19. THE Financial_Snapshot_Interface SHALL expose one shared State_Use_Receipt base for this journey.
20. IF receipt parsing finds a malformed digest or UTC_Instant, unknown enum or key, duplicate reference,
    non-canonical order, over-bound collection, prohibited value, or free-form value, THEN THE
    Financial_Truth_Repository SHALL return `Refused(PRIVACY_VALIDATION_FAILED)` or
    `Refused(REFERENCE_VALIDATION_FAILED)` before preparing SQL.
21. THE State_Use_Receipt SHALL bound each reference collection by the exact cardinality of eligible rows in
    the same Derived_Graph.
22. THE State_Use_Receipt evidence-reference collection SHALL equal the canonically ordered deduplicated
    union of every Canonical_Evidence_Reference used by the three Engine_Runs, Financial_Snapshot account
    balances, Financial_Snapshot freshness entries, and Financial_Snapshot unresolved items.
23. THE State_Use_Receipt unresolved-`MATERIAL` collection SHALL contain each Financial_Snapshot unresolved
    item with Materiality_State `MATERIAL` exactly once and no other item.
24. THE State_Use_Receipt unresolved-`UNKNOWN`-materiality collection SHALL contain each Financial_Snapshot
    unresolved item with Materiality_State `UNKNOWN` exactly once and no other item.
25. THE State_Use_Receipt SHALL place no unresolved item in more than one receipt collection.
26. WHEN the Financial_Truth_Repository validates a State_Use_Receipt, THE Financial_Truth_Repository SHALL
    calculate each collection bound from eligible rows in the same Derived_Graph rather than from caller
    input or stored collection length.
27. IF State_Use_Receipt privacy validation and reference validation both detect failures, THEN THE
    Financial_Truth_Repository SHALL return `Refused(PRIVACY_VALIDATION_FAILED)` before preparing SQL.
28. IF a receipt collection omits an eligible required reference, includes an ineligible reference, exceeds
    its graph-derived bound, duplicates an item, or violates canonical order, THEN THE
    Financial_Truth_Repository SHALL return `Refused(REFERENCE_VALIDATION_FAILED)` before preparing SQL.

### Requirement 6: Derive exhaustive currentness without invented policy

**User Story:** As the owner, I want every closed evidence-state combination to produce one deterministic
outcome, so that missing, failed, stale, and unreconciled evidence cannot appear current.

#### Acceptance Criteria

1. IF the freshness policy entry is `MISSING`, THEN THE Freshness_Policy_Port SHALL return
   `OK(UNKNOWN, FRESHNESS_POLICY_MISSING)`.
2. THE Financial_Snapshot_Interface SHALL use no built-in freshness duration, materiality amount, or policy
   threshold.
3. WHEN the required-account set is empty, THE Financial_Truth_Coordinator SHALL derive overall
   Freshness_State `UNKNOWN`.
4. WHEN at least one required account is `STALE`, THE Financial_Truth_Coordinator SHALL derive overall
   Freshness_State `STALE`.
5. WHEN no required account is `STALE` and at least one required account is `UNKNOWN`, THE
   Financial_Truth_Coordinator SHALL derive overall Freshness_State `UNKNOWN`.
6. WHEN no required account is `STALE` or `UNKNOWN` and at least one required account is `LIMITED`, THE
   Financial_Truth_Coordinator SHALL derive overall Freshness_State `LIMITED`.
7. WHEN the required-account set is non-empty and every required account is `FRESH`, THE
   Financial_Truth_Coordinator SHALL derive overall Freshness_State `FRESH`.
8. IF any request, caller, canonical read, candidate fence, version-set, engine, policy, reference, privacy,
   persistence, or read-back refusal applies, THEN THE Financial_Truth_Coordinator SHALL return the mapped
   Refused result before applying a Financial_Truth_Status rule.
9. IF any Required_Engine has status `FAILED`, THEN THE Financial_Truth_Coordinator SHALL return
   `Refused(REQUIRED_ENGINE_FAILED)` without persisting a Derived_Graph.
10. WHEN no refusal applies and overall Freshness_State is `STALE`, THE Financial_Truth_Coordinator SHALL
    return Financial_Truth_Status `STALE` before any lower-priority rule.
11. WHEN no refusal or `STALE` condition applies and any required Evaluation_Version_Entry is `MISSING`,
    overall freshness is `UNKNOWN`, required account evidence is unknown, or reconciliation is `UNKNOWN`,
    THE Financial_Truth_Coordinator SHALL return Financial_Truth_Status `UNKNOWN`.
12. WHEN no refusal, `STALE`, or `UNKNOWN` condition applies and overall freshness is `LIMITED`, THE
    Financial_Truth_Coordinator SHALL return Financial_Truth_Status `LIMITED`.
13. WHEN no higher-priority condition applies and any Required_Engine is `MISSING` or `DEGRADED`, THE
    Financial_Truth_Coordinator SHALL return Financial_Truth_Status `LIMITED`.
14. WHEN no higher-priority condition applies and reconciliation is
    `RECONCILED_WITH_REPORTED_DISAGREEMENT`, `UNEXPLAINED_RESIDUAL`, or `NOT_RECONCILED`, THE
    Financial_Truth_Coordinator SHALL return Financial_Truth_Status `LIMITED`.
15. WHEN every required account is `FRESH`, reconciliation is `RECONCILED`, all three Required_Engines are
    `PASS`, candidate inclusion is zero, and every required Evaluation_Version_Entry is `KNOWN` and
    resolvable, THE Financial_Truth_Coordinator SHALL return Financial_Truth_Status `CURRENT` and
    Completion_Status `COMPLETE`.
16. WHEN reconciliation evidence reports a reconciled result without disagreement or residual, THE
    Financial_Truth_Coordinator SHALL assign `RECONCILED`.
17. WHEN reconciliation evidence reports reconciled evidence with disagreement, THE
    Financial_Truth_Coordinator SHALL assign `RECONCILED_WITH_REPORTED_DISAGREEMENT`.
18. WHEN reconciliation evidence reports an unexplained residual, THE Financial_Truth_Coordinator SHALL
    assign `UNEXPLAINED_RESIDUAL`.
19. IF durable evidence establishes that reconciliation has not occurred, THEN THE
    Financial_Truth_Coordinator SHALL assign `NOT_RECONCILED`.
20. IF durable evidence cannot determine whether reconciliation occurred, THEN THE
    Financial_Truth_Coordinator SHALL assign `UNKNOWN`.
21. WHEN reconciliation derivation returns OK, THE Financial_Truth_Coordinator SHALL assign exactly one
    Reconciliation_State.
22. IF freshness evidence contains an invalid UTC_Instant, THEN THE Freshness_Policy_Port SHALL return
    `OK(UNKNOWN, EVIDENCE_TIMESTAMP_INVALID)`.
23. IF freshness evidence is later than request `asOf`, THEN THE Freshness_Policy_Port SHALL return
    `OK(UNKNOWN, EVIDENCE_FUTURE_DATED)`.
24. IF a fact, engine input, engine version, or policy version is unavailable, THEN THE
    Financial_Truth_Coordinator SHALL preserve the missing state separately from a valid zero-valued fact.
25. IF a closed-state combination reaches no defined Refused or Financial_Truth_Status outcome, THEN THE
    Financial_Truth_Coordinator SHALL return `Refused(REFERENCE_VALIDATION_FAILED)` without persisting a new
    Derived_Graph.
26. IF Freshness_Policy_Port execution fails or returns a malformed result, THEN THE
    Freshness_Policy_Port SHALL return `Refused(FRESHNESS_POLICY_FAILED)`.
27. WHEN Freshness_Policy_Port uses a `KNOWN` policy entry, THE Financial_Truth_Repository SHALL require the
    returned policy reference to equal the matching Evaluation_Version_Entry.
28. IF Freshness_Policy_Port returns a policy reference that differs from the matching
    Evaluation_Version_Entry, THEN THE Freshness_Policy_Port SHALL return
    `Refused(FRESHNESS_POLICY_FAILED)`.
29. THE Financial_Snapshot_Interface SHALL represent an unavailable freshness policy or policy version as
    `MISSING` without synthesizing a duration, threshold, digest, or version reference.
30. WHEN the Financial_Truth_Coordinator derives an outcome, THE Financial_Truth_Coordinator SHALL evaluate
    criteria 6.8 through 6.15 in ascending order and select exactly the first applicable outcome.
31. WHEN the matching freshness policy Evaluation_Version_Entry is `MISSING`, THE Freshness_Policy_Port SHALL
    return a null Policy_Version reference and the exact matching Evaluation_Version_Entry reference with
    `OK(UNKNOWN, FRESHNESS_POLICY_MISSING)`.
32. WHEN the matching freshness policy Evaluation_Version_Entry is `KNOWN`, THE Freshness_Policy_Port SHALL
    return the same Policy_Version reference and Evaluation_Version_Entry reference field-for-field.
33. IF the Freshness_Policy_Port returns more than one Freshness_State, omits Freshness_State, returns an
    unknown Reason_Code, or returns a policy reference inconsistent with the matching entry, THEN THE
    Freshness_Policy_Port SHALL return `Refused(FRESHNESS_POLICY_FAILED)`.
34. THE Financial_Truth_Coordinator SHALL map every combination of the closed refusal, freshness,
    Required_Engine, reconciliation, and required Version_Entry_State domains to exactly one Refused result
    or exactly one Financial_Truth_Status.

### Requirement 7: Persist atomically and recover by complete identity

**User Story:** As the owner, I want one append-only auditable graph for each complete evaluation identity,
so that retries and interruptions cannot create duplicate or partial truth.

#### Acceptance Criteria

1. WHEN the Financial_Truth_Repository persists a Derived_Graph, THE Financial_Truth_Repository SHALL append
   stored Financial_Truth_Status, Evaluation_Version_Set and entries, Canonical_Manifest and entries,
   Engine_Runs, Output_Sets, facts, Financial_Snapshot, State_Use_Receipt, and child rows in one transaction.
2. IF the persistence transaction does not commit, THEN THE Financial_Truth_Repository SHALL return
   `Refused(PERSISTENCE_FAILED)` and persist zero rows from the attempted Derived_Graph.
3. WHEN the transaction commits, THE Financial_Truth_Repository SHALL perform an independent complete graph
   read-back without reusing write-return values.
4. WHEN read-back completes, THE Financial_Truth_Repository SHALL compare every intended and stored scalar,
   identity, child, count, order, ownership relation, ordinal, and reference.
5. IF Financial_Snapshot read-back differs, THEN THE Financial_Truth_Repository SHALL return
   `Refused(SNAPSHOT_READBACK_MISMATCH)` without acknowledging success.
6. IF State_Use_Receipt read-back differs, THEN THE Financial_Truth_Repository SHALL return
   `Refused(RECEIPT_READBACK_MISMATCH)` without acknowledging success.
7. IF an unclassified graph child differs, THEN THE Financial_Truth_Repository SHALL return
   `Refused(REFERENCE_VALIDATION_FAILED)` without acknowledging success.
8. IF execution stops before commit, THEN THE Financial_Truth_Repository SHALL leave zero rows for the
   attempted Derived_Graph.
9. WHEN an exact retry reuses Canonical_State_Version, Version_Set_Content_Digest, Purpose, `asOf`,
   `generatedAt`, and identical complete graph content, THE Financial_Truth_Repository SHALL independently
   verify and return the existing Verified_Derived_Graph.
10. WHEN an exact retry returns an existing Verified_Derived_Graph, THE Financial_Truth_Repository SHALL
    append or rewrite zero rows.
11. IF the same Evaluation_Key resolves to different content, THEN THE Financial_Truth_Repository SHALL
    return `Refused(STATE_VERSION_CONFLICT)` without changing a row.
12. IF a caller attempts to update or delete a Derived_Graph row, THEN THE Financial_Truth_Repository SHALL
    refuse the operation.
13. WHEN Canonical_State_Version, Version_Set_Content_Digest, Purpose, `asOf`, or `generatedAt` changes,
    THE Financial_Snapshot_Interface SHALL derive a different Evaluation_Key and preserve the prior graph.
14. THE Financial_Snapshot_Interface SHALL derive each graph and child identity from Evaluation_Key, one
    closed role tag, and a deterministic ordinal or closed kind.
15. THE Financial_Snapshot_Interface SHALL obtain each persisted time from a caller-injected or
    dependency-injected UTC_Instant.
16. THE Financial_Snapshot_Interface SHALL use no randomness, UUID, process counter, repository-generated
    identity, or ambient clock for a persisted identity or time.
17. WHEN complete inputs and deterministic results are identical, THE Financial_Snapshot_Interface SHALL
    produce field-for-field identical write intent.
18. THE Financial_Truth_Repository SHALL be the sole repository that writes, reads back, verifies, replays,
    or performs Historical_Graph_Lookup for any Derived_Graph component.
19. THE Financial_Truth_Repository SHALL perform zero mutations against canonical financial tables.
20. IF Canonical_Manifest read-back differs, THEN THE Financial_Truth_Repository SHALL return
    `Refused(MANIFEST_READBACK_MISMATCH)`.
21. IF Evaluation_Version_Set read-back differs, THEN THE Financial_Truth_Repository SHALL return
    `Refused(VERSION_SET_READBACK_MISMATCH)`.
22. IF stored Financial_Truth_Status differs from intended or receipt status, THEN THE
    Financial_Truth_Repository SHALL return `Refused(STATUS_READBACK_MISMATCH)`.
23. WHEN Historical_Graph_Lookup returns a graph, THE Financial_Truth_Repository SHALL return the immutable
    stored Financial_Truth_Status, original complete evaluation identity, graph-owned evidence, and
    `READ_BACK_VERIFIED` verification state without applying current policy or reading mutable canonical
    rows.
24. THE Financial_Snapshot_Interface SHALL derive Evaluation_Key only from Canonical_State_Version,
    Version_Set_Content_Digest, Purpose, caller-supplied `asOf`, and caller-supplied `generatedAt`.
25. THE Financial_Snapshot_Interface SHALL exclude every Evaluation_Version_Set reference and
    Evaluation_Version_Entry reference from Evaluation_Key derivation.
26. THE Financial_Snapshot_Interface SHALL derive every graph-local identity from Evaluation_Key, one closed
    graph-local role tag, and a deterministic ordinal or closed kind without including an
    Evaluation_Version_Set reference or Evaluation_Version_Entry reference.
27. THE Financial_Snapshot_Interface SHALL derive Version_Set_Content_Digest, the Evaluation_Version_Set
    reference, and every Evaluation_Version_Entry reference before deriving Evaluation_Key or any
    graph-local identity.
28. IF an Evaluation_Key input depends on Evaluation_Key or on a graph-local identity, THEN THE
    Financial_Snapshot_Interface SHALL return `Refused(REFERENCE_VALIDATION_FAILED)` before persistence.
29. WHEN the Financial_Truth_Repository persists a new Derived_Graph, THE Financial_Truth_Repository SHALL
    validate derivation in this order: five identity-free payloads, Version_Set_Content_Digest,
    Evaluation_Version_Set reference, five Evaluation_Version_Entry references, Evaluation_Key, and
    graph-local identities.
30. IF an existing Evaluation_Version_Set row has Version_Set_Content_Digest equal to an attempted set and
    any payload, entry, ordinal, role, class, state, or reference differs, THEN THE
    Financial_Truth_Repository SHALL return `Refused(STATE_VERSION_CONFLICT)` without changing a row.
31. WHEN an exact retry finds an existing graph, THE Financial_Truth_Repository SHALL compare the complete
    intended graph with an independent complete read-back before returning the existing
    Verified_Derived_Graph.
32. IF an exact retry read-back differs in any stored status, identity, version payload, version entry,
    manifest entry, run, output set, fact, snapshot, receipt, child, count, order, ownership relation, or
    reference, THEN THE Financial_Truth_Repository SHALL return the corresponding closed read-back refusal
    without changing a row.
33. WHEN Historical_Graph_Lookup returns a Verified_Derived_Graph, THE Financial_Truth_Repository SHALL
    resolve every historical evidence reference only through graph-owned Canonical_Manifest_Entries and
    return the stored Financial_Truth_Status without reading mutable canonical rows.
34. WHEN any of the five Evaluation_Key inputs changes, THE Financial_Snapshot_Interface SHALL derive the
    complete version-set identities before deriving the new Evaluation_Key and preserve every prior graph.

### Requirement 8: Refuse corrupt and mismatched graphs through closed results

**User Story:** As an auditor, I want every fallible boundary and graph edge to fail closed, so that partial,
ambiguous, or cross-version evidence cannot appear valid.

#### Acceptance Criteria

1. THE Financial_Truth_Repository SHALL resolve every non-null Engine_Run Output_Set reference to exactly one
   Output_Set owned by the referring Engine_Run.
2. THE Financial_Truth_Repository SHALL require every resolved Output_Set to match the referring Engine_Run
   Evaluation_Key, Canonical_State_Version, and Evaluation_Version_Set.
3. THE Financial_Truth_Repository SHALL resolve every Output_Set fact reference to exactly one fact owned by
   the referring Output_Set and Engine_Run at the expected ordinal.
4. THE Financial_Truth_Repository SHALL require every resolved fact to match the referring Engine_Run and
   Derived_Graph identities.
5. THE Financial_Truth_Repository SHALL resolve every Financial_Snapshot monetary reference to exactly one
   fact in the expected Output_Set and Derived_Graph.
6. THE Financial_Truth_Repository SHALL require every Financial_Snapshot reference to match the snapshot
   Evaluation_Key and Canonical_State_Version.
7. THE Financial_Truth_Repository SHALL resolve every receipt snapshot reference to exactly one snapshot in
   the same Derived_Graph.
8. THE Financial_Truth_Repository SHALL resolve every receipt Engine_Run reference to exactly one matching
   run in the same Derived_Graph.
9. THE Financial_Truth_Repository SHALL resolve every receipt evidence reference to exactly one graph-owned
   Canonical_Manifest_Entry.
10. THE Financial_Truth_Repository SHALL require every receipt target to match Derived_Graph,
    Evaluation_Key, Canonical_State_Version, Purpose, and applicable ordinal.
11. IF a reference target, digest, owner, ordinal, graph, Evaluation_Key, Canonical_State_Version, Purpose,
    or cardinality is invalid, THEN THE Financial_Truth_Repository SHALL return the mapped Refused result
    before preparing SQL or acknowledging success.
12. THE Financial_Truth_Request parser, Canonical_State_Reader, Evaluation_Version_Set_Registry,
    Required_Engine_Registry, Freshness_Policy_Port, Financial_Truth_Repository, and
    Financial_Truth_Coordinator SHALL return Result for every fallible operation.
13. THE Financial_Snapshot_Interface SHALL map each named failure condition to exactly one closed
    Refusal_Code from the current design.
14. IF a fallible boundary returns Refused, THEN THE Financial_Truth_Coordinator SHALL invoke zero downstream
    boundaries after the refusal.
15. IF reference integrity or read-back returns Refused, THEN THE Financial_Snapshot_Interface SHALL return no
    historical substitute, Drive mirror, model statement, cached value, conversational value, or partial
    graph for the requested result.
16. THE Financial_Snapshot_Interface SHALL validate every Reference_Target, Required_Engine, Reason_Code,
    Refusal_Code, status, artifact role, Evaluation_Version_Entry_Payload, Version_Set_Content_Digest, digest,
    UTC_Instant, and collection bound against the exact closed domain before preparing SQL or emitting a
    Result.
17. IF repository transaction execution fails, THEN THE Financial_Truth_Repository SHALL return
    `Refused(PERSISTENCE_FAILED)`.
18. IF structural privacy validation fails, THEN THE Financial_Truth_Repository SHALL return
    `Refused(PRIVACY_VALIDATION_FAILED)`.
19. IF structural reference validation fails, THEN THE Financial_Truth_Repository SHALL return
    `Refused(REFERENCE_VALIDATION_FAILED)`.
20. THE Financial_Truth_Coordinator SHALL preserve the originating closed Refusal_Code without converting
    Refused into `UNKNOWN`, `MISSING`, an empty collection, or null success.
21. IF Evaluation_Version_Set validation fails, THEN THE Evaluation_Version_Set_Registry SHALL return
    `Refused(VERSION_SET_VALIDATION_FAILED)`.
22. IF Freshness_Policy_Port execution, result validation, or policy-reference matching fails, THEN THE
    Freshness_Policy_Port SHALL return `Refused(FRESHNESS_POLICY_FAILED)`.
23. IF a named failure condition occurs, THEN THE boundary that owns the failure SHALL return exactly the
    Refusal_Code assigned to that condition by the Closed refusal mapping and no other Refusal_Code.
24. IF complete read-back finds a manifest, version-set, stored-status, snapshot, or receipt mismatch, THEN
    THE Financial_Truth_Repository SHALL return the corresponding `MANIFEST_READBACK_MISMATCH`,
    `VERSION_SET_READBACK_MISMATCH`, `STATUS_READBACK_MISMATCH`, `SNAPSHOT_READBACK_MISMATCH`, or
    `RECEIPT_READBACK_MISMATCH` Refusal_Code.
25. IF complete read-back finds a graph mismatch outside the named mismatch categories, THEN THE
    Financial_Truth_Repository SHALL return `Refused(REFERENCE_VALIDATION_FAILED)`.
26. WHEN any fallible boundary completes, THE fallible boundary SHALL return exactly one Result branch and
    no null, partial success, empty-collection failure signal, fallback value, or untyped failure value.
27. IF more than one validation failure is detectable at the same boundary, THEN THE boundary SHALL return
    the first applicable Refusal_Code in this order: `UNAUTHORIZED_CALLER`, `INVALID_REQUEST`,
    `UNSUPPORTED_PURPOSE`, `MANIFEST_POLICY_MISSING`, `CANONICAL_READ_FAILED`, `CANDIDATE_FENCE_FAILED`,
    `CANONICAL_REREAD_CONFLICT`, `VERSION_SET_VALIDATION_FAILED`, `REQUIRED_ENGINE_FAILED`,
    `FRESHNESS_POLICY_FAILED`, `PRIVACY_VALIDATION_FAILED`, `REFERENCE_VALIDATION_FAILED`,
    `PERSISTENCE_FAILED`, `STATE_VERSION_CONFLICT`, `MANIFEST_READBACK_MISMATCH`,
    `VERSION_SET_READBACK_MISMATCH`, `STATUS_READBACK_MISMATCH`, `SNAPSHOT_READBACK_MISMATCH`, and
    `RECEIPT_READBACK_MISMATCH`.
28. THE Financial_Snapshot_Interface SHALL keep the Refusal_Code mapping total over every named request,
    admission, canonical-read, candidate-fence, reread, version-set, engine, freshness-policy, structural,
    privacy, persistence, state-conflict, and read-back failure condition.

### Requirement 9: Preserve privacy, model independence, and synthetic provenance

**User Story:** As the owner, I want deterministic currentness and test-only synthetic authority, so that
model outages, sensitive narratives, and scanned real data cannot alter or impersonate financial truth.

#### Acceptance Criteria

1. THE Financial_Snapshot_Interface SHALL complete every `FINANCIAL_TRUTH_STATUS` request with zero model
   calls and zero model-backed calls.
2. WHEN deterministic inputs and injected UTC_Instants are identical, THE Financial_Snapshot_Interface SHALL
   return a field-for-field identical Result regardless of model-provider availability.
3. THE Financial_Snapshot and State_Use_Receipt SHALL contain only the closed fields and reference types
   defined by the current design.
4. WHEN the Financial_Snapshot_Interface emits diagnostics, THE Financial_Snapshot_Interface SHALL emit only
   typed references, closed statuses, and closed Refusal_Codes or Reason_Codes.
5. THE Financial_Snapshot_Interface SHALL derive canonical identity, deterministic facts, freshness,
   reconciliation, and Financial_Truth_Status only from the Canonical_Read_Bundle, deterministic outputs,
   and approved policy evidence.
6. WHERE a downstream explanation is separately approved, THE Downstream_Adapter SHALL read only a
   Verified_Derived_Graph by Opaque_Reference.
7. WHERE a downstream explanation is separately approved, THE Downstream_Adapter SHALL preserve every
   persisted identity, fact, status, missing state, and graph field unchanged.
8. IF a downstream explanation or model provider is unavailable, THEN THE Financial_Snapshot_Interface SHALL
   preserve the completed deterministic graph unchanged.
9. IF persisted or diagnostic output contains a prohibited field or value, THEN THE
   Financial_Snapshot_Interface SHALL return `Refused(PRIVACY_VALIDATION_FAILED)` and preserve prior state.
10. THE Financial_Snapshot_Interface SHALL complete the selected currentness journey without requiring a
    model or changing deterministic behavior when a model is unavailable.
11. THE Synthetic_Fixture_Factory SHALL be the only component capable of constructing
    Synthetic_Fixture_Capability.
12. THE production Enclosing_Composition SHALL expose no constructor, provider, or accepting port for
    Synthetic_Fixture_Capability.
13. THE Synthetic_Verification_Profile SHALL make production canonical-store, transport, provider, Drive,
    model, and host adapters unavailable.
14. WHEN Synthetic_Shape_Guard accepts input without Synthetic_Fixture_Capability, THE
    Synthetic_Fixture_Factory SHALL return `Refused(INVALID_REQUEST)` before store construction.
15. WHEN the Synthetic_Fixture_Factory creates Synthetic_Fixture_Capability, THE
    Synthetic_Verification_Profile SHALL permit construction of only a synthetic store.
16. THE Synthetic_Shape_Guard SHALL operate as defense-in-depth without granting
    Synthetic_Fixture_Capability or asserting synthetic provenance.
17. IF the Synthetic_Shape_Guard finds a secret, personal identifier, real financial datum, hostname,
    domain, network address, provider identifier, Drive identifier, bot identifier, webhook path, or other
    deployment particular, THEN THE Synthetic_Shape_Guard SHALL return Refused before store construction.
18. THE Financial_Snapshot_Interface SHALL persist and emit canonical evidence references only to
    graph-owned Canonical_Manifest_Entries in the same Verified_Derived_Graph.
19. THE production build profile SHALL make the Synthetic_Fixture_Capability constructor, provider,
    accepting port, and Synthetic_Fixture_Factory unavailable to production composition code.
20. THE Synthetic_Verification_Profile SHALL make every production canonical-store, transport, provider,
    Drive, model, host, and outbound-network adapter unrepresentable in the synthetic composition.
21. WHEN the Financial_Snapshot_Interface derives or replays a deterministic graph, THE
    Financial_Snapshot_Interface SHALL invoke zero model ports regardless of model configuration,
    availability, response, or failure state.
22. IF a canonical evidence reference resolves outside the same Verified_Derived_Graph or requires a live
    canonical-row read, THEN THE Financial_Truth_Repository SHALL return
    `Refused(REFERENCE_VALIDATION_FAILED)`.

### Requirement 10: Add derived persistence through forward-only migration

**User Story:** As the repository maintainer, I want derived persistence sequenced after the actual migration
frontier, so that migration and rollback preserve canonical financial facts.

#### Acceptance Criteria

1. WHEN implementation and migration are separately authorized, THE Migration_Planner SHALL perform a
   final reread of the actual migration registry immediately before writing Derived_Persistence_Migration
   source.
2. WHEN the Migration_Planner rereads the migration registry, THE Migration_Planner SHALL select the observed
   frontier plus one.
3. THE Migration_Planner SHALL treat versions in historical documents, designs, requirements, tasks, and
   planning records as unreserved.
4. WHEN Derived_Persistence_Migration is applied, THE Derived_Persistence_Migration SHALL add only reviewed
   derived tables, constraints, indexes, and append-only guards.
5. THE Derived_Persistence_Migration SHALL preserve every existing schema object, migration source, applied
   checksum, and row unchanged.
6. IF an applied migration checksum differs from source, THEN THE Migrator SHALL refuse every pending
   migration and preserve the store unchanged.
7. IF the frontier changes after reread and before migration write, THEN THE Migrator SHALL refuse the
   migration and preserve the store unchanged.
8. IF Derived_Persistence_Migration fails before commit, THEN THE Migrator SHALL roll back the migration and
   preserve the pre-migration schema and data.
9. THE Financial_Snapshot_Interface SHALL treat compatibility across Derived_Persistence_Migration as
   forward-only.
10. IF earlier application code encounters an unrecognized newer migration, THEN THE Migrator SHALL refuse
    to open or mutate the store.
11. WHEN feature code is rolled back without crossing the migration boundary, THE Enclosing_Composition
    SHALL disable the Financial_Truth_Coordinator and return the prior typed unavailable behavior.
12. WHILE no approved derived-history retention policy exists, THE Financial_Truth_Repository SHALL perform
    zero scheduled or manual pruning operations.
13. IF rollback crosses the migration boundary, THEN THE Financial_Snapshot_Interface SHALL require the
    separately authorized PFOS Contract 12 §7.4 restore of a verified pre-migration snapshot to a fresh path.
14. WHEN a separately authorized cross-migration restore completes, THE recovery procedure SHALL pass the
    integrity check before any separately authorized promotion.
15. THE Migrator SHALL reject reverse migration, in-place live-store overwrite, and prior-code opening of an
    unrecognized newer schema.
16. WHEN the final authorized migration-registry reread completes, THE Migration_Planner SHALL bind the
    selected frontier-plus-one version and ordered prior migration checksums to the pending
    Derived_Persistence_Migration source operation.
17. IF the migration frontier cannot be proved unchanged between the final authorized reread and migration
    source creation, THEN THE Migration_Planner SHALL leave migration source absent and require a new final
    authorized reread.
18. WHEN Derived_Persistence_Migration commits, THE Migrator SHALL record the exact source checksum and new
    migration head without changing any prior migration row or checksum.
19. WHEN a separately authorized cross-migration restore begins, THE recovery procedure SHALL restore the
    verified pre-migration snapshot to a fresh path while preserving the current store path unchanged.
20. IF fresh-path restore integrity verification fails, THEN THE recovery procedure SHALL leave the current
    store unchanged and refuse promotion of the restored path.
21. WHEN feature code is disabled after Derived_Persistence_Migration, THE Enclosing_Composition SHALL retain
    the newer schema unopened by prior code and expose only the prior typed unavailable behavior.

### Requirement 11: Preserve local/live and task-execution separation

**User Story:** As the owner, I want review artifacts, local behavior, synthetic verification, and live
activation separated, so that drafting requirements cannot execute stale tasks or activate infrastructure.

#### Acceptance Criteria

1. THE Financial_Snapshot_Interface SHALL produce zero process-entrypoint, transport-listener,
   Slack-response, Telegram-response, scheduler-registration, timer, cron, queue-consumer, Drive, host,
   provider, outbound-network, model-call, and model-spend effects.
2. THE Financial_Snapshot_Interface SHALL produce zero ingestion, Candidate_Row promotion, canonical write,
   statement-close, reconciliation mutation, mirror activation, notification delivery, and financial action
   effects.
3. THE Financial_Snapshot_Interface SHALL read canonical state only from Canonical_Store through read-only
   repositories.
4. THE Financial_Snapshot_Interface SHALL open no database other than the finance Canonical_Store for the
   selected journey.
5. THE Financial_Snapshot_Interface SHALL use only existing deterministic financial behavior and the
   existing money implementation.
6. WHILE live activation lacks separate authorization, THE Enclosing_Composition SHALL contain no binding
   from a process entrypoint, transport registry, scheduler registry, timer registry, cron registry, or
   queue-consumer registry to the Financial_Snapshot_Interface.
7. IF a caller supplies any unknown request key, including an effect, tool, action, or transport key, THEN
   THE Financial_Truth_Request parser SHALL return `Refused(INVALID_REQUEST)` before a canonical read.
8. WHERE a Downstream_Adapter is separately approved, THE Downstream_Adapter SHALL read the persisted graph
   only by Opaque_Reference.
9. WHERE a Downstream_Adapter is separately approved, THE Downstream_Adapter SHALL perform zero Derived_Graph
   or canonical-table writes.
10. WHERE a Downstream_Adapter is separately approved, THE Downstream_Adapter SHALL preserve deterministic
    facts, Financial_Truth_Status, and missing evidence unchanged.
11. WHILE the current design and these requirements are not both owner-accepted or Task_Board
    regeneration from both accepted documents is incomplete, THE Task_Board SHALL remain classified
    `SUPERSEDED_NON_EXECUTABLE`.
12. WHILE the Task_Board is `SUPERSEDED_NON_EXECUTABLE`, THE development workflow SHALL execute zero existing
    Task_Board tasks.
13. WHEN the owner accepts the current design and these requirements, THE planning workflow SHALL
    regenerate the Task_Board from both accepted artifacts before changing the Task_Board classification.
14. THE requirements alignment workflow SHALL preserve `design.md` and `tasks.md` byte-for-byte.
15. THE requirements alignment workflow SHALL perform document-only checks and zero implementation,
    test, build, network, host, real-data, commit, push, deploy, or spend actions.
16. THE Financial_Truth_Request schema SHALL contain no effect, tool, action, transport, live-binding, or
    external-call field.
17. WHEN the owner accepts the current design and these requirements, THE acceptance SHALL authorize
    only the next design-first documentation phase.
18. WHEN the owner accepts the current design and these requirements, THE acceptance SHALL grant zero
    implementation, migration, test, build, live-binding, network, host, real-data, delivery, or spend
    authority.
19. WHILE `design.md` or `requirements.md` lacks owner acceptance, THE planning workflow SHALL classify both
    documents as current review artifacts without classifying either document as superseded or pending
    re-derivation.
20. WHILE `tasks.md` is `SUPERSEDED_NON_EXECUTABLE`, THE planning workflow SHALL preserve `tasks.md`
    byte-for-byte and execute zero existing Task_Board tasks.
21. THE current review artifacts SHALL define the fixed Version_Artifact_Key set as exactly the three
    Required_Engine roles followed by `MANIFEST_SCHEMA_POLICY` and `FRESHNESS_POLICY`.
22. IF a planning or runtime path proposes a sixth, missing, replacement, or reordered Version_Artifact_Key,
    THEN THE planning workflow SHALL preserve the current fixed set and require reviewed revisions to both
    current review artifacts before task regeneration.
23. WHILE either current review artifact lacks owner acceptance or regenerated tasks remain incomplete, THE
    planning workflow SHALL keep the Task_Board `SUPERSEDED_NON_EXECUTABLE`.
24. WHEN task regeneration completes from both owner-accepted current review artifacts, THE planning
    workflow SHALL replace the superseded Task_Board with a dependency-ordered Task_Board before any task is
    classified executable.
25. THE requirements detailer workflow SHALL preserve `design.md`, `tasks.md`, source, tests, contracts,
    operations artifacts, human-gate records, and unrelated user changes byte-for-byte.
26. THE requirements detailer workflow SHALL grant zero implementation, migration, execution, test, build,
    live-binding, network, host, real-data, commit, push, deploy, delivery, or spend authority.
27. WHEN the requirements detailer workflow completes, THE planning workflow SHALL preserve `design.md` and
    `requirements.md` as current review artifacts with owner-accepted state equal to false.
28. WHEN the requirements detailer workflow records completion, THE planning workflow SHALL append exactly
    one immutable `REQUIREMENTS_ACYCLIC_FINAL_DETAILED` event without rewriting an earlier planning event.

## Correctness-property traceability

The table maps all ten correctness properties in the current `design.md` to the current detailed criteria,
including the acyclic identity correction. The `Validates` lines in `design.md` remain unchanged because this
alignment is explicitly limited to `requirements.md`; newly added identity criteria are recorded here for the
next separately opened correctness-property phase.

| Design property | Exact validating acceptance criteria |
|---|---|
| Property 1: Deterministic canonical-state identity | Requirements **2.4, 2.5, 2.6, 2.7, 3.2, 3.3, 3.4, 3.5, 3.26, 3.27, 3.28, 3.29, 3.30, 3.31, 3.32, 3.33, 3.35, 3.36, 3.39, 3.40, 7.13, 7.24, 7.25, 7.27, 7.28, 7.29, 7.34** |
| Property 2: Candidate non-interference | Requirements **2.8, 2.9, 2.10, 2.11, 2.12, 2.23, 2.26** |
| Property 3: Exact money round-trip | Requirements **3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 3.25, 3.38** |
| Property 4: Missing and stale states remain distinct from zero and current | Requirements **3.3, 3.4, 3.9, 3.17, 3.18, 3.24, 3.34, 5.16, 5.17, 5.18, 6.1, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 6.14, 6.15, 6.19, 6.20, 6.22, 6.23, 6.24, 6.25, 6.26, 6.28, 6.29, 6.30, 6.31, 6.32, 6.33, 6.34** |
| Property 5: Reference resolvability and version agreement | Requirements **3.6, 3.7, 3.8, 3.21, 3.22, 3.25, 3.29, 3.30, 3.31, 3.35, 3.36, 3.37, 3.39, 4.3, 4.4, 4.7, 4.14, 4.17, 4.18, 4.19, 4.20, 4.21, 4.22, 4.23, 4.24, 4.25, 5.7, 5.8, 5.9, 5.10, 5.11, 5.21, 5.22, 5.23, 5.24, 5.25, 5.26, 5.28, 7.29, 7.30, 7.31, 7.32, 7.33, 7.34, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 9.18, 9.22** |
| Property 6: Idempotent derived writes and interruption recovery | Requirements **3.27, 3.28, 3.29, 3.30, 3.35, 3.39, 7.1, 7.2, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13, 7.14, 7.15, 7.16, 7.17, 7.20, 7.21, 7.22, 7.23, 7.24, 7.25, 7.26, 7.27, 7.28, 7.29, 7.30, 7.31, 7.32, 7.33, 7.34** |
| Property 7: Model independence | Requirements **9.1, 9.2, 9.8, 9.10, 9.11, 9.12, 9.13, 9.14, 9.15, 9.16, 9.17, 9.19, 9.20, 9.21** |
| Property 8: Closed refusals and amount-free state-use receipts | Requirements **1.10, 1.17, 1.19, 1.20, 1.21, 1.22, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.11, 5.12, 5.13, 5.14, 5.15, 5.16, 5.17, 5.18, 5.19, 5.20, 5.21, 5.22, 5.23, 5.24, 5.25, 5.26, 5.27, 5.28, 8.12, 8.13, 8.14, 8.15, 8.16, 8.17, 8.18, 8.19, 8.20, 8.21, 8.22, 8.23, 8.24, 8.25, 8.26, 8.27, 8.28** |
| Property 9: Single-read bundle coherence | Requirements **2.1, 2.2, 2.3, 2.17, 2.18, 2.19, 2.20, 2.21, 2.22, 2.23, 2.24, 2.25, 2.26, 3.1, 4.1, 4.2, 4.18, 4.19, 4.21** |
| Property 10: Currentness requires caller-time reevaluation | Requirements **1.1, 1.5, 1.11, 1.12, 1.13, 1.18, 1.19, 1.20, 1.21, 1.22, 1.23, 1.24, 3.40, 6.10, 6.11, 6.12, 6.13, 6.14, 6.15, 7.9, 7.13, 7.23, 7.24, 7.25, 7.27, 7.34** |

## Closed refusal mapping

| Fallible boundary | Named failure mapping |
|---|---|
| Financial_Truth_Request parser | malformed structure, invalid UTC_Instant, or unknown key → `INVALID_REQUEST`; unsupported Purpose → `UNSUPPORTED_PURPOSE` |
| Caller admission | caller not admitted → `UNAUTHORIZED_CALLER` |
| Canonical_State_Reader | unavailable manifest policy → `MANIFEST_POLICY_MISSING`; read failure → `CANONICAL_READ_FAILED`; candidate leak → `CANDIDATE_FENCE_FAILED`; reread mismatch → `CANONICAL_REREAD_CONFLICT` |
| Evaluation_Version_Set_Registry | malformed, incomplete, duplicate, out-of-order, wrong-class, runtime-added, payload-entry-mismatched, unresolved `KNOWN`, digest-mismatched, or reference-derivation-mismatched set → `VERSION_SET_VALIDATION_FAILED` |
| Required_Engine_Registry | failed required run or invalid adapter result → `REQUIRED_ENGINE_FAILED`; intentional absent input remains successful `MISSING` |
| Freshness_Policy_Port | execution failure, malformed result, or version mismatch → `FRESHNESS_POLICY_FAILED`; intentional missing policy remains successful `UNKNOWN/PARTIAL` |
| Structural validation | prohibited or free-form value → `PRIVACY_VALIDATION_FAILED`; malformed or wrong-target reference → `REFERENCE_VALIDATION_FAILED` |
| Financial_Truth_Repository write | transaction failure → `PERSISTENCE_FAILED`; same key with different graph → `STATE_VERSION_CONFLICT` |
| Financial_Truth_Repository read-back | manifest → `MANIFEST_READBACK_MISMATCH`; version set → `VERSION_SET_READBACK_MISMATCH`; status → `STATUS_READBACK_MISMATCH`; snapshot → `SNAPSHOT_READBACK_MISMATCH`; receipt → `RECEIPT_READBACK_MISMATCH`; other graph mismatch → `REFERENCE_VALIDATION_FAILED` |
| Financial_Truth_Coordinator | originating closed code is propagated; unreachable closed state → `REFERENCE_VALIDATION_FAILED` |

## Explicit unresolved decisions

These policy gaps remain unresolved. This document defines safe missing, unknown, unavailable, or refusal
behavior but does not select policy values. The five-role Version_Artifact_Key set is closed; a proposed role
change requires reviewed revisions to both current review artifacts and cannot occur through a runtime path.

1. The accepted contract amendment that owns stored Financial_Truth_Status, Evaluation_Version_Set,
   Canonical_Manifest, Engine_Run, Output_Set, Deterministic_Output_Fact, Financial_Snapshot, and
   State_Use_Receipt tables.
2. The exact Approved_Manifest_Schema, including financially consequential tables, fields, normalization,
   and ordering.
3. The approved artifact records and version digests for all five Version_Artifact_Key roles, including the
   policy content for `MANIFEST_SCHEMA_POLICY` and `FRESHNESS_POLICY`. Missing records remain `MISSING`; this
   document defines no artifact digest or policy content.
4. The approved per-account freshness policy and Policy_Version reference. No duration is defined here.
5. The materiality policy. No threshold is defined here; unclassified items remain `UNKNOWN`.
6. The retention policy for Derived_Graph history. No period is defined here; pruning remains disabled.
7. The transaction-pipeline migration immediately preceding Derived_Persistence_Migration.
8. The clean-gate-before-commit evidence procedure. No acceptance check is weakened here.
9. Permission for any amount-bearing financial response. This feature returns status and references only.
10. Gateway, ingress, and live process ownership. This feature activates none.
11. Operational soak, latency, resource, freshness-SLA, RPO, and RTO targets. No values are defined here.
12. Valuation source, cadence, and policy. This journey makes no valuation claim.

## Out of scope

- Amount-bearing conversational consultation or recommendation.
- Persistent local knowledge cache or knowledge-body retention.
- Source discovery, ingestion, parsing, candidate creation, candidate promotion, or canonical mutation.
- Drive mirror activation, upload, encryption lifecycle, concurrency repair, tombstones, or backup execution.
- Financial protection, capital allocation, decision support, goals, briefs, or later objectives.
- Scheduler registration, a new timer, transport, queue consumer, or gateway owner.
- Another canonical writer, receipt schema, financial engine, or money implementation.
- Selection of manifest fields, freshness or materiality thresholds, retention duration, migration number,
  ingress owner, financial-question permission, operational targets, or valuation policy.
- Editing or executing the superseded Task_Board before accepted artifacts and task regeneration.
- Implementation, tests, builds, host or network access, real data, credentials, commits, pushes, deployment,
  or spend.

## Requirements-phase completion boundary

This requirements alignment is ready for owner review when the bounded journey, EARS criteria, acyclic
identity coverage, property traceability, refusal mapping, task-board prohibition, and unresolved decisions
are reviewed together. `design.md` and `requirements.md` remain current review artifacts. Review readiness is
not owner acceptance and grants no implementation authority.

After owner acceptance of both current review artifacts, the design-first workflow may perform
acceptance-criteria testing prework for every criterion, reflect on property redundancy, and update
correctness-property references if required. The planning workflow must then regenerate `tasks.md` from the
accepted artifacts before any task becomes executable. Migration allocation, implementation, tests, builds,
live actions, and delivery remain later phases with separate authority.
