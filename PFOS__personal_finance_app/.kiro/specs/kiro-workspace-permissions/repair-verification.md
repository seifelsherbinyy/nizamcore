# Phase 2 permission-engine repair evidence

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 2 (KWP).
Date: 2026-09-16. Installed IDE 1.1.14, agent 1.1.28, Cedar WASM 4.9.1.

## Cause and correction

Original 557-entry exclusion reproduced `RuntimeError: memory access out of bounds`
in an isolated Node invocation of Kiro's installed Cedar partial evaluator. The
installed compiler emits one AND predicate per exclude entry. Match entries instead
become separate policies. Splitting match lists alone would not fix this defect.
The native log labels engine failures user/permissions generically; this was not proof
of a bad global file. Global permissions remained byte-for-byte unchanged.

Runtime shell patterns reduced to 46, with allow batches <=8; one 46-entry exclusion
preserves inherited-allow control. 557 concrete invocation cases remain tested.
A 64-pattern budget is a conservative project limit, not a documented vendor maximum.
Installed YAML shrank from 42,249 to 5,287 bytes. SHA-256:
f194c194fef113499cb605fdda82f33cba8fff06c0b5d131ce151d008fd420be.

Spec/script writes and context/skill/subagent capabilities now permit ordinary local
work. Kiro's web evaluator extracts hostnames, so nine hostname patterns replace the
incorrect full-URL patterns. No native/enterprise restriction or human gate was removed.

## Exact commands and observed results

Executed using native Node through PowerShell, not the Bun-backed tool alias:

- `node --test --test-reporter=dot scripts/kiro/permissions.test.mjs`: exit 0.
- `node --test --test-reporter=tap scripts/kiro/permissions.test.mjs`: 588 passed,
  zero failed/skipped. All prior command and negative-input coverage retained.
- `node scripts/kiro/permissions-cedar.mjs <installed-cedar-module> <original-workspace-backup>`:
  reproduced the original WASM bounds crash. Placeholders here redact local paths;
  actual explicit local paths were supplied, with no download or runtime patch.
- `node scripts/kiro/permissions-cedar.mjs <installed-cedar-module> <global-permissions> docs/kiro/workspace-permissions.yaml`:
  10 partial-capability evaluations and 10 synthetic allow/forbid decisions passed
  across 33 user+workspace rules. Kiro's ask maps to Cedar forbid until consent.
  This probe mirrors the inspected compiler subset, not the entire IDE shell parser.
- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0.
- `npm run build`: exit 0 including PWA generation.
- `npm run verify:all -- --all`: exit 1, 19/21. AC14 and AC15 fail because the tree
  is dirty (54 entries). Application suite: 3,141 passed, zero failed.

Two probe runs initially failed because the test expected `success`; installed API
inspection showed valid partial evaluation returns `residuals`. The probe was fixed,
not the acceptance criteria. An initial nested PowerShell quoting attempt failed
before reading data; it was replaced with a reviewed script. No hidden success claims.

## Actual IDE evidence

Native log after installation, 2026-09-16T15:10:15.005Z:
`[PolicySession] rebuild() complete: 49 rules parsed, engineActive=true, fatal=false`.
The prior installation logged engineActive=false/fatal=true and the reproduced crash.

Aki submitted a bounded smoke request through the existing Kiro chat. Observed UI:
- `npm run typecheck` ran with exit 0, no diagnostics and no approval interruption.
- Main agent delegated native file writing because its own toolset lacks a write tool.
- Subagent created only `activation-smoke.md` in this spec directory, then read it back.
- Kiro reported both halves passed without approval interruption or policy error.
- Aki did not click an approval button. Autopilot remained enabled; no reload was needed.

This verifies the previously failing command/delegation/spec-write/read paths, not
all conceivable tools or future sessions. No host, OAuth, production API, gate,
credential lifecycle, commit or push was exercised.

## Scope and remaining decisions

Unlisted shell commands and MCP still ask; sensitive/authority edits remain governed.
Build/test scripts can execute code; this is consent configuration, not a sandbox.
The concrete ingress owner, missing host identity/access, cadence alternatives and
working-tree disposition cannot be resolved by granting IDE permissions. Broad owner
approval allows design continuation, not fabricated evidence or arbitrary cutover.
Existing application files and unrelated changes were preserved. Policy backups and
hash manifests are outside the repository in Aki's local temporary folder.

Sources: https://kiro.dev/docs/permissions.md and installed compiler/API/log evidence.
No public documented numeric pattern limit was established by research.
