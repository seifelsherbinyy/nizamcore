# Coding Conventions

**Analysis Date:** 2026-06-14

---

## Persona JSON Shape (schema version 1.1)

All persona definitions live in `NIZAM__system/personas/*.json` and must validate against `NIZAM__system/schemas/persona.schema.json`.

### Required "soul fields" (immutable — never rewrite)

```json
{
  "module":          "UPPERCASE_MODULE_NAME",   // ^[A-Z][A-Z_]*$ — matches pillar_registry.json
  "meaning_ar":      "arabic root + role gloss",
  "phase":           1,                          // integer: 1, 2, or 3
  "role":            "One-sentence functional role.",
  "mode":            "Operating mode descriptor.",
  "tone":            "Voice and posture.",
  "inputs":          ["array of strings, minItems: 1"],
  "outputs":         ["array of strings, minItems: 1"],
  "operating_rules": ["array of strings, minItems: 1"],
  "skills":          ["/slash-command-name"],    // pattern: ^/[a-z][a-z0-9-]*$
  "gates":           ["HIMAYAH", "SUKOON", "THABAT"],  // OR structured object (see below)
  "privacy":         "strict_local",             // enum: review_before_commit | strict_local |
                                                 //       strict_local_maximum | private_github | mirror_sanitized
  "ledger_writes_to": ["EVENT_LEDGER.jsonl"]
}
```

### Optional soul fields

- `codename` — human-facing name (e.g. "Tariq", "Khaldun")
- `namesake` — historical figure reference
- `voice_constraints` — explicit speech rules
- `opening_voice` — startup greeting string or object (INVARIANT: zero subjective inner state; biometric fields only)
- `modes` — array of mode names if multiple modes
- `default_language` — e.g. `"egyptian_arabic"`
- `mode_bundle` — path to mode bundle directory
- `domains_covered` — array of strategic domain strings
- `target_folders` — object of `{ "key": "MODULE__folder/subfolder/" }` paths
- `target_folder` — single string (older single-target personas)

### Runtime block (v1.1 additive — append-only, never rewrite soul fields)

```json
{
  "schema_version": "1.1",
  "runtime": {
    "agent_enabled": true,
    "primary_model": "claude-sonnet-4-6",   // enum of approved models
    "reviewer_model": "kimi-k2.6",          // or null
    "fallback_chain": ["deepseek-v4-pro", "kimi-k2"],
    "delegates_to": ["Khaldun", "Khalid"],  // codenames only
    "max_tool_calls": 12,                   // 0–20
    "timeout_seconds": 240,                 // 5–600
    "retry_backoff_seconds": [2, 5, 15],    // 1–5 integers
    "context_sources": [                    // explicit file paths (anti-hallucination)
      "SOUL.md",
      "NIZAM__system/personas/TARIQ.json"
    ],
    "egress_class": "strict_local",         // matches privacy class enum
    "cost_ceiling": {
      "soft_usd": 50,
      "hard_usd": 300
    },
    "feedback_ledger": "NIZAM__system/ledgers/LEARNING_LEDGER.jsonl",
    "writes_to_ledgers": ["STRATEGY_LEDGER.jsonl"],
    "gates": {
      "pre":       ["SUKOON"],
      "pre_write": ["HIMAYAH"],
      "post":      ["THABAT"]
    }
  }
}
```

### Approved primary_model values

`deepseek-v4-pro`, `deepseek-v4-flash`, `kimi-k2`, `kimi-k2.6`, `claude-sonnet-4-6`, `local-llama-3b`, `local-deterministic`

### Privacy / egress class enum

| Value | Allowed egress targets |
|---|---|
| `strict_local_maximum` | None — hard blocked everywhere |
| `strict_local` | laptop_disk, vps_encrypted_volume, drive_crypt, telegram_operator, zdr_inference |
| `review_before_commit` | laptop_disk, vps_plaintext, github_private, drive_clear, telegram_operator, zdr_inference |
| `private_github` | All of review_before_commit + notion_sanitized |
| `mirror_sanitized` | Same as private_github |

### Existing persona files

