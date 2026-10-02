# NIZAM Financial Objectives Alignment Plan — O1 through O11

Status: **PLAN ONLY. No implementation authorized by this document.** Writing code, editing a test,
running a gate, touching a host, or spending against a key each need separate, explicit owner
approval. This document grants none of them.

**Revision 1** (2026-09-20).
Companion evidence: `docs/plans/nizam-financial-objectives-alignment-annex.md`.
Follow-on to `docs/plans/nizam-transaction-capture-pipeline-plan.md` (Revision 2), which **remains
authoritative for its own scope (S1–S12) and is not superseded, reopened, or re-decided here.** Its
decisions **D-A through D-K are inherited verbatim**; this document cites them by letter and adds new
letters from **D-L**.
Prepared against working tree at HEAD `5652edf`, `master` 4 ahead of `origin/master`, **54 dirty
entries** — of which `FINANCIAL/` is one (see G-1).

---

## §0 Scope and authority

### 0.1 What this document is for

The eleven objective documents in `FINANCIAL/` are each stamped *"PROPOSED OVERHAUL DESIGN —
owner-approved objective, implementation not yet verified."* Read literally: the **objectives** carry
owner approval; nobody has checked that the **implementation** — what exists in `src/`, what the
pipeline plan proposes next, and what `contracts/pfos/01–15` and `contracts/CONTRACT_1..6` already
claim to own — lines up with those eleven, in the right order, without duplicating authority or
breaching any objective's own non-goal clauses.

That check is this document. It answers four questions and nothing else: **who owns what**, **what
already exists**, **what order the remaining work must happen in**, and **which choices stand between
"pipeline plan approved" and "O11 buildable."**

### 0.2 Authority order used, with the new stack slotted in

1. **Domain steering** (`.kiro/steering/*`) — unchanged, still first. `money-rules.md` and
   `drive-db.md` are never traded away.
2. **Contracts** — `contracts/pfos/01–15`, `contracts/CONTRACT_1..6` (note **CONTRACT_6 is DRAFT and
   unapproved**; its content is not settled), `contracts/programs/*`.
3. **Specs** — `.kiro/specs/<spec>/{requirements,design,tasks}.md`.
4. **Supporting docs and dated receipts** — evidence, never authority.

**Where `FINANCIAL/O1..O11` sits is itself a finding, not an assumption — see G-1 and G-2.** The short
answer, on evidence: **level 4, supporting/evidence, until the owner promotes them** — and that is a
decision (**D-L**), not a verdict I am entitled to reach alone.

### 0.3 Evidence labels

| Label | Meaning |
|---|---|
| **VERIFIED** | Read or run in this session |
| **UNVERIFIED** | Asserted somewhere, not established |
| **STALE** | A dated receipt, not re-observed |
| **INACCESSIBLE** | Unreachable from this session |

Two standing cautions carried from the pipeline plan. A documented status is not fresh verification.
Passing tests are not live readiness. Prior reports were treated as hypotheses and re-checked.

### 0.4 Ten things this plan is not

| Not | Because |
|---|---|
| An implementation | No file under `src/` or `tests/` is touched. |
| An authorization | Every Stage-2 item — live operation, deployment, credentials, host mutation, provider spend, G1–G8 — remains separate and is never implied. |
| A resolution of D-A through D-K | Those are the pipeline plan's and are inherited unchanged. Where an objective depends on one, this document says **which** and **how**; it never proposes a different answer. |
| A supersession of the pipeline plan | S1–S12 stand exactly as written. §3 adds requirements **to** its scope; it re-decides nothing in it. |
| A schema migration | No `SCHEMA_VERSION`, table, column or enum is changed. Every migration the objectives imply is listed as an owner decision. |
| An approval of draft CONTRACT_6 | D-E is still open. Nothing here implies it. |
| A promotion of `FINANCIAL/O1..O11` to contract status | That is **D-L**. |
| A design of O2–O11's internals | §5 sequences them and names their modules. Each objective gets its own future plan-and-design cycle. |
| A claim about the host, Drive, or `nizamcore` | All **INACCESSIBLE** from this session. No host probed, no Drive token exists here. |
| A claim about anything outside this local working tree | Including PFOS v1.3 FINAL, which is absent — see G-2. |

### 0.5 Data discipline

Every example is synthetic. No real amount, balance, account identifier, payee, hostname, Drive
identifier, channel identifier or ledger excerpt appears, per `two-agent-vps.md` §0b R24.

---

## §0b The precedence finding — read this before §1

All eleven objectives carry the same precedence line (**VERIFIED byte-identical across O1–O10**;
O11 deviates, see G-12):

> safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting
> subordinate contract → verified runtime evidence → historical/draft material

**This ladder cannot be evaluated as written, for two independent reasons, and neither is resolvable
by me.**

**Reason one — rank 3 is absent.** `NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.3_FINAL_DRIVE_SAFE` and its
"LOCAL_FULL sibling" are named as the governance pack's `canonical_parent`, cited in all 21 pack
content files, and placed at step 2 of the pack's own **mandatory read order**. They are **not in this
repository**: a search of `contracts/**`, `docs/**` and `.kiro/steering/*` for `v1.3 FINAL`,
`MASTER_UNIFIED`, `LOCAL_FULL` or `DRIVE_SAFE` returns **exactly one tracked file**,
`contracts/programs/SEVEN_CONTRACT_RECOVERY.md`, and what it says is decisive (**VERIFIED**):

> "The reported unified v1.3 FINAL remains a lineage claim until its exact source and authoritative
> index can be inspected; local Contract 13 explicitly says its v1.4 proposal does not supersede it."

So the repository has **already ruled**: v1.3 FINAL is an uninspected lineage claim. The governance
pack compounds this by omitting v1.3 FINAL from its own `unresolved` array — it lists only the YNAB UI
contract, the teardown, and repository state. **The pack assumes its parent is in hand. It is not.**
Consequence: the pack's read order cannot be completed, and "subordinate to v1.3 FINAL when they
differ" is **unfalsifiable** — nobody can know whether the pack or the objectives diverge from a
parent no one has produced.

**Reason two — the objectives are untracked.** `git ls-files FINANCIAL/` returns **zero files**;
`git status --porcelain FINANCIAL/` returns `?? FINANCIAL/` (**VERIFIED**). The eleven documents are
untracked working-tree material and are part of the 54 dirty entries that **D-H** governs. Untracked
proposal documents stamped "implementation not yet verified" are, by the authority order in §0.2,
**level 4 — evidence, not authority.**

**The tension that makes this a decision rather than a conclusion.** Rank 2 of the ladder is "newest
explicit owner direction," and the objectives are stamped **owner-approved**. So they are plausibly
owner *direction* (rank 2, above contracts) while being, as artifacts, untracked unverified proposals
(level 4). Both readings are defensible from the evidence. **I will not choose. That is D-L.**

**The mechanism for resolving it already exists and should be used.** `contracts/pfos/_PFOS_CONTRACT_INDEX.md`
states the rule for exactly this class of conflict (**VERIFIED**):

> "Where the two disagree, the disagreement is recorded in `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md` and
> resolved by an owner decision — never by silently editing either side."

That is the channel. Not a new one.

**One further authority fact worth stating plainly.** `contracts/pfos/01–15` is **not** PFOS v1.3
FINAL. Per its own index, it is four Drive-ingested blueprints (01–04, SHA-256 recorded) plus
NIZAM-derived contracts authored inside this repository (05, 06, 09–15), with 07 and 08 **verified
absent after three independent sweeps**. So the objectives and the repository's PFOS stack are two
*sibling* decompositions of the same absent parent — which is precisely why they overlap and why the
overlap has to be adjudicated rather than assumed away.

---

## §1 Objective-by-objective current-state map

Scope, non-goal and dependency clauses were extracted verbatim; see the annex for the full text. Code
status was established by reading source and by capability probes over `src/**/*.ts(x)` (**VERIFIED**).

**The probe result, first, because it frames every row.** Identifier searches across `src/` return
**zero matches** for: `evidence_item`, `EvidenceRecord`, `FinancialSnapshot`, `claim_id`,
`confidence_profile`, `evidence_weight`, `regime`, `financial_regime`, `merchant_alias`,
`recurrence_series`, `behavioral_baseline`, `unusualness`, `leakage`, `open_loop`, `financial_brief`,
`longitudinal`, `cross_domain`, `hypothesis`. `src/features/` holds exactly: accounts, benchmark,
budget, decisions, demo, forecast, import, netWorth, obligations, reconciliation, reports, routing,
safeToSpend, settings, transactions.

