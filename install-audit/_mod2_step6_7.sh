#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
RC="/home/nizam/.local/bin/rclone"
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
HB="$HOME/.hermes/plugins/nizam-governor/.last_mirror"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"

echo "########## 6. RESTART GATE ##########"
systemctl --user restart hermes-gateway.service
sleep 4
echo -n "is-active="; systemctl --user is-active hermes-gateway.service
systemctl --user show hermes-gateway.service -p NRestarts -p MainPID -p ActiveState -p SubState 2>&1
echo "--- governor/traceback check (last 2 min) ---"
journalctl --user -u hermes-gateway.service --since "2 min ago" --no-pager 2>&1 \
  | grep -iE "nizam.governor|Traceback|Error loading|plugin.*error" || echo "NO_GOVERNOR_ERRORS"

echo "########## 7. POST-CHANGE VERIFY ##########"
echo "--- trigger one real mirror (--force) ---"
$VPY "$HOME/.hermes/plugins/nizam-governor/heartbeat_mirror.py" --force 2>&1
NOWTS=$(date -u +%Y-%m-%dT%H:%M)
echo "cycle_minute=$NOWTS"
echo "--- all drive_mirror* events (tail 6) — newest cycle must have _ok and NO bare drive_mirror ---"
grep -E '"type": ?"drive_mirror' "$EVENTS" 2>&1 | tail -6
echo "--- count bare 'drive_mirror' (type exactly drive_mirror) in last 6 events ---"
grep -E '"type": ?"drive_mirror"' "$EVENTS" 2>&1 | tail -3
echo "--- .last_mirror + now ---"
echo -n ".last_mirror="; cat "$HB"; echo ""
echo -n "now_utc="; date -u +%Y-%m-%dT%H:%M:%SZ
echo "--- crypt newest mtime ---"
$RC lsl drive-crypt: 2>&1 | sort -k2,3 | tail -2
echo "--- timer still scheduled ---"
systemctl --user list-timers --all --no-pager 2>&1 | grep -iE "mirror|NEXT"
echo "########## DONE_M2_6_7 ##########"
