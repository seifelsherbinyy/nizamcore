# NIZAM Kiro autonomy expansion

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 3 (KWP13-17).
Research and implementation: 2026-09-17. Supersedes Phase 2 counts, not its safeguards.

## Installed configuration

- Installed Kiro application 1.1.14; bundled agent 1.1.28. These were read from the
  installed packages, not inferred from current online documentation.
- Native policy: `~/.kiro/workspace-roots/<NIZAM-workspace-hash>/permissions.yaml`.
  Its existing migration marker independently identifies the NIZAM root.
- Reviewable repository copy: `docs/kiro/workspace-permissions.yaml`. Kiro does NOT
  load permissions from this repository copy. It is byte-identical to the installed file.
- 21 workspace rules, 52 shell patterns, 5,876 bytes. Allow batches <=8; a single
  ask.exclude with the same 52 patterns prevents inherited broad allows from silently
  authorizing unlisted commands. These budgets are project limits, not vendor limits.
- Installed SHA-256:
  `81ff83c22d8e1c6b4aa4ad0ddf45bfd0cb4fea8a60071bbebd56fbfdbe0ff69b`.
- User `kiroAgent.agentAutonomy` is already `Autopilot`. It is unchanged. Official
  documentation and installed code confirm that key. No workspace override was added:
  the installed package did not expose a setting declaration confirming its scope.
- Global permissions/settings/MCP, shell profile and OS security remain unchanged.
  Global MCP inventory: 12 servers, 10 with autoApprove lists; values were not printed.
  Workspace MCP config and workspace/global hooks directories were absent at inspection.
  No hook, MCP, CLI agent, ACP client or background continuation service was installed.

## Coverage, without counting aliases twice

| Concrete action | Existing targets | Operations |
| --- | ---: | ---: |
| Lint one source file | 391 TS/TSX files | 391 |
| Check formatting of one source file | 391 TS/TSX files | 391 |
| Format one task-owned source file | 391 TS/TSX files | 391 |
| Run one test file | 174 tests | 174 |
| **Conservative semantic total** | | **1,347** |

These are action/target pairs, NOT 1,347 utilities or ecosystems. The threshold is
exceeded within NIZAM's actual TypeScript workload. Native file operations, whole-app
build/typecheck/lint, public research, diagnostics, skills and delegation are additional
coverage, not numeric padding. The previous inventory still tests 562 unique command
strings, including alternate test invocation forms; those aliases do not increase the
semantic total above. Coverage is generated from live paths by `semanticInventory()`.

New family: `node scripts/kiro/develop.mjs <action> <source-path>`.
Actions: `lint`, `format-check`, `format`. Example:

```text
node scripts/kiro/develop.mjs lint src/lib/money/currency.ts
node scripts/kiro/develop.mjs format-check src/lib/money/currency.ts
```

Only format a file owned by the current task. The dispatcher accepts exactly two
arguments, an existing simple src TypeScript path, the real NIZAM cwd, and non-symlink
path/tool components. It invokes the locked local ESLint/Prettier CLI with argv arrays,
`--` before the target, and `shell:false`. It does not install packages, accept extra
flags, evaluate code strings or silently repair a failed quality check.

Exact additions also include `npm ls --depth=0`, `npm outdated --offline`,
`curl.exe --version` and focused permission/development test commands. Offline outdated
is cache-dependent; it has not been exercised and is not proof of registry freshness.

## Permission architecture and limitations

Current Kiro YAML uses capability/match/exclude/effect. Effects resolve deny > ask >
allow across scopes. Shell patterns support `*`, not regex, `?`, character classes or
filesystem-style glob semantics. Kiro documents independent parsing of compound shell
subcommands. This project's fixture glob matcher and Cedar probe are NOT that parser.

Workspace storage selects which project receives consent rules; it does not create an
OS sandbox or enforce cwd for arbitrary commands. Trusted build/test/config/plugin code
can execute arbitrary code, read files or network. Phase 2 shell read prefixes such as
`Get-Content *` and `rg *` remain unchanged and do not enforce native filesystem gates.
Consequently secret isolation and adversarial-code containment are NOT guaranteed here.
The dispatcher narrows its own inputs, but is itself editable project code, not a tamper-
proof security boundary. Native/enterprise restrictions remain effective and can prompt.

