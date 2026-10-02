/**
 * NIZAM · accounts repository — contract 06 §3.2, §4.2 (R1, R2)
 * Implemented by: PFOS Contract 06 / Phase 1.2 (spec 06-two-agent-vps)
 * Depends on: ../moneyBoundary.ts, ../errors.ts, rows.ts, support.ts
 *
 * The reads and writes the Stage 1-4 engines and the server tier actually need: create an
 * account, read one, list the set the budget and net-worth engines work over, and refresh the
 * two derived balance caches. Nothing more — a wider surface would be untested guesswork.
 *
 * Every write asserts its monetary values through the boundary guard BEFORE a statement is
 * prepared (§4.2.3), so a non-integer never reaches SQLite. The guarded values are what get
 * bound; the candidates the caller passed are not used again.
 *
 * A full account number is never persisted. The only identifier column is a last-four
 * fragment, and the DDL constrains its length (§3.2, contract 02 §9).
 */
import { assertMonetaryCoverage, assertMoneyField, assertOptionalMoneyField } from '../moneyBoundary.ts';
import { RepositoryStateError } from '../errors.ts';
import { DEFAULT_CURRENCY, type AccountInsert, type AccountRow, type AccountType, type Money } from './rows.ts';
import {
  fromStoredBoolean,
  recordAudit,
  toNullableText,
  toStoredBoolean,
  withTransaction,
  type RepositoryContext,
} from './support.ts';

const TABLE = 'accounts';

export interface AccountListFilter {
  /** Closed accounts are excluded by default; net-worth history asks for them explicitly. */
  readonly includeClosed?: boolean;
  /** Restrict to accounts that participate in the zero-based budget. */
  readonly onBudgetOnly?: boolean;
}

/** The derived caches a balance refresh writes. Both are guarded before the update runs. */
export interface AccountBalanceUpdate {
  readonly balance: Money;
  readonly clearedBalance: Money;
}

export interface AccountsRepository {
  insert(input: AccountInsert): AccountRow;
  /** F19: conflict-ignoring insert plus read-back in one transaction. The insert is the decision. */
  insertOrGet(input: AccountInsert): { row: AccountRow; inserted: boolean };
  get(id: string): AccountRow | null;
  list(filter?: AccountListFilter): AccountRow[];
  /** Refresh the derived balance caches. Throws a typed error if the account is not there. */
  updateBalances(id: string, update: AccountBalanceUpdate): AccountRow;
}

function mapRow(raw: Record<string, unknown>): AccountRow {
  return {
    id: String(raw['id']),
    name: String(raw['name']),
    type: String(raw['type']) as AccountType,
    currency: String(raw['currency']),
    onBudget: fromStoredBoolean(raw['on_budget']),
    balance: Number(raw['balance']),
    clearedBalance: Number(raw['cleared_balance']),
    creditLimit: raw['credit_limit'] === null || raw['credit_limit'] === undefined ? null : Number(raw['credit_limit']),
    accountIdentifierLast4: toNullableText(raw['account_identifier_last4']),
    closed: fromStoredBoolean(raw['closed']),
    sortOrder: Number(raw['sort_order']),
    createdAt: String(raw['created_at']),
    updatedAt: String(raw['updated_at']),
  };
}

