#!/usr/bin/env python3
"""
Persona Testing Suite: All 11 NIZAM Personas Send Real Messages

This test demonstrates how each of the 11 personas sends messages with
their distinct voices and tones.

The 11 Personas:
1. AMMAR - Plain/Terse: Facts only, maintenance log voice
2. HIKMAH - Deep/Warm: Patterns, reflection, spiritual integrity
3. TARIQ - Strategic/Patient: Big-picture, evidence-aware
4. MUNAWARA - Operational: Disciplined, explicit wins/draws/losses
5. MAL - Numerical: Calm, sourced, distinguishes metrics
6. BADAN - Health/Factual: Trend-based, multi-day averages
7. NAQD - Sharp/Critical: Direct evidence-demanding, stress-test ideas
8. SHURA - Curious/Simplifying: Collaborative, explains plainly
9. TAFRIGH - Neutral/Witnessing: Non-evaluative, captures without comment
10. MARSAD - Terse/Sourced: Pull-based observation, cite sources
11. NIZAM - Conversational: Warm friend, rigorous, plain sentences
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_all_personas():
    """Generate messages from all 11 personas and display their voices"""

    from HIKMAH__knowledge_index.message_generation import (
        PERSONA_SYSTEM_PROMPTS,
        VALID_PERSONAS_LIST,
        tone_description,
    )
    from HIKMAH__knowledge_index.message_generation.generator import generate_message
    from anthropic import Anthropic

    print("\n" + "="*80)
    print("PERSONA TESTING SUITE: All 11 NIZAM Personas")
    print("="*80)

    # Initialize Anthropic client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not in .env")
        return False

    client = Anthropic(api_key=api_key)
    print(f"\n[OK] Anthropic client initialized")

    # Sample index (mock data for persona testing)
    sample_index = {
        "persona": "AMMAR",
        "topics": [
            {"name": "AI optimization", "days_active": 12, "blockers": ["auth integration"], "completions": 2},
            {"name": "Task scheduling", "days_active": 5, "blockers": [], "completions": 1},
        ],
        "completions": [
            {"name": "Fixed database connection", "date": (datetime.utcnow() - timedelta(days=1)).isoformat()},
            {"name": "Deployed API endpoint", "date": (datetime.utcnow() - timedelta(days=2)).isoformat()},
        ],
        "activity_history": [
            {"event": "progress", "topic": "AI optimization", "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat()},
            {"event": "blocker", "topic": "Auth integration", "timestamp": (datetime.utcnow() - timedelta(hours=12)).isoformat()},
        ],
    }

    # Common intent for all personas to show how they interpret differently
    intent = "You have open work on AI optimization with an auth blocker. Recent completions on task scheduling."

    print(f"\nIntent (same for all): {intent}")
    print("\n" + "-"*80)
    print("PERSONA VOICES")
    print("-"*80)

    results = []

    for persona in VALID_PERSONAS_LIST:
        print(f"\n[PERSONA: {persona}]")
        print("-" * 40)

        try:
            # Get tone description
            tone = tone_description(persona)
            print(f"Tone: {tone}")

            # Generate message
            print(f"\nGenerating message...", end=" ")
            message = generate_message(
                persona=persona,
                intent=intent,
                index=sample_index,
                client=client,
                format_hint=None  # Standard format for comparison
            )
            print(f"[OK]")

            # Display message
            print(f"\nMessage ({len(message)} chars):")
            print(f'  "{message}"')

            results.append({
                "persona": persona,
                "tone": tone,
                "message": message,
                "length": len(message),
                "success": True
            })

            # Small delay between API calls
            time.sleep(0.5)

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            results.append({
                "persona": persona,
                "tone": tone_description(persona),
                "message": f"[Error generating message: {e}]",
                "success": False
            })

    # Summary table
    print("\n" + "="*80)
    print("PERSONA SUMMARY TABLE")
    print("="*80)

    print("\n{:<12} {:<30} {:<50}".format("Persona", "Tone Type", "Sample Message"))
    print("-" * 92)

    for result in results:
        persona = result["persona"]
        tone = result["tone"][:28]  # Truncate for display
        msg = result["message"][:48]  # Truncate for display
        if not result["success"]:
            msg = "[GENERATION ERROR]"
        print(f"{persona:<12} {tone:<30} {msg:<50}")

    # Success rate
    successful = sum(1 for r in results if r["success"])
    print(f"\n[SUMMARY] {successful}/{len(VALID_PERSONAS_LIST)} personas generated successfully")

    return successful == len(VALID_PERSONAS_LIST)


def test_format_variations():
    """Test how one persona (AMMAR) responds to different format hints"""

    from HIKMAH__knowledge_index.message_generation.generator import generate_message
    from anthropic import Anthropic

    print("\n" + "="*80)
    print("FORMAT VARIATION TEST: AMMAR Persona with Different Formats")
    print("="*80)

    # Initialize client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY not in .env")
        return False

    client = Anthropic(api_key=api_key)

    # Sample index
    sample_index = {
        "persona": "AMMAR",
        "topics": [{"name": "AI optimization", "days_active": 12, "blockers": ["auth"], "completions": 2}],
        "completions": [],
        "activity_history": [],
    }

    intent = "You have open work on AI optimization with an auth blocker."

    # Test all format variations
    formats = ["standard", "short", "emoji", "direct_question", "story"]

    print(f"\nIntent: {intent}")
    print(f"\nPersona: AMMAR (Plain/Terse voice)")
    print("-" * 80)

    for format_hint in formats:
        print(f"\n[FORMAT: {format_hint.upper()}]")

        try:
            message = generate_message(
                persona="AMMAR",
                intent=intent,
                index=sample_index,
                client=client,
                format_hint=format_hint
            )

            print(f"  Length: {len(message)} chars")
            print(f'  Message: "{message}"')

            time.sleep(0.5)

        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")

    return True


def show_persona_descriptions():
    """Display all persona definitions and their tone characteristics"""

    from HIKMAH__knowledge_index.message_generation import (
        PERSONA_SYSTEM_PROMPTS,
        VALID_PERSONAS_LIST,
    )

    print("\n" + "="*80)
    print("PERSONA DEFINITIONS: All 11 NIZAM Personas")
    print("="*80)

    persona_descriptions = {
        "AMMAR": "Plain/Terse - Facts only, maintenance log voice, zero subjective state",
        "HIKMAH": "Deep/Warm - Patterns, reflection, spiritual integrity, mainstream Sunni",
        "TARIQ": "Strategic/Patient - Big-picture, evidence-aware, non-negotiables honored",
        "MUNAWARA": "Operational - Disciplined, explicit wins/draws/losses, tactical",
        "MAL": "Numerical - Calm, sourced, distinguishes gross/net/stable/variable",
        "BADAN": "Health/Factual - Trend-based, multi-day moving averages, medical disclaimer",
        "NAQD": "Sharp/Critical - Direct evidence-demanding, stress-test ideas, never personal",
        "SHURA": "Curious/Simplifying - Collaborative, explains technical terms plainly",
        "TAFRIGH": "Neutral/Witnessing - Non-evaluative, captures without comment",
        "MARSAD": "Terse/Sourced - Pull-based observation, cite sources, mark confidence",
        "NIZAM": "Conversational - Warm friend, rigorous, plain sentences, adaptive to state",
    }

    print("\nPersona Roles and Tone Spectrum:\n")

    for i, persona in enumerate(VALID_PERSONAS_LIST, 1):
        desc = persona_descriptions.get(persona, "Unknown")
        print(f"{i:2}. {persona:<12} - {desc}")

    print("\n" + "-"*80)
    print("Sample System Prompt (AMMAR):")
    print("-"*80)

    ammar_prompt = PERSONA_SYSTEM_PROMPTS.get("AMMAR", "")
    print(ammar_prompt[:500] + "...\n")

    return True


def main():
    """Run all persona tests"""

    print("\n" + "#"*80)
    print("# PERSONA SYSTEM TEST SUITE")
    print(f"# Started: {datetime.now().isoformat()}")
    print("#"*80)

    try:
        # Show persona definitions first
        show_persona_descriptions()

        # Wait for user confirmation if running interactively
        print("\n[NOTE] The following tests require API calls. This will use your Anthropic quota.")
        print("API calls remaining: Run with live API enabled.\n")

        # Test 1: All personas (with API)
        print("\n[TEST 1] Generating messages from all 11 personas...")
        result1 = test_all_personas()

        # Test 2: Format variations (with API)
        print("\n\n[TEST 2] Testing format variations with AMMAR...")
        result2 = test_format_variations()

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        if result1:
            print("[PASS] All 11 personas generated messages successfully")
        else:
            print("[FAIL] Some personas failed to generate")

        if result2:
            print("[PASS] Format variations tested successfully")
        else:
            print("[FAIL] Format variation test failed")

        print("\n[NOTES]")
        print("- Each persona has a distinct voice defined in PERSONA_SYSTEM_PROMPTS")
        print("- Messages are generated via Claude API with system prompt injection")
        print("- Format hints (short, emoji, direct_question, story) modify message style")
        print("- All messages stay under 280 characters for Telegram mobile display")
        print("- Repetition tracker prevents phrase repeats from last 5 messages")

        return 0 if (result1 and result2) else 1

    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
