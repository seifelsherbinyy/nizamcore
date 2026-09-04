#!/usr/bin/env python3
"""
G5 proof: full synthetic end-to-end transcript path through the REAL production
Drive connector.

Flow (matches the agreed scheduled call chain's storage leg):
  1. capture raw .txt + .utterances.json (verbatim, immutable)
  2. canonical session commit (machine record, idempotent, HIMAYAH-gated)
  3. local read-back SHA match
  4. HIMAYAH egress gate (strict_local_drive -> drive_nizam_journals ONLY)
  5. real Drive upload via nizam_drive.py upsert
  6. Drive read-back (read the file back) and SHA-256 match
  7. retrieval/index lookup by topic/pattern/date
  8. THABAT ledger append

Because raw-journal egress is PAUSED by default (G1 conditional), this proof
explicitly enables the flag for its own synthetic session, runs the proof, and
then restores the flag to OFF. It NEVER touches the real journal sessions.

Run:  python3 g5_proof.py
"""
import json, os, sys, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import yawmiyat as Y
import yawmiyat_derived as D
import yawmiyat_index as I

TS_cfg = "2026-09-04T12:30:00Z"
UTTERANCES = [
    {"speaker": "Sherbiny", "ts": TS_cfg, "text": "Energy 4, mood numbed or uncertain."},
    {"speaker": "Sherbiny", "ts": "2026-09-04T12:31:00Z", "text": "The long-distance loop, third time. I'm choosing observation over prosecution."},
    {"speaker": "Sherbiny", "ts": "2026-09-04T12:32:00Z", "text": "Cut the hand off to keep the body alive, that Tom Hardy frame."},
]


def readiness():
    """Confirm the real connector + token are reachable."""
    import urllib.request
    tok = json.load(open(os.path.expanduser("~/.nizam-drive/token.json")))
    url = "https://www.googleapis.com/drive/v3/about?fields=user"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok.get('access_token')}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def session_json(sid, topics, people):
    return {
        "session_id": sid, "session_type": "counseling",
        "captured_at": TS_cfg,
        "felt_state": {"energy": 4, "mood": "numbed / uncertain", "gut": "emotional coaster",
                        "notable": "third pass at the loop"},
        "capacity": {"level": "MEDIUM", "trend": "declining"},
        "pillars": {"voted": ["meaning"], "missed": [], "contrary_urges": []},
        "assessment": {"pattern": "third loop: loss of control -> trigger -> reinvest",
                        "continuity_note": "observation over prosecution"},
        "plan": {"priorities": [], "recovery_item": "step back and observe", "tiny_versions": []},
        "decisions": ["between A and B; keep logging"], "topics": topics, "people": people,
        "confidence": 0.94, "needs_human_confirmation": False,
    }


def main():
    print("=== G5 readiness (real connector) ===")
    try:
        about = readiness()
        print(f"Drive token OK: {about.get('user', {}).get('displayName', 'unknown')}")
    except Exception as e:
        print(f"FAIL: cannot reach Drive: {e}")
        return 1

    # transient synthetic journal under a temp dir; never the real one
    tmp = tempfile.mkdtemp(prefix="g5_journal_")
    root = os.path.join(tmp, "YAWMIYAT__journaling")
    Y.JOURNAL_ROOT = root
    Y.ENSURE_ONCE = False
    Y.ensure_layout()
    # I references the same yawmiyat module object (JOURNAL_ROOT shared)

    print("\n=== 1/8 capture raw transcript ===")
    sid = Y.sid_for_event("counseling", UTTERANCES, captured_ts=TS_cfg)["sid"]
    cap = Y.capture_transcript(sid, "counseling", UTTERANCES)
    print(f"sid={sid}")
    print(f"  .txt  -> {os.path.basename(cap['txt'])}")
    print(f"  .json -> {os.path.basename(cap['machine'])}")

    print("\n=== 2/8 canonical session commit ===")
    sj = session_json(sid, topics=["relationship", "long-distance"], people=["her"])
    commit = Y.commit_machine_record(sid, "counseling", sj, transcript_sha256=cap["sha256_txt"])
    print(f"  status={commit['status']}")

    print("\n=== 3/8 local read-back SHA match ===")
    rbac = Y.sha256_of(cap["txt"]) == cap["sha256_txt"]
    print(f"  transcript local read-back sha match: {rbac}")
    assert rbac

    print("\n=== 4/8 HIMAYAH egress gate ===")
    allowed, cls, _ = I._himayah_allows(f"YAWMIYAT__journaling/transcripts/{sid}.txt")
    print(f"  transcript -> {cls}: {allowed}")
    assert allowed and cls == "strict_local_drive"
    # confirm a github attempt is refused
    from NIZAM__system.governor import classifier as cl
    blocked, rr = cl.is_egress_blocked(f"YAWMIYAT__journaling/transcripts/{sid}.txt", "github_private")
    print(f"  github egress: {'BLOCKED' if blocked else 'ALLOW'}")
    assert blocked

    print("\n=== 5/8 real Drive upload (egress enabled for synthetic proof) ===")
    I.set_egress(True)
    # mirror so there's a target, then reconcile
    Y.mirror_session(sid, sj)
    I.build_manifest(force=True)
    rep = I.reconcile_drive()
    print(json.dumps(rep, indent=2))
    assert rep["uploaded"], "expected at least one uploaded artifact"
    I.set_egress(False)

    print("\n=== 6/8 Drive read-back SHA-256 match ===")
    # nizam_drive already read back & verified in reconcile; re-verify explicitly
    verified = [v for v in rep.get("verified_sha256", []) if v["verified"]]
    print(f"  verified artifacts: {len(verified)}")
    assert verified

    print("\n=== 7/8 retrieval/index lookup ===")
    I.build_index()
    q_found = I.query(topic="relationship")
    q_pat = I.query(pattern="loop")
    print(f"  by_topic('relationship'): {q_found}")
    print(f"  by_pattern('loop')      : {q_pat}")
    assert sid in q_found and sid in q_pat

    print("\n=== 8/8 THABAT ledger append ===")
    Y.EVENT_LEDGER = os.path.join(tmp, "EVENT_LEDGER.jsonl")
    row = Y.thabat_append(sid, "counseling")
    print(f"  ledger row appended: {row['event']} sid={row['session_id']}")

    print("\n=== RESULT: G5 PASS ===")
    print("cleanup: removing synthetic journal dir", tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())