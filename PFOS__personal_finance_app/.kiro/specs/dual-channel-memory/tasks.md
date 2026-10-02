# Dual-channel memory tasks

Authority: Contract 14 section 12. Phase 14.2.

- [x] CM-A: Author dual-channel contract/spec before policy.
- [x] CM-B: Admission, exact reply routing, pseudonymous provenance and receipt assessment.
- [x] CM-C: Synthetic negative tests and real existing journal writer sourceRef/replay exercise.
- [ ] CM-D: Focused typecheck/lint/tests/build and full gate; preserve existing dirty-tree failures.
- [ ] CM-LIVE: Native schema/writer/retention, encrypted Drive adapter, credentials/enrollment,
  unique Telegram consumer, safe dual-channel live configuration and observed round trips.

CM-A through D are preparation, not fulfillment of CM-LIVE or actual VPS/Drive memory sync.

CM-D checks executed: 19/21, 3141 tests passed. Remains unchecked for clean-tree/push
readiness; no unauthorized cleanup or commit. CM-LIVE remains unimplemented.
