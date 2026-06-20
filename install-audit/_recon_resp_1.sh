#!/usr/bin/env bash
ROOT="$HOME/.hermes/hermes-agent"
SITE="$ROOT/hermes_cli"
echo "########## LAYOUT ##########"
echo "--- hermes-agent top dirs ---"
ls -1 "$ROOT" 2>&1 | head -40
echo "--- python packages (dirs with __init__) ---"
find "$ROOT" -maxdepth 2 -name "__init__.py" -not -path "*/venv/*" 2>/dev/null | sed 's#/__init__.py##' | head -30
echo "--- agent package? ---"
ls -1 "$ROOT/agent" 2>&1 | head -40

echo "########## LLM CALL SITE ##########"
grep -rnoE "messages\.create|chat\.completions|litellm\.|completion\(|acompletion\(|\.create\(|client\.responses|anthropic|openai" "$SITE" "$ROOT/agent" 2>/dev/null | grep -ivE "test|#" | head -30
echo "--- files that look like the LLM/agent core ---"
ls -1 "$SITE" 2>&1 | grep -iE "agent|loop|model|llm|core|runner|engine|chat"
ls -1 "$ROOT/agent" 2>&1 | grep -iE "agent|loop|model|llm|core|runner|engine|chat|prompt|system"

echo "########## DISPATCH CHAIN (gateway -> reply) ##########"
grep -rnoE "run_hook\([\"'][a-z_]+[\"']\)?" "$SITE/gateway.py" 2>/dev/null | head -30
echo "--- gateway dispatch / handle message functions ---"
grep -nE "def .*dispatch|def .*handle|def .*on_message|def .*process|MessageEvent|async def run" "$SITE/gateway.py" 2>/dev/null | head -30

echo "########## SYSTEM PROMPT ASSEMBLY ##########"
grep -rnoE "system_prompt|system prompt|build_system|assemble_system|persona|SOUL|owner_profile|prefill_messages" "$SITE" "$ROOT/agent" 2>/dev/null | grep -ivE "test" | head -30
echo "########## DONE_R1 ##########"
