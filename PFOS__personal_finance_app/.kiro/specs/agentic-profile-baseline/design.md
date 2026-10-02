# Agentic Profile baseline design

Contract 05 addendum; Phase 0. This extends evidence inspection, not the governor.

`docs/architecture/agentic-profile-baseline.json` contains redacted source refs,
capability targets and evidence metadata. No raw content, secrets or connection
configuration. A null target hash records an uninspected target honestly.

`src/server/hermes/baselineEvidence.ts` uses existing Zod to validate the closed
manifest, then pure deterministic assessment over an injected UTC instant.
Fixed capability requirements prevent receipts from selecting their own checks.
Evidence outcomes do not overwrite each other. A matching current failure remains
a blocker even beside a pass. This deliberately requires fresh reconciliation
rather than a last-write-wins health claim.

`scripts/inspect/agentic-baseline.mjs` reads the manifest (or an explicitly supplied
file) using Node 24 native TypeScript support and prints the assessment. Only this
CLI reads files and the clock. It does not connect to a host, invoke a shell,
change a runtime, or enter the app bundle. Input errors do not echo payloads.
The assessment verifies record consistency, not receipt authenticity.

The initial SSH-config-only inspection missed ignored operator metadata. A later
owner-directed read-only probe used the existing key by reference and strict
host-key verification successfully. The two ignored access records disagree on
the account; the account in VPS metadata succeeded. Neither record was modified.
Native contract/interface reconciliation remains necessary; see verification.md.

Tests independently spell out the eight required check sets. Synthetic evidence
covers the freshness boundary, calendar validity, environment/snapshot mismatch,
source basis, conflicts, and CLI exit semantics. The repository manifest is read
by tests and the command, so the implementation is not an orphaned helper.

Later native capture wiring depends on live journal writer, kill switch, governor,
retrieval and scheduler contracts. No copy of their implementation is added here.

## Local use

Run `npm run inspect:agentic-baseline` with the repository-pinned Node 24 runtime.
To inspect a separately collected metadata manifest, run
`npm run inspect:agentic-baseline -- <manifest-path>`.
The default repository manifest resolves relative to the script, not the caller's
working directory. CLI assessment time comes from the local UTC clock.

Exit 0 means all supplied evidence checks qualify; it never grants execution.
Exit 2 means the input is valid but reconciliation remains incomplete. Exit 1
means invalid arguments, unreadable input, malformed JSON or invalid evidence.
The CLI is not a collector and does not authenticate source references.

Current repository evidence remains REPORTED for ingress, journal and recovery,
and HISTORICAL for retrieval, capacity, scheduler, calendar and finance. Each has
an unknown target snapshot and incomplete observed checks. These labels describe
the supplied records, not a diagnosis that any live capability is absent.
