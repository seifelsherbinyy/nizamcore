/**
 * NIZAM · Notification outbox tests — the durable intent to notify
 * Implemented by: PFOS Contract 06 / Phase 1.2 (spec transaction-capture-pipeline, increment 9)
 * Owning authority: owner decision D-J, docs/adr/ADR-0004-production-release-decisions.md.
 *
 * ALL FIXTURE DATA IS SYNTHETIC. No amount appears in any fixture here at all, which is the point:
 * this table holds references and delivery state, never money and never message prose.
 *
 * The central test is the one the outbox exists for: a posting and its notification intent share a
 * transaction, so a failure after the posting but before the commit leaves NEITHER. That property is
 * asserted against the real engine, because it is a property of the engine's transaction semantics and
 * a double would assert nothing about it.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { openTestStore, type TestStore } from './testStore.ts';
import { withTransaction } from './support.ts';
import {
  createNotificationOutboxRepository,
  OutboxRowMissingError,
  OutboxTransitionError,
  type NotificationOutboxRepository,
} from './notificationOutboxRepository.ts';

let store: TestStore;
let outbox: NotificationOutboxRepository;

const CAUSE = 'txn-synthetic-0001';
const TARGET = 'target-ref-synthetic-01';
const BODY = 'body-ref-synthetic-01';

function enqueueOne(over: Partial<Parameters<NotificationOutboxRepository['enqueue']>[0]> = {}) {
  return outbox.enqueue({
    id: 'obx-synthetic-0001',
    dedupKey: 'dedup-synthetic-0001',
    channel: 'slack',
    targetRef: TARGET,
    bodyRef: BODY,
    causeRef: CAUSE,
    ...over,
  });
}

beforeEach(() => {
  store = openTestStore();
  outbox = createNotificationOutboxRepository(store.ctx);
});

afterEach(() => {
  store.close();
});

describe('migration 9 creates the outbox', () => {
  it('creates the table with its indexes, so the relay scan is not a table scan', () => {
    const tables = store.ctx.handle.db
      .prepare(`SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'notification_outbox'`)
      .all();
    expect(tables).toHaveLength(1);
    const indexes = store.ctx.handle.db
      .prepare(`SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'notification_outbox'`)
      .all()
      .map((r) => String((r as { name: string }).name));
    expect(indexes).toContain('notification_outbox_state');
    expect(indexes).toContain('notification_outbox_cause');
  });

  it('holds no monetary column, because a transport table is not a place to read a balance', () => {
    const columns = store.ctx.handle.db
      .prepare(`SELECT name FROM pragma_table_info('notification_outbox')`)
      .all()
      .map((r) => String((r as { name: string }).name));
    for (const banned of ['amount', 'amount_milliunits', 'currency', 'balance', 'inflow', 'outflow', 'total']) {
      expect(columns, `${banned} must not exist on the outbox`).not.toContain(banned);
    }
    expect(columns).toContain('body_ref');
    expect(columns).toContain('cause_ref');
  });
});

describe('enqueue is idempotent', () => {
  it('inserts a pending row with zero attempts and no send evidence', () => {
    const { row, inserted } = enqueueOne();
    expect(inserted).toBe(true);
    expect(row.state).toBe('pending');
    expect(row.attempts).toBe(0);
    expect(row.sentAt).toBeNull();
    expect(row.receiptRef).toBeNull();
    expect(row.lastErrorCode).toBeNull();
    expect(row.causeRef).toBe(CAUSE);
  });

  it('absorbs a replay of the same dedup key instead of queuing a second delivery', () => {
    const first = enqueueOne();
    const second = enqueueOne({ id: 'obx-synthetic-0002' });
    expect(first.inserted).toBe(true);
    expect(second.inserted).toBe(false);
    // The SECOND id is discarded and the first row is returned: one intent, one delivery.
    expect(second.row.id).toBe(first.row.id);
    expect(outbox.countByState('pending')).toBe(1);
  });

  it('keeps distinct dedup keys distinct, so two real notifications are not collapsed into one', () => {
    enqueueOne();
    const other = enqueueOne({ id: 'obx-synthetic-0003', dedupKey: 'dedup-synthetic-0002' });
    expect(other.inserted).toBe(true);
    expect(outbox.countByState('pending')).toBe(2);
  });
});

describe('the transaction property this table exists for', () => {
  it('leaves NO intent when the surrounding transaction fails after the enqueue', () => {
    expect(() =>
      withTransaction(store.ctx.handle.db, () => {
        enqueueOne();
        // Stand-in for the posting failing after the intent was recorded.
        throw new Error('synthetic posting failure');
      }),
    ).toThrow('synthetic posting failure');

    // Not "probably rolled back" — observed absent, by both lookups.
    expect(outbox.findById('obx-synthetic-0001')).toBeNull();
    expect(outbox.findByDedupKey('dedup-synthetic-0001')).toBeNull();
    expect(outbox.countByState('pending')).toBe(0);
  });

  it('keeps the intent when the surrounding transaction commits', () => {
    withTransaction(store.ctx.handle.db, () => {
      enqueueOne();
    });
    expect(outbox.findById('obx-synthetic-0001')).not.toBeNull();
    expect(outbox.countByState('pending')).toBe(1);
  });
});

describe('claiming and settling', () => {
  it('returns oldest pending first and bounds the batch', () => {
    enqueueOne();
    enqueueOne({ id: 'obx-synthetic-0004', dedupKey: 'dedup-synthetic-0004' });
    enqueueOne({ id: 'obx-synthetic-0005', dedupKey: 'dedup-synthetic-0005' });
    const batch = outbox.claimPending(2);
    expect(batch).toHaveLength(2);
    expect(batch[0]?.id).toBe('obx-synthetic-0001');
    expect(batch[1]?.id).toBe('obx-synthetic-0004');
  });

  it('refuses a nonsense batch size rather than inventing one', () => {
    enqueueOne();
    expect(outbox.claimPending(0)).toEqual([]);
    expect(outbox.claimPending(-1)).toEqual([]);
    expect(outbox.claimPending(1.5)).toEqual([]);
  });

  it('marks sent only with a receipt, and records the attempt', () => {
    enqueueOne();
    const sent = outbox.markSent('obx-synthetic-0001', 'receipt-ref-synthetic-01');
    expect(sent.state).toBe('sent');
    expect(sent.receiptRef).toBe('receipt-ref-synthetic-01');
    expect(sent.sentAt).not.toBeNull();
    expect(sent.attempts).toBe(1);
    expect(outbox.countByState('pending')).toBe(0);
  });

  it('absorbs a duplicated settle instead of counting a second attempt', () => {
    enqueueOne();
    const first = outbox.markSent('obx-synthetic-0001', 'receipt-ref-synthetic-01');
    const again = outbox.markSent('obx-synthetic-0001', 'receipt-ref-synthetic-02');
    expect(again.attempts).toBe(first.attempts);
    expect(again.receiptRef).toBe('receipt-ref-synthetic-01');
  });

  it('returns a failed row to pending with its code, so it stays claimable', () => {
    enqueueOne();
    const failed = outbox.markFailed('obx-synthetic-0001', 'SYNTHETIC_TRANSIENT');
    expect(failed.state).toBe('pending');
    expect(failed.attempts).toBe(1);
    expect(failed.lastErrorCode).toBe('SYNTHETIC_TRANSIENT');
    expect(outbox.claimPending(5)).toHaveLength(1);
  });

  it('abandons terminally, and nothing revives it', () => {
    enqueueOne();
    const abandoned = outbox.abandon('obx-synthetic-0001', 'SYNTHETIC_PERMANENT');
    expect(abandoned.state).toBe('abandoned');
    expect(outbox.claimPending(5)).toEqual([]);
    expect(() => outbox.markFailed('obx-synthetic-0001', 'SYNTHETIC_TRANSIENT')).toThrow(OutboxTransitionError);
    expect(() => outbox.markSent('obx-synthetic-0001', 'receipt-ref-synthetic-03')).toThrow(OutboxTransitionError);
  });

  it('refuses to settle a row that does not exist rather than creating one', () => {
    expect(() => outbox.markSent('obx-absent', 'receipt-ref-synthetic-04')).toThrow(OutboxRowMissingError);
    expect(() => outbox.markFailed('obx-absent', 'SYNTHETIC_TRANSIENT')).toThrow(OutboxRowMissingError);
    expect(outbox.countByState('pending')).toBe(0);
  });
});

describe('the engine refuses an incoherent sent row', () => {
  it('will not accept sent without send evidence, even by direct SQL', () => {
    enqueueOne();
    expect(() =>
      store.ctx.handle.db
        .prepare(`UPDATE notification_outbox SET state = 'sent' WHERE id = ?`)
        .run('obx-synthetic-0001'),
    ).toThrow();
  });

  it('will not accept send evidence on a row that is not sent', () => {
    enqueueOne();
    expect(() =>
      store.ctx.handle.db
        .prepare(`UPDATE notification_outbox SET sent_at = '2026-01-01T00:00:00.000Z' WHERE id = ?`)
        .run('obx-synthetic-0001'),
    ).toThrow();
  });
});

describe('the audit trail', () => {
  it('records the enqueue and the abandon, with column names and references only in the detail', () => {
    enqueueOne();
    outbox.abandon('obx-synthetic-0001', 'SYNTHETIC_PERMANENT');
    const rows = store.ctx.handle.db
      .prepare(`SELECT action, detail FROM audit_log WHERE entity_table = 'notification_outbox' ORDER BY id`)
      .all()
      .map((r) => r as { action: string; detail: string });
    const actions = rows.map((r) => r.action);
    expect(actions).toContain('notification_enqueued');
    expect(actions).toContain('notification_abandoned');

    // Asserted EXACTLY rather than by pattern. A first attempt here used /\d{3,}/ as a stand-in for
    // "no amount", and it failed on the cause reference `txn-synthetic-0001` — a reference is supposed
    // to be there. A fuzzy ban on digits cannot tell an identifier from a figure, so the detail is
    // pinned to its literal content instead: change it deliberately and this test tells you.
    const details = rows.map((r) => r.detail).sort();
    expect(details).toEqual(['channel,cause_ref,dedup_key for txn-synthetic-0001', 'state,last_error_code']);

    // And the property the exact match is protecting: no formatted monetary figure, in any detail.
    for (const detail of details) {
      expect(detail, 'a decimal amount must never reach an audit detail').not.toMatch(/\d+[.,]\d{2}\b/);
      expect(detail, 'a currency code must never reach an audit detail').not.toMatch(/\b(EGP|USD|EUR|GBP)\b/);
    }
  });

  it('records nothing for an absorbed replay, because nothing happened', () => {
    enqueueOne();
    enqueueOne({ id: 'obx-synthetic-0006' });
    const count = store.ctx.handle.db
      .prepare(`SELECT COUNT(*) AS n FROM audit_log WHERE action = 'notification_enqueued'`)
      .get() as { n: number };
    expect(Number(count.n)).toBe(1);
  });
});
