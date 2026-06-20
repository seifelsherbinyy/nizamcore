# Vendor repo ranking

| Rank | Repo | Score | Decision | Recommendation |
|------|------|-------|----------|----------------|
| 1 | openai/openai-agents-python | 40/60 | adapt_pattern | Adopt guardrails/handoff patterns for HIMAYAH + council triggers |
| 2 | microsoft/autogen | 38/60 | adapt_pattern | Council deliberation + termination rules |
| 3 | crewAIInc/crewAI | 36/60 | adapt_pattern | Skills YAML + member roles |
| 4 | run-llama/llama_index | 35/60 | adapt_pattern | context_refresh metadata filters |
| 5 | langchain-ai/langgraph | 34/60 | read_only_reference | Defer dependency; mimic state graph in stdlib |
| 6 | agno-agi/agno | 33/60 | adapt_pattern | Skills registry layout |
| 7 | dair-ai/Prompt-Engineering-Guide | 32/60 | adapt_pattern | Prompt rubric only |
| 8 | microsoft/semantic-kernel | 31/60 | adapt_pattern | Plugin contracts for skills |
| 9 | openai/openai-cookbook | 30/60 | read_only_reference | Eval fixtures reference |
| 10 | modelcontextprotocol/servers | 28/60 | read_only_reference | Future MCP connectors |
| 11 | camel-ai/camel | 26/60 | read_only_reference | Council concept only; avoid theater |
| 12 | f/prompts.chat | 22/60 | read_only_reference | Structure only; no import |

**Policy:** No production dependency adoption in MVP. Local Python modules implement selected patterns.
