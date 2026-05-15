# HIFZ — GitHub Version Control

Arabic: حفظ — "preservation."

## Purpose
Version-control automation beyond what root `.git` provides. Pre-commit hooks, mirror scripts, repo automation, audit utilities.

## Status
Shell only. Planned content:

- `hooks/` — git pre-commit / pre-push hooks (e.g., a script that re-checks `PRIVACY_CLASSIFICATION.json` before every commit and refuses strict-local paths).
- `scripts/` — PowerShell or Python automation (snapshot-on-major-change, MAKHZAN manifest auto-generation, push verification).
- `docs/` — operational notes specific to this repo.

## Planned skills
- `/hifz-precommit-check` — wrap `git status` + privacy classifier.
- `/hifz-snapshot` — convenience wrapper around the MAKHZAN snapshot routine.

## Privacy
review_before_commit. Scripts may contain repo metadata but never secrets.
