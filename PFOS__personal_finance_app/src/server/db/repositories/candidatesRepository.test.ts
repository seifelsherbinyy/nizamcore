/**
 * Staging isolation and the F19 concurrency fix.
 * Owning authority: PFOS Contract 6 section 5, clauses I5.2, I5.3, I5.4. Phase 1, increment 5.
 *
 * ALL FIXTURE DATA IS SYNTHETIC. Every amount is an integer milliunit literal, every payee is an
 * invented token, and no real account identifier, balance or ledger excerpt appears. Account
 * identifiers are four-character invented digits, not a real last-four.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { openTestStore, type TestStore } from './testStore.ts';
import { createAccountsRepository } from './accountsRepository.ts';
import { createTransactionsRepository } from './transactionsRepository.ts';
import { createStatementsRepository, type StatementRecord } from './statementsRepository.ts';
import { createCandidatesRepository, CANDIDATE_STATUS, CANDIDATE_VERIFICATION_LEVEL, type CandidateInsert } from './candidatesRepository.ts';
import { RepositoryStateError } from '../errors.ts';
import type { TransactionProvenance } from './rows.ts';

let store: TestStore;

const ACCOUNT_ID = 'acct-synthetic-0001';

/** Machine provenance: unknown method, empty references. Never `manual`. */
const MACHINE_PROVENANCE: TransactionProvenance = {
  sourceFile: 'synthetic-source.txt',
  sourcePageOrSheet: 'synthetic-page-1',
  extractionMethod: 'unknown',
  extractionMethodRaw: 'synthetic-extractor-token',
  transactionTypeRaw: 'synthetic-type-token',
  confidenceBps: null,
  confidenceBand: null,
  confidenceReason: 'synthetic fixture, no confidence stated',
};

function candidate(over: Partial<CandidateInsert> = {}): CandidateInsert {
  return {
    id: 'cand-synthetic-0001',
    accountId: ACCOUNT_ID,
    transactionDate: '2026-03-01',
    payee: 'synthetic-payee-alpha',
    transactionType: 'charge',
    // Integer milliunits. 1 EGP = 1000 milliunits.
    amount: -25_000,
    outflow: 25_000,
    inflow: 0,
    provenance: MACHINE_PROVENANCE,
    ...over,
  };
}

beforeEach(() => {
  store = openTestStore('nizam-candidates-');
  createAccountsRepository(store.ctx).insert({
    id: ACCOUNT_ID,
    name: 'synthetic account',
    type: 'CREDIT_OTHER',
    onBudget: true,
    balance: 0,
    clearedBalance: 0,
    creditLimit: null,
    accountIdentifierLast4: '0001',
    sortOrder: 0,
  });
});

afterEach(() => {
  store.close();
});

