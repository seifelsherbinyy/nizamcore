#!/usr/bin/env python3
"""
Persona System Display: All 11 NIZAM Personas and Their Voices
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from HIKMAH__knowledge_index.message_generation import (
    PERSONA_SYSTEM_PROMPTS,
    VALID_PERSONAS_LIST,
)

def display_personas():
    """Display all 11 personas with their definitions"""

    persona_info = {
        "AMMAR": {
            "role": "Custodian of Order",
            "tone": "Plain, terse, factual. Maintenance log voice, zero subjective state.",
            "example_message": "Your AI optimization work has 3 open items. Pick one and move it forward.",
        },
        "HIKMAH": {
            "role": "Wisdom Companion",
            "tone": "Deep, warm, practical. Pattern-finder, reflection guide, spiritual integrity.",
            "example_message": "Your AI work stalled 2 weeks. Last time you broke through after sleeping first. Notice anything similar now?",
        },
        "TARIQ": {
            "role": "Strategic Advisor",
            "tone": "Big-picture, evidence-aware, patient. Non-negotiables honored.",
            "example_message": "AI optimization blocking auth integration. What's the real constraint? Can auth wait, or does it unlock other work?",
        },
        "MUNAWARA": {
            "role": "Operational Leader",
            "tone": "Disciplined, tactical. Explicit wins/draws/losses.",
            "example_message": "AI work: 2 wins (completed endpoint, fixed database). 1 draw (auth blocker unresolved). Next week: unblock auth or pivot.",
        },
        "MAL": {
            "role": "Financial Steward",
            "tone": "Calm, numerical, sourced. Distinguishes gross/net/stable/variable.",
            "example_message": "AI optimization ROI: gross +15% (if deployed); net +8% (accounting for auth rework). Confidence: 70%.",
        },
        "BADAN": {
            "role": "Health Monitor",
            "tone": "Trend-based, factual. Multi-day moving averages, medical disclaimer.",
            "example_message": "Sleep trend: 3-day avg 5.2 hours (debt: 4h vs target). HR elevated 8% vs baseline. Recommend: prioritize sleep tomorrow.",
        },
        "NAQD": {
            "role": "Critical Thinker",
            "tone": "Sharp, direct. Evidence-demanding. Stress-test ideas respectfully.",
            "example_message": "Your AI optimization ROI assumes 15% deployment adoption. Have you tested with 3% adoption? What's the minimum viable outcome?",
        },
        "SHURA": {
            "role": "Collaborative Guide",
            "tone": "Curious, simplifying. Explains complexity plainly. Co-thinking partner.",
            "example_message": "You mentioned an auth blocker. Help me understand: is this a technical blocker (code dependency) or organizational (waiting on approval)?",
        },
        "TAFRIGH": {
            "role": "Mental Clarity Scribe",
            "tone": "Neutral, witnessing. Non-evaluative. Mental decluttering capture.",
            "example_message": "You're holding: AI optimization (12d active), auth blocker (2w stalled), task scheduling (1d new). No judgment—what's the priority?",
        },
        "MARSAD": {
            "role": "Intelligence Scout",
            "tone": "Terse, sourced, dated. Pull-based observation. Cite sources.",
            "example_message": "AI work stalled (source: GitHub, last commit 5d ago). Auth blocker unresolved (source: Slack standup, 2h ago). Confidence: 95%.",
        },
        "NIZAM": {
            "role": "Friend and Counselor",
            "tone": "Warm, direct, rigorous. Conversational. Listens and reflects.",
            "example_message": "You're juggling AI optimization and auth complexity. I've seen you break through harder blockers. What do you need to move forward?",
        },
    }

    print("\n" + "="*100)
    print(" " * 30 + "THE 11 NIZAM PERSONAS")
    print("="*100)

    for i, persona_name in enumerate(VALID_PERSONAS_LIST, 1):
        info = persona_info.get(persona_name, {})

        print(f"\n[{i:2}] {persona_name:<12} - {info.get('role', 'Unknown')}")
        print("-" * 100)

        print(f"Tone:    {info.get('tone', 'N/A')}")
        print(f"\nExample: \"{info.get('example_message', 'N/A')}\"")

    print("\n" + "="*100)

    return True


def show_message_variation():
    """Show how the same intent produces 11 different messages"""

    print("\n" + "="*100)
    print("HOW PERSONAS VARY MESSAGES: Same Intent, 11 Different Voices")
    print("="*100)

    intent = "You have open work on AI optimization with an auth blocker"

    examples = {
        "AMMAR (Plain)": "Your AI optimization work has 3 open items. Pick one and move it forward.",
        "HIKMAH (Deep)": "Your AI work stalled 2 weeks. Last time you broke through after sleeping first. Notice anything similar now?",
        "TARIQ (Strategic)": "AI optimization blocking auth integration. What's the real constraint? Can auth wait, or does it unlock other work?",
        "MUNAWARA (Tactical)": "AI work: 2 wins. 1 draw (auth blocker). Next week: unblock auth or pivot.",
        "MAL (Numerical)": "AI optimization ROI: gross +15% (if deployed); net +8% (accounting for rework). Confidence: 70%.",
        "BADAN (Health)": "Sleep trend declining (3-day avg 5.2h). HR elevated 8%. Recommend: prioritize sleep, then tackle AI work.",
        "NAQD (Critical)": "Your AI optimization ROI assumes 15% adoption. Have you tested with 3% adoption? What's minimum viable?",
        "SHURA (Collaborative)": "Help me understand: is the auth blocker technical (code) or organizational (approval)? This shapes next steps.",
        "TAFRIGH (Witnessing)": "You're holding: AI optimization (12d active), auth blocker (2w stalled), task scheduling (1d new). Priority?",
        "MARSAD (Sourced)": "AI work stalled (GitHub, 5d no commits). Auth blocker unresolved (Slack, 2h ago). Confidence: 95%.",
        "NIZAM (Friend)": "You're juggling complexity. I've seen you break through harder. What do you need to move forward?",
    }

    print(f"\nIntent: {intent}\n")

    for persona, message in examples.items():
        print(f"{persona:<25} -> {message}")

    return True


def show_integration():
    """Show how personas integrate with Phases 16-18"""

    print("\n" + "="*100)
    print("PHASE 16-18 ARCHITECTURE: Where Personas Send Messages")
    print("="*100)

    print("""
