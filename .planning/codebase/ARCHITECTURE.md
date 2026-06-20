# Architecture

**Analysis Date:** 2026-06-14

## Pattern Overview

**Overall:** Persona-module governance system with a privacy-first, recovery-gated, append-only persistence model

**Key Characteristics:**
- Every module is a named Arabic-rooted "pillar" folder (`SYMBOL__description/`) mapped to a persona agent codename (e.g. TAFRIGH → Amin, SHURA → Salman)
- A three-gate firewall (HIMAYAH / SUKOON / THABAT) sits inline on every write path; no output is "complete" until all three gates pass
- All persistence is local-first, append-only; durable outputs sync to GitHub (framework only), Google Drive, and Notion via a governed dual-write path — never the reverse
- A deterministic IR-1..IR-8 rule engine in `NIZAM__system/config/nizam_router.py` dispatches inbound Telegram messages to the correct agent codename before any LLM is invoked
- The Hermes long-poll runner (`NIZAM__system/relay/poller.py`) is the sole Telegram ingestion point; no public webhook is required
- The governor (`NIZAM__system/governor/`) enforces all policies in pure stdlib — no LLM dependency

---

## Persona / Module Model

Each top-level pillar folder is a self-contained cognitive domain. The folder name encodes the domain (`SYMBOL__meaning`) and every folder registers itself in `NIZAM_MASTER_REGISTER.json` and declares its own `_index.json`.

**Codename → module mapping** (source: `NIZAM__system/agent_personas.json`, runtime config: `NIZAM__system/config/agents.registry.yaml`):

| Codename | Persona file | Module folder | Role |
|---|---|---|---|
| Amin | `NIZAM__system/personas/TAFRIGH.json` | `TAFRIGH__brain_dumper/` | Verbatim capture, near-silent |
| Salman | `NIZAM__system/personas/SHURA.json` | `SHURA__brainstormer/` | Co-thinking / brainstorm |
| Hazim | `NIZAM__system/personas/NAQD.json` | `NAQD__brain_griller/` | Red-team / critic |
| Khalid | `NIZAM__system/personas/MUNAWARA.json` | `MUNAWARA__tactical_strategy/` | Tactical 1/3/5-yr planning |
| Tariq | `NIZAM__system/personas/TARIQ.json` | `TARIQ__long_horizon_strategy/` | 10/15/20-yr Long War Map |
| Khaldun | `NIZAM__system/personas/HIKMAH.json` | `HIKMAH__learnings/` | Weekly synthesis + Islamic Cosmic Wisdom |
| Tahir | `NIZAM__system/personas/MARSAD.json` | `MARSAD__flight_radar/` | External intel scout |
| Hayat | `NIZAM__system/personas/BADAN.json` | `BADAN__body_health_system/` | Biometric witness (never diagnostic) |
| Sadiq | *(persona pending)* | `YAWMIYAT__journaling/` | Journaling steward, append-only |
| Yusra | *(persona pending)* | `SUKOON__recovery_first/` | Recovery voice-alias, never initiates |
| Ammar | `NIZAM__system/personas/AMMAR.json` | `NIZAM__governor` | Egress firewall, cost ceiling, ledger writer |
| Coordinator | `NIZAM__system/personas/NIZAM.json` | `NIZAM__system` | Orchestrator; routes, delegates, initiates ledger writes |

Each persona JSON defines 14 soul fields (identity, tone, contract, gates) and a runtime block (model, delegates, context sources). The codename layer in `agent_personas.json` overlays the persona without rewriting the soul fields.

---

## Layers (Memory Model)

Defined in `NIZAM__system/docs/MEMORY_MODEL.md`. Six layers in order of permanence:

**Layer 1 — Orientation Files:**
- Purpose: ~500 tokens loaded at every session open
- Location: `CRITICAL_FACTS.md`, `SOUL.md`, `index.md`, `log.md`
- Read order: CRITICAL_FACTS → SOUL → index.md → NIZAM_TEMPLE.json → skill file → persona JSON

**Layer 2 — Personas + Schemas:**
- Purpose: Role definitions and data contracts
- Location: `NIZAM__system/personas/*.json`, `NIZAM__system/schemas/*.json`
- Depends on: Nothing — foundational
- Used by: All agents, `ledger_writer.py`, `NIZAM__system/governor/`

