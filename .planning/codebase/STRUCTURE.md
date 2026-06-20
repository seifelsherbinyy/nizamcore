# Codebase Structure

**Analysis Date:** 2026-06-14

## Directory Layout

```
D:/NIZAM/                                   ← canonical source of truth (local working tree)
│
├── CRITICAL_FACTS.md                       ← ~120 tokens; loaded first in every session
├── SOUL.md                                 ← identity / values (strict_local, gitignored)
├── index.md                                ← page catalog; read second in every session
├── log.md                                  ← human-readable activity timeline (review_before_commit)
├── NIZAM_TEMPLE.json                       ← master commandments, gate definitions, module registry
├── NIZAM_MASTER_REGISTER.json              ← folder inventory with privacy classifications
├── AGENTS.md                               ← agent onboarding notes
├── CHANGELOG.md                            ← versioned change history
├── user.md                                 ← operator profile (review_before_commit)
├── user_deep.md                            ← deep operator profile (strict_local)
├── pytest.ini                              ← test runner config
├── requirements.txt / requirements-dev.txt ← Python dependencies
│
├── NIZAM__system/                          ← Phase 0: governance kernel
│   ├── AGENT_MAPPING.json                  ← conceptual agent → repo artifact map
│   ├── PROTOCOLS_INDEX.json                ← machine-readable protocol registry
│   ├── SCHEMA_INDEX.json                   ← all schemas indexed
│   ├── WORKFLOWS_INDEX.json                ← machine-readable workflow registry
│   ├── agent_personas.json                 ← codename override layer (codename → persona file)
│   ├── pillar_registry.json                ← single source of truth for pillar naming
│   ├── _index.json                         ← self-registration to NIZAM_MASTER_REGISTER
│   │
│   ├── config/                             ← router + intent config
│   │   ├── nizam_router.py                 ← IR-1..IR-8 deterministic resolver (stdlib only)
│   │   ├── router.config.yaml              ← routing thresholds, intent targets, commands
│   │   ├── intent_exemplars.yaml           ← Jaccard exemplar lists per bucket
│   │   ├── agents.registry.yaml            ← codename → model / gates / delegates
│   │   ├── extraction.config.yaml          ← extraction pipeline config
│   │   └── fixtures/                       ← router dry-run test fixtures (jsonl)
│   │
│   ├── governor/                           ← privacy + cost + persistence enforcement
│   │   ├── classifier.py                   ← privacy classification + egress matrix
│   │   ├── sync_arbiter.py                 ← cross-plane write arbitration
│   │   ├── ledger_writer.py                ← sole writer for all JSONL ledgers (hash-chained)
│   │   ├── kill_switch.py                  ← NIZAM_KILL_ALL=1 panic stop
│   │   ├── cost_ceiling.py                 ← $50 soft / $300 hard monthly budget
│   │   ├── strategy_sth.py                 ← RFC 6962 Merkle STH for STRATEGY_LEDGER
│   │   ├── trace.py                        ← trace utilities
│   │   ├── utils.py                        ← shared helpers
│   │   ├── scripts/
│   │   │   ├── pre_commit_check.py         ← git pre-commit HIMAYAH enforcement
│   │   │   └── install_pre_commit_hook.py  ← hook installer
│   │   └── tests/                          ← governor test suite
│   │
│   ├── relay/                              ← Telegram / Hermes ingestion layer
│   │   ├── poller.py                       ← Hermes long-poll runner (main entry point)
│   │   ├── coordinator.py                  ← pipeline orchestrator (B4.4–B4.7)
│   │   ├── auth.py                         ← user_id whitelist enforcement
│   │   ├── dedup.py                        ← update_id deduplication
│   │   ├── sukoon_gate.py                  ← SUKOON pre-gate (reads overload_flags.jsonl)
│   │   ├── persona_runtime.py              ← provider-neutral LLM runtime
│   │   ├── persona_prompt.py               ← system prompt builder per persona
│   │   ├── providers.py                    ← LLM provider adapters
│   │   ├── gateway.py                      ← envelope builder
│   │   ├── env_loader.py                   ← .env loader
│   │   ├── runtime_events.py               ← runtime event persistence
│   │   ├── telemetry.py                    ← telemetry export
│   │   ├── webhook.py                      ← webhook alternative (not default)
│   │   ├── .state/                         ← relay runtime state (gitignored)
│   │   └── tests/                          ← relay test suite
│   │
│   ├── companion/                          ← proactive / companion subsystems
│   │   ├── capture.py                      ← raw inbound capture persistence
│   │   ├── context.py                      ← context management
│   │   ├── gateway.py                      ← envelope construction
│   │   ├── knowledge.py                    ← knowledge retrieval
│   │   ├── proactive.py                    ← proactive message scheduling
│   │   ├── scheduler.py                    ← cadence scheduler
│   │   ├── calendar_tasks.py               ← calendar integration
│   │   ├── reminders.py                    ← reminder management
│   │   ├── badan_import.py                 ← biometric data import (Whoop)
│   │   ├── whoop_import.py                 ← Whoop CSV ingester
│   │   ├── council/                        ← multi-agent deliberation subsystem
│   │   │   ├── deliberation.py             ← deliberation logic
│   │   │   ├── members.py                  ← council member definitions
│   │   │   ├── decision_protocols.py       ← decision protocol runner
│   │   │   ├── evidence.py                 ← evidence pack builder
│   │   │   └── ledger.py                   ← council ledger writer
│   │   └── pulsation/                      ← proactive pulsation loop
│   │       ├── loops.py                    ← main pulsation loop
│   │       ├── routing.py                  ← pulsation routing
│   │       ├── ledger.py                   ← pulsation ledger
│   │       ├── himayah_egress.py           ← HIMAYAH check for outbound pulsation
│   │       ├── state.py                    ← pulsation state management
│   │       ├── collision.py                ← collision detection (avoids duplicate sends)
│   │       └── message_builder.py          ← Telegram message formatter
│   │
│   ├── modes/                              ← persona mode bundles
│   │   ├── khaldun/                        ← Khaldun runtime mode (Python module)
│   │   │   ├── classifier.py               ← Islamic claim classifier
│   │   │   ├── context_linker.py
│   │   │   ├── miracle_review.py
│   │   │   ├── response_builder.py
│   │   │   ├── runtime_prompt.py
│   │   │   └── validator.py
│   │   └── khaldun_islamic_cosmic_wisdom/  ← Khaldun mode bundle (markdown + JSON policy)
│   │       ├── KHALDUN_ISLAMIC_COSMIC_WISDOM_MODE.md
│   │       ├── aqidah_risk_policy.md
│   │       ├── claim_classification.schema.json
│   │       ├── hadith_reference_corpus.json
│   │       ├── source_registry.json
│   │       └── templates/                  ← mode-specific output templates
│   │
│   ├── connectors/                         ← external service adapters
│   │   ├── google_adapter.py               ← Google Drive adapter
│   │   ├── google_oauth.py                 ← OAuth flow
│   │   └── health.py                       ← connector health checks
│   │
│   ├── skills_registry/                    ← skills index + routing
│   │   ├── index.json                      ← all skills indexed by command
│   │   ├── router.py                       ← skill router
│   │   └── registry.schema.json
│   │
│   ├── runtime/                            ← runtime plans and operator profiles
│   │   ├── owner_profile.md                ← operator profile for context
│   │   └── owner_profile_ingest.py
│   │
│   ├── personas/                           ← persona soul files
│   │   ├── NIZAM.json                      ← Coordinator persona
│   │   ├── TAFRIGH.json                    ← Amin — capture
│   │   ├── SHURA.json                      ← Salman — brainstorm
│   │   ├── NAQD.json                       ← Hazim — red-team
│   │   ├── TARIQ.json                      ← Tariq — long-horizon
│   │   ├── MUNAWARA.json                   ← Khalid — tactical
│   │   ├── BADAN.json                      ← Hayat — biometric
│   │   ├── HIKMAH.json                     ← Khaldun — weekly synthesis
│   │   ├── MARSAD.json                     ← Tahir — intel scout
│   │   ├── MAL.json                        ← financial persona
│   │   └── AMMAR.json                      ← governor / egress guardian
│   │
│   ├── schemas/                            ← JSON Schema files for all artifact types
│   │   ├── agent_message.schema.json
│   │   ├── conversational_session.schema.json
│   │   ├── event_ledger.schema.json
│   │   ├── decision_ledger.schema.json
│   │   ├── learning_ledger.schema.json
│   │   ├── note_frontmatter.schema.json    ← universal markdown frontmatter contract
│   │   ├── persona.schema.json
│   │   ├── overload_flag.schema.json
│   │   ├── body_signal.schema.json
│   │   ├── tactical_plan.schema.json
│   │   ├── long_horizon_plan.schema.json
│   │   ├── governor_runtime_record.schema.json
│   │   └── ...                             ← 30+ schemas total
│   │
│   ├── skills/                             ← slash-command skill files (markdown)
│   │   ├── _SKILLS_INDEX.md
│   │   ├── tafrigh-capture.md
│   │   ├── shura-brainstorm.md
│   │   ├── naqd-grill.md
│   │   ├── sukoon-check.md
│   │   ├── nizam-checkin.md
│   │   ├── nizam-governor.md
│   │   ├── thabat_ledger_closeout.skill.md ← THABAT enforcement skill
│   │   ├── himayah_egress_guard.skill.md   ← HIMAYAH check skill
│   │   ├── sukoon_recovery.skill.md        ← SUKOON gate skill
│   │   └── ...                             ← 45+ skill files total
│   │
│   ├── templates/                          ← markdown output templates
│   │   ├── brain_dump.template.md
│   │   ├── brainstorm.template.md
│   │   ├── note_frontmatter.template.md
│   │   ├── weekly_battle.template.md
│   │   ├── 10_year_vision.template.md
│   │   └── ...                             ← 28 templates total
│   │
│   ├── protocols/                          ← cadence-driven skill chains
│   │   ├── _PROTOCOLS_INDEX.md
│   │   ├── crisis_sukoon_red.md            ← SUKOON crisis protocol
│   │   ├── daily_morning.md
│   │   ├── daily_evening.md
│   │   ├── weekly_sunday.md
│   │   ├── monthly_close.md
│   │   ├── quarterly_close.md
│   │   ├── annual_close.md
│   │   └── ...
│   │
│   ├── workflows/                          ← scenario-driven skill chains
│   │   ├── _WORKFLOWS_INDEX.md
│   │   ├── idea_to_decision.md
│   │   ├── finance_decision.md
│   │   ├── weekly_synthesis.md
│   │   ├── contradiction_resolution.md
│   │   └── ...
│   │
│   ├── policies/                           ← governance policy JSON
│   │   ├── PRIVACY_CLASSIFICATION.json     ← path_glob → classification rules
│   │   ├── SYNC_POLICY.json                ← allowed/denied per sync surface
│   │   ├── DUAL_WRITE_GOVERNOR.json        ← Notion + Drive dual-write rules
│   │   ├── TOOL_ACCESS_MATRIX.json         ← which agents may use which tools
│   │   └── CONNECTORS.json                 ← external connector registry
│   │
│   ├── docs/                               ← doctrine and operator guides
│   │   ├── MEMORY_MODEL.md                 ← six-layer memory model
│   │   ├── CONTINUITY_PROTOCOL.md          ← THABAT gate + session lifecycle
│   │   ├── DATA_MODEL.md                   ← artifact type catalog
│   │   ├── NIZAM_CONVERSATIONAL_LAYER.md   ← portable conversational prompt
│   │   ├── NIZAM_ORCHESTRATION_LAYER.md    ← agent contract doc
│   │   ├── DUAL_WRITE_GOVERNOR.md          ← dual-write operator guide
│   │   ├── GITHUB_PRIVACY.md               ← visibility rules
│   │   └── diagrams/                       ← Mermaid architecture diagrams
│   │       ├── system_architecture.mmd
│   │       ├── write_path_sequence.mmd
│   │       ├── agent_dataflow.mmd
│   │       └── retention_lifecycle.mmd
│   │
│   ├── ledgers/                            ← append-only JSONL event stores
│   │   ├── EVENT_LEDGER.jsonl              ← review_before_commit
│   │   ├── DECISION_LEDGER.jsonl           ← review_before_commit
│   │   ├── LEARNING_LEDGER.jsonl           ← review_before_commit
│   │   ├── STRATEGY_LEDGER.jsonl           ← strict_local (+ Merkle STH)
│   │   ├── BATTLE_LEDGER.jsonl             ← strict_local
│   │   ├── DEAD_LETTER.jsonl               ← strict_local (failed writes, never commits)
│   │   ├── COUNCIL_LEDGER.jsonl
│   │   ├── PULSATION_LEDGER.jsonl
│   │   ├── .cost-month.json                ← gitignored cost tracker
│   │   └── sth/                            ← STRATEGY_LEDGER Signed Tree Heads
│   │
│   ├── hermes-config/                      ← Hermes deployment configuration
│   │   ├── CANONICAL_PATHS.md
│   │   ├── HIMAYAH_POSTURE.md
│   │   ├── nizam-budgets.json
│   │   ├── nizam-egress-greenlist.json
│   │   └── scripts/nizam-scheduled-pulse.py
│   │
│   └── hermes-plugins/
│       └── nizam-governor/
│           ├── __init__.py                 ← plugin implementation
│           └── plugin.yaml                 ← hook registrations (v1.11.2)
│
├── TAFRIGH__brain_dumper/                  ← Phase 1: verbatim capture
│   ├── README.md
│   ├── _index.json
│   └── raw/                                ← strict_local (gitignored)
│
├── SHURA__brainstormer/                    ← Phase 1: co-thinking
│   ├── README.md
│   ├── _index.json
│   └── sessions/                           ← strict_local (gitignored)
│
├── NAQD__brain_griller/                    ← Phase 1: red-team / critique
│   ├── README.md
│   ├── _index.json
│   └── sessions/                           ← strict_local (gitignored)
│
├── SUKOON__recovery_first/                 ← Phase 1: recovery gate + signals
│   ├── README.md
│   ├── _index.json
│   └── overload_flags.jsonl                ← strict_local; SUKOON gate reads this
│
├── TARIQ__long_horizon_strategy/           ← Phase 2: 10/15/20-yr strategy
│   ├── README.md
│   └── _index.json
│
├── MUNAWARA__tactical_strategy/            ← Phase 2: 1/3/5-yr + quarters + weeks
│   ├── README.md
│   └── _index.json
│
├── MAL__financial_engine/                  ← Phase 2: financial tracking
│   ├── README.md
│   ├── _index.json
│   └── pfa/                                ← Personal Financial Analysis
│
├── BADAN__body_health_system/              ← Phase 2: biometric advisory
│   ├── README.md
│   ├── _index.json
│   └── daily_signals/                      ← strict_local; Whoop import writes here
│
├── QARAR__decisions/                       ← Phase 2: ADR-style decision records
│   ├── README.md
│   └── _index.json
│
├── INTAJ__output_engine/                   ← Phase 2: tasks / deliverables (shell only)
├── YAWMIYAT__journaling/                   ← Phase 2: structured journal + sessions
├── HIKMAH__learnings/                      ← Phase 2: crystallized insights
├── HIKMAH__weekly_synthesis/              ← Weekly synthesis output folder (live)
├── NUR__obsidian_vault/                    ← Phase 2: Obsidian mirror (deferred)
├── JADWAL__notion_dashboards/              ← Phase 2: Notion mirror (deferred)
├── HIFZ__github_version_control/          ← Phase 2: repo automation + governor scripts
│   ├── README.md
│   ├── _index.json
│   └── scripts/
│       ├── nizam_governor_lib.py           ← pre-existing governor library
│       ├── nizam_dual_write.py             ← Notion + Drive dual-write executor
│       ├── nizam_drive_mirror.py           ← Drive mirror script
│       └── notion_preflight.py             ← Notion connection preflight
│
├── MARSAD__flight_radar/                   ← Phase 2: external intel scout (live)
├── BASIRA__future_visualization/           ← Phase 3: graph/dashboard (shell only)
├── MAKHZAN__archive/                       ← Phase 0: immutable timestamped snapshots
├── HAJR__quarantine/                       ← Phase 0: uncertain/unsafe artifact holding pen
│
├── tools/                                  ← utility scripts
├── scripts/                                ← automation scripts
├── docs/                                   ← root-level docs
├── .planning/                              ← planning artifacts (this dir)
│   └── codebase/                           ← codebase analysis documents
└── .github/                                ← GitHub Actions (if any)
```

