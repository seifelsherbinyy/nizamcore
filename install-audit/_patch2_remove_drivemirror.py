#!/usr/bin/env python3
# Remove ONLY the redundant unconditional _event("drive_mirror", ...) emission.
# Leaves drive_mirror_ok, drive_mirror_error, _egress_audit, .last_mirror, rclone cmd, AHEL filter, ledger set intact.
import sys, difflib
P = "/home/nizam/.hermes/plugins/nizam-governor/__init__.py"
s = open(P, encoding="utf-8").read()
orig = s

anchor = '    _event("drive_mirror", files=sorted(counts.keys()), rows=counts, ahel_excluded=True)\n'
n = s.count(anchor)
if n != 1:
    print("ABORT: anchor occurs %d times (expected 1) -- NO CHANGES WRITTEN" % n)
    sys.exit(2)
s = s.replace(anchor, "", 1)

if s == orig:
    print("ABORT: no change produced")
    sys.exit(3)

print("===== UNIFIED DIFF (orig -> patched) =====")
for line in difflib.unified_diff(orig.splitlines(), s.splitlines(),
                                 "a/__init__.py", "b/__init__.py", lineterm=""):
    print(line)

open(P, "w", encoding="utf-8").write(s)
print("===== WROTE %d bytes (was %d) =====" % (len(s.encode("utf-8")), len(orig.encode("utf-8"))))
