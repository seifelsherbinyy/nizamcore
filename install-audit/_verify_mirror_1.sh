#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
RC="/home/nizam/.local/bin/rclone"
GOV="$HOME/.hermes/plugins/nizam-governor/__init__.py"

echo "########## 1. WHEN DID THE MIRROR LAST RUN ##########"
echo "--- 48h grep (last 40) ---"
journalctl --user -u hermes-gateway.service --since "48 hours ago" 2>&1 | grep -iE "mirror|rclone|drive-crypt|_mirror_ledgers" | tail -40
echo "--- [exit grep above; empty = no mirror activity in 48h] ---"
echo "--- widen: any-time mirror lines (last 10) ---"
journalctl --user -u hermes-gateway.service --no-pager 2>&1 | grep -iE "mirror|rclone|drive-crypt|_mirror_ledgers" | tail -10
echo "--- mirror-related markers count (boot) ---"
journalctl --user -u hermes-gateway.service --no-pager 2>&1 | grep -ciE "mirror|rclone|drive-crypt"

echo "########## 2. IS THE TRIGGER WIRED ##########"
echo "--- call sites of _mirror_ledgers_async ---"
grep -nE "_mirror_ledgers_async" "$GOV" 2>&1
echo "--- scheduling / hook / interval registration context ---"
grep -nE "cron|interval|schedule|every|register|hook|@|on_|async def _governor|MIRROR_INTERVAL|_cycle|tick|period" "$GOV" 2>&1 | head -40

echo "########## 3. CAN RCLONE SEE THE REMOTE ##########"
echo "--- listremotes ---"; $RC listremotes 2>&1
echo "--- about drive: (head 5) ---"; $RC about drive: 2>&1 | head -5

echo "########## 4. WHAT IS IN THE CRYPT REMOTE ##########"
echo "--- ls drive-crypt: (tail 20) ---"; $RC ls drive-crypt: 2>&1 | tail -20
echo "--- file count ---"; $RC ls drive-crypt: 2>&1 | wc -l

echo "########## 5. AGE OF NEWEST MIRRORED FILE ##########"
echo "--- lsl sorted (tail 5) ---"; $RC lsl drive-crypt: 2>&1 | sort -k2,3 | tail -5
echo "--- now (UTC) ---"; date -u
echo "########## DONE_1_5 ##########"
