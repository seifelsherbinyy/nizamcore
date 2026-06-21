#!/usr/bin/env python3
"""
NIZAM Persona Scheduling System

Each of the 11 personas sends 2 messages per day at different times.
No two personas send at the same time - fully distributed across 24 hours.

Schedule Design:
  - 11 personas × 2 messages/day = 22 messages/day total
  - Spread across 24 hours in 1-hour intervals starting at 00:30
  - Each persona has 2 distinct send times
  - All scheduled via system cron/systemd timers
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple
import json
from pathlib import Path

# Persona metadata
PERSONAS = [
    "AMMAR",      # 0  - Plain/Terse
    "HIKMAH",     # 1  - Deep/Warm
    "TARIQ",      # 2  - Strategic
    "MUNAWARA",   # 3  - Operational
    "MAL",        # 4  - Numerical
    "BADAN",      # 5  - Health
    "NAQD",       # 6  - Critical
    "SHURA",      # 7  - Collaborative
    "TAFRIGH",    # 8  - Witnessing
    "MARSAD",     # 9  - Intelligence
    "NIZAM",      # 10 - Friend
]

# Schedule: 22 time slots (2 per persona), every hour starting at 00:30
SCHEDULE_SLOTS = [
    ("00:30", 0, 1),   # AMMAR - First message
    ("01:30", 1, 1),   # HIKMAH - First message
    ("02:30", 2, 1),   # TARIQ - First message
    ("03:30", 3, 1),   # MUNAWARA - First message
    ("04:30", 4, 1),   # MAL - First message
    ("05:30", 5, 1),   # BADAN - First message
    ("06:30", 6, 1),   # NAQD - First message
    ("07:30", 7, 1),   # SHURA - First message
    ("08:30", 8, 1),   # TAFRIGH - First message
    ("09:30", 9, 1),   # MARSAD - First message
    ("10:30", 10, 1),  # NIZAM - First message
    ("11:30", 0, 2),   # AMMAR - Second message
    ("12:30", 1, 2),   # HIKMAH - Second message
    ("13:30", 2, 2),   # TARIQ - Second message
    ("14:30", 3, 2),   # MUNAWARA - Second message
    ("15:30", 4, 2),   # MAL - Second message
    ("16:30", 5, 2),   # BADAN - Second message
    ("17:30", 6, 2),   # NAQD - Second message
    ("18:30", 7, 2),   # SHURA - Second message
    ("19:30", 8, 2),   # TAFRIGH - Second message
    ("20:30", 9, 2),   # MARSAD - Second message
    ("21:30", 10, 2),  # NIZAM - Second message
]

def display_schedule_table():
    """Display 24-hour schedule in table format"""

    print("\n" + "="*120)
    print("NIZAM PERSONA SCHEDULE: 11 Personas × 2 Messages/Day (22 Total)")
    print("="*120)

    print("\nEach persona sends at 2 distinct times, no overlap.\n")

    print("{:<8} {:<15} {:<30} {:<50}".format("Time", "Persona", "Type (1st/2nd)", "Voice Characteristic"))
    print("-"*120)

    persona_descriptions = {
        "AMMAR": "Plain/Terse - Facts only, maintenance log",
        "HIKMAH": "Deep/Warm - Patterns and reflection",
        "TARIQ": "Strategic/Patient - Big-picture thinking",
        "MUNAWARA": "Operational - Wins/losses, tactical",
        "MAL": "Numerical - Financial metrics",
        "BADAN": "Health/Factual - Trend-based health data",
        "NAQD": "Sharp/Critical - Evidence-demanding",
        "SHURA": "Curious/Simplifying - Collaborative",
        "TAFRIGH": "Neutral/Witnessing - Non-evaluative",
        "MARSAD": "Intelligence - Sourced observations",
        "NIZAM": "Conversational - Warm friend",
    }

    for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
        persona = PERSONAS[persona_idx]
        msg_type = f"Message {msg_num}/2"
        desc = persona_descriptions.get(persona, "Unknown")
        print("{:<8} {:<15} {:<30} {:<50}".format(time_slot, persona, msg_type, desc))

    print("\n" + "="*120)
    return True


def display_persona_schedule():
    """Display schedule from each persona's perspective"""

    print("\n" + "="*100)
    print("PERSONA PERSPECTIVES: When Each Persona Sends (UTC)")
    print("="*100 + "\n")

    # Group by persona
    persona_times = {}
    for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
        persona = PERSONAS[persona_idx]
        if persona not in persona_times:
            persona_times[persona] = []
        persona_times[persona].append((time_slot, msg_num))

    # Display each persona's schedule
    for persona in PERSONAS:
        times = persona_times[persona]
        times_str = " and ".join([f"{t[0]} (msg {t[1]})" for t in sorted(times)])
        print(f"{persona:<12} -> {times_str}")

    print("\n" + "="*100)
    return True


def display_daily_flow():
    """Display flow of messages throughout the day"""

    print("\n" + "="*120)
    print("HOURLY MESSAGE FLOW (UTC, One Message Per Hour)")
    print("="*120 + "\n")

    print("Time      | Persona    | Message # | Schedule")
    print("-"*120)

    for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
        persona = PERSONAS[persona_idx]
        if msg_num == 1:
            schedule_note = "FIRST MESSAGE OF THE DAY"
        else:
            schedule_note = "SECOND MESSAGE OF THE DAY"

        print(f"{time_slot:9} | {persona:10} | {msg_num}/2     | {schedule_note}")

    print("\n" + "="*120)
    return True


