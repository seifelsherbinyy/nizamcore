/**
 * Injected Slack Socket Mode adapter — no socket, SDK, endpoint or credential ownership.
 * Owning authority: PFOS Contract 14 §11 / Phase 14.3 Stage 1, D-7 Reading A; Contract 12.
 * Depends on interface-only Slack ports, secretBroker presence checks, exact daily controls,
 * and the Q7-only financial consultation seam. Every outside effect is injected.
 */
import type { Capacity } from '../hermes/dailyPolicy.ts';
import { routeDailyText, type DailyControl } from '../hermes/dailyControls.ts';
import {
  routeSlackFinancialConsultation,
  type SlackFinancialConsultationInput,
} from '../hermes/ingressRouter.ts';
import {
  renderFinancialResponse,
  type AssemblePorts,
  type FinancialResponse,
  type QuestionClass,
} from '../hermes/financialResponse.ts';
import {
  inspectSecretAlias,
  type SecretBrokerResult,
} from '../hermes/secretBroker.ts';
import type {
  SlackAcceptDecision,
  SlackDedupKey,
  SlackDelivery,
  SlackOutboundMessage,
  SlackPort,
  SlackSendReceipt,
  SlackSocketModeConfig,
  SlackWorkItem,
  SlackWorkOutcome,
} from '../ports/slack.ts';

export interface SlackAdmissionPort {
  /** Atomically deduplicate and enqueue. The adapter never performs a preceding read. */
  readonly accept: (key: SlackDedupKey, delivery: SlackDelivery) => SlackAcceptDecision;
}

export interface SlackControlSink {
  readonly apply: (
    control: DailyControl,
    context: { readonly workspaceRef: string; readonly userRef: string; readonly channelRef: string },
  ) => 'applied' | 'blocked' | 'conflict' | 'failed';
}

export interface SlackMessageSender {
  readonly send: (message: SlackOutboundMessage) => Promise<SlackSendReceipt>;
}

export interface SlackSocketModeDependencies {
  readonly config: SlackSocketModeConfig;
  /** Injected for presence checks only. The adapter never returns or logs any value. */
  readonly env: Readonly<Record<string, string | undefined>>;
  readonly now: () => string;
  readonly capacity: () => Capacity;
  readonly isAllowedUser: (userRef: string) => boolean;
  readonly admission: SlackAdmissionPort;
  readonly controls: SlackControlSink;
  readonly financial: AssemblePorts;
  readonly sender: SlackMessageSender;
}

export interface SlackSocketModeAdapter extends SlackPort {
  /** Presence records only, exposed for value-blind readiness reporting. */
  readonly credentialPresence: readonly SecretBrokerResult[];
}

const REQUIRED_ALIASES = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_ALLOWED_USERS'] as const;
const Q7_TEXT = new Set(['/finance_status', 'are you up to date']);

function questionClass(text: string): QuestionClass | null {
  const body = text.trim().toLowerCase();
  if (Q7_TEXT.has(body)) return 'Q7_META';
  if (/\b(balance|where am i)\b/u.test(body)) return 'Q1_BALANCE';
  if (/\b(spend|spent|this month)\b/u.test(body)) return 'Q2_SPEND';
  if (/\b(due|commitment|obligation)\b/u.test(body)) return 'Q3_COMMITMENT';
  if (/\b(forecast|will i make it)\b/u.test(body)) return 'Q4_FORECAST';
  if (/\b(pending|did that land)\b/u.test(body)) return 'Q5_PENDING';
  if (/\b(why|explain).*(change|move)|\b(change|move).*(why|explain)\b/u.test(body)) return 'Q6_EXPLAIN_CHANGE';
  return null;
}

function controlAllowed(control: DailyControl): boolean {
  return control.kind === 'pause' || control.kind === 'skip' || control.kind === 'snooze';
}

export function createSlackSocketModeAdapter(deps: SlackSocketModeDependencies): SlackSocketModeAdapter {
  const credentialPresence = Object.freeze(
    REQUIRED_ALIASES.map((alias) => inspectSecretAlias(alias, deps.env, 'slack-socket-mode', deps.now)),
  );
  const configured = credentialPresence.every((result) => result.configured);

  const outbound = {
    send(message: SlackOutboundMessage): Promise<SlackSendReceipt> {
      return deps.sender.send(message);
    },
  };

  return Object.freeze({
    credentialPresence,
    inbound: {
      accept(delivery: SlackDelivery): SlackAcceptDecision {
        if (!configured) return { outcome: 'rejected' };
        if (delivery.workspaceRef !== deps.config.workspaceRef) return { outcome: 'rejected' };
        if (!deps.isAllowedUser(delivery.userRef)) return { outcome: 'rejected' };
        return deps.admission.accept(
          { workspaceRef: delivery.workspaceRef, envelopeRef: delivery.envelopeRef },
          delivery,
        );
      },
    },
    worker: {
      async process(item: SlackWorkItem): Promise<SlackWorkOutcome> {
        if (!configured || item.workspaceRef !== deps.config.workspaceRef || !deps.isAllowedUser(item.userRef)) {
          return { outcome: 'abandoned', code: 'SLACK_REQUEST_REJECTED' };
        }

        const daily = routeDailyText(item.rawText, deps.capacity());
        if (daily.kind === 'control' && controlAllowed(daily.control)) {
          const outcome = deps.controls.apply(daily.control, {
            workspaceRef: item.workspaceRef,
            userRef: item.userRef,
            channelRef: item.channelRef,
          });
          return outcome === 'applied'
            ? { outcome: 'done' }
            : { outcome: 'abandoned', code: 'SLACK_REQUEST_REJECTED' };
        }

        const classification = questionClass(item.rawText);
        if (classification === null) return { outcome: 'abandoned', code: 'SLACK_REQUEST_REJECTED' };
        const consult: SlackFinancialConsultationInput = {
          questionClass: classification,
          locale: 'en',
          qualitative: null,
        };
        const response: FinancialResponse = routeSlackFinancialConsultation(consult, deps.financial);
        // Stage 1 has no real receipt. A typed refusal is available to the caller for status/UI handling,
        // but it is not emitted proactively into Slack; missing receipt therefore means zero outbound calls.
        if (response.kind !== 'REFERENCE') return { outcome: 'done' };
        const rendered = renderFinancialResponse(response);
        if (rendered === null) return { outcome: 'done' };
        await outbound.send({
          channelRef: item.channelRef,
          threadRef: item.threadRef,
          text: rendered.text,
          metadata: rendered.metadata,
        });
        return { outcome: 'done' };
      },
    },
    outbound,
  });
}