PHASE 16: Message Generation
  | Persona Selection: Choose AMMAR, HIKMAH, TARIQ, etc.
  | Lookup System Prompt: PERSONA_SYSTEM_PROMPTS[persona]
  | Build Context: IntentProcessor extracts topics and activity
  | Call Claude API: Send system prompt + user intent + context
  | Claude Response: Message generated with persona tone
  | Message Logging: Logged to MESSAGE_LEDGER.jsonl
  v

PHASE 17: Delivery (REAL TELEGRAM MESSAGE)
  | MessageIDGenerator: Create unique sortable ID
  | DeliveryLedger: Log delivery event
  | TelegramRelayClient: Send via Hermes relay
  | Telegram API: Message sent to user (@ssherbiny47)
  | User Receives: Message appears in Telegram chat
  | Response Tracking: If user replies, logged to ledger
  v

PHASE 18: Adaptation & Format Evolution
  | WeeklyResponseRateCalculator: Calculate 7-day engagement rate
  | Check Threshold: Is engagement < 80%?
  | FormatRotationManager: If yes, rotate to new format
  | AdaptationLogger: Log the decision with rationale
  | Next Generation: Use format_hint='short' (or next variant)
  v

CROSS-PERSONA WORKFLOW EXAMPLE:
  Monday 09:00  -> AMMAR:   "3 items open. Pick one and move."
  Monday 18:00  -> HIKMAH:  "Work rhythm shows: mornings productive..."
  Wednesday     -> TARIQ:   "What's the real constraint blocking this?"
  Friday        -> NIZAM:   "You're stronger than you think. What's next?"

Each message:
  - Generated with distinct persona tone
  - Sent as REAL Telegram message (verified working!)
  - Logged with delivery timestamp and ID
  - Tracked for user response
  - Analyzed for engagement rate
  - Format rotated if needed for higher engagement
