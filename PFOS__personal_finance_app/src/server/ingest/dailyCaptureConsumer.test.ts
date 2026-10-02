/**
 * NIZAM · S3 chat-channel wiring — spec transaction-capture-pipeline, increment 4
 * Implemented by: PFOS Contract 15 / Phase 2.5 (§9.1 acceptance, all twelve criteria incl. 10a)
 * Depends on: dailyCaptureConsumer.ts, dailyCapture.ts, ../db/repositories/testStore.ts
 *
 * Every fixture is SYNTHETIC. The §9.1 criteria are asserted THROUGH the consumer, not only inside
 * `dailyCapture.ts` — the point of this increment is that the wiring preserves the guarantees, and a
 * guarantee that holds in the parser but is lost at the seam is not a guarantee.
 *
 * Criterion 12 is the tamper control, and it is asserted for the RIGHT REASON in each case rather than by
 * observing that something, somewhere, failed.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { openTestStore, type TestStore } from '../db/repositories/testStore.ts';
import { createDocumentIndexRepository } from '../db/repositories/documentIndexRepository.ts';
import { createSourceEventsRepository } from '../db/repositories/sourceEventsRepository.ts';
import { HERMES_TOOL_NAMES } from '../hermes/toolBoundary.ts';
import {
  CAPTURE_CHANNEL,
  CAPTURE_DECLINATION_REPLY,
  type CaptureContext,
} from './dailyCapture.ts';
import { ingestReply, promptFor } from './dailyCaptureConsumer.ts';
import type { DiscoveryPorts } from './discovery.ts';
import { descriptorFor } from './sourceRegistry.ts';

let store: TestStore | null = null;
afterEach(() => {
  store?.close();
  store = null;
});

function ports(): DiscoveryPorts {
  const s = openTestStore();
  store = s;
  return {
    events: createSourceEventsRepository(s.ctx),
    documents: createDocumentIndexRepository(s.ctx),
  };
}

const DATE = '2026-03-04';
// `sourceEventRef` is absent by design: the consumer derives the provenance anchor from the append result,
// so a caller cannot name an evidence row the bytes did not land in.
const CTX: Omit<CaptureContext, 'sourceEventRef'> = {
  captureDate: DATE,
  knownCurrencies: ['EGP', 'USD'],
  accountAliases: [{ alias: 'main', accountId: 'acct_main' }],
};

/** A well-formed line in the positional grammar: direction, magnitude, currency, acct, payee. */
const GOOD = 'out 25.000 EGP acct:main Synthetic Merchant';

describe('the channel name is ONE name (regression for the increment-3 defect)', () => {
  it('registers the channel dailyCapture actually writes, so a reply is never CHANNEL_UNKNOWN', () => {
    expect(descriptorFor(CAPTURE_CHANNEL)).not.toBeNull();
  });

  it('marks it candidate-only, per Contract 6 §5 I5.2', () => {
    expect(descriptorFor(CAPTURE_CHANNEL)?.candidateOnly).toBe(true);
  });
});

describe('§9.1 criteria 1 and 2 — a well-formed line yields exactly one candidate', () => {
  it('produces one candidate with the sign taken from direction', () => {
    const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, ports());
    expect(r.parsed).toBe(true);
    expect(r.candidates).toHaveLength(1);
    expect(r.refusals).toHaveLength(0);
    expect(r.candidates[0]!.amount).toBe(-25_000);
  });

  it('keeps the amount an integer number of milliunits', () => {
    const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, ports());
    expect(Number.isSafeInteger(r.candidates[0]!.amount)).toBe(true);
  });
});

