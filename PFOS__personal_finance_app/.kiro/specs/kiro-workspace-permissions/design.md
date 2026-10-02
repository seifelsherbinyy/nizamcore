# Design

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 1 (KWP).

A pure command inventory consumes repository-relative test paths and emits three
supported invocation forms per test: npm test with a path, npm test with --run,
and the pinned local Vitest Node entrypoint. Add exact development and inspection
commands, never unrestricted node/npm/git/PowerShell prefixes. Discovery rejects
symlinks and unsafe command characters. No subprocess or installation in the generator.

Generate a reviewable YAML template in docs/kiro with one anchored shell list reused
by allow.match and ask.exclude. This is not a native repo configuration. Install a
byte-identical copy into Kiro's confirmed per-user workspace permission directory,
create-only, after access approval. Use explicit per-capability rules. No catch-all
allow. File rules use normal development subtrees; remaining writes ask. MCP asks.

Unlisted shell commands ask across inherited global/session allows. Built-in and
enterprise restrictions still win. File rules do not confine child processes; trusted
scripts, executable resolution, cwd and environment require agent review. Structural
tests model exact shell matching only, not Kiro's parser, sandbox or runtime activation.

Existing js-yaml from the repository's locked development dependency tree parses the
emitted template in tests only; production generator has no dependencies. No app imports.
Generator writes no file unless --write is explicit; exclusive create prevents overwrite.

## Phase 2 superseding runtime design

Phase 1's 557-item ask.exclude becomes 557 AND predicates in a single Cedar condition
in the installed compiler Hpd. Its match list is already expanded into individual
policies by that compiler. Reduce exclusion expression depth rather than simply
reformatting YAML or splitting excludes. Keep the inventory as test data. Bounded
shell patterns cover src test invocations; exact commands cover build and verification.
Batch allow matches by eight; one compact exclusion list controls inherited allows.
Budget checks fail before writing. No YAML aliases are needed in the runtime template.

Allow .kiro/specs and scripts edits in addition to src/tests/docs. Keep other authority
and sensitive edits approval-required. Allow skill, context and subagent capabilities;
subagents inherit the parent policy. Web fetch patterns use hostnames, as installed
Kiro Kpd extracts hostname before matching (not full URL paths as Phase 1 assumed).

Actual Cedar tests reproduce Kiro's inspected Gpd/Hpd/Vpd compilation subset, call
isAuthorizedPartial for each capability, and exercise synthetic requests. They are
engine-level evidence, not the entire IDE shell parser or proof of live host access.
Runtime test takes an explicit installed module path; no package download or patch.

## Phase 3 autonomy expansion

Keep legacy command fixtures and tests intact. Add one shell family:
`node scripts/kiro/develop.mjs *`. Its dispatcher accepts exactly an action and a
simple existing src/*.ts or src/*.tsx file. Actions are lint, format-check and format.
It checks real workspace cwd and every path component for symlinks, including the
local executable's path. It passes argv directly to the current Node executable,
never a shell or package downloader. Pure planning and an injected spawn port allow
rejection tests to assert zero subprocess calls. Formatting is only for task-owned
files; permission does not authorize formatting unrelated pre-existing changes.

Coverage uses actual file paths: one lint, one format-check and one format action
per source file, plus one run per test file. Alternate npm/Node test forms count once.
The old invocation inventory remains separately labeled. New exact metadata commands
cover package-tree inspection and local runtime/network-tool versions. No Docker,
remote service, migration or installer is activated just to increase the count.

Use native tools for file manipulation and public fetches. A shell prefix cannot
confine subprocess filesystem/network effects. In particular inherited Phase 2 read
prefixes retain their limitations; steering is behavioral, not secret isolation.
Keep native/enterprise overrides. Do not add stop hooks, recursive self-prompts,
trust-all presets, MCP auto-approval or persistent background agents.
