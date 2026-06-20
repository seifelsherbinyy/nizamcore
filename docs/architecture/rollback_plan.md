# Rollback plan

## L1 contracts
Revert `contracts.py` pulsation dataclasses; delete `schemas/pulsation_message.schema.json`.

## L2–L5 pulsation core
Remove `NIZAM__system/companion/pulsation/` directory.

## L6 ledger
Remove PULSATION_LEDGER and COUNCIL_LEDGER from `ledger_writer.KNOWN_LEDGERS`; delete ledger jsonl if bootstrapped only.

## L7 scheduler
Revert `scheduler.py` and `proactive.py` to pre-pulsation behavior.

## L8 runner / deploy
Restore hourly `run_proactive_scheduler.py` cron in `deploy_nizam_vps.py`.
Re-enable Hermes pulses via `setup_hermes_scheduled_telegram.py` without `--remove`.

## Council K1–K7
Remove `NIZAM__system/companion/council/` directory and council schemas.

## Skills Phase 4
Remove `skills_registry/` and added `.skill.md` files if isolated.
