# Container script resolution: false absence corrected

Authority: PFOS Contract 14 section 10; owner asked to investigate and fix missing script.
Phase TW-A3 diagnostic correction. Observed 2026-09-15 20:06:52 through 20:07:30 UTC.
Result: configured script EXISTS. No missing deployment file to replace.

## Root cause

Earlier probes used pathlib.is_file() against the container process-root filesystem view.
That returned false for an inaccessible path, and subsequent bounded search also concealed
access errors. Neither established ENOENT. The explicit stat diagnosis now returns EACCES.
Thus the previously suspected target/source mismatch was a diagnostic false negative, not
an established deployment defect. Claims or task blockers asserting the script was missing
are superseded by this receipt. Host permissions are not weakened to satisfy a probe.

## Independent file existence observation

Docker inspect located the same configured target, running. Read-only archive streaming
`docker cp <container>:<configured-script> -` returned exit 0 and exactly one regular file.
Archive consumed in memory through tarfile.extractfile, never extracted to disk. No docker
exec, launcher execution, application import, service restart, provider call or container
mutation. No protected data or full source contents printed.

Configured path is absolute. Retrieved source is 11219 bytes, parses as valid Python AST,
and has SHA-256 `6c0af2b6fa8d8f08e892bc2ace0f27227578471b9e56428b4e4661ea8560bf10`.
Interfaces: _pool_get, _get_recovery, _get_sleep, _get_strain, _get_workouts,
_get_daily_summary, _get_trends, _date_default, handle_request, main (plus avg/slope helpers).
WHOOP source markers and these interfaces identify health-data retrieval/summary, not a
PFOS financial writer or canonical journal/capture bridge. No health records were read and
no health tool/provider was invoked. Syntax/existence do not establish MCP readiness.

## Fix applied

Changed only our temporary diagnostic probes under the local assistant scratch directory:
remote_container_bridge.py and remote_container_source.py. Both now distinguish:

| stat outcome | host_view_status | configured_source_present |
|---|---|---|
| Regular file | present | true |
| Nonregular file | not_regular_file | false |
| FileNotFoundError | not_found | false |
| PermissionError | inaccessible | null |
| Other OSError | unknown_error | null |

Inaccessible/unknown paths stop before the misleading fallback search. Repeated remote reads
of both corrected probes returned inaccessible/null, agreeing with EACCES. The Docker archive
read supplies positive existence evidence despite the host-side visibility limitation.
No deployment script, configuration, permissions, service or native repository was modified.

## Verification actually performed

```text
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_script_diagnosis.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_container_bridge.py
python ~/.aki/tmp/telegram-window-inspection/run.py ~/.aki/tmp/telegram-window-inspection/remote_container_source.py
```

All three commands exited zero. Diagnosis: EACCES host view; archive exit 0; one regular file;
valid syntax. Corrected probes: inaccessible/null for the exact same configured target.
Inline local Python extracted the actual immediate stat guard from each probe and injected
five filesystem outcomes (regular, directory, missing, denied, generic OS error). Ten cases
passed. No remote/application code executed by the synthetic tests.

Failures recorded: initial local probe construction used an incorrect text anchor and failed
ValueError before creating/running the probe. Fixed exact anchor and syntax-checked locally.
Initial synthetic test selected the enclosing AST try block and failed NameError before its
first remote subprocess call; corrected selection to the immediate stat assignment. The final
ten-case test passed without changing any acceptance expectation.

Repository verification after documentation corrections is recorded in verification.md.
No new application runtime feature or live MCP round trip is certified by this correction.

## Current bridge inventory and remaining scope

- mcp_1: configured container script exists, WHOOP health interface, live readiness untested.
- mcp_2: Camofox browser automation, consequential tools not approved for initial Telegram.
- mcp_3: native knowledge retrieval, launcher statically resolved, live readiness untested.

Remove missing-script repair from the plan. Remaining blockers concern owner/bot admission,
non-destructive startup, durable intake, fail-closed grants, restricted tool exposure, native
privacy/capture authority, and separately authorized activation. Do not reinstall or restart
anything to repair a file that is already present.
