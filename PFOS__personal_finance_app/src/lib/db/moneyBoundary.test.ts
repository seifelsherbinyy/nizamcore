// @vitest-environment node
/**
 * NIZAM · exact milliunit validation at the JSON persistence boundary.
 * Owning contract: Contract 2 / Phase 2.2; seven-contract recovery / Recovery 1.
 * Synthetic fixtures only; no provider calls or real ledger data.
 */
import { describe, expect, it } from 'vitest';
import { isMoney } from '@/lib/money/money';
import { loadDb } from '@/lib/drive/driveDb';
import { FakeDrive } from '../../../tests/helpers/fakeDriveClient.ts';
import { migrate } from './migrations.ts';
import { createEmptyDb, validateDb, zMoney } from './schema.ts';

const NOW = '2026-01-01T00:00:00.000Z';
const safeEdges = [Number.MIN_SAFE_INTEGER, -1, 0, 1, Number.MAX_SAFE_INTEGER];
const unsafeEdges = [Number.MIN_SAFE_INTEGER - 1, Number.MAX_SAFE_INTEGER + 1];

function databaseWithBalance(value: number) {
  const db = createEmptyDb(NOW);
  db.accounts.push({
    id: 'synthetic-cash', name: 'Synthetic cash', type: 'CASH', onBudget: true,
    currency: 'EGP', balance: value, clearedBalance: 0, accountIdentifier: null,
    creditLimit: null, closed: false, order: 0, paymentCategoryId: null,
  });
  return db;
}

describe('JSON money boundary matches the deterministic money domain', () => {
  it.each(safeEdges)('preserves exact safe integer %s through JSON and migration', (value) => {
    expect(zMoney.parse(value)).toBe(value);
    const db = databaseWithBalance(value);
    const parsed: unknown = JSON.parse(JSON.stringify(db));
    expect(validateDb(parsed)).toEqual(db);
    expect(migrate(parsed)).toEqual(db);
  });

  it.each(unsafeEdges)('rejects unsafe integer %s before exposing a database', (value) => {
    expect(Number.isInteger(value)).toBe(true);
    expect(isMoney(value)).toBe(false);
    expect(zMoney.safeParse(value).success).toBe(false);
    const db = databaseWithBalance(value);
    expect(() => validateDb(db)).toThrow();
    expect(() => migrate(JSON.parse(JSON.stringify(db)))).toThrow();
    expect(db.accounts[0]?.balance).toBe(value);
  });

  it('agrees with the money core on malformed and non-number values without coercion', () => {
    const invalid: unknown[] = [...unsafeEdges, Number.MAX_VALUE, 1 / 2, NaN, Infinity,
      -Infinity, '1000', null, undefined, true, {}, [], 1000n];
    for (const value of invalid) {
      expect(isMoney(value)).toBe(false);
      expect(zMoney.safeParse(value).success).toBe(false);
    }
  });

  it('retains nullable and nonnegative compositions without allowing overflow', () => {
    const db = databaseWithBalance(0);
    db.accounts[0]!.creditLimit = Number.MAX_SAFE_INTEGER;
    db.policy.minimumLiquidityBuffer = Number.MAX_SAFE_INTEGER;
    expect(validateDb(db)).toEqual(db);
    db.policy.minimumLiquidityBuffer = Number.MAX_SAFE_INTEGER + 1;
    expect(() => validateDb(db)).toThrow();
    db.policy.minimumLiquidityBuffer = -1;
    expect(() => validateDb(db)).toThrow();
    db.policy.minimumLiquidityBuffer = 0;
    db.accounts[0]!.creditLimit = Number.MAX_SAFE_INTEGER + 1;
    expect(() => validateDb(db)).toThrow();
    db.accounts[0]!.creditLimit = null;
    expect(validateDb(db)).toEqual(db);
  });

  it.each(unsafeEdges)('refuses unsafe integer %s from a fake Drive load without rewriting evidence', async (value) => {
    const drive = new FakeDrive();
    const text = JSON.stringify(databaseWithBalance(value));
    const file = await drive.client().createTextFile('synthetic-db.json', text);
    await expect(loadDb(drive.client(), file.id)).rejects.toThrow();
    expect(await drive.client().downloadText(file.id)).toBe(text);
  });
});
