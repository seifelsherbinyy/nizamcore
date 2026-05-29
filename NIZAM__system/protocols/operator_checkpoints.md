# Operator-in-the-Loop Checkpoints (E1.4)

**Status:** ACTIVE.
**Owner:** Ammar (STEWARD) sets the flag; the coordinator enforces the pause.
**Cite:** Plan v2 §E1.4.

## What this is

A precise list of moments where the system **must** stop and ask the operator before acting. NIZAM is solo-operated; the operator is its only HITL. These checkpoints are the only places where automatic chains are interrupted by design.

## The 7 mandatory checkpoints

| # | Trigger | What the operator sees | Allowed replies |
|---|---------|------------------------|-----------------|
| C1 | `delegation_depth > 3` | "Chain at depth N — continue?" + chain summary | `/go <trace_id>`, `/halt <trace_id>` |
| C2 | Privacy escalation to `strict_local` or above | "About to access strict_local data X — confirm?" | `/go`, `/halt` |
| C3 | Cost soft ceiling crossed for this `trace_id` ($50) | "Trace cost now $X — continue spending?" | `/go`, `/halt` |
| C4 | Cost hard ceiling crossed ($300, lifetime) | "Hard ceiling tripped — system has stopped writers." | `/release` (manual unblock after lifting ceiling) |
| C5 | `egress_class = framework_egress` first occurrence in turn | "First framework egress this turn — allow?" | `/go`, `/halt` |
| C6 | Conflict arbitration resulted in `no_pick` | "Two candidates tied — pick one." + diff | `/override <trace_id> <choice>` |
| C7 | Any agent emits `kind = alert` | "ALERT from <agent>: <message>" | `/ack`, `/escalate` |

## How a pause is implemented

1. Coordinator marks the current envelope `needs_operator_confirm = true` and sets `operator_confirm_reason` to the reason code (e.g., `C1_depth`, `C3_cost_soft`).
2. Coordinator writes a `pause_for_operator_confirm` row to `EVENT_LEDGER`.
3. Coordinator sends a Telegram message to the whitelisted operator chat. The message contains:
   - Trace ID
   - Reason code + 1-sentence explanation
   - Chain summary (≤5 bullet lines, "From → To: purpose")
   - The two valid replies
4. Coordinator does **not** advance the chain until a reply arrives. If 24 hours elapse, coordinator emits a `DEAD_LETTER` row and the trace dies (operator can manually resurrect with `/resume <trace_id>` after the fact, subject to staleness checks).

## Off-by-default checkpoints (operator may enable)

These are paused **only** when the operator turns them on via `nizam_config.json#operator_checkpoints`:

- `C8_every_strict_local_write` — pauses before every persisted strict_local write (verbose mode).
- `C9_every_external_tool_call` — pauses before every external HTTP call.
- `C10_every_model_swap` — pauses when the fallback chain triggers a model swap mid-trace.

## Replies the operator may always send

| Reply | Effect |
|-------|--------|
| `/go <trace_id>` | Resume the chain at the paused envelope. |
| `/halt <trace_id>` | Terminate the trace. Khaldun summarizes into LEARNING_LEDGER. |
| `/override <trace_id> <choice>` | Pick a winner during conflict arbitration. |
| `/ack` | Acknowledge a non-blocking alert. |
| `/escalate` | Promote an alert to a `kind = challenge` envelope routed to Hazim. |
| `/release` | After C4 (hard cost ceiling), once the ceiling is lifted, unblocks writers. |
| `/resume <trace_id>` | Resurrect a `DEAD_LETTER` trace inside the 7-day window. |

All replies are validated by `auth.verify_user_id` first; no other Telegram user can issue them.

## Acceptance

Complete when:

1. This document exists. ✅
2. `nizam_config.json#operator_checkpoints` schema is defined (deferred to E2.x where user_profile/user_deep are scaffolded; operator preferences live alongside).
3. Telegram-side wiring of these replies happens in the same hop as G3/G4 (live mode), not before.
