# Technology Stack

**Analysis Date:** 2026-06-14

## Languages

**Primary:**
- Python 3.12.4 — all governor, relay, router, connector, and script code

**Secondary:**
- JSON — data model (personas, ledgers, policies, schemas, registries)
- YAML — configuration (router, agents registry, intent exemplars)
- Markdown — persona contracts, protocols, documentation, SOUL identity files

## Runtime

**Environment:**
- Python 3.12.4 (CPython)
- Platform: Windows 11 Pro (local/dev); Ubuntu VPS (production)
- Timezone: Africa/Cairo (`NIZAM_TIMEZONE` env var)

**Virtual Environments:**
- `D:/NIZAM/.venv/` — main project venv (Python 3.12.4); used for governor, relay, MARSAD
- `D:/NIZAM/hermes-venv/` — secondary venv for Hermes CLI agent runtime; chained from `.venv`
- `D:/NIZAM/install-audit/gap-closure-venv/` — audit/diagnostic venv

**Package Manager:**
- pip-tools (pip-compile) generates pinned files
- `D:/NIZAM/requirements.in` → compiled to `D:/NIZAM/requirements.txt`
- `D:/NIZAM/requirements-dev.in` → compiled to `D:/NIZAM/requirements-dev.txt`
- Lockfiles: `requirements.txt` and `requirements-dev.txt` (both present, pip-compile generated)

## Frameworks

**Core (Governor / Relay — pure stdlib):**
- No third-party framework in governor or relay. Modules are pure Python stdlib (json, re, uuid, hashlib, pathlib, threading, urllib).
- `NIZAM__system/governor/` — stdlib only by design ("Pure stdlib" stated in every module)
- `NIZAM__system/relay/` — stdlib only (urllib for HTTP; no requests)
- `NIZAM__system/config/nizam_router.py` — stdlib only (hand-rolled YAML mini-parser)

**Testing:**
- pytest 9.1.0 — test runner
- pytest-asyncio 1.4.0 — async test support
- Config: `D:/NIZAM/pytest.ini` (testpaths explicitly set; strict markers)

**Build/Dev:**
- pip-tools 7.5.3 — requirement pinning
- build 1.5.0, wheel 0.47.0 — packaging utilities

## Key Dependencies

**Google APIs (Drive, Calendar, Gmail, Tasks):**
- `google-api-python-client==2.197.0` — Google Drive v3, Calendar v3, Gmail v1
- `google-auth==2.54.0` — auth base
- `google-auth-httplib2==0.4.0` — HTTP transport for Google APIs
- `google-auth-oauthlib==1.4.0` — OAuth 2.0 flow (used by connectors)
- Declared in `D:/NIZAM/HIFZ__github_version_control/requirements-governor.txt`

**Cryptography:**
- `cryptography==49.0.0` — Fernet symmetric encryption (at-rest ledger key), Ed25519 signing (STRATEGY_LEDGER STH), Google auth
- Used in `NIZAM__system/hermes-plugins/nizam-governor/__init__.py` (`_atrest_fernet()`) and `NIZAM__system/governor/strategy_sth.py`

**HTTP / Web:**
- `requests==2.34.2` — used in `HIFZ__github_version_control/scripts/nizam_drive_mirror.py` (GitHub tree fetch, Google Drive uploads)
- Core relay and router use only `urllib.request` (stdlib)

**Data Processing (MARSAD module):**
- `pandas==3.0.3` — flight data analysis
- `numpy==2.4.6` — numeric support for pandas
- `playwright==1.60.0` — browser automation for flight scraping
- `beautifulsoup4==4.15.0` — HTML parsing
- `lxml==6.1.1` — fast XML/HTML parser
- `apscheduler==3.11.2` — in-process job scheduler for MARSAD radar loop
- `google-search-results==2.4.2` (SerpAPI) — flight search results

**Document Generation:**
- `python-docx==1.2.0` — generate `.docx` records for Google Drive
- Used in `HIFZ__github_version_control/scripts/` governor scripts

**Validation:**
- `pydantic==2.13.4` — data validation (MARSAD module)

**Scheduling:**
- `apscheduler==3.11.2` — task scheduler (MARSAD); Hermes itself manages cron for scheduled Telegram pulses via `hermes_cli` commands
- `tzdata==2026.2`, `tzlocal==5.3.1`, `python-dateutil==2.9.0.post0` — timezone support

**Rich / CLI:**
- `rich==15.0.0` — terminal output formatting (MARSAD)
- `python-dotenv==1.2.2` — `.env` file loading

**Misc:**
- `markdown-it-py==4.2.0` — Markdown processing
- `arc-protocol` — optional; enables RFC 6962 Merkle tree for STRATEGY_LEDGER STH (degrades gracefully if absent)

## Configuration

**Environment:**
- Primary: `D:/NIZAM/.env` (loaded first by `NIZAM__system/relay/env_loader.py`)
- Relay override: `NIZAM__system/relay/.env` (loaded second, can override)
- On VPS: `/home/nizam/.hermes/.env` (mode 600, authoritative at runtime)
- `env_loader.load_all()` reads both files; `normalize_aliases()` bridges name variants (e.g. `TELEGRAM_ALLOWED_CHAT_IDS` → `NIZAM_TELEGRAM_ALLOWED_IDS`)

