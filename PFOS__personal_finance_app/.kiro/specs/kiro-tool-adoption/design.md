# Kiro quality-tool adoption design

Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 3-6.

scripts/kiro/quality owns a separate package/lock, Node test properties, browser trial
and mutation trial. No src/tests or existing file changes. Reuse the existing browser
server and playwright-core installation. All new dependencies remain outside the app.

Properties use fixed seed and run count. Mutation trial creates an owned temporary
root beneath ~/.aki/tmp, supplies only authored synthetic code/tests and explicit Stryker
configuration, and spawns the installed CLI with a timeout. A positive run must kill
all generated mutants. The test source and mutated source are disjoint.

Browser trial requires explicit executable path and Node 24, uses an isolated browser
context and blocked network, injects local axe source and returns only rule IDs/counts.
Bad fixture must detect button-name and image-alt; corrected fixture must have no
violations. Built-app results are diagnostic and fail the command on violations, while
fixture success remains separate. Incomplete axe results remain manual-review work.

Package source snapshots and install logs stay in local cache. Persist public URLs,
versions, integrity and evaluated risks. No npm audit payload containing application
packages is sent. Developer-only lock may be audited; no automatic fix/update.
Rollback is a reviewed inverse of this increment's new files after checking later edits,
not deletion of another agent's work. Existing historic acceptance failures remain open.
