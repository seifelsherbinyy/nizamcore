# Khaldun Islamic Cosmic Wisdom Mode — Implementation Changelog

## Added

- Mode bundle under `NIZAM__system/modes/khaldun_islamic_cosmic_wisdom/` (charter, policies, registries, workflows, templates, test cases)
- Python runtime package `NIZAM__system/modes/khaldun/` (classifier, verification, validator, context linker, reminder composer)
- Hermes `/hikmah` command → Khaldun persona with charter injection
- Khaldun support in `persona_runtime.py` and `coordinator.py`
- Loop B Khaldun reminders in `message_builder.py` with dry-run logging
- Outbound gate `NIZAM_KHALDUN_OUTBOUND_APPROVED`
- Skills: `hikmah-weekly`, `hikmah-wisdom`, `hikmah-pattern-promote`, `hikmah-contradictions`
- `HIKMAH__weekly_synthesis/` scaffold

## Modified

- `HIKMAH.json`, `agent_personas.json`
- `islamic_reminder_config.json` (enabled, Khaldun agent)
- `scheduler.py` (Khaldun validation + outbound gate)
- `providers.py` (optional system_prompt)
- `TOOL_ACCESS_MATRIX.json`, `NIZAM_TEMPLE.json`
- `intent_exemplars.yaml`, `nizam_pilot_readiness.py`

## Unresolved

- Live web fetch for tafsir/hadith sources (registry is reference metadata)
- Full LLM-generated reminders (Loop B uses rule-based composer first)

## Next test prompts

- `/hikmah` then ask about expanding universe
- Enable Loop B dry-run and inspect `khaldun-reminders-dryrun.jsonl`
