# Workflow — Contradiction Resolution

> Scenario: new information contradicts what's already captured in POP. Reconcile without losing history.

## Skill chain
1. `/pop-health` or `/naqd-challenge` — surfaces the contradiction
2. `/naqd-reconcile "<new_info>"` — resolves it
3. MAKHZAN snapshot before any rewrite
4. STRATEGY_LEDGER + EVENT_LEDGER + DECISION_LEDGER appends as appropriate

## When to use
- A NAQD grill produced a revised position that contradicts an earlier QARAR decision.
- A SHURA-emerge surfaced a pattern that conflicts with an existing HIKMAH principle.
- New external evidence (article, conversation, data) contradicts a recorded claim.
- An annual review flags a pillar as no longer relevant.

## The "vault evolves, not grows" principle
When new info conflicts with old notes, POP doesn't blindly append. It *reconciles*. The old position isn't deleted — it's marked superseded, snapshotted, and the canonical view is updated.

## Procedure

### Step 1 — Identify affected notes
Grep POP for references to the disputed claim. List them with `[[wikilinks]]`.

### Step 2 — Snapshot prior state to MAKHZAN
**Before any rewrite**, mirror each affected file to `MAKHZAN__archive/<ISO8601_UTC>/<original-path-mirrored>` with SHA256 in `MANIFEST.json`.

This is non-negotiable. The "vault evolves" principle requires we never silently lose history.

### Step 3 — Decide per affected note
For each affected note:

**Option A — Update**: rewrite the note to reflect the new truth. Increment `updated:` date. Add `## Update <YYYY-MM-DD>` section explaining the change.

**Option B — Append**: if the new info doesn't invalidate the old but adds context, append a section.

**Option C — Mark stale**: the note becomes historical. Frontmatter: `confidence: low`, `superseded_by: "[[new note title]]"`. Leave the body intact for the historical record.

### Step 4 — Write the reconciliation summary
`/naqd-reconcile "<topic>"` creates `NAQD__brain_griller/sessions/{YYYY-MM-DD}__reconcile__<slug>.md` documenting:
- Which notes were affected (with wikilinks)
- The contradicting old vs new
- Decision per note (update / append / mark stale)
- Path to MAKHZAN snapshot
- Reasoning for the resolution

### Step 5 — Ledger appends
- **EVENT_LEDGER**: `{"event":"reconciliation_completed", "affected_notes":[...], "snapshot":"<path>"}`
- **DECISION_LEDGER**: one-line on the resolution rationale, confidence level.
- If the contradiction touches strategy: **STRATEGY_LEDGER** with `event_type: "strategy_belief_revised"`.

### Step 6 — Update orientation files
If the reconciliation changes a foundational claim (e.g., from `SOUL.md` or `CRITICAL_FACTS.md`), update those too. Note the change in `log.md`.

## Anti-patterns
- "Just edit and move on" — silently overwrites history, breaks continuity.
- Marking stale without setting `superseded_by` — orphans the historical context.
- Reconciling under SUKOON red — emotional reconciliation often regrets itself in a week. Defer if not urgent.
- Reconciling without evidence — a feeling that things are different ≠ new information.

## When NOT to reconcile
- The "new info" is actually just a mood shift, not evidence.
- The contradiction is in a brain-dump (TAFRIGH `raw/`) — brain dumps are by-design unfiltered, contradictions inside them aren't a problem to solve.

## Output
- 1 reconciliation session in `NAQD/sessions/`
- 1 MAKHZAN snapshot folder with mirrored files + MANIFEST.json
- Updated frontmatter / body on affected notes
- Multiple ledger appends (EVENT, DECISION, optional STRATEGY)
- Optional updates to SOUL.md / CRITICAL_FACTS.md
