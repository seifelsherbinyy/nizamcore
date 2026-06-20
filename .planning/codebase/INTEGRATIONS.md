# External Integrations

**Analysis Date:** 2026-06-14

## Telegram Bot (Primary Operator Interface)

**Role:** Sole inbound intake channel for operator messages; outbound reply channel for all agent responses and scheduled pulse notifications.

**Implementation:**
- Long-poll runner: `NIZAM__system/relay/poller.py` — calls `api.telegram.org/bot{token}/getUpdates` via `urllib.request` (stdlib only, no python-telegram-bot package)
- Pipeline: `getUpdates → dedup.record() → auth.verify_user_id() → coordinator.process() → tg_send_message(reply)`
- Auth: user ID whitelist (`NIZAM_TELEGRAM_ALLOWED_IDS` env var); 409 conflict detection when Hermes gateway also polls
- Webhook alternative: `NIZAM__system/relay/webhook.py` (exists but long-poll is the deployed path)
- Coordinator: `NIZAM__system/relay/coordinator.py` — routes each update through SUKOON gate → IR-1..IR-8 router → agent stub → HIMAYAH egress check → ledger append
- Hermes plugin hooks: `NIZAM__system/hermes-plugins/nizam-governor/__init__.py` — `pre_gateway_dispatch` hook captures messages, scrubs secrets, resolves route before LLM

**Credentials:**
- `TELEGRAM_BOT_TOKEN` — bot token issued by BotFather (env var; never committed)
- `NIZAM_TELEGRAM_ALLOWED_IDS` / `TELEGRAM_ALLOWED_CHAT_IDS` — comma-separated operator user IDs

**Modes:**
- `RELAY_MODE=standby` (default) — refuses to poll; safe state pre-launch
- `RELAY_MODE=live` — enables continuous polling loop

**Scheduled Pulses (outbound):**
- Three Hermes cron jobs: `nizam-morning-pulse` (09:00), `nizam-afternoon-pulse` (15:00), `nizam-evening-pulse` (21:00) — all Cairo time
- Script: `NIZAM__system/hermes-config/scripts/nizam-scheduled-pulse.py`
- Installer: `tools/setup_hermes_scheduled_telegram.py` — deploys via SSH/SCP to VPS, registers cron via `hermes_cli.main cron create --deliver telegram`
- Pulses include Google Calendar event counts and Gmail unread counts when Google OAuth is configured

**Operator slash commands (handled by hermes-plugin or relay coordinator):**
- `/dump <text>` → capture to TAFRIGH brain-dumper
- `/pulse recovery <n> hrv <n> strain <n>` → log biometrics to BODY_LEDGER
- `/shura` → brainstorm mode (Salman persona)
- `/naqd` → red-team mode (Hazim persona)
- `/hikmah` → Islamic Cosmic Wisdom mode (Khaldun persona)
- `/cost` → show MTD cost estimate
- `/pause` / `/resume` → buffer/un-buffer non-command messages
- `/kill` → engage hard kill switch
- `/greenlight <name>` → approve an outbound integration
- `/muhasaba` → soul/identity mutation report
- `/quiet` → toggle persona self-introductions

---

## LLM Providers (via OpenRouter primary)

**Role:** Model inference for agent personas (Coordinator, Salman, Hazim, Tariq, Khaldun, etc.)

**Primary Provider — OpenRouter:**
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Implementation: `NIZAM__system/relay/providers.py` (`OpenRouterProvider`), Hermes config: `NIZAM__system/hermes-config/config.vps-snapshot.yaml`
- All model calls route through OpenRouter per rule R4 (not direct to provider)
- ZDR constraint: `"provider": {"data_collection": "deny"}` set in every payload
- Credential: `OPENROUTER_API_KEY`
- Default model: `deepseek/deepseek-v4-flash` (routing-class, fast/low-cost)
- Per-agent models defined in `NIZAM__system/config/agents.registry.yaml`

**Model Roster (from agents.registry.yaml and hermes-plugin):**
- `deepseek/deepseek-v4-flash` — Coordinator, Amin, Tahir, Hayat (routing-class)
- `deepseek/deepseek-v4-pro` — Salman, Khalid (brainstorm/tactical)
- `claude-sonnet-4-6` / `anthropic/claude-sonnet-4.6` — Hazim (red-team), Tariq (long-horizon), Khaldun (synthesis)
- `kimi-k2.6` — reviewer_model for all agents (dual-lane critic)

