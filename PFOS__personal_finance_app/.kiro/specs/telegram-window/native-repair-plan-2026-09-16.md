# Authorized native relay repair plan

Authority: Contract 14 TW02-TW07/TW12, sections 10/12, owner instruction on 2026-09-16:
"Show me the repair plan, Repair the native relay and activate". Phase TW1.
This authorizes scoped repair, not relaxed privacy, financial writes, credential lifecycle,
human control record operations, commit/push, or blanket production readiness.

## Ordered implementation and acceptance

1. Preserve native dirty work. Record source fingerprints and require exact match before each
   write. Inspect target tests; do not execute tests that touch actual native ledgers/dedup.
2. Coordinator privacy order: evaluate the existing classification/egress decision before
   _agent_response (which can write memory and invoke Hermes). Blocked response has no content
   artifacts, no model/memory call and no ledger call. Preserve allowed-path response shape.
   Tests: allowed ordering, blocked zero effects, classifier failure zero effects, egress-check
   failure zero effects, model failure no ledger. Use the actual function AST with injected
   mocks, not a duplicate implementation or production imports.
3. Strict Telegram-only owner/private-chat admission before side effects. Wrong sender/chat,
   group, bot, malformed IDs and unsupported update types reach no queue/model/writer. Keep
   legacy assertions; a separately versioned ingress selects the repaired semantics.
4. Durable bot-scoped intake/result/delivery state before offset acknowledgement. Tests must
   cover restart, duplicates, conflicting same-key payloads, execution uncertainty and lost
   send acknowledgements. No second canonical memory/finance writer or deletion of old state.
   Resolve retention authority before storing real bodies; no invented transcript policy.
5. Existing Hermes execution under explicit no-tool request bounds, minimal environment and
   privacy-approved context. Test every retry/summary path and kill gate. Moving a Telegram
   egress check earlier is necessary but not sufficient to authorize model-provider egress.
6. Deploy only the tested selected path. Exactly one Telegram consumer; no automatic webhook
   removal, update dropping or Slack restart/config change. Verify genuine round trip, then
   independently assess VPS/Drive memory. No canned/direct-send substitution for Hermes proof.

## First repair blast radius

Only NIZAM__system/relay/coordinator.py, conditional on its inspected SHA-256 and clean status.
A protected backup outside the native repository precedes atomic replacement. Tests extract
only process(), replacing all dependencies with synthetic functions; no native module import,
provider call, ledger/memory access or service restart. Failed tests abort the write.

The existing native source's three-gate policy values remain unchanged. Explicit owner repair
approval resolves the previously recorded ordering-repair scope blocker, not all deployment
prerequisites. Other files remain untouched until their exact contracts and checks are ready.

## Execution evidence and tooling blocker

- Targeted native git inspection reported coordinator.py, poller.py, auth.py, dedup.py and
  hermes_adapter.py clean. Unrelated native changes were not modified.
- Read three existing native test files as redacted AST plus owner_memory implementation.
  Legacy phase1 tests can reset real dedup state / append actual event-ledger rows; they were
  NOT executed against the live checkout. Actual process() was extracted and all dependencies
  replaced with synthetic mocks to avoid private data and network side effects.
- Reviewed candidate transformer and preflight under the local operator temporary directory.
  Exact original hash required. It relocates the existing _agent_response call after the
  existing egress decision, returning empty artifacts and safe refusal on blocked content.
- Command: python -B ~/.aki/tmp/telegram-window-inspection/run.py
  ~/.aki/tmp/telegram-window-inspection/remote_privacy_repair_preflight.py
  Result: CANDIDATE_TESTED_NOT_APPLIED, original privacy violation reproduced, seven synthetic
  cases passed. Candidate SHA-256:
  bfa2f0261dc1a00120a4b75c3df04896801136535e765c4d3cc7166469ad3e3f.
- Reviewed apply script requires clean target, exact hash, operator ownership, private backup,
  atomic replacement and independent file read-back plus the same seven tests after write.
- Attempted command: python -B ~/.aki/tmp/telegram-window-inspection/run.py
  ~/.aki/tmp/telegram-window-inspection/remote_apply_privacy_repair.py
  TOOL DENIED: "Executing fetched script piped from network source is irreversible."
  No remote execution result returned; repair is NOT established as applied. No workaround,
  alternate execution channel or weaker safety classification was attempted.

Owner repair/activation authorization is already present. The current blocker is execution
policy, not missing owner budget or token. No service restart, poller, paid model call or
activation occurred. Remaining intake/executor repairs were not implemented. A permitted
execution environment is required to continue live repair; do not ask the owner to repeat
credential staging or infer deployment from the successful candidate tests.

Final repository handoff check: `npm.cmd run verify:all -- --all` exited 1 with 19/21
checks passing. Only AC14 (clean working tree) and AC15 (push readiness) failed due to 37
uncommitted entries. Typecheck, lint, tests, build and isolation checks passed. Existing
work was preserved; no acceptance check was weakened. This does not verify native repair
or Telegram activation, both still blocked as described above.
