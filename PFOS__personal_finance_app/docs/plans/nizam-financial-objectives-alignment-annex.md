# Annex — Financial Objectives Alignment (O1–O11)

Companion to `docs/plans/nizam-financial-objectives-alignment-plan.md` Revision 1. **Evidence, not
authority** (plan §0.2 level 4). Nothing here authorizes implementation.

All eleven objective documents and all 23 governance-pack files were read in full this session. The
pack was extracted to a temporary directory **outside the repository tree**, so the working-tree
dirty count (D-H) is unchanged by the extraction. **VERIFIED** unless labelled otherwise.

---

## §A The three stacks, and how they relate

| Stack | Location | Size | Self-declared status | Tracked? |
|---|---|---|---|---|
| **The objectives** | `FINANCIAL/01_O1…11_O11.md` | 11 files, 9,364 lines, 494 KB | "PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified", `0.1.0-design`, `review_before_commit` | **NO — `?? FINANCIAL/`, zero files in `git ls-files`** |
| **The governance pack** | `FINANCIAL/Financial_NIZAM_PFOS_Agentic_Governance_Pack_v1.0.0.zip` | 23 files + manifest, ~88 KB | "CANONICAL CANDIDATE — architecture package; implementation remains unverified", `review_before_commit`, "Subordinate to PFOS v1.3 FINAL" | No (inside the untracked dir) |
| **The repository contracts** | `contracts/pfos/01–15`, `contracts/CONTRACT_1..6` | 19 files | 01–04 Drive-ingested with SHA-256 recorded; 05,06,09–15 NIZAM-derived; **07, 08 VERIFIED ABSENT** after three sweeps | **YES** |

**Relationship, in one line:** the objectives and the repository's PFOS stack are two *sibling*
decompositions of the same absent parent (PFOS v1.3 FINAL), and the pack is a third — which is why they
overlap and why the overlap must be adjudicated rather than assumed away.

### A.1 The pack's own authority claims — every one is a claim of subordination

Repeated verbatim in all 21 pack content files:

> **Status:** CANONICAL CANDIDATE --- architecture package; implementation remains unverified
> **Canonical marker:** Subordinate to PFOS v1.3 FINAL; becomes operational only after repository integration and verification
> **Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting **owning** subordinate contract → verified runtime evidence → historical/draft material

File 00 supersession rule:

> "This package does not supersede PFOS v1.3 FINAL. It decomposes its financial requirements into
> operational subordinate contracts. Any conflict is resolved upward, recorded in artifact 22, and never
> silently patched."

`PACKAGE_MANIFEST.json`: `"canonical_parent": "NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.3_FINAL_DRIVE_SAFE / LOCAL_FULL sibling"`,
`"classification": "review_before_commit"`, `"artifact_count": 23`, sha256 per artifact, and
`"unresolved": ["CONTRACT_4_ui_ynab.md", "post-YNAB live-product teardown", "current repository/runtime implementation state"]`.

**The pack ranks itself below "verified runtime evidence" and below "newest explicit owner direction."**
On its own terms, repository inspection and current owner instruction both outrank it. The one place it
binds hardest is file 03's entity-compatibility rule (§C.2).

### A.2 The precedence deviation (plan G-12)

| Document | Rank 4 wording |
|---|---|
| Governance pack, all 21 files | "non-conflicting **owning** subordinate contract" |
| O1 – O10 | "non-conflicting subordinate contract" |
| **O11 header** | "non-conflicting **owning** subordinate contract" |
| **O11 §2.1 body** | "non-conflicting subordinate contract" |

So O11 copied the pack's wording into its header and the canonical form into its body, contradicting
itself; O1–O10 dropped "owning" uniformly. O1–O10 are otherwise **byte-identical** to each other.

---

## §B Per-objective extraction — the load-bearing clauses

Only the clauses that decide ownership, sequencing or migration are reproduced. Full documents are in
`FINANCIAL/`.

### B.1 The anti-duplication clause, verbatim, per objective

This is the clause family the whole alignment check turns on.

