---
type: recovery_signal
pop_module: SUKOON
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: high
tags: [recovery]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Daily recovery signal log. Drives the SUKOON gate (red/yellow/green) used by NAQD, MUNAWARA, and SHURA.

## Morning entry (or single-entry of the day)
- Sleep hours (last night):
- Sleep quality (1–10):
- Energy now (1–10):
- Stress now (1–10):
- Mood now (1–10):
- One-line note:

## Optional evening update
- Energy now (1–10):
- Stress now (1–10):
- Mood now (1–10):
- One-line note:

## Auto-determined flag color
- **red** if: sleep < 5h OR stress ≥ 8 OR mood ≤ 3 OR energy ≤ 3
- **yellow** if: sleep 5–6h OR any single metric in concerning range
- **green** otherwise

Flag written to `SUKOON__recovery_first/overload_flags.jsonl` if red or yellow.
