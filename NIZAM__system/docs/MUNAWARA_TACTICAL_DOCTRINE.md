# MUNAWARA Tactical Doctrine

> Dynamic War Strategy: flexible, maneuverable, opportunistic, progress-tracked. SUKOON-gated.

## Note on naming
MUNAWARA (منورة) literally means "illuminated." It carries a Madinah-honorific overlap. If you prefer strictly secular, rename folder/persona/skills/schema entries to **TADBIR** (تدبير — planning/strategy) — one-line edit across the system.

## The Dynamic War Strategy protocol (`/munawara-weekly-battle`)

Applied every week. Six steps after the SUKOON downshift check:

1. **Exploit opportunity** — What surfaced unplanned? Promote (add as battle) or ignore (park).
2. **Concentrate force** — The single biggest leverage move this week. Defend its time block.
3. **Defend recovery** — What threatens SUKOON? Downshift if amber/red.
4. **Retreat intelligently** — What is failing and should be abandoned without shame? Log a `strategic_retreat` event.
5. **Reallocate resources** — Time / money / attention shifts.
6. **Update objectives** — Quarter / month / week target adjustments with reasoning.

## SUKOON downshift rule

- Count red flags in `SUKOON__recovery_first/overload_flags.jsonl` over last 7 days.
- If ≥ 2 red flags → auto-cut weekly battle load by 50% and append `sukoon_downshift_triggered` to `BATTLE_LEDGER.jsonl`.
- This rule is non-negotiable. Recovery-first overrides tactical ambition.

## Battle ledger

Every battle outcome at week close gets one line in `BATTLE_LEDGER.jsonl`:
- outcome: win / draw / loss / deferred
- evidence (≤280 chars)
- next_maneuver
- recovery_impact: green / yellow / red

## Roll-up enforcement

Every quarter objective must reference a 1-year objective. Every 1-year objective must reference a 3-year. Every 3-year must reference a 5-year. Every 5-year must reference TARIQ 10-year. `/pop-health` audits the chain.

## Anti-patterns

- Running 7+ "battles" per week — overload. Auto-downshift refuses this.
- Same battle on the ledger 4 weeks straight with no movement — escalate via NAQD reconciliation.
- Quarter plans that ignore the 1-year roll-up — pure firefighting.
- Building a tactical plan while SUKOON shows persistent red — fantasy fueled by burnout.
