/**
 * NIZAM · S6 validation — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S6)
 * Depends on: ./pipeline.types.ts, ./recordIdentity.ts, ../../lib/money/money.ts. Pure, no clock.
 *
 * ## Three INDEPENDENT integrality guards, not one guard called three times
 *
 * A single `isMoney` call is one mechanism, and one mechanism that regresses takes the whole invariant
 * with it. So integrality is asserted three ways that fail for different reasons:
 *
 *   1. SEMANTIC  — the money core's own `isMoney`, which is what the rest of the codebase trusts.
 *   2. ARITHMETIC — `Number.isSafeInteger`, which independently rejects a fraction and anything past
 *                   2^53 where integer arithmetic stops being exact.
 *   3. LEXICAL   — the decimal rendering contains no `.` and no exponent. This is the one that catches
 *                  `1e21`, which IS a safe-integer-shaped float that renders as `1e+21` and would sail
 *                  through a naive check before corrupting a SQL literal downstream.
 *
 * All three must agree. Any disagreement is `AMOUNT_NOT_INTEGER`.
 *
 * ## Why this stage takes `asOf` instead of reading a clock
 *
 * A future-dated row must be refused, which needs today's date — but reading `Date.now()` here would make
 * the stage impure and its tests time-dependent, and would put a clock inside the ingest path where
 * `seedLoad`'s comment already warns against one. The caller supplies `asOf`. A validly BACK-dated row is
 * accepted at the date it states; only a date after `asOf` is refused.
 *
 * ## Where the sign is decided
 *
 * Here, once, from `direction`. Upstream stages carry a non-negative magnitude and a direction token;
 * nothing before this point holds a signed amount, so nothing before this point can get the sign wrong.
 */
import { isMoney, type Money } from '../../lib/money/money.ts';
import {
  type ResolvedRow,
  type StageResult,
  type ValidatedRow,
  err,
  ok,
  refuse,
} from './pipeline.types.ts';
import { contentFingerprint } from './recordIdentity.ts';

export interface ValidationContext {
  /** ISO calendar date the ingest run is anchored to. A row dated after this is refused. */
  readonly asOf: string;
}

/**
 * The three-guard integrality check. Exported so a test can assert each guard independently rather than
 * only observing the combined verdict.
 */
export function isIntegralMoney(value: number): boolean {
  const semantic = isMoney(value);
  const arithmetic = Number.isSafeInteger(value);
  const rendered = String(value);
  const lexical = !rendered.includes('.') && !rendered.includes('e') && !rendered.includes('E');
  return semantic && arithmetic && lexical;
}

/** S6. Assert integrality, ordering and coherence; derive the signed amount and the fingerprint. */
export function validateRow(row: ResolvedRow, ctx: ValidationContext): StageResult<ValidatedRow> {
  const at = row.rowRef;

  if (!isIntegralMoney(row.magnitude)) return err(refuse('AMOUNT_NOT_INTEGER', at));

  // A negative magnitude means the sign was put in the wrong field. That is a different defect from a
  // zero amount, and conflating them would hide it.
  if (row.magnitude < 0) return err(refuse('AMOUNT_DIRECTION_INCOHERENT', at));
  if (row.magnitude === 0) return err(refuse('AMOUNT_NOT_POSITIVE', at));

  if (row.occurredAt > ctx.asOf) return err(refuse('DATE_IN_FUTURE', at));
  if (row.postedAt !== null && row.postedAt > ctx.asOf) return err(refuse('DATE_IN_FUTURE', at));

  const amount: Money = row.direction === 'out' ? -row.magnitude : row.magnitude;

  const fingerprint = contentFingerprint({
    date: row.occurredAt,
    direction: row.direction,
    magnitude: row.magnitude,
    currency: row.currency,
    accountId: row.accountId,
    normalizedPayee: row.normalizedPayee,
  });

  return ok(Object.freeze({ ...row, amount, fingerprint }));
}
