# NIZAM Daily Governor — Architecture Research & Plan

**Status:** research + plan only. No code, contract, schema, or policy file has been created or modified by
this report. No command, test, credential, retrieval call, calendar mutation, or repository write described
below has been executed. Nothing in this document should be read as "verified", "approved", or "gate
complete" — those words are reserved for observed evidence, and none was produced here.

**Workspace identity (checked, not assumed):** `git remote -v` in this workspace resolves to
`seifelsherbinyy/nizamfinancialapp`. The five contracts and the two build directives repeatedly point at a
**different** repository — `D:/NIZAM/nizamcore`, module `NIZAM__system` — as their target. That distinction
drives most of Section 2.

**Sources read for this report:**
- `five_contracts/01...05_*.md` in the owner-supplied dropzone path (five numbered contracts, `status:
  proposed_for_implementation`)
- `_DROPZONE/01_NIZAM_Cross_Domain_Adaptive_Intelligence_Contract.md` (`status: execution_contract`)
- `_DROPZONE/02_Hermes_Noon_Governor_Build_Directive.md` (`status: executable_build_directive`)
- `_DROPZONE/03_NIZAM_Verification_Rollout_and_Learning_Playbook.md` (`status: execution_playbook`) — **not
  one of the two directives named in the task**, but it is the only file in the dropzone that defines the
  `S01-S05`, `E01-E04`, and `SL01-SL07` playbook IDs the task asks about, so it had to be read to answer
  Section 1 and Section 3 honestly. Flagged here rather than silently used.
- `.kiro/steering/two-agent-vps.md` (all sections, section 6/6a in full)
- the `money-rules` steering file, `.kiro/steering/drive-db.md`
- `AGENTS` (workspace root)
- `ops/DEPLOYMENT_CONTROL.md` Summary table and the G1/G5 entries, read-only, for gate status citation only —
  no gate step was executed, tested, or marked complete, per the AGENTS file's own restriction on that file.

One citation in `two-agent-vps.md` section 6a could not be independently confirmed: the file it names,
`OWNER_AUTHORITY_VPS_LIVE prompt file`, under a `.kiro/specs/06-two-agent-vps/` folder, does not exist anywhere
in this working tree (`.kiro/specs/` contains only `unified-personal-operating-intelligence`). The authority
may have existed in a prior commit or a different checkout; this report does not assume it is currently
present, and does not treat section 6a as unsupported on that basis — section 6a is quoted directly from the
steering file that IS present, which is what governs this session regardless of whether its own internal
citation resolves.

---

## 1. DEPENDENCY CHAIN

### 1.1 Contract order and what each unlocks (as declared in each contract's own `depends_on` / `unlocks`)

