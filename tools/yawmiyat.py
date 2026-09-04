#!/usr/bin/env python3
"""
yawmiyat.py — YAWMIYAT persistence architecture (core).

Lineage preserved on every artifact:
  raw transcript -> canonical session -> human journal -> biometrics/enrichment
  -> assessment -> evaluation -> analysis -> longitudinal indexes

Each artifact shares one immutable session_id (YWM-YYYYMMDD-HHMMSS-type-XXXX)
and cross-references its sources. The raw verbatim transcript is NEVER rewritten.

Privacy (HIMAYAH, per policy amendment under review):
  - transcripts/**, mirrors/**, _retrieval/** : strict_local_drive
        (on-disk only + MAY mirror one-way POP->Drive to the private designated
         NIZAM Drive location; read-back verified; never deleted from VPS)
  - sessions/**, analysis/**                 : strict_local (on-disk only)
  - GitHub always excluded for all of the above.
Sessions are the canonical machine record committed on human confirmation.
Assessment stays canonical INSIDE the session JSON; the analysis artifact
REFERENCES it and never holds a second copy (single authoritative value).
"""
import datetime, hashlib, json, os, re, secrets, tempfile

JOURNAL_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "YAWMIYAT__journaling")
)
SUBDIRS = ["transcripts", "sessions", "mirrors", "analysis", "_retrieval", "_recovery"]
EVENT_LEDGER = os.path.abspath(
    os.path.join(JOURNAL_ROOT, "..", "NIZAM__system", "ledgers", "EVENT_LEDGER.jsonl")
)
SID_RE = re.compile(r"^YWM-\d{8}-\d{6}-[a-z]+-[0-9a-f]{4}$")

ENSURE_ONCE = False
def ensure_layout():
    global ENSURE_ONCE
    if ENSURE_ONCE:
        return
    for s in SUBDIRS:
        os.makedirs(os.path.join(JOURNAL_ROOT, s), exist_ok=True)
    ENSURE_ONCE = True

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_of(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())

def load_json(path):
    with open(path) as f:
        return json.load(f)

def atomic_write(path, text):
    """Atomic write via tmp + rename. POSIX rename is atomic on the same fs."""
    ensure_layout()
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

def _now():
    return datetime.datetime.utcnow()

def new_session_id(session_type):
    ts = _now()
    return f"YWM-{ts:%Y%m%d-%H%M%S}-{session_type}-{secrets.randbelow(65536):04x}"


def _registry_path():
    return os.path.join(JOURNAL_ROOT, "_retrieval", "SID_REGISTRY.json")


def _aliases_path():
    return os.path.join(JOURNAL_ROOT, "_retrieval", "SID_ALIASES.json")


def _load_aliases():
    ensure_layout()
    p = _aliases_path()
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            pass
    return {"by_old_key": {}, "by_sid": {}}


def _save_aliases(aliases):
    ensure_layout()
    atomic_write(_aliases_path(), json.dumps(aliases, indent=2, ensure_ascii=False))


def register_alias(old_key, sid, old_path=None):
    """G8: map an old identifier / filename to its canonical SID so historical
    links remain resolvable. old_key accepts a bare stem or a filename."""
    _ensure_sid_valid(sid)
    a = _load_aliases()
    a["by_old_key"][old_key] = {"sid": sid, "old_path": old_path}
    a["by_sid"].setdefault(sid, []).append(old_key)
    _save_aliases(a)
    return old_key


def resolve_alias(old_key):
    """Return canonical sid for an old identifier, else None."""
    a = _load_aliases()
    hit = a["by_old_key"].get(old_key)
    return hit["sid"] if hit else None


def _load_registry():
    ensure_layout()
    p = _registry_path()
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            pass
    return {"by_event_key": {}, "by_sid": {}}


def _save_registry(reg):
    ensure_layout()
    atomic_write(_registry_path(), json.dumps(reg, indent=2, ensure_ascii=False))


def event_key(utterances):
    """Canonical event key for a raw source event (ingress idempotency).
    Deterministic over the ordered verbatim utterances; independent of any
    random session-id so the SAME source event always yields the SAME key."""
    return sha256_bytes(
        json.dumps(utterances, sort_keys=False, ensure_ascii=False).encode()
    )


