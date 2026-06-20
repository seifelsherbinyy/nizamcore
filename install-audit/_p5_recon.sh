#!/usr/bin/env bash
STATE="$HOME/.hermes/nizam"
NZ="$HOME/nizamcore"
LED="$NZ/NIZAM__system/ledgers"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
SITE="$HOME/.hermes/hermes-agent/hermes_cli"
GW="$HOME/.hermes/hermes-agent/gateway"

echo "########## 1. SCHEMA (full) ##########"
cat "$STATE/baseline_schema.json" 2>&1

echo "########## 1b. FEEDER REALITY CHECK ##########"
echo "--- EVENT_LEDGER distinct event types (count) ---"
grep -oE '"type": ?"[^"]+"' "$LED/EVENT_LEDGER.jsonl" 2>/dev/null | sed 's/.*: *//' | sort | uniq -c | sort -rn
echo "--- LEARNING_LEDGER rows ---"; wc -l "$LED/LEARNING_LEDGER.jsonl" 2>&1
echo "--- ledger files present ---"; ls -1 "$LED" 2>&1
echo "--- QARAR__decisions contents ---"; ls -1 "$NZ/QARAR__decisions" 2>&1 | head
echo "--- HIKMAH__learnings contents ---"; ls -1 "$NZ/HIKMAH__learnings" 2>&1 | head
echo "--- YAWMIYAT__journaling contents ---"; ls -1 "$NZ/YAWMIYAT__journaling" 2>&1 | head
echo "--- owner_profile.md present? ---"; ls -l "$STATE/owner_profile.md" 2>&1
echo "--- any command capturing QUALITATIVE notes (journal/note/yawmiyat/feel/mood)? ---"
grep -nE "register_command\(\"(journal|note|yawmiyat|mood|feel|emotion|reflect)" "$PLUG" 2>&1 || echo "none"
echo "--- BODY_LEDGER rows (health objective) ---"; wc -l "$LED/BODY_LEDGER.jsonl" 2>&1

echo "########## 2. SESSION AUTHORITIES ##########"
echo "--- (a) governor gap rule ---"
grep -nE "SESSION_GAP_SEC|_session_touch" "$PLUG" 2>&1 | head
echo "--- (b) _on_session_start + _muhasaba_check + Hermes on_session_start trigger ---"
awk 'NR>=1076 && NR<=1078{printf "%d: %s\n", NR, $0}' "$PLUG"
grep -nE "def _muhasaba_check" "$PLUG" 2>&1 | head -1
grep -rnoE "run_hook\(\"on_session_start\"|on_session_start" "$SITE" "$GW" 2>/dev/null | head -8
echo "--- (c) session_reset config: where read / acted on ---"
grep -rnoE "session_reset|after_each_pillar" "$SITE" "$GW" "$PLUG" "$NZ/NIZAM__system/config" 2>/dev/null | head -12

echo "########## 3. EXEMPLAR COVERAGE ##########"
echo "--- buckets + exemplar counts ---"
awk '/^[a-z_]+:/{b=$1} /^  - /{c[b]++} END{for(k in c)print c[k], k}' "$STATE/intent_exemplars.yaml" 2>&1 | sort -rn
echo "--- persona_route events with basis inference + confidence < 0.50 ---"
grep -E '"type": ?"persona_route"' "$LED/EVENT_LEDGER.jsonl" 2>/dev/null | grep '"basis": "inference"' | grep -E '"confidence": 0\.[0-4]' || echo "none < 0.50"
echo "--- total persona_route events so far ---"
grep -cE '"type": ?"persona_route"' "$LED/EVENT_LEDGER.jsonl" 2>/dev/null
echo "########## DONE_P5_RECON ##########"
