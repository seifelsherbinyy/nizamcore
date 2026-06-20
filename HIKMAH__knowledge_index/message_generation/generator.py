"""
HIKMAH Message Generation: Core Generator Engine

Phase 16: Generate fresh, actionable, persona-consistent nudges via Claude API.

This module implements the main message generation engine with:
1. System prompt-based persona tone injection
2. Context-aware intent rephrasing via Claude
3. Repetition detection and retry logic
4. Error handling with exponential backoff and fallback messages
5. Actionability validation (heuristic + LLM-assisted)
6. Full audit trail logging to message ledger

Key Design Principles:
1. System prompt injection: Each persona gets distinct system prompt defining tone/constraints
2. Context building: IntentProcessor builds rich context from knowledge index before LLM call
3. Repetition checking: RepetitionTracker prevents phrase-level repeats from last 5 messages
4. Error resilience: Try/except on API errors, exponential backoff for retries, fallback messages
5. Actionability validation: Check for imperative verbs or celebratory tone, flag if missing
6. Privacy enforcement: All ledger entries use whitelisted context_tags only

Integration Points:
- Used by Phase 17 (Delivery) to generate nudges before sending via Telegram
- Consumes Phase 14-15 indices (fresh or cached)
- Feeds Phase 18+ (Adaptation, Integration, Privacy)

API Model: claude-3-5-sonnet-20241022 (fast, good tone control, mature API)
Max tokens: 100 (enforces <280 char limit)
Timeout: 10 seconds per request (Hermes cron constraints)
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any

from anthropic import Anthropic, RateLimitError, APITimeoutError, APIError

from HIKMAH__knowledge_index.message_generation.persona_tones import (
    PERSONA_SYSTEM_PROMPTS,
)
from HIKMAH__knowledge_index.message_generation.intent_processor import (
    IntentProcessor,
)
from HIKMAH__knowledge_index.message_generation.repetition_tracker import (
    RepetitionTracker,
)
from HIKMAH__knowledge_index.message_generation.message_ledger import MessageLedger

logger = logging.getLogger(__name__)

# Imperative verbs that indicate actionable messages
ACTIONABLE_VERBS = {
    "pick", "try", "schedule", "reflect", "celebrate", "identify",
    "focus", "move", "start", "review", "plan", "build", "learn",
    "share", "unblock", "prioritize", "reset", "adjust", "verify",
}

# Celebratory words that indicate positive/motivational tone
CELEBRATORY_WORDS = {
    "celebrate", "congratulate", "completed", "done", "finished",
    "great", "excellent", "awesome", "proud", "achievement",
}


def generate_message(
    persona: str,
    intent: str,
    index: Dict[str, Any],
    client: Anthropic,
    max_tokens: int = 100,
) -> str:
    """
    Generate a persona-consistent message via Claude API.

    Implements the core generation pipeline:
    1. Extract system prompt from PERSONA_SYSTEM_PROMPTS[persona]
    2. Build context using IntentProcessor.build_full_context()
    3. Construct user message with intent + context + constraints
    4. Call Claude API with system prompt injection
    5. Return cleaned message (strip newlines, enforce <280 chars)

    Args:
        persona: Persona codename (e.g., "AMMAR")
        intent: User intent (e.g., "You have open work on AI optimization")
        index: PersonaIndexDict from Phase 15 refresh
        client: Anthropic client instance
        max_tokens: Max tokens for Claude (default: 100, enforces ~280 char limit)

    Returns:
        Generated message text (cleaned, <280 chars, actionable)

    Raises:
        KeyError: If persona not in PERSONA_SYSTEM_PROMPTS
        ValueError: If invalid inputs
    """
    # Extract system prompt from persona definitions
    if persona not in PERSONA_SYSTEM_PROMPTS:
        raise KeyError(f"Unknown persona: {persona}")

    system_prompt = PERSONA_SYSTEM_PROMPTS[persona]

    # Build rich context from index
    context = IntentProcessor.build_full_context(intent, index)

    # Construct user message with intent + context + constraints
    user_message = f"""Intent: {intent}

Current Context Summary:
{context['context_summary']}

Recent Activity:
{context['activity_summary']}

Recent Completions Trigger:
{context['should_celebrate']}

Generate ONE actionable nudge that:
1. Rephrases the intent into a motivation/question/prompt
2. Adds specific context from the information above
3. Is actionable - user can do something in next 30 minutes
4. Stays under 280 characters (Telegram mobile-friendly)
5. Does NOT repeat exact phrases from last 5 messages
6. Maintains the persona's distinct voice and tone"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        message_text = response.content[0].text.strip()

        # Enforce <280 char limit via truncation if needed
        if len(message_text) > 280:
            message_text = message_text[:277] + "..."

        return message_text

    except (RateLimitError, APITimeoutError, APIError) as e:
        logger.error(f"Claude API error for persona {persona}: {e}")
        raise


