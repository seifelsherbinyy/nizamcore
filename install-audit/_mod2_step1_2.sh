#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
HB="$HOME/.hermes/plugins/nizam-governor/.last_mirror"
EVENTS="$HOME/nizamcore/NIZAM__system/ledgers/EVENT_LEDGER.jsonl"

echo "########## 1. BACKUP ##########"
BAK="$PLUG.bak.$(date -u +%Y%m%dT%H%M%SZ)"
cp "$PLUG" "$BAK"
echo "BAK=$BAK"
O=$(wc -c < "$PLUG"); B=$(wc -c < "$BAK")
echo "orig_bytes=$O bak_bytes=$B"
[ "$O" = "$B" ] && echo "SIZE_MATCH=YES" || echo "SIZE_MATCH=NO -- ABORT"
sha256sum "$PLUG" "$BAK"

echo "########## 2. PRE-CHECK ##########"
echo "--- .last_mirror (current) ---"; cat "$HB" 2>&1; echo ""
echo -n "now_utc="; date -u +%Y-%m-%dT%H:%M:%SZ
echo "--- recent drive_mirror* events (tail 4) ---"
grep -E '"type": ?"drive_mirror' "$EVENTS" 2>&1 | tail -4
echo "--- heartbeat timer ---"
systemctl --user list-timers --all --no-pager 2>&1 | grep -iE "mirror|NEXT"
echo "--- gateway state + NRestarts baseline ---"
systemctl --user show hermes-gateway.service -p ActiveState -p SubState -p NRestarts -p MainPID 2>&1
echo "--- is plugin under git? uncommitted delta? ---"
git -C "$HOME/.hermes/plugins/nizam-governor" rev-parse --is-inside-work-tree 2>&1
echo "--- backups present in plugin dir ---"
ls -1 "$HOME/.hermes/plugins/nizam-governor/" | grep -E "\.bak\." | tail -6
echo "########## DONE_M2_1_2 ##########"
