# Top 20 capability patterns → NIZAM mapping

| # | Pattern | Source | NIZAM module | Risk | Acceptance test |
|---|---------|--------|--------------|------|-----------------|
| 1 | Guardrails pre-send | openai-agents-python | `pulsation/himayah_egress.py` | Over-blocking | `test_himayah_redacts_journal` |
| 2 | Agent handoff routing | openai-agents-python | `pulsation/routing.py` | Wrong agent | `test_routing_by_freshest_source` |
| 3 | Progressive multi-agent stop | autogen | `council/stability.py` | Token waste | `test_adaptive_stop` |
| 4 | Agent-as-tool (not voice) | autogen | `council/members.py` Ammar | Egress leak | `test_veto_blocks_approval` |
| 5 | Role/task YAML separation | crewAI | `skills_registry/` | Drift | `test_skills_registry` |
| 6 | Metadata-filtered retrieval | llama_index | `context_refresh.py` | Fabrication | `test_context_refresh_no_fabrication` |
| 7 | Evidence pack (no raw docs) | llama_index RAG | `council/evidence.py` | Journal leak | `test_evidence_pack_excludes_journal_body_egress` |
| 8 | State graph checkpoints | langgraph | `pulsation/state.py` | State corruption | `test_state_persistence` |
| 9 | Human-in-the-loop gate | langgraph | `council/triggers.py` | Noise | `test_routine_pulse_skips_full_council` |
| 10 | Cookbook skill layout | agno | `NIZAM__system/skills/*.skill.md` | Sprawl | registry schema validate |
| 11 | MCP tool boundaries | MCP servers | `CONNECTORS.json` | Unsafe tools | config-only probe |
| 12 | Prompt rubric taxonomy | Prompt-Engineering-Guide | `prompt_quality_rubric.md` | Generic prompts | rubric score ≥3 |
| 13 | Structured output schema | openai-cookbook | `schemas/*.schema.json` | Schema drift | jsonschema tests |
| 14 | Plugin/skill contracts | semantic-kernel | `skills_registry/registry.schema.json` | Over-abstraction | router mapping test |
| 15 | Dissent preservation | council gap report | `council/deliberation.py` | Lost minority | verdict dissent field |
| 16 | Hash-chained audit trail | NIZAM THABAT | `pulsation/ledger.py` | Ledger gap | `test_ledger_append` |
| 17 | Recovery downshift gate | NIZAM SUKOON | `proactive.py` + `loops.py` | Hard block | `test_sukoon_tiny_mode` |
| 18 | Collision scheduling | pulsation spec | `collision.py` | Double send | `test_collision_loop_a_wins` |
| 19 | Dry-run receipt | Phase 2 spec | `run_pulsation_loops.py` | Live send | `--dry-run` JSON |
| 20 | Visible council on demand | council spec | `view_renderer.py` | Routine debate | Loop A no debate text |