def generate_cron_jobs():
    """Generate systemd timer specifications for each persona"""

    print("\n" + "="*100)
    print("SYSTEMD TIMER CONFIGURATION")
    print("="*100)
    print("\nEach persona gets a systemd user timer that triggers at scheduled times.\n")

    persona_times = {}
    for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
        persona = PERSONAS[persona_idx]
        if persona not in persona_times:
            persona_times[persona] = []
        persona_times[persona].append(time_slot)

    for persona in PERSONAS:
        times = persona_times[persona]
        time1, time2 = sorted(times)
        hour1, min1 = time1.split(":")
        hour2, min2 = time2.split(":")

        print(f"[Timer] {persona}-nudge.timer")
        print(f"  Description=NIZAM {persona} Daily Nudges (2x/day)")
        print(f"  OnCalendar=*-*-* {hour1}:{min1}:00")
        print(f"  OnCalendar=*-*-* {hour2}:{min2}:00")
        print(f"  Persistent=true")
        print(f"  [Install]")
        print(f"  WantedBy=timers.target")
        print()

    return True


def generate_cron_script():
    """Generate crontab entries for each persona"""

    print("\n" + "="*100)
    print("CRONTAB CONFIGURATION (Alternative to systemd)")
    print("="*100 + "\n")

    persona_times = {}
    for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
        persona = PERSONAS[persona_idx]
        if persona not in persona_times:
            persona_times[persona] = []
        persona_times[persona].append(time_slot)

    print("Add these to crontab (crontab -e):\n")

    for persona in PERSONAS:
        times = persona_times[persona]
        for time_slot in sorted(times):
            hour, minute = time_slot.split(":")
            print(f"{minute} {hour} * * * cd /home/nizam && python -m HIKMAH__knowledge_index.delivery.send_message --persona {persona} --intent daily_nudge")

    print("\n" + "="*100)
    return True


def generate_schedule_json():
    """Generate schedule as JSON for programmatic access"""

    schedule_data = {
        "name": "NIZAM Persona Messaging Schedule",
        "version": "1.0",
        "total_personas": len(PERSONAS),
        "messages_per_persona": 2,
        "total_messages_per_day": len(SCHEDULE_SLOTS),
        "timezone": "UTC",
        "schedule": []
    }

    for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
        persona = PERSONAS[persona_idx]
        schedule_data["schedule"].append({
            "time_utc": time_slot,
            "persona": persona,
            "message_number": msg_num,
            "message_type": "first_daily" if msg_num == 1 else "second_daily"
        })

    return schedule_data


def display_implementation():
    """Show how to implement the schedule in code"""

    print("\n" + "="*100)
    print("IMPLEMENTATION: How the System Uses This Schedule")
    print("="*100)

    print("""
The schedule is used by the NIZAM delivery orchestrator:

1. Hermes Cron Job (runs every minute):
   - Check current time (UTC)
   - Look up schedule for this minute
   - If scheduled persona match:
     * Generate message for that persona
     * Send via TelegramRelayClient
     * Log to DELIVERY_LEDGER.jsonl

2. Python Code Pattern:
   from persona_schedule import SCHEDULE_SLOTS, PERSONAS
   import datetime

   now = datetime.datetime.utcnow()
   current_time = now.strftime("%H:%M")

   for time_slot, persona_idx, msg_num in SCHEDULE_SLOTS:
       if time_slot == current_time:
           persona = PERSONAS[persona_idx]
           send_message_for_persona(persona, msg_num)

3. Systemd Timer Pattern:
   - One timer per persona (11 total)
   - Each timer has 2 OnCalendar entries (morning + afternoon)
   - Timers are persistent (survives reboots)
   - Each timer triggers send_message.service with persona env var

4. VPS Deployment:
   - Timers run on nizam@31.97.154.5
   - Messages sent via Hermes relay
   - Delivery logged to VPS DELIVERY_LEDGER.jsonl
   - Synced to local via Google Drive every hour

5. Format Adaptation:
   - After 7 days, WeeklyResponseRateCalculator computes engagement
   - If < 80%, FormatRotationManager changes format_hint
   - Next message from same persona uses new format
   - Example: AMMAR standard -> AMMAR short

Example Flow (2026-06-22):
  00:30 UTC -> AMMAR sends message #1 (standard format)
  01:30 UTC -> HIKMAH sends message #1 (standard format)
  02:30 UTC -> TARIQ sends message #1 (strategic perspective)
  ...
  11:30 UTC -> AMMAR sends message #2 (standard format, or SHORT if adapted)
  12:30 UTC -> HIKMAH sends message #2 (standard format, or adapted)
  ...
  21:30 UTC -> NIZAM sends message #2 (warm friend perspective)

  All 22 messages logged to DELIVERY_LEDGER.jsonl with timestamps
  User can see all personas' messages in Telegram thread
  System tracks responses and adapts formats over time
    """)

    return True


def main():
    """Display all schedule information"""

    print("\n" + "#"*120)
    print("# NIZAM PERSONA MESSAGING SCHEDULE")
    print("# 11 Personas × 2 Messages/Day = 22 Messages/Day (Distributed, No Conflicts)")
    print("#"*120)

    # Display all views
    display_schedule_table()
    display_persona_schedule()
    display_daily_flow()
    generate_cron_jobs()
    generate_cron_script()
    display_implementation()

    # Save schedule as JSON
    schedule_json = generate_schedule_json()
    schedule_file = Path("persona_schedule.json")
    with open(schedule_file, "w") as f:
        json.dump(schedule_json, f, indent=2)
    print(f"\n[OK] Schedule saved to {schedule_file}")

    # Print JSON structure
    print("\n" + "="*100)
    print("SCHEDULE JSON (for integration with other systems)")
    print("="*100)
    print(json.dumps(schedule_json, indent=2)[:500] + "...\n")

    print("\n" + "#"*120)
    print("# SCHEDULE READY FOR DEPLOYMENT")
    print("#"*120 + "\n")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
