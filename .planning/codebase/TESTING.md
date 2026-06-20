# Testing Patterns

**Analysis Date:** 2026-06-14

---

## Test Framework

**Runner:** pytest

**Config:** `D:/NIZAM/pytest.ini`

```ini
[pytest]
testpaths =
    tools
    scripts
    NIZAM__system/config/fixtures
    NIZAM__system/governor/tests
    NIZAM__system/companion/tests
    NIZAM__system/relay/tests
    HIFZ__github_version_control/scripts
    MARSAD__flight_radar/tests
python_files = test_*.py *_test.py
norecursedirs =
    .git
    .venv
    hermes-venv
    install-audit
    graphify-out
    MAKHZAN__archive
    Research_docs
addopts = --strict-config --strict-markers
```

**Assertion Library:** Python stdlib `unittest` (via `unittest.TestCase`) — no third-party assertion library.

**Run Commands (from `D:/NIZAM/` repo root):**

```bash
# Run all tests (uses pytest.ini testpaths)
.venv\Scripts\python.exe -m pytest

# Run a specific test module via unittest directly
.venv\Scripts\python.exe -m unittest NIZAM__system.governor.tests.test_classifier_fixture

# Run a specific test module with verbose output
.venv\Scripts\python.exe -m unittest NIZAM__system.governor.tests.test_classifier_fixture -v

# Run relay phase-1 boot loop tests
.venv\Scripts\python.exe -m unittest NIZAM__system.relay.tests.test_phase1_boot_loop -v

# Run pre-commit hook tests
.venv\Scripts\python.exe -m unittest NIZAM__system.governor.tests.test_pre_commit_hook

# Run intent priority fixture (standalone script, not unittest)
.venv\Scripts\python.exe NIZAM__system/config/fixtures/intent_priority_test.py
```

---

## Test File Organization

**Location:** Co-located in `tests/` subdirectories under each subsystem package. NOT alongside source files.

**Directory pattern:**
```
NIZAM__system/
  governor/
    tests/
      __init__.py
      test_classifier_fixture.py
      test_pre_commit_hook.py
      test_agent_message_schema.py
      test_policy_invariants.py
      test_strategy_sth.py
      test_connector_health.py
  relay/
    tests/
      __init__.py
      test_phase1_boot_loop.py
      test_persona_runtime.py
      test_poller.py
      test_runtime_events.py
  companion/
    tests/
      __init__.py
      fixtures/
        (test fixtures: CSVs, JSON examples)
      test_companion.py
      test_production_modules.py
      test_pulsation.py
      test_skills_registry.py
    council/
      tests/
        __init__.py
        test_council.py
  modes/
    khaldun/
      tests/
        test_khaldun_mode.py
        test_khaldun_telegram.py
  connectors/
    tests/
      __init__.py
      test_google_adapter.py
config/
  fixtures/
    intent_priority_test.py           # standalone script (not unittest class)
```

**Naming:** `test_<module_or_feature_name>.py`

Every `tests/` directory contains an `__init__.py` (even if empty) to enable dotted-path unittest invocation.

---

## Test Structure

### unittest.TestCase pattern (standard)

All test files in `governor/tests/`, `relay/tests/`, `companion/tests/` use `unittest.TestCase`:

```python
"""Module docstring explaining what is tested and how to run.

Run with:
    .venv\\Scripts\\python.exe -m unittest NIZAM__system.governor.tests.test_classifier_fixture

(from `D:\\NIZAM\\nizamcore`)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from NIZAM__system.governor import classifier   # noqa: E402


class ClassifierFixtureTests(unittest.TestCase):
    def test_each_fixture_matches_expected_class(self) -> None:
        for path, expected in FIXTURE:
            with self.subTest(path=path):
                got = classifier.classify(path)
                self.assertEqual(got, expected, f"{path}: got {got}, want {expected}")


if __name__ == "__main__":
    unittest.main()
```

Key structural rules:
- Module-level docstring includes run command with explicit virtualenv path.
- `from __future__ import annotations` is first import.
- `_REPO = Path(__file__).resolve().parents[N]` + `sys.path.insert(0, str(_REPO))` before any local imports.
- `# noqa: E402` on local imports that follow the sys.path injection.
- `if __name__ == "__main__": unittest.main()` at the end of every file.

### `setUpClass` for expensive shared state

Used when loading schemas or config once per test class:

```python
class AgentMessageSchemaE11(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _load_schema()

    def test_good_envelope_validates(self) -> None:
        errs = _validate(_good_envelope(), self.schema)
        self.assertEqual([], errs)
```

### `self.subTest` for parameterized cases

Used for fixture-table-driven tests:

```python
def test_each_fixture_matches_expected_class(self) -> None:
    for path, expected in FIXTURE:
        with self.subTest(path=path):
            got = classifier.classify(path)
            self.assertEqual(got, expected, f"{path}: got {got}, want {expected}")
```

