#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"

echo "########## 3. FAULT-INJECTION (isolated, bogus remote, in-memory only) ##########"
cat > /tmp/_fault_inject.py <<'PYEOF'
import os, importlib.util
PLUG_DIR = "/home/nizam/.hermes/plugins/nizam-governor"
INIT = os.path.join(PLUG_DIR, "__init__.py")
HB = os.path.join(PLUG_DIR, ".last_mirror")
def rd():
    try:
        return open(HB).read().strip()
    except Exception:
        return "MISSING"
before = rd()
print("LAST_MIRROR_BEFORE=%s" % before)
spec = importlib.util.spec_from_file_location("nizam_governor_fault", INIT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("real_remote(in-memory)=%s" % mod.DRIVE_REMOTE)
mod.DRIVE_REMOTE = "drive-crypt-BOGUS:"   # ISOLATED: in-memory override only; disk file + live gateway untouched
print("patched_remote=%s" % mod.DRIVE_REMOTE)
mod._mirror_execute()   # rclone -> bogus remote -> nonzero exit -> should log drive_mirror_error, NOT advance .last_mirror
after = rd()
print("LAST_MIRROR_AFTER=%s" % after)
print("HELD_UNCHANGED=%s" % (before == after))
PYEOF
$VPY /tmp/_fault_inject.py 2>&1
echo "inject_exit=$?"

echo "----- (a) new EVENT_LEDGER rows from the bogus cycle (tail 3) -----"
grep -E '"type": ?"drive_mirror' "$EVENTS" 2>&1 | tail -3
echo "----- (c) gateway unaffected? -----"
echo -n "is-active="; systemctl --user is-active hermes-gateway.service
systemctl --user show hermes-gateway.service -p NRestarts -p MainPID 2>&1
echo "----- confirm REAL remote on disk is untouched (plugin still says drive-crypt:) -----"
grep -nE '^DRIVE_REMOTE' "$HOME/.hermes/plugins/nizam-governor/__init__.py"
echo "----- cleanup throwaway -----"
rm -f /tmp/_fault_inject.py && echo "fault_inject_removed"
echo "########## DONE_M2_3 ##########"