describe('candidatesRepository — staging is idempotent on a content-derived id', () => {
  it('stages once and reports it inserted', () => {
    const repo = createCandidatesRepository(store.ctx);
    const result = repo.stage(candidate());
    expect(result.inserted).toBe(true);
    expect(result.row.status).toBe(CANDIDATE_STATUS);
    expect(result.row.verificationLevel).toBe(CANDIDATE_VERIFICATION_LEVEL);
  });

  it('inserting the same candidate twice yields exactly one row', () => {
    const repo = createCandidatesRepository(store.ctx);
    const first = repo.stage(candidate());
    const second = repo.stage(candidate());

    expect(first.inserted).toBe(true);
    expect(second.inserted).toBe(false);
    expect(second.row.id).toBe(first.row.id);
    expect(repo.countCandidates()).toBe(1);
  });

  it('a retried interrupted write returns the EXISTING row rather than raising', () => {
    const repo = createCandidatesRepository(store.ctx);
    // Simulate the interruption rather than reason about it: the first attempt committed, the caller
    // never learned that, and it retries with the identical payload.
    const committed = repo.stage(candidate());
    const retried = repo.stage(candidate());
    expect(retried.row).toEqual(committed.row);
    expect(retried.inserted).toBe(false);
    expect(repo.countCandidates()).toBe(1);
  });

  it('READBACK_MISMATCH refuses a same-id/different-content retry and never acknowledges it', () => {
    const repo = createCandidatesRepository(store.ctx);
    const first = repo.stage(candidate({ id: 'cand-synthetic-mismatch' }));
    expect(first.inserted).toBe(true);

    let caught: unknown;
    try {
      repo.stage(candidate({ id: 'cand-synthetic-mismatch', payee: 'synthetic-different-payee' }));
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('READBACK_MISMATCH');

    // The existing row survives byte-for-byte at the repository boundary, the offered mutation is not
    // acknowledged, and no second audit record is written.
    expect(repo.getCandidate('cand-synthetic-mismatch')).toEqual(first.row);
    expect(repo.countCandidates()).toBe(1);
    const audit = store.ctx.handle.db
      .prepare(`SELECT COUNT(*) AS n FROM audit_log WHERE entity_table = 'transactions' AND entity_id = ?`)
      .get('cand-synthetic-mismatch') as { n: number };
    expect(audit.n).toBe(1);
  });

  it('manual provenance is refused from the STORED row and the outer transaction leaves no candidate', () => {
    const repo = createCandidatesRepository(store.ctx);
    let caught: unknown;
    try {
      repo.stage(candidate({
        id: 'cand-synthetic-manual-forgery',
        provenance: { ...MACHINE_PROVENANCE, extractionMethod: 'manual' },
      }));
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('CANDIDATE_PROVENANCE_FORGED');
    expect(repo.getCandidate('cand-synthetic-manual-forgery')).toBeNull();
  });
});

describe('F19 — the insert is the decision, proven by INTERLEAVING', () => {
  /**
   * Two attempts interleaved, not sequenced. The SQLite binding this tier uses is synchronous, so
   * genuine OS-thread interleaving is not available in-process; the interleaving that MATTERS is the one
   * the defect
   * depended on, which is that a decision was made from a read taken BEFORE the write. This test
   * reproduces exactly that: both callers take their read first, at a point where the row is absent, and
   * both then proceed. Under the old get-then-insert shape both would insert and the second would raise
   * on the primary key. Under the fix the second insert is a no-op and returns the existing row.
   */
  it('two attempts that both observed absence produce exactly one row, and the loser gets the existing row', () => {
    const repo = createCandidatesRepository(store.ctx);
    const input = candidate({ id: 'cand-synthetic-race' });

    // Both callers read first. This is the interleaving the race required.
    const observedByA = repo.getCandidate(input.id);
    const observedByB = repo.getCandidate(input.id);
    expect(observedByA).toBeNull();
    expect(observedByB).toBeNull();

    // A proceeds on its stale read.
    const a = repo.stage(input);
    // B proceeds on ITS stale read, which is now wrong. It must not raise.
    const b = repo.stage(input);

    expect(a.inserted).toBe(true);
    expect(b.inserted).toBe(false);
    expect(b.row.id).toBe(a.row.id);
    expect(repo.countCandidates()).toBe(1);
    expect(repo.listCandidatesForAccount(ACCOUNT_ID)).toHaveLength(1);
  });

  it('the read-back happens inside the same transaction as the insert', () => {
    const source = readFileSync(join('src', 'server', 'db', 'repositories', 'transactionsRepository.ts'), 'utf8');
    // The public method opens exactly one transaction and calls insertRow in RETURN_EXISTING mode.
    const methodStart = source.indexOf('insertOrGet(input: TransactionInsert): { row: TransactionRow; inserted: boolean } {');
    expect(methodStart).toBeGreaterThan(0);
    const methodEnd = source.indexOf('\n    },', methodStart);
    const method = source.slice(methodStart, methodEnd);
    expect(method).toContain('withTransaction(db, () =>');
    expect(method).toContain("'RETURN_EXISTING'");
    expect(method.split('withTransaction(db, () =>').length - 1).toBe(1);

    // The helper invoked inside that transaction performs INSERT, read-back and comparison in that order.
    const helperStart = source.indexOf('const insertRow = (');
    const helperEnd = source.indexOf('\n  const insertLink', helperStart);
    const helper = source.slice(helperStart, helperEnd);
    const insertSql = helper.indexOf('ON CONFLICT(id) DO NOTHING');
    const readback = helper.indexOf('const row = requireOne(input.id)');
    const mismatch = helper.indexOf("'READBACK_MISMATCH'");
    expect(insertSql).toBeGreaterThan(0);
    expect(readback).toBeGreaterThan(insertSql);
    expect(mismatch).toBeGreaterThan(readback);
  });

  it('the conflict-ignoring insert is in the SQL, so the engine decides rather than a prior read', () => {
    const source = readFileSync(join('src', 'server', 'db', 'repositories', 'transactionsRepository.ts'), 'utf8');
    expect(source).toContain('ON CONFLICT(id) DO NOTHING');
  });

  it('a direct duplicate insert still refuses loudly, with a typed code', () => {
    const transactions = createTransactionsRepository(store.ctx);
    const base = {
      ...candidate({ id: 'txn-synthetic-dup' }),
      status: 'posted' as const,
      verificationLevel: 'parser' as const,
    };
    transactions.insert(base);
    let caught: unknown;
    try {
      transactions.insert(base);
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('REPOSITORY_ROW_ALREADY_PRESENT');
  });
});

describe('F19 — every seedLoad get-then-insert site uses the same insert-as-decision idiom', () => {
  it('accounts: interleaved stale reads produce one row and the loser receives it', () => {
    const repo = createAccountsRepository(store.ctx);
    const entry = {
      id: 'acct-synthetic-race',
      name: 'synthetic race account',
      type: 'TRACKING' as const,
      onBudget: false,
      balance: 0,
      clearedBalance: 0,
      creditLimit: null,
      accountIdentifierLast4: '0002',
      sortOrder: 1,
    };
    const observedByA = repo.get(entry.id);
    const observedByB = repo.get(entry.id);
    expect(observedByA).toBeNull();
    expect(observedByB).toBeNull();

    const a = repo.insertOrGet(entry);
    const b = repo.insertOrGet(entry);
    expect(a.inserted).toBe(true);
    expect(b.inserted).toBe(false);
    expect(b.row).toEqual(a.row);
    expect(repo.list({ includeClosed: true }).filter((r) => r.id === entry.id)).toHaveLength(1);
  });

  it('accounts: same id with different facts refuses READBACK_MISMATCH', () => {
    const repo = createAccountsRepository(store.ctx);
    const entry = {
      id: 'acct-synthetic-mismatch',
      name: 'synthetic first account',
      type: 'TRACKING' as const,
      onBudget: false,
      balance: 0,
      clearedBalance: 0,
      creditLimit: null,
      accountIdentifierLast4: '0003',
      sortOrder: 2,
    };
    const first = repo.insertOrGet(entry);
    let caught: unknown;
    try {
      repo.insertOrGet({ ...entry, name: 'synthetic changed account' });
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('READBACK_MISMATCH');
    expect(repo.get(entry.id)).toEqual(first.row);
  });

  function statement(over: Partial<StatementRecord> = {}): StatementRecord {
    return {
      id: 'stmt-synthetic-race',
      accountId: ACCOUNT_ID,
      statementMonth: '2026-03',
      periodStart: '2026-03-01',
      periodEnd: '2026-03-31',
      // Exact integer-milliunit equation: opening + inflow - outflow = closing.
      openingBalance: 100_000,
      closingBalance: 90_000,
      totalOutflow: 30_000,
      totalInflow: 20_000,
      minimumDue: null,
      ...over,
    };
  }

  it('statements: interleaved stale reads produce one row, one audit, and the loser receives it', () => {
    const repo = createStatementsRepository(store.ctx);
    const entry = statement();
    const observedByA = repo.get(entry.id);
    const observedByB = repo.get(entry.id);
    expect(observedByA).toBeNull();
    expect(observedByB).toBeNull();

    const a = repo.recordOrGet(entry);
    const b = repo.recordOrGet(entry);
    expect(a.inserted).toBe(true);
    expect(b.inserted).toBe(false);
    expect(b.row).toEqual(a.row);
    expect(repo.listForAccount(ACCOUNT_ID)).toHaveLength(1);
    const audit = store.ctx.handle.db
      .prepare(`SELECT COUNT(*) AS n FROM audit_log WHERE entity_table = 'statements' AND entity_id = ?`)
      .get(entry.id) as { n: number };
    expect(audit.n).toBe(1);
  });

  it('statements: same id with different content refuses READBACK_MISMATCH and preserves the first row', () => {
    const repo = createStatementsRepository(store.ctx);
    const first = repo.recordOrGet(statement());
    let caught: unknown;
    try {
      repo.recordOrGet(statement({ periodEnd: '2026-03-30' }));
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('READBACK_MISMATCH');
    expect(repo.get(first.row.id)).toEqual(first.row);
    expect(repo.listForAccount(ACCOUNT_ID)).toHaveLength(1);
  });

  it('statements: a different id colliding on account/month refuses READBACK_MISMATCH', () => {
    const repo = createStatementsRepository(store.ctx);
    repo.recordOrGet(statement());
    let caught: unknown;
    try {
      repo.recordOrGet(statement({ id: 'stmt-other-id' }));
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('READBACK_MISMATCH');
    expect(repo.get('stmt-other-id')).toBeNull();
  });

  it('statements: direct record keeps refusing duplicates with a typed code', () => {
    const repo = createStatementsRepository(store.ctx);
    repo.record(statement());
    let caught: unknown;
    try {
      repo.record(statement());
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('REPOSITORY_ROW_ALREADY_PRESENT');
  });

  it('seedLoad contains no get-before-insert for accounts, transactions or statement periods', () => {
    const source = readFileSync(join('src', 'server', 'ingest', 'seedLoad.ts'), 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, ' ')
      .replace(/(^|[^:])\/\/.*$/gm, '$1');
    expect(source).not.toContain('accountsRepo.get(');
    expect(source).not.toContain('txnRepo.get(');
    expect(source).not.toContain('statementsRepo.get(');
    expect(source).toContain('accountsRepo.insertOrGet(');
    expect(source).toContain('txnRepo.insertOrGet(');
    expect(source).toContain('statementsRepo.recordOrGet(');
  });
});

describe('I5.2 — candidate and canonical read paths are structurally separate', () => {
  /** A NON-EMPTY baseline. An empty database passes every exclusion assertion vacuously. */
  function nonEmptyBaseline(): { candidates: number; canonical: number } {
    const repo = createCandidatesRepository(store.ctx);
    const transactions = createTransactionsRepository(store.ctx);

    repo.stage(candidate({ id: 'cand-a' }));
    repo.stage(candidate({ id: 'cand-b', payee: 'synthetic-payee-beta' }));
    repo.stage(candidate({ id: 'cand-c', payee: 'synthetic-payee-gamma' }));

    for (const [id, level] of [['txn-a', 'parser'], ['txn-b', 'unverified'], ['txn-c', 'statement']] as const) {
      transactions.insert({
        ...candidate({ id }),
        status: 'posted',
        verificationLevel: level,
      });
    }
    return { candidates: 3, canonical: 3 };
  }

  it('the baseline is genuinely non-empty, so nothing below can pass vacuously', () => {
    const { candidates, canonical } = nonEmptyBaseline();
    const repo = createCandidatesRepository(store.ctx);
    expect(candidates).toBeGreaterThan(0);
    expect(canonical).toBeGreaterThan(0);
    expect(repo.countCandidates()).toBe(candidates);
  });

  it('the canonical read path returns ZERO candidates against a database that contains several', () => {
    nonEmptyBaseline();
    const repo = createCandidatesRepository(store.ctx);
    const canonical = repo.listCanonicalForAccount(ACCOUNT_ID);

    expect(canonical.length).toBe(3);
    const staged = canonical.filter(
      (row) => row.status === CANDIDATE_STATUS && row.verificationLevel === CANDIDATE_VERIFICATION_LEVEL,
    );
    expect(staged).toEqual([]);
  });

  it('a posted row that is merely unverified is canonical, so the conjunction is what marks staging', () => {
    nonEmptyBaseline();
    const repo = createCandidatesRepository(store.ctx);
    const canonicalIds = repo.listCanonicalForAccount(ACCOUNT_ID).map((r) => r.id);
    // txn-b is posted + unverified. Excluding on verification_level alone would have dropped it.
    expect(canonicalIds).toContain('txn-b');
  });

  it('the candidate read path returns ZERO canonical rows', () => {
    nonEmptyBaseline();
    const repo = createCandidatesRepository(store.ctx);
    const ids = repo.listCandidatesForAccount(ACCOUNT_ID).map((r) => r.id);
    expect(ids.sort()).toEqual(['cand-a', 'cand-b', 'cand-c']);
    expect(ids).not.toContain('txn-a');
  });

  it('the ordinary transactions repository canonical list also returns ZERO candidates', () => {
    nonEmptyBaseline();
    const rows = createTransactionsRepository(store.ctx).listForAccount(ACCOUNT_ID, { includeSuperseded: true });
    expect(rows).toHaveLength(3);
    expect(rows.some((row) => row.status === 'pending' && row.verificationLevel === 'unverified')).toBe(false);
  });

  it('the canonical duplicate-key lookup cannot return a candidate', () => {
    const repo = createCandidatesRepository(store.ctx);
    const transactions = createTransactionsRepository(store.ctx);
    repo.stage(candidate({ id: 'cand-dedupe-only', duplicateKey: 'key-shared' }));
    transactions.insert({
      ...candidate({ id: 'txn-dedupe-canonical', duplicateKey: 'key-shared' }),
      status: 'posted',
      verificationLevel: 'parser',
    });
    expect(transactions.findByDuplicateKey('key-shared').map((row) => row.id)).toEqual(['txn-dedupe-canonical']);
  });

  it('a canonical id is not reachable through the candidate accessor', () => {
    nonEmptyBaseline();
    const repo = createCandidatesRepository(store.ctx);
    expect(repo.getCandidate('txn-a')).toBeNull();
    expect(repo.getCandidate('cand-a')).not.toBeNull();
  });

  it('no method returns candidates and canonical rows in one collection', () => {
    nonEmptyBaseline();
    const repo = createCandidatesRepository(store.ctx);
    const candidateIds = new Set(repo.listCandidatesForAccount(ACCOUNT_ID).map((r) => r.id));
    const canonicalIds = new Set(repo.listCanonicalForAccount(ACCOUNT_ID).map((r) => r.id));
    for (const id of candidateIds) expect(canonicalIds.has(id)).toBe(false);
    expect(candidateIds.size + canonicalIds.size).toBe(6);
  });
});

describe('I5.4 — provenance survives verbatim and a machine row never claims manual', () => {
  it('provenance is verbatim on read-back, field by field', () => {
    const repo = createCandidatesRepository(store.ctx);
    const { row } = repo.stage(candidate());
    expect(row.provenance).toEqual(MACHINE_PROVENANCE);
  });

  it('a machine-created row does not claim manual, asserted on the STORED value', () => {
    const repo = createCandidatesRepository(store.ctx);
    const { row } = repo.stage(candidate({ id: 'cand-machine' }));
    // Read back through a second, independent accessor rather than trusting the write's return value.
    const reread = repo.getCandidate('cand-machine');
    expect(reread).not.toBeNull();
    expect(reread?.provenance.extractionMethod).not.toBe('manual');
    expect(row.provenance.extractionMethod).toBe('unknown');
  });

  it('absent provenance stores unknown rather than claiming a human entered it', () => {
    const repo = createCandidatesRepository(store.ctx);
    const bare = candidate({ id: 'cand-bare' });
    const { provenance: _dropped, ...withoutProvenance } = bare;
    const { row } = repo.stage(withoutProvenance);
    expect(row.provenance.extractionMethod).toBe('unknown');
    expect(row.provenance.sourceFile).toBe('');
  });
});

describe('I5.3 — this module cannot approve anything', () => {
  /** Comments stripped first: the header DESCRIBES what it refuses, and describing is not doing. */
  function code(): string {
    return readFileSync(join('src', 'server', 'db', 'repositories', 'candidatesRepository.ts'), 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, ' ')
      .replace(/(^|[^:])\/\/.*$/gm, '$1');
  }

  it('contains no approval, no posting and no status mutation', () => {
    const body = code();
    expect(body).not.toContain('approved');
    expect(body).not.toContain("'posted'");
    expect(body).not.toMatch(/UPDATE\s+transactions/iu);
    expect(body).not.toContain('supersede');
    // Guard against a vacuous pass: the stripper must not have emptied the file.
    expect(body).toContain('export function createCandidatesRepository');
  });

  it('pins both isolation values itself, so a caller cannot supply either', () => {
    const body = code();
    expect(body).toContain('status: CANDIDATE_STATUS');
    expect(body).toContain('verificationLevel: CANDIDATE_VERIFICATION_LEVEL');
    // The input type removes them, which is what makes it impossible rather than merely unlikely.
    expect(body).toContain("Omit<TransactionInsert, 'status' | 'verificationLevel'>");
  });

  it('refuses if a staged row reads back outside the staging conjunction', () => {
    const body = code();
    expect(body).toContain('CANDIDATE_ISOLATION_BROKEN');
  });
});