---

## Directory Purposes

**`NIZAM__system/`:**
- Purpose: Governance kernel — all code, all policy, all registries live here
- Contains: Python modules (governor, relay, companion, connectors, modes, config), JSON policy files, markdown skills/templates/protocols/workflows/docs, JSONL ledgers, persona definitions, JSON schemas
- Key files: `AGENT_MAPPING.json`, `agent_personas.json`, `pillar_registry.json`, `config/agents.registry.yaml`, `config/nizam_router.py`

**Module folders (`SYMBOL__description/`):**
- Purpose: One per cognitive domain / life pillar
- Contains: `README.md`, `_index.json` (self-registration), and typed subfolders for output artifacts
- Key invariant: Folder naming pattern is `UPPERCASE_SYMBOL__snake_case_description`

**`MAKHZAN__archive/`:**
- Purpose: Immutable rollback anchors (Layer 6 of memory model)
- Contains: Timestamped snapshot directories with SHA256 MANIFEST
- Generated: Yes (by `/naqd-reconcile` and any rewrite operation)
- Committed: Only the manifests and public-framework snapshots; strict_local content not committed

**`HAJR__quarantine/`:**
- Purpose: Holding pen for uncertain, unclassified, or potentially unsafe artifacts
- Subdir `HAJR__quarantine/maximum/` → `strict_local_maximum` classification (hardest block)

