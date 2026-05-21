# PFA — Personal Financial Assistant Module

> Single source of truth for personal financial position inside MAL. Canonical state + append-only ledgers + continuous learnings log.

**Disclaimer**: Personal financial tracking and research, not professional financial advice. Decisions affecting major life outcomes warrant a qualified financial advisor.

## Architecture

```
MAL__financial_engine/pfa/
  canonical_state.json    ← current truth (single file, overwritten on refresh)
  ledgers/
    debts.jsonl           ← append-only debt state changes
    payments.jsonl        ← append-only payment records
    decisions.jsonl       ← append-only financial decisions
  learnings_log.jsonl     ← append-only life learnings (never overwritten)
  README.md               ← this file (committable)
```

**Privacy**: All data files are `strict_local` (gitignored). Only this README is committable.

## Schemas

All in `NIZAM__system/schemas/`:
- `pfa_canonical_state.schema.json` — canonical state structure
- `pfa_debt_event.schema.json` — debt ledger entry format
- `pfa_payment_event.schema.json` — payment ledger entry format
- `pfa_learning.schema.json` — learnings log entry format

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

## Confidence Labels

Every figure carries one of:
- **CONFIRMED** — verified from a primary source (statement, app screenshot, user confirmation)
- **ESTIMATED** — calculated or interpolated from known data
- **ASSUMPTION** — carried from a prior session or general knowledge, not verified this cycle
- **STALE** — as-of date is older than current month and no fresh value fetched
- **MISSING** — no data available; must be supplied before treating as current truth

## Update Routine (Monthly or On-Demand)

### Step 1 — Run the fetch cascade

1. **Layer 1**: Search past session transcripts for new PFA findings
2. **Layer 2**: Check workspace files for updated financial data
3. **Layer 3**: Read current `canonical_state.json` as the baseline
4. **Layer 4**: Ask user for any figures still MISSING or STALE

### Step 2 — Reconcile

- For each figure: compare fetched value against canonical state
- **Conflict resolution**: most-recent-wins (by as-of date). Both values retained in the debts ledger.
- Tag every updated figure with source, as-of date, and confidence label
- Compute derived fields: totals, debt-to-income ratio, runway, surplus/deficit

### Step 3 — Append to ledgers

- For each debt with a changed balance: append a `balance_updated` event to `debts.jsonl`
- For each payment reported: append to `payments.jsonl`
- For each decision made: append to `decisions.jsonl`
- Use idempotency keys (SHA256 of ts+debt_id+event_type) to prevent duplicate appends on re-runs

### Step 4 — Update canonical state

- Overwrite `canonical_state.json` with the reconciled current truth
- Update `provenance.last_updated` with current UTC timestamp
- Update `provenance.open_items` with any remaining MISSING values

### Step 5 — Append learnings

- Add any new insights, corrections, or patterns to `learnings_log.jsonl`
- Never overwrite existing entries — append only
- Use `supersedes` field to link corrections to prior learnings

### Step 6 — Commit (if repo-connected)

- Committable files only: this README, schemas, _index.json updates
- Data files stay strict_local — never committed
- UTC-timestamped commit message

## Resilience and Fallback Map

| Step | Primary | Fallback | If all fail |
|---|---|---|---|
| Fetch Layer 1 (transcripts) | Search session transcripts | Skip, proceed to Layer 2 | Log "Layer 1 empty" |
| Fetch Layer 2 (files) | Read workspace files | Skip, proceed to Layer 3 | Log "Layer 2 empty" |
| Fetch Layer 3 (repo state) | Read canonical_state.json | Use empty template | Log "Layer 3 fresh install" |
| Fetch Layer 4 (user) | Ask for MISSING figures | User defers | Mark MISSING, list in open_items |
| Reconcile conflicts | Most-recent-wins | Ask user to pick | Retain both, flag in open_items |
| Write canonical state | Write to pfa/canonical_state.json | Write to temp file | Log error, retain in-memory state |
| Append to ledger | Append to .jsonl | Create file if missing | Log error, surface to user |
| Commit to repo | git commit | Stage locally | Retain files, defer commit |
| Push to remote | git push | Defer push | Retain local commit |

**Never fails silently. Never fabricates to fill a gap.**

## How to Add a New Debt

1. Add a new entry to `canonical_state.json` → `debt_architecture.debts[]` with all fields
2. Append a `debt_opened` event to `ledgers/debts.jsonl`
3. Update `debt_architecture.summary` totals
4. If recycling-eligible: add to `credit_recycling.eligible_platforms`

## How to Record a Payment

1. Append a payment event to `ledgers/payments.jsonl`
2. Append a `balance_updated` event to `ledgers/debts.jsonl`
3. Update the debt's `current_balance_egp` and `available_credit_egp` in `canonical_state.json`
4. If recycling was used: set `recycling_used: true` on the payment event

## How to Add a Learning

1. Append to `learnings_log.jsonl` with the learning schema
2. Set `actionable: true` if it changes future behavior
3. If it corrects a prior learning: set `supersedes` to that entry's idempotency_key

## How to Roll Back

- `canonical_state.json` can be regenerated from the ledgers (debts.jsonl + payments.jsonl)
- Ledgers are append-only — "rolling back" means appending a correction event, not deleting
- Git history provides full audit trail for committed files (schemas, README)

## Privacy and Sensitivity

- All financial data files are `strict_local` — never leave disk, never sync, never commit
- The `.gitignore` excludes `MAL__financial_engine/pfa/` data files
- Only structural files (README, schemas) are committable as `private_github`
- No financial figures appear in commit messages
- No figures are shared externally under any circumstances
- Research-and-analysis framing only — never presented as financial advice
