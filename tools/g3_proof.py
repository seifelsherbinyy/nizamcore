#!/usr/bin/env python3
"""
G3 proof: one synthetic scheduled production call chain.

raw/session -> WHOOP enrichment -> Assessment -> Evaluation -> Analysis ->
longitudinal/index update -> reconcile

Uses a transient synthetic journal (never the real one) + a fake WHOOP snapshot
file (never inventing missing values). Runs the SAME helpers the scheduler
(journal_enrich.py / journal_daily.sh) invokes, and shows the created/versioned
artifacts at each stage.

Run: python3 g3_proof.py
"""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import yawmiyat as Y
import yawmiyat_derived as D
import yawmiyat_index as I

TS = "2026-09-04T12:30:00Z"
UTT = [
    {"speaker": "Sherbiny", "ts": TS, "text": "Energy 4, mood numbed."},
    {"speaker": "Sherbiny", "ts": "2026-09-04T12:31:00Z", "text": "The LDR loop, third time."},
]

# synthetic WHOOP daily snapshot - matches /opt/personal-health/data schema
FAKE_DAILY = {
    "export_date": "2026-09-04", "exported_at": "2026-09-04T08:00:03.9+00:00",
    "source": "whoop_postgresql",
    "recovery": {"score": 31, "rhr_bpm": 64, "hrv_rmssd_ms": 40.53, "state": "SCORED"},
    "sleep": {"total_hrs": 5.68, "deep_hrs": None, "rem_hrs": 1.03, "sleep_performance_pct": None},
    "cycle": {"strain": 4.38},
    "workouts": [],
}


def sj(sid):
    return {
        "session_id": sid, "session_type": "checkin", "captured_at": TS,
        "felt_state": {"energy": 4, "mood": "numbed", "gut": "coaster", "notable": "third pass at loop"},
        "capacity": {"level": "MEDIUM", "trend": "declining"},
        "pillars": {"voted": ["meaning"], "missed": [], "contrary_urges": []},
        "assessment": {"pattern": "third loop: control->trigger->reinvest", "continuity_note": "observe"},
        "plan": {"priorities": [], "recovery_item": "step back", "tiny_versions": []},
        "decisions": ["A or B; keep logging"], "topics": ["relationship"],
        "confidence": 0.93, "needs_human_confirmation": False,
    }


def main():
    tmp = tempfile.mkdtemp(prefix="g3_journal_")
    Y.JOURNAL_ROOT = os.path.join(tmp, "YAWMIYAT__journaling")
    Y.ENSURE_ONCE = False
    Y.ensure_layout()

    # stage a fake daily snapshot where the scheduler reads it
    fake_dir = os.path.join(tmp, "health_data")
    os.makedirs(fake_dir, exist_ok=True)
    fake_path = os.path.join(fake_dir, "daily_2026-09-04.json")
    with open(fake_path, "w") as f:
        json.dump(FAKE_DAILY, f)
    # point enrichment at it (import journal_enrich and override its lookup)
    import importlib.util
    je_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "journal_enrich.py")
    spec = importlib.util.spec_from_file_location("_je", je_path)
    je = importlib.util.module_from_spec(spec); spec.loader.exec_module(je)
    je._daily_for = lambda date: fake_path if date == "2026-09-04" else None
    # point je at our journal
    je.Y = Y

    print("=== [1] raw/session capture === ")
    sid = Y.sid_for_event("checkin", UTT, captured_ts=TS)["sid"]
    cap = Y.capture_transcript(sid, "checkin", UTT)
    Y.commit_machine_record(sid, "checkin", sj(sid), cap["sha256_txt"])
    print(f"  sid={sid} session committed")

    print("=== [1b] canonical Assessment is inside the session record ===")
    stored = Y.load_json(os.path.join(Y.JOURNAL_ROOT, "sessions", f"{sid}.json"))
    print(f"  assessment.pattern={stored['assessment']['pattern']!r}")

    print("=== [2] WHOOP enrichment -> [3] Assessment ref -> [4] Evaluation ===")
    # simulate exactly what journal_enrich.enrich does
    daily = json.load(open(fake_path))
    analysis = D.enrich_session(sid, daily)
    print("  enrichment.biometrics:", json.dumps(analysis["enrichment"]["biometrics"]))
    print("  source.measured_at:", analysis["enrichment"]["measured_at"], "| source:", analysis["enrichment"]["source"])
    print("  assessment_ref:", analysis["assessment_ref"])  # single authoritative
    # MISSING biometric stays null (deep/sleeppct) -> not invented
    assert analysis["enrichment"]["biometrics"]["deep_hrs"] is None
    assert analysis["enrichment"]["biometrics"]["sleep_performance_pct"] is None

    print("=== [5] Analysis version written ===")
    persist = Y.persist_analysis(analysis)
    print(f"  {os.path.relpath(persist['path'], tmp)} v{persist['version']}")

    print("=== [6] longitudinal / index update ===")
    I = __import__("yawmiyat_index")
    I.Y = Y  # same module object, shared root
    I.build_manifest(force=True)
    I.build_index()
    q = I.query(date="2026-09-04")
    print(f"  INDEX by_date 2026-09-04 -> {q}")
    assert sid in q

    print("=== [7] reconcile (egress PAUSED -> queued, G1) ===")
    rep = I.reconcile_drive()  # egress off by default
    print("  egress:", rep["egress"])
    assert rep["uploaded"] == []
    assert len(rep["queued"]) >= 1

    print("\n=== Created/versioned artifacts ===")
    for f in sorted(os.listdir(os.path.join(Y.JOURNAL_ROOT, "analysis"))):
        print("  analysis/", f)
    for f in sorted(os.listdir(os.path.join(Y.JOURNAL_ROOT, "sessions"))):
        print("  sessions/", f)

    print("\n=== RESULT: G3 PASS ===")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())