#!/usr/bin/env bash
A="$HOME/.hermes/hermes-agent/agent"
G="$HOME/.hermes/hermes-agent/gateway"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
HC="$HOME/.hermes/config.yaml"

echo "########## B: STOP / HANDBACK CONDITION ##########"
grep -nE "if not .*tool_calls|tool_calls:|no tool_calls|finish_reason ?=|finish_reason ==|return .*final|return .*response|break  #|hand.?back|done = True|completed" "$A/conversation_loop.py" 2>&1 | head -30
echo "--- loop head context 755-775 ---"; sed -n '755,775p' "$A/conversation_loop.py" 2>&1
echo "--- max_iterations default ---"; grep -rnoE "max_iterations *=|max_iterations: *int|DEFAULT_MAX_ITER|max_iterations\b" "$A/agent_init.py" "$A"/*.py 2>/dev/null | grep -iE "=|default" | head -8

echo "########## C: PERSONA / HANDOFF / SUB-AGENT SEARCH ##########"
grep -rnoiE "hand.?off|sub.?agent|delegate|delegation|spawn.*agent|route_to|transfer.*conversation|switch.*persona|persona.*switch|multi.?agent|take.?over" "$A" "$G" 2>/dev/null | grep -ivE "test|\.pyc" | head -30
echo "--- acp (agent client protocol) packages ---"
ls -1 "$HOME/.hermes/hermes-agent/acp_adapter" "$HOME/.hermes/hermes-agent/acp_registry" 2>&1 | head
echo "--- delegation tool? ---"
grep -rnoiE "def .*delegat|class .*Delegat|delegate_task|spawn" "$A" 2>/dev/null | head -10

echo "########## C: GOVERNOR persona modes (/shura /naqd) — framing or handoff? ##########"
grep -nE "_cmd_shura|_cmd_naqd|def _pre_llm|persona|PERSONA|Salman|Hazim|inject|system" "$PLUG" 2>&1 | head -30
echo "--- show _pre_llm persona injection block ---"
awk '/def _pre_llm/{f=NR} f && NR>=f && NR<=f+40{printf "%d: %s\n", NR, $0}' "$PLUG" 2>&1 | head -45

echo "########## A: SOUL.md resolution ##########"
awk '/def load_soul_md/{f=NR} f && NR>=f && NR<=f+28{printf "%d: %s\n", NR, $0}' "$HOME/.hermes/hermes-agent/agent/prompt_builder.py" 2>&1

echo "########## CONFIG SURFACE (section + 1st-level key names only) ##########"
grep -nE "^(agent|personalities|personas|display|voice|conversation|turn|response|style|tts|stt|skills|delegation|approvals|command_allowlist|quick_commands|hooks|plugins|provider_routing|privacy|model|toolsets):" "$HC" 2>&1
echo "--- agent: subkeys ---"
awk '/^agent:/{f=1;next} /^[a-zA-Z_]/{f=0} f&&/^  [a-zA-Z_]/{print}' "$HC" 2>&1 | sed 's/:.*/:/' | grep -ivE "key|token|secret|password" | head -40
echo "--- personalities: subkeys ---"
awk '/^personalities:/{f=1;next} /^[a-zA-Z_]/{f=0} f&&/^  [a-zA-Z_]/{print}' "$HC" 2>&1 | sed 's/:.*/:/' | head -20
echo "--- delegation: subkeys ---"
awk '/^delegation:/{f=1;next} /^[a-zA-Z_]/{f=0} f&&/^  [a-zA-Z_]/{print}' "$HC" 2>&1 | sed 's/:.*/:/' | head -20
echo "########## DONE_R3 ##########"
