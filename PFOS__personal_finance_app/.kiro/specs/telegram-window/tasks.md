# Telegram window dependency-ordered tasks

Authority: PFOS Contract 14 section 10. Phase TW0. Requirements TW01-TW15.
Unchecked means not delivered. BLOCKED is not permission. No checkbox authorizes credentials,
host/native changes, network effects, production spend, commit/push or human gates.

## A. Foundation

- [x] TW-A1: inspect local authority, reusable modules and historical capture evidence;
  record initial file fingerprints. No current VPS inspection.
- [x] TW-A2: append local-only Contract 14 section 10, author requirements/design/tasks/handoff,
  register index/log. Requires A1. No live policy change or source implementation.
- [ ] TW-A3: BLOCKED_DEPENDENCY: obtain current scoped native code/config/service metadata
  and supported Hermes hooks; select one consumer/mode. Requires authorized read-only
  inspection scope and A2. Covers TW01/TW03/TW07.
- [ ] TW-A4: map native privacy/retention/finite limits/writer contracts and supported PFOS
  reads; unresolved authority blocks policy implementation. Requires A3. Covers TW07/TW10-TW12.
- [ ] TW-A5: owner reviews primary Telegram cutover, inactive Slack fallback, private identity
  enrolment and protected replacement credential handoff. Owner prerequisites only, no
  bot/credential/gate operation executed here. Covers TW01-TW04/TW12/TW15.

## B. Runtime, after native reconciliation

- [ ] TW-B1: smallest versioned adapter at selected actual ingress. Preserve v2 checks/tests;
  enforce metadata, mode and bounded input; pin finite limits from A4. Requires A3/A4/A5.
- [ ] TW-B2: reuse durable queue/lease path; stable effect identity, conflict detection,
  result/outbound persistence under database authority. Requires B1. TW05/TW06/TW13.
- [ ] TW-B3: native governed Hermes, grants/caps/kill/context, cancellation and initial
  commands. Requires B2 and separately scoped native changes if needed. TW07-TW09/TW12.
- [ ] TW-B4: supported PFOS reads and deterministic rendering. Requires B2/A4; parallel
  with B3. TW10. No full-engine-coverage or financial-write claim.
- [ ] TW-B5: capture/continue through native writer with stable key/read-back/recovery.
  Requires A4/B3 and separate native authorization. TW09/TW11/TW12. Does not block M2.
- [ ] TW-B6: version-compatible placeholder templates and queue-preserving synthetic
  cutover/rollback rehearsal. Requires B1/B2/B3. TW03/TW04/TW14/TW15.

## C. Synthetic acceptance matrix

| Test | Positive control | Negative/crash control | Requirements | Depends |
|---|---|---|---|---|
| TW-T01 | Owner/configured private chat | Empty/wrong sender/chat, group, bot, malformed/spoofed envelope: zero dispatch | TW02 | B1 |
| TW-T02 | Authentic selected mode | Missing webhook secret, wrong namespace, unknown version or consumer: refuse | TW01/TW03 | B1 |
| TW-T03 | Enqueue before ack | Crash before enqueue, duplicate, cross-bot collision preserve correct effects | TW05 | B2 |
| TW-T04 | Stable effect/result replay | Crash after write, lost lease, conflicting payload, lost reply never duplicate effect | TW06 | B2 |
| TW-T05 | Scoped planning executes mock port | Missing/stale/cross-profile grant, kill, cap, injection: zero disallowed calls | TW07 | B3 |
| TW-T06 | English/Arabic commands and clarify | Unknown command, restricted context, cancel-after-commit and ordering race remain honest | TW08/TW09/TW12 | B3 |
| TW-T07 | Exact PFOS fact/version | Float/overflow/stale/unavailable source and financial write never yield substitute | TW10 | B4 |
| TW-T08 | Capture read-back before saved | Metadata-only/failed read-back, restart/retry, foreign reference prevent false success | TW09/TW11 | B5 |
| TW-T09 | Unicode-safe ordered chunks | Formatting injection, rate limit, partial send, lost ack retain uncertainty | TW13 | B2/B3 |
| TW-T10 | Synthetic isolated credential binding | Sentinel in exception/environment never reaches model/reply/diagnostic sinks | TW04/TW12 | B1/B3 |
| TW-T11 | Matching capability evidence/recovery | Historical/offline/stale/unknown cannot become live-ready; halt preserves queue | TW14 | B6 |
| TW-T12 | Existing full harness unchanged | No skipped assertions, lower floors, server browser import or private fixtures | TW15 | applicable B |

