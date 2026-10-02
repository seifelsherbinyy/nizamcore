/**
 * NIZAM · Notification outbox — the durable intent to notify
 * Implemented by: PFOS Contract 06 / Phase 1.2 (spec transaction-capture-pipeline, increment 9)
 * Depends on: support.ts, ../schema.ts (migration 9)
 *
 * Owner decision **D-J**, recorded in `docs/adr/ADR-0004-production-release-decisions.md`.
 *
 * ## What this is for
 *
 * `enqueue` is designed to be called **inside the posting's own transaction**. That is the whole point:
 * the financial fact and the intent to tell the owner about it either both land or neither does. A relay
 * then reads the intent and sends. A crash between them leaves a `pending` row, which is recoverable,
 * rather than nothing, which is not.
 *
 * ## The guarantee
 *
 * **At-least-once with deduplication. Not exactly-once**, and nothing here may be described as such.
 * `dedup_key` is UNIQUE, so a replayed enqueue is absorbed by the constraint rather than by a
 * read-then-write check that two concurrent callers could both pass.
 *
 * ## Money
 *
 * This module holds none, and must not import the money persistence boundary — `AC19` pins that
 * boundary's importer set to the financial writers exactly, so a new importer is a gate failure and
 * would also be a lie about what this table is. `bodyRef` and `causeRef` are references; the message is
 * composed from canonical state at send time, so a figure cannot be frozen here and delivered stale.
 */
import {
  recordAudit,
  toNullableText,
  withTransaction,
  type RepositoryContext,
} from './support.ts';

const TABLE = 'notification_outbox';

/** Delivery state. `failed` is retryable; `abandoned` is terminal. Collapsing them loses that. */
export type OutboxState = 'pending' | 'sent' | 'failed' | 'abandoned';

export interface OutboxRow {
  readonly id: string;
  readonly dedupKey: string;
  readonly channel: 'slack' | 'internal';
  readonly targetRef: string;
  readonly bodyRef: string;
  readonly causeRef: string;
  readonly state: OutboxState;
  readonly attempts: number;
  readonly enqueuedAt: string;
  readonly lastAttemptAt: string | null;
  readonly lastErrorCode: string | null;
  readonly sentAt: string | null;
  readonly receiptRef: string | null;
}

export interface EnqueueInput {
  /** Caller-supplied stable id. A retry of the same logical intent supplies the same id. */
  readonly id: string;
  /** The idempotency key. Two intents that mean the same delivery share it. */
  readonly dedupKey: string;
  readonly channel: 'slack' | 'internal';
  readonly targetRef: string;
  readonly bodyRef: string;
  /** What caused the notification — a transaction id, a statement id, a run id. */
  readonly causeRef: string;
}

export interface EnqueueResult {
  readonly row: OutboxRow;
  /** `false` when the dedup key was already present, so the existing row is returned unchanged. */
  readonly inserted: boolean;
}

/** Raised when a caller asks to settle a row that is not there. Never silently created. */
export class OutboxRowMissingError extends Error {
  readonly code = 'OUTBOX_ROW_MISSING';
  constructor(id: string) {
    super(`NIZAM outbox: no row with id "${id}"; a settle call never creates one`);
    this.name = 'OutboxRowMissingError';
  }
}

/** Raised when a transition is not legal from the row's current state. */
export class OutboxTransitionError extends Error {
  readonly code = 'OUTBOX_TRANSITION_REFUSED';
  constructor(id: string, from: OutboxState, to: OutboxState) {
    super(`NIZAM outbox: row "${id}" cannot move from ${from} to ${to}`);
    this.name = 'OutboxTransitionError';
  }
}

function mapRow(raw: unknown): OutboxRow {
  const r = raw as Record<string, unknown>;
  return {
    id: String(r.id),
    dedupKey: String(r.dedup_key),
    channel: String(r.channel) as 'slack' | 'internal',
    targetRef: String(r.target_ref),
    bodyRef: String(r.body_ref),
    causeRef: String(r.cause_ref),
    state: String(r.state) as OutboxState,
    attempts: Number(r.attempts),
    enqueuedAt: String(r.enqueued_at),
    lastAttemptAt: toNullableText(r.last_attempt_at),
    lastErrorCode: toNullableText(r.last_error_code),
    sentAt: toNullableText(r.sent_at),
    receiptRef: toNullableText(r.receipt_ref),
  };
}

export interface NotificationOutboxRepository {
  readonly enqueue: (input: EnqueueInput) => EnqueueResult;
  readonly findById: (id: string) => OutboxRow | null;
  readonly findByDedupKey: (dedupKey: string) => OutboxRow | null;
  readonly claimPending: (limit: number) => readonly OutboxRow[];
  readonly markSent: (id: string, receiptRef: string) => OutboxRow;
  readonly markFailed: (id: string, errorCode: string) => OutboxRow;
  readonly abandon: (id: string, errorCode: string) => OutboxRow;
  readonly countByState: (state: OutboxState) => number;
}

