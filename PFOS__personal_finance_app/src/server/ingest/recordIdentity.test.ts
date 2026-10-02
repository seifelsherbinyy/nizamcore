/**
 * NIZAM · Shared record identity and the two dedup keys — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S7, §C.1)
 * Depends on: recordIdentity.ts only. Every fixture is SYNTHETIC.
 *
 * These cases assert the properties that make the lift a LIFT rather than a rewrite: the pre-images are
 * unchanged, so ids already in the store still resolve; and the two dedup layers answer different
 * questions on different keys, so neither can be mistaken for the other.
 */
import { describe, it, expect } from 'vitest';
import { createHash } from 'node:crypto';
import {
  accountIdFor,
  contentFingerprint,
  periodKeyOf,
  rawPayloadDigest,
  rowContentHash,
  sourceEventIdFor,
  transactionIdFor,
} from './recordIdentity.ts';

const FP = {
  date: '2026-03-04',
  direction: 'out' as const,
  magnitude: 25_000,
  currency: 'EGP',
  accountId: 'acct_synthetic',
  normalizedPayee: 'SYNTHETIC MERCHANT',
};

describe('the lift preserves every pre-image', () => {
  it('derives an account id from name and last4 under a NUL separator, truncated to 24', () => {
    const expected = `acct_${createHash('sha256')
      .update('Synthetic Account\u00009999', 'utf8')
      .digest('hex')
      .slice(0, 24)}`;
    expect(accountIdFor({ name: 'Synthetic Account', last4: '9999' })).toBe(expected);
  });

  it('derives transaction and source-event ids from the same pre-image with different prefixes', () => {
    const digest = createHash('sha256').update('chan\u0000dupkey', 'utf8').digest('hex');
    expect(transactionIdFor('chan', 'dupkey')).toBe(`txn_${digest.slice(0, 32)}`);
    expect(sourceEventIdFor('chan', 'dupkey')).toBe(`sev_${digest.slice(0, 32)}`);
  });

  it('derives a period key from account and statement month, truncated to 24', () => {
    const expected = `stmt_${createHash('sha256')
      .update('acct_x\u00002026-03', 'utf8')
      .digest('hex')
      .slice(0, 24)}`;
    expect(periodKeyOf('acct_x', '2026-03')).toBe(expected);
  });

  it('renders a null or undefined row part as the empty string, as the original did', () => {
    expect(rowContentHash(['a', null, 'b'])).toBe(rowContentHash(['a', '', 'b']));
    expect(rowContentHash(['a', undefined, 'b'])).toBe(rowContentHash(['a', '', 'b']));
  });
});

describe('the channel is part of the identity', () => {
  it('gives two channels different ids for the same duplicate key', () => {
    expect(transactionIdFor('sms', 'k')).not.toBe(transactionIdFor('statement', 'k'));
  });
});

describe('layer 2 — the normalized record fingerprint', () => {
  it('hashes the magnitude with direction as its own field, so out and in differ', () => {
    expect(contentFingerprint(FP)).not.toBe(contentFingerprint({ ...FP, direction: 'in' }));
  });

  it('is sensitive to every consequential field', () => {
    const base = contentFingerprint(FP);
    expect(contentFingerprint({ ...FP, date: '2026-03-05' })).not.toBe(base);
    expect(contentFingerprint({ ...FP, magnitude: 25_001 })).not.toBe(base);
    expect(contentFingerprint({ ...FP, currency: 'USD' })).not.toBe(base);
    expect(contentFingerprint({ ...FP, accountId: 'acct_other' })).not.toBe(base);
    expect(contentFingerprint({ ...FP, normalizedPayee: 'OTHER' })).not.toBe(base);
  });

  it('is stable across calls, because nothing in it reads a clock or a counter', () => {
    expect(contentFingerprint(FP)).toBe(contentFingerprint(FP));
  });

  it('never admits a decimal rendering of the magnitude into the pre-image', () => {
    // 25000 milliunits and the decimal "25.000" must not collide, because only one of them is a Money.
    expect(contentFingerprint(FP)).not.toBe(
      contentFingerprint({ ...FP, magnitude: Number('25.000') }),
    );
  });
});

describe('layer 1 — the raw evidence digest', () => {
  it('digests the bytes exactly as they arrived, with no trimming or re-casing', () => {
    expect(rawPayloadDigest('  Padded Reply  ')).not.toBe(rawPayloadDigest('Padded Reply'));
    expect(rawPayloadDigest('reply')).not.toBe(rawPayloadDigest('REPLY'));
  });

  it('changes on a single byte, which is what lets S2 report a conflict rather than pick a winner', () => {
    expect(rawPayloadDigest('out 1 EGP acct:a x')).not.toBe(rawPayloadDigest('out 1 EGP acct:a y'));
  });

  it('is a different key from layer 2, so a raw duplicate and an economic duplicate never conflate', () => {
    expect(rawPayloadDigest(JSON.stringify(FP))).not.toBe(contentFingerprint(FP));
  });
});
