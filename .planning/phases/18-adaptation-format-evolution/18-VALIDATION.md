---
phase: 18
slug: adaptation-format-evolution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-21
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (3.11+) |
| **Config file** | pytest.ini (existing HIKMAH__knowledge_index, Phase 14-17 config) |
| **Quick run command** | `pytest HIKMAH__knowledge_index/adaptation/tests/ -x -v` |
| **Full suite command** | `pytest HIKMAH__knowledge_index/adaptation/tests/ -v --cov=HIKMAH__knowledge_index/adaptation --cov-report=term-missing` |
| **Estimated runtime** | ~45 seconds (quick), ~60 seconds (full with coverage) |

---

## Sampling Rate

- **After every task commit:** Run `pytest HIKMAH__knowledge_index/adaptation/tests/ -x -v`
- **After every plan wave:** Run `pytest HIKMAH__knowledge_index/adaptation/tests/ -v --cov=HIKMAH__knowledge_index/adaptation --cov-report=term-missing`
- **Before `/gsd:verify-work`:** Full suite must be green with ≥80% coverage
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | ADAPT-01 | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_response_rate_calculator.py -x` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | ADAPT-02 | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py -x` | ❌ W0 | ⬜ pending |
| 18-01-03 | 01 | 1 | ADAPT-03 | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py -x` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 2 | ADAPT-02 | integration | `pytest HIKMAH__knowledge_index/adaptation/tests/test_integration.py::test_rate_calc_counts_responses -x` | ❌ W0 | ⬜ pending |
| 18-02-02 | 02 | 2 | ADAPT-04 | integration | `pytest HIKMAH__knowledge_index/adaptation/tests/test_integration.py::test_ten_consecutive_no_repeats -x` | ❌ W0 | ⬜ pending |
| 18-02-03 | 02 | 2 | ADAPT-01-04 | integration | `pytest HIKMAH__knowledge_index/adaptation/tests/test_integration.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `HIKMAH__knowledge_index/adaptation/response_rate_calculator.py` — WeeklyResponseRateCalculator.calculate() with denominator=0 guard
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_response_rate_calculator.py` — 8 tests covering basic calc, edge cases, time filtering
- [ ] `HIKMAH__knowledge_index/adaptation/format_rotation_manager.py` — FormatRotationManager state machine with no-repeat enforcement
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py` — 12 tests covering rotation sequence, no-repeat, 5+ rotations
- [ ] `HIKMAH__knowledge_index/adaptation/adaptation_logger.py` — AdaptationLogger with JSONL append and metadata
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py` — 6 tests covering ledger writes, timestamps, rationale format
- [ ] `HIKMAH__knowledge_index/adaptation/adaptation_state.py` — AdaptationState dataclass with file I/O per persona
- [ ] `HIKMAH__knowledge_index/adaptation/tests/conftest.py` — shared fixtures with MockDeliveryLedger
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_integration.py` — 8 integration tests: rate calc → rotation → no-repeat validation
- [ ] `HIKMAH__knowledge_index/adaptation/__init__.py` — public API exports
- [ ] `HIKMAH__knowledge_index/README.md` (update) — Phase 18 architecture section
- [ ] `HIKMAH__knowledge_index/__init__.py` (update) — Phase 18 exports

**Total:** 12 new files + 2 updates.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Format rotation responds to actual 7-day response rate changes in production | ADAPT-02, ADAPT-04 | Production engagement data not reproducible in unit tests (depends on real user responses over 7 days) | After Phase 18 deployed: Observe ADAPTATION_LEDGER.jsonl for 2+ weeks. Verify rotation triggered when response_rate <80%. Check no-repeat constraint in format sequence. |
| Format-hint injection does not break Phase 16 message generation | ADAPT-02 | Integration between Phase 16 (existing, heavily used) and Phase 18 (new) requires live testing to catch regression | Run Phase 16 message generation with format_hint=None (default). Verify output unchanged vs. Phase 16 baseline. Then test with format_hint='short', verify constraints applied. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (12 new + 2 updates)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter after execution

**Approval:** pending — will sign off after execution phase completes with >80% coverage

---

## Requirements Coverage

| Req ID | Tests | Coverage |
|--------|-------|----------|
| ADAPT-01 (weekly rate calc) | test_calculate_basic, test_calculate_no_deliveries, test_rate_calc_counts_responses | 3 tests |
| ADAPT-02 (format rotation <80%) | test_rotate_advances_format, test_rotate_no_consecutive_repeat, test_ten_rotations_no_repeats, test_integration | 4 tests |
| ADAPT-03 (log with rationale) | test_log_rotation_writes_entry, test_log_rotation_includes_metadata, test_rationale_format | 3 tests |
| ADAPT-04 (no-repeat constraint) | test_ten_consecutive_no_repeats, test_no_repeat_validated_against_state | 2 tests |

**Total test cases:** 34+ (unit + integration)
