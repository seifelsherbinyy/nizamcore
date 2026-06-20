#!/usr/bin/env bash
RC="/home/nizam/.local/bin/rclone"
echo "########## 6. ROUND-TRIP UPLOAD ##########"
STAMP="nizam-verify-$(date -u +%Y%m%dT%H%M%SZ)"
echo "$STAMP" > /tmp/nizam_verify.txt
echo "LOCAL_WROTE=$STAMP"
echo "--- rclone copy -v (tail 15) ---"
$RC copy /tmp/nizam_verify.txt drive-crypt:_verify/ -v 2>&1 | tail -15

echo "########## 7. READ BACK ##########"
READBACK="$($RC cat drive-crypt:_verify/nizam_verify.txt 2>&1)"
echo "REMOTE_READBACK=$READBACK"
if [ "$READBACK" = "$STAMP" ]; then echo "MATCH=YES (encrypt->upload->download->decrypt OK)"; else echo "MATCH=NO"; fi

echo "########## 8. CLEANUP ##########"
$RC delete drive-crypt:_verify/ 2>&1
$RC rmdir drive-crypt:_verify/ 2>&1
rm -f /tmp/nizam_verify.txt
echo "--- verify gone: remote _verify listing (should be empty/notfound) ---"
$RC ls drive-crypt:_verify/ 2>&1; echo "rc_ls_exit=$?"
echo "--- verify gone: local ---"
[ -f /tmp/nizam_verify.txt ] && echo "LOCAL_STILL_PRESENT" || echo "LOCAL_GONE"
echo "--- confirm _verify not in crypt root listing ---"
$RC lsd drive-crypt: 2>&1 | grep -i "_verify" || echo "no _verify dir in crypt root"
echo "########## DONE_678 ##########"
