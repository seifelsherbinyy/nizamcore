#!/usr/bin/env bash
set -e
PLUG_DIR="$HOME/.hermes/plugins/nizam-governor"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"

echo "===== writing heartbeat_mirror.py ====="
cat > "$PLUG_DIR/heartbeat_mirror.py" <<'PYEOF'
#!/usr/bin/env python3
"""NIZAM Drive mirror heartbeat.

Runs the governor plugin's OWN _mirror_execute() ONLY IF the last successful mirror
(.last_mirror, written by the plugin on rclone rc==0) is missing or older than 10h.
Single-sources the ledger set + crypt remote from the plugin -- no divergent backup
definition. Invoked by nizam-mirror-heartbeat.timer (hourly check, 10h gate)."""
import os, sys, datetime, importlib.util

PLUG_DIR = os.path.dirname(os.path.abspath(__file__))
INIT = os.path.join(PLUG_DIR, "__init__.py")
HB = os.path.join(PLUG_DIR, ".last_mirror")
MAX_AGE_SEC = 10 * 3600

def _age_seconds():
    try:
        ts = open(HB).read().strip()
        dt = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
    except Exception:
        return None

force = "--force" in sys.argv
age = _age_seconds()
if not force and age is not None and age < MAX_AGE_SEC:
    print("skip: last successful mirror %.2fh ago (< 10h gate)" % (age / 3600.0))
    sys.exit(0)

spec = importlib.util.spec_from_file_location("nizam_governor_hb", INIT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    mod._mirror_execute()
except Exception as e:
    print("heartbeat mirror FAILED: %s" % (str(e)[:300]), file=sys.stderr)
    sys.exit(1)
now_hb = open(HB).read().strip() if os.path.exists(HB) else "MISSING"
print("heartbeat mirror ran (prior age=%s); .last_mirror now %s" %
      ("none" if age is None else ("%.2fh" % (age / 3600.0)), now_hb))
PYEOF
chmod +x "$PLUG_DIR/heartbeat_mirror.py"

echo "===== writing nizam-mirror-heartbeat.service ====="
cat > "$UNIT_DIR/nizam-mirror-heartbeat.service" <<'SVCEOF'
[Unit]
Description=NIZAM Drive mirror heartbeat (age-gated >=10h; runs plugin _mirror_execute)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/home/nizam/.hermes/hermes-agent/venv/bin/python /home/nizam/.hermes/plugins/nizam-governor/heartbeat_mirror.py
SVCEOF

echo "===== writing nizam-mirror-heartbeat.timer ====="
cat > "$UNIT_DIR/nizam-mirror-heartbeat.timer" <<'TMREOF'
[Unit]
Description=Hourly check; fires NIZAM Drive mirror only if >10h since last success

[Timer]
OnBootSec=15min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
TMREOF

echo "===== daemon-reload + enable --now timer ====="
systemctl --user daemon-reload
systemctl --user enable --now nizam-mirror-heartbeat.timer
echo "enable_exit=$?"

echo "===== verify: linger (headless durability) ====="
loginctl show-user "$USER" -p Linger 2>&1 || echo "loginctl UNKNOWN"
echo "===== verify: timer listed ====="
systemctl --user list-timers --all 2>&1 | grep -iE "mirror|NEXT" || echo "timer not listed"
echo "===== verify: files present ====="
ls -l "$PLUG_DIR/heartbeat_mirror.py" "$UNIT_DIR/nizam-mirror-heartbeat.service" "$UNIT_DIR/nizam-mirror-heartbeat.timer"
echo "===== DONE_DEPLOY ====="
