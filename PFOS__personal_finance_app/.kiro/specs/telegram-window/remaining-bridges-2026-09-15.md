# Remaining MCP bridge trace

Authority: PFOS Contract 14 section 10; owner request to trace remaining MCP bridges.
Phase TW-A3 partial. Observed 2026-09-15 19:56:20 through 20:00:09 UTC.
Read-only metadata/source/configuration projections. No MCP handshake, tool call, application
import/execution, credential use for Telegram, provider call, remote mutation or human gate.

## Results

| Bridge alias | Established from static evidence | Limits |
|---|---|---|
| mcp_1 | Shell wrapper uses docker exec with Python and a server-script argument; target container running | Configured script not found through current process-root view at the expected path; bounded source search also found zero candidates. Actual launch/functionality unverified. |
| mcp_2 | Camofox browser MCP bridge, version previously reported 1.14.0; stdio tool list/call handlers delegate to TOOL_DEFS/runTool and browser backend | No browser/backend contacted. Not PFOS, journal or governor. Actual advertised/live tool list unknown. |
| mcp_3 | Wrapper sets literal absolute PYTHONPATH; existing absolute interpreter; module path resolves to previously inspected native knowledge source | Static resolution now established, not runtime import/handshake or retrieval/privacy proof. |

mcp_1 discovery did NOT execute docker exec. Only docker inspect and filesystem metadata/read
through the running container process root were used. The not-found result is bounded to that
view/search; permission, target drift or another deployment layout need reconciliation. Do not
run the launcher to diagnose it, infer it works from container health, or repair a guessed path.

mcp_2 entrypoint fingerprint:
`ea8e570bf229a655c994ccc149443906db66a16e7d7cdc7e1bc4ac31a79d4bee`.
Its actual relative imports resolve to config.mjs and tool-contracts.mjs in their referenced
location, not initially guessed sibling files. Tool-contract fingerprint:
`3177875a9e41eeec147980d45dcc630b00ba5c1e5cd39ca1866ddbd9034f5d5a`.
Declared tools: camofox_create_tab, camofox_list_tabs, camofox_close_tab, camofox_navigate,
camofox_click, camofox_type, camofox_scroll, camofox_snapshot, camofox_screenshot,
camofox_evaluate, camofox_import_cookies. These include consequential browser actions and
session-sensitive operations; they are not approved for the initial Telegram conversation.
No real backend URL, user/session key, cookies or other private value was emitted or used.
No claim of absent upstream safety controls from mere text-marker absence.

mcp_3 wrapper fingerprint:
`3b707f718d615eff5807dd849fbd00fea38d9d3ee4c13cb89bc53bdbc8c813da`.
Literal PYTHONPATH resolves module source fingerprint:
`14d34daf865922c58987ea9245a0602d3dea8d2d6bcfa0156b29b05e1cd2209c`.
This closes the prior static launcher ambiguity without evaluating shell expressions. Source
contains knowledge search/context/timeline/entity interfaces, not a demonstrated canonical
capture writer or deterministic finance adapter. Dependencies/runtime behavior still untested.

## Actual filtering and model exposure path

Inspected tools/mcp_tool.py `_register_server_tools` (3177ff) reads nested
`mcp_servers.<alias>.tools.include` and `.tools.exclude`. Earlier probes checked guessed flat
keys; those projections were insufficient and are superseded by the actual nested-key read.
All three inspected definitions lack nested include/exclude lists.

Static registration behavior: a nonempty normalized include set wins; otherwise a nonempty
exclude set removes named tools; otherwise every advertised tool passes that filter. Empty
include is therefore NOT deny-all. Utility resources/prompts have a separate registration
path and need independent review. Registration is not proof of a running server or model use.

`hermes_cli/tools_config.py::_get_platform_tools` (1116ff) reads `platform_toolsets` and
platform defaults. In inspected profile YAML, top-level toolsets exists, platform_toolsets
does not, and agent.disabled_toolsets is not populated. A top-level toolsets entry is NOT
proof of gateway restrictions. The selector's default-MCP path adds enabled configured MCP
servers absent a specific selection/opt-out. Missing server enabled field defaults to enabled
in this selector. Actual loaded registry and final model tools were not invoked or inspected.

`_make_tool_handler` calls the MCP session through a lock/timeout and has auth/session-error
recovery retry paths. No tool execution was performed. Retry-safe domain effects must be
proven at the governed port; generic MCP retry is not canonical idempotency evidence.

## Implementation implications

- Keep browser actions, evaluation and cookie import out of first-release Telegram grants.
- Define platform-specific selection using inspected supported keys; never use empty include
  as deny-all or assume top-level toolsets filters gateway tools.
- Test nested include/exclude precedence, server disabling, default MCP inclusion, utility
  schemas, command bypasses and plugin fallback with deterministic mocks before activation.
- Treat knowledge MCP solely as attributed retrieval until native privacy and context egress
  are reconciled. Financial facts remain PFOS-only; capture remains unavailable.
- Resolve container-wrapper target/source mismatch before including that bridge in any pilot.
- Full TW-A3 remains incomplete: unique intended-bot ownership, registry/readiness, native
  authority and fail-closed dispatch still need reconciliation. Prior GW01-GW11 remain open.

## Commands and execution failures

Reviewed temporary scripts invoked with existing strict-host-trust runner; no inline secrets.
Nine successful read-only probe invocations (each exit zero with redacted output):

```text
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_bridge_identity.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_bridge_contracts.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_bridge_filters.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_last_bridge.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_selector_inline.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_inline_verified.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_wrapper_shape.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_container_bridge.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_container_source.py
```

An initial remote_bridge_contracts invocation returned HOST_READ_FAILED/exit 1: a local edit
inserted literal backslash-n instead of newline. Corrected and syntax-checked before successful
retry; no application execution occurred. One local probe construction failed compile with
IndentationError before file creation/SSH. A later insertion anchor missed its target, so the
selector-only probe did not inspect inline code as intended. Read-back revealed this; asserted
anchor and corrected probe established that the wrapper uses neither -m nor -c. Docker wrapper
classification then replaced those rejected hypotheses. No failed check was hidden as success.

Local changes are documentation only. No repository runtime code, acceptance checks, deployed
configuration, service, native source or secret was modified. No runtime tests/harness rerun;
previous 19/21 result is historical. Document scans and diff checks are separately reported.

## Correction: container script exists

`container-script-resolution-2026-09-15.md` supersedes the mcp_1 not-found/mismatch blocker.
Explicit stat returns EACCES, not ENOENT. Docker read-only archive at the configured path
returned the existing syntax-valid WHOOP health MCP source. Earlier is_file/search results
were visibility false negatives. No missing-file repair needed; MCP readiness still untested.
