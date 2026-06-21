# Phase 18: Adaptation & Format Evolution — Research

**Researched:** 2026-06-21  
**Domain:** Adaptive Messaging & Format Rotation  
**Confidence:** HIGH  
**Phase:** 18 of 20

---

## Summary

Phase 18 implements the adaptive feedback loop that closes the message delivery lifecycle. Building on Phase 17's delivery ledger (immutable JSONL with message_id, responses, engagement window events), this phase adds format rotation logic: if a persona's weekly response rate drops below 80%, the system automatically cycles through 5 format variations to improve engagement.

**Key finding:** Phase 17 already provides all the raw data needed (DELIVERY_LEDGER.jsonl with delivery and response events). Phase 18 adds three new capabilities:
1. **WeeklyResponseRateCalculator** — Queries ledger for past 7 days, calculates (responses/deliveries) per persona
2. **FormatRotationManager** — Tracks current format per persona, cycles to next format if <80%, prevents consecutive repeats
3. **AdaptationLogger** — Records format changes with rationale and engagement metrics for audit

The architecture is clean: during message generation (Phase 16 integration point), before calling the generator, check if adaptation is needed. If response_rate < 80%, look up next format, inject format hint into the system prompt, log the change.

**Primary recommendation:** Implement adaptation as a pipeline middleware (call WeeklyResponseRateCalculator before generate_message, inject format_hint into IntentProcessor). Store format state and rotation history in a lightweight AdaptationState ledger (JSONL). Test format cycling with synthetic low-engagement scenarios (mock ledger with 3/14 responses).

---

## User Constraints

*No CONTEXT.md provided for Phase 18. All research-driven recommendations.*

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ADAPT-01 | Track response rate per persona per week: (responses_in_1hour / messages_sent) for past 7 days | WeeklyResponseRateCalculator queries DeliveryLedger; response events vs. delivery events per persona |
| ADAPT-02 | If response rate <80%, automatically select next format from rotation [standard, short, emoji, direct_question, story] | FormatRotationManager with state machine; formats stored in AdaptationState ledger |
| ADAPT-03 | Format change logged with rationale (e.g., "TARIQ response rate 65% < 80%, switching from 'standard' to 'short'") | AdaptationLogger writes entry to ADAPTATION_LEDGER.jsonl with timestamp, persona, old_format, new_format, response_rate, rationale |
| ADAPT-04 | System never repeats same format twice consecutively; validates across 10+ consecutive messages | FormatRotationManager enforces no_repeat constraint; AdaptationState ledger tracks current+previous format per persona |

---

## Standard Stack

### Core Libraries
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Core language | Existing NIZAM stack; Phase 14–17 all Python |
| pathlib | stdlib | File path operations | Consistent with HIKMAH__knowledge_index patterns |
| json | stdlib | Ledger serialization | JSONL format established in Phase 14-17 |
| datetime | stdlib | Timestamp ISO 8601 | Consistent ledger timestamps (Phase 14-17 precedent) |
| dataclasses | stdlib | Config/state objects | Used in Phase 15 (RefreshConfig), Phase 17 (DeliveryResult) |

### Supporting Libraries (Existing in NIZAM)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HIKMAH__knowledge_index.delivery | (local) | Phase 17 ledger queries | Query delivery/response events for rate calculation |
| HIKMAH__knowledge_index.message_generation | (local) | Phase 16 tone system | Pass format_hint to generator via IntentProcessor context |
| NIZAM__system.relay.poller | (local) | Telegram relay | Already available; Phase 18 doesn't need it (reads ledger, not live) |

### No Additional Dependencies Needed
- No external HTTP clients (reads local JSONL ledger)
- No ML libraries (deterministic format rotation, no optimization)
- No databases (JSONL is sufficient for adaptation state)

**Installation:** None required. All dependencies are existing NIZAM infrastructure.

---

## Architecture Patterns

### Phase 18 Integration Point

```
Phase 16: Message Generation
     ↓
[NEW] Adaptation Check (Phase 18)
     ├─ Query: Weekly response rate for persona
     ├─ Decide: Is rate < 80%?
     ├─ If yes: Look up next format from rotation
     └─ Inject: format_hint into IntentProcessor context
     ↓
Message Generation with format applied
     ↓
Phase 17: Delivery
```

**Key insight:** Phase 18 is NOT a separate stage in message delivery. It's a **decision layer** inserted before Phase 16 generation. The system asks: "Should this persona's message use a different format?" before Claude receives the intent.

