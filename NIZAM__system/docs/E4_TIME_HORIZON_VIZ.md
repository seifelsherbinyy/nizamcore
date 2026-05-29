# Time-Horizon Visualization Spec (E4.4 — Phase 2.5)

**Status:** SPEC for Phase 2.5. No implementation in Phase 1.
**Owner:** Tariq commissions; Khaldun assembles; Tahir (MARSAD) overlays external signals.
**Phase gate:** Lands only after the Phase-1 boot loop has produced ≥ 4 quarter cycles of data,
to avoid building a visualization that overfits a 30-day window.

## Goal

Surface NIZAM's strategic-command structure visually so the operator can see, at a glance,
**how today's task ties to the 20-year vision** — and where the doctrine and reality have diverged.

The visualization is the chairman's wall map. It is **read-only by default**; edits happen via the
underlying ledgers, then the map rebuilds.

## What the map shows

Three nested time horizons stacked vertically:

```
[ TARIQ — 10/15/20-year doctrine ]               (top band, slow update)
        │ rolls down to
[ MUNAWARA — 5/3/1-year objectives ]             (middle band, quarterly update)
        │ rolls down to
[ Quarter → Month → Week → Today ]               (bottom band, daily update)
```

Overlaid on the right:

- **MARSAD signals** plotted on a time axis with relevance tags. Color-coded by `SignalKind`.
- **Hayat capacity band** as a thin strip showing recovery debt over the same time axis.
- **Sadiq runway band** plotted similarly.

## Data sources (read-only)

| Layer | Source |
|-------|--------|
| Doctrine (10/15/20-yr) | `TARIQ__long_horizon_strategy/{10_year,15_year,20_year}/**` |
| 5/3/1-yr | `MUNAWARA__tactical_strategy/{5_year,3_year,1_year}/**` |
| Quarter / month / week | `MUNAWARA__tactical_strategy/{quarters,months,weeks}/**` + `BATTLE_LEDGER` |
| Today | `EVENT_LEDGER` last 24 h |
| Doctrine checks | `STRATEGY_LEDGER` `kind=doctrine_check` rows |
| External signals | `MARSAD__flight_radar/briefs/**` + the new generic `signals_to_brief_markdown` output |
| Capacity | `BADAN__body_health_system/quarterly/**` + `body_signal.schema.json` rows |
| Runway | `MAL__financial_engine/quarters/**` |

## Output formats

The visualization is rendered **client-side**, not on the VPS. Two flavors:

1. **Static SVG** at `NIZAM__system/visualizations/horizon_map.svg`, rebuilt by Khaldun after each
   war room. Operator opens locally; no server needed.
2. **Single-page HTML** with vanilla JS for hover-to-cite (each band element opens the source
   markdown). Also generated locally.

Neither variant calls out to the network. Both regenerate deterministically from the ledgers and
folders above.

## Privacy

- The visualization may contain `strict_local` content (e.g., 10-year vision body). It is therefore
  classified `strict_local` and lives outside the framework-tier sync.
- A **sanitized** variant (titles only, no body text) may be published to a `private_github`-tier
  spot for cross-device reference. Generation gated by C2 checkpoint.

## Out of scope

- Edit-in-place. The map is a viewer, not an editor.
- 3D anything. Operator wants legibility, not novelty.
- Drag-to-rearrange. Strategic order is set in the ledgers, not the UI.

## Acceptance

Spec is complete (this document). Implementation lands in Phase 2.5 alongside a small Python
generator at `NIZAM__system/visualizations/horizon_map.py`.