`NIZAM__system/personas/AMMAR.json`, `BADAN.json`, `HIKMAH.json`, `MAL.json`, `MARSAD.json`, `MUNAWARA.json`, `NAQD.json`, `NIZAM.json`, `SHURA.json`, `TAFRIGH.json`, `TARIQ.json`

---

## Schema Naming Conventions

All JSON schemas live in `NIZAM__system/schemas/` and are registered in `NIZAM__system/SCHEMA_INDEX.json`.

### File naming pattern

```
<artifact_name>.schema.json
```

Examples: `event_ledger.schema.json`, `persona.schema.json`, `body_signal.schema.json`, `agent_message.schema.json`

### Schema file structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://pop.local/schemas/<name>.schema.json",
  "title": "Human-readable title",
  "type": "object",
  "required": ["field1", "field2"],
  "properties": { ... }
}
```

- Draft-07 is standard; the persona schema uses 2020-12 (noted exception).
- `$id` uses `https://pop.local/schemas/` namespace for local-only schemas.
- `$id` uses `https://github.com/seifelsherbinyy/nizamcore/schemas/` for persona schema.

### Schema Index registration

Every new schema must be added to `NIZAM__system/SCHEMA_INDEX.json` in this format:

```json
{
  "name": "artifact_name",
  "phase": 1,
  "path": "schemas/artifact_name.schema.json",
  "describes": "One-line description of what this schema validates",
  "live": true
}
```

The `"scaffolded": true` field is used for schemas that exist but are not yet in active use.

### Fixture files

Schema fixtures live in `NIZAM__system/schemas/fixtures/` with naming `<artifact_name>.fixture.json`. Example: `NIZAM__system/schemas/fixtures/conversational_session.fixture.json`.

---

## Protocol and Workflow Document Structure

### Protocols (`NIZAM__system/protocols/`)

Protocols are **cadence-driven** chained skill sequences (recurring time-based routines).

**Index file:** `NIZAM__system/protocols/_PROTOCOLS_INDEX.md` (leading underscore = index file convention)

**Protocol file naming:** `<protocol_name>.md` (snake_case, no date prefix)

Examples: `daily_morning.md`, `weekly_sunday.md`, `monthly_close.md`, `crisis_sukoon_red.md`, `agent_delegation_protocol.md`

**Protocol document structure:**

```markdown
# Protocol - <Name> (~<budget>, <cadence>)

> One-sentence description.

## Frontmatter
- **Cadence**: <time period>
- **Budget**: ~<N> minutes
- **Gates checked**: HIMAYAH, SUKOON, THABAT
- **Skills chained**: `/skill-a` -> `/skill-b` -> `/skill-c`

## Procedure
### Step 1 - <Name>
<Instructions>

## Output
- <artifact 1>
- <artifact 2>
```

### Workflows (`NIZAM__system/workflows/`)

Workflows are **scenario-driven** skill chains (triggered by a situation, not a calendar).

**Index file:** `NIZAM__system/workflows/_WORKFLOWS_INDEX.md`

**Workflow file naming:** `<scenario_name>.md` (snake_case)

Examples: `idea_to_decision.md`, `finance_decision.md`, `contradiction_resolution.md`, `weekly_synthesis.md`

---

## Skill File Structure (`NIZAM__system/skills/`)

Skills are **single encoded paths**: trigger → target folder → naming → template → gates → procedure. Frontmatter is binding, not advisory.

**Index file:** `NIZAM__system/skills/_SKILLS_INDEX.md`

**Skill file naming:** `<module-codename>-<verb>.md` (kebab-case, module prefix)

Examples: `hikmah-weekly.md`, `marsad-monitor.md`, `badan-daily-signal.md`, `tariq-annual-review.md`

Alternative naming for companion skills: `<skill_name>.skill.md` (e.g. `council_review.skill.md`, `himayah_egress_guard.skill.md`)

**Standard skill frontmatter (YAML, all keys binding):**

