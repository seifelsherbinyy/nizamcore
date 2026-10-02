# Kiro workspace foundation design

Authority: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE).

## Architecture

Use .kiro/skills/*/SKILL.md for discovery, docs/kiro/references for shared procedures,
and docs/kiro/capability-registry.json for bounded machine-readable metadata. The registry
is not a native Kiro configuration or runtime authority. A compact always-included loop
points to capabilities and relevant domain steering; large authority bodies stay in place
with manual inclusion. Explicit retrieval is required before domain work.

scripts/kiro/validate.mjs validates our deliberately small JSON and single-line YAML
frontmatter subset. It does not claim to implement the full Agent Skills or Kiro schemas.
It reads only declared skill/reference files, never global credentials or gate records.
Paths reject traversal and symlinks before reads. Diagnostics do not echo input payloads.
scripts/kiro/inspect.mjs reports package/version and directory metadata without executing
external commands. Tests use Node's built-in test runner and temporary synthetic trees.

A separate scripts/kiro/package.json/lock pins playwright-core. The browser runner serves
only dist with MIME types, binds to IPv4 loopback on an ephemeral port, rejects traversal
and symlinks, blocks external browser requests, uses an isolated context and tests actual
navigation plus reload. Browser path is supplied by the operator; no browser installer or
personal profile is used. All owned resources close in finally blocks. No remote target
argument exists. This is a local smoke test, not a deployment probe or all-browser suite.

## Compatibility and limitations

Inspected installation package: Kiro 0.12.333. Native discovery must still be observed in
the running IDE. Current docs describe 1.0 agents/permissions/hooks; do not install those
formats on assumption. Global steering/MCP may still load. Manual file retrieval is the
fallback. No IDE update, global cleanup, live MCP activation or host connection is included.

## Verification

Independent assertions cover every required skill, registry status, malformed inputs and
browser server rules. npm run verify:all -- --all remains unchanged. Existing dirty-tree
failures remain failures. Aki execution does not count as a Kiro activation transcript.
