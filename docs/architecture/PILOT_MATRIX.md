# NIZAM Smart Companion Pilot Matrix

This matrix maps roadmap stages to local evidence. External activation remains blocked until operator approvals are recorded.

## Local Implementation Gates

| Stage | Gate | Evidence | Status |
|---:|---|---|---|
| 0 | Read-only baseline | `docs/architecture/GAP_CLOSURE_DEBRIEF.md` | GREEN |
| 1 | Canonical path | `NIZAMCORE_PATH.txt`, `tools/test_canonical_path.py` | GREEN |
| 2 | Reproducible test gate | `pytest.ini`, locked requirements, `.github/workflows/nizam-ci.yml` | GREEN |
| 3 | Privacy ADR | `docs/architecture/ADR-0001-LOCAL-FIRST-EGRESS.md`, `test_policy_invariants.py` | GREEN |
| 4 | Connector registry | `CONNECTORS.json`, `tools/nizam_connector_health.py` | GREEN |
| 5 | Governed worker | `companion/gateway.py`, `relay/coordinator.py`, `relay/persona_runtime.py` | GREEN |
| 6 | Context packets | `companion/context.py`, `companion/contracts.py` | GREEN |
| 7 | Calendar/Tasks preview | `companion/calendar_tasks.py` | GREEN |
| 8 | WHOOP export import | `companion/whoop_import.py` | GREEN |
| 9 | Knowledge center | `companion/knowledge.py`, `companion/knowledge_eval.py` | GREEN |
| 10 | Proactive + Islamic reminders | `companion/proactive.py`, `companion/reminders.py` | GREEN |
| 11 | Observability | `relay/runtime_events.py`, `relay/tests/test_runtime_events.py` | GREEN |
| 12 | Pilot evaluator | `tools/nizam_pilot_readiness.py` | GREEN local / NO-GO external |

## Activation Gates (Operator Approval Required)

| Gate | Environment variable | Default |
|---|---|---|
| Live model | `NIZAM_LIVE_MODEL_APPROVED=1` | blocked |
| Live connectors | `NIZAM_LIVE_CONNECTORS_APPROVED=1` | blocked |
| Deployment | `NIZAM_DEPLOYMENT_APPROVED=1` | blocked |
| Remote telemetry | `NIZAM_REMOTE_TELEMETRY_APPROVED=1` | blocked |

## Verification Commands

```powershell
D:\NIZAM\scripts\verify-nizamcore.ps1 -SkipNetwork
D:\NIZAM\.venv\Scripts\python.exe -m pytest D:\NIZAM -q
D:\NIZAM\.venv\Scripts\python.exe D:\NIZAM\tools\nizam_pilot_readiness.py
```

Expected pilot output:

- `local_decision`: `GO`
- `decision`: `NO_GO` until activation variables are explicitly set

## Operational Thresholds For External Pilot

- p95 latency: at most 15 seconds
- error rate: below 2%
- privacy incidents: zero
- duplicate sends: zero
- GraphRAG top-five hit rate: 100%
- companion knowledge MRR: at least 0.60
