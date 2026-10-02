/**
 * Explicit owner review and candidate promotion — the only path from staging to canonical.
 * Owning authority: Contract 6 §5 I5.1-I5.6 (APPROVED). Phase 1, increment 6 of the
 * transaction-capture-pipeline spec. Every other section of Contract 6 remains DRAFT.
 *
 * Approved clauses, quoted literally because a paraphrase of approved authority is not authority:
 *
 * I5.1: "Authoritative intake for Release 1 is manual entry, account snapshots, and statement-file
 * ingestion (CSV/XLSX/statement parsers), per drive-db.md one-time Picker import."
 *
 * I5.2: "Telegram, SMS and email may only produce candidates in a staging collection distinct from
 * transactions[]. A candidate is not financial truth and MUST NOT be counted in any balance, budget,
 * forecast or report."
 *
 * I5.3: "Promotion of a candidate to canonical requires deterministic parsing plus validation plus the
 * normal review/reconciliation path. approved is a review flag, not an isolation boundary, and MUST NOT
 * be used as a substitute for staging."
 *
 * I5.4: "Provenance is preserved verbatim, including the honest unknown extraction method already
 * modelled in IngestLedgerRow. A machine-extracted row MUST NEVER claim manual."
 *
 * I5.5: "No LLM output may become a monetary value or a canonical row. It may only annotate or propose."
 *
 * I5.6: "Dedupe on promotion uses the existing duplicateKey and preserves both the original and cleaned
 * payee strings."
 *
 * Representation, with no migration. The server table has no approved column and adding one is forbidden.
 * The durable review fact is therefore the audit entry written in the same transaction as the existing
 * row's pending/unverified -> posted/parser transition. The result carries the server tier's one
 * `approved: true` marker for projection into the browser read model. `promotion.invariants.test.ts`
 * proves no other non-test server module sets that marker. Staging remains the isolation boundary.
 *
 * Notification is downstream. The transaction commits and reads back before the notifier is called; a
 * failed notifier never rolls back posting, and a failed posting never calls the notifier. D-J remains
 * proposed, so this module says only durable intent and makes no stronger delivery claim.
 */
import { RepositoryStateError } from '../db/errors.ts';
import { createCandidatesRepository } from '../db/repositories/candidatesRepository.ts';
import { createTransactionsRepository } from '../db/repositories/transactionsRepository.ts';
import { recordAudit, withTransaction, type RepositoryContext } from '../db/repositories/support.ts';
import type { LinkResolution, TransactionRow } from '../db/repositories/rows.ts';

export const PROMOTION_REFUSAL_CODES = [
  'AUTOMATIC_PROMOTION_FORBIDDEN',
  'DETERMINISTIC_PARSE_REQUIRED',
  'VALIDATION_REQUIRED',
  'CANDIDATE_NOT_FOUND',
  'DUPLICATE_KEY_MISSING',
  'DUPLICATE_AMBIGUOUS',
  'DUPLICATE_CONFIRMED',
] as const;
export type PromotionRefusalCode = (typeof PROMOTION_REFUSAL_CODES)[number];

export interface PromotionRefusal {
  readonly code: PromotionRefusalCode;
  readonly candidateId: string;
  /** Structural: a typed refusal is answered with new evidence, never retried. */
  readonly permanent: true;
}

/** One existing canonical match and the owner's explicit disposition of that suspected relationship. */
export interface ResolvedDuplicateLink {
  readonly transactionId: string;
  readonly resolution: LinkResolution;
}

export interface PromotionRequest {
  readonly candidateId: string;
  /** No schedule, score, streak or repetition may satisfy this. */
  readonly trigger: 'explicit_owner_action' | 'scheduler' | 'confidence' | 'streak' | 'repetition';
  readonly deterministicParsePassed: boolean;
  readonly validationPassed: boolean;
  /** Original payee remains in row.payee; the cleaned form is stored separately in row.merchant. */
  readonly cleanedPayee: string;
  /** Category assignment is allowed only now, at review. Null is an explicit no-category decision. */
  readonly categoryId: string | null;
  readonly resolvedLinks: readonly ResolvedDuplicateLink[];
}

export interface PromotionNotifier {
  /** A narrow injected port. No transport is bound in this repository. */
  readonly notifyPosted: (candidateId: string) => Promise<void>;
}

export type PromotionNotification = 'SENT' | 'FAILED' | 'NOT_REQUESTED';

export type PromotionResult =
  | { readonly ok: false; readonly refusal: PromotionRefusal }
  | {
    readonly ok: true;
    readonly row: TransactionRow;
    readonly review: typeof APPROVED_REVIEW;
    readonly alreadyPromoted: boolean;
    readonly notification: PromotionNotification;
  };

/** The one and only server-side assignment of approved=true. */
const APPROVED_REVIEW = Object.freeze({ approved: true as const });

function refusal(candidateId: string, code: PromotionRefusalCode): PromotionResult {
  return Object.freeze({ ok: false as const, refusal: Object.freeze({ code, candidateId, permanent: true as const }) });
}

function isCandidate(row: TransactionRow): boolean {
  return row.status === 'pending' && row.verificationLevel === 'unverified';
}

