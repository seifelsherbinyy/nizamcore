# KABIR_SHERBO → Tariq Rename Surface Report (G1.0)

Generated: 2026-05-28 (NIZAM Next Plan v2)
Source: rg case-insensitive scan of D:\NIZAM\nizamcore over patterns
{KABIR_SHERBO, kabir-sherbo, BIG_SHERBO, Big Sherbo} - 41 occurrences in tracked working tree (excluding MAKHZAN__archive history).
Pre-action anchor: `MAKHZAN__archive/2026-05-28T20-12-29Z/manifest.sha256` (253 files, root 3bf5a207...).

---

## A. File/folder RENAMES (5)

| # | Old path | New path | Task ID |
|---|----------|----------|---------|
| 1 | `NIZAM__system/personas/KABIR_SHERBO.json` | `NIZAM__system/personas/TARIQ.json` | G1.2 |
| 2 | `NIZAM__system/skills/kabir-sherbo-vision.md` | `NIZAM__system/skills/tariq-vision.md` | G1.4 |
| 3 | `NIZAM__system/skills/kabir-sherbo-annual-review.md` | `NIZAM__system/skills/tariq-annual-review.md` | G1.4 |
| 4 | `KABIR_SHERBO__long_horizon_strategy/` (folder + 2 contents) | `TARIQ__long_horizon_strategy/` | G1.5 |
| 5 | `NIZAM__system/docs/BIG_SHERBO_LONG_WAR_DOCTRINE.md` | `NIZAM__system/docs/TARIQ_LONG_WAR_DOCTRINE.md` | G1.6 |

## B. In-content TOKEN REPLACEMENTS

Mappings applied across all files below:

| Token (old) | Token (new) |
|-------------|-------------|
| `KABIR_SHERBO` | `TARIQ` |
| `KABIR_SHERBO__long_horizon_strategy` | `TARIQ__long_horizon_strategy` |
| `kabir-sherbo-vision` | `tariq-vision` |
| `kabir-sherbo-annual-review` | `tariq-annual-review` |
| `BIG_SHERBO` (in doctrine title + refs) | `TARIQ` |
| `BIG_SHERBO_LONG_WAR_DOCTRINE` | `TARIQ_LONG_WAR_DOCTRINE` |
| `"meaning_ar": "great / big (codename: Big Sherbo)"` | `"meaning_ar": "knocker / morning star (after Tariq ibn Ziyad)"` |
| `Big Sherbo codename` | dropped — replace with Tariq role descriptor |

### Per-file surface (line numbers from G1.0 scan)

#### G1.7 — `POP_TEMPLE.json` (2 lines)
- L35: `"KABIR_SHERBO": { "phase": 2, "persona": "NIZAM__system/personas/KABIR_SHERBO.json", "scaffolded": true }` → `"TARIQ": { "phase": 2, "persona": "NIZAM__system/personas/TARIQ.json", "scaffolded": true }`
- L57: `"phase_2_folders": [..., "KABIR_SHERBO", ...]` → `[..., "TARIQ", ...]`

#### G1.8 — `POP_MASTER_REGISTER.json` (1 line)
- L14: `{ "path": "KABIR_SHERBO__long_horizon_strategy", ..., "symbol": "KABIR_SHERBO", "meaning_ar": "great/big (Big Sherbo codename)", ... }` → path TARIQ__long_horizon_strategy, symbol TARIQ, meaning_ar updated.

#### G1.9 — workflows (5 files, 12 lines)
- `weekly_synthesis.md` L49
- `idea_to_project.md` L22
- `strategy_rollup.md` L6, L7, L8, L19, L23, L27, L48, L56  (7 hits)
- `finance_decision.md` L57
- `_WORKFLOWS_INDEX.md` L17, L58

#### G1.10 — templates (5 files, 8 lines)
- `major_pivot.template.md` L3 (`pop_module: KABIR_SHERBO`), L48 (event ledger example)
- `20_year_vision.template.md` L3, L36, L37
- `annual_review.template.md` L3
- `10_year_vision.template.md` L3
- `15_year_vision.template.md` L3

