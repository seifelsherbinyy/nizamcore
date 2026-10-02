# Kiro workspace permissions contract

NIZAM-derived from the owner's 2026-09-16 request to reduce repetitive approvals
and cover 500+ development commands. Program KWP, Phase 1: local IDE permissions.
Complements KDE; does not modify its Phase 1 scope or supersede AGENTS.md.

## Requirements

KWP01 Use the installed Kiro 1.x capability schema, not legacy trustedCommands.
KWP02 Install only into the independently confirmed per-user NIZAM workspace
permission directory after explicit folder access approval. Preserve global settings,
existing permission files and all pre-existing repository changes. No IDE upgrade.
KWP03 Inventory at least 500 unique, concrete local commands from existing tests
and reviewed development entrypoints. Never pad with arbitrary interpreters,
package installation, credential tools, production APIs or privileged commands.
KWP04 Allow only enumerated shell commands; add an ask rule excluding that same
list so inherited broad global allow rules cannot silently authorize other shell
commands. Preserve native/enterprise ask and deny precedence. Never bypass prompts.
KWP05 Allow normal source/test/docs edits and public documentation research.
Keep sensitive data, human controls, configuration/authority edits and external
mutations outside silent approval. MCP operations remain approval-required.
KWP06 Commands run only in the intended repository with reviewed scripts, synthetic
fixtures and no production environment. This is consent configuration, not a sandbox:
trusted test/build scripts can execute code and shell rules do not enforce cwd.
KWP07 Verify deterministic generation, schema, inventory, negative command cases,
precedence and installed byte equality. Run unchanged repository checks. Distinguish
structural verification from actual Kiro activation; do not claim zero prompts.

## Unchanged boundaries

Money remains integer milliunits (1 EGP = 1000); deterministic engines alone source
financial values. Drive stays drive.file, encrypted data only, no keys/secrets.
No application imports tooling. No real ledgers or deployment particulars in artifacts.
No G1-G8, credential lifecycle, OAuth consent, host/DNS/webhook mutations, production
spend, commits, pushes or destructive cleanup are authorized by this policy.
Never execute, test, populate or complete a human gate record.

## Rollback

Remove only this increment's installed file after checking its hash and obtaining
owner authorization. Never restore over later edits. Global settings stay unchanged.

## Phase 2 repair amendment (2026-09-16 owner request)

KWP08 Supersedes Phase 1's runtime enumeration in KWP03-04: retain 500+ concrete
commands as coverage fixtures, but compile a compact set of test-path globs and
reviewed commands. Limit every emitted match/exclude list to 64 patterns and allow
match lists to 8. These are conservative project budgets, not vendor limits.
Never split exclusions into independent ask rules: their union changes the policy.
KWP09 Normal local implementation includes scripts and .kiro/specs writes, context,
skills and delegated subagents. Parent restrictions still apply. Spec authorization
is not deployment authorization. Permission edits remain operator-controlled.
KWP10 Back up both user and workspace policies. Global match-only rules may be
rebatched without semantic change if needed; never broaden or delete existing rules.
Native compiler evidence takes priority over speculative repair steps.
KWP11 Test the installed Cedar WASM partial-authorization path in an isolated process
with synthetic requests and inspect native policy-reload evidence. YAML parsing is
not runtime proof. Do not patch Kiro, suppress a deny, or execute a gated action.
KWP12 The owner's approval permits continuing the researched design and local
implementation planning. Unresolved target identity and unchosen ingress/cadence
alternatives remain decisions, not facts created by permission configuration.

## Phase 3 autonomy expansion (2026-09-17 owner request)

KWP13 Preserve Phases 1-2 checks and boundaries. Count semantic operations separately
from invocation aliases: one test target is one operation, and lint, format-check and
format of a source file are distinct operations. Require 500+ concrete action/target
pairs from existing source files, not hypothetical ecosystems or wildcard cardinality.
KWP14 Add a reviewed local dispatcher for lint/format-check/format of one src TypeScript
file. Reject unknown actions, extra arguments, traversal, absolute paths, symlinks and
wrong cwd before subprocess execution. Use pinned workspace CLIs with argv arrays and
shell:false. The dispatcher is trusted mutable project code, NOT an OS sandbox.
KWP15 Keep bounded native patterns and a single matching ask.exclude. General package
installers, interpreters, Git writes, Docker daemon operations, remote APIs and deployment
remain gated. No trusted development host/database has been established by this task.
KWP16 Set documented workspace Autopilot mode only if supported by installed metadata;
otherwise retain the observed user Autopilot setting. Always-included steering requires
safe continuation and bounded diagnosis without approval evasion or unbounded retries.
KWP17 Validate negative dispatcher cases without executing prohibited commands; exercise
native Cedar and safe positive commands. Distinguish native reload from fresh-chat prompt
and continuation evidence. Preserve all earlier acceptance checks and global settings.
