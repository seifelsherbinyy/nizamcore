/**
 * NIZAM · S7 deduplication properties — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S7)
 * Depends on: dedupe.ts and the S4–S6 stages for fixtures. Every fixture is SYNTHETIC.
 *
 * Three properties carry this file: an un-run comparison FAILS CLOSED and is not mistaken for "no
 * duplicates found"; a pending record and its posted settlement are a lifecycle link rather than a
 * duplicate; and nothing here ever proposes a deletion, because a same-day repeat can be legitimate.
 */
import { describe, it, expect } from 'vitest';
import type { ValidatedRow } from './pipeline.types.ts';
import { normalizeRow } from './normalize.ts';
import { resolveRow } from './resolve.ts';
import { validateRow } from './validate.ts';
import {
  CONFIDENCE_EXACT_BPS,
  CONFIDENCE_PARTIAL_BPS,
  classifyDuplicate,
  duplicateKeyFor,
  type ExistingRecord,
} from './dedupe.ts';

/**
 * Build a validated row by threading a SYNTHETIC extracted row through S4, S5 and S6.
 *
 * `payeeRaw` is an argument rather than a post-hoc override because the fingerprint is computed inside
 * `validateRow`; overriding `normalizedPayee` afterwards would leave a STALE fingerprint and make a test
 * pass or fail for the wrong reason. Anything in `over` is applied after validation and must therefore be
 * a field the fingerprint does not read.
 */
function validated(over: Partial<ValidatedRow> = {}, payeeRaw = 'Synthetic Merchant'): ValidatedRow {
  const n = normalizeRow({
    rowRef: 'L1',
    transactionTypeRaw: 'charge',
    payeeRaw,
    directionRaw: 'out',
    magnitude: 25_000,
    currencyRaw: 'EGP',
    accountAliasRaw: 'main',
    occurredAtRaw: '2026-03-04',
  });
  if (!n.ok) throw new Error('fixture failed to normalize');
  const r = resolveRow(n.value, {
    accountAliases: [{ alias: 'main', accountId: 'acct_main' }],
    knownCurrencies: ['EGP'],
  });
  if (!r.ok) throw new Error('fixture failed to resolve');
  const v = validateRow(r.value, { asOf: '2026-03-10' });
  if (!v.ok) throw new Error('fixture failed to validate');
  return { ...v.value, ...over };
}

function existing(row: ValidatedRow, over: Partial<ExistingRecord> = {}): ExistingRecord {
  return {
    transactionId: 'txn_existing',
    fingerprint: row.fingerprint,
    duplicateKey: duplicateKeyFor(row),
    settlement: 'posted',
    ...over,
  };
}

describe('an un-run comparison fails closed', () => {
  it('refuses rather than reporting unique', () => {
    const out = classifyDuplicate(validated(), { comparisonRan: false });
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('DEDUPE_COMPARISON_NOT_RUN');
  });

  it('distinguishes "did not look" from "looked and found nothing"', () => {
    const notRun = classifyDuplicate(validated(), { comparisonRan: false });
    const ranEmpty = classifyDuplicate(validated(), { comparisonRan: true, matches: [] });
    expect(notRun.ok).toBe(false);
    expect(ranEmpty.ok).toBe(true);
    if (ranEmpty.ok) expect(ranEmpty.value.duplicateStatus).toBe('unique');
  });
});

describe('the duplicate key is built on the account and the derived SIGNED amount', () => {
  it('separates the two directions, repairing the collision F9 describes', () => {
    const outward = validated({ direction: 'out', amount: -25_000 });
    const inward = validated({ direction: 'in', amount: 25_000 });
    expect(duplicateKeyFor(outward)).not.toBe(duplicateKeyFor(inward));
  });

  it('separates two accounts with otherwise identical movements', () => {
    const a = validated({ accountId: 'acct_main' });
    const b = validated({ accountId: 'acct_card' });
    expect(duplicateKeyFor(a)).not.toBe(duplicateKeyFor(b));
  });

  it('separates two currencies', () => {
    expect(duplicateKeyFor(validated({ currency: 'EGP' }))).not.toBe(
      duplicateKeyFor(validated({ currency: 'USD' })),
    );
  });

  it('EXCLUDES the payee, so a differently spelled payee still lands in the same bucket to be compared', () => {
    const a = validated({}, 'Acme Corp');
    const b = validated({}, 'Acme Corporation');
    // Same bucket, so they MEET and get compared...
    expect(duplicateKeyFor(a)).toBe(duplicateKeyFor(b));
    // ...but the fingerprint still tells them apart, so they are not declared identical.
    expect(a.fingerprint).not.toBe(b.fingerprint);
  });
});

