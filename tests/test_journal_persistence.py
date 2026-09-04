#!/usr/bin/env python3
"""Regression + RPV tests for the YAWMIYAT persistence architecture.

Runs against a THROWAWAY temp journal root so the real nizamcore journal and
the real WHOOP data are never touched. Covers:
  1. synthetic session -> all layers (transcript txt+machine, session, mirror, analysis)
  2. duplicate retry (idempotency + refuse-to-clobber)
  3. scheduled enrichment (WHOOP provenance preserved; no invented values on missing)
  4. tamper detection (deliberate field flip proves MANIFEST verification)
  5. reconcile dry-run queue/retry behaviour
"""
import json, os, shutil, sys, tempfile, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import pytest
import yawmiyat as Y
import yawmiyat_derived as D
import yawmiyat_index as I


@pytest.fixture()
def tmpjournal(tmp_path, monkeypatch):
    root = os.path.join(tmp_path, "YAWMIYAT__journaling")
    monkeypatch.setattr(Y, "JOURNAL_ROOT", root)
    Y.ENSURE_ONCE = False
    Y.ensure_layout()
    return root


def _fake_daily(recovery=67, hrv=48.7, rhr=61):
    return {
        "export_date": "2026-09-04", "exported_at": "2026-09-04T08:00:00Z",
        "source": "WHOOP-daily-snapshot",
        "recovery": {"recovery_score": recovery, "hrv_rmssd_milli": hrv, "rhr": rhr},
        "sleep": {"total_hrs": 6.5, "deep_hrs": 1.3, "rem_hrs": 1.6, "sleep_performance_pct": 82},
        "cycle": {"strain": 12.4},
        "workouts": [],
    }


def _make_session(sid, mood="numbed", energy=4):
    return {
        "session_id": sid, "session_type": "checkin",
        "captured_at": "2026-09-04T12:40:49Z",
        "felt_state": {"energy": energy, "mood": mood,
                        "gut": "emotional coaster", "notable": "third pass at the loop"},
        "capacity": {"level": "MEDIUM", "trend": "declining"},
        "pillars": {"voted": ["meaning"], "missed": [], "contrary_urges": []},
        "assessment": {"pattern": "third loop: loss of control -> trigger -> reinvest",
                        "continuity_note": "observation over prosecution"},
        "plan": {"priorities": [], "recovery_item": "step back and observe", "tiny_versions": []},
        "decisions": ["between A and B; keep logging"],
        "confidence": 0.92, "needs_human_confirmation": False,
    }


# ------------------------------------------------------------------ 1. layers
def test_synthetic_all_layers(tmpjournal):
    sid = Y.new_session_id("checkin")
    utterances = [
        {"speaker": "Sherbiny", "ts": "2026-09-04T12:30:00Z", "text": "Energy 4, mood numbed or uncertain."},
        {"speaker": "Sherbiny", "ts": "2026-09-04T12:31:00Z", "text": "The LDR loop, third time."},
    ]
    cap = Y.capture_transcript(sid, "checkin", utterances)
    assert os.path.exists(cap["txt"]) and os.path.exists(cap["machine"])
    # machine record literal content identical to human transcript
    txt = open(cap["txt"]).read()
    mach = Y.load_json(cap["machine"])
    assert all(u["text"] in txt for u in mach["utterances"])
    assert len(mach["utterances"]) == 2
    # commit machine record (enriched SCRIBE)
    sj = _make_session(sid)
    res = Y.commit_machine_record(sid, "checkin", sj, transcript_sha256=cap["sha256_txt"])
    assert res["status"] == "committed"
    assert os.path.exists(os.path.join(Y.JOURNAL_ROOT, "sessions", f"{sid}.json"))
    # links embedded
    stored = Y.load_json(os.path.join(Y.JOURNAL_ROOT, "sessions", f"{sid}.json"))
    assert stored["session_id"] == sid
    assert stored["links"]["transcript"] == f"transcripts/{sid}.txt"
    # mirror
    m = Y.mirror_session(sid, stored)
    assert os.path.exists(m["path"])
    # analysis v1 (enrichment + eval, references assessment)
    ana = D.enrich_session(sid, _fake_daily())
    assert ana["analysis_version"] == 1
    assert ana["assessment_ref"]["field"] == "assessment"  # single authoritative
    persisted = Y.persist_analysis(ana)
    assert os.path.exists(persisted["path"])
    # all layers present
    for rel in [f"transcripts/{sid}.txt", f"transcripts/{sid}.utterances.json",
                f"sessions/{sid}.json", f"mirrors/{sid}.md", f"analysis/{sid}.v1.json"]:
        assert os.path.exists(os.path.join(Y.JOURNAL_ROOT, rel)), rel


