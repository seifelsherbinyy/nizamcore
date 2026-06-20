---
id: prompt_optimizer
version: 1.0
privacy_ceiling: strict_local
activation: on_demand
---

# Prompt Optimizer

Apply prompt_quality_rubric to skill text.

## Constraints
- No fabricated health or journal data
- No raw journal text in egress
- Recovery-first when SUKOON capacity is limited

## Acceptance
- Maps to registry entry prompt_optimizer
- Rubric score target >= 3/5
