# POP — Changelog

## 2026-10-02 — nizamfinancialapp (PFOS) merged in
- New top-level folder: `PFOS__personal_finance_app/` — the full nizamfinancialapp repository
  (853 tracked files: `src/`, `contracts/`, `docs/`, `ops/`, build + test tooling), carrying its own
  deterministic finance engine (integer milliunits), Drive sync (`drive.file` scope), and test suite.
  Not an interleaved file merge — it lands as its own self-contained software project, since nizamcore
  has no package.json/build of its own.
- `MAL__financial_engine/` folded onto PFOS as its computational core: MAL's `pfa_*` schemas migrated
  from float `*_egp` fields to integer `*_milliunits`; MAL's own "ask the user, estimate, label
  confidence" update routine retired in favor of a single sync-from-PFOS step; `canonical_state.json`
  redefined as a generated projection of PFOS's `finance.db`, not a second source of truth.
- MAL's codename fixed from a self-declared, unregistered "Sadiq" (which collided with QARAR's actual
  registered codename) to **Zayd**, now properly entered in `agent_personas.json`.
- Full decision record: `NIZAM__system/docs/ADR-ZAYD-001-pfos-engine-into-mal-zayd.md`.
- Staged in a local clone only — not committed, not pushed, pending owner review.

## v3.3.0 — 2026-05-15 (operational layers — protocols + workflows + memory model)
- New folder: `NIZAM__system/protocols/` — 8 cadence-driven skill chains.
  Daily morning, daily evening, weekly Sunday, monthly close, quarterly close, annual close, crisis (SUKOON red), onboarding (first 7 days).
- New folder: `NIZAM__system/workflows/` — 8 scenario-driven skill chains.
  Idea-to-decision, idea-to-project, strategy-rollup, finance-decision, body-routine, family-routine, contradiction-resolution, weekly-synthesis.
- New docs in `NIZAM/docs/`:
  - `MEMORY_MODEL.md` — six-layer memory architecture.
  - `CONTINUITY_PROTOCOL.md` — session / year / agent continuity guarantees.
  - `DATA_MODEL.md` — every artifact type mapped to schema + folder + skill + privacy.
- New JSON registries:
  - `PROTOCOLS_INDEX.json`
  - `WORKFLOWS_INDEX.json`
- POP_TEMPLE platform_version → 3.3.0, with `operational_layers` block.
- _SKILLS_INDEX, index.md updated to reference new layers.

## v3.2.0 — 2026-05-15 (Phase 3 scaffold)
- 2 new top-level folders: AHEL__family_network (live, strictest privacy), BASIRA__future_visualization (shell only).
- 1 new persona: AHEL.
- 3 new skills: ahel-add-person, ahel-support-log, ahel-connection-cadence.
- 2 new schemas: family_person, family_support_event.
- 4 new templates: person_card, support_event, connection_cadence, important_date.
- 2 new doctrine docs: SCHEDULED_AGENTS, CROSS_CLI_BUILD.
- AHEL/** fully gitignored except README.md and _index.json.
- FAMILY_LEDGER.jsonl touched (gitignored, strict_local).
- Updated POP_TEMPLE platform_version to 3.2.0, with AHEL + BASIRA modules registered.
- POP is now feature-complete at the framework level. Content awaits user fill.

## v3.1.0 — 2026-05-15 (Phase 2 scaffold)
- 11 new top-level folders: KABIR_SHERBO, MUNAWARA, MAL, BADAN, INTAJ, YAWMIYAT, QARAR, HIKMAH, NUR, JADWAL, HIFZ.
- 4 new module personas: KABIR_SHERBO, MUNAWARA, MAL, BADAN.
- 14 new skills: 2 kabir + 3 munawara + 5 mal + 3 badan + 1 qarar.
- 10 new schemas: long_horizon_plan, tactical_plan, battle_ledger, strategy_pivot, finance_baseline, finance_milestone, finance_scenario, body_signal, body_weekly_review, body_red_flag.
- 18 new templates across strategy / finance / body domains.
- 5 doctrine docs: BIG_SHERBO_LONG_WAR, MUNAWARA_TACTICAL, MAL_FINANCIAL_LADDER, BADAN_HEALTH_ADVISORY, AHEL_FAMILY_PRIVACY (Phase 3 reference).
- 22 folder shells with README + _index.json.
- 4 new strict-local ledgers touched (gitignored): STRATEGY, BATTLE, FINANCE, BODY.
- MAL `exchange_rate_log.jsonl` touched (gitignored).
- Updated registries: SCHEMA_INDEX, POP_MASTER_REGISTER, POP_TEMPLE, _SKILLS_INDEX.
- AHEL (Phase 3) + BASIRA (Phase 3) remain designed-only.

## v3.0.1 — 2026-05-15 (public-visibility enhancement)
- Canonical remote set to `github.com/seifelsherbinyy/nizamcore` (PUBLIC per user override).
- LICENSE added (MIT).
- README rewritten for public audience (visitor-friendly, links pattern lineage).
- `NIZAM__system/docs/GITHUB_PRIVACY.md` updated with public-override rationale and strengthened HIMAYAH discipline.
- `POP_TEMPLE.json` gains `canonical_remote` block documenting the visibility decision.
- `nizamcore` inspected and confirmed empty placeholder (one-line README) — nothing to cherry-pick from contents. Will adopt as canonical remote via merge of unrelated histories.

## v3.0.0 — 2026-05-15
- Phase 1 MVP scaffold created at `C:\Users\selsherb\POP`.
- 6 MVP folders: NIZAM__system, TAFRIGH__brain_dumper, SHURA__brainstormer, NAQD__brain_griller, SUKOON__recovery_first, MAKHZAN__archive, HAJR__quarantine.
- Orientation files: index.md, log.md, SOUL.md (placeholder, gitignored), CRITICAL_FACTS.md.
- Master registries: POP_TEMPLE.json, POP_MASTER_REGISTER.json, NIZAM/SCHEMA_INDEX.json.
- 3 personas (TAFRIGH, SHURA, NAQD), 12 Phase 1 skills, 6 schemas, 3 policies, 3 empty ledgers, 6 templates, 8 docs.
- `.gitignore` excludes all strict-local paths.
- Phase 2 (KABIR_SHERBO, MUNAWARA, MAL, BADAN) and Phase 3 (AHEL, BASIRA) branches DESIGNED but not yet scaffolded; documented in `NIZAM/docs/PHASE_2_FOLDERS.md` and `PHASE_3_FOLDERS.md`.
- External patterns cited: eugeniughelbur/obsidian-second-brain (MIT), jamesmcroft/obsidian-ai-second-brain (MIT), NicholasSpisak/second-brain.
- nizamcore integration: deferred to Phase 1.5 (private repo, requires gh auth).
