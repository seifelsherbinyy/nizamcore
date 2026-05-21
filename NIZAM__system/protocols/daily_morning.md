# Protocol — Daily Morning (5–10 min)

> Open the day intentionally. Recovery state → mental clutter → triage → one priority. Order matters.

## Frontmatter
- **Cadence**: every morning
- **Budget**: 5–10 minutes
- **Gates checked**: SUKOON (first), THABAT (each step)
- **Skills chained**: `/sukoon-check` → (optional `/nizam-checkin`) → `/tafrigh-capture` → `/tafrigh-triage`

## Procedure

### Step 1 — `/sukoon-check` (1–2 min)
Log sleep / energy / stress / mood / hydration / caffeine. Color (green / yellow / red) auto-computed.

**If red**: this protocol downshifts. Skip Step 1b and Step 3 (triage). Capture only. Tell yourself: "Today is for recovery, not output."

### Step 1b — `/nizam-checkin` (optional, ~60s; skip if red)
Felt-state + capacity + top pillar vote for the day. Commits SCRIBE JSON to `YAWMIYAT__journaling/sessions/` after operator confirms. Does not replace `/sukoon-check` numeric gate.

### Step 2 — `/tafrigh-capture` (3–5 min)
Brain dump every loose loop. No filtering. No judgment. Write what's on your mind verbatim.

Auto-overload-flag: if obligations > 7 or self-pressure language ("I must…", "I should already…") detected → flag to `SUKOON/overload_flags.jsonl`.

### Step 3 — `/tafrigh-triage` (only if not red) (3–5 min)
Sort items into 6 buckets:
- **Now** — today, ≤ 2 hours, high leverage
- **Next** — this week
- **Later** — parking lot, revisit weekly
- **Delete** — not worth doing
- **Reflect** — route to SHURA or NAQD
- **Escalate** — promise + deadline to a person

### Step 4 — Pick **one** Now item (30 sec)
Out of the Now bucket, pick the single most leveraged item. Defend it as the day's primary battle.

### Step 5 — log mirror (auto)
Each chained skill appends THABAT to `EVENT_LEDGER.jsonl` and mirrors a sanitized one-liner to `log.md`.

## Anti-patterns
- Skipping `/sukoon-check` because "I feel fine" — the gate exists for blind spots.
- Triaging during a red SUKOON state — produces fantasy.
- Picking 3+ "Now" items — that's overload, not prioritization.

## Adjustments by SUKOON state
| State | Adjustment |
|---|---|
| green | Full protocol. |
| yellow | Skip Step 4. Aim for 1–3 Now items, no defended priority. |
| red | Capture only. No triage. No priority pick. Rest is the priority. |
