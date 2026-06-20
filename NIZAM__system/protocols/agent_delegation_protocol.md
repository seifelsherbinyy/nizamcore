# Agent Delegation Protocol (E1.2)

**Status:** ACTIVE. Enforced by `NIZAM__system/relay/coordinator.py` and the agent_message envelope (`schemas/agent_message.schema.json`).
**Owner:** Ammar (STEWARD).
**Cite:** Plan v2 §E1 (agent communication network).

## What this protocol governs

Whether one agent may route a sub-request to another agent without operator confirmation, and at what depth that chain forces a checkpoint.

## Hard rules

1. **Depth counter.** Every `agent_message` envelope carries `delegation_depth`. Operator turn = 0. Each agent → agent hop = +1.
2. **Auto-permitted range.** `delegation_depth ∈ {0, 1, 2, 3}` proceeds without operator confirmation, **provided** every gate (SUKOON, HIMAYAH) passes.
3. **Confirm-required range.** `delegation_depth > 3` automatically sets `needs_operator_confirm = true` on the envelope. The coordinator **stops** the chain and sends a Telegram summary asking the operator whether to continue.
4. **Hard cap.** `delegation_depth > 8` is rejected by the schema. Any chain that wants more than 8 hops must be re-architected.
5. **Privacy escalation overrides depth.** If a hop would raise the envelope's `privacy_class` from `mirror_sanitized` / `private_github` to `strict_local` or higher, **always** ask the operator regardless of depth.
6. **Crisis short-circuits.** A SUKOON `crisis_protocol` decision forces the chain to terminate at depth 1 (operator → crisis protocol). No further auto-delegation.

## Allowed delegation edges

The defaults below mirror the persona contracts and `agents.registry.yaml`. They are starter values; tune by feedback.

| From | To | Reason |
|------|----|--------|
| Coordinator | Any agent | Routing |
| Salman (SHURA) | Hazim (NAQD) | Red-team a synthesis |
| Salman (SHURA) | Tariq | Long-horizon implication |
| Salman (SHURA) | Khalid (MUNAWARA) | Tactical implication |
| Hazim (NAQD) | Salman (SHURA) | Counter-synthesis |
| Khalid (MUNAWARA) | Tariq | Escalate scope |
| Tariq | Khaldun (HIKMAH) | Crystallize into doctrine |
| Tahir (MARSAD) | Tariq | Strategic context |
| Tahir (MARSAD) | Salman | Inform brainstorm |
| Hayat (BADAN) | Salman, Hazim, Coordinator | Biometric annotation |
| Sadiq (MAL) | Tariq, Khalid | Financial constraint propagation |
| Ammar (STEWARD) | Any | Governance / kill / cost |

**Disallowed by default:** Any agent → Ammar except as a `gate_decisions` event (Ammar is a gate, not a delegate).

## When `needs_operator_confirm` flips on

Coordinator sets it to `true` when **any** of the following holds:

- `delegation_depth > 3`
- `privacy_class` rises in this hop from `private_github`/`mirror_sanitized` to `strict_local` or higher
- Cumulative `cost_cents` for this `trace_id` would cross the soft ceiling ($50)
- A gate (`HIMAYAH`, `SUKOON`, `THABAT`) returned `escalate`
- A `tool_call` would invoke a `framework_egress`-tier tool that wasn't already authorized in this turn

## Operator confirm flow

1. Coordinator pauses the chain and writes the current envelope to `EVENT_LEDGER` with `decision: pause_for_operator_confirm`.
2. Coordinator sends a Telegram message: chain summary (≤5 lines), reason, and two replies the operator can send back: `/go <trace_id>` or `/halt <trace_id>`.
3. On `/go`, coordinator resumes from the paused envelope. On `/halt`, the trace is terminated and Khaldun summarizes the dead chain into LEARNING_LEDGER.
4. No state is mutated during the pause.

## Test fixtures (sketched, not yet executed)

- `depth_3_brainstorm_chain.jsonl` — Operator → Salman → Hazim → Salman → Operator. Must auto-resolve.
- `depth_5_overcommit.jsonl` — Operator → Salman → Tariq → Khalid → Salman → Hazim. Must pause and emit operator confirm at hop 4.
- `privacy_escalation.jsonl` — Operator → Coordinator → Salman (`mirror_sanitized`) → Hayat (`strict_local`). Must pause at the Hayat hop.

## Failure modes

- **Loop.** Coordinator tracks `(from_agent, to_agent)` edges per `trace_id` and refuses to re-traverse the same edge twice without operator confirm.
- **Starvation.** If a sub-agent never responds within `timeout_seconds`, the coordinator emits a DEAD_LETTER row and falls back to Amin's capture.
- **Schema violation.** Any envelope failing `agent_message.schema.json` validation is rejected at the coordinator and a DEAD_LETTER row is appended.

## Acceptance

Marked complete when:

1. `schemas/agent_message.schema.json` exists and is referenced by the coordinator. ✅ (E1.1)
2. This protocol document exists at `protocols/agent_delegation_protocol.md`. ✅ (this file)
3. `protocols/_PROTOCOLS_INDEX.md` lists it. (next change)

Coordinator-side enforcement of items above lives in code; the unit tests under `relay/tests/test_phase1_boot_loop.py` cover B4.5/B4.6 already. Depth-cap unit tests are added under E1.x phase.
