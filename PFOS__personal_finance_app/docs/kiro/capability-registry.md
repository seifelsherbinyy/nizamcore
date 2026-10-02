# Workspace capability registry

Owner: KDE contract. Phase 1. All skill activation remains UNVERIFIED in Kiro.
The JSON registry is metadata, not native Kiro configuration or permission.

| Skill | Trial request |
|---|---|
| `nizam-investigate` | Explain how the transaction register reaches the local cache. |
| `nizam-implement` | Implement a small governed feature with tests. |
| `nizam-debug` | The budget page fails after reload; reproduce and identify the cause. |
| `nizam-test-repair` | Diagnose a failing Vitest test and repair its root cause. |
| `nizam-code-quality` | Review the current diff for security and missing tests. |
| `nizam-docs-research` | Check the supported Dexie API for our installed version. |
| `nizam-repository` | Investigate an upstream GitHub issue and prepare a local patch plan. |
| `nizam-vps-inspect` | Inspect the authorized VPS service state without changing it. |
| `nizam-service-diagnostics` | Diagnose this container exit and systemd startup log. |
| `nizam-deploy` | Prepare this local release and its rollback procedure. |
| `nizam-validate` | Validate this completed change for repository handoff. |
| `nizam-browser-test` | Smoke-test local navigation and reload in an isolated browser. |

## Validation and maintenance

Use node scripts/kiro/validate.mjs for structural checks. Use node --test
scripts/kiro/validate.test.mjs scripts/kiro/browser.test.mjs for negative tests.
Run commands from the repository root with Node 24. See references/browser.md for the
pinned local smoke runner and compatibility.md for observed versus unverified behavior.

Before updating: check original source and exact revision, license, install scripts,
transitive dependencies, recent issues and necessity compared with native tools. Review
lockfile changes, rerun unit/local browser/full checks, then retest Kiro activation.
Never update packages or global settings automatically. Public docs/research is normal;
no credential is minted or widened merely to make a tool connect.

No source under src/ or tests/ is changed by this foundation. Application money, DB,
routing and Drive implementations are not duplicated. Existing acceptance is unmodified.
