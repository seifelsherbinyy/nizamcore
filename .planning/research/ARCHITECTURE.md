# Architecture: Career Radar Module (TARIQ Career Intelligence)

**Domain:** Strategic career opportunity research and scoring  
**Researched:** 2026-06-14  
**Pattern:** Mirrored from MARSAD__flight_radar pipeline (pluggable sources, connector-gating, append-only records)

---

## Recommended Folder Structure

**Module naming pattern (NIZAM convention):**  
`TARIQ__career_radar/` — "TARIQ" is the existing long-horizon strategy persona; appending "career" domain clarifies this is the career opportunity radar submodule under TARIQ's remit.

**Directory tree:**

```
TARIQ__career_radar/
├── README.md                          # Module overview + quick start
├── _index.json                        # Self-registration to NIZAM_MASTER_REGISTER
├── .env.example                       # Env var documentation (committed, no secrets)
├── requirements.txt                   # Python dependencies
├── conftest.py                        # Shared pytest config
│
├── radar/                             # Core pipeline (mirrors MARSAD structure)
│   ├── __init__.py
│   ├── main.py                        # Entry point: CLI + scheduler bootstrap
│   ├── config.py                      # All env vars & constants loaded here
│   ├── constraints.py                 # REMOTE USD lane constraints (extensible for GCC/EU later)
│   ├── opportunity_store.py           # Append-only JSONL store writer (write-to-temp-then-rename)
│   ├── dedup_engine.py                # Seen-role store + normalization logic
│   ├── profile_matcher.py             # Seif profile matching + gap detection
│   ├── scoring_engine.py              # 0–100 opportunity score + model weights
│   │
│   ├── sources/                       # Pluggable source adapters
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract source interface + rate-limit shared logic
│   │   ├── outlier_source.py          # Outlier Ai Jobs API
│   │   ├── dataannotation_source.py   # DataAnnotation Board (web + API)
│   │   ├── turing_source.py           # Turing.com (web + API)
│   │   ├── upwork_source.py           # Upwork RSS + API
│   │   ├── remotive_source.py         # Remotive.io RSS + Job API
│   │   ├── wellfound_source.py        # Wellfound (YC Startups) API
│   │   ├── generic_board_source.py    # Generic job board (We Work Remotely, RemoteOK, etc.)
│   │   └── ats_source.py              # ATS endpoints (Greenhouse, Lever, Ashby, Workable)
│   │
│   ├── stages/                        # Operational pipeline stages
│   │   ├── __init__.py
│   │   ├── fetch.py                   # Stage 1: Source fetching + raw normalization
│   │   ├── dedup.py                   # Stage 2: Duplicate detection via seen-role store
│   │   ├── enrich.py                  # Stage 3: Profile matching, fit/growth score, confidence
│   │   ├── tag.py                     # Stage 4: Tag assignment (APPLY NOW, REFERRAL, etc.)
│   │   ├── report.py                  # Stage 5: Report building (Telegram + Drive artifacts)
│   │   ├── deliver.py                 # Stage 6: Telegram + Drive delivery + ledger append
│   │   └── continuity.py              # Stage 7: Failure handling + unsaved output fallback
│   │
│   └── scheduler.py                   # APScheduler for Hermes cron (added Phase 2)
│
├── data/                              # Data store (strict_local — never committed)
│   ├── opportunities.jsonl            # Append-only master record store
│   ├── opportunities.tmp              # In-flight write buffer (deleted after rename)
│   ├── seen_roles.json                # Dedup index: {normalized_key → [opportunity_ids]}
│   ├── profile_cache.json             # Seif profile seed (strict_local_maximum)
│   └── backups/
│       └── YYYY-MM-DDTHH-MM-SSZ.jsonl # Daily snapshot before run
│
├── reports/                           # Report artifacts (mixed privacy)
│   ├── telegram_summaries/            # Short Telegram summaries (personal → Telegram)
│   ├── drive_reports/                 # Full evidence reports (.docx + links)
│   └── ledger_links/                  # Mapping report_id → ledger_id
│
└── tests/
    ├── __init__.py
    ├── test_constraints.py
    ├── test_dedup_engine.py
    ├── test_profile_matcher.py
    ├── test_scoring_engine.py
    ├── test_opportunity_store.py
    └── test_sources.py

NIZAM__system/
├── schemas/
│   └── career_opportunity_record.schema.json  # NEW: Opportunity record contract
│
└── skills/
    ├── tariq-career-radar-fetch.md            # NEW: Fetch stage
    ├── tariq-career-radar-dedup.md            # NEW: Dedup stage
    ├── tariq-career-radar-enrich.md           # NEW: Scoring + matching
    ├── tariq-career-radar-tag.md              # NEW: Tagging stage
    ├── tariq-career-radar-report.md           # NEW: Report generation
    └── tariq-career-radar-deliver.md          # NEW: Telegram + Drive delivery
```