| Obj | Clause |
|---|---|
| **O1** | (no single clause; expressed as §2.1 "O1 must reuse these entities rather than invent parallel definitions" + §7 "Exactly one component may mutate the canonical transaction/account/snapshot state for its domain") |
| **O2** | "It must not fabricate balances, create a parallel transaction ledger, or bypass reconciliation to generate faster warnings." · §22: "create an independent financial truth store" |
| **O3** | §3 excludes "canonical transaction ingestion or account reconciliation"; §40: "override O1 reconciliation", "override O2 protection", "compute authoritative money values inside the LLM" |
| **O4** | §32 invariants 1–15, incl. "only reconciled present capital may be treated as currently allocatable", "no LLM-generated authoritative money values", "no historical rewriting to hide overspending"; §23: "Temporary agents may analyze but may not maintain competing private versions of canonical financial truth or approved allocation state." |
| **O5** | "It does not create a competing balance, liquidity, allocation, or transaction truth store." · §25: "Agents must not maintain competing private financial truth." |
| **O6** | "It MUST NOT create a second transaction ledger, balance source, obligation store, budget truth, forecast truth, or wealth-state store." · §31 constraint 3: "No second canonical financial state." |
| **O7** | "O7 MUST NOT create a second transaction ledger, balance source, obligation registry, forecast store, wealth store, or decision ledger." |
| **O8** | "O8 MUST NOT create a second transaction ledger, account balance source, obligation registry, forecast store, regime engine, or decision authority." |
| **O9** | "O9 MUST NOT create a second transaction ledger, account balance source, budget truth, obligation registry, forecast authority, regime engine, or decision authority." · §5: "MUST reuse the canonical `Merchant` entity rather than create a competing merchant table definition." · §70: "Agents must not maintain hidden competing merchant ledgers." |
| **O10** | "O10 MUST NOT create a second financial ledger, health ledger, journal truth store, merchant ledger, regime engine, forecast authority, or decision authority." |
| **O11** | "O11 does not create financial truth." · §43: "Dependency does not grant write authority. O11 cannot mutate upstream truth stores." |

**Assessment:** every clause **HOLDS** against the current inventory. The stack is internally
well-behaved on anti-duplication. Its failures are *ownership overlap between objectives* (§D) and
*absent upstream dependencies* (§E), not requirement violations.

### B.2 Dependency chain, verbatim opening clauses

- **O2 §1:** "O2 consumes O1 canonical state."
- **O3 §1:** "O3 consumes O1 reconciled truth and O2 protection state. It must fail closed or narrow its conclusion when those prerequisites are stale, unresolved, or materially incomplete."
- **O4 §1:** "…after O1 Financial Truth and O2 Financial Protection establish the current state and protected requirements." §48 lists **O3 as upstream** — see §D.1.
- **O5 §1:** "O5 consumes reconciled financial truth from O1, protection state from O2, decision analysis from O3, and allocatable-capital outputs from O4."
- **O6 §1:** "O6 consumes reconciled financial truth from O1, protection state from O2, decision intelligence from O3, capital-allocation outputs from O4, and wealth trajectory from O5."
- **O7 §1:** "O7 consumes reconciled financial truth from O1, protection state from O2, decision context from O3, allocatable-capital outputs from O4, wealth trajectory from O5, and owner-facing continuity from O6."
- **O8 §1:** "O8 consumes canonical financial truth from O1, protection state from O2, decision records from O3, capital-allocation outputs from O4, wealth trajectory from O5, continuity/open-loop context from O6, and financial-regime history from O7."
- **O9 §1:** same chain through O8 ("…and historical windows/baselines from O8").
- **O10 §1:** same chain through O9 ("…and merchant/behavioral intelligence from O9").
- **O11 §1:** "O1 owns canonical financial facts. O8 owns longitudinal reconstruction. O9 owns merchant/behavioral enrichment. O10 owns cross-domain association validity. O11 consumes those outputs…"

**The chain is strictly cumulative and explicitly stated.** That is why plan §5 does not parallelize.

### B.3 The snapshot/receipt binding — why plan §3.2 is decisive

Every objective binds to `canonical_state_version` and to a computation receipt by name:

