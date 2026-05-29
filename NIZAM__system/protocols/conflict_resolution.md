# Agent Conflict Resolution Protocol (E1.3)

**Status:** ACTIVE.
**Owner:** Hazim (NAQD) is the arbiter; Ammar (STEWARD) enforces invocation.
**Cite:** Plan v2 §E1.3.

## When conflict resolution fires

Whenever two or more `agent_message` envelopes claim **incompatible** outputs for the same `trace_id`, AND the confidence spread between the top two alternatives is **≤ 0.15**.

"Incompatible" means: same `trace_id`, same target task slot (e.g., "the answer to /shura-brainstorm"), but mutually exclusive payloads.

## Resolution sequence

1. **Detect.** Coordinator notices two envelopes with same `trace_id` whose `kind = response` (or `kind = challenge` from Hazim) disagree.
2. **Compute spread.** `spread = |conf_top - conf_runner_up|`.
3. **If `spread > 0.15`.** Coordinator accepts the top envelope. No arbitration.
4. **If `spread ≤ 0.15`.** Coordinator emits a `delegation` envelope to Hazim with `kind = challenge`, payload containing both candidates plus their `context_refs`.
5. **Hazim red-teams.** Hazim's contract: name the strongest counter to each candidate, flag any unfounded claim (no `context_refs`), and either:
   - **Pick a winner** with new confidence, OR
   - **Refuse to pick** if both are equally weak, in which case Hazim emits a `kind = synthesis` envelope that downgrades both candidates and routes the trace to `needs_operator_confirm`.
6. **Operator-only override.** Operator may always override Hazim by sending `/override <trace_id> <choice>`. Override is logged with `actor: Operator, action: override_arbiter` in EVENT_LEDGER.

## Tie-break rules Hazim applies (in order)

1. **Citation rule.** A candidate that cites concrete `context_refs` beats a candidate that doesn't.
2. **Recency rule.** When both cite refs, the one citing the **most recent** ledger row wins (closer to current operator state).
3. **Privacy rule.** When still tied, the candidate with the **less invasive** `privacy_class` wins.
4. **No-pick.** If all three rules tie, Hazim refuses to pick. Operator decides.

## Examples

- **Salman vs Tariq disagree on Q3 priorities.** Salman: "ship feature X." Tariq: "delay X, doctrine demands focus on Y." Spread = 0.10. Hazim invoked. Tariq cites doctrine; Salman cites volatile capture. Hazim picks Tariq under citation rule.
- **Two MARSAD briefs from different runs.** Same `trace_id` re-run after a model swap. Confidence spread 0.05. Hazim picks the one with the newer `context_refs`.

## Bookkeeping

Every arbitration writes a row to `LEARNING_LEDGER` with:

```jsonc
{
  "trace_id": "...",
  "decision": "arbitrated|operator_override|no_pick",
  "winner": "Salman|Tariq|none",
  "rationale": "citation_rule|recency_rule|privacy_rule|operator|tie",
  "actor": "Hazim|Operator"
}
```

Khaldun reads these weekly to detect "arbitration debt" — a single agent that keeps losing arbitrations is a candidate for prompt revision (GEPA loop, E2.7).

## Acceptance

Complete when:

1. This document exists. ✅
2. `LEARNING_LEDGER` schema accepts the row above (no change required; ledger is open-payload).
3. Coordinator-side detection lives in code (deferred to a follow-up PR that wires the second envelope per trace_id; not blocking Phase-1 boot loop which is single-hop today).
