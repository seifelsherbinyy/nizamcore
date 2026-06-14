# TARIQ Career Radar

## What This Is

A new strategic-intelligence module inside the existing NIZAM system that turns the TARIQ persona into a daily career-and-opportunity research radar for Seif ElSherbiny. Each run researches job/income opportunities, compares them against Seif's profile, estimates salary with evidence and confidence, scores and ranks them, sends a short daily Telegram update, and saves a full evidence report into the correct Google Drive/NIZAM folders with ledger records. It is deliberately a *strategic* intelligence system — improving career position, income, relocation optionality, and long-term positioning — not a basic job-alert scraper.

## Core Value

Every run produces **evidence-backed, scored opportunities** (each with source link, access date, source type, and honest confidence) delivered to Telegram + Drive — never fabricated salaries, never leaked personal data, never silently dropped findings.

## Requirements

### Validated

<!-- Platform capabilities already shipped in NIZAM and RELIED UPON by this module — reused, not rebuilt. Confirmed against codebase map 2026-06-14. -->

- ✓ Telegram delivery: live relay (`relay/poller.py`) + 3 scheduled daily pulses (09:00/15:00/21:00 Cairo) via Hermes cron — existing
- ✓ Google Drive evidence storage: encrypted rclone-crypt ledger mirror + service-account `.docx` records writer (`Records/{lane}/...`) — existing
- ✓ Ledger writing: append-only JSONL ledgers + `governor/ledger_writer.py` — existing
- ✓ Privacy/egress rails: `HIMAYAH__egress_audit`, `PRIVACY_CLASSIFICATION`, `SYNC_POLICY` (strict_local/personal data never leaves), pre-commit leak guard — existing
- ✓ TARIQ persona (long-horizon strategy, `claude-sonnet-4.6`) + IR-1..IR-8 intent router — existing
- ✓ MARSAD flight-radar module (Tahir persona): pluggable-source "radar" pattern with connector-gating + SerpAPI — existing architectural precedent to mirror
- ✓ Greenlit web-research tool (per deployment state) — existing

### Active

<!-- New scope for this milestone (v1). All hypotheses until shipped and validated. -->

**v1 = full-depth radar pipeline, proven on the Remote USD lane only, triggered on-demand.**

- [ ] New Career Radar module wired into NIZAM rails (naming/placement matching NIZAM conventions — final codename is a design decision)
- [ ] Gap report: what NIZAM already has vs what the radar needs (blocker/high/medium/optional)
- [ ] Opportunity data model: title, company, location, remote status, salary, role link, source, source type, access date, fit score, growth score, confidence, tag, next action, profile gap
- [ ] Seif profile seed (role keyword groups + target-role taxonomy) stored privately
- [ ] Remote USD source set, deep: AI-eval/data/AI-ops/coordination roles across platforms (Outlier, DataAnnotation, Toloka, Turing, Upwork, Contra, Braintrust) + remote boards (Remotive, We Work Remotely, Wellfound, RemoteOK) + ATS (Greenhouse/Lever/Ashby/Workable)
- [ ] Researched tooling recommendation (official APIs / company pages / ATS / RSS / saved-search exports preferred before any risky scraping; least-privilege if browser automation is used)
- [ ] Evidence discipline: every opportunity has source link + access date + source type + confidence; every salary tagged employer-posted / estimated / recruiter-stated / guide-based / community-reported; low confidence when unclear (no invented numbers)
- [ ] Duplicate detection + seen-role store (title/company/location/URL normalization) so reruns don't repeat roles
- [ ] Scoring model 0–100 with weights: profile fit 25, salary upside 20, growth 15, visa/remote feasibility 10, company strength 10, referral/application leverage 10, freshness 5, side-income 5; penalties for no-evidence/scam/unclear-pay/severe-mismatch/exploitative-unpaid
- [ ] Opportunity tags: APPLY NOW / REFERRAL FIRST / WATCHLIST / PROFILE GAP / LOW CONFIDENCE / SIDE INCOME / RELOCATION BET / USD CASHFLOW
- [ ] Daily Telegram report (short, action-oriented): best opp, salary insight, main risk/gap, one recommended action
- [ ] Full Drive evidence report (date, run ID, sources searched, new/duplicate counts, top roles, salary evidence + confidence, fit/growth scores, feasibility, company strength, profile gaps, application route, next actions, evidence links, errors/blocked sources, Telegram summary, ledger IDs/paths)
- [ ] On-demand trigger (operator-invoked run) with output review before any unattended scheduling
- [ ] Cross-pillar connection: income → MAL, long-term strategy → TARIQ, weekly action items → MUNAWARA
- [ ] Save-everything-safely guarantee: retry Telegram/Drive on failure, else print full unsaved output + mark run incomplete; never silently drop findings
- [ ] Test pass on a small real source subset (extraction correct, salary confidence not fabricated, dedup works, Telegram readable, Drive saves, ledger written, rerun no-dup, no secret/profile leak)

