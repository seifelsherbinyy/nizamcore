# SUKOON — Recovery First

Arabic: سكون — "calm / stillness."

## Purpose
**Recovery-first** is POP's top operating principle. SUKOON tracks daily sleep / energy / stress / mood signals, and its overload flags drive downshift decisions across NAQD, MUNAWARA, and SHURA.

## How to use
- `/sukoon-check` — log today's signals. Auto-determines green / yellow / red and writes to `overload_flags.jsonl` if not green.

## Gate authority
SUKOON gate reads `overload_flags.jsonl` (24h window) to decide whether:
- NAQD switches to Supportive Reflection.
- MUNAWARA auto-cuts weekly battle load 50%.
- SHURA keeps sessions ≤ 20 min.

## Layout
- `signals/YYYY-MM-DD.md` — daily signal entries. **gitignored**.
- `overload_flags.jsonl` — append-only flag stream. **gitignored**.

## Privacy
**strict_local.**

## Color thresholds
- **red**: sleep < 5h OR stress ≥ 8 OR mood ≤ 3 OR energy ≤ 3
- **yellow**: sleep 5–6h OR any single metric in concerning range
- **green**: all metrics healthy
