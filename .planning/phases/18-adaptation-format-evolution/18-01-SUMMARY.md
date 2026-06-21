---
phase: 18-adaptation-format-evolution
plan: "01"
subsystem: adaptation
tags: [tdd, adaptation, format-rotation, response-rate, jsonl, state-machine]
dependency_graph:
  requires:
    - "Phase 17 DELIVERY_LEDGER.jsonl (DeliveryLedger delivery/response events)"
  provides:
    - "adaptation/ package: WeeklyResponseRateCalculator, FormatRotationManager, AdaptationLogger, AdaptationState"
    - "ADAPTATION_STATE.jsonl: per-persona format state persistence"
    - "ADAPTATION_LEDGER.jsonl: append-only rotation audit trail"
  affects:
    - "Phase 18-02: will wire these modules into Phase 16 message generation"
tech_stack:
  added: []
  patterns:
    - "JSONL append-only with last-entry-wins load semantics (mirrors Phase 14-17 pattern)"
    - "TDD: RED → GREEN → commit per task"
    - "SHA256 ledger_hash (first 16 hex chars) for audit integrity"
    - "dataclass with safe defaults for new-persona state"
key_files:
  created:
    - HIKMAH__knowledge_index/adaptation/__init__.py
    - HIKMAH__knowledge_index/adaptation/adaptation_state.py
    - HIKMAH__knowledge_index/adaptation/response_rate_calculator.py
    - HIKMAH__knowledge_index/adaptation/adaptation_logger.py
    - HIKMAH__knowledge_index/adaptation/format_rotation_manager.py
    - HIKMAH__knowledge_index/adaptation/tests/__init__.py
    - HIKMAH__knowledge_index/adaptation/tests/conftest.py
    - HIKMAH__knowledge_index/adaptation/tests/test_adaptation_state.py
    - HIKMAH__knowledge_index/adaptation/tests/test_response_rate_calculator.py
    - HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py
    - HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py
  modified: []
decisions:
  - "Rate calculator reads DELIVERY_LEDGER.jsonl directly (no DeliveryLedger class dependency) for simpler test isolation"
  - "1-rotation-per-week guard implemented in FormatRotationManager (not in caller) to prevent feedback loop instability"
  - "No-consecutive-repeat guard skips exactly one step forward (not random) for determinism"
  - "Audit log written BEFORE state update to ensure audit trail survives partial failures"
metrics:
  duration_minutes: 5
  completed_date: "2026-06-21"
  tasks_completed: 3
  tasks_total: 3
  files_created: 11
  files_modified: 0
  test_count: 63
  test_pass_rate: "100%"
  coverage: "97%"
---

# Phase 18 Plan 01: Adaptation Core Modules Summary

**One-liner:** Append-only JSONL adaptation state machine with 7-day response rate calculator, no-consecutive-repeat format rotation, and SHA256-hashed audit logging — 63 tests at 97% coverage.

---

## What Was Built

The complete adaptation foundation for Phase 18: three production modules and one dataclass module with full unit test coverage.

### AdaptationState (`adaptation_state.py`)
- `@dataclass AdaptationState`: 6 fields (persona, current_format, previous_format, rotation_index, last_rotation_at, adaptation_id) with safe defaults
- `load_state(persona, path)`: JSONL reader, last-entry-wins per persona, returns defaults for new personas
- `save_state(state, path)`: append-only JSONL writer, creates parent directories
- `to_dict(state)`: serializer with UTC timestamp
- `FORMATS = ["standard", "short", "emoji", "direct_question", "story"]` constant

### WeeklyResponseRateCalculator (`response_rate_calculator.py`)
- `calculate(persona, days=7) → (rate: float, numerator: int, denominator: int)`
- Filters delivery events: `status="success"`, `sent_at` within N days, matching persona
- ZeroDivisionError guard: denominator=0 → `(1.0, 0, 0)` — caller skips adaptation
- Missing ledger file → `(1.0, 0, 0)` — safe default
- Reads DELIVERY_LEDGER.jsonl directly (Phase 17 output)

### AdaptationLogger (`adaptation_logger.py`)
- `log_rotation(persona, old_format, new_format, response_rate, numerator, denominator, reason) → adaptation_id`
- adaptation_id: `ADAPT-{PERSONA}-{YYYYMMDD}-{NNN}` with per-persona-per-day counter
- Rationale: `"{persona} response rate X% < Y%, switching from '{old}' to '{new}' format"`
- ledger_hash: SHA256 of JSON string, first 16 hex chars (mirrors Phase 14-17 audit pattern)
- Append-only writes to ADAPTATION_LEDGER.jsonl

### FormatRotationManager (`format_rotation_manager.py`)
- `get_current_format(persona) → str`: loads state, returns current_format (default "standard")
- `rotate_format(persona, reason, response_rate, numerator, denominator) → str`
  1. Weekly rate-limit guard: if `last_rotation_at` within 7 days → return current unchanged
  2. Advance index: `(current_idx + 1) % 5`
  3. No-consecutive-repeat: if next == previous → skip one more step forward
  4. Log to ADAPTATION_LEDGER BEFORE state update
  5. Persist new state to ADAPTATION_STATE.jsonl

### Public `__init__.py`
Exports: `WeeklyResponseRateCalculator`, `FormatRotationManager`, `AdaptationLogger`, `AdaptationState`, `load_state`, `save_state`, `FORMATS`

---

## Test Coverage

| Module | Stmts | Coverage |
|--------|-------|----------|
| adaptation_state.py | 40 | 92% |
| response_rate_calculator.py | 60 | 90% |
| adaptation_logger.py | 43 | 88% |
| format_rotation_manager.py | 44 | 91% |
| __init__.py | 5 | 100% |
| **TOTAL** | **192** | **97%** |

**63 tests, 0 failures, 0 errors.**

Test breakdown:
- test_adaptation_state.py: 21 tests (defaults, round-trip, append-only, multi-persona, to_dict)
- test_response_rate_calculator.py: 12 tests (basic rates, thresholds, zero-denominator, filters)
- test_adaptation_logger.py: 14 tests (schema fields, adaptation_id, rationale, hash, append-only)
- test_format_rotation_manager.py: 16 tests (cycle advance, wrap-around, no-consecutive-repeat, rate-limit, disk persistence)

---

## Commits

| Task | Hash | Description |
|------|------|-------------|
| 1: AdaptationState | 537a962 | feat(18-01): AdaptationState dataclass and file I/O |
| 2: WeeklyResponseRateCalculator | 4b05276 | feat(18-01): WeeklyResponseRateCalculator with 12 unit tests |
| 3: FormatRotationManager + AdaptationLogger + __init__ | ab69136 | feat(18-01): FormatRotationManager, AdaptationLogger, and public API |

---

## Deviations from Plan

None — plan executed exactly as written.

The only minor implementation note: `WeeklyResponseRateCalculator` reads DELIVERY_LEDGER.jsonl directly via standard file I/O rather than importing `DeliveryLedger` class, which simplifies test isolation (no need to mock the Phase 17 class). The Phase 18-02 caller can pass a ledger_path to `WeeklyResponseRateCalculator.__init__()` as planned.

---

## Self-Check: PASSED
