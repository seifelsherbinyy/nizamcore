---
phase: 03-tier-2-rss-manual-sourcing
plan: "01"
subsystem: TARIQ__career_radar
tags: [tdd, wave-0, rss, manual-import, role-filter, fixtures, red-tests]
dependency_graph:
  requires: [02-tier-1-ats-sourcing]
  provides: [03-01-wave0-tdd-scaffold]
  affects: [03-02-rss-connectors, 03-03-manual-import, 03-04-role-filter]
tech_stack:
  added: []
  patterns:
    - TDD Wave-0 RED scaffold (collectible-but-failing via _require_module)
    - Static fixture files for offline HTTP mocking (RSS XML, JSON, JSONL)
    - conftest.py additive extension pattern (Phase-N block appended, prior fixtures untouched)
    - fake_rss_bytes_get factory (mirrors fake_requests_get, sets resp.content bytes)
key_files:
  created:
    - TARIQ__career_radar/tests/fixtures/remotive_sample_rss.xml
    - TARIQ__career_radar/tests/fixtures/weworkremotely_sample_rss.xml
    - TARIQ__career_radar/tests/fixtures/remoteok_sample_response.json
    - TARIQ__career_radar/tests/fixtures/manual_import_sample.jsonl
    - TARIQ__career_radar/tests/fixtures/malformed_rss.xml
  modified:
    - TARIQ__career_radar/conftest.py
    - TARIQ__career_radar/tests/test_sources.py
decisions:
  - "fake_rss_bytes_get fixture sets resp.content (bytes) rather than resp.json() to match how stdlib xml.etree.ElementTree parses raw HTTP response content"
  - "synthetic_profile_seed uses group-dict role_keywords (not flat list like Phase-1 sample_profile) to match the actual data/profile_cache.json structure SRC-06 will read"
  - "test_remoteok_mocked uses existing fake_requests_get (JSON-based) rather than fake_rss_bytes_get because RemoteOK uses a JSON API endpoint, not RSS XML bytes"
  - "malformed_rss.xml leaves </rss> absent and uses an unclosed <title> tag; ET.parse raises ParseError on this file as required by the graceful-error test"
metrics:
  duration: "162s"
  completed_date: "2026-06-15"
  tasks_completed: 3
  files_changed: 7
requirements_covered: [SRC-02, SRC-03, SRC-06]
---

# Phase 03 Plan 01: Wave 0 TDD Scaffold (RSS + Manual Import + Role Filter) Summary

**One-liner:** TDD Wave-0 RED scaffold with 5 offline fixtures, 6 conftest loaders, and 9 collectible-but-failing tests defining the acceptance contracts for RSS sourcing (SRC-02), manual JSONL import (SRC-03), and role-keyword filtering (SRC-06).

---

## What Was Built

Three additive changes to the TARIQ Career Radar test suite establish the RED baseline for Phase 3 implementation:

**1. Five static fixture files** (`TARIQ__career_radar/tests/fixtures/`):
- `remotive_sample_rss.xml` — valid RSS 2.0 with 1 `<item>` (title: "Senior AI Operations Manager", company: "Acme Corp", pubDate: "Tue, 14 Jun 2026 10:00:00 GMT")
- `weworkremotely_sample_rss.xml` — valid RSS 2.0 with 1 `<item>` and NO `<company>` element (tests fallback to "Unknown")
- `remoteok_sample_response.json` — JSON array with legal-notice stub + 1 job (salary_min: 80000, salary_max: 120000, epoch: Unix timestamp)
- `manual_import_sample.jsonl` — 2 JSONL records: AI Evaluator (hourly salary 30–60) and Data Annotator (no salary)
- `malformed_rss.xml` — intentionally unclosed `<title>` tag and no closing `</rss>` → triggers `ET.ParseError` on parse

