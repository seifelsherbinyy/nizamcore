---
id: himayah_egress_guard
version: 1.0
privacy_ceiling: strict_local
activation: on_demand
---

# HIMAYAH Egress Guard

Redact strict-local fields before Telegram send.

## Constraints
- No fabricated health or journal data
- No raw journal text in egress
- Recovery-first when SUKOON capacity is limited

## Acceptance
- Maps to registry entry himayah_egress_guard
- Rubric score target >= 3/5
