# /feedback Telegram Command Specification (E2.5)

**Status:** SPEC. Wire under G4 (live relay).
**Owner:** Coordinator routes; Khaldun synthesizes; Ammar gates.

## Purpose

Give the operator a single, structured channel to correct the system's model of them — without
hand-editing `user.md` or `user_deep.md`. Every `/feedback` is captured verbatim, processed by
Khaldun into a proposed mirroring update, and surfaced for operator approval before any persistent
change to user state lands.

## Syntax

```
/feedback [category] <text>
```

`[category]` (optional, one of):

| Category | Meaning | Routes to |
|----------|---------|-----------|
| `voice` | The system's tone, pacing, or brevity was wrong. | Khaldun → user.md voice |
| `values` | The system arbitrated against the operator's values. | Khaldun → user.md values |
| `focus` | Current focus / rocks were misread or stale. | Khaldun → user.md current_focus |
| `guardrail` | The system violated a topic boundary or messaging cadence. | Ammar → user.md guardrails |
| `agent:<codename>` | A named agent (e.g., `agent:Salman`) misfired. | Hazim → persona-level note |
| `deep` | Self-model correction. Routes to user_deep, never replicated. | Khaldun → user_deep.md |

If `[category]` is omitted, default route is `voice`.

`<text>` is free-form. Up to 1500 chars (Telegram-friendly without splitting).

## Flow

1. Webhook receives the message. `auth` + `dedup` apply as usual.
2. Coordinator parses the command; the body becomes Amin's Artifact A capture.
3. Coordinator routes the capture to Khaldun (kind=annotation) with the parsed category attached.
4. Khaldun:
   - Drafts a proposed diff against `user.md` (or `user_deep.md` for deep items).
   - Writes the proposal to `LEARNING_LEDGER` with `kind=mirroring_proposal`.
   - Replies to the operator with a 5-line summary of the proposed change + the C1/C2 checkpoint
     prompt.
5. Operator:
   - `/go <trace_id>` — Khaldun applies the diff (under Ammar's pre-write gate). EVENT_LEDGER
     records `kind=mirroring_applied`.
   - `/halt <trace_id>` — Proposal is filed as `kind=mirroring_rejected` in LEARNING_LEDGER for
     trend analysis (E2.8).
6. If the change touches `user_deep.md`, the C2 "privacy escalation" checkpoint always fires,
   even when the operator has otherwise auto-approved this category.

## What Khaldun is NOT allowed to do

- Edit any file other than `user.md` / `user_deep.md` based on a `/feedback`.
- Apply a change without the operator's explicit reply per turn.
- Carry context from one `/feedback` trace into another without the operator's permission
  (E2.8 anti-drift relies on independent traces).

## Examples

```
/feedback voice The bullets felt clinical. I want a slower opener when SUKOON is yellow.
/feedback values You weighted output speed over honesty in yesterday's brainstorm. Reverse it.
/feedback agent:Hazim He was too sharp on the housing decision. Soften the tone but keep the rigor.
/feedback deep I noticed I freeze when three meetings stack. Update stress_responses.
```

## Cost & rate

- Each `/feedback` is a single short LLM call (Khaldun). Budget: ≤ $0.02 per turn (deepseek-flash).
- Rate limit: ≤ 6 `/feedback` per day. Coordinator emits a polite `slow down — sleep on it` reply
  after the 6th.

## Acceptance

Spec is complete (this document) — coordinator implementation lands under T1/G4.