describe('classification', () => {
  it('reports a duplicate at exact confidence when the fingerprints match', () => {
    const row = validated();
    const out = classifyDuplicate(row, { comparisonRan: true, matches: [existing(row)] });
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.value.duplicateStatus).toBe('duplicate');
      expect(out.value.links[0]!.linkType).toBe('suspected_duplicate');
      expect(out.value.links[0]!.confidenceBps).toBe(CONFIDENCE_EXACT_BPS);
    }
  });

  it('reports ambiguous at partial confidence when only the duplicate key matches', () => {
    const row = validated();
    const other = validated({}, 'A Different Payee Entirely');
    // Same duplicate key (the payee is not in it), different fingerprint — the definition of ambiguous.
    expect(duplicateKeyFor(other)).toBe(duplicateKeyFor(row));
    expect(other.fingerprint).not.toBe(row.fingerprint);
    const out = classifyDuplicate(row, {
      comparisonRan: true,
      matches: [existing(other, { fingerprint: other.fingerprint })],
    });
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.value.duplicateStatus).toBe('ambiguous');
      expect(out.value.links[0]!.confidenceBps).toBe(CONFIDENCE_PARTIAL_BPS);
    }
  });

  it('links a pending record to its posted settlement WITHOUT calling it a duplicate', () => {
    const row = validated();
    const out = classifyDuplicate(
      row,
      { comparisonRan: true, matches: [existing(row, { settlement: 'pending' })] },
      'posted',
    );
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.value.duplicateStatus).toBe('unique');
      expect(out.value.links[0]!.linkType).toBe('pending_to_posted');
    }
  });

  it('confidence is always an integer basis-point value inside the DDL range', () => {
    const row = validated();
    const out = classifyDuplicate(row, { comparisonRan: true, matches: [existing(row)] });
    expect(out.ok).toBe(true);
    if (out.ok) {
      for (const link of out.value.links) {
        expect(Number.isInteger(link.confidenceBps)).toBe(true);
        expect(link.confidenceBps).toBeGreaterThanOrEqual(0);
        expect(link.confidenceBps).toBeLessThanOrEqual(10_000);
      }
    }
  });
});

describe('nothing is ever deleted or auto-resolved', () => {
  it('leaves every proposed link unresolved, because only an owner act closes one', () => {
    const row = validated();
    const out = classifyDuplicate(row, { comparisonRan: true, matches: [existing(row)] });
    expect(out.ok).toBe(true);
    if (out.ok) for (const link of out.value.links) expect(link.resolution).toBeNull();
  });

  it('surfaces a legitimate same-day repeat rather than suppressing it', () => {
    // Two coffees: identical movement, twice. The verdict is `duplicate`, and the REMEDY is a link plus a
    // question — there is no delete, no skip and no merge anywhere in the returned verdict.
    const row = validated();
    const out = classifyDuplicate(row, { comparisonRan: true, matches: [existing(row)] });
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.value.links).toHaveLength(1);
      expect(Object.keys(out.value)).not.toContain('delete');
      expect(Object.keys(out.value)).not.toContain('skip');
    }
  });

  it('carries the fingerprint and duplicate key forward so the caller persists what was compared', () => {
    const row = validated();
    const out = classifyDuplicate(row, { comparisonRan: true, matches: [] });
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.value.fingerprint).toBe(row.fingerprint);
      expect(out.value.duplicateKey).toBe(duplicateKeyFor(row));
    }
  });
});
