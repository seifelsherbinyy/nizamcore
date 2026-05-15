---
name: qarar-decide
module: QARAR
trigger: "/qarar-decide <decision_topic>"
target_folder: QARAR__decisions/
naming_pattern: "{YYYY-MM-DD}__{slug}.md"
template: NIZAM__system/templates/adr_decision.template.md
gates: [SUKOON, THABAT]
privacy: review_before_commit
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/DECISION_LEDGER.jsonl]
---

## For future Claude

Capture a notable decision as an ADR (Architecture Decision Record). Title → status → context → decision → reasoning → alternatives → consequences → review date → confidence.

## Procedure

1. Read SHURA or NAQD session that produced the decision (if any) and link via `[[wikilinks]]`.
2. Run through the ADR template structure.
3. **Recovery cost field**: explicitly score whether executing this decision will spike SUKOON red.
4. **Review date**: when to re-evaluate. For major decisions, set 6–12 months out.
5. Write `QARAR__decisions/{YYYY-MM-DD}__{slug}.md`.
6. Append `event_type: "decision_recorded"` to DECISION_LEDGER with full reasoning + confidence.
7. Append THABAT event. Mirror title to `log.md` (no decision details if marked strict_local).