```yaml
---
name: <skill-name>
module: MODULE_SYMBOL
trigger: "/skill-command"
target_folder: MODULE__folder/subfolder/
naming_pattern: "{YYYY-MM-DD}.md"            # or "{YYYY}-W{WW}.md", "{YYYY}_annual_review.md"
template: NIZAM__system/templates/<name>.template.md   # or null
frontmatter_schema: NIZAM__system/schemas/<name>.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl]
sources:                                      # optional, list of input files/folders
  - NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---
```

**Standard skill body:**

```markdown
## For future Claude
<One-paragraph context for any Claude instance invoked via this skill.>

## Procedure
1. <Step 1 with concrete action>
2. <Step N>
```

The `## For future Claude` section is mandatory — it provides anti-hallucination context for stateless Claude invocations.

---

## Template Conventions (`NIZAM__system/templates/`)

**Template file naming:** `<artifact_name>.template.md` (snake_case with `.template.md` suffix)

Examples: `daily_signal.template.md`, `weekly_battle.template.md`, `annual_review.template.md`, `career_radar_daily.template.md` (proposed)

**Template structure:**

```markdown
---
type: <artifact_type>                   # matches schema "type" field
pop_module: MODULE_SYMBOL
pop_privacy: strict_local
updated: <YYYY-MM-DD>                   # placeholder, filled at use time
confidence: high
tags: [tag1, tag2]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
<Context about this template type and schema reference.>

# <Artifact Title> — <YYYY-MM-DD>

> **Disclaimer**: <If medical/financial/advisory content, include disclaimer here.>

## Section 1
- Field:

## Section 2
<content>
```

Key rules:
- YAML frontmatter is required on every template.
- `## For future Claude` block is mandatory.
- Use `<YYYY-MM-DD>` angle-bracket placeholders for date slots (filled at generation time).
- Disclaimers are mandatory for BADAN (medical), MAL (financial), and advisory templates.

---

## Ledger Event Record Shape and Append Discipline

### Ledger registry (`NIZAM__system/ledgers/`)

| File | Privacy | Integrity |
|---|---|---|
| `EVENT_LEDGER.jsonl` | review_before_commit | hash-chained |
| `LEARNING_LEDGER.jsonl` | review_before_commit | hash-chained |
| `DECISION_LEDGER.jsonl` | review_before_commit | hash-chained |
| `DEAD_LETTER.jsonl` | strict_local | hash-chained; manual replay only |
| `STRATEGY_LEDGER.jsonl` | strict_local | RFC 6962 Merkle + Ed25519 STH |
| `BATTLE_LEDGER.jsonl` | strict_local | hash-chained |
| `FINANCE_LEDGER.jsonl` | strict_local | hash-chained |
| `BODY_LEDGER.jsonl` | strict_local | hash-chained |
| `PULSATION_LEDGER.jsonl` | strict_local | hash-chained |
| `COUNCIL_LEDGER.jsonl` | strict_local | hash-chained |

### Written row shape (all ledgers)

Every row written by `ledger_writer.append()` has this exact envelope:

```json
{
  "ts":            "2026-05-28T20:18:00Z",
  "ledger":        "EVENT_LEDGER",
  "row_id":        "<uuid4>",
  "trace_id":      "<uuid4-end-to-end-chain-id>",
  "actor":         "Ammar",
  "action":        "verb_noun",
  "module":        "NIZAM__governor",
  "privacy_class": "review_before_commit",
  "prev_hash":     "<sha256-of-prior-row | 0*64 for first row>",
  "payload":       {},
  "row_hash":      "<sha256-of-row-excluding-row_hash>"
}
```

- `ts` format: `%Y-%m-%dT%H:%M:%SZ` (UTC, always).
- `prev_hash` for the genesis row is exactly 64 zero characters.
- `row_hash` is SHA-256 of `json.dumps(row_without_row_hash, sort_keys=True, ensure_ascii=False)`.
- Lines are single-line JSON with `sort_keys=True, ensure_ascii=False` + newline terminator.

### Append discipline (from `NIZAM__system/governor/ledger_writer.py`)

