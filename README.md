# POP — Personal Optimization Project

> Local-first personal operating system for capture, recovery, planning, critique, privacy-safe GitHub scaffolding, and machine-readable continuity.

**Owner**: [Seif Elsherbiny](https://github.com/seifelsherbinyy)
**Status**: Phase 1 MVP scaffolded · Phase 2/3 designed
**License**: MIT
**Canonical remote**: [github.com/seifelsherbinyy/nizamcore](https://github.com/seifelsherbinyy/nizamcore)

---

## What is POP

POP is a personal operating system: a folder structure + machine-readable registries + AI-skill files that help you (a) reduce mental clutter, (b) co-think problems, (c) red-team your plans, (d) preserve continuity through timestamped logs, and (e) eventually plan across multi-decade horizons.

Three cognitive modules form the Phase 1 MVP:
- **TAFRIGH** (تفريغ — "unloading"): daily / twice-daily brain dump → triaged buckets.
- **SHURA** (شورى — "consultation"): co-thinking partner that scans your vault first before reaching for external sources.
- **NAQD** (نقد — "critique"): red-team your plans and reconcile contradictions when new info conflicts with old notes.

A fourth foundation module — **SUKOON** (سكون — "calm") — tracks recovery signals (sleep / energy / stress / mood) and drives a downshift gate that overrides tactical pressure. Recovery-first is POP's top operating principle.

## Architecture

| Folder | Phase | Role |
|---|---|---|
| `NIZAM__system/` | 1 | registries, schemas, personas, skills, policies, ledgers, templates, docs |
| `TAFRIGH__brain_dumper/` | 1 | brain dumps (raw + triaged) |
| `SHURA__brainstormer/` | 1 | co-thinking sessions |
| `NAQD__brain_griller/` | 1 | red-team sessions + contradiction reconciliation |
| `SUKOON__recovery_first/` | 1 | daily recovery signals + overload flags |
| `MAKHZAN__archive/` | 1 | immutable timestamped snapshots with `MANIFEST.json` SHA256 |
| `HAJR__quarantine/` | 1 | uncertain / unclassified holding pen |
| `KABIR_SHERBO__long_horizon_strategy/` | 2 | 10/15/20-yr Long War Map |
| `MUNAWARA__tactical_strategy/` | 2 | 1/3/5-yr → quarters → weeks → battles |
| `MAL__financial_engine/` | 2 | personal-finance milestone ladder + exchange-rate verification |
| `BADAN__body_health_system/` | 2 | advisory health-signal tracking (not diagnostic) |
| `AHEL__family_network/` | 3 | family map (strictest privacy) |

Each folder uses dual naming `ARABIC_SYMBOL__technical_function` so humans and machines both understand it.

## Three inviolable gates

- **HIMAYAH** (حماية — protection) — before any sync, commit, or external share, verify privacy classification.
- **SUKOON** — before any output-heavy session, check overload flags.
- **THABAT** (ثبات — continuity) — before session close, append to event ledger.

## Skills, not prompts

Slash commands like `/tafrigh-capture`, `/shura-brainstorm`, `/naqd-grill` are not free prompts — they're markdown files in `NIZAM__system/skills/` whose frontmatter encodes the exact target folder, naming pattern, template, gates, privacy level, and event ledger. This eliminates path hallucination by AI agents.

Skill design principle credit: [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) (MIT), [jamesmcroft/obsidian-ai-second-brain](https://github.com/jamesmcroft/obsidian-ai-second-brain) (MIT). See [`NIZAM__system/docs/EXTERNAL_PATTERNS_CITED.md`](NIZAM__system/docs/EXTERNAL_PATTERNS_CITED.md).

## Privacy model

This repo is **public** for the framework and scaffolding. Personal contents are **strict-local** by `.gitignore`:

**Public (in this repo):** schemas, templates, skills, policies, docs, READMEs, master registries, the architecture.

**Strict-local (never committed):** `raw/`, `triaged/`, `sessions/`, `signals/`, `overload_flags.jsonl`, `HAJR/`, `SOUL.md`, all Phase 2/3 ledgers, future `MAL/`, `BADAN/`, `AHEL/` contents, and any `.env` / token / secret files.

The framework is openly shareable; the personal life data inside it is not. Treat this repo as a **structural manifest** of how the system works, not a journal.

## How a day looks

**Morning (5–10 min)**:
1. `/sukoon-check` — log sleep / energy / stress.
2. `/tafrigh-capture` — brain-dump without judgment.
3. `/tafrigh-triage` — sort into Now / Next / Later / Delete / Reflect / Escalate.

**Ad-hoc**:
- `/shura-brainstorm "<topic>"` for co-thinking with vault-first research.
- `/naqd-grill "<topic>"` to red-team a plan (auto-downshifts to Supportive Reflection if SUKOON is red).

**Weekly (Sunday, ~30 min)**:
- `/pop-recap` — synthesize the week from ledgers.
- `/pop-health` — audit for stale claims, orphan notes, contradictions.

## Read order for new visitors

1. [`CRITICAL_FACTS.md`](CRITICAL_FACTS.md) — always-loaded context (~120 tokens)
2. [`index.md`](index.md) — page catalog
3. [`POP_TEMPLE.json`](POP_TEMPLE.json) — master commandments
4. [`NIZAM__system/docs/SKILL_DESIGN_PRINCIPLES.md`](NIZAM__system/docs/SKILL_DESIGN_PRINCIPLES.md) — how skills work
5. Any [`NIZAM__system/skills/*.md`](NIZAM__system/skills/) you want to understand

## Pattern lineage

POP mirrors structural DNA from the author's prior local project **SESHAT** (deity-themed Egyptian-vendor analytics) and cherry-picks design patterns from three open-source second-brain projects (see [`EXTERNAL_PATTERNS_CITED.md`](NIZAM__system/docs/EXTERNAL_PATTERNS_CITED.md)). No upstream code is copied — patterns are independently re-implemented with attribution.

## License

[MIT](LICENSE). Use the framework freely. Personal contents remain the author's.
