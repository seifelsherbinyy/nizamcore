# Telegram window design

Authority: PFOS Contract 14 section 10; Contracts 06/12/13 and invariant steering.
Phase TW0: design only. Requirements TW01-TW15 in `requirements.md`.

## 1. Inspected baseline, 2026-09-15

- `src/server/hermes/ingressPolicy.ts` and `gatewayWiring.ts`: Slack-v2 aliases/audits.
- `ops/hermes/nizam-ingress.*.example`: Slack templates; do not relabel in place.
- `src/server/telegram/operatorMessagePort.ts`: existing accept/dedup/queue composition.
- `src/server/telegram/liveTransport.ts`: injected client and mode-specific guards.
- `src/server/process/singleWindowFlow.ts`: offline rehearsal; some read routes return route
  descriptions. Journal append precedes reply, so production reuse needs a native stable-key
  write/result replay guarantee, not queue dedup alone.
- `.kiro/specs/agentic-profile-baseline/verification.md`: historical 2026-09-11 native source
  inspection reported metadata-only live-ingress persistence, not raw capture. No current
  service diagnosis is inferred. This increment has not inspected private data or the host.
- Node 24 finance runtime; native Python life runtime. No second money implementation.

## 2. Integration decision (TW01-TW07)

Private Telegram -> one selected consumer -> validated authentication metadata -> durable
queue -> native NIZAM governance -> bounded Hermes or PFOS read -> recorded execution result
-> tracked reply. Capture is a separate native authorized writer capability.

TW-A3 must select exactly one consumer:

1. Existing governed native relay retains transport ownership and invokes bounded tools.
2. Installed Hermes gateway owns transport only if the inspected version exposes hooks that
   preserve authentication, durable acceptance, native grants and retry-safe effects.
3. If neither satisfies these boundaries, report BLOCKED_DEPENDENCY and review a bounded
   adapter. Do not start the finance poller as a competing general gateway.

Preserve an appropriate current mode. Long polling is preferred only when ownership is clear
and no suitable existing mode needs preserving. No automatic webhook deletion, mode switching,
update dropping or dual consumption. Local config cannot prove fleet-wide single ownership;
current scoped process/provider evidence is also necessary. Empty webhook is insufficient.

Derive sender/chat from validated provider envelope, never message text or a caller-asserted
boolean. Apply byte limits before parsing, validate minimum authentication metadata, then parse
business content. Place TW02 at the actual ingress, not an unused helper. Unsupported edits,
attachments, voice, callback actions, groups and bot input are refused in the initial release.

## 3. Reliable state (TW05-TW09, TW13)

Execution states: queued, running, blocked, cancelled, failed, effect_uncertain, result_recorded.
Delivery states: not_prepared, pending, sending, delivered, send_uncertain, failed.

Durable provider identity is `(bot namespace, update ID)`. Derive operation identity from it
and the governed operation, not a fresh random ID on retry. Persist payload digest; same key
plus different content conflicts. Canonical writer honors identity independently of queue
dedup. No raw content/token/real identity in diagnostic correlation output.

Reuse queue/lease code where it satisfies the contract. Inspect database migration authority
before adding result/outbound persistence. Native writer's idempotency/read-back interface
provides cross-process recovery; do not invent a distributed transaction. A stale worker must
be fenced at the effect boundary, not only prevented from marking queue completion.

Record/recover results before preparing replies. Reply retry reuses the result. If provider
accepts a send but local acknowledgement is lost, retain send_uncertain. No exactly-once
Telegram-send guarantee. Persist per-chunk progress; avoid blindly resending prior chunks.
Capture conflict/uncertainty requires reconciliation rather than a success message.

Resolve finite input/context/attempt/lease/timeout/queue-age limits under TW-A4 before B1.
Do not invent numeric production thresholds in this document. Cancellation uses a bounded
control path that does not queue behind the very turn it must cancel.

## 4. Commands and ports (TW07-TW11)

| Command | Defined behavior | Milestone |
|---|---|---|
| /help | Actually enabled capabilities and privacy limits | M2 |
| /status | Redacted capability readiness, no host/secret/store details | M2 |
| /plan | Bounded planning, not external action approval | M2 |
| /new | New context generation without erasing saved records | M2 |
| /cancel | Pending cancellation or running request; no implied undo | M2 |
| /finance | Allowlisted versioned PFOS read | M3 |
| /capture | Native stable-key persistence plus read-back | M4 |
| /continue | Owner/profile-scoped persisted reference | M4 |

Deterministic-first natural language routing: test English/Arabic, mixed money/narrative,
unknown commands, injection and ambiguity. Text cannot expand grants. Keep financial facts
on a deterministic rendering path; LLM narrative cannot invent/alter amounts. Unavailable
is not zero or an estimate. Ingress never opens finance.db. Life/finance keys/caps/stores
stay separate; signal bus is bounded state, not a monetary information bridge.

Select native writer only after fresh writer/privacy/recovery reconciliation and separate
native write authority. Scheduled importer usage alone does not select the canonical live
capture writer. No second journal writer is implemented in this finance repository.

## 5. Secrets, privacy, retention (TW04, TW12)

Logical references: `<PRIMARY_TELEGRAM_BOT>`, `<TELEGRAM_BOT_TOKEN>`,
`<ALLOWED_TELEGRAM_USER_ID>`, `<ALLOWED_PRIVATE_CHAT_ID>`, `<PROTECTED_ENV_PATH>`.
Map to supported installed-version env names after inspection. Never copy exposed token or
real bot identity into this tree. Owner supplies protected replacement outside chat; this
workflow neither rotates credentials nor consumes the exposed one.

