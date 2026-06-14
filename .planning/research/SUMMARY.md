# Project Research Summary

**Project:** TARIQ Career Radar
**Domain:** Strategic career/income intelligence module (remote-USD job-opportunity radar) on the existing NIZAM platform
**Researched:** 2026-06-14
**Confidence:** HIGH

## Executive Summary

TARIQ Career Radar is a **strategic intelligence system, not a job-alert scraper**. It aggregates remote-USD opportunities from official no-auth ATS APIs (Greenhouse, Lever, Ashby, Workable), public RSS feeds (Remotive, We Work Remotely, RemoteOK), and operator manual imports (Outlier, DataAnnotation, Turing, Toloka, Braintrust, Contra, Wellfound). Each opportunity is deduplicated against a persistent seen-role store, scored 0–100 on a transparent weighted formula, tagged with an action label, and delivered as a short action-oriented Telegram summary plus a full Drive evidence report with ledger records. It is an **additive module on proven NIZAM rails** (Telegram relay, rclone-crypt Drive, JSONL ledgers, HIMAYAH/SYNC_POLICY privacy, TARIQ persona) and mirrors the existing MARSAD flight-radar pattern.

The recommended build approach is **simplest-safe-first sourcing**: Tier 1 public ATS APIs + Tier 2 RSS cover ~70%+ of the target market with zero ToS/anti-bot risk; Tier 3 is operator manual import for the AI-data platforms; Tier 4 browser automation (Playwright/Apify) is deferred. Only **one new pinned dependency is justified** — `rapidfuzz==3.14.0` for fuzzy dedup (100× faster than deprecated FuzzyWuzzy). v1 is **on-demand trigger only**, human-reviewed, with unattended cron deferred until ≥10 clean validation runs.

The dominant risks are domain-specific and have concrete mitigations: fabricated/over-confident salaries (provenance + confidence discipline, ranges only), ToS/scraping violations (API-first), dedup failures (normalized seen-store), privacy leakage of raw profile data (strict_local profile, scores-only egress), scam/exploitative AI-eval platforms (platform tier system), over-automation before trust (all-or-nothing completion contract + validation gate), generic-advice drift (charter clarity), and LLM scoring inconsistency/prompt-injection (deterministic base scoring, LLM as explainer-only on structured fields).

## Key Findings

### Recommended Stack

Reuse the NIZAM stack (stdlib-first Python, OpenRouter-routed personas, rclone-crypt Drive, JSONL ledgers). Add the minimum. See [STACK.md](STACK.md) for full version/rationale detail.

**Core technologies:**
- **Tier 1 public ATS APIs** (Greenhouse `/v1/boards/{id}/jobs`, Lever `/v0/postings/{id}`, Ashby public posting API, Workable) — no auth, designed for job boards, zero ToS ambiguity, ~50 LOC/connector
- **Tier 2 RSS/feeds** (Remotive API, We Work Remotely RSS, RemoteOK) — parsed with stdlib `xml.etree.ElementTree` (no `feedparser` dependency)
- **Tier 3 manual import** (Outlier, DataAnnotation, Turing, Toloka, Braintrust, Contra, Wellfound) — operator copy/paste → JSONL; safest entry, no scraping/credentials
- **`rapidfuzz==3.14.0`** — NEW, justified: fuzzy title dedup (`token_sort_ratio` ≥ 0.88), 100× FuzzyWuzzy
- **`sqlite3` + `json` (stdlib)** — seen-role store + JSONL ledgers, no new dependency
- **Reused, already pinned:** `requests`, `beautifulsoup4`, `lxml`, `python-dateutil`
- **Explicitly excluded:** Scrapy, Selenium, feedparser, pandas, APScheduler (Hermes owns cron); `playwright`/`toloka-kit` deferred to a later phase

### Expected Features

See [FEATURES.md](FEATURES.md). The line between "strategic intelligence" and "basic scraper" is evidence discipline + multi-dimensional ranking + human-gated safety.

**Must have (table stakes):**
- Multi-source aggregation (≥5 sources) with evidence discipline (source link + access date + source type on every opportunity)
- Salary with provenance tag (employer-posted / recruiter-stated / guide-based / community-reported / estimated) + confidence; never fabricated; low-confidence flagged
- Duplicate detection (zero repeats across runs) via persistent seen-store
- Transparent 0–100 scoring (fit 25, salary upside 20, growth 15, visa/remote 10, company 10, referral 10, freshness 5, side-income 5) + penalties
- 8 action tags: APPLY NOW / REFERRAL FIRST / WATCHLIST / PROFILE GAP / LOW CONFIDENCE / SIDE INCOME / RELOCATION BET / USD CASHFLOW
- Short Telegram report + full Drive evidence report + append-only ledger run history
- On-demand trigger with operator review; local-only profile seed; privacy rails enforced

