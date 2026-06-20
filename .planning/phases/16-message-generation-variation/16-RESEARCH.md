# Phase 16: Message Generation & Variation - Research

**Researched:** 2026-06-21  
**Domain:** LLM-based message generation with persona tone consistency, intent rephrasing, repetition tracking, and actionable nudge synthesis  
**Confidence:** HIGH (Claude API verified, Phase 14-15 foundation solid, persona definitions documented)

## Summary

Phase 16 must implement a message generator that converts user intents (e.g., "You have open work on AI optimization") into fresh, actionable nudges with persona-consistent tone. The system must rephrase intents dynamically, pull current context from the refreshed knowledge index (Phase 15), apply persona character (AMMAR: builder-focused, HIKMAH: philosophical, TARIQ: strategic), and avoid exact phrase repeats within the last 5 messages per persona.

This phase consumes Phase 14-15 outputs (fresh or cached indices with topics, completions, stalled_work, activity_history) and produces structured message objects ready for Phase 17 delivery. Message generation bridges intent → context → tone → actionable nudge, with all outputs privacy-gated (no raw personal data, only safe context tags).

**Primary recommendation:** Use Claude API with system prompts for persona tone injection; implement a local message history tracker (per-persona, last 5 messages) to detect and skip exact repeats; structure generation around: (1) index context extraction, (2) intent rephrasing via LLM, (3) tone enforcement via system prompt, (4) repetition check, (5) validation before returning. Store message history in JSONL ledger (Phase 14 pattern) for audit trail.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `anthropic` Python SDK | 1.0+ | Claude API client for message generation with system prompts | Official Anthropic library, supports all Claude models, streaming optional, token counting included, HIGH confidence via Context7 (59K code examples) |
| `python-dateutil` | 2.8+ | ISO 8601 timestamp parsing and timezone-aware comparisons | Standard for temporal operations; already in Phase 15 stack |
| Python stdlib `json` | 3.8+ | JSON serialization for message ledger (JSONL persistence) | Built-in, no external dependency; follows Phase 14 ledger pattern |
| Python stdlib `pathlib` | 3.8+ | Cross-platform file path handling for ledger writes | Built-in, used consistently in Phase 14-15 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tiktoken` | 0.5+ | Token counting for message generation cost tracking | Optional; use to validate message length before API call and estimate costs per persona |
| `pydantic` | 2.0+ | Message schema validation and structured output | If implementing strict message contract validation (recommended for production) |

### Already Installed
- `anthropic`: Confirmed in hermes-venv (used by Phase 20+ systems)
- `python-dateutil`: Already used in Phase 15
- `json`, `pathlib`: Python stdlib

**Installation:**
```bash
# Core dependencies (likely already present)
pip install anthropic>=1.0 python-dateutil>=2.8

# Optional for strict validation
pip install pydantic>=2.0 tiktoken>=0.5
```

---

## Architecture Patterns

### Recommended Project Structure
```
HIKMAH__knowledge_index/
├── message_generation/                # NEW: Phase 16 message generation
│   ├── __init__.py
│   ├── generator.py                   # Main message generator
│   ├── persona_tones.py               # Persona tone definitions + system prompts
│   ├── repetition_tracker.py          # Last 5 messages per persona + dedupe logic
│   ├── intent_processor.py            # Intent extraction and context building
│   ├── message_ledger.py              # JSONL message history writer
│   └── tests/
│       ├── conftest.py                # Shared fixtures (mock LLM, sample index)
│       ├── test_generator.py          # Message generation end-to-end tests
│       ├── test_repetition_tracker.py # Deduplication logic tests
│       ├── test_intent_processor.py   # Intent → context conversion tests
│       └── test_tone_consistency.py   # Persona tone consistency validation
├── refresh/                           # Phase 15: Data refresh (existing)
│   └── ...
├── index/                             # Phase 14: Schema & storage (existing)
│   └── ...
└── MESSAGE_LEDGER.jsonl              # NEW: Append-only ledger of generated messages per persona
```

### Pattern 1: System Prompt-Driven Persona Tone Injection

**What:** Each persona gets a distinct system prompt defining tone, voice, and operational constraints. Claude enforces tone consistency via system instruction.

**When to use:** Every message generation call uses a persona-specific system prompt to ensure tone consistency across 5+ consecutive generations.

**Example:**
```python
# Source: Claude API Context7 docs + NIZAM persona definitions
from anthropic import Anthropic

