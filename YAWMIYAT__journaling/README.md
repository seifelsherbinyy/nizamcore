# YAWMIYAT — Journaling

Arabic: يوميات — "diary / journal."

## Purpose

Structured journal — longer-form than TAFRIGH raw dumps. Hosts **NIZAM conversational session records** (canonical JSON) plus optional human-readable mirrors.

Distinct from:

- TAFRIGH brain dumps (unfiltered capture)
- SHURA sessions (topic co-thinking)
- SUKOON signals (numeric recovery gate)

## Layout

| Subfolder | Contents | Privacy |
|---|---|---|
| `sessions/` | Canonical SCRIBE JSON (`conversational_session.schema.json`) | strict_local |
| `mirrors/` | Optional markdown mirrors from template | strict_local |
| `weekly/` | `/nizam-almanac` interpretive weekly reviews | strict_local |
| `daily/` | Future `/yawmiyat-daily` entries | strict_local |
| `monthly/` | Future `/yawmiyat-monthly` closers | strict_local |

## Naming

- Sessions: `sessions/{YYYY-MM-DD}T{HH-MM-SS}Z__{session_type}.json`
- Mirrors: `mirrors/{YYYY-MM-DD}T{HH-MM-SS}Z__{session_type}.md`
- Almanac: `weekly/{YYYY-Wnn}__almanac.md`

## Skills

| Command | Session type |
|---|---|
| `/nizam-checkin` | checkin (~60s daily) |
| `/nizam-counsel` | counseling |
| `/nizam-assess` | assessment |
| `/nizam-consult <topic>` | consultation |
| `/nizam-almanac` | weekly_review (interpretive; complements `/pop-recap`) |

Prompt doctrine: [`NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md`](../NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md)

Persona: [`NIZAM__system/personas/NIZAM.json`](../NIZAM__system/personas/NIZAM.json)

## Privacy

**strict_local** — never committed. See `.gitignore`.
