---
inclusion: always
---

# Low-prompt local development

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 2 (KWP).

Use native file tools for edits and reads, and native web tools for public research.
The owner configured a per-user NIZAM command policy. Its reviewable catalog is
`docs/kiro/workspace-permissions.yaml`; it is not loaded from the repository itself.
Use simple single-line commands from the NIZAM root: `npm run typecheck`,
`npm run lint`, `npm run build`, `npm test`, `npm run verify:all -- --all`,
or `npm test -- <existing-test-path>` using a src test path. New test paths are covered by compact patterns.
Avoid unnecessary shell wrappers, variable assignments and directory changes.

Read scripts before execution. Use synthetic fixtures and no production environment.
An allowlisted command is not authority for deployment, production spend, credential
work, commits, pushes or any human gate. Never modify permission files to evade a
prompt; report its reason. All existing project and human-gate boundaries still apply.
Details and remaining activation limits: `docs/kiro/workspace-permissions.md`.

Local src/tests/docs/scripts and .kiro/specs edits, context, skills and subagent
invocations are allowed by the repaired operator-managed policy. Delegate bounded
research/design/test tasks; the parent restrictions still apply. Continue independent
local work when a live integration is blocked; record the blocker rather than stopping
all progress. Do not infer actual access or deployment state from permission grants.
The owner approved continuation of the researched design. Do not ask again whether to
write the design; unresolved concrete target/cutover/cadence choices still need evidence.

## Objective continuation (Phase 3, KWP13-17)

Once the owner gives an objective, continue inspect -> plan -> implement -> test ->
diagnose -> repair -> retest -> validate -> document. A successful step is not a
reason to ask for "continue". Announce bounded plans, then execute safe next steps.
Use checkpoints/backups; never automatic commits, stashes, resets or cleanup.
If a check fails, inspect the failure and attempt a relevant repair. After repeated
failure with no new evidence, report the concrete blocker rather than loop forever.
Continue independent safe work when one integration is blocked. Stop at completion,
missing necessary information/authorization, or a genuine high-risk boundary.

Read scripts before running and use the NIZAM root. For a single task-owned source
file use `node scripts/kiro/develop.mjs lint src/example.ts`, `format-check` or
`format`. Substitute an existing safe src TypeScript path; no extra flags are accepted.
Never format unrelated existing user changes. Native file tools handle ordinary
workspace edits; public fetch tools handle docs. No arbitrary shell/interpreter prefix
is approved. A missing dependency needs source/version/lifecycle review and applicable
installation authorization, not automatic npx/download execution.

Autopilot is a native IDE mode; this steering only describes continuation behavior.
Permissions are separate and not a sandbox. Never widen them or rewrite a command to
evade an ask/deny. Preserve G1-G8 and both human-only control records without execution,
testing, substitution or completion. Report only checks actually run and observations.
See docs/kiro/autonomy-expansion.md for current coverage, limits and rollback.
