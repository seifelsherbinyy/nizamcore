/**
 * Stage 1 Slack Socket Mode adapter tests — synthetic doubles only.
 * Owning authority: PFOS Contract 14 §11 / Phase 14.3, D-7 Reading A; Contract 12.
 * No credential, network, host, workspace, channel, user or financial datum appears in these fixtures.
 */
import { describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createSlackSocketModeAdapter, type SlackSocketModeDependencies } from './socketModeAdapter.ts';
import type { SlackDelivery, SlackOutboundMessage, SlackSendReceipt, SlackWorkItem } from '../ports/slack.ts';
import type { DailyControl } from '../hermes/dailyControls.ts';
import { deliverFinancialResponse, type DeliveryJournalPort } from '../hermes/financialResponse.ts';
import { HERMES_TOOL_NAMES } from '../hermes/toolBoundary.ts';

const NOW = 1_800_000_000_000;
const delivery: SlackDelivery = {
  workspaceRef: 'synthetic-workspace', envelopeRef: 'synthetic-envelope', eventRef: 'synthetic-event',
  userRef: 'synthetic-user', channelRef: 'synthetic-channel', threadRef: 'synthetic-thread',
  receivedAt: '2026-01-01T00:00:00Z', rawText: '/finance_status',
};
const work = (rawText: string): SlackWorkItem => ({ ...delivery, rawText, queuedRef: 'synthetic-queued', attempt: 1 });

function harness(over: Partial<SlackSocketModeDependencies> = {}) {
  const admission = { accept: vi.fn(() => ({ outcome: 'enqueued' as const, queuedRef: 'synthetic-queued' })) };
  const controls = {
    apply: vi.fn((_control: DailyControl, _context: { workspaceRef: string; userRef: string; channelRef: string }) => 'applied' as const),
  };
  const sender = {
    send: vi.fn(async (_message: SlackOutboundMessage): Promise<SlackSendReceipt> => ({
      messageRef: 'synthetic-message', sentAt: '2026-01-01T00:00:01Z',
    })),
  };
  const receipt = { latest: vi.fn(() => null) };
  const deps: SlackSocketModeDependencies = {
    config: { workspaceRef: 'synthetic-workspace', maxConcurrentWorkItems: 1 },
    env: { SLACK_BOT_TOKEN: 'synthetic-present', SLACK_APP_TOKEN: 'synthetic-present', SLACK_ALLOWED_USERS: 'synthetic-present' },
    now: () => '2026-01-01T00:00:00Z', capacity: () => 'high', isAllowedUser: () => true,
    admission, controls,
    financial: { receipt, suppression: { state: () => null }, clock: { nowMs: () => NOW } },
    sender,
    ...over,
  };
  return { adapter: createSlackSocketModeAdapter(deps), admission, controls, sender, receipt };
}

describe('presence-only admission', () => {
  it('accepts an authorized delivery through the injected atomic admission once', () => {
    const h = harness();
    expect(h.adapter.inbound.accept(delivery)).toEqual({ outcome: 'enqueued', queuedRef: 'synthetic-queued' });
    expect(h.admission.accept).toHaveBeenCalledOnce();
    expect(h.admission.accept).toHaveBeenCalledWith(
      { workspaceRef: 'synthetic-workspace', envelopeRef: 'synthetic-envelope' }, delivery,
    );
  });

  it('missing credential presence refuses before authorization or admission', () => {
    const allowed = vi.fn(() => true);
    const h = harness({ env: { SLACK_BOT_TOKEN: 'synthetic-present' }, isAllowedUser: allowed });
    expect(h.adapter.inbound.accept(delivery)).toEqual({ outcome: 'rejected' });
    expect(allowed).not.toHaveBeenCalled();
    expect(h.admission.accept).not.toHaveBeenCalled();
  });

  it('unauthorized user refuses before admission', () => {
    const h = harness({ isAllowedUser: () => false });
    expect(h.adapter.inbound.accept(delivery)).toEqual({ outcome: 'rejected' });
    expect(h.admission.accept).not.toHaveBeenCalled();
  });

  it('presence receipts never contain credential values', () => {
    const h = harness();
    expect(h.adapter.credentialPresence).toHaveLength(3);
    expect(JSON.stringify(h.adapter.credentialPresence)).not.toContain('synthetic-present');
  });
});

