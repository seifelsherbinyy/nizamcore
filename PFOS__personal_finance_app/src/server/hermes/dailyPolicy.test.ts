/**
 * Daily policy and control acceptance, synthetic fixed time/state.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1). DC01-DC05/DC09/DC11.
 */
import { describe, expect, it } from 'vitest';
import { PILLARS, dueDailyCycle, localDailyTime, parseDailySettings, parseDailyState,
  selectDailyPlan, type DailyHistory } from './dailyPolicy.ts';
import { renderDailyMessage } from './dailyMessages.ts';
import { applyDailyControl, routeDailyText } from './dailyControls.ts';
import { DAILY_NOW, dailySettings, dailyItem, dailyState } from './dailyFixtures.testSupport.ts';
const empty: DailyHistory = { lastReservedAt: null, pillars: {} };

describe('daily schedule and schema', () => {
  it.each([
    { version: 'unknown' }, { enabled: undefined }, { timeZone: 'not/a/timezone' },
    { maxItems: 4 }, { minGapMinutes: 0 }, { revision: 0.5 }, { extra: 'synthetic-private-marker' },
    { quiet: { start: -1, end: 100 } }, { pillars: {} },
  ])('refuses malformed settings without echoing values: %j', override => {
    expect(() => parseDailySettings({ ...dailySettings(), ...override })).toThrow(/^DAILY_SETTINGS_INVALID$/);
  });
  it('uses local date and weekday across UTC midnight', () => {
    expect(localDailyTime(Date.parse('2026-01-04T23:00:00Z'), 'Asia/Tokyo'))
      .toEqual({ day: '2026-01-05', minute: 480, weekday: 1 });
    expect(dueDailyCycle(dailySettings({ timeZone: 'Asia/Tokyo' }), Date.parse('2026-01-04T23:00:00Z'))).toBe('morning');
  });
  it('excludes the window end and never catches up missed cycles', () => {
    expect(dueDailyCycle(dailySettings(), DAILY_NOW + 29 * 60_000)).toBe('morning');
    expect(dueDailyCycle(dailySettings(), DAILY_NOW + 30 * 60_000)).toBeNull();
    expect(dueDailyCycle(dailySettings(), DAILY_NOW + 3 * 3_600_000)).toBeNull();
  });
  it('weekly replaces a colliding evening on configured weekday', () => {
    expect(dueDailyCycle(dailySettings(), Date.parse('2026-01-11T20:00:00Z'))).toBe('weekly');
    expect(dueDailyCycle(dailySettings(), Date.parse('2026-01-12T20:00:00Z'))).toBe('evening');
  });
  it('repeated DST hour maps to the same local date/cycle', () => {
    const settings = dailySettings({ timeZone: 'America/New_York',
      cycles: { morning: { minute: 90, windowMinutes: 30 }, midday: null, evening: null, weekly: null } });
    const first = Date.parse('2026-11-01T05:30:00Z');
    const second = Date.parse('2026-11-01T06:30:00Z');
    expect(localDailyTime(first, settings.timeZone)).toEqual(localDailyTime(second, settings.timeZone));
    expect(dueDailyCycle(settings, first)).toBe('morning');
    expect(dueDailyCycle(settings, second)).toBe('morning');
  });
  it('spring DST gap does not synthesize a missed run', () => {
    const settings = dailySettings({ timeZone: 'America/New_York',
      cycles: { morning: { minute: 150, windowMinutes: 30 }, midday: null, evening: null, weekly: null } });
    expect(dueDailyCycle(settings, Date.parse('2026-03-08T07:00:00Z'))).toBeNull();
  });
  it.each([
    { enabled: false }, { paused: true }, { skipDay: '2026-01-05' }, { snoozedUntil: DAILY_NOW + 1 },
    { quiet: { start: 480, end: 540 } }, { quiet: { start: 1200, end: 540 } }, { quiet: { start: 0, end: 0 } },
  ])('honors global suppression: %j', override => {
    expect(dueDailyCycle(dailySettings(override), DAILY_NOW)).toBeNull();
  });
  it('quiet/snooze expiry is inclusive and skip does not suppress tomorrow', () => {
    expect(dueDailyCycle(dailySettings({ quiet: { start: 1200, end: 480 }, snoozedUntil: DAILY_NOW }), DAILY_NOW)).toBe('morning');
    expect(dueDailyCycle(dailySettings({ skipDay: '2026-01-05' }), DAILY_NOW + 86_400_000)).toBe('morning');
  });
  it.each([NaN, Infinity, -1, 0.5])('refuses invalid clock %s', now => {
    expect(() => dueDailyCycle(dailySettings(), now)).toThrow('DAILY_CLOCK_INVALID');
  });
});

