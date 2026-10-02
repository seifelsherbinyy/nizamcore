# NIZAM development loop

Owner: KDE contract. Phase 1. Read only when a skill needs the procedure.

UNDERSTAND -> RETRIEVE_CONTEXT -> RESEARCH_IF_NEEDED -> PLAN -> IMPLEMENT ->
RUN_CHECKS -> INSPECT_FAILURES -> FIX -> RERUN -> VALIDATE_OBJECTIVE -> DOCUMENT.

- Start with git status --short and a targeted diff. Existing work is protected.
- Read AGENTS.md and money-rules.md/drive-db.md. Read pfos-current.md for PFOS;
  read two-agent-vps.md for server/agent/bot/ingestion/deployment before implementing.
- Historical status is not current readiness. PFOS Contracts 05 and 06 now exist;
  inspect contracts/pfos rather than following the old missing-contract statements.
  The six pre-foundation specs remain in place; do not tick their boxes here.
- Small well-understood fixes can proceed under existing authority. Substantial new
  behavior requires requirements/design/tasks; missing policy requires a contract first.
- Announce a short concrete plan before multi-file edits. Scope each worker to nonoverlapping
  files; independent reviewers are read-only. Two unsuccessful repair hypotheses require
  a new discriminating experiment, not unbounded edits.
- Read scripts before running them. Prefer argv APIs, exact targets and deterministic
  mocks. Do not run ops templates or human-gate instructions as an environment test.
- Use npm run typecheck; npm run lint; npm test -- --run <relevant-pattern>;
  npm run build; npm run verify:all -- --all. These are commands, not success claims.
- Actual Node must be version 24. Some agent shells alias node to a different runtime;
  verify process.versions before using Node-specific test/SQLite behavior.
- Never suppress acceptance, lower a floor, clean user files or commit to make the gate pass.
- Report objective result, exact commands, observed failures, owned paths and remaining work.
  Commit/push/deploy are separate explicitly authorized actions, not automatic loop steps.

The old scripts/loop/autobuild.mjs has a spec allowlist that did not match current specs
at inspection and an agent-specific executor. Do not invoke it for this expansion.
Use this spec's bounded tasks and ordinary tools instead. No new autonomous scheduler.
