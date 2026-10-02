# Telegram window requirements

Authority: PFOS Contract 14 section 10; Contracts 06/12/13 and money/Drive/server steering.
Phase TW0: local specification only. Runtime integration and live activation are NOT delivered.
Owner direction: 2026-09-15 request to execute the preceding Telegram restoration plan.

## Scope and precedence

One private text conversation, not a Mini App or second finance implementation. Contract 14
v2 remains live policy until separately reviewed cutover. Section 10 permits local design and
synthetic rehearsal only. No network, credential lifecycle, host, native-repository write,
production spend, commit, push or human-gate authority is granted by this specification.
Existing acceptance checks and Slack-v2 rejection coverage remain unchanged.

## Requirements and observable acceptance

| ID | Requirement | Acceptance criterion |
|---|---|---|
| TW01 | Versioned authority | Explicit restoration version required; unknown/missing versions fail closed. V2 aliases remain rejected in v2. No automatic Slack fallback or simultaneous activation. |
| TW02 | Owner-only private ingress | Missing owner/chat config rejects everyone. Validated transport metadata must match owner sender and approved private chat before dispatch. Wrong sender/chat/bot namespace, bot sender, group/channel, malformed IDs and unsupported updates cause zero tool/model calls. |
| TW03 | One consumer and mode | Exactly one consumer owns the bot namespace. Preserve an appropriate current mode. Empty webhook does not prove no poller; unknown ownership blocks activation. Preserve mode-specific guards. |
| TW04 | Credential isolation | Chat-exposed credential is not deployed by this workflow. Protected replacement and private identity handoff are live prerequisites. No secrets in prompts, logs, replies, Git, Drive, argv, fixtures or browser assets. Closed provider errors, never raw URLs/responses. |
| TW05 | Durable acceptance | Authenticate, bot-scope deduplicate and enqueue atomically before acknowledgement or polling-offset advancement. Duplicate is successful no-op. Limit bytes and parse only authentication metadata before business content. |
| TW06 | Retry-safe effects | Stable effect identity survives crash/reclaim. Same key with conflicting payload fails. Reuse recorded effects/results on reply retry. Lost lease prevents stale execution/settlement. Unknown effect outcome blocks blind replay. |
| TW07 | Bounded execution | Native grants govern Hermes. Missing/expired/cross-profile/excessive grants cause zero effects. Finite queue/context/attempt/time limits, conversation ordering, kill switch and separate model caps required. No shell/host/credential tool via chat. |
| TW08 | Honest UX | Received means durably queued; answered means response available; saved means verified canonical persistence. Routing labels do not substitute for Hermes execution. Unsupported capabilities report unavailable. Ambiguity asks one clarification with zero consequential effect. English and Arabic fixtures required. |
| TW09 | Sessions/cancellation | New detaches conversational context without deleting saved records. Cancel prevents pending effects where possible; running cancellation never claims to reverse committed effects. Continue requires owner/profile-scoped saved reference. Cancellation cannot wait behind the turn it must cancel. |
| TW10 | Finance authority | Expose only supported PFOS reads with source/version/freshness. No estimated substitute for unavailable/stale facts. Integer milliunits and existing formatting preserved. No ingress direct DB access, second writer or financial writes. |
| TW11 | Verified capture | Capture/continue unavailable until native writer/privacy/recovery reconciled. Stable-key persistence and read-back precede saved acknowledgement. Restart/lost-reply replay produces one canonical record. Metadata-only event is not capture evidence. |
| TW12 | Privacy/retention | Bot chat is not end-to-end encrypted. Strict-local material excluded from VPS/model/Drive egress. Bound context by profile/class/size/age/source. Queue/session/capture retention policies are separate and contract-derived; unresolved retention blocks real-content processing. No raw bodies/real IDs in telemetry. |
| TW13 | Reply delivery | Escape formatting or use plain text; Unicode-safe ordered chunks. Separate delivery from effect state. Ambiguous send remains uncertain, never reruns a tool. No exactly-once Telegram delivery promise. |
| TW14 | Readiness/recovery | Report ingress/worker/Hermes/PFOS/capture separately with environment/snapshot/time evidence. Historical/reported/offline/unknown evidence cannot establish live readiness. Queue-preserving halt/recovery rehearsal; no blind schema downgrade. |
| TW15 | Verification/authority | Source/test owner/phase headers, synthetic fixtures, server/routing bundle exclusion and unchanged acceptance floors. Focused then full gate; preserve failures/user work. Never execute/test/populate/complete either human control record or G1-G8. |

## Milestones

M0 = authored/reviewed preparation, not runtime delivery. M1 = tested synthetic integration.
M2 = separately authorized live conversation. M3 = selected PFOS reads, not all engines.
M4 = verified capture/continue, not unrestricted memory. M5 = authorized recovery evidence
and owner acceptance. No checkbox, token possession, installation receipt or greeting earns
these milestones without observed evidence.
