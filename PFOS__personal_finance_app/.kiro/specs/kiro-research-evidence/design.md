# Kiro research evidence design

Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research phase 2.

Add phase-2.md, phase-2-evidence.json and phase-2-verification.md beneath the existing
operational-excellence folder. Preserve earlier artifacts as historical phase records.
The JSON is a research index, not a second execution ledger or native Kiro configuration.

Use a pure validateResearch(value) function plus a small fixed-path CLI adapter in
scripts/kiro/research.mjs. Reuse localFile and ROOT from validate.mjs, so path/junction
rules are not independently reimplemented. Bound input to 2 MB before reading.
Errors are fixed identifiers without source text, paths or exception payloads.

Schema version 1 has authority, phase, sources and candidates. Source IDs are unique;
URLs allow public GitHub/raw GitHub HTTPS only, without credentials/query/fragment.
Each source has repository identity, kind, timestamp, SHA-256 and a bounded exact
excerpt/locator. Full snapshots remain outside the repository; hashes identify those
snapshots, but the offline validator cannot prove that an excerpt came from one.
Candidate citations must resolve to a source for that repository. Candidate execution
is NOT_RUN and Kiro activation NOT_TESTED; this discovery schema cannot encode a
runtime pass. Existing installed-tool trials remain in their original evidence record.

All A-Q domains must have a candidate with evidence. A retrieved README alone remains
SCREENED. ASSESSED means a bounded design comparison, not phase-3 eligibility or a full
source/security audit. UNRESOLVED means source access failed, not repository absence.
The report, not a numeric score, decides which findings warrant local execution.

Tests follow existing node:test patterns: cloned synthetic objects, hardcoded expected
refusals, injected roots for missing/malformed/oversize/junction inputs, and subprocess
CLI exit assertions. No fixtures under src or tests; no application imports, no added
package scripts or acceptance-harness edits. Remove only new owned files by reviewed
inverse after checking for later changes; never restore baseline files wholesale.
