# PFA — Personal Financial Assistant Module

> **v2, 2026-10-02 (ADR-ZAYD-001).** PFA is no longer an independent source of truth. Every figure in
> `canonical_state.json` and every ledger entry is a mirror of PFOS's deterministic engine
> (`finance.db`, integer milliunits) — the same `source_of_truth`/`mirrorOf` relationship Google
> Drive already has to PFOS, per `drive-db.md`. Zayd (MAL's persona codename, formerly the colliding
> "Sadiq") is the presentation and coaching layer on top of PFOS: baseline framing, scenario modeling,
> milestone-ladder narrative, decision scoring, and the append-only learnings log. Zayd does not compute
> or estimate a money figure — PFOS does, or the field stays `null` pending entry into PFOS.
>
> v1's "ask the user for anything MISSING/STALE, estimate, label CONFIDENCE" update routine is retired.
> See the superseded-wording record at the end of this file.

**Disclaimer**: Personal financial tracking and research, not professional financial advice. Decisions affecting major life outcomes warrant a qualified financial advisor.

## Architecture

```
MAL__financial_engine/pfa/
  canonical_state.json    ← generated view of PFOS's finance.db (overwritten on every sync, never hand-edited)
  ledgers/
    debts.jsonl           ← append-only mirror of PFOS debt-record changes
    payments.jsonl        ← append-only mirror of PFOS payment transactions
    decisions.jsonl        ← append-only financial decisions (Zayd-authored, non-monetary narrative)
  learnings_log.jsonl     ← append-only life learnings (never overwritten, Zayd-authored, non-monetary)
  README.md               ← this file (committable)
```

**Privacy**: All data files are `strict_local` (gitignored). Only this README is committable.

## Schemas

All in `NIZAM__system/schemas/`, v2 (2026-10-02, milliunits, see each file's `_migration_note`/description):
- `pfa_canonical_state.schema.json` — canonical state structure, now requires a `source_of_truth` stamp
- `pfa_debt_event.schema.json` — debt ledger entry format, `source` pinned to `PFOS_engine`
- `pfa_payment_event.schema.json` — payment ledger entry format, `source` pinned to `PFOS_engine`
- `pfa_learning.schema.json` — learnings log entry format (unchanged — narrative, not money)

## Debt Architecture Model

### Platform types

| Type | Platforms | Recycling | Description |
|---|---|---|---|
| `credit_card` | HSBC 8071, HSBC 5411 | When current + under limit | Revolving credit. Freed limit reusable after payment — but currently blocked (arrears/overlimit). |
| `bnpl_installment` | TRU, Halan, Souhoola, Valu | No | Fixed installments. No credit recycling. Payoff reduces balance but frees no reusable limit. |
| `family_loan` | Matthew, Yahia | No | Informal. Terms (interest, schedule) vary and may not be documented. |

**Correction (2026-05-21)**: Halan and Valu were originally assumed to support card-based recycling. Actual dashboard data shows pure installment behavior — reclassified to `bnpl_installment`.

### Credit recycling rule

Only `credit_card` types are recycling-eligible, and only when cards are: (1) current (no arrears), (2) under their credit limit, and (3) 30+ days clean. As of 2026-03-04, recycling is blocked on ALL platforms. All BNPL platforms are pure-installment — payments reduce balance but do not free reusable credit.

## Update Routine (v2 — sync, not estimate)

### Step 1 — Sync from PFOS

Read the current state directly from PFOS's `finance.db` (via its deterministic engine's export/query path, not by re-deriving figures). This is the only figure source. There is no transcript search, no workspace-file scan, and no "ask the user for a MISSING figure" step — if PFOS doesn't have a figure yet, the field stays `null` and is logged in `provenance.open_items`, pending entry into PFOS through its normal ingestion path (not through PFA).

### Step 2 — Write the projection

