/**
 * Staging for rows that are NOT financial truth.
 * Owning authority: PFOS Contract 6 section 5 (APPROVED), clauses I5.2, I5.3 and I5.4.
 * Phase 1, increment 5 of `.kiro/specs/transaction-capture-pipeline/`.
 *
 * I5.2, quoted literally because a paraphrase of an approved clause is an unapproved clause:
 *
 *   "Telegram, SMS and email may only produce candidates in a staging collection distinct from
 *    `transactions[]`. A candidate is not financial truth and MUST NOT be counted in any balance,
 *    budget, forecast or report."
 *
 * I5.3, literally:
 *
 *   "`approved` is a review flag, not an isolation boundary, and MUST NOT be used as a substitute for
 *    staging."
 *
 * I5.4, literally:
 *
 *   "Provenance is preserved verbatim, including the honest `unknown` extraction method already
 *    modelled in `IngestLedgerRow`. A machine-extracted row MUST NEVER claim `manual`."
 *
 * WHAT A CANDIDATE IS, AND WHY NO MIGRATION HAPPENED HERE. A candidate is already modelled: a row in
 * `transactions` whose `status` is 'pending' AND whose `verification_level` is 'unverified'. Both values
 * are already in the DDL's CHECK constraints, so this module adds no table, no column and no enum, and
 * `SCHEMA_VERSION` does not move. The conjunction is what marks a candidate, not either half alone: the
 * canonical ledger loader writes `status: 'posted'` with `verification_level` 'parser' or 'unverified'
 * (`src/server/ingest/seedLoad.ts:301,304`), so 'posted' + 'unverified' is a legitimate canonical row and
 * only 'pending' + 'unverified' is staged.
 *
 * HOW ISOLATION IS ENFORCED - by structure, never by a parameter a caller can get wrong:
 *  - `CandidateInsert` is `TransactionInsert` with `status` and `verificationLevel` REMOVED. The fields
 *    do not exist on the input type, so no caller can stage a row as 'posted'. This module pins both
 *    values itself and there is no code path that sets any other.
 *  - There is no method here that returns candidates and canonical rows together, and none that takes a
 *    flag to widen a read. Every read is hard-filtered to the conjunction.
 *  - This module cannot approve anything. Promotion is increment 6's and belongs to exactly one place.
 *    `candidatesRepository.invariants.test.ts` asserts that against this file's own text, in the style
 *    AC19's protected-invariants check already uses.
 */
import { RepositoryStateError } from '../errors.ts';
import type { TransactionInsert, TransactionRow } from './rows.ts';
import { withTransaction, type RepositoryContext } from './support.ts';
import { createTransactionsRepository, type InsertOrGetResult } from './transactionsRepository.ts';

const TABLE = 'transactions';

/** The two values that together mark a row as staged rather than canonical. Pinned, never passed in. */
export const CANDIDATE_STATUS = 'pending' as const;
export const CANDIDATE_VERIFICATION_LEVEL = 'unverified' as const;

/**
 * A candidate to stage. `status` and `verificationLevel` are deliberately ABSENT: they are the isolation
 * boundary, so allowing a caller to supply them would make the boundary a parameter rather than a
 * property, which is exactly what I5.3 forbids for `approved`.
 */
export type CandidateInsert = Omit<TransactionInsert, 'status' | 'verificationLevel'>;

export interface CandidatesRepository {
  /**
   * Stage a candidate. Idempotent on the content-derived id: a second identical call inserts nothing and
   * returns the row that already exists. Reuses the F19 conflict-ignoring insert plus read-back, so the
   * INSERT is the decision and no fifth idempotency mechanism is introduced.
   */
  stage(input: CandidateInsert): InsertOrGetResult;
  /** A candidate by id. Returns null for a canonical row, so a caller cannot reach one through here. */
  getCandidate(id: string): TransactionRow | null;
  /** Every staged row for an account. Hard-filtered; there is no parameter that widens this. */
  listCandidatesForAccount(accountId: string): TransactionRow[];
  /** How many rows are staged. For a report that must state a count WITHOUT counting the money. */
  countCandidates(): number;
  /**
   * The canonical read path, which is here precisely so the I5.2 separation is one file's responsibility
   * and is testable against a non-empty baseline. It EXCLUDES the candidate conjunction. This exists
   * because `transactionsRepository.listForAccount` does not exclude it - see the note on that below.
   */
  listCanonicalForAccount(accountId: string): TransactionRow[];
}

