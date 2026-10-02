/**
 * NIZAM · S4 normalization properties — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S4)
 * Depends on: normalize.ts, pipeline.types.ts. Every fixture is SYNTHETIC.
 *
 * The load-bearing case here is the FIRST one: normalization moves no money. Everything else in this
 * file guards against a value being invented where the source did not supply one.
 */
import { describe, it, expect } from 'vitest';
import { INGEST_TRANSACTION_TYPES, type ExtractedRow } from './pipeline.types.ts';
import { isCalendarDate, normalizePayee, normalizeRow } from './normalize.ts';

function row(over: Partial<ExtractedRow> = {}): ExtractedRow {
  return {
    rowRef: 'L1',
    transactionTypeRaw: 'charge',
    payeeRaw: 'Synthetic Merchant',
    directionRaw: 'out',
    magnitude: 25_000,
    currencyRaw: 'EGP',
    accountAliasRaw: 'main',
    occurredAtRaw: '2026-03-04',
    ...over,
  };
}

describe('normalization moves no money', () => {
  it('passes the magnitude through byte-identically for every vocabulary token', () => {
    for (const token of INGEST_TRANSACTION_TYPES) {
      const input = row({ transactionTypeRaw: token, magnitude: 123_456_789 });
      const out = normalizeRow(input);
      expect(out.ok).toBe(true);
      if (out.ok) expect(out.value.magnitude).toBe(input.magnitude);
    }
  });

  it('preserves the magnitude across a range of values including the smallest unit', () => {
    for (const m of [1, 2, 999, 1_000, 1_001, 999_999, 8_640_000_000]) {
      const out = normalizeRow(row({ magnitude: m }));
      expect(out.ok).toBe(true);
      if (out.ok) expect(out.value.magnitude).toBe(m);
    }
  });

  it('never introduces a signed amount — the sign is S6 territory', () => {
    const out = normalizeRow(row({ directionRaw: 'out' }));
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.magnitude).toBeGreaterThan(0);
    if (out.ok) expect(out.value).not.toHaveProperty('amount');
  });
});

describe('the transaction-type vocabulary is closed', () => {
  it('accepts each listed token, case-folded', () => {
    for (const token of INGEST_TRANSACTION_TYPES) {
      const out = normalizeRow(row({ transactionTypeRaw: token.toUpperCase() }));
      expect(out.ok).toBe(true);
      if (out.ok) expect(out.value.transactionType).toBe(token);
    }
  });

  it('REFUSES an unlisted token rather than absorbing it into charge', () => {
    for (const token of ['purchase', 'debit', 'POS', 'reversal', 'unknown', '']) {
      const out = normalizeRow(row({ transactionTypeRaw: token }));
      expect(out.ok).toBe(false);
      if (!out.ok) expect(out.refusal.code).toBe('TRANSACTION_TYPE_UNRECOGNISED');
    }
  });

  it('keeps the upstream token verbatim so nothing is lost by the refusal being strict', () => {
    const out = normalizeRow(row({ transactionTypeRaw: 'ChArGe' }));
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.transactionTypeRaw).toBe('ChArGe');
  });
});

describe('direction is read, never inferred', () => {
  it('accepts in and out, case-folded', () => {
    expect(normalizeRow(row({ directionRaw: 'IN' })).ok).toBe(true);
    expect(normalizeRow(row({ directionRaw: ' out ' })).ok).toBe(true);
  });

  it('refuses anything else, including words that merely suggest a direction', () => {
    for (const token of ['', 'debit', 'credit', 'paid', 'received', '-']) {
      const out = normalizeRow(row({ directionRaw: token }));
      expect(out.ok).toBe(false);
      if (!out.ok) expect(out.refusal.code).toBe('DIRECTION_MISSING');
    }
  });
});

describe('payee normalization is information-preserving', () => {
  it('collapses whitespace and folds case', () => {
    expect(normalizePayee('  acme   corp  ')).toBe('ACME CORP');
  });

  it('does NOT strip trailing reference or store numbers, which can distinguish two payees', () => {
    expect(normalizePayee('Store 12')).not.toBe(normalizePayee('Store 34'));
  });

  it('refuses a payee that is empty once trimmed', () => {
    const out = normalizeRow(row({ payeeRaw: '   ' }));
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('PAYEE_MISSING');
  });

  it('keeps merchantRaw verbatim so the normalization is auditable against its input', () => {
    const out = normalizeRow(row({ payeeRaw: '  acme   corp  ' }));
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.merchantRaw).toBe('  acme   corp  ');
  });
});

describe('dates are validated as calendar dates, not merely as shapes', () => {
  it('rejects a well-shaped impossible date', () => {
    expect(isCalendarDate('2026-02-30')).toBe(false);
    expect(isCalendarDate('2026-13-01')).toBe(false);
    expect(isCalendarDate('2026-00-10')).toBe(false);
    expect(isCalendarDate('20260304')).toBe(false);
  });

  it('accepts a real leap day and rejects a fake one', () => {
    expect(isCalendarDate('2024-02-29')).toBe(true);
    expect(isCalendarDate('2026-02-29')).toBe(false);
  });

  it('refuses a malformed occurrence date', () => {
    const out = normalizeRow(row({ occurredAtRaw: '04/03/2026' }));
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('OCCURRED_AT_MALFORMED');
  });

  it('refuses a posting that precedes the movement it posts', () => {
    const out = normalizeRow(row({ occurredAtRaw: '2026-03-04', postedAtRaw: '2026-03-03' }));
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('POSTED_BEFORE_OCCURRED');
  });

  it('accepts an absent posting date as null rather than substituting the occurrence date', () => {
    const out = normalizeRow(row({ postedAtRaw: undefined }));
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.postedAt).toBeNull();
  });
});

describe('every refusal is safe to log and permanent', () => {
  it('carries a code and a locator, and NEVER the offending value', () => {
    const out = normalizeRow(row({ rowRef: 'L7', payeeRaw: '  ' }));
    expect(out.ok).toBe(false);
    if (!out.ok) {
      expect(out.refusal.rowRef).toBe('L7');
      expect(JSON.stringify(out.refusal)).not.toContain('  ');
      expect(Object.keys(out.refusal).sort()).toEqual(['code', 'permanent', 'rowRef']);
    }
  });

  it('marks the refusal permanent, so no caller can justify retrying it', () => {
    const out = normalizeRow(row({ directionRaw: 'sideways' }));
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.permanent).toBe(true);
  });
});