function wasPromoted(ctx: RepositoryContext, id: string): boolean {
  const raw = ctx.handle.db
    .prepare(`SELECT COUNT(*) AS n FROM audit_log WHERE action = 'candidate.approved' AND entity_id = ?`)
    .get(id) as { n: number } | undefined;
  return Number(raw?.n ?? 0) === 1;
}

/**
 * Perform the atomic review/posting step. The caller-facing wrapper below handles notification only
 * AFTER this returns, which means the transaction is already committed and the canonical row already
 * read back.
 */
function post(request: PromotionRequest, ctx: RepositoryContext): PromotionResult {
  if (request.trigger !== 'explicit_owner_action') {
    return refusal(request.candidateId, 'AUTOMATIC_PROMOTION_FORBIDDEN');
  }
  if (!request.deterministicParsePassed) return refusal(request.candidateId, 'DETERMINISTIC_PARSE_REQUIRED');
  if (!request.validationPassed) return refusal(request.candidateId, 'VALIDATION_REQUIRED');

  const transactions = createTransactionsRepository(ctx);
  const candidates = createCandidatesRepository(ctx);

  return withTransaction(ctx.handle.db, () => {
    const candidate = candidates.getCandidate(request.candidateId);
    if (candidate === null) {
      const existing = transactions.get(request.candidateId);
      // Idempotent owner retry after a committed result: return the row, write no second audit, and do not
      // notify again. An arbitrary posted row is not a promotion; the audit fact must also exist.
      if (existing !== null && existing.status === 'posted' && wasPromoted(ctx, existing.id)) {
        return {
          ok: true,
          row: existing,
          review: APPROVED_REVIEW,
          alreadyPromoted: true,
          notification: 'NOT_REQUESTED',
        };
      }
      return refusal(request.candidateId, 'CANDIDATE_NOT_FOUND');
    }

    if (candidate.duplicateKey === null || candidate.duplicateKey === '') {
      return refusal(candidate.id, 'DUPLICATE_KEY_MISSING');
    }

    const canonicalMatches = transactions
      .findByDuplicateKey(candidate.duplicateKey)
      .filter((row) => row.id !== candidate.id && !isCandidate(row));
    const resolved = new Map(request.resolvedLinks.map((link) => [link.transactionId, link.resolution]));
    for (const match of canonicalMatches) {
      const decision = resolved.get(match.id);
      if (decision === undefined || decision === 'deferred') return refusal(candidate.id, 'DUPLICATE_AMBIGUOUS');
      if (decision === 'confirmed') return refusal(candidate.id, 'DUPLICATE_CONFIRMED');
      // `rejected` means the owner reviewed the suspected relation and decided these are distinct facts.
      const link = transactions.recordLink({
        id: ctx.newId(),
        fromTransactionId: candidate.id,
        toTransactionId: match.id,
        linkType: 'suspected_duplicate',
        confidenceBps: 0,
      });
      transactions.resolveLink(link.id, 'rejected');
    }

    const promoted = transactions.promotePending(candidate.id, {
      cleanedPayee: request.cleanedPayee,
      categoryId: request.categoryId,
    });

    // Approval is a review fact, not the staging boundary. It is recorded here, in the same outer
    // transaction as the status transition, and nowhere else in the server tier.
    recordAudit(ctx, {
      action: 'candidate.approved',
      entityTable: 'transactions',
      entityId: promoted.id,
      detail: 'explicit_owner_action; deterministic_parse=passed; validation=passed',
    });

    return {
      ok: true,
      row: promoted,
      review: APPROVED_REVIEW,
      alreadyPromoted: false,
      notification: 'NOT_REQUESTED',
    };
  });
}

/**
 * Promote one candidate. Never a batch. Notification is attempted only after committed posting and is
 * reported independently; a send failure is not a posting failure.
 */
export async function promoteCandidate(
  request: PromotionRequest,
  ports: { readonly ctx: RepositoryContext; readonly notifier: PromotionNotifier },
): Promise<PromotionResult> {
  let result: PromotionResult;
  try {
    result = post(request, ports.ctx);
  } catch (error) {
    // READBACK_MISMATCH is an exception by requirements §3.5 and must never acknowledge. Preserve the
    // typed repository error rather than translating it into a successful review result.
    if (error instanceof RepositoryStateError) throw error;
    throw error;
  }

  if (!result.ok || result.alreadyPromoted) return result;
  try {
    await ports.notifier.notifyPosted(result.row.id);
    return { ...result, notification: 'SENT' };
  } catch {
    return { ...result, notification: 'FAILED' };
  }
}

export interface PromotionClarificationPort {
  /** Must append the answer through S2 and return the NEW source-event identity. */
  readonly captureNewEvidence: (answer: string) => { readonly sourceEventId: string };
}

/**
 * A refusal is permanent and is never retried. The owner's clarification is a new piece of evidence,
 * appended through S2 by the injected port; promotion is not called from this function.
 */
export function recordPromotionClarification(
  prior: PromotionRefusal,
  answer: string,
  port: PromotionClarificationPort,
): { readonly kind: 'NEW_EVIDENCE'; readonly priorCode: PromotionRefusalCode; readonly sourceEventId: string } {
  if (!prior.permanent) throw new Error('PROMOTION_REFUSAL_NOT_PERMANENT');
  const captured = port.captureNewEvidence(answer);
  return Object.freeze({ kind: 'NEW_EVIDENCE', priorCode: prior.code, sourceEventId: captured.sourceEventId });
}
