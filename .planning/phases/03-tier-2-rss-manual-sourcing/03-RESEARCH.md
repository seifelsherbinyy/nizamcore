# Phase 3: Tier 2 RSS & Manual Sourcing - Research

**Researched:** 2026-06-15  
**Domain:** RSS/Atom feed parsing (stdlib xml.etree), operator manual import (JSONL), role-keyword filtering  
**Confidence:** HIGH (feeds verified via official endpoints 2026, stdlib parsing patterns proven, manual-import pattern aligned with Phase 2 dedup contract)

## Summary

Phase 3 adds Tier 2 public RSS/Atom feeds (Remotive, We Work Remotely, RemoteOK) and an operator manual-import path (JSONL for Outlier/DataAnnotation/Turing/Toloka) to the TARIQ Career Radar. This phase delivers **SRC-02, SRC-03, and SRC-06**: fetching from RSS feeds using **stdlib `xml.etree.ElementTree`** (zero new dependencies), accepting operator-provided JSONL imports, and filtering opportunities to remote-USD AI/data/AI-ops/coordination roles via keyword matching against Seif's profile seed (from `data/profile_cache.json`).

**Primary recommendation:** Build two new source connectors—`RSSSource` (base class for all feeds) + `ManualImportSource` (reads gitignored JSONL)—mirroring the Phase 2 `BaseSource` contract exactly. No feedparser dependency; stdlib `xml.etree` parses RSS/Atom in ~50 lines per feed. Add a `RoleKeywordFilter` stage that runs after fetch+normalize, matching opportunity titles/descriptions against Seif's `role_keywords` groups (AI_OPERATIONS, DATA_SCIENCE, etc.). Filter at Stage 1 (fetch time) or Stage 2 (post-fetch, pre-dedup)—recommend Stage 2 for composability. Register feed URLs and role filter thresholds in `config_sources.yaml` (matching Phase 2 layout).

**Validated 2026 feeds:**
- **Remotive:** RSS + JSON API both live; RSS structured cleanly
- **We Work Remotely:** RSS only (no API); attribution required; stable
- **RemoteOK:** RSS + API both live; API returns more fields

**Manual import shape:** Operator provides `.jsonl` file (one record per line, optional fields: title, company, location, salary_usd_low, salary_usd_high, source_url, role_category, notes). Validates JSON schema before import; rejects malformed lines.

**Critical caveat:** Phase 2's `BaseSource` + `SourceResult` contract is reused unchanged. `ManualImportSource.fetch()` reads a gitignored file at run time, not a hardcoded config. RSS feeds require no authentication; minimal rate-limiting (if fetching daily, 1 req/5 sec per feed is safe).

---

<user_constraints>

## User Constraints (from CONTEXT.md / STATE.md / REQUIREMENTS.md)

### Locked Decisions

- **SRC-02:** Fetch from Tier 2 public RSS/feeds (Remotive, We Work Remotely, RemoteOK) using **stdlib xml.etree parsing** — **NO feedparser dependency**
- **SRC-03:** Operator manual import path for structured JSONL (e.g., Outlier/DataAnnotation/Turing/Toloka platforms lacking APIs)
- **SRC-06:** Sourcing targets remote-USD **AI/data/AI-ops/coordination + analyst roles** matched to Seif's role keyword groups (from `data/profile_cache.json`)
- Module layout mirrors Phase 2 (`sources/`, `BaseSource` ABC reused, concrete per-platform classes)
- Blocked/failed sources logged gracefully; run degrades, never aborts (SRC-05, already established in Phase 2)
- Every fetched opportunity normalized into DATA-01 schema with `source_type`, `source`, `source_url`, `access_date`, `salary_confidence`
- No new pinned dependencies (stdlib only; xml.etree, urllib, json, csv included)
- Additive module work on LIVE NIZAM deployment — do NOT move/delete/overwrite Phase 1+2 files

### Claude's Discretion (Research Options, Make Recommendations)

- **RSS base class design:** Should all feeds use a shared `RSSSource` class with per-feed subclasses, or a single configurable `RSSSource`? → **Recommend:** Shared `RSSSource(BaseSource)` with per-feed URL config (simpler, less boilerplate)
- **Role-keyword filter location:** At fetch time (Stage 1), post-normalize (Stage 2), or as a standalone Stage 3? → **Recommend:** Stage 2 (post-dedup, pre-enrich), so filtered opportunities feed into dedup/profile-matching stages cleanly
- **Manual import file location:** Gitignored JSONL in `data/manual_imports.jsonl` or per-run temp upload? → **Recommend:** `data/manual_imports.jsonl` (gitignored, persistent per run; operator appends; fetch reads latest on each run)
- **Salary defaults for manual import:** If operator omits salary, how to tag confidence? → **Recommend:** `salary_confidence = "LOW"`, `salary_evidence_type = "not_disclosed"` (default); allow override via optional fields
- **Role filtering strictness:** Exact keyword match, fuzzy (RapidFuzz), or both? → **Recommend:** Exact keyword match for Phase 3 (simple, deterministic); fuzzy dedup already handles near-duplicates in Phase 4

### Deferred Ideas (OUT OF SCOPE)

- Tier 3 browser automation (Playwright for sites without RSS/API) — Phase 2+ decision
- Levels.fyi / Glassdoor salary scraping (Tier 3 enrichment) — Phase 6+
- Email-based job alerts (LinkedIn, Indeed saved searches) — Phase 2+ decision
- GCC/Europe lane feeds (Talyent, Bayt, Stack Overflow Jobs, GitHub Jobs) — Phase 2 roadmap (v2 lanes)
- Auto-apply, auto-contact, form-filling — explicitly out of scope (hard rule)

</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| **SRC-02** | System fetches opportunities from Tier 2 public RSS/feeds (Remotive, We Work Remotely, RemoteOK) using stdlib parsing | RSS endpoint shapes verified 2026; stdlib `xml.etree.ElementTree` parser pattern documented; no feedparser needed |
| **SRC-03** | Operator can manually import opportunities (e.g., Outlier/DataAnnotation/Turing/Toloka) via structured JSONL/paste path | Manual import source class mirrors Phase 2 `BaseSource` contract; JSONL schema defined; gitignored file location specified |
| **SRC-06** | Sourcing targets remote-USD AI/data/AI-ops/coordination + analyst roles matched to Seif's role keyword groups | Profile seed `role_keywords` groups loaded from `config.load_profile_seed()`; filter stage matches opportunity title against keyword groups; test fixture provides sample matches/mismatches |

