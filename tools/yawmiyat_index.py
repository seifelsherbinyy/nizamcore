#!/usr/bin/env python3
"""
yawmiyat_index.py — retrieval indexes/manifest, tamper detection, and Drive
reconciliation for YAWMIYAT.

Tamper detection: MANIFEST.json records the sha256 of every committed artifact.
verify_manifest() recomputes current hashes and flags any mismatch.

Drive reconcile (strict_local_drive surfaces only):
  - mirrors/**, _retrieval/**, and for continuity the raw transcript VERBATIM
    .txt mirror to the private designated NIZAM Drive location, one-way POP->Drive.
  - sessions/** and analysis/** stay VPS-only (strict_local).
  - On a Drive failure, mirrors are queued in _recovery/journal.mirror_queue.jsonl
    and retried later. The VPS copy is NEVER deleted because Drive is unavailable.
  - After each upload we READ THE DESTINATION BACK and compare sha256.
"""
import datetime, hashlib, json, os, re, subprocess, sys
import yawmiyat as Y
import yawmiyat_derived

KINDS_BY_DIR = {"transcripts": "transcript", "mirrors": "mirror", "sessions": "session",
                "analysis": "analysis", "_retrieval": "index"}
DRIVE_MIRRORABLE = {"transcripts", "mirrors"}   # strict_local_drive (per policy amendment)
DRIVE_FOLDER_NAME = "JOURNALS_REFERENCES"
EGRESS_FILE = None  # resolved dynamically against Y.JOURNAL_ROOT (_egress_path)


def _egress_path():
    return os.path.join(Y.JOURNAL_ROOT, "_retrieval", "EGRESS.json")


# Designated Drive target for strict_local_drive (harmonized w/ sync_arbiter.Plane)
DRIVE_NIZAM_JOURNALS_TARGET = "drive_nizam_journals"


# ----------------------------------------------------------- egress gate ----
def egress_status():
    """Return the current egress feature-flag. Defaults to ENABLED=false until
    the policy amendment is confirmed (G1: pause raw-journal Drive egress)."""
    pth = _egress_path()
    if os.path.exists(pth):
        try:
            return json.load(open(pth))
        except Exception:
            pass
    return {"enabled": False, "allowed_target": DRIVE_NIZAM_JOURNALS_TARGET,
            "note": "raw-journal Drive egress paused until policy amendment confirmed"}


