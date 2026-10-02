/**
 * NIZAM · S5 resolution properties — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S5)
 * Depends on: resolve.ts, normalize.ts, pipeline.types.ts. Every fixture is SYNTHETIC.
 *
 * Two properties carry this file. CURRENCY IS NEVER INFERRED FROM THE ACCOUNT — asserted behaviourally,
 * because the structural guarantee (the function is not given an account) is invisible to a test. And an
 * alias that matches zero OR many accounts is the SAME refusal, because neither identifies an account.
 */
import { describe, it, expect } from 'vitest';
import type { NormalizedRow } from './pipeline.types.ts';
import { normalizeRow } from './normalize.ts';
import {
  resolveAccountId,
  resolveCurrency,
  resolveRow,
  type ResolutionContext,
} from './resolve.ts';

const ALIASES = [
  { alias: 'main', accountId: 'acct_main' },
  { alias: 'card', accountId: 'acct_card' },
];
const CTX: ResolutionContext = { accountAliases: ALIASES, knownCurrencies: ['EGP', 'USD'] };

function normalized(over: Partial<NormalizedRow> = {}): NormalizedRow {
  const base = normalizeRow({
    rowRef: 'L1',
    transactionTypeRaw: 'charge',
    payeeRaw: 'Synthetic Merchant',
    directionRaw: 'out',
    magnitude: 25_000,
    currencyRaw: 'EGP',
    accountAliasRaw: 'main',
    occurredAtRaw: '2026-03-04',
  });
  if (!base.ok) throw new Error('fixture failed to normalize');
  return { ...base.value, ...over };
}

describe('currency is never inferred from the account', () => {
  it('refuses a missing currency even though the account resolves perfectly', () => {
    const out = resolveRow(normalized({ currencyRaw: '' }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('CURRENCY_MISSING');
  });

  it('resolves the same token identically whichever account the row names', () => {
    const viaMain = resolveRow(normalized({ accountAliasRaw: 'main', currencyRaw: 'USD' }), CTX);
    const viaCard = resolveRow(normalized({ accountAliasRaw: 'card', currencyRaw: 'USD' }), CTX);
    expect(viaMain.ok && viaCard.ok).toBe(true);
    if (viaMain.ok && viaCard.ok) expect(viaMain.value.currency).toBe(viaCard.value.currency);
  });

  it('lets a foreign currency land on any account, because an account is not a currency', () => {
    const out = resolveRow(normalized({ accountAliasRaw: 'main', currencyRaw: 'USD' }), CTX);
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.currency).toBe('USD');
  });

  it('refuses a code the store does not know rather than substituting the base currency', () => {
    const out = resolveRow(normalized({ currencyRaw: 'GBP' }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('CURRENCY_UNKNOWN');
  });

  it('folds case, because folding cannot produce a DIFFERENT currency', () => {
    const r = resolveCurrency('egp', ['EGP']);
    expect(r.kind).toBe('ok');
    if (r.kind === 'ok') expect(r.currency).toBe('EGP');
  });

  it('treats a non-three-letter token as missing, not as unknown', () => {
    expect(resolveCurrency('E', ['EGP']).kind).toBe('missing');
    expect(resolveCurrency('EGPX', ['EGP']).kind).toBe('missing');
    expect(resolveCurrency('12', ['EGP']).kind).toBe('missing');
  });
});

describe('an alias must identify exactly one account', () => {
  it('resolves a single match, case- and whitespace-insensitively', () => {
    expect(resolveAccountId('  MAIN ', ALIASES)).toBe('acct_main');
  });

  it('returns nothing for zero matches', () => {
    expect(resolveAccountId('savings', ALIASES)).toBeNull();
  });

  it('returns nothing for MORE than one match — an array keeps the ambiguity a Map would erase', () => {
    const duplicated = [
      { alias: 'main', accountId: 'acct_main' },
      { alias: 'main', accountId: 'acct_other' },
    ];
    expect(resolveAccountId('main', duplicated)).toBeNull();
  });

  it('collapses zero and many into ONE refusal, because the remedy for both is the same question', () => {
    const none = resolveRow(normalized({ accountAliasRaw: 'nope' }), CTX);
    const many = resolveRow(normalized({ accountAliasRaw: 'main' }), {
      ...CTX,
      accountAliases: [
        { alias: 'main', accountId: 'acct_a' },
        { alias: 'main', accountId: 'acct_b' },
      ],
    });
    expect(none.ok).toBe(false);
    expect(many.ok).toBe(false);
    if (!none.ok && !many.ok) {
      expect(none.refusal.code).toBe('ACCOUNT_ALIAS_UNRESOLVED');
      expect(many.refusal.code).toBe('ACCOUNT_ALIAS_UNRESOLVED');
    }
  });

  it('has no default account and no carry-over from a previous row', () => {
    const first = resolveRow(normalized({ rowRef: 'L1', accountAliasRaw: 'main' }), CTX);
    expect(first.ok).toBe(true);
    // The second row names nothing. A "usual account" fallback would make this resolve.
    const second = resolveRow(normalized({ rowRef: 'L2', accountAliasRaw: '' }), CTX);
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.refusal.code).toBe('ACCOUNT_ALIAS_UNRESOLVED');
  });

  it('refuses when the store knows no aliases at all, rather than inventing one', () => {
    const out = resolveRow(normalized(), { accountAliases: [], knownCurrencies: ['EGP'] });
    expect(out.ok).toBe(false);
    if (!out.ok) expect(out.refusal.code).toBe('ACCOUNT_ALIAS_UNRESOLVED');
  });
});

describe('resolution moves no money and keeps its refusals safe', () => {
  it('passes the magnitude through untouched', () => {
    const out = resolveRow(normalized({ magnitude: 777_777 }), CTX);
    expect(out.ok).toBe(true);
    if (out.ok) expect(out.value.magnitude).toBe(777_777);
  });

  it('never puts the offending alias or currency token in the refusal', () => {
    const out = resolveRow(normalized({ accountAliasRaw: 'SECRET-ALIAS' }), CTX);
    expect(out.ok).toBe(false);
    if (!out.ok) expect(JSON.stringify(out.refusal)).not.toContain('SECRET-ALIAS');
  });
});
