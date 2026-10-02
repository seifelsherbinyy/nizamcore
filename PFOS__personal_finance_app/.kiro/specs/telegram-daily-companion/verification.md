# Daily companion verification and live handoff

Authority: PFOS Contract 14 section 11. Phase 14.1 (DC1), 2026-09-15.
Environment: local Node 24 / TypeScript / Vitest, synthetic fixtures only.
Not a live Telegram, Hermes, WHOOP, PFOS-source or canonical-capture receipt.

## Implemented and architecture chosen

Five server-only modules: dailyPolicy, dailyControls, dailyMessages, dailyStore,
dailyCompanion. Three test/support files. No application or process startup imports them.
One existing storeless scheduler, synthetic life-tick composition, no second timer.
Five modules separate pure selection, command transitions, rendering, persistence and
orchestration. SQLite reference uses existing connection factory, WAL/FULL, transactional
reservation/CAS and close/reopen tests. It refuses non-reference filenames. No migration
of finance.db, native life.db, journal, existing queues or deployment configuration.

Closed metadata and bilingual question templates prevent arbitrary source text, amounts,
credentials and IDs from being carried in plans/messages. No LLM call or money computation.
The identity destination is injected only into the dispatch fence, never persisted/rendered.
Monotonic per-pillar revisions and local-day/cycle receipts suppress repeats. Uncertain
sends are held for reconciliation, not retried. This can miss a prompt after a crash;
it deliberately does not promise exactly-once Telegram delivery or lossless notification.

## Tests actually run

- `npm.cmd run typecheck`: initially 11 errors (unknown SQLite rows and invalid typed
  negative fixture), corrected using validated row shapes and unknown input at schema.
  Next attempt found two test indexed-access errors, corrected. Subsequent run passed.
- `npm.cmd test -- --run src/server/hermes/dailyPolicy.test.ts src/server/hermes/dailyCompanion.test.ts`:
  first invocation only found policy test file, 62 passed; integration file creation had
  failed in background shell and was NOT counted as coverage. Recreated/verified the file.
  Both files then ran: 92 passed (62 policy, 30 integration).
- `npm.cmd run lint`: initially one no-unexpected-multiline finding in new parameterized
  test; joined function call and reran successfully. No assertion changed.
- `npm.cmd test -- --run src/server/hermes src/server/telegram src/server/process/scheduler.test.ts src/server/process/singleWindowFlow.test.ts src/server/db/isolation.test.ts`:
  493 tests in 30 files passed, including 96 new cases after bilingual rendering tests.
- `npm.cmd run build`: passed; Vite non-fatal existing localCache.ts static/dynamic import
  chunking warning. SQLite tests emit Node's experimental-binding warning.
- `git diff --check`: passed.
- Inline Python scanned all 11 new source/spec artifacts for private-key, Telegram-token,
  provider-key, OAuth-secret and IPv4 patterns: zero findings. No real secrets retrieved.
- Inline Python checked source references: no companion imports outside its own increment.
- `npm.cmd run verify:all -- --all`: first run found AC10 because Phase DC1 is not numeric.
  Corrected all eight source/test headers to Phase 14.1 (DC1); unchanged
  `node scripts/verify/headers.mjs` then passed over 394 files. First full run: 18/21,
  AC10/AC14/AC15 failed. Corrected full rerun: **19/21, exit 1**; AC14 clean-tree and
  AC15 push-readiness failed because 33 working-tree entries remain uncommitted. All other
  checks passed, including build and bundle isolation. `.loop/tmp/test-results.json` confirms
  **3105 passed, 0 failed, 0 pending**. No acceptance check, floor, commit or user file
  was changed to eliminate the dirty-tree failures.

