---
name: munawara-weekly-battle
module: MUNAWARA
trigger: "/munawara-weekly-battle"
target_folder: MUNAWARA__tactical_strategy/weeks/
naming_pattern: "{YYYY-Wnn}.md"
template: NIZAM__system/templates/weekly_battle.template.md
gates: [SUKOON, THABAT]
privacy: strict_local
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/BATTLE_LEDGER.jsonl]
sukoon_downshift_rule:
  threshold_red_flags_in_7_days: 2
  action: "cut weekly battle load 50% and flag 'tactical load too high'"
---

## For future Claude

The Dynamic War Strategy protocol — applied weekly. Six steps. SUKOON downshift FIRST.

## Procedure

1. **SUKOON downshift check** — count red flags in `SUKOON__recovery_first/overload_flags.jsonl` last 7 days. If ≥ 2 red flags, cut intended battle count by 50% and add a `sukoon_downshift_triggered` event to BATTLE_LEDGER.
2. **Exploit opportunity** — what surfaced this week that wasn't planned? Promote (add as battle) or ignore (note + park)?
3. **Concentrate force** — what's the single biggest leverage move this week? Defend its time.
4. **Defend recovery** — what's threatening SUKOON? Downshift if amber/red.
5. **Retreat intelligently** — what battle is failing and should be abandoned without shame? Log a `strategic_retreat` event.
6. **Reallocate resources** — time / money / attention shifts.
7. **Update objectives** — quarter/month target adjustments with reasoning.
8. Write `MUNAWARA__tactical_strategy/weeks/{YYYY-Wnn}.md` with 7 sections matching steps 2–7 plus the SUKOON gate result.
9. For each battle outcome at week close, append to BATTLE_LEDGER:
   `{"ts": "...", "module": "MUNAWARA", "privacy_level": "strict_local", "event_type": "battle_outcome", "battle_id": "<slug>", "week_iso": "{YYYY-Wnn}", "outcome": "win|draw|loss|deferred", "evidence": "...", "next_maneuver": "...", "recovery_impact": "green|yellow|red", "summary": "..."}`
10. Mirror sanitized one-liner to `log.md`.