### `self.assertRaises` for exception testing

```python
def test_missing_secret_header_rejected(self) -> None:
    with self.assertRaises(auth.AuthError):
        auth.verify_secret_token(None)
```

### Named test classes map to spec items (B-refs, E-refs)

Test classes are named after the spec/blueprint item they validate:

```python
class B41_AuthSecretToken(unittest.TestCase):
    """B4.1 secret-token verification (CVE-2026-32980)."""

class AgentMessageSchemaE11(unittest.TestCase):
    """E1.1 — schemas/agent_message.schema.json shape tests."""

class MerkleRFC6962E43(unittest.TestCase):
    """Tests for strategy_sth.py (E4.3) — RFC 6962 + Ed25519 STH."""
```

### pytest-style function tests (test_policy_invariants.py)

`NIZAM__system/governor/tests/test_policy_invariants.py` uses bare `def test_*()` functions (no class), compatible with both pytest and plain execution:

```python
def test_dead_letter_contract_is_consistent() -> None:
    temple = _json(REPO / "NIZAM_TEMPLE.json")
    connectors = _json(POLICIES / "CONNECTORS.json")
    assert dead["privacy"] == "strict_local"
    assert connectors["retry_policy"]["max_attempts"] == 3
```

---

## Mocking

**Framework:** No mock library (no `unittest.mock`). Tests use:

1. **Real implementations with temporary directories** (`tempfile.TemporaryDirectory`, `tempfile.mkdtemp`)
2. **In-process state reset** via environment variables
3. **Fake/stub classes** defined inline

### Environment variable injection pattern

```python
# Set before importing modules that read env vars
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-secret-XYZ")
os.environ.setdefault("NIZAM_TELEGRAM_ALLOWED_IDS", "111222333")
```

Always use `setdefault` (not `os.environ[key] = value`) to avoid clobbering real values if tests are run in a live environment.

### Fake adapter / stub class pattern

```python
class FakeAdapter:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def read(self, capability: str) -> list[dict]:
        return list(self.rows)

    def write(self, capability: str, payload: dict) -> dict:
        self.rows.append(dict(payload))
        return dict(payload)
```

### Temporary file / ledger roots

Tests that write to ledgers pass a temporary `root` path to avoid contaminating live ledger files:

```python
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    row = ledger_writer.append("EVENT_LEDGER", {"note": "test"}, root=root)
    self.assertEqual(row["actor"], "Ammar")
```

---

## Fixtures and Test Data

### Inline FIXTURE tables (classifier / router tests)

Module-level constants define test cases directly in the test file:

```python
FIXTURE = [
    # (rel_path, expected_classification)
    ("TAFRIGH__brain_dumper/raw/2026-05-28.md",    "strict_local"),
    ("NIZAM__system/ledgers/EVENT_LEDGER.jsonl",   "review_before_commit"),
    ("HAJR__quarantine/maximum/record.md",          "strict_local_maximum"),
    ("README.md",                                   "private_github"),
]
```

```python
CLEAN_BATCH = [
    "README.md",
    "NIZAM__system/policies/PRIVACY_CLASSIFICATION.json",
    "NIZAM__system/schemas/persona.schema.json",
]

LEAKY_BATCH = CLEAN_BATCH + [
    "SHURA__brainstormer/sessions/2026-05-28.md",
    "HAJR__quarantine/maximum/record.md",
]
```

### JSON fixture files

Schema fixtures live at `NIZAM__system/schemas/fixtures/<name>.fixture.json`. Example: `NIZAM__system/schemas/fixtures/conversational_session.fixture.json`. These are valid representative instances of their schema.

Companion test fixtures live at `NIZAM__system/companion/tests/fixtures/`. Currently: `approved_reminders.json`, `whoop-sample.csv`.

### Inline `_good_envelope(**overrides)` factory pattern

For envelope/schema tests, a factory function builds a valid base object and allows field overrides:

```python
def _good_envelope(**overrides) -> dict:
    base = {
        "schema_version": "1.0",
        "trace_id": str(uuid.uuid4()),
        "delegation_depth": 0,
        "kind": "request",
        "privacy_class": "strict_local",
        # ... all required fields ...
    }
    base.update(overrides)
    return base

def test_delegation_depth_max_8_enforced(self) -> None:
    bad = _good_envelope(delegation_depth=9)
    errs = _validate(bad, self.schema)
    self.assertTrue(any("delegation_depth" in e for e in errs), errs)
```

### Telegram update factory

For relay / boot-loop tests, a factory builds fake Telegram update dicts:

```python
def _telegram_update(text: str, update_id: int = 1, user_id: int = 111222333) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "from": {"id": user_id, "is_bot": False, "first_name": "Op"},
            "chat": {"id": user_id, "type": "private"},
            "date": 1716926400,
            "text": text,
        },
    }
```

