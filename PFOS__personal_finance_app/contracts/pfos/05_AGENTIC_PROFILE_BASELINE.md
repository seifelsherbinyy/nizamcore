# Contract 05 addendum: Agentic Profile baseline evidence

NIZAM-derived from Contract 05 (readiness), Contracts 06, 12 and 14, and the
owner's first-increment instruction. UPOI draft requirements 1.1-1.4 are
supporting alignment only, not additional implementation authority.
Phase 0: offline baseline reconciliation. Version 1.0.0.
Status: governs the authorized local evidence-reporting slice only.

## Scope

The owner selected one Slack-connected, host-native Hermes runtime. Preserve
that direction without inferring installed versions or completed deployment.
This addendum does not amend money, privacy, store isolation, credential,
external action, or human-gate rules. It grants no runtime authority.

The local knowledge readiness score measures index coverage, not operational
readiness. Preserve that score and the existing runtime adapter API unchanged.
Add a separate read-only evidence report, exposed by a local inspection command.
It is not a new governor, database, writer, or production health probe.

## Required evidence dimensions

| Capability | Required checks |
|---|---|
| ingress | code, runtime |
| journal | code, persistence |
| retrieval | code, runtime |
| capacity | code, runtime |
| scheduler | code, schedule |
| calendar | code, runtime |
| recovery | code, mirror |
| finance | code, runtime |

All eight capabilities must occur exactly once. Check requirements live in code,
not in submitted receipts: dropping a required check cannot promote readiness.
Each capability targets one explicit environment and a nullable SHA-256 snapshot
hash. The snapshot represents code, relevant configuration and policy, including
uncommitted changes, not merely a Git commit. No hash is invented for an
uninspected target. Independent services may have different target hashes.

## Evidence rules

1. Accept only schema version 1.0.0, closed objects, known capabilities/checks,
   globally unique receipt IDs, valid UTC calendar instants, lowercase SHA-256
   hashes, and nonempty bounded symbolic references. Raw text is not supported.
2. Each receipt declares basis OBSERVED, USER_REPORTED or HISTORICAL; outcome
   PASS, FAIL or UNKNOWN; environment; snapshot hash (nullable); check;
   nullable timestamp and source reference. OBSERVED requires a snapshot hash
   and a timestamp. Unknown historical observation times stay null, not invented.
3. CURRENT means every required check has fresh OBSERVED PASS evidence matching
   the target environment and exact snapshot. Expiry is inclusive: an observation
   at the freshness limit is stale. Future receipts and invalid report clocks
   reject the report. The report clock is injected; no hidden clock reads.
4. Matching fresh observed FAIL evidence blocks CURRENT even if another receipt
   passes. Preserve disagreement as CONFLICTING_EVIDENCE, not latest-wins.
   Historical/user reports never establish current operational success or failure.
5. Missing target hash blocks CURRENT. Report MISSING_CHECK, STALE_EVIDENCE,
   BASELINE_MISMATCH and ENVIRONMENT_MISMATCH separately where applicable.
   Fallback states are PARTIAL (some observed evidence), REPORTED,
   HISTORICAL, or UNKNOWN. No evidence is not evidence of absence.
6. A report is a deterministic assessment of supplied records, not authentication
   of them. It does not fetch receipts, verify source bytes, sign attestations,
   grant tools, promote models, or authorize deployment. A later trusted collector
   must establish receipt origin and snapshot integrity before runtime use.
7. Use a fixed 24-hour freshness window for this inspection report only. This is
   not a general memory TTL or a provider health SLA. Every rerun reevaluates it.
8. File/CLI errors fail with a generic error; never echo untrusted payloads.
   A valid but noncurrent report returns exit 2; all-current returns exit 0;
   malformed input returns exit 1. Even exit 0 is not permission to act.

## Boundaries and unresolved conflicts

- Drive stays drive.file and holds encrypted data, never keys or secrets.
  Historical secret-backup reports do not amend that invariant.
- Host-local execution is not hostile-agent containment. An in-process grant
  check cannot constrain an agent that can bypass it through host shell access.
- Strict-local material is not forwarded to Slack or remote models. The highest
  local-only tier is excluded from the VPS. No privacy label is remapped here.
- One EGP is 1000 integer milliunits; this slice contains no monetary values.
- Internal scheduler profile ownership must be reconciled with the single ingress
  runtime before wiring. Do not start a second scheduler or gateway.
- Existing local core checkout changes are protected. Capture implementation waits
  for authoritative native code/contracts; do not duplicate it in this repository.

## Acceptance

AB01 closed schema, invalid-date, duplicate, unsupported-check and version refusal.
AB02 every literal capability/check requirement is independently pinned in tests.
AB03 source basis, environment, exact snapshot, time and outcome all gate CURRENT.
AB04 conflicting pass/fail remains blocked, missing evidence never becomes CURRENT.
AB05 command consumes the real repository manifest and emits metadata-only reports.
AB06 current manifest contains no current VPS attestation or invented target hash.
AB07 focused tests, typecheck, lint, build and full repository gate are reported
truthfully; unrelated working-tree failures never justify cleanup or suppression.

Rollback: stop using the inspection command; no production hook or data migration
is installed. Preserve evidence and owner changes. No reset or deletion required.
