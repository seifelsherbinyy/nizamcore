# NIZAM low-prompt development permissions

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 1 (KWP).
Research date: 2026-09-16.

## Current status: Phase 3 autonomy expansion

See [autonomy-expansion.md](autonomy-expansion.md) for the 2026-09-17 installed
52-pattern policy, 1,347 semantic operations, continuation steering and current limits.
The Phase 2 account below is historical; today's IDE activation remains unobserved.

## Historical status: Phase 2 repair

The Phase 1 runtime policy below caused a reproduced Cedar WASM crash and is superseded.
The installed policy now has 46 shell patterns and 20 rules (5,287 bytes), retaining
557 command coverage cases. Shell allow lists have at most eight patterns; the one
ask.exclude list has 46, not 557. Global permissions are byte-for-byte unchanged.
Spec and script writes, context, skill and subagent capabilities are now allowed.
Documentation fetches match nine hostnames, not URL paths.
Actual Kiro runtime at 2026-09-16T15:10:15Z: 49 merged rules, engineActive=true, fatal=false.
See repair-verification.md in the permission spec for reproduction and verification.

## Historical Phase 1 description (not the current configuration)

## Findings

- Installed application package: Kiro 1.1.14; bundled agent: 1.1.28. Earlier KDE
  foundation documents describe a previous installed version, not this inspection.
- User settings contain 383 legacy trustedCommands entries and Autopilot already set.
  Current global permissions.yaml also exists. Neither global file was edited.
- Kiro 1.x uses capability rules, not a larger legacy settings array. A repo-local
  .kiro/settings/permissions.yaml is NOT the workspace permission destination.
- Confirmed the per-user workspace directory using Kiro's existing migration marker
  and the installed loader/hash implementation. Machine identity stays out of this doc.
- Official precedence is deny > ask > allow across scopes. More allows cannot override
  an enterprise/native ask or deny. Compound shell commands are parsed independently.

## What the policy covers

557 concrete shell entries: 174 actual test files with three supported invocation
forms (522), plus 35 exact development/inspection commands. These are command
variations, NOT 557 different utilities. Test paths come from the live source tree.

Examples:

```text
npm run typecheck
npm run lint
npm run build
npm test
npm run verify:all -- --all
npm test -- src/lib/db/moneyBoundary.test.ts
npm test -- --run src/lib/db/moneyBoundary.test.ts
node node_modules/vitest/vitest.mjs run src/lib/db/moneyBoundary.test.ts
```

Also permits ordinary src/tests/docs file edits, workspace reads, diagnostics, web
search and fetches from ten public documentation URL patterns. Uses built-in file
and web tools instead of blanket shell interpreter/network permissions.

The shell ask rule excludes exactly the allow list, so unlisted commands still ask
when inherited global rules would allow them. MCP operations explicitly ask.
Configuration, contracts, steering, scripts and other non-src/tests/docs writes
remain subject to approval in this workspace. Sensitive-path rules also ask.

This deliberately narrows inherited broad permissions in NIZAM. Other workspaces
and global files are unchanged. Count is not a security boundary or a promise of
complete workflow coverage. New test files and unlisted argument forms can prompt.

## Limits and usage

Use the exact listed single-line commands from the NIZAM root. Do not wrap them in
PowerShell, cmd, bash, inline interpreters, variable assignments or unnecessary cd.
Kiro may normalize commands or apply native checks differently; observed activation
is still required. Do not use this policy to run a production server or live benchmark.

This is consent configuration, NOT a sandbox. Test/build code is executable and can
read/write/network through subprocesses; file rules do not constrain those effects.
Review scripts, cwd, executable resolution and environment; keep synthetic fixtures
and no production keys. Workspace filesystem rules are scoped by the native loader,
not a global filesystem lock. No claim is made to constrain other workspace roots.
Native/enterprise restrictions, ignored-file access, secret detection, untrusted
workspaces and new capability approvals can still prompt.

No automatic commits, pushes, deployments, installs, OAuth, credential lifecycle,
DNS, webhook changes, production spend or gate execution are granted. Those actions
require explicit owner authorization and applicable project authority. No auto-clicker,
trust-all flag, runtime patch, global cleanup or IDE upgrade is used.

## Maintenance and rollback

- Source: scripts/kiro/permissions.mjs. Review template: workspace-permissions.yaml
  beside this document. Template is not loaded directly by Kiro.
- `node scripts/kiro/permissions.mjs` reports inventory without writing.
- `node --test scripts/kiro/permissions.test.mjs` validates the authored policy.
- `--write` is create-only and intentionally refuses to overwrite an existing template.
  Updating the policy requires a reviewed edit/regeneration, tests and comparison with
  the installed copy. Do not overwrite later user approvals.
- Installed copy lives under ~/.kiro/workspace-roots/<workspace-hash>/permissions.yaml.
  Remove only that owned file, after hash comparison and owner authorization, to roll
  back. Since global permissions were preserved, rollback restores broader inherited
  permissions rather than a clean/default policy.

## Fresh-session activation check (not yet observed)

In Kiro, keep Autopilot selected and start a fresh NIZAM chat; reload the window if it
has not picked up the file. Ask it to run `npm run typecheck` from the workspace root.
Observe whether it runs without approval. If it still prompts, inspect the reason and
scope instead of appending arbitrary wildcard rules. Do not probe forbidden operations.

## Sources

- https://kiro.dev/docs/permissions.md
- https://kiro.dev/docs/ide/whats-new-v1/permissions.md
- https://kiro.dev/changelog/ide/1-0/
- Installed application/agent package metadata and permission loader, inspected read-only.

A public issue about multiline matching (kirodotdev/Kiro #6189) describes CLI 1.27,
not proof of a defect in this IDE. No CLI regex workaround was installed.