#### G1.11 — schemas (4 files, 5 lines)
- `strategy_pivot.schema.json` L4 (title), L9 (enum)
- `tactical_plan.schema.json` L13 (rolls_up_to example)
- `note_frontmatter.schema.json` L9 (enum of pop_module)
- `long_horizon_plan.schema.json` L4 (title)

#### G1.12 — protocols (7 files, 16 lines)
- `weekly_sunday.md` L52
- `quarterly_close.md` L3, L9, L24, L39, L40
- `onboarding_first_7_days.md` L58
- `monthly_close.md` L48
- `annual_close.md` L9, L16, L25, L41, L55, L58
- `crisis_sukoon_red.md` L27
- `_PROTOCOLS_INDEX.md` L23, L24

#### G1.13 — `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json` (1 line)
- L21: glob `KABIR_SHERBO__long_horizon_strategy/...` → `TARIQ__long_horizon_strategy/...`

#### G1.14 — skills (5 files, 9 lines)
- `pop-health.md` L23
- `munawara-quarter-plan.md` L17
- `munawara-pivot.md` L5, L21, L30
- `kabir-sherbo-vision.md` ENTIRE FILE (becomes tariq-vision.md): L2 name, L3 module, L4 trigger, L6-L8 target_folder, L26 context_sources
- `kabir-sherbo-annual-review.md` ENTIRE FILE (becomes tariq-annual-review.md): L2 name, L3 module, L4 trigger, L6 context_sources, L12 target_folder

#### G1.15 — docs (5 files, 8 lines)
- `SCHEDULED_AGENTS.md` L18
- `PHASE_2_FOLDERS.md` L7
- `MUNAWARA_TACTICAL_DOCTRINE.md` L35
- `GITHUB_PRIVACY.md` L25
- `DATA_MODEL.md` L20, L21, L22, L73, L102
- `BIG_SHERBO_LONG_WAR_DOCTRINE.md` (renamed → `TARIQ_LONG_WAR_DOCTRINE.md`): L1 title, L3 prose codename line (rewrite to Tariq doctrine framing)

#### G1.16 — MUNAWARA persona + folder (3 references)
- `NIZAM__system/personas/MUNAWARA.json` L5 (role description), L8 (inputs), L14 (rule)
- `MUNAWARA__tactical_strategy/_index.json` L6 (purpose)
- `MUNAWARA__tactical_strategy/README.md` L6 (description)

#### G1.17 — top-level (3 files, 3 lines)
- `index.md` L15, L44
- `README.md` L34
- `CHANGELOG.md` — DO NOT EDIT (history); G1.20 verification permits residue here.

#### G1.18 — 4 NIZAM__system index files (4 lines)
- `WORKFLOWS_INDEX.json` L8
- `SCHEMA_INDEX.json` L13, L16
- `PROTOCOLS_INDEX.json` L11
- `skills/_SKILLS_INDEX.md` L32, L35, L36, L111

#### G1.19 — gate lift in `POP_TEMPLE.json` (later `NIZAM_TEMPLE.json` after G2.1)
- Remove `no_naming_kabir` from `hard_gates`. Add Tariq registration entry under modules. Already covered partly by G1.7.

## C. EXCLUSIONS (will NOT be touched)

- `MAKHZAN__archive/**` — immutable history; residue is permitted.
- `CHANGELOG.md` lines 31, 32, 36, 58 — historical record; residue is permitted.

## D. G1.20 Verification predicate (post-rename)

```
rg -i 'KABIR_SHERBO|kabir-sherbo|BIG_SHERBO|Big Sherbo' D:\NIZAM\nizamcore
  --glob '!MAKHZAN__archive/**'
  --glob '!CHANGELOG.md'
```

Expected output: zero hits.

## E. Operator approval surface (G1.1)

This document is the input to operator gate G1.1. By saying "implement the plan",
operator has authorised the rename per locked decision section_A.P0_GAP_blocking.Q1.
Default new-name = `Tariq`. Doctrine reframed: "knocker / morning star — long-horizon
campaign commander, after Tariq ibn Ziyad."
