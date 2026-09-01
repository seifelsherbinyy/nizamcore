#!/usr/bin/env python3
"""
compute_features.py — Populate daily_features + daily_feature_vectors.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0 (BADAN / Health Intelligence)
Phase: cloud-first reconciliation — VPS operational plane
Storage class: vps_private / strict_local (VPS-only)

Day alignment: WHOOP's own cycle is the unit of a "day". A cycle's start_time is
rendered in Africa/Cairo (DST-aware, via Postgres AT TIME ZONE) to derive the
Cairo local date. Recovery and sleep join to that cycle, so all three align on
one calendar day. Workouts are assigned by their own Cairo start date.

Determinism: every number here comes from SQL or feature_engine. No LLM values.

Usage:
    python3 compute_features.py                 # today (Cairo) only
    python3 compute_features.py --backfill-all  # every date present in the DB
    python3 compute_features.py --date 2026-08-30
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature_engine import (  # noqa: E402
    METHODS_VERSION,
    assess_data_quality,
    build_metric_features,
)

CAIRO = "Africa/Cairo"

# Metric key -> human note. Provider metrics are stored, never recomputed.
METRICS = (
    "recovery_score",
    "hrv_rmssd_ms",
    "rhr_bpm",
    "spo2_pct",
    "skin_temp_c",
    "cycle_strain",
    "cycle_kilojoule",
    "sleep_total_hrs",
    "sleep_sws_hrs",
    "sleep_rem_hrs",
    "sleep_performance_pct",
    "sleep_efficiency_pct",
    "sleep_respiratory_rate",
    "sleep_disturbances",
    "workout_session_count",
    "workout_training_min",
    "workout_strain_sum",
)

# Cycle-aligned daily rows: one row per Cairo date built from WHOOP's cycle.
DAILY_SQL = f"""
WITH cyc AS (
  SELECT
    c.id            AS cycle_id,
    (c.start_time AT TIME ZONE '{CAIRO}')::date AS cairo_date,
    c.strain        AS cycle_strain,
    c.kilojoule     AS cycle_kilojoule,
    c.score_state   AS cycle_state,
    ROW_NUMBER() OVER (
      PARTITION BY (c.start_time AT TIME ZONE '{CAIRO}')::date
      ORDER BY c.start_time DESC
    ) AS rn
  FROM whoop_cycles c
),
cyc1 AS (SELECT * FROM cyc WHERE rn = 1),
rec AS (
  SELECT
    r.cycle_id,
    r.recovery_score,
    r.hrv_rmssd_milli,
    r.rhr,
    r.spo2_percentage,
    r.skin_temp_celsius,
    ROW_NUMBER() OVER (PARTITION BY r.cycle_id ORDER BY r.updated_at DESC) AS rn
  FROM whoop_recoveries r
  WHERE r.score_state = 'SCORED'
),
slp AS (
  SELECT
    s.cycle_id,
    s.total_in_bed_milli,
    s.total_sws_milli,
    s.total_rem_milli,
    s.sleep_performance_pct,
    s.sleep_efficiency_pct,
    s.respiratory_rate,
    s.disturbance_count,
    ROW_NUMBER() OVER (PARTITION BY s.cycle_id ORDER BY s.start_time DESC) AS rn
  FROM whoop_sleeps s
  WHERE s.nap = false AND s.score_state = 'SCORED'
)
SELECT
  cyc1.cairo_date,
  cyc1.cycle_id,
  cyc1.cycle_strain,
  cyc1.cycle_kilojoule,
  rec.recovery_score,
  rec.hrv_rmssd_milli,
  rec.rhr,
  rec.spo2_percentage,
  rec.skin_temp_celsius,
  slp.total_in_bed_milli,
  slp.total_sws_milli,
  slp.total_rem_milli,
  slp.sleep_performance_pct,
  slp.sleep_efficiency_pct,
  slp.respiratory_rate,
  slp.disturbance_count
