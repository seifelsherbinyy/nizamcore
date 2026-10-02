/**
 * Financial-pillar response assembly for the companion channel.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1), task NIZAM-SLACK-FINANCE-007 track_t.
 * Design: docs/kiro/slack-financial-pillar-response-design.md
 * Evidence: docs/kiro/operational-excellence/slack-finance-evidence.json
 *
 * WHAT THIS IS NOT. No transport is bound: D-B stands at (c) injected ports and mocks, so the
 * transport and the anchor evidence both arrive as ports and the only implementations in the tree are
 * test doubles. Nothing here delivers anywhere.
 *
 * THE INVARIANT THIS FILE EXISTS TO HOLD. There is no monetary field anywhere in FinancialResponse.
 * Contract 14 section 11 forbids monetary amounts crossing this boundary, and the way to hold that is
 * for the field not to exist rather than for a reviewer to notice it. An anchor is a REFERENCE, which
 * section 11 treats differently from an amount: it forbids amounts in one clause and in the next
 * requires financial alerts to carry PFOS provenance. See the brief at
 * docs/kiro/decisions/D-6-contract-14-financial-reference-brief.md, which is unanswered.
 *
 * stateUseReceipt.ts IS NOT IMPORTED and does not exist. Phase 1b design approval is owner-gated and
 * unsigned, so AnchorEvidence below is a local structural shape describing what the port must supply,
 * not a type borrowed from an unauthorised module.
 */
import { pillarQuestion, type Locale } from './dailyMessages.ts';
import { forLocale } from './bidiIsolate.ts';

/** The classes of financial question that can arrive in the channel. */
export type QuestionClass =
  | 'Q1_BALANCE'
  | 'Q2_SPEND'
  | 'Q3_COMMITMENT'
  | 'Q4_FORECAST'
  | 'Q5_PENDING'
  | 'Q6_EXPLAIN_CHANGE'
  | 'Q7_META';

/**
 * Direction and materiality only. This set is closed and enumerated at compile time, which is what
 * makes it impossible for a code to carry a quantity: there is no code that means "a number".
 */
export type QualitativeCode =
  | 'ATTENTION_NEEDED'
  | 'WORSE_THAN_LAST_REVIEW'
  | 'BETTER_THAN_LAST_REVIEW'
  | 'NO_MATERIAL_CHANGE'
  | 'ANCHOR_IS_CURRENT'
  | 'ANCHOR_IS_AGEING';

export type RefusalCode =
  | 'NO_RECEIPT'
  | 'NO_CANONICAL_STATE'
  | 'CANDIDATE_ONLY'
  | 'CLASS_UNANSWERABLE'
  | 'STALE_BEYOND_TOLERANCE';

export type SilenceCode =
  | 'QUIET_HOURS'
  | 'SNOOZED'
  | 'PAUSED'
  | 'ALREADY_SAID_TODAY'
  | 'NOTHING_TO_SAY';

/** What makes a claim checkable. Both parts required: a half anchor is a refusal, not a weak anchor. */
export interface Anchor {
  readonly canonicalStateVersion: string;
  readonly receiptRef: string;
  readonly observedAtMs: number;
}

export type FinancialResponse =
  | {
    readonly kind: 'REFERENCE';
    readonly pillar: 'MAL_PFOS';
    readonly questionClass: QuestionClass;
    readonly anchor: Anchor;
    readonly qualitative: QualitativeCode;
    readonly locale: Locale;
  }
  | { readonly kind: 'REFUSAL'; readonly code: RefusalCode; readonly locale: Locale }
  | { readonly kind: 'SILENCE'; readonly reason: SilenceCode };

/**
 * The shape the anchor port must supply. Deliberately permits every partial state, because the
 * refusal paths exist to name exactly which part was missing rather than to collapse them all into
 * one unavailable.
 */
export interface AnchorEvidence {
  readonly canonicalStateVersion: string | null;
  readonly receiptRef: string | null;
  readonly observedAtMs: number;
  readonly candidateOnly: boolean;
}

export interface ReceiptPort { readonly latest: () => AnchorEvidence | null }
export interface SuppressionPort { readonly state: () => SilenceCode | null }
export interface ClockPort { readonly nowMs: () => number }