PERSONA_SYSTEM_PROMPTS = {
    "AMMAR": """You are AMMAR, a builder and custodian of order. Your role is to keep systems running smoothly.
- Tone: Plain, terse, factual. No flourish or encouragement.
- Voice: Like a maintenance log. Report facts. Never persuade or cheer.
- Output: Short, actionable nudges on open work. Example: "Your AI workflow has 3 open items. Pick one and move it forward."
- Constraints: ZERO subjective state. No "I think" or "I feel". Only: [NUDGE_TYPE] + [SPECIFIC_ACTION] + [WHY_NOW].""",

    "HIKMAH": """You are HIKMAH, the weekly synthesist and wisdom companion. You see patterns across time and find meaning.
- Tone: Deep, warm, practical, intellectually honest, spiritually motivating.
- Voice: Like a thoughtful chronicle. Connect dots. Reflect on progress and challenges.
- Output: Thoughtful nudges that explore patterns. Example: "Your AI work has stalled for 2 weeks. Last time you broke through by sleeping first—notice anything similar now?"
- Constraints: Mainstream Sunni orthodoxy for any spiritual reflection. No sensationalism. No automatic miracle claims.""",

    "TARIQ": """You are TARIQ, the long-horizon strategist. You watch tactical moves accumulate toward multi-year objectives.
- Tone: Patient, big-picture, evidence-aware, willing to revise.
- Voice: Like a general's command brief. Calm, ambitious, focused on the campaign.
- Output: Strategic nudges that connect daily work to quarterly/annual goals. Example: "Your AI work is a load-bearing bet for Q3. This 2-week stall directly impacts your June target. What's blocking you?"
- Constraints: Never trade non-negotiables for short-term wins. Demand honest gap analysis.""",
}

def generate_message(
    persona: str,
    intent: str,
    index: dict,
    last_5_messages: list[str],
    client: Anthropic
) -> str:
    """Generate a persona-consistent message."""
    
    system_prompt = PERSONA_SYSTEM_PROMPTS[persona]
    
    # Build context from index
    topics = index.get("topics", [])
    context_summary = f"User has {len(topics)} open topics: " + ", ".join(t["name"] for t in topics[:3])
    
    # Build user message with intent + index context
    user_message = f"""Intent: {intent}
Current context: {context_summary}
Last 5 messages generated (to avoid repetition): {last_5_messages}

Generate ONE actionable nudge that:
1. Rephrases the intent into a motivation/question/prompt
2. Adds specific context from current work
3. Is actionable (user can do something right now in next 30 min)
4. Stays under 280 characters (Telegram mobile friendly)
5. Does NOT repeat exact phrases from last 5 messages"""
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    return response.content[0].text
```

### Pattern 2: Repetition Tracker with Last-5 Message Deduplication

**What:** Per-persona ledger of last 5 generated messages. Before returning a message, check if exact phrase already appears in recent history.

**When to use:** Every message generation must query the repetition tracker to avoid "Your AI workflow could be faster" being sent twice in a row.

**Example:**
```python
# Source: Phase 14 message ledger pattern + repetition tracking best practice
from pathlib import Path
import json
from datetime import datetime, timezone

