# Recovery 1 test and validation report

Owner: `contracts/programs/SEVEN_CONTRACT_RECOVERY.md`. Phase: Recovery 1.
Observed 2026-09-11. No production release or seven-contract completion is claimed.

## Code changes

- `src/lib/db/schema.ts`: `zMoney` now uses `.int().finite().safe()`; comments describe
  the exact domain. Existing `.nonnegative()`/`.nullable()` compositions remain intact.
- `src/lib/db/moneyBoundary.test.ts`: 11 synthetic cases covering signed safe endpoints,
  overflow, malformed/non-number inputs, composed fields, migration and fake Drive load.
- `scripts/verify/all.mjs`: test floor raised from 2301 to 3009 (observed 2998 baseline + 11).
  No acceptance assertion was removed or weakened.
- Program contract, requirements/design/tasks, source registry and master handover added.

No money computation, schema version, dependency, application route or provider adapter changed.
The supplied package.json modification and all pre-existing untracked work remain untouched.

## Commands actually run and observed results

Commands below ran from the repository root. npm used the installed Windows Node 24 toolchain,
via `powershell.exe -NoProfile -Command`, not the tool alias that can select a different runtime.

| Command | Observation |
|---|---|
| `powershell.exe -NoProfile -Command "(Get-Command node).Source; node --version; npm --version"` | Installed native node; v24.14.1 / npm 11.11.0 |
| `powershell.exe -NoProfile -Command "npm run typecheck; npm run lint"` | Both baseline checks passed |
| `powershell.exe -NoProfile -Command "npm run verify:all -- --all"` (baseline) | 19/21; 2998 tests passed. AC14 and AC15 failed on pre-existing dirty tree |
| `powershell.exe -NoProfile -Command "npm test -- --run src/lib/db/moneyBoundary.test.ts"` (before fix) | 11 tests: 5 passed, 6 failed, proving unsafe integer acceptance at primitive/composed/load boundaries |
| `powershell.exe -NoProfile -Command "npm test -- --run src/lib/db/moneyBoundary.test.ts src/lib/db/schema.test.ts src/lib/db/migrations.test.ts src/lib/drive/driveDb.test.ts src/lib/money/pfosBoundaryParity.test.ts"` | 5 files, 70 tests passed after repair |
| `powershell.exe -NoProfile -Command "npm run typecheck; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npm run lint; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npm run build; exit $LASTEXITCODE"` | TypeScript, lint and Vite production/PWA build passed |
| `powershell.exe -NoProfile -Command "npm run verify:all -- --all"` (after fix + floor) | 19/21; 3009 tests passed, zero failures in machine report. AC14/AC15 remain failed |
| `git diff --check` | No whitespace findings |
| `mcp list` | No MCP servers configured for current profile |
| `python ~/.aki/tmp/nizam-seven/probe.py` | Initial background wrapper produced exit 120/no evidence; foreground rerun reported SSH rejection and Drive HTTP 401; corrected configured account/key pairing authenticated |
| `python ~/.aki/tmp/nizam-seven/runtime_inventory.py` | Authenticated read-only discovery: one loaded/active/running ingress role, seven running containers, Node present, zero name-matched system/user project timers |
| `python ~/.aki/tmp/nizam-seven/drive_inventory.py` | Existing narrow refresh grant renewal refused, HTTP 400; no consent or scope expansion |

The inspected local probe scripts are session-local under the tool's private temp directory.
They consume existing credential references, retain no token renewal, print only allowlisted
status/counts and discard raw command/provider errors. No raw secret or deployment particular
was emitted. The first probe's anticipated inactive units were NOT treated as outage evidence.

A value-blind Python manifest comparison also recomputed each of the four local blueprint
SHA-256 digests: all four matched `contracts/pfos/_INGESTION_MANIFEST.json`. This proves local
byte consistency only, not current remote byte equality.

## Failure analysis

Red regression cause: Zod integer/finite checks accept values beyond JavaScript's safe-integer
range; the core `isMoney` rejects them. The `.safe()` addition aligns domain validation without
coercion, arithmetic, data rewriting or changes to valid schema-v9 input.

Full gate: every technical check passed, but AC14 requires a clean working tree and AC15 also
requires it. Existing uncommitted owner work was present before this program and new reviewed
work is deliberately uncommitted. No authorization to commit or push was supplied. These are
real unmet acceptance conditions, not skipped checks. Overall acceptance remains FAILED.

