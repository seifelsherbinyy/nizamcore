#!/usr/bin/env bash
echo "===== STEP 6: restart gateway ====="
systemctl --user restart hermes-gateway.service
sleep 4
echo -n "is-active="; systemctl --user is-active hermes-gateway.service
echo "----- journal since 2 min ago (tail 30) -----"
journalctl --user -u hermes-gateway.service --since "2 min ago" --no-pager 2>&1 | tail -30
echo "----- governor / traceback check -----"
journalctl --user -u hermes-gateway.service --since "2 min ago" --no-pager 2>&1 \
  | grep -iE "nizam.governor|Traceback|Error loading|plugin.*error|exit-code|FAILURE" \
  || echo "NO_GOVERNOR_ERRORS"
echo "===== timer arming check ====="
systemctl --user list-timers --all --no-pager 2>&1
echo "----- timer status (tail 8) -----"
systemctl --user status nizam-mirror-heartbeat.timer --no-pager 2>&1 | tail -8
echo "----- current .last_mirror -----"
cat "$HOME/.hermes/plugins/nizam-governor/.last_mirror" 2>&1 || echo "NOT_YET_WRITTEN"
echo "===== DONE_STEP6 ====="
