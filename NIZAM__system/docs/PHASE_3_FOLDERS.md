# PHASE_3_FOLDERS

These 2 folders are the most privacy-sensitive and are deferred to Phase 3.

| Folder | Symbol meaning | Purpose | Privacy default |
|---|---|---|---|
| `AHEL__family_network/` | "family/kin" | Family tree, support ledger, connection cadence, important dates | **strict_local_maximum** |
| `BASIRA__future_visualization/` | "insight/vision" | Future graph/dashboard layer | review_before_commit |

## AHEL — strictest privacy in POP

- Entire `AHEL__family_network/**` excluded from `.gitignore`, Obsidian sync, Notion sync.
- Only `AHEL__family_network/README.md` and `AHEL__family_network/_index.json` may be committed (and the `_index.json` content lists structure only, never names).
- HIMAYAH gate requires explicit per-person approval before any export.
- Sharing a person card requires `/ahel-export <person_id> --confirm` writing to a sanitized location.

## Phase 3 dependencies

- Phase 2 stable.
- Explicit user approval (`ACT PHASE 3`).
- Privacy posture audited.

## Phase 3 deliverables

- AHEL scaffold with maximum privacy: `_index.json`, `README.md`, subfolder shells (`family_tree/`, `support_ledger/`, `connection_cadence/`, `important_dates/`), persona JSON, 3 skills, 2 schemas, 4 templates.
- BASIRA scaffold (visualization design).
- Optional: scheduled agents documentation (`NIZAM__system/docs/SCHEDULED_AGENTS.md`).
- Optional: cross-CLI build (Codex/Gemini/OpenCode) — POP skill files are already platform-agnostic markdown.
