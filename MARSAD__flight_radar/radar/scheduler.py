"""
APScheduler-based daily monitor scheduler.
SWAPPABLE_DEFAULT: replace with external cron or GitHub Actions (see SCHEDULED_AGENTS.md).

Default schedule: 06:00 UTC daily — runs MONITOR → ALERT → FORECAST in sequence.
DISCOVER is NOT scheduled — it runs once manually on init.

To run: python -m radar.main schedule
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from radar.config import SCHEDULER_HOUR, SCHEDULER_MINUTE

logger = logging.getLogger(__name__)


def _daily_pipeline() -> None:
    """Run the three daily stages in sequence: MONITOR → ALERT → FORECAST."""
    from radar.stages.monitor import run_monitor
    from radar.stages.alert import run_alert
    from radar.stages.forecast import run_forecast

    logger.info("MARSAD daily pipeline starting (06:00 UTC)")

    try:
        monitor_stats = run_monitor()
        logger.info("MONITOR done: %s", monitor_stats)
    except Exception as exc:
        logger.error("MONITOR failed: %s", exc)

    try:
        alert_stats = run_alert()
        logger.info("ALERT done: %s buy_signals", alert_stats.get("buy_signals_triggered", 0))
    except Exception as exc:
        logger.error("ALERT failed: %s", exc)

    try:
        forecast_stats = run_forecast()
        logger.info("FORECAST done: %s updated", forecast_stats.get("series_updated", 0))
    except Exception as exc:
        logger.error("FORECAST failed: %s", exc)

    logger.info("MARSAD daily pipeline complete")


def start_scheduler() -> None:
    """Start the blocking APScheduler daemon. Runs until interrupted."""
    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        _daily_pipeline,
        trigger=CronTrigger(hour=SCHEDULER_HOUR, minute=SCHEDULER_MINUTE, timezone="UTC"),
        id="marsad_daily",
        name="MARSAD daily monitor pipeline",
        misfire_grace_time=3600,  # if machine was off, run within 1 hour of scheduled time
        coalesce=True,
    )

    logger.info(
        "MARSAD scheduler started — daily pipeline at %02d:%02d UTC",
        SCHEDULER_HOUR,
        SCHEDULER_MINUTE,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("MARSAD scheduler stopped")
        scheduler.shutdown()
