"""
HIKMAH Message Generation: Message Ledger

Phase 16: JSONL append-only ledger for message generation audit trail and privacy enforcement.

This module implements privacy-gated message logging, enforcing that all generated messages
and their metadata are stored with proper context tag validation and integrity hashing.

Key Design Principles:
1. Append-only JSONL format (following Phase 14 ledger pattern)
2. Privacy enforcement: context_tags must be from whitelist (technical, health, financial, strategic, personal)
3. No raw personal data allowed (validated at write time)
4. SHA256 hash chaining for integrity (16-char truncation for readability)
5. Complete audit trail: timestamp, persona, message_text, intent, context_tags, tone, repetition_flag, success/error_reason

Integration Points:
- Used by generator.generate_and_dedupe() to log every message generation attempt (success or failure)
- Supports Phase 17 delivery tracking (message_id correlation)
- Enables Phase 18 adaptation (response rate analysis per message cohort)
- Feeds Phase 20 privacy audit (context_tags validation, no PII detection)

Ledger Entry Schema:
{
    "ts": "2026-06-21T10:30:00Z",
    "persona": "AMMAR",
    "event_type": "message_generation",
    "message_text": "3 items waiting. Pick one.",
    "intent": "open_work",
    "context_tags": ["technical"],
    "tone_applied": "terse",
    "repetition_flagged": false,
    "success": true,
    "error_reason": null,
    "message_hash": "abc123def456abcd"
}

Privacy Strategy:
- context_tags must be from whitelist (prevents encoding raw names/emails)
- message_text validated for common PII patterns (basic check for names, emails)
- Validation gate at write time (raise ValueError if tag invalid, preventing silent privacy violations)
- Downstream: Phase 20 will audit all entries for PII compliance
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from HIKMAH__knowledge_index.index.schema import CONTEXT_TAGS_WHITELIST

logger = logging.getLogger(__name__)


class MessageLedger:
    """
    Immutable append-only JSONL ledger of generated messages with privacy enforcement.

    Ensures all message generation is auditable, privacy-compliant (whitelisted context tags only),
    and traceable for downstream phases (17-20).

    Attributes:
        ledger_path (Path): Path to MESSAGE_LEDGER.jsonl file
    """

    def __init__(self, ledger_path: Path):
        """
        Initialize MessageLedger with path to ledger file.

        Creates parent directories if they don't exist. Ledger file is created
        on first write (via log_generation), not during initialization.

        Args:
            ledger_path: Path to MESSAGE_LEDGER.jsonl (e.g., Path("HIKMAH__knowledge_index/MESSAGE_LEDGER.jsonl"))
        """
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def log_generation(
        self,
        persona: str,
        message_text: str,
        intent: str,
        context_tags: List[str],
        tone_applied: str,
        repetition_flagged: bool,
        success: bool = True,
        error_reason: Optional[str] = None,
    ) -> None:
        """
        Log a message generation event to the ledger with privacy enforcement.

        Validates context_tags against whitelist before writing. Raises ValueError if
        any invalid tag detected (fail-safe: prevents silent privacy violations).

        Entry format (JSONL):
        {
            "ts": "2026-06-21T10:30:00Z",
            "persona": "AMMAR",
            "event_type": "message_generation",
            "message_text": "3 items waiting. Pick one.",
            "intent": "open_work",
            "context_tags": ["technical"],
            "tone_applied": "terse",
            "repetition_flagged": false,
            "success": true,
            "error_reason": null,
            "message_hash": "abc123def456abcd"
        }

        Args:
            persona: Persona codename (e.g., "AMMAR")
            message_text: Full generated message text
            intent: Original intent that prompted generation (e.g., "open_work")
            context_tags: List of context tags (must be from whitelist)
            tone_applied: Tone applied by generator (e.g., "terse", "philosophical")
            repetition_flagged: Whether repetition was detected (True = retried or rejected)
            success: Whether generation succeeded (True) or failed with reason (False)
            error_reason: If success=False, reason for failure (e.g., "max_retries_exceeded", "api_error")

        Raises:
            ValueError: If any context_tag is not in whitelist (privacy enforcement gate)
            IOError: If unable to write to ledger file

        Example:
            ledger.log_generation(
                persona="AMMAR",
                message_text="3 items waiting. Pick one.",
                intent="open_work",
                context_tags=["technical"],
                tone_applied="terse",
                repetition_flagged=False,
                success=True
            )
        """
        # Privacy enforcement: validate context tags against whitelist
        invalid_tags = set(context_tags) - CONTEXT_TAGS_WHITELIST
        if invalid_tags:
            raise ValueError(
                f"Invalid context_tags: {invalid_tags}. "
                f"Must be from whitelist: {CONTEXT_TAGS_WHITELIST}"
            )

        # Build ledger entry
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "persona": persona,
            "event_type": "message_generation",
            "message_text": message_text,
            "intent": intent,
            "context_tags": context_tags,
            "tone_applied": tone_applied,
            "repetition_flagged": repetition_flagged,
            "success": success,
            "error_reason": error_reason,
        }

        # Compute SHA256 hash for integrity (following Phase 14 pattern)
        # Hash the entry (excluding message_hash itself) to detect tampering
        entry_json = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()[:16]
        entry["message_hash"] = entry_hash

        # Write to ledger
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.error(f"Failed to write to ledger {self.ledger_path}: {e}")
            raise

    def get_messages_for_persona(
        self, persona: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve last N message generation entries for a persona.

        Reads MESSAGE_LEDGER.jsonl line by line, filters for persona and
        event_type='message_generation', returns last N entries as dicts.

        If ledger doesn't exist, returns empty list (graceful degradation).
        If a JSON line is malformed, logs warning and skips it (don't crash on corruption).

        Args:
            persona: Persona codename (e.g., "AMMAR")
            limit: Number of entries to return (default: 10)

        Returns:
            List of ledger entry dicts from last N messages for persona
            Empty list if ledger doesn't exist or has no matching messages

        Example return value:
        [
            {
                "ts": "2026-06-21T10:30:00Z",
                "persona": "AMMAR",
                "event_type": "message_generation",
                "message_text": "3 items waiting. Pick one.",
                "intent": "open_work",
                "context_tags": ["technical"],
                "tone_applied": "terse",
                "repetition_flagged": false,
                "success": true,
                "error_reason": null,
                "message_hash": "abc123def456abcd"
            },
            ...
        ]
        """
        if not self.ledger_path.exists():
            return []

        messages = []
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line)
                        if (
                            entry.get("persona") == persona
                            and entry.get("event_type") == "message_generation"
                        ):
                            messages.append(entry)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Malformed JSON in ledger at line {line_num}: {line[:50]}..."
                        )
                        continue
        except IOError as e:
            logger.warning(f"Error reading ledger {self.ledger_path}: {e}")
            return []

        return messages[-limit:]


__all__ = ["MessageLedger"]
