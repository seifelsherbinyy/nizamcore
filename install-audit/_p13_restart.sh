#!/usr/bin/env bash
echo "===== RESTART GATE ====="
systemctl --user restart hermes-gateway.service
sleep 4
echo -n "is-active="; systemctl --user is-active hermes-gateway.service
systemctl --user show hermes-gateway.service -p NRestarts -p MainPID -p ActiveState -p SubState 2>&1
echo "--- governor/traceback check (last 2 min) ---"
journalctl --user -u hermes-gateway.service --since "2 min ago" --no-pager 2>&1 \
  | grep -iE "nizam.governor|Traceback|Error loading|plugin.*error|ImportError|NameError" || echo "NO_GOVERNOR_ERRORS"
echo "===== DONE_RESTART ====="
