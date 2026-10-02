/**
 * NIZAM · The F17 candidate-exclusion fence — spec transaction-capture-pipeline, increment 5
 * Implemented by: PFOS Contract 06 / Phase 2.6, governed by Contract 6 §5 I5.2 (APPROVED)
 * Depends on: every engine named in design §E, plus the Drive serialisation path. Tests only.
 *
 * ## What this file replaces, and why the old guarantee was not one
 *
 * Before this file the ENTIRE exclusion guarantee was one test in `migrations.test.ts`:
 *
 *   - it covered **netWorth only**, of the eleven engine surfaces design §E enumerates;
 *   - it ran against `createEmptyDb`, so the baseline had **no accounts and no transactions** and all
 *     three compared values were **zero** — an engine that summed candidates into an empty ledger would
 *     have been caught, but an engine that merged them into REAL rows would not, because zero-equals-zero
 *     passes whatever the engine does with a list it never reads;
 *   - and **nothing anywhere** asserted candidates stay out of the Drive-bound payload. That property
 *     existed only as a comment at `sync.ts` line ~193: *"Candidates are device-local (they are
 *     unreviewed, not synced to Drive)."*
 *
 * A comment is not a fence. This file is the fence.
 *
 * ## The governing clause, quoted because it is the reason this exists
 *
 * Contract 6 §5 **I5.2**: candidates live in a staging collection distinct from `transactions[]`, and a
 * candidate *"is not financial truth and MUST NOT be counted in any balance, budget, forecast or
 * report."* Every engine below is one of those four words.
 *
 * ## Why the baseline is NON-EMPTY, stated as the method
 *
 * The baseline holds two accounts, two category groups, three categories and four posted transactions, so
 * every engine returns a NON-ZERO result. The candidate added on top carries a deliberately absurd
 * magnitude, so any leak moves a number that was already moving. An identity assertion against a
 * non-trivial value is evidence; against zero it is a coincidence.
 */
import { describe, it, expect } from 'vitest';
import { createEmptyDb } from './schema.ts';
import type { NizamDb, TransactionCandidate } from './schema.ts';
// PRODUCTION module, per owner decision D-5 part 2 = (c), 2026-09-21. Previously a local helper at the
// foot of this file; the three Drive-payload assertions below are UNCHANGED in shape (binding condition 3).
import { projectForDrive, rehydrateFromDrive, serialiseDbForDrive } from '../drive/candidateExclusion.ts';
// E1 (plan NIZAM-MASTER-PLANNING-011): every engine under test is imported STATICALLY.
//
// These nine imports were previously `await import(...)` inside the nine tests. Each test therefore paid
// the module graph's first-time transform cost INSIDE its own 5 s budget, and under a full-suite run
// across thirteen workers that pushed "Budgets — computeMonth" over the limit while the assertion itself
// takes milliseconds. The timeout was measuring the bundler, not the fence.
//
// Hoisting moves that cost to collection, once per file, outside any per-test budget. The alternative —
// raising the timeout — would have left the cause in place and made the suite slower to fail honestly.
// No assertion, fixture or engine changed; only when the modules are resolved.
import { netWorth, realNetWorth } from '@/features/netWorth/netWorth.ts';
import { computeMonth } from '@/features/budget/budget.logic.ts';
import { safeToSpendAllHorizons } from '@/features/safeToSpend/safeToSpend.ts';
import { forecastAll } from '@/features/forecast/forecast.ts';
import { spendingByCategory } from '@/features/reports/spending.ts';
import { netWorthSeries } from '@/features/reports/netWorth.ts';
import { ageOfMoney } from '@/features/reports/ageOfMoney.ts';
import { cardUtilization, debtServiceRatio, liquidityRunway, controlPanel } from '@/features/reports/rescue.ts';

const AS_OF = '2026-03-15';
const MONTH = '2026-03';

/**
 * A deliberately NON-EMPTY store. Every figure below is synthetic and none is a real amount, balance,
 * payee or account identifier.
 */
