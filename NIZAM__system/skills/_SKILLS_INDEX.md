# POP Skills Index

Each skill is an encoded set of paths, conventions, and procedures — not a free prompt. Frontmatter is binding.

## Phase 1 — cognitive + recovery (12 skills + index)

| Skill | Module | Trigger | Purpose |
|---|---|---|---|
| [tafrigh-capture](tafrigh-capture.md) | TAFRIGH | `/tafrigh-capture` | Capture brain dump without judgment |
| [tafrigh-triage](tafrigh-triage.md) | TAFRIGH | `/tafrigh-triage` | Sort latest dump into Now/Next/Later/Delete/Reflect/Escalate |
| [shura-brainstorm](shura-brainstorm.md) | SHURA | `/shura-brainstorm <topic>` | Co-think a topic, vault-first research |
| [shura-connect](shura-connect.md) | SHURA | `/shura-connect <A> <B>` | Bridge two unrelated POP notes |
| [shura-emerge](shura-emerge.md) | SHURA | `/shura-emerge` | Surface unnamed patterns from last 30 days |
| [shura-graduate](shura-graduate.md) | SHURA | `/shura-graduate <fragment>` | Promote an idea fragment to a full project |
| [naqd-grill](naqd-grill.md) | NAQD | `/naqd-grill <topic>` | Red-team a position, return confidence score |
| [naqd-challenge](naqd-challenge.md) | NAQD | `/naqd-challenge <claim>` | Counter-argue using POP's own history |
| [naqd-reconcile](naqd-reconcile.md) | NAQD | `/naqd-reconcile <new_info>` | Resolve contradictions; snapshot to MAKHZAN |
| [sukoon-check](sukoon-check.md) | SUKOON | `/sukoon-check` | Log sleep/energy/stress signals |
| [pop-recap](pop-recap.md) | NIZAM | `/pop-recap` | Synthesize the week from ledgers |
| [pop-health](pop-health.md) | NIZAM | `/pop-health` | Audit POP for stale claims, orphans, contradictions, gaps |

## Phase 2 — strategy + finance + body + decisions (14 skills)

### KABIR_SHERBO (long horizon)
| Skill | Trigger | Purpose |
|---|---|---|
| [kabir-sherbo-vision](kabir-sherbo-vision.md) | `/kabir-sherbo-vision <horizon>` | Craft/update a 10/15/20-yr plan |
| [kabir-sherbo-annual-review](kabir-sherbo-annual-review.md) | `/kabir-sherbo-annual-review` | Annual scoring + pivot identification |

### MUNAWARA (tactical)
| Skill | Trigger | Purpose |
|---|---|---|
| [munawara-quarter-plan](munawara-quarter-plan.md) | `/munawara-quarter-plan` | Quarter plan with roll-up to 1-yr |
| [munawara-weekly-battle](munawara-weekly-battle.md) | `/munawara-weekly-battle` | Dynamic War Strategy + SUKOON downshift |
| [munawara-pivot](munawara-pivot.md) | `/munawara-pivot` | Major pivot record + MAKHZAN snapshot |

### MAL (finance)
| Skill | Trigger | Purpose |
|---|---|---|
| [mal-baseline](mal-baseline.md) | `/mal-baseline` | Snapshot current financial state |
| [mal-scenario](mal-scenario.md) | `/mal-scenario <pathway>` | What-if income/expense model |
| [mal-milestone-check](mal-milestone-check.md) | `/mal-milestone-check` | $1.5k → $10k ladder progress |
| [mal-exchange-rate-check](mal-exchange-rate-check.md) | `/mal-exchange-rate-check` | Verify EGP↔USD from ≥2 sources |
| [mal-decision-score](mal-decision-score.md) | `/mal-decision-score <topic>` | 7-factor decision scoring (ethical_fit + recovery_cost are vetoes) |