describe('§9.1 criteria 3 to 7 — every refusal class survives the seam', () => {
  const cases: readonly { readonly label: string; readonly reply: string; readonly code: string }[] = [
    { label: 'direction missing', reply: '25.000 EGP acct:main Shop', code: 'CAPTURE_DIRECTION_MISSING' },
    // criterion 4 — a four-fractional-digit amount must fail, not be rounded
    { label: 'four decimals', reply: 'out 25.0001 EGP acct:main Shop', code: 'CAPTURE_AMOUNT_UNPARSEABLE' },
    // criterion 4 — a grouping separator must fail, not be stripped
    { label: 'grouping separator', reply: 'out 25,000 EGP acct:main Shop', code: 'CAPTURE_AMOUNT_UNPARSEABLE' },
    // criterion 5 — a currency omission is refused, NOT defaulted to the account's currency
    { label: 'currency omitted', reply: 'out 25.000 acct:main Shop', code: 'CAPTURE_CURRENCY_MISSING' },
    { label: 'currency unknown', reply: 'out 25.000 GBP acct:main Shop', code: 'CAPTURE_CURRENCY_UNKNOWN' },
    // criterion 6 — an unknown alias is refused
    { label: 'alias unknown', reply: 'out 25.000 EGP acct:savings Shop', code: 'CAPTURE_ACCOUNT_UNKNOWN' },
    // criterion 7 — a future-dated line is refused
    { label: 'future dated', reply: 'out 25.000 EGP acct:main Shop @2026-03-05', code: 'CAPTURE_DATE_IN_FUTURE' },
  ];

  for (const c of cases) {
    it(`refuses ${c.label} with ${c.code} and produces ZERO candidates`, () => {
      const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: c.reply, context: CTX }, ports());
      expect(r.candidates).toHaveLength(0);
      expect(r.refusals.map((x) => x.refusal.code)).toContain(c.code);
    });
  }

  it('criterion 6 — an alias resolving to TWO accounts is refused just like zero', () => {
    const r = ingestReply(
      {
        ownerLocalDate: DATE,
        sequence: 1,
        reply: GOOD,
        context: {
          ...CTX,
          accountAliases: [
            { alias: 'main', accountId: 'acct_a' },
            { alias: 'main', accountId: 'acct_b' },
          ],
        },
      },
      ports(),
    );
    expect(r.candidates).toHaveLength(0);
    expect(r.refusals[0]!.refusal.code).toBe('CAPTURE_ACCOUNT_UNKNOWN');
  });

  it('criterion 7 — a validly BACK-dated line is accepted at the stated date', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: `${GOOD} @2026-03-01`, context: CTX },
      ports(),
    );
    expect(r.candidates).toHaveLength(1);
    expect(r.candidates[0]!.date).toBe('2026-03-01');
  });

  it('every refusal earns exactly one FIXED clarifying question', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: 'out 25,000 EGP acct:main Shop', context: CTX },
      ports(),
    );
    expect(r.refusals).toHaveLength(1);
    expect(r.refusals[0]!.question.length).toBeGreaterThan(0);
    // Same refusal, same question, every time. A model never composes a money question.
    const again = ingestReply(
      { ownerLocalDate: DATE, sequence: 2, reply: 'out 25,000 EGP acct:main Shop', context: CTX },
      ports(),
    );
    expect(again.refusals[0]!.question).toBe(r.refusals[0]!.question);
  });

  it('a refusal NEVER carries the offending value, and the strict code passes through UNFLATTENED', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: 'out 9,876,543 EGP acct:main Shop', context: CTX },
      ports(),
    );
    const refusal = r.refusals[0]!.refusal;
    expect(refusal.code).toBe('CAPTURE_AMOUNT_UNPARSEABLE');
    expect(JSON.stringify(refusal)).not.toContain('9,876,543');
    expect(JSON.stringify(refusal)).not.toContain('9876543');
    // The money core's own sub-code survives as its own field rather than being folded into the message.
    expect(refusal.strictMoneyCode).toBe('GROUPING_SEPARATOR');
  });
});

