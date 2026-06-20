# NIZAM Limited-Pilot Readiness

## Current Decision

**NO-GO for an externally connected pilot.**

Local remediation gates for stages 0–12 are implemented and green. External activation remains blocked until the operator separately approves:

- production model provider, model, budget, and data-egress terms;
- specific live connectors and credentials;
- deployment topology;
- remote telemetry destination and retention.

## Local Evidence Command

```powershell
D:\NIZAM\.venv\Scripts\python.exe D:\NIZAM\tools\nizam_pilot_readiness.py
```

## Go Live (operator approved)

```powershell
D:\NIZAM\scripts\go-live-local.ps1 -PollOnce
D:\NIZAM\scripts\go-live-local.ps1 -StartPoller -RequireTelegram
```

Fill `D:\NIZAM\.env` with `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_IDS`, and an LLM key before expecting Telegram replies.

Exit code `2` means activation remains blocked. The tool performs no network calls and no writes.

Check `local_decision` for local implementation status. It should read `GO` when all local gates pass.

See also `docs/architecture/PILOT_MATRIX.md` for the full stage-to-evidence map.

## Pilot Thresholds

- p95 response latency: at most 15 seconds;
- runtime error rate: below 2%;
- privacy incidents: zero;
- restart recovery and duplicate suppression: pass;
- GraphRAG expected-source top-five hit rate: 100%;
- unresolved P0/P1 gaps: zero.

Approvals must be recorded before setting any `NIZAM_*_APPROVED=1` activation variable.
