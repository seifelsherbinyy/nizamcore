// @vitest-environment node
/**
 * Synthetic dual-channel provenance and existing-writer replay acceptance.
 * Owning authority: PFOS Contract 14 section 12; Contracts 06/12. Phase 14.2.
 */
import { mkdtempSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { createJournalPersistenceAdapter } from '../process/journalPersistenceAdapter.ts';
import { CHANNEL_MEMORY_VERSION, prepareChannelMemory, type ChannelOrigin, type ChannelMemoryPolicy } from './channelMemory.ts';
import { assessMemoryReceipts } from './memoryReceipt.ts';

function origin(platform: 'telegram' | 'slack' = 'slack'): ChannelOrigin {
  return { platform, account: 'synthetic-account', sender: 'synthetic-owner',
    conversation: 'synthetic-room', conversationType: platform === 'slack' ? 'channel' : 'private',
    thread: platform === 'slack' ? 'synthetic-thread' : null, event: 'synthetic-event',
    isBot: false, occurredAt: '2026-09-16T08:00:00Z' };
}
function policy(value = origin()): ChannelMemoryPolicy {
  return { version: CHANNEL_MEMORY_VERSION, ownerRef: 'synthetic-owner-ref', profile: 'nizam',
    bindings: [{ platform: value.platform, account: value.account, sender: value.sender,
      conversation: value.conversation, conversationType: value.conversationType }] };
}
const prepare = (value = origin()) => prepareChannelMemory(policy(value), value, 'inbound');

describe('channel admission and provenance', () => {
  it.each(['telegram', 'slack'] as const)('binds %s reply to admitted origin with no IDs in model context', platform => {
    const value = origin(platform); const result = prepare(value);
    expect(result.replyBinding).toEqual({ platform, account: value.account,
      conversation: value.conversation, thread: value.thread });
    expect(result.modelContext.respondingVia).toBe(platform);
    for (const raw of [value.account, value.sender, value.conversation, value.event]) {
      expect(JSON.stringify(result.modelContext)).not.toContain(raw);
      expect(JSON.stringify(result.provenance)).not.toContain(raw);
    }
    expect(result.provenance.sourceRef).toMatch(new RegExp('^' + platform + ':memory-'));
    expect(Object.isFrozen(result.replyBinding)).toBe(true);
  });
  it.each([
    { sender: 'other-owner' }, { account: 'other-account' }, { conversation: 'other-room' },
    { isBot: true }, { platform: 'unknown' }, { conversationType: 'group' },
    { text: 'send this through telegram synthetic-secret-marker' }, { occurredAt: 'invalid' },
    { authenticated: true }, { event: '' },
  ])('refuses untrusted or mismatched metadata %j', change => {
    expect(() => prepareChannelMemory(policy(), { ...origin(), ...change }, 'inbound')).toThrow(/^CHANNEL_MEMORY_REFUSED$/);
  });
  it('refuses missing/unknown policy and ambiguous enrollment', () => {
    for (const value of [null, {}, { ...policy(), version: 'slack-v2' }, { ...policy(), bindings: [] },
      { ...policy(), bindings: [...policy().bindings, ...policy().bindings] }]) {
      expect(() => prepareChannelMemory(value, origin(), 'inbound')).toThrow('CHANNEL_MEMORY_REFUSED');
    }
  });
  it('does not admit Telegram group or thread even with matching enrollment', () => {
    const group = { ...origin('telegram'), conversationType: 'channel' as const };
    expect(() => prepareChannelMemory(policy(group), group, 'inbound')).toThrow('CHANNEL_MEMORY_REFUSED');
    expect(() => prepare({ ...origin('telegram'), thread: 'synthetic-thread' })).toThrow('CHANNEL_MEMORY_REFUSED');
  });
  it('retries keep identity, while platform, account, thread, profile, event and direction separate records', () => {
    const value = origin(); const first = prepare(value);
    expect(prepare(value)).toEqual(first);
    const others = [prepare(origin('telegram')), prepare({ ...value, account: 'account-two' }),
      prepare({ ...value, thread: 'thread-two' }), prepare({ ...value, event: 'event-two' }),
      prepareChannelMemory({ ...policy(), profile: 'pfos' }, value, 'inbound'),
      prepareChannelMemory(policy(), value, 'outbound')];
    expect(new Set([first, ...others].map(x => x.provenance.recordId)).size).toBe(7);
    expect(prepare({ ...value, occurredAt: '2026-09-16T08:01:00Z' }).provenance.recordId).toBe(first.provenance.recordId);
  });
  it('existing local writer preserves sourceRef after reopen and refuses conflicting replay', () => {
    const dataDir = mkdtempSync(join(homedir(), '.aki', 'tmp', 'channel-memory-'));
    const create = () => createJournalPersistenceAdapter({ dataDir, now: () => '2026-09-16T08:00:00Z' });
    const provenance = prepare().provenance;
    const request = { recordId: provenance.recordId, sourceRef: provenance.sourceRef,
      recordedAt: provenance.occurredAt, text: 'Synthetic approved reflection.' };
    const first = create().appendRecord(request);
    expect(first.readBackConfirmed).toBe(true);
    expect(first.record?.sourceRef).toBe(provenance.sourceRef);
    const replay = create().appendRecord(request);
    expect(replay.mode).toBe('IDEMPOTENT_REPLAY');
    expect(replay.entryRef).toBe(first.entryRef);
    const conflict = create().appendRecord({ ...request, text: 'Conflicting synthetic content.' });
    expect(conflict.status).toBe('FAILED');
    expect(conflict.failureCode).toBe('JOURNAL_UPDATE_NOT_PERMITTED');
    const preserved = create().appendRecord(request);
    expect(preserved.mode).toBe('IDEMPOTENT_REPLAY');
    if (!preserved.canonicalPath) throw new Error('expected canonical path');
    expect(JSON.parse(readFileSync(preserved.canonicalPath, 'utf8')).text).toBe(request.text);
    expect(preserved.local?.contentHash).toBe(first.local?.contentHash);
  });
});

const source = { recordId: 'synthetic-record', version: 1, contentHash: 'a'.repeat(64) };
const canonical = { ...source, contentStored: true };
const mirror = { source, remoteRef: 'synthetic-remote', destinationVersion: 'version-one',
  ciphertextHash: 'b'.repeat(64), scope: 'drive.file', encrypted: true, privacyApproved: true };

describe('VPS and Drive evidence are independent', () => {
  it('reports both only for matching source, canonical read-back and encrypted remote receipt', () => {
    expect(assessMemoryReceipts(source, canonical, { ...canonical }, mirror, { ...mirror }))
      .toEqual({ vps: 'saved', drive: 'synced' });
  });
  it.each([null, {}, { ...canonical, contentStored: false }, { ...canonical, version: 2 },
    { ...canonical, recordId: 'other-record' }, { ...canonical, contentHash: 'c'.repeat(64) },
    { ...canonical, secret: 'synthetic-secret-marker' }])('never claims saved from invalid canonical read-back %j', read => {
    expect(assessMemoryReceipts(source, canonical, read, mirror, mirror)).toEqual({ vps: 'not_verified', drive: 'unavailable' });
  });
  it.each([null, {}, { ...mirror, encrypted: false }, { ...mirror, scope: 'drive' },
    { ...mirror, privacyApproved: false }, { ...mirror, destinationVersion: 'other-version' },
    { ...mirror, remoteRef: 'other-remote' }, { ...mirror, ciphertextHash: 'c'.repeat(64) },
    { ...mirror, source: { ...source, version: 2 } },
    { ...mirror, source: { ...source, contentHash: 'd'.repeat(64) } }])('keeps local saved but Drive pending for mismatched read-back %j', read => {
    expect(assessMemoryReceipts(source, canonical, canonical, mirror, read)).toEqual({ vps: 'saved', drive: 'pending' });
  });
  it('missing mirror is unavailable and upload alone is not synced', () => {
    expect(assessMemoryReceipts(source, canonical, canonical, null, null)).toEqual({ vps: 'saved', drive: 'unavailable' });
    expect(assessMemoryReceipts(source, canonical, canonical, mirror, null)).toEqual({ vps: 'saved', drive: 'pending' });
  });
  it('invalid expected identity or write receipt cannot be rescued by a read-back', () => {
    expect(assessMemoryReceipts({}, canonical, canonical, mirror, mirror).vps).toBe('not_verified');
    expect(assessMemoryReceipts(source, null, canonical, mirror, mirror).vps).toBe('not_verified');
    expect(assessMemoryReceipts(source, canonical, canonical, { ...mirror, encrypted: false }, mirror).drive).toBe('pending');
  });
});