Use native filesystem tools for workspace read/edit/create operations and native web
fetch/search for public docs. Do not use broad shell wrappers merely to evade prompts.
No whole executable grants were added for npm/npx/node/PowerShell/git/curl/Docker/SSH.

| Family requested | Current disposition |
| --- | --- |
| Local build/test/typecheck/lint/format | Pre-authorized reviewed entrypoints |
| Workspace file operations | Existing native scoped tools; controlled deletion still needs ownership review |
| Git status/diff/log/list | Reviewed read commands allowed |
| Git add/commit/push/restore/reset/merge/rebase/stash | Not silently authorized; preserve user work and NIZAM approval gates |
| npm package metadata | Exact local inspection allowed |
| Dependency installation/update/removal | Review source, version and lifecycle scripts; not blanket-authorized |
| Python/Rust/Go/Java and other package managers | Not this project's active toolchain; no speculative grants |
| GitHub CLI writes/releases/workflows | Approval required; existing credentials are not task authorization |
| Docker/Compose | Not discoverable on inspected PATH; no daemon operations attempted |
| SSH/SCP/rsync, staging deployment, migrations | No trusted dev host/database established; approval remains |
| Network downloads/archive/process management | No unrestricted execution/extraction/termination; use bounded reviewed tools |
| Browser automation | Existing separate project tooling retained; no additional launch in this increment |
| MCP | Workspace ask remains; global autoApprove is not treated as unconditional authority |
| Credentials, production, G1-G8 and human controls | Unchanged high-risk boundaries, never exercised |

## Continuation

Always-included `workspace-development-permissions.md` now explicitly requires continuing
from success to the next safe step, repairing relevant failures, using recoverable
checkpoints, and completing independent work despite a blocked integration. Stop at
completion, missing essential information/authorization or high-risk boundaries. Repeated
failure without new evidence is a blocker, not permission to loop indefinitely.

This is steering, not a grant or a guarantee against context/model/product limits.
Autopilot is Kiro's native coarse mode; permissions remain the fine-grained layer.
No auto-clicker, stop-hook loop, trust-all preset or prompt-based permission bypass exists.

## Validation evidence

Executed on native Node 24.14.1 and npm 11.11.0 via PowerShell, not the Bun-backed alias.

- `node --test --test-reporter=tap scripts/kiro/permissions.test.mjs scripts/kiro/develop.test.mjs`:
  598 passed initially, zero failures/skips. Original permission tests were unchanged.
- Added a real isolated formatter test, then ran
  `node --test --test-reporter=spec scripts/kiro/develop.test.mjs`: 6/6 passed.
  A synthetic source file under Aki temporary storage was formatted and rechecked by the
  pinned Prettier package. No existing source was formatted.
- `node --test --test-reporter=dot scripts/kiro/permissions.test.mjs scripts/kiro/develop.test.mjs`:
  exit 0 after that addition (599 tests).
- `node scripts/kiro/permissions.mjs`: 174 tests, 562 concrete invocation fixtures;
  read-only inventory, templateWritten=false.
- `node scripts/kiro/permissions-cedar.mjs <installed-cedar-module> <global-policy> docs/kiro/workspace-permissions.yaml`:
  10 native partial-capability evaluations and 1,366 synthetic decisions passed across
  34 global+workspace rules. This mirrors the previously inspected compiler subset.
  All 1,347 semantic operations allowed; unapproved high-risk command strings forbid
  until consent (Kiro ask), without executing those strings or any human gate.
- `node scripts/kiro/develop.mjs lint src/lib/money/currency.ts`: exit 0.
- `node scripts/kiro/develop.mjs format-check src/lib/money/currency.ts`: exit 1,
  pre-existing style issues reported. This is a working failure signal, not a pass;
  the unrelated existing file was left unchanged.
