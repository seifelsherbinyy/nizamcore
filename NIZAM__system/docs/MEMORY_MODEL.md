# POP Memory Model

> How POP preserves continuity across sessions, across years, and across agents.

## Six layers of memory, in order of permanence

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 6 — IMMUTABLE ARCHIVE       MAKHZAN__archive/<ts>/    │ ← never edited
│   Timestamped snapshots with SHA256 MANIFEST                │
├─────────────────────────────────────────────────────────────┤
│ Layer 5 — APPEND-ONLY LEDGERS     NIZAM/ledgers/*.jsonl     │ ← one row per event
│   EVENT, DECISION, LEARNING, STRATEGY, BATTLE,              │
│   FINANCE, BODY, FAMILY                                     │
├─────────────────────────────────────────────────────────────┤
│ Layer 4 — CANONICAL CONTENT       <Module>__<function>/     │ ← evolves via reconcile
│   Brain dumps, sessions, plans, signals, person cards       │
├─────────────────────────────────────────────────────────────┤
│ Layer 3 — REGISTRIES + INDEXES    POP_TEMPLE.json + ...     │ ← updated with structure
│   POP_TEMPLE, POP_MASTER_REGISTER, SCHEMA_INDEX,            │
│   PROTOCOLS_INDEX, WORKFLOWS_INDEX, _SKILLS_INDEX,          │
│   per-folder _index.json                                    │
├─────────────────────────────────────────────────────────────┤
│ Layer 2 — PERSONAS + SCHEMAS      NIZAM/personas + schemas  │ ← occasional revision
│   Module roles, JSON schemas for every artifact type        │
├─────────────────────────────────────────────────────────────┤
│ Layer 1 — ORIENTATION FILES       root/4 files              │ ← Claude reads FIRST
│   CRITICAL_FACTS.md (~120 tokens, always loaded)            │
│   SOUL.md (identity, gitignored)                            │
│   index.md (page catalog)                                   │
│   log.md (human-readable timeline)                          │
└─────────────────────────────────────────────────────────────┘
```

## Read order in every session

When any Claude session opens POP, it should read in this order:

1. **`CRITICAL_FACTS.md`** (~120 tokens) — load mandatory constraints into the working set.
2. **`SOUL.md`** — if present, load identity / values / non-negotiables.
3. **`index.md`** — get the page catalog so you know where things live.
4. **`POP_TEMPLE.json`** — load the master commandments + gate definitions.
5. **The specific skill file you were invoked for** — read its frontmatter binding paths.
6. **Module-relevant persona JSON** — load tone + operating rules for the module.

This sequence puts ~500 tokens of foundation into context before any work begins. After this, queries into Layer 4 (canonical content) and Layer 5 (ledgers) are targeted, not exhaustive.

## Write order for any new artifact

When any skill writes a new file:

1. **Validate frontmatter against schema** (Layer 2 contract).
2. **Write canonical content** at the encoded `target_folder` (Layer 4).
3. **Append a row to the relevant ledger(s)** (Layer 5) — never overwrite existing rows.
4. **Mirror a sanitized one-liner to `log.md`** (Layer 1 — human read).
5. **If the operation rewrites existing notes**: snapshot affected files to MAKHZAN (Layer 6) BEFORE the rewrite.

## Memory expiration rules

| Memory type | When it can be edited / removed |
|---|---|
| Layer 6 — MAKHZAN | NEVER. Append-only forever. |
| Layer 5 — Ledgers | NEVER overwrite. Append-only. Corrections add new rows with `event_type: "correction"`. |
| Layer 4 — Canonical content | Edited via `/naqd-reconcile` (snapshot first). Marked stale via `superseded_by`. |
| Layer 3 — Registries | Updated when structure changes. Versioned (semver) for major changes. |
| Layer 2 — Personas / schemas | Revised carefully. Schema changes require migration plan + MAKHZAN snapshot. |
| Layer 1 — Orientation files | `CRITICAL_FACTS.md` updated rarely. `log.md` appended daily. `SOUL.md` revised by user only. |

## Continuity across agents

Because Layers 1–5 are markdown / JSON / JSONL files, *any* compatible agent (Claude Code, Codex, Gemini, OpenCode) can read POP. The agent-specific shims live in `NIZAM/docs/CROSS_CLI_BUILD.md`.

The memory model is **agent-portable**. If you switch agents, the memory survives the switch.

## Why this architecture

- **Layer 1** keeps token cost of orientation low (~500 tokens / session).
- **Layer 2** prevents schema drift and hallucinated frontmatter.
- **Layer 3** prevents path hallucination.
- **Layer 4** is where you (the human) actually live and write.
- **Layer 5** gives Claude a structured retrieval source for `/pop-recap`, `/pop-health`, `/shura-emerge`.
- **Layer 6** preserves history when Layer 4 rewrites happen.

Without all six layers, POP would either lose history (no MAKHZAN), drift silently (no ledgers), hallucinate paths (no schemas), or burn context every session (no orientation files).

## See also
- [`CONTINUITY_PROTOCOL.md`](CONTINUITY_PROTOCOL.md) — how state is preserved across sessions.
- [`DATA_MODEL.md`](DATA_MODEL.md) — the typed data model behind the memory layers.
- [`SKILL_DESIGN_PRINCIPLES.md`](SKILL_DESIGN_PRINCIPLES.md) — how skills interact with the memory model.