| # | Objective | Requires (abridged) | What exists (VERIFIED) | Status | Its own non-goal clause, checked against inventory |
|---|---|---|---|---|---|
| **O1** | Financial Truth | Evidence registry, identity/dedupe, relation matching, reconciliation, **canonical snapshot**, freshness/confidence exposure, supersession, **state-use receipt**, Drive discovery + read-back. 22 acceptance criteria. | Browser: `ledgerImport.ts` (parse+dedupe+post), `ledgerStore.ts` read model, `state/actions.ts` corrections/transfers, Drive `driveDb.ts`/`sync.ts`. Server: `source_events` immutable inbox, `transactionsRepository` single writer, `transaction_links`, `statements`, `audit_log`, `reconcile.ts`, `dailyCapture.ts` (unwired). | **PARTIAL — the substrate exists, two interfaces do not.** See §3: 14 of 22 criteria covered by the pipeline plan, 4 partial, 4 absent. **`FinancialSnapshot` and the state-use receipt are absent from code and from the pipeline plan.** | "Exactly one canonical current-state writer" — **AT RISK, already a live defect.** Pipeline-plan **F7**: two canonical stores, no bridge, divergent correction semantics. This is O1 criterion 1 failing *today*, and it is why **D-A** is the gate for everything. |
| **O2** | Financial Protection | Obligation protection object, liquidity protection object, protection exception, 5-family event taxonomy, P0–P3 severity, alert lifecycle, protected-floor interface. 22 criteria. | `src/features/obligations/` (`obligationFundingReport`, `confidentInflowsBy`, `pendingOutflowsBy`, horizons), `Obligation` entity in `schema.ts` with `verificationSource`/`confidence`/`protectedReserve`. No alert store, no exception queue, no severity engine. | **PARTIAL.** Obligation math exists; the entire protection/alert/exception layer is **ABSENT**. | "create an independent financial truth store" — **HOLDS.** O2 §15 explicitly hedges: decide whether `protection_event` is needed "or whether the existing alert/obligation/audit schemas can represent O2 without creating duplicate truth." Best-behaved schema clause in the set. |
| **O3** | Decision Intelligence | `decision_packet` (33 fields), 5 prerequisite gates, option generation, recommendation labels, computation-proof receipt, decision ledger (11 event types). 22 criteria. | `src/features/decisions/` — `decidePurchase`, `applyPurchase`, `harmsProtectedObligation`, `decisionRegistry.ts` (append-only, `recordDecision`/`reviewDecision` enforcing byte-identity of core keys, `matureDecisions`). | **PARTIAL — the strongest existing match of any O2–O11 objective.** An append-only decision registry with frozen forecasts already exists. The packet, the gates and the receipt are ABSENT. | "override O1 reconciliation / override O2 protection / compute authoritative money inside the LLM" — **HOLDS**, and is already structurally enforced: `runtimeAdapter.AUTHORITY_KEY` makes a monetary key unrepresentable across the Hermes tool boundary. |
| **O4** | Capital Optimization | `allocation_proposal`, `allocation_event` (append-only, versioned), capital-pool classification, 12-category registry, 15 engine interfaces, computation receipt. 20 criteria. | `src/features/budget/` — `computeBudget`, `computeMonth`, `setAssigned`, `applySeed`, `ensureCreditCardPaymentCategories`, `targets.ts`, `month.ts`. `CategoryTarget` 8-type vocabulary. | **PARTIAL.** Envelope budgeting exists and is tested. Allocation *proposals*, allocation *events*, versioning and pool classification are ABSENT. | Fifteen invariants incl. "no silent reallocation of restricted funds," "all material allocation changes preserve provenance and version history" — **HOLDS in intent**, but note pipeline-plan **F16**: `MonthBudget.activity`/`.available` are persisted, written stale, and read by nobody. O4 must not start reading them. |
| **O5** | Wealth Growth | `goal`, `wealth_trajectory`, `wealth_recommendation`, realized-vs-unrealized taxonomy (8 classes), 14 engine interfaces. 14 criteria. | `src/features/netWorth/` — `netWorth`, `realNetWorth`, `realValue`, `toEgp`/`fromEgp`/`convert`, `resolveMacro`; `src/features/reports/netWorth.ts` `netWorthSeries`; `assets`, `fxRates`, `macro` collections. | **PARTIAL.** Net worth and FX-ratio conversion exist. Goals, trajectory objects and the realized/unrealized taxonomy are ABSENT. | "does not create a competing balance, liquidity, allocation, or transaction truth store" — **HOLDS.** But see **G-6**: O5's headline metric (realized net worth) depends on a valuation engine O1's entity list does not contain, and O5 §3 disclaims building. |
| **O6** | Cognitive Offloading | 11 new objects (`financial_open_loop`, `financial_brief`, `financial_refresh_proof`, `drive_discovery_receipt`, …), 3 daily windows, twice-daily Drive discovery, review packets. 17 tests. | `scheduler.ts` single clock (`SCHEDULER_TARGETS = ['life','finance']`, a `const` tuple), `liveness.ts`, `haltGate.ts`, `workQueueRepo` (claim/settle/reclaim/prune). **No brief, no open-loop ledger, no discovery receipt.** | **PARTIAL — the clock exists, the cognition does not.** | "MUST NOT create a second transaction ledger, balance source, obligation store, budget truth, forecast truth, or wealth-state store" — **HOLDS**, and §31 gives twelve implementation constraints including "No second canonical financial state." **But see G-3**: O6 §3 item 4 claims Drive discovery, which **O1 §3 item 14 also claims.** |
| **O7** | Regime Management | `financial_regime_state`, `regime_period` (append-only history), `regime_computation_receipt`, 5 enums, 7 signal families, hard gates, hysteresis. 20 DoD conditions. | **NOTHING.** Zero `regime` matches in `src/`. | **ABSENT.** And per the annex, **the entire quantitative core is `[MISSING]` in the document itself** — nine of nine numeric decisions (thresholds, gates, dwell, weights, success bars) unspecified. | "MUST NOT create a second transaction ledger, balance source, obligation registry, forecast store, wealth store, or decision ledger" — **HOLDS**, strongest phrasing in the set, plus "O7 must never calculate a floor amount itself." |
| **O8** | Longitudinal Intelligence | 17 registered windows, `historical_coverage` (COMPLETE/PARTIAL/UNKNOWN), `forecast_evaluation`, `longitudinal_analysis` with `supersedes_analysis_id`, receipts. 22 DoD + 14 questions. | **NOTHING** by name. Adjacent: `ageOfMoney.ts`, `spending.ts` `activityMonths`, `netWorthSeries`, `getIndex().byMonth`. | **ABSENT** as specified; primitive month-bucketing exists. | "MUST NOT create a second transaction ledger, account balance source, obligation registry, forecast store, regime engine, or decision authority" — **HOLDS.** But **G-4/G-5**: O8 defines its own receipt *and* its own confidence model, and **§23 defines a parallel cross-pillar join contract with no hypothesis registry and no multiple-comparison control** — an analysis path that could bypass O10's gates. **Severity: HIGH.** |
| **O9** | Merchant & Behavioral Intelligence | `merchant_alias`, `merchant_relationship`, `merchant_research`, `recurrence_series`, `behavioral_baseline`, `unusualness_signal`, `leakage_candidate`, `behavioral_pattern`, review queue. 18 DoD. | `normalizePayee` in `ledgerImport.ts`; `Payee {id,name}` registry; `importInfo.normalizedPayee` (declared, **never written** — pipeline-plan F11). No `Merchant` entity at all. | **ABSENT.** One normalization function exists. | "MUST NOT create a second transaction ledger, account balance source, budget truth, obligation registry, forecast authority, regime engine, or decision authority" plus "MUST reuse the canonical `Merchant` entity rather than create a competing merchant table" — **HOLDS**, but the canonical `Merchant` entity **does not exist in `src/`**, so "reuse" has nothing to reuse. **G-13.** |
| **O10** | Cross-Domain Decision Intelligence | `cross_domain_evidence`, `decision_context_packet`, `context_windows`, `cross_domain_hypothesis`, `association_result` (with `causal_claim_allowed: false` hardcoded), `signal_eligibility` state machine, `reassessment_trigger`. 20 criteria. | **NOTHING.** | **ABSENT.** | "MUST NOT create a second financial ledger, health ledger, journal truth store, merchant ledger, regime engine, forecast authority, or decision authority" — **HOLDS, and it is the best-guarded document in the set**: causality is refused *structurally* (`causal_claim_allowed: false`, with a tamper test that injects a causal claim and requires policy failure). |
| **O11** | Evidence-Based Reasoning | `claim`, `evidence_item`, `independence_analysis`, `freshness_policy`, `expectation_signal`, `contradiction_record`, `assumption`, `missing_evidence_item`, `weak_signal`, `research_request`, `confidence_profile`, `evidence_weight_receipt`. 20 criteria. | **NOTHING.** The only confidence fields in `src/` are unrelated: `importInfo.confidenceScore`/`confidenceReason`, `Obligation.confidence`, `confidenceBps`/`confidenceBand` on decisions and ledger rows. | **ABSENT.** | "O11 does not create financial truth" / "cannot mutate upstream truth stores" — **HOLDS.** Note a real constraint: `ledger.types.ts` deliberately refuses band→score conversion ("A band is not a score"), which bounds how O11's `*_class` enums may be implemented. |

### 1.1 Findings, with severity

