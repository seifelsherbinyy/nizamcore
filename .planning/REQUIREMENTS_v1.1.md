# Requirements: NIZAM v1.1 — Persona Knowledge Index & Adaptive Messaging

**Defined:** 2026-06-20  
**Core Value:** Each persona delivers fresh, contextual, actionable nudges twice daily — refreshing user knowledge, motivating action on open topics, celebrating closed topics — with adaptive messaging that evolves when engagement drops.

## v1.1 Requirements

### Knowledge Index & Schema

- [ ] **INDEX-01**: Each persona has optimized JSON knowledge index schema (topics, status, timestamps, context, activity history)
- [ ] **INDEX-02**: Knowledge index tracks: open/active topics, completed/closed topics, user accomplishments, stalled work, context snapshots
- [ ] **INDEX-03**: Knowledge index stored locally (strict_local per SYNC_POLICY); never egressed to Telegram/Drive
- [ ] **INDEX-04**: Index versioning + schema evolution support (future persona additions)

### Data Refresh & Synchronization

- [ ] **REFRESH-01**: Knowledge index refreshes from Google Drive conversation logs/activity on each message generation
- [ ] **REFRESH-02**: Refresh handles missing/unavailable Drive data gracefully (cached index if refresh fails)
- [ ] **REFRESH-03**: Refresh logs all data sources read + timestamps (audit trail)

### Message Generation & Variation

- [ ] **MSG-01**: Each persona generates fresh message: rephrase intent + pull new index data + apply persona tone
- [ ] **MSG-02**: Message avoids repetition (tracks last 5 messages, doesn't duplicate phrasing)
- [ ] **MSG-03**: Message is actionable (nudge to activity, reminder on open topic, or celebration of closed topic)
- [ ] **MSG-04**: Message respects persona character (AMMAR builds, HIKMAH philosophizes, TARIQ strategizes, BADAN heals, MAL enriches, etc.)

### Delivery & Response Tracking

- [x] **DELIVERY-01**: Scheduled delivery twice daily (09:00 & 18:00 Cairo via Hermes cron) to Telegram
- [x] **DELIVERY-02**: Message includes unique message_id for response tracking
- [x] **DELIVERY-03**: System records: sent_at, delivered_at, message_content, message_id
- [x] **DELIVERY-04**: Response tracking monitors Telegram for user response within 1-hour window
- [x] **DELIVERY-05**: If response received → mark as successful, record response content + time

### Adaptation & Format Changes

- [ ] **ADAPT-01**: Track response rate per persona per week (≥80% in 1-hour window = successful messaging)
- [ ] **ADAPT-02**: If response rate <80% → persona adapts format (shorter, longer, emoji, direct question, story format, etc.)
- [ ] **ADAPT-03**: Adaptation changes logged with rationale (which format being tried next)
- [ ] **ADAPT-04**: System never repeats same format twice in a row (cycling through N variations)

### Integration & Signaling

- [ ] **INTEGRATION-01**: Messages can reference/trigger MUNAWARA action items
- [ ] **INTEGRATION-02**: Messages can reference MAL financial context or goals
- [ ] **INTEGRATION-03**: Messages can reference TARIQ strategic goals or progress
- [ ] **INTEGRATION-04**: Ledger writes: persona_message_log with message_id, persona, content, response_status, adaptation_trigger

### Privacy & Safety

- [ ] **PRIVACY-01**: Knowledge index never includes raw personal data; only derived/tagged context
- [ ] **PRIVACY-02**: No user PII in Telegram messages (references only to safe context tags)
- [ ] **PRIVACY-03**: Sensitive topics flagged in index; persona skips them if confidence <80%

## Future Requirements (v1.2+)

- **MULTI-01**: Multi-channel delivery (email, Slack, in-app notifications)
- **LEARNING-01**: ML-based tone/format optimization (beyond manual persona tuning)
- **COLLABORATION-01**: Personas discussing/debating before sending (SHURA consensus)

## Out of Scope (v1.1)

| Feature | Reason |
|---------|--------|
| Multi-channel delivery | Telegram proven; add in v1.2 after v1.1 validates core messaging |
| Auto-response generation from user replies | v1 is nudge-only; conversation in future |
| Persona-to-persona discussion before sending | Defer; single-persona messages first |
| Machine learning tone optimization | Manual persona tuning sufficient for v1 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INDEX-01 | 14 | Pending |
| INDEX-02 | 14 | Pending |
| INDEX-03 | 14 | Pending |
| INDEX-04 | 14 | Pending |
| REFRESH-01 | 15 | Pending |
| REFRESH-02 | 15 | Pending |
| REFRESH-03 | 15 | Pending |
| MSG-01 | 16 | Pending |
| MSG-02 | 16 | Pending |
| MSG-03 | 16 | Pending |
| MSG-04 | 16 | Pending |
| DELIVERY-01 | 17 | Complete |
| DELIVERY-02 | 17 | Complete |
| DELIVERY-03 | 17 | Complete |
| DELIVERY-04 | 17 | Complete |
| DELIVERY-05 | 17 | Complete |
| ADAPT-01 | 18 | Pending |
| ADAPT-02 | 18 | Pending |
| ADAPT-03 | 18 | Pending |
| ADAPT-04 | 18 | Pending |
| INTEGRATION-01 | 19 | Pending |
| INTEGRATION-02 | 19 | Pending |
| INTEGRATION-03 | 19 | Pending |
| INTEGRATION-04 | 19 | Pending |
| PRIVACY-01 | 20 | Pending |
| PRIVACY-02 | 20 | Pending |
| PRIVACY-03 | 20 | Pending |

**Coverage:**
- v1.1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---

*Requirements defined: 2026-06-20*  
*Roadmap created: 2026-06-20*  
*Last updated: 2026-06-20 after Phase 14-20 roadmap creation*
