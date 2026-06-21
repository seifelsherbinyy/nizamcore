---
phase: 17-delivery-response-tracking
plan: "02"
subsystem: HIKMAH__knowledge_index/delivery
tags: [delivery, orchestrator, response-monitor, telegram, hermes-relay, daemon-threads, jsonl-ledger, crash-safe]
dependency_graph:
  requires:
    - Phase 17-01 Wave 1 (MessageIDGenerator, DeliveryLedger, TelegramRelayClient)
    - NIZAM__system.relay.poller (tg_send_message, tg_get_updates, GatewayPollingConflict)
    - Phase 16 message_generation (generate_and_dedupe → message_text consumed by deliver())
  provides:
    - DeliveryOrchestrator (full delivery lifecycle: ID gen → relay send → ledger log → monitor spawn)
    - ResponseMonitor (daemon thread polling for replies within 1-hour engagement window)
    - DeliveryResult (dataclass: message_id, telegram_message_id, sent_at, delivered_at, status, error)
  affects:
    - Phase 18 Adaptation (queries DeliveryLedger for response rate: responses / deliveries)
    - Scheduler (calls orchestrator.deliver() twice daily via Hermes cron)
tech_stack:
  added: []
  patterns:
    - Fail-safe pre-send logging (message_id recorded before relay call → crash protection)
    - Daemon thread per message (exit with main process, no zombie threads)
    - 30s poll interval (balance: latency vs. relay load)
    - reply_to_message_id exact match (Telegram native correlation, no custom conventions)
    - threading.Lock for _global_offset (thread-safe deduplication across monitors)
    - GatewayPollingConflict backoff (60s, prevents relay ownership conflicts)
key_files:
  created:
    - HIKMAH__knowledge_index/delivery/delivery_orchestrator.py
    - HIKMAH__knowledge_index/delivery/response_monitor.py
    - HIKMAH__knowledge_index/delivery/tests/test_orchestrator.py
    - HIKMAH__knowledge_index/delivery/tests/test_response_monitor.py
  modified:
    - HIKMAH__knowledge_index/delivery/__init__.py
    - HIKMAH__knowledge_index/delivery/tests/conftest.py
    - HIKMAH__knowledge_index/__init__.py
    - pytest.ini
decisions:
  - "DeliveryOrchestrator logs pre-send 'pending' entry BEFORE relay call — fail-safe audit trail even if relay call crashes mid-flight"
  - "ResponseMonitor uses daemon threads (not asyncio) — fits existing threading model; daemon=True means no zombies on process exit"
  - "Poll interval is 30s (not 25s Telegram timeout) — keeps polls short, allows relay long-poll to complete before we check again"
  - "fresh_sent_at() test helper required — SAMPLE_SENT_AT is historical (past deadline), tests needing active windows use current UTC"
  - "Context_tags ValueError propagated (not caught) — invalid tags are a caller coding error, not a runtime failure"
metrics:
  duration: "14 minutes"
  completed_date: "2026-06-21"
  tasks_completed: 4
  tasks_total: 4
  files_created: 4
  files_modified: 4
---

# Phase 17 Plan 02: Delivery Orchestrator & Response Monitor Summary

**One-liner:** Fail-safe message delivery orchestrator with daemon-thread response monitoring via reply_to_message_id correlation within 1-hour engagement windows.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 0 | Create Delivery Orchestrator | 9e830c7 | delivery/delivery_orchestrator.py |
| 1 | Create Response Monitor | 79761e8 | delivery/response_monitor.py |
| 2 | Create Comprehensive Test Suite | 450b4e7 | tests/test_orchestrator.py, tests/test_response_monitor.py |
| 3 | Update Public API Exports | 132e672 | delivery/__init__.py, HIKMAH__knowledge_index/__init__.py |

## Wave 2 Components Implemented

### DeliveryOrchestrator (delivery_orchestrator.py)

Orchestrates the complete message delivery lifecycle in `deliver()`:

