#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
RC="/home/nizam/.local/bin/rclone"
STATE="$HOME/.hermes/nizam"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"
HB="$HOME/.hermes/plugins/nizam-governor/.last_mirror"
AC="$STATE/active_codename"; MODE="$STATE/mode"

echo "===== snapshot live persona state (restore after) ====="
[ -f "$AC" ] && cp "$AC" /tmp/_ac.bak && echo "AC present" || echo "AC absent"
[ -f "$MODE" ] && cp "$MODE" /tmp/_mode.bak && echo "MODE present" || echo "MODE absent"

cat > /tmp/_p13_verify.py <<'PYEOF'
import os, importlib.util
PLUG_DIR = "/home/nizam/.hermes/plugins/nizam-governor"
spec = importlib.util.spec_from_file_location("nz_governor_v", PLUG_DIR + "/__init__.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod._capture = lambda *a, **k: None   # stub: no fake user text -> LEARNING_LEDGER, no mirror of test content
tests = [("what does year 10 look like if I stay in Cairo?", "long_horizon"),
         ("tear apart this idea: launch a paid product before Series A", "redteam"),
         ("plan the next quarter and give me a weekly battle map", "tactical_plan")]
print("=== _resolve_route (pure, no side effects) ===")
for t, exp in tests:
    r = mod._resolve_route(t)
    print("expect=%-13s target=%-7s conf=%s action=%s steps=%s" %
          (exp, r.get("target"), r.get("confidence"), r.get("route_action"), r.get("resolver_steps")))
print("=== end-to-end _pre_dispatch (logs persona_route; _capture stubbed) ===")
for t, exp in tests:
    mod._pre_dispatch(event={"text": t, "chat_id": "verifyP13"})
    print("dispatched: %s" % exp)
print("=== command override: enter /shura mode, then send a redteam-flavored msg ===")
mod._cmd_shura("")
mod._pre_dispatch(event={"text": "tear apart this idea: launch before Series A", "chat_id": "verifyP13"})
print("override dispatched (expect chosen=Salman, basis=command)")
PYEOF
$VPY /tmp/_p13_verify.py 2>&1
echo "verify_exit=$?"
rm -f /tmp/_p13_verify.py

echo "===== restore live persona state ====="
if [ -f /tmp/_ac.bak ]; then cp /tmp/_ac.bak "$AC"; rm -f /tmp/_ac.bak; echo "AC restored"; else rm -f "$AC"; echo "AC cleared (was absent)"; fi
if [ -f /tmp/_mode.bak ]; then cp /tmp/_mode.bak "$MODE"; rm -f /tmp/_mode.bak; echo "MODE restored"; else rm -f "$MODE"; echo "MODE cleared (was absent)"; fi

echo "===== (6) persona_route events (tail 6) ====="
grep -E '"type": ?"persona_route"' "$EVENTS" 2>&1 | tail -6
echo "===== (6) SESSIONS.jsonl ====="
cat "$STATE/SESSIONS.jsonl" 2>&1 | tail -4
echo "----- current_session.json -----"
cat "$STATE/current_session.json" 2>&1; echo ""
echo "===== (6) baseline_schema.json valid + QUALITATIVE constraint present ====="
$VPY -m json.tool "$STATE/baseline_schema.json" >/dev/null && echo "JSON_VALID=YES" || echo "JSON_VALID=NO"
grep -oE '"qualitative_never_auto_scored": (true|false)' "$STATE/baseline_schema.json" 2>&1
echo "===== (6) mirror undisturbed: force one real mirror ====="
$VPY "$HOME/.hermes/plugins/nizam-governor/heartbeat_mirror.py" --force 2>&1
grep -E '"type": ?"drive_mirror_ok"' "$EVENTS" 2>&1 | tail -1
echo -n ".last_mirror="; cat "$HB"; echo ""
echo -n "now_utc="; date -u +%Y-%m-%dT%H:%M:%SZ
echo "===== DONE_VERIFY ====="
