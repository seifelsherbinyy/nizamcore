#!/usr/bin/env python3
"""
journal_enrich.py — scheduled YAWMIYAT enrichment + derive + index (idempotent).

Cadence is configurable (-d/--date single day, --since range, --all). Idempotent:
re-running produces no new version if no new biometric evidence exists. A failed
run is safe to retry: analysis versions are immutable and enrichment merges
deterministically. Each session is enriched with ITS OWN captured-date WHOOP
daily snapshot (never a neighbour day's).

Usage:
  journal_enrich.py --date 2026-09-04            # sessions captured that day
  journal_enrich.py --since 2026-09-01           # sessions from that date onward
  journal_enrich.py --all                        # every session
  journal_enrich.py --dry-run --since 2026-09-01 # report without writing
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yawmiyat as Y
import yawmiyat_derived as D
import yawmiyat_index as I


def _daily_for(date):
    p = os.path.join("/opt/personal-health/data", f"daily_{date}.json")
    return p if os.path.exists(p) else None

def _all_sessions():
    """sid -> captured date for every canonical session."""
    out = {}
    d = os.path.join(Y.JOURNAL_ROOT, "sessions")
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if not fn.endswith(".json"):
                continue
            try:
                sj = Y.load_json(os.path.join(d, fn))
            except Exception:
                continue
            sid = sj.get("session_id") or fn[:-5]
            out[sid] = (sj.get("captured_at") or "")[:10]
    return out

def enrich(sel_dates=None, all_sessions=False, dry_run=False):
    """sel_dates: explicit set of captured-dates to enrich (None + all=False => today)."""
    rep = {"processed": 0, "new_versions": [], "noop": [], "missing_daily": [], "errors": []}
    sdates = _all_sessions()
    if all_sessions:
        targets = list(sdates.keys())
    elif sel_dates:
        targets = [sid for sid, dt in sdates.items() if dt in sel_dates]
    else:
        targets = [sid for sid, dt in sdates.items() if dt == Y._now().strftime("%Y-%m-%d")]
    for sid in targets:
        date = sdates[sid]
        daily_path = _daily_for(date)
        if daily_path is None:
            rep["missing_daily"].append({"sid": sid, "date": date})
            continue
        daily = Y.load_json(daily_path)
        try:
            analysis = D.enrich_session(sid, daily)
        except Exception as e:
            rep["errors"].append({"sid": sid, "err": str(e)})
            continue
        rep["processed"] += 1
        latest = Y.current_analysis_path(sid)
        new_bios = analysis.get("enrichment", {}).get("biometrics", {})
        if latest and Y.load_json(latest).get("enrichment", {}).get("biometrics") == new_bios:
            rep["noop"].append(sid)
            continue
        if dry_run:
            rep["new_versions"].append(f"{sid}.v{analysis['analysis_version']} (dry)")
            continue
        Y.persist_analysis(analysis)
        rep["new_versions"].append(f"{sid}.v{analysis['analysis_version']}")
    if not dry_run:
        I.build_manifest(force=True)
        I.build_index()
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", "-d", type=str, default=None)
    ap.add_argument("--since", type=str, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sel = None
    if a.date:
        sel = {a.date}
    elif a.since:
        sdates = _all_sessions()
        sel = {dt for dt in sdates.values() if dt >= a.since}
    rep = enrich(sel_dates=sel, all_sessions=a.all, dry_run=a.dry_run)
    print(json.dumps(rep, indent=2, default=str))


if __name__ == "__main__":
    main()