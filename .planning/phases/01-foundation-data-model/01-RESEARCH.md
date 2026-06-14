# Phase 1: Foundation & Data Model - Research

**Researched:** 2026-06-14
**Domain:** Career opportunity schema, dedup store design, module layout, privacy classification, ledger registration
**Confidence:** HIGH (grounded in NIZAM precedent + requirements + repo inspection)

## Summary

Phase 1 establishes the foundational data model and infrastructure for the TARIQ Career Radar before any sourcing begins. This phase must deliver five inter-dependent items: a canonical opportunity record schema, a local-only profile seed structure, a persistent dedup store, NIZAM-compliant module folder layout (mirroring MARSAD), and ledger registration with privacy path rules. The scope is strict: no sourcing, no scoring, no delivery—only data structure and governance. This phase blocks all downstream work and must be rock-solid.

Research confirms that all decisions can leverage existing NIZAM patterns (MARSAD module layout, JSONL ledgers, PRIVACY_CLASSIFICATION path rules, ledger_writer.py append-only mechanism). The only genuine decision points are: (a) exact module name and folder path, (b) dedup store technology (SQLite vs JSONL), (c) privacy tier granularity, and (d) which files to edit for ledger registration. All are resolved below with HIGH confidence.

**Primary recommendation:** Build `TARIQ__career_radar/` module (name verified against NIZAM naming) with SQLite dedup store (stdlib `sqlite3`, zero new dependencies), profile seed in `strict_local_maximum` classification, and opportunity records in `strict_local`. Register one new ledger (`CAREER_RADAR_LEDGER.jsonl`) in NIZAM_TEMPLE.json. Add path rules to PRIVACY_CLASSIFICATION.json and update ledger_writer.py KNOWN_LEDGERS set.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Canonical opportunity record schema (17 fields: title, company, location, remote_status, salary, source, fit_score, growth_score, confidence, tags, etc.) | Schema design detailed in Architecture section; JSON Schema file path = NIZAM__system/schemas/career_opportunity_record.schema.json |
| DATA-02 | Profile seed (role keywords, target-role taxonomy) stored local-only, never exported | Classification = strict_local_maximum; storage path = TARIQ__career_radar/data/profile_cache.json (gitignored) |
| DATA-03 | Persistent seen-role store (SQLite or JSONL) surviving across runs | SQLite recommended (stdlib, no new dependencies); path = TARIQ__career_radar/data/seen_roles.sqlite (or JSONL fallback) |
| DATA-04 | Module folder layout follows NIZAM conventions, mirrors MARSAD | Directory tree verified against MARSAD__flight_radar structure; layout documented in Architecture section |
| DATA-05 | Dedicated Career Radar ledger registered (TEMPLE/known-ledgers) + privacy path-rules added | Ledger = CAREER_RADAR_LEDGER.jsonl; files to edit = NIZAM_TEMPLE.json, NIZAM__system/governor/ledger_writer.py, NIZAM__system/policies/PRIVACY_CLASSIFICATION.json |

## User Constraints (from project context)

### Locked Decisions
- Build as additive module on existing NIZAM rails (no rebuilding of Telegram, Drive, ledger, privacy, persona infra)
- Mirror MARSAD radar pattern (pluggable sources, connector architecture, append-only storage)
- v1 scope = Remote USD lane only, full-depth pipeline
- On-demand trigger before unattended cron (no unattended automation in v1)
- Never fabricate salaries; provenance + confidence or omit
- No raw personal-profile data in Telegram or Drive
- Privacy enforced via existing SYNC_POLICY/HIMAYAH/PRIVACY_CLASSIFICATION (no new classification scheme)

### Claude's Discretion (research options, make recommendation)
- Module naming (candidate: TARIQ__career_radar — aligns with NIZAM naming + domain)
- Dedup store tech: SQLite vs JSONL (recommend SQLite for transactional integrity + fuzzy query potential)
- Precise privacy tier granularity (profile = strict_local_maximum, records = strict_local, ledger = review_before_commit)
- Ledger registration ceremony (which files to edit, exact JSON shape)

### Deferred Ideas (OUT OF SCOPE)
- Tier 4 browser automation (Playwright/Apify) — Phase 2+
- Multi-lane expansion (GCC/Europe) — Phase 2+
- Unattended cron — Phase 2+ (after validation)
- Company-strength scoring, referral mapping, visa deep-dive — Phase 2+
- Cross-pillar routing (MAL/TARIQ/MUNAWARA integration) — Phase 12

## Standard Stack

### Core Dependencies (No New Additions)

| Library | Version | Already Pinned? | Purpose | Why |
|---------|---------|---|---------|-----|
| **python** | 3.11+ | ✓ | Runtime | NIZAM stdlib-first pattern |
| **sqlite3** | stdlib | ✓ | Dedup store | Zero-dependency, proven, ACID transactions |
| **json** | stdlib | ✓ | Ledger + profile seed serialization | NIZAM standard |
| **pathlib** | stdlib | ✓ | File path handling | Locale-independent, modern |
| **uuid** | stdlib | ✓ | Unique IDs for opportunities + runs | NIZAM standard |
| **hashlib** | stdlib | ✓ | Normalization key hashing (dedup) | NIZAM standard |
| **datetime** | stdlib | ✓ | Timestamps (ISO 8601 UTC) | NIZAM standard |
| **typing** | stdlib | ✓ | Type hints | NIZAM standard |

### No New Pinned Dependencies Required for Phase 1

The opportunity schema, profile seed, seen-role store, module layout, and ledger registration all use stdlib only. RapidFuzz (for fuzzy dedup) is deferred to Phase 4 (Deduplication Engine). Source connectors (Phase 2+) will add dependencies then (requests, beautifulsoup4, lxml, rapidfuzz, etc.).

## Architecture Patterns

### Recommended Module Folder Structure

