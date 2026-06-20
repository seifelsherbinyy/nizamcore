# HIMAYAH Posture — Egress Governance (v3, P4)

> HIMAYAH redefined for the cloud topology: **egress *governance*, not prevention.** Govern, audit, and greenlight outbound; encrypt sensitive data so the provider cannot read it.

## 1. Encryption at rest
| Layer | State | Notes |
|---|---|---|
| **Google Drive** | ✅ ciphertext | `drive-crypt` encrypt-before-upload — Drive stores ciphertext only; provider cannot read NIZAM data |
| **AHEL / family (strict_local_maximum)** | ✅ Fernet at-rest, **VPS-only** | Written to `LEARNING_LEDGER` with `ahel:true` + `text_enc` (Fernet); **AHEL written to ledger + VPS, encrypted at rest, NOT mirrored to Drive** — the mirror sends an AHEL-excluded projection (absence in the cloud, not just encryption). Governor **v1.10.0** (`_build_ledger_projection` / `_mirror_ledger_async`). |
| **VPS sensitive files** | ✅ access-control (`chmod 600`) | `.env`, `SOUL.md`, `user.md`, `rclone.conf` are `600` (owner-only) |
| **VPS full-disk** | ☑️ **ACCEPTED-RISK (option b)** | root `/dev/sda1` ext4, no LUKS. Operator decision 2026-05-30: **accept** access-control (`600`) + Drive-ciphertext + AHEL-never-cloud as sufficient mitigation; a destructive LUKS re-provision isn't worth the downtime now. **Revisitable later.** |

**Recommendation:** treat FDE as a deliberate, flagged gap. Highest-sensitivity material (`strict_local`, AHEL) should prefer encrypted-at-rest storage (e.g., an encrypted volume or the drive-crypt remote) over the bare ext4 root.

## 2. Least-privilege credentials (per integration)
| Integration | Credential | Scope | Posture |
|---|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | model inference | `data_collection=deny` enforced (ZDR-routed) |
| Anthropic | `ANTHROPIC_API_KEY` | reviewer model | no-train default |
| ElevenLabs | `ELEVENLABS_API_KEY` | TTS (P7) | egress-gated to non-sensitive text only |
| Telegram | `TELEGRAM_BOT_TOKEN` | bot gateway | allow-list = operator id 8001780136 |
| Google Drive | `rclone [drive]` token | **full `drive` scope** | **deliberate, operator-reviewed grant** (cross-Drive agent by design); data still ciphertext via drive-crypt |
| GitHub | (none) | public repo | read-only, no PAT needed |

No MCP servers configured (clean egress surface).

## 3. Audit every external write
`nizam-governor` logs **every** outbound to `HIMAYAH__egress_audit.jsonl`:
- **model_call** (post_llm_call) — provider, model, est_usd
- **drive_mirror** (async mirror) — google_drive, file
- **tool:<name>** (pre_tool_call) — browser/search → `web`, tts → `elevenlabs`, terminal → `shell`

Each row carries `integration`, `channel`, `greenlit` (bool). Refusals → `HIMAYAH__egress_refusals.jsonl` (AHEL hard-block, etc.).

## 4. Greenlight gate (new outbound)
`~/.hermes/nizam/egress_greenlist.json` lists approved integrations. Any egress to a **non-greenlit** integration is **flagged** — `egress_ungreenlit` event + Telegram soft-warn — never silently blocked (governance, not prevention). Operator approves a new integration with **`/greenlight <name>`**; `/greenlight` (no arg) lists current.

Default greenlist: `openrouter, anthropic, elevenlabs, telegram, google_drive, github, web`.

## 5. Invariants
- **AHEL/family is ordinary context** (v3.1: cloud-model hard-block RETIRED — family is allowed context, not a blocked tier). But **AHEL written to ledger + VPS, encrypted at rest, NOT mirrored to Drive** — the Drive mirror sends an AHEL-excluded projection (governor v1.10.0). Absence in the cloud > encryption-in-the-cloud, for the most sensitive tier.
- Secrets are scrubbed before any at-rest write and rewritten upstream so no downstream sink (agent context, memory tool, reply) sees plaintext.
- `data_collection=deny` on every OpenRouter call (ZDR-constrained).
- No hard caps anywhere (soft-warn only).
