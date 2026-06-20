# ROADMAP: NIZAM v1.1 — Persona Knowledge Index & Adaptive Messaging

**Project:** NIZAM Multi-Persona System v1.1  
**Scope:** Each persona delivers fresh, contextual, actionable nudges twice daily — refreshing user knowledge, motivating action, celebrating completion — with adaptive messaging when engagement drops  
**Granularity:** FINE (7 phases, derived from message lifecycle and integration boundaries)  
**Last Updated:** 2026-06-21  
**Progress:** Phase 16 planning complete (2 of 2 plans created)  
**Status:** In Progress (Phase 16 execution next)

---

## Phases

- [x] **Phase 14: Knowledge Index Schema & Storage** - Define optimized JSON schema per persona, initialize local storage (strict_local), versioning support (14-02: HIKMAH registration ✓, 14-05: comprehensive test suite ✓)
- [x] **Phase 15: Data Refresh & Synchronization** - Refresh index from Google Drive logs, handle graceful degradation, audit all data sources (15-01: refresh pipeline ✓, 15-02: configuration & integration ✓)
- [ ] **Phase 16: Message Generation & Variation** - Fresh message per intent, avoid repetition, actionable nudges, persona-consistent tone (16-01: core infrastructure ◐, 16-02: test suite + integration ◐)
- [ ] **Phase 17: Delivery & Response Tracking** - Twice-daily Telegram delivery (09:00 & 18:00 Cairo), message ID assignment, 1-hour response window capture
- [ ] **Phase 18: Adaptation & Format Evolution** - Track weekly response rates, adapt format if <80%, cycle through variations, log rationale
- [ ] **Phase 19: Cross-Pillar Integration** - Wire messages to MUNAWARA (actions), MAL (finance), TARIQ (strategy), ledger append
- [ ] **Phase 20: Privacy & Safety Validation** - No raw personal data in index/messages, sensitive topics flagged, confidence gates, full test validation

---

## Phase Details

### Phase 14: Knowledge Index Schema & Storage
**Goal:** Define and initialize an optimized JSON knowledge index schema that tracks user knowledge state, activity history, and context per persona, stored locally with versioning support.

**Depends on:** Nothing (first phase of v1.1)

**Requirements:** INDEX-01, INDEX-02, INDEX-03, INDEX-04

**Success Criteria** (what must be TRUE when phase completes):
1. Knowledge index JSON schema is documented with fields: topics (array of objects with name, status, timestamps, context), completions (closed topics), activity_history (user actions), stalled_work (tracking blockers), context_snapshots (current state)
2. Index is initialized per persona and stored locally in strict_local directory (not egressed to Telegram/Drive)
3. Index schema supports versioning and evolution (e.g., new topic types added in future personas without breaking existing indices)
4. Empty test run with a persona creates a valid, readable index file with correct structure

**Plans:** 
5/5 plans complete
  - Module registered in NIZAM Temple
  - Privacy enforcement configured (PRIVACY_CLASSIFICATION + .gitignore)
  - Documentation complete (README.md + _index.json)
  - INDEX-02 requirement satisfied
- [x] 14-05: Comprehensive Test Suite (COMPLETE)
  - Created shared pytest fixtures (conftest.py)
  - 14 schema validation tests (>80% coverage)
  - 15 initialization tests covering all 11 personas
  - 14 versioning and snapshot tests
  - All 43 tests passing with >80% coverage on core modules
  - All INDEX-01, INDEX-02, INDEX-03, INDEX-04 requirements verified

---

### Phase 15: Data Refresh & Synchronization
**Goal:** Refresh knowledge index from Google Drive conversation logs and activity data on each message generation, with graceful fallback to cached index if refresh fails.

**Depends on:** Phase 14 (index schema and storage initialized)

**Requirements:** REFRESH-01, REFRESH-02, REFRESH-03

**Success Criteria** (what must be TRUE when phase completes):
1. Refresh reads conversation logs and activity snapshots from Google Drive (correct folder, correct file types)
2. New activity from Drive is merged into the local index without overwriting stalled/completed tracking
3. If Drive is unavailable (network error, auth failure, missing file), system falls back to cached index and logs the degradation (audit entry with timestamp)
4. Every refresh logs data sources read, timestamps, and success/failure status (audit trail persists locally)

