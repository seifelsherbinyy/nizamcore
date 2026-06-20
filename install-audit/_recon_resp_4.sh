#!/usr/bin/env bash
A="$HOME/.hermes/hermes-agent/agent"
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
echo "########## B: no-tool-calls exit + max_iterations source ##########"
grep -nE "not .*tool_calls|tool_calls and|if .*tool_calls|_turn_exit_reason ?=|no_tool|else:.*final|break$" "$A/conversation_loop.py" 2>&1 | grep -iE "tool_calls|exit_reason" | head -20
echo "--- agent_init max_iterations line ---"; sed -n '250,262p' "$A/agent_init.py" 2>&1
echo "--- where max_turns config read ---"; grep -rnoE "max_turns|max_iterations" "$A/agent_init.py" 2>&1 | head
echo "--- auto_continue logic ---"; grep -rnoiE "auto_continue|auto-continue|gateway_auto_continue" "$A"/*.py 2>/dev/null | head -8

echo "########## C: persona router source files (governor P3) ##########"
awk '/def _route|def _active_persona|def _intent_route/{f=NR} f && NR>=f && NR<=f+18{printf "%d: %s\n", NR, $0; if(NR==f+18)f=0}' "$PLUG" 2>&1 | head -60
echo "--- register_command shura/naqd handlers (framing only?) ---"
awk '/def _cmd_shura|def _cmd_naqd/{f=NR} f && NR>=f && NR<=f+8{printf "%d: %s\n", NR, $0}' "$PLUG" 2>&1 | head -25
echo "########## DONE_R4 ##########"