### Recommended Project Structure

```
HIKMAH__knowledge_index/
├── adaptation/                          # Phase 18 (NEW)
│   ├── __init__.py                      # Public API (WeeklyResponseRateCalculator, FormatRotationManager, AdaptationLogger)
│   ├── response_rate_calculator.py      # Weekly rate calculation from DeliveryLedger
│   ├── format_rotation_manager.py       # Format state machine + no-repeat logic
│   ├── adaptation_logger.py             # JSONL audit trail for format changes
│   ├── adaptation_state.py              # AdaptationState dataclass + file operations
│   ├── ADAPTATION_LEDGER.jsonl          # (created on first write) Format change audit trail
│   ├── ADAPTATION_STATE.jsonl           # (created on first write) Current format per persona
│   └── tests/                           # Phase 18 test suite (30-40 tests)
│       ├── conftest.py                  # Fixtures (mock ledgers, sample delivery events)
│       ├── test_response_rate_calculator.py
│       ├── test_format_rotation_manager.py
│       ├── test_adaptation_logger.py
│       └── test_integration.py          # End-to-end adaptation flow

ADAPTATION_LEDGER.jsonl                 # (at root; persisted)
```

### Pattern 1: Format Rotation State Machine

**What:** Track current format per persona, advance to next on engagement threshold breach.

**When to use:** Adaptation decisions before message generation. Query at the start of each message generation call (Phase 16 integration point).

**Design:**
```python
# ADAPTATION_STATE.jsonl structure (one line per persona's current state)
{
  "ts": "2026-06-21T09:30:00Z",
  "persona": "AMMAR",
  "current_format": "standard",
  "previous_format": "story",
  "rotation_index": 0,
  "last_rotation_at": "2026-06-21T09:30:00Z",
  "trigger_response_rate": 0.65,
  "adaptation_id": "ADAPT-AMMAR-20260621-001"
}

# Rotation cycle: [standard → short → emoji → direct_question → story → standard → ...]
FORMATS = ["standard", "short", "emoji", "direct_question", "story"]
```

**Why this pattern:**
- **Immutable audit trail:** Format changes logged with rationale before applied (fail-safe)
- **No consecutive repeats enforced:** previous_format prevents rotate() from returning same format
- **Queryable history:** Can answer "When did AMMAR switch formats? Why?" by reading ADAPTATION_LEDGER.jsonl
- **Resettable:** If engagement recovers (rate >= 80%), can reset to "standard" and clear previous_format

**Example:**
```python
from HIKMAH__knowledge_index.adaptation import FormatRotationManager

manager = FormatRotationManager()
current = manager.get_current_format("AMMAR")  # Returns "standard"

# If response_rate < 80%:
next_format = manager.rotate_format("AMMAR")   # Returns "short" (next in cycle, not "standard")
# Ledger updated: previous_format="standard", current_format="short"
```

### Pattern 2: Weekly Response Rate Calculation

**What:** Query DeliveryLedger for past 7 days, count delivery + response events per persona.

**When to use:** Before deciding format adaptation. Typically called at message generation time.

**Formula:**
```
response_rate = (responses_received_in_1h_window) / (messages_sent_past_7_days)
```

**Example:**
```python
from HIKMAH__knowledge_index.adaptation import WeeklyResponseRateCalculator

calc = WeeklyResponseRateCalculator(ledger_path)
rate, numerator, denominator = calc.calculate("AMMAR", days=7)
# rate=0.65, numerator=13 (responses), denominator=20 (messages sent)

if rate < 0.80:
    print(f"AMMAR engagement low ({rate:.0%}). Consider format rotation.")
```

**Key design:**
- **Numerator:** Count of "response" events in DELIVERY_LEDGER.jsonl, past 7 days, persona="AMMAR"
- **Denominator:** Count of "delivery" events (status="success"), past 7 days, persona="AMMAR"
- **Missing responses:** If a delivery has NO corresponding "response" or "engagement_window_closed" event, count it as 0 (no response)
- **Edge case handling:** If denominator=0 (no sends), return rate=1.0 (skip adaptation for new personas)

### Pattern 3: Adaptation Logging with Rationale

**What:** Every format change recorded with metadata for audit and analysis.

**When to use:** Inside format rotation decision, after selecting next format.

