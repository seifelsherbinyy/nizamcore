#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
RC="/home/nizam/.local/bin/rclone"
HB="$HOME/.hermes/plugins/nizam-governor/.last_mirror"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"

echo "===== STEP 6 (confirm stability) ====="
echo -n "is-active="; systemctl --user is-active hermes-gateway.service
systemctl --user show hermes-gateway.service -p MainPID -p NRestarts -p ActiveState -p SubState -p ActiveEnterTimestamp 2>&1
echo -n "FAILURE lines since restart settle (should be 0): "
journalctl --user -u hermes-gateway.service --since "10:34:40" --no-pager 2>&1 | grep -c "FAILURE"
echo "main proc:"; ps -o pid,etime,cmd -p "$(systemctl --user show -p MainPID --value hermes-gateway.service)" 2>&1 | tail -2

echo "===== STEP 7a/b: trigger one mirror via edited path (heartbeat --force) ====="
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
$VPY "$HOME/.hermes/plugins/nizam-governor/heartbeat_mirror.py" --force 2>&1
echo "force_exit=$?"

echo "----- (a) new logging lines in EVENT_LEDGER (last drive_mirror* events) -----"
grep -E '"type": ?"drive_mirror' "$EVENTS" 2>&1 | tail -4

echo "----- (b) .last_mirror contents (current ts) -----"
cat "$HB" 2>&1; echo ""
echo -n "now_utc="; date -u +%Y-%m-%dT%H:%M:%SZ

echo "===== STEP 7c: timer scheduled + service last run ====="
systemctl --user list-timers --all --no-pager 2>&1 | grep -iE "mirror|NEXT"
echo "----- heartbeat service status (tail 6) -----"
systemctl --user status nizam-mirror-heartbeat.service --no-pager 2>&1 | tail -6

echo "===== STEP 7: confirm fresh mirror landed (crypt newest mtime) ====="
$RC lsl drive-crypt: 2>&1 | sort -k2,3 | tail -4
echo "===== verify .last_mirror gate works: re-run WITHOUT --force (should skip) ====="
$VPY "$HOME/.hermes/plugins/nizam-governor/heartbeat_mirror.py" 2>&1
echo "===== DONE_STEP7 ====="