### BADAN (body — advisory only)
| Skill | Trigger | Purpose |
|---|---|---|
| [badan-daily-signal](badan-daily-signal.md) | `/badan-daily-signal` | Log today's body signals |
| [badan-weekly-review](badan-weekly-review.md) | `/badan-weekly-review` | Trend-based review (7-day min) |
| [badan-red-flag-check](badan-red-flag-check.md) | `/badan-red-flag-check <symptom>` | Route to qualified professionals; never diagnose |

### QARAR (decisions)
| Skill | Trigger | Purpose |
|---|---|---|
| [qarar-decide](qarar-decide.md) | `/qarar-decide <topic>` | ADR-style decision record |

## Phase 3 — family network (3 skills, scaffolded + live)

### AHEL (family — strictest privacy)
| Skill | Trigger | Purpose |
|---|---|---|
| [ahel-add-person](ahel-add-person.md) | `/ahel-add-person` | Create or update a person card (strict_local_maximum) |
| [ahel-support-log](ahel-support-log.md) | `/ahel-support-log <person_id>` | Log support promise/delivery; recovery_cost mandatory |
| [ahel-connection-cadence](ahel-connection-cadence.md) | `/ahel-connection-cadence` | Surface ≤3 overdue people/week; SUKOON-aware |

## Phase 3 — scheduled agents (designed; runner choice pending)
See [`NIZAM__system/docs/SCHEDULED_AGENTS.md`](../docs/SCHEDULED_AGENTS.md) for full cadence map + runner options (Windows Task Scheduler / claude-code-router / GitHub Actions). Recovery-first override is mandatory across all runner choices.

## Phase 3 — cross-CLI portability (designed)
See [`NIZAM__system/docs/CROSS_CLI_BUILD.md`](../docs/CROSS_CLI_BUILD.md). POP skills are already platform-agnostic markdown. Build shim script for Codex / Gemini / OpenCode pending if needed.

## Operational layers above individual skills

### Protocols (cadence-driven skill chains)
Daily / weekly / monthly / quarterly / annual / crisis / onboarding routines that chain skills in a specific order.
See [`NIZAM__system/protocols/_PROTOCOLS_INDEX.md`](../protocols/_PROTOCOLS_INDEX.md).

### Workflows (scenario-driven skill chains)
Multi-skill chains for specific situations (idea-to-decision, finance-decision, contradiction-resolution, etc.).
See [`NIZAM__system/workflows/_WORKFLOWS_INDEX.md`](../workflows/_WORKFLOWS_INDEX.md).

### Memory + continuity + data model
- [`MEMORY_MODEL.md`](../docs/MEMORY_MODEL.md) — six layers of POP memory.
- [`CONTINUITY_PROTOCOL.md`](../docs/CONTINUITY_PROTOCOL.md) — how state survives sessions / years / agents.
- [`DATA_MODEL.md`](../docs/DATA_MODEL.md) — every artifact type mapped to schema + folder + skill.

## Skill design principles
[`NIZAM__system/docs/SKILL_DESIGN_PRINCIPLES.md`](../docs/SKILL_DESIGN_PRINCIPLES.md)

## Doctrine docs per module
- KABIR_SHERBO → [`BIG_SHERBO_LONG_WAR_DOCTRINE.md`](../docs/BIG_SHERBO_LONG_WAR_DOCTRINE.md)
- MUNAWARA → [`MUNAWARA_TACTICAL_DOCTRINE.md`](../docs/MUNAWARA_TACTICAL_DOCTRINE.md)
- MAL → [`MAL_FINANCIAL_LADDER.md`](../docs/MAL_FINANCIAL_LADDER.md)
- BADAN → [`BADAN_HEALTH_ADVISORY_NOTES.md`](../docs/BADAN_HEALTH_ADVISORY_NOTES.md)
- AHEL (Phase 3) → [`AHEL_FAMILY_PRIVACY_RULES.md`](../docs/AHEL_FAMILY_PRIVACY_RULES.md)
