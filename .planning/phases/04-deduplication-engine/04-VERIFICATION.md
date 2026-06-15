---
phase: 04-deduplication-engine
verified: 2026-06-15T18:30:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 04: Deduplication Engine Verification Report

**Phase Goal:** Normalize opportunities into canonical form, apply fuzzy matching, and maintain a persistent seen-role store so reruns do not surface already-seen roles.

**Verified:** 2026-06-15T18:30:00Z  
**Status:** PASSED  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Opportunities are normalized (title/company/location/URL canonicalization) into a deterministic dedup key | VERIFIED | `compute_dedup_key()` returns deterministic tuple; handles company suffixes (Inc., LLC, Ltd); location collapses "remote" variants |
| 2 | Fuzzy matching with `rapidfuzz` (token_sort_ratio/partial_token_sort_ratio ≥0.88) detects duplicates within a single run | VERIFIED | `fuzzy_match_opportunities()` uses `partial_token_sort_ratio >= 0.88`; detects title variants ("AI Ops Manager" vs "AI Operations Manager" → 0.963); avoids false positives ("Finance Manager" vs "AI Ops Manager" → 0.727) |
| 3 | Re-running the radar against the same sources does not re-surface already-seen roles; seen-store is consulted before including in results | VERIFIED | `DedupeEngine.check_or_add()` persists to SQLite; second run returns 0 new roles (all suppressed); integration verified via `run_dedup_pass()` |
| 4 | Freshness rule allows genuine reposts (same role posted >30 days after first seen) to surface as new | VERIFIED | `is_fresh_repost()` returns True for gaps >= 30 days (45-day test: True); False for gaps < 30 days (10-day test: False); edge case (exactly 30 days): True |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `TARIQ__career_radar/radar/dedup_engine.py` | Normalization functions + fuzzy + freshness + run_dedup_pass | VERIFIED | Contains all 4 components; `normalize_title()`, `normalize_company()`, `normalize_location()`, `compute_dedup_key()` exist; `fuzzy_match_opportunities()` and `is_fresh_repost()` implemented; `run_dedup_pass()` delegates to stages/dedup.py |
| `TARIQ__career_radar/radar/stages/dedup.py` | Full orchestrator combining SQLite + fuzzy + freshness | VERIFIED | File exists with `run_dedup_pass()` function; implements pipeline: (1) check_or_add cross-run, (2) freshness rule check, (3) fuzzy within-run |
| `TARIQ__career_radar/radar/stages/__init__.py` | Package marker for stages module | VERIFIED | File exists (70 bytes) |
| `TARIQ__career_radar/tests/test_dedup_engine.py` | 9 tests (3 Phase-1 + 6 Phase-4) | VERIFIED | All 9 tests collected and passing; phase-1 tests unchanged; phase-4 tests: test_fuzzy_match_title_variants, test_fuzzy_match_no_false_positive, test_fuzzy_match_same_company_exact_location, test_is_fresh_repost_old_role_surfaces, test_is_fresh_repost_recent_stays_hidden, test_run_dedup_pass_removes_within_run_dups |
| `TARIQ__career_radar/tests/fixtures/dedup_test_data.jsonl` | 50+ role pairs with title variants, cross-source, >30-day gaps | VERIFIED | File exists with 52 records (≥50 required); confirmed cross-source pairs (greenhouse/remotive); confirmed records with access_date "2026-01-10" (>30 days before 2026-06-15) |
| `TARIQ__career_radar/conftest.py` | Phase-4 fixtures: dedup_opp_pairs, dedup_fresh_record, cross_source_batch | VERIFIED | All 3 fixtures added; dedup_opp_pairs loads JSONL; dedup_fresh_record returns first_seen 45 days ago; cross_source_batch returns 4-item list with duplicate pair |
| `TARIQ__career_radar/radar/stages/fetch.py` | Wired to call `run_dedup_pass()` after filtering | VERIFIED | Lines 35-36: imports added; lines 461-468: dedup pass integrated with try/except fallback; logs "[DEDUP] X raw → Y unique opportunities" |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `dedup_engine.fuzzy_match_opportunities()` | `rapidfuzz.fuzz.partial_token_sort_ratio` | Import + direct call | WIRED | Line 16: `from rapidfuzz import fuzz`; line 150: `fuzz.partial_token_sort_ratio()` used with `/100.0` normalization |
| `dedup_engine.is_fresh_repost()` | `datetime.datetime.fromisoformat()` | Stdlib datetime | WIRED | Line 177-178: parses ISO strings with `fromisoformat()`; line 179: calculates gap with `.days` |
| `dedup_engine.run_dedup_pass()` | `stages.dedup.run_dedup_pass()` | Import delegation | WIRED | Line 201: imports implementation; line 202: delegates with correct signature |
| `stages.dedup.run_dedup_pass()` | `dedup_engine.DedupeEngine`, `fuzzy_match_opportunities()`, `is_fresh_repost()` | Direct imports | WIRED | Lines 17-22: all three imported; used in orchestrator logic (lines 91-129) |
| `stages.fetch.run_fetch()` | `stages.dedup.run_dedup_pass()` | Import + call in pipeline | WIRED | Lines 35-36: imports added; lines 463-468: called after filtering; fallback exception handling present |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DEDUP-01 | 04-01, 04-02, 04-03 | Opportunities are normalized into dedup key | SATISFIED | `compute_dedup_key()` implemented; handles title/company/location normalization; deterministic output |
| DEDUP-02 | 04-01, 04-02, 04-03 | Exact + fuzzy matching detects duplicates within run | SATISFIED | `fuzzy_match_opportunities()` uses rapidfuzz with 0.88 threshold; passes 3 tests; cross-source detection verified |
| DEDUP-03 | 04-01, 04-02, 04-03 | Rerun no-dup guarantee + freshness rule | SATISFIED | `is_fresh_repost()` implemented; 30-day threshold; seen-store prevents reruns; integration tested |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Status |
|------|------|---------|----------|--------|
| `dedup_engine.py` | 277, 103 | `datetime.datetime.utcnow()` deprecated | INFO | Standard deprecation warning; no functional issue; not blocker |
| (none) | — | Stub/TODO/placeholder | NONE | No blocking stubs found |

