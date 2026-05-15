---
name: shura-graduate
module: SHURA
trigger: "/shura-graduate <fragment>"
source_folder: TAFRIGH__brain_dumper/triaged/
target_promotion: HIKMAH__learnings/ (Phase 2) OR QARAR__decisions/ (Phase 2) OR INTAJ__output_engine/ (Phase 2)
fallback_phase_1_target: SHURA__brainstormer/sessions/
naming_pattern: "{YYYY-MM-DD}__graduate__{fragment-slug}.md"
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Promote an idea fragment into a full project, learning, or decision. In Phase 1, target folders are not yet built — write to SHURA sessions with a `phase_2_target` field noting where it will eventually move.

## Procedure

1. Read the fragment in its current location (typically a brain dump or session note).
2. Classify the promotion target:
   - **Project** → INTAJ__output_engine (Phase 2)
   - **Learning principle** → HIKMAH__learnings (Phase 2)
   - **Decision record** → QARAR__decisions (Phase 2)
3. Build the promotion artifact with: Objective → Success criteria → Constraints → Steps → Owner → Deadline → Recovery cost estimate.
4. Write to `SHURA__brainstormer/sessions/<YYYY-MM-DD>__graduate__<slug>.md` (Phase 1) with frontmatter including `phase_2_target: "<intended phase-2 folder>"`.
5. Append `[[wikilinks]]` to source fragment.
6. Append a THABAT event with `event: "fragment_graduated"`.
7. Tell the user where this will move once Phase 2 scaffolds the target folder.
