---
type: decision
pop_module: MAL
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: medium
tags: [decision_score, 7_factor]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Score a decision on 7 factors. Ethical fit + recovery cost are vetoes (any < 3 = no-go).

# Decision Score — <YYYY-MM-DD> — <topic>

> **Disclaimer**: Personal scoring, not professional financial advice.

## Decision
<one sentence>

## 7-factor scoring (1–10)
| Factor | Score | Reasoning |
|---|---|---|
| Expected value (prob × payoff) | | |
| Effort (inverse — lower effort = higher score) | | |
| Risk (inverse — lower risk = higher score) | | |
| Cashflow timing (sooner = higher) | | |
| Skill leverage | | |
| Ethical fit (SOUL.md non-negotiables) | | |
| Recovery cost (lower cost = higher) | | |
| **Average** | | |

## Veto check
- Ethical fit < 3: <yes/no — if yes, VETO>
- Recovery cost < 3 (red): <yes/no — if yes, VETO or downshift>

## Recommendation
- **go / no-go / defer**

## Reasoning (2–3 sentences)

## Watch-outs for execution
1.
2.

## DECISION_LEDGER entry
`{"event_type":"decision_scored","module":"MAL","decision":"...","reasoning":"...","confidence":"medium"}`
