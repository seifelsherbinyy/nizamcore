# L8 — Runner + deploy

- `tools/run_pulsation_loops.py` (primary)
- `tools/run_proactive_scheduler.py` (wrapper)
- `deploy_nizam_vps.py` cron `*/15`

Graphify path: `run_pulsation_loops` → `evaluate_loops` → `send_pulsation` → ledger.
