/**
 * NIZAM · S4 normalization — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S4)
 * Depends on: ./pipeline.types.ts only. Pure, channel-agnostic, no I/O.
 *
 * ## The invariant this stage is built around
 *
 * NORMALIZATION MOVES NO MONEY. It reads `magnitude` and passes it through unchanged; it never rounds,
 * re-scales, re-signs or re-parses it. The amount arrives as integer milliunits from the money core's
 * strict boundary and leaves as the same integer. A property test asserts byte-identical amounts in and
 * out, because this is exactly the stage where a well-meant "clean up" would silently misstate a figure.
 *
 * ## What normalization is allowed to do
 *
 * Fold case and collapse whitespace on the payee, map a closed vocabulary token, and validate dates.
 * That is all. Each of those is information-preserving or refusing — none of them can invent a value.
 *
 * ## Why an unrecognised type is refused rather than defaulted
 *
 * `charge` is the commonest type, which makes it the most tempting default and the most dangerous one: a
 * mis-defaulted `payment` or `transfer` double-counts consumption. So the vocabulary is closed and an
 * unlisted token produces `TRANSACTION_TYPE_UNRECOGNISED`. The upstream token survives verbatim in
 * `transactionTypeRaw`, so nothing is lost and a later mapping can be added deliberately.
 */
import {
  INGEST_TRANSACTION_TYPES,
  type ExtractedRow,
  type IngestTransactionType,
  type NormalizedRow,
  type StageResult,
  err,
  ok,
  refuse,
} from './pipeline.types.ts';
import type { IngestDirection } from './recordIdentity.ts';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** A real calendar date, not merely a well-shaped string. `2026-02-30` is refused. */
export function isCalendarDate(value: string): boolean {
  if (!ISO_DATE.test(value)) return false;
  const [y, m, d] = value.split('-').map(Number) as [number, number, number];
  if (m < 1 || m > 12 || d < 1) return false;
  const date = new Date(Date.UTC(y, m - 1, d));
  return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d;
}

/**
 * Deterministic payee normalization: trim, collapse internal whitespace, fold to upper case.
 *
 * Deliberately conservative. It does NOT strip reference numbers, branch codes or store numbers, because
 * those sometimes distinguish two genuinely different payees, and a normalizer that merges them would
 * silently merge their fingerprints too. Folding case cannot produce a DIFFERENT payee; stripping tokens
 * can.
 */
export function normalizePayee(raw: string): string {
  return raw.trim().replace(/\s+/gu, ' ').toUpperCase();
}

function asTransactionType(token: string): IngestTransactionType | null {
  const folded = token.trim().toLowerCase();
  return (INGEST_TRANSACTION_TYPES as readonly string[]).includes(folded)
    ? (folded as IngestTransactionType)
    : null;
}

function asDirection(token: string): IngestDirection | null {
  const folded = token.trim().toLowerCase();
  return folded === 'in' || folded === 'out' ? folded : null;
}

/**
 * S4. Narrow an extracted row to a normalized one, or refuse it.
 *
 * Order matters only in that each check is independent and the first failure wins; no later check can
 * repair an earlier one, and none of them mutates the input.
 */
export function normalizeRow(row: ExtractedRow): StageResult<NormalizedRow> {
  const at = row.rowRef;

  const direction = asDirection(row.directionRaw);
  if (direction === null) return err(refuse('DIRECTION_MISSING', at));

  const transactionType = asTransactionType(row.transactionTypeRaw);
  if (transactionType === null) return err(refuse('TRANSACTION_TYPE_UNRECOGNISED', at));

  const normalizedPayee = normalizePayee(row.payeeRaw);
  if (normalizedPayee === '') return err(refuse('PAYEE_MISSING', at));

  if (!isCalendarDate(row.occurredAtRaw)) return err(refuse('OCCURRED_AT_MALFORMED', at));

  let postedAt: string | null = null;
  if (row.postedAtRaw !== undefined && row.postedAtRaw !== '') {
    if (!isCalendarDate(row.postedAtRaw)) return err(refuse('OCCURRED_AT_MALFORMED', at));
    // A posting cannot precede the movement it posts. This is an ordering fact, not a preference.
    if (row.postedAtRaw < row.occurredAtRaw) return err(refuse('POSTED_BEFORE_OCCURRED', at));
    postedAt = row.postedAtRaw;
  }

  return ok(
    Object.freeze({
      ...row,
      normalizedPayee,
      merchantRaw: row.payeeRaw,
      transactionType,
      direction,
      occurredAt: row.occurredAtRaw,
      postedAt,
    }),
  );
}