Host holding: root-owned mode-600 environment file outside Git/Drive, loaded through the
service manager; local holding uses restrictive platform ACLs. No secret in argv, tracing,
HTTP errors, crash dumps, prompts or reports. Environment variables are NOT isolated from
other tools in the same process. If general Hermes tools can inspect the token-bearing
environment, isolate transport through supported ports or block activation. Diagnostic
handling translates errors to closed codes before any sink.

Telegram is cloud ingress, not end-to-end encryption. Warn at interface and gate downstream
egress; the server cannot retroactively make a message already sent to Telegram local-only.
Queue bodies, conversation context, diagnostic metadata and canonical captures have distinct
contract-derived retention. Unresolved retention blocks real-message processing. No invented
purge or backup schedule. Drive remains encrypted data under `drive.file`, never keys. M2
requires no new Drive integration.

## 6. Installation and recovery (TW03-TW04, TW14-TW15)

Handoff: `docs/plans/nizam-telegram-window-installation-plan.md`. No executable deployment
script before integration selection. Later scoped inspection excludes application imports,
private data, environment dumps and getUpdates diagnostics. Authorized getMe/getWebhookInfo
reads produce sanitized match/status only; they do not complete a human gate.

Preserve a supported compatible installed Hermes version, no blind upgrade. Use one service
manager, unprivileged identity, bounded writable paths and compatible hardening under separate
host authorization. Inspect schema/binary compatibility and queue recovery before cutover.
No simultaneous ingress or automatic Slack fallback.

Rollback: halt intake/fence workers, preserve queue/results, reconcile uncertain effects,
restore compatible known-good binary/config under authorization. No blind schema downgrade,
DB restore, offset rewind, update deletion or credential rotation as cleanup. Do not execute,
test or modify either human control record or G1-G8.

## 7. Test/readiness model

Injected clocks, identities, ports and synthetic stores only. Existing acceptance checks
unchanged; any policy/check conflict stops for explicit review. Tests listed in `tasks.md`.
Each observation has environment, code/config/policy snapshot, UTC time, method, test IDs and
outcomes. Unknown thresholds/snapshots remain unknown; historical/offline success never
establishes live readiness. No runtime certification from M0 document review. Server/routing/
benchmark code remains excluded from browser bundle.

## 8. Current inspection delta (2026-09-15)

See `inspection-2026-09-15.md`: SSH read-only access succeeded; container-based runtime and
Hermes 0.15.2 source with Telegram adapter observed. Anticipated systemd services absent.
Prior default systemd-install assumption is rejected: reconcile existing container gateway
before any new service. Host Node 22 is not container-runtime evidence. Single bot-consumer
ownership, enabled platform, native grants/tool wiring and capture remain unverified.

## 9. Wiring trace supersedes topology assumption

`wiring-trace-2026-09-15.md` withdraws section 8's container-gateway inference: inspected
gateway processes did not match the running Docker container PID namespaces. Reconcile actual
supervisor/profile before choosing service manager. No new service or poller now.

Unmodified token-present startup can enable Telegram, mutate webhook state, drop pending
updates and publish menus. Never restart it as a read-only test. Existing pre_gateway_dispatch
runs before normal auth and fails open on callback errors; plugin-only governance is inadequate.
Place strict owner/private-chat admission and durable intake before any plugin/command path,
and require explicit fail-closed execution grants. Restrict direct shell commands as well as
tools. Current pending-message dictionaries/tasks do not establish durable enqueue. Kill-all
substring evidence is not native NIZAM_KILL_ALL enforcement. GW01-GW11 remain design blockers.

## 10. Supervisor and extension reconciliation

See `supervisor-extensions-2026-09-15.md`. Source-inspected gateway is an actual system-level
systemd service with explicit profile A; previous guessed service names were insufficient.
Second gateway-shaped process is shell/user-scope with inferred profile B, not proved duplicate.
Profile A configures three MCP servers. Native-named module candidate provides knowledge
retrieval, not a proven governor/finance/capture bridge. Another native-referencing Node bridge
remains unresolved. Effective NoNewPrivileges/ProtectSystem/ProtectHome/PrivateTmp are off;
review compatible hardening under later host authority. Bot ownership/tool execution remain
unverified; no new service, plugin-only guard, or blind token insertion is justified.

## 11. MCP bridge selection delta

See `remaining-bridges-2026-09-15.md`. Node bridge is Camofox browser automation with evaluate/
cookie-import and interaction tools, not finance/capture. Native knowledge launcher resolves
statically through literal PYTHONPATH and existing interpreter. Third bridge is a container
exec wrapper whose expected script was not found in the bounded process-root inspection.
No bridge executed. Use actual nested MCP tools.include/exclude and platform_toolsets keys;
empty include does not deny all, top-level toolsets does not establish gateway restrictions,
and default MCP inclusion must be explicitly fenced. First-release browser grants stay absent.

## 12. Missing-script hypothesis resolved

`container-script-resolution-2026-09-15.md` supersedes section 11's target/source mismatch.
The exact container script exists; host process-root stat was EACCES. Docker archive read
proved file presence and valid Python syntax. It provides WHOOP health interfaces, not PFOS
or capture. Fixed local probes classify inaccessible separately from missing. No deployment
repair or permission relaxation warranted. Live tool execution remains unverified.