- [ ] TW-C1: implement/run matrix as predecessors permit. Record command/snapshot/outcome;
  descriptions alone are not executed tests.
- [ ] TW-C2: focused typecheck/lint/tests/build then `npm run verify:all -- --all`.
  Preserve unrelated and dirty-tree failures; no commit authorized.
- [ ] TW-C3: independent review if permitted; otherwise explicitly record unavailable
  review. Producer cannot self-certify as independent verifier.

## D. Owner-held milestones, NOT executable leaves

M2 conversation: BLOCKED_HUMAN/BLOCKED_DEPENDENCY until current inspection, protected
replacement, scoped host/send/spend authority and offline evidence. M3 adds B4/T07 and
available PFOS source. M4 adds B5/T08 and native writer/privacy authority. M5 adds authorized
recovery observations and owner acceptance. Neither human record is tested/populated/marked.

## TW0 document checks

- [x] TW-V1: direct document/link/requirement/dependency review, secret-pattern scan including
  new untracked artifacts, byte-prefix preservation of existing files.
- [x] TW-V2: focused existing ingress regression and full harness; record actual outcomes
  in `verification.md`. Existing-code success is not restored Telegram functionality.

Critical path: A1 -> A2 -> A3/A4/A5 -> B1 -> B2 -> B3 -> C -> owner-held M2.
Parallel: B4 -> M3; native B5 -> M4; B6 -> T11. Voice, attachments, reminders, writes,
Mini App, DNS and new Drive integration are outside this increment.

TW0 checks executed; full gate 19/21, not green. See verification.md. All runtime tasks
remain unchecked. Independent review unavailable due to tool denial.

TW-A3 follow-up: scoped read-only inspection performed; see `inspection-2026-09-15.md`.
Access/container/source discovery succeeded, but A3 remains unchecked because unique intended-
bot consumer and full grant/tool integration are not established. Next bounded read: actual
gateway configuration loader and native dispatch hooks, without secret values or execution.
No runtime/activation task advanced by service health or source marker presence.

TW-A3 wiring trace: see `wiring-trace-2026-09-15.md` GW01-GW11. Container ownership assumption
withdrawn; supervisor/profile and registered native extension wiring remain unresolved.
B1/B6 must fence token-driven automatic enablement, webhook/menu mutations and pending-update
drops. T01/T05 must cover auth before hooks, pairing/wildcard bypass, missing/throwing hooks
and direct command-shell paths; T03/T04 cover in-memory batching crash before durable enqueue.
T10 additionally asserts identifier/exception redaction. These are required planned tests,
not assertions weakened or executed. No runtime task ticked by this source trace.

TW-A3 supervisor/extension follow-up: managed gateway A now mapped to system-level systemd
and explicit profile. Candidate B remains separate shell/user-scope; not stopped. Configured
native knowledge MCP identified as retrieval candidate, launcher resolution not fully proven;
Node bridge still unresolved. See `supervisor-extensions-2026-09-15.md`. A3 remains unchecked.
Next source checks: static wrapper/interpreter resolution, Node bridge purpose, effective tool
restrictions and native authority. B6 additionally includes four observed hardening gaps;
no service changes or new runtime tests executed by this trace.

TW-A3 remaining bridge trace: native knowledge launcher static resolution established; Camofox
browser bridge identified; container Python wrapper target/source mismatch remains unresolved.
Receipt: `remaining-bridges-2026-09-15.md`. Add B3/T05 cases for actual platform_toolsets,
nested tools.include/exclude precedence, empty-include fallback, default MCP inclusion and
utility tool registration. No browser/cookie/evaluation capability implicitly admitted.
No runtime task complete, no live bridge or model invocation occurred.

TW-A3 container-script correction: missing-file repair is NOT required. Exact configured
script exists, identified as WHOOP health source via read-only Docker archive. Prior host
is_file lookup was EACCES false absence; two owned probes fixed and ten synthetic cases pass.
See `container-script-resolution-2026-09-15.md`. Unique bot ownership/governance/readiness
still outstanding; no runtime/activation task ticked and no host file changed.