**Ledger format (ADAPTATION_LEDGER.jsonl):**
```json
{
  "ts": "2026-06-21T09:30:00Z",
  "adaptation_id": "ADAPT-AMMAR-20260621-001",
  "persona": "AMMAR",
  "event_type": "format_rotation",
  "old_format": "standard",
  "new_format": "short",
  "trigger": "engagement_threshold_breach",
  "response_rate": 0.65,
  "response_rate_threshold": 0.80,
  "calculation_window_days": 7,
  "denominator": 20,
  "numerator": 13,
  "rationale": "AMMAR response rate 65% < 80%, switching from 'standard' to 'short' format",
  "adaptation_ledger_hash": "a1b2c3d4e5f6a7b8"
}
```

**Why this pattern:**
- **Traceable decisions:** Operator can see "Why did we switch AMMAR from standard to short on Jun 21?"
- **Performance analysis:** Can correlate format changes with future response rate improvements
- **Safety:** If format rotation causes problems, can revert and disable via rationale review

### Anti-Patterns to Avoid

- **Silent format changes:** Never rotate format without logging. Always write ADAPTATION_LEDGER entry BEFORE applying format.
- **Consecutive repeat formats:** Don't allow "standard → standard". Always check previous_format.
- **Real-time response rate:** Don't recalculate on every message (expensive). Cache calculation result for up to 1 hour, then refresh.
- **Hardcoded format rotation:** Don't embed format logic in generator.py. Keep rotation logic separate (FormatRotationManager), injected as context hint.
- **Lost format state:** Don't keep rotation state in memory. Persist ADAPTATION_STATE.jsonl; reload on each message generation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tracking format rotation state | Custom in-memory dict, file I/O on each access | ADAPTATION_STATE.jsonl (JSONL pattern from Phase 14) + FormatRotationManager class | Immutable ledger prevents race conditions; mirrors HIKMAH__knowledge_index patterns |
| Calculating weekly response rates | Manual loop through all deliveries, manual count | WeeklyResponseRateCalculator.calculate() with time filtering + event type check | Clean API, testable, handles edge cases (denominator=0, missing responses) |
| Logging format changes | print() statements | AdaptationLogger.log_rotation() writing to ADAPTATION_LEDGER.jsonl | Immutable audit trail; queryable; timestamp integrity |
| Preventing consecutive format repeats | if new_format == old_format: try_again() loop | FormatRotationManager.rotate_format() with previous_format check + advance() | Simple state machine; no loops; no race conditions |
| Format hint injection into generation | Modify generator.py, add format parameter | Pass format_hint via IntentProcessor context (Phase 16 integration) | No changes to Message Generation module; respects phase boundaries |

**Key insight:** Adaptation is not complex business logic — it's state machine + ledger queries. Build exactly what the requirements specify, no more.

---

## Common Pitfalls

### Pitfall 1: Race Condition Between Format Rotation and Response Rate Calculation

**What goes wrong:** Two concurrent message generation calls for same persona both see rate < 80%, both try to rotate format, both write to ADAPTATION_STATE.jsonl, one write is lost.

**Why it happens:** ADAPTATION_STATE.jsonl is a file, not a database with locks. If two processes read the state, make independent decisions, and write back, last-write-wins and one rotation is lost.

**How to avoid:**
- Phase 18 is single-threaded per persona (scheduled delivery is synchronous: 09:00 send AMMAR, then 09:05 send HIKMAH)
- If multi-threaded scenario arises (parallel generation for different personas), use file-level locking (fcntl on Unix, msvcrt on Windows)
- For v1.1, document: "Single persona at a time. Multi-threading support deferred to v1.2."

**Warning signs:** If same persona's format rotates twice in one hour (check ADAPTATION_LEDGER.jsonl), investigate for concurrent write.

### Pitfall 2: Response Rate Threshold Oscillation

**What goes wrong:** Persona at 79% engagement switches format. New format slightly improves rate to 81%, then next week drops to 79% again. Format oscillates every week (standard ↔ short).

**Why it happens:** 80% is a razor-thin boundary. Small random variance in user engagement causes crossing back and forth.

**How to avoid:**
- Add **hysteresis buffer:** Only rotate if rate < 75% (not 80%), and only rotate back if rate > 85% (not 80%)
- Alternative: Require ≥ 2 days of low engagement before rotating (moving window, not immediate threshold)
- Limit: "Don't rotate more than once per week for same persona" (check last_rotation_at in ADAPTATION_STATE.jsonl, skip if within 7 days)

**Warning signs:** ADAPTATION_LEDGER.jsonl shows same persona with format_rotation events 2+ times per week.

### Pitfall 3: Denominator = 0 (New Persona, No Deliveries Yet)

