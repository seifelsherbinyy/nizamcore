---
name: naqd-challenge
module: NAQD
trigger: "/naqd-challenge <claim>"
source_folders: [TAFRIGH__brain_dumper/triaged/, SHURA__brainstormer/sessions/, NAQD__brain_griller/sessions/]
target_folder: NAQD__brain_griller/sessions/
naming_pattern: "{YYYY-MM-DD}__challenge__{claim-slug}.md"
gates: [SUKOON, THABAT]
privacy: strict_local
emotional_state_check:
  source: SUKOON__recovery_first/overload_flags.jsonl
  window_hours: 24
  fallback_mode: supportive_reflection
---

## For future Claude

Argue against the user's claim using POP's OWN HISTORY. Quote prior notes that contradict the claim. Useful when the user is about to repeat a known mistake.

## Procedure

1. SUKOON emotional-state gate (same as `/naqd-grill`).
2. Grep POP for past notes referencing the claim or related topics.
3. Find concrete contradictions: prior decisions, learnings, or outcomes that argue against the current claim.
4. For each contradiction: quote verbatim, cite file + frontmatter `updated` date, score confidence.
5. End with: "Given X (from <file>, <date>), are you sure about Y now?"
6. Write to `NAQD__brain_griller/sessions/<YYYY-MM-DD>__challenge__<slug>.md` with frontmatter. Use `[[wikilinks]]` to source files.
7. Append THABAT event.
