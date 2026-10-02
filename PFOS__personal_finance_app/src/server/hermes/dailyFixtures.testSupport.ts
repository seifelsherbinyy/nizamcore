/**
 * Synthetic daily-companion fixtures only; no credentials, private records or live bindings.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1). DC12.
 */
import { DAILY_POLICY_VERSION, PILLARS, type DailySettings, type DailyState,
  type Pillar, type PillarState } from './dailyPolicy.ts';
export const DAILY_NOW = Date.parse('2026-01-05T08:00:00Z');
export function dailySettings(overrides: Partial<DailySettings> = {}): DailySettings {
  return { version: DAILY_POLICY_VERSION, revision: 0, enabled: true, paused: false,
    timeZone: 'UTC', quiet: null, skipDay: null, snoozedUntil: null, maxItems: 3, minGapMinutes: 60,
    cycles: { morning: { minute: 480, windowMinutes: 30 }, midday: { minute: 720, windowMinutes: 30 },
      evening: { minute: 1200, windowMinutes: 30 }, weekly: { minute: 1200, windowMinutes: 30, weekday: 0 } },
    pillars: Object.fromEntries(PILLARS.map(p => [p, { enabled: true, snoozedUntil: null, minIntervalMinutes: 60 }])) as DailySettings['pillars'],
    ...overrides };
}
export function dailyItem(pillar: Pillar = 'THABAT', overrides: Partial<PillarState> = {}): PillarState {
  return { pillar, revision: 1, observedAt: DAILY_NOW - 60_000, freshUntil: DAILY_NOW + 86_400_000,
    status: 'active', privacy: 'approved', source: pillar === 'MAL_PFOS' ? 'pfos' : 'native',
    urgent: true, material: true, ...overrides };
}
export function dailyState(items = [dailyItem()], level: DailyState['capacity']['level'] = 'high'): DailyState {
  return { capacity: { level, observedAt: DAILY_NOW - 60_000, freshUntil: DAILY_NOW + 86_400_000 }, items };
}