### Out of Scope

<!-- Explicit boundaries with reasoning. -->

- GCC and Europe lanes — deferred; v1 proves the full pipeline on Remote USD only, then these inherit the proven pattern (later milestone)
- Unattended scheduled cron run — deferred; on-demand + review first, scheduling added once trustworthy
- Auto-applying to jobs / auto-messaging recruiters — never without explicit per-action approval (hard rule)
- Filling forms, using credentials, or submitting personal data — never without explicit approval (hard rule)
- Exposing raw LinkedIn / resume / personal profile data in public files or Telegram — forbidden; sensitive matching stays local/private
- Aggressive scraping of anti-bot-protected job boards — prefer APIs/ATS/RSS/saved-search; least-privilege only if automation is unavoidable
- Deleting/moving/overwriting existing NIZAM files — preserve everything; additive only

## Context

- **Brownfield.** NIZAM is a live, self-hosted Hermes-Agent deployment (VPS `nizam@31.97.154.5`, Paris). Canonical path `D:\NIZAM`. The radar is an additive module on proven Telegram/Drive/ledger/privacy rails — see `.planning/codebase/` (INTEGRATIONS, ARCHITECTURE, STRUCTURE, STACK) for the current map.
- **Persona system.** TARIQ already exists as the long-horizon strategy persona; NAQD (Hazim) supplies red-team/risk reasoning that should briefly explain attractive-but-risky roles.
- **MARSAD precedent.** The flight-radar module already implements the pluggable-source + connector-gating + evidence pattern this radar should mirror for jobs.
- **User profile seed.** Seif ElSherbiny — Cairo/Egypt. Amazon AVS / Brand Specialist / vendor management, PMI AMPlify, field channel planning, omnichannel, customer care, commercial planning, e-commerce, FMCG; SQL, Excel, Power BI, AI/LLM automation, agentic systems, cost optimization. Target roles: Commercial Planner, Vendor/Category Manager, Brand Specialist, Business/Data/BI Analyst, Growth/Revenue Analyst, E-commerce Analyst, AI Operations Specialist, AI Project Coordinator, LLM Evaluator, AI Workflow Consultant. LinkedIn: linkedin.com/in/elsherbiny-19071999 (treat as private seed; manual export only if exact details needed).
- **Privacy is infrastructure, not aspiration.** Existing SYNC_POLICY/HIMAYAH/PRIVACY_CLASSIFICATION already enforce "personal/strict_local never leaves" — the radar must classify its profile-matching data into these tiers rather than reinventing privacy.

## Constraints

- **Process**: Inspect + research before each major tooling/architecture decision; do not assume a specific IDE "mode" — use whatever tools are available.
- **Safety**: No deletion/move/overwrite of existing NIZAM files; verify privacy/recovery/continuity gates before implementation.
- **Privacy**: No raw personal-profile data in public files or Telegram; sensitive matching local/private.
- **Approval gates**: No auto-apply, no recruiter contact, no credential use / form submission without explicit approval.
- **Evidence**: Every opportunity → source link + access date + source type + confidence. Every salary → provenance tag; low confidence if unclear; never invent exact pay.
- **Sourcing**: Prefer official APIs / company pages / ATS pages / RSS / saved-search exports before risky scraping; least-privilege automation only.
- **Tech stack**: Reuse NIZAM stack (stdlib-first relay, rclone-crypt Drive, JSONL ledgers, OpenRouter-routed personas). Pinned/minimal new dependencies; check existing deps + official docs before adding any.
- **Completion bar**: A run is not done until Telegram report + Drive report + ledger record are saved, or the full unsaved output is printed clearly for manual saving.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build as additive module on existing NIZAM rails (not greenfield) | Telegram/Drive/ledger/privacy/persona infra already live and proven | — Pending |
| Mirror the MARSAD radar pattern (pluggable sources + connector-gating) | Proven in-repo precedent for an evidence-driven radar | — Pending |
| v1 = full-depth pipeline on Remote USD lane only | Fastest payoff, no visa gate, lowest legal/anti-bot risk → safest terrain to prove machinery | — Pending |
| On-demand trigger before unattended cron | Live-data + privacy gates warrant human review before automation | — Pending |
| Connect findings to MAL / TARIQ / MUNAWARA | Keeps it strategic intelligence, not generic job alerts | — Pending |

---
*Last updated: 2026-06-14 after initialization*
