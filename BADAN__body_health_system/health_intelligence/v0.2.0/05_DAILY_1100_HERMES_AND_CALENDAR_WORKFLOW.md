# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Daily 11:00 Hermes & Calendar Workflow

## Status

**Proposed runtime workflow. Not activated by this package.** Target schedule: daily at 11:00 `Africa/Cairo` after the live VPS timezone/scheduler semantics are verified.

## Scheduler preflight

1. inspect actual VPS timezone and Hermes scheduler behavior;
2. prove a synthetic scheduled job fires at the expected Cairo instant;
3. record the discovered workdir/service identity in the system manifest;
4. only then activate the real health job.

Do not silently assume UTC, Cairo time, or server-local semantics.

## Daily run

```text
A. acquire single-run lock + run_id
B. verify server clock and Africa/Cairo conversion
C. load retrieval/source manifests
D. refresh WHOOP incrementally
E. refresh workout references
F. refresh journal/assessment references
G. incrementally sync calendar read model
H. validate timestamps, duplicates, score states and coverage
I. calculate 3/7/14/30/90-day deterministic features
J. evaluate prior interventions/adherence from explicit human records
K. update hypothesis/counterevidence ledger
L. build bounded context packet
M. Hermes generates 1–3 realistic targets + proposed agenda
N. deterministic validator checks overlaps/constraints/idempotency
O. commit operational truth to VPS
P. classify durable knowledge outputs
Q. write permitted artifacts to 47_NIZAM and read them back
R. update retrieval indexes/manifests
S. emit run + sync receipts
T. calendar writes remain gated by human approval
```

## Retrieval before generation

Hermes must not plan from memory alone. It loads, in order:
- `47_NIZAM` master knowledge map;
- health domain index;
- source/retrieval manifest;
- fresh VPS operational features;
- relevant longitudinal Drive records;
- current calendar constraints.

## Idempotent calendar proposal

A deterministic key may use an HMAC derived from planning date, intervention identifier, start time and schema version. The key material/secret stays on VPS. Query existing events by the non-secret derived key before insert/update. Multiple matches fail closed.

## Drive persistence

Drive is a durable knowledge plane, not a mere redacted receipt sink. When classification permits, save structured daily plans, health summaries, workout/journal references, longitudinal reviews and research under `47_NIZAM/06_HEALTH_FITNESS` with compact indexes for retrieval.

## Failure behavior

| Failure | Behavior |
|---|---|
| WHOOP unavailable | preserve last good state; mark source stale |
| Drive unavailable | keep VPS truth; queue sync retry; mark `SYNC_PENDING` |
| Calendar incomplete | never infer free time from blank space |
| LLM unavailable | persist deterministic snapshot; skip narrative/agenda generation |
| Duplicate calendar key | fail closed |
| Token refresh race | serialized refresh lock; do not continue with uncertain credentials |
| Retrieval index stale | rebuild index from canonical pointers before synthesis |

## Human-only gates

Habit completion, `Decision Made?`, `Calendar Approved` and final calendar approval are not inferred or auto-completed by Hermes.
