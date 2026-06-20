#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"

echo "########## 1. BACKUP ##########"
BAK="$PLUG.bak.$(date -u +%Y%m%dT%H%M%SZ)"
cp "$PLUG" "$BAK"
echo "BAK=$BAK"
echo "--- ls -l original + bak ---"
ls -l "$PLUG" "$BAK"
O=$(wc -c < "$PLUG"); B=$(wc -c < "$BAK")
echo "orig_bytes=$O bak_bytes=$B"
[ "$O" = "$B" ] && echo "SIZE_MATCH=YES" || echo "SIZE_MATCH=NO -- DO NOT PROCEED"
echo "--- sha256 match ---"
sha256sum "$PLUG" "$BAK"

echo "########## 2a. TOP IMPORTS (lines 1-60) ##########"
awk 'NR>=1 && NR<=60{printf "%d: %s\n", NR, $0}' "$PLUG"

echo "########## 2b. _filter_ahel / _build_mirror_set / _mirror_ledgers_async (260-360) ##########"
awk 'NR>=260 && NR<=360{printf "%d: %s\n", NR, $0}' "$PLUG"

echo "########## 2c. register(ctx) (970-996) ##########"
awk 'NR>=970 && NR<=996{printf "%d: %s\n", NR, $0}' "$PLUG"

echo "########## 2d. what _event() does + LEDGERS defs ##########"
grep -nE "^def _event|^def _append|^LEARNING_LEDGER|^EVENT_LEDGER|^DEAD_LETTER|^def _utc|^import logging|logging\.|^LOG |getLogger" "$PLUG" | head -30

echo "########## 2e. HERMES periodic/cron/interval hook API? (read-only grep of installed pkg) ##########"
VENV="$HOME/.hermes/hermes-agent/venv"
SITE=$($VENV/bin/python -c "import hermes_cli,os;print(os.path.dirname(hermes_cli.__file__))" 2>&1)
echo "hermes_cli at: $SITE"
echo "--- register_* methods exposed to plugins ---"
grep -rnoE "register_(hook|command|cron|interval|periodic|timer|schedule|task)" "$SITE" 2>/dev/null | sort | uniq -c | sort -rn | head -20
echo "--- known hook names referenced ---"
grep -rhoE "\"(pre_gateway_dispatch|post_llm_call|on_session_start|on_tick|on_interval|periodic|cron_tick|on_schedule|heartbeat)\"" "$SITE" 2>/dev/null | sort | uniq -c | head -20
echo "--- cron registration surface ---"
grep -rnoE "def register_cron|add_cron|cron_job|schedule_job|register_periodic|add_interval" "$SITE" 2>/dev/null | head -20
echo "########## DONE_STEP_1_2 ##########"
