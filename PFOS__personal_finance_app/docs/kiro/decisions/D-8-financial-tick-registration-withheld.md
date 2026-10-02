# D-8 — financial pillar tick registration deliberately withheld

**Status: NOT TAKEN.** **Task:** NIZAM-FINAL-009 item F. **Phase:** registration record only; no runtime
binding. The wiring change would add an internal finance-tick composition seam beside
`src/server/process/financeAgent.ts`, with that process supplying the real receipt, suppression, clock,
delivery-journal and outbound ports to the already-built `financialPillarTick`; `scheduler.ts` would
remain unchanged, `SCHEDULER_TARGETS` would remain the two-member `['life', 'finance']` tuple, and no new
timer, cron, endpoint target or transport path would be created. It becomes safe only after (1) the owner
answers D-7 so a Slack financial response has applicable authority, (2) Phase 1b is approved and the real
`stateUseReceipt` adapter exists with canonical-version and freshness read-back, and (3) the separately
governed outbound transport is authorized and bound. Verification would prove one finance tick invokes
one consumer, a missing receipt emits no outbound call, quiet/snoozed state emits no outbound call,
ambiguous delivery is not replayed across restart, `scheduler.ts` is byte-identical, and a source-level
assertion still rejects any third `SCHEDULER_TARGETS` member. Registering the handler today would create a
bot path that can only refuse and would be worse than silence, so the registration remains withheld.
