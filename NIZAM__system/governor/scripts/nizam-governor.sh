#!/bin/bash
# Contract: NIZAM-DAILY-ORCHESTRATION-04 schedule | Phase: R2_SCHEDULER
# nizam-governor.sh — NIZAM autonomous governor slot runner.
#
# Owning contract: NIZAM-DAILY-ORCHESTRATION-04 schedule, daily_dag
#                  NIZAM-CONTRACT-01 required_runtime_receipt
# Phase: R2_SCHEDULER
#
# SCHEDULING (Contract 04 "schedule", proven by the 2026-09-03 preflight)
#   This host's cron has no CRON_TZ support and the scheduler runs in UTC — the
#   live preflight recorded scheduler_timezone_localtime=UTC+0000 with TZ unset,
#   so this is measured, not assumed. A single fixed UTC slot therefore cannot
#   hold a Cairo wall time across DST:
#       EEST (+3, summer)   EET (+2, winter)
#       10:00 Cairo == 07:00        08:00 UTC
#       11:40 Cairo == 08:40        09:40 UTC
#       12:00 Cairo == 09:00        10:00 UTC
#       13:00 Cairo == 10:00        11:00 UTC
#   Cron fires at BOTH candidates for each slot and exactly one passes the gate.
#
# WHY THIS SCRIPT DOES NOT GATE ON THE CAIRO HOUR ITSELF
#   daily-ingest.sh gates in shell with `TZ=Africa/Cairo date +%H` because it
#   predates the scheduler package. This script deliberately does NOT, and that
#   is the single most important line in this header. The gate and the run-once
#   guard live in `scheduler.cairo_gate` and `scheduler.preflight_cli`, are swept
#   against every Cairo day of 2026-2030, and are the SAME code path the Contract
#   04 preflight proved. A shell re-implementation here would be a second,
#   unproven gate; the package suite forbids a second `decide(` call site for
#   exactly that reason. This wrapper supplies a lock, an environment and a log,
#   and delegates every scheduling decision to the tested module.
#
# FAILURE ISOLATION
#   `set -uo pipefail` and deliberately NOT `-e`. A `set -euo pipefail` chain in
#   the health job stalled the Drive copy for ~2.5 months, because one step's
#   failure silently skipped every step after it. Here the governor is a single
#   invocation, so the rule matters less, but the house convention is kept so
#   that adding a second step later cannot reintroduce that defect by accident.
#
# EXIT CODES
#   0  the slot ran, or correctly stood down, or another run holds its lock.
#      Standing down is the designed behaviour of the slot that is not due, so
#      it must not page anyone.
#   1  the governor itself failed.
#   2  the wrapper was called wrongly, or its environment is not usable.
#
# CALENDAR: this wrapper attempts no calendar write today. R5 lands calendar
#   actuation under NIZAM-CALENDAR-ACTUATION-001, and the governor records the
#   stage as BLOCKED with a named open loop until it does. It is not blocked on a
#   human approval; it is blocked on not being built yet.

set -uo pipefail

SLOT="${1:-}"

# Derive the package root from this script's own location rather than hardcoding
# a checkout path, matching `scripts/install_pre_commit_hook.py`, which resolves
# REPO_ROOT the same way. This script lives in .../governor/scripts/, so the
# package parent is its parent directory. An override exists for testing only.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_PARENT="${NIZAM_GOVERNOR_PKG_PARENT:-$(dirname "$SCRIPT_DIR")}"
STATE_DIR="${NIZAM_GOVERNOR_STATE:-$HOME/.nizam-governor}"
LOG_DIR="${NIZAM_GOVERNOR_LOG_DIR:-$STATE_DIR/logs}"
PYTHON="${NIZAM_GOVERNOR_PYTHON:-python3}"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

case "$SLOT" in
  refresh_1000|volatile_1140|primary_1200|reconcile_1300) ;;
  *)
    echo "$(ts) [governor] usage: nizam-governor.sh SLOT" >&2
    echo "$(ts) [governor]   SLOT is one of: refresh_1000 volatile_1140 primary_1200 reconcile_1300" >&2
    echo "$(ts) [governor]   got: '${SLOT}'" >&2
    exit 2
    ;;
esac

# ── A. single-run lock, PER SLOT ────────────────────────────────────────────
# Per slot, not global, on purpose: a hung 12:00 run must not silently suppress
# the 13:00 reconciliation, which is the run whose whole job is to clean up
# after a bad 12:00. Two different slots overlapping is the safer failure mode.
LOCK_DIR="/var/lock"
[ -w "$LOCK_DIR" ] || LOCK_DIR="$STATE_DIR"
LOCK="${LOCK_DIR}/nizam-governor-${SLOT}.lock"

mkdir -p "$STATE_DIR" "$LOG_DIR" || {
  echo "$(ts) [governor] cannot create state or log directory" >&2
  exit 2
}

exec 9>"$LOCK" || { echo "$(ts) [governor] cannot open lock ${LOCK}" >&2; exit 2; }
if ! flock -n 9; then
  echo "$(ts) [governor] ${SLOT}: another run holds the lock; exiting"
  exit 0
fi

# ── B. record the environment the run actually got ──────────────────────────
CAIRO_NOW=$(TZ=Africa/Cairo date '+%Y-%m-%d %H:%M:%S %Z%z')
UTC_NOW=$(date -u '+%Y-%m-%d %H:%M:%S UTC')
echo "$(ts) [governor] ${SLOT}: utc=${UTC_NOW} cairo=${CAIRO_NOW}"

if [ ! -d "${PKG_PARENT}/scheduler" ]; then
  echo "$(ts) [governor] ${SLOT}: no scheduler package under ${PKG_PARENT}" >&2
  exit 2
fi

# ── C. delegate every scheduling decision to the tested module ──────────────
# The module decides whether this firing is the one that runs. It writes its own
# receipt to ${STATE_DIR}/receipts.jsonl and prints the decision as one JSON
# line, which is what makes a cron log machine-checkable rather than prose.
RUN_LOG="${LOG_DIR}/governor-$(TZ=Africa/Cairo date +%Y-%m-%d).jsonl"

cd "$PKG_PARENT" || { echo "$(ts) [governor] cannot enter ${PKG_PARENT}" >&2; exit 2; }

if NIZAM_GOVERNOR_STATE="$STATE_DIR" "$PYTHON" -m scheduler.governor_cli "$SLOT" \
     >> "$RUN_LOG" 2>>"${LOG_DIR}/governor-stderr.log"; then
  VERDICT=$("$PYTHON" - "$RUN_LOG" <<'PY'
import json, sys
try:
    line = [l for l in open(sys.argv[1], encoding="utf-8") if l.strip()][-1]
    d = json.loads(line)
    sd = d.get("slot_decision") or {}
    ran = "ran" if d.get("receipt") else "stood_down"
    print(f"{ran} verdict={sd.get('verdict')} guard={sd.get('guard')} "
          f"cairo={sd.get('cairo_local')} delta={sd.get('delta_minutes')}")
except Exception as exc:  # the run succeeded; only the summary failed
    print(f"summary_unavailable ({exc.__class__.__name__})")
PY
)
  echo "$(ts) [governor] ${SLOT}: OK — ${VERDICT}"
  echo "$(ts) [governor] ${SLOT}: ===== done OK ====="
  exit 0
fi

echo "$(ts) [governor] ${SLOT}: FAILED — see ${LOG_DIR}/governor-stderr.log" >&2
echo "$(ts) [governor] ${SLOT}: ===== done WITH FAILURE ====="
exit 1