| # | Finding | Severity | Evidence |
|---|---|---|---|
| **G-1** | **`FINANCIAL/` is untracked.** Zero files in `git ls-files`; `?? FINANCIAL/`. The eleven objectives are working-tree material inside D-H's 54 dirty entries, not repository authority. | **CRITICAL** — it determines whether anything below is binding. | VERIFIED |
| **G-2** | **The O-stack's precedence rank 3 is absent and already adjudicated.** PFOS v1.3 FINAL / LOCAL_FULL exist nowhere in the tree; `SEVEN_CONTRACT_RECOVERY.md` calls it "a lineage claim until its exact source and authoritative index can be inspected." The governance pack omits it from its own unresolved list. | **CRITICAL** — the ladder is unfalsifiable, so "subordinate to v1.3 FINAL" cannot be checked. | VERIFIED |
| **G-3** | **Drive discovery is claimed twice.** O1 §3 item 14 ("discovery of new/modified Drive financial evidence even when the owner does not mention it") vs O6 §3 item 4 + §8 (twice-daily discovery, cadence, receipt, pipeline ending in `authoritative write`). Neither document assigns the split. Separately, O8 §46, O9 §66, O10 §27 and O11 §31 each define their **own** Drive mirror/read-back record against O1 §3.13's mirroring scope. | **HIGH** — four subordinate mirror contracts against one owned scope is exactly the second-source pattern every objective forbids. | VERIFIED |
| **G-4** | **Seven parallel computation-receipt schemas.** O3 §31, O4 §21, O5 §23, O6 §23, O7 §26, O8 §29, O9 §49, O10 §29, O11 §35 each define one. O5/O6/O8/O10 defer to **O29 Computation Proof**; **O7 never mentions O29**; no shared base type is named anywhere. | **HIGH** — guaranteed schema duplication, and O29 does not exist. | VERIFIED |
| **G-5** | **Four parallel confidence models.** O8 §30, O9 §50, O10 §25, O11 §25 + §14. O11 claims the epistemic control plane and states "Overall confidence is engine/policy-owned," but **none of O8/O9/O10 defer to O11.** | **HIGH** | VERIFIED |
| **G-6** | **Three capabilities are consumed by multiple objectives and disclaimed by their suppliers — but are in fact already owned by the repository's own PFOS 03.** ① **Safe-to-spend policy**: O1 §3 and §17 disclaim it, O2 §3 disclaims it, yet O2 §5.2, O3 §9 and O4 §33 all consume it. ② **Forecasting/probability methodology**: O1 and O2 §3 disclaim it; O3 §11, O4 §33, O5 §20 consume it. ③ **Asset valuation / realized net worth**: O1's canonical entity list contains **no asset or valuation entity**, O5 §3 disclaims "authoritative market-price retrieval," yet realized net worth is O5's headline metric. **The resolution is already in the repository:** `contracts/pfos/03` governs "Safe-to-spend engine, … risk engine, forecast engine, debt and capital allocation, net-worth engine, leak and behavioural intelligence, macro engine, evidence packages, decision outcome registry" — and `src/features/safeToSpend`, `forecast` and `netWorth` implement it. **The O-stack did not check the repository and declared unowned what is owned.** | **HIGH** — but it resolves *downward*, not into new work. This is the single most important correction this document makes to the objective stack. | VERIFIED |
| **G-7** | **O3↔O4 dependency direction is contradictory.** O4 §48 lists O3 as **upstream**; O4 §22.5 has the Decision Agent consuming O4 output and invoking O3 packets (both directions); **O3 §39 omits O4 entirely.** Sequencing cannot be derived from these three clauses. | **MEDIUM** — blocks §5 phase ordering between 3 and 4. | VERIFIED |
| **G-8** | **Briefing content is specified twice.** O6 §3 items 2/3/14 own briefing orchestration and O7 §28 concedes cleanly ("O6 remains responsible for communication scheduling"). **O5 §29 never concedes** — it prescribes the content of the same three windows, marked `[AGREED]`. | **MEDIUM** | VERIFIED |
| **G-9** | **Twenty-one forward-referenced objectives are not supplied.** Union across O8/O9/O10/O11: O12, O15, O16, O17, O19, O20, O21, O22, O23, O24, O25, O26, O27, O28, O34, O35, O39, O40–O43, plus pillars MAL, BADAN/WHOOP, YAWMIYAT, QARAR, MARSAD, THABAT. At least six are **load-bearing**: O15 (protected floor — O2/O3/O4/O5/O7 all consume), O28 (materiality — O2/O3/O5/O8/O9/O10), O19 (challenge), O22/O27 (the decision-outcome composite O10 §18 refuses to invent), O16 (macro feed — O5/O7/O11), O34/O35 (storage policy O10 §28 defers to). | **MEDIUM** — O2 onward are each blocked on undocumented objectives. Each objective self-guards correctly ("Until O15 exists, O4 must not invent a number"), so this is a sequencing constraint, not a contract breach. | VERIFIED |
| **G-10** | **Drive content policy diverges, and the change-control step was not performed.** Pack 14 + FN-D006/FN-D008: Drive is "one-way reviewed mirror/archive, **not live ledger**," `strict_local` means "never sync," and "plaintext personal-data archives MUST NOT enter Drive." O1 §8: Drive is inspected **twice daily**, and "statements, SMS transaction exports, merchant descriptions, transaction dates, amounts, balances … should remain **readable** in the approved Drive representation." O1 is careful (O1-D004 requires formal change control; O1 §2.2 concedes the older contract stays operational) — **but pack 01 requires the change be recorded in artifact 22, and artifact 22 still holds only FN-D001…D008 with FN-D006/D008 intact.** | **MEDIUM** — a real policy expansion inherited as though already permitted. | VERIFIED |
| **G-11** | **`drive-db.md` steering conflicts with both the pack and O1.** Steering: "**Canonical store:** one JSON file `nizam_db.json` … in the user's Drive" — Drive *is* the database. Pack 14: Drive is "never live ledger." O1 §8: Drive is the evidence/recovery mirror; the VPS is compute. `tech.md` D1 already anticipates the landing ("this Drive-JSON store is the Profile-A build, NOT the final database"), which agrees with the pack and O1 and disagrees with `drive-db.md` as currently written. **Steering outranks both**, so this must be reconciled *in steering* before either is relied on. | **MEDIUM** — and it is the same question as pipeline-plan **D-A**, arriving from a second direction. | VERIFIED |
| **G-12** | **O11's precedence header deviates and contradicts its own body.** O11's header reads "non-conflicting **owning** subordinate contract"; O1–O10 read "non-conflicting subordinate contract"; O11 §2.1 then restates the canonical form **without** "owning." The pack's own ladder includes "owning," so O11 copied the pack and O1–O10 dropped a word. | **LOW** — but it is a precedence line, so it should be made uniform deliberately rather than left as drift. | VERIFIED |
| **G-13** | **The canonical entity contract is unenforceable against current code.** Pack 03: "No dependent document may invent a second definition of Account, Transaction, BudgetCategory, BudgetPeriod, Obligation, IncomeEvent, ForecastItem, FinancialSnapshot, DecisionRecord, Alert, EvidenceRecord, AuditEvent, Merchant, or FinancialGoal." Of those fourteen, `src/` has Account, Transaction, Obligation and a decision record; **`EvidenceRecord`, `FinancialSnapshot`, `IncomeEvent`, `ForecastItem`, `Merchant`, `Alert`, `FinancialGoal` are absent by name.** O5 §8 then defines a `goal` object while the pack defines `FinancialGoal` — a parallel definition of the kind pack 03 forbids. | **MEDIUM** | VERIFIED |
| **G-14** | **Seven of eleven objectives open no decision-register entries.** Only O1 (4), O2 (6), O3 (8) and O11 (8) do. O4–O10 open **none** — so O4's fifteen invariants, O7's regime authority and O10's causality guards are not registered as lockable decisions. | **MEDIUM** — an invariant nobody can cite by ID is hard to defend in review. | VERIFIED |
| **G-15** | **The governance pack is materially thinner than the objectives' citations imply.** 23 files, roughly two-thirds boilerplate by line count, self-labelled "CANONICAL CANDIDATE … implementation remains unverified," `review_before_commit`, three uncited E1 references (YNAB docs, OFX/FDX, NIST), no fixture code. Specifically absent despite being cited as established: **any reconciliation tolerance value** (05 step 6 says only "currency-specific exact/tolerance policy"), **any enumerated event-type registry** (13 names exactly one, inside an example), any field types or sign conventions, and any executable fixtures. | **MEDIUM** — where an O-doc says "the contract already specifies," that is true for the pipeline string, the eight reconciliation steps, the entity name list and the tenets, and generous for anything field-level, numeric or testable. | VERIFIED |

**No objective demands from O1 something O1 explicitly disclaims.** Checked clause by clause across all
ten dependents: every one asks O1 only for canonical state, freshness, reconciliation status,
unresolved exceptions, identity/relation outcomes and currency explicitness — all inside O1 §3 items
1–14. O1's disclaimer of causal inference from behavioral/recovery correlations is precisely what O10
§10 hardcodes. **The stack is internally well-behaved on this axis.** Its problems are ownership
overlaps (G-3 … G-8) and absent dependencies (G-2, G-9), not requirement violations.

---

## §2 Objective-to-contract cross-reference

Contract scopes are quoted from `contracts/pfos/_PFOS_CONTRACT_INDEX.md` and the contract headers
(**VERIFIED**). `O` = owns/claims the scope · `P` = partial · `—` = no claim · `!` = conflict.

| Objective | pfos 01 | pfos 02 | pfos 03 | pfos 04 | pfos 05 | pfos 06 | pfos 12 | pfos 14 | pfos 15 | C1 | C2 | C3 | C4 | C5 | C6 (DRAFT) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **O1** Truth | P | **O** | — | — | — | **O** | — | — | **O** | P | **O** | — | — | — | **O** | **EXTENDS, heavy overlap.** Four contracts already own it. |
| **O2** Protection | **O** | — | **O** | — | — | P | — | — | — | — | — | — | — | — | — | **EXTENDS.** pfos 01 owns obligation tiers P0–P3; pfos 03 owns obligation protection + risk engine. |
| **O3** Decision | P | — | **O** | P | — | — | — | — | — | — | — | — | — | — | — | **EXTENDS.** pfos 03 owns "purchase decision engine … decision outcome registry." |
| **O4** Capital | — | — | **O** | — | — | — | — | — | — | — | — | **O** | — | — | P | **EXTENDS + `!`.** pfos 03 owns "debt and capital allocation"; C3 owns the budget engine. G-7 unresolved. |
| **O5** Wealth | **O** | — | **O** | — | — | — | — | — | — | — | — | — | — | P | — | **EXTENDS.** pfos 01 owns "net-worth views"; pfos 03 owns "net-worth engine, macro engine." |
| **O6** Offloading | — | P | — | **O** | P | — | **O** | **O** | P | — | — | — | P | — | — | **EXTENDS + `!`.** pfos 14 owns the single window; pfos 12 owns scheduling/ops. G-3 with O1. |
| **O7** Regime | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | **GAP — no contract coverage.** pfos 01's "financial constitution" is doctrine, not a regime engine. |
| **O8** Longitudinal | — | — | P | — | — | P | — | — | — | — | — | — | — | P | — | **GAP, mostly.** C5 "Reports, Rescue Analytics" and pfos 06 retention touch it; no owner for windows/coverage/temporal provenance. |
| **O9** Merchant/Behavioral | — | P | **O** | — | — | — | — | — | — | — | — | — | — | — | — | **`!` CONFLICT.** pfos 03 explicitly owns **"leak and behavioural intelligence."** Two owners for the same scope. |
| **O10** Cross-Domain | — | — | — | — | P | — | P | — | — | — | — | — | — | — | — | **GAP — no contract coverage.** pfos 05/12 govern cross-agent signals, not cross-domain statistics. |
| **O11** Evidence Reasoning | P | — | P | — | — | — | — | — | — | — | — | — | — | — | — | **GAP, mostly.** pfos 01 has "confidence bands"; pfos 03 has "evidence packages." **pfos 08 Research is VERIFIED ABSENT** — the one contract that would own this was never authored. |

### 2.1 The answer to "does `FINANCIAL/` duplicate, extend, or contradict?" — per objective

**It extends, unevenly, and contradicts in two places.** Stated precisely:

- **Heavy duplication, openly credited — O1.** O1 §2.1 restates the governance pack's pipeline string,
  its three-sentence dedupe rule and its eight reconciliation steps almost verbatim and labels them
  `[FACT]`. It then extends materially: cross-channel SMS↔statement dedupe, scheduled Drive discovery,
  a persistence health check, a `calculation_receipt`/`state_use_receipt`, 22 acceptance criteria, a
  15-row test matrix, a 12-step migration. **This is the right behaviour** — cite the base, add the
  testable surface.
- **Genuine extension over a thin base — O2, O3, O4, O5, O11.** The pack's domain files are 2.5–7 KB
  each; the objectives are 32–48 KB. They add acceptance criteria, test matrices, migration
  strategies, required artifacts, dependency graphs and per-claim evidence labels that the pack has no
  equivalent of. **But the repository's PFOS 03 already owns the engines they specify**, and those
  engines are **implemented** (`src/features/safeToSpend`, `forecast`, `netWorth`, `decisions`,
  `obligations`, `budget`). So for these five the correct reading is: *the objectives are a
  specification layer over contracts and code that already exist*, not a request for new subsystems.
  **G-6 is the proof that this was not checked.**
- **Pure extension with no base at all — O7, O8, O10, and most of O9.** Four objectives have no pack
  counterpart and (for O7, O8, O10) no repository contract either. Six pack files' worth of governance
  is all that constrains them. These are the genuine new-capability objectives.
