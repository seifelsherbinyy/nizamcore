/**
 * Tests for financial-pillar response assembly.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1), task NIZAM-SLACK-FINANCE-007 track_t.
 *
 * ALL FIXTURE DATA IS SYNTHETIC. There is no real balance, account identifier, payee or ledger excerpt
 * anywhere in this file, and no monetary value of any kind appears because the type under test has no
 * field that could hold one. Anchor identifiers are obviously invented tokens.
 */
import { describe, expect, it, vi } from 'vitest';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  ANSWERABLE_WITH_ANCHOR,
  STALENESS_TOLERANCE_MS,
  assembleFinancialResponse,
  deliverFinancialResponse,
  financialPillarTick,
  renderFinancialResponse,
  type AnchorEvidence,
  type AssembleInput,
  type AssemblePorts,
  type DeliveryJournalPort,
  type DeliveryOutcome,
  type FinancialResponse,
  type QuestionClass,
  type RenderedMessage,
  type SilenceCode,
} from './financialResponse.ts';
import { LRI, PDI, hasUnisolatedLtrRun, isolateLtrRuns, stripIsolates } from './bidiIsolate.ts';
import { pillarQuestion } from './dailyMessages.ts';

const NOW_MS = 1_800_000_000_000;
const SYNTHETIC_RECEIPT_REF = 'synthetic-receipt-ref-aaaa';
const SYNTHETIC_STATE_VERSION = 'synthetic-state-version-0001';

function evidence(over: Partial<AnchorEvidence> = {}): AnchorEvidence {
  return {
    canonicalStateVersion: SYNTHETIC_STATE_VERSION,
    receiptRef: SYNTHETIC_RECEIPT_REF,
    observedAtMs: NOW_MS,
    candidateOnly: false,
    ...over,
  };
}

function ports(over: { evidence?: AnchorEvidence | null; suppressed?: SilenceCode | null; nowMs?: number } = {}): AssemblePorts {
  const ev = over.evidence === undefined ? evidence() : over.evidence;
  return {
    receipt: { latest: () => ev },
    suppression: { state: () => over.suppressed ?? null },
    clock: { nowMs: () => over.nowMs ?? NOW_MS },
  };
}

function input(over: Partial<AssembleInput> = {}): AssembleInput {
  return { questionClass: 'Q1_BALANCE', locale: 'en', solicited: true, qualitative: 'ATTENTION_NEEDED', ...over };
}

describe('the closed-set rule is intact', () => {
  it('exposes no monetary field on any response variant', () => {
    const response = assembleFinancialResponse(input(), ports());
    const keys = Object.keys(response).join(' ');
    for (const forbidden of ['amount', 'balance', 'total', 'figure', 'money', 'value', 'minorUnits', 'milliunits']) {
      expect(keys.toLowerCase()).not.toContain(forbidden);
    }
  });

  it('reads the MAL_PFOS pillar string unchanged rather than substituting into it', () => {
    const response = assembleFinancialResponse(input(), ports());
    const rendered = renderFinancialResponse(response);
    expect(rendered).not.toBeNull();
    expect(rendered?.text).toContain(pillarQuestion('MAL_PFOS', 'en'));
  });

  it('never places the anchor identifier in the visible text', () => {
    const rendered = renderFinancialResponse(assembleFinancialResponse(input(), ports()));
    expect(rendered?.metadata?.receiptRef).toBe(SYNTHETIC_RECEIPT_REF);
    expect(rendered?.text).not.toContain(SYNTHETIC_RECEIPT_REF);
    expect(rendered?.text).not.toContain(SYNTHETIC_STATE_VERSION);
  });
});