def set_egress(enabled: bool, target: str = DRIVE_NIZAM_JOURNALS_TARGET) -> dict:
    """Explicitly flip the egress feature-flag (operator-only)."""
    Y.ensure_layout()
    cfg = {"enabled": bool(enabled), "allowed_target": target,
           "set_at": Y._now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    Y.atomic_write(_egress_path(), json.dumps(cfg, indent=2))
    return cfg


def _himayah_allows(rel):
    """Route the artifact through the REAL HIMAYAH firewall (classifier +
    sync_arbiter). Returns (allowed, classification, decision)."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    from NIZAM__system.governor import sync_arbiter as sa
    d = sa.decide(rel, sa.Plane(DRIVE_NIZAM_JOURNALS_TARGET))
    return d.allowed, d.classification, d


# ---------------------------------------------------------------- manifest --
def _relative(p):
    return os.path.relpath(p, Y.JOURNAL_ROOT)

def build_manifest(force=False):
    """Record sha256 of every committed artifact under the journal (by sid)."""
    Y.ensure_layout()
    manifest = {"version": 1, "generated_at": Y._now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "artifacts": {}}
    for sub in Y.SUBDIRS:
        if sub in ("_recovery", "_retrieval"):
            continue  # _retrieval is self-referential; _recovery is transient
        d = os.path.join(Y.JOURNAL_ROOT, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".tmp"):
                continue
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            # derive sid from filename
            sid = None
            m = re.match(r"^(YWM-\d{8}-\d{6}-[a-z]+-[0-9a-f]{4})", fn)
            if m:
                sid = m.group(1)
            manifest["artifacts"][_relative(p)] = {
                "kind": KINDS_BY_DIR.get(sub, sub.strip("_")),
                "sid": sid,
                "sha256": Y.sha256_of(p),
            }
    path = os.path.join(Y.JOURNAL_ROOT, "_retrieval", "MANIFEST.json")
    Y.atomic_write(path, json.dumps(manifest, indent=2))
    return manifest

def verify_manifest(report=None):
    """
    Compute current hashes and compare to MANIFEST.json. Returns list of
    tampered/missing artifacts (mismatch => tamper detected).
    """
    mpath = os.path.join(Y.JOURNAL_ROOT, "_retrieval", "MANIFEST.json")
    if not os.path.exists(mpath):
        return [{"artifact": "_retrieval/MANIFEST.json", "issue": "missing manifest"}]
    manifest = Y.load_json(mpath)
    issues = []
    recorded = manifest.get("artifacts", {})
    for rel, meta in sorted(recorded.items()):
        p = os.path.join(Y.JOURNAL_ROOT, rel)
        if not os.path.exists(p):
            issues.append({"artifact": rel, "issue": "missing", "recorded_sha256": meta["sha256"]})
            continue
        cur = Y.sha256_of(p)
        if cur != meta["sha256"]:
            issues.append({"artifact": rel, "issue": "TAMPERED", "recorded_sha256": meta["sha256"], "current_sha256": cur})
    return issues

# ------------------------------------------------------------------- index --
def _tags(sid, session_json):
    """Extract searchable tags: date, topics, people, entities, pattern."""
    topics = session_json.get("topics") or []
    people = session_json.get("people") or []
    entities = session_json.get("entities") or []
    date = (session_json.get("captured_at") or "")[:10]
    pat = (session_json.get("assessment", {}) or {}).get("pattern") or ""
    return {"date": date, "topics": topics, "people": people,
            "entities": entities, "pattern_words": re.findall(r"[a-z]{3,}", pat.lower())}

def build_index():
    Y.ensure_layout()
    inv = {"by_date": {}, "by_topic": {}, "by_person": {}, "by_entity": {}, "by_window": {}}
    d = os.path.join(Y.JOURNAL_ROOT, "sessions")
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            sid = fn[:-5]
            try:
                sj = Y.load_json(os.path.join(d, fn))
            except Exception:
                continue
            t = _tags(sid, sj)
            if t["date"]:
                inv["by_date"].setdefault(t["date"], []).append(sid)
            for topic in t["topics"]:
                inv["by_topic"].setdefault(topic.lower(), []).append(sid)
            for person in t["people"]:
                inv["by_person"].setdefault(person.lower(), []).append(sid)
            for entity in t["entities"]:
                inv["by_entity"].setdefault(entity.lower(), []).append(sid)
            for w in t["pattern_words"]:
                inv["by_window"].setdefault(w, []).append(sid)
    # exact-version lookup
    inv["manifest_ref"] = "_retrieval/MANIFEST.json"
    path = os.path.join(Y.JOURNAL_ROOT, "_retrieval", "INDEX.json")
    Y.atomic_write(path, json.dumps(inv, indent=2))
    return inv

def query(date=None, topic=None, person=None, entity=None, pattern=None):
    idx = Y.load_json(os.path.join(Y.JOURNAL_ROOT, "_retrieval", "INDEX.json")) if os.path.exists(
        os.path.join(Y.JOURNAL_ROOT, "_retrieval", "INDEX.json")) else {}
    sids = None
    def _and(add):
        nonlocal sids
        addset = set(add)
        sids = addset if sids is None else (sids & addset)
    if date: _and(idx.get("by_date", {}).get(date, []))
    if topic: _and(idx.get("by_topic", {}).get(topic.lower(), []))
    if person: _and(idx.get("by_person", {}).get(person.lower(), []))
    if entity: _and(idx.get("by_entity", {}).get(entity.lower(), []))
    if pattern: _and(idx.get("by_window", {}).get(pattern.lower(), []))
    return sorted(sids or [])


# ------------------------------------------------------- drive reconcile ---
def _drive_script(*args):
    return subprocess.run(
        [sys.executable, "/home/nizam/.nizam-drive/nizam_drive.py", *args],
        capture_output=True, text=True)

def _resolve_drive_folder():
    """Resolve the JOURNALS_REFERENCES folder id via the Drive API (token)."""
    import urllib.request, urllib.parse
    token = json.load(open(os.path.expanduser("~/.nizam-drive/token.json")))
    at = token.get("access_token")
    url = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode({
        "q": f"name = '{DRIVE_FOLDER_NAME}' and trashed = false and mimeType='application/vnd.google-apps.folder'",
        "fields": "files(id,name,parents)"})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {at}"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    for f in data.get("files", []):
        return f["id"]
    raise RuntimeError(f"Drive folder {DRIVE_FOLDER_NAME!r} not found")

def enqueue_mirror(rel):
    """Queue a mirror op for later retry after a Drive failure. VPS copy untouched."""
    Y.ensure_layout()
    q = os.path.join(Y.JOURNAL_ROOT, "_recovery", "journal.mirror_queue.jsonl")
    with open(q, "a") as f:
        f.write(json.dumps({"rel": rel, "queued_at": Y._now().strftime("%Y-%m-%dT%H:%M:%SZ")}) + "\n")

def _read_queue():
    q = os.path.join(Y.JOURNAL_ROOT, "_recovery", "journal.mirror_queue.jsonl")
    if not os.path.exists(q):
        return []
    rows = []
    with open(q) as f:
        for ln in f:
            if ln.strip():
                rows.append(json.loads(ln))
    return rows

def reconcile_drive(dry_run=False):
    """
    Mirror strict_local_drive artifacts (transcripts + mirrors) to the private
    NIZAM DRIVE location, ONE artifact at a time, gated FIRST by the egress
    feature-flag (G1) and THEN by the real HIMAYAH sync-arbiter firewall.
    On failure/flag-off, the artifact is queued for later retry.
    Receipts -> _retrieval/DRIVE_RECEIPTS.json. Returns report.
    """
    status = egress_status()
    if not status.get("enabled"):
        # G1: egress paused -> queue mirrorable artifacts, never upload
        q = _read_queue()
        for sub in (DRIVE_MIRRORABLE if "transcripts" in DRIVE_MIRRORABLE else DRIVE_MIRRORABLE):
            d = os.path.join(Y.JOURNAL_ROOT, sub)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn.endswith(".txt") or fn.endswith(".md"):
                        enqueue_mirror(f"{sub}/{fn}")
        report = {"uploaded": [], "queued": _read_queue(), "verified_sha256": [],
                  "skipped_vps_only": [], "errors": [],
                  "egress": "PAUSED (feature-flag off, G1)"}
        return report

    folder_id = None
    report = {"uploaded": [], "queued": [], "verified_sha256": [], "skipped_vps_only": [], "errors": []}
    if not dry_run:
        try:
            folder_id = _resolve_drive_folder()
        except Exception as e:
            report["errors"].append(f"cannot resolve drive folder: {e}")
            # queue everything, keep VPS authoritative
            for sub in ("transcripts", "mirrors"):
                d = os.path.join(Y.JOURNAL_ROOT, sub)
                if os.path.isdir(d):
                    for fn in os.listdir(d):
                        if fn.endswith(".txt") or fn.endswith(".md"):
                            enqueue_mirror(f"{sub}/{fn}")
            report["queued"] = _read_queue()
            return report
    # process queue + any current mirrorable files
    # (transcripts + mirrors, PLUS _retrieval INDEX/MANIFEST, which are
    #  strict_local_drive, permitted to drive_nizam_journals)
    targets = []
    for sub, exts in (("transcripts", (".txt",)), ("mirrors", (".md",))):
        d = os.path.join(Y.JOURNAL_ROOT, sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(exts):
                    targets.append(f"{sub}/{f}")
    for rel in ("_retrieval/INDEX.json", "_retrieval/MANIFEST.json"):
        if os.path.exists(os.path.join(Y.JOURNAL_ROOT, rel)):
            targets.append(rel)
    for rel in targets:
        p = os.path.join(Y.JOURNAL_ROOT, rel)
        # ---- REAL HIMAYAH GATE before any external transport ----
        # firewall expects repo-root-relative paths (classifier reads
        # PRIVACY_CLASSIFICATION.json globs which are repo-root based)
        repo_rel = f"YAWMIYAT__journaling/{rel}"
        allowed, cls, dec = _himayah_allows(repo_rel)
        if not allowed:
            enqueue_mirror(rel)
            report["queued"].append(rel)
            report["errors"].append(f"HIMAYAH refuse {rel}: {dec.reason}")
            continue
        if cls != "strict_local_drive":
            enqueue_mirror(rel)
            report["queued"].append(rel)
            report["errors"].append(f"{rel}: classified {cls}, not strict_local_drive (not mirrorable)")
            continue
        local_sha = Y.sha256_of(p)
        if dry_run:
            report["skipped_vps_only"].append(rel)
            continue
        r = _drive_script("upsert", p, folder_id, "--name", os.path.basename(rel))
        if r.returncode != 0:
            enqueue_mirror(rel)
            report["queued"].append(rel)
            continue
        # ---- read the destination back and verify sha256 ----
        out_upload = r.stdout.strip().splitlines()
        file_id = None
        for ln in out_upload:
            if "file_id:" in ln or "id:" in ln:
                file_id = ln.split(":")[-1].strip()
        if not file_id:
            file_id = _read_back_id(folder_id, os.path.basename(rel))
        verified = False
        if file_id:
            rd = _drive_script("read", file_id)
            if rd.returncode == 0 and Y.sha256_bytes(rd.stdout.encode()) == local_sha:
                verified = True
        report["uploaded"].append(rel)
        report["verified_sha256"].append({"rel": rel, "verified": verified})
        if not verified:
            report["errors"].append(f"read-back verification FAILED for {rel}")
    return report

def _read_back_id(folder_id, name):
    import urllib.request, urllib.parse
    token = json.load(open(os.path.expanduser("~/.nizam-drive/token.json")))
    url = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode({
        "q": f"'{folder_id}' in parents and name = '{name}' and trashed=false", "fields": "files(id)"})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token.get('access_token')}"})
    try:
        with urllib.request.urlopen(req) as r2:
            data = json.loads(r2.read())
        if data.get("files"):
            return data["files"][0]["id"]
    except Exception:
        pass
    return None