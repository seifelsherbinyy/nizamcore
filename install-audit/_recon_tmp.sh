#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
echo "########## SECTION 1: ENVIRONMENT ##########"
echo "--- os-release ---"
cat /etc/os-release 2>&1 | grep -E "^(PRETTY_NAME|NAME|VERSION)=" || echo "UNKNOWN os-release"
echo "--- host/uptime/disk ---"
hostname; uptime; df -h / 2>&1
echo "--- RAM ---"
free -h 2>&1
echo "--- user/home ---"
echo "user=$(whoami) home=$HOME shell=$SHELL"

echo "########## SECTION 2: NIZAM LOCATION ##########"
ROOT=""
for c in "$HOME/nizamcore" "$HOME/NIZAM" "$HOME/nizam"; do
  if [ -d "$c" ]; then ROOT="$c"; break; fi
done
if [ -z "$ROOT" ]; then
  echo "auto-search:"; find "$HOME" -maxdepth 3 -iname "*nizam*" -type d 2>/dev/null | head -20
else
  echo "NIZAM_ROOT=$ROOT"
fi
echo "ROOT_USED=$ROOT"
if [ -n "$ROOT" ]; then
  echo "--- tree depth2 ---"
  find "$ROOT" -maxdepth 2 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/venv/*' 2>/dev/null | sort | head -120
  echo "--- runtimes ---"
  echo "node=$(node -v 2>&1) python3=$(python3 -V 2>&1) hermes=$(hermes --version 2>&1 | head -1)"
  echo "--- git HEAD ---"
  git -C "$ROOT" log --oneline -1 2>&1; git -C "$ROOT" remote -v 2>&1 | head -2
fi

echo "########## SECTION 3: PROCESS/RUNTIME ##########"
echo "--- systemd (system) nizam/hermes ---"
systemctl list-units --all 2>/dev/null | grep -iE "nizam|hermes" || echo "none (system)"
echo "--- systemd (user) ---"
systemctl --user list-units --all 2>/dev/null | grep -iE "nizam|hermes" || echo "none (user)"
echo "--- pm2 ---"; (command -v pm2 >/dev/null && pm2 list) 2>&1 || echo "pm2 not installed"
echo "--- docker ---"; (command -v docker >/dev/null && docker ps) 2>&1 || echo "docker not installed"
echo "--- processes ---"; ps aux 2>/dev/null | grep -iE "hermes|nizam" | grep -v grep || echo "no matching processes"

echo "########## SECTION 4: DRIVE INTEGRATION ##########"
echo "--- rclone present? ---"; command -v rclone >/dev/null && rclone version 2>&1 | head -1 || echo "rclone not on PATH"
echo "--- rclone remotes (names only) ---"; rclone listremotes 2>&1 || echo "UNKNOWN"
echo "--- googleapis-style references in repo ---"
if [ -n "$ROOT" ]; then
  grep -rIl -E "googleapis|google\.auth|service_account|oauth2|drive\.googleapis" "$ROOT" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv 2>/dev/null | head -20 || echo "none"
  echo "--- rclone/drive refs in repo ---"
  grep -rIl -E "rclone|drive-crypt|drive_crypt|NIZAM_config|mirror" "$ROOT" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv 2>/dev/null | head -20 || echo "none"
fi
echo "--- governor plugin Drive logic ---"
GOV="$HOME/.hermes/plugins/nizam-governor"
[ -d "$GOV" ] && grep -rIl -E "rclone|drive|mirror" "$GOV" 2>/dev/null | head -10 || echo "no governor plugin dir"
echo "--- credentials files (existence only, NO contents) ---"
for f in "$HOME/.config/rclone/rclone.conf" "$HOME/.rclone.conf"; do
  [ -f "$f" ] && echo "EXISTS: $f ($(wc -c <"$f") bytes)" || echo "absent: $f"
done
ls -la "$HOME"/*.json 2>/dev/null | awk '{print $NF, $5"B"}' || true

echo "########## SECTION 5: DEPS/CONFIG ##########"
if [ -n "$ROOT" ]; then
  for m in package.json requirements.txt pyproject.toml; do
    [ -f "$ROOT/$m" ] && { echo "--- $m (first 40 lines) ---"; head -40 "$ROOT/$m"; } || echo "absent: $m"
  done
  echo "--- node_modules present? ---"; [ -d "$ROOT/node_modules" ] && echo yes || echo no
fi
echo "--- hermes config.yaml KEY NAMES only ---"
HC="$HOME/.hermes/config.yaml"
[ -f "$HC" ] && grep -E "^[a-zA-Z_]+:" "$HC" | sed 's/:.*/:/' || echo "no $HC"
echo "--- .env key names (repo) ---"
if [ -n "$ROOT" ] && [ -f "$ROOT/.env" ]; then grep -oE "^[A-Z0-9_]+=" "$ROOT/.env" | sed 's/=$//' || echo "(empty)"; else echo "no repo .env"; fi

echo "########## SECTION 6: NETWORK ##########"
echo -n "googleapis drive about HTTP="; curl -sS -o /dev/null -w "%{http_code}" --max-time 15 https://www.googleapis.com/drive/v3/about 2>&1; echo ""
echo -n "google.com HTTP="; curl -sS -o /dev/null -w "%{http_code}" --max-time 15 https://www.google.com 2>&1; echo ""
echo "########## RECON COMPLETE ##########"