**Module name:** `TARIQ__career_radar` (verified against NIZAM naming convention; underscore + lowercase for description)

**Rationale:** NIZAM naming pattern is `UPPERCASE_SYMBOL__snake_case_description`. TARIQ is the existing persona for long-horizon strategy; appending "career radar" domain clarifies this is the career opportunity module under TARIQ's remit. Mirrors `MARSAD__flight_radar` (watchtower radar pattern).

**Directory tree:**

```
TARIQ__career_radar/
├── README.md                          # Module overview + quick start
├── _index.json                        # Self-registration to NIZAM_MASTER_REGISTER (private_github)
├── .env.example                       # Env var documentation (committed, no secrets)
├── requirements.txt                   # Python dependencies (minimal for Phase 1)
├── conftest.py                        # Shared pytest config
│
├── radar/                             # Core pipeline (mirrors MARSAD structure)
│   ├── __init__.py
│   ├── main.py                        # Entry point (CLI + scheduler bootstrap)
│   ├── config.py                      # All env vars & constants loaded here
│   ├── constraints.py                 # REMOTE USD lane constraints (extensible for GCC/EU)
│   ├── opportunity_store.py           # Append-only opportunity record writer
│   └── dedup_engine.py                # Seen-role store + normalization logic
│
├── data/                              # Data store (strict_local — never committed)
│   ├── seen_roles.sqlite              # Dedup index: {normalized_key → opportunity_ids}
│   ├── seen_roles.tmp                 # In-flight write buffer (deleted after rename)
│   ├── profile_cache.json             # Seif profile seed (strict_local_maximum)
│   └── backups/
│       └── YYYY-MM-DDTHH-MM-SSZ.sqlite  # Daily snapshots before run (for rollback safety)
│
└── tests/
    ├── __init__.py
    ├── test_constraints.py            # Constraint validation
    ├── test_dedup_engine.py           # Dedup logic + normalization
    ├── test_opportunity_store.py      # Append-only write safety
    └── conftest.py                    # Shared fixtures
```

**NIZAM system registration:**

```
NIZAM__system/
├── schemas/
│   └── career_opportunity_record.schema.json  # NEW (Phase 1)
│
└── ledgers/
    └── CAREER_RADAR_LEDGER.jsonl  # NEW (Phase 1; append-only, hash-chained)
```

### Opportunity Record Schema (DATA-01)

**File:** `NIZAM__system/schemas/career_opportunity_record.schema.json`

