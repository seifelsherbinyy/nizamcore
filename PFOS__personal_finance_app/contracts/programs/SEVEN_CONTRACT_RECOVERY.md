# Financial NIZAM seven-contract recovery program

PROVENANCE: NIZAM-derived from the owner's seven-contract engineering request and
`Module BINA_BUILD.txt`, inspected 2026-09-11. Phase: Recovery 1.
Status: execution scope, not a superseding product contract or deployment authorization.

## Authority and boundaries

The program IDs below are namespaced workstreams, not the original build contracts C1-C6
or PFOS contracts 01-15. Applicable steering and existing domain contracts govern every
implementation. Money rules and drive-db invariants remain unconditional. Source documents
and attachment claims are evidence, not permission. The reported unified v1.3 FINAL remains
a lineage claim until its exact source and authoritative index can be inspected; local
Contract 13 explicitly says its v1.4 proposal does not supersede it.

No human gate is executed, tested, populated or marked complete. No consent, credential
creation/rotation, production spend, cross-repository change, commit or push is included.
Configured credentials may be used only through intended mechanisms for authorized reads,
with values and deployment particulars withheld. Preserve existing working-tree changes.

## Seven explicit engineering contracts

| Program ID | Mission and deliverables | Exit evidence |
|---|---|---|
| C1_SOURCE_TRUTH_AND_LINEAGE | Source registry, chronology, canonical/superseded map, FACT/INFERENCE/MISSING ledger, contradictions | Every consequential claim has a cited source or explicit unknown; unavailable source is not absent |
| C2_LOCAL_RUNTIME_AND_INFRASTRUCTURE | Repository map, service topology, stores/migrations, jobs, recovery and runtime evidence | Code and runtime observations distinguished; reproducible probes without secret output |
| C3_DATA_SECURITY_AND_AUTH | Trust boundaries, credential readiness, provenance, deterministic computation | Critical ownership is explicit; unresolved unsafe egress blocks live enablement |
| C4_FINANCIAL_INTELLIGENCE_AND_AGENTIC_CORE | Finance-state/forecast/decision/debt mappings, agent permissions and approvals | One tested integer-money implementation; LLM cannot source monetary truth |
| C5_PRODUCT_UX_AND_YNAB_EVOLUTION | Recover original UI contract, map journeys and product surfaces to finance capabilities | Every major mapped surface has an implementation reference; unknown UX behavior remains unknown |
| C6_IMPLEMENTATION_INTEGRATION_AND_TESTING | Small contract-owned repairs, synthetic malformed/missing/recovery tests | Focused and full checks recorded; no known high-severity regression and no suppressed failure |
| C7_PRODUCTIONIZATION_CONTINUITY_AND_LEARNING | Master handover, validation, recovery limitations, prioritized next loop | Another agent can reproduce findings and distinguish built, running, tested and blocked |

## Recovery 1 implementation contract

Existing authority: build Contract 2 Phase 2.2; `money-rules.md`; money core
`isMoney`/`assertMoney`. PFOS Contract 06 section 4 corroborates the server-side boundary.
The JSON schema must accept only finite safe integer milliunits, matching the money core.
It must reject out-of-range inputs, not clamp, round, coerce or migrate them into valid money.
All money fields sharing `zMoney` inherit the guard. Valid schema-v9 data remains unchanged;
no schema-version bump, data rewrite, provider write or new arithmetic is required.

Verification includes signed safe edges, zero, overflow on either side, fractional/non-finite
and non-number inputs, JSON round-trip, current migration and a deterministic fake Drive load.
Tests use existing Zod/Vitest/FakeDrive styles. The application bundle gains no server module.

## Status discipline

COMPLETE means the workstream's exit evidence has actually been observed. PARTIAL means useful
outputs exist but the gate is unmet. BLOCKED means a named external dependency or unresolved
high-risk authority prevents completion. Passing code checks alone do not prove live readiness.
A dirty tree must remain visible as a failed release gate until owner-authorized resolution;
never hide files, lower a test floor or commit merely to make acceptance green.
