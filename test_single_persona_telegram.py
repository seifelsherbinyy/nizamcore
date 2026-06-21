#!/usr/bin/env python3
"""
Test Individual Personas Sending Real Telegram Messages

This script lets you test any of the 11 personas sending a REAL message to your Telegram.

Usage:
  python test_single_persona_telegram.py AMMAR
  python test_single_persona_telegram.py HIKMAH
  python test_single_persona_telegram.py TARIQ
  etc.

Each persona generates a message with its distinct voice and sends it to your Telegram.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_persona_telegram(persona_name: str):
    """Test a single persona sending a real Telegram message"""

    from HIKMAH__knowledge_index.message_generation import VALID_PERSONAS_LIST
    from HIKMAH__knowledge_index.delivery import MessageIDGenerator, DeliveryLedger, TelegramRelayClient

    print("\n" + "="*80)
    print(f"PERSONA TELEGRAM TEST: {persona_name}")
    print("="*80)

    # Validate persona
    if persona_name not in VALID_PERSONAS_LIST:
        print(f"\n[ERROR] Unknown persona: {persona_name}")
        print(f"Valid personas: {', '.join(VALID_PERSONAS_LIST)}")
        return False

    print(f"\n[OK] Persona '{persona_name}' is valid")

    # Get credentials
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not in .env")
        return False

    YOUR_TELEGRAM_ID = 8001780136

    # Create message infrastructure
    gen = MessageIDGenerator()
    msg_id = gen.generate()

    print(f"[STEP 1] Generate message ID")
    print(f"  Message ID: {msg_id}")

    # Create relay client
    relay_client = TelegramRelayClient(token=token)
    print(f"\n[STEP 2] Initialize TelegramRelayClient")
    print(f"  [OK] Client ready")

    # Compose message specific to persona
    persona_messages = {
        "AMMAR": "3 items open. Pick one and move it forward.",
        "HIKMAH": "Your work rhythm shows: mornings productive, afternoons slow. Schedule accordingly?",
        "TARIQ": "What's the real constraint blocking progress? Financial? Technical? Time?",
        "MUNAWARA": "This week: 2 wins, 1 draw (auth blocker). Next week: unblock auth or pivot.",
        "MAL": "ROI modeling: gross +15% (if deployed), net +8% (accounting for rework). Confidence: 70%.",
        "BADAN": "Sleep trend: 3-day avg 5.2h (debt: 4h). HR elevated 8%. Recommend: prioritize sleep.",
        "NAQD": "Your ROI assumes 15% adoption. Have you tested 3% adoption scenarios?",
        "SHURA": "Is the auth blocker technical (code) or organizational (approval)? This shapes next steps.",
        "TAFRIGH": "You're holding: AI work (12d active), auth blocker (2w stalled), scheduling (1d new). Priority?",
        "MARSAD": "AI work stalled (GitHub, 5d no commits). Auth blocker unresolved (Slack, 2h ago). Confidence: 95%.",
        "NIZAM": "You're juggling complexity. I've seen you break through harder. What do you need?",
    }

    message_text = f"{persona_messages.get(persona_name, '[Unknown persona]')}\n\nFrom {persona_name}, {datetime.utcnow().strftime('%H:%M UTC')}\nID: {msg_id}"

    print(f"\n[STEP 3] Compose message")
    print(f"  Persona: {persona_name}")
    print(f"  Message:\n    {message_text}")

    # Send via Telegram relay
    print(f"\n[STEP 4] Send REAL message to Telegram (ID {YOUR_TELEGRAM_ID})")
    try:
        telegram_message_id = relay_client.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=message_text
        )
        print(f"  [OK] Message sent! Telegram ID: {telegram_message_id}")
        sent_at = datetime.utcnow().isoformat() + "Z"

    except Exception as e:
        print(f"  [ERROR] Failed to send: {e}")
        print(f"  Attempting to continue with logging...")
        telegram_message_id = "error"
        sent_at = datetime.utcnow().isoformat() + "Z"

    # Log delivery
    print(f"\n[STEP 5] Log delivery to DELIVERY_LEDGER.jsonl")
    ledger_path = Path("DELIVERY_LEDGER.jsonl")
    ledger = DeliveryLedger(ledger_path)

    ledger.log_delivery(
        message_id=msg_id,
        telegram_message_id=str(telegram_message_id),
        persona=persona_name,
        message_text=message_text,
        intent=f"Daily nudge from {persona_name}",
        sent_at=sent_at,
        delivered_at=sent_at,
        context_tags=["technical"],
        status="success" if telegram_message_id != "error" else "failed"
    )
    print(f"  [OK] Logged to DELIVERY_LEDGER.jsonl")

    # Display summary
    print(f"\n" + "="*80)
    print(f"SUMMARY: {persona_name} Telegram Test")
    print("="*80)
    print(f"""
Message ID:       {msg_id}
Telegram ID:      {telegram_message_id}
Persona:          {persona_name}
Your Account:     @ssherbiny47 (ID: {YOUR_TELEGRAM_ID})
Bot:              NIZAM relay bot (8953667021)
Time:             {sent_at}
Status:           {'SUCCESS' if telegram_message_id != 'error' else 'FAILED'}

The message should now be in your Telegram chat.

Next Steps:
  1. Check your Telegram to see the message from {persona_name}
  2. Optionally reply to it (response will be tracked)
  3. Test another persona:
     python test_single_persona_telegram.py HIKMAH
     python test_single_persona_telegram.py TARIQ
     etc.

All personas can be tested one at a time to verify their distinct voices.
    """)

    return True


def show_all_personas():
    """Display all 11 personas and their example messages"""

    from HIKMAH__knowledge_index.message_generation import VALID_PERSONAS_LIST

    print("\n" + "="*80)
    print("ALL 11 PERSONAS (Available for Testing)")
    print("="*80)

    personas_info = {
        "AMMAR": "Plain/Terse",
        "HIKMAH": "Deep/Warm",
        "TARIQ": "Strategic/Patient",
        "MUNAWARA": "Operational",
        "MAL": "Numerical",
        "BADAN": "Health/Factual",
        "NAQD": "Sharp/Critical",
        "SHURA": "Curious/Simplifying",
        "TAFRIGH": "Neutral/Witnessing",
        "MARSAD": "Terse/Sourced",
        "NIZAM": "Conversational",
    }

    print("\nRun any of these to test a persona:\n")

    for i, persona in enumerate(VALID_PERSONAS_LIST, 1):
        tone = personas_info.get(persona, "Unknown")
        print(f"  {i:2}. python test_single_persona_telegram.py {persona:<12} # {tone}")

    return True


def main():
    """Run persona Telegram test"""

    if len(sys.argv) < 2:
        print("\n" + "#"*80)
        print("# NIZAM PERSONA TELEGRAM TEST")
        print(f"# Test any of the 11 personas sending a real message to your Telegram")
        print("#"*80)

        show_all_personas()

        print(f"\n\nUsage: python test_single_persona_telegram.py <PERSONA>")
        print(f"\nExample: python test_single_persona_telegram.py AMMAR")
        print(f"\nEach persona will send a distinct message to your Telegram account.")
        print(f"Messages will be logged to DELIVERY_LEDGER.jsonl for tracking.")

        return 0

    persona = sys.argv[1].upper()
    return 0 if test_persona_telegram(persona) else 1


if __name__ == "__main__":
    sys.exit(main())
