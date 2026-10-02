# Daily companion tasks

Authority: PFOS Contract 14 section 11. Phase 14.1 (DC1).

- [x] DC-A: contract/spec and live-vs-reference pillar registry.
- [x] DC-B: pure policy/config/time/control parsing (depends A).
- [x] DC-C: synthetic SQLite persistence with atomic reservation and settings CAS (depends B).
- [x] DC-D: injected authorized tick orchestration and controls (depends B/C).
- [x] DC-E: policy, privacy, auth, restart, race, uncertainty and canonical-clock tests (depends D).
- [ ] DC-F: focused typecheck/lint/test/build, full gate, redacted evidence (depends E).
- [ ] DC-LIVE: native sole-owner adapter, configured sources/retention/dispatch fence,
  protected credential and unique consumer, governed Hermes integration, authorized live
  conversation/send/restart/control observation. Blocked dependencies, not complete by DC1.

Tests use fixed clocks, synthetic metadata, real SQLite close/reopen and injected recorders.
No live sends or provider spend. No edits to acceptance assertions or unrelated user files.

DC-A through DC-E refer to the bounded DC1 reference only, not all attachment deliverables.
The broader regression run observed 96 new tests. DC-F ran: final gate 19/21, 3105 tests passed. Remains unchecked because AC14/AC15
require an intentionally clean owner-approved tree, not unauthorized cleanup or commit.