function nonEmptyDb(): NizamDb {
  const base = createEmptyDb('2026-03-15T00:00:00.000Z');
  return {
    ...base,
    accounts: [
      {
        id: 'acc_cash',
        name: 'Synthetic Current',
        // Domain enum, not a generic label: AccountType is CIB_DEBIT | HSBC_CC | CASH | BANK_OTHER |
        // CREDIT_OTHER | TRACKING. `isCreditType` keys off it, so the card below must be a real credit type
        // or `cardUtilization` and `debtServiceRatio` would see no card and pass vacuously.
        type: 'CASH',
        onBudget: true,
        currency: 'EGP',
        balance: 400_000,
        clearedBalance: 400_000,
        accountIdentifier: null,
        creditLimit: null,
        closed: false,
        order: 0,
        paymentCategoryId: null,
      },
      {
        id: 'acc_card',
        name: 'Synthetic Card',
        type: 'CREDIT_OTHER',
        onBudget: true,
        currency: 'EGP',
        balance: -60_000,
        clearedBalance: -60_000,
        accountIdentifier: null,
        creditLimit: 500_000,
        closed: false,
        order: 1,
        paymentCategoryId: 'cat_cardpay',
      },
    ],
    categoryGroups: [
      { id: 'grp_ess', name: 'Essentials', order: 0, hidden: false },
      { id: 'grp_inc', name: 'Income', order: 1, hidden: false },
    ],
    categories: [
      {
        id: 'cat_food',
        groupId: 'grp_ess',
        name: 'Food',
        order: 0,
        hidden: false,
        target: null,
        isCreditCardPayment: false,
        linkedAccountId: null,
      },
      {
        // The card-payment category is linked to the credit account, so `debtServiceRatio` and
        // `controlPanel` see a real servicing path rather than an empty one.
        id: 'cat_cardpay',
        groupId: 'grp_ess',
        name: 'Credit Card Payment',
        order: 1,
        hidden: false,
        target: null,
        isCreditCardPayment: true,
        linkedAccountId: 'acc_card',
      },
      {
        id: 'cat_salary',
        groupId: 'grp_inc',
        name: 'Salary',
        order: 0,
        hidden: false,
        target: null,
        isCreditCardPayment: false,
        linkedAccountId: null,
      },
    ],
    transactions: [
      txn('txn_1', 'acc_cash', '2026-03-01', 'Synthetic Employer', 'cat_salary', 900_000),
      txn('txn_2', 'acc_cash', '2026-03-03', 'Synthetic Grocer', 'cat_food', -120_000),
      txn('txn_3', 'acc_card', '2026-03-05', 'Synthetic Grocer', 'cat_food', -60_000),
      txn('txn_4', 'acc_cash', '2026-03-09', 'Synthetic Grocer', 'cat_food', -80_000),
    ],
  };
}

function txn(
  id: string,
  accountId: string,
  date: string,
  payee: string,
  categoryId: string,
  amount: number,
) {
  return {
    id,
    accountId,
    date,
    payee,
    categoryId,
    memo: '',
    amount,
    currency: 'EGP' as const,
    cleared: 'cleared' as const,
    approved: true,
    transferAccountId: null,
    transferTransactionId: null,
    splits: null,
    importInfo: null,
  };
}

/**
 * One candidate, with an absurd magnitude so a leak is unmissable, and a category and account that
 * ALREADY EXIST in the baseline — so an engine that naively concatenated staging onto `transactions`
 * would produce a plausible, silently wrong number rather than an obvious crash.
 */
function candidate(): TransactionCandidate {
  return {
    id: 'cand_fence_1',
    accountId: 'acc_cash',
    date: '2026-03-10',
    payee: 'Synthetic Unreviewed',
    categoryId: 'cat_food',
    memo: '',
    amount: -999_000_000,
    currency: 'EGP',
    cleared: 'cleared',
    approved: false,
    transferAccountId: null,
    transferTransactionId: null,
    splits: null,
    importInfo: null,
    duplicateStatus: 'unique',
  } as TransactionCandidate;
}

function withCandidates(db: NizamDb): NizamDb {
  return { ...db, transactionCandidates: [candidate()] };
}

describe('F17 fence — the baseline is genuinely non-empty', () => {
  it('produces non-zero engine output, so an identity assertion means something', async () => {
    const db = nonEmptyDb();
    expect(db.transactions.length).toBeGreaterThan(0);
    expect(db.accounts.length).toBeGreaterThan(0);
    // The guard on the guard: if this ever became zero, every identity test below would pass vacuously.
    expect(netWorth(db).nominal).not.toBe(0);
  });

  it('the candidate is large enough that any leak changes a number', () => {
    expect(Math.abs(candidate().amount)).toBeGreaterThan(900_000_000);
  });
});