# ------------------------------------------------------------ 2. duplicate
def test_duplicate_noop_and_refuse(tmpjournal):
    sid = Y.new_session_id("checkin")
    cap = Y.capture_transcript(sid, "checkin", [{"speaker": "X", "ts": "t", "text": "hi"}])
    sj = _make_session(sid)
    assert Y.commit_machine_record(sid, "checkin", json.loads(json.dumps(sj)), cap["sha256_txt"])["status"] == "committed"
    # identical retry -> noop (duplicate prevented)
    res = Y.commit_machine_record(sid, "checkin", json.loads(json.dumps(sj)), cap["sha256_txt"])
    assert res["status"] == "noop"
    # different content, same sid -> refuse (never clobber)
    sj2 = _make_session(sid, mood="changed")
    res2 = Y.commit_machine_record(sid, "checkin", sj2, cap["sha256_txt"])
    assert res2["status"] == "refused"
    stored = Y.load_json(os.path.join(Y.JOURNAL_ROOT, "sessions", f"{sid}.json"))
    assert stored["felt_state"]["mood"] == "numbed"  # unchanged


# ------------------------------------------------------------ 3. enrichment
def test_enrichment_provenance_and_no_invent(tmpjournal):
    sid = Y.new_session_id("checkin")
    cap = Y.capture_transcript(sid, "checkin", [{"speaker": "X", "ts": "t", "text": "hi"}])
    Y.commit_machine_record(sid, "checkin", _make_session(sid), cap["sha256_txt"])
    daily = _fake_daily(recovery=31, hrv=40.5, rhr=64)  # red day evidence present
    ana = D.enrich_session(sid, daily)
    bios = ana["enrichment"]["biometrics"]
    assert bios["recovery_score"] == 31 and bios["hrv_rmssd_milli"] == 40.5
    assert ana["enrichment"]["source"] == "WHOOP-daily-snapshot"
    assert ana["generated_at"]
    # missing biometric stays MISSING, never estimated
    daily_missing_sleep = {"export_date": "2026-09-04", "exported_at": "t", "source": "WHOOP",
                           "recovery": {"recovery_score": 67}, "sleep": None, "cycle": None}
    ana2 = D.enrich_session(sid, daily_missing_sleep)
    assert ana2["enrichment"]["biometrics"]["total_sleep_hrs"] is None
    assert ana2["enrichment"]["biometrics"]["recovery_score"] == 67
    # versioning: two distinct evidence sets -> two versions, old recoverable
    Y.persist_analysis(ana)                       # v1 (red-day evidence)
    ana2 = D.enrich_session(sid, daily_missing_sleep)   # different evidence -> v2
    assert ana2["analysis_version"] == 2
    assert ana2["supersedes"] == 1
    Y.persist_analysis(ana2)
    vs = Y._glob_versions(sid)
    assert vs == [1, 2]
    assert os.path.exists(os.path.join(Y.JOURNAL_ROOT, "analysis", f"{sid}.v1.json"))
    # transcript untouched
    assert open(os.path.join(Y.JOURNAL_ROOT, "transcripts", f"{sid}.txt")).read() == "[t] X:\nhi\n"