**Fallback Providers:**
- Anthropic direct: `https://api.anthropic.com/v1/messages` (`AnthropicProvider` in `providers.py`; credential `ANTHROPIC_API_KEY` / `CLAUDE_API_KEY`)
- OpenAI: `https://api.openai.com/v1/chat/completions` (`OpenAIProvider`; credential `OPENAI_API_KEY`)
- `build_provider()` in `providers.py` checks `OPENROUTER_API_KEY` first, then `OPENAI_API_KEY`, then `ANTHROPIC_API_KEY`

**Cost Tracking:**
- Every LLM call appends a row to `NIZAM__system/ledgers/NIZAM-COSTS.jsonl` via `_post_llm` hook
- Soft-warn thresholds at 70/85/95% of monthly budget: OpenRouter $30, Anthropic $20 (`NIZAM__system/hermes-config/nizam-budgets.json`)
- Hard ceiling: $50 soft / $300 hard enforced by `NIZAM__system/governor/cost_ceiling.py`

---

## Google Drive (Encrypted Ledger Mirror + Repo Mirror)

**Role — Encrypted ledger mirror (operational):**
- LEARNING_LEDGER, EVENT_LEDGER, NIZAM-COSTS.jsonl, HIMAYAH egress audit, BODY_LEDGER are mirrored via rclone-crypt after every capture session
- Cipher: encrypt-before-upload (Drive stores ciphertext only); remote name `drive-crypt:`; target path `NIZAM_ledgers`
- Transport: `rclone copy` called as subprocess from hermes-plugin (`NIZAM__system/hermes-plugins/nizam-governor/__init__.py`)
- rclone binary: `/home/nizam/.local/bin/rclone` (absolute path; no PATH/HOME reliance)
- rclone conf: `/home/nizam/.config/rclone/rclone.conf`
- Throttle: 30-second debounce (`MIRROR_THROTTLE_SEC`); MIRROR-1 pattern = immediate attempt if >30s since last + trailing Timer(30) for final flush

**Role — Repo mirror (framework content):**
- Script: `HIFZ__github_version_control/scripts/nizam_drive_mirror.py`
- Fetches GitHub tree via API → uploads blobs as Drive files; preserves runtime folders (`Records`, `Projects`, `_Archive`)
- Uses service account credentials (`GOOGLE_APPLICATION_CREDENTIALS`) via `google-api-python-client`
- Target Drive folder ID: `1N_Cx5i4UPxp7qkCb6WxA3TYPgion4RUi`

**Role — Records/Documents:**
- `.docx` records written to Drive via `google-api-python-client` (Weekly Reviews, Meetings, Check-Ins)
- Path pattern: `Records/{lane}/{filename}` (lanes: Personal, Amazon, Outreach, Faith, Health, Relationship, Recovery)
- Dual-write config: `NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json`

**Credentials:**
- `GOOGLE_APPLICATION_CREDENTIALS` — path to service account JSON file (used by `nizam_governor_lib.build_drive_service()` for Drive API v3)
- `GOOGLE_OAUTH_CLIENT_SECRETS` (path to oauth-client.json) — for OAuth2 Calendar/Gmail flow
- `GOOGLE_OAUTH_TOKEN` (path to oauth-token.json) — cached OAuth2 token

**Local credential files (NOT read for values):**
- `NIZAM__system/connectors/oauth-client.json` — OAuth client credentials file
- `NIZAM__system/connectors/oauth-token.json` — OAuth token cache

---

## GitHub (Version Control / Framework Mirror)

**Role:** Immutable framework mirror; private repository for `mirror_sanitized` and `private_github` classified content.

**Repo:** `seifelsherbinyy/nizamcore` (private)

**Implementation:**
- Pre-commit hook (`NIZAM__system/governor/scripts/pre_commit_check.py`) calls `sync_arbiter.pre_commit_check()` before every git commit to block `strict_local` and `strict_local_maximum` content from leaving
- Drive mirror script (`HIFZ__github_version_control/scripts/nizam_drive_mirror.py`) fetches GitHub API tree to sync repo content to Drive
- Credential: `GITHUB_TOKEN` or `GH_TOKEN` env var

