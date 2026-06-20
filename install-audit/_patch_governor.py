#!/usr/bin/env python3
# Additive patch to nizam-governor __init__.py: mirror success/failure logging + heartbeat marker.
# Each anchor is asserted to occur exactly once; aborts without writing if any anchor is missing/ambiguous.
import sys, difflib
P = "/home/nizam/.hermes/plugins/nizam-governor/__init__.py"
s = open(P, encoding="utf-8").read()
orig = s

edits = []

# E1: HEARTBEAT_FILE constant, right after MIRROR_STATE definition
a1 = 'MIRROR_STATE = os.path.join(STATE_DIR, "last_mirror")\n'
r1 = a1 + 'HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_mirror")  # ISO ts of last SUCCESSFUL mirror (10h heartbeat gate)\n'
edits.append(("E1", a1, r1))

# E2: capture rclone returncode + stderr (observation only); success-gated heartbeat + failure event.
# Command, remote, AHEL filter, and ledger set are NOT changed.
a2 = (
'    subprocess.run(\n'
'        [RCLONE, "--config", RCLONE_CONF, "copy", MIRROR_DIR, DRIVE_REMOTE + DRIVE_LEDGER_DIR],\n'
'        timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,\n'
'    )\n'
'    _event("drive_mirror", files=sorted(counts.keys()), rows=counts, ahel_excluded=True)\n'
'    _egress_audit("google_drive", "drive_mirror", files=len(counts), ahel_excluded=True)\n'
)
r2 = (
'    _mr = subprocess.run(\n'
'        [RCLONE, "--config", RCLONE_CONF, "copy", MIRROR_DIR, DRIVE_REMOTE + DRIVE_LEDGER_DIR],\n'
'        timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,\n'
'    )\n'
'    _event("drive_mirror", files=sorted(counts.keys()), rows=counts, ahel_excluded=True)\n'
'    _egress_audit("google_drive", "drive_mirror", files=len(counts), ahel_excluded=True)\n'
'    # --- ADDITIVE: success/failure visibility + heartbeat marker (does not alter what/where/filter) ---\n'
'    if _mr.returncode == 0:\n'
'        try:\n'
'            with open(HEARTBEAT_FILE, "w") as _hb:\n'
'                _hb.write(_utc())\n'
'            _event("drive_mirror_ok", files=len(counts))\n'
'        except Exception:\n'
'            pass\n'
'    else:\n'
'        _event("drive_mirror_error", returncode=_mr.returncode,\n'
'               stderr=(_mr.stderr or b"").decode("utf-8", "replace")[:300])\n'
)
edits.append(("E2", a2, r2))

# E3: error event alongside existing DEAD_LETTER (trailing flush)
a3 = '        _append(DEAD_LETTER, {"ts": _utc(), "stage": "drive_mirror_trailing", "error": str(e)[:200]})\n'
r3 = a3 + '        _event("drive_mirror_error", stage="trailing", error=str(e)[:200])\n'
edits.append(("E3", a3, r3))

# E4: error event alongside existing DEAD_LETTER (immediate path)
a4 = '        _append(DEAD_LETTER, {"ts": _utc(), "stage": "drive_mirror_immediate", "error": str(e)[:200]})\n'
r4 = a4 + '        _event("drive_mirror_error", stage="immediate", error=str(e)[:200])\n'
edits.append(("E4", a4, r4))

for name, a, r in edits:
    n = s.count(a)
    if n != 1:
        print("ABORT: anchor %s occurs %d times (expected 1) -- NO CHANGES WRITTEN" % (name, n))
        sys.exit(2)
    s = s.replace(a, r, 1)

if s == orig:
    print("ABORT: no change produced")
    sys.exit(3)

print("===== UNIFIED DIFF (orig -> patched) =====")
for line in difflib.unified_diff(orig.splitlines(), s.splitlines(),
                                 "a/__init__.py", "b/__init__.py", lineterm=""):
    print(line)

open(P, "w", encoding="utf-8").write(s)
print("===== WROTE %d bytes (was %d) =====" % (len(s.encode("utf-8")), len(orig.encode("utf-8"))))
