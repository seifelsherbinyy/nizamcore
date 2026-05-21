# JADWAL — Notion Dashboards

Arabic: جدول — "table / schedule."

## Purpose
Notion mirror as a structured dashboard layer. Databases, filtered views, weekly reviews, task boards.

## What syncs (sanitized only)
- Decision titles (no body).
- Milestone names.
- Weekly review headlines.
- High-level progress metrics.

## What NEVER syncs
- Raw dumps, sessions, signals, finance baselines, body metrics, family data.

## API token handling
- Notion API token: `$env:NOTION_TOKEN` — never in git.
- Promotion script reads from environment, never from file.

## Dual-write governor (active)

Runtime records sync to NIZAM // POP via [`/nizam-governor-push`](../NIZAM__system/skills/nizam-governor.md). Config: [`DUAL_WRITE_GOVERNOR.json`](../NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json).

Pre-flight: `python HIFZ__github_version_control/scripts/notion_preflight.py`

## Status (legacy promote skill)

Shell promote path still deferred. To activate full JADWAL promote:
1. Create Notion integration token in Notion settings.
2. Set `$env:NOTION_TOKEN`.
3. Design databases (Weekly Reviews, Milestones, Decisions, Learning Principles).
4. Build `/jadwal-promote` skill.

## Reference repo
[`aegis_rpm_brightmind`](https://github.com/seifelsherbinyy/aegis_rpm_brightmind) — sibling repo using Notion + AI bot patterns. Consider for inspiration.

## Doctrine
[`NIZAM__system/docs/NOTION_PATHWAY.md`](../NIZAM__system/docs/NOTION_PATHWAY.md)

## Privacy
mirror_sanitized_metadata_only.