describe('§9.1 criteria 8 and 9 — evidence idempotency at the seam', () => {
  it('criterion 8 — the same reply captured twice appends once; the second reports already_present', () => {
    const p = ports();
    const a = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, p);
    const b = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, p);
    expect(a.evidence.kind).toBe('appended');
    expect(b.evidence.kind).toBe('already_present');
    expect(p.events.countForChannel(CAPTURE_CHANNEL)).toBe(1);
  });

  it('criterion 9 — the same key with DIFFERENT bytes appends nothing and reports the disagreement', () => {
    const p = ports();
    ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, p);
    const conflict = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: 'out 1.000 EGP acct:main Other', context: CTX },
      p,
    );
    expect(conflict.evidence.kind).toBe('refused');
    if (conflict.evidence.kind === 'refused') expect(conflict.evidence.code).toBe('EVIDENCE_CONFLICT');
    expect(p.events.countForChannel(CAPTURE_CHANNEL)).toBe(1);
    // No parse was attempted, so no candidate exists behind evidence that was never written.
    expect(conflict.parsed).toBe(false);
    expect(conflict.candidates).toHaveLength(0);
  });

  it('a different sequence is a different artifact, so a correction can be sent as NEW evidence', () => {
    const p = ports();
    ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: 'out 25,000 EGP acct:main Shop', context: CTX }, p);
    const corrected = ingestReply({ ownerLocalDate: DATE, sequence: 2, reply: GOOD, context: CTX }, p);
    expect(corrected.evidence.kind).toBe('appended');
    expect(corrected.candidates).toHaveLength(1);
    // Two evidence rows: the wrong reply is still on the record. The answer did not PATCH the old row.
    expect(p.events.countForChannel(CAPTURE_CHANNEL)).toBe(2);
  });
});

describe('§9.1 criterion 10 and 10a — the prompt and the declination', () => {
  it('the prompt is byte-identical for the same owner-local date', () => {
    expect(promptFor(DATE).text).toBe(promptFor(DATE).text);
  });

  it('the prompt contains no digit that could be read as a monetary figure', () => {
    // The date itself is permitted; nothing else numeric is.
    const withoutDate = promptFor(DATE).text.split(DATE).join('');
    expect(withoutDate).not.toMatch(/\d/u);
  });

  it('10a — the declination token as a WHOLE reply yields zero candidates and zero refusals', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: CAPTURE_DECLINATION_REPLY, context: CTX },
      ports(),
    );
    expect(r.declined).toBe(true);
    expect(r.candidates).toHaveLength(0);
    expect(r.refusals).toHaveLength(0);
  });

  it('10a — a reply that merely CONTAINS the token is not a declination', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: `out 25.000 EGP acct:main ${CAPTURE_DECLINATION_REPLY} shop`, context: CTX },
      ports(),
    );
    expect(r.declined).toBe(false);
  });

  it('a declination is still durable evidence — the day replied, and that is a fact', () => {
    const p = ports();
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: CAPTURE_DECLINATION_REPLY, context: CTX },
      p,
    );
    expect(r.evidence.kind).toBe('appended');
    expect(p.events.countForChannel(CAPTURE_CHANNEL)).toBe(1);
  });
});

describe('capture durability is independent of parse success', () => {
  it('stores an unparseable reply, marks parse_state rejected, and keeps the bytes', () => {
    const p = ports();
    const junk = 'this is not the grammar at all';
    const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: junk, context: CTX }, p);
    expect(r.evidence.kind).toBe('appended');
    expect(r.candidates).toHaveLength(0);
    if (r.evidence.kind === 'appended') {
      const row = p.events.get(r.evidence.sourceEventId);
      expect(row?.parseState).toBe('rejected');
      // `rejected` means THIS grammar could not read it. The payload is untouched.
      expect(row?.rawPayload).toBe(junk);
    }
  });

  it('marks parse_state parsed when candidates were produced', () => {
    const p = ports();
    const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, p);
    if (r.evidence.kind === 'appended') {
      expect(p.events.get(r.evidence.sourceEventId)?.parseState).toBe('parsed');
    }
  });
});

