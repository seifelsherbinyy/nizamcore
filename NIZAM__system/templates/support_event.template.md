---
type: family_support
pop_module: AHEL
pop_privacy: strict_local_maximum
updated: <YYYY-MM-DD>
confidence: high
tags: [family, support]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Family support event. Tracks promises, deliveries, overdue follow-ups. Recovery_cost mandatory.

# Support Event — <person_id> — <YYYY-MM-DD>

## Event
- **Type**: support_promised / support_delivered / support_overdue / contact_made / important_date_acknowledged / support_completed
- **Support kind**: emotional / financial / logistical / medical / social / spiritual / other

## Promise
<Plain language description of what we said we'd do.>

## Deadline
<YYYY-MM-DD or none>

## Status
promised / in_progress / delivered / overdue / cancelled

## Emotional load (1–10)
<self-report>

## Recovery cost
- **Color**: green / yellow / red
- **Reasoning**: <if yellow/red, why and what to adjust>

## Follow-up
<What's next?>

## FAMILY_LEDGER entry
`{"ts":"...","person_id":"<id>","module":"AHEL","privacy_level":"strict_local_maximum","event_type":"...","support_type":"...","promised_action":"...","status":"...","recovery_cost_estimate":"..."}`