- **Contradiction 1 — O9 vs pfos 03.** `contracts/pfos/03` owns "leak and behavioural intelligence"
  by name. O9 claims merchant resolution, behavioral baselines, unusualness and **leakage candidates**.
  Two contracts, one scope. Must be adjudicated (**D-O**).
- **Contradiction 2 — Drive, three ways.** Pack 14 ("never live ledger," `strict_local` never syncs,
  no plaintext personal-data archives) vs O1 §8 (twice-daily discovery, readable financial context) vs
  `drive-db.md` steering (Drive *is* the canonical database). **Steering outranks both**, so this is
  the one place the new material cannot simply be layered on. **G-10, G-11, D-S.**
- **Numbering:** the pack's 00–22 and the objectives' O1–O11 are **not two schemes over the same
  material.** The pack is a document-type/domain decomposition with its own seven-phase roadmap
  (file 17); the objectives are an outcome decomposition with eleven "Owning phase" numbers that
  **already drift from** file 17's phases 0–6. Roughly six pack files are covered by an objective, at
  least six objectives have no pack counterpart, and **eight-plus pack files have no objective
  counterpart** — notably file 12 (agent roles/authority table), file 14 (approval ladder) and file 16
  (tamper requirement). If the objectives become the working authority, **those three must not be
  dropped.**

---

## §3 Where the transaction-capture pipeline plan sits in this stack

### 3.1 The pipeline plan is the O1 substrate — traced criterion by criterion

O1's 22 acceptance criteria against pipeline-plan segments S1–S12 (**VERIFIED** against both
documents). This is the requested sentence-level trace.

| O1 criterion | Pipeline-plan segment | Status |
|---|---|---|
| 1 exactly one canonical current-state writer | S10 single writer + §10 coherence; gated by **D-A** | **COVERED as a decision, failing today.** Plan F7 records two stores with no bridge. O1 criterion 1 is currently false. |
| 2 integer milliunits + explicit currency | `money-rules.md`; S5 resolution; S6 validation; AC07 | **COVERED.** Plan **F2** (currency discarded) is the live defect and S5 repairs it. |
| 3 re-importing identical evidence is idempotent | S2 evidence identity `(channel, idempotency_key)`; S7 fingerprint; record identity §5.1 | **COVERED**, and stronger than O1 asks: three independent mechanisms. |
| 4 legitimate same-amount/date not collapsed | S7 + §7 `DUPLICATE_AMBIGUOUS` ("two coffees") | **COVERED.** |
| 5 SMS + statement resolve to one economic event | S7 cross-channel fingerprint | **PARTIAL.** The matching is designed; **the SMS channel does not exist** (plan §1.2: notification parsers PROPOSED ONLY). Designed, unexercisable. |
| 6 pending + posted count once | S11 `pending_to_posted` linking; server `status` enum | **PARTIAL.** Linking is specified; the *count-once* rule is not stated at S12. |
| 7 card payments / internal transfers create no false expense or income | S10 transfer pair in one transaction; S11 "credit-card payment treated as a transfer, not an expense" | **COVERED.** Plan **F14** (imported transfers one-sided) is the live defect and S10 repairs it. |
| 8 refunds/reversals retain linkage | §7 `REFUND_AMBIGUOUS`; `transaction_links` correction | **COVERED** — staged and linked, never auto-netted. |
| 9 installment economics do not double count purchase and repayment | — | **ABSENT.** The plan never mentions installments. Pack 04 and O2 §9 both require it. |
| 10 FX retains original/settlement values, rate/date, fees | S5 says "no FX at ingest; store in own currency" | **PARTIAL/ABSENT.** Refusing capture-time conversion is correct (O1 and PFOS 15 §5.4 agree). **Retaining the settlement amount, provider rate/date and fees is not in the plan.** |
| 11 reconciliation closes exactly or within policy tolerance | S11 zero-milliunit tolerance, derived | **COVERED, and stronger.** The plan *derives* zero; pack 05 never states a number (G-15). |
| 12 unresolved mismatches stay exceptions, never averaged | S11 three verdicts, never averaged | **COVERED.** |
| 13 current-state responses expose freshness and reconciliation status | — | **ABSENT.** The plan has no freshness/as-of exposure requirement on any output. |
| 14 a stale historically correct balance is not presented as current | — | **ABSENT.** Same gap as 13. |
| 15 manual corrections outrank model inference, auditably | S9 owner promotion; S10 supersede; `audit_log` | **PARTIAL.** Owner primacy holds; the pack's six-rank **evidence hierarchy** is not modelled. |
| 16 historical corrections are superseding/append-only | S10 `supersede`, `audit_version`, no delete | **COVERED.** |
| 17 downstream agents cannot bypass canonical state via chat memory | §8.3 Hermes boundary; `AUTHORITY_KEY`; worker-branch-not-tool | **COVERED**, structurally. |
| 18 Drive-discovered evidence does not directly mutate canonical state | S1 → S2 (bytes → evidence, never direct) | **COVERED.** |
| 19 approved Drive persistence produces a write receipt and read-back | §5.6 canonical read-back; §10 mirror; **D-G** | **PARTIAL.** Canonical read-back is specified; *Drive* read-back sits behind D-G and plan **F6** (no `If-Match`). |
| 20 a failed Drive mirror is detectable | §10 preconditions F5/F6/F12 | **PARTIAL.** Named as preconditions, not as a health check. |
| 21 secrets absent from Drive-safe artifacts | AC09, AC18, steering | **COVERED.** |
| 22 deliberate tamper test proves verification detects a broken invariant | Increment 11 + §7 exception taxonomy | **COVERED.** |

**Score: 13 covered, 6 partial, 3 absent.** The pipeline plan is a *correct* first phase of O1 — every
one of its twelve segments maps onto an O1 scope item, and nothing in S1–S12 contradicts an O1 clause.
It is not a complete one.

### 3.2 The two structural absences — and why they are the most important finding here

O1 §15 lists twelve required implementation artifacts. The pipeline plan covers ten. **Two are absent,
and they are the two that every downstream objective binds to:**

**① The canonical `FinancialSnapshot` builder (O1 §5.7).** O1 requires "a versioned `FinancialSnapshot`
containing the current state references, as-of/freshness, unresolved items, calculation version, and
policy version," of which "exactly one … is canonical for a given snapshot/calculation/policy version."
It is **absent from `src/`** (zero `FinancialSnapshot` matches) and **absent from the pipeline plan** —
S12 recomputes derived values on demand but produces no versioned snapshot object.

