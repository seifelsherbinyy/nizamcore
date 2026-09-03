# Contract: NIZAM-DAILY-ORCHESTRATION-04 | Phase: R2_SCHEDULER
"""Deterministic scheduling spine for the daily NIZAM governor.

Owning contract: NIZAM Contract 04 -- Daily Autonomous Orchestration & Actuation
  schedule.timezone = Africa/Cairo
  schedule.primary_run.target_time = "12:00" (exact_after_scheduler_preflight)
  schedule.reconciliation_run.target_time = "13:00" (retry_or_reconcile_only)
  schedule.preflight_requirement -- prove the Cairo instant before activation
Phase: R2_SCHEDULER

No network, no database, no clock read. Every function takes the instant as an
argument so the whole layer is testable across both DST regimes without waiting.
"""
CONTRACT = "NIZAM Contract 04 -- Daily Autonomous Orchestration & Actuation"
PHASE = "R2_SCHEDULER"
