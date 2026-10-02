# Operations workflow reference

Owner: KDE contract Phase 1; operational policy remains PFOS Contract 12.

Read .kiro/steering/two-agent-vps.md, the applicable contract and current task authority.
Existing templates: ops/docker-compose.yml, ops/Caddyfile, ops/images and ops/runbook.
They describe intended architecture, not proof that a live service uses that topology.
Native runtime, supervisor ownership and the actual checkout must be established first.

## Read-only diagnosis

Use established SSH access only when the current task authorizes that target. Keep host-key
verification enabled. A missing key/tool is a blocker, not permission to create one.
Inspect narrow metadata: OS/runtime versions, systemctl show selected nonsecret properties,
container names/status, bounded redacted journal output, disk availability and repository
revision/dirty status. Do not dump env, /proc environment, resolved Compose config, secret
files, full process arguments, database rows or raw logs into model context.
Avoid health URLs that trigger provider calls or production spend; inspect their code first.

## Repair/release plan

Identify the exact process/service, pre-change snapshot, artifact identity, dependencies,
health assertions, rollback trigger and prior artifact. Prefer local synthetic reproduction.
Check SQLite migration/integrity with synthetic stores and no cross-database ATTACH.
Keep runtime and application-level checks separate. Backup existence is not a tested restore.
Do not restore a production database as a rehearsal.

Host mutation, restart, deployment, uploads, credential lifecycle and production spend need
explicit owner authorization and applicable authority. Nothing here runs or tests a human
gate. Do not copy commands from ops/DEPLOYMENT_CONTROL.md or ops/GATE_REGISTER.md into trials.
No SSH broker, Docker socket MCP, credentials or extra daemon is installed by this foundation.