**What is committed (SYNC_POLICY.json `github_private` allowed list):**
- README.md, NIZAM_TEMPLE.json, NIZAM_MASTER_REGISTER.json, index.md, CRITICAL_FACTS.md, CHANGELOG.md
- `NIZAM__system/schemas/**`, `NIZAM__system/templates/**`, `NIZAM__system/skills/**`, `NIZAM__system/policies/**`, `NIZAM__system/docs/**`, `NIZAM__system/personas/**`
- `*/README.md`, `*/_index.json`

**What is NEVER committed (denied list):**
- Session data, raw brain dumps, signals
- `HAJR__quarantine/**`, `SOUL.md`, `MAL__financial_engine/**`, `BADAN__body_health_system/**`
- `STRATEGY_LEDGER.jsonl`, `BATTLE_LEDGER.jsonl`, `FINANCE_LEDGER.jsonl`, `BODY_LEDGER.jsonl`
- `.env`, `*token*`, `*secret*`, `*credentials*`

---

## Google Calendar, Tasks, Gmail (Companion Connectors)

**Role:** Read schedule context for scheduled pulses; write approved calendar events and tasks; read Gmail for pulse summary.

**Implementation:**
- OAuth2 adapter: `NIZAM__system/connectors/google_oauth.py`
- Route adapter: `NIZAM__system/connectors/google_adapter.py` (`GoogleConnectorAdapter`)
- Scopes: Calendar, Tasks, Gmail (read/modify/compose) — all in single token
- Credential lookup: `GOOGLE_OAUTH_CLIENT_SECRETS` and `GOOGLE_OAUTH_TOKEN` env vars (paths to JSON files)
- Used in scheduled pulse script (`hermes-config/scripts/nizam-scheduled-pulse.py`) to count calendar events and unread Gmail

**Status:** Disabled in CONNECTORS.json (`"enabled": false, "status": "disabled"`); activates when env vars are configured.

---

## Notion (Dual-Write Dashboard)

**Role:** Queryable structured database rows for Pulse, Witness, and Audit Log. Sanitized dashboards and milestone data for `JADWAL__notion_dashboards`.

**Implementation:**
- Dual-write via `HIFZ__github_version_control/scripts/nizam_dual_write.py`
- Notion workspace: `NIZAM // POP`
- Data sources: Pulse (`1be25cf8-dac2-45d4-a1c8-25e9824a6afc`), Witness (`0b8c702f-5691-4987-9096-b19dc4cafe51`), Audit Log (`916ed7de-27ef-4051-8e8a-d7fa8fb0d3bf`)
- Databases to resolve by name: Tasks, Projects, Inbox, CRM, Meetings, Habits, Objectives, Metrics
- Config: `NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json`
- Credential: `NOTION_TOKEN` env var (accessed via `nizam_governor_lib.get_notion_token()`)

**Status:** Phase 2 target. Currently `notion_JADWAL_phase2` in SYNC_POLICY. Connector listed as disabled in CONNECTORS.json.

---

## OAuth (Google — Prod Client)

**Role:** Google OAuth 2.0 client for Calendar/Tasks/Gmail access (NIZAM companion connectors).

**Files (existence only — contents never read):**
- `D:/NIZAM/nizam-prod-oauthclient.json` — production OAuth client credentials (top-level, synced to VPS by `tools/setup_hermes_scheduled_telegram.py`)
- `NIZAM__system/connectors/oauth-client.json` — runtime copy
- `NIZAM__system/connectors/oauth-token.json` — cached token

**VPS paths (authoritative):**
- `/home/nizam/.hermes/connectors/oauth-client.json`
- `/home/nizam/.hermes/connectors/oauth-token.json`
- Referenced in `/home/nizam/.hermes/.env` as `GOOGLE_OAUTH_CLIENT_SECRETS` and `GOOGLE_OAUTH_TOKEN`

---

## NIZAM-secrets.json (Secrets Bundle)

**Role:** Secrets bundle at repo root; existence confirmed, contents never read.

**File:** `D:/NIZAM/NIZAM-secrets.json` — production secrets; referenced by deploy/provisioning scripts in `D:/NIZAM/tools/`

---

## SerpAPI (MARSAD Flight Radar)

**Role:** Primary flight-price data feed for `MARSAD__flight_radar` module (Tahir persona).

**Implementation:**
- `MARSAD__flight_radar/radar/sources/serpapi_source.py`
- Package: `google-search-results==2.4.2`
- Credential: `SERPAPI_API_KEY` env var
- Listed as disabled in CONNECTORS.json (`serpapi_marsad`)