**What goes wrong:** Phase 18 launches, AMMAR has no delivery history (denominator = 0). Division by zero in rate calculation.

**Why it happens:** Calculation designed without edge case: new personas have no history.

**How to avoid:**
- Explicit check in WeeklyResponseRateCalculator: if denominator = 0, return rate = 1.0 (assume healthy engagement, skip adaptation)
- Rationale: New personas should not start with format rotation (not enough data)
- Test: Unit test for denominator = 0 case

**Warning signs:** Crash log shows ZeroDivisionError in response_rate_calculator.py.

### Pitfall 4: Format Hint Ignored by Message Generator

**What goes wrong:** Phase 18 decides to use "short" format, injects format_hint into IntentProcessor context. Phase 16 generator receives it but ignores it (still generates long message).

**Why it happens:** Format_hint is just context, not a system prompt constraint. Generator uses persona tone (AMMAR_system_prompt) but doesn't incorporate format guidance.

**How to avoid:**
- **Modify persona system prompts** in Phase 16 to include format guidance: "When format_hint='short', keep message ≤100 characters. When format_hint='story', tell a 2-3 sentence arc."
- Alternative: Create **format-specific system prompts** (e.g., AMMAR_standard_prompt, AMMAR_short_prompt) and select at generation time
- Test: Verify generator output format matches injected hint (e.g., short format → check len(message) ≤ 100)

**Warning signs:** Messages are always the same length regardless of format_hint in ledger.

### Pitfall 5: Ledger Query Performance (Large Delivery Ledger)

**What goes wrong:** After 6 months of messages (360 deliveries), WeeklyResponseRateCalculator reads entire DELIVERY_LEDGER.jsonl and scans for 7-day window. Calculation takes 5+ seconds on every message generation.

**Why it happens:** JSONL is human-readable but not indexed. No way to query "all deliveries from past 7 days, persona=AMMAR" without full scan.

**How to avoid:**
- For v1.1 (proof of concept), accept the full scan. Document: "Performance degrades with ledger size; optimize with ledger indexing in v1.2"
- Optimization strategy (if needed): Create **ledger index file** (DELIVERY_LEDGER_INDEX.jsonl) with summary: persona, date_bucket (YYYYMM), count. Speeds up calculations.
- Alternative: Keep in-memory cache of response_rate per persona, invalidate every 1 hour

**Warning signs:** Calculation takes >1 second. Profile code (time.time() around main loop) and adjust if needed.

---

## Code Examples

### Example 1: Weekly Response Rate Calculation

**Source:** Phase 17 VERIFICATION.md (integration readiness section) shows the exact API:

```python
from HIKMAH__knowledge_index.delivery import DeliveryLedger
from pathlib import Path

# Load ledger (Phase 17 artifact)
ledger = DeliveryLedger(Path("HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl"))

# Query deliveries and responses (Phase 17 provides these methods)
deliveries = ledger.get_deliveries_for_persona("AMMAR", limit=14)  # Past ~7 days
responses = [ledger.get_responses_for_message(d["message_id"]) for d in deliveries]

# Calculate rate
response_rate = len([r for r in responses if r]) / len(deliveries)
if response_rate < 0.80:
    print(f"AMMAR rate {response_rate:.0%} < 80%. Consider format rotation.")
```

**Phase 18 wraps this in WeeklyResponseRateCalculator class:**

```python
from HIKMAH__knowledge_index.adaptation import WeeklyResponseRateCalculator

calc = WeeklyResponseRateCalculator(ledger_path="HIKMAH__knowledge_index/DELIVERY_LEDGER.jsonl")
rate, numerator, denominator = calc.calculate(
    persona="AMMAR",
    days=7,
    ledger_path=None  # Uses default from __init__
)
# rate=0.65, numerator=13, denominator=20
```

### Example 2: Format Rotation State Machine

**Design:**

```python
from HIKMAH__knowledge_index.adaptation import FormatRotationManager
from pathlib import Path

# Initialize rotation manager
manager = FormatRotationManager(
    state_path=Path("HIKMAH__knowledge_index/adaptation/ADAPTATION_STATE.jsonl"),
    ledger_path=Path("HIKMAH__knowledge_index/adaptation/ADAPTATION_LEDGER.jsonl")
)

# Get current format (reads ADAPTATION_STATE.jsonl)
current = manager.get_current_format("AMMAR")
# Returns: "standard" (or cached state if exists)

# If response_rate < 80%, rotate format
if response_rate < 0.80:
    new_format = manager.rotate_format(
        persona="AMMAR",
        reason=f"Response rate {response_rate:.0%} < 80%"
    )
    # new_format = "short" (advances from "standard", logs to ADAPTATION_LEDGER.jsonl)
    # ADAPTATION_STATE.jsonl updated: current_format="short", previous_format="standard"
```

