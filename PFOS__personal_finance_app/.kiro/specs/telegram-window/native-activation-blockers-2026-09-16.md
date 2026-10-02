# Native activation reconciliation, 2026-09-16

Authority: PFOS Contract 14 sections 10 and 12; TW02-TW07/TW12/TW14.
Phase TW-A3, read-only source reconciliation. NOT activation or live acceptance.

## Owner scope and established evidence

Owner explicitly requested activation alongside working Slack. Replacement credential was
owner-staged outside all active profiles. Independent metadata check found operator-owned
700 directory / 600 regular file. VPS getMe matched the staged bot identity; getWebhookInfo
reported no webhook and three pending updates at 2026-09-16T12:08:46Z. No poller, send,
offset advance, webhook mutation or model call was performed. No credential/identity value
is recorded here. Do not rerun staging. Budget permission is not the outstanding owner ask.

## Current source findings

Bounded AST inspection found one native checkout under the expanded search roots. The first
search limited to /opt and /srv found none; that was an inspection scope limitation, not an
absent-checkout diagnosis. Source was parsed as text, never imported or executed.

| Source | Observed ordering / behavior | Activation implication |
|---|---|---|
| relay/coordinator.py process, lines 140-233 | Calls _agent_response before classify/is_egress_blocked | Content may reach model before downstream egress decision. A later blocked reply cannot undo disclosure. |
| relay/coordinator.py _agent_response, lines 84-132 | Calls append_explicit_memory before invoking Hermes | Native content writer integration now exists in source; earlier metadata-only inference is not a complete current account. Writer privacy, stable identity and independent read-back are not established by this trace. |
| relay/poller.py handle_update, lines 89-113 | dedup.record before auth.verify_user_id and coordinator.process | Seen marker can survive without completed processing/result. Crash may suppress retry. |
| relay/poller.py poll_once, lines 116-124 | Next offset derives from dedup.max_seen + 1 | Seen marker is used as acknowledgement without demonstrated durable enqueue. |
| relay/auth.py verify_user_id, lines 77-96 | Sender allowlist membership only in inspected function | This function does not establish required owner AND private-chat match, or bot rejection. |
| relay/hermes_adapter.py invoke_hermes, lines 134-189 | Copies environment, adds memory/grounding, invokes CLI | Not a verified no-tool, private-context-isolated smoke path. Explicit request budget and credential isolation remain unproved. |

Source fingerprints:
- coordinator.py: 888c329ca79e688079b5be6ce3708e520e88132f6c218e217236ed0fec579018
- hermes_adapter.py: ff99151deb72f04505547fc7ef469f18ed0f1463ad3b37edbdab13b326dd7d75
- poller.py: 7faaa16de8006d2928aaf971fed0f80bfe939fd742fdfa9840c584832a96c5ef
- auth.py: 4efc5ba69ca180ba23ac30c5191760f66d66249d5bb47aad4505aa84778ba1da
- dedup.py: bd15ea2fa5a56342ce5f6adb5a3fa3688388c6af553e01e995b2ff10a6ab5d44

These are on-disk observations, not proof the running Slack gateway uses these modules.
No global claim is made about all upstream guards or all possible consumers.

## Disposition

Neither unmodified Hermes Telegram startup (previous GW01-GW11) nor unmodified native
poller meets current Telegram-window requirements. No token insertion/restart workaround.
No second independent chatbot, life writer or competing finance poller.

Next scope requires explicit review of native relay gate-ordering/durable-intake repair:
1. Owner/private-chat admission before dedup, plugins, commands or content execution.
2. Existing native privacy/egress decision before model or content write. Preserve its policy;
   fail closed, never alter classification merely to enable a reply.
3. Durable bot-scoped intake before acknowledging; stable execution identity, recorded result
   and uncertain-delivery handling across restart. Reconcile existing native writer authority.
4. Explicit no-tool conversation executor, minimal environment/context and bounded model calls
   including retry/summary paths. Preserve Slack configuration/process and queues.
5. Synthetic negative/crash acceptance, then authorized versioned deployment and live reply.

Two-agent steering section 6a explicitly preserves the native three-gate pipeline as authored.
Activation approval does not silently authorize restructuring that pipeline. Record this as a
scope blocker rather than bypassing it. No human control record was executed/tested/updated.

## Commands and checks

- agent spawn --name telegram-activation-architecture --profile nizam-architect --mode plan
  with bounded read-only task: denied by tool policy; no independent review occurred.
- python -B ~/.aki/tmp/telegram-window-inspection/run.py
  ~/.aki/tmp/telegram-window-inspection/remote_native_activation_source.py:
  first limited-root run found zero; expanded-root run found one; final selection additionally
  inspected process/auth/dedup. All returned redacted JSON. No remote file writes.
- A malformed local rg glob path failed; repeated using rg -g patterns on the directory.
- An identical-string local edit was refused and changed nothing; subsequent actual source
  selection edit was viewed before execution.

No repository application code changed in this increment. Prior full-gate result: 19/21,
AC14/AC15 fail on 37 uncommitted entries; not rerun or represented as new runtime evidence.
