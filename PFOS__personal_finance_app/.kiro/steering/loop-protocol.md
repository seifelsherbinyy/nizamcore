---
inclusion: always
---

# NIZAM development loop and context routing

Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase 1 (KDE).
Read AGENTS.md, money-rules.md and drive-db.md. Research -> Plan -> Implement -> Verify.
For PFOS work explicitly read .kiro/steering/pfos-current.md. Before server, agent, bot,
ingestion or deployment work explicitly read .kiro/steering/two-agent-vps.md; it wins in
that area. Before provider-specific work read cloudflare-dns.md. Manual inclusion reduces
idle context; it never removes these authorities from applicable tasks.

Current capability entrypoints: .kiro/skills/*/SKILL.md; human index:
docs/kiro/capability-registry.md. Load the matching skill and its references on demand.
Skills cover investigation, implementation, debugging, test repair, quality, docs,
repository work, VPS inspection, service diagnostics, deployment preparation, validation
and local browser testing. Skills guide tools, never grant authorization.

Choose the relevant contract and spec, not the original 1-to-5 build sequence. Substantial
new behavior needs requirements/design/tasks; missing policy needs a contract first.
Historical statuses/test counts are not fresh verification. PFOS Contracts 05/06 exist;
server runtime and later status are addressed by the server authority. Do not replay old
missing-contract next steps or infer current host state from dated documentation.

Preserve existing modifications, announce a bounded multi-file plan and use deterministic
mocks. Read scripts before running. Routine local code/tests and public docs research are
normal development actions. Validate focused behavior, then typecheck/lint/build and
npm run verify:all -- --all. Keep every failure visible; no weakened gates or cleanup.

No automatic commit/push/deploy. Human gate records are never executed, tested, populated
or marked complete by this workflow. Credential lifecycle, host mutation and production
spend require explicit owner authorization and applicable authority. Do not inherit broad
authorization from an old receipt. Detailed loop: docs/kiro/references/development-loop.md.

The installed IDE was 0.12.333 at inspection; fresh-session skill activation is unverified.
See docs/kiro/compatibility.md. Do not install new agent/hook schemas on version assumption.
