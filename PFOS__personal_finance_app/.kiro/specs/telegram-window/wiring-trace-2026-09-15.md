# Gateway wiring trace: read-only findings

Authority: PFOS Contract 14 section 10; scoped owner request to continue gateway tracing.
Phase TW-A3 partial. Observed 2026-09-15 18:59:03 through 19:00:57 UTC.
Source inspection, not executed behavior or live bot readiness. No application imports/runs,
remote writes, provider calls, exposed-token use, private content, service changes or gates.

## Correction to previous inspection

The earlier receipt/design described a container-based gateway without establishing the
relationship. That description is withdrawn. Two gateway/run processes were matched; neither
shared a PID namespace with the currently running Docker containers inspected. One had the
inspected Hermes source in its working directory, the other did not. This does not by itself
identify supervisor, configuration, platform, or intended bot owner. Containers and gateway
processes coexist; do not infer that the containers supervise the gateway. Do not install a
competing systemd service or select a container for cutover without actual ownership evidence.

## Trace of the inspected source

```text
profile config.yaml / dotenv / environment
  -> gateway config platform enablement
  -> Telegram adapter connect
  -> _handle_text_message
  -> _should_process_message
  -> _enqueue_text_event (in-memory batching)
  -> _flush_text_batch -> base.handle_message
  -> background processing -> bound _message_handler
  -> gateway._handle_message
     -> pre_gateway_dispatch plugin hook
     -> ordinary _is_user_authorized check
     -> commands / plugin commands / _handle_message_with_agent
     -> _run_agent -> selected tools and AIAgent
```

Bindings: gateway/run.py lines 4156 and 5816 set adapter message handler to
self._handle_message. Config path helper resolves get_hermes_home()/config.yaml; reload loads
Hermes/project dotenv and YAML. Files containing deployed configuration/secret values were
not read. Actual effective configuration remains unknown.

## Findings, scope and required changes

| ID | Source evidence | Risk/required disposition |
|---|---|---|
| GW01 | gateway/config.py 1214-1220: nonempty TELEGRAM_BOT_TOKEN sets Telegram enabled and assigns token | Token insertion is activation configuration, not harmless secret storage. Block implicit enablement in approved composition. |
| GW02 | telegram.py connect at 1475ff: polling branch calls delete_webhook(drop_pending_updates=False), then start_polling(drop_pending_updates=True) at 1678 | Ordinary connect can mutate webhook state and discard pending updates. Do NOT call/restart to test connectivity. Require explicitly selected, non-destructive transport startup and owner authority. |
| GW03 | Same connect method: webhook startup uses drop_pending_updates=True; then set_my_commands for multiple scopes | Webhook mode is not a safe workaround. Command/menu publication and webhook operations are external changes, separately authorized. |
| GW04 | run.py 6786-6818 calls pre_gateway_dispatch before authorization at 6820ff | A hook sees inbound events before ordinary auth. Put owner/private-chat admission before any plugin/domain processing; no ambient bypass. |
| GW05 | run.py catches hook errors and continues; hermes_cli/plugins.py invoke_hook catches individual callback exceptions and returns remaining results | A governance hook alone is not fail-closed. Missing, failing or malformed governance response must prevent ordinary agent fallback. |
| GW06 | _is_user_authorized 6443ff supports group allowlists, allow-all flags, pairing approvals, global/platform allowlists and wildcard success branches | General Hermes auth is broader than one configured owner/private chat. No evidence these branches are enabled. An outer strict NIZAM gate is required regardless. |
| GW07 | telegram.py _should_process_message 4837ff returns true for non-group input before group allowed-chat logic | TELEGRAM_ALLOWED_CHATS cannot be assumed to restrict private DMs in this path. Explicit sender AND private-chat match required. |
| GW08 | _enqueue_text_event 5038ff, _flush_text_batch 5070ff, run._enqueue_fifo 2580ff use dictionaries/lists/tasks | These inspected queues are not durable acceptance. Recoverable enqueue/offset/effect identity must be established before native Telegram transport is adopted. Other stores may exist; no claim that all persistence is absent. |
| GW09 | run.py _handle_message includes create_subprocess_shell at 7704 and plugin commands; _run_agent constructs AIAgent with selected toolsets | Restrict commands before upstream dispatch; toolset restriction alone cannot fence a direct command-shell branch. Branch presence does not prove actual execution or current authorization. |
| GW10 | run.py has no exact NIZAM_KILL_ALL string reference; prior kill_all marker includes unrelated subprocess cleanup | Withdraw any implication the earlier text marker proved native kill-switch enforcement. It may exist elsewhere; composition must demonstrate it before effects. |
| GW11 | Unauthorized-source branch logs source.user_id and source.user_name | Default diagnostic path is not NIZAM-redacted. Add closed-code logging at actual boundary; do not expose upstream raw exceptions/identifiers. |

Plugin discovery is real: gateway startup calls discover_plugins; manager loads directory or
entrypoint modules and calls registration functions. That proves an extension mechanism,
NOT a deployed NIZAM plugin. Hook lists, active registered tools, MCP endpoints, actual allowed
identities and token validity remain uninspected. No absent direct-import claim is treated as
proof of absent dynamic integration.

## Revised implementation decision

Do not select an unmodified Hermes Telegram gateway or install a second poller. Preferred
candidate remains a governed durable ingress invoking Hermes only through bounded execution
ports, provided current consumer ownership and native contracts are reconciled. Alternative
is a narrowly scoped upstream adapter change with the SAME guarantees, not plugin-only guard.
This is a design candidate, not authorization to edit Hermes or nizamcore.

Required offline acceptance additions before activation:

1. Synthetic token-present startup performs zero webhook/menu/drop operations unless the
   corresponding explicit capability is authorized; absent startup approval is fail-closed.
2. Unknown user/wrong private chat/group/wildcard/pairing/global-allow bypass attempts reach
   neither plugins, parsing with effects, model, command shell nor domain tools.
3. Missing/throwing/invalid pre-dispatch grant handler never falls back to generic AIAgent.
4. Crash between update receipt, batching, durable acceptance and reply retains original
   identity and acknowledged work; prove offset semantics rather than rely on queue names.
5. Kill switch applies to every command/worker/model/domain path. Upstream shell, menus,
   reload/configuration, media and deletion capabilities remain inaccessible in first release.
6. Diagnostic sinks reject real identifiers, token-bearing exceptions and sensitive payloads.

Next read-only reconciliation: map each gateway to its actual supervisor/profile and inspect
registered extension metadata with secret-safe projections; locate exact native contracts
for persistence/privacy/limits. No endpoint, credential or plugin execution is needed for a
source/configuration metadata review. TW-A3 remains unchecked; intended bot ownership unknown.

## Commands executed

Each script reviewed with view before invoking existing strict-host-trust SSH runner. All
five commands exited zero with redacted JSON. No remote script file was created.

```text
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_wiring_index.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_wiring_detail.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_wiring_guards.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_plugin_trace.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_startup_trace.py
```

AST excerpts redact unknown strings/format strings; they are inspection projections, not
runnable patches. Source line numbers refer to on-disk code, not proof of exact modules
already loaded by the process. No runtime tests or repository harness were rerun for this
document-only follow-up. Explicit new-document scans and diff whitespace checks are separate.
