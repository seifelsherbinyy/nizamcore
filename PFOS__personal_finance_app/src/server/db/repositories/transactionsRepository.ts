/**
 * NIZAM · transactions repository — contract 06 §3.2, §4.2, §8.1 (R1, R2)
 * Implemented by: PFOS Contract 06 / Phase 1.2 (spec 06-two-agent-vps)
 * Depends on: ../moneyBoundary.ts, ../errors.ts, rows.ts, support.ts
 *
 * Two contract rules shape this surface, and both are structural rather than advisory:
 *
 *  CORRECTION IS BY SUPERSEDING ROW (§8.1). `supersede` INSERTS the corrected row, points it
 *  at its predecessor through `supersedes_transaction_id`, bumps `audit_version`, and moves
 *  the predecessor's `status` to 'superseded' so derived balances stop counting it. The
 *  predecessor's monetary columns, dates, and payee are never altered and the row is never
 *  deleted: history stays legible, which is the whole reason those two columns exist. A
 *  second correction of an already-superseded row is REFUSED rather than allowed to fork the
 *  chain, because two successors would make "the current row" ambiguous.
 *
 *  A SUSPECTED DUPLICATE IS NEVER AUTO-DELETED (contract 02 §5.2, §3.2). There is no delete
 *  on this repository at all. A suspicion is RECORDED in `transaction_links` with a
 *  confidence in integer basis points, and settled later by an explicit resolution that
 *  likewise removes nothing.
 *
 * Every write asserts its monetary values through the boundary guard BEFORE a statement is
 * prepared (§4.2.3). `amount` is signed; `outflow` and `inflow` are non-negative magnitudes
 * (money-rules §4), which the DDL also checks.
 */
import { assertMonetaryCoverage, assertMoneyField } from '../moneyBoundary.ts';
import { RepositoryStateError } from '../errors.ts';
import type { ConfidenceBand, IngestExtractionMethod } from '../../../lib/ledger/ledger.types.ts';
import {
  DEFAULT_CURRENCY,
  type LedgerTransactionType,
  type LinkResolution,
  type TransactionInsert,
  type TransactionProvenance,
  type TransactionLinkInsert,
  type TransactionLinkRow,
  type TransactionLinkType,
  type TransactionRow,
  type TransactionStatus,
  type VerificationLevel,
} from './rows.ts';
import { recordAudit, toNullableText, withTransaction, type RepositoryContext } from './support.ts';

const TABLE = 'transactions';
const LINK_TABLE = 'transaction_links';

/** The monetary columns of `transactions`, named once for the coverage assertion. */
const MONEY_FIELDS = ['amount', 'outflow', 'inflow'] as const;

export interface TransactionListFilter {
  /** Inclusive lower bound on `transaction_date` (ISO date). */
  readonly from?: string;
  /** Inclusive upper bound on `transaction_date` (ISO date). */
  readonly to?: string;
  /** Superseded rows are excluded by default; an audit read asks for them explicitly. */
  readonly includeSuperseded?: boolean;
}

/** What a correction produced: the frozen predecessor and the row that replaces it. */
export interface SupersedeResult {
  readonly superseded: TransactionRow;
  readonly replacement: TransactionRow;
  readonly link: TransactionLinkRow;
}

/** What `insertOrGet` decided: the row that now exists, and whether THIS call is the one that wrote it. */
export interface InsertOrGetResult {
  readonly row: TransactionRow;
  readonly inserted: boolean;
}

export interface TransferPairResult {
  readonly outflow: TransactionRow;
  readonly inflow: TransactionRow;
  readonly link: TransactionLinkRow;
}