describe('refusal paths, asserted on the typed code', () => {
  it('refuses NO_RECEIPT when the receipt port has nothing', () => {
    const r = assembleFinancialResponse(input(), ports({ evidence: null }));
    expect(r).toEqual({ kind: 'REFUSAL', code: 'NO_RECEIPT', locale: 'en' });
  });

  it('refuses NO_RECEIPT when the evidence carries no receipt reference', () => {
    const r = assembleFinancialResponse(input(), ports({ evidence: evidence({ receiptRef: null }) }));
    expect(r).toEqual({ kind: 'REFUSAL', code: 'NO_RECEIPT', locale: 'en' });
  });

  it('refuses CANDIDATE_ONLY when the only evidence is a staged candidate', () => {
    const r = assembleFinancialResponse(input(), ports({ evidence: evidence({ candidateOnly: true }) }));
    expect(r).toEqual({ kind: 'REFUSAL', code: 'CANDIDATE_ONLY', locale: 'en' });
  });

  it('refuses NO_CANONICAL_STATE when there is no version to anchor to', () => {
    const r = assembleFinancialResponse(input(), ports({ evidence: evidence({ canonicalStateVersion: null }) }));
    expect(r).toEqual({ kind: 'REFUSAL', code: 'NO_CANONICAL_STATE', locale: 'en' });
  });

  it('refuses CLASS_UNANSWERABLE for every class a reference cannot answer truthfully', () => {
    for (const questionClass of ['Q2_SPEND', 'Q4_FORECAST', 'Q6_EXPLAIN_CHANGE'] as QuestionClass[]) {
      const r = assembleFinancialResponse(input({ questionClass }), ports());
      expect(r).toEqual({ kind: 'REFUSAL', code: 'CLASS_UNANSWERABLE', locale: 'en' });
    }
  });

  it('refuses STALE_BEYOND_TOLERANCE one millisecond past the bound and not at the bound', () => {
    const atBound = assembleFinancialResponse(input(), ports({ nowMs: NOW_MS + STALENESS_TOLERANCE_MS }));
    expect(atBound.kind).toBe('REFERENCE');
    const pastBound = assembleFinancialResponse(input(), ports({ nowMs: NOW_MS + STALENESS_TOLERANCE_MS + 1 }));
    expect(pastBound).toEqual({ kind: 'REFUSAL', code: 'STALE_BEYOND_TOLERANCE', locale: 'en' });
  });

  it('throws DAILY_LOCALE_INVALID for a locale that is neither en nor ar', () => {
    for (const bad of ['fr', 'EN', '', 'en-US']) {
      expect(() => assembleFinancialResponse(
        input({ locale: bad as unknown as 'en' }),
        ports(),
      )).toThrow('DAILY_LOCALE_INVALID');
    }
  });

  it('decides class unanswerability before consulting the receipt, so the code is stable', () => {
    const receipt = { latest: vi.fn(() => null) };
    const r = assembleFinancialResponse(
      input({ questionClass: 'Q4_FORECAST' }),
      { ...ports(), receipt },
    );
    expect(r).toEqual({ kind: 'REFUSAL', code: 'CLASS_UNANSWERABLE', locale: 'en' });
    expect(receipt.latest).not.toHaveBeenCalled();
  });

  it('renders every refusal as readable text in both locales and carries no metadata', () => {
    const codes = ['NO_RECEIPT', 'NO_CANONICAL_STATE', 'CANDIDATE_ONLY', 'CLASS_UNANSWERABLE', 'STALE_BEYOND_TOLERANCE'] as const;
    for (const code of codes) {
      for (const locale of ['en', 'ar'] as const) {
        const rendered = renderFinancialResponse({ kind: 'REFUSAL', code, locale });
        expect(rendered?.metadata).toBeNull();
        expect(stripIsolates(rendered?.text ?? '').length).toBeGreaterThan(10);
      }
    }
  });

  it('says unavailable rather than zero', () => {
    const rendered = renderFinancialResponse({ kind: 'REFUSAL', code: 'NO_RECEIPT', locale: 'en' });
    expect(rendered?.text).toContain('not zero');
  });
});

