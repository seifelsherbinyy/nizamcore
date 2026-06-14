# TARIQ Career Radar

Career opportunity radar — Remote USD lane. Fetches, deduplicates, scores,
and delivers evidence-backed opportunity intelligence for Seif's job search.

The module integrates with the NIZAM pipeline: sourcing connectors pull
opportunities from Tier-1 ATSes (Greenhouse, Lever, Ashby, Workable) and
Tier-2 RSS/manual feeds, deduplicates across runs via a persistent SQLite
store, scores each opportunity with a deterministic 0-100 weighted algorithm,
and delivers a concise action-oriented summary to Telegram and a full evidence
report to Google Drive — with zero fabricated salaries, zero raw profile data
in any egress path, and zero silent drops.

## Quick start

```bash
python -m radar.main
```

> Phase 1 stub: returns a scaffold message.
> Full pipeline is wired in Phase 11 (RUN-01/RUN-02).

## Privacy

| Data element | Classification | Storage |
|---|---|---|
| `data/profile_cache.json` | `strict_local_maximum` | Never leaves disk; local matching only |
| `data/seen_roles.sqlite` | `strict_local` | Local dedup index; no egress |
| `data/opportunities.jsonl` | `strict_local` | Local store; encrypted Drive mirror only |
| Code/config | `private_github` | Committed; no secrets |

The `data/` directory is gitignored entirely. Never commit files under `data/`.
