# A3 — R2 governor live receipt

Owning contracts: NIZAM-DAILY-ORCHESTRATION-04 (`schedule`, `daily_dag`,
`reconciliation_1300`), NIZAM-CONTRACT-01 (`required_runtime_receipt`,
`autonomy_classes`), NIZAM-CALENDAR-ACTUATION-001 v1.0.0
Phase: R2_SCHEDULER (closing) → R3
Date: 2026-09-03
Status: R2 timing authority is LIVE and registered with OS cron. No slot has
executed its RUN branch yet; the first real firing is 2026-09-04 07:00 UTC.

---

## 1. What went live

The four owner-decided slots are registered with OS cron, each at both its EEST
and EET UTC candidate, because the host's cron has no `CRON_TZ` support and the
live Contract 04 preflight **measured** the scheduler's own zone as UTC with
`TZ` unset.

| slot | Cairo target | role |
|---|---|---|
| `refresh_1000` | 10:00 | heavier Drive, index and cache refresh |
| `volatile_1140` | 11:40 | volatile WHOOP, Calendar, location, weather, news |
| `primary_1200` | 12:00 | primary governor run |
| `reconcile_1300` | 13:00 | reconciliation and retry only |

Install post-conditions, all asserted by the installer rather than assumed:
block installed; every pre-existing line survived; exactly four slot lines;
stripping the managed block reproduces the pre-install snapshot. An independent
byte-diff of the pre-install crontab against the post-install crontab with the
block stripped returned **IDENTICAL**, and the snapshot digest equals the
pre-install digest (492 bytes). Cron daemon `active`.

## 2. Wrapper contract: 28 cases, 0 failures

The shared clock module deliberately exposes no injection hook, so the wrapper's RUN branch
cannot be driven by faking the clock. It was proven instead through the
documented `NIZAM_GOVERNOR_PKG_PARENT` override — a real injected port — with
the module's own RUN behaviour proven separately by the package suite.

Branches proven: module reports RUN (wrapper reports `ran`, surfaces verdict,
guard, Cairo instant and delta, writes exactly one log line, invents no
receipts file); module reports stand-down; module fails (exit 1, failure banner,
no OK banner, stderr captured); module succeeds but emits unparseable output
(exit 0, `summary_unavailable`, and it does **not** claim `ran`); bad slot name
(exit 2, no state created); missing package (exit 2, names what is missing);
real per-slot lock already held (exit 0, module never runs); second invocation
appends rather than truncates; the real package standing down at a non-slot
instant.

## 3. Calendar reconciliation completed: 3 script sites plus 1 pinning test

`CALENDAR-ACTUATION-001` supersedes "a calendar write requires human approval".
Seven statements were reconciled earlier. Locating the ingest cron script turned
up three more, not two as first recorded, because the **section header itself**
asserted the superseded rule.

| site | before | after |
|---|---|---|
| script line 23 | `# HUMAN GATES: no calendar write happens here.` | separation-of-duties boundary owned by the governor |
| script line 128 | `# ── T. calendar stays human-gated ──` | relabelled, comment-box width preserved exactly |
| script line 129 | `…(human approval required)` | `…here (owned by the governor under …-001)` |
| `test_schedule_gate.py:154` | `assert "human approval required" in src` | **four** assertions replacing one |

The test change is a strengthening, not a weakening. The tempting move was to
delete the marker assertion so the suite went green; that would be weakening an
acceptance check to make it pass. Instead the marker was replaced by four
assertions (new statement present, governing contract named, both superseded
phrasings pinned as absent), and the patcher asserts that the substantive
forbidden-call-path loop survives **byte-identically**.

The ingest job's own log file still contains the superseded sentence and was
deliberately left alone. Logs are evidence of what the job actually printed on
2026-09-02 and 2026-09-03. Editing them to make a scan look clean would be
falsifying a record.

Health stack: 239 passed before, 239 passed after. `bash -n` clean.

## 4. Defects found and fixed this session, none by weakening a check

1. **Patcher post-condition was wrong, not the patch.** `"set -euo pipefail" not
   in after` failed on the header comment that *documents* the two-and-a-half-month Drive
   stall. The house test's `_active_lines()` helper exists for exactly this
   ("Comments explain the old bug and must not trip a check") and I re-created
   the bug it was written to prevent. The check now strips comments the same way
   and additionally asserts the lesson comment survives verbatim. The script was
   restored from the backup taken minutes earlier and re-patched cleanly; the
   final content is **byte-identical** to the first attempt, proving the edit was
   always right and only the check was wrong.
2. **A redaction fragment still matched the scanner.** `test_package_hygiene.py`
   splits forbidden tokens so the file does not become the thing it scans for,
   but the left fragment `/opt/personal` (13 chars) still matched
   `abs_host_path` on its own. Re-split so neither half matches; the
   reconstructed token is unchanged, so detection is identical.
