---
name: hikmah-weekly
module: HIKMAH
codename: Khaldun
trigger: "/hikmah-weekly"
window_days: 7
sources:
  - NIZAM__system/ledgers/EVENT_LEDGER.jsonl
  - NIZAM__system/ledgers/LEARNING_LEDGER.jsonl
target_folder: HIKMAH__weekly_synthesis/weekly/
naming_pattern: "{YYYY}-W{WW}.md"
gates: [HIMAYAH, THABAT]
privacy: strict_local
---

## Procedure

1. Read last 7 days of EVENT_LEDGER and LEARNING_LEDGER.
2. Promote patterns with confidence labels (CONFIRMED requires ≥3 events).
3. Flag contradictions for Hazim — do not silently resolve.
4. Write weekly brief to `HIKMAH__weekly_synthesis/weekly/`.
5. Append LEARNING_LEDGER promotions via Ammar/HIMAYAH.
