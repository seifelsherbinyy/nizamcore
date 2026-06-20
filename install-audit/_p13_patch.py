#!/usr/bin/env python3
# Phase 1 + Phase 3 ADDITIVE scaffold for nizam-governor.
# Inference-based persona selection ALREADY EXISTS and is wired (_resolve_route ->
# _set_active_codename -> _active_persona). This patch ADDS ONLY:
#   (P1) a persona_route event logging the effective route decision (basis/confidence),
#   (P3) a time-gap SESSION scaffold (_session_touch + SESSIONS.jsonl) and baseline constants.
# No existing function body is rewritten. Anchors asserted unique; aborts on mismatch.
import sys, difflib
P = "/home/nizam/.hermes/plugins/nizam-governor/__init__.py"
s = open(P, encoding="utf-8").read()
orig = s
edits = []

# --- E1: constants (after ACTIVE_CODENAME) ---
a1 = 'ACTIVE_CODENAME = os.path.join(STATE_DIR, "active_codename")\n'
r1 = a1 + (
'# --- P1/P3 scaffold (additive): session capture + baseline schema spec ---\n'
'SESSIONS_LEDGER = os.path.join(STATE_DIR, "SESSIONS.jsonl")        # append-only per-session summary rows\n'
'CURRENT_SESSION = os.path.join(STATE_DIR, "current_session.json")  # live (mutable) session state\n'
'SESSION_GAP_SEC = 1800            # >=30 min inactivity rotates to a new session (simplest gap rule)\n'
'BASELINE_SCHEMA = os.path.join(STATE_DIR, "baseline_schema.json")  # documented spec ONLY (never auto-populated here)\n'
'BASELINE_TRIGGER = 10             # synthesis builds first baseline at N=10 sessions; diffs forward every +N. NOT IMPLEMENTED THIS PASS.\n'
)
edits.append(("E1-constants", a1, r1))

# --- E2: _session_touch function (before the HIMAYAH section) ---
a2 = '# ---------------------------------------------------------------- HIMAYAH egress governance (P4)\n'
r2 = (
'def _session_touch(persona):\n'
'    """P3 session-capture scaffold (additive, swallow-all). Time-gap sessions: a gap of\n'
'    >= SESSION_GAP_SEC of inactivity rotates to a new session. Appends an OPEN row on\n'
'    session start and a CLOSE row (final counts) on rotation to SESSIONS.jsonl (append-only).\n'
'    \'synthesis\' is always null this pass -- synthesis is NOT implemented (see BASELINE_TRIGGER)."""\n'
'    try:\n'
'        now = time.time()\n'
'        cur = None\n'
'        if os.path.exists(CURRENT_SESSION):\n'
'            try:\n'
'                cur = json.load(open(CURRENT_SESSION, encoding="utf-8"))\n'
'            except Exception:\n'
'                cur = None\n'
'        if cur and (now - float(cur.get("last_ts", 0))) < SESSION_GAP_SEC:\n'
'            cur["message_count"] = int(cur.get("message_count", 0)) + 1\n'
'            cur["last_ts"] = now\n'
'            pu = cur.get("personas_used") or []\n'
'            if persona and persona not in pu:\n'
'                pu.append(persona)\n'
'            cur["personas_used"] = pu\n'
'            _ensure(STATE_DIR)\n'
'            with open(CURRENT_SESSION, "w", encoding="utf-8") as f:\n'
'                json.dump(cur, f)\n'
'            return\n'
'        # rotate: close previous (if any), then open a new session\n'
'        if cur:\n'
'            _append(SESSIONS_LEDGER, {"session_id": cur.get("session_id"), "status": "closed",\n'
'                                      "start_ts": cur.get("start_iso"), "end_ts": _utc(),\n'
'                                      "message_count": int(cur.get("message_count", 0)),\n'
'                                      "personas_used": cur.get("personas_used") or [], "synthesis": None})\n'
'        sid = "sess-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + _sha16(str(now) + (persona or ""))[:6]\n'
'        new = {"session_id": sid, "start_ts": now, "start_iso": _utc(), "last_ts": now,\n'
'               "message_count": 1, "personas_used": ([persona] if persona else [])}\n'
'        _ensure(STATE_DIR)\n'
'        with open(CURRENT_SESSION, "w", encoding="utf-8") as f:\n'
'            json.dump(new, f)\n'
'        _append(SESSIONS_LEDGER, {"session_id": sid, "status": "open", "start_ts": _utc(),\n'
'                                  "end_ts": None, "message_count": 1,\n'
'                                  "personas_used": ([persona] if persona else []),\n'
'                                  "synthesis": None, "baseline_trigger": BASELINE_TRIGGER})\n'
'    except Exception:\n'
'        pass\n'
'\n'
'\n'
) + a2
edits.append(("E2-session_touch", a2, r2))

# --- E3: persona_route event + session touch (after _set_active_codename in _pre_dispatch) ---
a3 = '            _set_active_codename(route.get("target"))\n'
r3 = a3 + (
'            # P1 (additive): log the EFFECTIVE route decision (command/mode override wins; else inference).\n'
'            _mode_code = MODE_TO_CODENAME.get(_read_mode())\n'
'            if _mode_code:\n'
'                _chosen, _basis, _conf = _mode_code, "command", 1.0\n'
'            else:\n'
'                _rsteps = route.get("resolver_steps") or []\n'
'                _chosen = route.get("target")\n'
'                _basis = "command" if (route.get("kind") == "COMMAND" or any(str(_x).startswith("IR-1:command") for _x in _rsteps)) else "inference"\n'
'                _conf = route.get("confidence")\n'
'            _event("persona_route", chosen=_chosen, basis=_basis, confidence=_conf,\n'
'                   bucket=route.get("bucket"), route_action=route.get("route_action"),\n'
'                   steps=route.get("resolver_steps"))\n'
'            _session_touch(_chosen)\n'
)
edits.append(("E3-persona_route", a3, r3))

for name, a, r in edits:
    n = s.count(a)
    if n != 1:
        print("ABORT: anchor %s occurs %d times (expected 1) -- NO CHANGES WRITTEN" % (name, n))
        sys.exit(2)
    s = s.replace(a, r, 1)

if s == orig:
    print("ABORT: no change produced"); sys.exit(3)

print("===== UNIFIED DIFF =====")
for line in difflib.unified_diff(orig.splitlines(), s.splitlines(), "a/__init__.py", "b/__init__.py", lineterm=""):
    print(line)
open(P, "w", encoding="utf-8").write(s)
print("===== WROTE %d bytes (was %d) =====" % (len(s.encode("utf-8")), len(orig.encode("utf-8"))))
