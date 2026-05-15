# NOTION_PATHWAY (JADWAL — Phase 2)

> **Status**: designed, not yet built.
> **Role**: Structured dashboard layer — databases, filtered views, weekly reviews, task boards.

## Sync model
Manual or scripted promotion of **non-sensitive metadata only**:
- Decision titles (no body)
- Milestone names
- Weekly review headlines
- High-level progress metrics

## What's NEVER promoted
- Raw dumps, sessions, signals, finance baselines, body metrics, family data, strategic plan bodies.

## API token handling
- Notion API token lives in Windows credential manager.
- Never committed to git.
- Promotion script reads token from `$env:NOTION_TOKEN`, not from a file.

## Phase 2 work
1. Design databases: Weekly Reviews, Milestones, Decisions (titles only), Learning Principles.
2. Build promotion script: `NIZAM__system/skills/jadwal-promote.md`.
3. Document token rotation procedure.