**State machine logic (inside rotate_format):**
```python
FORMATS = ["standard", "short", "emoji", "direct_question", "story"]

def rotate_format(self, persona: str, reason: str) -> str:
    # Load current state
    state = self._load_state(persona)  # {"current_format": "standard", "previous_format": "story"}
    
    # Find current index
    current_idx = FORMATS.index(state["current_format"])  # 0
    
    # Advance to next, wrapping around
    next_idx = (current_idx + 1) % len(FORMATS)  # 1
    next_format = FORMATS[next_idx]  # "short"
    
    # Check: is next_format same as previous? (prevent immediate repeat)
    if next_format == state.get("previous_format"):
        next_idx = (next_idx + 1) % len(FORMATS)
        next_format = FORMATS[next_idx]  # Skip and try next
    
    # Log rotation (BEFORE updating state)
    self.logger.log_rotation(
        persona=persona,
        old_format=state["current_format"],
        new_format=next_format,
        response_rate=self.calc.calculate(persona)[0],
        reason=reason
    )
    
    # Update state
    state["previous_format"] = state["current_format"]
    state["current_format"] = next_format
    self._save_state(persona, state)
    
    return next_format
```

### Example 3: Format Hint Injection into Message Generation

**Phase 16 integration point:**

```python
# In Phase 16 message_generation/__init__.py (generate_and_dedupe function)

from HIKMAH__knowledge_index.adaptation import FormatRotationManager
from HIKMAH__knowledge_index.message_generation.intent_processor import IntentProcessor

def generate_and_dedupe(
    persona: str,
    intent: str,
    index: dict,
    context_tags: list,
    **kwargs
) -> tuple[str, bool, str]:
    """Generate message with optional format adaptation."""
    
    # NEW: Check if format adaptation needed (Phase 18)
    rotation_manager = FormatRotationManager()
    response_rate, _, _ = rotation_manager.calc.calculate(persona, days=7)
    format_hint = None
    
    if response_rate < 0.80:
        format_hint = rotation_manager.get_current_format(persona)
        # format_hint = "short" (if rotation happened)
    
    # Process intent with format hint
    processor = IntentProcessor()
    context = processor.build_context(
        intent=intent,
        index=index,
        format_hint=format_hint  # NEW: inject hint
    )
    
    # Generate message (format hint passed via context)
    message, ok, reason = generator.generate_message(
        persona=persona,
        intent_context=context,
        ...
    )
    
    return message, ok, reason
```

**Phase 16 generator receives format_hint in context:**

