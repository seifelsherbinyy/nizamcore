# Phase 3 live Kiro activation smoke

Owner: contracts/programs/KIRO_WORKSPACE_PERMISSIONS.md. Phase 3 (KWP17).
Observed 2026-09-17, approximately 13:25-13:26 Africa/Cairo.
This adds live evidence to autonomy-verification.md; it does not replace its repository
check results or certify every permission family.

## Procedure and observations

The owner explicitly requested opening Kiro and testing the installed configuration.
Opened the installed Kiro application on NIZAM and created a fresh Default chat.
The Autopilot toggle was visibly enabled. Existing task tabs/work were preserved.

Submitted one bounded request to read scripts/kiro/develop.mjs and the localFile helper
in scripts/kiro/validate.mjs using native tools, then run only these two terminal calls:

1. `npm ls --depth=0`
2. `node scripts/kiro/develop.mjs lint src/lib/money/currency.ts`

The request prohibited edits, installations, additional shell commands, MCP, credentials,
host actions, human gate records, commits/pushes and permission changes.

Observed in Kiro's UI:
- Native script reads completed.
- Both requested commands appeared in separate terminal tool cards rooted at NIZAM.
- Package command emitted the local dependency tree.
- Lint command completed without diagnostic output.
- Kiro reported exit code 0 for each and no approval interruption.
- No approval button was clicked and no follow-up user message was sent.
- Kiro proceeded from reads through commands to a final summary within one request.

The UI grouped the commands as two tool calls. Strict result-dependent scheduling between
those calls was not independently established. This proves a multi-step no-follow-up
smoke workflow, not indefinite autonomous execution or comprehensive approval coverage.

## Independent checks and limits

After the trial, SHA-256 checks against the earlier post-change receipt found no changes
to its 14 listed paths. Native policy still equals the repository template; global policy
still equals its pre-edit backup. No policy modification was needed for this trial.

A targeted search of the new log session did not find the prior-style PolicySession
rebuild line, so no fresh engineActive/fatal log claim is made. Live positive behavior
is the activation evidence. Negative decisions remain supported by earlier synthetic
Cedar tests only; no dangerous command or human gate was exercised live.

No application code or acceptance check changed. Full repository verification was not
rerun for this documentation-only receipt: the earlier observed result remains 19/21,
with dirty-tree AC14/AC15 failures and 3,141 passing application tests.
Kiro was left open on the completed smoke-test chat. Nothing was committed or pushed.


## Sequential continuation trial, 13:31-13:32 Africa/Cairo

Following the owner's "continue", submitted one further bounded verification request
in the same Kiro Autopilot chat. Required native reads first and one command at a time,
with the result inspected before issuing the next. No edits, installs, other commands,
permission changes, MCP, host/credential actions, commits/pushes or human gate work.
Normal build outputs and the tests' isolated synthetic temporary fixtures were permitted.

Observed sequence in the Kiro UI:

1. `node --test scripts/kiro/permissions.test.mjs scripts/kiro/develop.test.mjs`:
   exit 0, 599 tests passed, zero failed/cancelled/skipped.
2. Kiro explicitly reported the test result and "Proceeding to typecheck", then ran
   `npm run typecheck`: exit 0, no diagnostics.
3. Kiro explicitly reported "Typecheck clean, exit 0. Running the build", then ran
   `npm run build`: exit 0, Vite transformed 100 modules and emitted application/PWA
   output. Non-fatal warning: localCache.ts has both static and dynamic imports, so
   the dynamic import does not create a separate chunk. No repair was attempted.
4. Kiro summarized all three results. No intervening user message, approval click,
   approval prompt or blocked-command workaround occurred.

This closes the earlier trial's result-dependent scheduling uncertainty for these three
commands: the agent observed success before selecting/executing the next requested step.
It does not certify indefinite autonomy, automatic repair, every command family, native
reload logs or live enforcement of dangerous-command gates.

Kiro initially raised a possible js-yaml resolution concern after reading the tests,
then corrected it when execution succeeded: js-yaml is available transitively via ESLint.
No dependency was installed or package manifest edited.

Independent post-trial hash comparisons again found all 14 earlier receipt paths
unchanged. Native policy equals the review template; global policy equals its backup.
Only this additive evidence receipt was changed by Aki after those comparisons; its
previous contents were backed up outside the repository. No full acceptance harness was
rerun in this trial. The earlier 19/21 dirty-tree result remains the repository status.
Kiro remains open on the completed sequential trial. No commit or push was performed.