# ------------------------------------------------------------ 4. tamper
def test_tamper_detection(tmpjournal):
    sid = Y.new_session_id("checkin")
    cap = Y.capture_transcript(sid, "checkin", [{"speaker": "X", "ts": "t", "text": "hi"}])
    Y.commit_machine_record(sid, "checkin", _make_session(sid), cap["sha256_txt"])
    I.build_manifest(force=True)
    assert I.verify_manifest() == []  # clean
    # DELIBERATE TAMPER: flip the recovery value in the session json
    sess = os.path.join(Y.JOURNAL_ROOT, "sessions", f"{sid}.json")
    data = json.load(open(sess))
    data["felt_state"]["mood"] = "TAMPERED"
    json.dump(data, open(sess, "w"))
    issues = I.verify_manifest()
    assert any(i["issue"] == "TAMPERED" for i in issues)
    assert any(i["artifact"] == f"sessions/{sid}.json" for i in issues)


# ------------------------------------------------------------ 5. reconcile
def test_reconcile_queues_on_drive_unavailable(tmpjournal, monkeypatch):
    sid = Y.new_session_id("checkin")
    cap = Y.capture_transcript(sid, "checkin", [{"speaker": "X", "ts": "t", "text": "hello raw transcript"}])
    Y.commit_machine_record(sid, "checkin", _make_session(sid), cap["sha256_txt"])
    Y.mirror_session(sid, _make_session(sid))
    I.set_egress(True)  # enable egress for this test (real firewall gating)
    monkeypatch.setattr(I, "_resolve_drive_folder", lambda: (_ for _ in ()).throw(RuntimeError("drive dc")))
    rep = I.reconcile_drive()
    assert rep["errors"], "expected outage error"
    assert len(rep["queued"]) > 0, "mirrors must be queued for retry"
    # VPS copy must still exist and be authoritative (never deleted on outage)
    assert os.path.exists(os.path.join(Y.JOURNAL_ROOT, "transcripts", f"{sid}.txt"))
    # dry-run sweep still lists targets (no external IO)
    monkeypatch.setattr(I, "_resolve_drive_folder", lambda: "fake-folder-id")
    rep2 = I.reconcile_drive(dry_run=True)
    assert any("transcripts/" in r for r in rep2["skipped_vps_only"])


# ------------------------------------------------------ G1 egress feature-flag
def test_egress_paused_by_default(tmpjournal, monkeypatch):
    """G1: raw-journal Drive egress is OFF by default; reconcile queues and
    never uploads under the new policy class until the flag is set on."""
    sid = Y.new_session_id("checkin")
    cap = Y.capture_transcript(sid, "checkin", [{"speaker": "X", "ts": "t", "text": "SENSITIVE raw transcript"}])
    Y.commit_machine_record(sid, "checkin", _make_session(sid), cap["sha256_txt"])
    Y.mirror_session(sid, _make_session(sid))
    # default (no EGRESS.json in a fresh tmp journal = off)
    st = I.egress_status()
    assert st["enabled"] is False
    # should NEVER reach the real Drive transport while paused
    I._drive_script = lambda *a, **k: (_ for _ in ()).throw(AssertionError("EGRESS should be blocked, no upload attempted"))
    rep = I.reconcile_drive()
    assert rep["egress"] == "PAUSED (feature-flag off, G1)"
    assert rep["uploaded"] == []
    assert "transcripts/" + os.path.basename(cap["txt"]) in [q["rel"] for q in rep["queued"]]


