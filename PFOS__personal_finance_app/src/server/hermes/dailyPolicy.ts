/**
 * Daily companion deterministic policy. No source text, monetary value, tool or credential.
 * Owning authority: PFOS Contract 14 section 11; Contracts 06/12. Phase 14.1 (DC1).
 * Spec: telegram-daily-companion, DC01-DC05/DC11. Injected state only, not native truth.
 */
import { z } from 'zod';

export const DAILY_POLICY_VERSION = 'telegram-companion-v3' as const;
export const PILLARS = ['HIMAYAH', 'SUKOON', 'THABAT', 'MAL_PFOS', 'SHURA', 'QARAR',
  'BADAN', 'YAWMIYAT', 'TAFRIGH', 'NAQD'] as const;
export type Pillar = typeof PILLARS[number];
export const CYCLES = ['weekly', 'morning', 'midday', 'evening'] as const;
export type DailyCycle = typeof CYCLES[number];
const minute = z.number().int().min(0).max(1439);
const instant = z.number().int().min(0).max(8_640_000_000_000_000);
const revision = z.number().int().min(0).max(Number.MAX_SAFE_INTEGER - 1);
const day = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const pillar = z.enum(PILLARS);
const windowSchema = z.object({ minute, windowMinutes: z.number().int().min(1).max(180) }).strict();
const pillarPreference = z.object({
  enabled: z.boolean(), snoozedUntil: instant.nullable(),
  minIntervalMinutes: z.number().int().min(1).max(10080),
}).strict();
const timeZone = z.string().min(1).max(100).refine(value => {
  try { new Intl.DateTimeFormat('en', { timeZone: value }).format(0); return true; }
  catch { return false; }
});
export const dailySettingsSchema = z.object({
  version: z.literal(DAILY_POLICY_VERSION), revision, enabled: z.boolean(), paused: z.boolean(),
  timeZone, quiet: z.object({ start: minute, end: minute }).strict().nullable(),
  skipDay: day.nullable(), snoozedUntil: instant.nullable(),
  maxItems: z.number().int().min(1).max(3), minGapMinutes: z.number().int().min(1).max(1440),
  cycles: z.object({
    morning: windowSchema.nullable(), midday: windowSchema.nullable(), evening: windowSchema.nullable(),
    weekly: windowSchema.extend({ weekday: z.number().int().min(0).max(6) }).nullable(),
  }).strict(),
  pillars: z.object(Object.fromEntries(PILLARS.map(p => [p, pillarPreference])) as
    Record<Pillar, typeof pillarPreference>).strict(),
}).strict();
export type DailySettings = z.infer<typeof dailySettingsSchema>;

const itemSchema = z.object({
  pillar, revision, observedAt: instant, freshUntil: instant,
  status: z.enum(['active', 'acknowledged', 'completed', 'dismissed']),
  privacy: z.enum(['approved', 'denied']), source: z.enum(['native', 'pfos', 'unavailable']),
  urgent: z.boolean(), material: z.boolean(),
}).strict().refine(item => item.freshUntil > item.observedAt);
export type PillarState = z.infer<typeof itemSchema>;
const capacitySchema = z.enum(['low', 'normal', 'high', 'unknown']);
export type Capacity = z.infer<typeof capacitySchema>;
const dailyStateSchema = z.object({
  capacity: z.object({ level: capacitySchema, observedAt: instant, freshUntil: instant }).strict(),
  items: z.array(itemSchema).max(PILLARS.length),
}).strict().refine(state => new Set(state.items.map(item => item.pillar)).size === state.items.length);
export type DailyState = z.infer<typeof dailyStateSchema>;
export interface DailyHistory {
  readonly lastReservedAt: number | null;
  readonly pillars: Partial<Record<Pillar, { revision: number; reservedAt: number }>>;
}
export const dailyPlanSchema = z.object({
  version: z.literal(DAILY_POLICY_VERSION), settingsRevision: revision, day, cycle: z.enum(CYCLES),
  createdAt: instant, capacity: capacitySchema,
  items: z.array(z.object({ pillar, revision, mode: z.enum(['stabilize', 'review']) }).strict()).min(1).max(3),
  capture: z.literal('unavailable'),
}).strict();
export type DailyPlan = z.infer<typeof dailyPlanSchema>;

/** Never propagate validation details: rejected values may be credentials. */
export function parseDailySettings(value: unknown): DailySettings {
  const result = dailySettingsSchema.safeParse(value);
  if (!result.success) throw new Error('DAILY_SETTINGS_INVALID');
  return result.data;
}
export function parseDailyState(value: unknown): DailyState {
  const result = dailyStateSchema.safeParse(value);
  if (!result.success) throw new Error('DAILY_STATE_INVALID');
  return result.data;
}
export function parseDailyPlan(value: unknown): DailyPlan {
  const result = dailyPlanSchema.safeParse(value);
  if (!result.success) throw new Error('DAILY_PLAN_INVALID');
  return result.data;
}
export function assertDailyInstant(now: number): void {
  if (!instant.safeParse(now).success) throw new Error('DAILY_CLOCK_INVALID');
}