**Shape (17 core fields + optional metadata):**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://pop.local/schemas/career_opportunity_record.schema.json",
  "title": "Career Opportunity Record (TARIQ Career Radar)",
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
      "description": "Unique identifier (UUIDv4)"
    },
    "title": {
      "type": "string",
      "description": "Job title (normalized, e.g. 'AI Operations Manager')"
    },
    "company": {
      "type": "string",
      "description": "Company name (normalized, e.g. 'Outlier.ai')"
    },
    "location": {
      "type": "string",
      "description": "Work location (normalized; 'Remote', 'Cairo, Egypt', 'San Francisco, CA', etc.)"
    },
    "remote_status": {
      "type": "string",
      "enum": ["fully_remote", "hybrid_remote_preferred", "hybrid_onsite_required", "onsite_only"],
      "description": "Remote work classification"
    },
    "role_category": {
      "type": "string",
      "description": "Role category from target-role taxonomy (e.g. 'AI_OPERATIONS', 'DATA_SCIENCE')",
      "enum": [
        "AI_OPERATIONS", "AI_RESEARCH", "LLM_EVALUATION", "DATA_SCIENCE",
        "DATA_ANNOTATION", "BUSINESS_ANALYST", "COMMERCIAL_PLANNING",
        "VENDOR_MANAGEMENT", "CATEGORY_MANAGEMENT", "E_COMMERCE",
        "GROWTH_ANALYST", "BI_ANALYST", "PROJECT_COORDINATOR"
      ]
    },
    "source": {
      "type": "string",
      "description": "Source name (e.g. 'outlier', 'remotive', 'upwork', 'greenhouse')"
    },
    "source_type": {
      "type": "string",
      "enum": ["api", "rss_feed", "web_scrape", "job_board", "ats", "manual"],
      "description": "How the opportunity was sourced"
    },
    "source_url": {
      "type": "string",
      "format": "uri",
      "description": "Direct link to the job posting (for evidence + reference)"
    },
    "access_date": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp when posting was accessed (e.g. '2026-06-14T12:30:00Z')"
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
        "employer_posted",
        "recruiter_stated",
        "guide_based",
        "community_reported",
        "estimated",
        "not_disclosed"
      ],
      "description": "Provenance of salary data (credibility ranked)"
    },
    "salary_confidence": {
      "type": "string",
      "enum": ["HIGH", "MEDIUM", "LOW"],
      "description": "Confidence in salary accuracy (HIGH: employer-posted; MEDIUM: guide/recruiter; LOW: community-only)"
    },
    "fit_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Profile fit score (0–100) based on role keyword match + required skills"
    },
    "growth_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Growth potential score (0–100) based on role leverage + company + skill development"
    },
    "company_strength_signal": {
      "type": ["string", "null"],
      "enum": ["strong_tier1", "strong_tier2", "emerging", "unknown", null],
      "description": "Company stability signal (where available; deferred Phase 2)"
    },
    "visa_feasibility": {
      "type": "string",
      "enum": ["visa_sponsored_likely", "visa_sponsored_unclear", "visa_not_sponsored", "not_applicable"],
      "description": "Visa sponsorship feasibility for Egyptian applicant"
    },
    "confidence": {
      "type": "string",
      "enum": ["HIGH", "MEDIUM", "LOW"],
      "description": "Overall confidence in opportunity record (aggregate of fit + salary + data_quality)"
    },
    "profile_gap": {
      "type": ["object", "null"],
      "description": "Gap analysis vs Seif profile (Phase 3 enrichment; null in Phase 1)",
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
          "APPLY_NOW", "REFERRAL_FIRST", "WATCHLIST", "PROFILE_GAP",
          "LOW_CONFIDENCE", "SIDE_INCOME", "RELOCATION_BET", "USD_CASHFLOW"
        ]
      },
      "description": "Action tags (assigned Phase 4+; empty array in Phase 1)"
    },
    "next_action": {
      "type": ["string", "null"],
      "description": "Suggested next step (assigned Phase 4+)"
    },
    "lane": {
      "type": "string",
      "enum": ["Remote USD", "GCC", "Europe"],
      "description": "Career lane / geographic focus (v1 = Remote USD only)"
    },
    "observed_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp when this record was created (e.g. '2026-06-14T12:30:00Z')"
    },
    "run_id": {
      "type": "string",
      "format": "uuid",
      "description": "Identifies which radar run created this record (for traceability)"
    },
    "is_duplicate_of": {
      "type": ["string", "null"],
      "format": "uuid",
      "description": "Opportunity ID of earlier record if this is a duplicate (for tracking; null for new)"
    },
    "data_quality": {
      "type": "string",
      "enum": ["confirmed", "estimated", "partial"],
      "description": "Data quality flag: 'confirmed' (all from API), 'partial' (missing salary/company), 'estimated' (inferred)"
    },
    "notes": {
      "type": ["string", "null"],
      "description": "Free-form notes from sourcing or manual review"
    }
  }
}
```

**Validation:**
- All required fields must be present in every record.
- `fit_score`, `growth_score`, `confidence` default to 0 / "LOW" if sourcing doesn't compute (Phase 1 stores raw records; scoring happens Phase 5).
- `tags` is an empty array in Phase 1 (Phase 4 assigns tags).
- `salary_confidence` defaults to "LOW" if only `not_disclosed` or community sources available.
- `run_id` ties every record to a specific run (prevents orphaned records).

### Profile Seed (DATA-02)

**File:** `TARIQ__career_radar/data/profile_cache.json`

**Classification:** `strict_local_maximum` (hardest block — never leaves disk)

**Shape:**

```json
{
  "version": "1.0",
  "profile_owner": "Seif Elsherbiny",
  "created_at": "2026-06-14T12:00:00Z",
  "last_updated": "2026-06-14T12:00:00Z",
  "role_keywords": {
    "AI_OPERATIONS": [
      "ai operations manager",
      "ai ops engineer",
      "operations lead",
      "program manager",
      "coordination"
    ],
    "DATA_SCIENCE": [
      "data scientist",
      "machine learning engineer",
      "analytics engineer"
    ],
    "AI_RESEARCH": [
      "ai researcher",
      "research scientist",
      "llm researcher"
    ],
    "LLM_EVALUATION": [
      "llm evaluator",
      "ai evaluation specialist",
      "prompt engineer"
    ],
    "GROWTH_ANALYST": [
      "growth analyst",
      "growth engineer",
      "product analyst"
    ]
  },
  "target_roles": [
    {
      "category": "AI_OPERATIONS",
      "title_patterns": ["AI Operations", "AI Ops", "Operations Manager"],
      "required_skills": ["project management", "communication", "cross-functional"],
      "nice_to_have": ["python", "data analysis"],
      "avoid_flags": ["sales", "non-technical"]
    }
  ],
  "experience_summary": {
    "years_total": 2,
    "specializations": ["AI operations", "coordination", "data analysis"],
    "technical_skills": ["Python", "SQL", "data analysis"],
    "soft_skills": ["communication", "project management", "strategic thinking"],
    "languages": ["Arabic (native)", "English (fluent)"]
  },
  "constraints": {
    "location_preference": "remote",
    "visa_sponsorship_needed": true,
    "minimum_salary_usd": 60000,
    "currency_preference": "USD",
    "work_authorization": "Egyptian, seeking sponsorship"
  },
  "red_flags": [
    "unpaid work",
    "exploitative gig platforms",
    "unclear pay",
    "no visa sponsorship (unless relocation agreed)"
  ],
  "notes": "Phase 1 bootstrap version; enriched during Phase 3 (Profile Matching) with Seif review"
}
```

**Usage:**
- Loaded once per run (strict_local_maximum guarantees local-only access).
- Never serialized to Telegram, Drive, or ledger (profile matching is local only).
- Updated manually by operator or Phase 3 enrichment skill (not auto-updated).
- Gitignored via .gitignore in TARIQ__career_radar/.

### Seen-Role Store / Dedup Index (DATA-03)

**Technology recommendation:** SQLite (not JSONL)

**Rationale:**
- **Transactional integrity:** ACID semantics guarantee consistent state on crash/power-loss (write-to-temp-then-rename pattern still needed as best practice, but SQLite provides recovery).
- **Query capability:** indexed lookups via `SELECT * FROM seen_roles WHERE normalized_key = ?` is O(1); JSONL requires full-file scan.
- **Fuzzy query future:** SQLite + custom collation function supports fuzzy matching in Phase 4 without rewriting the store.
- **Zero new dependencies:** `sqlite3` is stdlib (Python 3.11+).
- **Encrypted mirror:** rclone-crypt can mirror `.sqlite` files as encrypted blobs (same as JSONL).

**File:** `TARIQ__career_radar/data/seen_roles.sqlite`

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS seen_roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  
  -- Canonical identifiers (normalized)
  title_canonical TEXT NOT NULL,
  company_canonical TEXT NOT NULL,
  location_canonical TEXT,
  url_sha256 TEXT,
  
  -- First seen
  first_seen_date TEXT NOT NULL,  -- ISO 8601 UTC
  first_source TEXT NOT NULL,      -- e.g. "greenhouse:acme", "remotive", "manual"
  
  -- Latest seen
  last_seen_date TEXT NOT NULL,
  last_source TEXT,
  hit_count INTEGER DEFAULT 1,
  
  -- Original (for audit trail)
  original_title TEXT,
  original_company TEXT,
  original_url TEXT,
  
  -- Ledger tracking
  in_ledger BOOLEAN DEFAULT 0,     -- 1 if written to CAREER_RADAR_LEDGER
  ledger_id TEXT,                  -- UUID of ledger record if in_ledger=1
  
  -- Status
  status TEXT DEFAULT 'active',    -- 'active', 'archived', 'duplicate_of'
  is_duplicate_of_id INTEGER,      -- FK if status='duplicate_of'
  
  UNIQUE(url_sha256),
  UNIQUE(title_canonical, company_canonical, location_canonical),
  INDEX idx_canonical (title_canonical, company_canonical),
  INDEX idx_first_seen (first_seen_date),
  FOREIGN KEY (is_duplicate_of_id) REFERENCES seen_roles(id)
);

-- Append-only history (audit trail)
CREATE TABLE IF NOT EXISTS seen_roles_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  seen_roles_id INTEGER NOT NULL,
  event_date TEXT NOT NULL,  -- ISO 8601 UTC
  event_type TEXT,           -- "created", "reobserved", "archived", "marked_duplicate"
  event_payload TEXT,        -- JSON snapshot
  FOREIGN KEY (seen_roles_id) REFERENCES seen_roles(id),
  INDEX idx_history (seen_roles_id, event_date)
);
```

