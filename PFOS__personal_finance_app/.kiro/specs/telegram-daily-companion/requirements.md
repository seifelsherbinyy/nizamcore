# Telegram daily companion requirements

Authority: PFOS Contract 14 section 11; Contracts 06/12; server, money and Drive steering.
Phase 14.1 (DC1): offline implementation. TW01-TW15 remain required for live integration.
The legacy spec 06-two-agent-vps referenced by scheduler source is absent in this checkout;
this specification does not reconstruct or claim completion of that missing history.

| ID | Required behavior and acceptance |
|---|---|
| DC01 | Closed versioned policy; explicit opt-in, valid IANA timezone and bounded windows. Unknown/missing/malformed configuration fails closed. |
| DC02 | Local morning/midday/evening/weekly windows; at most one cycle per tick; weekly wins collisions; DST repeats reuse identity; missed windows never catch up. |
| DC03 | Quiet (including overnight), pause/resume, skip-today, global and pillar snooze, per-pillar cadence and less/more persist; no control expands tool grants. |
| DC04 | Approved fresh pillar state only; acknowledged/completed/dismissed, unchanged and snoozed inputs excluded. Stable priority with urgent obligations before financial alerts; max three questions, one for low/unknown capacity; NAQD only high capacity. |
| DC05 | PFOS-only alert provenance, no monetary values/free text in policy plans. Missing integration yields unavailable, never fabricated state or saved acknowledgements. |
| DC06 | Durable atomic reservation with preference revision fence, per-cycle identity and monotonic pillar-revision suppression. Reopen actual SQLite and prove no duplicate dispatch. |
| DC07 | Persist plan/result separately from delivery state; uncertain-before-send and no automatic replay. Crash/throw/lost acknowledgement cannot cause repeat domain work; settings changed during preparation cancel. |
| DC08 | Owner user AND private chat required before source/model/dispatch calls. Missing/wrong/group/bot identities, revoked consent and engaged/throwing kill gates cause zero calls. Source data cannot authorize itself. |
| DC09 | Commands/English/Arabic exact control phrases map deterministically; unrecognized/ambiguous input delegates to existing governed routing without returning input text. No shell or native write granted. |
| DC10 | Integrate synthetically through existing SchedulerHost life tick, no second timer. Test halt, replay, source failure, preference race, restart and uncertainty. |
| DC11 | All ten pillars have source, privacy, authority, freshness, triggers/cadence and unavailable behavior mapped; native adapter capability remains distinct from policy support. |
| DC12 | Synthetic data only, contract/phase headers, bundle exclusion, focused checks then unchanged full harness. Live readiness requires observed authorized conversation, scheduled send, restart and controls, not these tests. |