**Should have (competitive differentiators):**
- Salary-upside & company-strength scoring; referral/leverage mapping; NAQD red-team risk note; side-income detection; visa/remote feasibility deep-dive
- Cross-pillar routing (income → MAL, strategy → TARIQ, weekly actions → MUNAWARA)

**Defer / anti-features (explicitly NOT build):**
- Auto-apply, auto-contact recruiters, form-filling/credential use (hard rules)
- Fabricated salaries; raw LinkedIn/resume/profile in Telegram or Drive
- Unattended cron before validation; scraping anti-bot-protected boards; real-time alert streaming; predictive success scoring; generic career advice

### Architecture Approach

See [ARCHITECTURE.md](ARCHITECTURE.md). Module lives at `TARIQ__career_radar/` (mirrors NIZAM naming; a specialized feed into TARIQ, not a new persona). It implements a 7-stage pipeline expanded from MARSAD's 4-stage pattern. Zero new credentials/personas/gates beyond source API keys; integrates onto existing Telegram/Drive/ledger/privacy by adding path rules + one ledger registration.

**Major components (pipeline stages):**
1. **Fetch** — pluggable sources → normalized opportunity records
2. **Dedup** — seen-role store (SQLite/JSONL), normalized key (URL + company + title + location)
3. **Enrich** — local profile matcher (fit) + deterministic scoring engine (0–100) + salary provenance tagging
4. **Tag** — assign action labels from scores + gaps
5. **Report** — build Telegram summary + Drive evidence document
6. **Deliver** — existing relay (Telegram) + google_adapter (Drive) + ledger_writer (append)
7. **Continuity** — retry ladder; on failure print full unsaved output + mark run incomplete; never silently drop

**Privacy tiers (mapped onto existing classification):** profile seed = `strict_local`/`strict_local_maximum` (never leaves); opportunity records = `strict_local` (local + ciphertext Drive mirror); Telegram = `personal` (operator egress, no personal context); Drive report + ledger = review-before-commit. New path rules only, no new classification scheme.

### Critical Pitfalls

Top items from [PITFALLS.md](PITFALLS.md):

1. **Fabricated / over-confident salary** — every salary tagged with source_type + confidence + link; ranges not point estimates; LLM restricted to tagged evidence; cap confidence when only community/anonymous sources.
2. **ToS / legal / anti-bot scraping violations** — API-first (Tier 1 ATS + Tier 2 RSS); respect robots.txt; least-privilege; defer browser automation; graceful degradation when a source blocks.
3. **Dedup failures (same role every run)** — persistent normalized seen-store + multi-signal + fuzzy match + freshness heuristic (repost >30 days = new).
4. **Privacy leakage of raw profile** — profile strict_local; matching runs local; egress is scores/tags only; pre-commit PII scan.
5. **Scam / exploitative AI-eval platforms** — platform TIER system (trust/caution/avoid), unpaid-screening detection, ⚠ tags, user feedback loop.
6. **Over-automation before trust** — all-or-nothing completion contract (Telegram+Drive+ledger together or print unsaved), ≥10 validation runs + explicit sign-off before cron.
7. **Drift into generic advice** — charter clarity; Telegram = best opp + salary + risk + next action only; long-term guidance handled by MAL/TARIQ/MUNAWARA.
8. **LLM scoring inconsistency / injection** — deterministic base scoring (not LLM); LLM as explainer-only; extract structured fields only (never concatenate raw job text into scoring prompt); same data → same score.

## Implications for Roadmap

Research suggests this build order. The four researchers used different phase numberings/timeboxes; the **unified view below is a starting point** — the roadmapper owns final slicing (config granularity = **fine**, so expect more, smaller phases than the 5-week blocks below).

### Phase 1: Foundation & data model
**Rationale:** Everything depends on the opportunity schema, config/constraints, and the seen-role store.
**Delivers:** opportunity record schema, profile seed (local), seen-role store, config/constraints, ledger registration.
**Addresses:** evidence-discipline + privacy data-model table stakes.
**Avoids:** dedup failure, privacy leakage (designed in from the start).

### Phase 2: Sourcing (Tier 1 + Tier 2 + manual)
**Rationale:** API-first sourcing is the safe backbone; prove fetch+normalize before enrichment.
**Delivers:** Greenhouse/Lever/Ashby/Workable connectors, RSS connectors, manual-import path, normalization.
**Uses:** stdlib HTTP/XML + `requests`; no scraping.
**Avoids:** ToS/anti-bot pitfall.

