# Dual-channel memory preparation evidence

Authority: Contract 14 section 12. Phase 14.2. Local synthetic work, 2026-09-16.

## Scope

Two pure server-only modules and one test file. Contract/spec authored before code.
No live Slack change, Telegram activation, token installation, external send, native writer
change, Drive upload, scope expansion or money computation. Slack works per owner report;
replacement Telegram token creation is owner-reported, not tested here.

Channel envelope separates reply binding from model context and memory provenance. Protected
raw IDs never enter the model-context object. Replay keys include platform/account/profile/
conversation/thread/event/direction, not text chosen by a model. Hashes are pseudonymous private
metadata, not anonymous. Enrollment checks assume authentic provider envelopes from trusted
adapters; they do not implement Slack signature checking or Telegram transport authentication.

The existing local journal writer was exercised with a synthetic sourceRef and stable identity,
independent reopen/read-back and conflicting retry. It was not replaced. Structured native
memory metadata schema still needs integration. No claim that this local test writes VPS memory.
Receipt assessment verifies matching attestations from trusted adapters, not actual encryption
or Drive provider behavior. Matching source and ciphertext/version/read-back is required before
reporting Drive synced. The source's expected hash/version must come from canonical content,
not from the LLM. Missing mirror preserves saved-local/unavailable; partial mirror is pending.

## Commands and observations

- `npm.cmd run typecheck`: first run passed. First new test run: 35 passed, 1 failed because
  test expected a throw, whereas existing writer returns FAILED/JOURNAL_UPDATE_NOT_PERMITTED.
  Corrected to exact documented refusal and original-content preservation. Next typecheck
  caught a test reference to text on a metadata-only result; changed to independent canonical
  file read, matching the existing writer test style. No production writer/check was altered.
- `git diff --check`: passed.
- `node scripts/verify/headers.mjs`: passed, 397 files.
- Explicit Python scan of six authored source/spec files found zero private-key/token/provider
  key/IPv4 pattern findings. This is bounded pattern coverage, not global secret certification.
- Source reference scan: no imports/references to new modules outside this increment.
- Final `npm.cmd run typecheck` and `npm.cmd run lint`: passed.
- `npm.cmd test -- --run src/server/hermes/channelMemory.test.ts src/server/process/journalPersistenceAdapter.test.ts src/server/hermes/ingressPolicy.test.ts src/server/db/isolation.test.ts`:
  62 passed in four files, including 36 new tests.
- `npm.cmd run build`: passed; existing non-fatal localCache.ts static/dynamic import warning.
- `npm.cmd run verify:all -- --all`: 19/21 checks passed, exit 1. Only AC14 clean tree
  and AC15 push readiness failed (38 uncommitted entries, including protected user work).
  Full machine test report: 3141 passed, zero failed/pending. Typecheck/lint/build, money,
  Drive scope, headers and bundle isolation passed. No acceptance check changed or user
  changes cleaned/committed to remove the failures. Final seven-artifact scan found no
  credential-pattern matches; this does not certify unrelated untracked files.

No independent reviewer or line/branch coverage percentage claimed. Direct review checked
closed schemas/refusals, immutable route binding, separate model projection, deterministic keys,
strict privacy/scope/encryption receipt requirements and no new network/DB dependencies.

## Remaining implementation before live acceptance

- Protected Telegram token transfer and owner/private-chat enrollment; unique consumer and
  non-destructive startup; actual fail-closed auth before Hermes plugins and commands.
- Native sole-owner brain schema/writer, approved capture/retention, structured provenance,
  independent content read-back and durable mirror retry state.
- Trusted encryption/upload/read-back adapter under drive.file, with keys outside Drive.
- Trusted outbound receipt provenance and channel-bound execution; actual channel replies
  and actual saved-on-VPS/mirrored-to-Drive observations for both channels.
- Cross-channel retrieval only through approved owner/profile privacy filtering, not raw
  transcript concatenation. No silent channel fallback or duplicate proactive broadcast.

A suspected credential file appeared untracked in repository-root status. Its contents were
not opened, changed, moved, tested or printed. Owner warned to move any token into protected
storage outside the repository. Existing tracked-only secret scan cannot certify that file.


## Capability matrix

| Capability | Evidence state |
|---|---|
| Slack conversation | Owner-confirmed working; untouched by this increment |
| Telegram conversation | Not activated or tested here |
| Channel label/model context | Local pure boundary tested for Slack and Telegram |
| Same-channel reply binding | Local immutable binding tested; live dispatch not wired |
| Shared brain with channel provenance | Contract and source identity prepared; native schema pending |
| Canonical content persistence | Existing local reference writer tested, not live VPS writer |
| Encrypted Drive copy | Receipt matching tested with synthetic evidence; no encryption/upload performed |
| Cross-channel continuity | Governed retrieval requirement specified, not implemented here |

This is preparation, not a live feature release. Contract ledger checker covers original
build-contract consistency; registration of the new PFOS section was reviewed directly.
