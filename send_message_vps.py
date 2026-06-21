#!/usr/bin/env python3
"""
NIZAM Persona Message Sender (for systemd timer execution)
Sends a persona-specific message via Telegram
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/nizamcore"))
os.chdir(os.path.expanduser("~/nizamcore"))

from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.env"))

from HIKMAH__knowledge_index.delivery import MessageIDGenerator, DeliveryLedger, TelegramRelayClient

def send_message(persona: str):
    """Send a message from specified persona to Telegram"""

    print(f"[{datetime.utcnow().isoformat()}] Sending message from {persona}...")

    try:
        gen = MessageIDGenerator()
        msg_id = gen.generate()

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        YOUR_TELEGRAM_ID = 8001780136

        if not token:
            print(f"[ERROR] TELEGRAM_BOT_TOKEN not configured")
            return False

        now_utc = datetime.utcnow().isoformat() + "Z"

        persona_messages = {
            "AMMAR": "3 items in your queue. Pick one and move it forward.",
            "HIKMAH": "Your work rhythm shows a pattern. Notice it?",
            "TARIQ": "Big picture question: what matters most right now?",
            "MUNAWARA": "This week: wins, draws, losses. What's your tally?",
            "MAL": "Financial runway check: can you sustain 3 months?",
            "BADAN": "Body metrics: sleep trend, HR, stress level?",
            "NAQD": "Before scaling: what's the smallest proof you need?",
            "SHURA": "Explain your blocker as if to a beginner. What's unclear?",
            "TAFRIGH": "What's weighing on you? No judgment. Just clarity.",
            "MARSAD": "Latest signal from the team: sentiment, blockers, wins?",
            "NIZAM": "You're stronger than you think. Trust yourself.",
        }

        message_text = persona_messages.get(persona, f"Nudge from {persona}")
        time_str = datetime.utcnow().strftime('%H:%M UTC')
        full_message = f"{message_text}\n\nFrom {persona}, {time_str}\nMsg ID: {msg_id}"

        relay = TelegramRelayClient(token=token)
        result = relay.send_message(chat_id=YOUR_TELEGRAM_ID, text=full_message)

        tg_msg_id = "scheduled"
        try:
            if isinstance(result, dict) and 'result' in result:
                tg_msg_id = result['result'].get('message_id', 'scheduled')
        except:
            pass

        ledger_path = Path(os.path.expanduser("~/DELIVERY_LEDGER.jsonl"))
        ledger = DeliveryLedger(ledger_path)

        ledger.log_delivery(
            message_id=msg_id,
            telegram_message_id=str(tg_msg_id),
            persona=persona,
            message_text=message_text,
            intent="scheduled_daily_nudge",
            sent_at=now_utc,
            delivered_at=now_utc,
            context_tags=["technical"],
            status="success"
        )

        print(f"[OK] {persona} message sent (ID: {msg_id}, Telegram: {tg_msg_id})")
        return True

    except Exception as e:
        print(f"[ERROR] {persona}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    persona = sys.argv[1] if len(sys.argv) > 1 else "AMMAR"
    success = send_message(persona)
    sys.exit(0 if success else 1)
