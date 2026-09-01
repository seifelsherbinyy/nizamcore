# NIZAM-HEALTH-INTELLIGENCE v0.2.0 — Research Report & Evidence Register

## Executive findings

- **FACT:** The fresh supplement below contains **57** directly traceable sources, independent of the existing 123-record internal evidence ledger. This satisfies the prompt's 50+ source floor without treating the older ledger as the only evidence base.
- **FACT:** WHOOP's current developer surface is v2/OAuth-oriented. `offline` is required for refresh tokens; refresh responses rotate the refresh token, so refresh must be serialized and persisted atomically [S02]. Collection endpoints paginate through `next_token` [S07] and default rate limits include 100 requests/minute and 10,000/day [S08].
- **FACT:** WHOOP itself models activity around physiological cycles, not ordinary calendar days [S06]. NIZAM therefore needs a separate Cairo-local planning date derived from timestamps, while preserving WHOOP cycle identity.
- **FACT:** Consumer sleep wearables, including WHOOP, are useful field measures but differ from polysomnography and should not be treated as clinical ground truth [S23–S25].
- **FACT:** HRV is influenced by recording method, respiration, posture, exercise, lifestyle, environment and other factors; current guidelines explicitly caution against simplistic autonomic or mental-state interpretations [S26–S28].
- **FACT:** Intensive longitudinal stress studies show mixed relationships between subjective stress, physiological stress and behavior; disagreement between modalities is expected, not an error [S38–S40].
- **FACT:** JITAI literature supports state/context-sensitive interventions but the evidence is heterogeneous; simple rules, explicit decision points and user input are defensible MVP choices [S31–S33].
- **FACT:** N-of-1 observational time series require trend/autocorrelation handling and cannot convert correlation into causation by themselves [S48–S49].
- **FACT:** Change-point/anomaly methods can flag unusual transitions but cannot identify their cause [S50–S52].
- **INFERENCE:** The safest and most useful NIZAM design is therefore deterministic normalization + robust within-person summaries + explicit confounder/context records, with the LLM restricted to synthesis, hypothesis wording and achievable agenda construction.

## Sleep-shift design note

- **FACT:** AASM/NIOSH practical guidance for one-hour time changes uses small 15–20 minute shifts [S20,S54]; a controlled small study found repeated 30-minute phase advances less disruptive than repeated 2-hour advances in a special simulated context [S21].
- **INFERENCE:** NIZAM may use 15–30 minutes as a **conservative behavioral adjustment heuristic**, not as a medical circadian treatment protocol. It should be changed or withheld when adherence, sleep opportunity, work constraints or user preference argue against it.

## Research coverage matrix

| Required topic | Coverage | Primary sources |
|---|---|---|
| WHOOP API / fields / OAuth / sync | Strong | S01–S10 |
| Hermes scheduler | Strong for features; timezone unresolved | S11–S13 |
| Calendar sync/idempotency/reminders | Strong | S14–S17 |
| Sleep timing/regularity/gradual changes | Strong but heterogeneous | S18–S25,S54–S56 |
| HRV/RHR/personal baselines | Strong | S26–S30,S57 |
| Exercise readiness/fatigue | Moderate; avoid universal thresholds | S29–S30 + existing internal ledger |
| Behavior change / JITAI / implementation intentions | Strong | S31–S37 |
| EMA / stress / contextual triggers | Strong | S38–S40 |
| Digital phenotyping & multimodal systems | Strong for methods/limitations | S41–S47 |
| N-of-1 / time series / anomaly/change-point | Strong method support | S48–S52 |
| Wearable diagnostic limitations | Strong safeguard | S23–S25,S53 |

## Internal NIZAM evidence reused

