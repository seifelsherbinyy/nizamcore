/**
 * Slack transport boundary — interface declarations only.
 * Owning authority: PFOS Contract 14 §11 / Phase 14.3 Stage 1, D-7 Reading A; Contract 12.
 * Mirrors the Telegram role split without importing Telegram identity assumptions.
 * No implementation, network primitive, endpoint, credential value or default exists here.
 */
import type { PortFailureCode } from './errors.ts';

export interface SlackDelivery {
  readonly workspaceRef: string;
  readonly envelopeRef: string;
  readonly eventRef: string;
  readonly userRef: string;
  readonly channelRef: string;
  readonly threadRef: string | null;
  readonly receivedAt: string;
  readonly rawText: string;
}

export interface SlackDedupKey {
  readonly workspaceRef: string;
  readonly envelopeRef: string;
}

export type SlackAcceptDecision =
  | { readonly outcome: 'enqueued'; readonly queuedRef: string }
  | { readonly outcome: 'duplicate' }
  | { readonly outcome: 'rejected' };

export interface SlackInboundPort {
  accept(delivery: SlackDelivery): SlackAcceptDecision;
}

export interface SlackWorkItem extends SlackDelivery {
  readonly queuedRef: string;
  readonly attempt: number;
}

export type SlackWorkOutcome =
  | { readonly outcome: 'done' }
  | { readonly outcome: 'retry'; readonly notBefore: string }
  | { readonly outcome: 'abandoned'; readonly code: PortFailureCode };

export interface SlackWorkerPort {
  process(item: SlackWorkItem): Promise<SlackWorkOutcome>;
}

export interface SlackOutboundMetadata {
  readonly canonicalStateVersion: string;
  readonly receiptRef: string;
}

export interface SlackOutboundMessage {
  readonly channelRef: string;
  readonly threadRef: string | null;
  readonly text: string;
  readonly metadata: SlackOutboundMetadata | null;
}

export interface SlackSendReceipt {
  readonly messageRef: string;
  readonly sentAt: string;
}

export interface SlackOutboundPort {
  send(message: SlackOutboundMessage): Promise<SlackSendReceipt>;
}

export interface SlackPort {
  readonly inbound: SlackInboundPort;
  readonly worker: SlackWorkerPort;
  readonly outbound: SlackOutboundPort;
}

export interface SlackSocketModeConfig {
  readonly workspaceRef: string;
  readonly maxConcurrentWorkItems: number;
}
