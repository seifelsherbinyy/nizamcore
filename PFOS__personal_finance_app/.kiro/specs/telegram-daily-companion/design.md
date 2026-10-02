# Telegram daily companion design

Authority: PFOS Contract 14 section 11. Phase 14.1 (DC1), synthetic reference only.

## Composition

`process/scheduler.ts` remains the one storeless clock. Its injected life tick can invoke
`dailyCompanion.tick`; finance ticks remain independent. No process main, socket, cron,
service or Hermes plugin is activated. The real life agent is Python in another repository;
this TypeScript reference is not a replacement writer or a claim of deployable native wiring.

`dailyMessages.ts`: closed bilingual questions selected by plan; no arbitrary interpolation,
figures, inferred measurements or saved acknowledgements. It is not native weekly synthesis.
`dailyPolicy.ts`: strict Zod settings/source schemas, local windows via Intl.DateTimeFormat,
priority selection, closed plans and deterministic command/control parsing.
`dailyStore.ts`: injected StoreHandle from existing WAL/FULL connection factory. Explicit
reference-schema initialization on synthetic stores only; settings CAS, transactional run
reservation, monotonic revision tombstones and closed receipt state. Never used in finance
schema migration or mounted into scheduler. Production requires native sole-owner adapter.
`dailyCompanion.ts`: auth/kill checks before reads, read settings, read bounded state, select,
reserve, recheck controls/governance, mark uncertain, invoke one injected bounded dispatch,
settle receipt. No underlying domain effect occurs here. A delivery exception returns a closed
code; a storage failure blocks dispatch. Unknown sending outcome is retained without retry.

## Time and identity

Configured integer local minute/window (1..180 minutes), weekday (0 Sunday..6 Saturday),
max three items, minimum gap and bounded snoozes (up to seven days). These are conservative
DC1 policy bounds, not inferred existing runtime settings. End-of-day windows are clipped,
not carried into tomorrow. Equal quiet endpoints mean quiet all day; null disables quiet.
Run identity = local date + cycle, deliberately excluding mutable timezone/config revision.
Last reserved instant fences backward clock movement and enforces the configured minimum
gap; no missed-run queue. Per-pillar cadence is elapsed time, not calendar-day arithmetic.

Native state port accepts only closed enums, source revision and freshness timestamps.
Each pillar revision is monotonically increasing and denotes changed actionable state.
Safety/private material is excluded before the policy port. No labels, text, IDs, amounts,
ledger rows or arbitrary model input are accepted. Freshness is checked against injected now.
Low/unknown recovery allows stabilization, urgent continuity and PFOS alerts only; NAQD
requires high capacity. Plan contains closed pillar/question codes; renderer must separately
retrieve approved facts with provenance through governed ports. A plan is not a synthesis
of unavailable native journal data. Weekly selects fresh changed items, not fabricated trends.

## Controls and dispatch fence

Control parser is exact-match, not an LLM authority oracle. Control persistence uses revision
CAS, is authorized separately and returns no success until durable read-back. /resume_daily
only removes pause, never enables a disabled policy. /less and /more adjust question count
within 1..3; pillar cadence/snooze can be changed via validated structured settings/control.
Natural-language ambiguity has no configuration effect. Rendering/command execution of other
pillar requests remains the existing governed runtime's responsibility, not tool execution here.
After async source retrieval, reservation rejects stale preference revision. The native dispatch
port must atomically enforce current identity/consent/kill/control fences at the actual send;
this reference's final synchronous check cannot revoke an already-started provider request.

## Pillar registry / operational status

All sources below are injected, unavailable until a native privacy-approved adapter exists.
All scheduled triggers require fresh active changed state plus consent/cadence. Every pillar
is private; strict-local has no egress. No medical diagnosis, money computation or ledger write.

| Pillar | Existing evidence/source candidate | Authority | Trigger / failure |
|---|---|---|---|
| HIMAYAH | Native governor/privacy pre-gate; toolBoundary | gate only | always first; unknown denies |
| SUKOON | read_recovery_state; WHOOP bridge source inspected only | approved recovery read | first; missing downshifts |
| BADAN | WHOOP bridge/static health tools | approved health read | fresh routine; unavailable, no diagnosis |
| THABAT | native continuity post-gate, no verified writer here | native sole owner | open/urgent loops; no false update |
| SHURA | existing ingressRouter planning route | governed conversation | consequential decision; no native action |
| NAQD | existing ingressRouter critique route | governed conversation | high recovery only; defer otherwise |
| YAWMIYAT | journalPersistenceAdapter reference; native writer unverified | native sole writer only | evening/reflection; discussed, not saved |
| TAFRIGH | existing capture routing | conversation first | unload/reflection; no claimed persistence |
| QARAR | existing decision routing, native ledger unverified | owner decision/native writer | decisions; no inferred decision made |
| MAL_PFOS | PfosToolPort deterministic facts; bounded signal bus | PFOS read only | material fresh alert; unavailable not zero |

Reactive routes include /help /status /today /checkin /plan /tafrigh /journal /finance
/decision /grill /body /recap /new /cancel. Router returns intent only; actual enabled
capabilities must be reported separately. /grill refuses under low/unknown recovery.

## Remaining deployment prerequisites

TW-A3/A4/A5 and TW-B remain open. Source-inspected Hermes startup mutates webhook/menu and
drops pending updates; pre-dispatch hooks precede normal auth and fail open. A safe native
integration must fix those boundaries, restrict platform_toolsets/MCP tools, prove unique
consumer ownership, select protected replacement credential and owner/private-chat identity,
and implement the native durable adapter before activation. Existing Slack-v2 checks stay.
No deploy script is emitted pretending this reference can be installed unchanged in Python.


## Legacy check-in reconciliation

Read-only inspection of `ops/hermes/daily_owner_checkin.py` found a deterministic morning
message generator over confirmed memory/evidence labels. It does not itself schedule or send.
It is not reused as a native source adapter: keyword privacy filtering is not the companion's
closed HIMAYAH boundary, and it has no durable run receipt. Its actual timer/cron ownership
remains to be reconciled before any activation; do not run it against private context here.
Existing Slack ingress config/service templates remain untouched. No new service template
points the Python gateway at this TypeScript reference.
