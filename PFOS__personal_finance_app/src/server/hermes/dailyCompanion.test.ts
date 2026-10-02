// @vitest-environment node
/**
 * Real SQLite restart/race acceptance, synthetic ports only.
 * Owning authority: PFOS Contract 14 section 11; Contracts 06/12. Phase 14.1 (DC1). DC06-DC12.
 */
import { mkdtempSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { openStore, type StoreHandle } from '../db/connection.ts';
import { bootScheduler } from '../process/scheduler.ts';
import { createDailyReferenceStore } from './dailyStore.ts';
import { createDailyCompanion, type DailyPorts, type DailyActor } from './dailyCompanion.ts';
import { applyDailyControl } from './dailyControls.ts';
import { DAILY_NOW, dailyItem, dailySettings, dailyState } from './dailyFixtures.testSupport.ts';
const handles: StoreHandle[] = [];
afterEach(() => { for (const h of handles.splice(0)) { try { h.close(); } catch { /* restart closed it */ } } });
function harness(initial = dailySettings()) {
  const dataDir = mkdtempSync(join(homedir(), '.aki', 'tmp', 'daily-companion-'));
  const open = () => {
    const handle = openStore({ dataDir, fileName: 'daily-reference.db', busyTimeoutMs: 1000 });
    handles.push(handle); return { handle, store: createDailyReferenceStore(handle, initial) };
  };
  const first = open();
  const actor: DailyActor = { user: String(100 + 1), chat: String(200 + 2), chatType: 'private', isBot: false };
  const readState = vi.fn(async (): Promise<unknown> => dailyState());
  const dispatch = vi.fn(async () => 'delivered' as const);
  const ports: DailyPorts = { store: first.store, now: () => DAILY_NOW, permitted: () => true,
    identity: () => ({ owner: actor.user, privateChat: actor.chat }), readState, dispatch };
  return { ...first, open, actor, readState, dispatch, ports, companion: createDailyCompanion(ports) };
}
const receipt = (h: ReturnType<typeof harness>) => h.store.receipt('2026-01-05', 'morning');

describe('durable daily runs', () => {
  it('records uncertainty before the injected send, then settles delivery', async () => {
    const h = harness();
    const dispatch = vi.fn(async () => { expect(receipt(h)?.delivery).toBe('uncertain'); return 'delivered' as const; });
    expect(await createDailyCompanion({ ...h.ports, dispatch }).tick()).toBe('delivered');
    expect(receipt(h)?.plan.items[0]?.pillar).toBe('THABAT');
    expect(receipt(h)?.delivery).toBe('delivered'); expect(dispatch).toHaveBeenCalledTimes(1);
  });
  it('close/reopen cannot dispatch a completed cycle twice', async () => {
    const h = harness(); expect(await h.companion.tick()).toBe('delivered'); h.handle.close();
    const reopened = h.open();
    expect(await createDailyCompanion({ ...h.ports, store: reopened.store }).tick()).toBe('duplicate_or_changed');
    expect(reopened.store.receipt('2026-01-05', 'morning')?.delivery).toBe('delivered');
    expect(h.dispatch).toHaveBeenCalledTimes(1); expect(h.readState).toHaveBeenCalledTimes(1);
  });
  it('independent connections racing reserve one run', async () => {
    const h = harness(); const other = h.open();
    const results = await Promise.all([h.companion.tick(), createDailyCompanion({ ...h.ports, store: other.store }).tick()]);
    expect(results.sort()).toEqual(['delivered', 'duplicate_or_changed']); expect(h.dispatch).toHaveBeenCalledTimes(1);
  });
  it.each(['reserved', 'uncertain'] as const)('crash after %s never blindly replays', async stage => {
    const h = harness(); const reserved = h.store.reserve(0, dailyState(), DAILY_NOW);
    if (!reserved) throw new Error('expected reservation');
    if (stage === 'uncertain') expect(h.store.beginDispatch(reserved.plan)).toBe(true);
    h.handle.close(); const reopened = h.open();
    expect(await createDailyCompanion({ ...h.ports, store: reopened.store }).tick()).toBe('duplicate_or_changed');
    expect(reopened.store.receipt('2026-01-05', 'morning')?.delivery).toBe(stage); expect(h.dispatch).not.toHaveBeenCalled();
  });
  it.each(['provider', 'settlement', 'ambiguous'])('retains uncertainty on %s failure without exposing marker', async failure => {
    const h = harness();
    const dispatch = vi.fn(async (): Promise<'delivered' | 'uncertain'> => {
      if (failure === 'provider') throw new Error('synthetic-private-marker');
      return failure === 'ambiguous' ? 'uncertain' : 'delivered';
    });
    const store = failure === 'settlement' ? { ...h.store, delivered: () => { throw new Error('synthetic-private-marker'); } } : h.store;
    expect(await createDailyCompanion({ ...h.ports, store, dispatch }).tick()).toBe('uncertain');
    expect(receipt(h)?.delivery).toBe('uncertain'); expect(JSON.stringify(receipt(h))).not.toContain('synthetic-private-marker');
    h.handle.close(); const reopened = h.open();
    expect(await createDailyCompanion({ ...h.ports, store: reopened.store, dispatch }).tick()).toBe('duplicate_or_changed');
    expect(dispatch).toHaveBeenCalledTimes(1);
  });
  it('rolls back run when pillar reservation fails', () => {
    const h = harness();
    h.handle.db.exec("CREATE TRIGGER fail_seen BEFORE INSERT ON companion_seen BEGIN SELECT RAISE(ABORT, 'synthetic-failure'); END;");
    expect(() => h.store.reserve(0, dailyState(), DAILY_NOW)).toThrow('DAILY_STORE_FAILED'); expect(receipt(h)).toBeNull();
  });
  it('only changed pillar state is eligible in a later cycle', async () => {
    const h = harness(); await h.companion.tick(); const midday = DAILY_NOW + 4 * 3_600_000;
    expect(h.store.reserve(0, dailyState(), midday)).toBeNull();
    expect(h.store.reserve(0, dailyState([dailyItem('THABAT', { revision: 2 })]), midday)?.plan.cycle).toBe('midday');
  });
  it('cannot reserve another cycle identity in repeated DST hour', () => {
    const first = Date.parse('2026-11-01T05:30:00Z');
    const h = harness(dailySettings({ timeZone: 'America/New_York', minGapMinutes: 1,
      cycles: { morning: { minute: 90, windowMinutes: 30 }, midday: null, evening: null, weekly: null } }));
    const state = dailyState([dailyItem('THABAT', { observedAt: first - 1, freshUntil: first + 7_200_000 })]);
    state.capacity = { level: 'high', observedAt: first - 1, freshUntil: first + 7_200_000 };
    expect(h.store.reserve(0, state, first)).not.toBeNull(); state.items = state.items.map(item => ({ ...item, revision: 2 }));
    expect(h.store.reserve(0, state, first + 3_600_000)).toBeNull();
  });
  it('refuses finance file before reference schema writes', () => {
    const h = harness();
    expect(() => createDailyReferenceStore({ ...h.handle, filePath: 'finance.db' }, dailySettings())).toThrow('DAILY_REFERENCE_STORE_ONLY');
  });
});

describe('auth, consent, controls and races', () => {
  it.each([{ user: 'wrong' }, { chat: 'wrong' }, { chatType: 'group' }, { chatType: 'supergroup' }, { isBot: true }])('refuses actor %j before any store/source/dispatch', patch => {
      const h = harness(); const settings = vi.fn(h.store.settings);
      const companion = createDailyCompanion({ ...h.ports, store: { ...h.store, settings } });
      expect(companion.control({ ...h.actor, ...patch }, { kind: 'pause' })).toBe('blocked');
      expect(settings).not.toHaveBeenCalled(); expect(h.readState).not.toHaveBeenCalled(); expect(h.dispatch).not.toHaveBeenCalled();
    });
  it.each([null, { owner: '', privateChat: '' }, { owner: '-1', privateChat: '2' }])('blocks missing/malformed identity %j', async owner => {
    const h = harness(); expect(await createDailyCompanion({ ...h.ports, identity: () => owner }).tick()).toBe('blocked');
    expect(h.readState).not.toHaveBeenCalled(); expect(h.dispatch).not.toHaveBeenCalled();
  });
  it.each([false, 'throw'])('blocks false/throwing governance %s', async kind => {
    const h = harness(); const permitted = () => { if (kind === 'throw') throw new Error('synthetic-private-marker'); return false; };
    expect(await createDailyCompanion({ ...h.ports, permitted }).tick()).toBe('blocked');
    expect(h.readState).not.toHaveBeenCalled(); expect(h.dispatch).not.toHaveBeenCalled();
  });
  it('pause during source retrieval prevents a stale reservation', async () => {
    const h = harness(); const readState = async () => { expect(h.companion.control(h.actor, { kind: 'pause' })).toBe('applied'); return dailyState(); };
    expect(await createDailyCompanion({ ...h.ports, readState }).tick()).toBe('duplicate_or_changed');
    expect(receipt(h)).toBeNull(); expect(h.dispatch).not.toHaveBeenCalled();
  });
  it('revoked consent during retrieval prevents reservation', async () => {
    const h = harness(); let permitted = true;
    const readState = async () => { permitted = false; return dailyState(); };
    expect(await createDailyCompanion({ ...h.ports, permitted: () => permitted, readState }).tick()).toBe('blocked');
    expect(receipt(h)).toBeNull(); expect(h.dispatch).not.toHaveBeenCalled();
  });
  it('settings changed after reservation cancel old plan', () => {
    const h = harness(); const run = h.store.reserve(0, dailyState(), DAILY_NOW); if (!run) throw new Error('expected run');
    expect(h.companion.control(h.actor, { kind: 'pause' })).toBe('applied');
    expect(h.store.beginDispatch(run.plan)).toBe(false); expect(receipt(h)?.delivery).toBe('cancelled');
  });
  it('pause/resume/global and pillar snooze survive close/reopen', async () => {
    const h = harness(); expect(h.companion.control(h.actor, { kind: 'pause' })).toBe('applied');
    expect(await h.companion.tick()).toBe('idle'); expect(h.companion.control(h.actor, { kind: 'resume' })).toBe('applied');
    expect(h.companion.control(h.actor, { kind: 'snooze', minutes: 30, pillar: null })).toBe('applied');
    expect(h.companion.control(h.actor, { kind: 'snooze', minutes: 60, pillar: 'BADAN' })).toBe('applied');
    h.handle.close(); const reopened = h.open();
    expect(reopened.store.settings()).toMatchObject({ revision: 4, paused: false, snoozedUntil: DAILY_NOW + 1_800_000 });
    expect(reopened.store.settings().pillars.BADAN.snoozedUntil).toBe(DAILY_NOW + 3_600_000);
    expect(await createDailyCompanion({ ...h.ports, store: reopened.store }).tick()).toBe('idle');
  });
  it('stale CAS cannot overwrite newer preferences', () => {
    const h = harness(); const next = applyDailyControl(h.store.settings(), { kind: 'pause' }, DAILY_NOW);
    expect(h.store.changeSettings(0, next)).toBe(true); expect(h.store.changeSettings(0, { ...next, paused: false })).toBe(false);
    expect(h.store.settings().paused).toBe(true);
  });
  it.each(['throw', 'invalid'])('bad source %s causes closed failure without send', async kind => {
    const h = harness(); const readState = async () => {
      if (kind === 'throw') throw new Error('synthetic-private-marker');
      return { ...dailyState(), secret: 'synthetic-private-marker' };
    };
    expect(await createDailyCompanion({ ...h.ports, readState }).tick()).toBe('failed');
    expect(receipt(h)).toBeNull(); expect(h.dispatch).not.toHaveBeenCalled();
  });
});

describe('canonical clock composition', () => {
  it('life tick invokes companion once, finance stays independent, kill stops both', async () => {
    const h = harness(); let halted = false; let financeTicks = 0;
    const scheduler = bootScheduler({
      env: { LIFE_TICK_ENDPOINT: 'life-agent:9001', FINANCE_TICK_ENDPOINT: 'finance-agent:9002',
        SCHEDULER_TICK_INTERVAL: '60', KILL_SENTINEL_PATH: '/synthetic/halt', NIZAM_KILL_ALL: '0' },
      sentinelExists: () => halted, now: () => new Date(DAILY_NOW).toISOString(), sleep: async () => {},
      host: { listen: async () => { throw new Error('no listener'); }, deliverTick: async target => {
        if (target === 'life') await h.companion.tick(); else financeTicks += 1; return { delivered: true };
      } },
    });
    await scheduler.tickOnce(); await scheduler.tickOnce();
    expect(h.dispatch).toHaveBeenCalledTimes(1); expect(financeTicks).toBe(2);
    halted = true; expect((await scheduler.tickOnce()).attempts).toEqual([]);
    expect(h.dispatch).toHaveBeenCalledTimes(1); expect(financeTicks).toBe(2); expect(scheduler.listeningPorts).toEqual([]);
  });
});
