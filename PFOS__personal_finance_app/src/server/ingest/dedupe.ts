/**
 * NIZAM · S7 deduplication — spec transaction-capture-pipeline, increment 2
 * Implemented by: PFOS Contract 06 / Phase 2.3 (shared ingest core; design §B/S7)
 * Depends on: ./pipeline.types.ts, ./recordIdentity.ts. Pure: no repository, no I/O, no clock.
 *
 * ## This is LAYER 2 only
 *
 * Layer 1 — "did this exact source artifact already arrive" — belongs to S2 and is keyed on
 * `(channel, idempotencyKey)` over the raw bytes. It runs BEFORE parsing and a raw duplicate caught there
 * never reaches this file. See `recordIdentity.ts` for both keys side by side.
 *
 * This file answers the different question: do two DIFFERENT source artifacts describe the same economic
 * event? It cannot run earlier because it reads `normalizedPayee`, which does not exist until S4.
 *
 * ## Nothing here deletes anything, ever
 *
 * A same-day, same-amount, same-payee repeat is LEGITIMATE — two coffees. So a collision is surfaced and
 * linked, never resolved by deletion, and the original source is retained. `resolution` starts `null` and
 * only an owner act (S9) closes it. The only uniqueness in the store comes from the content-derived
 * primary key; `duplicate_key` is indexed but NOT unique, precisely so a legitimate repeat can exist.
 *
 * ## Fail closed, structurally
 *
 * `DuplicateEvidence` is a discriminated union whose `comparisonRan: false` arm carries no matches at all.
 * An un-run comparison therefore cannot be mistaken for "no duplicates found" — the two are different
 * types, and the first one refuses with `DEDUPE_COMPARISON_NOT_RUN`. An empty array means the comparison
 * ran and found nothing; absence of the array means it never ran.
 *
 * ## Integer basis points, never a float score
 *
 * Confidence is `confidence_bps`, an integer in 0..10000, matching the DDL's CHECK. A float "0.92" would
 * be a money-adjacent float in a financial table, and the codebase does not have those.
 */
import {
  type StageResult,
  type ValidatedRow,
  err,
  ok,
  refuse,
} from './pipeline.types.ts';

const FIELD_SEP = '\u0000';

/** Exact agreement on every consequential field. The fingerprints matched. */
export const CONFIDENCE_EXACT_BPS = 10_000;
/** Same account, date and signed amount, but the payee differs. Enough to link, not to conclude. */
export const CONFIDENCE_PARTIAL_BPS = 5_000;

/** Matches the DDL `link_type` CHECK on `transaction_links`. No new link type is introduced. */
export type DedupeLinkType = 'suspected_duplicate' | 'pending_to_posted';

/** Settlement state of an existing record, which decides link type rather than duplicate status. */
export type SettlementState = 'pending' | 'posted';

/**
 * The duplicate key. Keyed on `accountId` and the DERIVED SIGNED amount — repairing F9, where the key
 * used a display name and the pre-fix sign, so an unsigned export collided across directions.
 *
 * `normalizedPayee` is deliberately absent: it belongs to the fingerprint. Keeping it out here means two
 * records with the same money movement and a differently spelled payee still collide into the same
 * bucket and get COMPARED, instead of never meeting.
 */
export function duplicateKeyFor(row: {
  readonly accountId: string;
  readonly occurredAt: string;
  readonly amount: number;
  readonly currency: string;
}): string {
  return [row.accountId, row.occurredAt, String(row.amount), row.currency].join(FIELD_SEP);
}

/** An already-stored record, as far as this stage needs to know about one. */
export interface ExistingRecord {
  readonly transactionId: string;
  readonly fingerprint: string;
  readonly duplicateKey: string;
  readonly settlement: SettlementState;
}

/**
 * What the caller found. The `false` arm has no `matches` field, so "did not look" is unrepresentable as
 * "looked and found nothing".
 */
export type DuplicateEvidence =
  | { readonly comparisonRan: false }
  | { readonly comparisonRan: true; readonly matches: readonly ExistingRecord[] };

/** A link this stage proposes. The caller persists it; this stage writes nothing. */
export interface ProposedLink {
  readonly toTransactionId: string;
  readonly linkType: DedupeLinkType;
  readonly confidenceBps: number;
  /** Always null from here. Only an owner act sets it. */
  readonly resolution: null;
}

export type DuplicateStatus = 'unique' | 'duplicate' | 'ambiguous';

export interface DedupeVerdict {
  readonly duplicateKey: string;
  readonly fingerprint: string;
  readonly duplicateStatus: DuplicateStatus;
  readonly links: readonly ProposedLink[];
}

/**
 * S7. Classify the row against evidence the caller gathered.
 *
 * Returns a verdict; persists nothing and deletes nothing.
 */
export function classifyDuplicate(
  row: ValidatedRow,
  evidence: DuplicateEvidence,
  settlement: SettlementState = 'posted',
): StageResult<DedupeVerdict> {
  if (!evidence.comparisonRan) return err(refuse('DEDUPE_COMPARISON_NOT_RUN', row.rowRef));

  const duplicateKey = duplicateKeyFor(row);
  const links: ProposedLink[] = [];
  let sawExactDuplicate = false;
  let sawPartial = false;

  for (const match of evidence.matches) {
    // A pending record and its posted settlement are the SAME movement seen twice by design. That is a
    // lifecycle link, not a duplicate, and calling it a duplicate would suppress a real posting.
    if (match.settlement !== settlement) {
      links.push(
        Object.freeze({
          toTransactionId: match.transactionId,
          linkType: 'pending_to_posted' as const,
          confidenceBps: CONFIDENCE_EXACT_BPS,
          resolution: null,
        }),
      );
      continue;
    }

    if (match.fingerprint === row.fingerprint) {
      sawExactDuplicate = true;
      links.push(
        Object.freeze({
          toTransactionId: match.transactionId,
          linkType: 'suspected_duplicate' as const,
          confidenceBps: CONFIDENCE_EXACT_BPS,
          resolution: null,
        }),
      );
      continue;
    }

    if (match.duplicateKey === duplicateKey) {
      sawPartial = true;
      links.push(
        Object.freeze({
          toTransactionId: match.transactionId,
          linkType: 'suspected_duplicate' as const,
          confidenceBps: CONFIDENCE_PARTIAL_BPS,
          resolution: null,
        }),
      );
    }
  }

  // `unique` is only reachable because the comparison demonstrably ran and produced nothing.
  const duplicateStatus: DuplicateStatus = sawExactDuplicate
    ? 'duplicate'
    : sawPartial
      ? 'ambiguous'
      : 'unique';

  return ok(
    Object.freeze({
      duplicateKey,
      fingerprint: row.fingerprint,
      duplicateStatus,
      links: Object.freeze(links),
    }),
  );
}
