/**
 * NIZAM · S6 validation properties — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S6)
 * Depends on: validate.ts, resolve.ts, normalize.ts. Every fixture is SYNTHETIC.
 *
 * The three integrality guards are asserted INDEPENDENTLY as well as in combination, because a test that
 * only observes the combined verdict cannot tell which guard is load-bearing — and the lexical guard is
 * the one that catches `1e21`, which the other two accept.
 */
import { describe, it, expect } from 'vitest';
import type { ResolvedRow } from './pipeline.types.ts';
import { normalizeRow } from './normalize.ts';
import { resolveRow } from './resolve.ts';
import { isIntegralMoney, validateRow } from './validate.ts';

const CTX = { asOf: '2026-03-10' };

function resolved(over: Partial<ResolvedRow> = {}): ResolvedRow {
  const n = normalizeRow({
    rowRef: 'L1',
    transactionTypeRaw: 'charge',
    payeeRaw: 'Synthetic Merchant',
    directionRaw: 'out',
    magnitude: 25_000,
    currencyRaw: 'EGP',
    accountAliasRaw: 'main',
    occurredAtRaw: '2026-03-04',
  });
  if (!n.ok) throw new Error('fixture failed to normalize');
  const r = resolveRow(n.value, {
    accountAliases: [{ alias: 'main', accountId: 'acct_main' }],
    knownCurrencies: ['EGP', 'USD'],
  });
  if (!r.ok) throw new Error('fixture failed to resolve');
  return { ...r.value, ...over };
}

describe('three independent integrality guards', () => {
  it('accepts a plain safe integer', () => {
    expect(isIntegralMoney(25_000)).toBe(true);
    expect(isIntegralMoney(0)).toBe(true);
    expect(isIntegralMoney(-1)).toBe(true);
  });

  it('SEMANTIC and ARITHMETIC guards both reject a fraction — must be integer', () => {
    expect(isIntegralMoney(0.5)).toBe(false);
    expect(isIntegralMoney(25_000.001)).toBe(false);
  });

  it('LEXICAL guard rejects 1e21, which renders with an exponent and would corrupt a SQL literal', () => {
    // 1e21 is not a safe integer either, but the lexical guard is what makes the rejection independent
    // of Number.isSafeInteger ever regressing.
    expect(String(1e21)).toContain('e');
    expect(isIntegralMoney(1e21)).toBe(false);
  });

  it('rejects the non-finite values entirely', () => {
    expect(isIntegralMoney(Number.NaN)).toBe(false);
    expect(isIntegralMoney(Number.POSITIVE_INFINITY)).toBe(false);
  });

  it('refuses a non-integral magnitude at the stage boundary — invalid input must fail', () => {
    const out = validateRow(resolved({ magnitude: 1.5 }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('AMOUNT_NOT_INTEGER');
  });
});

describe('the sign is decided once, here, from direction', () => {
  it('derives a negative amount for out and a positive one for in', () => {
    const outward = validateRow(resolved({ direction: 'out' }), CTX);
    const inward = validateRow(resolved({ direction: 'in' }), CTX);
    expect(outward.ok && inward.ok).toBe(true);
    if (outward.ok) expect(outward.value.amount).toBe(-25_000);
    if (inward.ok) expect(inward.value.amount).toBe(25_000);
  });

  it('keeps the magnitude non-negative alongside the signed amount', () => {
    const out = validateRow(resolved({ direction: 'out' }), CTX);
    expect(out.ok).toBe(true);
    if (out.ok) {
      expect(out.value.magnitude).toBe(25_000);
      expect(out.value.amount).toBe(-out.value.magnitude);
    }
  });

  it('treats a negative magnitude as the sign being in the WRONG FIELD, not as a zero', () => {
    const out = validateRow(resolved({ magnitude: -25_000 }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('AMOUNT_DIRECTION_INCOHERENT');
  });

  it('distinguishes a zero amount from a misplaced sign', () => {
    const out = validateRow(resolved({ magnitude: 0 }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('AMOUNT_NOT_POSITIVE');
  });
});

describe('dating is anchored to an injected asOf, never to a clock', () => {
  it('accepts a validly back-dated row at the date it states', () => {
    const out = validateRow(resolved({ occurredAt: '2026-01-01' }), CTX);
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.occurredAt).toBe('2026-01-01');
  });

  it('accepts a row dated exactly asOf', () => {
    expect(validateRow(resolved({ occurredAt: '2026-03-10' }), CTX).ok).toBe(true);
  });

  it('refuses a future occurrence date', () => {
    const out = validateRow(resolved({ occurredAt: '2026-03-11' }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('DATE_IN_FUTURE');
  });

  it('refuses a future posting date even when the occurrence is in the past', () => {
    const out = validateRow(resolved({ occurredAt: '2026-03-01', postedAt: '2026-03-20' }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('DATE_IN_FUTURE');
  });

  it('is deterministic — the same row and asOf give the same verdict every time', () => {
    const r = resolved();
    expect(validateRow(r, CTX)).toEqual(validateRow(r, CTX));
  });
});

describe('the fingerprint excludes memo and categoryId', () => {
  it('produces the SAME fingerprint for two rows differing only in memo', () => {
    const a = validateRow(resolved({ memo: 'first note' }), CTX);
    const b = validateRow(resolved({ memo: 'a completely different note' }), CTX);
    expect(a.ok && b.ok).toBe(true);
    if (a.ok && b.ok) expect(a.value.fingerprint).toBe(b.value.fingerprint);
  });

  it('produces the same fingerprint whether a memo is present or absent', () => {
    const withMemo = validateRow(resolved({ memo: 'note' }), CTX);
    const without = validateRow(resolved({ memo: undefined }), CTX);
    expect(withMemo.ok && without.ok).toBe(true);
    if (withMemo.ok && without.ok) {
      expect(withMemo.value.fingerprint).toBe(without.value.fingerprint);
    }
  });

  it('still changes when a consequential field changes', () => {
    const a = validateRow(resolved({ magnitude: 25_000 }), CTX);
    const b = validateRow(resolved({ magnitude: 25_001 }), CTX);
    expect(a.ok && b.ok).toBe(true);
    if (a.ok && b.ok) expect(a.value.fingerprint).not.toBe(b.value.fingerprint);
  });

  it('is unaffected by the transaction type, which is not a financial consequence of the movement', () => {
    const a = validateRow(resolved({ transactionType: 'charge' }), CTX);
    const b = validateRow(resolved({ transactionType: 'fee' }), CTX);
    expect(a.ok && b.ok).toBe(true);
    if (a.ok && b.ok) expect(a.value.fingerprint).toBe(b.value.fingerprint);
  });
});

describe('refusals stay safe and permanent', () => {
  it('never carries the offending value and is always permanent', () => {
    const out = validateRow(resolved({ magnitude: -99_999 }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) {
      expect(out.refusal.permanent).toBe(true);
      expect(JSON.stringify(out.refusal)).not.toContain('99999');
    }
  });
});