export interface TransactionsRepository {
  insert(input: TransactionInsert): TransactionRow;
  /** F19: conflict-ignoring insert plus read-back in one transaction. The insert is the decision. */
  insertOrGet(input: TransactionInsert): InsertOrGetResult;
  /**
   * Increment 6's single-writer transition. Promotes an existing staged row in place; no new identity,
   * no delete, and no second SQL writer outside this repository.
   */
  promotePending(id: string, edit: { readonly cleanedPayee: string; readonly categoryId: string | null }): TransactionRow;
  /** Insert both transfer legs and their link in one transaction; a one-legged return is impossible. */
  insertTransferPair(outflow: TransactionInsert, inflow: TransactionInsert): TransferPairResult;
  get(id: string): TransactionRow | null;
  listForAccount(accountId: string, filter?: TransactionListFilter): TransactionRow[];
  /** Canonical dedup lookup. Staged candidates are structurally excluded; superseded facts remain. */
  findByDuplicateKey(duplicateKey: string): TransactionRow[];
  /** Correct a row by appending its replacement. Nothing is edited away and nothing deleted. */
  supersede(originalId: string, replacement: TransactionInsert): SupersedeResult;
  /** Record a relationship between two rows — never a deletion. */
  recordLink(input: TransactionLinkInsert): TransactionLinkRow;
  listLinks(transactionId: string): TransactionLinkRow[];
  /** Settle a recorded suspicion. Removes nothing; only the resolution columns are set. */
  resolveLink(linkId: string, resolution: LinkResolution): TransactionLinkRow;
}

/**
 * Absent provenance is UNKNOWN provenance — spec 08 task A2.4 (K4, finding F23).
 *
 * A write path that does not state where a row came from gets `unknown` and empty references, never a
 * plausible-looking default. That keeps K4 checkable by query rather than by trusting the loader: a row
 * claiming `manual` was entered by a human, and nothing else may say so.
 */
const UNKNOWN_PROVENANCE: TransactionProvenance = {
  sourceFile: '',
  sourcePageOrSheet: '',
  extractionMethod: 'unknown',
  extractionMethodRaw: '',
  transactionTypeRaw: '',
  confidenceBps: null,
  confidenceBand: null,
  confidenceReason: '',
};

function mapProvenance(raw: Record<string, unknown>): TransactionProvenance {
  const bps = raw['confidence_bps'];
  const band = toNullableText(raw['confidence_band']);
  return {
    sourceFile: String(raw['source_file'] ?? ''),
    sourcePageOrSheet: String(raw['source_page_or_sheet'] ?? ''),
    extractionMethod: String(raw['extraction_method'] ?? 'unknown') as IngestExtractionMethod,
    extractionMethodRaw: String(raw['extraction_method_raw'] ?? ''),
    transactionTypeRaw: String(raw['transaction_type_raw'] ?? ''),
    confidenceBps: bps === null || bps === undefined ? null : Number(bps),
    confidenceBand: band === null ? null : (band as ConfidenceBand),
    confidenceReason: String(raw['confidence_reason'] ?? ''),
  };
}

function mapRow(raw: Record<string, unknown>): TransactionRow {
  return {
    provenance: mapProvenance(raw),
    id: String(raw['id']),
    accountId: String(raw['account_id']),
    sourceEventId: toNullableText(raw['source_event_id']),
    transactionDate: String(raw['transaction_date']),
    postingDate: toNullableText(raw['posting_date']),
    payee: String(raw['payee']),
    merchant: String(raw['merchant']),
    memo: String(raw['memo']),
    categoryId: toNullableText(raw['category_id']),
    transactionType: String(raw['transaction_type']) as LedgerTransactionType,
    amount: Number(raw['amount']),
    outflow: Number(raw['outflow']),
    inflow: Number(raw['inflow']),
    currency: String(raw['currency']),
    status: String(raw['status']) as TransactionStatus,
    verificationLevel: String(raw['verification_level']) as VerificationLevel,
    supersedesTransactionId: toNullableText(raw['supersedes_transaction_id']),
    auditVersion: Number(raw['audit_version']),
    duplicateKey: toNullableText(raw['duplicate_key']),
    createdAt: String(raw['created_at']),
    updatedAt: String(raw['updated_at']),
  };
}

function mapLinkRow(raw: Record<string, unknown>): TransactionLinkRow {
  const resolution = toNullableText(raw['resolution']);
  return {
    id: String(raw['id']),
    fromTransactionId: String(raw['from_transaction_id']),
    toTransactionId: String(raw['to_transaction_id']),
    linkType: String(raw['link_type']) as TransactionLinkType,
    confidenceBps: Number(raw['confidence_bps']),
    createdAt: String(raw['created_at']),
    resolvedAt: toNullableText(raw['resolved_at']),
    resolution: resolution === null ? null : (resolution as LinkResolution),
  };
}