---

## Fixture Scripts (Non-unittest)

`NIZAM__system/config/fixtures/intent_priority_test.py` is a standalone script (not a `unittest.TestCase`) that validates the `routing_priority` YAML structure offline without an LLM:

```python
CASES = [
    ("PANIC: overload red, I can't breathe.", "CRISIS"),
    ("/tariq-vision 15", "COMMAND"),
    ("Plan the next quarter.", "TRIGGER"),
    ("zxcv qwerty asdf", "AMBIGUOUS"),
]

def main() -> int:
    priority = _load_priority()
    ok = 0
    for text, expected in CASES:
        got = detect_kind(text, priority)
        mark = "OK " if got == expected else "FAIL"
        print(f"  [{mark}] expected={expected:<13} got={got:<13} input={text!r}")
        if got == expected:
            ok += 1
    print(f"\nintent priority cascade: {ok}/{len(CASES)} passed")
    return 0 if ok == len(CASES) else 1

if __name__ == "__main__":
    sys.exit(main())
```

This is included in `pytest.ini` testpaths so pytest discovers it, but it self-reports via `sys.exit` return code.

---

## Inline Schema Validation (No jsonschema Library)

`NIZAM__system/governor/tests/test_agent_message_schema.py` implements a minimal JSON Schema Draft-7 validator in pure stdlib to avoid the `jsonschema` dependency:

```python
def _validate(instance: dict, schema: dict) -> list[str]:
    """Minimal JSON-schema-draft-7 validator covering the constructs we use."""
    errors: list[str] = []
    # Checks: required fields, type checking, enum validation, const, min/max, maxLength
    # Returns list of error strings; empty list = valid
    ...
    return errors
```

When adding new schema tests, extend this pattern rather than adding `jsonschema` as a dependency.

---

## Test Types

### Unit tests (majority)

- **Scope:** Single module function, single policy invariant, single schema field.
- **Location:** `NIZAM__system/governor/tests/`, `NIZAM__system/modes/khaldun/tests/`
- **Examples:** `test_classifier_fixture.py`, `test_strategy_sth.py`, `test_khaldun_mode.py`

### Integration tests

- **Scope:** Multi-module flow (relay → auth → coordinator → ledger_writer).
- **Location:** `NIZAM__system/relay/tests/`
- **Examples:** `test_phase1_boot_loop.py` (covers B4.1–B4.10 spec items end-to-end)

### Policy invariant tests

- **Scope:** Cross-file consistency: NIZAM_TEMPLE.json ↔ CONNECTORS.json ↔ classifier.
- **Location:** `NIZAM__system/governor/tests/test_policy_invariants.py`
- **Pattern:** Load real JSON files, assert contractual relationships. Also runs `git ls-files` to verify secret files are not tracked.

### Shape tests

- **Scope:** YAML config structure validation (offline, no LLM).
- **Location:** `NIZAM__system/config/fixtures/intent_priority_test.py`
- **Pattern:** Load config, simulate routing logic against a fixture table, assert kind resolution.

### E2E / boot loop tests

- **Scope:** Full webhook → auth → classify → route → ledger write → response path.
- **Location:** `NIZAM__system/relay/tests/test_phase1_boot_loop.py`
- **Pattern:** Uses real modules with env-var-injected secrets and temp ledger roots.

---

## What to Test vs. What Not to Test

**Test:**
- All privacy classification decisions (every tier and edge case).
- All egress matrix decisions (blocked and allowed targets).
- Hash-chain integrity of ledger writes.
- Schema shape: required fields, enum values, numeric bounds.
- Routing priority cascade: CRISIS wins, HIMAYAH wins, COMMAND wins.
- Pre-commit blocking: mixed batches with strict_local and maximum-private paths.
- Policy invariants: cross-file contractual consistency.

**Do NOT test (or test only with stubs):**
- Live LLM API calls.
- Live Telegram API calls.
- Live Google Drive or Notion API calls.
- Ledger STRATEGY_LEDGER STH publication (best-effort; test the Merkle math, not the publish).

---

## Coverage

**Requirements:** No enforced coverage minimum (no `--cov` in `addopts`).

**Coverage can be run with:**
```bash
.venv\Scripts\python.exe -m pytest --cov=NIZAM__system --cov-report=term-missing
```

---

## Adding New Tests

1. Create `tests/` directory under the new subsystem package if it does not exist.
2. Add `tests/__init__.py` (empty).
3. Name the file `test_<feature>.py`.
4. Add the directory to `pytest.ini` `testpaths` if it is a new top-level location.
5. Follow the `sys.path` injection pattern and include the run command in the module docstring.
6. Name the test class after the spec/blueprint reference (e.g. `class TariqCareerRadarTests(unittest.TestCase)`).

---

*Testing analysis: 2026-06-14*
