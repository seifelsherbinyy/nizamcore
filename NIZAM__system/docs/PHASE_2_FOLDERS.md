# PHASE_2_FOLDERS

These 11 folders are designed in the v3.0 plan but NOT scaffolded in Phase 1. They are scaffolded after Phase 1 stabilizes for ≥7 days OR on explicit user approval (`ACT PHASE 2`).

| Folder | Symbol meaning | Purpose | Privacy default |
|---|---|---|---|
| `TARIQ__long_horizon_strategy/` | "great/big" | 10/15/20-yr Long War Map (wealth, career, body, family, faith, location, learning, relationships, business, assets, identity) | strict_local |
| `MUNAWARA__tactical_strategy/` | "illuminated" (or rename to TADBIR) | 1/3/5-yr → quarters → months → weeks → battles | strict_local |
| `MAL__financial_engine/` | "wealth/money" | $900 → $10k/mo milestone ladder; exchange-rate verification | strict_local |
| `BADAN__body_health_system/` | "body" | Advisory health tracking, NOT diagnostic | strict_local |
| `INTAJ__output_engine/` | "production" | Tasks, execution plans, agendas | review_before_commit |
| `YAWMIYAT__journaling/` | "diary" | Structured journal entries, weekly reviews | strict_local |
| `QARAR__decisions/` | "decision" | ADR-style decision records | review_before_commit |
| `HIKMAH__learnings/` | "wisdom" | Precious insights, principles | review_before_commit |
| `NUR__obsidian_vault/` | "light" | Obsidian mirror (curated promotions from POP canonical, one-way) | mirror_curated_only |
| `JADWAL__notion_dashboards/` | "table" | Notion mirror (sanitized metadata only) | mirror_sanitized_metadata_only |
| `HIFZ__github_version_control/` | "preservation" | Repo metadata, scripts | review_before_commit |

## Phase 2 dependencies

- Phase 1 stable (≥7 days of daily use OR explicit user override).
- gh CLI authenticated, repo verified private.
- For MAL: exchange-rate source identified (e.g., XE, central bank).
- For BADAN: health-data sources decided (WHOOP / Apple Health / manual).

## Phase 2 deliverables (per branch)

Each new branch ships with:
- `_index.json` + `README.md`
- Subfolder shells (empty)
- Persona JSON in `NIZAM__system/personas/`
- 3–5 skill files in `NIZAM__system/skills/` (per plan §12–§15)
- Schemas in `NIZAM__system/schemas/`
- Templates in `NIZAM__system/templates/`
- Doctrine doc in `NIZAM__system/docs/`
- Ledger file added to `NIZAM__system/ledgers/` (strict_local for new ledgers)
- `.gitignore` updated
- Snapshot to `MAKHZAN__archive/`

## Recovery-first override

Phase 2 scaffolding is deferred if SUKOON shows persistent red flags. Building new structure while in recovery debt violates the recovery-first principle.