---

## Module Folder Content Conventions

Each active module folder follows this pattern:

```
MODULE__description/
├── README.md                   ← human overview (private_github)
├── _index.json                 ← machine-readable self-registration (private_github)
└── <typed subfolders>/         ← actual content (usually strict_local)
    ├── raw/                    ← unstructured captures
    ├── sessions/ or entries/   ← structured session output
    ├── triaged/                ← triage-sorted captures
    ├── signals/                ← biometric or recovery signals
    ├── weekly/ or reviews/     ← periodic summaries
    └── ...                     ← module-specific types
```

Privacy level is declared in `_index.json#privacy_level` and must match `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`.

---

## Key File Locations

**Mandatory session reads (every Claude session):**
- `D:/NIZAM/CRITICAL_FACTS.md` — constraints; read first
- `D:/NIZAM/SOUL.md` — identity (strict_local; not in git)
- `D:/NIZAM/index.md` — page catalog
- `D:/NIZAM/NIZAM_TEMPLE.json` — master config, gate definitions

**Router + intent config:**
- `D:/NIZAM/NIZAM__system/config/nizam_router.py` — IR-1..IR-8 resolver
- `D:/NIZAM/NIZAM__system/config/router.config.yaml` — thresholds, intents, commands
- `D:/NIZAM/NIZAM__system/config/intent_exemplars.yaml` — Jaccard exemplar lists
- `D:/NIZAM/NIZAM__system/config/agents.registry.yaml` — codename → model/gates/delegates