- `npm ls --depth=0`, `curl.exe --version`: successful local metadata queries.
- `git diff --no-ext-diff --no-textconv --check`: no whitespace errors; existing CRLF
  conversion warnings on three unrelated steering files.
- `node scripts/kiro/validate.mjs`: structuralValidation=PASS, no findings.
- `npm run typecheck`, `npm run lint`, `npm run build`: exit 0; production/PWA emitted.
- `npm run verify:all -- --all`: exit 1, **19/21**. AC14/AC15 fail on the dirty
  working tree (54 entries). All other checks pass; application tests 3,141/3,141.
  Receipt: `.kiro/specs/kiro-workspace-permissions/autonomy-verification.md`.

Not observed today: actual new-policy Kiro reload, fresh-chat terminal prompts, or
multi-step continuation. No running Kiro window was found. Latest policy log was from
September 16 and belongs to the previous policy; it is not reused as today's proof.
No measured percentage reduction in prompts is claimed. No Docker, deployment,
credentialed GitHub, package install or SSH operation was attempted to manufacture proof.

## Sources and conflicting advice

Primary/current, fetched 2026-09-17:

1. https://kiro.dev/docs/permissions.md : YAML locations, patterns, precedence,
   compound commands and ACP presets. Presets are ACP session metadata, not IDE settings.
2. https://kiro.dev/docs/ide/chat/autopilot.md : native Autopilot/Supervised and
   `kiroAgent.agentAutonomy`. Autopilot does not override capability ask/deny.
3. https://kiro.dev/docs/ide/chat/terminal.md : persistent consent and Windows shell profile.
4. https://kiro.dev/docs/hooks.md : event automation, not justification for bypassing consent.
5. https://kiro.dev/docs/mcp/configuration.md : separate MCP config and autoApprove layer.
6. https://kiro.dev/docs/cli/v3/permissions.md : CLI 3 glob migration. The page conflicts
   internally about default approvals and trust-all flags. No CLI was installed/configured,
   and those ambiguous statements were not used to authorize anything.
7. Installed agent loader and Cedar WASM, read-only package metadata and policy marker.

Secondary, not authority:

- https://github.com/kirodotdev/Kiro/issues/7842 (April 2026, IDE 0.11.133): user report
  of write/hook prompts despite Autopilot. Supports tracing the actual prompt layer, not
  deleting security hooks or assuming this old defect exists in 1.1.14.
- https://github.com/EndSpiel39/Kiro-Autopilot-Safe-Config : inspected README recommends
  legacy trustedCommands=["*"] plus a short denylist. Rejected: outdated schema and an
  incomplete security boundary. Popularity/activity was not established.
- GitHub and Reddit-targeted public searches surfaced approval-loop discussions but no
  independently verified current Reddit fix that justified further grants. One initial
  public search failed with provider rate limiting; later searches succeeded.

## Rollback and maintenance

Backup directory: `~/.aki/tmp/nizam-kiro-autonomy-20260917/`.
It contains baseline workspace copies, native/global policy copies, manifest hashes
and an install receipt. Nothing was committed, pushed, reset or cleaned.

1. Obtain owner approval for rollback. Compare current hashes with this increment's
   post-change receipt. If anything changed later, stop and review an inverse patch.
2. Restore the prior native policy from `native-policy.yaml`, not by deleting the policy:
   deletion would reactivate broader inherited global grants. Preserve the global file.
3. Apply only this increment's inverse workspace edits from the backups. Newly created
   files are develop.mjs, develop.test.mjs, this report and the Phase 3 verification receipt.
   Never remove them without checking for later edits and owner authorization.
4. In Kiro, open NIZAM and a fresh Autopilot chat. Confirm policy reload without fatal
   errors; reload the window only if required, after preserving active work.
5. For activation, request the existing `npm ls --depth=0` and dispatcher lint command
   sequentially, then a read-back summary. Observe whether both execute without another
   user turn or approval prompt. Inspect actual prompt scope if blocked; never broaden
   all permissions. Do not test intentionally dangerous commands in a live shell.