### Phase 3: Dedup engine
**Rationale:** Must work before delivery or reruns spam repeats.
**Delivers:** normalization + `rapidfuzz` fuzzy matching + persistent store; rerun-no-dup guarantee.

### Phase 4: Scoring, salary provenance & tagging
**Rationale:** Deterministic scoring + salary discipline are the credibility core.
**Delivers:** 0–100 weighted scorer + penalties, salary provenance/confidence tagger, 8 action tags, local profile matcher.
**Avoids:** salary fabrication, LLM scoring inconsistency.

### Phase 5: Reports & delivery (Telegram + Drive + ledger)
**Rationale:** Close the loop to operator value with the completion contract.
**Delivers:** Telegram summary, Drive evidence report, ledger append, retry-or-print continuity.
**Avoids:** silent-drop / partial-publish.

### Phase 6: On-demand trigger & end-to-end wiring
**Rationale:** Operator-invoked run through the relay/router/TARIQ persona, full pipeline.
**Delivers:** `/tariq-career-radar-run` command path, cron seam (inactive), NIZAM registration.

### Phase 7: Validation & safety sign-off
**Rationale:** Prove trust before any automation; the brief's Step 9 test bar.
**Delivers:** small-subset test runs, salary-not-fabricated audit, dedup verification, privacy/leak scan, rerun-no-dup, readability checks; operator sign-off.
**Avoids:** over-automation pitfall.

### Deferred (out of v1, future milestones)
GCC + Europe lanes; unattended cron; company-strength/referral/visa deep-dives; browser automation; cross-pillar routing maturity.

### Phase Ordering Rationale
- Schema/store before sourcing before dedup before scoring before delivery — strict data-dependency chain.
- Validation last and explicit, because on-demand-then-cron is a core safety decision.
- Cross-pillar + automation deferred so v1 ships a trustworthy single-lane pipeline first.

### Research Flags

Phases likely needing deeper research during planning:
- **Sourcing phase:** Outlier/DataAnnotation/Turing/Upwork/Wellfound/Braintrust API availability (MEDIUM) — fallback to manual JSONL import.
- **Reports phase:** confirm existing `google_adapter` `.docx`/Drive write path supports the evidence-report shape (verify, don't assume).
- **Scoring phase:** salary-confidence operationalization heuristics; weight calibration on 10–20 real roles (MEDIUM).

Phases with standard patterns (can skip deep research):
- **Dedup, ledger, Telegram delivery, privacy classification** — MARSAD/NIZAM precedents are established; RapidFuzz documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Tier 1 ATS APIs + Tier 2 RSS verified against official docs; RapidFuzz benchmarked; stdlib-first reduces risk |
| Features | HIGH | Table-stakes/differentiators/anti-features clearly delineated; anti-features encode the hard rules |
| Architecture | HIGH | MARSAD precedent; clear stage boundaries; reuses existing rails; privacy tiers map to existing scheme |
| Pitfalls | MEDIUM-HIGH | 8 pitfalls with prevention + phase mapping; real-world validation needed in the validation phase |

**Overall confidence:** HIGH

### Gaps to Address
- **Platform API availability** (Outlier/Turing/Wellfound/Braintrust/Upwork): confirm during the sourcing phase; manual import is the guaranteed fallback.
- **Scoring-weight calibration:** weights are educated defaults; tune against real roles during validation.
- **Drive evidence-report format:** verify the existing google_adapter write path before building the reporter.

## Sources

### Primary (HIGH confidence)
- Greenhouse / Lever / Ashby / Workable official job-board API docs — public no-auth endpoints
- Remotive / We Work Remotely / RemoteOK feed docs — public RSS/API
- RapidFuzz (PyPI) — fuzzy-matching performance + API
- NIZAM `.planning/codebase/` map (INTEGRATIONS, ARCHITECTURE, STRUCTURE, STACK) — existing rails

### Secondary (MEDIUM confidence)
- Upwork GraphQL API docs (OAuth flow needs a test run)
- Levels.fyi / Glassdoor / PayScale — salary evidence (ToS-sensitive; gray-zone)
- 2026 web-scraping legal/anti-bot risk write-ups

### Tertiary (LOW confidence)
- Community salary reports (TeamBlind-style) — weak supporting evidence only, tag low confidence

---
*Research completed: 2026-06-14*
*Ready for roadmap: yes*
