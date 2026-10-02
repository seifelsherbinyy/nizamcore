# Tasks: financial-snapshot-interface

Owner: `docs/plans/nizam-financial-objectives-alignment-plan.md` §5, Phase **1b**.
Requirements: `./requirements.md` · Design: `./design.md`
Predecessor spec: `.kiro/specs/transaction-capture-pipeline/` (Phase 1).

## Status vocabulary

Same as the pipeline spec's, plus one value this spec needs:

| Value | Meaning |
|---|---|
| `done` | Performed, with an evidence pointer. |
| `ready` | No open decision and no unapproved design blocks it. |
| `blocked-on-<letter>` | An **owner decision** is unanswered. |
| `blocked-on-design-approval` | **This spec's `requirements.md` + `design.md` are not yet owner-approved.** All `src/` work sits here, because `two-agent-vps.md` §5 requires the governing design to exist *and be approved* before its area is built. |

**Decision state loaded:** **D-A ANSWERED** (server canonical) · **D-W ANSWERED** (one shared receipt base)
· **D-N ANSWERED** (pfos 03 owns and implements safe-to-spend/forecast/net-worth — reference them, build no
second engine) · **D-S ANSWERED** (Drive is the mirror) · **D-Z OPEN** (FX retention placement; recommended
(b), no migration) · **D-H OPEN, `None offered`** ⇒ `AC14`/`AC15` fail, **19/21 is the baseline**.

**Why every code task is blocked and that is correct, not a stall.** This spec exists precisely so the
design lands before the code. Marking a code task `ready` before the design is approved would be the
violation `two-agent-vps.md` §5 names. Task 1 is the one task that is genuinely startable now.

---

## Increments

- [ ] **1. Authority — identify and record the owning contract for the snapshot and the receipt.** · status **`ready`** · sequenced-after: —
  - **No code.** This is the `two-agent-vps.md` §5 precondition for everything below it.
  - **Files:** `contracts/pfos/_PFOS_BUILD_LOG.md` (a dated inline amendment section), possibly a new NIZAM-derived contract; `contracts/programs/FINANCIAL_NIZAM_OBJECTIVES.md` (register the spec against O1)
  - **Work:** establish which existing contract owns the canonical snapshot and the state-use receipt, or author one. Candidates already on record: **PFOS 06** (store schema and the money persistence boundary) for the tables, **PFOS 02 §4** (transaction state model) for the state semantics. The `FinancialSnapshot` *entity* is defined only in governance-pack file 03, which is **level-4 direction, not a contract** — so the entity has a name and no contract owner, and that is the gap this task closes.
  - **Acceptance:** the owning contract is named for (a) the snapshot tables, (b) the receipt base, (c) the installment `link_type` question of design §E. Where no contract owns one, a NIZAM-derived contract is authored before its task unblocks. The amendment is recorded in the build log; note that **`AC12` cannot verify that channel** — it parses a single-digit contract number and hard-requires exactly five index rows — so the gap is recorded, not filled.
  - _Source: requirements §1, §3.1; design §B, §E; alignment plan §2.1 Gap 1; annex §A.1._

- [ ] **2. `financialSnapshot.ts` — the versioned snapshot builder.** · status **`blocked-on-design-approval`** · sequenced-after: 1
  - **Files (new):** `src/server/state/financialSnapshot.ts` + test
  - **Work:** assemble design §C.1's shape from the derivation table in requirements §6. Every monetary field an `EngineRef`, never a number. `| null` where an engine output is unavailable — never zero.
  - **Acceptance:** governance-pack file 03's field names used verbatim (no second `FinancialSnapshot` definition); a second canonical snapshot for one version triple is **unrepresentable**; assembly fails closed on each of design §C.4's four refusal conditions; a property test asserts the builder computes no monetary value.
  - _Source: requirements §3.1–§3.3, §3.6, §6; design §C._

- [ ] **3. `stateUseReceipt.ts` — the one shared receipt base.** · status **`blocked-on-design-approval`** · sequenced-after: 1
  - **Files (new):** `src/server/state/stateUseReceipt.ts` + test
  - **Work:** design §D.1's base, extended by downstream objectives and never redefined. `MISSING` a first-class `EngineRunStatus`.
  - **Acceptance:** carries **no** monetary field, asserted by reusing the existing Hermes `AUTHORITY_KEY` pattern against every key of the type rather than writing a second guard; a receipt cannot claim an engine ran without an `EngineRun` entry; `completion_status: 'PARTIAL'` is reachable and is what a missing engine produces; a confidence field, if present, is a **band** (`ledger.types.ts` refuses band→score conversion).
  - _Source: requirements §4.1–§4.5; design §D; **D-W**._

- [ ] **4. Installment relation matcher (closes O1 criterion 9).** · status **`blocked-on-design-approval`**, and **`blocked-on-D-Z`-class migration question if a new `link_type` is needed** · sequenced-after: 1
  - **Files (new):** `src/server/ingest/installmentRelations.ts` + test
  - **Work:** link the purchase event to the financing obligation and mark repayments as servicing it, so purchase and repayment are not both counted as consumption. **Creates no obligation** and nets nothing; an uncertain link raises an exception rather than resolving itself.
  - **Open, deliberately:** whether this needs a fifth `transaction_links.link_type` beyond `suspected_duplicate | pending_to_posted | transfer_pair | correction`. A new enum member is a **migration** and is therefore owner-gated. Task 1 must answer who owns that decision.
  - **Acceptance:** an installment purchase plus its full repayment schedule produces exactly one unit of consumption in every engine in the pipeline spec's design §E; an ambiguous financing link produces a named exception and zero canonical rows.
  - _Source: requirements §5.1; design §E; governance-pack file 04; O1 §5.5; O2 §9._