**Plans:** 2/2 plans complete
- [x] 15-01: Refresh Pipeline Implementation (Wave 1, 5 tasks, COMPLETE)
  - GoogleDriveClient: Drive API wrapper with credential management
  - merge_activity_into_index(): Preserves stalled_work and completions
  - RefreshAuditLogger: JSONL audit trail for all refresh attempts
  - refresh_persona_index(): Graceful fallback on Drive unavailability
  - Comprehensive test suite: 63 tests, all passing (0 failures)
  - Covers requirements: REFRESH-01, REFRESH-02, REFRESH-03

- [x] 15-02: Configuration & Integration (Wave 2, 4 tasks, COMPLETE)
  - Externalized refresh configuration (YAML, config.yaml) for operator customization
  - RefreshConfig dataclass + config_loader.py module with validation
  - Updated HIKMAH.__init__.py public API for Phase 16 consumption
  - README.md comprehensive Phase 15 documentation with Phase 16 integration example
  - All Phase 14-15 functions exposed in public API
  - Covers requirements: REFRESH-01, REFRESH-02, REFRESH-03 (documentation & integration)

---

### Phase 16: Message Generation & Variation
**Goal:** Generate fresh, actionable messages per intent by rephrasing intent, pulling updated index data, applying persona tone, and avoiding repetition from last 5 messages.

**Depends on:** Phase 14 (index available), Phase 15 (fresh data loaded)

**Requirements:** MSG-01, MSG-02, MSG-03, MSG-04

**Success Criteria** (what must be TRUE when phase completes):
1. Message generator rephrases the user intent (e.g., "You have open work on AI optimization" → "Your AI workflow could be faster — ready to tackle that?"), adds current context from index, applies persona character
2. System tracks last 5 messages per persona and detects exact phrase repeats (avoids sending identical phrasing twice in a row)
3. Generated message is actionable: nudges open topic, motivates action, or celebrates completion (not generic or passive)
4. Persona tone is consistent (e.g., AMMAR is builder-focused, HIKMAH is philosophical, TARIQ is strategic) across 5 consecutive test message generations

**Plans:** 2/2 plans planned
- [ ] 16-01: Core Infrastructure & Generator (Wave 1, 6 tasks, PLANNED)
  - Persona system prompts for all 11 personas (AMMAR, HIKMAH, TARIQ, MUNAWARA, MAL, BADAN, NAQD, SHURA, TAFRIGH, MARSAD, NIZAM)
  - RepetitionTracker: Last-5 message tracking with phrase-level deduplication (3-grams)
  - IntentProcessor: Extract topics from intent, build rich context from index
  - MessageLedger: JSONL audit trail with privacy gates (context_tags whitelist only)
  - Generator: Claude API with system prompt injection, error handling, exponential backoff
  - Public API in HIKMAH__knowledge_index.message_generation module
  - Addresses requirements: MSG-01 (rephrasing + tone), MSG-02 (repetition tracking), MSG-03 (actionability heuristic), MSG-04 (tone consistency via system prompts)

- [ ] 16-02: Test Suite & Integration (Wave 2, 6 tasks, PLANNED)
  - 5 test modules: conftest.py (fixtures), test_generator.py (9 tests), test_repetition_tracker.py (6 tests), test_intent_processor.py (10 tests), test_tone_consistency.py (5 tests)
  - 28+ tests total covering all MSG-01-04 requirements
  - MockClaude fixture for persona-specific responses without real API calls
  - Tone consistency validation: 5 consecutive message generations per persona
  - >80% coverage on core modules (generator.py, repetition_tracker.py, message_ledger.py, intent_processor.py)
  - README.md Phase 16 documentation with Phase 17 integration example
  - Addresses requirements: Comprehensive validation of MSG-01-04

---

### Phase 17: Delivery & Response Tracking
**Goal:** Deliver twice-daily scheduled Telegram nudges with unique message IDs and capture user responses within a 1-hour engagement window.

**Depends on:** Phase 16 (message generated), Phase 14 (index available)

**Requirements:** DELIVERY-01, DELIVERY-02, DELIVERY-03, DELIVERY-04, DELIVERY-05