describe('silence is a first-class output', () => {
  it('stays silent for every suppression reason on the proactive surface', () => {
    for (const reason of ['QUIET_HOURS', 'SNOOZED', 'PAUSED', 'ALREADY_SAID_TODAY'] as SilenceCode[]) {
      const r = assembleFinancialResponse(input({ solicited: false }), ports({ suppressed: reason }));
      expect(r).toEqual({ kind: 'SILENCE', reason });
    }
  });

  it('does not suppress a reply to a question the owner just asked', () => {
    const r = assembleFinancialResponse(input({ solicited: true }), ports({ suppressed: 'SNOOZED' }));
    expect(r.kind).toBe('REFERENCE');
  });

  it('stays silent when nothing was detected, which is not the same as zero', () => {
    const r = assembleFinancialResponse(input({ qualitative: null }), ports());
    expect(r).toEqual({ kind: 'SILENCE', reason: 'NOTHING_TO_SAY' });
  });

  it('emits nothing at all for silence', () => {
    expect(renderFinancialResponse({ kind: 'SILENCE', reason: 'NOTHING_TO_SAY' })).toBeNull();
  });
});

describe('the meta class, the only one answerable today', () => {
  it('answers freshness as current inside the tolerance', () => {
    const r = assembleFinancialResponse(input({ questionClass: 'Q7_META' }), ports());
    expect(r).toMatchObject({ kind: 'REFERENCE', qualitative: 'ANCHOR_IS_CURRENT' });
  });

  it('answers freshness as ageing rather than refusing, because staleness is the answer', () => {
    const r = assembleFinancialResponse(
      input({ questionClass: 'Q7_META' }),
      ports({ nowMs: NOW_MS + STALENESS_TOLERANCE_MS + 1 }),
    );
    expect(r).toMatchObject({ kind: 'REFERENCE', qualitative: 'ANCHOR_IS_AGEING' });
  });

  it('still refuses when there is no anchor at all to describe', () => {
    const r = assembleFinancialResponse(input({ questionClass: 'Q7_META' }), ports({ evidence: null }));
    expect(r).toEqual({ kind: 'REFUSAL', code: 'NO_RECEIPT', locale: 'en' });
  });

  it('is answerable without being in the anchored-answer set', () => {
    expect(ANSWERABLE_WITH_ANCHOR).not.toContain('Q7_META');
  });
});

describe('bilingual and right-to-left rendering, by code point', () => {
  it('isolates a Latin run inside Arabic with LRI and PDI', () => {
    expect(isolateLtrRuns('تنبيه PFOS جديد')).toBe(`تنبيه ${LRI}PFOS${PDI} جديد`);
  });

  it('leaves English untouched', () => {
    const rendered = renderFinancialResponse(assembleFinancialResponse(input(), ports()));
    expect(rendered?.text).not.toContain(LRI);
    expect(rendered?.text).not.toContain(PDI);
  });

  it('isolates the Latin run that the existing Arabic pillar string already embeds', () => {
    // The shipped Arabic MAL_PFOS question contains the Latin run PFOS with no isolation, so this is
    // a real hazard in the current tree rather than a hypothetical one.
    expect(hasUnisolatedLtrRun(pillarQuestion('MAL_PFOS', 'ar'))).toBe(true);
    const rendered = renderFinancialResponse(assembleFinancialResponse(input({ locale: 'ar' }), ports()));
    expect(rendered?.text).toContain(`${LRI}PFOS${PDI}`);
    expect(hasUnisolatedLtrRun(rendered?.text ?? '')).toBe(false);
  });

  it('preserves the content exactly once the controls are stripped', () => {
    const rendered = renderFinancialResponse(assembleFinancialResponse(input({ locale: 'ar' }), ports()));
    expect(stripIsolates(rendered?.text ?? '')).toContain(pillarQuestion('MAL_PFOS', 'ar'));
  });

  it('is idempotent, because a second pass would change resolved display order', () => {
    const once = isolateLtrRuns('تنبيه PFOS جديد');
    expect(isolateLtrRuns(once)).toBe(once);
  });

  it('answers the same way on repeated predicate calls', () => {
    const text = pillarQuestion('MAL_PFOS', 'ar');
    expect([hasUnisolatedLtrRun(text), hasUnisolatedLtrRun(text), hasUnisolatedLtrRun(text)]).toEqual([true, true, true]);
  });

  it('does not swallow a trailing separator into the isolate', () => {
    expect(isolateLtrRuns('راجع PFOS.')).toBe(`راجع ${LRI}PFOS${PDI}.`);
  });
});

