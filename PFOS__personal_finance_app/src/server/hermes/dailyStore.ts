/**
 * Synthetic daily-companion persistence reference, NOT a native life or finance writer.
 * Owning authority: PFOS Contract 14 section 11; Contract 06. Phase 14.1 (DC1). DC06/DC07.
 * Injected existing WAL/FULL StoreHandle. No connection, timer, provider or canonical content.
 */
import { z } from 'zod';
import { basename } from 'node:path';
import type { StoreHandle } from '../db/connection.ts';
import { PILLARS, parseDailySettings, parseDailyState, parseDailyPlan, selectDailyPlan,
  type DailySettings, type DailyState, type DailyPlan, type DailyHistory } from './dailyPolicy.ts';

export type DailyDelivery = 'reserved' | 'uncertain' | 'delivered' | 'cancelled';
export interface DailyReceipt { readonly plan: DailyPlan; readonly delivery: DailyDelivery }
export interface DailyStore {
  settings(): DailySettings;
  changeSettings(expectedRevision: number, next: DailySettings): boolean;
  reserve(expectedRevision: number, state: DailyState, now: number): DailyReceipt | null;
  beginDispatch(plan: DailyPlan): boolean;
  cancel(plan: DailyPlan): void;
  delivered(plan: DailyPlan): void;
  receipt(day: string, cycle: string): DailyReceipt | null;
}
const SCHEMA = `
CREATE TABLE IF NOT EXISTS companion_settings (singleton INTEGER PRIMARY KEY CHECK(singleton=1), body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS companion_runs (
  day TEXT NOT NULL, cycle TEXT NOT NULL, created_at INTEGER NOT NULL, plan TEXT NOT NULL,
  delivery TEXT NOT NULL CHECK(delivery IN ('reserved','uncertain','delivered','cancelled')),
  PRIMARY KEY(day,cycle));
CREATE TABLE IF NOT EXISTS companion_seen (
  pillar TEXT PRIMARY KEY, revision INTEGER NOT NULL, reserved_at INTEGER NOT NULL);
`;

/** Only explicit synthetic reference files. Never invoked by app/process startup or migrations. */
export function createDailyReferenceStore(handle: StoreHandle, initial: DailySettings): DailyStore {
  if (basename(handle.filePath) !== 'daily-reference.db') throw new Error('DAILY_REFERENCE_STORE_ONLY');
  const db = handle.db;
  const settingsBody = JSON.stringify(parseDailySettings(initial));
  db.exec(SCHEMA);
  db.prepare('INSERT OR IGNORE INTO companion_settings VALUES (1, ?)').run(settingsBody);

  function transaction<T>(work: () => T): T {
    db.exec('BEGIN IMMEDIATE');
    try { const result = work(); db.exec('COMMIT'); return result; }
    catch { db.exec('ROLLBACK'); throw new Error('DAILY_STORE_FAILED'); }
  }
  function settings(): DailySettings {
    const row = db.prepare('SELECT body FROM companion_settings WHERE singleton=1').get();
    try { return parseDailySettings(JSON.parse(z.object({ body: z.string() }).parse(row).body)); }
    catch { throw new Error('DAILY_SETTINGS_INVALID'); }
  }
  function history(): DailyHistory {
    const last = z.object({ at: z.number().int().nonnegative().nullable() }).parse(
      db.prepare('SELECT MAX(created_at) AS at FROM companion_runs').get());
    const pillars: DailyHistory['pillars'] = {};
    for (const raw of db.prepare('SELECT * FROM companion_seen').all()) {
      const row = z.object({ pillar: z.enum(PILLARS), revision: z.number().int().nonnegative(),
        reserved_at: z.number().int().nonnegative() }).parse(raw);
      pillars[row.pillar] = { revision: row.revision, reservedAt: row.reserved_at };
    }
    return { lastReservedAt: last.at, pillars };
  }
  function transition(plan: DailyPlan, from: DailyDelivery, to: DailyDelivery): boolean {
    return db.prepare('UPDATE companion_runs SET delivery=? WHERE day=? AND cycle=? AND plan=? AND delivery=?')
      .run(to, plan.day, plan.cycle, JSON.stringify(parseDailyPlan(plan)), from).changes === 1;
  }
  return {
    settings,
    changeSettings(expectedRevision, next) {
      const parsed = parseDailySettings(next);
      return transaction(() => {
        if (settings().revision !== expectedRevision || parsed.revision !== expectedRevision + 1) return false;
        const body = JSON.stringify(parsed);
        db.prepare('UPDATE companion_settings SET body=? WHERE singleton=1').run(body);
        if (JSON.stringify(settings()) !== body) throw new Error('DAILY_SETTINGS_READBACK_FAILED');
        return true;
      });
    },
    reserve(expectedRevision, rawState, now) {
      const state = parseDailyState(rawState);
      return transaction(() => {
        const current = settings();
        if (current.revision !== expectedRevision) return null;
        const plan = selectDailyPlan(current, state, history(), now);
        if (plan === null) return null;
        const inserted = db.prepare('INSERT OR IGNORE INTO companion_runs VALUES (?, ?, ?, ?, ?)')
          .run(plan.day, plan.cycle, now, JSON.stringify(plan), 'reserved').changes;
        if (inserted !== 1) return null;
        for (const item of plan.items) db.prepare(`INSERT INTO companion_seen VALUES (?, ?, ?)
          ON CONFLICT(pillar) DO UPDATE SET revision=excluded.revision, reserved_at=excluded.reserved_at`)
          .run(item.pillar, item.revision, now);
        return { plan, delivery: 'reserved' };
      });
    },
    beginDispatch(plan) {
      return transaction(() => {
        if (settings().revision !== plan.settingsRevision) { transition(plan, 'reserved', 'cancelled'); return false; }
        return transition(plan, 'reserved', 'uncertain');
      });
    },
    cancel: plan => { transition(plan, 'reserved', 'cancelled'); },
    delivered: plan => {
      if (!transition(plan, 'uncertain', 'delivered')) throw new Error('DAILY_SETTLEMENT_FAILED');
    },
    receipt(day, cycle) {
      const raw = db.prepare('SELECT plan, delivery FROM companion_runs WHERE day=? AND cycle=?').get(day, cycle);
      if (!raw) return null;
      try {
        const row = z.object({ plan: z.string(), delivery: z.enum(['reserved', 'uncertain', 'delivered', 'cancelled']) }).parse(raw);
        return { plan: parseDailyPlan(JSON.parse(row.plan)), delivery: row.delivery };
      } catch { throw new Error('DAILY_RECEIPT_INVALID'); }
    },
  };
}