export function createAccountsRepository(ctx: RepositoryContext): AccountsRepository {
  const { db } = ctx.handle;

  const readOne = (id: string): AccountRow | null => {
    const raw = db.prepare(`SELECT * FROM ${TABLE} WHERE id = ?`).get(id) as Record<string, unknown> | undefined;
    return raw ? mapRow(raw) : null;
  };

  const requireOne = (id: string): AccountRow => {
    const row = readOne(id);
    if (!row) {
      throw new RepositoryStateError('REPOSITORY_ROW_NOT_FOUND', `NIZAM store: no ${TABLE} row with id ${id}`, {
        table: TABLE,
        rowId: id,
      });
    }
    return row;
  };

  /**
   * The one INSERT. F19: `ON CONFLICT(id) DO NOTHING` makes the INSERT the decision, so a caller never
   * has to read first to find out whether to write. `changes` reports which caller won.
   */
  const insertRow = (
    input: AccountInsert,
    onConflict: 'THROW' | 'RETURN_EXISTING',
  ): { row: AccountRow; inserted: boolean } => {
    // The guard runs first, and it accounts for every monetary column of the table.
    assertMonetaryCoverage(TABLE, ['balance', 'cleared_balance', 'credit_limit']);
    const balance = assertMoneyField(TABLE, 'balance', input.balance);
    const clearedBalance = assertMoneyField(TABLE, 'cleared_balance', input.clearedBalance);
    const creditLimit = assertOptionalMoneyField(TABLE, 'credit_limit', input.creditLimit);
    const at = ctx.now();

    // Nothing above threw, so a statement may now be prepared.
    return withTransaction(db, () => {
      const written = db.prepare(
        `INSERT INTO ${TABLE}
             (id, name, type, currency, on_budget, balance, cleared_balance, credit_limit,
              account_identifier_last4, closed, sort_order, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO NOTHING`,
      ).run(
        input.id,
        input.name,
        input.type,
        input.currency ?? DEFAULT_CURRENCY,
        toStoredBoolean(input.onBudget),
        balance,
        clearedBalance,
        creditLimit,
        input.accountIdentifierLast4,
        toStoredBoolean(input.closed ?? false),
        input.sortOrder ?? 0,
        at,
        at,
      );
      const inserted = Number(written.changes) === 1;
      if (!inserted && onConflict === 'THROW') {
        throw new RepositoryStateError(
          'REPOSITORY_ROW_ALREADY_PRESENT',
          `${TABLE} already holds a row with id ${input.id}`,
          { table: TABLE, rowId: input.id },
        );
      }
      if (inserted) recordAudit(ctx, { action: 'account.insert', entityTable: TABLE, entityId: input.id });
      // The read-back is inside this same transaction, and it is compared rather than trusted. A
      // content-derived id resolving to different account facts is a collision or caller defect, not an
      // idempotent success.
      const row = requireOne(input.id);
      const expected = {
        id: input.id,
        name: input.name,
        type: input.type,
        currency: input.currency ?? DEFAULT_CURRENCY,
        onBudget: input.onBudget,
        balance,
        clearedBalance,
        creditLimit,
        accountIdentifierLast4: input.accountIdentifierLast4 ?? null,
        closed: input.closed ?? false,
        sortOrder: input.sortOrder ?? 0,
      };
      const actual = {
        id: row.id,
        name: row.name,
        type: row.type,
        currency: row.currency,
        onBudget: row.onBudget,
        balance: row.balance,
        clearedBalance: row.clearedBalance,
        creditLimit: row.creditLimit,
        accountIdentifierLast4: row.accountIdentifierLast4,
        closed: row.closed,
        sortOrder: row.sortOrder,
      };
      if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new RepositoryStateError(
          'READBACK_MISMATCH',
          `${TABLE} row ${input.id} does not match the account offered to it`,
          { table: TABLE, rowId: input.id },
        );
      }
      return { row, inserted };
    });
  };

  return {
    insert(input: AccountInsert): AccountRow {
      return insertRow(input, 'THROW').row;
    },

    /** F19: conflict-ignoring insert plus read-back in one transaction. The loser gets the existing row. */
    insertOrGet(input: AccountInsert): { row: AccountRow; inserted: boolean } {
      return insertRow(input, 'RETURN_EXISTING');
    },

    get(id: string): AccountRow | null {
      return readOne(id);
    },

    list(filter: AccountListFilter = {}): AccountRow[] {
      const clauses: string[] = [];
      if (!filter.includeClosed) clauses.push('closed = 0');
      if (filter.onBudgetOnly) clauses.push('on_budget = 1');
      const where = clauses.length > 0 ? ` WHERE ${clauses.join(' AND ')}` : '';
      const raws = db.prepare(`SELECT * FROM ${TABLE}${where} ORDER BY sort_order, id`).all() as Record<
        string,
        unknown
      >[];
      return raws.map(mapRow);
    },

    updateBalances(id: string, update: AccountBalanceUpdate): AccountRow {
      // A partial write guards only the columns it writes, each proven integer first.
      const balance = assertMoneyField(TABLE, 'balance', update.balance);
      const clearedBalance = assertMoneyField(TABLE, 'cleared_balance', update.clearedBalance);
      const at = ctx.now();

      return withTransaction(db, () => {
        requireOne(id);
        db.prepare(`UPDATE ${TABLE} SET balance = ?, cleared_balance = ?, updated_at = ? WHERE id = ?`).run(
          balance,
          clearedBalance,
          at,
          id,
        );
        recordAudit(ctx, {
          action: 'account.updateBalances',
          entityTable: TABLE,
          entityId: id,
          detail: 'balance, cleared_balance',
        });
        return requireOne(id);
      });
    },
  };
}