export interface AssemblePorts {
  readonly receipt: ReceiptPort;
  readonly suppression: SuppressionPort;
  readonly clock: ClockPort;
}

export interface AssembleInput {
  readonly questionClass: QuestionClass;
  readonly locale: Locale;
  /** True when the owner just asked. A solicited reply is a different surface from a scheduled line. */
  readonly solicited: boolean;
  /** Null means nothing was detected. It never means zero. */
  readonly qualitative: QualitativeCode | null;
}

/**
 * Classes that a reference plus a qualitative code can answer truthfully under the rule AS IT STANDS.
 * Q2 needs a period and a basis that an anchor does not carry; Q4 needs a projection with its
 * uncertainty; Q6 needs the composition of a change. All three are redirects today, and whether any
 * becomes answerable is the subject of the unanswered brief, not of this module.
 */
export const ANSWERABLE_WITH_ANCHOR: readonly QuestionClass[] = ['Q1_BALANCE', 'Q3_COMMITMENT', 'Q5_PENDING'];

/** One day in milliseconds, as an integer. */
export const STALENESS_TOLERANCE_MS = 86_400_000;

/**
 * Assemble one response, or refuse, or stay silent. Never a best-effort answer: section 11 says
 * unavailable PFOS means unavailable, not zero.
 *
 * Check order is deliberate and asserted in tests. Class unanswerability is intrinsic to the question
 * and independent of the anchor, so it is decided first: that way the code an owner sees for
 * "will I make it" does not change depending on whether a receipt happened to exist.
 */
export function assembleFinancialResponse(input: AssembleInput, ports: AssemblePorts): FinancialResponse {
  if (input.locale !== 'en' && input.locale !== 'ar') throw new Error('DAILY_LOCALE_INVALID');

  // Suppression governs the proactive surface only. The owner who just asked is not snoozed.
  if (!input.solicited) {
    const suppressed = ports.suppression.state();
    if (suppressed !== null) return { kind: 'SILENCE', reason: suppressed };
  }

  const meta = input.questionClass === 'Q7_META';
  if (!meta && !ANSWERABLE_WITH_ANCHOR.includes(input.questionClass)) {
    return { kind: 'REFUSAL', code: 'CLASS_UNANSWERABLE', locale: input.locale };
  }

  const evidence = ports.receipt.latest();
  if (evidence === null || evidence.receiptRef === null) {
    return { kind: 'REFUSAL', code: 'NO_RECEIPT', locale: input.locale };
  }
  // A staged candidate is not financial truth, so it cannot anchor a claim even when present.
  if (evidence.candidateOnly) return { kind: 'REFUSAL', code: 'CANDIDATE_ONLY', locale: input.locale };
  if (evidence.canonicalStateVersion === null) {
    return { kind: 'REFUSAL', code: 'NO_CANONICAL_STATE', locale: input.locale };
  }

  const ageMs = ports.clock.nowMs() - evidence.observedAtMs;
  const stale = ageMs > STALENESS_TOLERANCE_MS;

  const anchor: Anchor = {
    canonicalStateVersion: evidence.canonicalStateVersion,
    receiptRef: evidence.receiptRef,
    observedAtMs: evidence.observedAtMs,
  };

  // For a meta question, staleness IS the answer rather than an obstacle to it, so it resolves to a
  // reference carrying an ageing code instead of to a refusal.
  if (meta) {
    return {
      kind: 'REFERENCE',
      pillar: 'MAL_PFOS',
      questionClass: input.questionClass,
      anchor,
      qualitative: stale ? 'ANCHOR_IS_AGEING' : 'ANCHOR_IS_CURRENT',
      locale: input.locale,
    };
  }

  if (stale) return { kind: 'REFUSAL', code: 'STALE_BEYOND_TOLERANCE', locale: input.locale };
  if (input.qualitative === null) return { kind: 'SILENCE', reason: 'NOTHING_TO_SAY' };

  return {
    kind: 'REFERENCE',
    pillar: 'MAL_PFOS',
    questionClass: input.questionClass,
    anchor,
    qualitative: input.qualitative,
    locale: input.locale,
  };
}