**Governor Python modules:**
- `D:/NIZAM/NIZAM__system/governor/classifier.py` — HIMAYAH privacy classification
- `D:/NIZAM/NIZAM__system/governor/sync_arbiter.py` — cross-plane write arbitration
- `D:/NIZAM/NIZAM__system/governor/ledger_writer.py` — sole ledger writer (hash-chained)
- `D:/NIZAM/NIZAM__system/governor/kill_switch.py` — `NIZAM_KILL_ALL` panic stop
- `D:/NIZAM/NIZAM__system/governor/cost_ceiling.py` — $50 soft / $300 hard budget
- `D:/NIZAM/NIZAM__system/governor/strategy_sth.py` — Merkle STH for STRATEGY_LEDGER

**Relay / Hermes:**
- `D:/NIZAM/NIZAM__system/relay/poller.py` — Telegram long-poll runner (main entry)
- `D:/NIZAM/NIZAM__system/relay/coordinator.py` — pipeline coordinator (B4.4–B4.7)
- `D:/NIZAM/NIZAM__system/relay/sukoon_gate.py` — SUKOON pre-gate implementation
- `D:/NIZAM/NIZAM__system/relay/auth.py` — operator whitelist

**Policies:**
- `D:/NIZAM/NIZAM__system/policies/PRIVACY_CLASSIFICATION.json` — path_glob → classification rules (source of truth for HIMAYAH)
- `D:/NIZAM/NIZAM__system/policies/SYNC_POLICY.json` — allowed/denied per surface
- `D:/NIZAM/NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json` — Notion/Drive dual-write spec

