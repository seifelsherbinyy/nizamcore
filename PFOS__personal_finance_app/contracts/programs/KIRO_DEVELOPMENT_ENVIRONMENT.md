# Kiro development environment contract

NIZAM-derived from the owner's Kiro Execution Upgrade instruction, 2026-09-16.
Program ID: KDE. Phase 1: workspace foundation. Status: local implementation authority.
This governs developer tooling, not deployed agents or financial policy. Existing
PFOS contracts 05, 06 and 12 retain their runtime scope. AGENTS.md and applicable
steering retain precedence. No existing contract is superseded.

## Scope

KDE01 Preserve existing user changes and global configuration. Capture workspace
configuration backups outside the repository before edits; record owned paths.
KDE02 Use standard workspace skills with narrow activation descriptions and shared
on-demand references. Preserve every existing spec and historical authority body.
KDE03 Validate our authored metadata subset, registry references, unique skill names,
local paths and explicit activation-test coverage. Missing/malformed input fails.
Validation is structural, not proof of Kiro activation or hostile-code containment.
KDE04 Inspect original sources and package metadata before installation. Pin executable
dependencies in a separate developer-tool lockfile; disable lifecycle scripts. Never
load browser tooling into the application bundle. No automatic updates or installs.
KDE05 Keep evidence dimensions separate: configuration, command execution, Kiro activation
and live operation. A successful command never establishes IDE activation. Missing
credentials, runtime support or authorization remains an explicit blocker.
KDE06 Browser trials use a fresh isolated context, synthetic/empty app state, a loopback
server and blocked external requests. Never attach to a personal browser profile,
load real ledgers, perform OAuth, or write to a provider. Stop only owned processes.
KDE07 Reuse existing focused checks and the unmodified full repository harness. Preserve
all failures and test floors. Baseline failures never become permission to skip checks.
KDE08 Registry updates and transcripts are metadata/redacted evidence only. Source URLs
and synthetic fixture values are permitted; secrets and deployment particulars are not.

## Boundaries

Money remains integer milliunits, 1 EGP = 1000. Deterministic engines alone source money.
Drive stays drive.file and holds encrypted data, never keys/secrets. Source/test headers
and routing/benchmark bundle isolation remain unchanged. No new money implementation.
Routine local coding, inspection, reversible tests and public documentation research
are normal development work, not individually gated actions.
No gate record is executed, tested, populated or marked complete. G1-G8, host mutation,
credential lifecycle, production spend, OAuth consent, DNS, webhooks, cross-repository
writes, commits and pushes are outside this increment. Neither a skill nor a receipt
creates authorization. No global config or IDE upgrade is included.

## Acceptance and rollback

Unit tests cover valid and invalid metadata, traversal, duplicate identity, missing files,
false readiness and browser-path restrictions. Exercise actual local app navigation and
regression suites, and document unperformed Kiro/GitHub-auth/VPS trials. Reconcile owned
changes against baseline hashes. Run npm run verify:all -- --all without modifying it.
Rollback is a reviewed inverse patch to owned files only, after checking for later edits;
backup restore is never an unconditional overwrite. Installed tooling can remain unused.
Do not remove another session's files, browser, process, profile or configuration.