| Obj | Binding field(s) |
|---|---|
| O2 | liquidity protection object: "canonical snapshot/version"; protection exception: "canonical-state version" |
| O3 | `decision_packet.canonical_state_version`; §7.1 truth gate requires "canonical state ID/version; account freshness state; reconciliation status; unresolved high-impact exceptions; currency explicitness"; §31 computation-proof receipt |
| O4 | `allocation_proposal.canonical_state_version`; §21 computation receipt |
| O5 | `wealth_trajectory.canonical_state_version`; `wealth_recommendation.canonical_state_version`; §23 computation-proof record |
| O6 | `financial_brief.canonical_state_version`; `financial_refresh_proof.canonical_state_before` / `canonical_state_after` |
| O7 | `financial_regime_state.canonical_state_version`; `regime_computation_receipt.canonical_state_version` |
| O8 | `longitudinal_analysis.canonical_state_refs`; `longitudinal_computation_receipt` |
| O9 | `merchant_intelligence_snapshot.canonical_state_ref: O1_snapshot_ref`; `merchant_computation_receipt` |
| O10 | `decision_context_packet.financial_snapshot_id: canonical_snapshot_id`; `cross_domain_computation_receipt` |
| O11 | `decision_evidence_packet` requires `canonical_state_version`; `evidence_reasoning_receipt` |

And O1's own source: §5.7 "The authoritative writer produces a versioned `FinancialSnapshot` containing
the current state references, as-of/freshness, unresolved items, calculation version, and policy
version. **[FACT]** Exactly one current snapshot is canonical for a given snapshot/calculation/policy
version." §10 `[INFERENCE]`: "This proof contract should later become a shared `calculation_receipt` or
`state_use_receipt` schema consumed by O2+ objectives."

**Neither exists in `src/`** (zero `FinancialSnapshot` matches) **nor in the pipeline plan.**

### B.4 External-data dependency, per objective

| Obj | External requirement | Verdict |
|---|---|---|
| O1 | None beyond Drive | No external feed |
| O2 | "external risk input later approved by O16/O17" — indirect only | No O2-owned network call |
| O3 | **Required.** §20: "External research is permitted when the decision depends on facts not contained in canonical personal finance state, such as: provider terms; regulatory conditions; travel costs/requirements; product resale/depreciation context; market conditions; macroeconomic conditions; FX/rate context; asset-specific risk factors." Defines a Research Agent, forbidden from "leaking unnecessary private transaction data into external research queries." | Hard dependency; bounded |
| O4 | Consumed, not owned: "O4 does not directly scrape or score external intelligence. It consumes bounded, provenance-rich signals from O16/O17." Plus **a functional FX-provenance requirement** for any multi-currency allocation | Deferred to O16/O17 |
| O5 | **Required.** §12: "O5 may consume inflation, FX, rate, and regional/global economic assumptions only through governed O16/O17 intelligence interfaces." §3 disclaims "authoritative market-price retrieval itself" and "the complete external-news radar" | Hard unowned dependency on O16/O17, **plus an unowned asset-valuation source** |
| O6 | Drive API on a schedule ("at least twice daily"); WHOOP/BADAN and MARSAD **as references only** | No new provider integration |
| O7 | **Required.** §21: "O16 will own the Economic Early-Warning Radar. O7 may consume approved risk-state outputs such as: inflation/purchasing-power risk; currency risk; interest-rate/credit conditions; labor/income risk; regional/global disruption risk." Schema field is `external_risk_state: <future O16 ref\|null>` — **nullable, so O7 runs degraded without it** | Hard unowned dependency; degradable |
| O8 | **NONE required.** "O8 may **later** consume versioned economic/news/market context from O16/O17/MARSAD" | Optional, deferred |
| O9 | **Conditional only.** Resolution precedence works entirely from owner evidence: "1. explicit owner rule; 2. verified merchant mapping; 3. high-confidence historical pattern; 4. reliable statement/provider metadata; 5. model suggestion; 6. UNKNOWN/REVIEW." External escalates only when "internal evidence is insufficient and the identity/category materially affects analysis" | **Own-evidence sufficient** — this is what makes plan D-P(a) viable |
| O10 | Cross-**domain**, not external-market: FINANCIAL, WEARABLE, JOURNAL, DECISION, WORKLOAD, EXTERNAL, OTHER; pillars MAL, BADAN/WHOOP, YAWMIYAT, QARAR, MARSAD, THABAT | Governed by `sensitivity_class` + HIMAYAH v2 — plan D-Q |
| O11 | **Required by design.** Evidence tiers E1–E6 plus market/expectation signals (FX spot/forward, government yields, commodity prices, inflation breakevens, prediction markets, survey expectations, consensus forecasts) | Hard dependency; degrades to "return missing evidence rather than fabricate research" |

### B.5 Decision-register coverage (plan G-14)