**Success Criteria** (what must be TRUE when phase completes):
1. Messages are delivered twice daily (09:00 & 18:00 Cairo via Hermes cron) to Telegram using existing relay infrastructure
2. Each message receives a unique message_id, sent_at timestamp, and delivered_at timestamp; metadata stored in index
3. System monitors Telegram for user responses in 1-hour window after delivery (polls relay for incoming messages matching message_id)
4. Response received within 1-hour window is recorded with response_content and response_time; marked as "successful engagement"
5. Response tracking test validates: sent message recorded, monitor waits 1 hour, simulated response detected and logged

**Plans:** TBD

---

### Phase 18: Adaptation & Format Evolution
**Goal:** Track weekly response rates per persona and adapt message format when engagement drops below 80%, cycling through format variations.

**Depends on:** Phase 17 (response data available)

**Requirements:** ADAPT-01, ADAPT-02, ADAPT-03, ADAPT-04

**Success Criteria** (what must be TRUE when phase completes):
1. System calculates weekly response rate per persona: (responses_in_1hour / messages_sent) for past 7 days (e.g., 14/20 = 70%)
2. If response rate <80% for a persona, system automatically selects next format from rotation (e.g., [standard, short, emoji, direct_question, story] → next unuse format)
3. Format change is logged with rationale (e.g., "TARIQ response rate 65% < 80%, switching from 'standard' to 'short' format")
4. System never repeats same format twice consecutively; validates format rotation across 10 consecutive message generations under low-engagement scenario

**Plans:** TBD

---

### Phase 19: Cross-Pillar Integration
**Goal:** Wire knowledge-index messages to downstream pillars (MUNAWARA for actions, MAL for finance, TARIQ for strategy) so nudges feed broader intelligence system.

**Depends on:** Phase 16 (messages generated), Phase 14 (index available), Phase 18 (adaptation logic)

**Requirements:** INTEGRATION-01, INTEGRATION-02, INTEGRATION-03, INTEGRATION-04

**Success Criteria** (what must be TRUE when phase completes):
1. Messages referencing action items (MUNAWARA topic) trigger optional action-item creation in weekly task list (signal available, opt-in by user in Telegram reply)
2. Messages referencing financial goals (MAL topic) can pull latest financial snapshot and reflect updated context (e.g., "Your monthly target: $X, currently at $Y")
3. Messages referencing strategic goals (TARIQ topic) can pull latest position/progress and adapt nudge tone (e.g., celebrating progress vs. nudging stalled work)
4. Ledger append includes message_id, persona, content, pillar_signals_sent (array of [MUNAWARA, MAL, TARIQ] if triggered), response_status
5. Integration test: mock messages for each pillar, verify ledger record includes correct pillar_signals_sent

**Plans:** TBD

---

### Phase 20: Privacy & Safety Validation
**Goal:** Validate that knowledge index contains no raw personal data, Telegram messages expose only safe context tags, sensitive topics are flagged with confidence gates, and full test run passes privacy audit.

**Depends on:** All upstream phases (complete system ready for validation)

**Requirements:** PRIVACY-01, PRIVACY-02, PRIVACY-03

**Success Criteria** (what must be TRUE when phase completes):
1. Knowledge index inspection confirms: topics use only derived/tagged context (e.g., "achievement_count: 5" not "user accomplishment: …"); no raw PII, addresses, or sensitive personal identifiers stored
2. Telegram message review confirms: no raw personal data references, only safe context tags (e.g., "Your AI work" not "Seif's AI workflow"); sensitive topics (e.g., health, family) skipped if persona confidence <80%
3. Privacy classification check: all local files tagged strict_local per SYNC_POLICY; no egress to public folders or unencrypted Drive locations
4. Full test validation run: multiple personas generate 10+ messages across 2 days, all messages Telegram-readable, all indices remain local, no PII leakage to logs/console, auditor sign-off obtained

**Plans:** TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 14. Knowledge Index Schema & Storage | 5/5 | Complete    | 2026-06-20 |
| 15. Data Refresh & Synchronization | 2/2 | Complete    | 2026-06-20 |
| 16. Message Generation & Variation | 2/2 | Complete    | 2026-06-21 |
| 17. Delivery & Response Tracking | 0/? | Not started | — |
| 18. Adaptation & Format Evolution | 0/? | Not started | — |
| 19. Cross-Pillar Integration | 0/? | Not started | — |
| 20. Privacy & Safety Validation | 0/? | Not started | — |

---
