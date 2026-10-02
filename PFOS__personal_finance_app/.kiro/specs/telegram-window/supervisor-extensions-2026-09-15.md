# Supervisor and NIZAM extension trace

Authority: Contract 14 section 10; owner request "Trace supervisor and NIZAM extensions".
Phase TW-A3 partial. Observations 2026-09-15 19:08:30 through 19:11:55 UTC.
Read-only host metadata, safe configuration projections and source inspection, not live tools.

## Supervisor and profile mapping

The source-inspected gateway is the main process of an active system-level systemd service:
LoadState loaded, ActiveState active, SubState running, Type simple, Restart always. Its
parent is systemd/PID 1, it has a service cgroup and an explicit HERMES_HOME. Call this
managed gateway/profile A. The earlier five guessed unit names missed the actual service;
absence of those names was never evidence of absent systemd supervision. Actual unit name,
profile paths and process identifiers remain private and are not copied here.

A second gateway/run process has a shell parent followed by systemd, a user scope, no service
cgroup matched by the probe, and no explicit HERMES_HOME in its initial process environment.
The profile inferred from HOME/.hermes differs from profile A. Call it candidate B; overrides
through CLI/runtime code remain possible, so default-profile inference is not certainty.
No systemd supervision inferred for B. No process stopped or restarted.

Effective managed-service properties queried with systemctl show:
NoNewPrivileges=no, ProtectSystem=no, ProtectHome=no, PrivateTmp=no, DynamicUser=no.
The first four are hardening gaps against proposed service isolation; DynamicUser=no alone
is not a failure because a dedicated static user can be appropriate. Unit fragment has a User
entry, but effective account privilege was not inspected. Fragment lacks EnvironmentFile;
this does not establish absent secrets because dotenv/runtime loading can supply them.
Do not change these properties without an approved compatibility/hardening plan.

## Configured extensions, not proven loaded extensions

Policy projection parsed profile config.yaml through yaml.safe_load. It emitted no tokens,
identity lists, endpoints, filesystem roots, command values, arguments or arbitrary YAML.
Only HERMES_HOME/HOME values were selected internally from process initial environments to
locate profiles; no environment dump. Loaded service fragment was projected to directive
presence, not printed. No plugin/app module imported; standard parser libraries only.

| Observation | Scope and limit |
|---|---|
| Profile A has three command-based MCP definitions | No explicit enabled field in inspected definitions; effective loading/handshake unknown |
| Two MCP definitions reference native NIZAM | String/path-reference classification only, followed by source tracing below |
| Profile A has a Slack platforms entry and no Telegram platforms entry | Environment and loader precedence can enable Telegram; not proof Telegram is off |
| Profile A has toolsets configuration | Actual tool selection and effective permission surface were not output or verified |
| Profile B has no MCP definitions or Telegram/Slack platform entries in inferred file | Overrides/defaults/other processes remain possible |
| Neither inspected profile has a user plugins directory or explicit plugins.enabled list | Not proof no plugins loaded; bundled/platform/entrypoint sources also exist |
| Bounded source-manifest scan found 69 candidates, none native-named or declaring pre_gateway_dispatch | Limited name/declaration search, not exhaustive dynamic registration or entrypoint inventory |

Plugin loader statically scans bundled, user, optionally project, and installed-entrypoint
sources. It applies disabled/enabled rules; certain bundled platform/messaging categories
have special loading behavior. Missing explicit plugin allowlist is NOT equivalent to no
plugins. Did not call discovery, import plugin modules, or inspect in-process hook registry.

## Native MCP trace

The native-named MCP command references an eight-line shell wrapper containing exec and a
Python -m launch. Wrapper fingerprint:
`3b707f718d615eff5807dd849fbd00fea38d9d3ee4c13cb89bc53bdbc8c813da`.
Initial direct-file lookup found no Python argument. Static shell token parsing found the
module name but could not resolve its working directory without expanding runtime variables.
A bounded native-checkout search found ONE matching module source candidate, fingerprint:
`14d34daf865922c58987ea9245a0602d3dea8d2d6bcfa0156b29b05e1cd2209c`.
This is candidate source resolution, NOT proof of runtime PYTHONPATH/cwd/import resolution.

Candidate interfaces and source lines:
- tool_knowledge_search: 87-116, calls hybrid_search and embedding/model helpers.
- tool_knowledge_context: 119-129, calls hybrid_search.
- tool_knowledge_timeline: 132-145, calls hybrid_search and sorts results.
- tool_knowledge_entity: 148-155, calls hybrid_search.
- _handle: 227-255, JSON-RPC dispatch; main: 258-269, input processing.

This supports classification as a configured retrieval integration, not finance execution or
canonical capture. The inspected candidate has privacy markers but no exact native kill/grant/
idempotency/read-back markers; absence of markers is not proof of all imported behavior.
No search, embedding, retrieval, journal, financial tool or provider operation was executed.
Do not use presence of knowledge context as monetary authority or capture-success evidence.

The other native-referencing MCP uses a Node entrypoint. Bounded package inspection reported
version 1.14.0 and entrypoint fingerprint:
`ea8e570bf229a655c994ccc149443906db66a16e7d7cdc7e1bc4ac31a79d4bee`.
It did not match the probe's filesystem-server/read-write markers. Its functional purpose and
native boundary are UNRESOLVED; no filesystem server diagnosis is made. Package/version alone
is not capability evidence. The third MCP was not traced because it was not native-referencing.

## Plan impact and remaining work

1. Reuse the actual managed-service/profile boundary as the candidate integration target;
   do not install a duplicate gateway. Actual bot ownership still needs safe reconciliation.
2. Candidate B must be distinguished before cutover, never killed because it looks redundant.
3. Treat native knowledge MCP as retrieval-only candidate pending source/privacy/runtime checks.
   It does not replace NIZAM governance, a PFOS port, or the canonical capture writer.
4. Resolve wrapper working directory/interpreter/module lookup statically and trace the Node
   bridge before deciding which adapters are required. No shell-variable execution to inspect.
5. Review actual command/tool configuration and native authority before a bounded implementation.
6. Include managed-service hardening compatibility in later owner-authorized deployment scope.
7. Prior GW01-GW11 startup/auth/queue/grant blockers remain. A service health or MCP config entry
   does not establish end-to-end readiness. TW-A3 remains unchecked, with supervisor now resolved
   for A but unique intended-bot ownership and execution authority still unverified.

## Exact commands executed

Each reviewed local temporary script was invoked using the existing strict-host-trust runner.
All seven returned redacted JSON with exit 0. Intermediate empty source resolution was an
inspection limitation, not a missing-implementation conclusion, and was refined without
executing wrappers or changing remote files.

```text
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_supervisor.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_extensions.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_native_mcp.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_mcp_launchers.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_mcp_modules.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_mcp_resolve.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_node_mcp.py
```

No remote writes, application/plugin loading, MCP invocation, secret output, private journal/
ledger reads, Telegram/provider calls, production spend, credentials, human-gate operations,
commit or push. No runtime tests or repository harness rerun in this documentation-only trace.
The previous 19/21 acceptance result remains historical, not a current live verdict.