| Contract | Depends on | Unlocks | Purpose (one line, contract's own wording) |
|---|---|---|---|
| **01 Constitution & Governance** | none | 02 | "Define the non-negotiable operating constitution... before any domain-specific intelligence is allowed to run." |
| **02 Knowledge Acquisition & Retrieval** | 01 | 03 | "Make the latest 47_NIZAM Drive knowledge plane, VPS operational truth, and GitHub logic retrievable in a deterministic, incremental, provenance-aware order." |
| **03 Cross-Domain Intelligence & Learning** | 01, 02 | 04 | "Convert verified cross-domain observations into longitudinal features, hypotheses, counterevidence, interventions, and promoted learnings." |
| **04 Daily Autonomous Orchestration & Actuation** | 01, 02, 03 | 05 | "Define the production daily governor that refreshes evidence, applies the NIZAM tenets, dispatches domain checks, synthesizes a bounded plan, autonomously executes authorized actions, verifies them, and records learning." |
| **05 Verification, Promotion & Self-Evolution** | 01, 02, 03, 04 | none | "Ensure NIZAM becomes smarter through verified outcomes... while preventing self-modification from weakening constitutional, evidentiary, privacy, financial-authority, or human-truth boundaries." |

Each `handoff completion_condition` is a real gate, not decoration: Contract 02 cannot "start" (per Contract
01's own text) until Contract 01's tenets are machine-addressable by ID and its acceptance tests are
deterministically evaluable; Contract 05's `release_gate` cannot pass until Contracts 01-04's schemas
validate and a chain of shadow/read-only/tamper runs all pass (`release_gate.required_before_production`).
None of that chain has been executed in this repository. There is no evidence in this workspace that it has
been executed anywhere.

### 1.2 What "satisfiable by a pure deterministic function, zero credentials, zero network" means here

Every acceptance test in Contracts 01-05, and every test in the playbook's `test_matrix`, is written as a
`given: <synthetic scenario> / expect: <deterministic outcome>` fixture. That phrasing is not incidental —
Contract 05's `progressive_activation.P0_FIXTURES` phase is explicitly `autonomy: none`, and its requirement
is exactly "all contract and synthetic fixtures pass." The playbook's own `release_stages.R1_FIXTURES` is
`mode: synthetic_only`. So the acceptance-test text itself, read literally, describes a decision function
over already-supplied inputs — never a live retrieval, a live calendar write, or a live model call. That is
the distinction this section holds to: the decision/classification logic is pure; the actuation the decision
would authorize (fetching from Drive, writing to Calendar, pushing to GitHub, calling an LLM, calling a
weather/news API) is not, and is scored separately in Sections 3 and 4.

### 1.3 Per-contract acceptance IDs, evaluated against that standard

**Contract 01 (Constitution)** — all six are pure. Each is a threshold/branch function over
`(sukoon_state, recovery_percent, hard_safety_flag)` or a policy-conflict resolver over two declared rules:
- `C01-T01` (yellow/35 -> bounded NAQD/SHURA) — pure.
- `C01-T02` (red/39 -> heavy planning + NAQD blocked) — pure.
- `C01-T03` (red/55, no hard safety -> cognitive actions allowed, evidence recorded) — pure.
- `C01-T04` (metric absent -> stays MISSING) — pure validation, no imputation.
- `C01-T05` (calendar optimization useful+compliant -> class-B decision made, human-only field untouched) —
  the classification ("this action is class B and does not touch the approval field") is pure; the actual
  Calendar write it would authorize is not (Section 4).
- `C01-T06` (GitHub change inside blast radius but an older policy forbids push -> stricter rule wins,
  conflict emitted) — pure conflict-resolution function.

**Contract 02 (Retrieval)** — all five are pure, because each operates over a supplied BOOTSTRAP/index
fixture, not a live Drive call: `C02-T01` (diff two index snapshots), `C02-T02` (refuse to resolve duplicate
display names), `C02-T03` (hash-unchanged despite mtime-changed -> no semantic change), `C02-T04` (narrative
figure vs. deterministic engine value -> engine wins, narrative marked stale), `C02-T05` (domain absent from
BOOTSTRAP -> UNINDEXED, not empty). The live "read the BOOTSTRAP manifest from 47_NIZAM" step these fixtures stand in
for is a Drive read and is not pure (Section 4).

**Contract 03 (Learning)** — all five are pure state-machine transitions over a supplied ledger fixture:
`C03-T01` (three similar observations -> hypothesis, not FACT), `C03-T02` (hypothesis with only supporting
evidence -> counterevidence search required before promotion), `C03-T03` (calendar says scheduled, no
completion evidence -> completion stays unknown), `C03-T04` (LLM-recalled figure vs. engine value -> engine
wins, LLM value discarded), `C03-T05` (weekly evidence contradicts a promoted learning -> superseded, history
preserved).

**Contract 04 (Daily Orchestration)** — all seven are pure given injected mock ports, per the directive's own
engineering rule ("pure functions and injected ports where practical"): `C04-T01` (verified run at 12:00 ->
13:00 reconciliation no-ops), `C04-T02` (yellow -> bounded targets), `C04-T03` (red/42, no hard safety ->
cognitive stages run, state recorded), `C04-T04` (event generated twice -> idempotency key collision
detected, no duplicate) — this is precisely the "calendar idempotency-key derivation with no API calls"
candidate in Section 3, `C04-T05` (mock write returns success, mock readback returns mismatch -> receipt is
FAILED/SYNC_PENDING, never OK), `C04-T06` (unrelated file in a fixture changeset -> blast-radius gate fails),
`C04-T07` (no source pointer on a fixture claim -> action cannot be justified).

**Contract 05 (Verification/Promotion)** — all six are pure meta-tests over fixtures: `C05-T01` (a fixture
skill change that improves output but weakens HIMAYAH -> promotion blocked), `C05-T02` (three comparable
failed interventions -> confidence drops, alt strategy required), `C05-T03` (stronger later evidence -> old
learning superseded, not deleted), `C05-T04` (validator passes both the clean and the deliberately-broken
fixture -> this is the tamper test itself; release blocked because the validator's own proof failed),
`C05-T05` (mock commit succeeds, mock readback absent -> status UNPROVEN), `C05-T06` (fixture duplicate
calendar event on retry -> incident raised, Class B promotion blocked until fixed).

**Playbook `test_matrix` (03_NIZAM_Verification_Rollout_and_Learning_Playbook.md):**
- `S01-S05` (SUKOON) — pure threshold/override functions over `(state, recovery, crisis_flag)`, with one
  caveat: `S05`'s input is "crisis/safety language; recovery 80". The override branch ("if crisis flag is
  true, stop regardless of recovery") is pure. Detecting a crisis from unstructured free text is not a pure
  deterministic function — it is model/human judgment. This report treats only the override-given-a-flag
  logic as buildable-pure; see Section 5 for why the detection side must not be built as if it were.
- `E01-E04` (Evidence) — pure: missing-stays-missing, both-sides-preserved-on-conflict, freshness-flag-on-
  stale-data, single-observation-stays-non-causal are all functions over already-labeled inputs.
- `SL01-SL07` (Sleep) — pure: each is a branch of the controller state machine over already-computed inputs
  (prior target, adherence measure, recovery delta, travel flag, consecutive-adherence count). Detailed in
  Section 3.

**Also present in the same `test_matrix` but not asked about, noted for completeness and to flag a naming
collision:** the playbook's own `calendar` sub-block reuses the bare IDs `C01-C05` for calendar-specific cases
(retry/no-duplicate, weather-triggered reschedule, conflict-before-write, human-only-field-untouched,
13:00-no-new-agenda), which collide in string form with Contract 01's `C01-T01...T06` IDs even though the
formats differ (`C01` vs `C01-T01`). Contract 01's `T08_NEVER_FABRICATE_STATE` tenet and the evidence-label
discipline both argue against ambiguous identifiers surviving into a release record; this collision is worth
fixing before any of these IDs appear in a real `run_receipt`, but this report is not the place to rename
them unilaterally.

### 1.4 A spec-vs-spec discrepancy surfaced while building this table (not resolved here)

Contract 01 (five_contracts) and Contract 04 define the SUKOON `full` mode as `state == green` only, and name
**40%** as the sole recovery threshold, and only as an override that unlocks bounded action under
yellow/red — never as an independent trigger for `full`. The dropzone's Cross-Domain Adaptive Intelligence
contract (`sukoon_policy.full_mode.when_any`) adds a second, independent trigger: `objective_recovery >= 67`
grants `full` mode even under yellow or red. This is a material behavioral difference (it would allow
full-strength NAQD/optimization under a red SUKOON state purely on a 67%+ recovery reading), and no
acceptance test in either source isolates it — `S01`'s "green; recovery 70" input is consistent with either
rule. This is flagged as an unresolved spec-vs-spec conflict, not adjudicated by this report.

---
## 2. GOVERNANCE CONFLICT REGISTER

`two-agent-vps.md` section 6a grants nizamcore write authority for exactly four enumerated
purposes: (1) model-layer wiring changes, (2) env-file template entries (never live secret
values), (3) relay standby-to-active release steps, and (4) the `ledger_writer.py`
idempotency/concurrency fix. Section 6a states explicitly that this is not a licence to
restructure that repository, and section 6 (parent) frames all of this as scoped, narrow,
audited write access layered on top of an otherwise read-only relationship to nizamcore. Every
row below is a place where a supplied spec (the five contracts, the dropzone Cross-Domain
contract, or the Hermes/Noon Governor Build Directive) assumes an authority that section 6a does
not enumerate. This register does not resolve the conflicts; per the workspace's own precedence
rule (steering and contracts outrank supporting docs, and stricter/narrower rules win over
broader ones when they conflict), the narrower `two-agent-vps.md` grant controls and the
spec-assumed authority stays blocked until the owner extends section 6a in writing.

Additional scope note: even where the four purposes nominally overlap a spec's language (for
example the ledger_writer.py fix touching money-adjacent code), the contracts describe
functionality — a 21-stage-class daily governor, learning promotion, cross-domain intelligence —
that is not any of the four purposes and not a narrow extension of them. Building that
functionality inside `NIZAM__system` (the contracts' stated home, itself outside this workspace's
own repository) is a restructuring act by the plain meaning of section 6a's own prohibition,
independent of any single write's size.

| Spec clause | Governing clause | Stricter rule that wins | What stays BLOCKED |
|---|---|---|---|
| Contract 04 ("Daily Autonomous Orchestration and Actuation Contract") describes the governor committing generated artifacts (daily plans, learning logs, promoted-learning records) directly into the nizamcore/NIZAM__system tree as part of its normal daily run, with no owner review step named before the commit. The Hermes/Noon Governor Build Directive likewise describes the governor as a standing service that writes its own outputs back into the repository it runs from. | `two-agent-vps.md` section 6a: the four enumerated purposes are model-layer wiring, env-file template entries, relay standby release, and the ledger_writer.py fix. None of the four is "commit generated daily-governor artifacts." Section 6a also states this is not a licence to restructure the repository. | Section 6a's enumerated-purposes list is narrower and more specific than the contract's general "the governor writes its outputs" design, and the AGENTS file's human-gate rule ("never commit... without explicit owner authorization") layers on top. The narrower, more specific, human-gated rule controls. | Autonomous `git commit` / `git push` of any governor-generated artifact into nizamcore/NIZAM__system, on any cadence, for any content type not itself one of the four purposes, stays blocked. Any writer role in the eventual design must emit unapplied patches or files outside nizamcore for owner review, not commit directly. |
| Contract 04's sleep trajectory controller and the Hermes/Noon directive both describe the
governor autonomously creating, updating, moving, and deleting calendar events (sleep-shift
blocks, recovery windows, rescheduled commitments) as part of its daily actuation loop, gated
only by internal confidence/evidence thresholds, not by a human approval step per mutation. | `two-agent-vps.md` section 6a's four purposes contain no calendar-write grant at all — calendar mutation is not model-layer wiring, not an env template entry, not the relay release, and not the ledger_writer.py fix. Cross-checked against `ops/DEPLOYMENT_CONTROL.md`: its G1-G8 gate list contains no Calendar OAuth/consent gate; G5 is a Drive storage-consent grant for the backup path only. This is read as an absence of a granted path for Calendar autonomy, not as silent permission — the AGENTS file's human-gate rule requires explicit owner authorization for anything not already gated, and no gate exists for Calendar. | The absence of any Calendar-scoped clause in section 6a, combined with the AGENTS file's default-deny framing for OAuth/consent/mutation actions, is stricter than the contracts' assumption that calendar autonomy is simply part of the governor's normal operating envelope. | Autonomous calendar event create/update/move/delete stays blocked entirely, regardless of confidence score, evidence label, or SUKOON state. Any calendar action first requires an owner-authorized human gate that does not yet exist in `ops/DEPLOYMENT_CONTROL.md`, and until the owner defines and completes that gate, calendar-touching logic can be designed and unit-tested against a mock calendar port only. |
| The five contracts collectively describe, and the Hermes/Noon Governor Build Directive names outright, a new standing daily-governor pipeline (ingestion through orchestration through verification through promotion) to be stood up inside nizamcore's `NIZAM__system` module, including new directories, new scheduled entry points, and new persistent state stores. | `two-agent-vps.md` section 6a again: none of the four purposes is "stand up a new pipeline/module." The section's closing sentence is explicit that the grant "is not a licence to restructure" nizamcore. Standing up a new top-level system inside `NIZAM__system` is restructuring by any plain reading, not a wiring change, template entry, relay step, or the named ledger fix. | The explicit anti-restructuring sentence in section 6a is a direct, named override of the broader architectural intent in the contracts. Explicit narrower prohibitions win over broad implicit designs per this workspace's stated precedence rule. | Creating any new files, directories, scheduled jobs, or persistent stores inside nizamcore/`NIZAM__system` stays blocked from this workspace. The only currently-open path for governor-pipeline code is to build and test it as pure, credential-free modules living in this workspace (or another owner-designated location) and to hand nizamcore integration to the owner as reviewable, unapplied patches — mirroring the existing `ops/nizamcore-patches/` pattern this workspace already uses for the four permitted purposes. |
| Contract 03 ("Cross-Domain Intelligence and Learning Contract") and the dropzone Cross-Domain Adaptive Intelligence contract both describe a `governance_reconciliation` / cross-domain synthesis stage that calls out to a production LLM endpoint and/or external data sources (weather, event feeds) as a normal, scheduled part of the daily run, with network egress treated as a given capability of the deployed governor. | the AGENTS file and `two-agent-vps.md` (parent section 6, read together with the human-gates rule) require explicit owner authorization before any live network call, production key spend, or credential mint/rotation; `ops/DEPLOYMENT_CONTROL.md` gates most of these paths (e.g. relevant G1-G8 entries) as human-only, never to be executed, substituted into, or marked complete by an agent. | The human-gate rule is unconditional and does not carve out an exception for a stage merely because a contract names it as routine; the stricter, owner-only rule controls over the contract's operational assumption. | Any network call to an LLM endpoint, weather API, or external event feed, and any use of a production credential for such a call, stays blocked this session and every session until the owner explicitly authorizes and the relevant `ops/DEPLOYMENT_CONTROL.md` gate is completed by the owner. Deterministic modules that would consume such data must be designed to accept it via an injected port/mock, never to fetch it themselves. |

Two further points belong in this register even though they did not fit the table's row
structure. First, the dropzone directives use "Slack" as the notification/actuation channel
throughout, while `two-agent-vps.md` describes the existing bot/notification infrastructure in
terms of Telegram; this report treats that as an unresolved channel-selection conflict between
supplied specs, not something section 6a or any other governing clause resolves, and does not
recommend either channel without an owner decision. Second, section 6a's text (as read in this
workspace's copy of `two-agent-vps.md`) references an `OWNER_AUTHORITY_VPS_LIVE prompt file`
companion file; this report could not locate that file under `.kiro/specs/` in this workspace
(only `.kiro/specs/unified-personal-operating-intelligence/` was found) and does not treat that
absence as invalidating section 6a's text, only as an uncorroborated citation worth the owner's
attention.

---
## 3. BUILDABLE-TODAY SLICE

The candidates below are evaluated against the same test: zero credentials, zero network calls,
zero mutation of any external system (calendar, Drive, nizamcore, filesystem outside this
workspace), pure functions of explicit inputs to explicit outputs. All seven candidates the task
named pass that test at the design level; none of them has been implemented or tested in this
session, so "satisfies acceptance ID X" below means the module's contractually-defined behavior,
if implemented exactly as specified and tested against the cited acceptance criteria, would
satisfy it — not that any test has been run.

### 3.1 SUKOON capacity gate

- **Inputs:** a SUKOON reading (a numeric capacity/recovery-style value per Contract 01/04's
  definition) and, per the unresolved 40-vs-67 conflict noted in section 1.4, either one or two
  threshold parameters depending on which source's rule the owner selects (five_contracts: a
  single 40% recovery override threshold layered on a green/yellow/red band; dropzone Cross-Domain
  contract: an additional independent 67% recovery trigger for `full_mode`). A crisis flag
  (boolean or enum) that hard-overrides the computed state regardless of the numeric reading.
- **Outputs:** one of the enumerated SUKOON states (green/yellow/red, each possibly modified by a
  recovery-override sub-state), plus the specific evidence trail (which threshold fired, whether
  the crisis override fired) needed for the evidence-label discipline in 3.6.
- **Invariants:** the crisis hard-override always wins over any computed band or recovery
  threshold; the function is total (every valid input reading maps to exactly one state); the
  function is pure (no clock, no I/O, same input always yields same output); the 40-vs-67
  discrepancy must be implemented as an explicit, owner-selected parameter, not silently resolved
  by this report or by the implementer.
- **Acceptance IDs satisfiable:** Contract 01/04's SUKOON-gate acceptance tests that exercise
  green/yellow/red banding and the 40% override in isolation from any network or credential
  dependency (per section 1.3's analysis, the SUKOON-gate-only tests within `C01-T01..T06` and
  `C04`'s corresponding SUKOON checks); playbook `S01` ("green; recovery 70") as literally stated,
  since a 70% reading is consistent with either the 40%-only rule or the 40-and-67 rule and does
  not itself require resolving the conflict to pass.

### 3.2 Sleep trajectory controller

- **Inputs:** current sleep-time baseline, target sleep-time, a fixed 10-minute default daily
  shift, a fixed 15-minute maximum daily shift, and the current SUKOON state from 3.1.
- **Outputs:** one of the five controller states named in the task (ADVANCE, HOLD, RECOVER,
  RECALIBRATE, TARGET_REACHED) and the specific minute-delta it recommends for the next
  scheduling step (still just a recommendation value — not a calendar mutation, which stays
  blocked per section 2's row 2).
- **Invariants:** the recommended shift never exceeds the 15-minute ceiling; the default path
  uses 10 minutes; RECOVER/RECALIBRATE states are reachable only through SUKOON inputs that the
  gate in 3.1 has already classified, keeping the two modules composable and independently
  testable; TARGET_REACHED is terminal for a given target (no further shift recommended once
  reached); the function is pure and total over its defined input domain.
- **Acceptance IDs satisfiable:** the sleep-controller-specific checks within Contract 04's
  acceptance set and the playbook's `SL01`-`SL07` series to the extent each `SL0x` case, as read
  in the playbook's test_matrix, is expressed purely in terms of baseline/target/SUKOON-state
  inputs and a state/delta output with no calendar-write or network step folded into the same
  test; any `SL0x` case that also asserts a calendar side effect is out of scope for this slice
  and belongs in section 4 instead.
### 3.3 External-event clustering and relevance scoring

- **Inputs:** a pre-fetched, already-in-memory list of event records (title, time window,
  category, source tag) — explicitly not a live fetch, since any live fetch is blocked per
  section 2's row 4. Clustering parameters (time-window proximity, category weights) and a
  relevance-scoring rubric as defined in Contract 02/03.
- **Outputs:** a set of event clusters, each with a computed relevance score and the specific
  evidence label (see 3.6) for how that score was derived (FACT if from an explicit rubric match,
  INFERENCE if derived from a weighted combination, never ASSUMPTION for a scoring output).
- **Invariants:** clustering is deterministic given identical input ordering and parameters (no
  hidden randomness, no wall-clock dependency beyond what is passed in as an explicit "as-of"
  timestamp parameter); the module never performs the fetch itself, only the clustering/scoring
  arithmetic on data handed to it.
- **Acceptance IDs satisfiable:** Contract 02's ingestion/relevance acceptance tests that specify
  input event lists directly rather than requiring a live source, and playbook `E01`-`E04` to the
  extent each case supplies its event data as a fixture rather than asserting a live-fetch
  behavior; any `E0x` case that asserts network retrieval, retry, or rate-limit handling is out of
  scope here and belongs in section 4.

### 3.4 Weather-impact record validation

- **Inputs:** a single already-fetched weather-impact record (temperature, precipitation flag,
  any derived impact tag) matching Contract 02/03's schema for such a record.
- **Outputs:** a validation verdict (schema-valid/invalid, with the specific field-level reason on
  invalid) and, when valid, the record re-emitted unchanged with its evidence label set per 3.6.
- **Invariants:** pure schema/range validation only — no unit conversion policy invented beyond
  what the contract specifies, no live weather-API call, no persistence; unknown or out-of-range
  fields fail closed (marked invalid) rather than being silently coerced.
- **Acceptance IDs satisfiable:** the weather-record-validation acceptance criteria within
  Contract 02/03 that are phrased as "given a record, validate it," as opposed to any criterion
  that also asserts the record was live-fetched from a named provider — the latter half of any
  such combined criterion is out of scope here per section 2's row 4.

### 3.5 Calendar idempotency-key derivation (no API calls)

- **Inputs:** the semantic identity fields of a would-be calendar event (title, canonical start
  time, canonical end time, and any owner-defined event-type tag) as Contract 04 defines the
  idempotency-key derivation rule.
- **Outputs:** a deterministic idempotency key string, computed the same way every time for the
  same semantic identity fields, with no calendar API involved in the derivation itself.
- **Invariants:** pure hashing/formatting function; the key derivation itself never calls the
  Calendar API and never mutates anything — it produces a value that a (currently blocked, per
  section 2 row 2) future calendar-writer module would use to detect duplicates once that writer
  is itself authorized; this module's output has no effect until a human-gated writer exists.
- **Acceptance IDs satisfiable:** Contract 04's idempotency-key-derivation acceptance criteria
  that assert key stability/determinism given fixed inputs, with no live calendar call in the same
  criterion; any criterion that also asserts the key was checked against a live calendar (that is,
  actually detected a duplicate against a real event) is out of scope here.
### 3.6 Evidence-label discipline (FACT/INFERENCE/ASSUMPTION/MISSING)

- **Inputs:** any data value produced by any of the other modules in this section, plus the
  provenance metadata of how that value was produced (direct field read, computed combination,
  default fallback used, or field absent).
- **Outputs:** the same value annotated with exactly one of the four labels the task names —
  FACT (directly read from a validated input field), INFERENCE (computed/derived from one or more
  FACTs via a defined rule), ASSUMPTION (a default or fallback value substituted because the real
  input was missing or invalid), or MISSING (no value could be produced and none was assumed).
- **Invariants:** every output value from every other module in this slice carries exactly one
  label, never zero and never more than one; ASSUMPTION is never silently presented as FACT
  anywhere downstream (this is the discipline's entire purpose per Contract 01/03); MISSING
  propagates rather than being coerced into a default without the ASSUMPTION label attached to
  that default.
- **Acceptance IDs satisfiable:** the evidence-labeling acceptance criteria distributed across
  Contract 01 (constitutional labeling rule) and Contract 03 (labeling as applied to cross-domain
  synthesis outputs), to the extent each criterion is expressed as "given a value and its
  provenance, assign the correct label" — a pure classification function with no network or
  credential dependency of its own; this module also underwrites the evidence-trail requirement
  named in 3.1 for the SUKOON gate's own outputs.

### 3.7 Learning promotion state machine (observation to promoted_learning)

- **Inputs:** a sequence of observation records (already collected, in-memory — not fetched by
  this module) and the promotion-gate parameters Contract 05 defines (minimum observation count,
  minimum consistency/confidence threshold, any required evidence-label floor from 3.6).
- **Outputs:** for each observation or observation-group, one of the promotion states Contract 05
  defines (e.g. observed, candidate, promoted_learning, or rejected, per that contract's exact
  vocabulary) plus the specific reason the state was assigned.
- **Invariants:** promotion is monotonic and rule-driven only — no partial-credit heuristics
  beyond what Contract 05 specifies; an observation carrying an ASSUMPTION-or-weaker evidence
  label per 3.6 cannot reach promoted_learning if Contract 05's evidence floor excludes it; the
  state machine is pure and total over its defined input domain, with no write to any persistent
  learning store (persistence of a promoted_learning record is itself a write this session cannot
  perform per section 2, since Contract 05 locates that store inside nizamcore/NIZAM__system).
- **Acceptance IDs satisfiable:** Contract 05's promotion-state-machine acceptance criteria that
  are expressed purely in terms of an observation sequence and gate parameters in, and a promotion
  state out, with no live persistence step folded into the same criterion; any criterion that also
  asserts the promoted record was durably written to the nizamcore learning store is out of scope
  here and belongs in section 4.

---
## 4. BLOCKED PENDING CREDENTIAL OR OWNER

| Item | Precise blocker |
|---|---|
| Calendar create/update/move/delete (any of the sleep-controller's or governor's calendar-touching behavior) | No Calendar OAuth/consent gate exists in `ops/DEPLOYMENT_CONTROL.md` (G1-G8 checked; G5 is the Drive backup-path storage-consent grant only). Blocked on the owner defining and completing a new Calendar gate, and on `two-agent-vps.md` section 6a being extended (in writing, by the owner) to cover it, since it names no such authority today. |
| Live LLM endpoint calls for `governance_reconciliation` / cross-domain synthesis | Blocked on owner-authorized production key provisioning and the corresponding `ops/DEPLOYMENT_CONTROL.md` gate being completed by the owner; the AGENTS file prohibits any agent from executing, substituting values into, or marking such a gate complete. |
| Live weather-API and live external-event-feed fetches (the fetch step feeding 3.3/3.4, as distinct from the pure clustering/validation logic itself) | Blocked on owner-provisioned API credentials for whichever provider(s) the owner selects; no provider has been named or authorized in this workspace's visible configuration. |
| Slack notification/actuation channel named in the dropzone directives | Blocked on an owner decision resolving the Slack-vs-Telegram channel conflict noted in section 2, and, if Slack is chosen, on owner-provisioned Slack app credentials that do not currently exist in this workspace. |
| Any `git commit` / `git push` of governor-generated artifacts into nizamcore/`NIZAM__system` | Blocked on an owner-authorized extension of `two-agent-vps.md` section 6a beyond its current four enumerated purposes, per section 2 row 1/3, plus the AGENTS file's standing commit/push authorization gate. |
| Persistent write of a `promoted_learning` record into the nizamcore learning store (Contract 05) | Blocked for the same reason as the commit/push row above — the store's location is inside nizamcore, and no section 6a purpose covers writing to it. |
| Relay standby-to-active release itself (distinct from wiring the model layer that talks to it) | Named as a section 6a purpose, but this report found no evidence in this session of the relay's current state, credentials, or readiness; treat the purpose as authorized in principle but its execution as blocked pending the owner confirming current relay state and explicitly invoking this session (or a designated one) to perform it. |
| Any OAuth consent completion (Calendar, Slack, or any other new scope) | the AGENTS file: OAuth consent completion is an explicit human gate; never to be completed by an agent regardless of which contract calls for the resulting scope. |
| Any DNS mutation, host provisioning/mutation, or webhook registration implied by standing up a new governor service | the AGENTS file: each of these is independently named as a human-only gate; the governor-pipeline stand-up in section 2 row 3 would require some combination of these once it reaches deployment, compounding the blocker already established there. |
| Resolution of the SUKOON 40-vs-67 threshold conflict (section 1.4) | Blocked on an owner decision selecting which source's rule (or a merged rule) governs; this report does not adjudicate it. |
| Verification that `OWNER_AUTHORITY_VPS_LIVE prompt file` exists and states what section 6a's text attributes to it | Blocked on the owner locating/confirming that file's location, or confirming section 6a's text should be read as self-contained without it. |

---
## 5. MUST NOT BUILD OR ACTIVATE THIS SESSION

- Any code path that calls `git commit` or `git push` against nizamcore/`NIZAM__system` for
  governor-generated artifacts (daily plans, learning logs, promoted-learning records) — not
  covered by any of section 6a's four purposes.
- Any code path that creates, updates, moves, or deletes a Calendar event, directly or via a
  wrapped client library, even behind a high-confidence/high-evidence gate — no Calendar
  authority exists in section 6a or in `ops/DEPLOYMENT_CONTROL.md`.
- Any new directory, module, scheduled entry point, or persistent store created inside
  nizamcore/`NIZAM__system` for the governor pipeline — section 6a's anti-restructuring sentence
  applies regardless of the change's size or the contract's framing of it as routine.
- Any live network call to an LLM endpoint, weather API, external event feed, or Slack API,
  including calls framed as "read-only" test calls — these are human-gated per the AGENTS file and
  `ops/DEPLOYMENT_CONTROL.md` regardless of read/write direction.
- Any minting, rotation, retrieval, or use of a production credential, API key, or OAuth token
  for any of the above.
- Any OAuth consent flow completion for Calendar, Slack, or any other new scope.
- Any DNS mutation, host provisioning, host mutation, or webhook registration in support of
  standing up a governor service.
- Any resolution, silent or explicit, of the SUKOON 40-vs-67 threshold conflict, the
  Slack-vs-Telegram channel conflict, or the playbook `C01`-`C05` bare-ID collision with
  Contract 01's `C01-T01..T06` — all three are flagged as owner decisions in this report, not
  decided by it.
- Any action taken against, or file modification of, `ops/DEPLOYMENT_CONTROL.md` itself (the
  active human-only control record) — read-only in this and every session absent explicit owner
  authorization for a specific change.
- Any commit of this report itself, or of any other file in this workspace beyond
  `ops/NIZAM_GOVERNOR_ARCHITECTURE_PLAN.md`, without explicit owner authorization — this task's
  own scope is a single new report file, and no other file has been modified to produce it.
- Any claim, anywhere in this report or in future sessions building on it, that a gate is
  complete, a design is owner-approved, a credential is available, or an acceptance test has
  actually been run and passed — none of that has occurred in this session; every acceptance-ID
  reference above is a citation of what a criterion requires, not a report of a result.
