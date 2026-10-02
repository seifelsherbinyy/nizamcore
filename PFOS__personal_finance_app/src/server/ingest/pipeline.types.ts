/**
 * NIZAM · Shared ingest pipeline row shapes and the refusal taxonomy — increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S4–S7)
 * Depends on: ../../lib/money/money.ts and ../../lib/money/currency.ts (types only)
 *
 * ## The one rule these types exist to make mechanical
 *
 * Every stage narrows, and every stage either produces its output or produces a REFUSAL. There is no
 * partial row, no "best effort" row, and no field that quietly holds a guess. A stage that cannot
 * determine a value does not choose one.
 *
 * ## Why the refusal carries no value
 *
 * `IngestRefusal` holds a code and a locator, never the offending text. A refusal is logged, surfaced
 * and sometimes mirrored, and the offending text is by definition unvalidated owner financial data. The
 * same rule `dailyCapture.CaptureRefusal` and `StrictMoneyError` already follow, for the same reason.
 *
 * ## Why a refusal is permanent
 *
 * `permanent: true` is structural rather than documented. A malformed line does not become well formed
 * because it is retried, so a retry loop around a typed refusal is an infinite loop that also hides the
 * defect. What a typed refusal needs is a clarifying question to the owner. Only TRANSPORT failures
 * retry, and those are not `IngestRefusal` at all.
 */
import type { CurrencyCode } from '../../lib/money/currency.ts';
import type { Money } from '../../lib/money/money.ts';
import type { IngestDirection } from './recordIdentity.ts';

/**
 * Every way a row can be refused by S4 through S7. Flat and closed: an exhaustive `switch` over this
 * union is a compile error the moment a code is added without a message for it.
 */
export const INGEST_REFUSAL_CODES = [
  // S4 normalization
  'TRANSACTION_TYPE_UNRECOGNISED',
  'DIRECTION_MISSING',
  'PAYEE_MISSING',
  'OCCURRED_AT_MALFORMED',
  'POSTED_BEFORE_OCCURRED',
  // S5 resolution
  'ACCOUNT_ALIAS_UNRESOLVED',
  'CURRENCY_MISSING',
  'CURRENCY_UNKNOWN',
  // S6 validation
  'AMOUNT_NOT_INTEGER',
  'AMOUNT_NOT_POSITIVE',
  'AMOUNT_DIRECTION_INCOHERENT',
  'DATE_IN_FUTURE',
  // S7 deduplication
  'DEDUPE_COMPARISON_NOT_RUN',
] as const;
export type IngestRefusalCode = (typeof INGEST_REFUSAL_CODES)[number];

/**
 * A refusal. Carries WHERE and WHY, never WHAT.
 *
 * `rowRef` is an opaque caller-supplied locator — a line number, a sheet cell, a page — so the owner can
 * be pointed at the input without the input being reproduced.
 */
export interface IngestRefusal {
  readonly code: IngestRefusalCode;
  readonly rowRef: string;
  /** Always true. A typed refusal is never retried; it is answered. */
  readonly permanent: true;
  /** The sub-code from the money core, where one applies. Still never the value. */
  readonly strictMoneyCode?: string;
}

export function refuse(
  code: IngestRefusalCode,
  rowRef: string,
  strictMoneyCode?: string,
): IngestRefusal {
  return Object.freeze(
    strictMoneyCode === undefined
      ? { code, rowRef, permanent: true as const }
      : { code, rowRef, permanent: true as const, strictMoneyCode },
  );
}

/** A stage result. Either the narrowed row, or the reason there is not one. */
export type StageResult<T> = { readonly ok: true; readonly value: T } | { readonly ok: false; readonly refusal: IngestRefusal };

export const ok = <T>(value: T): StageResult<T> => Object.freeze({ ok: true as const, value });
export const err = <T>(refusal: IngestRefusal): StageResult<T> => Object.freeze({ ok: false as const, refusal });

/**
 * S3's output. Strings, because nothing has been interpreted yet — except the amount, which the channel
 * adapter parsed through the money core's STRICT boundary and therefore already holds as integer
 * milliunits. No adapter parses an amount loosely; per ADR-0003 D7-C an edge relay forwards bytes.
 */
export interface ExtractedRow {
  /** Opaque locator for refusals. Never content. */
  readonly rowRef: string;
  /** Verbatim upstream token for the type. Kept for provenance even after normalization. */
  readonly transactionTypeRaw: string;
  /** Verbatim upstream merchant/payee text. */
  readonly payeeRaw: string;
  readonly directionRaw: string;
  /** Non-negative integer milliunits. The SIGN lives in `directionRaw`, never here. */
  readonly magnitude: Money;
  readonly currencyRaw: string;
  /** The alias the source names. Resolution is S5's job, not the adapter's. */
  readonly accountAliasRaw: string;
  /** ISO calendar date the movement occurred. */
  readonly occurredAtRaw: string;
  /** ISO calendar date it posted, where the source states one. */
  readonly postedAtRaw?: string;
  /** Owner-editable annotation. Deliberately NOT part of any identity. */
  readonly memo?: string;
}

/** Closed vocabulary. An unlisted token is refused, never folded into `charge`. */
export const INGEST_TRANSACTION_TYPES = [
  'charge',
  'payment',
  'fee',
  'interest',
  'transfer',
  'salary',
] as const;
export type IngestTransactionType = (typeof INGEST_TRANSACTION_TYPES)[number];

/** S4's output. Interpreted, but not yet bound to an account or a currency the store knows. */
export interface NormalizedRow extends ExtractedRow {
  readonly normalizedPayee: string;
  /** Verbatim, so the normalization is auditable against its input. */
  readonly merchantRaw: string;
  readonly transactionType: IngestTransactionType;
  readonly direction: IngestDirection;
  readonly occurredAt: string;
  readonly postedAt: string | null;
}

/** S5's output. The account and currency are now store identities rather than source text. */
export interface ResolvedRow extends NormalizedRow {
  readonly accountId: string;
  readonly currency: CurrencyCode;
}

/** S6's output. The signed amount is derived HERE and nowhere else. */
export interface ValidatedRow extends ResolvedRow {
  /** Signed: negative for `out`, positive for `in`. Derived from magnitude plus direction. */
  readonly amount: Money;
  /** Layer-2 fingerprint over the consequential fields. */
  readonly fingerprint: string;
}
