# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Journal, Behavior & Stress-Trigger Method

## 1. Separation contract

```text
Raw journal transcript (vps_private / highest sensitivity)
  └─> immutable transcript reference + timestamp
Structured journal/assessment (cloud_private)
  └─> user-owned labels/questions; never overwrites raw transcript
Derived journal feature record (cloud_private)
  └─> themes, event tags, sentiment/valence cues, quoted-span REFERENCES only
Hypothesis ledger (cloud_private)
  └─> associations + counterevidence + confounders + next observation
```

**FACT:** Drive knowledge records may contain curated journal material when explicitly classified for private Drive; raw transcripts and highly sensitive working text default to VPS-only unless the governing privacy contract explicitly permits Drive storage.

## 2. Non-diagnostic journal feature extraction

Allowed derived fields:
- event categories supplied or directly inferable from the text context (workload, commute, social interaction, unfinished obligation, workout, travel, sleep disruption, etc.);
- sentiment/valence as a text feature, with confidence;
- recurring terms/themes;
- explicit self-reported energy/stress/mood values when the user states them;
- temporal anchors;
- action/obligation mentions;
- source span offsets or hashes for audit without forcing raw text into every derived record.

Forbidden transformations:
- diagnosis;
- personality or disorder labels presented as facts;
- inferred medication effects without evidence;
- treating negative wording as proof of physiological stress;
- rewriting raw history to match a later hypothesis.

## 3. Stress-trigger candidate record

Each candidate stores:
`candidate_trigger`, `observed_response`, `frequency`, `physiological_evidence_refs`, `journal_evidence_refs`, `counterevidence_refs`, `confounders`, `lag_definition`, `confidence_dimensions`, `next_observation_needed`, `low_risk_intervention_candidate`.

### Candidate trigger classes
people/interactions · meeting category · workload pattern · location category · commute · sleep loss · training load · time of day · journal theme · unfinished obligation · social conflict · schedule fragmentation.

## 4. Hypothesis promotion rules

- One event → **observation**, not pattern.
- Repeated co-occurrence → **candidate association**.
- Same-direction association across multiple windows + low missingness → **within-person pattern candidate**.
- Confounded or contradictory evidence → confidence down; never hide counterexamples.
- Causal language remains prohibited unless a deliberately designed N-of-1 test and appropriate analysis support it.

## 5. Behavior engine

Deterministic selection sequence:
1. Identify constraints that cannot move today.
2. List modifiable variables with evidence and current confidence.
3. Exclude actions that conflict with safety, work, relationship/recovery blocks, or user boundaries.
4. Prefer a variable already linked to a repeated problem or a foundational constraint (e.g., insufficient sleep opportunity) over novelty.
5. Choose the **smallest useful intervention**.
6. Limit to 1–3 targets.
7. Schedule only after checking calendar coverage.
8. Define one measurable next-day outcome and one human-only adherence field.
9. Next run: retain, adjust, or retire based on adherence + downstream signals.

### Difficulty scaling

- recent low adherence → simplify/reduce friction before increasing demand;
- recent physiological strain/stale data → conservative agenda;
- repeated success → small progression, one variable at a time where possible;
- no evidence → maintenance/default routine, not an invented optimization.

## 6. Sleep timing intervention example

If demonstrated sleep onset is late, NIZAM may propose a 15–30 minute earlier **behavioral target** when feasible, using recent baseline and work constraints. This is a conservative heuristic supported by practical gradual-adjustment guidance and small circadian studies, not medical treatment. The system should prefer a stable wake/sleep opportunity and adherence over demanding a multi-hour jump.

## 7. Intervention record lifecycle

`suggested -> human_approved -> active -> evaluated -> retained|modified|retired`

Human-only fields: `approved`, `completion`, `Calendar Approved`, final calendar approval.

## 8. Planner language policy

Use:
- "associated with" / "coincided with" / "followed by"
- "unusual versus your recent baseline"
- "candidate trigger"
- "possible competing explanation"

Avoid:
- "caused" unless causal evidence exists
- "your HRV proves you are stressed"
- "you need medical treatment"
- "this score means you should train hard" as a universal rule

> Advisory only — not medical diagnosis. Red flags route to qualified professionals.
