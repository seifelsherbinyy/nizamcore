# SKILL_DESIGN_PRINCIPLES

> Skills are encoded paths and conventions, not free prompts.
> They produce reliable grounded output instead of hallucinated guesses.

Pattern source: [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) (MIT), [jamesmcroft/obsidian-ai-second-brain](https://github.com/jamesmcroft/obsidian-ai-second-brain) (MIT). Re-implemented independently.

## Required frontmatter fields

| Field | Purpose |
|---|---|
| `name` | Unique skill identifier (matches filename without .md) |
| `module` | Which POP module owns it (TAFRIGH/SHURA/NAQD/SUKOON/NIZAM/...) |
| `trigger` | The exact slash command, including argument shape |
| `target_folder` | Where output files are written |
| `naming_pattern` | Filename template (e.g., `{ISO8601_UTC_FS}.md`) |
| `template` | Path to the markdown template to start from |
| `frontmatter_schema` | Schema the output's YAML must validate against |
| `gates` | Which gates fire: HIMAYAH, SUKOON, THABAT |
| `privacy` | strict_local / review_before_commit / private_github |
| `appends_event_to` | Which ledger(s) get a row |

## Required content sections

1. `## For future Claude` — 1–3 lines explaining the skill's intent. Mandatory.
2. `## Procedure` — numbered steps. Each step references concrete paths from the frontmatter.

## Forbidden in skills

- Free-form "be creative" instructions without path constraints.
- Hallucinable paths (always reference frontmatter fields).
- Silent file operations (must surface intended path before write).
- Skipping gate checks.

## Adding a new skill

1. Copy an existing skill file as template.
2. Update frontmatter completely. Validate against the principles above.
3. Add an entry to `NIZAM__system/skills/_SKILLS_INDEX.md`.
4. Update the owning persona JSON's `skills` array.
5. Add a one-line entry to `index.md` under the appropriate module section.