---

## Hermes Agent Runtime (VPS)

**Role:** Long-running agent process that hosts the nizam-governor plugin, routes Telegram messages, and manages cron jobs.

**Runtime location:** `/home/nizam/.hermes/hermes-agent/` on VPS
**CLI:** `hermes_cli.main` (installed in `hermes-venv` or VPS venv)
**Config:** `/home/nizam/.hermes/config.yaml`
**Plugin:** `/home/nizam/.hermes/plugins/nizam-governor/` (loads `NIZAM__system/hermes-plugins/nizam-governor/__init__.py`)
**Plugin version:** 1.11.2 (declared in `NIZAM__system/hermes-plugins/nizam-governor/plugin.yaml`)
**Plugin hooks registered:** `pre_gateway_dispatch`, `pre_llm_call`, `post_llm_call`, `pre_tool_call`, `transform_llm_output`, `on_session_start`

**VPS access:**
- IP: `31.97.154.5`, user: `nizam`
- SSH/SCP used by `tools/deploy_nizam_vps.py`, `tools/setup_hermes_scheduled_telegram.py`, `tools/sync_production_env_from_vps.py`

---

## rclone (Encrypted Drive Transport)

**Role:** Encrypted-before-upload transport layer for Drive ledger mirror (ciphertext stored in Drive, never plaintext for `strict_local` data).

**Remote name:** `drive-crypt:` (rclone crypt backend wrapping Google Drive)
**Target path:** `NIZAM_ledgers`
**Binary:** `/home/nizam/.local/bin/rclone` (hardcoded absolute; works under cron/systemd with no PATH)
**Config:** `/home/nizam/.config/rclone/rclone.conf`
**Invocation:** `subprocess.run([RCLONE, "--config", RCLONE_CONF, "copy", MIRROR_DIR, DRIVE_REMOTE + DRIVE_LEDGER_DIR])` in hermes-plugin

---

## Webhooks & Callbacks

**Incoming:**
- Webhook alternative to long-poll: `NIZAM__system/relay/webhook.py` (not the deployed path; long-poll via `poller.py` is primary)

**Outgoing:**
- All outbound calls are to Telegram API, OpenRouter, Anthropic, OpenAI, Google APIs, GitHub API
- Every outbound call is audit-logged to `NIZAM__system/ledgers/HIMAYAH__egress_audit.jsonl` via `_egress_audit()` in hermes-plugin
- Ungreenlit integrations trigger a warning queued to `pending_warn` and surfaced in the next Telegram reply

---

## Environment Configuration

**Required env vars for full operation:**
```
TELEGRAM_BOT_TOKEN
NIZAM_TELEGRAM_ALLOWED_IDS
RELAY_MODE=live
OPENROUTER_API_KEY
GOOGLE_APPLICATION_CREDENTIALS   # for Drive service-account mirror
GOOGLE_OAUTH_CLIENT_SECRETS       # for Calendar/Gmail OAuth
GOOGLE_OAUTH_TOKEN                # cached OAuth token
GITHUB_TOKEN                      # for Drive mirror script
NOTION_TOKEN                      # for dual-write
```

**Optional (with fallback):**
```
OPENAI_API_KEY            # fallback LLM provider
ANTHROPIC_API_KEY         # fallback LLM provider
CLAUDE_API_KEY            # alias for ANTHROPIC_API_KEY
DEEPSEEK_API_KEY          # DeepSeek provider
SERPAPI_API_KEY           # MARSAD flight radar
NIZAM_TIMEZONE            # default: Africa/Cairo
NIZAM_TG_POLL_TIMEOUT     # default: 25 seconds
NIZAM_KILL_ALL            # =1 to panic-stop all operations
NIZAM_STRATEGY_STH_KEY_PATH  # Ed25519 private key for STH signing
```

**Secrets location:**
- Local dev: `D:/NIZAM/.env` (root env) + `D:/NIZAM/NIZAM__system/relay/.env` (relay override)
- VPS production: `/home/nizam/.hermes/.env` (mode 600, authoritative)
- Credentials bundle: `D:/NIZAM/NIZAM-secrets.json` (not committed; synced to VPS by deploy scripts)
- Google OAuth client: `D:/NIZAM/nizam-prod-oauthclient.json` → synced to `/home/nizam/.hermes/connectors/oauth-client.json`

---

*Integration audit: 2026-06-14*