FROM cyc1
LEFT JOIN rec ON rec.cycle_id = cyc1.cycle_id AND rec.rn = 1
LEFT JOIN slp ON slp.cycle_id = cyc1.cycle_id AND slp.rn = 1
ORDER BY cyc1.cairo_date
"""

WORKOUT_SQL = f"""
SELECT
  (start_time AT TIME ZONE '{CAIRO}')::date AS cairo_date,
  COUNT(*)                                   AS session_count,
  SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60.0) AS training_min,
  SUM(strain)                                AS strain_sum
FROM whoop_workouts
WHERE score_state = 'SCORED' AND end_time IS NOT NULL
GROUP BY 1
ORDER BY 1
"""


def _ms_to_hrs(ms) -> Optional[float]:
    return round(float(ms) / 3_600_000.0, 4) if ms is not None else None


def _f(v) -> Optional[float]:
    return float(v) if v is not None else None


async def load_series(conn) -> Dict[str, Dict[date, Optional[float]]]:
    """Build per-metric {cairo_date: value} maps. Absent days stay absent."""
    series: Dict[str, Dict[date, Optional[float]]] = {m: {} for m in METRICS}

    for row in await conn.fetch(DAILY_SQL):
        d = row["cairo_date"]
        series["recovery_score"][d] = _f(row["recovery_score"])
        series["hrv_rmssd_ms"][d] = _f(row["hrv_rmssd_milli"])
        series["rhr_bpm"][d] = _f(row["rhr"])
        series["spo2_pct"][d] = _f(row["spo2_percentage"])
        series["skin_temp_c"][d] = _f(row["skin_temp_celsius"])
        series["cycle_strain"][d] = _f(row["cycle_strain"])
        series["cycle_kilojoule"][d] = _f(row["cycle_kilojoule"])
        series["sleep_total_hrs"][d] = _ms_to_hrs(row["total_in_bed_milli"])
        series["sleep_sws_hrs"][d] = _ms_to_hrs(row["total_sws_milli"])
        series["sleep_rem_hrs"][d] = _ms_to_hrs(row["total_rem_milli"])
        series["sleep_performance_pct"][d] = _f(row["sleep_performance_pct"])
        series["sleep_efficiency_pct"][d] = _f(row["sleep_efficiency_pct"])
        series["sleep_respiratory_rate"][d] = _f(row["respiratory_rate"])
        series["sleep_disturbances"][d] = _f(row["disturbance_count"])

    for row in await conn.fetch(WORKOUT_SQL):
        d = row["cairo_date"]
        series["workout_session_count"][d] = _f(row["session_count"])
        series["workout_training_min"][d] = (
            round(float(row["training_min"]), 2) if row["training_min"] is not None else None
        )
        series["workout_strain_sum"][d] = (
            round(float(row["strain_sum"]), 4) if row["strain_sum"] is not None else None
        )

    # Workout absence on a cycle day is a real zero, not missing data:
    # WHOOP records a cycle every day, so "no workout logged" == 0 sessions.
    cycle_days = set(series["cycle_strain"].keys())
    for d in cycle_days:
        series["workout_session_count"].setdefault(d, 0.0)
        series["workout_training_min"].setdefault(d, 0.0)
        series["workout_strain_sum"].setdefault(d, 0.0)

    return series


def build_vector(series, planning_date: date) -> tuple[dict, dict]:
    """Assemble the schema-0.2.0 feature vector for one Cairo planning date."""
    metric_features = {
        m: build_metric_features(series[m], planning_date) for m in METRICS
    }
    data_quality = assess_data_quality(metric_features)

    today_block = {m: metric_features[m]["today"] for m in METRICS}

    windows = {}
    for w in ("3", "7", "14", "30", "90"):
        windows[w] = {m: metric_features[m]["windows"][w] for m in METRICS}

    vector = {
        "schema_version": "0.2.0",
        "planning_date": planning_date.isoformat(),
        "timezone": CAIRO,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "methods_version": METHODS_VERSION,
        "data_quality": data_quality,
        "today": today_block,
        "windows": windows,
        "baselines": {m: metric_features[m]["baseline"] for m in METRICS},
        "acceleration_proxy_7": {
            m: metric_features[m]["acceleration_proxy_7"] for m in METRICS
        },
        "source_refs": [
            "postgresql://personal_health/whoop_cycles",
            "postgresql://personal_health/whoop_recoveries",
            "postgresql://personal_health/whoop_sleeps",
            "postgresql://personal_health/whoop_workouts",
        ],
        "privacy_level": "strict_local",
    }
    return vector, data_quality


UPSERT_VECTOR = """
INSERT INTO daily_feature_vectors
  (planning_date, schema_version, timezone, methods_version, computed_at,
   vector, data_quality, source_refs, privacy_level)
