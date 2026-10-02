# Telegram window scoped VPS inspection

Authority: PFOS Contract 14 section 10; two-agent-vps read-only carve-out.
Phase TW-A3 partial reconciliation. Owner continued after the explicit read-only inspection
request. Observed 2026-09-15 18:42:29 through 18:44:38 UTC. Not live readiness certification.

## Scope and method

Five bounded SSH probes used existing ignored access metadata and key by reference. Strict
existing host-key verification, BatchMode, IdentitiesOnly, no agent forwarding or forwarding,
connection timeout and bounded overall timeout. Remote Python used -B and only standard
library inspection. No application module imported or executed. No remote file written.
No private journal/ledger content, Telegram calls, provider/model spend, credential lifecycle,
service changes, container exec, control-record operation, commit or push.

Docker inspection necessarily reads configuration in memory; only environment NAME presence
was emitted, never values. Process arguments were classified in memory, not printed. Neither
secret files nor process environments were dumped. Source was parsed as AST, never imported.
No raw provider output or real host/container/bot/user identifier is in this receipt.

## Observations and limits

| Observation | Evidence | What it does NOT establish |
|---|---|---|
| SSH access works | All five reviewed probes returned structured output | Permission to mutate the host |
| Host default Node v22.22.1 | node --version in SSH environment | Container Node version or readiness for finance's Node 24 requirement |
| Five anticipated system services not found | systemctl show selected aliases; no related user service found | No runtime exists; Docker discovery found one |
| Three related running containers | Docker name classification, inspect returned running/healthy and zero restart counts | End-to-end bot connectivity; healthcheck semantics were not inspected |
| No recognized Telegram/Slack credential names in container Config.Env | Boolean name-set projection only | Credentials absent; protected files/runtime loading may supply them |
| Gateway processes exist | Two matched processes explicitly carried gateway/run args; broad Hermes pattern also matched another process | Unique consumer for the intended bot; counts alone are not ownership evidence |
| Telegram adapter source present | Read via running-process filesystem view | That platform is configured/enabled or using intended credential |
| Hermes source declares 0.15.2 | Static version extraction from selected running gateway source tree | Package integrity, exact active imported modules or compatible upgrades |
| Native checkout matches historical HEAD; seven dirty entries | Git read with optional locks disabled | Complete code/config/policy snapshot; all local modifications remain protected |
| Native writer/relay interfaces remain present | Seven selected files parsed and hashed | Complete live call graph or durable capture capability |

Native HEAD: `711b7cd111753d53ddf9c610ab021def646650d1`.
Source fingerprints (not deployment identifiers):

| File | SHA-256 |
|---|---|
| gateway/platforms/telegram.py | c8054b03463e50e1eda06d5cafa355896e1cd981fe4f8d8ebabc4568de07fee7 |
| gateway/run.py | 9e3a780cfa36ac8931ad42481a56d4c55d9643efc1f7ec9b595fa886967d0a3f |
| gateway/platforms/base.py | de4b50de9920534ad17abbb22e5bffdd72149c2425eea73462e36c992960a078 |
| NIZAM__system/relay/coordinator.py | 888c329ca79e688079b5be6ce3708e520e88132f6c218e217236ed0fec579018 |
| NIZAM__system/relay/hermes_adapter.py | ff99151deb72f04505547fc7ef469f18ed0f1463ad3b37edbdab13b326dd7d75 |
| NIZAM__system/governor/ledger_writer.py | 8c734e6a0eae841b7586acf583f432ee8dd4a759886124b65afeae20d5f3f8b8 |
| NIZAM__system/governor/journal_persistence.py | 500b9b1dfb8c76fec47a243cb429575fcd1584332ea914d75a24dc1677ef9611 |
| tools/yawmiyat.py | 73686946a41ed88c9297fb8d82e902d03614880932498904d3b0c16dc54a0325 |

Telegram adapter interfaces include connect/disconnect/send, _should_process_message,
_handle_text_message, _build_message_event, callback authorization and polling-conflict
handling. Upstream also exposes exec-approval, media and deletion methods: presence is NOT
authority to expose them through NIZAM. The intended first release must remain narrower.

gateway/run.py contains allowed_users, allowed_chats, kill_all, dedup, sqlite and queue text
markers. Selected gateway/adapter files had no direct ImportFrom references containing nizam,
governor or pfos. These are bounded static observations, not proof of missing integration:
dynamic loading, MCP, subprocess ports, hooks or other files can implement it. Marker presence
is not an executable security test. Native coordinator imports governor and Hermes adapter;
selected journal/ledger interfaces exist but native live capture is still unreconciled.

## Plan corrections

1. Prefer reconciliation of the existing container-based gateway. Do not install the earlier
   systemd template as a second consumer. Map running gateway to its container and configuration
   owner before choosing a single ingress consumer. Current observations do not finish TW-A3.
2. Preserve Hermes 0.15.2 pending compatibility review; no need demonstrated for reinstall.
3. Resolve finance runtime inside its actual execution boundary; do not upgrade host Node just
   because the host default is 22. No container executable was invoked in these probes.
4. Read the actual dispatch/grant hooks and configuration loader next, projecting policy only.
   Determine whether native NIZAM tools are integrated through dynamic/external interfaces.
5. Keep capture unavailable pending native writer/privacy/recovery reconciliation, not merely
   file presence. No canonical financial or journal data was inspected.
6. Credential replacement and live activation remain owner-held. No intended-bot identity,
   webhook state, actual token validity, enabled platform or single-consumer proof obtained.

## Exact inspection commands

All scripts are temporary, reviewed locally with view before execution; contain no credentials.
The commands below were each actually run and exited zero with sanitized JSON output:

```text
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_metadata.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_runtime.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_containers.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_process_sources.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_gateway_ast.py
```

Initial conventional-path/service lookup was insufficient, corrected by bounded container and
home-source inspection rather than declared absence. No runtime tests ran this follow-up.
Prior local 19/21 repository result remains historical for this new documentation increment.

## Subsequent correction: gateway/container relationship

See `wiring-trace-2026-09-15.md`. The container-based-gateway description above was an
unsupported inference and is withdrawn. Neither matched gateway process shared the running
Docker containers' PID namespaces. Supervisor/profile ownership remains unresolved. Earlier
kill_all text-marker presence did not establish NIZAM_KILL_ALL enforcement. Retain raw
observations above as history, not current topology conclusions.