**Layer 3 — Registries + Indexes:**
- Purpose: Path truth, folder inventory, protocol/workflow catalogs
- Location: `NIZAM_TEMPLE.json`, `NIZAM_MASTER_REGISTER.json`, `NIZAM__system/AGENT_MAPPING.json`, `NIZAM__system/PROTOCOLS_INDEX.json`, `NIZAM__system/SCHEMA_INDEX.json`, `NIZAM__system/WORKFLOWS_INDEX.json`, `NIZAM__system/pillar_registry.json`, per-folder `_index.json`
- Updated when: Structure changes (semver-versioned for major changes)

**Layer 4 — Canonical Content:**
- Purpose: The actual work product — brain dumps, sessions, plans, signals
- Location: Each module folder's typed subfolders (e.g. `TAFRIGH__brain_dumper/raw/`, `SHURA__brainstormer/sessions/`)
- Modified via: `/naqd-reconcile` skill (snapshot to MAKHZAN first)

**Layer 5 — Append-Only Ledgers:**
- Purpose: Immutable event record, cross-session continuity
- Location: `NIZAM__system/ledgers/*.jsonl`
- Invariant: Never overwrite; corrections append new rows with `event_type: "correction"`

**Layer 6 — Immutable Archive:**
- Purpose: Pre-change snapshots with SHA256 MANIFEST
- Location: `MAKHZAN__archive/<timestamp>/`
- Invariant: Never edited, append-only forever

---

## Control / Data Flow: Telegram → Agent → Ledger

### Startup sequence
When any session opens, the agent reads in this order:
1. `CRITICAL_FACTS.md` — mandatory constraints (always in context)
2. `SOUL.md` — identity / values
3. `index.md` — page catalog / path map
4. `NIZAM_TEMPLE.json` — master commandments, gate definitions, module registry
5. The invoked skill file (encoded paths in frontmatter)
6. Module-relevant persona JSON (tone + operating rules)

For Hermes relay sessions, `NIZAM__system/relay/env_loader.py` loads `.env` first, then `NIZAM__system/relay/poller.py` starts the long-poll loop.

### Per-message pipeline (source: `NIZAM__system/relay/coordinator.py` + `poller.py`)

```
Telegram getUpdates
    → NIZAM__system/relay/poller.py (long-poll loop; no public endpoint)
        → dedup.record(update_id)           # dedup.py: drop replays
        → auth.verify_user_id(update)       # auth.py: whitelist check
        → coordinator.process(update, uid)
            ├─ capture.persist(...)         # companion/capture.py: raw inbound written first
            ├─ runtime_events.persist_inbound(...)
            ├─ sukoon_gate.pre_gate(text)   # SUKOON gate — B4.4
            ├─ nizam_router.resolve(...)    # IR-1..IR-8 deterministic router — B4.5
            │       reads router.config.yaml + intent_exemplars.yaml
            ├─ [HIMAYAH egress check]       # B4.6 — classifier.is_egress_blocked()
            ├─ persona_runtime.run(...)     # LLM invocation (if not blocked, not protocol:)
            └─ ledger_writer.append(...)    # B4.7 — Ammar writes EVENT_LEDGER row
        → tg_send_message(reply)            # reply to operator
```

### Router resolver steps (IR-1..IR-8)
Defined in `NIZAM__system/config/nizam_router.py`:

1. **IR-1** — Command registry lookup (`/dump`, `/pulse`, `/shura`, etc.) → direct target
2. **IR-2** — Biometric pattern detector (HRV, recovery, strain triplet) → Hayat
3. **IR-3** — Occasion + planning term detector → Khalid
4. **IR-4** — Habit opener + lexicon match → Salman
5. **IR-5** — Explicit dump markers (`/tafrigh-capture`, "random thought") → Amin
6. **IR-6** — SUKOON overlay (does not change target; applies tone-only downshift)
7. **IR-7** — Kin planning detector → Khalid
8. **IR-8** — Exemplar Jaccard fallback; below 0.50 confidence → `fallback_capture` (Amin)

Confidence thresholds from `NIZAM__system/config/router.config.yaml`:
- `≥ 0.70` → auto_route
- `0.50–0.70` → confirm_band (single confirmation prompt, reviewer_model: kimi-k2.6)
- `< 0.50` → fallback to `/tafrigh-capture`

---

## The Three Gate Mechanisms

Gates are defined in `NIZAM_TEMPLE.json#gates` and enforced in the Python layer.

