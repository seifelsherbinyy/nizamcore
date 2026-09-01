# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Metric Dictionary & Deterministic Calculation Specification

## Calculation doctrine

- **FACT:** Provider metrics are stored, not recomputed unless the provider publishes the exact method and NIZAM has a reason to reproduce it.
- **FACT:** Personal baselines take precedence over population norms for ordinary trend interpretation.
- **ASSUMPTION:** The MVP defaults below are engineering rules, not physiological cutoffs. Every rule carries a `method_version` and can be recalibrated.
- **FACT:** Missing inputs produce `null`/`insufficient_data`, never imputation by the LLM.

## Common statistics

For each metric `x` over windows `W ∈ {3,7,14,30,90}` calendar days:

| Metric | Deterministic method | Guard |
|---|---|---|
| `n_obs_W` | count(valid observations in W) | always |
| `coverage_W` | valid calendar days / W | distinguish missingness from stability |
| `mean_W` | arithmetic mean | only if metric supports averaging |
| `median_W` | median | preferred robust center |
| `sd_W` | sample SD | return null if n<2 |
| `mad_W` | median(abs(x - median(x))) | robust variability |
| `pctl_today_W` | empirical percentile rank of today within W | null if today missing |
| `robust_z_W` | `0.67448975 * (x_today - median_W) / mad_W` | if MAD=0 => null + `zero_mad` |
| `slope_W` | OLS slope of value versus elapsed day | expose n and coverage; no causal meaning |
| `acceleration_proxy_7` | `slope(last_7d) - slope(previous_7d)` | trend-change proxy, not a physical acceleration |

### Data sufficiency

- **FACT:** Existing BADAN doctrine requires at least 4 of 7 daily signals for a weekly trend. Preserve that rule for 7-day compatibility.
- **ASSUMPTION:** For other windows, initial MVP confidence should depend on `n_obs`, coverage and source quality rather than inventing a hard medical threshold. Values may be calculated with low coverage, but the planner must not label them a stable trend.

## Personal baseline registry

Each metric declares one baseline policy. Proposed default:
- `baseline_center = trailing_30d_median` excluding the target observation;
- `baseline_dispersion = trailing_30d_MAD`;
- when 30-day evidence is insufficient, widen to 90 days rather than substitute a population norm;
- when both are insufficient, baseline fields are null.

**ASSUMPTION:** Thirty days is a practical initial engineering window, not a biological truth. Recalibrate per metric after longitudinal review.

## WHOOP/source metric map

| Source fact | Store | Derived use | Interpretation guard |
|---|---|---|---|
| Recovery score | `provider_recovery_score_pct` | baseline delta/trend only | proprietary score; no diagnosis |
| HRV RMSSD | `provider_hrv_rmssd_ms` | rolling center/variability | context-sensitive; no "mental stress" claim alone |
| Resting HR | `provider_resting_hr_bpm` | rolling center/variability | use personal baseline |
| Respiratory rate | source field when exposed | rolling center/anomaly flag | unusual != disease |
| SpO2 / skin temp | source field when device/account exposes | trend/anomaly flag | no diagnostic thresholding |
| Cycle strain | `provider_cycle_strain` | within-person context | proprietary scale; no universal readiness cutoff |
| Workout strain | `provider_workout_strain` | session context | separate from gym volume |
| Sleep performance | `provider_sleep_performance_pct` | trend/context | retain provider semantics |
| Sleep stage durations | milliseconds → normalized minutes | duration summaries | wearable estimates, not PSG truth |
| Sleep start/end | UTC + source offset | Cairo timing, midpoint | preserve nap flag |
| Sleep need components | provider fields if exposed | shortfall context | do not reverse-engineer proprietary formulas |

## Sleep metrics

### `derived_sleep_duration_min`
Sum provider sleep-stage durations designated as sleep, after unit normalization. Keep provider total if provided and compare for QA.

### `derived_sleep_shortfall_min`
`max(0, provider_sleep_need_min - derived_sleep_duration_min)` only when a provider/user target exists for that sleep opportunity. If no target exists, `null`. Do not label this a clinical sleep debt.

### `derived_sleep_onset_drift_min`
Circular signed difference between today's local sleep onset and the baseline circular center. Range `[-720, +720]` minutes.

### `derived_sleep_midpoint_drift_min`
Same method using sleep midpoint.

### `derived_sleep_timing_variability_min_W`
Circular MAD/dispersion of local sleep onset and wake times in W. Keep WHOOP's own sleep-consistency score separately if available.

## Workout metrics

- `session_count_W`: count completed human-logged sessions.
- `training_minutes_W`: sum validated durations.
- `exercise_exposure_count_W`: per-exercise session exposures.
- `volume_load`: `sum(load * reps)` **only within comparable exercise/unit conventions**; never aggregate unlike machines/exercises into a universal physiological load.
- `provider_strain`: retained separately from gym ledger volume.
- `symptom_flag_count_W`: count explicitly human-recorded symptoms; no symptom inferred from performance.

## Recommendation adherence

Human-only completion fields:
- `due_count` = approved interventions due in period.
- `completed_count` = user explicitly marked completed.
- `adherence_rate = completed_count / due_count` when due_count>0.

**FACT:** Calendar occurrence, app opening, or wearable movement does not equal completion unless the user has explicitly authorized that proxy as the completion definition.

## Weekday/weekend comparison

For a metric, report each group's median, MAD, n and date range. Compare with raw difference and optional standardized effect; never phrase as causal.

## Lagged association

For candidate X and outcome Y:
- define exact lag: e.g. `X(day t) -> Y(sleep ending t+1)`;
- align on timestamps, not vague calendar labels;
- report Spearman rho and optionally Pearson r, n_pairs, missingness and date range;
- repeat across rolling windows;
- test/adjust autocorrelation in advanced models before elevating confidence;
- store competing explanations/confounders.

No association becomes causal evidence without a designed intervention/experiment and adequate analysis.

## Anomaly/change-point layer

MVP:
1. robust-z and percentile flags;
2. missingness/staleness checks;
3. cross-signal corroboration;
4. change-point analysis only as a separate offline detector.

**ASSUMPTION:** Any alert threshold is a versioned engineering heuristic. Alert text says "unusual versus your recent baseline," not "abnormal" or "disease."

## Epistemic confidence

Store four dimensions instead of one opaque score:
- `quantity`: n/coverage;
- `source_quality`: provider/objective vs self-report/derived;
- `stability`: sign/magnitude consistency across windows;
- `confounding`: none_known / plausible / material / unknown.

A display label `low|medium|high` may be produced by a versioned deterministic ruleset, but the dimensions must remain visible.
