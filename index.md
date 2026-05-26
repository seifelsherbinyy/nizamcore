# POP — Page Catalog

Claude reads this FIRST in any POP session. Keep it curated and current.

## Orientation (root)
- [`SOUL.md`](SOUL.md) — Seif's identity, values, operating principles (gitignored)
- [`CRITICAL_FACTS.md`](CRITICAL_FACTS.md) — ~120 tokens always loaded
- [`POP_TEMPLE.json`](POP_TEMPLE.json) — master registry
- [`POP_MASTER_REGISTER.json`](POP_MASTER_REGISTER.json) — folder inventory + privacy
- [`log.md`](log.md) — human-readable activity timeline
- [`CHANGELOG.md`](CHANGELOG.md) — versioned change history

## NIZAM__system (00 — governance)
- [`NIZAM__system/SCHEMA_INDEX.json`](NIZAM__system/SCHEMA_INDEX.json) — all schemas
- [`NIZAM__system/personas/`](NIZAM__system/personas/) — 8 persona JSONs (NIZAM, TAFRIGH, SHURA, NAQD, KABIR_SHERBO, MUNAWARA, MAL, BADAN)
- [`NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md`](NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md) — portable conversational front-end prompt
- [`NIZAM__system/skills/`](NIZAM__system/skills/) — 35 POP slash-command skill files (Phase 1 + 2 + 3)
- [`NIZAM__system/protocols/`](NIZAM__system/protocols/) — 8 cadence-driven skill chains (daily/weekly/monthly/quarterly/annual/crisis/onboarding)
- [`NIZAM__system/workflows/`](NIZAM__system/workflows/) — 8 scenario-driven skill chains (idea-to-decision, finance-decision, etc.)
- [`NIZAM__system/PROTOCOLS_INDEX.json`](NIZAM__system/PROTOCOLS_INDEX.json) — machine-readable protocol registry
- [`NIZAM__system/WORKFLOWS_INDEX.json`](NIZAM__system/WORKFLOWS_INDEX.json) — machine-readable workflow registry
- [`NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`](NIZAM__system/policies/PRIVACY_CLASSIFICATION.json)
- [`NIZAM__system/policies/SYNC_POLICY.json`](NIZAM__system/policies/SYNC_POLICY.json)
- [`NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json`](NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json) — Drive mirror + Notion dual-write
- [`NIZAM__system/docs/DUAL_WRITE_GOVERNOR.md`](NIZAM__system/docs/DUAL_WRITE_GOVERNOR.md) — governor operator guide
- [`NIZAM__system/policies/TOOL_ACCESS_MATRIX.json`](NIZAM__system/policies/TOOL_ACCESS_MATRIX.json)
- [`NIZAM__system/ledgers/`](NIZAM__system/ledgers/) — 8 ledgers (EVENT, DECISION, LEARNING, STRATEGY, BATTLE, FINANCE, BODY, FAMILY)
- [`NIZAM__system/templates/`](NIZAM__system/templates/) — 28 markdown templates
- [`NIZAM__system/docs/`](NIZAM__system/docs/) — doctrine + memory/data-model docs ([`MEMORY_MODEL`](NIZAM__system/docs/MEMORY_MODEL.md), [`CONTINUITY_PROTOCOL`](NIZAM__system/docs/CONTINUITY_PROTOCOL.md), [`DATA_MODEL`](NIZAM__system/docs/DATA_MODEL.md))

## Cognitive modules (Phase 1)
- [`TAFRIGH__brain_dumper/`](TAFRIGH__brain_dumper/) — daily/twice-daily declutter
- [`SHURA__brainstormer/`](SHURA__brainstormer/) — co-think, vault-first research
- [`NAQD__brain_griller/`](NAQD__brain_griller/) — red-team, reconciliation

## Recovery (Phase 1)
- [`SUKOON__recovery_first/`](SUKOON__recovery_first/) — signals, overload flags

## Continuity (Phase 1)
- [`MAKHZAN__archive/`](MAKHZAN__archive/) — immutable timestamped snapshots
- [`HAJR__quarantine/`](HAJR__quarantine/) — uncertain / unclassified holding pen

## Strategic + Life Branches (Phase 2 — scaffolded with skills/schemas/templates; content awaits user fill)
- [`KABIR_SHERBO__long_horizon_strategy/`](KABIR_SHERBO__long_horizon_strategy/) — 10/15/20-yr Long War Map → [doctrine](NIZAM__system/docs/BIG_SHERBO_LONG_WAR_DOCTRINE.md)
- [`MUNAWARA__tactical_strategy/`](MUNAWARA__tactical_strategy/) — 1/3/5-yr → quarters → weeks → battles → [doctrine](NIZAM__system/docs/MUNAWARA_TACTICAL_DOCTRINE.md)
- [`MAL__financial_engine/`](MAL__financial_engine/) — $1.5k → $10k+ /mo milestone ladder → [doctrine](NIZAM__system/docs/MAL_FINANCIAL_LADDER.md)
- [`BADAN__body_health_system/`](BADAN__body_health_system/) — advisory health tracking → [doctrine](NIZAM__system/docs/BADAN_HEALTH_ADVISORY_NOTES.md)
- [`QARAR__decisions/`](QARAR__decisions/) — ADR-style decision records
- [`INTAJ__output_engine/`](INTAJ__output_engine/) — tasks / agendas / deliverables (shell only)
- [`YAWMIYAT__journaling/`](YAWMIYAT__journaling/) — structured journal + NIZAM conversational sessions (JSON + mirrors)
- [`HIKMAH__learnings/`](HIKMAH__learnings/) — crystallized insights (shell only)
- [`NUR__obsidian_vault/`](NUR__obsidian_vault/) — Obsidian mirror (shell only — pending install)
- [`JADWAL__notion_dashboards/`](JADWAL__notion_dashboards/) — Notion mirror; dual-write via [`nizam-governor`](NIZAM__system/skills/nizam-governor.md)
- [`HIFZ__github_version_control/`](HIFZ__github_version_control/) — repo automation (shell only)

## MARSAD — Flight Intelligence Module (additive, active)
- [`MARSAD__flight_radar/`](MARSAD__flight_radar/) — CAI-to-USA price monitoring pipeline (Business + Premium Economy, post-Ramadan 2027)
  - Skills: `/marsad-discover` → `/marsad-monitor` → `/marsad-alert` → `/marsad-forecast`
  - Entry point: `cd MARSAD__flight_radar && python -m radar.main <command>`
  - Data store: `data/flight_prices.json` (private_github — price time series, no credentials)
  - Alerts log: `alerts/radar_alerts.json` (strict_local — gitignored)

## Phase 3 — scaffolded + live
- [`AHEL__family_network/`](AHEL__family_network/) — strictest privacy family map → [doctrine](NIZAM__system/docs/AHEL_FAMILY_PRIVACY_RULES.md)
- [`BASIRA__future_visualization/`](BASIRA__future_visualization/) — graph/dashboard layer (shell only)
- See [`NIZAM__system/docs/SCHEDULED_AGENTS.md`](NIZAM__system/docs/SCHEDULED_AGENTS.md) for daily/weekly/quarterly automation design.
- See [`NIZAM__system/docs/CROSS_CLI_BUILD.md`](NIZAM__system/docs/CROSS_CLI_BUILD.md) for Codex/Gemini/OpenCode portability.
- See [`PHASE_2_FOLDERS.md`](NIZAM__system/docs/PHASE_2_FOLDERS.md) and [`PHASE_3_FOLDERS.md`](NIZAM__system/docs/PHASE_3_FOLDERS.md).