**2. Six Phase-3 conftest.py fixtures** (appended after existing Phase-2 block):
- `mock_remotive_rss(fixtures_dir)` → raw bytes of remotive_sample_rss.xml
- `mock_weworkremotely_rss(fixtures_dir)` → raw bytes of weworkremotely_sample_rss.xml
- `mock_remoteok_response(fixtures_dir)` → parsed JSON list from remoteok_sample_response.json
- `manual_import_fixture(tmp_path)` → creates temporary manual_imports.jsonl with 2 records
- `fake_rss_bytes_get()` → factory returning fakes that set `resp.content = bytes` (mirrors fake_requests_get)
- `synthetic_profile_seed()` → group-dict `role_keywords` (AI_OPERATIONS, DATA_SCIENCE, COORDINATION, LLM_EVALUATION)

**3. Nine failing Phase-3 tests** appended to `test_sources.py`:

| Test | Req | Targets | Status |
|------|-----|---------|--------|
| `test_remotive_rss_mocked` | SRC-02 | `radar.sources.rss_source.RemotiveSource` | RED |
| `test_weworkremotely_rss_mocked` | SRC-02 | `radar.sources.rss_source.WeWorkRemotelySource` | RED |
| `test_remoteok_mocked` | SRC-02 | `radar.sources.rss_source.RemoteOKSource` | RED |
| `test_rss_malformed_xml_graceful` | SRC-02 | `radar.sources.rss_source.RemotiveSource` | RED |
| `test_manual_import_valid_jsonl` | SRC-03 | `radar.sources.manual_import_source.ManualImportSource` | RED |
| `test_manual_import_file_not_found` | SRC-03 | `radar.sources.manual_import_source.ManualImportSource` | RED |
| `test_manual_import_malformed_json` | SRC-03 | `radar.sources.manual_import_source.ManualImportSource` | RED |
| `test_role_filter_matches` | SRC-06 | `radar.stages.filter.run_filter` | RED |
| `test_role_filter_rejects` | SRC-06 | `radar.stages.filter.run_filter` | RED |

---

## Test Results

```
9 failed (RED), 24 passed (GREEN), 0 errors
```

- Phase-1 tests (13): GREEN
- Phase-2 tests (11): GREEN
- Phase-3 tests (9): RED (as required — Wave 0 scaffold)

---

## Decisions Made

1. **fake_rss_bytes_get sets `resp.content` (bytes)** — RSS sources use `ET.fromstring(resp.content)` not `resp.json()`, so the bytes-based mock factory is the correct contract to enforce.

2. **synthetic_profile_seed uses group-dict role_keywords** — The real `data/profile_cache.json` stores `role_keywords` as `{group_name: [keywords]}`, not a flat list like the Phase-1 `sample_profile` fixture. Tests for `run_filter` require the group-dict form.

3. **test_remoteok_mocked uses `fake_requests_get` (existing JSON factory)** — RemoteOK uses a JSON API, not RSS XML bytes. Using the existing `fake_requests_get(200, json_data)` factory (returns `resp.json()`) is correct; RSS tests use `fake_rss_bytes_get`.

4. **malformed_rss.xml uses unclosed `<title>` inside `<item>`** — This causes `ET.ParseError` during both `ET.parse()` and `ET.fromstring()`, satisfying the graceful-error contract.

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Self-Check

Verifying artifacts exist and commits are present:

- `TARIQ__career_radar/tests/fixtures/remotive_sample_rss.xml` — FOUND
- `TARIQ__career_radar/tests/fixtures/weworkremotely_sample_rss.xml` — FOUND
- `TARIQ__career_radar/tests/fixtures/remoteok_sample_response.json` — FOUND
- `TARIQ__career_radar/tests/fixtures/manual_import_sample.jsonl` — FOUND
- `TARIQ__career_radar/tests/fixtures/malformed_rss.xml` — FOUND
- `TARIQ__career_radar/conftest.py` (6 new fixtures) — FOUND
- `TARIQ__career_radar/tests/test_sources.py` (9 new tests) — FOUND

Commits:
- `b35f4f9` — test(03-01): add 5 Phase-3 fixture files
- `bdbb418` — test(03-01): augment conftest.py with 6 Phase-3 fixture loaders
- `9910f15` — test(03-01): append 9 failing Phase-3 TDD tests

## Self-Check: PASSED
