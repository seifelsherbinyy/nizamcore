#!/usr/bin/env bash
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
SITE="$HOME/.hermes/hermes-agent/hermes_cli"

echo "########## A. VALID HOOK EVENT NAMES plugins can register ##########"
echo "--- register_hook signature + any allowed-event list/validation in plugins.py ---"
awk 'NR>=920 && NR<=975{printf "%d: %s\n", NR, $0}' "$SITE/plugins.py"
echo "--- search for a hook-name enum / VALID_HOOKS / dispatch points ---"
grep -rnoE "(VALID_HOOKS|HOOK_NAMES|known_hooks|allowed_hooks|run_hook|dispatch_hook|call_hook)\b" "$SITE" 2>/dev/null | head
echo "--- where 'heartbeat' appears ---"
grep -rnE "heartbeat" "$SITE" 2>/dev/null | head -10
echo "--- periodic/interval/tick dispatch to plugins? ---"
grep -rnoE "run_hook\([\"'][a-z_]+[\"']" "$SITE" 2>/dev/null | sort -u | head -40

echo "########## B. MIRROR trigger path + call sites ##########"
echo "--- all references to _mirror_execute / _mirror_schedule_trailing / _mirror_trailing_flush ---"
grep -nE "_mirror_execute|_mirror_schedule_trailing|_mirror_trailing_flush" "$PLUG"
echo "--- context lines 360-375 (anything after schedule_trailing) ---"
awk 'NR>=360 && NR<=378{printf "%d: %s\n", NR, $0}' "$PLUG"

echo "########## C. defs referenced by mirror (EGRESS_AUDIT/BODY_LEDGER/_egress_audit/_event/_ensure) ##########"
grep -nE "^EGRESS_AUDIT|^BODY_LEDGER|^def _egress_audit|^def _event|^def _ensure|^def _utc" "$PLUG"
echo "--- _event body ---"
awk 'NR>=148 && NR<=165{printf "%d: %s\n", NR, $0}' "$PLUG"
echo "--- _utc body ---"
awk 'NR>=128 && NR<=147{printf "%d: %s\n", NR, $0}' "$PLUG"

echo "########## D. existing user systemd timers (so we do not collide) ##########"
ls -1 "$HOME/.config/systemd/user/" 2>&1 | grep -iE "timer|service" | head -30
echo "########## DONE_INVEST ##########"