def sid_for_event(session_type, utterances, captured_ts=None):
    """
    RESOLVE (ingress-level idempotency, G6): replaying the same source event
    returns the SAME canonical session_id — never a new {4hex}.

    Event key is derived deterministically from the verbatim utterance content.
    If the event has already produced a session, its existing SID is returned
    and recorded as a replay. Otherwise a NEW deterministic SID is created
    (hex part = first 4 of the event key, so it too is reproducible) and the
    registry maps event_key -> sid.
    """
    key = event_key(utterances)
    reg = _load_registry()
    if key in reg["by_event_key"]:
        return {"sid": reg["by_event_key"][key], "replayed": True, "event_key": key}
    if isinstance(captured_ts, str):
        date_part = re.sub(r"[^0-9]", "", captured_ts)[:8]
    elif captured_ts is not None:
        date_part = captured_ts.strftime("%Y%m%d")
    else:
        date_part = _now().strftime("%Y%m%d")
    time_part = _now().strftime("%H%M%S")
    hexpart = key[:4]
    sid = f"YWM-{date_part}-{time_part}-{session_type}-{hexpart}"
    reg["by_event_key"][key] = sid
    reg["by_sid"][sid] = {"event_key": key, "created_at": _now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    _save_registry(reg)
    return {"sid": sid, "replayed": False, "event_key": key}

def _ensure_sid_valid(sid):
    if not SID_RE.match(sid):
        raise ValueError(f"invalid session_id: {sid!r}")

# ------------------------------------------------------------------ capture --
def capture_transcript(sid, session_type, utterances):
    """
    Persist the verbatim chronological record of everything said. Immutable.
    Writes BOTH a human-readable .txt and a machine .utterances.json with
    identical literal content (structured timestamped utterances).
    Returns capture receipt dict.
    """
    _ensure_sid_valid(sid)
    ensure_layout()
    txt_lines = []
    for u in utterances:
        t = u.get("ts") or ""
        head = f"[{t}] {u['speaker']}:" if t else f"{u['speaker']}:"
        txt_lines.append(f"{head}\n{u['text']}\n")
    txt = "\n".join(txt_lines).rstrip() + "\n"
    txtpath = os.path.join(JOURNAL_ROOT, "transcripts", f"{sid}.txt")
    atomic_write(txtpath, txt)
    machine = {
        "session_id": sid,
        "session_type": session_type,
        "format": "timestamped_utterances",
        "utterances": [
            {"seq": i, "speaker": u["speaker"], "ts": u.get("ts"), "text": u["text"]}
            for i, u in enumerate(utterances, 1)
        ],
    }
    jsonpath = os.path.join(JOURNAL_ROOT, "transcripts", f"{sid}.utterances.json")
    atomic_write(jsonpath, json.dumps(machine, indent=2, ensure_ascii=False))
    return {
        "session_id": sid,
        "txt": txtpath,
        "machine": jsonpath,
        "sha256_txt": sha256_of(txtpath),
        "utterance_count": len(utterances),
    }

# ------------------------------------------------------- canonical session --
def _core_record(d):
    """Canonical-compare view: drop engine-embedded linkage fields so an
    identical user retry is recognised as a duplicate rather than a change."""
    return {k: v for k, v in d.items() if k not in ("links", "source")}

def commit_machine_record(sid, session_type, session_json, transcript_sha256=None):
    """
    Atomic, idempotent commit of the canonical session machine record.
    Dedupe on session_id: identical content -> no-op; different content -> refuse
    (never clobber) unless force=True. Returns status dict.
    session_json must already carry session_id == sid.
    """
    _ensure_sid_valid(sid)
    ensure_layout()
    if session_json.get("session_id") != sid:
        raise ValueError("session_json.session_id must equal sid")
    path = os.path.join(JOURNAL_ROOT, "sessions", f"{sid}.json")
    if os.path.exists(path):
        existing = json.load(open(path))
        if _core_record(existing) == _core_record(session_json):
            return {"status": "noop", "path": path, "reason": "identical content (duplicate prevented)"}
        if not session_json.get("_force_commit", False):
            return {"status": "refused", "path": path, "reason": "different content for existing session_id; refusing to clobber"}
    # embed source transcript link + hash
    if transcript_sha256:
        session_json["links"] = session_json.get("links", {})
        session_json["links"]["transcript"] = f"transcripts/{sid}.txt"
        session_json["links"]["transcript_sha256"] = transcript_sha256
        session_json.setdefault("source", {})["transcript_sha256"] = transcript_sha256
    atomic_write(path, json.dumps(session_json, indent=2, ensure_ascii=False))
    return {"status": "committed", "path": path}

# ---------------------------------------------------------------- mirror ----
def build_mirror(sid, session_json):
    """Clean Markdown human journal from the canonical session record."""
    _ensure_sid_valid(sid)
    fs = session_json.get("felt_state", {})
    cap = session_json.get("capacity", {})
    plan = session_json.get("plan", {})
    asm = session_json.get("assessment", {})
    lines = [
        f"# YAWMIYAT — {sid}",
        "",
        f"**Type:** {session_json.get('session_type')}",
        f"**Captured:** {session_json.get('captured_at')}",
        f"**Capacity:** {cap.get('level')} ({cap.get('trend')}) — {cap.get('driver')}",
        "",
        "## Felt state",
        f"- Energy: {fs.get('energy')}",
        f"- Mood: {fs.get('mood')}",
        f"- Gut: {fs.get('gut')}",
        f"- Notable: {fs.get('notable')}",
        "",
        "## Plan",
        f"- Priorities: {', '.join(plan.get('priorities', [])) or '—'}",
        f"- Recovery item: {plan.get('recovery_item') or '—'}",
        f"- Tiny versions: {', '.join(plan.get('tiny_versions', [])) or '—'}",
        "",
        "## Assessment",
        f"- Pattern: {asm.get('pattern') or '—'}",
        f"- Continuity: {asm.get('continuity_note') or '—'}",
        "",
        "## Decisions",
    ]
    for d in session_json.get("decisions", []):
        lines.append(f"- {d}")
    lines += ["", "## Raw transcript", f"- `transcripts/{sid}.txt` (verbatim, immutable)"]
    return "\n".join(lines) + "\n"

def mirror_session(sid, session_json):
    ensure_layout()
    path = os.path.join(JOURNAL_ROOT, "mirrors", f"{sid}.md")
    atomic_write(path, build_mirror(sid, session_json))
    return {"status": "mirrored", "path": path, "sha256": sha256_of(path)}

# ------------------------------------------------- embedded canonical hash --
def canonical_fingerprint(session_json):
    """Stable fingerprint of the canonical session record (for provenance)."""
    copy = dict(session_json)
    copy.pop("_force_commit", None)
    return sha256_bytes(json.dumps(copy, sort_keys=True, ensure_ascii=False).encode())

# ----------------------------------------------------------------- THABAT ---
def thabat_append(sid, session_type, event="journal_session_committed", note=None):
    """Append session row to EVENT_LEDGER.jsonl (THABAT gate). review_before_commit."""
    ensure_layout()
    row = {
        "ts": _now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor": "YAWMIYAT",
        "skill": "/nizam-checkin",
        "gate": "THABAT",
        "event": event,
        "artifact": f"YAWMIYAT__journaling/sessions/{sid}.json",
        "session_id": sid,
        "note": note,
    }
    os.makedirs(os.path.dirname(EVENT_LEDGER), exist_ok=True)
    with open(EVENT_LEDGER, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row

def _glob_versions(sid):
    """Return sorted list of existing analysis version numbers for sid."""
    _ensure_sid_valid(sid)
    d = os.path.join(JOURNAL_ROOT, "analysis")
    out = []
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        m = re.match(rf"^{re.escape(sid)}\.v(\d+)\.json$", fn)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)

def current_analysis_path(sid):
    vs = _glob_versions(sid)
    if not vs:
        return None
    return os.path.join(JOURNAL_ROOT, "analysis", f"{sid}.v{vs[-1]}.json")

def persist_analysis(analysis):
    """Write a versioned analysis artifact (never overwrites a version)."""
    sid = analysis["session_id"]
    _ensure_sid_valid(sid)
    ensure_layout()
    v = analysis["analysis_version"]
    path = os.path.join(JOURNAL_ROOT, "analysis", f"{sid}.v{v}.json")
    if os.path.exists(path):
        raise ValueError(f"analysis version {v} already exists for {sid}; refusing to overwrite (immutable version)")
    atomic_write(path, json.dumps(analysis, indent=2, ensure_ascii=False))
    return {"status": "committed", "path": path, "version": v, "sha256": sha256_of(path)}