**Personas:**
- `D:/NIZAM/NIZAM__system/personas/` — all persona JSON files
- `D:/NIZAM/NIZAM__system/agent_personas.json` — codename → persona file mapping

**Ledgers (append-only, hash-chained):**
- `D:/NIZAM/NIZAM__system/ledgers/EVENT_LEDGER.jsonl` — primary event log (review_before_commit)
- `D:/NIZAM/NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl` — strategy events (strict_local + Merkle STH)
- `D:/NIZAM/NIZAM__system/ledgers/DEAD_LETTER.jsonl` — failed writes (strict_local, never commits)
- `D:/NIZAM/NIZAM__system/ledgers/.cost-month.json` — monthly LLM cost tracker (gitignored)
- `D:/NIZAM/NIZAM__system/ledgers/sth/` — STRATEGY_LEDGER Signed Tree Head files

**Skills (slash-command encoded paths):**
- `D:/NIZAM/NIZAM__system/skills/` — 45+ skill markdown files
- `D:/NIZAM/NIZAM__system/skills/_SKILLS_INDEX.md` — all skills indexed

**Documentation:**
- `D:/NIZAM/NIZAM__system/docs/MEMORY_MODEL.md` — six-layer memory model
- `D:/NIZAM/NIZAM__system/docs/CONTINUITY_PROTOCOL.md` — THABAT gate + session lifecycle
- `D:/NIZAM/NIZAM__system/docs/DATA_MODEL.md` — artifact type catalog
- `D:/NIZAM/NIZAM__system/docs/diagrams/` — Mermaid diagrams

