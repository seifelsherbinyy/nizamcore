---
name: sukoon-check
module: SUKOON
trigger: "/sukoon-check"
target_folder: SUKOON__recovery_first/signals/
naming_pattern: "{YYYY-MM-DD}.md"
template: NIZAM__system/templates/recovery_check.template.md
frontmatter_schema: NIZAM__system/schemas/note_frontmatter.schema.json
gates: [THABAT]
privacy: strict_local
flag_target: SUKOON__recovery_first/overload_flags.jsonl
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Log a recovery signal entry. Tracks sleep/energy/stress so SUKOON gate can make recovery-first downshift decisions later.

## Procedure

1. If a file already exists at `SUKOON__recovery_first/signals/<YYYY-MM-DD>.md`, ask user: "You already logged today. Update or add evening entry?"
2. Otherwise, prompt for each (each is optional; blanks allowed):
   - Sleep hours (last night)
   - Sleep quality (1–10)
   - Energy now (1–10)
   - Stress now (1–10)
   - Mood now (1–10)
   - One-line note about current state (optional)
3. Write to file with frontmatter:
   ```yaml
   ---
   type: recovery_signal
   pop_module: SUKOON
   pop_privacy: strict_local
   updated: <YYYY-MM-DD>
   confidence: high  # self-report
   ---
   ```
4. Determine flag color:
   - **red**: sleep < 5h OR stress ≥ 8 OR mood ≤ 3 OR energy ≤ 3
   - **yellow**: sleep 5–6h OR any single metric in concerning range
   - **green**: all metrics healthy
5. If red or yellow, append to `SUKOON__recovery_first/overload_flags.jsonl`:
   `{"ts":"<ISO8601_UTC>","module":"SUKOON","privacy_level":"strict_local","event_type":"overload_flag","severity":"red|yellow","summary":"<one line>","source":"<signal file>","next_action":"downshift planning load"}`
6. Append THABAT event to `EVENT_LEDGER.jsonl`. Mirror sanitized one-liner to `log.md` ("SUKOON signal logged — green/yellow/red"; no metric values in log.md).