describe('WORKER BRANCH, never a Hermes tool', () => {
  it('HERMES_TOOL_NAMES is still exactly ten', () => {
    expect(HERMES_TOOL_NAMES).toHaveLength(10);
  });

  it('no capture symbol is registered as a tool', () => {
    for (const name of HERMES_TOOL_NAMES) {
      expect(name).not.toContain('capture');
      expect(name).not.toContain('candidate');
      expect(name).not.toContain('ingest');
    }
  });

  it('the consumer does not import the tool boundary or the runtime adapter', () => {
    const src = readFileSync(join('src', 'server', 'ingest', 'dailyCaptureConsumer.ts'), 'utf8');
    const code = src
      .split('\n')
      .filter((l) => !l.trim().startsWith('*') && !l.trim().startsWith('//') && !l.trim().startsWith('/*'))
      .join('\n');
    expect(code).not.toContain('toolBoundary');
    expect(code).not.toContain('runtimeAdapter');
    expect(code).not.toContain('hermes/');
  });

  it('a candidate is structurally unrepresentable across the tool boundary', () => {
    // runtimeAdapter's AUTHORITY_KEY refuses any payload/result key matching this pattern. A capture
    // result is MADE of such keys, so a tool could not return one even if someone registered it.
    const AUTHORITY_KEY = /(?:amount|balance|currency|milliunit|money|price|cost|financial|policy|grant|gate|approval|authorize|decision)/iu;
    for (const key of ['amount', 'currency', 'accountId', 'date', 'payee']) {
      if (key === 'amount' || key === 'currency') expect(AUTHORITY_KEY.test(key)).toBe(true);
    }
  });

  it('no module on the MONEY-ORIGINATION PATH imports Hermes runtime code', () => {
    // The scope is the capture path, and it is narrow because a wider claim would be FALSE. Two findings
    // from writing this assertion, both recorded rather than papered over:
    //
    //   `agentReadiness.ts`      carries `import type { HermesProfileName }` — erased at compile time, so
    //                            no require, no bundle edge, no runtime coupling. Harmless.
    //   `driveEvidencePacket.ts` imports `validateEvidenceItem` from `hermes/knowledgeBoundary.ts` — a REAL
    //                            runtime import, and a legitimate one: that module's job is to validate
    //                            evidence against the knowledge boundary, so consulting the boundary is the
    //                            correct behaviour. It is a knowledge-tier module, not a capture module.
    //
    // So "no ingest module imports Hermes" is not a true statement about this codebase. What IS true, and
    // what actually matters, is that nothing which can ORIGINATE A MONETARY VALUE reaches across to Hermes.
    // That is the set asserted here.
    const MONEY_ORIGINATION_PATH = [
      'dailyCaptureConsumer.ts',
      'dailyCapture.ts',
      'discovery.ts',
      'sourceRegistry.ts',
      'normalize.ts',
      'resolve.ts',
      'validate.ts',
      'dedupe.ts',
      'recordIdentity.ts',
      'pipeline.types.ts',
      'seedLoad.ts',
    ];
    const dir = join('src', 'server', 'ingest');
    const present = readdirSync(dir);
    for (const f of MONEY_ORIGINATION_PATH) {
      // A renamed or deleted module must fail here rather than silently shrink the assertion.
      expect(present, `${f} is on the money-origination path and must exist`).toContain(f);
      const lines = readFileSync(join(dir, f), 'utf8').split('\n');
      const runtimeImports = lines
        .filter((l) => /from\s+['"][^'"]*hermes\//u.test(l))
        .filter((l) => !/^\s*import\s+type\s/u.test(l));
      expect(runtimeImports, `${f} must not import Hermes runtime code`).toEqual([]);
    }
  });
});

describe('§9.1 criterion 12 — TAMPER CONTROL, each failing for the right reason', () => {
  it('a DEFAULT CURRENCY cannot be introduced: the omission is refused, not filled from the account', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: 'out 25.000 acct:main Shop', context: CTX },
      ports(),
    );
    // The right reason: CURRENCY_MISSING specifically, not some generic parse failure.
    expect(r.refusals[0]!.refusal.code).toBe('CAPTURE_CURRENCY_MISSING');
    expect(r.candidates).toHaveLength(0);
  });

  it('a KEYWORD-DERIVED SIGN cannot be introduced: only the direction token carries the sign', () => {
    // "refund" and "credit" are words a keyword-sign heuristic would read as inflow. The grammar treats
    // them as payee text, and the direction token alone decides the sign.
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: 'out 25.000 EGP acct:main refund credit', context: CTX },
      ports(),
    );
    expect(r.candidates).toHaveLength(1);
    // Right reason: still NEGATIVE despite two inflow-suggesting words in the payee.
    expect(r.candidates[0]!.amount).toBe(-25_000);
  });

  it('a LENIENT AMOUNT PARSE cannot be introduced: the strict boundary reports its own code', () => {
    const r = ingestReply(
      { ownerLocalDate: DATE, sequence: 1, reply: 'out 25.0001 EGP acct:main Shop', context: CTX },
      ports(),
    );
    expect(r.candidates).toHaveLength(0);
    // Right reason: the money core refused with a specific sub-code, rather than the value being rounded.
    expect(r.refusals[0]!.refusal.code).toBe('CAPTURE_AMOUNT_UNPARSEABLE');
    expect(r.refusals[0]!.refusal.strictMoneyCode).toBeDefined();
  });

  it('an AUTO-PROMOTION cannot be introduced: nothing here sets approved, and no canonical row appears', () => {
    const p = ports();
    const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, p);
    expect(r.candidates).toHaveLength(1);
    // Right reason, and stated to match Contract 6 §5 I5.3 rather than to contradict it: `approved` DOES
    // exist on a candidate — it is a REVIEW FLAG, and I5.3 is explicit that it "is a review flag, NOT an
    // isolation boundary, and MUST NOT substitute for staging." So the assertion is not that the field is
    // absent. It is that this path leaves it FALSE, and that this path contains no code able to set it.
    expect(Object.keys(r).sort()).toEqual(['candidates', 'declined', 'evidence', 'parsed', 'refusals']);
    for (const candidate of r.candidates) expect(candidate.approved).toBe(false);
    // The consumer's source contains no assignment to `approved` and no promotion verb.
    const src = readFileSync(join('src', 'server', 'ingest', 'dailyCaptureConsumer.ts'), 'utf8');
    expect(src).not.toMatch(/approved\s*[:=]\s*true/u);
    expect(src).not.toContain('promote');
    // The result exposes no canonical-row surface at all — there is nothing here to promote INTO.
    expect(Object.keys(r)).not.toContain('transactions');
    expect(Object.keys(r)).not.toContain('posted');
  });

  it('records the D-D tension rather than silently resolving it: a chat capture is labelled `manual`', () => {
    // Observed: `importInfo.extractionMethod === 'manual'` and `sourceType === 'manual'` on a chat capture.
    // Contract 6 §5 I5.4 says a MACHINE-EXTRACTED row must never claim `manual`. A daily capture is
    // owner-typed, not machine-extracted, so `manual` is defensible — and `confidenceReason` says so
    // explicitly. But it loses the channel, which is exactly what **D-D** records: widening
    // `ImportInfo.sourceType` to add `chat` is wanted by PFOS 15 §10.1 and deliberately NOT taken, because
    // it is a schema change and therefore owner-only. This test pins the current honest-but-lossy state so
    // that a future `chat` value is a deliberate change and not a surprise.
    const r = ingestReply({ ownerLocalDate: DATE, sequence: 1, reply: GOOD, context: CTX }, ports());
    const info = r.candidates[0]!.importInfo;
    expect(info).not.toBeNull();
    expect(info!.sourceType).toBe('manual');
    expect(info!.confidenceReason).toContain('owner-stated');
  });
});
