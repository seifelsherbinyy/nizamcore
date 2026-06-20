# NIZAM Environment Setup

This note documents which local `.env` files exist and what each connector needs. Do not store real secrets in documentation or commit them to git.

## Local Env Files

| File | Purpose | Git status |
| --- | --- | --- |
| `D:\NIZAM\.env` | Root orchestration layer keys for LLM, Notion, Drive, GitHub, Telegram, Gmail, and MARSAD | Ignored by `.gitignore` |
| `D:\NIZAM\MARSAD__flight_radar\.env` | MARSAD flight radar settings and API keys | Ignored by `.gitignore` |

Both files were scaffolded from their `.env.example` templates with empty or placeholder values.

## Connector Keys

| Connector | Variables | Needed for |
| --- | --- | --- |
| LLM runtime | `CLAUDE_API_KEY` or `OPENAI_API_KEY` | Scribe, Witness, Counselor-style agent work |
| Notion | `NOTION_TOKEN` | Steward writes to Pulse, Witness, and Audit Log |
| Google Drive | `GOOGLE_APPLICATION_CREDENTIALS` or OAuth fallback variables | Human-readable dual-write mirror |
| GitHub | `GITHUB_TOKEN` or `GH_TOKEN` | Higher API rate limits or push from scripts |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_IDS` | Future Warden intake adapter |
| Gmail | `GMAIL_OAUTH_JSON_PATH`, `GMAIL_LABEL_FILTER` | Future Warden email intake adapter |
| MARSAD | `SERPAPI_KEY` in `MARSAD__flight_radar\.env` | Flight radar live data source |

The root `.env.example` also mentions `SERPAPI_API_KEY`; MARSAD's module-local `.env.example` uses `SERPAPI_KEY`. Prefer the module-local name when running MARSAD unless the code is updated to accept both.

## References

- `D:\NIZAM\.env.example`
- `D:\NIZAM\MARSAD__flight_radar\.env.example`
- `D:\NIZAM\NIZAM__system\policies\CONNECTORS.json`
- `D:\NIZAM\NIZAM__system\docs\NIZAM_ORCHESTRATION_LAYER.md`

## Verification Without Secrets

Local install verification does not require any real secrets:

```powershell
D:\NIZAM\scripts\verify-nizamcore.ps1
```

Live Notion, Drive, Telegram, Gmail, and MARSAD data-source operations require their respective keys.