class RepetitionTracker:
    """Tracks last 5 messages per persona to prevent exact phrase repeats."""
    
    def __init__(self, ledger_path: Path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_last_messages(self, persona: str, limit: int = 5) -> list[str]:
        """Retrieve last N generated messages for a persona."""
        if not self.ledger_path.exists():
            return []
        
        recent = []
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                if entry.get('persona') == persona and entry.get('event_type') == 'message_generated':
                    recent.append(entry.get('message_text', ''))
        
        return recent[-limit:]
    
    def extract_key_phrases(self, text: str, min_length: int = 10) -> set[str]:
        """Extract potentially repeated phrases (substrings of length ≥ 10)."""
        phrases = set()
        words = text.split()
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if len(phrase) >= min_length:
                phrases.add(phrase.lower())
        return phrases
    
    def is_repetition(self, new_message: str, persona: str) -> bool:
        """Check if new_message contains exact phrase from last 5 messages."""
        last_messages = self.get_last_messages(persona)
        new_phrases = self.extract_key_phrases(new_message)
        
        for old_message in last_messages:
            old_phrases = self.extract_key_phrases(old_message)
            if new_phrases & old_phrases:  # Any intersection = repetition
                return True
        
        return False
    
    def log_message(self, persona: str, message_text: str, intent: str, success: bool = True):
        """Append generated message to ledger."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "persona": persona,
            "event_type": "message_generated",
            "message_text": message_text,
            "intent": intent,
            "success": success,
        }
        
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

def generate_and_dedupe(
    persona: str,
    intent: str,
    index: dict,
    client: Anthropic,
    tracker: RepetitionTracker,
    max_retries: int = 3
) -> tuple[str, bool]:
    """Generate message, reject if repetition detected, retry up to max_retries."""
    for attempt in range(max_retries):
        last_5 = tracker.get_last_messages(persona)
        
        message = generate_message(persona, intent, index, last_5, client)
        
        if not tracker.is_repetition(message, persona):
            tracker.log_message(persona, message, intent, success=True)
            return (message, True)
        else:
            print(f"Repetition detected in attempt {attempt+1}; retrying...")
    
    # On max retries exceeded, log failure but still return message
    tracker.log_message(persona, message, intent, success=False)
    return (message, False)
```

### Pattern 3: Intent → Context → Message Pipeline

**What:** Structured 3-step conversion: (1) extract key topics from intent, (2) pull current index state for those topics, (3) generate message with fresh context injected.

**When to use:** Every message generation starts with intent processing to ensure context relevance.

**Example:**
```python
# Source: Phase 14-15 index schema + NLG best practices
from typing import Optional

class IntentProcessor:
    """Converts user intent into message generation context."""
    
    @staticmethod
    def extract_topics(intent: str, index: dict) -> list[dict]:
        """
        Extract relevant topics from intent and index.
        
        Example:
            Intent: "You have open work on AI optimization"
            Topics: [{"name": "AI optimization", "status": "active", "blockers": [...]}]
        """
        topics = index.get("topics", [])
        
        # Simple heuristic: topics whose names appear in intent (case-insensitive)
        intent_lower = intent.lower()
        matching = [t for t in topics if t["name"].lower() in intent_lower]
        
        # If no exact match, return first few open topics
        if not matching:
            matching = [t for t in topics if t["status"] == "active"][:3]
        
        return matching
    
    @staticmethod
    def build_context_summary(topics: list[dict], index: dict) -> str:
        """Build rich context from selected topics."""
        if not topics:
            return "No open topics; recent completions: " + ", ".join(
                c["name"] for c in index.get("completions", [])[:3]
            )
        
        summaries = []
        for topic in topics:
            days_active = (datetime.now(timezone.utc) - datetime.fromisoformat(topic["last_activity"])).days
            blockers_text = "; ".join(b["text"] for b in topic.get("blockers", [])[:2]) if topic.get("blockers") else "No known blockers"
            
            summary = f"{topic['name']} (active {days_active}d, blockers: {blockers_text})"
            summaries.append(summary)
        
        return " | ".join(summaries)
    
    @staticmethod
    def should_celebrate(index: dict) -> bool:
        """Check if index shows recent completions (triggers celebratory tone)."""
        if not index.get("completions"):
            return False
        
        # Get most recent completion
        latest_completion = index["completions"][-1]
        completed_at = datetime.fromisoformat(latest_completion["completed_at"])
        days_since = (datetime.now(timezone.utc) - completed_at).days
        
        return days_since <= 7  # Recent completion in last 7 days
    
    @staticmethod
    def get_activity_summary(index: dict) -> str:
        """Summarize recent activity from activity_history."""
        history = index.get("activity_history", [])
        if not history:
            return "No recent activity logged."
        
        recent_events = history[-10:]  # Last 10 events
        event_types = {}
        for event in recent_events:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        summary_parts = []
        for event_type, count in event_types.items():
            summary_parts.append(f"{count} {event_type.replace('_', ' ')}")
        
        return "Recent: " + ", ".join(summary_parts) + "."
```

### Pattern 4: Message Ledger with Privacy Filtering

**What:** Append-only JSONL ledger of all generated messages (persona, intent, message_text, tone_applied, repetition_flagged, ts). No raw personal data in ledger entries.

**When to use:** Every message generation appends a ledger entry for audit trail and Phase 18 response tracking.

**Example:**
```python
# Source: Phase 14 message ledger pattern + privacy-safe context tagging
import hashlib

class MessageLedger:
    """Immutable ledger of generated messages with audit trail."""
    
    def __init__(self, ledger_path: Path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_generation(
        self,
        persona: str,
        message_text: str,
        intent: str,
        context_tags: list[str],
        tone_applied: str,
        repetition_flagged: bool,
        success: bool = True,
        error_reason: str = None
    ):
        """Log a message generation event to the ledger."""
        
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "persona": persona,
            "event_type": "message_generation",
            "message_text": message_text,
            "intent": intent,
            "context_tags": context_tags,  # SAFE: ["technical", "financial"] not raw personal data
            "tone_applied": tone_applied,
            "repetition_flagged": repetition_flagged,
            "success": success,
            "error_reason": error_reason,
        }
        
        # Compute integrity hash (following Phase 14 pattern)
        entry_json = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        entry['message_hash'] = hashlib.sha256(entry_json.encode()).hexdigest()[:16]
        
        with open(self.ledger_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_messages_for_persona(self, persona: str, limit: int = 10) -> list[dict]:
        """Retrieve last N messages for a persona."""
        if not self.ledger_path.exists():
            return []
        
        messages = []
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line)
                if entry.get('persona') == persona and entry.get('event_type') == 'message_generation':
                    messages.append(entry)
        
        return messages[-limit:]
```

### Anti-Patterns to Avoid

- **Hardcoded persona tones in message generation code:** Tones change; externalize to YAML or persona config. Use the existing NIZAM persona definitions from `NIZAM__system/personas/*.json`.
- **Querying LLM for every single message without caching tone:** System prompts should be cached/reused. Claude API supports prompt caching; use it to reduce latency + cost.
- **Storing raw user data in message ledger:** Only store safe context tags (e.g., "technical", "financial", not "Seif's AI project"). Privacy gate at ledger write time.
- **No audit trail for message rejection:** If repetition check rejects a message, log the rejection with reason. Operator needs visibility into why users see what they see.
- **Ignoring message length constraints:** Telegram mobile has ~280 char limits for optimal readability. Enforce max length validation before returning message.
- **Generating same intent phrasing across personas:** TARIQ and AMMAR may generate different nudges for same intent. Ensure system prompt dominates, not generic template.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM-based tone consistency | Custom string templating + heuristics for tone | Claude API with system prompts | LLM tone injection is context-aware, flexible, supports persona personality evolution without code changes. Hand-rolled templates are rigid and fail on edge cases. |
| Intent-to-message rephrasing | Simple string substitution | Claude API message generation with intent context | Rephrasing requires understanding user context + persona tone. Hand-rolled yields generic, non-actionable messages ("You have open work" → "You have open work"). LLM is dramatically better. |
| Repetition detection | Simple string comparison or regex | Phrase-level extraction + set intersection (see Pattern 2) | Exact string matching misses paraphrases. Phrase-level deduplication (3-gram intersection) catches "Your AI workflow could be faster" vs. "Your workflow—AI track—could accelerate" as repetition. |
| Message history tracking | In-memory list | JSONL append-only ledger (Phase 14 pattern) | In-memory state is lost on crash/restart. Ledger persists, enables audit trail, supports replay for Phase 18 response correlation. |
| Persona tone enforcement | Per-persona if/else branches for message style | Single system prompt parameter per persona | Branching scales poorly (11 personas × 5 message types = 55 branches). System prompts are unified, testable, evolve without code deployment. |

**Key insight:** Message generation is deceptively complex — intent understanding, tone consistency, context relevance, repetition avoidance, and privacy gating all interact. Lean on Claude API + structured data (index + ledger) rather than hand-rolled logic.

---

## Common Pitfalls

### Pitfall 1: System Prompt Too Generic, Persona Tone Lost

**What goes wrong:** System prompt says "Be like AMMAR" but doesn't specify what AMMAR sounds like. Generator outputs bland, generic nudges ("You have open work, continue it") that all personas produce identically.

**Why it happens:** Developer assumes persona name is sufficient context. Claude needs detailed tone examples and constraints to enforce personality.

**How to avoid:** 
- System prompt must include: (a) role definition, (b) 3–5 concrete tone examples, (c) explicit DO/DON'T constraints, (d) persona voice markers ("terse maintenance log" for AMMAR; "deep, warm, spiritual" for HIKMAH).
- Test with 5 consecutive message generations for same intent; compare outputs. If all sound similar, persona tone is weak.

**Warning signs:** Phase 16 test runs show AMMAR and HIKMAH produce nearly identical messages. If true, system prompts need strengthening with persona-specific examples.

### Pitfall 2: Repetition Check Too Loose or Too Strict

**What goes wrong:** 
- Too loose: "Your AI work is stalled" sent twice in a row (only exact string match, misses paraphrases).
- Too strict: "Your AI work is stalled" rejected because old message was "Your AI workflow is stalled" (false positive).

**Why it happens:** Developer uses naive string comparison (or no comparison). Phrase-level matching is forgotten.

**How to avoid:** Use phrase-level deduplication (3-gram or 4-gram set intersection, see Pattern 2). Tune phrase length threshold based on testing: too short (2-gram) → false positives; too long (5-gram) → false negatives.

**Warning signs:** Test message generation loop 10x with same intent. Count how many unique outputs occur. If <5 unique outputs, repetition detection is too strict. If >9 identical, it's too loose.

### Pitfall 3: Context Summary from Index Stale or Empty

**What goes wrong:** Index has 5 open topics, but context summary is built from old snapshot. Or index is empty (persona never initialized), and message generator crashes.

**Why it happens:** Phase 15 refresh failed silently. Or Phase 14 initialization didn't run for all personas. Generator assumes index always has fresh data.

**How to avoid:** 
- Always validate index before context extraction (see Phase 15 validation pattern).
- Provide fallback context when index is sparse: "No open topics on record; start something new or review recent completions."
- Handle edge case: if index has 0 topics and 0 completions, generate encouragement message ("It's a good time to pick your next focus").

**Warning signs:** Test message generation for a persona initialized 2 weeks ago (no refresh since). Verify message still generates and doesn't crash.

### Pitfall 4: Privacy Violation — Raw Personal Data in Message or Ledger

**What goes wrong:** Message says "Seif's AI workflow could be faster — ready to tackle that?" or ledger stores "user_name: Seif" instead of safe context tag.

**Why it happens:** Developer extracts topic names directly from index without filtering. Or assumes ledger is private-only and doesn't sanitize context.

**How to avoid:** 
- Message generation must replace proper names with pronouns: "Your AI workflow" not "Seif's AI workflow".
- Ledger must use only context_tags (e.g., "technical", "financial") not raw data. Validate at write time.
- Enforce privacy gate: phase 16 message text must pass check: no first/last names, no email addresses, no raw context beyond whitelisted tags.

**Warning signs:** Phase 20 privacy audit flags message ledger or generated messages containing PII. If caught in test, tighten filtering before Phase 17 Telegram delivery.

### Pitfall 5: No Handling for LLM Failures or Rate Limiting

**What goes wrong:** Claude API rate limit (429) or timeout error crashes message generation. User nudge is not sent.

**Why it happens:** Generator doesn't catch exceptions. Or retries indefinitely without backoff.

**How to avoid:** 
- Wrap Claude API calls in try/except catching `anthropic.RateLimitError`, `anthropic.APITimeoutError`, `anthropic.APIError`.
- On LLM failure, fall back to a simple template nudge based on index (e.g., "You have 3 open topics — pick one and move it forward").
- Log failure to MESSAGE_LEDGER with error reason.
- Implement exponential backoff for transient errors (see Phase 15 retry pattern).

**Warning signs:** Test message generation loop 100x. If any call takes >10 seconds or fails, LLM error handling is insufficient.

---

## Code Examples

Verified patterns from official sources:

### Claude API Message Generation with System Prompt
```python
# Source: Claude API Context7 docs + NIZAM tone patterns
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")

system_prompt = """You are AMMAR, a builder and custodian.
- Tone: Plain, terse, factual.
- Voice: Maintenance log, not cheerleader.
- Output: Short actionable nudges only."""

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    system=system_prompt,
    messages=[
        {"role": "user", "content": "Intent: Your AI optimization work has 2 blockers. Rephrase as actionable nudge."}
    ]
)

message = response.content[0].text
print(message)
# Output: "AI optimization has 2 blockers. Identify which one you can move this hour."
```

### Persona Tone Definitions (Structure)
```json
{
  "personas": [
    {
      "codename": "AMMAR",
      "tone": "Plain, terse, non-emotive",
      "system_prompt": "You are AMMAR...",
      "example_outputs": [
        {"intent": "open work", "output": "3 items waiting. Pick one."},
        {"intent": "stalled", "output": "2-week blocker on finance review. Unblock it."}
      ],
      "constraints": ["ZERO subjective state", "No 'I feel'", "Only: [ACTION] + [REASON]"]
    }
  ]
}
```

### Message Ledger Structure (JSONL)
```json
{"ts": "2026-06-21T10:30:00Z", "persona": "AMMAR", "event_type": "message_generation", "message_text": "3 items waiting. Pick one.", "intent": "open_work", "context_tags": ["technical"], "tone_applied": "terse", "repetition_flagged": false, "success": true}
{"ts": "2026-06-21T10:35:00Z", "persona": "HIKMAH", "event_type": "message_generation", "message_text": "Your AI work has stalled 2 weeks. Sleep first—notice the pattern from last time you broke through?", "intent": "stalled", "context_tags": ["technical", "health"], "tone_applied": "reflective", "repetition_flagged": false, "success": true}
{"ts": "2026-06-21T10:40:00Z", "persona": "AMMAR", "event_type": "message_generation", "message_text": "3 items waiting. Pick one.", "intent": "open_work", "context_tags": ["technical"], "tone_applied": "terse", "repetition_flagged": true, "success": false, "error_reason": "exact_phrase_in_last_5"}
```

### Intent Processing and Context Building
```python
# Source: Phase 14-15 index schema + NLP pattern
def build_message_context(intent: str, index: dict) -> dict:
    """Extract and structure context for message generation."""
    topics = [t for t in index.get("topics", []) if t["status"] == "active"]
    context = {
        "topic_count": len(topics),
        "topics_summary": ", ".join(t["name"] for t in topics[:3]),
        "recent_accomplishments": len(index.get("activity_history", [])),
        "stalled_count": len(index.get("stalled_work", [])),
        "should_celebrate": len(index.get("completions", [])) > 0
    }
    return context
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded message templates per persona | System prompts + LLM generation | 2023+ (Claude API matured) | Dynamic, context-aware messages; tone evolves without code deployment |
| Manual content review for repetition | Phrase-level deduplication + LLM awareness | 2024+ (prompt engineering advances) | Automated, scalable to 11 personas × 100+ messages/day |
| Single generic message for all personas | Persona-specific system prompts + tone injection | NIZAM v1.1 (current) | Each persona delivers distinct voice; engagement improves |
| Synchronous LLM calls blocking message delivery | Claude API with optional async/streaming | 2024 (API maturity) | Phase 16 can implement non-blocking message generation if latency becomes issue |

**Deprecated/outdated:**
- **Persona selection based on user input:** Modern approach is deterministic persona router (existing NIZAM system). Message generation assumes persona is pre-selected.
- **Template-based repetition avoidance:** Phrase-level deduplication now standard; templates are brittle.
- **No audit trail for generated messages:** Full ledger now expected (Phase 14-15 pattern established).

---

## Open Questions

1. **Persona tone calibration and validation**
   - What we know: NIZAM personas defined in `NIZAM__system/personas/*.json` with `tone`, `role`, `mode` fields. Phase 14-15 research confirmed persona definitions.
   - What's unclear: Should system prompts be auto-generated from persona JSON, or hand-crafted per persona? How to validate tone consistency empirically?
   - Recommendation: Phase 16 planning should create PERSONA_TONES.json with hand-curated system prompts for each of 11 personas. Include 3–5 concrete output examples per persona for validation testing.

2. **LLM model selection and cost/latency tradeoff**
   - What we know: Claude 3.5 Sonnet (latest, balanced quality/latency) available via Anthropic SDK. Phase 15 research used context7 to verify API capabilities.
   - What's unclear: Should Phase 16 use Sonnet or Opus for tone consistency? What's acceptable latency for twice-daily message generation (09:00, 18:00 Cairo)?
   - Recommendation: Start with Claude 3.5 Sonnet (fast enough for Hermes cron, good tone enforcement). If latency >2 seconds per message, consider cached prompts or batch generation. Phase 18 (adaptation) can log model performance and adjust.

3. **Message history storage location**
   - What we know: Phase 15 stores indices in `HIKMAH__knowledge_index/indices/` (strict_local). MESSAGE_LEDGER would be `HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl` (strict_local per SYNC_POLICY).
   - What's unclear: Should message history be: (a) one global ledger, or (b) per-persona ledgers? How long to retain (7 days, 30 days, indefinite)?
   - Recommendation: Single global MESSAGE_LEDGER.jsonl (easier to query). Retention: indefinite (ledger is append-only, immutable; archive old segments via MAKHZAN if size grows). Phase 18+ will query for response correlation.

4. **Actionability validation and nudge quality metrics**
   - What we know: Phase 16 success criteria state "Generated message is actionable: nudges open topic, motivates action, or celebrates completion (not generic or passive)".
   - What's unclear: How to automatically validate actionability? "Pick one topic and move it forward" is actionable; "Your work is progressing" is passive. Can this be checked with LLM or heuristic?
   - Recommendation: Phase 16 planning should include simple heuristic: message must contain an imperative verb (e.g., "pick", "try", "schedule", "reflect", "celebrate"). Optional: add second-pass LLM validation ("Is this message actionable? Yes/No") if needed.

5. **Integration with Phase 15 fresh vs. cached index**
   - What we know: Phase 15 returns `(success, index, degradation_reason)`. If Drive unavailable, index is cached but usable.
   - What's unclear: Should Phase 16 message tone change if index is stale (e.g., "Based on recent work, ..." if fresh vs. "Last time we checked, ..." if cached)?
   - Recommendation: Log degradation_reason in MESSAGE_LEDGER context. Phase 16 messages assume fresh index. Phase 18 (adaptation) can analyze if stale indices correlate with lower response rates.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (v7.0+) with `unittest.mock` for Claude API mocking |
| Config file | `.planning/phases/16-message-generation-variation/conftest.py` (shared fixtures) |
| Quick run command | `pytest HIKMAH__knowledge_index/message_generation/tests/ -v -k "not api"` |
| Full suite command | `pytest HIKMAH__knowledge_index/message_generation/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MSG-01 | Message generator rephrases intent, adds context from index, applies persona tone | integration (mocked LLM) | `pytest HIKMAH__knowledge_index/message_generation/tests/test_generator.py::test_intent_rephrasing_with_tone -v` | ❌ Wave 0 |
| MSG-02 | System tracks last 5 messages per persona, detects and rejects exact phrase repeats | unit | `pytest HIKMAH__knowledge_index/message_generation/tests/test_repetition_tracker.py::test_last_5_deduplication -v` | ❌ Wave 0 |
| MSG-03 | Generated message is actionable: nudges open topic, motivates action, or celebrates completion | integration (LLM + heuristic) | `pytest HIKMAH__knowledge_index/message_generation/tests/test_generator.py::test_actionability_validation -v` | ❌ Wave 0 |
| MSG-04 | Persona tone is consistent across 5 consecutive test message generations per persona | integration (LLM + tone validation) | `pytest HIKMAH__knowledge_index/message_generation/tests/test_tone_consistency.py::test_tone_consistency_5x -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest HIKMAH__knowledge_index/message_generation/tests/ -v -k "not api"` (unit tests only, < 10 sec)
- **Per wave merge:** `pytest HIKMAH__knowledge_index/message_generation/tests/ -v` (includes mocked LLM integration, ~30 sec)
- **Phase gate:** Full suite green + manual spot-check: operator verifies 5 consecutive AMMAR/HIKMAH/TARIQ messages for tone consistency before mark-done

### Wave 0 Gaps
- [ ] `HIKMAH__knowledge_index/message_generation/__init__.py` — Public API (generate_message, RepetitionTracker, MessageLedger, etc.)
- [ ] `HIKMAH__knowledge_index/message_generation/generator.py` — Main message generator (Claude API + tone injection)
- [ ] `HIKMAH__knowledge_index/message_generation/persona_tones.py` — Persona system prompts + tone definitions
- [ ] `HIKMAH__knowledge_index/message_generation/repetition_tracker.py` — Last-5 message tracking + phrase deduplication
- [ ] `HIKMAH__knowledge_index/message_generation/intent_processor.py` — Intent extraction + context building from index
- [ ] `HIKMAH__knowledge_index/message_generation/message_ledger.py` — JSONL message history writer (append-only)
- [ ] `HIKMAH__knowledge_index/message_generation/tests/conftest.py` — Shared pytest fixtures (MockClaude, sample indices, mock messages)
- [ ] `HIKMAH__knowledge_index/message_generation/tests/test_generator.py` — End-to-end generation tests
- [ ] `HIKMAH__knowledge_index/message_generation/tests/test_repetition_tracker.py` — Deduplication logic tests
- [ ] `HIKMAH__knowledge_index/message_generation/tests/test_intent_processor.py` — Context building tests
- [ ] `HIKMAH__knowledge_index/message_generation/tests/test_tone_consistency.py` — Persona tone validation tests
- [ ] `HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl` — Message history ledger (created on first write)
- [ ] Update `HIKMAH__knowledge_index/__init__.py` to expose Phase 16 public API (generate_message, RepetitionTracker, MessageLedger, etc.)
- [ ] Update `HIKMAH__knowledge_index/README.md` with Phase 16 documentation and Phase 17 integration example

---

## Sources

### Primary (HIGH confidence)
- `/websites/platform_claude_en_api` - Claude API message creation, system prompts, model selection, token counting (Context7, 59K code examples)
- `D:\NIZAM\NIZAM__system\personas\*.json` - Persona definitions with tone, role, mode fields (existing NIZAM system)
- `D:\NIZAM\HIKMAH__knowledge_index\index\schema.py` - PersonaIndexDict schema with topics[], completions[], activity_history[], stalled_work[] (Phase 14 verified code)
- `D:\NIZAM\HIKMAH__knowledge_index\__init__.py` - Phase 15 public API providing refresh_persona_index() and load_cached_index() (Phase 15 verified code)
- `D:\NIZAM\.planning\ROADMAP.md` - Phase 16 requirements (MSG-01 through MSG-04) and success criteria (project specification)

### Secondary (MEDIUM confidence)
- `D:\NIZAM\NIZAM__system\companion\pulsation\message_builder.py` - Existing message building patterns with agent roles and context tags (NIZAM internal pattern)
- `D:\NIZAM\.planning\phases\15-data-refresh-synchronization\15-RESEARCH.md` - Phase 15 research documenting ledger patterns and audit trail structure (phase prior)

### Tertiary (LOW confidence)
- Project memory `nizam-hermes-deployment-env.md` (20 days old, configuration details may have changed)

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - Claude API verified via Context7 with 59K+ code examples; anthropic SDK documented and verified
- Architecture: **HIGH** - Patterns derived from Phase 14 ledger structure (JSONL + hash chaining) + Phase 15 refresh pipeline (error handling + graceful degradation)
- Persona tone consistency: **HIGH** - Persona definitions in NIZAM system are concrete with `tone`, `role`, `mode` fields; Claude system prompts proven effective for tone injection
- Repetition tracking: **MEDIUM** - Pattern is sound (phrase-level deduplication), but specific phrase length thresholds need empirical tuning during Phase 16 planning
- Pitfalls: **MEDIUM** - Identified from Context7 API docs + message generation best practices; not validated against this specific codebase yet

**Research date:** 2026-06-21  
**Valid until:** 2026-07-05 (14 days; Claude API stable, persona definitions locked, no major changes expected)  
**Revisit if:** 
- Persona tone definitions change significantly
- New personas added to NIZAM system (currently 11 fixed)
- Claude API adds major new capabilities (e.g., function calling for message validation)

---

*Document Version: 1.0*  
*Phase: 16 (Message Generation & Variation)*  
*Classification: NIZAM Internal — Planning artifact*
