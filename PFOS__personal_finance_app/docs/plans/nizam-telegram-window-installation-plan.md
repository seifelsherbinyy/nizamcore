# NIZAM Telegram window installation handoff

Date: 2026-09-15. Authority: PFOS Contract 14 section 10. Phase TW0.
Status: preparation only; no restored runtime or live activation.
Specification: `.kiro/specs/telegram-window/{requirements,design,tasks}.md`.
Evidence: `.kiro/specs/telegram-window/verification.md`.

## Deliverables and dependencies

| Stage | Deliverable | Depends on | Exit evidence |
|---|---|---|---|
| M0 | Contract/spec/handoff | Local research | Document checks; no runtime claim |
| A3 | Current native interface/service inventory | Authorized scoped read | Redacted snapshot and single consumer selected |
| A4/A5 | Authority and private handoff | A3; owner decisions | Privacy/limits/capabilities and protected references |
| M1 | Synthetic guarded conversation | A3/A4/A5; B1-B3/B6 | Positive/negative/replay/recovery tests |
| M2 | Private planning/status/new/cancel pilot | M1; explicit live authority | Actual bounded multi-turn execution and restart |
| M3 | Supported PFOS reads | B4/T07; authoritative source | Exact sourced facts/version/freshness |
| M4 | Capture/continue | Native B5/T08 | Read-back/restart/retry yield one canonical record |
| M5 | Operational handoff | Applicable pilots/recovery | Current capability evidence and owner acceptance |

Life remains native Python, finance Node 24. Existing supported Hermes is reused, not blindly
upgraded. One Telegram private text conversation, not Mini App, voice or financial writes.
Telegram is not end-to-end encrypted or canonical storage. Capture is separately blocked
until the native writer/privacy/recovery boundary is reconciled.

## Secret handoff, logical references only

| Reference | Purpose | Live prerequisite |
|---|---|---|
| `<PRIMARY_TELEGRAM_BOT>` | Intended identity | Scoped match against private operator record |
| `<TELEGRAM_BOT_TOKEN>` | Transport credential | Protected replacement, not chat-exposed token |
| `<ALLOWED_TELEGRAM_USER_ID>` | Owner sender | Strict allowlist; never confused with bot ID |
| `<ALLOWED_PRIVATE_CHAT_ID>` | Approved private chat | Check both sender and chat context |
| `<PROTECTED_ENV_PATH>` | Credential source | Outside Git/Drive; restricted host ownership/access |

These are not asserted installed-Hermes env names. Map after version inspection. Owner
replaces the exposed token and stores replacement securely outside chat; no token operation
is delegated here. Message deletion is not proof of revocation. No actual secret, bot
username, host/account/identifier/webhook path enters this tree. No credentials in argv,
logs, replies, prompts, browser assets or Drive. Existing model caps remain separately governed.

## Bounded read-only inspection request

Name target by protected reference, metadata-only scope, time bound, excluded private content
and redacted output. Inspect installed Hermes version, native snapshot/dirty metadata,
service manager, consumer/mode/queue owner, supported hooks, credential presence/permissions.
No application imports/execution, environment dumps, token-bearing process arguments,
journal/ledger bodies, raw provider output or arbitrary logs.

Authorized safe getMe/getWebhookInfo reads can report bot match and webhook state only.
Empty webhook does not prove no poller. Do not use getUpdates for diagnosis or enrolment:
it can interfere with the current consumer. Establish owner identity through approved private
enrolment after consumer ownership is known. Provider reads never complete human gates.

## Installation package, after integration selection

1. Choose exactly one existing service manager and consumer, no parallel token use.
2. Produce version-compatible placeholder templates after native hook reconciliation.
3. Plan unprivileged identity, compatible filesystem hardening, minimal writable paths,
   restricted environment loading and bounded restart behavior. No host mutation in M0/M1.
4. Demonstrate general Hermes tools cannot inspect token-bearing environment. Environment
   variables alone are not isolation; separate transport using supported ports or block release.
5. Resolve finite execution limits and queue/session/capture retention under native contracts.
6. Rehearse compatible binary/config/schema recovery without discarding queue/results.
7. Present bounded live authorization request: target/service by private reference, permitted
   changes, messages/model budget, observation duration, rollback scope and prohibited actions.

No implicit webhook removal/registration, service stopping, public ports, queue clearing,
update dropping, credential creation, Drive-scope expansion or production model spending.
No fixed delivery date before current native reconciliation determines the actual change.

## Human boundary

Never execute, test, substitute values into, populate or mark complete
`ops/GATE_REGISTER.md` or `ops/DEPLOYMENT_CONTROL.md`. G1-G8 remain human-controlled.
Host mutation, Telegram sends, production spend, native changes, commit and push each require
explicit applicable authority. Generic continuation or green local checks are not live approval.

## Acceptance and rollback

Authorized synthetic pilot: owner round trip, actual bounded planning, non-owner refusal,
secret-safe output, profile caps, restart queue recovery and honest unavailable capabilities.
Live unauthorized-sender testing needs an approved test identity, never broader allowlists.
Offline negatives do not substitute for live observation. PFOS facts cite source/version;
capture requires raw canonical persistence plus read-back, not event metadata alone.
Persist effects/results before reply retry; ambiguous sends remain uncertain.

Rollback under separate authority: halt intake/fence workers, preserve queue/results,
reconcile uncertain effects, restore compatible binary/config, reclaim original identities,
recheck readiness. No blind database restore/schema downgrade/offset rewind, update deletion,
automatic Slack fallback or credential rotation as cleanup.

## Outstanding decisions and blockers

- Owner-managed protected replacement credential: blocks live validation/activation.
- Current scoped native inspection: blocks integration selection, not documentation.
- Explicit restoration/cutover review: Slack-v2 remains live policy; checks unchanged.
- Private identity/privacy/retention/limit reconciliation: blocks real-message processing.
- Historical metadata-only capture: native writer review blocks capture, not limited planning.
- Scoped host/send/spend/native-change authority: blocks live execution.
- Existing user edits: preserve; owner handles disposition separately, no unauthorized cleanup.

Detailed task/test dependencies are maintained once in `tasks.md`. Runtime tasks stay unchecked.