```python
def generate_message(persona: str, intent_context: dict, ...) -> tuple[str, bool, str]:
    """Generate message with format guidance."""
    
    format_hint = intent_context.get("format_hint")  # "short" or None
    
    # Modify system prompt if format_hint present
    system_prompt = PERSONA_SYSTEM_PROMPTS[persona]
    if format_hint == "short":
        system_prompt += "\n\nFORMAT CONSTRAINT: Keep message under 100 characters. Be even more terse."
    elif format_hint == "emoji":
        system_prompt += "\n\nFORMAT CONSTRAINT: Include 1-2 emojis. Use visual markers to emphasize."
    elif format_hint == "direct_question":
        system_prompt += "\n\nFORMAT CONSTRAINT: Frame as a direct question. Start with '?'"
    elif format_hint == "story":
        system_prompt += "\n\nFORMAT CONSTRAINT: Tell a brief 2-3 sentence story or example. Make it relatable."
    
    # Call Claude API with modified system prompt
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=150,
        system=system_prompt,  # Now includes format guidance
        messages=[{"role": "user", "content": intent_context["summary"]}]
    )
    
    return response.content[0].text, True, None
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed message format per persona (AMMAR always terse, HIKMAH always warm) | Format rotation if engagement drops <80% | Phase 18 (this phase) | Adaptive messaging: low engagement triggers format experiments without manual operator intervention |
| No engagement tracking | Weekly response rate calculated from delivery ledger (Phase 17) | Phase 17 (delivery tracking phase) | Foundation for Phase 18 adaptation decisions |
| Engagement metrics in memory | Immutable JSONL ledgers (ADAPTATION_STATE, ADAPTATION_LEDGER) | Phase 14-18 (all phases) | Audit trail; crash recovery; queryable history |

**No deprecated patterns in Phase 18** — this is new capability. No legacy code to refactor.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (3.11+) |
| Config file | pytest.ini (existing HIKMAH__knowledge_index, Phase 14-17 config) |
| Quick run command | `pytest HIKMAH__knowledge_index/adaptation/tests/ -x -v` |
| Full suite command | `pytest HIKMAH__knowledge_index/adaptation/tests/ -v --cov=HIKMAH__knowledge_index/adaptation` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADAPT-01 | WeeklyResponseRateCalculator.calculate(persona, days=7) returns (rate, numerator, denominator) | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_response_rate_calculator.py::test_calculate_basic -x` | ❌ Wave 0 |
| ADAPT-01 | Edge case: denominator=0 (new persona) returns rate=1.0 (skip adaptation) | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_response_rate_calculator.py::test_calculate_no_deliveries -x` | ❌ Wave 0 |
| ADAPT-01 | Correctly counts response events vs. delivery events from DELIVERY_LEDGER.jsonl | integration | `pytest HIKMAH__knowledge_index/adaptation/tests/test_integration.py::test_rate_calc_counts_responses -x` | ❌ Wave 0 |
| ADAPT-02 | FormatRotationManager.rotate_format() advances format in sequence: standard → short → emoji → direct_question → story → standard | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py::test_rotate_advances_format -x` | ❌ Wave 0 |
| ADAPT-02 | Format rotation respects no-consecutive-repeat rule | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py::test_rotate_no_consecutive_repeat -x` | ❌ Wave 0 |
| ADAPT-02 | Supports 5+ format rotations without repeat constraint violation | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py::test_ten_rotations_no_repeats -x` | ❌ Wave 0 |
| ADAPT-03 | AdaptationLogger.log_rotation() writes entry to ADAPTATION_LEDGER.jsonl with persona, old_format, new_format, response_rate, rationale | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py::test_log_rotation_writes_entry -x` | ❌ Wave 0 |
| ADAPT-03 | Ledger entry includes timestamp, adaptation_id, calculation_window_days for traceability | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py::test_log_rotation_includes_metadata -x` | ❌ Wave 0 |
| ADAPT-03 | Rationale is human-readable and includes response_rate + threshold | unit | `pytest HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py::test_rationale_format -x` | ❌ Wave 0 |
| ADAPT-04 | Format rotation never produces consecutive repeats across 10+ consecutive messages | integration | `pytest HIKMAH__knowledge_index/adaptation/tests/test_integration.py::test_ten_consecutive_no_repeats -x` | ❌ Wave 0 |
| ADAPT-04 | Validates format rotation against ADAPTATION_STATE history | integration | `pytest HIKMAH__knowledge_index/adaptation/tests/test_integration.py::test_no_repeat_validated_against_state -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest HIKMAH__knowledge_index/adaptation/tests/test_*.py -x -v` (all unit tests, quick)
- **Per wave merge:** `pytest HIKMAH__knowledge_index/adaptation/tests/ -v --cov=HIKMAH__knowledge_index/adaptation --cov-report=term-missing` (full suite, coverage report)
- **Phase gate:** Full suite green + coverage ≥80% before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `HIKMAH__knowledge_index/adaptation/response_rate_calculator.py` — implements WeeklyResponseRateCalculator.calculate()
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_response_rate_calculator.py` — 8 tests covering basic calc, edge cases (denominator=0), time filtering
- [ ] `HIKMAH__knowledge_index/adaptation/format_rotation_manager.py` — implements FormatRotationManager with no-repeat state machine
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_format_rotation_manager.py` — 12 tests covering rotation sequence, no-repeat, edge cases
- [ ] `HIKMAH__knowledge_index/adaptation/adaptation_logger.py` — implements AdaptationLogger with JSONL writes
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_adaptation_logger.py` — 6 tests covering ledger writes, timestamp format, metadata
- [ ] `HIKMAH__knowledge_index/adaptation/adaptation_state.py` — AdaptationState dataclass + file I/O (load/save per persona)
- [ ] `HIKMAH__knowledge_index/adaptation/tests/conftest.py` — shared fixtures: MockDeliveryLedger with synthetic delivery/response events
- [ ] `HIKMAH__knowledge_index/adaptation/tests/test_integration.py` — 8 integration tests: rate calc → rotation decision → no-repeat validation
- [ ] `HIKMAH__knowledge_index/adaptation/__init__.py` — exports all public classes
- [ ] `HIKMAH__knowledge_index/adaptation/ADAPTATION_LEDGER.jsonl` — (created on first write)
- [ ] `HIKMAH__knowledge_index/adaptation/ADAPTATION_STATE.jsonl` — (created on first write)
- [ ] `HIKMAH__knowledge_index/README.md` (update) — add Phase 18 section with adaptation architecture + integration example
- [ ] `HIKMAH__knowledge_index/__init__.py` (update) — export Phase 18 classes

**Total:** 12 new files + 2 updates. 3 production modules + 3 test modules.

---

## Open Questions

1. **Format Variation Efficacy:** How many format variations are sufficient? Research suggests 5 (standard, short, emoji, direct_question, story) but no data on which formats improve engagement for which personas.
   - What we know: Phase 17 logs response_rate; Phase 18 can A/B test formats over time
   - What's unclear: Which format lifts engagement most (short? emoji? story?)
   - Recommendation: Implement rotation with 5 formats as specified. Measure engagement per format in ADAPTATION_LEDGER.jsonl. Analyze in v1.2 post-launch retrospective.

2. **80% Threshold Hardcoded:** Requirement specifies "response rate <80%" but no justification for this specific number.
   - What we know: 80% is reasonable (20% disengagement triggers intervention)
   - What's unclear: Is 80% right for all personas? (AMMAR might tolerate lower; HIKMAH higher?)
   - Recommendation: Make threshold configurable in adaptation/config.yaml (v1.1 default: 0.80). Operator can adjust per persona in v1.2.

3. **Hysteresis Buffer for Oscillation:** Pitfall 2 mentions oscillation risk at 80% boundary.
   - What we know: Small random variance in user engagement can cause threshold crossings
   - What's unclear: Should we implement hysteresis (rotate at <75%, reset at >85%) or just enforce 1-rotation-per-week limit?
   - Recommendation: For v1.1, use 1-rotation-per-week limit (check last_rotation_at in ADAPTATION_STATE.jsonl). Hysteresis buffer defer to v1.2 if oscillation observed.

4. **Multi-Persona Concurrency:** Phase delivery is scheduled (09:00 AMMAR, 18:00 any persona). What if Hermes cron triggers multiple personas simultaneously?
   - What we know: ADAPTATION_STATE.jsonl is a file, not atomic database
   - What's unclear: Should we add file-level locking? Or document single-persona-at-a-time constraint?
   - Recommendation: Document for v1.1: "Single persona message generation at a time. Multi-threading deferred to v1.2 with file locking support (fcntl/msvcrt)."

---

## Integration Points

### Upstream (Phase 16: Message Generation)

**What Phase 18 consumes:** Generated messages with format applied.

**Integration:** Inside `generate_and_dedupe()` (Phase 16 public API):
1. Before calling IntentProcessor, check if adaptation needed
2. If response_rate < 80%, call FormatRotationManager.get_current_format() → receive format_hint
3. Pass format_hint to IntentProcessor.build_context() as optional parameter
4. Generator receives hint and modifies system prompt accordingly

**Code change in Phase 16:**
```python
# HIKMAH__knowledge_index/message_generation/__init__.py
from HIKMAH__knowledge_index.adaptation import FormatRotationManager