</phase_requirements>

---

## Standard Stack

### Core Libraries (All Stdlib or Already Pinned)

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|---|
| **xml.etree.ElementTree** | stdlib | RSS/Atom feed parsing (XML DOM access) | Stdlib; no new dependencies; mature, stable; sufficient for RSS/Atom spec |
| **urllib** | stdlib | URL handling, encoding | Stdlib; already used in Phase 2 modules |
| **requests** | 2.34.2 | HTTP GET for RSS feed URLs (already pinned) | No new cost; used in Phase 2 sources |
| **json** | stdlib | Parse JSONL manual-import records | Stdlib; no new cost |
| **csv** | stdlib | Optional: parse CSV variant of manual imports | Stdlib; fallback if operator prefers CSV |
| **datetime, pathlib, logging** | stdlib | Timestamps, path management, logging | Stdlib |

### No New Dependencies

- **feedparser (EXPLICITLY AVOIDED):** Single-use library; stdlib `xml.etree` handles RSS/Atom adequately; adds unnecessary pinning burden
- **lxml (OPTIONAL if already in requirements.txt):** Faster XML parsing; not required; stdlib ElementTree sufficient for typical feed sizes (1K–10K items)
- **rapidfuzz:** Deferred to Phase 4 (deduplication); not needed for Phase 3 keyword matching (exact match is fine)

---

## Architecture Patterns

### New Source Types (Phase 3 Extensions)

**File Layout:**
```
TARIQ__career_radar/radar/sources/
├── base.py                    # Reused from Phase 2 (unchanged)
├── greenhouse_source.py        # Phase 2
├── lever_source.py            # Phase 2
├── ashby_source.py            # Phase 2
├── workable_source.py         # Phase 2
├── rss_source.py              # NEW: RSS base class (Remotive, We Work Remotely, RemoteOK)
└── manual_import_source.py    # NEW: Operator JSONL import

TARIQ__career_radar/radar/stages/
├── fetch.py                   # Phase 2 (augmented to register new sources)
├── filter.py                  # NEW: Role-keyword filtering (SRC-06)
└── dedup.py                   # Phase 2 (unchanged; receives filtered opportunities)
```

### RSSSource Base Class

**Pattern:** Reuses `BaseSource`, `OpportunityRaw`, `SourceResult` from Phase 2 unchanged.

```python
from .base import BaseSource, OpportunityRaw, SourceResult
import xml.etree.ElementTree as ET

class RSSSource(BaseSource):
    """Base class for RSS/Atom feed sources (Remotive, We Work Remotely, RemoteOK).
    
    Subclasses set feed_url; fetch() parses XML and normalizes to OpportunityRaw.
    Never raises; returns errors in SourceResult.errors.
    """
    
    name: str = "rss"
    feed_url: str = ""  # Overridden by subclass
    
    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch and parse RSS feed.
        
        Returns:
            SourceResult with opportunities and/or errors.
        """
        opportunities = []
        errors = []
        
        if not self.feed_url:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["feed_url not configured"],
            )
        
        try:
            resp = requests.get(self.feed_url, timeout=30)
            resp.raise_for_status()
            
            root = ET.fromstring(resp.content)
            
            # RSS or Atom namespace handling
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'rss': None  # RSS uses no namespace
            }
            
            # Parse RSS <item> or Atom <entry> elements
            items = (
                root.findall(".//item") or  # RSS
                root.findall(".//{http://www.w3.org/2005/Atom}entry")  # Atom
            )
            
            for item in items:
                try:
                    opp = self._parse_item(item)
                    if opp:
                        opportunities.append(opp)
                except Exception as parse_exc:
                    errors.append(f"Parse error on item: {parse_exc}")
            
            return SourceResult(
                source_name=self.name,
                opportunities=opportunities,
                errors=errors,
            )
        
        except requests.Timeout:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Request timeout fetching {self.feed_url}"],
            )
        except Exception as exc:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Unexpected error: {type(exc).__name__}: {exc}"],
            )
    
    def _parse_item(self, item: ET.Element) -> OpportunityRaw or None:
        """Parse a single <item> (RSS) or <entry> (Atom) into OpportunityRaw.
        
        Subclasses override this to handle feed-specific field names.
        """
        raise NotImplementedError
```

### Concrete RSS Feeds (SRC-02)

#### 1. RemoativeSource

**Endpoint:** `https://remotive.com/remote-jobs/rss-feed` (RSS) or `https://api.remotive.com/v0/jobs` (JSON API)

**Recommendation:** Use RSS endpoint (simpler parsing, no pagination).

**RSS item structure:**
```xml
<item>
  <title>Senior AI Operations Manager</title>
  <link>https://remotive.com/remote-jobs/...</link>
  <description>Full HTML job description...</description>
  <pubDate>Tue, 14 Jun 2026 10:00:00 GMT</pubDate>
  <category>AI Operations</category>
  <company>Acme Corp</company>
</item>
```

**Field mapping:**
| RSS field | Schema field | Notes |
|-----------|--------------|-------|
| `<title>` | `title` | Direct |
| `<link>` | `source_url` | Direct |
| `<company>` | `company` | Custom Remotive field; may be missing (fallback to "Unknown") |
| `<category>` | `role_category` (optional) | Remotive categorizes; extract if present |
| `<description>` | (job description text for filtering) | Not stored; used for keyword matching in SRC-06 |
| "remotive" | `source` | Hardcoded |
| "rss_feed" | `source_type` | Hardcoded |
| `<pubDate>` | `access_date` | Parse RFC 2822 → ISO 8601 UTC |
| Absent | `salary_usd_low`, `salary_usd_high` | RSS feed typically omits salary; `confidence = LOW` |

**Confidence: HIGH** — Remotive RSS feed verified live 2026; structure stable for years.

#### 2. WeWorkRemotelySource

**Endpoint:** `https://weworkremotely.com/remote-job-rss-feed` (RSS only, no API)

**Note:** Attribution required in credits (legal requirement; add to ledger/report).

**RSS item structure:**
```xml
<item>
  <title>Data Analyst - Remote</title>
  <link>https://weworkremotely.com/remote-jobs/...</link>
  <description>HTML job description...</description>
  <pubDate>Mon, 13 Jun 2026 14:00:00 GMT</pubDate>
  <category>Data</category>
</item>
```

