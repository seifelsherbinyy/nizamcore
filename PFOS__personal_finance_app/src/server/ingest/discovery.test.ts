/**
 * NIZAM · S1/S2 evidence and discovery — spec transaction-capture-pipeline, increment 3
 * Implemented by: PFOS Contract 06 / Phase 2.4 (design §B/S1–S2)
 * Depends on: discovery.ts, sourceRegistry.ts, channels/fileChannel.ts, ../db/repositories/testStore.ts
 *
 * Every fixture is SYNTHETIC. The properties asserted here are the ones the staging design leans on:
 * idempotency is STRUCTURAL rather than procedural, a same-key-different-bytes disagreement is REPORTED
 * rather than resolved, the bytes survive verbatim, and capture durability does not depend on anything
 * downstream being able to parse them.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { openTestStore, type TestStore } from '../db/repositories/testStore.ts';
import { createDocumentIndexRepository } from '../db/repositories/documentIndexRepository.ts';
import { createSourceEventsRepository, PARSE_STATES } from '../db/repositories/sourceEventsRepository.ts';
import { SCHEDULER_TARGETS } from '../process/scheduler.ts';
import { buildFileSourceEvent } from './channels/fileChannel.ts';
import {
  captureEvent,
  captureFile,
  runDiscovery,
  type ChannelLister,
  type DiscoveryPorts,
} from './discovery.ts';
import { CHANNEL_DESCRIPTORS, CHAT_CAPTURE_CHANNEL, descriptorFor, isCandidateOnly } from './sourceRegistry.ts';

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

const FILE = { documentRef: 'synthetic/statement-a.csv', rawBytes: 'header\nrow one\nrow two\n' };

describe('the same evidence captured twice appends once', () => {
  it('appends on the first call and reports already_present on the second', () => {
    const p = ports();
    const first = captureFile(FILE, p);
    const second = captureFile(FILE, p);
    expect(first.kind).toBe('appended');
    expect(second.kind).toBe('already_present');
    expect(p.events.countForChannel('file:statement')).toBe(1);
  });

  it('is structural, not a check-then-insert — the repository reports appended:false itself', () => {
    const p = ports();
    const event = buildFileSourceEvent(FILE);
    const a = p.events.append({ ...event });
    const b = p.events.append({ ...event });
    expect(a.appended).toBe(true);
    expect(b.appended).toBe(false);
    // Same row identity both times: the unique index decided, not a prior read.
    expect(b.row.id).toBe(a.row.id);
  });

  it('indexes the pointer once as well, because indexDocument is conflict-ignoring too', () => {
    const p = ports();
    captureFile(FILE, p);
    captureFile(FILE, p);
    expect(p.documents.count()).toBe(1);
  });
});

describe('the same key with DIFFERENT bytes is reported, never resolved', () => {
  it('surfaces EVIDENCE_CONFLICT and leaves the stored row exactly as it was', () => {
    const p = ports();
    // The chat strategy keys on date+sequence, so the key does NOT move with the content. That is the
    // only way a genuine conflict can arise, which is why this case uses it.
    const base = {
      id: 'sev_synthetic_conflict',
      channel: CHAT_CAPTURE_CHANNEL,
      idempotencyKey: 'chat:2026-03-04#1',
      contentHash: 'hash-of-the-first-bytes',
      rawPayload: 'the first reply',
      documentRef: 'synthetic/chat/2026-03-04',
      byteCount: 15,
      documentClass: 'chat-capture',
    };
    const first = captureEvent(base, p);
    expect(first.kind).toBe('appended');

    const stored = p.events.findByKey(base.channel, base.idempotencyKey);
    const conflicting = captureEvent(
      { ...base, contentHash: 'hash-of-DIFFERENT-bytes', rawPayload: 'a different reply' },
      p,
    );

    expect(conflicting.kind).toBe('refused');
    if (conflicting.kind === 'refused') expect(conflicting.code).toBe('EVIDENCE_CONFLICT');

    // Nothing moved.
    const after = p.events.findByKey(base.channel, base.idempotencyKey);
    expect(after).toEqual(stored);
    expect(after?.contentHash).toBe('hash-of-the-first-bytes');
    expect(after?.rawPayload).toBe('the first reply');
    expect(p.events.countForChannel(base.channel)).toBe(1);
  });

  it('for a FILE, changed bytes are a NEW ARTIFACT rather than a conflict — the digest is in the key', () => {
    const p = ports();
    const a = captureFile(FILE, p);
    const b = captureFile({ ...FILE, rawBytes: 'header\nrow one\nrow two CORRECTED\n' }, p);
    expect(a.kind).toBe('appended');
    expect(b.kind).toBe('appended');
    expect(p.events.countForChannel('file:statement')).toBe(2);
  });

  it('refuses a conflict WITHOUT carrying the offending bytes in the outcome', () => {
    const p = ports();
    const base = {
      id: 'sev_synthetic_conflict2',
      channel: CHAT_CAPTURE_CHANNEL,
      idempotencyKey: 'chat:2026-03-05#1',
      contentHash: 'h1',
      rawPayload: 'SECRET-PAYLOAD-ONE',
      documentRef: 'synthetic/chat/2026-03-05',
      byteCount: 18,
      documentClass: 'chat-capture',
    };
    captureEvent(base, p);
    const refused = captureEvent({ ...base, contentHash: 'h2', rawPayload: 'SECRET-PAYLOAD-TWO' }, p);
    expect(JSON.stringify(refused)).not.toContain('SECRET-PAYLOAD-TWO');
    expect(JSON.stringify(refused)).not.toContain('SECRET-PAYLOAD-ONE');
  });
});

describe('raw_payload is byte-identical to what arrived', () => {
  it('does not trim, re-case or re-wrap', () => {
    const p = ports();
    const messy = '  Leading and trailing   \n\n\tTabbed\r\nMiXeD CaSe  ';
    captureFile({ documentRef: 'synthetic/messy.txt', rawBytes: messy }, p);
    const event = buildFileSourceEvent({ documentRef: 'synthetic/messy.txt', rawBytes: messy });
    const row = p.events.findByKey(event.channel, event.idempotencyKey);
    expect(row?.rawPayload).toBe(messy);
  });

  it('measures byteCount as UTF-8 bytes, not JS string length', () => {
    // A multi-byte payload is measured as the store will hold it.
    const event = buildFileSourceEvent({ documentRef: 'synthetic/u.txt', rawBytes: 'é' });
    expect(event.byteCount).toBe(2);
  });

  it('honours the channel descriptor when deciding whether to retain the payload at all', () => {
    expect(descriptorFor('file:statement')?.retainsRawPayload).toBe(true);
    // The canonical ledger channel deliberately does NOT retain: the payload would be the owner's rows.
    expect(descriptorFor('ledger:canonical')?.retainsRawPayload).toBe(false);
  });
});

describe('capture durability and parse success are independent', () => {
  it('stores an unparseable payload and leaves parse_state pending', () => {
    const p = ports();
    const junk = '\u0001 not a ledger at all {{{ ,,,, "unclosed';
    const out = captureFile({ documentRef: 'synthetic/junk.bin', rawBytes: junk }, p);
    expect(out.kind).toBe('appended');
    const event = buildFileSourceEvent({ documentRef: 'synthetic/junk.bin', rawBytes: junk });
    const row = p.events.findByKey(event.channel, event.idempotencyKey);
    expect(row?.rawPayload).toBe(junk);
    expect(row?.parseState).toBe('pending');
  });

  it('REFUSES a NUL-bearing payload rather than truncating it — invalid input must fail', () => {
    // Found by this suite, not predicted: `raw_payload` is TEXT in a STRICT table and SQLite terminates
    // a TEXT value at the first NUL, so this payload would round-trip as '' while the insert reported
    // success. A BLOB column would fix it and needs a migration, which is not authorized. So the layer
    // refuses instead, and this test is what stops the truncation from returning unnoticed.
    const p = ports();
    const withNul = 'before\u0000after';
    const out = captureFile({ documentRef: 'synthetic/nul.bin', rawBytes: withNul }, p);
    expect(out.kind).toBe('refused');
    if (out.kind === 'refused') expect(out.code).toBe('PAYLOAD_NOT_STORABLE');
    // Nothing was written, so there is no half-captured row claiming bytes it does not hold.
    expect(p.events.countForChannel('file:statement')).toBe(0);
    expect(p.documents.count()).toBe(0);
  });

  it('offers only the four declared parse states, and pending is the entry state', () => {
    expect([...PARSE_STATES]).toEqual(['pending', 'parsed', 'rejected', 'replayed']);
  });

  it('moves parse state forward without touching identity, keys or payload', () => {
    const p = ports();
    captureFile(FILE, p);
    const event = buildFileSourceEvent(FILE);
    const before = p.events.findByKey(event.channel, event.idempotencyKey);
    const after = p.events.setParseState(before!.id, 'rejected');
    expect(after.parseState).toBe('rejected');
    expect(after.id).toBe(before!.id);
    expect(after.idempotencyKey).toBe(before!.idempotencyKey);
    expect(after.contentHash).toBe(before!.contentHash);
    expect(after.rawPayload).toBe(before!.rawPayload);
  });
});

describe('the clock is not touched', () => {
  it('SCHEDULER_TARGETS is still exactly two members', () => {
    expect([...SCHEDULER_TARGETS]).toEqual(['life', 'finance']);
    expect(SCHEDULER_TARGETS).toHaveLength(2);
  });

  it('discovery owns no timer, interval or port of its own', () => {
    const src = readFileSync(join('src', 'server', 'ingest', 'discovery.ts'), 'utf8');
    for (const forbidden of ['setInterval', 'setTimeout', 'listen(', 'createServer']) {
      expect(src).not.toContain(forbidden);
    }
  });

  it('a halted deployment discovers nothing', () => {
    const p = ports();
    const lister: ChannelLister = { channel: 'file:statement', list: () => [FILE] };
    const report = runDiscovery({ ...p, listers: [lister], halted: () => true });
    expect(report.appended).toBe(0);
    expect(report.channelsAttempted).toEqual([]);
    expect(p.events.countForChannel('file:statement')).toBe(0);
  });
});

describe('one channel failing costs no other channel its tick', () => {
  it('records the failure, continues the pass, and never throws', () => {
    const p = ports();
    const raising: ChannelLister = {
      channel: 'file:statement',
      list: () => {
        throw new Error('synthetic lister failure');
      },
    };
    const working: ChannelLister = {
      channel: 'file:statement',
      list: () => [FILE],
    };
    const report = runDiscovery({ ...p, listers: [raising, working], halted: () => false });
    expect(report.refusals).toEqual([{ channel: 'file:statement', code: 'CHANNEL_UNAVAILABLE' }]);
    expect(report.appended).toBe(1);
    expect(report.channelsAttempted).toHaveLength(2);
  });

  it('reports counts and codes only — no payload, payee or amount reaches the report', () => {
    const p = ports();
    const lister: ChannelLister = { channel: 'file:statement', list: () => [FILE] };
    const report = runDiscovery({ ...p, listers: [lister], halted: () => false });
    expect(JSON.stringify(report)).not.toContain('row one');
    expect(Object.keys(report).sort()).toEqual([
      'alreadyPresent',
      'appended',
      'channelsAttempted',
      'refusals',
    ]);
  });

  it('does not nest its own retry inside the scheduler budget', () => {
    const src = readFileSync(join('src', 'server', 'ingest', 'discovery.ts'), 'utf8');
    expect(src).not.toContain('maxAttempts');
    expect(src).not.toMatch(/for\s*\(\s*let\s+attempt/);
  });
});

describe('NO ADAPTER PARSES AN AMOUNT — asserted over the whole adapter directory', () => {
  const ADAPTER_DIR = join('src', 'server', 'ingest', 'channels');

  it('has at least one adapter, so this check cannot pass vacuously', () => {
    const files = readdirSync(ADAPTER_DIR).filter((f) => f.endsWith('.ts') && !f.endsWith('.test.ts'));
    expect(files.length).toBeGreaterThan(0);
  });

  it('no adapter imports the money core, a parser, or any monetary helper', () => {
    const files = readdirSync(ADAPTER_DIR).filter((f) => f.endsWith('.ts') && !f.endsWith('.test.ts'));
    const forbidden = [
      'lib/money',
      'fromDecimal',
      'fromMilliunits',
      'parseLedgerCsv',
      'assertMoney',
      'toDecimal',
      'mulRatio',
      'allocate(',
      'parseFloat',
      'toFixed',
      'Number(',
    ];
    for (const f of files) {
      const src = readFileSync(join(ADAPTER_DIR, f), 'utf8');
      for (const token of forbidden) {
        expect(src, `${f} must not reference ${token}`).not.toContain(token);
      }
    }
  });

  it('no adapter names a currency, a direction or an account', () => {
    const files = readdirSync(ADAPTER_DIR).filter((f) => f.endsWith('.ts') && !f.endsWith('.test.ts'));
    for (const f of files) {
      const src = readFileSync(join(ADAPTER_DIR, f), 'utf8');
      // Deliberately checks the CODE, not the prose: comments explaining the prohibition are expected.
      const code = src
        .split('\n')
        .filter((l) => !l.trim().startsWith('*') && !l.trim().startsWith('//') && !l.trim().startsWith('/*'))
        .join('\n');
      for (const token of ['EGP', 'USD', "'out'", "'in'", 'accountId']) {
        expect(code, `${f} must not name ${token}`).not.toContain(token);
      }
    }
  });
});

describe('the channel registry', () => {
  it('marks conversational capture as candidate-only, per Contract 6 §5 I5.2', () => {
    expect(isCandidateOnly(CHAT_CAPTURE_CHANNEL)).toBe(true);
  });

  it('marks file and ledger intake as authoritative, per I5.1', () => {
    expect(isCandidateOnly('file:statement')).toBe(false);
    expect(isCandidateOnly('ledger:canonical')).toBe(false);
  });

  it('FAILS CLOSED on an unregistered channel — an unknown channel is candidate-only', () => {
    expect(isCandidateOnly('channel-nobody-registered')).toBe(true);
    expect(descriptorFor('channel-nobody-registered')).toBeNull();
  });

  it('refuses to capture through an unregistered channel', () => {
    const p = ports();
    const out = captureEvent(
      {
        id: 'sev_x',
        channel: 'unregistered',
        idempotencyKey: 'k',
        contentHash: 'h',
        rawPayload: null,
        documentRef: 'r',
        byteCount: 0,
        documentClass: 'c',
      },
      p,
    );
    expect(out.kind).toBe('refused');
    if (out.kind === 'refused') expect(out.code).toBe('CHANNEL_UNKNOWN');
  });

  it('carries no parser, currency, account or money unit on any descriptor', () => {
    for (const d of CHANNEL_DESCRIPTORS) {
      expect(Object.keys(d).sort()).toEqual([
        'candidateOnly',
        'channel',
        'documentClass',
        'keyStrategy',
        'retainsRawPayload',
      ]);
    }
  });
});