**Schemas:**
- `D:/NIZAM/NIZAM__system/schemas/note_frontmatter.schema.json` — universal markdown frontmatter contract
- `D:/NIZAM/NIZAM__system/schemas/event_ledger.schema.json` — EVENT_LEDGER row contract
- `D:/NIZAM/NIZAM__system/schemas/conversational_session.schema.json` — YAWMIYAT session contract

**SUKOON gate input:**
- `D:/NIZAM/SUKOON__recovery_first/overload_flags.jsonl` — `sukoon_gate.pre_gate()` reads this

---

## Naming Conventions

**Module folders:**
- Pattern: `UPPERCASE_ARABIC_SYMBOL__snake_case_english_description`
- Examples: `TAFRIGH__brain_dumper`, `SHURA__brainstormer`, `MAL__financial_engine`
- Registration: Every folder registers itself in `NIZAM_MASTER_REGISTER.json` and has `_index.json`

**Persona files:**
- Pattern: `UPPERCASE_SYMBOL.json` in `NIZAM__system/personas/`
- Examples: `NIZAM.json`, `TAFRIGH.json`, `SHURA.json`

**Schema files:**
- Pattern: `snake_case_name.schema.json`
- Mode schemas: `snake_case_name.schema.json` (same pattern, in mode bundle folder)

**Skill files:**
- Pattern: `kebab-case-command.md` or `kebab-case-command.skill.md`
- Examples: `tafrigh-capture.md`, `thabat_ledger_closeout.skill.md`

**Template files:**
- Pattern: `snake_case_name.template.md`

**Ledger files:**
- Pattern: `SCREAMING_SNAKE_CASE.jsonl`
- Examples: `EVENT_LEDGER.jsonl`, `STRATEGY_LEDGER.jsonl`

**Skill template files (modes):**
- Pattern: `template_snake_case.md` in `NIZAM__system/modes/<mode_name>/templates/`

**Timestamps in filenames:**
- Format: `YYYY-MM-DDTHH-MM-SSZ` (hyphens replace colons for filesystem compat)
- In JSON/JSONL: `YYYY-MM-DDTHH:MM:SSZ` (standard ISO 8601 UTC with Z)

**Index files:**
- `_index.json` — per-folder machine-readable self-registration
- `NIZAM__system/*_INDEX.json` — system-level registries (AGENT_MAPPING, PROTOCOLS_INDEX, SCHEMA_INDEX, WORKFLOWS_INDEX)

---

## Where to Add New Code

**New module / pillar:**
1. Create folder: `NEWMODULE__description/` at repo root
2. Add `README.md` and `_index.json` (copy pattern from `TAFRIGH__brain_dumper/_index.json`)
3. Register in `NIZAM_MASTER_REGISTER.json` (add entry to `folders` array)
4. Register in `NIZAM_TEMPLE.json#modules` with phase, persona path
5. Add entry to `NIZAM__system/pillar_registry.json`
6. Create persona JSON in `NIZAM__system/personas/NEWSYMBOL.json`
7. Add codename entry to `NIZAM__system/agent_personas.json`
8. Add agent entry to `NIZAM__system/config/agents.registry.yaml`

