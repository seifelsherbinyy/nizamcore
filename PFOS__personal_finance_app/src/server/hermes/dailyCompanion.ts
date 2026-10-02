/**
 * Authorized daily tick orchestration behind injected source/store/dispatch ports.
 * Owning authority: PFOS Contract 14 section 11; Contracts 06/12. Phase 14.1 (DC1). DC07-DC10.
 * No live binding. Native dispatch must enforce current fences at the actual effect boundary.
 */
import { dueDailyCycle, localDailyTime, parseDailyState, parseDailySettings, type DailyPlan } from './dailyPolicy.ts';
import { applyDailyControl } from './dailyControls.ts';
import type { DailyStore } from './dailyStore.ts';

export interface DailyIdentity { readonly owner: string; readonly privateChat: string }
export interface DailyActor { readonly user: string; readonly chat: string; readonly chatType: string; readonly isBot: boolean }
export interface DailyPorts {
  readonly store: DailyStore;
  readonly now: () => number;
  /** True only with current HIMAYAH consent AND both kill forms clear. Throw means deny. */
  readonly permitted: () => boolean;
  readonly identity: () => DailyIdentity | null;
  /** Privacy/source identity validated by native governor before returning closed bounded metadata. */
  readonly readState: () => Promise<unknown>;
  /** Must revalidate current fences, bound timeout, grant/cap and private destination itself. */
  readonly dispatch: (plan: DailyPlan, fence: { identity: DailyIdentity; settingsRevision: number }) => Promise<'delivered' | 'uncertain'>;
}
export type DailyTickOutcome = 'blocked' | 'idle' | 'duplicate_or_changed' | 'delivered' | 'uncertain' | 'failed';

function identity(ports: DailyPorts): DailyIdentity | null {
  try {
    if (ports.permitted() !== true) return null;
    const value = ports.identity();
    if (!value || typeof value.owner !== 'string' || typeof value.privateChat !== 'string' || !/^[1-9][0-9]{0,19}$/.test(value.owner) || !/^[1-9][0-9]{0,19}$/.test(value.privateChat)) return null;
    return { owner: value.owner, privateChat: value.privateChat };
  } catch { return null; }
}
function sameIdentity(a: DailyIdentity, b: DailyIdentity | null): boolean {
  return b !== null && a.owner === b.owner && a.privateChat === b.privateChat;
}
export function dailyActorAuthorized(ports: DailyPorts, actor: DailyActor): boolean {
  const owner = identity(ports);
  return owner !== null && actor.isBot === false && actor.chatType === 'private' &&
    actor.user === owner.owner && actor.chat === owner.privateChat;
}

export function createDailyCompanion(ports: DailyPorts): {
  tick(): Promise<DailyTickOutcome>;
  control(actor: DailyActor, command: unknown): 'applied' | 'blocked' | 'conflict' | 'failed';
} {
  return {
    async tick() {
      const owner = identity(ports);
      if (!owner) return 'blocked';
      let attempted = false;
      try {
        const settings = parseDailySettings(ports.store.settings());
        const startedAt = ports.now();
        const cycle = dueDailyCycle(settings, startedAt);
        if (cycle === null) return 'idle';
        if (ports.store.receipt(localDailyTime(startedAt, settings.timeZone).day, cycle)) return 'duplicate_or_changed';
        const state = parseDailyState(await ports.readState());
        if (!sameIdentity(owner, identity(ports))) return 'blocked';
        const reservation = ports.store.reserve(settings.revision, state, ports.now());
        if (!reservation) return 'duplicate_or_changed';
        const plan = reservation.plan;
        if (!sameIdentity(owner, identity(ports))) { ports.store.cancel(plan); return 'blocked'; }
        if (!ports.store.beginDispatch(plan)) return 'duplicate_or_changed';
        attempted = true;
        const result = await ports.dispatch(plan, { identity: owner, settingsRevision: plan.settingsRevision });
        if (result !== 'delivered') return 'uncertain';
        ports.store.delivered(plan);
        return 'delivered';
      } catch { return attempted ? 'uncertain' : 'failed'; }
    },
    control(actor, command) {
      if (!dailyActorAuthorized(ports, actor)) return 'blocked';
      try {
        const current = ports.store.settings();
        const next = applyDailyControl(current, command, ports.now());
        if (!dailyActorAuthorized(ports, actor)) return 'blocked';
        return ports.store.changeSettings(current.revision, next) ? 'applied' : 'conflict';
      } catch { return 'failed'; }
    },
  };
}