**Field mapping:**
| RSS field | Schema field | Notes |
|-----------|--------------|-------|
| `<title>` | `title` | Direct; typically includes "Remote" tag |
| `<link>` | `source_url` | Direct |
| (not present) | `company` | Fallback: extract from domain or use "Unknown" |
| `<category>` | `role_category` (optional) | Data, Design, Developer, etc. |
| `<description>` | (for keyword filtering) | Not stored in opportunity record |
| "weworkremotely" | `source` | Hardcoded |
| "rss_feed" | `source_type` | Hardcoded |
| `<pubDate>` | `access_date` | Parse RFC 2822 → ISO 8601 UTC |
| Absent | `salary_usd_low`, `salary_usd_high` | RSS typically omits; `confidence = LOW` |

**Confidence: HIGH** — We Work Remotely RSS verified live 2026; stable source.

#### 3. RemoteOKSource

**Endpoint:** `https://remoteok.com/remote-api-jobs` (JSON API; recommended) or RSS feed

**Recommendation:** Use JSON API (more fields, salary often included).

**JSON response shape:**
```json
[
  {
    "id": "12345",
    "title": "ML Engineer",
    "company": "Company Name",
    "url": "https://remoteok.com/remote-jobs/...",
    "location": "Remote",
    "salary": "$80,000 - $120,000",
    "description": "Full job description...",
    "posted_at": 1686398400,
    "tags": ["python", "machine learning"]
  }
]
```

**Field mapping:**
| API field | Schema field | Notes |
|-----------|--------------|-------|
| `title` | `title` | Direct |
| `url` | `source_url` | Direct |
| `company` | `company` | Direct |
| `location` | `location` | Direct ("Remote" → remote_status = "fully_remote") |
| `salary` | `salary_usd_low`, `salary_usd_high` | Parse "$80,000 - $120,000" → (80000, 120000); confidence = MEDIUM (user-provided, unverified) |
| `tags` | (for keyword filtering) | Not stored; used in role matching |
| "remoteok" | `source` | Hardcoded |
| "api" | `source_type` | Hardcoded (not "rss_feed" since we use JSON API) |
| `posted_at` | `access_date` | Unix timestamp → ISO 8601 UTC |
| Absent | `salary_usd_low`, `salary_usd_high` | If absent: `confidence = LOW` |

**Confidence: HIGH** — RemoteOK API verified live 2026; documented endpoint.

### ManualImportSource (SRC-03)

**Purpose:** Operator manually imports opportunities from platforms lacking APIs (Outlier, DataAnnotation, Turing, Toloka, etc.).

**File location (gitignored):** `TARIQ__career_radar/data/manual_imports.jsonl`

**Format:** One JSON record per line (JSONL). Operator appends records; fetch reads all lines on each run.

**Schema (example record):**
```jsonl
{"title": "AI Evaluator", "company": "Outlier AI", "location": "Remote", "salary_usd_low": 30, "salary_usd_high": 60, "salary_per": "hour", "source_url": "https://app.outlier.ai/jobs/123", "role_category": "LLM_EVALUATION", "notes": "high pay, good reviews, check payment schedule"}
{"title": "Data Annotator", "company": "DataAnnotation.tech", "location": "Remote", "source_url": "https://app.datannotation.tech/work", "notes": "invite-only platform, verify access"}
```

**JSON schema for manual import records:**
```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "company": {"type": "string"},
    "location": {"type": "string", "default": "Remote"},
    "source_url": {"type": "string", "format": "uri"},
    "salary_usd_low": {"type": ["number", "null"]},
    "salary_usd_high": {"type": ["number", "null"]},
    "salary_per": {"type": "string", "enum": ["hour", "annual", "project"], "default": "annual"},
    "role_category": {"type": "string"},
    "notes": {"type": "string"},
    "source": {"type": "string", "default": "manual"}
  },
  "required": ["title", "source_url"],
  "additionalProperties": false
}
```

**ManualImportSource implementation:**

```python
class ManualImportSource(BaseSource):
    """Operator-provided JSONL import source."""
    
    name = "manual"
    
    def __init__(self, config: dict) -> None:
        """Initialize from config.
        
        Args:
            config: Must contain "import_file_path" (path to .jsonl).
        """
        self.import_file_path = Path(config.get("import_file_path", ""))
    
    def fetch(self, constraints: dict) -> SourceResult:
        """Read and parse JSONL file."""
        opportunities = []
        errors = []
        
        if not self.import_file_path.exists():
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Import file not found: {self.import_file_path}"],
            )
        
        try:
            with open(self.import_file_path, "r", encoding="utf-8") as fh:
                for line_num, line in enumerate(fh, start=1):
                    line = line.strip()
                    if not line or line.startswith("#"):  # Skip empty/comment lines
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Validate required fields
                        if "title" not in record or "source_url" not in record:
                            errors.append(f"Line {line_num}: missing title or source_url")
                            continue
                        
                        # Convert salary_per format if needed
                        salary_annual_low = record.get("salary_usd_low")
                        salary_annual_high = record.get("salary_usd_high")
                        salary_per = record.get("salary_per", "annual")
                        
                        if salary_per == "hour" and salary_annual_low:
                            # Rough annualization: hour * 40 * 52
                            salary_annual_low = salary_annual_low * 40 * 52
                            salary_annual_high = salary_annual_high * 40 * 52 if salary_annual_high else None
                        
                        opp = OpportunityRaw(
                            title=record.get("title", ""),
                            company=record.get("company", "Unknown"),
                            location=record.get("location", "Remote"),
                            source_url=record.get("source_url", ""),
                            source="manual",
                            source_type="manual",
                            salary_usd_low=salary_annual_low,
                            salary_usd_high=salary_annual_high,
                            raw_payload=record,
                        )
                        opportunities.append(opp)
                    
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: invalid JSON — {e}")
        
        except Exception as exc:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Error reading import file: {type(exc).__name__}: {exc}"],
            )
        
        return SourceResult(
            source_name=self.name,
            opportunities=opportunities,
            errors=errors,
        )
```

### Role-Keyword Filter Stage (SRC-06)

**Location:** New file `TARIQ__career_radar/radar/stages/filter.py` or inline in fetch.py post-normalization.

**Recommendation:** Standalone `filter.py` stage (Stage 1.5, after fetch+normalize, before dedup).

**Implementation:**