describe('F17 fence — EVERY engine in design §E is unchanged by candidates', () => {
  it('Net worth — netWorth and realNetWorth', async () => {
    const a = nonEmptyDb();
    const b = withCandidates(a);
    expect(netWorth(b)).toEqual(netWorth(a));
    expect(realNetWorth(b, 'EGP', 5)).toEqual(realNetWorth(a, 'EGP', 5));
  });

  it('Budgets — computeMonth', async () => {
    const a = nonEmptyDb();
    expect(computeMonth(withCandidates(a), MONTH)).toEqual(computeMonth(a, MONTH));
  });

  it('Safe-to-spend — safeToSpendAllHorizons', async () => {
    const a = nonEmptyDb();
    expect(safeToSpendAllHorizons(withCandidates(a), AS_OF)).toEqual(safeToSpendAllHorizons(a, AS_OF));
  });

  it('Forecast — forecastAll', async () => {
    const a = nonEmptyDb();
    expect(forecastAll(withCandidates(a), AS_OF)).toEqual(forecastAll(a, AS_OF));
  });

  it('Reports — spendingByCategory', async () => {
    const a = nonEmptyDb();
    expect(spendingByCategory(withCandidates(a), MONTH)).toEqual(spendingByCategory(a, MONTH));
  });

  it('Reports — netWorthSeries', async () => {
    const a = nonEmptyDb();
    expect(netWorthSeries(withCandidates(a))).toEqual(netWorthSeries(a));
  });

  it('Reports — ageOfMoney', async () => {
    const a = nonEmptyDb();
    expect(ageOfMoney(withCandidates(a))).toEqual(ageOfMoney(a));
  });

  it('Reports — cardUtilization, debtServiceRatio, liquidityRunway, controlPanel', async () => {
    const a = nonEmptyDb();
    const b = withCandidates(a);
    expect(cardUtilization(b)).toEqual(cardUtilization(a));
    expect(debtServiceRatio(b, MONTH)).toEqual(debtServiceRatio(a, MONTH));
    expect(liquidityRunway(b, MONTH)).toEqual(liquidityRunway(a, MONTH));
    expect(controlPanel(b, MONTH)).toEqual(controlPanel(a, MONTH));
  });

  it('Balances — the cached fields are untouched by staging', () => {
    const a = nonEmptyDb();
    const b = withCandidates(a);
    expect(b.accounts.map((x) => x.balance)).toEqual(a.accounts.map((x) => x.balance));
    expect(b.accounts.map((x) => x.clearedBalance)).toEqual(a.accounts.map((x) => x.clearedBalance));
  });
});

describe('F17 fence — NO candidate reaches the Drive-bound payload (asserted, not commented)', () => {
  it('the serialised payload contains no candidate field and no candidate id', async () => {
    const db = withCandidates(nonEmptyDb());
    // This is the shape `driveDb` uploads: the whole store, serialised. If candidates are present in the
    // serialisation, they leave the device — regardless of what the merge path does with them afterwards.
    const serialised = JSON.stringify(db);
    expect(serialised).toContain('cand_fence_1'); // the local store DOES hold it...

    // ...so the Drive-bound payload must be a PROJECTION that drops it. Until D-G is answered and that
    // single serialisation-time projection exists, this asserts the property on the projection shape the
    // pipeline requires, so the requirement is executable rather than aspirational.
    const driveBound = projectForDrive(db);
    const driveJson = JSON.stringify(driveBound);
    expect(driveJson).not.toContain('cand_fence_1');
    expect(driveJson).not.toContain('transactionCandidates');
    expect(driveJson).not.toContain('Synthetic Unreviewed');
    expect(Object.keys(driveBound)).not.toContain('transactionCandidates');
  });

  it('the projection keeps everything else, so exclusion is not achieved by dropping the payload', async () => {
    const db = withCandidates(nonEmptyDb());
    const driveBound = projectForDrive(db);
    const json = JSON.stringify(driveBound);
    // Canonical rows must survive; only staging is dropped.
    expect(json).toContain('txn_1');
    expect(json).toContain('acc_cash');
    expect(Object.keys(driveBound).sort()).toEqual(
      Object.keys(db)
        .filter((k) => k !== 'transactionCandidates')
        .sort(),
    );
  });

  it('a db with NO candidate field still projects cleanly', () => {
    const db = nonEmptyDb();
    expect(() => projectForDrive(db)).not.toThrow();
    expect(Object.keys(projectForDrive(db))).not.toContain('transactionCandidates');
  });
});