/**
 * A second closed bilingual table, held here rather than added to the ten pillar strings. This is the
 * "separate typed structure" the pillar seam requires: the MAL_PFOS string is read unchanged and this
 * line is appended beside it, so no substitution happens inside a pillar string.
 */
const QUALITATIVE_TEXT: Record<QualitativeCode, Record<Locale, string>> = {
  ATTENTION_NEEDED: { en: 'Direction: something needs attention.', ar: 'الاتجاه: هناك ما يحتاج انتباها.' },
  WORSE_THAN_LAST_REVIEW: { en: 'Direction: worse than the last review.', ar: 'الاتجاه: أسوأ من المراجعة السابقة.' },
  BETTER_THAN_LAST_REVIEW: { en: 'Direction: better than the last review.', ar: 'الاتجاه: أفضل من المراجعة السابقة.' },
  NO_MATERIAL_CHANGE: { en: 'Direction: no material change.', ar: 'الاتجاه: لا تغير جوهري.' },
  ANCHOR_IS_CURRENT: { en: 'The authoritative record is current.', ar: 'السجل المعتمد محدث.' },
  ANCHOR_IS_AGEING: { en: 'The authoritative record is ageing. Treat it as out of date.', ar: 'السجل المعتمد قديم. اعتبره غير محدث.' },
};

const REFUSAL_TEXT: Record<RefusalCode, Record<Locale, string>> = {
  NO_RECEIPT: { en: 'No authoritative record is available, so there is nothing to report. This is not zero.', ar: 'لا يوجد سجل معتمد متاح، لذا لا شيء للإبلاغ عنه. هذا ليس صفرا.' },
  NO_CANONICAL_STATE: { en: 'No canonical version exists to anchor an answer, so none is given.', ar: 'لا توجد نسخة معتمدة لتثبيت الإجابة، لذا لن تعطى إجابة.' },
  CANDIDATE_ONLY: { en: 'Only unconfirmed staged entries exist. A staged entry is not a result.', ar: 'توجد مدخلات مبدئية غير مؤكدة فقط. المدخل المبدئي ليس نتيجة.' },
  CLASS_UNANSWERABLE: { en: 'This cannot be answered truthfully here. Open the authoritative finance view.', ar: 'لا يمكن الإجابة على هذا بصدق هنا. افتح العرض المالي المعتمد.' },
  STALE_BEYOND_TOLERANCE: { en: 'The authoritative record is too old to answer from. Refresh it first.', ar: 'السجل المعتمد أقدم من أن يجاب منه. حدثه أولا.' },
};

/**
 * The anchor travels as METADATA, never inside the text.
 *
 * A receiptRef is an identifier, and interpolating an identifier into a pillar string is forbidden.
 * Carrying it structurally satisfies section 11's provenance requirement without putting an
 * identifier in front of a reader, and a test asserts the identifier is absent from the text.
 */
export interface RenderedMessage {
  readonly text: string;
  readonly metadata: { readonly canonicalStateVersion: string; readonly receiptRef: string } | null;
}

/** Null means emit nothing at all. Silence is an output, not a failure to produce one. */
export function renderFinancialResponse(response: FinancialResponse): RenderedMessage | null {
  if (response.kind === 'SILENCE') return null;

  if (response.kind === 'REFUSAL') {
    return { text: forLocale(REFUSAL_TEXT[response.code][response.locale], response.locale), metadata: null };
  }

  const lines = [
    pillarQuestion('MAL_PFOS', response.locale),
    QUALITATIVE_TEXT[response.qualitative][response.locale],
  ];
  return {
    text: forLocale(lines.join('\n'), response.locale),
    metadata: {
      canonicalStateVersion: response.anchor.canonicalStateVersion,
      receiptRef: response.anchor.receiptRef,
    },
  };
}

export type DeliveryOutcome = 'SENT' | 'FAILED' | 'AMBIGUOUS';
export type DeliveryVerdict = 'SENT' | 'UNCERTAIN' | 'SUPPRESSED_ALREADY_ATTEMPTED';

