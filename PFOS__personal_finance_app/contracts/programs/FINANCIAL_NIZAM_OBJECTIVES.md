# Financial NIZAM objectives program (O1-O11)

PROVENANCE: owner-supplied. Eleven objective designs plus a 23-artifact governance pack, authored
2026-09-15/2026-09-02 and delivered as the untracked directory `FINANCIAL/`. Tracked here 2026-09-20
under decision **D-L(a)**. Phase: Objectives 1.
Status: **execution direction, not a superseding product contract and not a deployment authorization.**
Artifacts: `contracts/programs/financial-nizam-objectives/` (11 objective documents + the governance pack).
Analysis of record: `docs/plans/nizam-financial-objectives-alignment-plan.md` and its annex.

## Why this program exists and what tracking it does not grant

The eleven documents each carry the status line *"PROPOSED OVERHAUL DESIGN - owner-approved objective,
implementation not yet verified."* The **objectives** carry owner approval. The **implementations** do not,
and none has been verified. Tracking them here makes them citable, reviewable and diffable. It does not
make any of them a contract.

Decision **D-L(a)**, recorded 2026-09-20: track the objectives as a named program and treat them as
direction that must be decomposed into contracts, never as contracts themselves. **Contract status is
granted per objective, at that objective's phase boundary, and not before** - which is what
`two-agent-vps.md` §5 requires ("author the contract before building its area"). Options (b) promote each
to a numbered contract now and (c) leave untracked were rejected: (b) asserts eleven contracts at once for
areas that are not being built, and (c) leaves authority material that cannot be reviewed or diffed.

## Authority and boundaries

These documents sit at authority level 4 - supporting direction - under
`.kiro/steering/*` (level 1), contracts (level 2) and specs (level 3). They do not outrank
`money-rules.md`, `drive-db.md`, `pfos-current.md`, `two-agent-vps.md`, `contracts/pfos/01-15` or
`contracts/CONTRACT_1..6`. Money rules and the Drive scope remain unconditional.

**Two authority defects are recorded rather than resolved:**

- **The precedence ladder cannot be evaluated as written.** All eleven cite
  "safety/platform policy -> newest explicit owner direction -> PFOS v1.3 FINAL -> non-conflicting
  subordinate contract -> verified runtime evidence -> historical/draft material". Rank 3,
  `NIZAM_PFOS_MASTER_UNIFIED_CONTRACT_v1.3_FINAL_DRIVE_SAFE` and its LOCAL_FULL sibling, **is absent from
  this repository**, and `SEVEN_CONTRACT_RECOVERY.md` already records it as "a lineage claim until its
  exact source and authoritative index can be inspected". The governance pack compounds this by omitting
  v1.3 FINAL from its own unresolved list, so its mandatory read order cannot be completed and its
  subordination claim is unfalsifiable. Open as decision **D-M**, `None offered`, owner-only.
- **Twenty-one forward-referenced objectives do not exist** (O12, O15, O16, O17, O19-O28, O34, O35, O39,
  O40-O43). Six are load-bearing: O15 (protected floor), O28 (materiality), O16 (macro), O19 (challenge),
  O22/O27 (decision-outcome composite), O34/O35 (storage policy). Open as decision **D-V**, `None
  offered`, owner-only.

## Objective register

| ID | Objective | Owning phase | Implementation status | Governing spec, where one exists |
|---|---|---|---|---|
| O1 | Financial Truth | 1 | PARTIAL - substrate exists; the canonical snapshot and the state-use receipt do not | `.kiro/specs/transaction-capture-pipeline/` (Phase 1), `.kiro/specs/financial-snapshot-interface/` (Phase 1b) |
| O2 | Financial Protection | 2 | PARTIAL - obligation math exists; protection/alert/exception layer absent | none yet |
| O3 | Decision Intelligence | 3 | PARTIAL - append-only decision registry exists; packet and gates absent | none yet |
| O4 | Capital Optimization | 4 | PARTIAL - envelope budgeting exists; allocation proposals and events absent | none yet |
| O5 | Wealth Growth | 5 | PARTIAL - net worth and FX ratios exist; goals and trajectory absent | none yet |
| O6 | Cognitive Offloading | 6 | PARTIAL - the single clock exists; briefs and open-loop ledger absent | none yet |
| O7 | Financial Regime Management | 7 | ABSENT, and its entire quantitative core is `[MISSING]` in the document itself | none yet |
| O8 | Longitudinal Financial Intelligence | 8 | ABSENT | none yet |
| O9 | Merchant and Behavioral Intelligence | 9 | ABSENT | none yet |
| O10 | Cross-Domain Decision Intelligence | 10 | ABSENT | none yet |
| O11 | Evidence-Based Reasoning | 11 | ABSENT | none yet |

Evidence for every status cell: `docs/plans/nizam-financial-objectives-alignment-plan.md` §1.

## Corrections applied to this program's own claims

Recorded 2026-09-20 in `docs/PFOS_REPOSITORY_GAP_ANALYSIS.md` §3.1, which is the channel
`contracts/pfos/_PFOS_CONTRACT_INDEX.md` names for a repo-versus-PFOS disagreement:

- **D-N.** The objectives defer safe-to-spend policy, forecasting methodology and the net-worth engine to
  unwritten objectives. All three are already owned by `contracts/pfos/03` and implemented under
  `src/features/safeToSpend/`, `src/features/forecast/`, `src/features/netWorth/`. **No second engine is to
  be built.** Genuinely unowned and still open: the protected-floor formula and asset valuation.
- **D-O.** "Leak and behavioural intelligence" is owned by `contracts/pfos/03`; O9 claimed it too. Split:
  pfos 03 keeps leakage, O9 takes merchant identity, aliasing and recurrence.
- **D-S.** `.kiro/steering/drive-db.md` amended so Drive is the durable evidence/recovery mirror and the
  server tier is canonical, matching `tech.md` D1 and resolving gap-analysis conflict C-1.
- **D-T.** O3 and O4 contradicted each other on dependency direction. Build order: **O4 before O3**;
  allocatable capital is an input to decision comparison, not the reverse.
- **D-U.** Briefing content belongs to O6; O5 supplies fields to it rather than authoring the same windows.
- **D-P.** O9 runs on owner evidence only for its first increment; external merchant enrichment is a later,
  separately approved step, bounded by `product.md`'s v1 non-goals and the egress policy.
- **D-W.** One shared computation-receipt base and one confidence profile, extended by each objective
  rather than redefined - instead of the seven receipt schemas and four confidence models the documents
  currently specify independently.

## Status discipline

COMPLETE means an objective's own acceptance criteria have been observed against running code. PARTIAL
means useful outputs exist but the gate is unmet. BLOCKED means a named decision or absent upstream
objective prevents progress, and the blocker is named by letter. ABSENT means no implementation exists.
Passing code checks alone do not prove live readiness, and a documented status is not fresh verification.
No human gate is executed, tested, populated or marked complete by this program. No objective document is
promoted to contract status by being listed here.