---

## Component Boundaries & Data Flow

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Career Radar Pipeline (TARIQ__career_radar)                      │
└─────────────────────────────────────────────────────────────────┘

STAGE 1: FETCH
  Sources (Outlier, DataAnnotation, Turing, Upwork, Remotive, etc.)
    ↓ (raw_opportunities)
  fetch.py → normalize job title/company/location/salary
    ↓ (normalized_opportunities)

STAGE 2: DEDUP
  dedup_engine.py → check seen_roles.json for (title/company/location) signature
    ├─ NEW: add to opportunities.jsonl + update seen_roles
    └─ SEEN: skip (return duplicate marker)
    ↓ (deduplicated_batch)

STAGE 3: ENRICH
  enrich.py
    ├─ profile_matcher.py → compare against Seif profile (strict_local_maximum)
    │   ├─ Role keyword match → fit_score (0–100)
    │   ├─ Growth potential → growth_score (0–100)
    │   └─ Gap summary → profile_gap (skill/cert/visa constraints)
    │
    ├─ salary evidence classification
    │   ├─ employer-posted / recruiter-stated / guide-based / community-reported / estimated
    │   └─ confidence: HIGH/MEDIUM/LOW
    │
    └─ secondary signals
        ├─ company strength (Crunchbase / public signals)
        ├─ visa/remote feasibility (role attributes)
        └─ freshness (days since posting)
    ↓ (scored_opportunities)

STAGE 4: TAG
  tag.py → assign tags based on scores + fit + gaps
    • APPLY NOW        (fit ≥ 70, growth ≥ 60, salary evidence clear, no visa blocker)
    • REFERRAL FIRST   (referral leverage available + fit ≥ 60)
    • WATCHLIST        (interesting but gaps or low confidence)
    • PROFILE GAP      (strong role but missing cert/visa/skill)
    • LOW CONFIDENCE   (salary/fit unclear; insufficient evidence)
    • SIDE INCOME      (part-time / gig income supplement)
    • RELOCATION BET   (non-remote requiring relocation decision)
    • USD CASHFLOW     (explicitly tracked for income strategy)
    ↓ (tagged_opportunities)

STAGE 5: REPORT
  report.py → build two report artifacts
    ├─ TELEGRAM (short, action-oriented)
    │   ├─ Best 1–3 opps (ranked by fit_score + salary)
    │   ├─ Salary insight summary (range + confidence notes)
    │   ├─ Main risk/gap (if any)
    │   └─ One recommended action
    │
    └─ DRIVE (full evidence document)
        ├─ Run metadata (date, run_id, lane, sources searched)
        ├─ New/duplicate counts
        ├─ Top 10 ranked opportunities (full record)
        ├─ Salary evidence breakdown (confidence + provenance)
        ├─ Feasibility analysis (visa, remote, timeline)
        ├─ Company strength notes (where available)
        ├─ Application strategy (how to apply, where to apply first)
        ├─ Profile gaps (skills/certs to close)
        ├─ Error/blocked sources log
        └─ Evidence links (source URLs + access dates)
    ↓ (report_artifacts)

STAGE 6: DELIVER
  deliver.py → write to Telegram + Drive + ledger
    ├─ Telegram (via existing relay/poller.py → tg_send_message())
    │   └─ format_telegram_report() → send(reply_text, chat_id)
    │
    ├─ Drive (via existing google_adapter.py → service_account)
    │   ├─ .docx to Records/TARIQ/ (template + markdown conversion)
    │   └─ Metadata row to Drive (note_id, report_date, lane, opp_count)
    │
    └─ Ledger append (via existing ledger_writer.py)
        └─ CAREER_RADAR_LEDGER.jsonl row
            {
              "ts": "2026-06-14T09:00:00Z",
              "module": "TARIQ__career_radar",
              "event_type": "run_complete",
              "run_id": "<uuid>",
              "lane": "Remote USD",
              "opportunities_fetched": 145,
              "opportunities_new": 12,
              "opportunities_seen": 133,
              "top_fit_score": 87,
              "telegram_sent": true,
              "drive_docx_id": "doc_xxx",
              "drive_metadata_url": "https://...",
              "errors": []
            }
    ↓

STAGE 7: CONTINUITY (Error handling)
  continuity.py
    ├─ Telegram delivery failed
    │   └─ Retry ladder: 1s → 4s → 16s (max 3 attempts)
    │   └─ If all fail: log to DEAD_LETTER.jsonl + print full output to operator
    │
    ├─ Drive delivery failed
    │   └─ Retry ladder: 1s → 4s → 16s (max 3 attempts)
    │   └─ If all fail: log to DEAD_LETTER.jsonl + print full output to operator
    │
    ├─ Ledger append failed
    │   └─ Halt; do not mark run complete; print full record to stdout
    │
    └─ Mark run incomplete in ledger
        └─ Next run detects incomplete flag + alerts operator