1. **Step 1: Generate message_id** — `MessageIDGenerator.generate()` called BEFORE relay
2. **Step 2: Pre-send log** — `ledger.log_delivery(status="pending")` written BEFORE relay call (crash safety)
3. **Step 3: Relay send** — `TelegramRelayClient.send_message()` called (try/except on all exceptions)
4a. **Success path** — `ledger.log_delivery(status="success", telegram_message_id=...)` + `response_monitor.monitor()`
4b. **Failure path** — `ledger.log_delivery(status="failure", error_reason=str(exc))`, returns failure result
5. **Return DeliveryResult** — dataclass with full delivery metadata

Key design: All relay exceptions are caught and returned as failure DeliveryResult. No exceptions propagate to caller. Pre-send "pending" entry ensures every attempted send is traceable even if the process crashes between relay call and confirmation.

### ResponseMonitor (response_monitor.py)

Background polling for user replies within engagement window:

- `monitor()` — Non-blocking: spawns daemon thread, returns immediately
- `_monitor_loop()` — Polls `get_updates()` every 30 seconds until deadline or response found
- Response correlation: `check_reply_to_message_id(update) == telegram_message_id` (exact integer match)
- Offset tracking: `_global_offset` updated after each poll cycle (prevents update replay)
- Lock protection: `threading.Lock` on `_global_offset` for concurrent monitors
- On response: logs `log_response()` with engagement_latency_seconds, exits thread
- On deadline: logs `log_no_response()` (engagement_window_closed event), exits thread
- On GatewayPollingConflict: sleeps 60s, retries (Hermes relay may own polling channel)
- On other errors: sleeps 30s, retries (never propagates, thread never crashes)

### DeliveryResult (dataclass)

```python
@dataclass
class DeliveryResult:
    message_id: str           # MSG-{YYYYMMDDHHMMSSMMMM}-{8-HEX}
    telegram_message_id: Optional[int]  # Telegram's ID (None on failure)
    sent_at: str              # ISO 8601 UTC (before relay call)
    delivered_at: Optional[str]  # ISO 8601 UTC (after relay confirms)
    status: Literal["success", "failure"]
    error: Optional[str]      # Error message if failure
```

## Test Suite

**36 tests total, 36/36 passing.**

| File | Tests | Coverage Areas |
|------|-------|----------------|
| test_orchestrator.py | 17 | delivery flow, unique IDs, timestamps, ledger entries, relay error handling, monitor spawning, integration |
| test_response_monitor.py | 19 | daemon thread spawning, deadline calculation, response detection, latency calc, no-response timeout, polling conflict, network errors, offset tracking |

Key test infrastructure:
- `MockTelegramRelay`: Simulates tg_send_message/tg_get_updates with configurable responses
- `fresh_sent_at()`: Returns current UTC ISO timestamp for tests needing active polling windows
- `make_reply_update()` / `make_non_reply_update()`: Update dict factories for correlation testing
- No real Telegram API calls; no real sleep in orchestrator tests

**Deviation discovered (auto-fixed, Rule 1):** Initial tests used `SAMPLE_SENT_AT` (historical 09:30 UTC) with short `window_seconds` values. The monitor loop immediately exits when deadline is already in the past, so tests needing active polling windows produced false results. Fixed by adding `fresh_sent_at()` helper and updating 12 tests to use current UTC as sent_at.

## Requirements Satisfied

| Requirement | Satisfied By | Status |
|-------------|-------------|--------|
| DELIVERY-01 | DeliveryOrchestrator.deliver() calls TelegramRelayClient.send_message() | Full |
| DELIVERY-02 | MessageIDGenerator.generate() called per deliver() (unique per send) | Full |
| DELIVERY-03 | DeliveryLedger.log_delivery() records sent_at, delivered_at, telegram_message_id | Full |
| DELIVERY-04 | ResponseMonitor._monitor_loop() polls until deadline (1-hour window enforced) | Full |
| DELIVERY-05 | DeliveryLedger.log_response() records response_text + engagement_latency_seconds | Full |

Wave 1 + Wave 2 together satisfy all 5 DELIVERY requirements.

## Thread Model