## Design/security review

- One shared validator, no duplicated money logic or dependencies.
- One small synthetic fixture factory; tests exercise production migration and load functions.
- No network in tests, no model call, no secrets in fixtures, no mutation of private data.
- Contract/phase headers present within first 20 lines of both changed source/test files.
- Test floor only increases; routing/benchmark modules remain outside app bundle (AC08b).
- Limits: this repair does not add a validator to every typed write API and does not remediate
  plaintext Drive egress. Those are explicitly open in MASTER_HANDOVER.md.

## Independent review reconciliation

Three read-only evidence reviewers returned lineage/UX, core/security, and runtime/continuity
findings; a fourth was assigned the small repair. Findings are evidence, not instructions or automatic truth.
The lead confirmed the restored-steering chronology and separately authorized C6 implementation
in ADR-0003. Reviewer suggestions to restore old specs or infer missing full Contract 05 are not
adopted: old spec deletion was intentional, and full Contract 05 exists in the live tree.

Independent repair review returned with no blocking defect in the bounded change. Its
commit-readiness recommendation is not adopted as release acceptance or owner authorization: 
AC14/AC15 and the production blockers remain unmet. Details and caveats follow below.

## Additional scope checks

A local Python presence/pattern check examined all eight newly added program/spec/handover/test
files for private-key blocks, provider-token shapes and IPv4 literals: zero findings. Both
changed source/test headers declare contract and phase. This bounded check is not a complete
secret-detection proof: repository secret/generic scanners inspect tracked files, while the new
files remain untracked. A Python byte-prefix comparison confirmed all historical bytes of both
PFOS index and build log remain preserved; this session only appended entries.

## Final handoff gate

After index/build-log/handover creation, ran:
`powershell.exe -NoProfile -Command "npm run verify:all -- --all"; git diff --check`.
Observed again: **19 of 21 executed checks passed**, with 3009 passing tests and only
AC14/AC15 failing (20 uncommitted entries at that observation). The wrapper task reported
success because its last command was `git diff --check`; that does not change the harness's
explicit FAILED verdict. No whitespace findings were emitted.

Source-reference existence check found only the intentionally deleted original UI spec
path, already marked unavailable. No other concrete file reference in the new documents
was missing. No gate was hidden or reclassified as passed.


## Independent repair review received

The reviewer reported these commands and observations (independent evidence, not additional
lead executions):
- `npm test -- --run src/lib/db/moneyBoundary.test.ts`: 11/11 passed.
- `npm test -- --run "src/lib/db"`: 63/63 passed across four files.
- `npm test -- --run`: 3009/3009 passed across 173 files.
- `npm run typecheck`, `npm run lint`, `npm run build`: passed.
- `node scripts/verify/headers.mjs`: passed, 386 files.
- `node scripts/verify/secret-scan.mjs`, `node scripts/verify/generic-only.mjs`,
  `node scripts/verify/money-invariant.mjs`: passed within their scanner scope.
- `npm run verify:ledger`: 20 certificates, intact chain, zero uncovered.
- `node scripts/verify/clean-tree.mjs`, `node scripts/verify/push-ready.mjs`: failed on dirty tree.

No blocking repair defect was reported. Two caveats remain:
1. The 3009 floor includes protected pre-existing untracked tests. Their ownership and release
   disposition must be resolved explicitly before any commit. Do not silently omit those files,
   commit unrelated owner work, or lower the floor to hide the dependency.
2. Legacy migration coercion is outside this repair. The lead confirmed
   `src/lib/db/migrations.ts:31-32` returns a fallback for invalid integers, and the v0-to-v1
   account/month conversion uses it at lines 60-62 and 75-78. Some policy migration fields
   also use this helper. Such paths can replace malformed money before final validation.
   The review's broader assertion that all v0-v8 balances are coerced is not established;
   behavior depends on the actual migration path and field. Current-schema migration refusal
   is tested; universal legacy-input refusal is not. Never test for or bless silent zeroing as
   the desired financial outcome. A follow-up needs synthetic legacy cases and a reviewed
   distinction between missing-field defaults and rejection of present-but-invalid evidence.

The review does not clear canonical-source access, encrypted persistence design or release gates.
