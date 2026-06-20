# GATE-2 — Preflight graph paths

## scheduler → poller
`companion/scheduler.py::send_pulsation` → `relay/poller.py` Telegram send (when not dry-run).

## ledger_writer → EVENT_LEDGER
`pulsation/ledger.py::append_pulsation` → `governor/ledger_writer.py` → `PULSATION_LEDGER` + `EVENT_LEDGER` hash excerpt.

## sukoon_gate → proactive policy
`relay/sukoon_gate.py` capacity → `companion/proactive.py::eligible` tiny-mode / crisis suppress.

## runner cron path
`tools/run_pulsation_loops.py` → `pulsation/loops.py::evaluate_loops` → `scheduler.send_pulsation`.