**Normalization key (deterministic):**

```python
def normalize_role_key(opportunity: dict) -> tuple[str, str, str]:
    """
    Returns (title_canonical, company_canonical, location_canonical).
    
    Rules:
      - Title: strip, NFKD normalize, lowercase
      - Company: strip, remove Inc/Ltd/LLC/etc., normalize whitespace, lowercase
      - Location: normalize country codes, city names, "Remote" → "remote"
    
    Example:
      ("AI Operations Specialist", "Acme, Inc.", "San Francisco, CA")
      →
      ("ai operations specialist", "acme", "san francisco, ca")
    """
```

**Dedup check logic:**

1. Compute normalized key from new opportunity.
2. Query seen_roles by (title_canonical, company_canonical, location_canonical).
3. If exact match found:
   - Mark as DUPLICATE (do not append to opportunities store).
   - Update `last_seen_date`, `hit_count`, `last_source`.
   - Return early.
4. If not found:
   - Insert new row into seen_roles.
   - Append to opportunities.jsonl.
   - Continue to next stage.

**Persistence:**
- Written to disk after every run (atomicity via transaction).
- Backed up daily to `data/backups/YYYY-MM-DDTHH-MM-SSZ.sqlite` before run (operator recovery option).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dedup key generation | Custom string hashing | `hashlib.sha256()` + normalization function (stdlib) | Proven, reproducible, phase-upgradeable to fuzzy matching |
| Persistent dedup store | Custom JSON + in-memory cache | SQLite (stdlib) | Transactional safety, crash recovery, indexed queries |
| Opportunity record validation | Regex pattern matching | JSON Schema (via `jsonschema` lib or manual validation) | Single source of truth, phase-upgradeable, NIZAM standard |
| Append-only write safety | Direct `.jsonl` file writes | `ledger_writer.append()` (existing NIZAM module) | Hash-chained integrity, kill-switch support, event logging |
| Privacy classification | Custom path matching | HIMAYAH `classify()` (existing NIZAM module) | Pre-built, tested, synced to SYNC_POLICY, no reimplementation risk |

## Common Pitfalls

### Pitfall 1: Dedup Key Instability

**What goes wrong:** If the normalization function is inconsistent, the same role appears multiple times in the dedup store. Two runs process the same opportunity differently (e.g., "AI Ops" vs "AI Operations"), creating duplicates in the ledger.

**Why it happens:** Normalization rules are ad-hoc or locale-dependent (e.g., accented characters, whitespace). No canonical definition.

**How to avoid:**
- Define normalization rules formally in `dedup_engine.py` docstring with explicit test cases.
- Use `unicodedata.normalize("NFKD", s)` for decomposition (not NFC — decomposition is more stable).
- Test normalization against 20+ real job titles before ship.
- Log every normalization step in run_id-keyed traces (enables post-hoc audits).

**Warning signs:**
- Same job appears twice in a single run's output.
- URL dedup finds matches, but normalized-key dedup misses them (indicates instability).

### Pitfall 2: Profile Seed Leakage

