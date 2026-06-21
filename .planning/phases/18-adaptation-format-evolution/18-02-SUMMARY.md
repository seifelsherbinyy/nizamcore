---
phase: 18-adaptation-format-evolution
plan: "02"
subsystem: adaptation-generator-integration
tags:
  - phase-18
  - format-hint
  - adaptation-hook
  - integration-tests
  - generator
dependency_graph:
  requires:
    - 18-01  # WeeklyResponseRateCalculator, FormatRotationManager, AdaptationLogger
    - 16-01  # generate_message(), generate_and_dedupe() base implementation
  provides:
    - format_hint injection into system prompt
    - adaptation hook in generate_and_dedupe()
    - end-to-end feedback loop (delivery ledger → format rotation → constrained generation)
  affects:
    - 19-01  # cross-pillar integration will call generate_and_dedupe() with adaptation paths
    - 20-01  # privacy validation will see format_hint in ledger metadata
tech_stack:
  added:
    - FORMAT_CONSTRAINTS dict (generator.py module-level constant)
    - format_hint: Optional[str] parameter on generate_message()
    - delivery_ledger_path, adaptation_state_path, adaptation_ledger_path on generate_and_dedupe()
    - lazy import of WeeklyResponseRateCalculator + FormatRotationManager inside adaptation block
  patterns:
    - audit-before-apply (ledger written before state update)
    - lazy conditional import (avoids circular dependency risk)
    - backward-compatible parameter extension (all new params default to None)
    - no-consecutive-repeat enforcement via previous_format guard
key_files:
  created:
    - HIKMAH__knowledge_index/message_generation/tests/test_format_hint.py
    - HIKMAH__knowledge_index/adaptation/tests/test_integration.py
  modified:
    - HIKMAH__knowledge_index/message_generation/generator.py
    - HIKMAH__knowledge_index/__init__.py
    - HIKMAH__knowledge_index/README.md
decisions:
  - "Lazy import of adaptation classes inside generate_and_dedupe() adaptation block to avoid circular import risk"
  - "format_hint parameter position: after max_tokens to preserve backward-compat with positional callers"
  - "All 3 adaptation paths required (delivery_ledger_path AND adaptation_state_path AND adaptation_ledger_path) to enable adaptation; any None skips adaptation entirely"
  - "FORMAT_CONSTRAINTS.get(format_hint, empty_string) pattern: unknown hints and None key produce no change to system prompt"
metrics:
  duration_minutes: 20
  completed_date: "2026-06-21"
  tasks_completed: 3
  tasks_total: 3
  files_created: 2
  files_modified: 3
  tests_added: 26
  tests_total: 170
  coverage_adaptation_module: "98%"
requirements_satisfied:
  - ADAPT-01
  - ADAPT-02
  - ADAPT-03
  - ADAPT-04
---

# Phase 18 Plan 02: Adaptation-Generator Integration Summary

**One-liner:** Format hint injection and adaptation hook wired into generator.py, validated by 8 integration tests — closing the adaptive messaging feedback loop end-to-end.

---

## What Was Built

### Task 1: generate_message() format_hint + generate_and_dedupe() adaptation hook

Modified `HIKMAH__knowledge_index/message_generation/generator.py`:

- Added `FORMAT_CONSTRAINTS` dict at module level with 5 entries (`standard`, `short`, `emoji`, `direct_question`, `story`). `standard` maps to `""` (no change); unknown hints fall back to `""` via `.get()`.
- Added `format_hint: Optional[str] = None` parameter to `generate_message()`. When not None, appends `FORMAT_CONSTRAINTS.get(format_hint, "")` to system_prompt before the Claude API call.
- Added `delivery_ledger_path`, `adaptation_state_path`, `adaptation_ledger_path` (all `Optional[Path] = None`) to `generate_and_dedupe()`.
- Added adaptation block at function start: if all 3 paths provided, calls `WeeklyResponseRateCalculator.calculate(persona, days=7)`. If rate < 0.80, calls `FormatRotationManager.rotate_format()` then `get_current_format()` to set `format_hint`.
- Lazy import of adaptation classes (`from HIKMAH__knowledge_index.adaptation import ...`) inside the `if all([...])` block to avoid circular import risk.
- Passes `format_hint=format_hint` to every `generate_message()` call inside the retry loop.

18 new tests in `test_format_hint.py`: all 8 described behaviors validated. All 81 original Phase 16 tests still pass (0 regressions).

### Task 2: Integration tests — end-to-end adaptation flow

Created `HIKMAH__knowledge_index/adaptation/tests/test_integration.py` with 8 tests:

| Test | What it validates |
|------|-------------------|
| `test_rate_calc_counts_responses` | 20 deliveries + 13 responses → rate=0.65, num=13, den=20 |
| `test_rate_calc_within_7_days` | Deliveries older than 7 days excluded from denominator |
| `test_no_format_hint_when_rate_sufficient` | rate=0.90 → format_hint=None, no ADAPTATION_LEDGER written |
| `test_format_hint_injected_when_rate_low` | rate=0.65 → format_hint is not None and is in FORMATS |
| `test_ten_consecutive_no_repeats` | 10 consecutive rotate_format() calls → zero adjacent identical formats **(ADAPT-04)** |
| `test_adaptation_ledger_written_before_format_applied` | ADAPTATION_LEDGER entry exists immediately after rotate_format() |
| `test_rationale_string_format` | Rationale matches "TARIQ response rate 65% < 80%, switching from 'standard' to 'short' format" |
| `test_no_repeat_validated_against_state` | 2nd rotation does not return 'standard' (previous_format guard active) |

All 8 pass.

### Task 3: Parent __init__.py exports + Phase 18 README section

- Added Phase 18 import block to `HIKMAH__knowledge_index/__init__.py` exporting `WeeklyResponseRateCalculator`, `FormatRotationManager`, `AdaptationLogger`, `AdaptationState` — all 4 added to `__all__`.
- Added 131-line Phase 18 section to `README.md` including: architecture ASCII diagram, format rotation cycle table, how-adaptation-works steps, key files table, integration code example, guards and safety table, ADAPT requirements coverage table.

---

## Verification Results

```
pytest adaptation/tests/ message_generation/tests/ — 170 passed
Phase 16 regression check — 81 passed (0 regressions)
Adaptation module coverage — 98%
test_ten_consecutive_no_repeats — PASSED (ADAPT-04 validated)
Import check — from HIKMAH__knowledge_index import WeeklyResponseRateCalculator, FormatRotationManager — OK
```

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Self-Check: PASSED

- `HIKMAH__knowledge_index/message_generation/generator.py` — EXISTS, contains `FORMAT_CONSTRAINTS` and `format_hint`
- `HIKMAH__knowledge_index/message_generation/tests/test_format_hint.py` — EXISTS, 18 tests
- `HIKMAH__knowledge_index/adaptation/tests/test_integration.py` — EXISTS, 8 tests
- `HIKMAH__knowledge_index/__init__.py` — EXISTS, Phase 18 imports present
- `HIKMAH__knowledge_index/README.md` — EXISTS, Phase 18 section 131 lines
- Commits: 9035ec4, 004245e, 2da5970 — all present