No blocking anti-patterns. Deprecation warnings are Python 3.13 future notices only.

### Test Results

**Full suite:** All 9 dedup tests PASSED (100% pass rate)

```
test_sqlite_roundtrip PASSED
test_normalization_deterministic PASSED
test_persistence_across_restarts PASSED
test_fuzzy_match_title_variants PASSED
test_fuzzy_match_no_false_positive PASSED
test_fuzzy_match_same_company_exact_location PASSED
test_is_fresh_repost_old_role_surfaces PASSED
test_is_fresh_repost_recent_stays_hidden PASSED
test_run_dedup_pass_removes_within_run_dups PASSED
```

**Phase 1-3 tests:** All 20 source tests PASSED (no regressions)

### Human Verification Required

None. All observable behaviors verified programmatically:
- Deterministic key generation: confirmed via output check
- Fuzzy matching thresholds: confirmed via score calculations
- Seen-store persistence: confirmed via two-run test
- Freshness rule: confirmed via day-gap calculations
- Integration with fetch pipeline: confirmed via code inspection + log statements

## Summary

Phase 04 goal is **FULLY ACHIEVED**. All four must-haves are satisfied:

1. **Normalization:** `compute_dedup_key()` is deterministic and handles all variant forms (company suffixes, location "remote" collapse, Unicode normalization)
2. **Fuzzy matching:** `fuzzy_match_opportunities()` uses rapidfuzz `partial_token_sort_ratio` with 0.88 threshold; detects cross-source duplicates; avoids false positives
3. **Rerun no-dup:** `DedupeEngine` persists to SQLite; second runs return 0 duplicates (unless >30 days old); integration confirmed in `fetch.py`
4. **Freshness rule:** `is_fresh_repost()` returns True for gaps >= 30 days, False otherwise; allows genuine reposts to surface

All 9 tests GREEN. No Phase 1-3 regressions. Ready for Phase 5 (Scoring Engine).

---

_Verified: 2026-06-15T18:30:00Z_  
_Verifier: Claude (gsd-verifier)_