```
Main process
├── orchestrator.deliver() → synchronous
│   ├── MessageIDGenerator.generate()      # <1ms
│   ├── DeliveryLedger.log_delivery()      # <5ms (JSONL append)
│   ├── TelegramRelayClient.send_message() # 1-5s (network)
│   ├── DeliveryLedger.log_delivery()      # <5ms
│   └── ResponseMonitor.monitor()          # <1ms (spawns thread)
│
└── [daemon thread] ResponseMonitor._monitor_loop()
    ├── Every 30s: get_updates(offset=N, timeout=25)
    ├── On reply match: log_response() → exit
    └── After deadline: log_no_response() → exit
```

Typical NIZAM load: ~1 active monitor thread at any time (22 messages/day, 1-hour windows).
Maximum concurrent: 11 personas × 2 sends within same hour = 22 (rare scenario).

## Integration Points

**Upstream (Phase 16):**
```python
message_text, ok, reason = generate_and_dedupe(persona="AMMAR", ...)
result = orchestrator.deliver(persona="AMMAR", message_text=message_text, ...)
```

**Downstream (Phase 18):**
```python
# Phase 18 queries DeliveryLedger to compute response_rate
deliveries = ledger.get_deliveries_for_persona("AMMAR", limit=14)
responses = [ledger.get_responses_for_message(d["message_id"]) for d in deliveries]
response_rate = len([r for r in responses if r]) / len(deliveries)
# response_rate < 0.80 → trigger format rotation
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SAMPLE_SENT_AT causes premature window expiration in tests**
- **Found during:** Task 2 (test suite implementation)
- **Issue:** `SAMPLE_SENT_AT = "2026-06-21T09:30:45+00:00"` is a historical timestamp. ResponseMonitor's `_monitor_loop()` has `while datetime.now(utc) < deadline` — with a 1-second window from a past timestamp, the deadline was already passed before the thread started. Tests expecting polling to occur got no-response events instead.
- **Fix:** Added `fresh_sent_at()` helper in conftest.py that returns `datetime.now(timezone.utc).isoformat()`. Updated 12 response monitor tests to use `fresh_sent_at()` for sent_at when they need active polling windows. Tests validating window expiration still use `SAMPLE_SENT_AT` (which correctly triggers immediate expiration).
- **Files modified:** conftest.py, test_response_monitor.py
- **Commit:** 450b4e7

**2. [Rule 2 - Missing critical functionality] pytest.ini lacked delivery test paths and timeout marker**
- **Found during:** Task 2 (test collection)
- **Issue:** `pytest.ini` didn't include delivery test paths; `--strict-markers` mode rejected `@pytest.mark.timeout` used in one test.
- **Fix:** Added `HIKMAH__knowledge_index/delivery/tests` and `HIKMAH__knowledge_index/message_generation/tests` to `testpaths`; added `timeout` marker registration; removed the `@pytest.mark.timeout(5)` decorator since `pytest-timeout` plugin is not installed (replaced with simpler wait logic).
- **Files modified:** pytest.ini
- **Commit:** 450b4e7

## Self-Check: PASSED

Files verified to exist:
- HIKMAH__knowledge_index/delivery/delivery_orchestrator.py: FOUND
- HIKMAH__knowledge_index/delivery/response_monitor.py: FOUND
- HIKMAH__knowledge_index/delivery/tests/test_orchestrator.py: FOUND
- HIKMAH__knowledge_index/delivery/tests/test_response_monitor.py: FOUND

Commits verified:
- 9e830c7: Task 0 — DeliveryOrchestrator
- 79761e8: Task 1 — ResponseMonitor
- 450b4e7: Task 2 — Test suite (36 tests)
- 132e672: Task 3 — Public API exports

Import verification:
- `from HIKMAH__knowledge_index.delivery import DeliveryOrchestrator, ResponseMonitor, DeliveryResult` — OK
- `from HIKMAH__knowledge_index import DeliveryOrchestrator, DeliveryResult, ResponseMonitor` — OK
- All 36 tests: PASSED (36/36)