export function createTransactionsRepository(ctx: RepositoryContext): TransactionsRepository {
  const { db } = ctx.handle;

  const readOne = (id: string): TransactionRow | null => {
    const raw = db.prepare(`SELECT * FROM ${TABLE} WHERE id = ?`).get(id) as Record<string, unknown> | undefined;
    return raw ? mapRow(raw) : null;
  };

  const requireOne = (id: string): TransactionRow => {
    const row = readOne(id);
    if (!row) {
      throw new RepositoryStateError('REPOSITORY_ROW_NOT_FOUND', `NIZAM store: no ${TABLE} row with id ${id}`, {
        table: TABLE,
        rowId: id,
      });
    }
    return row;
  };

  const readLink = (id: string): TransactionLinkRow | null => {
    const raw = db.prepare(`SELECT * FROM ${LINK_TABLE} WHERE id = ?`).get(id) as Record<string, unknown> | undefined;
    return raw ? mapLinkRow(raw) : null;
  };

  const requireLink = (id: string): TransactionLinkRow => {
    const row = readLink(id);
    if (!row) {
      throw new RepositoryStateError('REPOSITORY_ROW_NOT_FOUND', `NIZAM store: no ${LINK_TABLE} row with id ${id}`, {
        table: LINK_TABLE,
        rowId: id,
      });
    }
    return row;
  };

  /**
   * The one INSERT statement. `supersedesTransactionId` and `auditVersion` are set by the
   * correction path and by nothing else, so an ordinary insert cannot claim to supersede.
   */
  const insertRow = (
    input: TransactionInsert,
    lineage: { supersedesTransactionId: string | null; auditVersion: number },
    onConflict: 'THROW' | 'RETURN_EXISTING' = 'THROW',
  ): { row: TransactionRow; inserted: boolean } => {
    // The guard runs first, and it accounts for every monetary column of the table.
    assertMonetaryCoverage(TABLE, MONEY_FIELDS);
    const amount = assertMoneyField(TABLE, 'amount', input.amount);
    const outflow = assertMoneyField(TABLE, 'outflow', input.outflow);
    const inflow = assertMoneyField(TABLE, 'inflow', input.inflow);
    const at = ctx.now();

    const provenance = input.provenance ?? UNKNOWN_PROVENANCE;

    // Nothing above threw, so a statement may now be prepared.
    //
    // F19: the insert IS the decision. `ON CONFLICT(id) DO NOTHING` makes a second attempt at the same
    // content-derived id a no-op inside the engine rather than a race between a preceding read and this
    // write. `changes` then reports which of the two callers won, and neither had to read first.
    const written = db.prepare(
      `INSERT INTO ${TABLE}
         (id, account_id, source_event_id, transaction_date, posting_date, payee, merchant, memo,
          category_id, transaction_type, amount, outflow, inflow, currency, status,
          verification_level, supersedes_transaction_id, audit_version, duplicate_key,
          source_file, source_page_or_sheet, extraction_method, extraction_method_raw,
          transaction_type_raw, confidence_bps, confidence_band, confidence_reason,
          created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(id) DO NOTHING`,
    ).run(
      input.id,
      input.accountId,
      input.sourceEventId ?? null,
      input.transactionDate,
      input.postingDate ?? null,
      input.payee ?? '',
      input.merchant ?? '',
      input.memo ?? '',
      input.categoryId ?? null,
      input.transactionType,
      amount,
      outflow,
      inflow,
      input.currency ?? DEFAULT_CURRENCY,
      input.status,
      input.verificationLevel,
      lineage.supersedesTransactionId,
      lineage.auditVersion,
      input.duplicateKey ?? null,
      provenance.sourceFile,
      provenance.sourcePageOrSheet,
      provenance.extractionMethod,
      provenance.extractionMethodRaw,
      provenance.transactionTypeRaw,
      provenance.confidenceBps,
      provenance.confidenceBand,
      provenance.confidenceReason,
      at,
      at,
    );

    const inserted = Number(written.changes) === 1;
    if (!inserted && onConflict === 'THROW') {
      // Existing callers keep failing loudly on a duplicate id. The refusal is now a TYPED one rather
      // than a raw driver constraint error, which is strictly more legible and equally refusing.
      throw new RepositoryStateError(
        'REPOSITORY_ROW_ALREADY_PRESENT',
        `${TABLE} already holds a row with id ${input.id}`,
        { table: TABLE, rowId: input.id },
      );
    }

    const row = requireOne(input.id);
    if (onConflict === 'RETURN_EXISTING') {
      // An id derived from content means the existing row must be the SAME fact. Checking only the id
      // would acknowledge a collision or a caller bug as success. Compare every caller-controlled fact,
      // including verbatim provenance; timestamps are excluded because they describe the first write.
      const expected = {
        id: input.id,
        accountId: input.accountId,
        sourceEventId: input.sourceEventId ?? null,
        transactionDate: input.transactionDate,
        postingDate: input.postingDate ?? null,
        payee: input.payee ?? '',
        merchant: input.merchant ?? '',
        memo: input.memo ?? '',
        categoryId: input.categoryId ?? null,
        transactionType: input.transactionType,
        amount,
        outflow,
        inflow,
        currency: input.currency ?? DEFAULT_CURRENCY,
        status: input.status,
        verificationLevel: input.verificationLevel,
        supersedesTransactionId: lineage.supersedesTransactionId,
        auditVersion: lineage.auditVersion,
        duplicateKey: input.duplicateKey ?? null,
        provenance,
      };
      const actual = {
        id: row.id,
        accountId: row.accountId,
        sourceEventId: row.sourceEventId,
        transactionDate: row.transactionDate,
        postingDate: row.postingDate,
        payee: row.payee,
        merchant: row.merchant,
        memo: row.memo,
        categoryId: row.categoryId,
        transactionType: row.transactionType,
        amount: row.amount,
        outflow: row.outflow,
        inflow: row.inflow,
        currency: row.currency,
        status: row.status,
        verificationLevel: row.verificationLevel,
        supersedesTransactionId: row.supersedesTransactionId,
        auditVersion: row.auditVersion,
        duplicateKey: row.duplicateKey,
        provenance: row.provenance,
      };
      if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new RepositoryStateError(
          'READBACK_MISMATCH',
          `${TABLE} row ${input.id} does not match the write that resolved to it`,
          { table: TABLE, rowId: input.id },
        );
      }
    }
    return { row, inserted };
  };

  const insertLink = (input: TransactionLinkInsert): TransactionLinkRow => {
    db.prepare(
      `INSERT INTO ${LINK_TABLE} (id, from_transaction_id, to_transaction_id, link_type, confidence_bps, created_at)
       VALUES (?, ?, ?, ?, ?, ?)`,
    ).run(input.id, input.fromTransactionId, input.toTransactionId, input.linkType, input.confidenceBps ?? 0, ctx.now());
    return requireLink(input.id);
  };

  return {
    insert(input: TransactionInsert): TransactionRow {
      return withTransaction(db, () => {
        const { row } = insertRow(input, { supersedesTransactionId: null, auditVersion: 1 });
        recordAudit(ctx, { action: 'transaction.insert', entityTable: TABLE, entityId: row.id });
        return row;
      });
    },

    /**
     * F19. A conflict-ignoring insert followed by a read-back, in ONE transaction, so the INSERT is the
     * decision and no preceding read can be raced. This is the `enqueueWork` idiom
     * (`src/server/telegram/workQueueRepo.ts:243`) rather than a variant of it.
     *
     * Not a lock, not a mutex, not a retry loop, and NOT a widened read. Widening a read to cover the
     * `get` would shrink the race window without closing it, and a smaller window is the most dangerous
     * kind because it stops reproducing in a test.
     *
     * The loser of a race receives the EXISTING row, never an error, because an id derived from content
     * means both callers were describing the same fact.
     */
    insertOrGet(input: TransactionInsert): { row: TransactionRow; inserted: boolean } {
      return withTransaction(db, () => {
        const result = insertRow(input, { supersedesTransactionId: null, auditVersion: 1 }, 'RETURN_EXISTING');
        // `insertRow` performs the full field-for-field read-back comparison while this outer
        // transaction is still open. A mismatch throws READBACK_MISMATCH before any audit or return.
        if (result.inserted) {
          recordAudit(ctx, { action: 'transaction.insert', entityTable: TABLE, entityId: result.row.id });
        }
        return result;
      });
    },

    promotePending(id: string, edit: { readonly cleanedPayee: string; readonly categoryId: string | null }): TransactionRow {
      return withTransaction(db, () => {
        const before = requireOne(id);
        if (before.status !== 'pending' || before.verificationLevel !== 'unverified') {
          throw new RepositoryStateError(
            'REPOSITORY_DERIVED_STATE_NOT_ASSIGNABLE',
            `${TABLE} row ${id} is not a pending/unverified candidate`,
            { table: TABLE, rowId: id },
          );
        }
        const at = ctx.now();
        db.prepare(
          `UPDATE ${TABLE}
              SET status = 'posted', verification_level = 'parser', merchant = ?, category_id = ?, updated_at = ?
            WHERE id = ? AND status = 'pending' AND verification_level = 'unverified'`,
        ).run(edit.cleanedPayee, edit.categoryId, at, id);

        const after = requireOne(id);
        const expected = {
          ...before,
          merchant: edit.cleanedPayee,
          categoryId: edit.categoryId,
          status: 'posted',
          verificationLevel: 'parser',
          updatedAt: at,
        };
        if (JSON.stringify(after) !== JSON.stringify(expected)) {
          throw new RepositoryStateError(
            'READBACK_MISMATCH',
            `${TABLE} row ${id} did not read back as the exact promoted candidate`,
            { table: TABLE, rowId: id },
          );
        }
        recordAudit(ctx, {
          action: 'transaction.promoteCandidate',
          entityTable: TABLE,
          entityId: id,
          // No payee or amount in the audit detail. The row already holds those facts.
          detail: 'status=pending->posted; verification_level=unverified->parser; owner_reviewed',
        });
        return after;
      });
    },

    insertTransferPair(outflow: TransactionInsert, inflow: TransactionInsert): TransferPairResult {
      return withTransaction(db, () => {
        const invalid =
          outflow.id === inflow.id ||
          outflow.accountId === inflow.accountId ||
          outflow.transactionType !== 'transfer' ||
          inflow.transactionType !== 'transfer' ||
          outflow.status !== 'posted' ||
          inflow.status !== 'posted' ||
          (outflow.currency ?? DEFAULT_CURRENCY) !== (inflow.currency ?? DEFAULT_CURRENCY) ||
          outflow.amount >= 0 || inflow.amount <= 0 ||
          outflow.amount + inflow.amount !== 0 ||
          outflow.outflow !== Math.abs(outflow.amount) || outflow.inflow !== 0 ||
          inflow.inflow !== inflow.amount || inflow.outflow !== 0;
        if (invalid) {
          throw new RepositoryStateError(
            'REPOSITORY_DERIVED_STATE_NOT_ASSIGNABLE',
            'transfer pair does not form two opposite equal linked legs',
            { table: TABLE, rowId: outflow.id },
          );
        }
        const out = insertRow(outflow, { supersedesTransactionId: null, auditVersion: 1 }, 'RETURN_EXISTING');
        const into = insertRow(inflow, { supersedesTransactionId: null, auditVersion: 1 }, 'RETURN_EXISTING');
        if (out.inserted !== into.inserted) {
          throw new RepositoryStateError(
            'READBACK_MISMATCH',
            'transfer pair resolved to only one newly inserted leg',
            { table: TABLE, rowId: outflow.id },
          );
        }
        const existingRaw = db.prepare(
          `SELECT * FROM ${LINK_TABLE} WHERE from_transaction_id = ? AND to_transaction_id = ? AND link_type = 'transfer_pair'`,
        ).get(out.row.id, into.row.id) as Record<string, unknown> | undefined;
        const existing = existingRaw ? mapLinkRow(existingRaw) : null;
        const link = existing ?? insertLink({
          id: ctx.newId(), fromTransactionId: out.row.id, toTransactionId: into.row.id,
          linkType: 'transfer_pair', confidenceBps: 10_000,
        });
        if (out.inserted) {
          recordAudit(ctx, { action: 'transaction.insertTransferPair', entityTable: TABLE, entityId: out.row.id });
          recordAudit(ctx, { action: 'transaction.insertTransferPair', entityTable: TABLE, entityId: into.row.id });
        }
        return { outflow: out.row, inflow: into.row, link };
      });
    },

    get(id: string): TransactionRow | null {
      return readOne(id);
    },

    listForAccount(accountId: string, filter: TransactionListFilter = {}): TransactionRow[] {
      // Canonical read by construction. Candidate reads live in candidatesRepository; there is no flag
      // here that can widen this collection and mix staged rows back into financial truth.
      const clauses = [
        'account_id = ?',
        `NOT (status = 'pending' AND verification_level = 'unverified')`,
      ];
      const bindings: (string | number)[] = [accountId];
      if (filter.from !== undefined) {
        clauses.push('transaction_date >= ?');
        bindings.push(filter.from);
      }
      if (filter.to !== undefined) {
        clauses.push('transaction_date <= ?');
        bindings.push(filter.to);
      }
      if (!filter.includeSuperseded) clauses.push(`status <> 'superseded'`);
      const raws = db
        .prepare(`SELECT * FROM ${TABLE} WHERE ${clauses.join(' AND ')} ORDER BY transaction_date, id`)
        .all(...bindings) as Record<string, unknown>[];
      return raws.map(mapRow);
    },

    findByDuplicateKey(duplicateKey: string): TransactionRow[] {
      // Promotion asks whether a candidate collides with CANONICAL facts. Returning another candidate in
      // the same collection would mix the two sets and make a caller decide which rows are truth.
      const raws = db
        .prepare(
          `SELECT * FROM ${TABLE}
            WHERE duplicate_key = ?
              AND NOT (status = 'pending' AND verification_level = 'unverified')
            ORDER BY transaction_date, id`,
        )
        .all(duplicateKey) as Record<string, unknown>[];
      return raws.map(mapRow);
    },

    supersede(originalId: string, replacement: TransactionInsert): SupersedeResult {
      return withTransaction(db, () => {
        const original = requireOne(originalId);
        if (original.status === 'superseded') {
          throw new RepositoryStateError(
            'REPOSITORY_ROW_ALREADY_SUPERSEDED',
            `NIZAM store: ${TABLE} row ${originalId} has already been superseded. Correct the row that replaced it, so the chain stays single-threaded.`,
            { table: TABLE, rowId: originalId },
          );
        }

        const { row: inserted } = insertRow(replacement, {
          supersedesTransactionId: original.id,
          auditVersion: original.auditVersion + 1,
        });

        // The predecessor's facts are untouched; only its persistence status moves, so that
        // derived balances stop counting it while the row itself remains readable forever.
        db.prepare(`UPDATE ${TABLE} SET status = 'superseded', updated_at = ? WHERE id = ?`).run(ctx.now(), original.id);

        const link = insertLink({
          id: ctx.newId(),
          fromTransactionId: inserted.id,
          toTransactionId: original.id,
          linkType: 'correction',
          confidenceBps: 10_000,
        });

        recordAudit(ctx, {
          action: 'transaction.supersede',
          entityTable: TABLE,
          entityId: original.id,
          detail: `replaced by ${inserted.id}; status, updated_at`,
        });
        recordAudit(ctx, {
          action: 'transaction.insert.correction',
          entityTable: TABLE,
          entityId: inserted.id,
          detail: `supersedes ${original.id}`,
        });

        return { superseded: requireOne(original.id), replacement: inserted, link };
      });
    },

    recordLink(input: TransactionLinkInsert): TransactionLinkRow {
      return withTransaction(db, () => {
        requireOne(input.fromTransactionId);
        requireOne(input.toTransactionId);
        const link = insertLink(input);
        recordAudit(ctx, {
          action: 'transactionLink.record',
          entityTable: LINK_TABLE,
          entityId: link.id,
          detail: `${link.linkType}: ${link.fromTransactionId} -> ${link.toTransactionId}`,
        });
        return link;
      });
    },

    listLinks(transactionId: string): TransactionLinkRow[] {
      const raws = db
        .prepare(
          `SELECT * FROM ${LINK_TABLE} WHERE from_transaction_id = ? OR to_transaction_id = ? ORDER BY created_at, id`,
        )
        .all(transactionId, transactionId) as Record<string, unknown>[];
      return raws.map(mapLinkRow);
    },

    resolveLink(linkId: string, resolution: LinkResolution): TransactionLinkRow {
      return withTransaction(db, () => {
        requireLink(linkId);
        db.prepare(`UPDATE ${LINK_TABLE} SET resolution = ?, resolved_at = ? WHERE id = ?`).run(
          resolution,
          ctx.now(),
          linkId,
        );
        recordAudit(ctx, {
          action: 'transactionLink.resolve',
          entityTable: LINK_TABLE,
          entityId: linkId,
          detail: `resolution=${resolution}`,
        });
        return requireLink(linkId);
      });
    },
  };
}
