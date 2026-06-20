#!/usr/bin/env bash
A="$HOME/.hermes/hermes-agent/agent"
echo "########## B: TURN-HANDBACK — conversation_loop.py ##########"
echo "--- size ---"; wc -l "$A/conversation_loop.py" 2>&1
echo "--- loop control keywords ---"
grep -nE "while |for .* in |max_steps|max_turns|max_iterations|max_tool|finish_reason|stop_reason|end_turn|should_continue|tool_calls|no tool|break$|return .*messages|auto.?continue" "$A/conversation_loop.py" 2>&1 | head -50

echo "########## A: SYSTEM PROMPT — system_prompt.py ##########"
echo "--- head 40 ---"; sed -n '1,40p' "$A/system_prompt.py" 2>&1
echo "--- sources/assembly refs ---"
grep -nE "SOUL|owner_profile|persona|prefill|style|tone|verbos|format|length|concise|brief|read_file|open\(|config|personalit" "$A/system_prompt.py" 2>&1 | head -40

echo "########## A: prompt_builder.py ##########"
echo "--- size + def list ---"; wc -l "$A/prompt_builder.py" 2>&1; grep -nE "^def |^class |^    def " "$A/prompt_builder.py" 2>&1 | head -30
echo "--- style/persona/system refs ---"
grep -nE "persona|style|tone|verbos|system|SOUL|personalit|format" "$A/prompt_builder.py" 2>&1 | head -25

echo "########## who calls the model (adapter entry) ##########"
grep -rnoE "def .*generate|def .*complete|def .*chat|messages\.create|client\.messages|\.create\(|response_format" "$A/anthropic_adapter.py" "$A/chat_completion_helpers.py" 2>&1 | head -20
echo "########## DONE_R2 ##########"
