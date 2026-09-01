# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Proposed Schema Package

**Status:** proposed until reviewed in the canonical GitHub repository.

## Compatibility note

The extracted schemas retain the legacy `strict_local` privacy enum where it existed because the current governing NIZAM contract gives that value special semantics. In v0.2 architecture documentation, `strict_local` is explicitly interpreted as **VPS-only**, not workstation-local and not automatically Drive-synchronized. A future schema migration may replace ambiguous privacy names with explicit storage classes, but this package does not silently weaken an existing privacy gate.

## Proposed files

- `behavior_intervention.schema.json` — JSON Schema draft-07 proposal, schema version 0.2.0.
- `daily_agenda_plan.schema.json` — JSON Schema draft-07 proposal, schema version 0.2.0.
- `daily_health_feature_vector.schema.json` — JSON Schema draft-07 proposal, schema version 0.2.0.
- `health_hypothesis_record.schema.json` — JSON Schema draft-07 proposal, schema version 0.2.0.
- `health_source_event.schema.json` — JSON Schema draft-07 proposal, schema version 0.2.0.
- `journal_feature_record.schema.json` — JSON Schema draft-07 proposal, schema version 0.2.0.
