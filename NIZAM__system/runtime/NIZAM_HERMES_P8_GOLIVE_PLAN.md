# P8 — Go-Live Plan (gateway + G4/G5 + relay-lift) — STAGED, HOLD FOR CONFIRM

> Stage-first. Nothing deployed/started. This is the go-live; deploy only on explicit operator confirm.
> Interactive: G4/G5 require the bot live + operator sending Telegram messages to @nizam_relay_sherbiny_bot.

## Sequence (on confirm)
1. Start gateway **foreground** (`hermes gateway run`, backgrounded via nohup) — live but not yet persistent.
2. Run **G4** (governance gate tests) — operator sends specified messages; I verify ledgers/refusals.
3. Run **G5** (end-to-end round-trips) — operator sends; I verify replies + ledgers + latency.
4. On G4+G5 pass → **relay-lift** (persistence) → **reboot-recovery** check.

## G4 — Governance gate tests (each = a real Telegram message → defined pass condition)
| # | Test | Operator sends | PASS condition |
|---|---|---|---|
| G4.1 | **AHEL hard-block** | `#ahel test note about family` | captured to `strict_local_capture.jsonl` (VPS-only); **NOT** in `LEARNING_LEDGER`; **NOT** mirrored to Drive; no model reply; `HIMAYAH__egress_refusals.jsonl` row `reason=ahel_hard_block` |
| G4.2 | **Capture-first dual-write** | any normal thought | `LEARNING_LEDGER.jsonl` row **and** encrypted object in `drive-crypt:NIZAM_ledgers` |
| G4.3 | **Egress audit** | (same turn) | `HIMAYAH__egress_audit.jsonl` `model_call` row `greenlit=true`; reply latency unaffected by async Drive |
| G4.4 | **SUKOON downshift** | (I seed 2 red overload flags) then a message | reply is a single warm line, no enumerated failure-mode list |
| G4.5 | **Pause/resume** | `/pause` → a thought → `/resume` → a thought | paused thought buffered (no LLM call/cost row); resumed thought processed |
| G4.6 | **Kill switch** | `/kill` → a thought → (I `rm` flag) | post-kill thought fully skipped (no cost row, no capture); restore returns to normal |
| G4.7 | **Greenlight gate** | (audit inspection) | every egress row carries `integration`/`greenlit`; nothing un-greenlit silently passes |

**G4 pass = all of G4.1–G4.7 green.** Any FAIL halts (esp. G4.1 = P0-class privacy bug).

## G5 — End-to-end round-trips (the product working)
| # | Test | Operator sends | PASS condition |
|---|---|---|---|
| G5.1 | **Capture (Amin)** | a free thought | Amin self-intro + near-silent capture; `LEARNING_LEDGER`+Drive+cost rows |
| G5.2 | **/shura (Salman)** | `/shura` then a topic | Salman self-intro + generative reply (options/opening question) |
| G5.3 | **/naqd (Hazim)** | `/naqd` then a plan | Hazim self-intro + adversarial reply (weakest-assumption-first, no flattery) |
| G5.4 | **/cost** | `/cost` | today + MTD per-provider $/budget/% breakdown |
| G5.5 | **/muhasaba** | `/muhasaba` | baseline-vs-now + flow(7d) |
| G5.6 | **/pulse** | `/pulse recovery 60 hrv 45 strain 12` | logged + opening_voice (objective only) + capacity band |
| G5.7 | **Latency** | (across the above) | **p95 < 30s** end-to-end per turn |

**G5 pass = G5.1–G5.6 behave per contract + G5.7 latency.**

## Relay-lift (persistence) — DECISION REQUIRED
- **Option A (cleanest):** `hermes gateway install` (user systemd service) + **one-time `sudo loginctl enable-linger nizam`** (your Hostinger root creds, once) → auto-restart + boot-start.
- **Option B (sudo-free):** cron `@reboot` starts the gateway (nohup) + a keepalive cron (every 2 min: restart if down). Durable, no root.

After lift: reboot the VPS → confirm bot answers a `/pulse` post-reboot (proves auto-start).

## "Dumb relay / no sensitive data on host" — RECONCILIATION (confirm which governs)
The v2.1 "dumb relay, zero sensitive data on host" was **superseded by v3**, which made the **VPS the canonical live runtime** holding working state: `SOUL.md`, the canonical ledgers, `.env`, persona map. So sensitive data **does** live on the host — protected by: `chmod 600`, Drive-ciphertext mirror, AHEL/strict_local-maximum never reaching cloud, and **FDE accepted-risk (option b)**.
- The **relay process itself stays dumb**: the systemd/cron unit only runs `hermes gateway` (orchestration/webhook/scheduling) — it adds no new data path or capability.
- **Confirm:** govern relay-lift under the **v3 VPS-canonical posture** (sensitive-on-host, mitigated as above) — *not* the retired v2.1 zero-sensitive stance (which would require re-architecting SOUL/ledgers to Drive-only with VPS as pure cache, a separate project).

## Non-goals at lift
No voice (P7 deferred). No new integrations. No Gmail/Calendar. Cron limited to relay keepalive (+ optional daily digest later).