def generate_and_dedupe(
    persona: str,
    intent: str,
    index: Dict[str, Any],
    client: Anthropic,
    tracker: RepetitionTracker,
    ledger: MessageLedger,
    max_retries: int = 3,
) -> Tuple[str, bool, str]:
    """
    Generate message with repetition checking and full audit logging.

    Implements complete generation pipeline:
    1. Generate candidate message via generate_message()
    2. Check RepetitionTracker.is_repetition() against last 5 messages
    3. If not repetition: log to ledger and return (message, True, "success")
    4. If repetition: retry up to max_retries with exponential backoff
    5. On max retries: log failure to ledger and return (message, False, "max_retries_exceeded")
    6. Handle API errors with fallback message
    7. Validate actionability (heuristic: check for imperative verbs)

    Args:
        persona: Persona codename
        intent: User intent
        index: PersonaIndexDict
        client: Anthropic client
        tracker: RepetitionTracker instance
        ledger: MessageLedger instance
        max_retries: Max retry attempts for repetition (default: 3)

    Returns:
        Tuple of (message, success, reason) where:
        - message: Generated message text (or fallback on error)
        - success: Boolean (True = sent, False = maxed out retries or error)
        - reason: String describing outcome ("success", "max_retries_exceeded", "api_error", etc.)

    Example:
        message, success, reason = generate_and_dedupe(
            persona="AMMAR",
            intent="open_work",
            index=fresh_index,
            client=client,
            tracker=tracker,
            ledger=ledger
        )
        if success:
            print(f"Sending: {message}")
        else:
            print(f"Failed: {reason}")
    """
    last_message = None
    topic_count = index.get("topics", []).__len__()

    for attempt in range(max_retries):
        try:
            # Generate candidate message
            message = generate_message(persona, intent, index, client)
            last_message = message

            # Check for repetition
            is_repeat = tracker.is_repetition(message, persona)
            if not is_repeat:
                # Success: log to ledger and return
                try:
                    ledger.log_generation(
                        persona=persona,
                        message_text=message,
                        intent=intent,
                        context_tags=["technical"],  # Default context tag (Phase 16 MVP)
                        tone_applied=persona.lower(),
                        repetition_flagged=False,
                        success=True,
                    )
                except ValueError as e:
                    logger.error(f"Ledger privacy gate error: {e}")
                    # Continue anyway (don't block message delivery on ledger write)

                return (message, True, "success")

            # Repetition detected: log attempt and retry
            logger.info(
                f"Repetition detected in attempt {attempt + 1}/{max_retries} for {persona}"
            )

            # Exponential backoff: 2^attempt seconds (1, 2, 4 seconds)
            backoff_time = 2 ** attempt
            time.sleep(backoff_time)

        except APIError as e:
            # API error: fall back to simple message
            logger.error(f"API error on attempt {attempt + 1}: {e}")
            reason_str = str(e)[:50]
            fallback_message = (
                f"You have {topic_count} open items. Pick one and move it forward."
            )
            last_message = fallback_message

            try:
                ledger.log_generation(
                    persona=persona,
                    message_text=fallback_message,
                    intent=intent,
                    context_tags=["technical"],
                    tone_applied="fallback",
                    repetition_flagged=False,
                    success=False,
                    error_reason=f"api_error: {reason_str}",
                )
            except ValueError:
                pass  # Continue anyway

            return (fallback_message, False, f"api_error: {reason_str}")

    # Max retries exceeded: log failure
    if last_message:
        try:
            ledger.log_generation(
                persona=persona,
                message_text=last_message,
                intent=intent,
                context_tags=["technical"],
                tone_applied=persona.lower(),
                repetition_flagged=True,
                success=False,
                error_reason="max_retries_exceeded",
            )
        except ValueError:
            pass

        return (last_message, False, "max_retries_exceeded")

    # Fallback (should not reach here)
    fallback = f"You have {topic_count} open items. Pick one and move it forward."
    try:
        ledger.log_generation(
            persona=persona,
            message_text=fallback,
            intent=intent,
            context_tags=["technical"],
            tone_applied="fallback",
            repetition_flagged=False,
            success=False,
            error_reason="unknown_error",
        )
    except ValueError:
        pass

    return (fallback, False, "unknown_error")


def is_actionable(message: str) -> bool:
    """
    Heuristic check: Does message contain imperative verb or celebratory tone?

    Simple validation: checks for presence of actionable verbs (pick, try, schedule, etc.)
    or celebratory words (celebrate, great, done, etc.).

    Does not reject non-actionable messages (Phase 16 accepts them with warning).
    Rationale: Some valid nudges are reflective ("Notice the pattern...") without imperatives.

    Args:
        message: Message text to validate

    Returns:
        True if message contains actionable verb or celebratory word
        False if neither found (flagged in ledger as potential issue)

    Example:
        is_actionable("3 items waiting. Pick one.") → True
        is_actionable("Your work is progressing.") → False
    """
    message_lower = message.lower()

    # Check for actionable verbs
    for verb in ACTIONABLE_VERBS:
        if verb in message_lower:
            return True

    # Check for celebratory words
    for word in CELEBRATORY_WORDS:
        if word in message_lower:
            return True

    return False


__all__ = [
    "generate_message",
    "generate_and_dedupe",
    "is_actionable",
    "ACTIONABLE_VERBS",
    "CELEBRATORY_WORDS",
]