| ID | Type | Artifact | Link | Relevance |
|---|---|---|---|---|
| I01 | NIZAM health prompt | Attached build brief | source: user attachment | Governing requested outcomes and deliverables |
| I02 | NIZAM repo | BADAN Health Advisory Notes | https://github.com/seifelsherbinyy/nizamcore/blob/main/NIZAM__system/docs/BADAN_HEALTH_ADVISORY_NOTES.md | Current BADAN non-diagnostic/trend/privacy doctrine |
| I03 | NIZAM repo | body_signal.schema.json | https://github.com/seifelsherbinyy/nizamcore/blob/main/NIZAM__system/schemas/body_signal.schema.json | Current mixed snapshot schema to preserve/extend rather than silently rewrite |
| I04 | Drive | 100+ Source Evidence Ledger — WHOOP & Human-Performance Training | drive-doc (id withheld from git; resolve via Drive `47_NIZAM/SYSTEM/SOURCE_REGISTRY.json` and `RESEARCH/INDEX.json`, or VPS `sync/drive_layout.py`) | Existing evidence base; 123 traceable records documented on 2026-08-24 |
| I05 | Drive | WHOOP/Human-Performance Master Research Report | drive-doc (id withheld from git; resolve via Drive `47_NIZAM/SYSTEM/SOURCE_REGISTRY.json` and `RESEARCH/INDEX.json`, or VPS `sync/drive_layout.py`) | Existing synthesis to reuse rather than duplicate |
| I06 | Drive | Workout Ledger — Exercise Intelligence | drive-sheet (id withheld from git; resolve via Drive `47_NIZAM/SYSTEM/SOURCE_REGISTRY.json` and `RESEARCH/INDEX.json`, or VPS `sync/drive_layout.py`) | Existing workout source; current sheet timezone metadata requires normalization layer |
| I07 | Drive | NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.3_FINAL_DRIVE_SAFE | drive-doc (id withheld from git; resolve via Drive `47_NIZAM/SYSTEM/SOURCE_REGISTRY.json` and `RESEARCH/INDEX.json`, or VPS `sync/drive_layout.py`) | Current Drive-safe governance contract |

> **Redaction note.** Drive document and spreadsheet ids are deployment particulars and are
> not tracked in git. The four Drive rows above cite the artifact by title only. Resolved ids
> live in Drive `47_NIZAM/SYSTEM/SOURCE_REGISTRY.json`, the relevant domain `INDEX.json`, and
> the VPS-only module `sync/drive_layout.py`. An un-redacted copy is retained on the VPS
> outside the repository.

## Fresh bibliography supplement