const CANDIDATE_PREDICATE = `status = '${CANDIDATE_STATUS}' AND verification_level = '${CANDIDATE_VERIFICATION_LEVEL}'`;
const CANONICAL_PREDICATE = `NOT (${CANDIDATE_PREDICATE})`;

export function createCandidatesRepository(ctx: RepositoryContext): CandidatesRepository {
  const { db } = ctx.handle;
  const transactions = createTransactionsRepository(ctx);

  const readCandidate = (id: string): TransactionRow | null => {
    const row = transactions.get(id);
    if (row === null) return null;
    // A canonical row reached through a candidate accessor is not a near miss, it is the I5.2 defect.
    if (row.status !== CANDIDATE_STATUS || row.verificationLevel !== CANDIDATE_VERIFICATION_LEVEL) return null;
    return row;
  };

  const idsWhere = (predicate: string, accountId: string): TransactionRow[] => {
    const raws = db
      .prepare(`SELECT id FROM ${TABLE} WHERE account_id = ? AND ${predicate} ORDER BY transaction_date, id`)
      .all(accountId) as { id: string }[];
    const out: TransactionRow[] = [];
    for (const raw of raws) {
      const row = transactions.get(raw.id);
      if (row !== null) out.push(row);
    }
    return out;
  };

  return {
    stage(input: CandidateInsert): InsertOrGetResult {
      // This outer transaction is essential: `transactions.insertOrGet` joins it through withTransaction's
      // WeakSet, so every STORED-VALUE assertion below runs before commit. A forged provenance or broken
      // isolation marker therefore rolls the insert back rather than leaving a row this method refused.
      return withTransaction(db, () => {
        const result = transactions.insertOrGet({
          ...input,
          // Pinned here and nowhere else. There is no branch that can produce another pair.
          status: CANDIDATE_STATUS,
          verificationLevel: CANDIDATE_VERIFICATION_LEVEL,
        });

        // I5.4 is asserted on the STORED value read back from the database, not on the argument that was
        // passed in, because an argument proves what a caller intended and only a read-back proves what the
        // database holds. Every row staged by this repository is machine-created, so `manual` is forbidden
        // regardless of what the caller claimed.
        if (result.row.provenance.extractionMethod === 'manual') {
          throw new RepositoryStateError(
            'CANDIDATE_PROVENANCE_FORGED',
            `staged row ${result.row.id} read back as manual provenance, which a machine-created row may never claim`,
            { table: TABLE, rowId: result.row.id },
          );
        }
        if (result.row.status !== CANDIDATE_STATUS || result.row.verificationLevel !== CANDIDATE_VERIFICATION_LEVEL) {
          throw new RepositoryStateError(
            'CANDIDATE_ISOLATION_BROKEN',
            `staged row ${result.row.id} read back as ${result.row.status}/${result.row.verificationLevel}`,
            { table: TABLE, rowId: result.row.id },
          );
        }
        return result;
      });
    },

    getCandidate(id: string): TransactionRow | null {
      return readCandidate(id);
    },

    listCandidatesForAccount(accountId: string): TransactionRow[] {
      return idsWhere(CANDIDATE_PREDICATE, accountId);
    },

    countCandidates(): number {
      const raw = db.prepare(`SELECT COUNT(*) AS n FROM ${TABLE} WHERE ${CANDIDATE_PREDICATE}`).get() as
        | { n: number }
        | undefined;
      return Number(raw?.n ?? 0);
    },

    listCanonicalForAccount(accountId: string): TransactionRow[] {
      return idsWhere(CANONICAL_PREDICATE, accountId);
    },
  };
}