export function localDailyTime(now: number, zone: string): { day: string; minute: number; weekday: number } {
  assertDailyInstant(now);
  try {
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: zone, year: 'numeric', month: '2-digit',
      day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', weekday: 'short' }).formatToParts(now);
    const get = (name: Intl.DateTimeFormatPartTypes): string => parts.find(p => p.type === name)?.value ?? '';
    const localDay = `${get('year')}-${get('month')}-${get('day')}`;
    if (!day.safeParse(localDay).success) throw new Error();
    return { day: localDay, minute: Number(get('hour')) * 60 + Number(get('minute')),
      weekday: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(get('weekday')) };
  } catch { throw new Error('DAILY_CLOCK_INVALID'); }
}

export function dueDailyCycle(settings: DailySettings, now: number): DailyCycle | null {
  const local = localDailyTime(now, settings.timeZone);
  if (!settings.enabled || settings.paused || settings.skipDay === local.day ||
      (settings.snoozedUntil !== null && now < settings.snoozedUntil)) return null;
  const quiet = settings.quiet;
  if (quiet !== null && (quiet.start === quiet.end || (quiet.start < quiet.end
    ? local.minute >= quiet.start && local.minute < quiet.end
    : local.minute >= quiet.start || local.minute < quiet.end))) return null;
  for (const cycle of CYCLES) {
    const window = settings.cycles[cycle];
    if (window === null || (cycle === 'weekly' && settings.cycles.weekly?.weekday !== local.weekday)) continue;
    if (local.minute >= window.minute && local.minute < window.minute + window.windowMinutes) return cycle;
  }
  return null;
}

function priority(item: PillarState): number {
  if (item.pillar === 'HIMAYAH') return 0;
  if (item.pillar === 'SUKOON') return 1;
  if (item.pillar === 'THABAT' && item.urgent) return 2;
  if (item.pillar === 'MAL_PFOS') return 3;
  return PILLARS.indexOf(item.pillar) + 4;
}
function fresh(observedAt: number, freshUntil: number, now: number): boolean {
  return observedAt <= now && now < freshUntil;
}
function eligible(item: PillarState, settings: DailySettings, history: DailyHistory,
  cycle: DailyCycle, capacity: Capacity, now: number): boolean {
  const pref = settings.pillars[item.pillar];
  const seen = history.pillars[item.pillar];
  if (!pref.enabled || (pref.snoozedUntil !== null && now < pref.snoozedUntil) ||
    item.status !== 'active' || item.privacy !== 'approved' || item.source === 'unavailable' ||
    !fresh(item.observedAt, item.freshUntil, now)) return false;
  if (seen && (item.revision <= seen.revision || now - seen.reservedAt < pref.minIntervalMinutes * 60_000)) return false;
  if (item.pillar === 'MAL_PFOS' && (item.source !== 'pfos' || !item.material)) return false;
  if (item.pillar !== 'MAL_PFOS' && item.source !== 'native') return false;
  if (item.pillar === 'NAQD' && capacity !== 'high') return false;
  if ((capacity === 'low' || capacity === 'unknown') &&
    !['HIMAYAH', 'SUKOON', 'MAL_PFOS'].includes(item.pillar) && !(item.pillar === 'THABAT' && item.urgent)) return false;
  if (cycle === 'midday' && !item.urgent && !item.material) return false;
  if (cycle === 'morning' && ['YAWMIYAT', 'TAFRIGH', 'NAQD'].includes(item.pillar)) return false;
  return true;
}

export function selectDailyPlan(settings: DailySettings, state: DailyState,
  history: DailyHistory, now: number): DailyPlan | null {
  const cycle = dueDailyCycle(settings, now);
  if (cycle === null || (history.lastReservedAt !== null &&
    now - history.lastReservedAt < settings.minGapMinutes * 60_000)) return null;
  const capacity = fresh(state.capacity.observedAt, state.capacity.freshUntil, now) ? state.capacity.level : 'unknown';
  const downshift = capacity === 'low' || capacity === 'unknown';
  const items = state.items.filter(item => eligible(item, settings, history, cycle, capacity, now))
    .sort((a, b) => priority(a) - priority(b)).slice(0, downshift ? 1 : settings.maxItems)
    .map(item => ({ pillar: item.pillar, revision: item.revision, mode: downshift ? 'stabilize' as const : 'review' as const }));
  if (items.length === 0) return null;
  return { version: DAILY_POLICY_VERSION, settingsRevision: settings.revision,
    day: localDailyTime(now, settings.timeZone).day, cycle, createdAt: now, capacity, items, capture: 'unavailable' };
}
