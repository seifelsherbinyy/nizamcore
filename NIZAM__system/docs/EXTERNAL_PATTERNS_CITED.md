# EXTERNAL_PATTERNS_CITED

POP cherry-picks patterns from open-source projects with attribution. Each pattern is independently re-implemented — no upstream code dependency.

| Source | License | Stars (as of 2026-05) | Patterns cherry-picked into POP |
|---|---|---|---|
| [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) | MIT | 1,100 | AI-first frontmatter (`## For future Claude`, recency markers, confidence levels); orientation files (`index.md`, `log.md`, `SOUL.md`, `CRITICAL_FACTS.md`); skill-as-markdown command format; vault-first research; "vault evolves, not grows" reconciliation principle; `/pop-health` vault audit concept; cross-CLI portability hooks (designed for Phase 2/3). |
| [jamesmcroft/obsidian-ai-second-brain](https://github.com/jamesmcroft/obsidian-ai-second-brain) | MIT | 7 | "Skills are encoded paths, not prompts" principle; optional PARA overlay for Phase 2 Obsidian/Notion interop. |
| [NicholasSpisak/second-brain](https://github.com/NicholasSpisak/second-brain) | (see repo) | 323 | Karpathy LLM Wiki pattern: raw/ → wiki/ separation. |
| **SESHAT** (Seif's prior local project at `C:\Users\selsherb\OneDrive - amazon.com\SESHA`) | n/a (private) | n/a | Symbol + functional folder naming pair; `_index.json` per folder; `<TEMPLE>.json` master commandments file; three inviolable gates pattern; immutable archive with `MANIFEST.json`; append-only `.jsonl` ledgers; ISO 8601 with `Z`; persona JSON files; semver on registry files. |
| **nizamcore** (Seif's private repo at `https://github.com/seifelsherbinyy/nizamcore`) | (private) | n/a | TBD — pattern audit happens in Phase 1.5 after `gh auth login`. See `NIZAMCORE_INTEGRATION.md`. |

## Note on attribution

Cherry-picked patterns are conceptual; no source code is copied. POP's files were written independently against these design ideas. License obligations for cherry-picked design ideas (vs. code) are minimal under MIT, but attribution is preserved for audit and credit.