**② The state-use / calculation receipt (O1 §10, `[INFERENCE]`: "should later become a shared
`calculation_receipt` or `state_use_receipt` schema consumed by O2+ objectives").** Also absent from
both.

**Why this is decisive.** Every one of O2–O11 binds to these two artifacts by name:

- `canonical_state_version` is a required field in O2's liquidity protection object, O3's
  `decision_packet`, O4's `allocation_proposal`, O5's `wealth_trajectory` and `wealth_recommendation`,
  O6's `financial_brief` and `financial_refresh_proof`, O7's `financial_regime_state` and
  `regime_computation_receipt`, O8's `longitudinal_analysis`, O9's `merchant_intelligence_snapshot`,
  O10's `decision_context_packet` (`financial_snapshot_id`), O11's `decision_evidence_packet`.
- O3 §7.1's **truth gate** requires "canonical state ID/version; account freshness state;
  reconciliation status; unresolved high-impact exceptions; currency explicitness" — which is
  precisely the snapshot's field list.
- Every objective's acceptance criteria include a computation-proof requirement, which is the receipt.

**So: without the snapshot and the receipt, O2 is not buildable — and neither is anything above it.**
The pipeline plan builds the *ledger*; O2–O11 consume the *snapshot over* that ledger and the *receipt
proving which snapshot was used*. Those are the interface, and they are missing from both the code and
the plan.

This is the answer to the commissioning question. The pipeline plan is **a correct first phase, not an
accidentally-scoped fragment** — its twelve segments are O1's pipeline, its exception taxonomy is O1's
truth-state model, its zero tolerance is stronger than the pack's. But it stops one layer short of the
interface the other ten objectives were written against. **Closing that gap is the whole content of
Phase 1b below, and it is small: two artifacts, both derivable from work S1–S12 already does.**

### 3.3 What each objective still needs once the pipeline plan is fully built

Assuming increments 0–11 land and D-A resolves to the server tier:

| Objective | Met by the pipeline plan | Still missing before it is buildable |
|---|---|---|
| **O1** | S1–S12, 13 of 22 criteria | Snapshot builder; state-use receipt; installment relation; FX settlement retention; freshness/staleness exposure. **Phase 1b.** |
| **O2** | Canonical truth, reconciliation, exception taxonomy, `audit_log` | Snapshot + receipt (§3.2); alert store with lifecycle `OPEN → ACKNOWLEDGED\|SNOOZED → RESOLVED`, dedupe/cooldown; protection exception queue; severity engine. **Blocked on O15 for the protected floor** — O2 §8 forbids inventing it. |
| **O3** | Reconciled truth; the existing append-only `decisionRegistry` | Snapshot + receipt; `decision_packet`; the five gates; recommendation-label enum. **Blocked on O7 (regime), O15 (floor), O28 (materiality)** per O3's own open items 3–6. **G-7 must be resolved to sequence against O4.** |
| **O4** | Reconciled truth; existing `computeBudget` | Snapshot + receipt; `allocation_proposal`; `allocation_event` (append-only, versioned); capital-pool classification. **Blocked on O7, O15, O28.** |
| **O5** | Net worth, FX ratios, assets/macro collections | Snapshot + receipt; `goal` (reconciled against pack `FinancialGoal` — G-13); `wealth_trajectory`; realized/unrealized taxonomy; **an asset-valuation source (G-6 ③)**. **Blocked on O7, O16.** |
| **O6** | `scheduler.ts` single clock; `workQueueRepo`; `liveness` | Snapshot + receipt; 11 new objects; brief composer; open-loop ledger. **Blocked on D-B (transport) for the owner-facing half, and on G-3 for Drive-discovery ownership.** |
| **O7** | Nothing | Everything, **plus its own nine `[MISSING]` numeric decisions** — thresholds, hard gates, dwell, weights, success bars. A contract must author those before code. |
| **O8** | `getIndex().byMonth`, `ageOfMoney`, `netWorthSeries` | Everything. **Plus G-4/G-5 must be settled first**, and O8 §23's parallel join contract reconciled with O10. |
| **O9** | `normalizePayee`; `Payee` registry | Everything, **and the canonical `Merchant` entity it is required to reuse does not exist** (G-13). **D-P** decides the external-enrichment question. |
| **O10** | Nothing | Everything. **D-Q** decides the cross-domain data boundary; **blocked on HIMAYAH v2** (O10 §26 forbids claiming the Trusted-Boundary behaviour before the contract is updated). |
| **O11** | Nothing | Everything, including a **net-new claim/evidence/weight/confidence schema** (**D-R**, a migration). **Blocked on O16/O17** for the external evidence plane. |

---

## §4 Blocking owner decisions — continued from the pipeline plan

**D-A through D-K are inherited verbatim from `nizam-transaction-capture-pipeline-plan.md` §3 and are
not restated or re-litigated here.** Where an objective depends on one, §3.3 names which. New letters
only where an objective introduces a choice the pipeline plan never touched.

### 4.0 F7 is RELEASE-BLOCKING — the highest-priority finding in this program

**Escalated 2026-09-20. This is not a recommendation and it is not waivable.**

F7 is the two-canonical-stores defect: the browser Drive-JSON projection and the server tier both behave
as canonical, with no bridge and divergent corrections. It was recorded as a finding. It is now a
**release-gate failure**, by the canonical contract's own machinery:

- **v1.3 FINAL §43** requires *one authoritative writer per canonical domain*, and assigns the financial
  ledger to the PFOS deterministic ledger service — with the dashboard and every conversational surface
  as **non-authoritative consumers**.
- **AC-48** states it as a testable criterion: *"No two services can independently become authoritative
  writers for the same canonical domain."*
- **§54 places AC-48 inside release gate RG-5**, and the pass rule for every gate is *"ALL mapped
  criteria pass; **no waived gate in final release**."*
- **§54.2** forbids the escape hatch explicitly: *"No acceptance criterion may be silently skipped,
  weakened, or reworded to make an implementation pass."*

**Exactly what F7 gates, enumerated so it cannot be argued around:**

| Gated | Why |
|---|---|
| **VPS deployment** | Deploying makes the server tier live while the browser tier still writes canonically. That does not fix the split — it ships it. |
| **The Slack cutover** | A transport carrying financial state implies a single canonical state behind it. Cutting over first means choosing which store the owner is being told about, silently. |
| **Any Hermes message carrying a real figure** | Including the daily brief. A figure drawn from one of two disagreeing stores is unciteable, which is the precise failure O8 §29, O9 §49, O10 §29 and O11 all forbid. |

**What it does NOT gate:** local development, every increment on the pipeline board, the snapshot and
receipt design, and anything behind injected ports with deterministic mocks (**D-B(c)**). The finance
pipeline can be built to completion under F7. It cannot be *released* under F7.

**Relationship to D-A.** D-A is ANSWERED (a) — server `finance.db` canonical. F7 is what remains
**unexecuted** about that answer. So this escalation changes no decision; it changes the cost of not
acting on one, from "architectural debt" to "cannot ship."

### 4.0b F-SCOPE-1 — a domain-scoped Drive search missed the statement corpus entirely

**Severity: HIGH (methodological). VERIFIED 2026-09-20.**

A prior pass concluded "no statement corpus was located" and re-derived **D-Y** on that basis. The
conclusion was false and the mechanism is worth recording, because it will recur: the search was scoped
to `47_NIZAM/05_FINANCE`, and the statements live at the **Drive ROOT** in `CIB` and `HSBC` folders. A
domain-scoped search cannot find a root-level artifact, and **absence of a search result was reported as
absence of the artifact.**

The Knowledge Map anticipated exactly this. Its retrieval order says to *"Search My Drive root only for
explicitly recorded exceptions"* — and these statements are precisely such an exception, which **has
never been recorded**. So the index is incomplete in a way that makes the corpus invisible to anyone
following the index correctly.

**Proposed, NOT performed** (no Drive write is authorized in this program): record the `CIB` and `HSBC`
roots as explicit root exceptions in the Drive index, alongside the `BANKING` and `BADAN`
permission-blocked exceptions it already lists. Until that happens, any Drive claim scoped to a domain
folder must state its scope, and **"not found" must be written as "not found within scope X"**.

| # | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| **D-L** [ANSWERED 2026-09-20] | **What is the authority status of `FINANCIAL/O1..O11`?** They are owner-approved as *objectives* (ladder rank 2, "newest explicit owner direction") yet are **untracked**, stamped "implementation not yet verified," and cite an absent rank-3 parent (G-1, G-2). | (a) Track them under `contracts/programs/` as a named program; treat as **direction that must be decomposed into contracts**, never as contracts themselves. (b) Promote each to a numbered contract as its phase begins. (c) Leave untracked; treat as evidence only. | **(a) now, (b) per objective at its phase boundary.** Grounds: it matches the precedent `contracts/programs/SEVEN_CONTRACT_RECOVERY.md` already sets for a namespaced workstream; it makes the objectives citable and version-controlled without asserting eleven new contracts at once; and it respects `two-agent-vps.md` §5 ("author the contract before building its area") by deferring contract status to the moment the area is built. **(c) is unsafe**: untracked authority cannot be reviewed or diffed. Note that (a) adds files to the working tree, which interacts with **D-H**. | **Everything in §5.** No phase can begin while its governing document's authority is undetermined. |
| **D-M** [OPEN - `None offered`, owner-only — **NARROWED 2026-09-20**, see `nizam-drive-truth-inventory.md` §5.1] | **PFOS v1.3 FINAL / LOCAL_FULL** — rank 3 of every precedence ladder. **No longer "absent": located on Drive, retrieved, read in full, hashed** (alias `DOC-PFOS-V13-FINAL`, 2026-08-13, 4,634 lines, SHA-256 `2766e17b…e80d` over the exported bytes). G-2 was accurate about the *tree*, not about *Drive*. **But what exists is the `DRIVE_SAFE` mirror, which declares itself non-canonical** — its header, §42.3, §55.4 and C-15 all say *"The LOCAL_FULL sibling remains canonical when the two differ."* **`LOCAL_FULL` is not on Drive**: a 32-hit search of the knowledge root returned no such variant, so it is local-only by design and **cannot be produced from Drive by any means available to an agent.** | (a) Produce it and record its index and hash. (b) Formally strike or annotate rank 3 across the pack and the objectives, recording that the ladder operates without it — **now re-stated as: annotate rank 3 as served by a self-declared mirror, canonical sibling outstanding.** (c) Leave as is. | **`None offered` on (a)** — only the owner knows whether `LOCAL_FULL` exists to be produced. **(a) is now half-satisfied**: a substantive rank-3 document and its hash exist, and the mirror is usable as strong evidence of owner intent. **The ladder is NOT declared satisfied** — recording a mirror's hash and calling rank 3 populated is exactly the unfalsifiable-rank defect this decision was opened to name. **If `LOCAL_FULL` cannot be produced, (b)**, which is now cheap and honest. **(c) remains the defect.** | Any claim that an objective is or is not subordinate to its declared parent. Does **not** block §5 work if (b) is taken. **Newly relevant:** F-DRIVE-4 — the retrieved mirror ranks itself above the repository's contracts and omits `.kiro/steering` from its ladder entirely. Settling D-M now also means settling whether that ladder or the repository's own (steering → contracts → docs) governs. |
| **D-Z** [OPEN — recommendation offered 2026-09-20] | **Where does a foreign-exchange rate live?** `FIN-O1` acceptance criterion 10 requires multi-currency handling; the repository has EGP milliunits and no FX representation. **v1.3 FINAL does not settle it** — read in full, it carries no rule about FX storage, versioning, reference currency, or whether a converted amount may be persisted. Its only normative FX statement is negative (§41.1 forbids an LLM from sourcing a currency conversion), and its §17 backlog lists *"reliable FX sources"* and EGP purchasing-power methodology as **Priority A prerequisites**, i.e. explicitly unsettled. | (a) Add FX columns to `transactions`. (b) Retain the source-supplied rate on `source_events.raw_payload` and derive on read. (c) Defer entirely. | **(b).** The captured rate is *evidence*, and `source_events` is already the immutable evidence surface — so nothing is persisted that can drift from the ledger, no migration is required, and the derived figure carries its own as-of date. It also matches §41.1: conversion happens inside the deterministic engine while the stored fact stays the source's. **(a) is rejected** because `assertMonetaryCoverage` is bidirectional, so a new monetary column forces a coordinated change across every write path for a capability nothing consumes yet. **(c) is rejected** because criterion 10 is an acceptance criterion, not an aspiration. | `FIN-O1` criterion 10, and Increment 5 of the `financial-snapshot-interface` board. Nothing else. |
| **D-X** [OPEN — opened 2026-09-20, **the letter's ONLY meaning; the FX question is now D-Z**] | **Does the external PDF→CSV pipeline become the statement channel's S1–S3, or does NIZAM build its own statement adapter?** An external pipeline has already turned ~30 statement PDFs into **1,216 rows** matching the 25-column `master_ledger` schema exactly, deterministically (`pdftotext-layout`, not OCR, not a model), covering all twelve months of 2025-07 to 2026-06. Adopting it would satisfy S1–S3 for the statement channel **today**. But it carries four defects that NIZAM's own layers would have to repair rather than trust: `confidence_score` is the **constant string `medium` on all 1,216 rows** (so per-row confidence is not a signal at all — it is a placeholder); **245 rows (20%) are `Uncategorized`**; **514 rows (42%) are `Transfers`**, never checked against NIZAM's transfer-pairing logic; and **0 rows are flagged `is_duplicate`** by that pipeline's own dedup, never checked against NIZAM's two layers. | (a) Adopt its CSV output as the statement channel's S1–S3, treating every one of its own judgement columns as UNVERIFIED and re-deriving them through S4–S7. (b) Treat it as evidence only and build a NIZAM statement adapter from the PDFs. (c) Adopt it wholesale, including its confidence, category and duplicate columns. | **(a).** Grounds: the extraction is the expensive, deterministic, already-done part, and re-implementing PDF text extraction buys nothing — but its *judgements* are exactly what NIZAM's layers exist to make, and a constant `medium` confidence is the clearest possible evidence that they were not really made. So take the rows, re-derive the verdicts. **(c) is unsafe** and would import a 42%-transfer classification and a zero-duplicate claim as truth. **(b) is wasteful** unless (a) proves the extraction itself unreliable. **Note the interaction:** (a) means the rows enter through the **CSV boundary**, which is **D-C's** subject — so D-C and D-X should be answered together. | Increment 1's statement channel. Also gates **R4** and **R5** on the readiness matrix, because both are claims this pipeline makes and NIZAM has not verified. |
| **D-Y** [OPEN — recommendation offered 2026-09-20] | **D-I's ingestion source order is wrong for the evidence that actually exists.** D-I set **statements → SMS → OFX-if-offered** on the reasoning that a statement is the most structured source. **CORRECTED 2026-09-20 — the premise this row was first opened on was FALSE.** The earlier claim "no statement corpus was located" was a **search-scope failure, not a fact**: the statements live at the **Drive ROOT** (`CIB` and `HSBC` folders), not under `47_NIZAM/05_FINANCE`, so a domain-scoped search could not see them. The true inventory is: **~30 statement PDFs** across accounts 5411, 8071 and a debit account, **already deterministically extracted** by an external pipeline into **1,216 normalized 25-column rows** spanning 2025-07-01 to 2026-06-04 with all twelve months populated, `extraction_method = pdftotext-layout` (not OCR, not a model); **254 SMS messages covering ONE month** (2026-07-25 to 2026-08-26); manual entry, implemented and live; and **no confirmed OFX source anywhere.** And v1.3 FINAL §27.6 **J4 makes statement reconciliation the matcher, not the first source** — it arrives later and matches the "provisional entries" J2 already created from raw events. | (a) Keep statements-first. (b) Resequence to SMS-first, statements as the reconciliation source. (c) Build both adapters before exercising either. | **(a) — D-I's ORIGINAL ORDER SURVIVES THE CORRECTED PREMISE, and the earlier (b) recommendation is WITHDRAWN.** The reasoning that produced (b) was "SMS is the only corpus", which was false. On the true inventory, statements win on every axis that matters: **12 months of coverage against 1 month**; **1,216 rows already deterministically extracted** against a Google Doc of prose whose adapter input shape is still unresolved; and a structured 25-column schema against free text needing a marker-vocabulary parser. **Do not conflate ROLE with PRIORITY.** v1.3 FINAL §27.6 J4 makes statements the *matcher* in reconciliation — that is a statement about what statements DO once a candidate exists, not about which corpus is ingested first. A matcher with nothing to match is idle; a matcher fed 12 months of extracted rows is the fastest route to a reconciled ledger. **(b)** would start with the thinner, harder, less structured corpus. **(c)** doubles Increment 1's surface for no earned confidence. **The SMS corpus is not discarded** — it is the right SECOND channel, because it covers a month the statements do not reach and because its declines, pre-authorizations and reversals exercise exception paths statements never will. | Increment 1's **adapter choice only**. **Does not touch D-C**, which remains the separate question of whether the CSV cutover happens at all — though note the two now point the same way, since the already-extracted rows arrive as CSV. |
| **D-N** [ANSWERED 2026-09-20] | **G-6: three "unowned" capabilities are in fact owned by `contracts/pfos/03` and implemented in `src/features/`.** Safe-to-spend, forecasting methodology and the net-worth engine. | (a) Record the correction: pfos 03 + existing code own them; the objectives consume, and must cite them rather than defer to unwritten O15/O12. (b) Treat the objectives' deferral as authoritative and build new engines under O15/O12. | **(a), firmly.** Building a second safe-to-spend or forecast engine because an objective document did not check the repository is exactly the second-source-of-truth failure all eleven objectives forbid. This correction should be recorded through the established channel — `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md`. **Note the residual:** the *protected-floor formula* genuinely is unowned (O15), and **asset valuation** genuinely is unowned (G-6 ③, no asset entity in the pack, no valuation engine in `src/`). Those two remain open. | O2, O3, O4, O5 — all four consume at least one of these. |
| **D-O** [ANSWERED 2026-09-20] | **O9 vs `contracts/pfos/03` — "leak and behavioural intelligence" has two owners** (G-9 in §2.1). | (a) pfos 03 keeps the engine; O9 becomes its specification and test surface. (b) O9 supersedes pfos 03 for this scope, recorded as an amendment. (c) Split: pfos 03 keeps leakage, O9 takes merchant identity/recurrence. | **(c).** Merchant resolution, aliasing and recurrence are genuinely new and have no pfos owner; "leak and behavioural intelligence" is pfos 03's by name. A clean split avoids both a supersession and a duplicate. | O9 Phase 9. |
| **D-P** [ANSWERED 2026-09-20] | **Does O9 require an external merchant-enrichment source, and is that in scope given `product.md`'s non-goals?** O9's resolution precedence works entirely from owner evidence (owner rule → verified mapping → historical pattern → statement metadata → model suggestion → UNKNOWN); external research is **conditional** ("permitted when internal evidence is insufficient and the identity materially affects analysis") against a six-tier source hierarchy. | (a) Own-evidence only; refuse external enrichment. (b) Conditional external research per O9 §10/§29 with provenance. (c) Standing external directory integration. | **(a) for the first increment, (b) later behind its own approval.** Grounds: `product.md` lists "real-time bank API/open-banking" as a v1 non-goal and the privacy tenet is that the data belongs to the owner; O9 is *designed* to work without external calls; and (b) requires an egress path that pack 14 classifies as an egress event needing HIMAYAH classification. **(c) is out of scope.** | O9 only. It is the extension point, not the core. |
| **D-Q** [OPEN - `None offered`, owner-only] | **O10's cross-domain data boundary.** It names FINANCIAL, WEARABLE, JOURNAL, DECISION, WORKLOAD, EXTERNAL and the pillars MAL, BADAN/WHOOP, YAWMIYAT, QARAR, MARSAD, THABAT, with `sensitivity_class: trusted_private\|trusted_sensitive\|strict_local\|other`. | (a) Out of scope until a **HIMAYAH v2 contract exists and is runtime-verified**. (b) In scope for wearable + journal now, under bounded per-question retrieval. (c) Full cross-pillar scope. | **(a).** This is not caution for its own sake: **O10 §26 itself says** the Trusted-Boundary direction "must not be represented as deployed until the governing HIMAYAH contracts are formally updated and runtime-verified," and `two-agent-vps.md` §4 invariant 4 excludes `strict_local_maximum` family data from the deployment entirely. Taking (b) before the contract exists would be the objective's own violation. | O10 Phase 10 in full. |
| **D-R** [OPEN] | **O11 requires a claim/evidence/weight/confidence schema that does not exist** — `evidence_weight_receipt` (with `final_strength_class` and `confidence_class`) and `confidence_profile` (7 dimensions + `contradiction_burden` + `overall_class`), plus twelve new objects. A migration. | (a) Approve as a migration when Phase 11 begins. (b) Reduce to a minimal `confidence_class` on existing records. (c) Defer O11 indefinitely. | **(a), with one constraint carried from code:** `src/lib/ledger/ledger.types.ts` deliberately refuses band→score conversion ("A band is not a score and converting one into the other invents precision that was never measured"). O11's `*_class` enums must be **bands, not scores rendered as bands** — which happens to match O11 §13's own rule that the LLM may not invent a numeric weight. Also settle **G-5** first: if O11 owns confidence, O8/O9/O10 must defer to it explicitly. | O11; and via G-5, the confidence model of O8/O9/O10. |
| **D-S** [ANSWERED 2026-09-20] | **Drive's role, three-way conflict** (G-10, G-11). `drive-db.md` steering says Drive *is* the canonical database; pack 14 says "never live ledger"; O1 §8 says durable evidence/recovery mirror with readable financial context and twice-daily discovery. | (a) Amend `drive-db.md` to the Profile-A framing `tech.md` D1 already states, making Drive the mirror and the server tier canonical. (b) Keep `drive-db.md` as written and reject the pack/O1 framing. (c) Defer. | **(a)** — and note this is **the same question as D-A arriving from a second direction**, so it should be answered once, not twice. Grounds: `tech.md` D1 already says the Drive-JSON store "is the Profile-A build, NOT the final database"; pack 14 and O1 §8 both agree; `drive-db.md` is the outlier. **Steering outranks everything here, so the amendment must be made in steering before any objective relies on the new framing.** Separately: the **readable-financial-context expansion** (G-10) is its own sub-decision and must be recorded where pack 01 requires — in artifact 22 — which has not happened. | O1's Drive half, O6's discovery, O8/O9/O10/O11's mirrors, and pipeline-plan §10. |
| **D-T** [ANSWERED 2026-09-20] | **G-7: O3↔O4 dependency direction.** O4 says O3 is upstream; O3 does not acknowledge O4; O4 §22.5 implies both. | (a) O3 upstream of O4 (decision packet feeds allocation). (b) O4 upstream of O3 (allocatable capital feeds decisions). (c) Bidirectional through a typed interface, with no cycle in the build order. | **(b) for build order, (c) for runtime.** Grounds: O4's own doctrine §4 steps 1–5 computes allocatable capital *before* any decision comparison, and O3 §7.1's truth gate needs a capital figure it does not compute. So capital is the input and the decision is the consumer; at runtime a decision may then request a re-allocation, which is the (c) edge. **Also resolve the duplicated opportunity-cost object** (O3 `opportunity_cost_refs` vs O4 `opportunity_cost_ref`) in the same decision. | Ordering of Phases 3 and 4. |
| **D-U** [ANSWERED 2026-09-20] | **G-8: briefing content ownership.** O6 owns briefing orchestration; O7 concedes; **O5 §29 does not** and prescribes the content of the same three windows. | (a) O6 owns the brief; O5 §29 is restated as "fields O5 supplies to O6," matching O7 §28's pattern. (b) O5 keeps authorship of the strategic section. | **(a).** O6 §13 already makes `financial_brief.trajectory_ref` a *reference*, which is the correct shape; O5 §29 just needs rewording, and its "quarterly review reassesses regime" line should drop "reassesses" since O5 §7.5 concedes regime authority to O7. | Phase 5 and Phase 6 content boundaries. |
| **D-V** [OPEN - `None offered`, owner-only] | **G-9: twenty-one forward-referenced objectives are not supplied**, six load-bearing (O15, O16, O28, O19, O22/O27, O34/O35). | (a) Author the six load-bearing ones before the phases that consume them. (b) Author all 21. (c) Build the eleven and stub the interfaces. | **(a).** Grounds: each objective already self-guards ("Until O15 exists, O4 must not invent a number"), so stubs are honest — but a stub cannot supply a protected-floor *value*, and O2/O3/O4/O5/O7 all need one. **(c) alone will strand Phases 2–5 at "designed, unbuildable."** `None offered` on the ordering among the six: that is a scope call. | Phases 2 onward, each on a different subset. |
| **D-W** [ANSWERED 2026-09-20] | **G-4/G-5/G-14: one shared receipt and confidence base, or N per objective?** Seven receipt schemas and four confidence models are specified; O29 is named as owner by four objectives and does not exist; O4–O10 open no decision-register entries at all. | (a) Author one shared `computation_receipt` base + one `confidence_profile` now, under O11/O29, and require every objective to extend rather than redefine. (b) Let each objective define its own and reconcile later. | **(a).** Seven near-identical receipt tables is the schema-duplication equivalent of the second-ledger problem these documents exist to prevent, and reconciling after implementation means migrating live data. Pair it with a rule that **each objective opens decision-register entries for its own invariants** (G-14), so O4's fifteen invariants and O10's causality guards become citable IDs. | Every phase from 2 onward. Cheapest to fix first. |

---

## §5 Phased roadmap, O1 through O11

**Phase 1 is the pipeline plan's own increment set 0–11, unchanged.** Those eleven increments stay
exactly as written in `nizam-transaction-capture-pipeline-plan.md` §11 and are not restated, renumbered
or edited here. This section adds **Phase 1b and Phases 2–11**.

**Sequencing rule.** The objectives declare a cumulative dependency chain ("O*n* consumes … from O1 …
O*n-1*"), so phases run in order and are **not** parallelized across a declared dependency. Phase
numbers track objective numbers for legibility. **One exception to execution order:** if **D-T**
resolves as recommended, **Phase 3 (O4 Capital) is built before Phase 4 (O3 Decision)**, because
allocatable capital is an input to decision comparison and not the reverse. The phase *numbers* stay
tied to the objectives; only the build order swaps.

**This section sequences. It does not design.** Modules are *named*, not specified. Each objective gets
its own plan-and-design cycle at its phase boundary, and `two-agent-vps.md` §5 requires its governing
contract to exist first.

| Phase | Targets | Requires from every earlier phase | Net-new modules (named only) | Blocked by |
|---|---|---|---|---|
| **1** | **O1 substrate** | — | The pipeline plan's own eleven increments. | D-A, D-C, D-E (hard), D-H; plus D-B/D-D/D-G/D-I/D-J/D-K |
| **1b** | **O1 interface — the §3.2 gap** | Phase 1 complete | `financialSnapshot.ts` (versioned snapshot builder: state refs, as-of/freshness, unresolved items, calculation + policy version, exactly one canonical per version triple) · `stateUseReceipt.ts` (the shared `calculation_receipt`/`state_use_receipt` O1 §10 names and O2–O11 all bind to) · installment relation matcher · FX settlement-retention fields (original + settlement amount, provider rate/date, fees) · freshness/staleness exposure on every current-state output | **D-A** (which tier holds the snapshot), **D-W** (one receipt base, not seven), **D-M** if the ladder must be repaired first |
| **2** | **O2 Protection** | 1, 1b — snapshot + receipt are the gate | Protection exception queue · alert store with lifecycle `OPEN → ACKNOWLEDGED\|SNOOZED → RESOLVED` + dedupe/cooldown/snooze · severity engine (P0–P3) · obligation-completeness check · fee/penalty detector · delayed-income trigger · protected-floor **interface** (not the formula) · post-override recalculation | **D-V (O15 for the floor)** — O2 §8 forbids inventing it; D-N; D-W |
| **3** | **O4 Capital** *(built before Phase 4 if D-T resolves as recommended)* | 1, 1b, 2 | `allocation_proposal` · `allocation_event` (append-only, versioned) · capital-pool classifier (`protected\|allocatable\|contingent\|restricted`) · allocatable-capital engine · rollover/sinking-fund engines · opportunity-cost comparator (**one**, shared with O3 per D-T) | D-T, D-V (O15, O28), D-N; must not read `MonthBudget.activity`/`.available` (F16) |
| **4** | **O3 Decision** | 1, 1b, 2, 3 | `decision_packet` · the five prerequisite gates (truth, protection, forecast, research, human authority) · recommendation-label enum · option generator · challenge/override handoff contract · decision ledger event types | D-T, D-V (O7, O15, O28, O19/O23/O25 — O3's own open items 3–6), D-N |
| **5** | **O5 Wealth Growth** | 1, 1b, 2, 3, 4 | `goal` (**reconciled against pack `FinancialGoal`**, G-13) · `wealth_trajectory` · `wealth_recommendation` · realized/unrealized/forecast/counterfactual taxonomy · **asset-valuation source** (G-6 ③, genuinely unowned) | D-V (O7, O16), D-N ③, D-U |
| **6** | **O6 Cognitive Offloading** | 1, 1b, 2, 3, 4, 5 | `financial_open_loop` ledger · `financial_brief` composer · `financial_refresh_proof` · `drive_discovery_receipt` · `attention_queue_item` · `owner_schedule_profile` · `persistence_exception` · review-packet manifests — all as **consumers of the existing `finance` tick**; `scheduler.ts` unmodified, `SCHEDULER_TARGETS` unchanged | **D-B** (transport, for the owner-facing half), **G-3/D-S** (Drive-discovery ownership), D-U |
| **7** | **O7 Regime Management** | 1–6 | `financial_regime_state` · `regime_period` (append-only history) · deterministic classifier · hysteresis/dwell policy · hard-gate policy · transition explanation artifact | **Its own contract first** — O7's nine numeric decisions are all `[MISSING]`, and `two-agent-vps.md` §5 forbids building an ungoverned area. D-V (O15, O16) |
| **8** | **O8 Longitudinal Intelligence** | 1–7 | Window registry (17 windows) · `historical_coverage` · `forecast_evaluation` · `longitudinal_analysis` (with `supersedes_analysis_id`) · trailing-window engines | **D-W** (receipt + confidence base) and **G-5** must land first; O8 §23's parallel join contract must be subordinated to O10's gates before O10 exists, not after |
| **9** | **O9 Merchant & Behavioral** | 1–8 | `Merchant` **canonical entity first** (G-13 — it does not exist) · `merchant_alias` · `merchant_relationship` · `recurrence_series` · `behavioral_baseline` · `unusualness_signal` · `leakage_candidate` · review queue | **D-O** (split with pfos 03), **D-P** (external enrichment) |
| **10** | **O10 Cross-Domain** | 1–9 | `cross_domain_evidence` · `decision_context_packet` · hypothesis registry · `association_result` (with `causal_claim_allowed: false`) · `signal_eligibility` state machine · method registry | **D-Q — hard block on a runtime-verified HIMAYAH v2 contract**, per O10 §26's own words |
| **11** | **O11 Evidence-Based Reasoning** | 1–10 | `claim` · `evidence_item` · `independence_analysis` · `freshness_policy` · `contradiction_record` · `assumption` · `missing_evidence_item` · `weak_signal` · `expectation_signal` · `research_request` · `confidence_profile` · `evidence_weight_receipt` | **D-R** (migration), **D-W**/G-5 (O11 must be the confidence owner or not), D-V (O16/O17) |

**Three observations about this sequence that matter more than the table.**

1. **Phase 1b is the cheapest high-value work in the entire roadmap.** Two artifacts, both derivable
   from what S1–S12 already computes, and they unblock **all ten** remaining objectives. Nothing else
   in this document has that ratio.
2. **Phases 2–5 are each blocked on an objective that does not exist** (O15 for the floor, O28 for
   materiality, O16 for macro). That is **D-V**, and it is the real schedule risk — not implementation
   difficulty. Four phases of specification work cannot begin because six upstream objectives were
   never written.
3. **Phase 7 (O7) inverts the usual problem.** Every other objective's gap is missing code. O7's gap is
   a missing *policy*: its thresholds, hard gates, dwell periods, signal weights and success bars are
   all `[MISSING]` **in the objective document itself**. Code cannot be written against it at all until
   a contract supplies numbers, and O7 §9 explicitly forbids inventing them conversationally.

---

## §6 Continuous-research protocol

This document is not a one-shot artifact. The codebase and `FINANCIAL/**` both keep changing, and every
row in §1 is a claim about a moving target.

### 6.1 Revision discipline — identical to the pipeline plan's

Every time a claim in this document is checked against source and found wrong or incomplete, that is a
**numbered revision with a §-changelog entry** citing what changed, what it was, and why — exactly as
`nizam-transaction-capture-pipeline-plan.md` §14 does. That plan's Revision 2 is the worked example:
one over-claim corrected (F17), one "new" mechanism demoted to "already exists" (§5.1), one researched
risk found already mitigated, five findings added, two decisions added.

Rules carried over unchanged:

- **Never silently fix a claim.** A corrected row gets a changelog line. A reader must be able to see
  what this document used to assert.
- **Label every state claim** VERIFIED / UNVERIFIED / STALE / INACCESSIBLE. A row with no label is a
  defect in the row.
- **A documented status is not fresh verification.** Re-read the file.
- **Never invent an owner decision.** `None offered` stays `None offered`.

### 6.2 Re-verification triggers — when this document must be re-checked rather than trusted

**Mandatory re-verification of the affected rows:**

| Trigger | What to re-verify |
|---|---|
| Any change under `contracts/pfos/**` or `contracts/CONTRACT_*` | §2 matrix in full; the affected §1 rows; D-N and D-O |
| Any change under `FINANCIAL/**` | §1 in full; §0b precedence finding; G-12; the affected §4 decisions |
| Any migration — `src/server/db/migrations.ts` or `src/lib/db/schema.ts` | §1 status column; G-13 entity inventory; D-R; D-W |
| Any new file under `src/features/**` | The §1 capability probes (the identifier searches in §1) |
| Any change to `.kiro/steering/*` | §0.2 authority order; G-11; D-S |
| An answer to any of D-A … D-W | Every row and phase that cites that letter |
| PFOS v1.3 FINAL being produced | §0b in full — the entire precedence finding is conditional on its absence |

**Fixed cadence, regardless of triggers:** **before any Phase 2+ increment starts, re-verify every §1
row against current source.** Not a summary — re-run the capability probes and re-read the cited files.
A phase that begins from a stale §1 row is building against a status that may have changed underneath
it, which is the failure mode this whole document exists to prevent.

### 6.3 Where external research will be warranted — a forward list, not work done now

The pipeline plan's annex set the precedent: SQLite write-concurrency literature grounded D-A(a); the
transactional-outbox pattern named the mechanism its §5.5 was describing; OFX/FITID research changed
the D-I format recommendation. The same discipline applies to the objectives below, **when their phase
is actually planned** — not speculatively here. Use the `nizam-docs-research` skill and public fetch
tools at that point, and record URL, retrieval date, version and limitations.

| Phase | Objective | What will need external grounding | Why it cannot be invented |
|---|---|---|---|
| 2 | O2 | Alert fatigue / notification-cadence research; severity-ladder practice in operational monitoring | O2's own AC 13 forbids escalating severity "merely to gain attention"; a defensible ladder needs a source |
| 3 | O4 | Envelope-budgeting and rollover practice (the pack cites YNAB product docs as its only E1 source for this); sinking-fund and overspend-handling precedent | Pack 06 is 3 KB and states no rollover arithmetic; G-15 |
| 4 | O3 | Decision-analysis practice: option framing, reversibility/option value, close-call handling without false precision | O3 §2.1 prohibits the word "optimal" unless objective and constraints are explicit — that rule needs a methodology behind it |
| 4, 8 | O3, O8 | **Forecasting methodology and calibration** — scenario construction, horizon limits vs evidence density, forecast-error scoring | O1 and O2 both disclaim forecasting methodology; **pfos 03 owns the engine** (D-N), but its calibration method is not specified anywhere |
| 5 | O5 | Real-vs-nominal wealth measurement under high inflation; purchasing-power framing; concentration/fragility metrics | O5 §6 forbids inventing a composite score and §17 forbids an unvalidated "optionality score" — both need published method |
| 7 | O7 | **Regime-classification methodology** — state classification over financial time series, hysteresis/dwell design, anti-flapping | O7's nine numeric decisions are `[MISSING]` and §9 forbids inventing thresholds conversationally. This is the single largest external-research dependency in the roadmap |
| 9 | O9 | **Behavioral-finance leak detection** — what distinguishes misaligned recurring spend from ordinary discretionary spend | O9 §22 explicitly refuses "non-essential = leakage" and demands a goal-alignment definition instead; that definition needs literature |
| 10 | O10 | Observational-study method: multiple-comparison control, repeated measures, temporal autocorrelation, confounder review, effect size vs significance | O10 §38's tamper test requires policy failure on an unjustified causal claim — the method registry must cite real statistical practice |
| 11 | O11 | Source-independence and evidence-weighting method; freshness windows by claim domain; prediction-market/market-implied signal interpretation | O11 §48 lists exactly these as open items 1–5 and §47 marks the coefficients `[ASSUMPTION]` to be "validated rather than invented" |

**One standing caution on this table.** External content is **untrusted data**, never authority. It may
ground a method; it may never override a contract, a steering file or an owner decision. And per pack
14, sending data to an external model or research provider is itself an **egress event** requiring
classification — so the research path for O9/O10/O11 is constrained by D-P and D-Q, not just by the
availability of sources.

---

## §7 Verification

**This document changes no file under `src/` or `tests/`, so the repository gate does not apply to it
and is not claimed for it.** `npm run typecheck`, `npm run lint`, `npm test`, `npm run build` and
`npm run verify:all -- --all` verify code; a planning document with zero source changes cannot pass or
fail them, and stating otherwise would be a false claim of the exact kind §6.1 forbids. This section is
present rather than omitted so that absence is explicit.

**What was actually run to produce this document, and what it proves:**

| Command / action | What it established |
|---|---|
| `git -P status --porcelain FINANCIAL/`, `git -P ls-files FINANCIAL/` | **G-1** — `FINANCIAL/` is untracked, zero tracked files |
| `Select-String` over `contracts/**`, `docs/**`, `.kiro/steering/*` for `v1.3 FINAL\|MASTER_UNIFIED\|LOCAL_FULL\|DRIVE_SAFE` | **G-2** — exactly one tracked mention, in `SEVEN_CONTRACT_RECOVERY.md` |
| Identifier probes over `src/**/*.ts(x)` for 18 O-objective identifiers | §1 status column — zero matches for all of O7–O11's core identifiers, and for `EvidenceRecord`/`FinancialSnapshot` |
| `Get-ChildItem src/features` | The 15 implemented feature directories |
| Full reads of O1, O2, and clause-level extraction of O3–O11 and all 23 governance-pack files | §1, §2, §4 and the annex |
| `Expand-Archive` of the governance pack **to `$env:TEMP`, outside the repository tree** | The pack contents, **without adding an untracked entry to the working tree** — D-H's count is unchanged by the extraction |

**What this document does not verify, stated plainly:** the host, Drive, `nizamcore`, PFOS v1.3 FINAL,
and any runtime behaviour — all **INACCESSIBLE** from this session. The pipeline plan's 19-of-21 gate
baseline is **inherited, not re-measured**; its cause (D-H's 54 dirty entries) is VERIFIED.

**This document's own effect on the dirty tree, stated precisely** (VERIFIED, and corrected from a
looser first draft of this line): `docs/plans/` is itself an **untracked directory**, so
`git status --porcelain` collapses it to the single entry `?? docs/plans/`. Writing this plan and its
annex therefore leaves the **collapsed count unchanged at 54**, while the fully-expanded count
(`--untracked-files=all`, currently 242) grows by two. No file under `src/` or `tests/` was touched —
the 15 dirty entries there are the owner's pre-existing in-flight work and are untouched. This still
interacts with **D-H**, `AC14` and `AC15`; it is stated here rather than discovered later.

---

## §8 What this plan does not authorize

No code is written. No test is created or edited. No gate is run. No schema, migration or
`SCHEMA_VERSION` is changed. No O2–O11 module is created. No contract is amended, authored or
superseded. **No approval of draft `CONTRACT_6` is implied — D-E is still open.** No promotion of
`FINANCIAL/O1..O11` to contract status occurs — that is **D-L**. No decision from **D-A through D-K** is
resolved, re-litigated or reinterpreted. No decision from **D-L through D-W** is resolved. **No default
is adopted where none was offered** — D-M(a) and D-V's ordering both stand as `None offered`.

No host is touched. No credential is created, rotated, read or echoed. No OAuth consent is completed.
No webhook is registered. No DNS is mutated. No provider key is spent against. No commit and no push.
**G1–G8 in `ops/DEPLOYMENT_CONTROL.md` are untouched, uncompleted, untested and unsubstituted.** The 54
dirty working-tree entries are preserved exactly as found; the governance pack was extracted to a
temporary directory outside the repository specifically so that count would not grow.

`money-rules.md` and `drive-db.md` are preserved without amendment — **including through D-S, which
proposes an amendment to `drive-db.md` and does not make one.** The Drive scope stays `drive.file`.
`HERMES_TOOL_NAMES` stays at 10 and no authority guard is weakened. No acceptance check in the
repository gate (`AC01`–`AC19`, `AC05b`, `AC08b`, `LOOP`) is invented, weakened, or claimed satisfied by
this document.

Where the eleven objectives and the fifteen PFOS contracts disagree, the disagreement is **named and
left open with a recommendation**, and the resolution channel is the one the repository already
declares: `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md`, "resolved by an owner decision — never by silently
editing either side."

**Approval requested: none for implementation.** What is requested is answers to **D-L, D-M, D-N and
D-W** — the four that gate everything else, and the three of them (D-L, D-N, D-W) that cost nothing but
a decision.

---

## §9 Revision notes

### Revision 2 — 2026-09-20, Drive inspection

**Nothing in Revisions 1 is superseded. Three things changed, all additive.**

1. **D-M narrowed.** PFOS v1.3 FINAL was located on Drive, retrieved, read in full and hashed. It is no
   longer "absent" — but the copy that exists is the `DRIVE_SAFE` mirror, which declares `LOCAL_FULL`
   canonical, and `LOCAL_FULL` is **not on Drive**. D-M stays OPEN and `None offered`. **G-2's wording
   should be read as "absent from the tree", which was accurate; "absent" without qualification is not.**
2. **D-Z opened** — where an FX rate lives. Recommendation (b), derive on read from
   `source_events.raw_payload`. v1.3 FINAL was searched in full and settles nothing here.
3. **D-Y opened** — D-I's ingestion source order is inverted relative to both the evidence on hand and
   v1.3 FINAL §27.6's J2→J4 journey model. Recommendation (b), SMS-first with statements as the matcher.

**§3.1 is corroborated from outside this repository and does not change.** v1.3 FINAL §20.1 mandates
`RAW SOURCE → VALIDATED EVENT → DETERMINISTIC LEDGER → DETERMINISTIC CALCULATION → POLICY → LLM
EXPLANATION`; §5.2 names an `Immutable Event Inbox`; §27.6 J2/J4 give the candidate-then-reconcile shape;
§43 assigns one authoritative writer per canonical domain; §52.1 requires an idempotency key and a
verification state on `FinancialEvent`. The pipeline plan's segmentation was arrived at independently and
matches. **One escalation follows:** F7 (two canonical stores) is not merely a finding under that
contract — §43 plus AC-48 place it inside release gate RG-5, which §54.2 forbids waiving.

**A correction to this document's own §0.4.** Its table said "A claim about anything outside this local
working tree — including PFOS v1.3 FINAL, which is absent — see G-2." That row is now **too strong**: the
document was inspected, and claims about it in Revision 2 are VERIFIED. The *scope* limit still holds for
everything else outside the tree.

Full evidence, findings F-DRIVE-1 through F-DRIVE-9, the readiness matrix and the alias→id discipline are
in **`docs/plans/nizam-drive-truth-inventory.md`**. Two of its findings bear on this document directly:
**F-DRIVE-4** (v1.3 FINAL ranks itself above the repository's contracts and omits steering from its
ladder, in a copy that declares itself non-canonical) and **F-DRIVE-9** (v1.3 FINAL has its own O1–O6,
colliding with `FINANCIAL/O1..O11` on the same labels — cite `v1.3-O1` and `FIN-O1`, never bare "O1").

**Two integrity notes, recorded so they are not re-litigated.**

- The task that triggered this revision asserted that six Increment 0 artifacts did not exist. **All six
  were probed and all six exist.** Increment 0 was therefore **not** reverted and **not** redone; its
  board status stays `done`. The premise was stale.
- `.kiro/steering/two-agent-vps.md` was found **deleted** in the working tree (unstaged ` D `, intact in
  HEAD, 97 inbound citations across 23 files, no successor). It was **restored** from HEAD by a
  single-path checkout, following the precedent of commit `7a43d2f`.

### Revision 1

First revision. Nothing superseded.

Method, for the reader who wants to audit it: all eleven objective documents and all 23 governance-pack
files were read in full (the pack extracted to a temporary directory outside the tree); clause-level
extraction used a fixed twelve-item template per objective so that non-goal and dependency clauses were
captured verbatim rather than paraphrased; every code claim was re-established by reading source or by
identifier probe in this session rather than inherited from the pipeline plan or from any dated receipt.

The single most consequential finding is **§3.2** — the pipeline plan builds O1's ledger but not O1's
snapshot or its state-use receipt, and all ten remaining objectives bind to exactly those two
artifacts. The cheapest correction is **Phase 1b**. The correction most likely to prevent wasted work
is **D-N**: three capabilities the objective stack declares unowned are already owned by
`contracts/pfos/03` and already implemented under `src/features/`.
