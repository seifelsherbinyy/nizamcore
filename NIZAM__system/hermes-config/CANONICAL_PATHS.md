# NIZAM × Hermes — Canonical Runtime Paths (VPS)

> So future verification isn't tripped by the repo clone. The `~/nizamcore` clone is **reference/source**, NOT the live runtime read-path for files that have a runtime copy.

## Canonical runtime (what the live agent reads)
| Artifact | Canonical runtime path (VPS) | Notes |
|---|---|---|
| Persona override map | `/home/nizam/.hermes/nizam/agent_personas.json` | **P3 router MUST read here.** Stale clone copy quarantined → `~/nizamcore/NIZAM__system/agent_personas.json.STALE_PRE_B2` |
| Governance plugin | `/home/nizam/.hermes/plugins/nizam-governor/` | enabled in `config.yaml plugins.enabled` |
| Hermes config | `/home/nizam/.hermes/config.yaml` | |
| Secrets | `/home/nizam/.hermes/.env` (600) | |
| Identity | `/home/nizam/.hermes/SOUL.md`, `/home/nizam/.hermes/user.md` | |
| NIZAM runtime state | `/home/nizam/.hermes/nizam/` | pause/kill/mode flags, seen-keys, last_mirror, atrest.key, pulse, budgets, greenlist |
| **Agent memory (distinct store)** | `/home/nizam/.hermes/memories/MEMORY.md` + `state.db` | hermes-native, separate from the ledger. **Secret-scrubbed** at write (v1.8.0): dispatch-rewrite scrubs inbound + `pre_tool_call` scrubs `memory`-tool args. Mode `600`. At-rest encryption N/A (hermes reads MEMORY.md directly); protected by 600 + FDE-accepted-risk + the no-secrets-land-here guarantee. |
| Ledgers (canonical) | `/home/nizam/nizamcore/NIZAM__system/ledgers/*.jsonl` | LEARNING/EVENT/NIZAM-COSTS/DEAD_LETTER + HIMAYAH refusals |
| Encrypted Drive mirror | `drive-crypt:NIZAM_ledgers` | async, ciphertext (encrypt-before-upload) |
| rclone binary / conf | `/home/nizam/.local/bin/rclone` · `/home/nizam/.config/rclone/rclone.conf` | **hardcoded absolute** in plugin (no PATH/HOME reliance) |

## Reconciled to canonical in P3 (2026-05-30) — clones quarantined
| Artifact | Canonical runtime path | Quarantined clone copy |
|---|---|---|
| Persona map | `~/.hermes/nizam/agent_personas.json` | `…/agent_personas.json.STALE_PRE_B2` |
| Router config | `~/.hermes/nizam/config/router.config.yaml` | `…/config/router.config.yaml.STALE_PRE_CANON` |
| Intent exemplars | `~/.hermes/nizam/config/intent_exemplars.yaml` | `…/config/intent_exemplars.yaml.STALE_PRE_CANON` |
| Persona soul files (12) | `~/.hermes/nizam/personas/*.json` | `…/personas.STALE_PRE_CANON/` (dir) |

Confirmed: **no live copy of any of these remains in `~/nizamcore`** — nothing can load them as live. The `nizam-governor` plugin reads the persona map from `~/.hermes/nizam/agent_personas.json` (proven on a real runtime turn).

Still clone-only (not yet used by the router; reconcile if needed): `extraction.config.yaml`.

## Operational hardening (this pass)
- `nizam-governor` uses **absolute** `RCLONE`/`RCLONE_CONF` and `HOME = os.environ.get("HOME") or "/home/nizam"` — verified working under `env -i` (no PATH, no HOME), the cron/systemd worst case.
- **Crypto/HIMAYAH path untouched** — drive-crypt encrypt-before-upload unchanged.
