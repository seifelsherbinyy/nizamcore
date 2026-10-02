/**
 * Explicit owner promotion under Contract 6 §5 I5.1-I5.6 (APPROVED).
 * Implemented for Phase 1 / increment 6 of transaction-capture-pipeline.
 *
 * ALL FIXTURES ARE SYNTHETIC. Money is integer milliunits; all ids and payees are invented; no real
 * ledger, account identifier, transport, credential or deployment particular appears. The notifier is
 * an in-memory double and sends nowhere.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { openTestStore, type TestStore } from '../db/repositories/testStore.ts';
import { createAccountsRepository } from '../db/repositories/accountsRepository.ts';
import { createCandidatesRepository, type CandidateInsert } from '../db/repositories/candidatesRepository.ts';
import { createTransactionsRepository } from '../db/repositories/transactionsRepository.ts';
import { RepositoryStateError } from '../db/errors.ts';
import {
  promoteCandidate,
  recordPromotionClarification,
  type PromotionNotifier,
  type PromotionRequest,
  type PromotionResult,
} from './promotion.ts';

let store: TestStore;
const ACCOUNT = 'acct-synthetic-promotion';
const CANDIDATE = 'cand-synthetic-promotion';

beforeEach(() => {
  store = openTestStore('nizam-promotion-');
  createAccountsRepository(store.ctx).insert({
    id: ACCOUNT,
    name: 'synthetic promotion account',
    type: 'TRACKING',
    onBudget: false,
    balance: 0,
    clearedBalance: 0,
    creditLimit: null,
    accountIdentifierLast4: '0004',
    sortOrder: 0,
  });
});

afterEach(() => store.close());

function candidate(over: Partial<CandidateInsert> = {}): CandidateInsert {
  return {
    id: CANDIDATE,
    accountId: ACCOUNT,
    sourceEventId: null,
    transactionDate: '2026-03-11',
    postingDate: null,
    payee: 'Synthetic Original Payee',
    merchant: '',
    memo: 'synthetic memo',
    categoryId: null,
    transactionType: 'charge',
    amount: -30_000,
    outflow: 30_000,
    inflow: 0,
    currency: 'EGP',
    duplicateKey: 'synthetic-duplicate-key',
    provenance: {
      sourceFile: 'synthetic-source-event',
      sourcePageOrSheet: 'synthetic-line-1',
      extractionMethod: 'unknown',
      extractionMethodRaw: 'synthetic-parser',
      transactionTypeRaw: 'synthetic-charge',
      confidenceBps: null,
      confidenceBand: null,
      confidenceReason: 'synthetic fixture',
    },
    ...over,
  };
}

function request(over: Partial<PromotionRequest> = {}): PromotionRequest {
  return {
    candidateId: CANDIDATE,
    trigger: 'explicit_owner_action',
    deterministicParsePassed: true,
    validationPassed: true,
    cleanedPayee: 'synthetic original payee',
    categoryId: null,
    resolvedLinks: [],
    ...over,
  };
}

function notifier(outcome: 'sent' | 'failed' = 'sent'): PromotionNotifier & { notifyPosted: ReturnType<typeof vi.fn> } {
  return {
    notifyPosted: vi.fn(async () => {
      if (outcome === 'failed') throw new Error('synthetic notification failure');
    }),
  };
}

function stage(over: Partial<CandidateInsert> = {}) {
  return createCandidatesRepository(store.ctx).stage(candidate(over)).row;
}

function approvalAudits(id = CANDIDATE): number {
  const raw = store.ctx.handle.db
    .prepare(`SELECT COUNT(*) AS n FROM audit_log WHERE action = 'candidate.approved' AND entity_id = ?`)
    .get(id) as { n: number };
  return raw.n;
}

function expectRefusal(result: PromotionResult, code: string): void {
  expect(result.ok).toBe(false);
  if (!result.ok) {
    expect(result.refusal.code).toBe(code);
    expect(result.refusal.permanent).toBe(true);
  }
}

describe('explicit owner action is the only promotion trigger', () => {
  it.each(['scheduler', 'confidence', 'streak', 'repetition'] as const)(
    'refuses automatic trigger %s with the typed code and leaves the candidate byte-identical',
    async (trigger) => {
      const before = stage();
      const n = notifier();
      const result = await promoteCandidate(request({ trigger }), { ctx: store.ctx, notifier: n });
      expectRefusal(result, 'AUTOMATIC_PROMOTION_FORBIDDEN');
      expect(createCandidatesRepository(store.ctx).getCandidate(CANDIDATE)).toEqual(before);
      expect(approvalAudits()).toBe(0);
      expect(n.notifyPosted).not.toHaveBeenCalled();
    },
  );

  it('refuses without deterministic parse proof', async () => {
    stage();
    const result = await promoteCandidate(request({ deterministicParsePassed: false }), {
      ctx: store.ctx,
      notifier: notifier(),
    });
    expectRefusal(result, 'DETERMINISTIC_PARSE_REQUIRED');
  });

  it('refuses without validation proof', async () => {
    stage();
    const result = await promoteCandidate(request({ validationPassed: false }), {
      ctx: store.ctx,
      notifier: notifier(),
    });
    expectRefusal(result, 'VALIDATION_REQUIRED');
  });

  it('refuses an absent candidate rather than inventing a row', async () => {
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: notifier() });
    expectRefusal(result, 'CANDIDATE_NOT_FOUND');
  });
});

describe('successful promotion is one atomic reviewed transition', () => {
  it('moves pending/unverified to posted/parser and removes the row from candidate reads', async () => {
    stage();
    const n = notifier();
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: n });
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.review.approved).toBe(true);
    expect(result.row.status).toBe('posted');
    expect(result.row.verificationLevel).toBe('parser');
    expect(createCandidatesRepository(store.ctx).getCandidate(CANDIDATE)).toBeNull();
    expect(createCandidatesRepository(store.ctx).listCanonicalForAccount(ACCOUNT).map((r) => r.id)).toContain(CANDIDATE);
    expect(approvalAudits()).toBe(1);
  });

  it('preserves original and cleaned payee forms separately and provenance verbatim', async () => {
    const before = stage();
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: notifier() });
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.row.payee).toBe(before.payee);
    expect(result.row.merchant).toBe(request().cleanedPayee);
    expect(result.row.provenance).toEqual(before.provenance);
    expect(result.row.amount).toBe(before.amount);
    expect(result.row.categoryId).toBe(request().categoryId);
  });

  it('one outer withTransaction encloses review, dedupe, transition, read-back and approval audit', () => {
    const source = readFileSync(join('src', 'server', 'ingest', 'promotion.ts'), 'utf8');
    const start = source.indexOf('function post(');
    const end = source.indexOf('\n}\n\n/**\n * Promote one candidate', start);
    const body = source.slice(start, end);
    expect(body.split('withTransaction(ctx.handle.db, () =>').length - 1).toBe(1);
    expect(body.indexOf('findByDuplicateKey')).toBeGreaterThan(body.indexOf('withTransaction'));
    expect(body.indexOf('promotePending')).toBeGreaterThan(body.indexOf('findByDuplicateKey'));
    expect(body.indexOf("action: 'candidate.approved'")).toBeGreaterThan(body.indexOf('promotePending'));
  });

  it('an idempotent second promotion returns the committed row, adds no audit and sends no second notification', async () => {
    stage();
    const n = notifier();
    const first = await promoteCandidate(request(), { ctx: store.ctx, notifier: n });
    const second = await promoteCandidate(request(), { ctx: store.ctx, notifier: n });
    expect(first.ok).toBe(true);
    expect(second.ok).toBe(true);
    if (!second.ok) return;
    expect(second.alreadyPromoted).toBe(true);
    expect(second.notification).toBe('NOT_REQUESTED');
    expect(approvalAudits()).toBe(1);
    expect(n.notifyPosted).toHaveBeenCalledTimes(1);
  });
});

describe('dedupe is required and resolved links are explicit', () => {
  function canonicalMatch() {
    return createTransactionsRepository(store.ctx).insert({
      ...candidate({ id: 'txn-synthetic-existing' }),
      status: 'posted',
      verificationLevel: 'parser',
    });
  }

  it('refuses a candidate with no duplicateKey', async () => {
    stage({ duplicateKey: null });
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: notifier() });
    expectRefusal(result, 'DUPLICATE_KEY_MISSING');
  });

  it('refuses an unresolved canonical match and leaves both rows intact', async () => {
    stage();
    const existing = canonicalMatch();
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: notifier() });
    expectRefusal(result, 'DUPLICATE_AMBIGUOUS');
    expect(createCandidatesRepository(store.ctx).getCandidate(CANDIDATE)).not.toBeNull();
    expect(createTransactionsRepository(store.ctx).get(existing.id)).toEqual(existing);
  });

  it('refuses a confirmed duplicate rather than posting it again', async () => {
    stage();
    const existing = canonicalMatch();
    const result = await promoteCandidate(
      request({ resolvedLinks: [{ transactionId: existing.id, resolution: 'confirmed' }] }),
      { ctx: store.ctx, notifier: notifier() },
    );
    expectRefusal(result, 'DUPLICATE_CONFIRMED');
  });

  it('promotes only after the owner rejects the suspected duplicate relation, and records that resolution', async () => {
    stage();
    const existing = canonicalMatch();
    const result = await promoteCandidate(
      request({ resolvedLinks: [{ transactionId: existing.id, resolution: 'rejected' }] }),
      { ctx: store.ctx, notifier: notifier() },
    );
    expect(result.ok).toBe(true);
    const links = createTransactionsRepository(store.ctx).listLinks(CANDIDATE);
    expect(links).toHaveLength(1);
    expect(links[0]).toMatchObject({
      fromTransactionId: CANDIDATE,
      toTransactionId: existing.id,
      linkType: 'suspected_duplicate',
      resolution: 'rejected',
    });
  });
});

describe('tamper and read-back failure never acknowledge and roll back the whole promotion', () => {
  it('a post-update tamper causes READBACK_MISMATCH and leaves the candidate byte-identical', async () => {
    const before = stage();
    // The trigger runs inside the same transaction immediately after the promotion UPDATE. It changes a
    // financially consequential field, so read-back must catch it and the thrown mismatch must roll the
    // UPDATE and trigger mutation back together.
    store.ctx.handle.db.exec(`
      CREATE TRIGGER synthetic_promotion_tamper
      AFTER UPDATE OF status ON transactions
      WHEN NEW.id = '${CANDIDATE}'
      BEGIN
        UPDATE transactions SET amount = amount + 1 WHERE id = NEW.id;
      END
    `);
    const n = notifier();
    let caught: unknown;
    try {
      await promoteCandidate(request(), { ctx: store.ctx, notifier: n });
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(RepositoryStateError);
    expect((caught as RepositoryStateError).code).toBe('READBACK_MISMATCH');
    expect(createCandidatesRepository(store.ctx).getCandidate(CANDIDATE)).toEqual(before);
    expect(approvalAudits()).toBe(0);
    expect(n.notifyPosted).not.toHaveBeenCalled();
  });
});

describe('posting and notification are independent in both directions', () => {
  it('a failed notification never rolls back committed posting', async () => {
    stage();
    const n = notifier('failed');
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: n });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.notification).toBe('FAILED');
    expect(createTransactionsRepository(store.ctx).get(CANDIDATE)?.status).toBe('posted');
    expect(approvalAudits()).toBe(1);
  });

  it('a failed posting never invokes notification', async () => {
    const n = notifier();
    const result = await promoteCandidate(request(), { ctx: store.ctx, notifier: n });
    expectRefusal(result, 'CANDIDATE_NOT_FOUND');
    expect(n.notifyPosted).not.toHaveBeenCalled();
  });

  it('the implementation uses durable intent language and makes no stronger delivery claim', () => {
    const source = readFileSync(join('src', 'server', 'ingest', 'promotion.ts'), 'utf8');
    expect(source).toContain('durable intent');
    expect(source.toLowerCase()).not.toContain('exactly-once');
  });
});

describe('a permanent refusal is answered with NEW S2 evidence, never retried', () => {
  it('captures the owner answer once and does not call promotion', () => {
    const captureNewEvidence = vi.fn(() => ({ sourceEventId: 'source-synthetic-new-evidence' }));
    const prior = {
      code: 'DUPLICATE_AMBIGUOUS' as const,
      candidateId: CANDIDATE,
      permanent: true as const,
    };
    const result = recordPromotionClarification(prior, 'synthetic owner clarification', { captureNewEvidence });
    expect(result).toEqual({
      kind: 'NEW_EVIDENCE',
      priorCode: 'DUPLICATE_AMBIGUOUS',
      sourceEventId: 'source-synthetic-new-evidence',
    });
    expect(captureNewEvidence).toHaveBeenCalledOnce();
    expect(captureNewEvidence).toHaveBeenCalledWith('synthetic owner clarification');
  });
});

describe('source-level automation and approval tamper guards', () => {
  function productionServerSources(): { path: string; code: string }[] {
    const root = join('src', 'server');
    const walk = (path: string): string[] => readdirSync(path, { withFileTypes: true }).flatMap((entry) => {
      const child = join(path, entry.name);
      return entry.isDirectory() ? walk(child) : [child];
    });
    return walk(root)
      .filter((path) => /\.tsx?$/.test(path) && !/\.test\.tsx?$/.test(path))
      .map((path) => ({ path, code: readFileSync(path, 'utf8').replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/.*$/gm, '$1') }));
  }

  it('sets approved true in exactly one non-test server module and exactly one place', () => {
    const hits = productionServerSources().flatMap(({ path, code }) =>
      [...code.matchAll(/approved\s*:\s*true/g)].map(() => path.replace(/\\/g, '/')),
    );
    expect(hits).toEqual(['src/server/ingest/promotion.ts']);
  });

  it('no other production module imports the promotion function', () => {
    const offenders = productionServerSources()
      .filter(({ path }) => !path.replace(/\\/g, '/').endsWith('/promotion.ts'))
      // Audit action names may legitimately describe the operation. Only an import makes the function
      // reachable, so the guard checks import declarations rather than every string occurrence.
      .filter(({ code }) => /import\s+\{[^}]*\bpromoteCandidate\b[^}]*\}\s+from/iu.test(code))
      .map(({ path }) => path.replace(/\\/g, '/'));
    expect(offenders).toEqual([]);
  });

  it('the promotion module imports no model or Hermes tool surface', () => {
    const source = readFileSync(join('src', 'server', 'ingest', 'promotion.ts'), 'utf8');
    expect(source).not.toMatch(/from\s+['"][^'"]*(?:hermes|model|openrouter)/iu);
    expect(source).not.toContain('HERMES_TOOL_NAMES');
  });
});