describe('adaptive policy', () => {
  it('orders safety, recovery, urgent obligations, finance before ordinary continuity', () => {
    const all = dailyState([...PILLARS].reverse().map(p => dailyItem(p)));
    expect(selectDailyPlan(dailySettings(), all, empty, DAILY_NOW)?.items.map(i => i.pillar))
      .toEqual(['HIMAYAH', 'SUKOON', 'THABAT']);
    const items = [dailyItem('THABAT', { urgent: false }), dailyItem('MAL_PFOS')];
    expect(selectDailyPlan(dailySettings(), dailyState(items), empty, DAILY_NOW)?.items.map(i => i.pillar))
      .toEqual(['MAL_PFOS', 'THABAT']);
  });
  it.each(['low', 'unknown'] as const)('downshifts %s to one stabilization item, not critique', capacity => {
    const plan = selectDailyPlan(dailySettings(), dailyState([dailyItem('NAQD'), dailyItem('SHURA'), dailyItem('SUKOON')], capacity), empty, DAILY_NOW + 12 * 3_600_000);
    expect(plan?.items).toEqual([{ pillar: 'SUKOON', revision: 1, mode: 'stabilize' }]);
  });
  it('stale recovery is unknown, never permission for critique', () => {
    const state = dailyState([dailyItem('NAQD')]);
    state.capacity.freshUntil = DAILY_NOW;
    expect(selectDailyPlan(dailySettings(), state, empty, DAILY_NOW + 12 * 3_600_000)).toBeNull();
  });
  it('evening permits reflection/critique that morning defers', () => {
    const state = dailyState([dailyItem('YAWMIYAT'), dailyItem('NAQD')]);
    expect(selectDailyPlan(dailySettings(), state, empty, DAILY_NOW)).toBeNull();
    expect(selectDailyPlan(dailySettings(), state, empty, DAILY_NOW + 12 * 3_600_000)?.items.map(i => i.pillar))
      .toEqual(['YAWMIYAT', 'NAQD']);
  });
  it('does not send midday merely because the clock fired', () => {
    expect(selectDailyPlan(dailySettings(), dailyState([dailyItem('THABAT', { urgent: false, material: false })]), empty,
      DAILY_NOW + 4 * 3_600_000)).toBeNull();
  });
  it.each([
    { status: 'acknowledged' as const }, { status: 'completed' as const }, { status: 'dismissed' as const },
    { privacy: 'denied' as const }, { source: 'unavailable' as const }, { freshUntil: DAILY_NOW }, { observedAt: DAILY_NOW + 1 },
  ])('omits non-actionable state %j', override => {
    expect(selectDailyPlan(dailySettings(), dailyState([dailyItem('THABAT', override)]), empty, DAILY_NOW)).toBeNull();
  });
  it('rejects free text, money, duplicate pillars and unknown sources before policy', () => {
    for (const extra of [{ text: 'synthetic-private-marker' }, { amountMilliunits: 1000 }, { source: 'llm' }]) {
      expect(() => parseDailyState({ ...dailyState(), items: [{ ...dailyItem(), ...extra }] })).toThrow(/^DAILY_STATE_INVALID$/);
    }
    expect(() => parseDailyState(dailyState([dailyItem(), dailyItem()]))).toThrow('DAILY_STATE_INVALID');
  });
  it('requires material PFOS-origin alert; never returns invented money or saved status', () => {
    expect(selectDailyPlan(dailySettings(), dailyState([dailyItem('MAL_PFOS', { source: 'native' })]), empty, DAILY_NOW)).toBeNull();
    expect(selectDailyPlan(dailySettings(), dailyState([dailyItem('MAL_PFOS', { material: false })]), empty, DAILY_NOW)).toBeNull();
    const plan = selectDailyPlan(dailySettings(), dailyState([dailyItem('MAL_PFOS')]), empty, DAILY_NOW);
    expect(plan?.items).toEqual([{ pillar: 'MAL_PFOS', revision: 1, mode: 'review' }]);
    expect(plan?.capture).toBe('unavailable');
    expect(JSON.stringify(plan)).not.toMatch(/amount|saved|balance/);
  });
  it('respects pillar snooze, cadence, disabled state and monotonic source revisions', () => {
    for (const pref of [{ enabled: false }, { snoozedUntil: DAILY_NOW + 1 }]) {
      const settings = dailySettings(); Object.assign(settings.pillars.THABAT, pref);
      expect(selectDailyPlan(settings, dailyState(), empty, DAILY_NOW)).toBeNull();
    }
    for (const seen of [{ revision: 1, reservedAt: 0 }, { revision: 2, reservedAt: 0 },
      { revision: 0, reservedAt: DAILY_NOW - 1 }]) {
      expect(selectDailyPlan(dailySettings(), dailyState(), { ...empty, pillars: { THABAT: seen } }, DAILY_NOW)).toBeNull();
    }
  });
  it('clock rollback and minimum gap suppress another plan', () => {
    for (const lastReservedAt of [DAILY_NOW + 1, DAILY_NOW - 1]) {
      expect(selectDailyPlan(dailySettings(), dailyState(), { ...empty, lastReservedAt }, DAILY_NOW)).toBeNull();
    }
  });
});