**New skill (slash command):**
1. Create `NIZAM__system/skills/module-verb.md` following frontmatter contract in `note_frontmatter.schema.json`
2. Add entry to `NIZAM__system/skills/_SKILLS_INDEX.md`
3. Add entry to `NIZAM__system/skills_registry/index.json`
4. If it maps to a Telegram command, add to `commands:` block in `NIZAM__system/config/router.config.yaml`

**New schema:**
1. Create `NIZAM__system/schemas/snake_case_name.schema.json`
2. Add entry to `NIZAM__system/SCHEMA_INDEX.json`
3. Add corresponding template to `NIZAM__system/templates/` if needed

**New protocol (cadence-driven skill chain):**
1. Create `NIZAM__system/protocols/name.md`
2. Add entry to `NIZAM__system/PROTOCOLS_INDEX.json`
3. Update `NIZAM__system/protocols/_PROTOCOLS_INDEX.md`

**New workflow (scenario-driven skill chain):**
1. Create `NIZAM__system/workflows/name.md`
2. Add entry to `NIZAM__system/WORKFLOWS_INDEX.json`
3. Update `NIZAM__system/workflows/_WORKFLOWS_INDEX.md`

**New ledger:**
1. Add name to `KNOWN_LEDGERS` set in `NIZAM__system/governor/ledger_writer.py`
2. Add entry to `NIZAM_TEMPLE.json#ledgers` with path and privacy
3. Add privacy rule to `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`
4. Create corresponding schema in `NIZAM__system/schemas/`

**New module content (artifact):**
- Brain dumps → `TAFRIGH__brain_dumper/raw/YYYY-MM-DDTHH-MM-SSZ.md` (strict_local)
- Brainstorm sessions → `SHURA__brainstormer/sessions/YYYY-MM-DD.md` (strict_local)
- Critique sessions → `NAQD__brain_griller/sessions/YYYY-MM-DD.md` (strict_local)
- Recovery signals → `SUKOON__recovery_first/signals/YYYY-MM-DD.md` (strict_local)
- Overload flags → `SUKOON__recovery_first/overload_flags.jsonl` (append line; strict_local)
- Biometric signals → `BADAN__body_health_system/daily_signals/YYYY-MM-DD.md` (strict_local)
- Tactical plans → `MUNAWARA__tactical_strategy/weeks/YYYY-Wnn.md` (strict_local)
- Long-horizon plans → `TARIQ__long_horizon_strategy/10_year/` or `15_year/` or `20_year/` (strict_local)
- Decisions → `QARAR__decisions/YYYY-MM-DD-slug.md` (review_before_commit)
- Journal sessions → `YAWMIYAT__journaling/sessions/YYYY-MM-DDTHH-MM-SSZ.json` (strict_local)
- Snapshots → `MAKHZAN__archive/<YYYY-MM-DDTHH-MM-SSZ>/` with MANIFEST (immutable)

---

## Special Directories

**`NIZAM__system/ledgers/`:**
- Generated: Partially (EVENT_LEDGER grows on every session; sth/ on every STRATEGY_LEDGER append)
- Committed: Only README.md and .gitignore — all JSONL files gitignored (strict_local or review_before_commit with human gate)

**`NIZAM__system/relay/.state/`:**
- Generated: Yes (poller state, telemetry, proactive state)
- Committed: No (gitignored)

**`MAKHZAN__archive/`:**
- Generated: Yes (by reconcile / rewrite operations)
- Committed: Framework snapshots only; strict_local content not committed

**`HAJR__quarantine/maximum/`:**
- Generated: Yes (by quarantine operations)
- Committed: Never (`strict_local_maximum` — nothing leaves disk)

**`NIZAM__system/modes/khaldun_islamic_cosmic_wisdom/`:**
- Purpose: Full mode bundle for Khaldun's Islamic Cosmic Wisdom mode; all policies, schemas, corpus, templates self-contained here
- Committed: Yes (`private_github` tier)

**`NIZAM__system/governor/scripts/`:**
- Purpose: Git hook installer and pre-commit HIMAYAH enforcement
- Install via: `python NIZAM__system/governor/scripts/install_pre_commit_hook.py`

---

*Structure analysis: 2026-06-14*