export function createNotificationOutboxRepository(ctx: RepositoryContext): NotificationOutboxRepository {
  const db = ctx.handle.db;

  function requireRow(id: string): OutboxRow {
    const row = findById(id);
    if (row === null) throw new OutboxRowMissingError(id);
    return row;
  }

  function findById(id: string): OutboxRow | null {
    const raw = db.prepare(`SELECT * FROM ${TABLE} WHERE id = ?`).get(id);
    return raw === undefined || raw === null ? null : mapRow(raw);
  }

  function findByDedupKey(dedupKey: string): OutboxRow | null {
    const raw = db.prepare(`SELECT * FROM ${TABLE} WHERE dedup_key = ?`).get(dedupKey);
    return raw === undefined || raw === null ? null : mapRow(raw);
  }

  return {
    /**
     * Insert the intent, or return the one already there. The insert IS the decision: a
     * conflict-ignoring insert followed by a read cannot be raced, whereas checking first and then
     * inserting can be — two callers would both see "absent" and both insert.
     */
    enqueue(input: EnqueueInput): EnqueueResult {
      return withTransaction(db, () => {
        const before = findByDedupKey(input.dedupKey);
        if (before !== null) return { row: before, inserted: false };
        db.prepare(
          `INSERT INTO ${TABLE}
             (id, dedup_key, channel, target_ref, body_ref, cause_ref, state, attempts, enqueued_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, ?)
           ON CONFLICT(dedup_key) DO NOTHING`,
        ).run(
          input.id,
          input.dedupKey,
          input.channel,
          input.targetRef,
          input.bodyRef,
          input.causeRef,
          ctx.now(),
        );
        const after = findByDedupKey(input.dedupKey);
        if (after === null) {
          // The insert reported no error and the row is absent: refuse rather than return a fiction.
          throw new Error('NIZAM outbox: enqueue wrote no row and raised nothing; refusing to report success');
        }
        const inserted = after.id === input.id;
        if (inserted) {
          recordAudit(ctx, {
            action: 'notification_enqueued',
            entityTable: TABLE,
            entityId: after.id,
            detail: `channel,cause_ref,dedup_key for ${input.causeRef}`,
          });
        }
        return { row: after, inserted };
      });
    },

    findById,
    findByDedupKey,

    /** Oldest pending first. The relay's only read path; `limit` bounds a batch. */
    claimPending(limit: number): readonly OutboxRow[] {
      if (!Number.isSafeInteger(limit) || limit < 1) return [];
      return db
        .prepare(`SELECT * FROM ${TABLE} WHERE state = 'pending' ORDER BY enqueued_at, id LIMIT ?`)
        .all(limit)
        .map(mapRow);
    },

    /**
     * Terminal success. Requires a receipt reference, because "sent" without evidence of the send is
     * the claim the schema's own CHECK refuses. A row already sent is returned unchanged, so a
     * duplicated settle is absorbed instead of double-counting an attempt.
     */
    markSent(id: string, receiptRef: string): OutboxRow {
      return withTransaction(db, () => {
        const row = requireRow(id);
        if (row.state === 'sent') return row;
        if (row.state === 'abandoned') throw new OutboxTransitionError(id, row.state, 'sent');
        const at = ctx.now();
        db.prepare(
          `UPDATE ${TABLE}
              SET state = 'sent', sent_at = ?, receipt_ref = ?, attempts = attempts + 1,
                  last_attempt_at = ?, last_error_code = NULL
            WHERE id = ?`,
        ).run(at, receiptRef, at, id);
        recordAudit(ctx, { action: 'notification_sent', entityTable: TABLE, entityId: id, detail: 'state,receipt_ref' });
        return requireRow(id);
      });
    },

    /** Retryable failure. Records the code and the attempt; the row stays claimable. */
    markFailed(id: string, errorCode: string): OutboxRow {
      return withTransaction(db, () => {
        const row = requireRow(id);
        if (row.state === 'sent' || row.state === 'abandoned') {
          throw new OutboxTransitionError(id, row.state, 'failed');
        }
        db.prepare(
          `UPDATE ${TABLE}
              SET state = 'pending', attempts = attempts + 1, last_attempt_at = ?, last_error_code = ?
            WHERE id = ?`,
        ).run(ctx.now(), errorCode, id);
        return requireRow(id);
      });
    },

    /** Terminal failure. Nothing retries an abandoned row, and nothing revives it. */
    abandon(id: string, errorCode: string): OutboxRow {
      return withTransaction(db, () => {
        const row = requireRow(id);
        if (row.state === 'sent') throw new OutboxTransitionError(id, row.state, 'abandoned');
        if (row.state === 'abandoned') return row;
        db.prepare(
          `UPDATE ${TABLE}
              SET state = 'abandoned', attempts = attempts + 1, last_attempt_at = ?, last_error_code = ?
            WHERE id = ?`,
        ).run(ctx.now(), errorCode, id);
        recordAudit(ctx, {
          action: 'notification_abandoned',
          entityTable: TABLE,
          entityId: id,
          detail: 'state,last_error_code',
        });
        return requireRow(id);
      });
    },

    countByState(state: OutboxState): number {
      const raw = db.prepare(`SELECT COUNT(*) AS n FROM ${TABLE} WHERE state = ?`).get(state) as
        | { n: number }
        | undefined;
      return Number(raw?.n ?? 0);
    },
  };
}
