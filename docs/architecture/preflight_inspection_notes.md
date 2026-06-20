# Pre-flight inspection notes

Generated: 2026-06-14

## companion/

- `contracts.py` — ProactiveCandidate, extended with ContextRefresh/PulsationMessage
- `proactive.py` — eligibility policy; updated tiny-mode vs crisis
- `scheduler.py` — send_proactive + send_pulsation
- `pulsation/` — new package L1–L8
- `council/` — new package K1–K7

## relay/

- `sukoon_gate.py` — overload flags, crisis keywords
- `runtime_events.py` — privacy-safe inbound events
- `poller.py` — Telegram send

## governor/

- `ledger_writer.py` — PULSATION_LEDGER, COUNCIL_LEDGER added
- `classifier.py` — HIMAYAH path classification

## tools/

- `run_proactive_scheduler.py` — wrapper to pulsation runner
- `run_pulsation_loops.py` — primary cron entry

## tests/

- `test_pulsation.py`, `test_companion.py`, `test_production_modules.py`
- `council/tests/test_council.py`
