#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
STATE="$HOME/.hermes/nizam"
HB="$HOME/.hermes/plugins/nizam-governor/.last_mirror"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"

echo "########## BACKUP (hard rule; no code edit expected this pass) ##########"
PRE=$(sha256sum "$PLUG" | awk '{print $1}')
BAK="$PLUG.bak.$(date -u +%Y%m%dT%H%M%SZ)"
cp "$PLUG" "$BAK"
echo "BAK=$BAK"
echo "pre_sha=$PRE"

echo "########## 4. RESET TEST SESSION (data-file only) ##########"
echo "--- before ---"
echo -n "current_session.json: "; cat "$STATE/current_session.json" 2>&1; echo ""
echo -n "SESSIONS.jsonl lines: "; wc -l < "$STATE/SESSIONS.jsonl" 2>&1
echo "--- archive current_session.json -> .testseed.bak ---"
cp "$STATE/current_session.json" "$STATE/current_session.json.testseed.bak" && echo "archived"
echo "--- move SESSIONS.jsonl -> SESSIONS.testseed.jsonl (preserves test open row; append-only archive) ---"
mv "$STATE/SESSIONS.jsonl" "$STATE/SESSIONS.testseed.jsonl" && echo "moved (live SESSIONS.jsonl now absent -> next real msg opens session #1)"
echo "--- re-init current_session.json to empty {} (no active session) ---"
printf '{}' > "$STATE/current_session.json" && echo "reinit"

echo "########## confirm __init__.py NOT modified ##########"
POST=$(sha256sum "$PLUG" | awk '{print $1}')
echo "post_sha=$POST"
[ "$PRE" = "$POST" ] && echo "CODE_UNCHANGED=YES (no __init__.py edit this pass)" || echo "CODE_UNCHANGED=NO"

echo "########## 5. SYNTAX + RESTART GATE ##########"
$VPY -m py_compile "$PLUG" && echo "PY_COMPILE=PASS" || echo "PY_COMPILE=FAIL"
systemctl --user restart hermes-gateway.service
sleep 4
echo -n "is-active="; systemctl --user is-active hermes-gateway.service
systemctl --user show hermes-gateway.service -p NRestarts -p MainPID 2>&1
journalctl --user -u hermes-gateway.service --since "2 min ago" --no-pager 2>&1 \
  | grep -iE "nizam.governor|Traceback|Error loading|NameError|ImportError" || echo "NO_GOVERNOR_ERRORS"

echo "########## 6. VERIFY ##########"
echo -n "current_session.json (should be {} ): "; cat "$STATE/current_session.json" 2>&1; echo ""
echo -n "live SESSIONS.jsonl present? "; ls "$STATE/SESSIONS.jsonl" 2>&1 || echo "absent (clean — opens on first real msg)"
echo -n "archived testseed row: "; cat "$STATE/SESSIONS.testseed.jsonl" 2>&1
echo -n "baseline_schema.json valid? "; $VPY -m json.tool "$STATE/baseline_schema.json" >/dev/null && echo "YES" || echo "NO"
echo "--- mirror health ---"
$VPY "$HOME/.hermes/plugins/nizam-governor/heartbeat_mirror.py" --force 2>&1
grep -E '"type": ?"drive_mirror_ok"' "$EVENTS" 2>&1 | tail -1
echo -n ".last_mirror="; cat "$HB"; echo ""
echo -n "now_utc="; date -u +%Y-%m-%dT%H:%M:%SZ
echo "########## DONE_P5_STEP4 ##########"
