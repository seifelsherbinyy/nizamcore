# GITHUB_PRIVACY

## Visibility decision (2026-05-15)

> **OVERRIDE**: User elected to keep the canonical remote `seifelsherbinyy/nizamcore` **PUBLIC**.
>
> Rationale (per user direction): POP's framework, schemas, skills, and architecture are publicly shareable as a portfolio/manifest. Personal contents are protected by `.gitignore` regardless of repo visibility.
>
> This overrides plan §9 / §22's "PRIVATE ONLY" default. The HIMAYAH gate is **strengthened**: `.gitignore` is the primary defense; visibility is secondary.

## What's public on this repo
- README, LICENSE, CHANGELOG, .gitignore
- POP_TEMPLE.json, POP_MASTER_REGISTER.json, index.md, CRITICAL_FACTS.md
- NIZAM__system/schemas/**, templates/**, skills/**, policies/**, docs/**, personas/**
- Each folder's _index.json and README.md
- MAKHZAN__archive/<ts>/MANIFEST.json (the snapshot hashes only; snapshot contents that mirror strict-local paths are themselves gitignored)

## What's NEVER public (strict-local via .gitignore)
- `TAFRIGH__brain_dumper/raw/**`, `triaged/**`
- `SHURA__brainstormer/sessions/**`, `NAQD__brain_griller/sessions/**`
- `SUKOON__recovery_first/signals/**`, `overload_flags.jsonl`
- `HAJR__quarantine/**`
- `SOUL.md` (identity / values placeholder)
- All `*_LEDGER.jsonl` files (EVENT, DECISION, LEARNING, STRATEGY, BATTLE, FINANCE, BODY, FAMILY)
- All Phase 2/3 strict-local folder contents: `KABIR_SHERBO/{10,15,20}_year/`, `MUNAWARA/{1,3,5}_year/` etc., `MAL/**`, `BADAN/**`, `AHEL/**`
- `MAKHZAN__archive/**/{raw,triaged,sessions,signals}/**` (snapshots inherit privacy)
- All secrets: `.env`, `*token*`, `*secret*`, `*credentials*`

## Pre-commit checklist (HIMAYAH gate — UNCHANGED)

1. `git status` — surface every staged file.
2. For each, look up `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`.
3. If any path is classified `strict_local` or `strict_local_maximum` → ABORT. Surface offending file. Do not commit.
4. Commit with message format: `YYYY-MM-DD | module | short summary`.

**Note**: with the public-override, the consequence of a strict-local leak is more severe (publicly visible immediately). HIMAYAH gate must be enforced rigorously.

## Pre-push checklist

1. `git diff origin/main..HEAD --stat` — what's actually going up.
2. Re-scan for any path matching strict-local globs.
3. If clean, push.
4. After push, `gh repo view --json visibility` should show `"PUBLIC"` (acknowledged override).

## Commit-message convention

`YYYY-MM-DD | module | short summary` — e.g. `2026-05-15 | NIZAM | add overload_flag schema`.

## Force-push policy

Never force-push to `main` after initial sync, except for the one-time history reconciliation when adopting the nizamcore placeholder commit (documented in `NIZAMCORE_INTEGRATION.md`).

## If you change your mind later

To flip back to private:
```powershell
gh repo edit seifelsherbinyy/nizamcore --visibility private --accept-visibility-change-consequences
```

Update this doc and `POP_TEMPLE.json` to reflect the new state.