describe('Q7-only consultation', () => {
  it('missing receipt produces no outbound call', async () => {
    const h = harness();
    expect(await h.adapter.worker.process(work('/finance_status'))).toEqual({ outcome: 'done' });
    expect(h.receipt.latest).toHaveBeenCalledOnce();
    expect(h.sender.send).not.toHaveBeenCalled();
  });

  it('Q7 with a synthetic fresh anchor sends one reference through the injected sender', async () => {
    const h = harness({
      financial: {
        receipt: { latest: () => ({ canonicalStateVersion: 'synthetic-state', receiptRef: 'synthetic-receipt', observedAtMs: NOW, candidateOnly: false }) },
        suppression: { state: () => null }, clock: { nowMs: () => NOW },
      }
    });
    expect(await h.adapter.worker.process(work('are you up to date'))).toEqual({ outcome: 'done' });
    expect(h.sender.send).toHaveBeenCalledOnce();
    const message = h.sender.send.mock.calls[0]?.[0];
    expect(message?.metadata).toEqual({ canonicalStateVersion: 'synthetic-state', receiptRef: 'synthetic-receipt' });
    expect(message?.text).not.toContain('synthetic-receipt');
  });

  it.each(['balance', 'how much did I spend this month', 'what is due', 'forecast', 'is it pending', 'why did it move'])(
    'Q1-Q6 input %s sends nothing in Stage 1', async (text) => {
      const h = harness();
      expect(await h.adapter.worker.process(work(text))).toEqual({ outcome: 'done' });
      expect(h.receipt.latest).not.toHaveBeenCalled();
      expect(h.sender.send).not.toHaveBeenCalled();
    },
  );
});

describe('Slack daily-control binding', () => {
  it.each([
    ['/pause_daily', { kind: 'pause' }],
    ['/skip_today', { kind: 'skip' }],
    ['/snooze 30', { kind: 'snooze', minutes: 30, pillar: null }],
    ['/snooze 45 mal_pfos', { kind: 'snooze', minutes: 45, pillar: 'MAL_PFOS' }],
  ] as const)('binds %s once to the injected control sink', async (text, expected) => {
    const h = harness();
    expect(await h.adapter.worker.process(work(text))).toEqual({ outcome: 'done' });
    expect(h.controls.apply).toHaveBeenCalledOnce();
    expect(h.controls.apply.mock.calls[0]?.[0]).toEqual(expected);
    expect(h.sender.send).not.toHaveBeenCalled();
  });

  it.each(['/resume_daily', '/less', '/more'])('does not widen Stage 1 controls with %s', async (text) => {
    const h = harness();
    expect(await h.adapter.worker.process(work(text))).toEqual({ outcome: 'abandoned', code: 'SLACK_REQUEST_REJECTED' });
    expect(h.controls.apply).not.toHaveBeenCalled();
  });
});

describe('composition invariants', () => {
  it('one work item invokes one Q7 consumer and at most one sender', async () => {
    const h = harness();
    await h.adapter.worker.process(work('/finance_status'));
    expect(h.receipt.latest).toHaveBeenCalledTimes(1);
    expect(h.sender.send).toHaveBeenCalledTimes(0);
  });

  it('ambiguous delivery is never replayed after a reopened journal sees uncertainty', async () => {
    const state = new Map<string, 'UNCERTAIN' | 'SENT'>();
    const journal: DeliveryJournalPort = {
      find: (key) => state.get(key) ?? null,
      markUncertain: (key) => { state.set(key, 'UNCERTAIN'); },
      markSent: (key) => { state.set(key, 'SENT'); },
    };
    const send = vi.fn(async () => 'AMBIGUOUS' as const);
    const message = { text: 'synthetic', metadata: null };
    expect(await deliverFinancialResponse('synthetic-key', message, { transport: { send }, journal })).toBe('UNCERTAIN');
    const reopened: DeliveryJournalPort = { ...journal };
    expect(await deliverFinancialResponse('synthetic-key', message, { transport: { send }, journal: reopened }))
      .toBe('SUPPRESSED_ALREADY_ATTEMPTED');
    expect(send).toHaveBeenCalledOnce();
  });

  it('adds no tool, scheduler, receipt implementation, timer, socket or network primitive', () => {
    expect(HERMES_TOOL_NAMES).toHaveLength(10);
    const source = readFileSync(join('src', 'server', 'slack', 'socketModeAdapter.ts'), 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/.*$/gm, '$1');
    expect(source).not.toMatch(/from\s+['"][^'"]*(?:scheduler|financeAgent|stateUseReceipt|node:http|node:https|node:net|node:tls|@slack)/u);
    expect(source).not.toMatch(/\b(?:WebSocket|fetch|setInterval|setTimeout)\b/u);
  });
});