1. **Check kill switch**: if `NIZAM_KILL_ALL=1`, raise `RuntimeError` — no write.
2. **Verify tail integrity**: call `verify_tail(name)` — refuse on broken hash chain.
3. **Write row**: `path.open("a")` → `fh.write(line)` → `fh.flush()` → `os.fsync()` (best-effort on Windows).
4. **STRATEGY_LEDGER only**: call `strategy_sth.publish_sth()` after every append (best-effort; failure must not block the append).
5. **NEVER open `.jsonl` files directly** outside of `ledger_writer.py` — all code calls `ledger_writer.append(name, payload, ...)`.

### Payload shape for EVENT_LEDGER (common pattern from live rows)

```json
{
  "note":          "human-readable description",
  "target":        "AgentCodename",
  "kind":          "COMMAND | TRIGGER | CRISIS",
  "confidence":    0.95,
  "classification": "strict_local",
  "trace_id":      "<uuid4>",
  "sukoon_mode":   "normal | yellow | red"
}
```

### Default privacy_class assignment in `append()`

- `EVENT_LEDGER`, `LEARNING_LEDGER`, `DECISION_LEDGER`, `DEAD_LETTER` → `"review_before_commit"`
- All others → `"strict_local"`

---

## Dated-File Naming Conventions

### Standard date prefix

```
YYYY-MM-DD__<name>.md          # recommended separator: double underscore
YYYY-MM-DD.md                  # date-only (e.g. daily signals: 2026-05-28.md)
YYYY_annual_review.md          # year-only for annual artifacts
YYYY-W<NN>.md                  # ISO week (e.g. 2026-W22.md) for weekly artifacts
```

### MAKHZAN archive snapshots

```
MAKHZAN__archive/YYYY-MM-DDTHH-MM-SSZ/       # ISO 8601 UTC with hyphens for colons
MAKHZAN__archive/YYYY-MM-DDTHH-MM-SSZ-<slug>/  # optional slug suffix
```

### File-preservation / no-overwrite rule

**Never overwrite an existing precious file. Create a new dated file instead.**

- Existing ledger rows: append-only via `ledger_writer.append()`. Never edit prior rows.
- Existing plan/review markdown files: do not modify in place. Produce a new dated file or a dated amendment note.
- Templates: never overwrite. Skills that "update" plans do so by writing a new dated document.
- The only exception is `log.md` (human-readable mirror of EVENT_LEDGER) which is append-only in reverse-chronological order.

---

## Python Code Style

### Module header pattern

Every `.py` module begins with:
```python
"""<module_name.py> — <one-line purpose>.

<Extended description paragraph.>

Pure stdlib. / Pure stdlib (except <optional dep>).
"""
from __future__ import annotations
```

- The `from __future__ import annotations` import is **mandatory first import** in every file.
- Modules note their stdlib purity prominently; external deps are exceptions, not defaults.

### Import ordering

```python
from __future__ import annotations          # always first

import <stdlib modules>                     # standard library
from pathlib import Path                    # stdlib
from typing import Any, Iterable            # stdlib

from . import classifier, kill_switch       # relative package imports
from .governor import ledger_writer         # relative with subpath
```

### Type annotations

- All public functions are fully annotated: `def func(x: str, y: int = 0) -> dict[str, Any]:`
- Use `X | Y` union syntax (requires `from __future__ import annotations`).
- Use `str | None` not `Optional[str]`.
- Use lowercase generic aliases: `dict`, `list`, `tuple`, not `Dict`, `List`, `Tuple`.

### Config loading pattern

Config is loaded from JSON/YAML policy files via stdlib only. Pattern from `classifier.py`:

```python
_DEFAULT_REPO = Path(__file__).resolve().parents[N]
_CONFIG_PATH = _DEFAULT_REPO / "NIZAM__system" / "policies" / "POLICY.json"

_cache: dict[str, list[tuple[str, str]]] = {}

def _load_rules(config_path: Path = _CONFIG_PATH) -> list[tuple[str, str]]:
    key = str(config_path)
    if key in _cache:
        return _cache[key]
    data = json.loads(config_path.read_text(encoding="utf-8"))
    # ... process ...
    _cache[key] = rules
    return rules
```