Coverage evidence is behavioral, not a line/branch percentage: coverage-v8 is not installed,
no dependency installed and no coverage percentage claimed. Cases cover local-day/timezone,
DST gap/repeat, quiet hours, pause/resume/snooze, cadence, stale/denied/completed/unchanged
state, low capacity, PFOS provenance, no fake capture, bilingual controls/rendering, unknown
inputs, auth rejection, consent/settings races, atomic rollback, real SQLite reopen,
concurrent connections, reserved/uncertain crash, provider/settlement failure and clock halt.
Direct review only; no independent-review claim. Checked DRY, responsibility separation,
parameterized SQL, closed exceptions, opt-in, no network, no new dependency and no app import.

## Operational status matrix

| Capability | Offline evidence | Current live status |
|---|---|---|
| Telegram ingress | Existing auth/queue regression tests retained | Restoration not activated; intended unique consumer unproven |
| Hermes conversation | Existing bounded-port tests retained | Config/source inspected; new governed end-to-end conversation unobserved |
| Daily clock | Existing SchedulerHost composition test | No daily job activated |
| Daily policy/controls | 96 new synthetic cases with SQLite restart | Native adapter/settings store/dispatch fence not integrated |
| HIMAYAH | Consent/kill/identity gating tested | Actual native pre-plugin enforcement unresolved |
| SUKOON | Downshift and stale recovery tested | Approved current recovery input unavailable here |
| BADAN | Bounded selection and bilingual question | WHOOP source exists; live tool/source freshness untested |
| THABAT | Open/urgent state and revision suppression | No verified canonical continuity update |
| SHURA | Planning intent, selection/question | No new native planning execution |
| NAQD | High-capacity gating | No new native critique execution |
| QARAR | Decision intent/selection/question | No decision record written or claimed |
| YAWMIYAT | Honest unavailable-capture reflection | Native writer/read-back still unverified |
| TAFRIGH | Unload intent/question, no saved claim | Conversation capture only; no durable native evidence |
| MAL_PFOS | PFOS-origin material flag only; no figures | Authoritative live adapter not connected |
| Weekly synthesis | Changed-signal selection in weekly window | Native fact synthesis/trend feedback unavailable, not fabricated |
| Recovery | SQLite receipt restart and uncertainty tests | No live restart/cutover rehearsal executed |

## Current blockers and remaining implementation

The companion is PARTIAL OFFLINE IMPLEMENTATION, not full attachment completion. Native
multi-turn execution, durable intake/effect/result/outbound integration, live-source pillar
adapters, natural-language preference disambiguation/focus-this-week, real weekly synthesis,
interactive /today and /checkin execution, and native configuration deployment remain open.
The command parser returns intents only; it does not turn classification into execution.
Retention and timeouts remain native adapter obligations before live content is admitted.

Prior read-only receipts remain authoritative within their scope under ../telegram-window/:
startup can drop pending updates/mutate webhook/menu; pre-dispatch hook precedes ordinary
auth and exceptions fall through; multiple gateway-shaped processes observed; no proven
unique intended-bot consumer; MCP selection/filtering and native grants need reconciliation.
The container script is NOT missing: Docker archive read proved WHOOP source exists.
Do not repair that false diagnosis or weaken permissions. Live MCP function remains untested.

## Exact owner-held prerequisites

1. Replace the chat-exposed Telegram credential through BotFather yourself. Store replacement
   outside chat/Git/Drive in the approved protected environment file. Provide only the file
   reference and confirmation it is the replacement, never its value. No rotation performed.
2. Enrol the approved owner sender and private chat through the protected configuration path;
   bot identity alone is insufficient. No real identifiers belong in this report.
3. Approve the specific reviewed cutover/native deployment and capped provider/send scope once
   safe ingress, unique consumer, native persistence, grants and non-destructive startup are
   ready. Generic token possession does not authorize activation or production spending.

These owner actions do not magically resolve the engineering blockers above. No live success
can be claimed until authorized conversation, scheduled trigger, restart and controls are
actually observed. Existing dirty-tree checks remain; no commit/push or cleanup authorized.