CROSS-PILLAR ROUTING (Post-delivery)
  On successful deliver:
    ├─ Income findings → MAL__financial_engine (import opportunities.jsonl for salary modeling)
    ├─ Career strategy → TARIQ__long_horizon_strategy (update 10/15-yr positioning)
    └─ Action items → MUNAWARA__tactical_strategy (weekly action tasks from APPLY NOW tags)
```

---

## Opportunity Record Schema

**File:** `NIZAM__system/schemas/career_opportunity_record.schema.json` (new)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://pop.local/schemas/career_opportunity_record.schema.json",
  "title": "Career Opportunity Record (TARIQ Career Radar)",
  "description": "Individual job opportunity record with scoring, matching, and evidence fields.",
  "type": "object",
  "required": [
    "opportunity_id", "title", "company", "location", "remote_status",
    "source", "source_type", "source_url", "access_date",
    "fit_score", "growth_score", "confidence", "tags",
    "salary_usd_low", "salary_usd_high", "salary_evidence_type", "salary_confidence",
    "observed_at", "lane", "data_quality"
  ],
  "properties": {
    "opportunity_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this opportunity record"
    },
    "title": {
      "type": "string",
      "description": "Job title (normalized; e.g. 'AI Operations Manager')"
    },
    "company": {
      "type": "string",
      "description": "Company name (normalized; e.g. 'Outlier.ai')"
    },
    "location": {
      "type": "string",
      "description": "Primary work location (normalized; 'Remote', 'Cairo, Egypt', 'Mountain View, CA', etc.)"
    },
    "remote_status": {
      "type": "string",
      "enum": ["fully_remote", "hybrid_remote_preferred", "hybrid_onsite_required", "onsite_only"],
      "description": "Remote work status classification"
    },
    "role_category": {
      "type": "string",
      "description": "Normalized role category (e.g. 'AI_OPERATIONS', 'DATA_ANALYST', 'BRAND_SPECIALIST')",
      "enum": [
        "AI_OPERATIONS", "AI_RESEARCH", "LLM_EVALUATION", "DATA_SCIENCE",
        "DATA_ANNOTATION", "BUSINESS_ANALYST", "COMMERCIAL_PLANNING",
        "VENDOR_MANAGEMENT", "CATEGORY_MANAGEMENT", "E_COMMERCE",
        "GROWTH_ANALYST", "BI_ANALYST", "PROJECT_COORDINATOR"
      ]
    },
    "source": {
      "type": "string",
      "description": "Source name (e.g. 'outlier', 'dataannotation', 'turing', 'upwork', 'remotive', 'wellfound')"
    },
    "source_type": {
      "type": "string",
      "enum": ["api", "rss_feed", "web_scrape", "job_board", "ats", "manual"],
      "description": "How the opportunity was sourced"
    },
    "source_url": {
      "type": "string",
      "format": "uri",
      "description": "Direct link to the job posting (for reference + evidence)"
    },
    "access_date": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp when the posting was accessed"
    },
    "salary_usd_low": {
      "type": ["number", "null"],
      "minimum": 0,
      "description": "Salary range low in USD (null if not disclosed)"
    },
    "salary_usd_high": {
      "type": ["number", "null"],
      "minimum": 0,
      "description": "Salary range high in USD (null if not disclosed)"
    },
    "salary_usd_annual": {
      "type": ["number", "null"],
      "description": "Annual equivalent if hourly rate was provided"
    },
    "salary_evidence_type": {
      "type": "string",
      "enum": [
        "employer_posted",       # On official job board, verified by source
        "recruiter_stated",      # Recruiter / LinkedIn stated (less reliable)
        "guide_based",           # Market guide / Glassdoor / Payscale estimation
        "community_reported",    # Community reports / anonymous surveys
        "estimated",             # Inferred from role/level/company
        "not_disclosed"          # No evidence at all
      ],
      "description": "Provenance of salary data"
    },
    "salary_confidence": {
      "type": "string",
      "enum": ["HIGH", "MEDIUM", "LOW"],
      "description": "Confidence in salary accuracy"
    },
    "fit_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Profile fit score based on role keyword match + required skills"
    },
    "growth_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Growth potential score based on role leverage + company + skill development"
    },
    "company_strength_signal": {
      "type": ["string", "null"],
      "enum": ["strong_tier1", "strong_tier2", "emerging", "unknown", null],
      "description": "Company stability signal (where available)"
    },
    "visa_feasibility": {
      "type": "string",
      "enum": ["visa_sponsored_likely", "visa_sponsored_unclear", "visa_not_sponsored", "not_applicable"],
      "description": "Visa sponsorship feasibility for Egyptian applicant"
    },
    "confidence": {
      "type": "string",
      "enum": ["HIGH", "MEDIUM", "LOW"],
      "description": "Overall confidence in opportunity record (fit + salary + data quality)"
    },
    "profile_gap": {
      "type": ["object", "null"],
      "description": "Gap analysis vs Seif profile",
      "properties": {
        "missing_skills": { "type": "array", "items": { "type": "string" } },
        "required_cert": { "type": ["string", "null"] },
        "visa_constraint": { "type": ["string", "null"] },
        "summary": { "type": "string" }
      }
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "APPLY_NOW",
          "REFERRAL_FIRST",
          "WATCHLIST",
          "PROFILE_GAP",
          "LOW_CONFIDENCE",
          "SIDE_INCOME",
          "RELOCATION_BET",
          "USD_CASHFLOW"
        ]
      },
      "description": "Action tags assigned by tagging engine"
    },
    "next_action": {
      "type": ["string", "null"],
      "description": "Suggested next step (e.g. 'Apply directly via Outlier', 'Contact recruiter', 'Build cert X')"
    },
    "lane": {
      "type": "string",
      "enum": ["Remote USD", "GCC", "Europe"],
      "description": "Career lane / geographic focus"
    },
    "observed_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp when this record was created/observed"
    },
    "run_id": {
      "type": "string",
      "format": "uuid",
      "description": "Identifies which radar run created this record"
    },
    "is_duplicate_of": {
      "type": ["string", "null"],
      "format": "uuid",
      "description": "Opportunity ID of the earlier record if this is a duplicate (for tracking)"
    },
    "data_quality": {
      "type": "string",
      "enum": ["confirmed", "estimated", "partial"],
      "description": "confirmed: all fields from API; partial: missing salary/company info; estimated: inferred"
    },
    "notes": {
      "type": ["string", "null"],
      "description": "Free-form notes from profile matching or manual review"
    }
  }
}
```

