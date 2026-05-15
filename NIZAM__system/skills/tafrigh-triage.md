---
name: tafrigh-triage
module: TAFRIGH
trigger: "/tafrigh-triage"
source_folder: TAFRIGH__brain_dumper/raw/
target_folder: TAFRIGH__brain_dumper/triaged/
naming_pattern: "{YYYY-MM-DD}__triage.md"
buckets: [Now, Next, Later, Delete, Reflect, Escalate]
gates: [SUKOON, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Triage the latest brain dump(s) into 6 buckets. SUKOON gate FIRST — if distress flag in last 24h, suggest skipping triage and resting.

## Procedure

1. Read `SUKOON__recovery_first/overload_flags.jsonl`. If any flag in last 24h with `event_type: "overload_flag"` AND severity implied red, tell user: "Recovery signals red — recommend skipping triage today." Ask before continuing.
2. List undamuned items from latest `TAFRIGH__brain_dumper/raw/*.md` files (filter on `triaged: false` frontmatter or unmarked).
3. For each item, ask the user (or infer if explicitly delegated) to classify:
   - **Now** (today, <2 hours, high-leverage)
   - **Next** (this week)
   - **Later** (parking lot, revisit weekly)
   - **Delete** (not worth doing)
   - **Reflect** (route to SHURA/NAQD for thinking)
   - **Escalate** (route to a person — promise + deadline)
4. Write `TAFRIGH__brain_dumper/triaged/<YYYY-MM-DD>__triage.md` with 6 sections, frontmatter per schema.
5. Mark source dump frontmatter `triaged: true`.
6. Append a THABAT event:
   `{"ts":"<ISO8601_UTC>","actor":"TAFRIGH","skill":"/tafrigh-triage","gate":"THABAT","event":"dump_triaged","artifact":"<triage file>","source_dumps":[...]}`
7. Mirror one-liner to `log.md`.
