# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Validation, Risks & Roadmap

## Validation targets

1. storage authority manifest resolves VPS/Drive/GitHub roles;
2. no secret/token value appears in Drive-bound fixtures;
3. WHOOP refresh rotation is serialized and atomic;
4. pagination checkpoint cannot advance after partial failure;
5. timestamps survive UTC/provider-offset/Cairo conversion tests;
6. rolling features handle sparse data and MAD=0;
7. raw journal text is not unintentionally embedded into retrieval indexes;
8. Drive write is read back before sync success;
9. stale Drive index cannot override fresher VPS operational truth;
10. duplicate canonical pointers are detected;
11. calendar idempotency fails closed on duplicates;
12. calendar coverage gate blocks false “free time” inference;
13. LLM outage leaves deterministic state intact;
14. scheduled job fires at proven 11:00 Cairo time;
15. tamper test proves the package verifier fails when cloud-authority marker is removed.

## Primary risks

| Risk | Severity | Mitigation |
|---|---|---|
| secrets copied to Drive | Critical | `vps_secret`, scanning, deny-by-default sync |
| Drive used as transactional database | High | VPS operational DB is runtime truth |
| VPS becomes an unindexed file dump | High | retrieval catalog + Drive knowledge indexes |
| duplicate records across VPS/Drive | High | canonical IDs, provenance, authority manifest |
| stale Drive summary overrides current metrics | High | freshness/source-authority resolution |
| wearable data treated clinically | High | advisory language, provider/derived separation |
| stress inferred from HRV alone | High | multimodal evidence and causal guardrails |
| correlation phrased as causation | High | hypothesis/counterevidence lifecycle |
| 11:00 executes in wrong timezone | High | live timezone test before activation |
| calendar blank spaces treated as availability | High | coverage status gate |
| context grows too large/slow | Medium | index-first retrieval and bounded context packets |

## Roadmap

| Phase | Work | Output |
|---|---|---|
| P0 | inspect live VPS + reconcile storage doctrine | verified authority manifest |
| P1 | land cloud storage/retrieval contracts | canonical schemas/contracts |
| P2 | WHOOP read-only ingestion | fresh VPS provider store |
| P3 | deterministic feature engine | rolling features + tests |
| P4 | Drive knowledge organization/indexes | fast Hermes retrieval |
| P5 | journal/workout/calendar joins | contextual feature packet |
| P6 | hypothesis/intervention ledger | longitudinal learning |
| P7 | bounded daily planner | 1–3 realistic targets |
| P8 | prove scheduler and activate 11:00 job | daily automated run |
| P9 | approved calendar write path | idempotent reminders/events |
| P10 | advanced N-of-1/change-point models | deeper personalization |

## Verification requirement

Run the focused verifier, then the repository's existing gate on the actual VPS checkout. A test observed only passing is not proven: remove or alter a required authority marker once, confirm failure, restore it and rerun cleanly.

**MISSING:** live OVH VPS path, service names, repository gate commands and scheduler timezone are intentionally not invented in this package.