---

## Seen-Role Store Design (Dedup)

**File:** `TARIQ__career_radar/data/seen_roles.json`

**Purpose:** Prevent duplicate opportunities on reruns; identify when the same role reappears (potentially changed).

**Normalization key:**

```python
def normalize_role_key(opportunity: dict) -> str:
    """
    Create a stable, case-insensitive key for dedup.
    Multiple sources may post the same role differently.
    """
    # Normalize title, company, location, and URL (if stable)
    title_norm = opportunity['title'].lower().strip()
    company_norm = opportunity['company'].lower().strip()
    location_norm = opportunity['location'].lower().strip()
    
    # Extract domain from URL for stability (most reliable unique identifier)
    url = opportunity['source_url']
    url_domain = urlparse(url).netloc
    
    # Create key: {domain}:{company}:{title}:{location}
    # This allows the same role to appear in multiple sources but only once per source
    key = f"{url_domain}:{company_norm}:{title_norm}:{location_norm}"
    
    return hashlib.sha256(key.encode()).hexdigest()[:16]
```

**Store structure:**

```json
{
  "version": "1.0",
  "updated_at": "2026-06-14T09:00:00Z",
  "total_seen": 1847,
  "by_normalization_key": {
    "abc123def456": {
      "first_seen": "2026-05-15T10:30:00Z",
      "last_seen": "2026-06-14T09:00:00Z",
      "opportunity_ids": ["uuid1", "uuid2"],
      "sources": ["outlier", "upwork"],
      "status": "active"  // or "archived" if role goes stale (30+ days)
    },
    "def456abc123": {
      "first_seen": "2026-05-20T14:00:00Z",
      "last_seen": "2026-06-14T09:00:00Z",
      "opportunity_ids": ["uuid3"],
      "sources": ["dataannotation"],
      "status": "active"
    }
  }
}
```

**Dedup logic:**

1. Compute `normalize_role_key(new_opp)`
2. Look up in `seen_roles.json[by_normalization_key]`
3. If found:
   - Mark as DUPLICATE (do not append opportunities.jsonl)
   - Update `last_seen` timestamp
   - Return early (Stage 2 complete, skip to Stage 3 for context)
4. If not found:
   - Add entry to seen_roles
   - Append to opportunities.jsonl
   - Continue to Stage 3

---

## Privacy & Data-Tier Mapping

**Mapping onto existing NIZAM PRIVACY_CLASSIFICATION tiers:**

