/**
 * Daily companion exact control parsing and bounded preference transitions.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1). DC03/DC09.
 * Intent only: no text executes a tool or widens authority.
 */
import { z } from 'zod';
import { PILLARS, localDailyTime, parseDailySettings, assertDailyInstant,
  type Capacity, type DailySettings } from './dailyPolicy.ts';

const controlSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.enum(['pause', 'resume', 'skip', 'less', 'more']) }).strict(),
  z.object({ kind: z.literal('snooze'), minutes: z.number().int().min(1).max(10080),
    pillar: z.enum(PILLARS).nullable() }).strict(),
]);
export type DailyControl = z.infer<typeof controlSchema>;
const CONTROL_WORDS: Readonly<Record<string, DailyControl['kind']>> = {
  '/pause_daily': 'pause', 'pause daily': 'pause', 'أوقف المتابعة': 'pause',
  '/resume_daily': 'resume', 'resume daily': 'resume', 'استأنف المتابعة': 'resume',
  '/skip_today': 'skip', 'skip today': 'skip', 'تخطى اليوم': 'skip',
  '/less': 'less', less: 'less', 'أقل': 'less', '/more': 'more', more: 'more', 'أكثر': 'more',
};
const COMMANDS = {
  '/help': 'help', '/status': 'status', '/today': 'today', '/checkin': 'checkin',
  '/plan': 'SHURA', '/tafrigh': 'TAFRIGH', '/journal': 'YAWMIYAT', '/finance': 'MAL_PFOS',
  '/decision': 'QARAR', '/grill': 'NAQD', '/body': 'BADAN', '/recap': 'THABAT',
  '/new': 'new', '/cancel': 'cancel',
} as const;
export type DailyRoute = { kind: 'control'; control: DailyControl } |
  { kind: 'intent'; intent: typeof COMMANDS[keyof typeof COMMANDS] } |
  { kind: 'defer' | 'clarify' | 'delegate' };

export function routeDailyText(text: string, capacity: Capacity): DailyRoute {
  if (text.length > 2000) return { kind: 'clarify' };
  const body = text.trim().toLowerCase();
  const control = Object.hasOwn(CONTROL_WORDS, body) ? CONTROL_WORDS[body] : undefined;
  if (control && control !== 'snooze') return { kind: 'control', control: { kind: control } };
  const snooze = /^\/snooze ([1-9][0-9]{0,4})(?: (himayah|sukoon|thabat|mal_pfos|shura|qarar|badan|yawmiyat|tafrigh|naqd))?$/.exec(body);
  if (snooze) {
    const result = controlSchema.safeParse({ kind: 'snooze', minutes: Number(snooze[1]), pillar: snooze[2]?.toUpperCase() ?? null });
    return result.success ? { kind: 'control', control: result.data } : { kind: 'clarify' };
  }
  if (Object.hasOwn(COMMANDS, body)) {
    const intent = COMMANDS[body as keyof typeof COMMANDS];
    if (intent === 'NAQD' && capacity !== 'high') return { kind: 'defer' };
    return { kind: 'intent', intent };
  }
  return { kind: body.startsWith('/') ? 'clarify' : 'delegate' };
}

export function applyDailyControl(settings: DailySettings, raw: unknown, now: number): DailySettings {
  assertDailyInstant(now);
  const parsed = controlSchema.safeParse(raw);
  if (!parsed.success) throw new Error('DAILY_CONTROL_INVALID');
  const control = parsed.data;
  const next = parseDailySettings(settings);
  next.revision += 1;
  switch (control.kind) {
    case 'pause': next.paused = true; break;
    case 'resume': next.paused = false; break;
    case 'skip': next.skipDay = localDailyTime(now, next.timeZone).day; break;
    case 'less': next.maxItems = Math.max(1, next.maxItems - 1); break;
    case 'more': next.maxItems = Math.min(3, next.maxItems + 1); break;
    case 'snooze': {
      const until = now + control.minutes * 60_000;
      if (control.pillar === null) next.snoozedUntil = until;
      else next.pillars[control.pillar].snoozedUntil = until;
      break;
    }
  }
  return parseDailySettings(next);
}