describe('durable intent, and not exactly-once', () => {
  function journal(): DeliveryJournalPort & { state: Map<string, 'UNCERTAIN' | 'SENT'> } {
    const state = new Map<string, 'UNCERTAIN' | 'SENT'>();
    return {
      state,
      find: (k) => state.get(k) ?? null,
      markUncertain: (k) => { state.set(k, 'UNCERTAIN'); },
      markSent: (k) => { state.set(k, 'SENT'); },
    };
  }
  const message: RenderedMessage = { text: 'synthetic', metadata: null };

  it('marks delivery uncertain before invoking the outbound port', async () => {
    const j = journal();
    const order: string[] = [];
    const transport = { send: async () => { order.push(`send:${j.find('k') ?? 'none'}`); return 'SENT' as DeliveryOutcome; } };
    await deliverFinancialResponse('k', message, { transport, journal: j });
    expect(order).toEqual(['send:UNCERTAIN']);
  });

  it('reports SENT and records it', async () => {
    const j = journal();
    const verdict = await deliverFinancialResponse('k', message, { transport: { send: async () => 'SENT' }, journal: j });
    expect(verdict).toBe('SENT');
    expect(j.find('k')).toBe('SENT');
  });

  it('never replays an ambiguous send', async () => {
    const j = journal();
    const send = vi.fn(async (): Promise<DeliveryOutcome> => 'AMBIGUOUS');
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('UNCERTAIN');
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('SUPPRESSED_ALREADY_ATTEMPTED');
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('never replays a failed send', async () => {
    const j = journal();
    const send = vi.fn(async (): Promise<DeliveryOutcome> => 'FAILED');
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('UNCERTAIN');
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('SUPPRESSED_ALREADY_ATTEMPTED');
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('treats a throwing transport as ambiguous rather than as a reason to retry', async () => {
    const j = journal();
    const send = vi.fn(async (): Promise<DeliveryOutcome> => { throw new Error('synthetic transport failure'); });
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('UNCERTAIN');
    expect(j.find('k')).toBe('UNCERTAIN');
  });

  it('declines to send after a restart that finds an uncertain marker', async () => {
    const j = journal();
    j.markUncertain('k');
    const send = vi.fn(async (): Promise<DeliveryOutcome> => 'SENT');
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('SUPPRESSED_ALREADY_ATTEMPTED');
    expect(send).not.toHaveBeenCalled();
  });

  it('suppresses a duplicate delivery of an already sent identity', async () => {
    const j = journal();
    const send = vi.fn(async (): Promise<DeliveryOutcome> => 'SENT');
    await deliverFinancialResponse('k', message, { transport: { send }, journal: j });
    expect(await deliverFinancialResponse('k', message, { transport: { send }, journal: j })).toBe('SUPPRESSED_ALREADY_ATTEMPTED');
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('delivers nowhere in this tree: the only transport is a double', async () => {
    const j = journal();
    const sent: RenderedMessage[] = [];
    await deliverFinancialResponse('k', message, {
      transport: { send: async (m) => { sent.push(m); return 'SENT'; } },
      journal: j,
    });
    expect(sent).toEqual([message]);
  });
});

describe('the tick handler, as a consumer and not a second delivery path', () => {
  function tickPorts(over: Parameters<typeof ports>[0] = {}) {
    const state = new Map<string, 'UNCERTAIN' | 'SENT'>();
    const send = vi.fn(async (): Promise<DeliveryOutcome> => 'SENT');
    return {
      ...ports(over),
      transport: { send },
      journal: {
        find: (k: string) => state.get(k) ?? null,
        markUncertain: (k: string) => { state.set(k, 'UNCERTAIN'); },
        markSent: (k: string) => { state.set(k, 'SENT'); },
      },
      send,
    };
  }

  it.each(['QUIET_HOURS', 'SNOOZED'] as const)(
    'reaches the transport not at all when proactive output is %s', async (reason) => {
      const p = tickPorts({ suppressed: reason });
      const result = await financialPillarTick({ ...input({ solicited: false }), deliveryKey: 'k' }, p);
      expect(result.outcome).toBe('SILENT');
      expect(p.send).not.toHaveBeenCalled();
    },
  );

  it('delivers a reference when the anchor is present and fresh', async () => {
    const p = tickPorts();
    const result = await financialPillarTick({ ...input(), deliveryKey: 'k' }, p);
    expect(result.outcome).toBe('DELIVERED_REFERENCE');
    expect(p.send).toHaveBeenCalledTimes(1);
  });

  it('delivers a refusal as a refusal rather than reporting success', async () => {
    const p = tickPorts({ evidence: null });
    const result = await financialPillarTick({ ...input(), deliveryKey: 'k' }, p);
    expect(result.outcome).toBe('DELIVERED_REFUSAL');
    expect(result.response).toMatchObject({ kind: 'REFUSAL', code: 'NO_RECEIPT' });
  });

  it('does not replay across two ticks after an ambiguous send', async () => {
    const state = new Map<string, 'UNCERTAIN' | 'SENT'>();
    const send = vi.fn(async (): Promise<DeliveryOutcome> => 'AMBIGUOUS');
    const p = {
      ...ports(),
      transport: { send },
      journal: {
        find: (k: string) => state.get(k) ?? null,
        markUncertain: (k: string) => { state.set(k, 'UNCERTAIN'); },
        markSent: (k: string) => { state.set(k, 'SENT'); },
      },
    };
    expect((await financialPillarTick({ ...input(), deliveryKey: 'k' }, p)).outcome).toBe('UNCERTAIN');
    expect((await financialPillarTick({ ...input(), deliveryKey: 'k' }, p)).outcome).toBe('SUPPRESSED_ALREADY_ATTEMPTED');
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('still throws on an invalid locale before touching the transport', async () => {
    const p = tickPorts();
    await expect(financialPillarTick(
      { ...input({ locale: 'de' as unknown as 'en' }), deliveryKey: 'k' },
      p,
    )).rejects.toThrow('DAILY_LOCALE_INVALID');
    expect(p.send).not.toHaveBeenCalled();
  });

  /**
   * Strip comments first. The module header DESCRIBES what it refuses to touch, and describing a thing
   * is not doing it, so a naive substring scan flags the documentation rather than the code.
   */
  function codeOf(...segments: string[]): string {
    return readFileSync(join(...segments), 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, ' ')
      .replace(/(^|[^:])\/\/.*$/gm, '$1');
  }

  it('neither imports nor widens the scheduler', () => {
    const code = codeOf('src', 'server', 'hermes', 'financialResponse.ts');
    expect(code).not.toMatch(/from\s+'[^']*scheduler/u);
    expect(code).not.toContain('SCHEDULER_TARGETS');
    // Guard against a vacuous pass: the stripper must not have emptied the file.
    expect(code).toContain('export async function financialPillarTick');
  });

  it('does not import the unauthorised receipt module, whose design is unsigned', () => {
    const code = codeOf('src', 'server', 'hermes', 'financialResponse.ts');
    expect(code).not.toMatch(/from\s+'[^']*stateUseReceipt/u);
    expect(existsSync(join('src', 'server', 'hermes', 'stateUseReceipt.ts'))).toBe(false);
    expect(existsSync(join('src', 'server', 'state', 'stateUseReceipt.ts'))).toBe(false);
  });
});

describe('the response type admits no eleventh pillar', () => {
  it('pins the pillar to MAL_PFOS on every reference', () => {
    const responses: FinancialResponse[] = [
      assembleFinancialResponse(input(), ports()),
      assembleFinancialResponse(input({ questionClass: 'Q3_COMMITMENT' }), ports()),
      assembleFinancialResponse(input({ questionClass: 'Q5_PENDING' }), ports()),
      assembleFinancialResponse(input({ questionClass: 'Q7_META' }), ports()),
    ];
    for (const r of responses) {
      expect(r.kind).toBe('REFERENCE');
      if (r.kind === 'REFERENCE') expect(r.pillar).toBe('MAL_PFOS');
    }
  });
});