# ------------------------------------------------------ G2 firewall matrix
def test_g2_strict_local_drive_firewall():
    """G2: strict_local_drive permits ONLY the designated NIZAM Drive target;
    fails closed everywhere else incl. unknown connectors."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    import sys
    if root not in sys.path:
        sys.path.insert(0, root)
    from NIZAM__system.governor import sync_arbiter as sa
    from NIZAM__system.governor import classifier as cl
    tpath = "YAWMIYAT__journaling/transcripts/YWM-1.txt"
    # permitted
    assert sa.decide(tpath, sa.Plane("drive_nizam_journals")).allowed
    # blocked on every REAL external-egress surface (GitHub, Notion, other Drive,
    # Obsidian connector is unknown -> fail closed, telegram, and plaintext VPS)
    for t in ["github_private", "notion_sanitized", "drive_clear", "drive_crypt",
              "telegram_operator", "vps_plaintext"]:
        assert not sa.decide(tpath, sa.Plane(t)).allowed, t
    # unknown connector fails closed
    assert cl.is_egress_blocked(tpath, "obsidian")[0]
    assert cl.is_egress_blocked(tpath, "unknown_connector")[0]
    # benign local-only surfaces (not external egress) remain permitted
    for t in ["laptop_disk", "vps_encrypted_volume", "zdr_inference"]:
        assert sa.decide(tpath, sa.Plane(t)).allowed, t
    # strict_local session/analysis BLOCKED for the Journal drive target too
    assert not sa.decide("YAWMIYAT__journaling/sessions/YWM-1.json",
                         sa.Plane("drive_nizam_journals")).allowed
    assert not sa.decide("YAWMIYAT__journaling/analysis/YWM-1.v1.json",
                         sa.Plane("drive_nizam_journals")).allowed


# ------------------------------------------------------ G6 ingress idempotency
def test_g6_ingress_idempotency(tmpjournal):
    """G6: replaying the same source event resolves to the SAME canonical SID
    (no new {4hex}), because the SID is derived from a deterministic event key."""
    utt = [
        {"speaker": "Sherbiny", "ts": "2026-09-04T12:30:00Z", "text": "energy 4, mood numbed"},
        {"speaker": "Sherbiny", "ts": "2026-09-04T12:31:00Z", "text": "the loop, third time"},
    ]
    first = Y.sid_for_event("checkin", utt, captured_ts="2026-09-04T12:30:00Z")
    assert first["replayed"] is False
    # replay the SAME utterances -> same sid, marked replayed
    second = Y.sid_for_event("checkin", utt, captured_ts="2026-09-04T12:30:00Z")
    assert second["sid"] == first["sid"]
    assert second["replayed"] is True
    # a DIFFERENT event (different content) -> different sid
    other = Y.sid_for_event("checkin", [{"speaker": "X", "ts": "t", "text": "totally different"}],
                            captured_ts="2026-09-04T12:30:00Z")
    assert other["sid"] != first["sid"]
    # sid is deterministic (hex = event key prefix), same for the same event
    third = Y.sid_for_event("checkin", utt, captured_ts="2026-09-04T12:30:00Z")
    assert third["sid"] == first["sid"]


# ------------------------------------------------------ G8 alias migration map
def test_g8_alias_migration(tmpjournal):
    """G8: old filenames/stems resolve to canonical SIDs via the alias map."""
    sid = "YWM-20260901-204500-checkin-f033"
    Y.register_alias("2026-09-01T20-45-00Z__checkin.json", sid)
    Y.register_alias("2026-09-01T20-45-00Z__checkin", sid)
    assert Y.resolve_alias("2026-09-01T20-45-00Z__checkin.json") == sid
    assert Y.resolve_alias("2026-09-01T20-45-00Z__checkin") == sid
    assert Y.resolve_alias("missing-thing") is None


# ------------------------------------------------------------ manifest index
def test_index_query_by_pattern(tmpjournal):
    sid = Y.new_session_id("checkin")
    cap = Y.capture_transcript(sid, "checkin", [{"speaker": "X", "ts": "t", "text": "loop again"}])
    sj = _make_session(sid)
    sj["topics"] = ["relationship", "long-distance"]; sj["people"] = ["her"]
    Y.commit_machine_record(sid, "checkin", sj, cap["sha256_txt"])
    I.build_index()
    assert sid in I.query(pattern="loop")
    assert sid in I.query(topic="relationship")
    assert sid in I.query(date="2026-09-04")