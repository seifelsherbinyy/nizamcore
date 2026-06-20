#!/usr/bin/env bash
SITE="$HOME/.hermes/hermes-agent/hermes_cli"
A="$HOME/.hermes/hermes-agent/agent"
GW="$HOME/.hermes/hermes-agent/gateway"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
echo "--- plugins.py 130-150 (on_session_start + session_reset context) ---"
awk 'NR>=130 && NR<=150{printf "%d: %s\n", NR, $0}' "$SITE/plugins.py"
echo "--- where on_session_start hook is FIRED (run_hook / dispatch) across pkg ---"
grep -rnoE "on_session_start" "$SITE" "$A" "$GW" 2>/dev/null | grep -ivE "valid|#" | head -15
echo "--- session_reset RUNTIME use (exclude setup.py wizard) ---"
grep -rnoE "session_reset" "$SITE" "$A" "$GW" 2>/dev/null | grep -iv "setup.py" | head -15
echo "--- governor _on_session_start current location + _muhasaba_check head ---"
grep -nE "def _on_session_start|register_hook\(\"on_session_start" "$PLUG" 2>&1
awk 'NR>=753 && NR<=772{printf "%d: %s\n", NR, $0}' "$PLUG"
echo "--- config.yaml session_reset value (name+value ok, not secret) ---"
grep -nE "session_reset" "$HOME/.hermes/config.yaml" 2>&1 | head
echo "DONE_SESSAUTH"