### HIMAYAH — Privacy Gate
- **Definition:** "Before any sync, commit, or external share, verify privacy classification."
- **Enforcement files:** `NIZAM__system/governor/classifier.py`, `NIZAM__system/governor/sync_arbiter.py`, `NIZAM__system/governor/scripts/pre_commit_check.py`
- **Policy source:** `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`
- **How it works:**
  1. `classifier.classify(rel_path)` → one of: `strict_local_maximum`, `strict_local`, `review_before_commit`, `private_github`, `mirror_sanitized`
  2. `classifier.is_egress_blocked(rel_path, target)` checks against `EGRESS_MATRIX`
  3. `sync_arbiter.decide(rel_path, Plane)` enforces the same matrix for cross-plane writes
  4. `.git/hooks/pre-commit` calls `pre_commit_check.py` — any path classified `strict_local` or `strict_local_maximum` blocks the commit
  5. In the relay coordinator (B4.6), `is_egress_blocked(capture_path, "telegram_operator")` gates the reply
- **Kill switch:** `NIZAM__system/governor/kill_switch.py` — `NIZAM_KILL_ALL=1` halts all writers

**Egress classes:**
| Classification | Allowed targets |
|---|---|
| `strict_local_maximum` | nothing leaves disk |
| `strict_local` | laptop_disk, vps_encrypted_volume, drive_crypt, telegram_operator, zdr_inference |
| `review_before_commit` | + vps_plaintext, github_private, drive_clear |
| `private_github` | + notion_sanitized |
| `mirror_sanitized` | same as private_github |

### SUKOON — Recovery Gate
- **Definition:** "Before any output-heavy session, check overload flags."
- **Enforcement file:** `NIZAM__system/relay/sukoon_gate.py`
- **Data source:** `SUKOON__recovery_first/overload_flags.jsonl` (last 24 hours)
- **How it works:**
  1. `sukoon_gate.pre_gate(text)` runs before every router call (coordinator B4.4)
  2. Returns `{downshift: bool, mode: "normal"|"supportive_reflection"|"crisis_protocol", reasons, recent_flag_count}`
  3. Crisis keywords (`panic`, `overload red`, `crisis`) → immediate `crisis_protocol` mode regardless of flags
  4. Any recent overload flag → `supportive_reflection` mode; NAQD/Hazim auto-downshifts to Salman
  5. In `nizam_router.resolve()`, `sukoon_hot=True` applies IR-6 overlay (tone-only, target unchanged unless crisis)
- **Crisis protocol:** Defined in `NIZAM__system/protocols/crisis_sukoon_red.md`; routes to `protocol:crisis_sukoon_red`; only `/sukoon-check`, `/tafrigh-capture`, and `/badan-red-flag-check` remain allowed
- **Agent registry gate config:** Every agent in `agents.registry.yaml` declares `gates: {pre: [SUKOON], pre_write: [HIMAYAH], post: [THABAT]}`

### THABAT — Continuity Gate
- **Definition:** "Before session close, append to event ledger."
- **Enforcement:** Operational protocol — `NIZAM__system/docs/CONTINUITY_PROTOCOL.md`; skill files declare THABAT in frontmatter; `ledger_writer.append()` is the implementation
- **How it works:**
  1. Every skill that writes significant output must append a row to `NIZAM__system/ledgers/EVENT_LEDGER.jsonl` at session close
  2. `log.md` gets a sanitized one-liner mirror
  3. If files were rewritten: MAKHZAN snapshot with MANIFEST must precede the rewrite
  4. The `thabat_ledger_closeout.skill.md` skill codifies the close sequence
- **No-data-loss guarantee:** The `write_path_sequence.mmd` diagram declares: "COMPLETE only when (a) record persisted, (b) audit row written, (c) pending queue reported"

---

## Persistence / No-Data-Loss Model

### Capture-first invariant
Raw capture to disk happens BEFORE routing, BEFORE LLM, BEFORE any gate check (see `coordinator.process()` — `capture.persist()` is the very first call).

### Ledger durability
`ledger_writer.append()` (`NIZAM__system/governor/ledger_writer.py`):
- Each row is hash-chained: `prev_hash` links to the prior row's `row_hash` (SHA-256)
- Every write is `fsync()`-ed before returning
- `verify_tail()` is called before every append; broken chain → refuses to write
- `STRATEGY_LEDGER` additionally publishes an RFC 6962 Merkle Tree Signed Tree Head (STH) via `NIZAM__system/governor/strategy_sth.py` on every append; STH files land in `NIZAM__system/ledgers/sth/`
- `NIZAM_KILL_ALL=1` env var immediately halts all ledger writes (checked first in every writer)

