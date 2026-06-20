# GATE-0 — Companion baseline wiring

**Status:** PASS (pre-pulsation inventory)

## Existing companion modules

| Module | Role |
|--------|------|
| `contracts.py` | GatewayEnvelope, ContextPacket, ProactiveCandidate |
| `proactive.py` | Quiet hours, cooldown, daily max eligibility |
| `scheduler.py` | evaluate_candidates, send_proactive via Telegram poller |
| `reminders.py` | Sourced Islamic reminder validation |
| `context.py` | ContextPacket builder with privacy ceiling |
| `gateway.py` | Telegram ingress envelope |
| `capture.py` | Redacted inbound capture |
| `badan_import.py` / `whoop_import.py` | Health observation import |

## Outbound path (current)

`run_proactive_scheduler.py` → `ProactiveCandidate` → `scheduler.send_proactive` → `poller.tg_send_message`

## Gaps (to be filled L1–L8)

- No `context_refresh` before send
- No `PULSATION_LEDGER` / THABAT append on send
- `proactive.py` hard-blocks on sukoon_red instead of tiny-mode
- Static hourly message body

## Graph baseline

See `NIZAM__system/companion/graphify-out/graph.json` (AST-derived module graph).