| ID | Source type | Title | URL | Relevance |
|---|---|---|---|---|
| S01 | WHOOP official | WHOOP API Docs | https://developer.whoop.com/api/ | API scopes, v2 resource surface |
| S02 | WHOOP official | OAuth 2.0 | https://developer.whoop.com/docs/developing/oauth/ | Authorization, offline scope, rotating refresh tokens |
| S03 | WHOOP official | Recovery | https://developer.whoop.com/docs/developing/user-data/recovery/ | Recovery object, HRV/RHR/SpO2/skin temperature fields |
| S04 | WHOOP official | Sleep | https://developer.whoop.com/docs/developing/user-data/sleep/ | Sleep IDs, score state, timestamps, naps, timezone offset |
| S05 | WHOOP official | Workout | https://developer.whoop.com/docs/developing/user-data/workout/ | Workout IDs, timestamps, strain and activity data |
| S06 | WHOOP official | Cycle | https://developer.whoop.com/docs/developing/user-data/cycle/ | Physiological cycle model; not identical to calendar day |
| S07 | WHOOP official | Pagination | https://developer.whoop.com/docs/developing/pagination/ | Collection next_token pagination |
| S08 | WHOOP official | API Rate Limiting | https://developer.whoop.com/docs/developing/rate-limiting/ | 100/min and 10,000/day defaults; 429 handling |
| S09 | WHOOP official | Webhooks | https://developer.whoop.com/docs/developing/webhooks/ | v2 update/delete webhook semantics |
| S10 | WHOOP official | v1 to v2 Migration Guide | https://developer.whoop.com/docs/developing/v1-v2-migration/ | ID/type/timezone migration details |
| S11 | Hermes official | Scheduled Tasks (Cron) | https://hermes-agent.nousresearch.com/docs/user-guide/features/cron/ | Recurring jobs, workdir, skill injection, execution records |
| S12 | Hermes official | CLI Commands Reference | https://hermes-agent.nousresearch.com/docs/reference/cli-commands/ | hermes cron lifecycle commands |
| S13 | Hermes official | Cron Internals | https://hermes-agent.nousresearch.com/docs/developer-guide/cron-internals | 5-field cron, scheduler internals, atomic storage |
| S14 | Google official | Calendar Extended Properties | https://developers.google.com/workspace/calendar/api/guides/extended-properties | Private app metadata for idempotency |
| S15 | Google official | Calendar Incremental Sync | https://developers.google.com/workspace/calendar/api/guides/sync | nextSyncToken incremental synchronization |
| S16 | Google official | Calendar Create Events | https://developers.google.com/workspace/calendar/api/guides/create-events | Event timezone and reminder overrides |
| S17 | Google official | Calendar Push Notifications | https://developers.google.com/workspace/calendar/api/guides/push | HTTPS callback channels and delivery caveats |
| S18 | PubMed systematic review | Sleep regularity as an important component of sleep hygiene: a systematic review | https://pubmed.ncbi.nlm.nih.gov/41259946/ | Sleep regularity outcomes; heterogeneous metrics |
| S19 | PubMed systematic review | Sleep timing, sleep consistency, and health in adults: a systematic review | https://pubmed.ncbi.nlm.nih.gov/33054339/ | Later/variable sleep timing associated with adverse outcomes |
| S20 | AASM | Daylight Saving Time Advice | https://aasm.org/daylight-saving-time-advice/ | Practical 15–20 minute gradual adjustment advice for time changes |
| S21 | PubMed study | Using daily 30-min phase advances to achieve a 6-hour advance | https://pubmed.ncbi.nlm.nih.gov/16856351/ | Controlled gradual phase-advance example; special context |
| S22 | PubMed systematic review/meta-analysis | Behavioral interventions to extend sleep duration | https://pubmed.ncbi.nlm.nih.gov/34507028/ | Behavioral sleep-extension evidence with high heterogeneity |
| S23 | PubMed meta-analysis | Performance of consumer wrist-worn sleep tracking devices compared to polysomnography | https://pubmed.ncbi.nlm.nih.gov/39484805/ | Consumer sleep trackers show measurement error vs PSG |
| S24 | PubMed systematic review | Accuracy of Fitbit Charge 4, Garmin Vivosmart 4, and WHOOP Versus Polysomnography | https://pubmed.ncbi.nlm.nih.gov/38557808/ | Wearable sleep validity including WHOOP |
| S25 | PubMed validation study | A validation study of the WHOOP strap against polysomnography to assess sleep | https://pubmed.ncbi.nlm.nih.gov/32713257/ | WHOOP sleep staging validation and limitations |
| S26 | PubMed guideline | Publication guidelines for human heart rate and heart rate variability studies in psychophysiology—Part 1 | https://pubmed.ncbi.nlm.nih.gov/38873876/ | HR/HRV measurement and interpretation rigor |
| S27 | PubMed review | Heart rate variability measurement and influencing factors: Towards standardization | https://pubmed.ncbi.nlm.nih.gov/39351472/ | Physiological, lifestyle, environmental and methodological confounders |
| S28 | PubMed guideline | Guidelines for rigor and reproducibility of heart rate variability within human cardiovascular research | https://pubmed.ncbi.nlm.nih.gov/42495990/ | 2026 HRV interpretation cautions; wearable context |
| S29 | PubMed cohort study | Inter- and intraindividual variability in daily resting heart rate | https://pubmed.ncbi.nlm.nih.gov/32023264/ | Large longitudinal cohort supporting individual baselines |
| S30 | PubMed systematic review/meta-analysis | Monitoring Athletic Training Status Through Autonomic Heart Rate Regulation | https://pubmed.ncbi.nlm.nih.gov/26888648/ | Training adaptation and autonomic markers; athlete-specific evidence |
| S31 | PubMed systematic review | Just-in-Time Adaptive Interventions for Behavior Change in Physiological Health Outcomes | https://pubmed.ncbi.nlm.nih.gov/39331951/ | 45 JITAI studies; simple rules and tailoring variables |
| S32 | PubMed systematic review | Just-in-Time Adaptive Interventions for Adolescent and Young Adult Substance Use | https://pubmed.ncbi.nlm.nih.gov/41065631/ | JITAI feasibility and timing patterns; population-specific |
| S33 | PubMed scoping review | Just-In-Time Adaptive Interventions for Weight Management Among Adults | https://pubmed.ncbi.nlm.nih.gov/41447266/ | Prompt/feedback/coping strategy patterns in adult JITAIs |
| S34 | PubMed meta-analysis | A systematic review and meta-analysis on the effectiveness of if-then plans | https://pubmed.ncbi.nlm.nih.gov/41987207/ | Recent implementation-intention evidence in dietary behavior |
| S35 | PubMed meta-analysis | Does forming implementation intentions help people with mental health problems to achieve goals? | https://pubmed.ncbi.nlm.nih.gov/25965276/ | If-then planning and goal attainment; clinical/analogue samples |
| S36 | PubMed systematic review/meta-analysis | Making Specific Plan Improves Physical Activity and Healthy Eating | https://pubmed.ncbi.nlm.nih.gov/35664117/ | Action/implementation planning in chronic conditions |
| S37 | PubMed review | Implementation intention and action planning interventions in health contexts | https://pubmed.ncbi.nlm.nih.gov/24591064/ | Planning intervention design and heterogeneity |
| S38 | PubMed systematic review | Physiological reactions to acute stressors and subjective stress during daily life: EMA review | https://pubmed.ncbi.nlm.nih.gov/35895674/ | Daily-life stress physiology; confounding and inconsistent associations |
| S39 | PubMed systematic review | Ecological Momentary Assessment: A Systematic Review of Validity Research | https://pubmed.ncbi.nlm.nih.gov/35719870/ | EMA validity and measurement considerations |
| S40 | PubMed systematic review | Assessment of stress and its relationship with health behaviour in daily life | https://pubmed.ncbi.nlm.nih.gov/40844372/ | 100 intensive-longitudinal studies; mixed stress-behavior relations |
| S41 | PubMed systematic review | Digital phenotyping for mental health conditions: implementation and application | https://pubmed.ncbi.nlm.nih.gov/42495051/ | 2026 methodological heterogeneity and implementation limits |
| S42 | PubMed systematic review | Digital phenotyping for mental health based on data analytics | https://pubmed.ncbi.nlm.nih.gov/40058310/ | 2025 data analytics review; reliance on self-report and methodological variation |
| S43 | PubMed systematic review | Key Features of Digital Phenotyping for Monitoring Mental Disorders | https://pubmed.ncbi.nlm.nih.gov/41191793/ | Wearable/smartphone feature heterogeneity and reproducibility limits |
| S44 | PubMed systematic review | Digital Phenotyping for Stress, Anxiety, and Mild Depression | https://pubmed.ncbi.nlm.nih.gov/38780995/ | Context-dependent associations; nonclinical passive sensing |
| S45 | PubMed systematic review | Sensing Apps and Public Data Sets for Digital Phenotyping of Mental Health | https://pubmed.ncbi.nlm.nih.gov/35175202/ | Sensing architecture and limited high-quality feature evidence |
| S46 | PubMed scoping review | Digital Phenotyping in Health Using Machine Learning Approaches | https://pubmed.ncbi.nlm.nih.gov/38935947/ | Privacy, prospective-design and standardization gaps |
| S47 | PubMed systematic review | Digital Phenotyping of Mental Health using multimodal sensing | https://pubmed.ncbi.nlm.nih.gov/36586498/ | Multimodal sensing architecture and methodological open issues |
| S48 | PubMed methods paper | Dynamic modelling of n-of-1 data | https://pubmed.ncbi.nlm.nih.gov/28629262/ | N-of-1 time trend/autocorrelation and dynamic regression |
| S49 | PubMed methods paper | Causal Analysis of Self-tracked Time Series Data Using a Counterfactual Framework | https://pubmed.ncbi.nlm.nih.gov/29621835/ | Separates observational hypothesis generation from causal N-of-1 testing |
| S50 | PubMed survey | A Survey of Methods for Time Series Change Point Detection | https://pubmed.ncbi.nlm.nih.gov/28603327/ | Change-point methods and limitations |
| S51 | PubMed review | Anomaly Detection Framework for Wearables Data | https://pubmed.ncbi.nlm.nih.gov/35161502/ | Wearable anomaly-data challenges and method classes |
| S52 | PubMed systematic review | Spectral anomaly detection in physiological time-series data | https://pubmed.ncbi.nlm.nih.gov/41411902/ | 2026 anomaly-detection evidence; clinical signal context |
| S53 | PubMed systematic review/meta-analysis | Real-World Accuracy of Wearable Activity Trackers for Detecting Medical Conditions | https://pubmed.ncbi.nlm.nih.gov/39213525/ | Diagnostic-use limitations; supports non-diagnostic boundary |
| S54 | CDC/NIOSH | Daylight Saving: Suggestions to help workers adapt to the time change | https://www.cdc.gov/niosh/bulletin/2016/daylight-savings.html | Practical gradual 15–20 minute schedule adjustment |
| S55 | Johns Hopkins Medicine | How to Sleep Well Despite Changes in Your Schedule | https://www.hopkinsmedicine.org/health/wellness-and-prevention/how-to-sleep-well-despite-changes-in-your-schedule | Practical 15-minute schedule-shift guidance |
| S56 | Sleep Foundation | How to Fix Your Sleep Schedule | https://www.sleepfoundation.org/sleep-hygiene/how-to-reset-your-sleep-routine | Practical 15–30 minute incremental schedule adjustment |
| S57 | PubMed cohort/model validation | Detection of Common Respiratory Infections Using Consumer Wearable Devices | https://pubmed.ncbi.nlm.nih.gov/39018555/ | Longitudinal physiological baseline deviations; not diagnostic for NIZAM |

## Evidence-use rules

1. **FACT:** Raw provider values remain provider facts with source IDs/timestamps.
2. **INFERENCE:** Derived associations are NIZAM calculations; they never overwrite provider fields.
3. **ASSUMPTION:** Versioned engineering thresholds are not clinical cutoffs and must be configurable/tested.
4. **MISSING:** If data coverage, timezone, confounder, or calendar coverage is insufficient, output `insufficient_data` rather than a narrative guess.
5. **FACT:** No wearable or journal pattern is permitted to become a diagnosis or medication/treatment recommendation.
