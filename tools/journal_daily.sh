#!/usr/bin/env bash
# journal_daily.sh — scheduled YAWMIYAT enrichment + derive + index + reconcile.
#
# SCHEDULED TIME: 14:30 Africa/Cairo (2:30 PM local) — a deterministic daily run
# inside the 12:00–18:00 Cairo window mandated by G7.
#
# WHY 14:30:
#   - Mid-window, comfortably above the WAKE horizon and the 08:00/09:00 UTC WHOOP
#     daily-ingest (11:00 Cairo) that populates /opt/personal-health/data for the
#     current day, so enrichment usually has today's snapshot fresh.
#   - Leaves the evening clear; the pipeline is not racing end-of-day close.
#
# DST SAFETY (no duplicate / skipped runs):
#   - This host's crontab runs in UTC (no CRON_TZ). Africa/Cairo is UTC+2 (EET,
#     winter) or UTC+3 (EEST, summer). 14:30 Cairo == 11:30 UTC (EEST) or
#     12:30 UTC (EET). So the shared cron entry fires BOTH candidates:
#        30 11,12 * * * journal_daily.sh
#   - cairo_gate() below resolves the CURRENT Cairo time; only if the real Cairo
#     HH:MM equals the intended 14:30 does the run proceed. Exactly one of the two
#     UTC firings matches in any DST regime -> exactly one run per day.
#   - once_per_cairo_day() writes a marker file keyed on the CAIRO date. Even if
#     a scheduler somehow duplicated a firing (or a retry re-ran the same day),
#     the second attempt for the same Cairo calendar day exits 0 WITHOUT writing
#     any analytical version. Re-running on a NEW date is always allowed.
#
# Enrichment is idempotent regardless (no new analysis version if evidence is
# unchanged) — the Cairo-day guard is belt-and-suspenders / explicit as required.

set -u
TZ_WANTED="14:30"
MARKER_DIR="$HOME/nizamcore/YAWMIYAT__journaling/_recovery"
MARKER_FILE="$MARKER_DIR/today.marker"

# --- Cairo gate: only proceed if Africa/Cairo time is exactly the intended slot
CAIRO_NOW=$(TZ=Africa/Cairo date +%H:%M 2>/dev/null || python3 -c "import datetime;print(datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=3))).strftime('%H:%M'))")
if [ "$CAIRO_NOW" != "$TZ_WANTED" ]; then
  echo "$(date -u +%FT%TZ) [journal_daily] Cairo now $CAIRO_NOW != $TZ_WANTED; standing down (DST safety)." >> "$MARKER_DIR/journal_cron_standdown.log" 2>/dev/null
  exit 0
fi

# --- once-per-Cairo-calendar-day guard
CAIRO_DATE=$(TZ=Africa/Cairo date +%Y-%m-%d 2>/dev/null || python3 -c "import datetime;print(datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=3))).strftime('%Y-%m-%d'))")
mkdir -p "$MARKER_DIR"
if [ -f "$MARKER_FILE" ] && [ "$(cat "$MARKER_FILE" 2>/dev/null)" = "$CAIRO_DATE" ]; then
  echo "$(date -u +%FT%TZ) [journal_daily] Cairo day $CAIRO_DATE already ran; skipping (dup guard)." >> "$MARKER_DIR/journal_cron_skip.log" 2>/dev/null
  exit 0
fi

# proceed
echo "$(date -u +%FT%TZ) [journal_daily] RUN Cairo=$CAIRO_DATE @ $CAIRO_NOW"
python3 "$HOME/nizamcore/tools/journal_enrich.py" --since="$CAIRO_DATE" 2>&1
echo "$(date -u +%FT%TZ) [journal_daily] enrich exit=$?"
python3 -c "import sys;sys.path.insert(0,'$HOME/nizamcore/tools');import yawmiyat_index as I;import json;print(json.dumps(I.reconcile_drive(),indent=2,default=str))" 2>&1
echo "$(date -u +%FT%TZ) [journal_daily] reconcile exit=$?"

# stamp the marker only AFTER a successful run completes the unique analytical step
echo "$CAIRO_DATE" > "$MARKER_FILE"
echo "$(date -u +%FT%TZ) [journal_daily] done, marker set to $CAIRO_DATE"