describe('F5 — the production projection covers EVERY serialisation site in driveDb', () => {
  it('serialiseDbForDrive drops staging, which is what all three sites now call', () => {
    const json = serialiseDbForDrive(withCandidates(nonEmptyDb()));
    expect(json).not.toContain('cand_fence_1');
    expect(json).not.toContain('transactionCandidates');
    expect(json).not.toContain('Synthetic Unreviewed');
  });

  it('the SNAPSHOT upload is covered — it shares one `json` variable with the canonical update', () => {
    // `driveDb.saveDb` computes `const json = serialiseDbForDrive(db)` ONCE and passes it to both
    // `createTextFile(snapshotName(now), json, …)` and `updateTextFile(handle.fileId, json)`. So the
    // snapshot cannot diverge from the canonical file by construction. Asserted because the snapshot is
    // the site a reader is most likely to forget, and under the previous code it leaked identically.
    const json = serialiseDbForDrive(withCandidates(nonEmptyDb()));
    const parsed = JSON.parse(json) as Record<string, unknown>;
    expect(Object.keys(parsed)).not.toContain('transactionCandidates');
    // The canonical rows survive, so exclusion is not achieved by uploading an empty snapshot.
    expect(json).toContain('txn_1');
  });

  it('keeps the on-Drive artifact shape unchanged — two-space indentation, as before the refactor', () => {
    // The projection changed WHAT is serialised, not HOW. A reformatting would rewrite every artifact on
    // Drive on the next save, which is a migration nobody authorized.
    const json = serialiseDbForDrive(nonEmptyDb());
    expect(json).toContain('\n  "schemaVersion"');
  });

  it('a database with no staging key at all still projects cleanly', () => {
    const db = nonEmptyDb();
    const stripped = { ...db } as Record<string, unknown>;
    delete stripped['transactionCandidates'];
    expect(() => projectForDrive(stripped as unknown as NizamDb)).not.toThrow();
  });
});

describe('the boundary is SYMMETRIC — project strips, rehydrate restores', () => {
  it('rehydrate injects an empty staging collection when the key is absent', () => {
    const projected = projectForDrive(withCandidates(nonEmptyDb()));
    const restored = rehydrateFromDrive(projected) as Record<string, unknown>;
    expect(restored['transactionCandidates']).toEqual([]);
  });

  it('project then rehydrate is lossless on EVERY other collection', () => {
    // The round trip must lose staging and nothing else. Asserted against the full key set rather than a
    // sample, so a collection added to NizamDb later cannot quietly fall out of the mirror.
    const original = withCandidates(nonEmptyDb());
    const restored = rehydrateFromDrive(projectForDrive(original)) as Record<string, unknown>;
    expect(Object.keys(restored).sort()).toEqual(Object.keys(original).sort());
    for (const key of Object.keys(original)) {
      if (key === 'transactionCandidates') continue;
      expect(restored[key], `${key} must survive the round trip`).toEqual(
        (original as unknown as Record<string, unknown>)[key],
      );
    }
    // And staging specifically does NOT survive — that is the whole point.
    expect(restored['transactionCandidates']).toEqual([]);
    expect(restored['transactionCandidates']).not.toEqual(original.transactionCandidates);
  });

  it('leaves a PRESENT staging value untouched, even a malformed one, so validation still rejects it', () => {
    // Coercing a present-but-wrong value would turn a corruption signal into silence. Absence is filled;
    // presence is judged by `validateDb`, not repaired here.
    const corrupt = { schemaVersion: 9, transactionCandidates: 'not-an-array' };
    expect(rehydrateFromDrive(corrupt)).toBe(corrupt);
    const present = { schemaVersion: 9, transactionCandidates: [{ id: 'keep_me' }] };
    expect(rehydrateFromDrive(present)).toBe(present);
  });

  it('hands a non-object through untouched rather than inventing a diagnostic', () => {
    expect(rehydrateFromDrive(null)).toBeNull();
    expect(rehydrateFromDrive('a string')).toBe('a string');
    expect(rehydrateFromDrive(42)).toBe(42);
    const arr = [1, 2];
    expect(rehydrateFromDrive(arr)).toBe(arr);
  });
});

/**
 * MOVED TO PRODUCTION 2026-09-21, and this note records that the move happened the right way round.
 *
 * This helper used to be defined here, because **D-G was open** and D-G decided where the single
 * serialisation-time projection lands. Building it then would have been an ungoverned-area build.
 *
 * D-5 answered it on 2026-09-21 — part 2 = **(c) a single serialisation-time projection** — so the helper
 * now lives at `src/lib/drive/candidateExclusion.ts` and is imported at the top of this file.
 *
 * **The three Drive-payload assertions above did not change shape.** That was the owner's binding
 * condition 3, and it is the real test of the refactor: if the production module had required an
 * assertion to be reshaped, the module would have been wrong. Only the import changed.
 */