- [ ] **5. FX settlement retention (closes O1 criterion 10).** · status **`blocked-on-D-Z`** · sequenced-after: 1
  - **Files:** a derived accessor over `source_events.raw_payload` (per **D-Z(b)**, the recommendation) — **or** a migration adding `transactions` columns (per D-Z(a)), which is why this is decision-blocked rather than design-blocked
  - **Work:** retain and expose the original amount/currency, settlement amount/currency, provider rate, rate date and fees where the source provides them. **No FX at ingest** — unchanged.
  - **Acceptance:** a foreign-currency row retains every value the source supplied; nothing is converted at capture; `mulRatio` remains the only ratio path and no second conversion implementation exists; no converted figure is persisted as truth.
  - **Why decision-blocked:** D-Z(a) adds monetary columns, and `assertMonetaryCoverage` is bidirectional, so every existing `transactions` write path would then have to mention them or refuse. That is a coordinated change and an owner call.
  - _Source: requirements §5.2, §7 (**D-Z**); design §F._

- [ ] **6. Freshness and staleness exposure (closes O1 criteria 13 and 14).** · status **`blocked-on-design-approval`** · sequenced-after: 2
  - **Files:** the freshness derivation inside `financialSnapshot.ts` + test
  - **Acceptance:** every current-state output carries `as_of` and a reconciliation state; **a stale historically correct balance is never presented as current**; `overall_freshness` is the **worst** state present, never an average; an account with no evidence reads `UNKNOWN`, not `FRESH`.
  - _Source: requirements §3.4, §5.3; design §C.3._

- [ ] **7. Persistence — `financial_snapshots` and `state_use_receipts`.** · status **`blocked-on-design-approval`** + **migration gate** · sequenced-after: 2, 3
  - **Files (new):** `src/server/db/repositories/snapshotRepository.ts` + test; a migration adding the two tables
  - **Acceptance:** `UNIQUE (canonical_state_version, calculation_version, policy_version)`; conflict-ignoring insert with read-back so the insert *is* the decision; append-only with no delete; column names avoid all 18 `TELEMETRY_FORBIDDEN_COLUMNS`; `MONETARY_COLUMNS` gains **no** entry because these tables hold no money; append-only triggers matching `decisions`/`spend_ledger`.
  - **Note:** this task contains the only migration in the spec. It is gated exactly as every other migration in this project is — the tables do not exist until that gate opens.
  - _Source: design §G; requirements §3.2._

- [ ] **8. Downstream consumability proof.** · status **`blocked-on-design-approval`** · sequenced-after: 2, 3, 7
  - **Files:** tests only
  - **Acceptance:** a synthetic consumer binds to `canonical_state_version`, resolves every `EngineRef`, and can prove which snapshot and which engines a conclusion rested on. A consumer presented with a `PARTIAL` receipt **narrows** its conclusion rather than proceeding. This is the test that O2 is actually unblocked.
  - _Source: requirements §1, §8.3; design §D.3._

- [ ] **9. Tamper and failure injection.** · status **`blocked-on-design-approval`** · sequenced-after: 8
  - **Files:** tests only
  - **Cases:** author a second canonical snapshot for one version triple; place an amount on a receipt; claim an engine ran with no `EngineRun`; present a stale account as `FRESH`; average two freshness states; double-count an installment purchase and its repayments.
  - **Acceptance:** each case **fails a test**. A guard that cannot be made to fail is not a guard.
  - _Source: requirements §8.6; pipeline spec requirements §1.7._

---

## Board summary

| # | Task | Status |
|---|---|---|
| 1 | Authority — owning contract for snapshot + receipt | **`ready`** |
| 2 | `financialSnapshot.ts` | `blocked-on-design-approval` |
| 3 | `stateUseReceipt.ts` | `blocked-on-design-approval` |
| 4 | Installment relation matcher | `blocked-on-design-approval` (+ migration question) |
| 5 | FX settlement retention | **`blocked-on-D-Z`** |
| 6 | Freshness / staleness exposure | `blocked-on-design-approval` |
| 7 | Persistence + migration | `blocked-on-design-approval` (+ migration gate) |
| 8 | Downstream consumability proof | `blocked-on-design-approval` |
| 9 | Tamper and failure injection | `blocked-on-design-approval` |

**Next startable work: Task 1** — name the owning contract. It is the only task that needs no approval
beyond what is already given, and it is the precondition for unblocking tasks 2, 3, 4, 6, 7, 8 and 9 all at
once.

## Downstream effect of this spec

**Phase 2 (O2 Financial Protection) is blocked on this spec**, not on its own complexity: O2 binds to
`canonical_state_version` and to a computation receipt, and neither exists until tasks 2, 3 and 7 land.
The same is true of Phases 3–11. Recorded in `docs/plans/nizam-financial-objectives-alignment-plan.md`
§3.3 and §5, and in `contracts/programs/FINANCIAL_NIZAM_OBJECTIVES.md`.

Separately and unchanged: **Phase 10 (O10 Cross-Domain) is `blocked-on-D-Q`** — a runtime-verified
HIMAYAH v2 contract, which is O10 §26's own instruction — and **D-Q remains `None offered`, owner-only.**

## Standing constraints

Every new `src/`/`tests/` file declares its contract and phase in the first twenty lines (`AC10`). A decimal
money literal in a fixture needs a line naming the invalidity (`AC07`). Tests ratchet **up only**, against
both floors (`AC04 --min 3009`, `AC19`'s 2301). The declared harness count stays **21**; no check is
invented or weakened. Expected gate while **D-H** is unanswered: **19 of 21, `AC14`/`AC15` only.**
