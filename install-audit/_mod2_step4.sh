#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
RC="/home/nizam/.local/bin/rclone"
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
HB="$HOME/.hermes/plugins/nizam-governor/.last_mirror"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"

echo "########## 4. RESTORE + RE-VERIFY REAL MIRROR ##########"
echo "--- confirm no test artifacts remain ---"
ls -1 /tmp/_fault_inject.py 2>&1 || echo "no fault_inject temp (good)"
echo "--- run ONE real mirror (genuine remote) via heartbeat --force ---"
$VPY "$HOME/.hermes/plugins/nizam-governor/heartbeat_mirror.py" --force 2>&1
echo "force_exit=$?"
echo "--- drive_mirror_ok logged? (tail 3) ---"
grep -E '"type": ?"drive_mirror' "$EVENTS" 2>&1 | tail -3
echo "--- .last_mirror advanced to ~now? ---"
echo -n ".last_mirror="; cat "$HB"; echo ""
echo -n "now_utc=";  date -u +%Y-%m-%dT%H:%M:%SZ
echo "--- crypt remote newest mtime advanced? ---"
$RC lsl drive-crypt: 2>&1 | sort -k2,3 | tail -3
echo "########## DONE_M2_4 ##########"