| Objective | Entries opened |
|---|---|
| O1 | 4 — O1-D001 … O1-D004 |
| O2 | 6 — O2-D001 … O2-D006 |
| O3 | 8 — O3-D01 … O3-D08 |
| **O4** | **none** |
| **O5** | **none** |
| **O6** | **none** |
| **O7** | **none** (substitutes a FACT/INFERENCE/ASSUMPTION/MISSING block) |
| **O8** | **none** (same substitution) |
| **O9** | **none** (same substitution) |
| **O10** | not ID'd — §47 has AGREED (7) / PROPOSED DEFAULTS (6) / OPEN (7) / REJECTED (6) blocks |
| O11 | 8 — O11-D01 … O11-D08 |

So O4's fifteen invariants, O7's regime authority and O10's causality guards have **no citable IDs**.

### B.6 O7 — the quantitative core is entirely `[MISSING]`

Verbatim, from O7's own text:

- §9: "Exact hard-gate thresholds are **MISSING** until implemented in a governed policy contract. O7 must not invent them conversationally."
- §11: "Exact durations/thresholds are configuration decisions and remain `MISSING` until deterministic policy is authored and tested."
- §25: "Exact success thresholds remain `MISSING` until the implementation/validation contract defines them."
- §39 tagged: verified runtime schema/path; verified deterministic transition thresholds; verified hysteresis/dwell configuration; verified hard-gate policy values; verified historical regime reconstruction quality; verified integration with O15/O16/O18/O19/O28.
- §39 `[ASSUMPTION]`: "The current repository does not already contain a fully implemented equivalent four-regime engine. This must be confirmed during implementation research." — **confirmed absent this session: zero `regime` matches in `src/`.**

**Nine of nine numeric decisions unspecified.** This is why plan §5 Phase 7 requires a contract before
code, not merely a design.

---

## §C The governance pack — what it actually contains

### C.1 The 28 tenets (O1 paraphrases nine of them)

