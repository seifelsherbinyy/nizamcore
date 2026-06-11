"""
MARSAD — NIZAM Flight Intelligence Module
Entry point: python -m radar.main <command>

Commands:
  discover   — Stage 1: baseline collection (run once on init)
  monitor    — Stage 2: daily delta
  alert      — Stage 3: price drop signal detection
  forecast   — Stage 4: trend model update
  run-all    — Run all four stages in sequence
  schedule   — Start APScheduler daemon (06:00 UTC daily)
  dashboard  — Live executive dashboard at http://localhost:7329
  status     — Print current store summary
  validate   — Validate credentials and configuration

Usage:
  cd MARSAD__flight_radar
  python -m radar.main discover
  python -m radar.main schedule
"""

from __future__ import annotations

import argparse
import logging
import sys

from radar.config import LOG_LEVEL, validate_credentials


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


def cmd_seed(args: argparse.Namespace) -> int:
    from pathlib import Path
    from radar.stages.seed import run_seed
    csv_path = Path(args.csv) if args.csv else None
    json_path = Path(args.json_file) if args.json_file else None
    stats = run_seed(csv_path=csv_path, json_path=json_path, dry_run=args.dry_run)
    print(f"\nSEED: {stats['rows_imported']} imported, {stats['rows_filtered']} filtered, {stats['rows_error']} errors")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    from radar.stages.discover import run_discover
    stats = run_discover(dry_run=args.dry_run)
    print(f"\nDISCOVER: {stats}")
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    from radar.stages.monitor import run_monitor
    stats = run_monitor()
    print(f"\nMONITOR: {stats}")
    return 0


def cmd_alert(args: argparse.Namespace) -> int:
    from radar.stages.alert import run_alert
    stats = run_alert()
    print(f"\nALERT: {stats['buy_signals_triggered']} BUY_SIGNAL(s), {stats['watch_signals_triggered']} WATCH")
    return 0


def cmd_forecast(args: argparse.Namespace) -> int:
    from radar.stages.forecast import run_forecast
    stats = run_forecast()
    print(f"\nFORECAST: {stats['series_updated']} series updated, {stats['buy_signals']} buy_signals")
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    from radar.stages.discover import run_discover
    from radar.stages.monitor import run_monitor
    from radar.stages.alert import run_alert
    from radar.stages.forecast import run_forecast

    if args.with_discover:
        print("Running DISCOVER (baseline collection)...")
        run_discover()

    print("Running MONITOR...")
    run_monitor()

    print("Running ALERT...")
    run_alert()

    print("Running FORECAST...")
    run_forecast()

    print("\nAll stages complete.")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from radar.dashboard import run_dashboard
    run_dashboard(host=args.host, port=args.port)
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    from radar.scheduler import start_scheduler
    print("Starting MARSAD scheduler daemon...")
    start_scheduler()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from radar.schema_store import load_store, get_all_series_keys
    store = load_store()
    keys = get_all_series_keys(store)

    total_obs = sum(k["observation_count"] for k in keys)
    buy_signals = 0
    try:
        for rk_data in store.get("routes", {}).values():
            for sk_data in rk_data.get("observations", {}).values():
                if sk_data.get("forecast", {}).get("buy_signal"):
                    buy_signals += 1
    except Exception:
        pass

    print(f"\nMARS AD Status")
    print(f"  Schema version:    {store.get('schema_version', '?')}")
    print(f"  Last updated:      {store.get('last_updated', 'never')}")
    print(f"  Total series:      {len(keys)}")
    print(f"  Total observations:{total_obs}")
    print(f"  Active BUY_SIGNAL: {buy_signals}")
    print(f"  Travel window:     {store.get('metadata', {}).get('travel_window_start')} → {store.get('metadata', {}).get('travel_window_end')}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    missing = validate_credentials()
    if missing:
        print("Missing configuration:")
        for item in missing:
            print(f"  ✗ {item}")
        print("\nSee .env.example for setup instructions.")
        return 1
    else:
        from radar.config import DATA_SOURCE, WINDOW_START, WINDOW_END, ALERT_DELIVERY
        print("Configuration valid:")
        print(f"  DATA_SOURCE:      {DATA_SOURCE}")
        print(f"  Travel window:    {WINDOW_START} → {WINDOW_END}")
        print(f"  Alert delivery:   {ALERT_DELIVERY}")
        return 0


def main() -> int:
    _setup_logging()

    parser = argparse.ArgumentParser(
        prog="python -m radar.main",
        description="MARSAD — NIZAM Flight Intelligence Module",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # seed (Stage 0 — historical import, runs before discover)
    p_seed = subparsers.add_parser("seed", help="Stage 0: import historical price seed data (CSV or JSON)")
    p_seed.add_argument("--csv", default="", help="Path to seed CSV file")
    p_seed.add_argument("--json-file", default="", dest="json_file", help="Path to seed JSON file")
    p_seed.add_argument("--dry-run", action="store_true", help="Parse and validate without writing")
    p_seed.set_defaults(func=cmd_seed)

    # discover
    p_discover = subparsers.add_parser("discover", help="Stage 1: baseline collection")
    p_discover.add_argument("--dry-run", action="store_true", help="Log what would be fetched without writing")
    p_discover.set_defaults(func=cmd_discover)

    # monitor
    p_monitor = subparsers.add_parser("monitor", help="Stage 2: daily delta")
    p_monitor.set_defaults(func=cmd_monitor)

    # alert
    p_alert = subparsers.add_parser("alert", help="Stage 3: price drop signal detection")
    p_alert.set_defaults(func=cmd_alert)

    # forecast
    p_forecast = subparsers.add_parser("forecast", help="Stage 4: trend model update")
    p_forecast.set_defaults(func=cmd_forecast)

    # run-all
    p_all = subparsers.add_parser("run-all", help="Run monitor + alert + forecast in sequence")
    p_all.add_argument("--with-discover", action="store_true", help="Also run discover first")
    p_all.set_defaults(func=cmd_run_all)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Live executive dashboard at http://localhost:7329")
    p_dash.add_argument("--port", type=int, default=7329, help="HTTP port (default: 7329)")
    p_dash.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    p_dash.set_defaults(func=cmd_dashboard)

    # schedule
    p_schedule = subparsers.add_parser("schedule", help="Start scheduler daemon (06:00 UTC daily)")
    p_schedule.set_defaults(func=cmd_schedule)

    # status
    p_status = subparsers.add_parser("status", help="Print current store summary")
    p_status.set_defaults(func=cmd_status)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate credentials and configuration")
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