export interface TransportPort { readonly send: (message: RenderedMessage) => Promise<DeliveryOutcome> }

export interface DeliveryJournalPort {
  readonly find: (key: string) => 'UNCERTAIN' | 'SENT' | null;
  readonly markUncertain: (key: string) => void;
  readonly markSent: (key: string) => void;
}

/**
 * Durable intent. NOT exactly-once.
 *
 * D-J is proposed and not taken, and the transport evidence says the unqualified claim would be wrong
 * regardless: standard queues guarantee at-least-once and place duplicate handling on the consumer
 * (claim C006, ASSESSED at S045, a major cloud provider's standard queue service), and where a platform advertises
 * exactly-once it scopes the phrase to a deduplication window or a processing boundary rather than to
 * end-to-end delivery (C007, an explicitly recorded contradiction because the vendors' framings differ).
 *
 * So: mark uncertain BEFORE invoking the outbound port, and never replay a failed or ambiguous send.
 * Section 11 is explicit that this prefers a possibly missed prompt to a duplicate, and that an
 * uncertain receipt is not proof a message was sent. A process that dies between the mark and the send
 * therefore finds an UNCERTAIN marker on restart and declines to send, which is the intended
 * behaviour and not a stuck state: the next tick may reserve a fresh identity.
 */
export async function deliverFinancialResponse(
  key: string,
  message: RenderedMessage,
  ports: { readonly transport: TransportPort; readonly journal: DeliveryJournalPort },
): Promise<DeliveryVerdict> {
  if (ports.journal.find(key) !== null) return 'SUPPRESSED_ALREADY_ATTEMPTED';

  ports.journal.markUncertain(key);

  let outcome: DeliveryOutcome;
  try {
    outcome = await ports.transport.send(message);
  } catch {
    // A throw is indistinguishable from an ambiguous send, so it is treated as one and not retried.
    return 'UNCERTAIN';
  }

  if (outcome === 'SENT') {
    ports.journal.markSent(key);
    return 'SENT';
  }
  return 'UNCERTAIN';
}

export type TickOutcome =
  | 'SILENT'
  | 'DELIVERED_REFERENCE'
  | 'DELIVERED_REFUSAL'
  | 'UNCERTAIN'
  | 'SUPPRESSED_ALREADY_ATTEMPTED';

export interface TickPorts extends AssemblePorts {
  readonly transport: TransportPort;
  readonly journal: DeliveryJournalPort;
}

/**
 * One pass of the financial pillar, as a pure handler over injected ports.
 *
 * THIS IS NOT REGISTERED ANYWHERE, deliberately. The design has it running as a CONSUMER of the
 * existing finance tick, and that registration is the one remaining step: it is withheld because the
 * receipt port has no real implementation, so wiring it into live scheduling would add a delivery path
 * that can only refuse. scheduler.ts is neither imported nor modified here and SCHEDULER_TARGETS is not
 * widened; a test asserts both by reading this file's own text.
 *
 * `deliveryKey` is supplied by the caller rather than derived here. Reserving a local-day and cycle
 * identity needs a calendar and a store, which belong to the scheduler that already does it; deriving a
 * second identity here is how two reservations for the same message come to exist.
 */
export async function financialPillarTick(
  input: AssembleInput & { readonly deliveryKey: string },
  ports: TickPorts,
): Promise<{ readonly outcome: TickOutcome; readonly response: FinancialResponse }> {
  const response = assembleFinancialResponse(input, ports);
  const rendered = renderFinancialResponse(response);

  // Silence reaches the transport not at all. This is the point of silence being an output.
  if (rendered === null) return { outcome: 'SILENT', response };

  const verdict = await deliverFinancialResponse(input.deliveryKey, rendered, ports);
  if (verdict === 'UNCERTAIN') return { outcome: 'UNCERTAIN', response };
  if (verdict === 'SUPPRESSED_ALREADY_ATTEMPTED') return { outcome: 'SUPPRESSED_ALREADY_ATTEMPTED', response };
  return {
    outcome: response.kind === 'REFUSAL' ? 'DELIVERED_REFUSAL' : 'DELIVERED_REFERENCE',
    response,
  };
}
