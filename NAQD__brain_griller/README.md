# NAQD — Brain Griller

Arabic: نقد — "critique."

## Purpose
Aggressively stress-test ideas, plans, beliefs before external critique does. **Attack the idea, never the person.** Owns contradiction resolution when new info conflicts with existing POP notes.

## How to use
- `/naqd-grill "<topic>"` — red-team a position. Returns weak points + counterarguments + revised position + confidence score.
- `/naqd-challenge "<claim>"` — argue against the claim using POP's own history.
- `/naqd-reconcile "<new info>"` — resolve contradictions; snapshot to MAKHZAN before rewrites.

## Emotional-state gate
If SUKOON shows a distress / red flag in the last 24 hours, NAQD switches to **Supportive Reflection** mode automatically. Never grills a user in distress.

## Layout
- `sessions/` — markdown per session (filename: `YYYY-MM-DD__grill__topic-slug.md`, etc.). **gitignored**.

## Privacy
**strict_local.**

## Persona
[`NIZAM__system/personas/NAQD.json`](../NIZAM__system/personas/NAQD.json)