3. **My own test design produced a false negative.** A Cairo-vs-UTC date
   comparison written as `date -d "… UTC"` reported "same" for both zones,
   which looked like missing zoneinfo. It was not: naming a zone inside `-d`
   makes the tool render output in that zone. Re-tested with epoch conversion,
   which discriminates correctly (22:30Z is 2026-09-04 in Cairo). Incidental
   finding: this host's `date` is **uutils coreutils 0.8.0**, not GNU, so
   GNU-only `date` flags must not be assumed anywhere.

## 5. Correction to an earlier finding of mine

`INSPECT_FINDINGS` item 9 recorded the BADAN body-health README as
`strict_local`. The repository's own classifier says otherwise, and the
distinction matters:

| path | `classify()` | path gate |
|---|---|---|
| the BADAN body-health README | `private_github` | **ALLOW** |
| `BADAN…/WHOOP_INFRASTRUCTURE.md` | `strict_local` | **BLOCK** |

So the path gate would **not** have stopped that README. What protects it is its
content — an embedded WHOOP numeric identifier — which a path classifier
structurally cannot see. For a public repository the path gate and the content
scanner guard different failure modes and neither substitutes for the other. I
had conflated them.

## 6. Public-safety triage before committing

`nizamcore` is public, so every new file was scanned. 269 raw findings were
triaged rather than accepted:

| pattern | cause | verdict |
|---|---|---|
| `long_opaque_token` ×264 | `NIZAM-DAILY-ORCHESTRATION-04` and `NIZAM-CALENDAR-ACTUATION-001` are exactly 28 characters, plus long snake_case test names | benign; contract identifiers are a house requirement |
| `public_hostname` ×5 | the regex treats a `.sh` filename suffix as a TLD | benign; filenames |
| `abs_host_path` ×1 | the `/opt/personal` fragment | **real, fixed** |

After the fix every sensitive class — absolute host path, home path, IPv4, IPv6,
database URL, password, secret, private key, container name, bind port — reports
**zero**.

## 7. Commits

Two narrowly scoped commits on the local `nizamcore` checkout. The repository's
own HIMAYAH egress gate passed on each staged set before each commit.

| commit | scope | files |
|---|---|---|
| `cae6053` | scheduler package: Cairo gate, single clock read, receipt and manifest, two entrypoints, eight test modules | 14, +3332 |
| `48aab2f` | cron wrapper (first tracked shell script in the repository, mode 100755) and the slot installer | 2, +357 |

Nine commits are now unpushed. **Nothing has been pushed.** Push remains
unauthorised.

Three pre-existing owner modifications were preserved and remain uncommitted:
the BADAN body-health README, the SUKOON recovery-first README, and
`BADAN__body_health_system/WHOOP_INFRASTRUCTURE.md`.

## 8. Seven `REQUIRED_BY_R2_R7` files: reproducible in Git

Items 2 through 7 are tracked. Item 1 (the retrieval tree) has 29 files on disk
excluding bytecode, 23 tracked, and 6 deliberately excluded with a documented
reason in `.gitignore`: two deployment receipts that name containers and bind
addresses, two benchmark result files that quote real corpus paths and real
owner query text, and two pre-redaction rollback backups.

## 9. Verification totals

| check | result |
|---|---|
| scheduler suite, local | 243 passed, 1 skipped |
| scheduler suite, host | 244 passed |
| health stack, host | 239 passed |
| wrapper contract cases | 28 / 28 |
| tamper cases, cumulative | 83 / 83 detected, 0 missed, 0 inconclusive |
| Contract 04 live preflight | 4 / 4 firings matched pre-stated expectations |
| sensitive scan classes on new files | 0 |

## 10. Honest evidence gap

`faketime`, `datefudge` and `libfaketime` are all absent from the host — checked,
not assumed — so the clock cannot be virtualised and the wrapper's RUN branch
cannot be observed end-to-end against the real module today. What is proven
today: real cron fired four times and every firing matched a pre-stated
expectation; the module's RUN and stand-down paths at exact instants in both DST
regimes, by 244 tests; the wrapper's RUN branch against an injected module. All
four Cairo targets for 2026-09-03 had already passed by 14:00 UTC. **The first
real governor RUN is 2026-09-04 07:00 UTC = 10:00 Cairo (`refresh_1000`).**

## 11. Not done, and not claimed

No Drive write, no Calendar write, no GitHub push, no network call, no money.
Nine governor stages are recorded as BLOCKED with a named open loop and landing
phase each, because Contract 01 requires `blocked_actions` and `open_loops`
precisely so an incomplete run cannot present itself as a complete one.
