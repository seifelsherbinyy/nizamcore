#!/usr/bin/env bash
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
STATE="$HOME/.hermes/nizam"
CFG="$HOME/nizamcore/NIZAM__system/config"
LED="$HOME/nizamcore/NIZAM__system/ledgers"

echo "########## WIRING GAP: is _resolve_route CALLED + ACTIVE_CODENAME WRITTEN? ##########"
echo "--- all refs to _resolve_route / _route / _active_persona / ACTIVE_CODENAME ---"
grep -nE "_resolve_route|_active_persona|ACTIVE_CODENAME|_route\b|nizam_router" "$PLUG" 2>&1
echo "--- _resolve_route full body ---"
awk '/^def _resolve_route/{f=NR} f && NR>=f && NR<=f+30{printf "%d: %s\n", NR, $0; if(/^def /&&NR>f)exit}' "$PLUG" 2>&1 | head -34
echo "--- ACTIVE_CODENAME constant def ---"
grep -nE "^ACTIVE_CODENAME|ACTIVE_CODENAME =" "$PLUG" 2>&1

echo "########## _capture row shape (confirm fields) ##########"
awk 'NR>=401 && NR<=433{printf "%d: %s\n", NR, $0}' "$PLUG" 2>&1 | grep -E "row|_append|session|ahel|dedupe|text|redact"
echo "--- where _capture is called (session value source) ---"
grep -nE "_capture\(|def _pre_dispatch|session =|session_key|chat_id" "$PLUG" 2>&1 | head -15

echo "########## DAIR-15 / journaling / session stores on disk ##########"
echo "--- grep plugin + config for DAIR / journal / session markers ---"
grep -rniE "DAIR|journal|yawmiyat|session_start|session_end|SESSIONS" "$PLUG" "$CFG" 2>/dev/null | head -15
echo "--- ledgers dir listing ---"
ls -1 "$LED" 2>&1 | head -40
echo "--- YAWMIYAT journaling dir ---"
ls -1 "$HOME/nizamcore/YAWMIYAT__journaling" 2>&1 | head
echo "--- any existing SESSIONS / baseline files in state dir ---"
ls -1 "$STATE" 2>&1 | head -40

echo "########## router.config.yaml: route_confidence / intents / commands ##########"
sed -n '1,70p' "$STATE/router.config.yaml" 2>&1
echo "########## DONE_RECON_B ##########"