T01 Evidence Before Interpretation · T02 Ledger Is Not Memory · T03 Reconcile Before Optimize ·
T04 Cash Timing Matters · T05 Budget Is Allocation, Not Punishment · T06 Protect the Buffer ·
T07 Obligations Are First-Class · T08 Transfers Are Not Spending · T09 Uncertainty Is Data ·
T10 Forecasts Are Scenarios · T11 No Silent Mutation · T12 Automate Repetition, Not Authority ·
T13 Alerts Must Earn Attention · T14 Decision Before Dashboard · T15 One Canonical State ·
T16 Security by Data Minimization · T17 Human-Centered Recovery · T18 Learning Changes Rules Carefully ·
T19 Currency Explicitness · T20 Reversible by Default · T21 Freshness Is Part of Truth ·
T22 Explicit Sign Conventions · T23 Corrections Beat Convenient Consistency ·
T24 Few High-Leverage Actions · **T25 Deterministic Monetary Truth** ("Stored money uses integer
milliunits; the conversational layer MUST NOT calculate, convert, estimate, or restate authoritative
money values") · **T26 Single Writer** ("Each canonical domain MUST have exactly one authoritative
writer") · T27 Bounded Cross-Domain Signals · T28 Evidence Labels.

O1's nine-bullet summary maps to T01, T02, T03, T09, T15, T25, T26, T21, T23 — accurate, but **under a
third** of the set. T04–T08, T10–T14, T16–T20, T22, T24, T27, T28 are unrepresented in that summary.

Also in file 01, not in O1's summary: the **human approval boundary** ("Payment, transfer, spend,
borrowing, investment execution, account closure, external disclosure, consent completion, credential
actions, webhook registration, host/DNS mutation, commit, and push remain human-controlled.
`Decision Made?`, habit completion, and final calendar approval remain human-only fields") and the
**anti-shame rule** ("MUST NOT use humiliation, guilt, moral-worth scoring, fabricated urgency, or
coercive religious framing").

### C.2 File 03 — the entity compatibility rule (plan G-13)

> "No dependent document may invent a second definition of Account, Transaction, BudgetCategory,
> BudgetPeriod, Obligation, IncomeEvent, ForecastItem, FinancialSnapshot, DecisionRecord, Alert,
> EvidenceRecord, AuditEvent, Merchant, or FinancialGoal."

Fourteen entities. Present in `src/` by name: **Account, Transaction, Obligation**, plus a decision
record (`DecisionRecord` in `schema.ts`). **Absent by name: `EvidenceRecord`, `FinancialSnapshot`,
`IncomeEvent`, `ForecastItem`, `Merchant`, `Alert`, `FinancialGoal`, `BudgetCategory`, `BudgetPeriod`**
(the repo uses `Category`/`CategoryGroup`/`MonthBudget`). And **O5 §8 defines a `goal` object** while
the pack defines `FinancialGoal` — the parallel definition the rule forbids.

**Fidelity caveat:** file 03 is a *naming* contract, not a schema. Fields are flat backtick lists with
no types, no nullability, no keys. `direction` has no enum. `transaction_type` has no enum. T22 defers
sign conventions to "contract" and no contract supplies them.

### C.3 What the pack does **not** contain despite being cited as established

- **Any reconciliation tolerance value.** File 05 step 6 says only "Compare to authoritative assertion
  using currency-specific exact/tolerance policy." No number, no table, no pointer. O1 criterion 11
  inherits the same vagueness. **The pipeline plan's derived zero-milliunit tolerance is stronger than
  its cited source.**
- **Any enumerated event-type registry.** File 13 names exactly one event type,
  `BUDGET_ALLOCATION_CHANGED`, inside a synthetic example.
- **Any allocation-exactness rule.** File 04 says only "Split children MUST equal the parent under
  deterministic precision rules." `money-rules.md` rule 3 (`allocate()` sums exactly to total) has **no
  pack counterpart**.
- **Any mention of `drive.file`.** The string appears nowhere in the 23 files. The pack neither upholds
  nor breaches the scope invariant; it does not address it, so it cannot be cited either way.
- **Any executable fixture.** File 16 describes fixture families in prose; there is no test code and no
  expected values.
- **Its own declared parent.** See §A.

### C.4 Pack files with no objective counterpart — do not lose these

Eight-plus files have no O-doc equivalent: **02** (source lineage), **12** (agent roles + the
single-writer rule), **14** (privacy classes + approval ladder), **15** (UI/journeys), **16**
(validation + the eight verification levels + tamper requirement), **17** (seven-phase roadmap), **18**
and **19** (current-state and monthly-close templates), **20** (agent runbook + the RPV loop), **21**
(evidence register + E1–E6 tiers), **22** (changelog + FN-D001…D008).

The three that matter most if the objectives become the working authority:

- **File 12's single-writer rule:** "Temporary/sub-agents MAY analyze but MUST write only through the
  authoritative port. UI, LLM, Telegram, and temporary agents MUST NOT directly mutate canonical
  finance tables/ledgers."
- **File 14's authority ladder:** read-only analysis permitted in scope; reversible internal writes
  require owning policy; external reversible writes require exact approval; "Financial, destructive,
  credential, consent, webhook, host/DNS, commit/push, borrowing, investment execution, and account
  closure remain human-controlled."
- **File 16's honesty clause:** "A package may be called **contract-verified** after static integrity +
  deliberate tamper proof. Runtime **verified** requires actual repository/runtime tests and observed
  output."

### C.5 Pack vs the three hard NIZAM invariants

| Invariant | Pack position |
|---|---|
| Money is integer milliunits, never float | **Reinforced.** T25, file 03 global invariant, file 16 static gate, FN-D004; every monetary field suffixed `_milliunits`; floats never mentioned. **Gap:** no rounding, remainder or allocation-exactness rule (§C.3). |
| Drive scope stays `drive.file`; Drive never holds keys or secrets | **Secrets: aligned and stronger** — file 14 bans "Secrets, credentials, OTPs, PINs, full card/account authentication data, private keys, `.env` content, and plaintext personal-data archives." **Scope: silent** (§C.3). **Conflict is with `drive-db.md`, not with the invariant** — see plan G-11. |
| The LLM tier never computes or sources a monetary value | **Most emphatically repeated rule in the pack.** T25; file 01 non-goals; file 08 ("`safe_to_spend` … never inferred from bank balance alone"); file 09 ("The conversational layer explains the engine result but does not compute it"); file 12; file 02 deprecates "LLM as arithmetic authority"; file 18's template carries no literal monetary values at all. |

One adjacent item needing an explicit boundary before Phase 10: **O10 §30** says "O10 does not require
every statistical algorithm to produce byte-identical floating-point output across all hardware." That
concerns statistical analysis, not stored money, so it does not breach the invariant — but it is the one
place in the corpus where floating point is sanctioned, and the line between "statistical output" and "a
figure shown to the owner" must be stated.

---

## §D The collision register

Ownership overlaps found between objectives. Each needs a single owner before its phase.

| # | Collision | Documents | Severity |
|---|---|---|---|
| **D.1** | **O3↔O4 dependency direction.** O4 §48 lists O3 **upstream**; O4 §22.5 has the Decision Agent consuming O4 output *and* invoking O3 packets; **O3 §39 omits O4 entirely** while O3 §1 claims scope over "competing uses of capital." | O3, O4 | **Material** — plan D-T |
| **D.2** | **Opportunity cost, twice.** O3 scope 11 + §16 + `opportunity_cost_refs` vs O4 scope 16 + §16 (full object) + §33 engine + `opportunity_cost_ref`. Neither §3 non-govern list excludes it. | O3, O4 | **Material** — fold into D-T |
| **D.3** | **Productive-credit vs dependency-loop classifier, three definitions.** O2 §9, O3 §15, O4 §10.1/§10.2 — all three define it, all three defer to O14. | O2, O3, O4 | Medium |
| **D.4** | **Incremental debt payoff vs liquidity.** O3 §5.5 + scope 9 vs O4 §9's five proposal classes. O2 §3 cleanly excludes itself. | O3, O4 | Medium |
| **D.5** | **Materiality dimension lists, three times.** O2 §7, O3 §24, O4 §28 — near-identical dimension sets feeding O28; only O3 enumerates the output enum `LOW\|MODERATE\|HIGH\|CRITICAL`. | O2, O3, O4 | Medium |
| **D.6** | **Protected floor + emergency reserve.** O2 scope 4/5 claim breach *detection*; O3 §14 and O4 §11 each independently define the operating-floor/emergency-reserve *distinction*. Three definitions of one boundary; all three defer the formula to O15. | O2, O3, O4 | Medium |
| **D.7** | **Briefing content.** O6 scope 2/3/14 owns orchestration; **O7 §28 concedes** ("O6 remains responsible for communication scheduling"); **O5 §29 does not** and prescribes the content of the same three windows, marked `[AGREED]`. | O5, O6 | **Material** — plan D-U / G-8 |
| **D.8** | **Computation-proof receipts, seven schemas.** O3 §31, O4 §21, O5 §23, O6 §23, O7 §26, O8 §29, O9 §49, O10 §29, O11 §35. O5/O6/O8/O10 defer to O29; **O7 never mentions O29**; no shared base named. | all | **High** — plan D-W / G-4 |
| **D.9** | **Confidence models, four.** O8 §30 (11 inputs), O9 §50 (10), O10 §25 (12), O11 §25 + §14. O11 claims ownership; **none of O8/O9/O10 defer to it.** | O8–O11 | **High** — plan D-W / G-5 |
| **D.10** | **Envelope schema, twice.** O5 §25 `agent_envelope` and O6 §18 `financial_task_envelope` have effectively identical field sets. Both mirror pack file 12's handoff schema. | O5, O6 | Low |
| **D.11** | **Unusualness.** O8 scope 20/21 + §21 provides "a historical unusualness interface to O28" and emits `unusualness_ref`; O9 scope 20 + §21 defines `unusualness_signal` with `unusualness_score_ref`. O9 §26 asserts a split; **O8 never cedes it.** | O8, O9 | **High** |
| **D.12** | **Merchant history.** O8 §10 lists 13 merchant outputs (spend, frequency, cadence, concentration, alias change, normalization confidence); O8 §3 disclaims only "merchant master-data ownership beyond consuming canonical merchant mappings." O9 §26's split table is the only arbiter and is not mirrored in O8. | O8, O9 | **High** |
| **D.13** | **Cross-pillar joins, two contracts.** O8 §23 defines its own join requirements (join key, time alignment, missing-data handling, confounder notes, uncertainty) **with no hypothesis registry, no multiple-comparison control and no eligibility gates** — an analysis path that bypasses O10 §15/§19. | O8, O10 | **High** |
| **D.14** | **Journal retrieval, two paths.** O9 §43 lets O9 itself retrieve journal context; O10 §1 forbids a second "journal truth store" and O10 §7 requires bounded packet-mediated retrieval. O9 §42/FM-09 correctly routes *causality* to O10 — the conflict is *retrieval*, not causality. | O9, O10 | Medium |
| **D.15** | **Drive mirror, four subordinate contracts** against O1 §3.13's owned mirroring scope: O8 §46, O9 §66, O10 §27, O11 §31. Plus **O1 §3 item 14 vs O6 §3 item 4** on discovery itself. | O1, O6, O8–O11 | **High** — plan G-3 |
| **D.16** | **Retention/storage, three specifications.** O8 §48, O9 §67, O10 §28. **O10 defers to O34/O35; O8 and O9 do not reference them.** | O8–O10 | Medium |

---

## §E Absent dependencies

### E.1 The twenty-one forward-referenced objectives (plan G-9)

Union across O8/O9/O10/O11's forward references: **O12, O15, O16, O17, O19, O20, O21, O22, O23, O24,
O25, O26, O27, O28, O34, O35, O39, O40, O41, O42, O43.** Plus non-financial pillars **MAL, BADAN/WHOOP,
YAWMIYAT, QARAR, MARSAD, THABAT**. `FINANCIAL/` holds exactly `01_`–`11_`; none of the twenty-one is
present.

**Load-bearing, with who is blocked:**

| Missing | Owns | Blocks |
|---|---|---|
| **O15 Dynamic Resilience** | the protected-liquidity floor and emergency reserve | O2 (§8 "does not invent the floor"), O3 §14, O4 §11 ("Until O15 exists, O4 must not invent a number"), O5 §5.3, O7 §17 ("O7 must never calculate a floor amount itself") |
| **O28 Dynamic Materiality** | multi-dimensional severity | O2 §7, O3 §24, O5 §35, O8 §21, O9 §37, O10 §17.3 |
| **O16 Economic Early-Warning Radar** | macro/FX/inflation/rate risk state | O5 §12/§34, O7 §21, O11 §29 |
| **O19 Adversarial Decision Protection** | high-friction challenge sequencing | O2 §13, O3 §2.2, O5 §36, O10 §21, O11 §23 |
| **O22 / O27** | the decision-outcome composite | O10 §18 explicitly **refuses to invent** it |
| **O34 / O35** | storage and persistence policy | O10 §28 defers to it; O8/O9 do not |
| **O29 Computation Proof** | the shared receipt | O5, O6, O8, O10 defer; O7 does not |
| **O12 Forecast Accountability** | forecast-vs-actual calibration | O3, O4, O5, O8, O10, O11 |

### E.2 The three "unowned" capabilities that are actually owned (plan G-6 / D-N)

| Capability | Who disclaims it | Who consumes it | **Actual owner, found this session** |
|---|---|---|---|
| **Safe-to-spend policy** | O1 §3 and §17; O2 §3 | O2 §5.2, O3 §9, O4 §33, O6 §24 | **`contracts/pfos/03`** — "Safe-to-spend engine"; implemented at **`src/features/safeToSpend/`** (`safeToSpendForHorizon`, `safeToSpendAllHorizons`, `computeForWindow`) |
| **Forecasting / probability methodology** | O1 §3; O2 §3 | O3 §11, O4 §33, O5 §20 | **`contracts/pfos/03`** — "forecast engine"; implemented at **`src/features/forecast/`** (`forecastHorizon`, `forecastAll`, `simulate`, `forecastStartReconciles`) |
| **Net-worth engine** | — (O5 §3 disclaims market-price retrieval) | O5 throughout | **`contracts/pfos/03`** — "net-worth engine"; implemented at **`src/features/netWorth/`** (`netWorth`, `realNetWorth`, `convert`) and `src/features/reports/netWorth.ts` |

**Genuinely still unowned:** the **protected-floor formula** (O15) and **asset valuation** (no asset or
valuation entity in pack 03's fourteen; no valuation engine in `src/`; O5 §3 disclaims retrieval).

---

## §F What this annex does not do

It authorizes nothing. It resolves no owner decision. It promotes no document to contract status. It
amends no contract and no steering file. It adds no acceptance check and changes no declared harness
count. It proposes migrations (D-R, D-W) and takes none. No external source was consulted for it — every
finding is from files in this working tree, read this session. The governance pack was extracted outside
the repository tree so that the working-tree dirty count governed by **D-H** is unchanged.
