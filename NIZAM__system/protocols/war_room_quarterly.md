# War Room — Quarterly Strategic Command (E4.1)

**Status:** ACTIVE protocol. Sits inside the `quarterly_close` cadence (`protocols/quarterly_close.md`).
**Owners:** Tariq leads, Khalid runs scenarios, Tahir (MARSAD) supplies intel, Khaldun (HIKMAH)
synthesizes outputs. Hazim (NAQD) is convened only for the red-team round. Operator chairs.
**Cite:** Plan v2 §E4 strategic-command architecture deepening.

## Purpose

NIZAM is a strategic-command architecture, not a task tracker. Every quarter, the system must
**actually convene** as a command. The war room is that convening. It is the moment where the
2-3-year horizon (Tariq), the 4-12-week horizon (Khalid), the external map (MARSAD), and the
operator's lived state (Hayat, Salman) get reconciled into one set of decisions.

## Cadence

- End of each calendar quarter (≈90-day rhythm).
- Budget: ~3 hours real time. The operator may split across two evenings.
- Pre-requisite: `quarterly_close` other steps (`/munawara-quarter-plan` cross-domain
  `/shura-brainstorm`) have already produced raw inputs.

## Phases

### Phase 0 — Pre-read (asynchronous)

| Agent | Produces | Where |
|-------|----------|-------|
| Tariq | "2-3 yr trajectory check" — 1-page note: are we still pointed at the doctrine? | `TARIQ__long_horizon_strategy/reviews/Q*.md` |
| MARSAD (Tahir) | "External map" — 3 best signals from web/news/scholarly adapters (E4.2), capped at 1 page. | `MARSAD__flight_radar/briefs/Q*.md` |
| Khalid | "Tactical scoreboard" — what worked, what stalled, why. | `MUNAWARA__tactical_strategy/quarters/Q*.md#scoreboard` |
| Hayat | "Operator capacity band" — recovery debt, sleep trend, stress signals. | `BADAN__body_health_system/quarterly/Q*.md` |
| Sadiq | "Financial runway delta" — quarter-over-quarter cash, expense, milestone. | `MAL__financial_engine/quarters/Q*.md` |

All five pre-reads must exist before Phase 1. The operator reviews them quietly first.

### Phase 1 — Tariq frames

Operator + Tariq only. Tariq reads the pre-read aloud (literally, into the chat) and asks two
questions:

1. "Is the doctrine still right?" (yes / yes-with-edits / no — pivot)
2. "What did this quarter teach about the 3-year picture?"

Outputs go into `STRATEGY_LEDGER` as `kind: doctrine_check` rows.

### Phase 2 — Khalid stress-tests with MARSAD

Khalid runs each of next quarter's draft objectives through MARSAD's external map:

- For each draft objective, what external signal would invalidate it?
- For each external signal, what objective should we add or kill?

Outputs are `kind: scenario_pair` rows in STRATEGY_LEDGER. One row per (objective, signal) pair.

### Phase 3 — Hazim red-teams

Hazim is convened with the Phase-2 output. He must do exactly two things:

1. Name the **strongest counter** to next quarter's leading objective. One sentence.
2. Flag any pair from Phase 2 that he believes is **overfit to MARSAD's recent inputs**. Two
   sentences max.

Hazim writes a single `kind: red_team_brief` row.

### Phase 4 — Operator decides

The operator picks 3–5 quarter objectives, with explicit acknowledgment of the strongest counter
to each. The decision goes to `DECISION_LEDGER`.

### Phase 5 — Khaldun synthesizes

Khaldun rolls the four prior phases into a single quarter brief (`HIKMAH__weekly_synthesis/quarter/Q*.md`).
The brief contains: doctrine check verdict, top 3 scenario pairs, the strongest counter, and the
final decision. The brief is signed by Khaldun and archived; downstream weekly battles cite it.

### Phase 6 — Action propagation

The operator's `current_focus.rocks` in `user.md` is bumped to the new quarter's objectives. Khalid
emits a `/munawara-weekly-battle` for the first week of the new quarter. War room ends.

## What is OFF-LIMITS in the war room

- Private personal details. Such considerations enter only as the operator's
  own voice.
- New cost commits. No budget approvals during war room. Cost discussion is staged for the next
  `/cost`-tagged review.
- Spontaneous prompt changes. Adopting a new prompt requires a GEPA cycle (E2.7), not a war room.

## Failure modes

- **Pre-read incomplete.** Coordinator refuses to start Phase 1; Khaldun emits an alert listing
  the missing pre-reads.
- **Operator overload.** If SUKOON is red on war room day, the war room is **suspended by default**.
  Operator must explicitly override with `/proceed_anyway`. Phases 1+3 are mandatory; the rest may
  be deferred a week.
- **MARSAD has no fresh signal.** Khalid runs scenarios against the prior quarter's signals; Tahir
  is flagged for a re-spin.

## Acceptance

Protocol is complete (this document) — the next quarterly close runs it for the first time.
Implementation lands incrementally; the doc is the contract.