### Dual-write path (Phase 2, defined in `NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json`)
1. Agent → Steward (Ammar) with record + payload
2. Steward normalizes, computes `dedupe_key` ({Lane}:{Type}:{date}:{slug})
3. Primary write: Notion (CREATE or UPDATE) with retry ladder: 1s → 4s → 16s → DeadLetter queue
4. Secondary write: Google Drive (header includes `notion_page_id`, `dedupe_key`, `captured_at`, `repo_commit`)
5. Write-back: Notion row updated with Drive URL
6. Audit row appended to `NIZAM__system/ledgers/EVENT_LEDGER.jsonl`
7. **Last resort** (all layers down): serialize full JSON bundle to operator stdout — "§1.1 operator saves by hand"

Realized in `HIFZ__github_version_control/scripts/nizam_dual_write.py` and `nizam_drive_mirror.py`.

### DeadLetter queue
- Path: `NIZAM__system/ledgers/DEAD_LETTER.jsonl`
- Classification: `strict_local` (never commits to GitHub)
- Max attempts: 3; replay requires manual operator approval
- Owner: Ammar persona

### GitHub sync
Direction: local → GitHub only (one-way, defined in `NIZAM__system/policies/SYNC_POLICY.json#sync_direction`)
- Pre-commit hook (`NIZAM__system/governor/scripts/pre_commit_check.py`) blocks any file classified `strict_local` or `strict_local_maximum`
- Framework files (`schemas/`, `templates/`, `skills/`, `personas/`, `docs/`, `protocols/`, `workflows/`) are `private_github` — committed freely to private repo
- Personal content (sessions, journals, finance, body, SOUL.md) never commits

### Cost ceiling
`NIZAM__system/governor/cost_ceiling.py`:
- Soft ceiling: $50/month → WARN logged to EVENT_LEDGER
- Hard ceiling: $300/month → `CostCeilingExceeded` raised; recommends `NIZAM_KILL_ALL=1`
- State persisted in `NIZAM__system/ledgers/.cost-month.json` (gitignored); auto-rolls monthly

---

## Entry Points

**Hermes long-poll runner:**
- Location: `NIZAM__system/relay/poller.py`
- Invoked: `python -m NIZAM__system.relay.poller [--dry-run | --once]`
- Requires: `RELAY_MODE=live`, `TELEGRAM_BOT_TOKEN`, `NIZAM_TELEGRAM_ALLOWED_IDS`
- Dry-run mode: synthetic update, exercises full pipeline + EVENT_LEDGER write, no network

**Hermes plugin hooks:**
- Location: `NIZAM__system/hermes-plugins/nizam-governor/`
- Plugin: `plugin.yaml` (version 1.11.2) registers hooks: `pre_gateway_dispatch`, `pre_llm_call`, `post_llm_call`, `pre_tool_call`, `transform_llm_output`, `on_session_start`

**Scheduled pulse:**
- Location: `NIZAM__system/hermes-config/scripts/nizam-scheduled-pulse.py`

**Companion pulsation loop:**
- Location: `NIZAM__system/companion/pulsation/loops.py`
- Drives proactive HIKMAH reminders and context refresh

**Manual/conversational entry:**
- Claude loads orientation files (Layer 1) → invokes skill (`NIZAM__system/skills/<name>.md`) → reads persona JSON → performs work → appends ledger row (THABAT)

---

## Error Handling

**Strategy:** No silent operations (NIZAM_TEMPLE.json principle: `no_silent_operations`)

**Patterns:**
- Capture-first: raw text persisted before any processing — nothing lost even if routing fails
- DeadLetter queue: failed Notion/Drive writes enqueue rather than drop
- Last resort: if all persistence layers down, serialize full JSON to operator stdout (§1.1)
- Kill switch: `NIZAM_KILL_ALL=1` cleanly halts all writers without data corruption
- Hash-chain verification: `verify_tail()` on every append prevents writing to a corrupted ledger
- Retry ladder: 1s / 4s / 16s / max 3 attempts before DeadLetter

## Cross-Cutting Concerns

**Privacy enforcement:** HIMAYAH gate — `classifier.py` + `sync_arbiter.py` + pre-commit hook
**Cost control:** `cost_ceiling.py` — soft/hard USD limits per month, kill switch integration
**Logging:** Every significant event → `EVENT_LEDGER.jsonl` row via `ledger_writer.append(actor="Ammar")`
**Validation:** Every markdown artifact requires YAML frontmatter matching `note_frontmatter.schema.json`; JSONL rows require minimum fields (`ts`, `module`, `event_type`)
**Authentication:** Telegram operator whitelist enforced in `NIZAM__system/relay/auth.py`; `NIZAM_TELEGRAM_ALLOWED_IDS` env var

---

*Architecture analysis: 2026-06-14*
