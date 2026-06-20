# GATE-1 — Research patterns → implementation

## Patterns feeding L layers
- openai-agents guardrails → L4 `himayah_egress.py`
- llama_index metadata filters → L2 `context_refresh.py`
- autogen progressive stop → K4 `stability.py`

## Patterns feeding K layers
- camel society (concept only) → K4 deliberation boundaries
- semantic-kernel plugins → Phase 4 skills_registry

## Rejected for production copy
See `rejected_patterns.md` — prompts.chat unfiltered import, LangGraph dependency (deferred).