- Overwrite `canonical_state.json` with the synced state, stamped with `source_of_truth.projectedAt` = now (UTC)
- Append any changed debt/payment facts to `ledgers/debts.jsonl` / `ledgers/payments.jsonl`, `source: "PFOS_engine"`, using the existing idempotency-key convention (SHA256 of ts+debt_id+event_type) to prevent duplicate appends on re-sync

### Step 3 — Zayd's layer on top (narrative, not figures)

- Scenario modeling, milestone-ladder status, and 7-factor decision scoring are computed from the synced figures — Zayd's judgment applies to the *interpretation*, never to the number itself
- Record any insight, correction, or pattern in `learnings_log.jsonl` (append-only, non-monetary)
- Record any financial decision made in `decisions.jsonl` (append-only, non-monetary narrative — "chose to pay down HSBC 8071 first," not a recomputation of its balance)

### Step 4 — Commit (if repo-connected)

- Committable files only: this README, schemas, `_index.json` updates
- Data files stay strict_local — never committed
- UTC-timestamped commit message

## Resilience and Fallback Map

| Step | Primary | Fallback | If all fail |
|---|---|---|---|
| Sync from PFOS | Query PFOS's finance.db / engine export | Skip the sync, keep the last-known projection, flag it stale in `provenance.open_items` | Log "PFOS sync unavailable," surface to user, do not fabricate a figure |
| Write canonical state | Write to `pfa/canonical_state.json` | Write to temp file | Log error, retain in-memory state |
| Append to ledger | Append to `.jsonl` | Create file if missing | Log error, surface to user |
| Commit to repo | git commit | Stage locally | Retain files, defer commit |
| Push to remote | git push | Defer push | Retain local commit |

**Never fails silently. Never fabricates to fill a gap. v2 adds: never estimates to fill a gap either — that was v1's job, now retired.**

## How to Add a New Debt

Enter it into PFOS through PFOS's normal data-entry path. PFA's next sync picks it up automatically into `canonical_state.json` and appends a `debt_opened` event to `ledgers/debts.jsonl`. PFA has no independent "add a debt" step of its own anymore.

## How to Record a Payment

Enter it into PFOS through PFOS's normal transaction path. PFA's next sync mirrors it into `ledgers/payments.jsonl` and `ledgers/debts.jsonl`, and updates `canonical_state.json`.

## How to Add a Learning

1. Append to `learnings_log.jsonl` with the learning schema
2. Set `actionable: true` if it changes future behavior
3. If it corrects a prior learning: set `supersedes` to that entry's idempotency_key

## How to Roll Back

- `canonical_state.json` is regenerated by re-syncing from PFOS — there is nothing to "roll back" in PFA itself, since PFA no longer holds independent state
- A correction to a monetary fact is made in PFOS (its own append-only ledger + audit trail), then PFA re-syncs
- Git history provides a full audit trail for committed files (schemas, README)

## Privacy and Sensitivity

- All financial data files are `strict_local` — never leave disk, never sync to Drive directly from PFA, never commit
- The `.gitignore` excludes `MAL__financial_engine/pfa/` data files
- Only structural files (README, schemas) are committable as `private_github`
- No financial figures appear in commit messages
- No figures are shared externally under any circumstances
- Research-and-analysis framing only — never presented as financial advice

## Superseded wording (v1, retained for traceability)

v1's Step 1 ran a four-layer fetch cascade (search past session transcripts → check workspace files →
read `canonical_state.json` as baseline → ask the user for anything MISSING/STALE), then reconciled
conflicts "most-recent-wins" and tagged every figure CONFIRMED / ESTIMATED / ASSUMPTION / STALE / MISSING.
This made an LLM session the thing deciding a monetary figure, which conflicts with the repository-wide
rule that deterministic engines are the sole source of financial truth. Superseded by the single-source
sync routine above. Full record: `NIZAM__system/docs/ADR-ZAYD-001-pfos-engine-into-mal-zayd.md`.
