# CROSS_CLI_BUILD

> POP skills are platform-agnostic markdown. Same source → multiple agent CLIs (Claude Code, Codex, Gemini, OpenCode). Pattern source: [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain).

## Why cross-CLI

If you switch agents (Anthropic ↔ OpenAI ↔ Google ↔ open-source), POP's skill library should travel with you. Skill files in `NIZAM__system/skills/*.md` are already platform-agnostic — they encode paths and procedures, not API-specific calls.

## Platform-specific shims

Each platform expects skill discovery in a different location:

| Platform | Skill discovery path | Routing file |
|---|---|---|
| Claude Code | `~/.claude/commands/<name>.md` (symlink to POP skill) | none |
| Codex CLI | `.codex/commands/<name>.md` | `AGENTS.md` |
| Gemini CLI | `.gemini/commands/<name>.md` | `GEMINI.md` |
| OpenCode | `.opencode/commands/<name>.md` | `AGENTS.md` |

## Build script (pattern, not yet implemented)

A future `HIFZ__github_version_control/scripts/build-cli-shim.ps1`:

1. Argument: target platform (`claude-code` / `codex-cli` / `gemini-cli` / `opencode`).
2. For each skill in `NIZAM__system/skills/*.md`:
   - Validate frontmatter against skill-design principles.
   - Generate platform-specific shim (symlink for Claude Code; copy + routing for others).
3. Generate `AGENTS.md` / `GEMINI.md` routing file from `_SKILLS_INDEX.md`.
4. Write a `build_manifest.json` so re-runs are idempotent.

## Why not implement today

Implementing for multiple platforms is engineering work that compounds maintenance. Default to **Claude Code only** until Phase 1+2+3 are stable and there's evidence a switch is needed.

## Path of least surprise

If you do switch:
1. Run build script for new platform.
2. Confirm new platform reads `CRITICAL_FACTS.md` and `SOUL.md` on session start.
3. Test one skill end-to-end (e.g., `/sukoon-check`).
4. Migrate logging from `EVENT_LEDGER.jsonl` to new platform's session log convention if different.

## Status
Designed only. No build script yet. POP runs on Claude Code natively as of v3.x.