def generate_and_dedupe(...):
    # Check format adaptation (Phase 18)
    rotation_mgr = FormatRotationManager()
    rate, _, _ = rotation_mgr.calc.calculate(persona, days=7)
    format_hint = None
    if rate < 0.80:
        format_hint = rotation_mgr.get_current_format(persona)
    
    # Pass format_hint to processor
    processor = IntentProcessor()
    context = processor.build_context(intent, index, format_hint=format_hint)
    
    # Generate (format constraint already in system prompt)
    message, ok, reason = generator.generate_message(persona, context, ...)
```

### Downstream (Phase 19: Cross-Pillar Integration)

**What Phase 19 consumes:** Format rotation history from ADAPTATION_LEDGER.jsonl.

**Integration:** Phase 19 can use adaptation data to decide signaling strategy:
- E.g., "If TARIQ is in 'short' format (low engagement), don't send complex strategic signals"
- Or: "When persona rotates from 'standard' to 'story' format, increase narrative context in TARIQ signals"

**Not required for Phase 18.** Phase 19 planning will define integration.

---

## Confidence Assessment

| Area | Level | Reasoning |
|------|-------|-----------|
| **Data source clarity** | HIGH | Phase 17 VERIFICATION.md explicitly confirms DeliveryLedger API (get_deliveries_for_persona, get_responses_for_message) |
| **Response rate formula** | HIGH | Simple arithmetic: count responses / count deliveries, both from immutable Phase 17 ledger |
| **Format rotation logic** | HIGH | Standard state machine pattern (advance index, wrap around, no-repeat check); well-defined requirements |
| **Format hint injection** | MEDIUM | Requires Phase 16 generator modification to respect format constraints in system prompt. Generator is complex (Claude API, tones); need to verify generator accepts format_hint without breaking tone consistency. Minor risk: format_hint conflicts with persona tone. Mitigation: test format_hint + tone consistency together |
| **Ledger design** | HIGH | Mirrors Phase 14-17 JSONL patterns (immutable, append-only, timestamp integrity) |
| **Integration points** | HIGH | Phase 16 (before generation) and Phase 19 (consumption) are natural; no circular dependencies |
| **Test strategy** | HIGH | All behaviors testable via unit tests + integration tests. Mock DeliveryLedger enables deterministic rate scenarios |

**Overall Confidence: HIGH**
- Core logic is straightforward state machine + ledger queries
- Data sources well-defined (Phase 17 ledger)
- Test scenarios clear (response_rate thresholds, format rotation, no-repeat validation)
- Minor uncertainty: how format_hint interacts with persona tone (testable)

---

## Sources

### Primary (HIGH confidence)

- **Phase 17 VERIFICATION.md** (`/d/NIZAM/.planning/phases/17-delivery-response-tracking/17-VERIFICATION.md`) — Confirms DeliveryLedger API, ledger format, integration readiness for Phase 18 queries
- **REQUIREMENTS_v1.1.md** (`/d/NIZAM/.planning/REQUIREMENTS_v1.1.md`) — Specifies ADAPT-01-04 requirements verbatim
- **ROADMAP.md** (`/d/NIZAM/.planning/ROADMAP.md`) — Phase 18 goal, dependencies, success criteria
- **Phase 17 Source Code** — DeliveryLedger.get_deliveries_for_persona(), get_responses_for_message() verified implemented

### Secondary (MEDIUM confidence)

- **Phase 16 Message Generation** (`/d/NIZAM/HIKMAH__knowledge_index/message_generation/`) — Persona system prompts, generator.py API; format_hint injection requires testing but pattern clear
- **Phase 14-17 JSONL Patterns** — Schema, append-only semantics, privacy gates (context_tags) — all apply to Phase 18 ADAPTATION_LEDGER.jsonl

### Methodology

- Researched Phase 17 verification report to confirm available APIs (DeliveryLedger methods)
- Reviewed requirements document to ensure all ADAPT-01-04 mapped to design
- Analyzed Phase 14-17 code patterns to maintain architectural consistency
- Identified integration points in Phase 16 (format_hint injection) and Phase 19 (signal strategy)

---

## Summary for Planner

**Phase 18 is feasible with 2-3 days of focused work (2 waves):**

**Wave 1 (Foundations):**
- WeeklyResponseRateCalculator (response_rate.py) — queries Phase 17 ledger
- FormatRotationManager (format_rotation_manager.py) — state machine + ADAPTATION_STATE.jsonl I/O
- AdaptationLogger (adaptation_logger.py) — ADAPTATION_LEDGER.jsonl writes
- 18 unit tests covering logic, edge cases, state persistence

**Wave 2 (Integration & Validation):**
- Integration tests: rate calc → rotation decision → no-repeat validation
- Phase 16 hook: format_hint injection into generate_and_dedupe()
- README.md Phase 18 section with architecture + example
- Full test suite: 30-40 tests, >80% coverage

**Key points:**
- No new external dependencies (JSONL, stdlib only)
- Reuses Phase 17 DeliveryLedger API (verified available)
- Mirrors Phase 14-17 JSONL patterns (low risk)
- Format hint injection to Phase 16 requires testing but is isolated change
- Comprehensive audit trail (ADAPTATION_LEDGER.jsonl) for operator visibility

**Risks:**
- Format hint might conflict with persona tone (MEDIUM, testable)
- Race condition on format rotation if multi-threaded (LOW for v1.1, document constraint)
- Threshold oscillation at 80% boundary (LOW, mitigated with 1-rotation-per-week limit)

---

*Research completed: 2026-06-21 16:35 UTC*  
*Researcher: Claude (gsd-researcher)*  
*Status: Ready for Phase 18 planning*
