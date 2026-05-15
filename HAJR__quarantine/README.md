# HAJR — Quarantine

Arabic: حجر — "isolation / quarantine."

## Purpose
Holding pen for files that don't yet belong anywhere else: uncertain classification, sensitive content needing review, malformed entries, or items pending decision.

## Rules
- **Nothing leaves HAJR without explicit triage.**
- Strict-local. Excluded from git in its entirety.
- Routine review: `/pop-health` audit lists HAJR contents weekly and prompts triage.

## Common patterns
- A brain dump that looks like a decision but isn't ready → HAJR.
- A document a third party shared that needs review before classification → HAJR.
- A file with broken frontmatter → HAJR until fixed.

## Privacy
**strict_local.** Entire folder `.gitignored`.
