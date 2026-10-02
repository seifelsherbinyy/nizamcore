# Telegram window TW0 verification receipt

Date: 2026-09-15. Authority: PFOS Contract 14 section 10. Phase TW0.
Outcome: local documents authored and directly reviewed; repository acceptance 19/21.
Telegram runtime restoration, installation, capture and live readiness are NOT delivered.

## Scope

Created requirements/design/tasks/handoff; appended Contract 14 section 10 and PFOS index/log.
No source, tests, runtime templates, acceptance scripts or package files changed by this task.
Pre-existing edits/untracked work preserved. No exposed credential used or copied, no host/
provider connection, credential lifecycle, native modification, G1-G8 operation, commit/push.

## Commands actually run and observations

Commands used native PowerShell with Node v24.14.1; npm invoked as npm.cmd to avoid shim ambiguity.

| Exact check command | Observed result |
|---|---|
| `git status --short` | Existing dirty tree before work; dirty tree after additive documentation |
| `git diff --check` | Exit 0, no whitespace findings |
| `powershell.exe -NoProfile -Command "npm.cmd test -- --run src/server/hermes src/server/telegram src/server/process/singleWindowFlow.test.ts; exit $LASTEXITCODE"` | Exit 0; 26 files, 365 tests passed |
| `powershell.exe -NoProfile -Command "npm.cmd run verify:all -- --all; exit $LASTEXITCODE"` | Exit 1; 19 of 21 executed checks passed |

The unchanged full harness actually ran typecheck, lint, all tests, build, launch-path,
source/financial/Drive/security/bundle checks and repository disposition checks. Its machine
report `.loop/tmp/test-results.json` reported 3009 total, 3009 passed, zero failed, success true.
No separate standalone typecheck/lint/build command is claimed.

Passing harness checks: AC16, AC10, AC01, AC07, AC19, AC08, AC09, AC11, AC18, AC02, AC03,
AC04, AC13, LOOP, AC05, AC05b, AC06, AC08b, AC12.
Failing: AC14 working tree clean; AC15 push-ready state. AC15 reported 24 dirty entries.
Cause: existing user work plus these uncommitted documents. No cleanup, staging, commit,
threshold reduction or acceptance edit attempted. This is NOT a green repository handoff.

Full harness ran while the initial handoff-write failure was being corrected. Final handoff
and this receipt are documentation-only; explicit artifact checks run after creation cover
untracked/append regions. No claim that tracked-only secret scans cover untracked artifacts.
AC12 checks the original five-contract index/log, not PFOS additions; PFOS registration was
reviewed directly rather than treating AC12 as proof of the new addendum's consistency.

## Direct document verification

Inline Python checks executed against explicit paths:

- SHA-256 of original byte prefixes for Contract 14/index/log matched pre-edit fingerprints.
- Entire package.json, scripts/verify/all.mjs and src/lib/db/schema.ts matched pre-edit bytes.
- 15 unique TW requirement IDs and 12 planned test rows; all requirements referenced in tasks.
- Seven cited implementation/evidence/handoff paths exist.
- Explicit sensitive-pattern scan of seven authored/new regions including untracked files:
  token-shaped values, Telegram bot URLs, private-key headers, provider-key shape and IPv4.
  No matches. This is bounded pattern coverage, not proof that every possible secret is absent.
- Direct review checked consumer ownership, metadata trust, effect/delivery separation,
  cancellation ordering, same-process environment exposure, capture honesty and authority.

TW-T01 through TW-T12 are planned acceptance cases, NOT new tests executed in this increment.
Existing 365 focused tests remain Slack-v2/transport/offline-regression evidence, not proof of
restored Telegram functionality. Existing 3009-test suite is not live VPS evidence.

## Execution failures and limits, not hidden

- `agent spawn --help` was blocked by an environment deny rule. No alternate agent route
  attempted. Independent review unavailable; direct producer review is not independent approval.
- Initial oversized multi-document command failed Windows CreateProcess length limit before
  execution. Split foreground writes succeeded and were read back with view.
- A compound background write/test command ended with passing tests but did not create the
  handoff. Explicit subsequent artifact audit failed FileNotFoundError. A foreground exclusive
  create fixed the missing file; view and repeated artifact audit then succeeded. Background
  command success alone was not accepted as document creation evidence.
- Repository gate failed AC14/AC15. Preserved and reported, not bypassed.

## Outstanding full-delivery blockers

Current native consumer/interfaces and governing privacy/retention/limits remain unreconciled.
A protected owner-managed replacement credential and private identity handoff are required for
live validation. Slack-v2 remains live policy until reviewed cutover. Native writes, host/
transport changes, Telegram sends and production spend require explicit scoped authority.
Capture additionally needs native writer/read-back/recovery reconciliation. No human gate is
marked or tested. The overall autonomous objective is not marked complete.

## Read-only follow-up (2026-09-15)

Owner continued the scoped inspection request. Five reviewed SSH probes returned sanitized
metadata/source AST results; receipt `inspection-2026-09-15.md`. No exposed Telegram token,
provider call, remote write, application execution, private data or human-gate operation.
Local changes in this follow-up are documentation only. No runtime tests rerun; earlier gate
outcomes are not promoted to current live readiness. TW-A3 remains partial, not completed.

## Gateway wiring follow-up

Five further reviewed read-only probes succeeded; exact commands and GW01-GW11 evidence in
`wiring-trace-2026-09-15.md`. Corrected unsupported container-gateway and kill-switch-marker
inferences. No deployed configuration values, provider calls, application execution or remote
mutations. No source/test changes or new runtime verification; prior 19/21 gate is historical.

## Supervisor and extensions follow-up

Seven reviewed read-only probes succeeded; exact commands and qualified findings in
`supervisor-extensions-2026-09-15.md`. Actual managed service/profile identified; configured
knowledge MCP source candidate traced. No plugin/MCP/app execution, remote mutations, provider
calls or private content. Config/environment values were projected internally, never emitted.
No source/test changes or full harness rerun. Prior acceptance remains historical.

## Remaining bridges follow-up

Nine successful read-only probes plus one corrected probe syntax failure; local construction/
anchor failures and limitations recorded in `remaining-bridges-2026-09-15.md`. Source inspected,
not executed. Camofox capabilities, knowledge static launcher and actual filter semantics
identified; container-wrapper script mismatch remains unresolved. No runtime/harness rerun.

## Container script diagnostic fix

Owner requested investigation/repair. Three read-only probes established EACCES in host view
and an existing 11219-byte syntax-valid WHOOP health script via Docker archive. Two owned
temporary probes fixed to distinguish inaccessible/missing, with ten synthetic guard cases
passing. Failures and commands in `container-script-resolution-2026-09-15.md`. No deployment
repair, permission change, docker exec, provider call or native write. Full gate pending below.

Diagnostic-correction repository check actually run:
`powershell.exe -NoProfile -Command "npm.cmd run verify:all -- --all; exit $LASTEXITCODE"`.
Observed exit 1, 19/21 checks passed. AC14/AC15 fail on dirty working tree (24 entries),
including protected pre-existing work and this thread's documentation. Typecheck, lint,
full tests, build and all other harness checks passed. No check edited, no cleanup/commit.
Machine report: 3009 total, 3009 passed, 0 failed; success=True.
