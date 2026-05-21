# HIFZ — GitHub Version Control

Arabic: حفظ — "preservation."

## Purpose
Version-control automation beyond what root `.git` provides. Pre-commit hooks, mirror scripts, repo automation, audit utilities.

## Status

**Governor scripts (implemented):**

- [`scripts/nizam_drive_mirror.py`](scripts/nizam_drive_mirror.py) — GitHub `main` → Google Drive root mirror
- [`scripts/nizam_dual_write.py`](scripts/nizam_dual_write.py) — Notion + Drive runtime dual-write
- [`scripts/notion_preflight.py`](scripts/notion_preflight.py) — verify `dedupe_key`, `DriveLink`, `captured_at`
- [`scripts/test_governor_lib.py`](scripts/test_governor_lib.py) — unit tests (no API)
- [`requirements-governor.txt`](requirements-governor.txt) · [`.env.example`](.env.example)

See [`NIZAM__system/docs/DUAL_WRITE_GOVERNOR.md`](../NIZAM__system/docs/DUAL_WRITE_GOVERNOR.md).

**Planned:**

- `hooks/` — git pre-commit / pre-push hooks (e.g., a script that re-checks `PRIVACY_CLASSIFICATION.json` before every commit and refuses strict-local paths).
- `docs/` — operational notes specific to this repo.

## Planned skills
- `/hifz-precommit-check` — wrap `git status` + privacy classifier.
- `/hifz-snapshot` — convenience wrapper around the MAKHZAN snapshot routine.

## Privacy
review_before_commit. Scripts may contain repo metadata but never secrets.
