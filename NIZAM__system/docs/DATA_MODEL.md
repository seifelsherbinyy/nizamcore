# POP Data Model

> Every artifact POP produces fits one of a fixed set of types. This doc maps types to schemas to folders to skills.

## Artifact type catalog

| Type | Schema | Primary folder | Primary skill | Privacy |
|---|---|---|---|---|
| `brain_dump` | `note_frontmatter` | `TAFRIGH/raw/` | `/tafrigh-capture` | strict_local |
| (triage) | `note_frontmatter` | `TAFRIGH/triaged/` | `/tafrigh-triage` | strict_local |
| `brainstorm` | `note_frontmatter` | `SHURA/sessions/` | `/shura-brainstorm` | strict_local |
| `griller_session` | `note_frontmatter` | `NAQD/sessions/` | `/naqd-grill` | strict_local |
| `challenge` | `note_frontmatter` | `NAQD/sessions/` | `/naqd-challenge` | strict_local |
| `reconciliation` | `note_frontmatter` | `NAQD/sessions/` | `/naqd-reconcile` | strict_local |
| `recovery_signal` | `note_frontmatter` | `SUKOON/signals/` | `/sukoon-check` | strict_local |
| `conversational_session` | `conversational_session` | `YAWMIYAT/sessions/` | `/nizam-checkin`, `/nizam-counsel`, `/nizam-assess`, `/nizam-consult` | strict_local |
| `conversational_session_mirror` | `note_frontmatter` | `YAWMIYAT/mirrors/`, `YAWMIYAT/weekly/` | `/nizam-*`, `/nizam-almanac` | strict_local |
| `decision` | `decision_ledger` + `note_frontmatter` | `QARAR/` | `/qarar-decide` | review_before_commit |
| `learning` | `learning_ledger` | `HIKMAH/` (Phase 2) | (shell) | review_before_commit |
| `strategy_plan` (10/15/20yr) | `long_horizon_plan` | `TARIQ/{10,15,20}_year/` | `/tariq-vision` | strict_local |
| `strategy_plan` (annual review) | `note_frontmatter` | `TARIQ/reviews/annual/` | `/tariq-annual-review` | strict_local |
| `strategy_pivot` | `strategy_pivot` | `TARIQ/major_pivots/` | `/munawara-pivot` | strict_local |
| `strategy_plan` (1/3/5yr / quarter) | `tactical_plan` | `MUNAWARA/{1,3,5}_year/, quarters/` | `/munawara-quarter-plan` | strict_local |
| `battle` (weekly) | `note_frontmatter` | `MUNAWARA/weeks/` | `/munawara-weekly-battle` | strict_local |
| (battle outcome) | `battle_ledger` | `BATTLE_LEDGER.jsonl` | `/munawara-weekly-battle` | strict_local |
| `misc` (finance baseline) | `finance_baseline` | `MAL/baseline/` | `/mal-baseline` | strict_local |
| `milestone` | `finance_milestone` | `MAL/baseline/` | `/mal-milestone-check` | strict_local |
| `scenario` | `finance_scenario` | `MAL/scenario_models/` | `/mal-scenario` | strict_local |
| (exchange-rate snapshot) | inline | `MAL/exchange_rate_log.jsonl` | `/mal-exchange-rate-check` | strict_local |
| `body_signal` | `body_signal` | `BADAN/daily_signals/` | `/badan-daily-signal` | strict_local |
| `body_review` | `body_weekly_review` | `BADAN/weekly_reviews/` | `/badan-weekly-review` | strict_local |
| (red flag) | `body_red_flag` | `BADAN/red_flags/` | `/badan-red-flag-check` | strict_local |
| (event row) | `event_ledger` | `EVENT_LEDGER.jsonl` | (every skill appends) | review_before_commit |

## Universal frontmatter contract

Every markdown artifact has YAML frontmatter validated against `note_frontmatter.schema.json`. Minimum fields:

```yaml
---
type: <enum>
pop_module: <enum>
pop_privacy: <enum>
updated: YYYY-MM-DD
confidence: speculative | low | medium | high
---
```

Plus optional: `sources`, `related` (wikilinks), `tags`, `recency_anchor`, `superseded_by`, `triaged`, `phase_2_target`.

## Universal ledger row contract

Every `.jsonl` row has these minimum fields:

```json
{
  "ts": "ISO8601 UTC with Z",
  "module": "<MODULE>",
  "event_type": "<verb_noun>"
}
```

Plus schema-specific fields per ledger.

## Cross-references (wikilinks)

POP uses `[[wikilinks]]` for cross-references between artifacts. Convention:
- Wikilink target = the artifact's filename without extension.
- Bidirectional backlinks are NOT auto-maintained — `/pop-health` audits for orphans.
- Wikilinks across phases respected (e.g., a SHURA session can `[[TARIQ 10-yr vision]]`).

## Identifiers

| ID type | Format | Example |
|---|---|---|
| Filesystem timestamp | `YYYY-MM-DDTHH-MM-SSZ` | `2026-05-15T14-17-30Z` |
| ISO timestamp in JSON | `YYYY-MM-DDTHH:MM:SSZ` | `2026-05-15T14:17:30Z` |
| ISO date | `YYYY-MM-DD` | `2026-05-15` |
| ISO week | `YYYY-Wnn` | `2026-W20` |
| Quarter | `YYYY-Qn` | `2026-Q2` |
| Month | `YYYY-MM` | `2026-05` |
| Person ID | slug (lowercase, no spaces) | `mom_seham` |
| Battle ID | slug | `negotiate_remote_role` |

## Schema versioning

Each schema file is committable. Major schema changes:
1. Snapshot existing schema to MAKHZAN.
2. Increment schema `$id` / version comment.
3. Document migration in CHANGELOG.
4. Run `/pop-health` to surface schema violations on existing artifacts.
5. Migrate or mark superseded.

## Privacy classifications (recap)

| Level | Meaning | Where it lives |
|---|---|---|
| `strict_local_maximum` | Never leaves disk; never syncs anywhere | Explicitly classified maximum-sensitivity records |
| `strict_local` | Never commits; on-disk only | TAFRIGH/raw, triaged, SHURA/sessions, NAQD/sessions, SUKOON/signals, MAL/**, BADAN/**, TARIQ content, MUNAWARA content, all P2/P3 ledgers, SOUL.md |
| `review_before_commit` | Committable only after manual review | ledgers (EVENT/DECISION/LEARNING), log.md |
| `private_github` | Default-committable in private repo | schemas, templates, skills, protocols, workflows, docs, personas, manifests |
| `mirror_curated_only` | Curated selection to Obsidian | NUR (Phase 2) |
| `mirror_sanitized_metadata_only` | Sanitized metadata only to Notion | JADWAL (Phase 2) |
| `sync_safe` | OK on any surface | (none in POP by default) |

## How `/pop-health` uses the data model

`/pop-health` runs schema validation against every markdown artifact's frontmatter and every JSONL row. Violations surface as actionable items in the health audit.

This audit is the operational guarantee that the data model remains coherent over time.

## See also
- [`MEMORY_MODEL.md`](MEMORY_MODEL.md)
- [`CONTINUITY_PROTOCOL.md`](CONTINUITY_PROTOCOL.md)
- [`SKILL_DESIGN_PRINCIPLES.md`](SKILL_DESIGN_PRINCIPLES.md)