VALUES ($1,'0.2.0',$2,$3,now(),$4,$5,$6,'strict_local')
ON CONFLICT (planning_date) DO UPDATE SET
  methods_version = EXCLUDED.methods_version,
  computed_at     = now(),
  vector          = EXCLUDED.vector,
  data_quality    = EXCLUDED.data_quality,
  source_refs     = EXCLUDED.source_refs
"""

UPSERT_DAILY = """
INSERT INTO daily_features
  (date, recovery_score, hrv_rmssd_milli, rhr, strain, sleep_hrs,
   deep_sleep_pct, rem_sleep_pct, spo2_pct, skin_temp_c, computed_at)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,now())
ON CONFLICT (date) DO UPDATE SET
  recovery_score  = EXCLUDED.recovery_score,
  hrv_rmssd_milli = EXCLUDED.hrv_rmssd_milli,
  rhr             = EXCLUDED.rhr,
  strain          = EXCLUDED.strain,
  sleep_hrs       = EXCLUDED.sleep_hrs,
  deep_sleep_pct  = EXCLUDED.deep_sleep_pct,
  rem_sleep_pct   = EXCLUDED.rem_sleep_pct,
  spo2_pct        = EXCLUDED.spo2_pct,
  skin_temp_c     = EXCLUDED.skin_temp_c,
  computed_at     = now()
"""


async def persist(conn, planning_date: date, series, vector, data_quality) -> None:
    await conn.execute(
        UPSERT_VECTOR,
        planning_date,
        CAIRO,
        METHODS_VERSION,
        json.dumps(vector),
        json.dumps(data_quality),
        vector["source_refs"],
    )

    def g(metric):
        return series[metric].get(planning_date)

    total = g("sleep_total_hrs")
    sws = g("sleep_sws_hrs")
    rem = g("sleep_rem_hrs")
    deep_pct = round(sws / total * 100.0, 2) if (total and sws is not None and total > 0) else None
    rem_pct = round(rem / total * 100.0, 2) if (total and rem is not None and total > 0) else None

    rec = g("recovery_score")
    rhr = g("rhr_bpm")
    dist = g("sleep_disturbances")  # noqa: F841  (kept for clarity of available fields)

    await conn.execute(
        UPSERT_DAILY,
        planning_date,
        int(rec) if rec is not None else None,
        g("hrv_rmssd_ms"),
        int(rhr) if rhr is not None else None,
        g("cycle_strain"),
        total,
        deep_pct,
        rem_pct,
        g("spo2_pct"),
        g("skin_temp_c"),
    )


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="Cairo planning date YYYY-MM-DD")
    ap.add_argument("--backfill-all", action="store_true")
    args = ap.parse_args()

    import asyncpg
    db_url = os.environ["POSTGRES_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    try:
        series = await load_series(conn)
        all_days = sorted(series["cycle_strain"].keys())
        if not all_days:
            print("no cycle data present; nothing to compute", file=sys.stderr)
            return 1

        if args.backfill_all:
            targets: List[date] = all_days
        elif args.date:
            targets = [date.fromisoformat(args.date)]
        else:
            targets = [all_days[-1]]

        for d in targets:
            vector, dq = build_vector(series, d)
            await persist(conn, d, series, vector, dq)

        print(json.dumps({
            "status": "OK",
            "methods_version": METHODS_VERSION,
            "dates_computed": len(targets),
            "first": targets[0].isoformat(),
            "last": targets[-1].isoformat(),
        }, indent=2))
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