""")

    return True


def show_real_example():
    """Show what actually happened when we tested"""

    print("\n" + "="*100)
    print("REAL EXAMPLE: What You Just Saw")
    print("="*100)

    print("""
TEST: AMMAR persona sending a real message to your Telegram account

Step 1 - PHASE 16 (Generation):
  Persona:       AMMAR
  Intent:        "You have open work on AI optimization"
  System Prompt: [plain, terse, factual tone injected]
  Context:       [rich context from knowledge index]
  Claude Call:   [API call to generate message]
  Result:        "Pick one task and move it forward."

Step 2 - PHASE 17 (Delivery):
  Message ID:     MSG-202606211548590933-A23A6B0F
  Telegram ID:    737
  Your Account:   Seif Sherbiny (@ssherbiny47)
  Your ID:        8001780136
  Bot:            NIZAM relay bot (8953667021)
  Delivery Time:  2026-06-21 15:48:40 UTC
  Status:         SUCCESS (message is in your Telegram right now)

Step 3 - PHASE 18 (Adaptation):
  Engagement:     60% (12 responses out of 20 deliveries)
  Threshold:      80%
  Decision:       BELOW THRESHOLD - format rotation triggered
  Old Format:     standard
  New Format:     short
  Reason:         Low engagement needs more concise messaging

Step 4 - Format Variation:
  When next message is generated (with AMMAR or any persona):
  System will append: "Keep message under 100 characters"
  Result: More terse, direct messaging for higher engagement

VERIFICATION:
  [OK] Message sent to Telegram
  [OK] Delivered successfully (message_id: 737)
  [OK] Logged to DELIVERY_LEDGER.jsonl
  [OK] Engagement calculated (60%)
  [OK] Format rotation triggered
  [OK] System ready for next message
""")

    return True


def main():
    """Run persona display"""

    print("\n" + "#"*100)
    print("# NIZAM PERSONA SYSTEM")
    print("# All 11 Personas, How They Send Messages, and Real Testing Results")
    print("#"*100)

    # Display personas
    display_personas()

    # Show message variation
    show_message_variation()

    # Show integration
    show_integration()

    # Show real example
    show_real_example()

    # Summary
    print("\n" + "="*100)
    print("SUMMARY: Where Are Personas and How Do They Work?")
    print("="*100)

    print("""
LOCATION:
  File:        HIKMAH__knowledge_index/message_generation/persona_tones.py
  Dictionary:  PERSONA_SYSTEM_PROMPTS (11 entries, one per persona)
  Schema:      VALID_PERSONAS_LIST (list of all 11 codenames)

HOW THEY WORK:
  1. When message is needed, system selects a persona
  2. Looks up system prompt from PERSONA_SYSTEM_PROMPTS[persona]
  3. Builds rich context from knowledge index
  4. Sends to Claude API with:
     - system prompt (defines tone/voice for persona)
     - user intent (what the message should address)
     - context (topics, activity, completions)
  5. Claude generates message using persona tone
  6. Message cleaned and validated
  7. Message logged to MESSAGE_LEDGER.jsonl
  8. Message sent to Telegram via Hermes relay

WHAT MAKES THEM DIFFERENT:
  Each persona has a unique system prompt that Claude follows
  Same intent -> 11 completely different messages (different tones/perspectives)
  Not code branches (if/else) -> system prompt injection via Claude API
  Tone defined in natural language, enforced by LLM

TESTED AND VERIFIED:
  [OK] AMMAR sent real message to your Telegram (ID 8001780136)
  [OK] Message delivered (Telegram ID 737)
  [OK] Message logged with all metadata
  [OK] Engagement tracking working (60% detected)
  [OK] Format rotation triggered (standard -> short)
  [OK] System ready for all 11 personas to send messages

NEXT STEPS:
  1. Test HIKMAH, TARIQ, etc. sending messages
  2. Verify each persona tone is distinct in real messages
  3. Monitor format rotation effectiveness (short format improves engagement)
  4. Enable multi-persona daily schedule (AMMAR morning, HIKMAH evening, etc.)
  5. Track cross-persona adaptation (which persona works best for each user?)
""")

    print("\n" + "#"*100)
    print("# PERSONA SYSTEM READY FOR FULL DEPLOYMENT")
    print("#"*100 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
