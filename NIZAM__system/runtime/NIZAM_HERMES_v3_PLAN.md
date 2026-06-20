# NIZAM × Hermes — v3 Architecture Plan (PLAN_ONLY)

> Issued: 2026-05-30 (Africa/Cairo). Mode: **PLAN_ONLY** — staged at `D:\NIZAM`, nothing built/deployed.
> Discipline (locked): **stage-local-first → explicit operator confirm → deploy.** Never auto-push to VPS.
> Supersedes the build assumptions of NIZAM_HERMES_LIVE_PRODUCTION_v2.1 (G2/G3 + Phase-E governance remain the live baseline-of-record, SHA256-pinned).

## 0. Resolved decisions (this session)
- **Limits:** no hard token caps. Graduated soft-warns 70/85/95% → Telegram + AUDIT. `agent.max_turns`→30 (runaway-only safety). Default soft-warn; greenlight required before any hard limit.
- **Persistence:** **phased dual-write** — VPS canonical (in-flight truth + conversation context) **+ async/non-blocking encrypted Drive mirror** (durable audit, inspectable). Start with the learning ledger, then soul + remaining ledgers. Telegram replies never block on the Drive write.
- **Baseline:** current VPS config/SOUL/user.md/plugin = confirmed baseline-of-record, SHA256-pinned (`hermes-config/BASELINE_SHA256.txt`). New discipline is forward-only.

## 1. Target architecture
- **Hermes = voice; NIZAM Core = mind.** Cloud-resident: device normally offline, all interaction via Telegram `@nizam_relay_sherbiny_bot`. VPS = live runtime/orchestration/webhook/scheduling + working state. **Drive = durable encrypted mirror (canonical audit); VPS = canonical live truth (dual-write).** GitHub = code/schemas only, never data.
- **Per-turn single-persona routing** from `agent_personas.json` (one override point), each honoring a distinct behavioral contract (below).
- **HIMAYAH = egress governance** (not prevention): encryption at rest (VPS + Drive), encrypt-before-upload (Drive stores ciphertext), least-privilege per integration, audit every external write, greenlight before any new outbound.

## 2. Verified ground truth (live state, 2026-05-30)
- Personas source-of-truth = `NIZAM__system/agent_personas.json` (11 codenames).
- `learning_ledger.schema.json` ✓ present. `ELEVENLABS_API_KEY` ✓ on VPS. BADAN targets WHOOP/Garmin/HRV/recovery.
- HIMAYAH model-egress already enforced: `provider_routing.data_collection: deny` (live).
- nizam-governor plugin live (hooks + 7 commands), cost+ledger writing verified.

## 3. BLOCKERS (must clear before the dependent phase builds)
- **B1 — rclone absent on VPS.** The Drive encrypt-before-upload path doesn't exist. Need: install rclone + configure the `drive-crypt` remote (recovery on file). Blocks dual-write Drive mirror (Phase 2).
- **B2 — persona reassignment.** v3 says **Sadiq = YAWMIYAT/journaling** and **Yusra = SUKOON voice-alias (never initiates)**, but `agent_personas.json` has Sadiq→QARAR and Yusra→AHEL/family. AHEL family steward role then needs a new owner (or stays under Ammar/strict_local_maximum). **Operator confirm required** before the router phase.
- **B3 — biometric feed.** `opening_voice` objective-biometrics invariant needs a live recovery/HRV/strain source (WHOOP/Garmin). No confirmed feed yet. Blocks Hayat opening-voice (Phase 6).
- **B4 — Drive auth mechanism.** Clarify: hermes `auth.json` vs rclone vs google-workspace skill as the Drive credential path.

## 4. Persona behavioral contracts (router targets)
| Codename | Pillar | Contract | Register |
|---|---|---|---|
| Amin | TAFRIGH | Lossless capture; mirror minimally; ≤1 disambiguating Q; never analyze/advise; near-silent | silent |
| Salman | SHURA | Generative co-thinking; framings; hold options open; opening questions | warmest |
| Hazim | NAQD | Adversarial; name weakest assumption; counter-case; red-team | coldest, not cruel |
| Khalid | MUNAWARA | Tactical 1/3/5-yr + quarterly | neutral |
| Khaldun | HIKMAH | Weekly synthesis / muhasaba | neutral |
| Hayat | BADAN | Biometric advisory, never diagnostic; objective fields only | factual |
| Sadiq | YAWMIYAT* (v3) | Journaling steward (*was QARAR — B2) | reflective |
| Yusra | SUKOON voice-alias* (v3) | Voice render only; never initiates (*was AHEL — B2) | warm/soft |
| Ammar | governor | Egress firewall, cost, kill switch, ledger writer; no LLM | deterministic |
- Cross-cutting: accurate empathy + honest pushback over flattery; precise, short, logic-based. **Hard invariant: `opening_voice` only objective biometrics; Hermes never claims to feel.**

## 5. Phased build (each: stage at D:\NIZAM → confirm → deploy → validate)
- **P0 — Reconcile & unblock.** Resolve B2 (persona map) → update `agent_personas.json` staged. Decide B4 Drive auth. Install+configure rclone drive-crypt on VPS (clears B1). Raise `max_turns`→30.
- **P1 — Capture-first dual-write (learning ledger).** Earliest-hook write of every inbound message → VPS learning ledger (sync, before LLM, idempotent dedupe) **+ async encrypted Drive copy**; misparse → dead-letter + retry, never silent drop. Validate: ledger rows on both sinks; reply latency unaffected.
- **P2 — Token instrumentation.** Consumption tracking per model/provider; 70/85/95% graduated warnings → Telegram + AUDIT; no hard cap. Surface MTD via `/cost`.
- **P3 — Per-turn persona router.** Resolve active trigger/open thread → load single persona from `agent_personas.json` (one override point) → enforce its contract via injected context + (where available) model selection. Grounds in `router.config.yaml` + `intent_exemplars.yaml`.
- **P4 — HIMAYAH egress governance.** Encryption at rest (VPS + Drive ciphertext), least-privilege creds per integration, audit-log every external write, greenlight gate for new outbound. Extend nizam-governor.
- **P5 — Continuous-learning / AUDIT (muhasaba).** Soul-mutation diffs vs prior baseline; baseline-vs-now on demand; version-bound via `learning_ledger.schema.json`. Soul joins the dual-write.
- **P6 — Hayat capacity routing + opening_voice.** Biometric feed (B3) → capacity gate (HIGH ≤3 deep / MEDIUM 1–2 / LOW TINY-MODE / no-data → MEDIUM-with-LOW-fallback). Objective-biometrics-only invariant. Skips/misses/contrary votes first-class, shame-free.
- **P7 — Voice (egress-gated).** ElevenLabs TTS over already-surfaced non-sensitive text only, via Yusra's register; never raw brain-dump/journal; never sole sink. Text remains source of truth.
- **P8 — Validate & lift.** Gateway live → G4 governance leak tests + G5 round-trips (Telegram) → systemd relay-lift on `/confirm relay_lift`. Phase B (code-fix push via GitHub MCP). Phase I (rotate leaked OpenRouter key).

## 6. Carry-over from v2.1 (still open)
- G4 leak tests, G5 round-trips (need gateway live + operator on Telegram).
- Phase B repo code-fixes push (GitHub MCP). Phase I secret rotation (closes R1 leaked-key window).