**Key env vars referenced by code:**
- `TELEGRAM_BOT_TOKEN` — Telegram bot token (poller + hermes-plugin)
- `NIZAM_TELEGRAM_ALLOWED_IDS` / `TELEGRAM_ALLOWED_CHAT_IDS` — operator whitelist
- `RELAY_MODE` — `standby` (default) or `live` (enables polling)
- `NIZAM_KILL_ALL` — panic stop; if `=1`, all writers and dispatchers halt
- `OPENROUTER_API_KEY` — primary LLM provider (OpenRouter)
- `OPENAI_API_KEY` — alternate LLM provider
- `ANTHROPIC_API_KEY` / `CLAUDE_API_KEY` — Anthropic (alias bridged by env_loader)
- `DEEPSEEK_API_KEY` — DeepSeek provider
- `GOOGLE_APPLICATION_CREDENTIALS` — service account JSON path (Drive v3 via service account)
- `GOOGLE_OAUTH_CLIENT_SECRETS` — OAuth client secrets file path (Calendar/Gmail)
- `GOOGLE_OAUTH_TOKEN` — OAuth token file path (Calendar/Gmail)
- `GITHUB_TOKEN` / `GH_TOKEN` — GitHub API token (Drive mirror script)
- `NOTION_TOKEN` — Notion API token (dual-write governor)
- `NIZAM_TIMEZONE` — timezone for scheduled pulses (default: Africa/Cairo)
- `NIZAM_TG_POLL_TIMEOUT` — long-poll timeout seconds (default 25)
- `NIZAM_STRATEGY_STH_KEY_PATH` — Ed25519 private key path for STH signing
- `SERPAPI_API_KEY` — flight search (MARSAD module)

**Activation bundle (live mode):**
- `NIZAM_LIVE_MODEL_APPROVED`, `NIZAM_LIVE_CONNECTORS_APPROVED`, `NIZAM_DEPLOYMENT_APPROVED`, `NIZAM_REMOTE_TELEMETRY_APPROVED` — all set to `"1"` by `env_loader.apply_activation_bundle()`

**Build:**
- `D:/NIZAM/requirements.in` — direct deps
- `D:/NIZAM/requirements-dev.in` — dev deps (adds pip-tools, build, wheel, pytest)
- `D:/NIZAM/pytest.ini` — test configuration

## How the System is Invoked / Run

**Relay long-poll runner (primary Telegram loop):**
```bash
python -m NIZAM__system.relay.poller             # continuous loop (RELAY_MODE=live required)
python -m NIZAM__system.relay.poller --once      # single poll cycle
python -m NIZAM__system.relay.poller --dry-run   # synthetic update, no network
```

**Router (standalone):**
```bash
python -m NIZAM__system.config.nizam_router      # (no __main__ block; imported as module)
```

**Governor modules (standalone CLI):**
```bash
python -m NIZAM__system.governor.classifier <rel_path> [<target>]
python -m NIZAM__system.governor.ledger_writer verify <LEDGER_NAME>
python -m NIZAM__system.governor.sync_arbiter <rel_path> <target_plane>
python -m NIZAM__system.governor.kill_switch    # prints status JSON
```

**Drive mirror scripts:**
```bash
python HIFZ__github_version_control/scripts/nizam_drive_mirror.py
python HIFZ__github_version_control/scripts/nizam_dual_write.py
```

**Hermes cron job installer (deploys to VPS via SSH):**
```bash
python tools/setup_hermes_scheduled_telegram.py
python tools/setup_hermes_scheduled_telegram.py --remove
```

**Tests:**
```bash
pytest   # from D:/NIZAM root; picks up pytest.ini testpaths
```

**Hermes CLI (on VPS):**
```bash
cd ~/.hermes/hermes-agent && ./venv/bin/python -m hermes_cli.main cron list
cd ~/.hermes/hermes-agent && ./venv/bin/python -m hermes_cli.main cron status
```

## Platform Requirements

**Development (local laptop — Windows 11):**
- Python 3.12.4
- `.venv` at `D:/NIZAM/.venv/`
- Git with pre-commit hook (`NIZAM__system/governor/scripts/pre_commit_check.py`)

**Production (VPS — Linux):**
- VPS IP: `31.97.154.5`, user: `nizam`
- repo clone at `/home/nizam/nizamcore`
- Hermes runtime at `/home/nizam/.hermes/`
- rclone at `/home/nizam/.local/bin/rclone`
- rclone config at `/home/nizam/.config/rclone/rclone.conf`
- Hermes CLI installed in `/home/nizam/.hermes/hermes-agent/venv/`
- Plugin: `/home/nizam/.hermes/plugins/nizam-governor/`
- Secrets file: `/home/nizam/.hermes/.env` (mode 600)

---

*Stack analysis: 2026-06-14*