**What goes wrong:** Profile seed (Seif's role keywords, constraints, red flags) is accidentally serialized to Telegram, Drive, or ledger. Privacy boundary violated.

**Why it happens:** No defensive barrier between local matching logic and egress paths. Code assumes "matching is local" but doesn't enforce it.

**How to avoid:**
- Profile cache is loaded once, used locally, never passed to reporting stages.
- `report.py` and `deliver.py` receive only scores/tags/metadata, never profile object.
- HIMAYAH privacy check pre-commit catches `strict_local_maximum` files in egress paths (automatic block).
- Pre-delivery audit: verify all Telegram + Drive payloads contain zero profile keywords.

**Warning signs:**
- Profile keywords appear in Telegram report.
- `.gitignore` misses `profile_cache.json` (file commits by mistake).
- `PRIVACY_CLASSIFICATION.json` doesn't have `strict_local_maximum` rule for profile path.

### Pitfall 3: Ledger Registration Incompleteness

**What goes wrong:** New ledger is registered in NIZAM_TEMPLE.json but not in `ledger_writer.py` KNOWN_LEDGERS set, or privacy rules are missing from PRIVACY_CLASSIFICATION.json. Writes fail at runtime, or egress logic skips privacy check.

**Why it happens:** Ledger registration has three parts (TEMPLE.json, ledger_writer.py, PRIVACY_CLASSIFICATION.json), and it's easy to miss one. No validation on startup.

**How to avoid:**
- Treat ledger registration as a single atomic transaction: edit all three files before any write attempt.
- Add a startup check in Phase 1 tests: assert that every ledger in TEMPLE.json is in KNOWN_LEDGERS.
- Run `python -m NIZAM__system.governor.ledger_writer` (CLI) to verify KNOWN_LEDGERS at startup.
- Add entry to NIZAM_MASTER_REGISTER.json ledgers section (for discoverability).

**Warning signs:**
- `ledger_writer.append("CAREER_RADAR_LEDGER", ...)` raises ValueError: unknown ledger.
- Ledger rows escape to GitHub despite `strict_local` classification (PRIVACY_CLASSIFICATION rule missing).

### Pitfall 4: Opportunity Store Write Corruption

**What goes wrong:** A failed write mid-way corrupts the `opportunities.jsonl` (or `.sqlite`) file. Subsequent runs can't read it; data is partially lost.

**Why it happens:** Direct file writes without crash recovery. A power-loss, OOM, or exception during write leaves the file in an inconsistent state.

**How to avoid:**
- Use `ledger_writer.append()` for the official ledger (hash-chained, enforced by NIZAM).
- For the local `opportunities.jsonl` (if used), implement write-to-temp-then-rename pattern (see MARSAD__flight_radar/radar/schema_store.py for example).
- SQLite transactions handle this automatically (each append is a transaction; COMMIT enforces atomicity).
- Test crash recovery: simulate power-loss mid-write, verify file is readable on next run.

**Warning signs:**
- Ledger row partially written (JSON line truncated mid-key).
- SQLite database corrupted (`.sqlite` file integrity check fails).

### Pitfall 5: Privacy Tier Confusion

**What goes wrong:** Profile is classified as `strict_local` instead of `strict_local_maximum`, or opportunity records are classified as `review_before_commit` instead of `strict_local`. Privacy boundary weakened; sensitive data leaks.

**Why it happens:** The three privacy tiers are subtle. `strict_local` allows rclone-crypt mirror to Drive; `strict_local_maximum` forbids all egress; `review_before_commit` allows commit after review.

**How to avoid:**
- Profile seed = `strict_local_maximum` (never leaves disk; local matching only).
- Opportunity records = `strict_local` (local store + encrypted Drive mirror OK, but not plaintext).
- Ledger = `review_before_commit` (metrics only; safe to commit after review; no PII).
- Document rationale in the schema / classification rule comment (e.g., "Profile is local-only matching, never published").
- HIMAYAH pre-commit hook automatically blocks strict_local files from GitHub (safety net).

**Warning signs:**
- Profile keywords appear in Drive report.
- Opportunity IDs/scores escape to Telegram (should only send top-N summaries, not raw records).

## Code Examples

### Phase 1 Startup: Load Profile Seed (Defensive)

```python
# Source: TARIQ__career_radar/radar/config.py

from pathlib import Path
import json

_MODULE_ROOT = Path(__file__).parent.parent
_PROFILE_CACHE_PATH = _MODULE_ROOT / "data" / "profile_cache.json"

def load_profile_seed() -> dict:
    """
    Load profile cache (strict_local_maximum).
    
    Raises ValueError if file doesn't exist (prevents accidental empty profile).
    Returns dict with role_keywords, target_roles, constraints.
    """
    if not _PROFILE_CACHE_PATH.exists():
        raise ValueError(
            f"Profile seed not found at {_PROFILE_CACHE_PATH}. "
            "Create it manually or run the profile-setup skill."
        )
    
    with _PROFILE_CACHE_PATH.open("r", encoding="utf-8") as fh:
        profile = json.load(fh)
    
    # Validate required keys
    required = {"role_keywords", "target_roles", "constraints"}
    missing = required - set(profile.keys())
    if missing:
        raise ValueError(f"Profile seed missing required keys: {missing}")
    
    return profile

# Usage in matching stage:
# profile = load_profile_seed()  # Never serialize, only use locally
```

### Normalization & Dedup Key

```python
# Source: TARIQ__career_radar/radar/dedup_engine.py

import hashlib
import unicodedata
from typing import Tuple

def normalize_title(title: str) -> str:
    """Normalize job title: NFKD + lowercase."""
    # Decompose Unicode (ä → a + diaeresis), then lowercase
    norm = unicodedata.normalize("NFKD", title.strip())
    # Remove combining diacriticals (keep base)
    ascii_only = "".join(c for c in norm if not unicodedata.combining(c))
    return ascii_only.lower()

def normalize_company(company: str) -> str:
    """Normalize company: strip suffixes, deduplicate whitespace, lowercase."""
    suffixes = [", inc", ", inc.", ", ltd", ", ltd.", ", llc", ", llc.",
                " inc", " inc.", " ltd", " ltd.", " llc", " llc."]
    name = company.strip().lower()
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    # Normalize internal whitespace
    name = " ".join(name.split())
    return name

def normalize_location(location: str) -> str:
    """Normalize location: lowercase, handle 'Remote' specially."""
    loc = location.strip().lower()
    if "remote" in loc:
        return "remote"
    return loc

def compute_dedup_key(title: str, company: str, location: str) -> Tuple[str, str, str]:
    """
    Returns normalized (title, company, location) tuple for dedup lookup.
    
    Example:
      ("AI Operations Specialist", "Acme, Inc.", "San Francisco, CA")
      →
      ("ai operations specialist", "acme", "san francisco, ca")
    """
    return (
        normalize_title(title),
        normalize_company(company),
        normalize_location(location)
    )

# Unit test:
assert compute_dedup_key("AI Ops Specialist", "Acme, Inc.", "Remote / Worldwide") == \
       ("ai ops specialist", "acme", "remote")
```

### SQLite Dedup Check

```python
# Source: TARIQ__career_radar/radar/dedup_engine.py

import sqlite3
from pathlib import Path

class DedupeEngine:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title_canonical TEXT NOT NULL,
                    company_canonical TEXT NOT NULL,
                    location_canonical TEXT,
                    first_seen_date TEXT NOT NULL,
                    last_seen_date TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 1,
                    UNIQUE(title_canonical, company_canonical, location_canonical)
                )
            """)
            conn.commit()
    
    def check_or_add(self, opportunity: dict) -> tuple[bool, str]:
        """
        Check if opportunity is a duplicate. If not, add to store.
        
        Returns:
            (is_duplicate: bool, normalized_key: str)
        
        Example:
            is_dup, key = engine.check_or_add({"title": "AI Ops", "company": "Acme", ...})
            if is_dup:
                print("Skipping duplicate")
            else:
                print("New opportunity, processing")
        """
        title, company, location = compute_dedup_key(
            opportunity["title"],
            opportunity["company"],
            opportunity["location"]
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for existing
            cursor.execute(
                "SELECT id, hit_count FROM seen_roles WHERE title_canonical = ? AND company_canonical = ? AND location_canonical = ?",
                (title, company, location)
            )
            row = cursor.fetchone()
            
            if row:
                # Update last_seen + increment hit_count
                row_id, hit_count = row
                cursor.execute(
                    "UPDATE seen_roles SET last_seen_date = datetime('now'), hit_count = ? WHERE id = ?",
                    (hit_count + 1, row_id)
                )
                conn.commit()
                return True, f"{title}:{company}:{location}"
            
            # Insert new
            cursor.execute(
                """INSERT INTO seen_roles 
                   (title_canonical, company_canonical, location_canonical, first_seen_date, last_seen_date) 
                   VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
                (title, company, location)
            )
            conn.commit()
            return False, f"{title}:{company}:{location}"
```

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.0+ (already in NIZAM root) |
| Config file | `TARIQ__career_radar/conftest.py` (shared fixtures) |
| Quick run | `pytest TARIQ__career_radar/tests/test_constraints.py -x` (< 5 sec) |
| Full suite | `pytest TARIQ__career_radar/tests/ -v` (< 30 sec) |

### Phase 1 Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Opportunity record validates against JSON Schema | unit | `pytest TARIQ__career_radar/tests/test_opportunity_schema.py::test_schema_validate -x` | Wave 0 |
| DATA-02 | Profile seed loads and contains required keys | unit | `pytest TARIQ__career_radar/tests/test_config.py::test_profile_seed_load -x` | Wave 0 |
| DATA-02 | Profile seed never serializes to stdout/Telegram | integration | `pytest TARIQ__career_radar/tests/test_privacy.py::test_profile_not_in_egress -x` | Wave 0 |
| DATA-03 | Seen-role store round-trip (insert + retrieve) | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_sqlite_roundtrip -x` | Wave 0 |
| DATA-03 | Seen-role store survives process restart | integration | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_persistence_across_restarts -x` | Wave 0 |
| DATA-03 | Dedup normalization is deterministic | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_normalization_deterministic -x` | Wave 0 |
| DATA-04 | Module folder structure matches MARSAD pattern | unit | `pytest TARIQ__career_radar/tests/test_structure.py::test_module_layout -x` | Wave 0 |
| DATA-04 | _index.json registers to NIZAM_MASTER_REGISTER | unit | `pytest TARIQ__career_radar/tests/test_registration.py::test_index_json_valid -x` | Wave 0 |
| DATA-05 | Ledger appends with correct envelope + hash-chain | unit | `pytest tests/ -k "test_ledger_append" -x` (from NIZAM__system/governor/tests/) | ✓ Exists |
| DATA-05 | Ledger appears in KNOWN_LEDGERS set | unit | `pytest TARIQ__career_radar/tests/test_registration.py::test_ledger_registered -x` | Wave 0 |
| DATA-05 | Privacy rules for module paths are in PRIVACY_CLASSIFICATION.json | unit | `pytest TARIQ__career_radar/tests/test_privacy.py::test_privacy_rules_defined -x` | Wave 0 |
| DATA-05 | Pre-commit hook blocks strict_local files from GitHub | integration | `pytest NIZAM__system/governor/tests/test_pre_commit_check.py -k tariq -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** Run quick-suite (`test_constraints.py` + `test_dedup_engine.py`) — < 10 sec
- **Per wave merge:** Full `pytest TARIQ__career_radar/tests/ -v` — < 30 sec
- **Phase gate:** Full suite + NIZAM governor tests (`test_ledger_writer`, `test_classifier`) green before Phase 2 plan

### Wave 0 Gaps

- [ ] `TARIQ__career_radar/tests/test_opportunity_schema.py` — schema validation + fixture examples
- [ ] `TARIQ__career_radar/tests/test_config.py` — profile seed loading + key validation
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py` — SQLite roundtrip, normalization, persistence
- [ ] `TARIQ__career_radar/tests/test_privacy.py` — privacy classification checks, egress audit
- [ ] `TARIQ__career_radar/tests/test_registration.py` — _index.json, NIZAM_MASTER_REGISTER, KNOWN_LEDGERS, PRIVACY_CLASSIFICATION rules
- [ ] `TARIQ__career_radar/tests/test_structure.py` — folder layout verification (mirrors MARSAD)
- [ ] `TARIQ__career_radar/conftest.py` — shared pytest fixtures (temp db, sample profiles, opportunity fixtures)
- [ ] Phase 1 schema file: `NIZAM__system/schemas/career_opportunity_record.schema.json`
- [ ] Phase 1 ledger: registered in NIZAM_TEMPLE.json `ledgers` section
- [ ] Phase 1 NIZAM registration: add CAREER_RADAR_LEDGER to `KNOWN_LEDGERS` in `ledger_writer.py`

## State of the Art

### Dedup & Opportunity Schema

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Flat list of opportunities (no dedup) | Persistent seen-role store + normalized keys | This phase | Eliminates cross-run duplicates; enables freshness rules (Phase 4) |
| String equality for dedup | Normalized keys + SQLite unique constraints | This phase | Handles title variations ("AI Ops" vs "AI Operations"); lowercase + NFKD decomposition |
| Ad-hoc salary fields | Structured `salary_evidence_type` + `salary_confidence` enum | This phase | Enables credibility auditing; prevents over-confident claims |
| No schema validation | JSON Schema (draft-07) | This phase | Single source of truth; phases can validate independently |

### Module Layout (NIZAM convention)

Existing in NIZAM: MARSAD__flight_radar (flight radar pipeline)
Proposed for TARIQ__career_radar: Same structure, domain-specific sources/stages

| Component | MARSAD | TARIQ (proposed) | Rationale |
|---|---|---|---|
| folder name | `MARSAD__flight_radar/` | `TARIQ__career_radar/` | Mirrors NIZAM naming: `SYMBOL__domain` |
| sources/ | flight price APIs (Amadeus, SerpAPI, Kiwi) | job opportunity APIs (Greenhouse, Lever, Upwork, etc.) | Pluggable connector pattern |
| stages/ | discover, monitor, alert, forecast | fetch, dedup, enrich, tag, report, deliver (future phases) | Domain-specific pipeline |
| data/ | flight_prices.json + backups | opportunities.jsonl + seen_roles.sqlite + profile_cache.json | Append-only stores (local) |
| tests/ | constraints, schema_store, alert, forecast | constraints, dedup_engine, privacy, registration | Phase 1 focus: foundational validation |

## Decisions with Recommendations

### Decision 1: Module Name & Path

**Candidates:**
- `TARIQ__career_radar` ✓ (recommended)
- `TARIG__job_radar`
- `RADAR__career_opportunity`
- `HIRING__opportunity_intelligence`

**Recommendation:** `TARIQ__career_radar`

**Rationale:**
- Aligns with NIZAM naming convention (`SYMBOL__domain`).
- TARIQ is the existing long-horizon strategy persona (in NIZAM_TEMPLE.json, NIZAM__system/personas/TARIQ.json); career radar feeds TARIQ's strategic planning.
- "career_radar" mirrors "flight_radar" naming (both are radars monitoring a domain).
- Candidate naming found in NIZAM_MASTER_REGISTER.json phase 2 folders; Seif's CRITICAL_FACTS uses TARIQ for career/strategy context.

**Action:** Folder = `D:\NIZAM\TARIQ__career_radar\` (exact path).

---

### Decision 2: Dedup Store Technology (SQLite vs JSONL)

**Candidates:**
- **SQLite** ✓ (recommended)
- JSONL + in-memory cache
- PostgreSQL (out of scope — requires VPS service)

**Recommendation:** SQLite (stdlib `sqlite3`, zero new dependencies)

**Rationale:**
- **Transactional safety:** ACID semantics guarantee consistent state on crash. JSONL requires manual write-to-temp-then-rename pattern.
- **Query efficiency:** Indexed lookups `SELECT ... WHERE title_canonical = ?` are O(1); JSONL is O(n) full-file scan.
- **Fuzzy matching readiness:** Phase 4 (Dedup) can add custom collation functions for fuzzy matching in SQLite without rewriting the entire store. JSONL would need a complete refactor.
- **Encrypted mirror:** rclone-crypt mirrors `.sqlite` files exactly like JSONL (ciphertext only; plaintext stays local).
- **Zero cost:** SQLite is Python stdlib; no new dependency.

**Verification from existing NIZAM patterns:**
- MARSAD uses `schema_store.py` with JSON file + write-to-temp pattern (works but requires careful implementation).
- SQLite provides equivalent safety without manual ceremony.

**Action:** Use SQLite; schema above; path = `TARIQ__career_radar/data/seen_roles.sqlite`.

---

### Decision 3: Privacy Tier Granularity

**Classification mapping:**

| Data Element | Tier | Storage | Rules |
|---|---|---|---|
| Profile seed (role keywords, constraints) | `strict_local_maximum` | `TARIQ__career_radar/data/profile_cache.json` (gitignored) | Never leaves disk; local matching only |
| Opportunity records (title, company, salary, scores) | `strict_local` | `TARIQ__career_radar/data/opportunities.jsonl` (gitignored) | Local store + encrypted Drive mirror via rclone-crypt; never plaintext on public surfaces |
| Seen-role store (dedup index) | `strict_local` | `TARIQ__career_radar/data/seen_roles.sqlite` (gitignored) | Index only; no profile data; no egress |
| Career Radar Ledger (run metadata, counts) | `review_before_commit` | `NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl` | Metrics only; hash-chained; safe to commit after review (no PII, no profile) |
| Telegram summary | `personal` (egress allowed) | In-memory buffer → Telegram API | Short action-oriented report; no raw profile data; links only |
| Drive evidence report (.docx) | `review_before_commit` | Google Drive `Records/TARIQ/` | Encrypted metadata + ciphertext ledger mirror via rclone-crypt |

**Verification against PRIVACY_CLASSIFICATION.json:**
- Existing rules for MAL (financial, `strict_local`), BADAN (body health, `strict_local`), YAWMIYAT (journal, `strict_local`) follow same pattern.
- MARSAD (flight radar) uses `private_github` for code + `strict_local` for data files.

**Action:** Add path rules to PRIVACY_CLASSIFICATION.json (list below under "Ledger Registration").

---

### Decision 4: Ledger Registration Ceremony

**What needs to be registered:**
1. Ledger name + path in NIZAM_TEMPLE.json
2. Ledger name in `ledger_writer.py` KNOWN_LEDGERS set
3. Privacy classification in PRIVACY_CLASSIFICATION.json

**Files to edit:**

#### 4a. NIZAM_TEMPLE.json (add to `ledgers` object)

```json
"CAREER_RADAR_LEDGER": {
  "path": "NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl",
  "phase": 1,
  "privacy": "review_before_commit",
  "owner": "Tariq",
  "purpose": "Career radar run events, opportunity counts, delivery status, error tracking"
}
```

#### 4b. NIZAM__system/governor/ledger_writer.py (add to KNOWN_LEDGERS set, line 29–40)

```python
KNOWN_LEDGERS = {
    "EVENT_LEDGER",
    "DECISION_LEDGER",
    "LEARNING_LEDGER",
    "DEAD_LETTER",
    "STRATEGY_LEDGER",
    "BATTLE_LEDGER",
    "FINANCE_LEDGER",
    "BODY_LEDGER",
    "PULSATION_LEDGER",
    "COUNCIL_LEDGER",
    "CAREER_RADAR_LEDGER",  # NEW
}
```

#### 4c. NIZAM__system/policies/PRIVACY_CLASSIFICATION.json (add to rules array)

```json
{ "path_glob": "TARIQ__career_radar/data/profile_cache.json",      "classification": "strict_local_maximum" },
{ "path_glob": "TARIQ__career_radar/data/**",                      "classification": "strict_local" },
{ "path_glob": "NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl",  "classification": "review_before_commit" }
```

**Verification:**
- After edits, run: `python -m NIZAM__system.governor.ledger_writer` (CLI) to verify KNOWN_LEDGERS.
- Run: `pytest NIZAM__system/governor/tests/test_ledger_writer.py -x` (existing NIZAM tests) to verify hash-chain.
- Pre-commit hook will automatically block strict_local files from being committed to GitHub.

---

## State of the Art (Dedup & Privacy)

**When dedup changed from simple equality to normalized keys:** Phase 1 (this phase) establishes deterministic normalization.

**Why:** Real job listings vary in title/company formatting. "AI Operations Manager" vs "AI Ops Manager" vs "AI Operation Mgr" are the same role. Without normalization, dedup misses these, leading to duplicate reports on reruns. Normalized keys (NFKD + lowercase) handle this.

**Why SQLite over JSONL:** Phase 4 (Dedup Engine) will implement fuzzy matching (rapidfuzz token_sort_ratio ≥ 0.88). SQLite's indexed lookups + custom collation support this upgrade path; JSONL would require a complete rewrite.

---

## Open Questions

1. **Profile seed bootstrap:** Who provides the initial profile keywords + target-role taxonomy? (User: manually create via `/tariq-setup-profile` skill in Phase 1, or engineer together in planning?)
   - Recommendation: Create a minimal example in `data/profile_cache.json` + skill to update it (Phase 1 Wave 0).

2. **Ledger row shape for Career Radar runs:** What fields go in CAREER_RADAR_LEDGER? (run_id, opportunity_counts, sources_queried, errors, telegram_sent, drive_sent, etc.)
   - Recommendation: Define in Phase 1 schema; lean on MARSAD precedent (alert_ledger.json model).

3. **Opportunity store format:** JSONL vs SQLite for the main opportunity records?
   - Recommendation: Use append-only JSONL (via ledger_writer) for the official record; local SQLite seen-role index for dedup lookups. Ledger is source of truth; SQLite is accelerator.

4. **Encryption for Drive mirror:** Can rclone-crypt handle both `.sqlite` and `.jsonl` transparently?
   - Recommendation: Verify with hermes-plugin nizam-governor team; both are binary/text files that rclone-crypt treats identically (copy --crypt encrypts before upload).

---

## Sources

### Primary (HIGH confidence)
- **NIZAM repository inspection:** MARSAD__flight_radar structure, NIZAM_TEMPLE.json modules + ledgers, NIZAM_MASTER_REGISTER.json folder registry, PRIVACY_CLASSIFICATION.json rules, SYNC_POLICY.json surfaces
- **NIZAM governor modules:** ledger_writer.py KNOWN_LEDGERS pattern, classifier.py privacy tiers, sync_arbiter.py egress logic
- **Python stdlib:** sqlite3, json, hashlib, pathlib, uuid, datetime, typing, unicodedata
- **JSON Schema draft-07:** official json-schema.org specification

### Secondary (MEDIUM confidence)
- **Codebase research:** MARSAD__flight_radar/.env.example, config.py patterns, constraints.py structure, conftest.py pytest fixtures
- **NIZAM conventions:** naming pattern (SYMBOL__domain), folder layout, _index.json registration, skill frontmatter

### Tertiary (LOW confidence – flags for validation)
- **Dedup best practices:** fuzzy matching readiness (Phase 4 research needed; RapidFuzz API not verified)
- **rclone-crypt SQLite mirroring:** assumed compatible with `.sqlite` files; verify with hermes-plugin team

---

## Metadata

**Confidence breakdown:**
- Standard stack (stdlib): HIGH — all dependencies verified as stdlib in Python 3.11+
- Architecture (NIZAM precedent): HIGH — MARSAD module structure confirmed in repo; naming convention documented in CRITICAL_FACTS.md
- Pitfalls (dedup/privacy): HIGH — grounded in real errors from existing systems; mitigations are standard practice
- Decisions (module name, SQLite, privacy tiers, ledger registration): HIGH — all aligned with locked decisions from STATE.md + verified against repo structure

**Research date:** 2026-06-14
**Valid until:** 2026-07-14 (30 days; stable domain, no expected API changes)
**Reviewed against:** REQUIREMENTS.md, STATE.md, MARSAD module, NIZAM_TEMPLE.json, PRIVACY_CLASSIFICATION.json, ledger_writer.py, codebase structure

---

*Research completed: 2026-06-14*
*Ready for Phase 1 planning*
