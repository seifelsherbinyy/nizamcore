# Seven-contract recovery design

Owner: contracts/programs/SEVEN_CONTRACT_RECOVERY.md. Phase: Recovery 1.

Research -> Plan -> Implement -> Verify. Independent read-only reviewers cover lineage/UX,
finance/security, and runtime/continuity. Only the lead edits repository files.

## Evidence model

Use a source registry and handover with FACT, INFERENCE and MISSING labels. Local code proves
implementation, not deployment. Historical reports do not prove current health. Existing
in-flight baseline assessment code remains untouched; do not duplicate its receipt machinery.

## Smallest vertical repair

`src/lib/db/schema.ts` exports the shared `zMoney` Zod number schema. Its current `.int().finite()`
accepts integers outside the exact number domain, unlike `isMoney` in the deterministic core.
Add Zod's safe-integer range restriction while retaining the number schema type and existing
`.nonnegative()` compositions. This is validation, not a second money engine.

Create `src/lib/db/moneyBoundary.test.ts` with synthetic fixtures. Exercise the primitive and
representative composed account/policy fields, migration and FakeDrive load. Capture a red
regression run first, then apply the validator repair. No live Drive write or financial-data
migration is needed. Invalid pre-existing data is refused, never silently repaired.

## Verification and continuity

Use Node 24 from the installed native toolchain. Run focused tests, typecheck, lint, build,
then the unmodified full gate. Ratchet the suite floor upward after observing the new total.
Record clean-tree/push-readiness blockers without modifying unrelated files or ignoring them.
The handover is the non-secret evidence entrypoint for the next loop.
