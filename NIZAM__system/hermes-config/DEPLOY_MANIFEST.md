# NIZAM/Hermes Deploy Manifest

> Per build-discipline rule (#11, 2026-05-30): `D:\NIZAM` is the pre-live staging source of truth.
> This file records what is currently live on the VPS so local staging stays authoritative.
> **No automatic VPS pushes. Explicit operator confirmation required before any deploy.**

## Currently LIVE on VPS (nizam@31.97.154.5, `~/.hermes/`) — deployed under v2.1 autonomous full-authority, before rule #11

| Artifact | VPS path | Local staging mirror |
|---|---|---|
| Hermes config deltas | `~/.hermes/config.yaml` | `NIZAM__system/hermes-config/config.vps-snapshot.yaml` (redacted) |
| Secrets | `~/.hermes/.env` (mode 600) | sourced from `NIZAM-secrets.json` (not mirrored) |
| Identity — SOUL | `~/.hermes/SOUL.md` | `SOUL.md` |
| Identity — profile | `~/.hermes/user.md` | `user.md` |
| Governance plugin | `~/.hermes/plugins/nizam-governor/` | `NIZAM__system/hermes-plugins/nizam-governor/` |

### Config settings applied (live)
- `model.default: deepseek/deepseek-v4-flash`
- `display.personality: professional`
- `timezone: Africa/Cairo`
- `agent.max_turns: 7`  ⚠ conflicts with v3 "no hard caps" — pending resolution
- `memory.nudge_interval: 120`
- `provider_routing.data_collection: deny` + `require_parameters: true`  (HIMAYAH model-egress)
- `plugins.enabled: [nizam-governor]`

### Gates passed: G2 (doctor green), G3 (ZDR-routable verified).

## NOT yet done (v2.1 remainder)
- G4 leak tests, G5 round-trips (need gateway live + operator on Telegram)
- Relay-lift (systemd), Phase B (code-fix push via GitHub MCP), Phase I (rotate leaked OpenRouter key)

## v3 reframe (2026-05-30) — NOT yet built; requires plan + per-piece confirmation
Cloud-canonical topology (Drive = sink for all data), per-turn single-persona routing from
`agent_personas.json`, capture-first-to-Drive, HIMAYAH-as-egress-governance + encrypt-before-upload,
egress-gated voice, token soft-warn instrumentation (no hard caps), Hayat capacity routing.