describe('closed controls and intent mapping', () => {
  it.each(['/pause_daily', 'pause daily', 'أوقف المتابعة'])('maps %s to pause without a tool grant', text => {
    expect(routeDailyText(text, 'unknown')).toEqual({ kind: 'control', control: { kind: 'pause' } });
  });
  it.each(['/help', '/status', '/today', '/checkin', '/plan', '/tafrigh', '/journal', '/finance', '/decision', '/body', '/recap', '/new', '/cancel'])('maps %s to intent only', text => {
    expect(routeDailyText(text, 'unknown').kind).toBe('intent');
  });
  it('defers critique unless high capacity and delegates unrecognized natural text without echo', () => {
    expect(routeDailyText('/grill', 'unknown')).toEqual({ kind: 'defer' });
    expect(routeDailyText('/grill', 'high')).toEqual({ kind: 'intent', intent: 'NAQD' });
    expect(routeDailyText('synthetic-private-marker', 'high')).toEqual({ kind: 'delegate' });
    expect(routeDailyText('/snooze', 'high')).toEqual({ kind: 'clarify' });
    expect(routeDailyText('/snooze 10081', 'high')).toEqual({ kind: 'clarify' });
    expect(routeDailyText('/pause_daily and deploy', 'high')).toEqual({ kind: 'clarify' });
  });
  it('bounds controls, keeps resume distinct from enable, and never mutates its input', () => {
    const original = dailySettings({ enabled: false, paused: true });
    const resumed = applyDailyControl(original, { kind: 'resume' }, DAILY_NOW);
    expect(resumed).toMatchObject({ enabled: false, paused: false, revision: 1 });
    expect(original.paused).toBe(true);
    expect(applyDailyControl(dailySettings(), { kind: 'more' }, DAILY_NOW).maxItems).toBe(3);
    expect(applyDailyControl(dailySettings({ maxItems: 1 }), { kind: 'less' }, DAILY_NOW).maxItems).toBe(1);
    expect(applyDailyControl(dailySettings(), { kind: 'skip' }, DAILY_NOW).skipDay).toBe('2026-01-05');
    expect(() => applyDailyControl(original, { kind: 'snooze', minutes: 10081, pillar: null }, DAILY_NOW)).toThrow('DAILY_CONTROL_INVALID');
  });
  it('maps and applies bounded pillar snooze', () => {
    const route = routeDailyText('/snooze 60 badan', 'high');
    expect(route).toEqual({ kind: 'control', control: { kind: 'snooze', minutes: 60, pillar: 'BADAN' } });
    if (route.kind !== 'control') throw new Error('expected control');
    const next = applyDailyControl(dailySettings(), route.control, DAILY_NOW);
    expect(next.pillars.BADAN.snoozedUntil).toBe(DAILY_NOW + 3_600_000);
    expect(next.snoozedUntil).toBeNull();
  });
});


describe('closed bilingual messages', () => {
  it.each(['en', 'ar'] as const)('renders only selected approved pillar questions in %s', locale => {
    const plan = selectDailyPlan(dailySettings(), dailyState([dailyItem('SUKOON')], 'low'), empty, DAILY_NOW);
    const message = renderDailyMessage(plan, locale);
    expect(message.length).toBeGreaterThan(0);
    expect(message).not.toMatch(/THABAT|MAL_PFOS|NAQD|amount|saved/);
    expect(message.split('\n')).toHaveLength(3);
    if (locale === 'en') expect(message).toContain('No pressure');
    else expect(message).toContain('لا ضغط');
  });
  it('rejects a sentinel hidden in a plan rather than rendering or logging it', () => {
    const plan = selectDailyPlan(dailySettings(), dailyState(), empty, DAILY_NOW);
    expect(() => renderDailyMessage({ ...plan, text: 'synthetic-private-marker' }, 'en')).toThrow(/^DAILY_PLAN_INVALID$/);
  });
  it('journal reflection reports unavailable persistence explicitly', () => {
    const plan = selectDailyPlan(dailySettings(), dailyState([dailyItem('YAWMIYAT')]), empty, DAILY_NOW + 12 * 3_600_000);
    expect(renderDailyMessage(plan, 'en')).toContain('Durable journal capture is unavailable');
  });
});
