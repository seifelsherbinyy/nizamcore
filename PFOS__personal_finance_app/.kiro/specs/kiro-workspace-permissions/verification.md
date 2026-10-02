# Verification evidence

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 1 (KWP).
Date: 2026-09-16. Native Node 24.14.1, npm 11.11.0.

## Observed results

Commands executed through native PowerShell (not Aki's Bun-backed node alias):

| Command | Result |
| --- | --- |
| node scripts/kiro/permissions.mjs --write | 174 test files, 557 unique commands; create-only template generated |
| node --test --test-reporter=dot scripts/kiro/permissions.test.mjs | exit 0 |
| node --test --test-reporter=tap scripts/kiro/permissions.test.mjs | 587 passed, 0 failed, 0 skipped |
| node scripts/kiro/permissions.mjs | inventory reported, no write |
| node scripts/kiro/validate.mjs | structural validation PASS, IDE activation UNVERIFIED |
| npm run typecheck | exit 0 |
| npm run lint | exit 0, zero-warning configuration |
| npm run build | exit 0; Vite and PWA output generated |
| npm test -- src/lib/db/moneyBoundary.test.ts | 11 passed |
| npm test -- --run src/lib/db/moneyBoundary.test.ts | 11 passed |
| node node_modules/vitest/vitest.mjs run src/lib/db/moneyBoundary.test.ts | 11 passed |
| git diff --check | exit 0; existing CRLF conversion warnings only |
| npm run verify:all -- --all | exit 1; 19/21 checks passed; AC14 and AC15 fail on the dirty working tree (54 entries) |

The three test invocation checks confirm syntax against one existing synthetic suite;
this does not mean every command was individually executed. Policy tests compare
strings and parse YAML, not actual Kiro shell parsing or hostile command containment.

## Installation and preservation

Narrow folder grant obtained. Existing migration marker and installed hash/loader
confirmed the NIZAM per-user workspace directory. No existing workspace YAML/JSON
policy was overwritten. Installed copy is byte-identical to the 42,249-byte template.
SHA-256: 44addef47d87362fabb9494888f0b53649cd6ca71181c93786cebbf53231bc67.

All 866 pre-existing nonignored repository files checked against captured hashes:
none changed. Global Kiro permissions and IDE user settings retain their baseline
hashes. Backups/hashes and local receipt are outside the repository under Aki tmp.
No application source, package manifest, lockfile or acceptance check was modified.

## Failures and limitations

- Initial generator rejected the colon in existing npm script names. Validation was
  corrected and generation plus all focused tests then passed. No live policy was
  installed before the focused tests passed.
- Two attempted test-file writes were denied by tool safety matching negative-fixture
  command strings. They did not run. Fixtures now use harmless synthetic inputs.
- Independent subagent review was blocked by the environment's agent-spawn deny rule.
  No subagent review is claimed. Manual review covered schema, exact-list reuse,
  precedence, scope, input validation, duplication and truthful security limitations.
- Optional expensive regex scanning of the minified extension was cancelled. Installed
  schema, workspace identity and loader evidence had already been read successfully.
- Fresh-session Kiro activation and absence of prompts remain UNVERIFIED. Autopilot was
  already configured. Native and enterprise ask/deny rules are intentionally preserved.
- No human gates, credentials, hosts, production providers, commits or pushes were run.

Full harness failures: AC14 (working tree not clean) and AC15 (release readiness
requires a clean tree). The initial tree was already dirty; this increment also adds
uncommitted files. No cleanup, commit or acceptance-check modification was attempted.
The full application suite reports 3141 passed and 0 failed tests.