```python
"""filter.py — Role-keyword filtering (SRC-06).

After fetch+normalize, filter opportunities to remote-USD AI/data/AI-ops/coordination roles
matched against Seif's profile_cache.json role_keywords groups.
"""

from radar.config import load_profile_seed
from pathlib import Path

def run_filter(opportunities: list[dict], profile_seed: dict = None) -> dict:
    """Filter opportunities by role keyword match against profile seed.
    
    Args:
        opportunities: List of normalized opportunity dicts from fetch stage.
        profile_seed: Profile dict with role_keywords; defaults to load_profile_seed().
    
    Returns:
        Dict with:
            "in_scope": list of opportunities matching role keywords
            "out_of_scope": list of opportunities not matching
            "filter_summary": {"total": int, "in_scope_count": int, "out_of_scope_count": int}
    """
    if profile_seed is None:
        profile_seed = load_profile_seed()
    
    role_keywords = profile_seed.get("role_keywords", {})
    in_scope = []
    out_of_scope = []
    
    for opp in opportunities:
        title_lower = (opp.get("title", "") or "").lower()
        
        # Check if title matches any keyword group
        matched = False
        for group_name, keywords in role_keywords.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    matched = True
                    opp["matched_role_group"] = group_name  # Tag for later use
                    break
            if matched:
                break
        
        if matched:
            in_scope.append(opp)
        else:
            out_of_scope.append(opp)
    
    return {
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "filter_summary": {
            "total": len(opportunities),
            "in_scope_count": len(in_scope),
            "out_of_scope_count": len(out_of_scope),
            "filter_rate": len(in_scope) / max(len(opportunities), 1),
        }
    }
```

**Integration into fetch.py:**

Modify `run_fetch()` to call the filter stage after normalizing all opportunities:

```python
def run_fetch(constraints: dict, run_id: str) -> dict:
    """Stage 1 orchestrator (modified to include filtering)."""
    all_opportunities = []
    # ... existing fetch code ...
    
    # NEW: Apply role-keyword filter (SRC-06)
    from radar.stages.filter import run_filter
    filter_result = run_filter(all_opportunities)
    in_scope_opps = filter_result["in_scope"]
    
    return {
        "opportunities": in_scope_opps,  # ONLY in-scope after this phase
        "blocked_sources": blocked_sources,
        "out_of_scope_opportunities": filter_result["out_of_scope"],  # Log for transparency
        "filter_summary": filter_result["filter_summary"],
        "fetch_summary": {...},
    }
```

---

## Tier 2 Feeds: Verified 2026 Endpoint Shapes

### Feed Availability & Parsing Notes

| Feed | Format | Endpoint | Public? | Auth? | Update Freq | Notes |
|------|--------|----------|---------|-------|-------------|-------|
| **Remotive** | RSS + JSON API | `remotive.com/remote-jobs/rss-feed` + `api.remotive.com/v0/jobs` | ✓ | ✗ | Daily | RSS is stable, well-formed; API has more fields |
| **We Work Remotely** | RSS only | `weworkremotely.com/remote-job-rss-feed` | ✓ | ✗ | Daily | Attribution req'd in credits; simple RSS structure |
| **RemoteOK** | RSS + JSON API | `remoteok.com/remote-api-jobs` + RSS endpoint | ✓ | ✗ | Daily | JSON API includes salary (user-provided); RSS is basic |

### XML Parsing Strategy (stdlib xml.etree)

**Why not feedparser?**
- Single-use library (only needed for Phase 3); adds pinning burden
- Stdlib `xml.etree.ElementTree` handles RSS/Atom parsing in ~50 lines
- Performance sufficient for typical feed sizes (1K–10K items)
- No external dependencies

**Parsing example (Remotive RSS):**

```python
import xml.etree.ElementTree as ET
import requests
from datetime import datetime

def parse_remotive_rss(feed_url: str) -> list[dict]:
    """Parse Remotive RSS feed into opportunity dicts."""
    opportunities = []
    
    resp = requests.get(feed_url, timeout=30)
    resp.raise_for_status()
    
    root = ET.fromstring(resp.content)
    
    # RSS uses no namespace; find all <item> elements
    for item in root.findall(".//item"):
        try:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            company = item.findtext("company", "Unknown")
            category = item.findtext("category", "")
            
            # Convert RFC 2822 → ISO 8601
            pub_date_iso = _rfc2822_to_iso8601(pub_date)
            
            opp = {
                "title": title,
                "source_url": link,
                "company": company,
                "access_date": pub_date_iso,
                "location": "Remote",  # Remotive = remote jobs by definition
                "source": "remotive",
                "source_type": "rss_feed",
                "salary_usd_low": None,
                "salary_usd_high": None,
                "salary_confidence": "LOW",
            }
            opportunities.append(opp)
        except Exception as e:
            logger.warning(f"Parse error on Remotive RSS item: {e}")
    
    return opportunities

def _rfc2822_to_iso8601(rfc_date: str) -> str:
    """Convert RFC 2822 'Tue, 14 Jun 2026 10:00:00 GMT' → '2026-06-14T10:00:00Z'."""
    try:
        dt = datetime.strptime(rfc_date, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.isoformat() + "Z"
    except:
        return datetime.utcnow().isoformat() + "Z"
```

---

## Manual Import & Role Filtering: Integration

### Config Section (config_sources.yaml augment)

```yaml
tier_1_ats:
  # ... existing Greenhouse, Lever, Ashby, Workable ...

tier_2_rss:
  enabled: true
  remotive:
    enabled: true
    feed_url: "https://remotive.com/remote-jobs/rss-feed"
    company: "Remotive"  # for logging

  weworkremotely:
    enabled: true
    feed_url: "https://weworkremotely.com/remote-job-rss-feed"
    company: "WeWorkRemotely"

  remoteok:
    enabled: true
    use_api: true  # Use JSON API instead of RSS
    api_url: "https://remoteok.com/remote-api-jobs"
    company: "RemoteOK"

manual_import:
  enabled: true
  import_file_path: "data/manual_imports.jsonl"  # gitignored; operator appends

role_filter:
  enabled: true  # SRC-06: filter by role keywords
  filter_threshold: 1  # Require ≥1 keyword match (exact match)
  profile_seed_path: "data/profile_cache.json"
```

### Fetch Stage Integration

Modify `radar/stages/fetch.py` to instantiate RSS + manual sources:

```python
# In run_fetch():

tier2_config = _load_tier2_config()

# RSS sources
rss_sources = []
if tier2_config.get("tier_2_rss", {}).get("enabled"):
    if tier2_config["tier_2_rss"].get("remotive", {}).get("enabled"):
        rss_sources.append(RemoativeSource(tier2_config["tier_2_rss"]["remotive"]))
    # ... etc for We Work Remotely, RemoteOK ...

# Manual import
manual_config = tier2_config.get("manual_import", {})
if manual_config.get("enabled"):
    source_list.append(ManualImportSource(manual_config))

# All sources (Phase 2 + Phase 3)
all_sources = source_list + rss_sources
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSS/Atom feed parsing | Custom XML parsing logic | `xml.etree.ElementTree` (stdlib) | Handles XML spec edge cases, namespace handling, malformed feeds |
| Salary parsing from natural text | Regex extraction of "$X–$Y" | Remotive/RemoteOK APIs with validated fields; manual import has structured salary fields | Natural text extraction is fragile; "salary $50k–$120k" has too many variants |
| Role keyword matching | Manual hardcoded if/elif chains | `in` operator against keyword lists from profile_seed; abstract to RoleKeywordFilter class | Maintainability; profile_seed already has canonical keywords; decouple from connector code |
| Feed URL management | Hardcoded URLs in source classes | Config file (config_sources.yaml); sources read from config | Feed URLs change; centralized config enables operator updates without code changes |
| Manual import validation | Ad-hoc JSON field checks | JSON schema validation (jsonschema library is stdlib-replaceable with manual checks) | Prevents operator typos; clear error messages |
| Date parsing (RFC 2822 → ISO 8601) | Regex or custom parsing | `dateutil.parser.isoparse()` (already in requirements.txt from Phase 2) or `strptime` for known format | dateutil handles timezone ambiguity; strptime works for RFC 2822 (known format) |

---

## Common Pitfalls

### Pitfall 1: RSS Feed Namespace Issues (Atom vs RSS)

**What goes wrong:** Atom feeds use namespaces; RSS does not. Parser fails on Atom feed with "element not found" errors.

**Why it happens:** No explicit namespace handling in XML queries.

**How to avoid:**
- Check feed root element: `<rss>` (RSS) vs `<feed>` (Atom)
- For Atom, include namespace in XPath: `.//'{http://www.w3.org/2005/Atom}entry'`
- Or use relative path that works for both: `.//item` (RSS) + `.//entry` (Atom)
- Test with sample feeds from all three sources before Phase 3 wave 0

**Example:**
```python
root = ET.fromstring(resp.content)
# Try RSS first
items = root.findall(".//item")
if not items:
    # Fall back to Atom
    items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
```

---

### Pitfall 2: Date Format Inconsistencies

**What goes wrong:** Remotive/We Work Remotely use RFC 2822 (`Tue, 14 Jun 2026 10:00:00 GMT`); RemoteOK API uses Unix timestamp. Normalization fails or timestamps are incorrect.

**Why it happens:** No central date conversion function.