| Data Element | Classification | Storage | Rules | NIZAM Gate |
|---|---|---|---|---|
| **Profile seed** (Seif role keywords, target roles, resume text) | `strict_local_maximum` | `TARIQ__career_radar/data/profile_cache.json` (gitignored, never leaves disk) | Never exported; used only in local matching | HIMAYAH + SUKOON |
| **Opportunity records** (title, company, salary, fit scores) | `strict_local` | `TARIQ__career_radar/data/opportunities.jsonl` (gitignored) | Append-only; retained locally + encrypted mirror to Drive via rclone-crypt | HIMAYAH |
| **Telegram summary** (short, action-oriented report) | `personal` (egress allowed to operator) | In-memory buffer → Telegram API via relay | No personal profile data; links only; safe for real-time delivery | HIMAYAH (egress_allowed for telegram_operator) |
| **Drive full report** (.docx + evidence) | `review_before_commit` | Google Drive `Records/TARIQ/` folder | Encrypted metadata + ciphertext ledger mirror via rclone-crypt; .docx in plaintext (within Drive's own encryption) | HIMAYAH (egress_allowed for drive_crypt) |
| **Ledger row** (EVENT_LEDGER / CAREER_RADAR_LEDGER) | `review_before_commit` | `NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl` | Hash-chained append-only; no personal data; metrics only | HIMAYAH + THABAT |
| **Seen-role store** (dedup index) | `strict_local` | `TARIQ__career_radar/data/seen_roles.json` | Index only; no profile data; keys are role hashes | HIMAYAH |
| **Salary evidence** (within opportunities.jsonl) | `strict_local` | Same as opportunities | Confidence tags attached; no employer identity (generic "guide-based", "community-reported") | HIMAYAH |

**HIMAYAH egress check (classifier.py augment):**

```python
# In NIZAM__system/policies/PRIVACY_CLASSIFICATION.json, add:
"TARIQ__career_radar/**": "strict_local",
"TARIQ__career_radar/data/profile_cache.json": "strict_local_maximum",
"NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl": "review_before_commit",
```

**Egress matrix (SYNC_POLICY.json augment):**

```json
{
  "egress_targets": {
    "TARIQ__career_radar/data/opportunities.jsonl": {
      "telegram_operator": false,      // profile matching stays local
      "telegram_broadcast": false,
      "drive_crypt": true,             // encrypted mirror OK
      "drive_clear": false,
      "github_private": false,
      "notion_sanitized": false,
      "zdr_inference": false
    },
    "TARIQ__career_radar/data/profile_cache.json": {
      "all": false                     // never leaves disk
    }
  }
}
```

---

## On-Demand Trigger Design (Phase 1) + Hermes Cron Seam (Phase 2+)

### Phase 1: On-Demand Trigger (Current)

**Operator command:**

```
/tariq-career-radar-run [--lane Remote USD] [--sources all | outlier,turing,upwork]
```

**Implementation path:**

1. Telegram → relay/coordinator.py (detects `/tariq-career-radar-run` command)
2. Router (IR-1..IR-8) → maps to TARIQ persona + skill `tariq-career-radar-run.md`
3. Skill invokes `TARIQ__career_radar/radar/main.py run-all --lane "Remote USD"`
4. CLI orchestrates Stage 1–7 in sequence
5. Return telegram reply + ledger append + Drive write

**No unattended scheduling in Phase 1.** Operator reviews findings before any automation.

### Phase 2: Hermes Cron Seam (Clean Integration Point)

**Setup for later scheduled runs (Phase 2):**

```python
# TARIQ__career_radar/radar/scheduler.py (placeholder in Phase 1, active in Phase 2)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

def start_scheduler():
    """
    Start daily TARIQ Career Radar run at 09:00 Cairo time.
    Mirrored from MARSAD__flight_radar/radar/scheduler.py pattern.
    """
    scheduler = BackgroundScheduler()
    
    # Schedule daily run: 09:00 Cairo time = 06:00 UTC (note: adjust for DST)
    trigger = CronTrigger(
        hour=6,
        minute=0,
        timezone='Africa/Cairo'
    )
    
    scheduler.add_job(
        run_all_stages,
        trigger=trigger,
        name='tariq-career-radar-daily-06utc',
        id='career-radar-daily'
    )
    
    scheduler.start()
    logger.info("Career Radar scheduled for 06:00 UTC daily")
```

**Hermes cron deployment (Phase 2):**

```bash
# Via tools/setup_hermes_scheduled_telegram.py (augment)
hermes_cli.main cron create \
  --name "tariq-career-radar-daily" \
  --schedule "0 6 * * *" \
  --deliver telegram \
  --command "cd TARIQ__career_radar && python -m radar.main run-all"
```

**Clean seam:** Switching Phase 1 → Phase 2 is only a config change (`.env` `SCHEDULER_ENABLED=true`); no code changes needed.

---

## Failure & Continuity Handling

**Principle:** "Save everything safely or print full unsaved output; never silently drop findings."

### Failure ladder (retry + fallback):

```
┌─ STAGE 6: DELIVER
│
├─ Telegram delivery
│  ├─ Try 1: immediate send
│  ├─ Fail? → wait 1s → retry 2
│  ├─ Fail? → wait 4s → retry 3
│  ├─ Fail? → wait 16s → final retry
│  └─ All fail? → log to DEAD_LETTER.jsonl + print full Telegram text to stdout
│
├─ Drive delivery (.docx + metadata)
│  ├─ Try 1: immediate write
│  ├─ Fail? → wait 1s → retry 2
│  ├─ Fail? → wait 4s → retry 3
│  ├─ Fail? → wait 16s → final retry
│  └─ All fail? → log to DEAD_LETTER.jsonl + print .docx JSON to stdout
│
└─ Ledger append
   ├─ Try 1: append to CAREER_RADAR_LEDGER.jsonl
   ├─ Fail? → halt (do NOT continue; ledger is authoritative)
   └─ CRITICAL: print full run record to stdout; operator must save manually
```

### Continuity.py implementation:

```python
def ensure_completion(run_record: dict, artifacts: dict) -> None:
    """
    Guarantee run is either fully saved or operator receives full output.
    Called at end of Stage 6 (Deliver).
    """
    
    # Attempt Telegram
    tg_sent = False
    for attempt in range(3):
        try:
            tg_send_message(artifacts['telegram_text'])
            tg_sent = True
            break
        except Exception as e:
            logger.warning(f"Telegram attempt {attempt+1}/3 failed: {e}")
            time.sleep([1, 4, 16][attempt])
    
    if not tg_sent:
        ledger_writer.append({
            'module': 'TARIQ__career_radar',
            'event_type': 'delivery_failed',
            'target': 'telegram',
            'run_id': run_record['run_id'],
            'error': str(e)
        })
        # Print to operator
        print("\n" + "="*70)
        print("TELEGRAM DELIVERY FAILED — OPERATOR SAVE REQUIRED")
        print("="*70)
        print(artifacts['telegram_text'])
        print("="*70)
    
    # Attempt Drive
    drive_sent = False
    for attempt in range(3):
        try:
            drive_id = write_docx_to_drive(artifacts['drive_report'])
            drive_sent = True
            break
        except Exception as e:
            logger.warning(f"Drive attempt {attempt+1}/3 failed: {e}")
            time.sleep([1, 4, 16][attempt])
    
    if not drive_sent:
        ledger_writer.append({
            'module': 'TARIQ__career_radar',
            'event_type': 'delivery_failed',
            'target': 'drive',
            'run_id': run_record['run_id'],
            'error': str(e)
        })
        # Print to operator
        print("\n" + "="*70)
        print("DRIVE DELIVERY FAILED — OPERATOR SAVE REQUIRED")
        print("="*70)
        print(json.dumps(artifacts['drive_report'], indent=2))
        print("="*70)
    
    # Append ledger (critical; do not swallow errors)
    try:
        ledger_writer.append({
            'ts': datetime.utcnow().isoformat() + 'Z',
            'module': 'TARIQ__career_radar',
            'event_type': 'run_complete',
            'run_id': run_record['run_id'],
            'lane': run_record['lane'],
            'opportunities_fetched': run_record['opportunities_fetched'],
            'opportunities_new': run_record['opportunities_new'],
            'opportunities_seen': run_record['opportunities_seen'],
            'telegram_sent': tg_sent,
            'drive_sent': drive_sent,
            'errors': [e for e in run_record.get('errors', [])]
        })
    except Exception as e:
        # HALT: ledger is source of truth
        print("\n" + "="*70)
        print("LEDGER APPEND FAILED — RUN MARKED INCOMPLETE")
        print("DO NOT CONTINUE WITHOUT RESOLVING THIS")
        print("="*70)
        print(json.dumps(run_record, indent=2))
        raise
```

---

## Build Order & Dependencies

**Suggested phase-by-phase build order** (informs roadmap sequencing):

### Phase 1: On-Demand MVP (Full pipeline, single lane)

| Build order | Component | Dependencies | Rationale |
|---|---|---|---|
| **1** | `config.py` + `constraints.py` | None | Foundation; all downstream read from config |
| **2** | `opportunity_store.py` | config | Write primitive; data durability before fetch |
| **3** | `dedup_engine.py` | store | Duplicate detection enables rerun safety |
| **4** | `sources/base.py` | config | Abstract source interface; establishes pattern |
| **5** | `sources/outlier_source.py` | base | Simplest source (API); validates pattern |
| **6** | `sources/turing_source.py` | base | Add second source; test multi-source dedup |
| **7** | `fetch.py` (Stage 1) | store + sources | Data ingestion orchestration |
| **8** | `dedup.py` (Stage 2) | dedup_engine | Dedup orchestration + run detection |
| **9** | `profile_matcher.py` | config | Profile matching logic (strict_local) |
| **10** | `scoring_engine.py` | config | Opportunity scoring (0–100) |
| **11** | `enrich.py` (Stage 3) | matcher + scorer | Profile matching + scoring orchestration |
| **12** | `tag.py` (Stage 4) | enrich | Tag assignment based on scores |
| **13** | `report.py` (Stage 5) | tag | Report template building (Telegram + Drive) |
| **14** | `deliver.py` (Stage 6) | report + existing relay/google_adapter | Delivery via existing NIZAM rails |
| **15** | `continuity.py` (Stage 7) | deliver | Failure handling + ledger append |
| **16** | `main.py` | all stages | CLI orchestration + entry point |
| **17** | `tests/` | all | Unit + integration tests |
| **18** | `_index.json` + README + NIZAM registration | main | Module self-registration |

### Phase 2: Scheduled + Multi-Lane (Unattended + GCC/EU)

| Build order | Component | Dependencies | Rationale |
|---|---|---|---|
| **1** | `scheduler.py` | main from Phase 1 | Enable Hermes cron slot |
| **2** | `sources/remotive_source.py` | base | Add RSS source (cheapest, high quality) |
| **3** | `sources/wellfound_source.py` | base | Add VC-backed startup opportunities |
| **4** | `sources/upwork_source.py` | base | Gig income supplement |
| **5** | `constraints.py` (augment for GCC/EU) | config | Lane expansion; add Riyadh, Dubai, Berlin targets |
| **6** | `profile_matcher.py` (augment for GCC roles) | matcher | Extend profile keywords for locale-specific roles |
| **7** | Hermes cron registration | scheduler | Deploy scheduled runner to VPS |
| **8** | Cross-pillar routing (MAL/MUNAWARA) | deliver | Income discovery → MAL, actions → MUNAWARA |

### Phase 3: Intelligence Features (Later)

- Browser automation for ATS + saved-search sources (riskier; Phase 2 proves MVP first)
- Salary history tracking + trend visualization (add to Drive reports)
- Company strength API integration (Crunchbase, PitchBook)
- Referral network matching (cross-reference with YAWMIYAT journaling)

---

## Component Responsibilities & Interface Contracts

### Core Components

**config.py**
- Loads all env vars + constants
- Validates credentials on startup
- Single source of truth for all thresholds (fit score weights, salary confidence levels, etc.)
- Contract: exports `Config` dataclass; no I/O side effects

**opportunity_store.py**
- Append-only JSONL writer with temp-file safety (write-to-temp → rename)
- Hash-chain versioning (future enhancement)
- Contract: `AppendOnlyStore.append(opportunity_record: dict) -> str` (returns record_id)

**dedup_engine.py**
- Maintains seen-role index (in-memory during run; persisted to seen_roles.json)
- Normalizes opportunity keys
- Contract: `DedupeEngine.check_or_add(opportunity: dict) -> (is_duplicate: bool, normalized_key: str)`

**profile_matcher.py**
- Loads Seif profile seed (strict_local_maximum)
- Compares opportunity against profile keywords + target roles
- Returns fit_score (0–100) + gap analysis
- Contract: `ProfileMatcher.match(opportunity: dict) -> MatchResult { fit_score, growth_score, gaps, confidence }`

**scoring_engine.py**
- Weighted scoring: fit (25) + salary_upside (20) + growth (15) + visa_feasibility (10) + company_strength (10) + referral_leverage (10) + freshness (5) + side_income (5) = 0–100
- Applies penalties for missing evidence, scams, unclear pay, severe mismatch
- Contract: `ScoringEngine.score(opportunity: dict, match_result: MatchResult) -> int`

**sources/base.py**
- Abstract source interface (fetch, normalize, rate_limit)
- Shared rate-limit logic (exponential backoff)
- Contract: `BaseSource(abstract)` with `fetch(constraints: Constraints) -> List[RawOpportunity]`

**fetch.py (Stage 1)**
- Orchestrates all sources in parallel (ThreadPoolExecutor)
- Normalizes raw → standardized opportunity records
- Contract: `run_fetch(config: Config) -> List[Opportunity]`

**dedup.py (Stage 2)**
- Checks each opportunity against seen_roles index
- Updates index + persists seen_roles.json
- Returns (new_opportunities, duplicates)
- Contract: `run_dedup(opportunities: List, engine: DedupeEngine) -> (new, dupes)`

**enrich.py (Stage 3)**
- Runs profile_matcher + scoring_engine on each opportunity
- Computes confidence (aggregate of fit, salary, data_quality)
- Contract: `run_enrich(opportunities: List, matcher: ProfileMatcher, scorer: ScoringEngine) -> List[Opportunity]`

**tag.py (Stage 4)**
- Assigns tags based on scores + gaps + salary confidence
- Contract: `run_tag(opportunities: List) -> List[Opportunity]`

**report.py (Stage 5)**
- Builds Telegram summary (short, ranked by fit + salary)
- Builds Drive .docx report (full evidence + links)
- Contract: `build_reports(opportunities: List, run_metadata: dict) -> (telegram_text: str, drive_dict: dict)`

**deliver.py (Stage 6)**
- Sends Telegram (via existing relay)
- Writes .docx to Drive (via existing google_adapter)
- Contract: `run_deliver(telegram_text: str, drive_dict: dict, config: Config) -> DeliveryResult`

**continuity.py (Stage 7)**
- Retry ladder for Telegram + Drive
- Ledger append (via existing ledger_writer)
- Print full output on failure
- Contract: `ensure_completion(run_record: dict, artifacts: dict) -> None` (may raise on ledger failure)

---

## Integration Points with Existing NIZAM Rails

### Telegram Relay

**Integration:** `NIZAM__system/relay/coordinator.py` + `poller.py`

- Career Radar does NOT poll Telegram; uses operator command `/tariq-career-radar-run`
- Router (IR-1..IR-8) recognizes command → delegates to TARIQ persona + skill
- Skill invokes CLI; CLI returns plain-text reply
- Relay sends reply via `tg_send_message(reply_text, chat_id)` — existing mechanism

**No new code in relay layer.** Use existing `/dump`, `/shura`, etc. pattern.

### Google Drive Adapter

**Integration:** `NIZAM__system/connectors/google_adapter.py` + `nizam_governor_lib.py`

- Career Radar calls `GoogleConnectorAdapter.write_docx_to_drive(report_dict, folder_id='Records/TARIQ')`
- Existing service-account credentials (`GOOGLE_APPLICATION_CREDENTIALS`) used
- .docx written via `google-api-python-client` (already a NIZAM dependency)
- No new credential setup needed; reuses Hermes Drive mirror infrastructure

### Ledger Writer

**Integration:** `NIZAM__system/governor/ledger_writer.py`

- Career Radar appends to new ledger `NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl`
- Add ledger to `KNOWN_LEDGERS` set in `ledger_writer.py`
- Register in `NIZAM_TEMPLE.json#ledgers` section
- Hash-chained append automatically enforced; no extra work needed

**New ledger registration:**

```json
// NIZAM_TEMPLE.json
"CAREER_RADAR_LEDGER": {
  "path": "NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl",
  "phase": 2,
  "privacy": "review_before_commit",
  "owner": "Tariq",
  "purpose": "Career radar run events, opportunity counts, delivery status"
}
```

### Privacy Classifier (HIMAYAH)

**Integration:** `NIZAM__system/governor/classifier.py` + `PRIVACY_CLASSIFICATION.json`

- Career Radar module files classified as `strict_local` (data never commits; profile stays local)
- Ledger rows classified as `review_before_commit` (metrics only, safe to commit)
- No new code; add path rules to `PRIVACY_CLASSIFICATION.json`

### Cost Ceiling

**Integration:** `NIZAM__system/governor/cost_ceiling.py`

- Career Radar sources (Outlier, Turing, DataAnnotation APIs) are free or cheap
- LLM cost (profile matching, scoring) charged to TARIQ persona's model budget
- Existing `cost_ceiling.py` already tracks per-persona LLM costs; no changes needed

### SYNC_POLICY & Drive Mirror

**Integration:** `rclone-crypt` ledger mirror + `nizam_drive_mirror.py`

- `opportunities.jsonl` automatically mirrored to Drive via `rclone copy` in hermes-plugin
- Encrypted-before-upload; plaintext stays on laptop only
- No new code; leverages existing MIRROR-1 pattern

---

## Suggested Build Order (Phase 1 Roadmap)

Based on dependencies + risk + learning value:

1. **Week 1:** `config.py` → `constraints.py` → `opportunity_store.py` → basic unit tests
2. **Week 2:** `dedup_engine.py` → `sources/base.py` + `sources/outlier_source.py` → fetch-stage end-to-end test
3. **Week 3:** `profile_matcher.py` → `scoring_engine.py` → enrich-stage unit tests
4. **Week 4:** `report.py` + `deliver.py` → integration test (fetch → report → telegram)
5. **Week 5:** `continuity.py` → failure-mode tests; NIZAM registration; operator review
6. **Phase 1 ship:** On-demand CLI + Telegram trigger working; landing in main branch

---

*Architecture analysis: 2026-06-14*
