# CONTINUITY_PROTOCOL

> How POP state is preserved across sessions, days, and years — so a session in 2030 can pick up where 2026 left off.

## The THABAT gate (continuity)

`THABAT` (ثبات — "constancy / continuity") is one of POP's three inviolable gates. Every session-closing skill must append to the EVENT_LEDGER. No exceptions.

## Session lifecycle

### Session open
1. Read orientation files (Layer 1 of memory model).
2. Read POP_TEMPLE.json + relevant persona JSONs.
3. Read the specific skill file invoked.
4. Read `log.md` last 10 lines for recent context.
5. Read EVENT_LEDGER last 10 entries for cross-skill context (optional, when relevant).

### Session work
1. Each skill writes per its encoded paths.
2. Each artifact gets validated frontmatter.
3. Each significant action appends to a ledger (EVENT minimum; module-specific ledger if applicable).

### Session close (THABAT gate)
1. Final ledger append confirming session boundary if work was substantial.
2. `log.md` mirror with sanitized one-liner.
3. If files were rewritten via reconciliation: MAKHZAN snapshot complete with MANIFEST.

## Cross-session continuity guarantees

| What gets preserved | Where |
|---|---|
| What happened, when | EVENT_LEDGER.jsonl (Layer 5) |
| What was decided | DECISION_LEDGER.jsonl |
| What was learned | LEARNING_LEDGER.jsonl |
| What changed at strategic level | STRATEGY_LEDGER.jsonl |
| What battles were fought / won / lost | BATTLE_LEDGER.jsonl |
| Financial trajectory | FINANCE_LEDGER.jsonl (strict_local) |
| Body trajectory | BODY_LEDGER.jsonl (strict_local) |
| Family support history | FAMILY_LEDGER.jsonl (strict_local) |
| Identity / values | SOUL.md |
| Architecture / commandments | POP_TEMPLE.json |
| Folder inventory + privacy | POP_MASTER_REGISTER.json |
| Schemas (data contracts) | NIZAM/schemas/*.json |
| Skill procedures | NIZAM/skills/*.md |
| Templates | NIZAM/templates/*.md |
| Protocols (cadence chains) | NIZAM/protocols/*.md |
| Workflows (scenario chains) | NIZAM/workflows/*.md |
| Doctrine docs | NIZAM/docs/*.md |
| Pre-change snapshots | MAKHZAN__archive/<ts>/ |

## Long-horizon continuity

The system is designed to be readable by future-Seif in 5, 10, 20 years. Specifically:

1. **No proprietary formats**: everything is markdown, JSON, JSONL — readable in any text editor.
2. **No vendor lock-in**: agent-portable (any LLM with file access can use POP).
3. **No silent erasure**: MAKHZAN preserves prior states.
4. **Self-documenting structure**: README + _index.json in every folder explains itself.
5. **Versioned registries**: POP_TEMPLE.json carries `platform_version` semver.

## Agent-handoff protocol

If switching agents (Claude → Codex → Gemini → OpenCode):

1. Run a `/pop-health` audit in the current agent.
2. Snapshot to MAKHZAN with trigger `agent_handoff_<from>_<to>`.
3. Document the handoff in `STRATEGY_LEDGER` with `event_type: "agent_switched"` if material to operations.
4. On the new agent, build platform-specific shims per [`CROSS_CLI_BUILD.md`](CROSS_CLI_BUILD.md).
5. First task in the new agent: read `CRITICAL_FACTS.md` + `index.md` + last 20 EVENT_LEDGER lines to load context.

## Decade-scale continuity

POP is designed to outlast any specific tool. Things that must survive a decade:
- **SOUL.md** — identity / values / non-negotiables. User-maintained.
- **POP_TEMPLE.json** — operating commandments.
- **All canonical content** in module folders.
- **All ledgers** (append-only forever).
- **All MAKHZAN snapshots** (immutable forever).

Things that may change:
- Specific skill implementations (the encoded paths can evolve).
- Schema definitions (with migration + MAKHZAN snapshot).
- Folder structure (rarely; logged to STRATEGY_LEDGER if it happens).
- The agent itself.

The boundary between "must survive" and "may change" is the durable contract POP makes with future-self.

## Failure modes for continuity

| Failure | Recovery |
|---|---|
| Ledger row written without `ts` | `/pop-health` flags as schema violation; re-write with timestamp |
| File rewritten without MAKHZAN snapshot | NAQD reconciliation skill is supposed to enforce this; if missed, write a `corrective_snapshot` event and snapshot from current state (acknowledged loss of prior state) |
| Skill drift (skill rewrites itself in a way that breaks frontmatter contract) | `/pop-health` flags; revert from MAKHZAN |
| Agent switch breaks continuity | Re-bootstrap on new agent via the read order in MEMORY_MODEL.md |
| Catastrophic data loss (laptop death) | Local backups beyond POP scope — but the GitHub remote at github.com/seifelsherbinyy/nizamcore has the public framework |

## What this protocol does NOT promise

- **Backup of strict-local content**: GitHub has the framework; user is responsible for local backups of strict-local files (`SOUL.md`, journals, finance, body, family). Use a separate encrypted backup (Cryptomator, age, etc.).
- **Long-term server availability**: GitHub could disappear. Keep a local clone + at least one secondary location for the public framework.

## See also
- [`MEMORY_MODEL.md`](MEMORY_MODEL.md) — six layers of memory.
- [`DATA_MODEL.md`](DATA_MODEL.md) — typed data model behind the layers.
- [`GITHUB_PRIVACY.md`](GITHUB_PRIVACY.md) — visibility rules.