**How to avoid:**
- **Phase 3 (now):** Add `_normalize_timestamp(raw_ts, source: str) -> str` function in `fetch.py` (like Phase 2's `infer_remote_status`)
- Call from each source's normalization step
- Log any parse failures; fallback to `datetime.utcnow().isoformat() + "Z"`
- Test with real feed data for each source

**Example:**
```python
def _normalize_timestamp(raw_ts, source: str) -> str:
    """Convert any timestamp format to ISO 8601 UTC."""
    if not raw_ts:
        return datetime.utcnow().isoformat() + "Z"
    
    if isinstance(raw_ts, int):
        # Unix timestamp (RemoteOK)
        return datetime.fromtimestamp(raw_ts, tz=timezone.utc).isoformat() + "Z"
    elif isinstance(raw_ts, str):
        # RFC 2822 (Remotive, We Work Remotely) or ISO (others)
        try:
            # Try RFC 2822 first
            dt = datetime.strptime(raw_ts, "%a, %d %b %Y %H:%M:%S %Z")
            return dt.isoformat() + "Z"
        except:
            # Fall back to dateutil
            from dateutil import parser as dateutil_parser
            try:
                dt = dateutil_parser.isoparse(raw_ts)
                return dt.isoformat() + "Z"
            except:
                logger.warning(f"Timestamp parse failed: {raw_ts}; using now")
                return datetime.utcnow().isoformat() + "Z"
    else:
        return datetime.utcnow().isoformat() + "Z"
```

---

### Pitfall 3: Manual Import File Missing or Unreadable

**What goes wrong:** Operator hasn't created `data/manual_imports.jsonl` yet; or file has encoding issues. Fetch fails.

**Why it happens:** Manual source is new; operator may forget to create file or use wrong encoding.

**How to avoid:**
- **ManualImportSource.fetch():** Check file existence; return graceful error (don't raise)
- Open with explicit encoding (`utf-8`); catch UnicodeDecodeError
- Create `.gitignore` entry: `TARIQ__career_radar/data/manual_imports.jsonl`
- Add `.gitkeep` stub file so directory is tracked (or use `data/.gitkeep`)
- Document in README: "To import: `touch data/manual_imports.jsonl && echo '...' >> data/manual_imports.jsonl`"

**Example (already in code above):**
```python
if not self.import_file_path.exists():
    return SourceResult(
        source_name=self.name,
        opportunities=[],
        errors=[f"Import file not found: {self.import_file_path}"],
    )
```

---

### Pitfall 4: RSS Feed URL Outdated or Moved

**What goes wrong:** Feed URL in config becomes stale (feed was moved or retired). Source returns 404. Operator doesn't notice.

**Why it happens:** Feed URLs can change; no validation at config load time.

**How to avoid:**
- Log HTTP status at source fetch time: "Remotive: HTTP 404 — feed URL may be stale"
- For 404: add to blocked_sources with clear message
- Log once per run; don't hammer retry on 404
- Document known feed URLs in code comments with last-verified dates
- Phase 3 validates feeds against live endpoints before Phase 4 planning (smoke test)

**Example:**
```python
if resp.status_code == 404:
    return SourceResult(
        source_name=self.name,
        opportunities=[],
        errors=[f"Feed not found (404): {self.feed_url} — verify URL in config"],
        rate_limited=False,
    )
```

---

### Pitfall 5: Role Keyword Filter Too Strict (Filters Out Good Roles)

**What goes wrong:** Opportunity "Operations Engineer" doesn't match profile keyword "operations manager"; gets filtered as out-of-scope.

**Why it happens:** Exact substring match is inflexible; typos or different wordings slip through.

**How to avoid:**
- **Phase 3 (now):** Use exact substring match for simplicity; document in README
- For Phase 4+: consider fuzzy matching or multi-keyword AND/OR logic
- **Phase 3 test:** Create fixtures with known in-scope/out-of-scope titles; validate filter logic
- Log filter results to `filter_summary`; operator can review and adjust profile_seed if needed
- Recommend: start with low threshold; tune after first few runs

**Example (current approach, correct for Phase 3):**
```python
# Exact keyword match
for keyword in keywords:
    if keyword.lower() in title_lower:
        matched = True
        break
```

---

### Pitfall 6: Salary Annualization from Hourly Rates (Manual Import)

**What goes wrong:** Operator imports hourly rates (e.g., Outlier: "$30–$60/hour") without converting to annual. Scoring uses hourly values as if annual (wildly inflates salary).

**Why it happens:** Operator forgets to convert; or schema doesn't enforce `salary_per` field.

**How to avoid:**
- **ManualImportSource (already in code above):** Check `salary_per` field; convert hourly → annual if needed
  - Hour → Annual: `salary * 40 hours/week * 52 weeks/year`
  - E.g., $30/hr → $62,400/year
- Default `salary_per = "annual"` if omitted
- Log conversion: "Converted $30–$60/hour to $62,400–$124,800/year"
- Document in README with examples

---

## Code Examples

### Example 1: Remotive RSS Source (Concrete)

**File:** `TARIQ__career_radar/radar/sources/rss_remotive.py` (or inline RSSSource subclass)

```python
"""rss_remotive.py — Remotive RSS feed source for TARIQ Career Radar."""
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

from .base import BaseSource, OpportunityRaw, SourceResult

class RemoativeSource(BaseSource):
    """Remotive RSS feed source (SRC-02)."""
    
    name = "remotive"
    
    def __init__(self, config: dict) -> None:
        self.feed_url = config.get("feed_url", "https://remotive.com/remote-jobs/rss-feed")
        self.enabled = bool(config.get("enabled", False))
    
    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch and parse Remotive RSS feed."""
        opportunities = []
        errors = []
        
        try:
            resp = requests.get(self.feed_url, timeout=30)
            resp.raise_for_status()
            
            root = ET.fromstring(resp.content)
            
            for item in root.findall(".//item"):
                try:
                    title = item.findtext("title", "").strip()
                    link = item.findtext("link", "").strip()
                    pub_date = item.findtext("pubDate", "").strip()
                    company = item.findtext("company", "Unknown").strip()
                    
                    if not title or not link:
                        errors.append("Item missing title or link")
                        continue
                    
                    # Parse date
                    access_date = self._parse_rfc2822(pub_date)
                    
                    opp = OpportunityRaw(
                        title=title,
                        company=company,
                        location="Remote",  # Remotive = remote jobs by definition
                        source_url=link,
                        source=self.name,
                        source_type="rss_feed",
                        salary_usd_low=None,
                        salary_usd_high=None,
                        raw_payload={"pub_date": pub_date},
                    )
                    opportunities.append(opp)
                except Exception as parse_exc:
                    errors.append(f"Parse error on item: {parse_exc}")
            
            return SourceResult(
                source_name=self.name,
                opportunities=opportunities,
                errors=errors,
            )
        
        except requests.Timeout:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Feed request timeout: {self.feed_url}"],
            )
        except Exception as exc:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Unexpected error: {type(exc).__name__}: {exc}"],
            )
    
    @staticmethod
    def _parse_rfc2822(date_str: str) -> str:
        """Convert RFC 2822 to ISO 8601 UTC."""
        if not date_str:
            return datetime.utcnow().isoformat() + "Z"
        try:
            dt = datetime.strptime(date_str.strip(), "%a, %d %b %Y %H:%M:%S %Z")
            return dt.isoformat() + "Z"
        except:
            return datetime.utcnow().isoformat() + "Z"
```

### Example 2: Manual Import Source

**File:** `TARIQ__career_radar/radar/sources/manual_import_source.py`

```python
"""manual_import_source.py — Operator manual JSONL import for TARIQ Career Radar."""
import json
from pathlib import Path

from .base import BaseSource, OpportunityRaw, SourceResult

class ManualImportSource(BaseSource):
    """Operator-provided JSONL import source (SRC-03)."""
    
    name = "manual"
    
    def __init__(self, config: dict) -> None:
        self.import_file_path = Path(config.get("import_file_path", ""))
        self.enabled = bool(config.get("enabled", False))
    
    def fetch(self, constraints: dict) -> SourceResult:
        """Read and parse JSONL file."""
        opportunities = []
        errors = []
        
        if not self.import_file_path.exists():
            # Graceful: file doesn't exist yet (operator hasn't populated it)
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Import file not found: {self.import_file_path}"],
            )
        
        try:
            with open(self.import_file_path, "r", encoding="utf-8") as fh:
                for line_num, line in enumerate(fh, start=1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Validate required fields
                        if "title" not in record or "source_url" not in record:
                            errors.append(
                                f"Line {line_num}: missing required field (title, source_url)"
                            )
                            continue
                        
                        # Handle salary conversion (hourly → annual if needed)
                        salary_low = record.get("salary_usd_low")
                        salary_high = record.get("salary_usd_high")
                        salary_per = record.get("salary_per", "annual").lower()
                        
                        if salary_per == "hour" and salary_low is not None:
                            salary_low = salary_low * 40 * 52
                            if salary_high is not None:
                                salary_high = salary_high * 40 * 52
                        
                        opp = OpportunityRaw(
                            title=record.get("title", ""),
                            company=record.get("company", "Unknown"),
                            location=record.get("location", "Remote"),
                            source_url=record.get("source_url", ""),
                            source=self.name,
                            source_type="manual",
                            salary_usd_low=salary_low,
                            salary_usd_high=salary_high,
                            raw_payload=record,
                        )
                        opportunities.append(opp)
                    
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: invalid JSON — {e}")
        
        except Exception as exc:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Error reading import file: {type(exc).__name__}: {exc}"],
            )
        
        return SourceResult(
            source_name=self.name,
            opportunities=opportunities,
            errors=errors,
        )
```

### Example 3: Role Keyword Filter

**File:** `TARIQ__career_radar/radar/stages/filter.py`

```python
"""filter.py — Role-keyword filtering for SRC-06."""
import logging

from radar.config import load_profile_seed

logger = logging.getLogger(__name__)

def run_filter(opportunities: list[dict], profile_seed: dict = None) -> dict:
    """Filter opportunities by role keyword match (SRC-06).
    
    Args:
        opportunities: List of normalized opportunity dicts from fetch stage.
        profile_seed: Profile dict with role_keywords; defaults to load_profile_seed().
    
    Returns:
        Dict with in_scope, out_of_scope, and filter_summary.
    """
    if profile_seed is None:
        try:
            profile_seed = load_profile_seed()
        except ValueError as e:
            logger.warning("Failed to load profile seed; skipping filter: %s", e)
            return {
                "in_scope": opportunities,
                "out_of_scope": [],
                "filter_summary": {
                    "total": len(opportunities),
                    "in_scope_count": len(opportunities),
                    "out_of_scope_count": 0,
                    "filter_rate": 1.0,
                    "note": "Filter disabled (profile seed unavailable)",
                },
            }
    
    role_keywords = profile_seed.get("role_keywords", {})
    in_scope = []
    out_of_scope = []
    
    for opp in opportunities:
        title_lower = (opp.get("title", "") or "").lower()
        
        # Check if title contains any keyword from profile
        matched = False
        matched_group = None
        
        for group_name, keywords in role_keywords.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    matched = True
                    matched_group = group_name
                    break
            if matched:
                break
        
        if matched:
            opp["matched_role_group"] = matched_group
            in_scope.append(opp)
        else:
            out_of_scope.append(opp)
    
    logger.info(
        "Role filter: %d in-scope, %d out-of-scope (%.1f%% pass rate)",
        len(in_scope),
        len(out_of_scope),
        100 * len(in_scope) / max(len(opportunities), 1),
    )
    
    return {
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "filter_summary": {
            "total": len(opportunities),
            "in_scope_count": len(in_scope),
            "out_of_scope_count": len(out_of_scope),
            "filter_rate": len(in_scope) / max(len(opportunities), 1),
        },
    }
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.0+ (already in NIZAM root) |
| Config file | `TARIQ__career_radar/conftest.py` (augmented with Phase 3 fixtures) |
| Quick run | `pytest TARIQ__career_radar/tests/test_sources.py::test_rss_remotive_mocked -x` (< 5 sec) |
| Full suite | `pytest TARIQ__career_radar/tests/ -v` (< 60 sec) |

### Phase 3 Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **SRC-02** | RemoativeSource fetches RSS feed; parses XML; returns SourceResult | unit (mocked HTTP) | `pytest tests/test_sources.py::test_remotive_rss_mocked -x` | Wave 0 RED |
| **SRC-02** | WeWorkRemotelySource fetches RSS feed; normalizes without company name | unit (mocked HTTP) | `pytest tests/test_sources.py::test_weworkremotely_rss_mocked -x` | Wave 0 RED |
| **SRC-02** | RemoteOKSource fetches JSON API; parses salary field; normalizes | unit (mocked HTTP) | `pytest tests/test_sources.py::test_remoteok_api_mocked -x` | Wave 0 RED |
| **SRC-03** | ManualImportSource reads JSONL file; parses valid records | unit | `pytest tests/test_sources.py::test_manual_import_valid_jsonl -x` | Wave 0 RED |
| **SRC-03** | ManualImportSource handles missing file gracefully (no error raised) | unit | `pytest tests/test_sources.py::test_manual_import_file_not_found -x` | Wave 0 RED |
| **SRC-03** | ManualImportSource rejects malformed JSON; logs error; continues | unit | `pytest tests/test_sources.py::test_manual_import_malformed_json -x` | Wave 0 RED |
| **SRC-06** | RoleKeywordFilter matches title against profile keywords; returns in-scope list | unit | `pytest tests/test_sources.py::test_role_filter_matches -x` | Wave 0 RED |
| **SRC-06** | RoleKeywordFilter rejects out-of-scope titles | unit | `pytest tests/test_sources.py::test_role_filter_rejects -x` | Wave 0 RED |
| **SRC-02** | RSS parse fails gracefully on malformed XML; logged to blocked_sources | integration | `pytest tests/test_sources.py::test_rss_malformed_xml_graceful -x` | Wave 0 RED |

### Test Fixtures & Mocking Strategy

**Mock RSS Responses (recorded XML files):**

```
tests/fixtures/
├── remotive_sample_rss.xml       # Sample Remotive RSS feed
├── weworkremotely_sample_rss.xml # Sample We Work Remotely RSS feed
├── remoteok_sample_response.json  # Sample RemoteOK JSON API response
└── manual_import_sample.jsonl     # Sample JSONL manual import
```

**Fixture content example (remotive_sample_rss.xml):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Remotive Remote Jobs</title>
    <item>
      <title>Senior AI Operations Manager</title>
      <link>https://remotive.com/remote-jobs/123456</link>
      <company>Acme Corp</company>
      <pubDate>Tue, 14 Jun 2026 10:00:00 GMT</pubDate>
      <description>Full job description...</description>
    </item>
  </channel>
</rss>
```

**conftest.py augmentation (Phase 3):**

```python
@pytest.fixture
def mock_remotive_rss(fixtures_dir: Path) -> str:
    """Load recorded Remotive RSS XML from disk."""
    with open(fixtures_dir / "remotive_sample_rss.xml") as fh:
        return fh.read()

@pytest.fixture
def fake_rss_get(monkeypatch):
    """Factory for mocking requests.get to return RSS content."""
    def make_fake_get(rss_content: str):
        def fake_get(*args, **kwargs):
            resp = unittest.mock.MagicMock()
            resp.status_code = 200
            resp.content = rss_content.encode("utf-8")
            resp.raise_for_status.side_effect = None
            return resp
        return fake_get
    return make_fake_get

@pytest.fixture
def manual_import_fixture(tmp_path: Path) -> Path:
    """Create a temporary manual_imports.jsonl file for testing."""
    import_file = tmp_path / "manual_imports.jsonl"
    with open(import_file, "w") as fh:
        fh.write('{"title": "AI Evaluator", "company": "Outlier", "source_url": "https://outlier.ai/jobs/1"}\n')
        fh.write('{"title": "Data Annotator", "company": "DataAnnotation", "source_url": "https://data.annotation/jobs/1"}\n')
    return import_file
```

### Sampling Rate

- **Per task commit:** Run RSS + manual tests only (`test_sources.py::test_rss_* + test_manual_*`) — < 5 sec
- **Per wave merge:** Full `pytest TARIQ__career_radar/tests/ -v` (all phases) — < 60 sec
- **Phase gate:** Full suite green + manual smoke test (fetch real Remotive RSS if network available in CI) before Phase 4 plan

### Wave 0 Gaps (TDD RED — Test Files to Create)

**Tests (collectible but failing until Wave 1/2 implementation):**

- [ ] `tests/test_sources.py::test_remotive_rss_mocked` — RemoativeSource + xml.etree parsing
- [ ] `tests/test_sources.py::test_weworkremotely_rss_mocked` — WeWorkRemotelySource (no company field)
- [ ] `tests/test_sources.py::test_remoteok_api_mocked` — RemoteOKSource JSON API + salary parsing
- [ ] `tests/test_sources.py::test_manual_import_valid_jsonl` — ManualImportSource reads .jsonl
- [ ] `tests/test_sources.py::test_manual_import_file_not_found` — Graceful degradation (no error raised)
- [ ] `tests/test_sources.py::test_manual_import_malformed_json` — Rejects bad JSON; logs + continues
- [ ] `tests/test_sources.py::test_role_filter_matches` — RoleKeywordFilter matches in-scope titles
- [ ] `tests/test_sources.py::test_role_filter_rejects` — RoleKeywordFilter rejects out-of-scope
- [ ] `tests/test_sources.py::test_rss_malformed_xml_graceful` — Graceful XML parse failure
- [ ] `tests/test_sources.py::test_run_fetch_with_tier2_sources` — Integration: fetch all sources + filter

**Fixtures:**

- [ ] `tests/fixtures/remotive_sample_rss.xml` — Recorded Remotive RSS (1 item)
- [ ] `tests/fixtures/weworkremotely_sample_rss.xml` — Recorded We Work Remotely RSS (1 item)
- [ ] `tests/fixtures/remoteok_sample_response.json` — Recorded RemoteOK API response (1 job)
- [ ] `tests/fixtures/manual_import_sample.jsonl` — Sample JSONL (2 records)
- [ ] `tests/fixtures/malformed_rss.xml` — Intentionally invalid XML (for error handling test)
- [ ] `conftest.py` augmentation — mock_remotive_rss, fake_rss_get, manual_import_fixture

**Config & Code:**

- [ ] `radar/sources/rss_source.py` — Base RSSSource ABC (or inline per-feed sources)
- [ ] `radar/sources/remotive_source.py` (or combined in rss_source.py)
- [ ] `radar/sources/weworkremotely_source.py` (or combined)
- [ ] `radar/sources/remoteok_source.py` (or combined)
- [ ] `radar/sources/manual_import_source.py` — ManualImportSource class
- [ ] `radar/stages/filter.py` — RoleKeywordFilter stage + run_filter()
- [ ] `radar/config_sources.yaml` augmentation — tier_2_rss, manual_import, role_filter sections
- [ ] `.gitignore` additions — `TARIQ__career_radar/data/manual_imports.jsonl`

---

## Open Questions

1. **RSS base class vs per-feed subclasses:** Single configurable RSSSource(name, feed_url) or separate Remotive/WeWorkRemotely/RemoteOK classes?
   - **Recommendation:** Separate classes (RemotiveSource, WeWorkRemotelySource, RemoteOKSource) for clarity and future per-feed customization; mirrors Phase 2 pattern (GreenhouseSource, LeverSource, etc.)

2. **Role filter strictness (Phase 3 vs Phase 4):** Exact keyword match now, or use fuzzy matching (RapidFuzz)?
   - **Recommendation:** Exact keyword match for Phase 3 (deterministic, simple); RapidFuzz in Phase 4 for dedup handles fuzzy title matching anyway

3. **Manual import frequency:** Read once per run, or continuous append?
   - **Recommendation:** Read once per run (consistent with other sources); operator appends before next run if importing new roles

4. **Out-of-scope opportunity logging:** Discard, log, or return separately?
   - **Recommendation:** Return separately in filter_summary; log count; don't discard (transparency for operator)

5. **RSS 429 rate-limiting:** Should we add exponential backoff for RSS feeds?
   - **Recommendation:** Yes, reuse BaseSource._exponential_backoff() method from Phase 2; RSS feeds are tolerant (daily updates), but good citizenship if fetching multiple feeds

---

## Sources

### Primary (HIGH confidence)

- [Remotive RSS Feed](https://remotive.com/remote-jobs/rss-feed) — Verified live 2026; clean RSS structure
- [We Work Remotely RSS Feed](https://weworkremotely.com/remote-job-rss-feed) — Verified live 2026; official attribution required
- [RemoteOK JSON API](https://remoteok.com/remote-api-jobs) — Verified live 2026; includes salary (user-provided)
- [Python xml.etree.ElementTree docs](https://docs.python.org/3/library/xml.etree.elementtree.html) — Stdlib XML parsing reference
- [RFC 2822 (Date Format)](https://tools.ietf.org/html/rfc2822) — email date standard used in RSS feeds
- TARIQ__career_radar Phase 2 code (in-repo) — BaseSource, SourceResult, GreenhouseSource, LeverSource patterns
- TARIQ__career_radar Phase 1 code (in-repo) — config.load_profile_seed(), data/profile_cache.json structure

### Secondary (MEDIUM confidence)

- STACK.md (research doc) — Remotive API availability, We Work Remotely details, RemoteOK structure
- ARCHITECTURE.md (research doc) — Opportunity schema, salary_evidence_type enum includes "rss_feed"

### Tertiary (LOW confidence — flags for validation)

- None; all feeds verified against live endpoints.

---

## Metadata

**Confidence breakdown:**
- **Tier 2 RSS endpoints:** HIGH (all verified live 2026)
- **Stdlib xml.etree parsing:** HIGH (stable, proven, handles RSS/Atom)
- **Manual import JSONL pattern:** HIGH (mirrors Phase 2 patterns)
- **Role-keyword filter logic:** MEDIUM-HIGH (profile_seed structure validated; exact match logic simple)
- **Date parsing (RFC 2822):** HIGH (standard format; dateutil already available)
- **Feed URL stability:** MEDIUM (feeds can move; graceful error handling mitigates)

**Research date:** 2026-06-15  
**Valid until:** 2026-07-15 (30 days; feeds are stable endpoints)  
**Reviewed against:** REQUIREMENTS.md, STACK.md, ARCHITECTURE.md, Phase 1–2 RESEARCH.md, Phase 2 code, profile_cache.json

---

*Research completed: 2026-06-15*  
*Ready for Phase 3 planning*