Key rules:
- Always `encoding="utf-8"` on every file read/write.
- Use module-level `_cache` dict for in-process caching of config files.
- Config path is resolved relative to `__file__` using `.parents[N]` — never hardcoded absolute paths.
- `_DEFAULT_REPO = Path(__file__).resolve().parents[N]` pattern for finding repo root.

### Secret / credential loading

Credentials are retrieved from environment variables only — never hardcoded:

```python
def get_github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
```

Pattern from `HIFZ__github_version_control/scripts/nizam_governor_lib.py`.

### Error handling

- Raise typed, descriptive exceptions: `raise RuntimeError("NIZAM_KILL_ALL=1 — writer halted (HIMAYAH panic stop)")`
- Error messages always include the blocking reason and relevant config field.
- No silent failures on critical paths — errors propagate up.
- Best-effort operations (e.g. `os.fsync`, `strategy_sth.publish_sth`) are wrapped in `try/except Exception: pass` with a comment explaining why failure is non-fatal.

### Logging

No `logging` module in governor/router code. Status is reported via:
- Return values (e.g. `Decision(allowed=bool, reason=str, ...)`)
- Raised exceptions for blocking conditions
- Ledger rows for audit trail
- Print statements only in `if __name__ == "__main__":` CLI blocks

### Module-level constants

Module-level constants use `SCREAMING_SNAKE_CASE`. Private helpers use `_leading_underscore`:

```python
KNOWN_LEDGERS = { "EVENT_LEDGER", "DECISION_LEDGER", ... }
_DEFAULT_REPO = Path(__file__).resolve().parents[2]
_LEDGERS_DIR = _DEFAULT_REPO / "NIZAM__system" / "ledgers"
```

### Public API pattern

Each module exposes a minimal public API and documents it in the module docstring:

```python
"""
Public API:
    classify(rel_path: str) -> str
    classify_many(paths: Iterable[str]) -> dict[str, str]
    is_egress_blocked(rel_path: str, target: str) -> tuple[bool, str]
"""
```

### CLI entrypoint pattern

Every governor module includes a minimal CLI block:

```python
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: module.py <arg>")
        sys.exit(2)
    # ... minimal CLI logic ...
```

### sys.path injection in tests

Tests inject repo root into `sys.path` at the top, before any local imports:

```python
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
```

Then imports use full dotted paths: `from NIZAM__system.governor import classifier`.

### Dataclasses for structured results

Structured return values use `@dataclass` from `dataclasses`:

```python
@dataclass
class Decision:
    allowed: bool
    reason: str
    classification: str
    rel_path: str
    target: Plane
    def __bool__(self) -> bool:
        return self.allowed
```

### Enums for controlled vocabularies

`str, enum.Enum` pattern is used for plane/target constants:

```python
class Plane(str, enum.Enum):
    LAPTOP = "laptop_disk"
    VPS_PLAINTEXT = "vps_plaintext"
```

---

## File-Preservation / No-Overwrite Rule (Summary)

This is a system-level constraint, not just a style preference:

1. **Ledgers are append-only.** No row is ever modified or deleted. `ledger_writer.py` is the sole writer.
2. **Plans/reviews/sessions are dated artifacts.** When content changes, create a new dated file; do not edit the prior one.
3. **Snapshots go to MAKHZAN.** Before any significant refactor or migration, a snapshot is taken to `MAKHZAN__archive/YYYY-MM-DDTHH-MM-SSZ/`.
4. **Schemas are additive.** The persona schema v1.1 documents this explicitly: "Soul fields are immutable across versions; runtime block is additive per Blueprint v7 sec.6."
5. **Write-to-tmp then os.replace() for atomic writes.** Used in MARSAD file writes to avoid corrupting the original if a write fails (from `marsad-monitor.md`).
6. **New additions register in index files.** New skills → `_SKILLS_INDEX.md`. New schemas → `SCHEMA_INDEX.json`. New protocols → `_PROTOCOLS_INDEX.md`. New workflows → `_WORKFLOWS_INDEX.md`.

---

*Convention analysis: 2026-06-14*
