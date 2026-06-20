#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
ROOT="$HOME/nizamcore"
echo "########## 3b. GATEWAY LOGS (last 30) ##########"
journalctl --user -u hermes-gateway.service -n 30 --no-pager 2>&1 | tail -32 || echo "UNKNOWN logs"
echo "--- gateway service ExecStart/state ---"
systemctl --user show hermes-gateway.service -p ActiveState -p SubState -p ExecStart -p Restart 2>&1

echo "########## 4b. WHAT IS THE googleapis MATCH ##########"
grep -nE "googleapis|google\.auth|service_account|oauth2" "$ROOT/HIFZ__github_version_control/scripts/nizam_governor_lib.py" 2>&1 | head -10

echo "########## 4c. DRIVE MIRROR OPERATION (rclone invocation) ##########"
DM="$ROOT/HIFZ__github_version_control/scripts/nizam_drive_mirror.py"
echo "--- file size ---"; wc -l "$DM" 2>&1
echo "--- rclone subprocess calls ---"
grep -nE "rclone|subprocess|copyto|copy |sync|mkdir|drive-crypt|drive:" "$DM" 2>&1 | head -40

echo "########## 4d. GOVERNOR __init__ mirror functions ##########"
grep -nE "def (_mirror|_filter_ahel|_build_mirror|_drive)|rclone|drive-crypt" "$HOME/.hermes/plugins/nizam-governor/__init__.py" 2>&1 | head -30

echo "########## 4e. rclone.conf SECTION + KEY NAMES ONLY (no secret values) ##########"
grep -E "^\[|^type =|^type=|^remote =|^remote=" "$HOME/.config/rclone/rclone.conf" 2>&1

echo "########## 5b. GOVERNOR DEPENDENCY MANIFEST ##########"
RG="$ROOT/HIFZ__github_version_control/requirements-governor.txt"
[ -f "$RG" ] && cat "$RG" || echo "absent"
echo "--- governor deps importable in hermes venv? ---"
VPY="$HOME/.hermes/hermes-agent/venv/bin/python"
$VPY -c "import importlib;[print(m, '->', 'OK' if importlib.util.find_spec(m) else 'MISSING') for m in ['requests','yaml','dateutil','schedule']]" 2>&1 | head
echo "--- other requirements files in repo ---"
find "$ROOT" -name "requirements*.txt" -not -path '*/.git/*' 2>/dev/null

echo "########## 5c. config.yaml plugins + privacy + provider_routing (key subkeys only) ##########"
HC="$HOME/.hermes/config.yaml"
awk '/^(plugins|privacy|provider_routing|secrets):/{f=1;print;next} /^[a-zA-Z_]/{f=0} f&&/^  [a-zA-Z_]/{print}' "$HC" 2>&1 | grep -ivE "key|token|secret|password|sk-|salt" | head -40
echo "########## DONE2 ##########"
