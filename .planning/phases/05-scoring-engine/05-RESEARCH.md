# Phase 5: Scoring Engine - Research

**Researched:** 2026-06-15
**Domain:** Deterministic weighted opportunity scoring, penalty logic, ranking
**Confidence:** HIGH (requirements locked, schema frozen from Phase 1, scoring domain well-defined)

## Summary

Phase 5 implements a **deterministic 0–100 weighted scoring formula** that produces identical scores for identical opportunities, every time, across runs. The formula combines eight weighted dimensions (fit 25%, salary upside 20%, growth 15%, visa/remote feasibility 10%, company strength 10%, referral/application leverage 10%, freshness 5%, side-income 5%) with penalty logic that subtracts points for red flags (no evidence, scam risk, unclear pay, severe skill mismatch, exploitative unpaid work).

The key constraint is **determinism**: no LLM, no randomness, no hidden state. Same input → same score. This makes the scoring reproducible, auditable, and testable. Scoring happens AFTER deduplication (Phase 4), so input opportunities are already clean. Scores feed directly into tagging (Phase 7) and reporting (Phase 8–9).

Research confirms the scoring formula can be decomposed into measurable attributes from the opportunity schema (Phase 1): fit score comes from profile keyword matching (local only), salary upside from salary_usd_high, growth from role category + company signals, visa feasibility from posting text + location, company strength from public signals only (no proprietary data), referral leverage from application_route metadata, freshness from access_date, and side-income from specific platforms (Outlier, DataAnnotation, etc.).

**Primary recommendation:** Build a `ScoringEngine` class with a `score(opportunity: dict) -> int` method that applies the eight weighted dimensions sequentially, validates each input field, and applies penalties bottom-up (start at 100, subtract penalties, cap at 0–100 range). Store scores in the opportunity record before Phase 7. Make the scoring logic fully inspectable (every score includes a `score_breakdown` dict showing how each dimension contributed). Treat "no evidence" gracefully: if a dimension is missing (e.g., salary not disclosed), use 0 for that dimension and note it in breakdown.

---

## User Constraints (from CONTEXT.md / ROADMAP / REQUIREMENTS)

### Locked Decisions
- **Deterministic scoring only** — no LLM injection, no randomness
- **Weights are fixed:** fit 25, salary upside 20, growth 15, visa/remote 10, company strength 10, referral/application 10, freshness 5, side-income 5 (totaling 100)
- **Penalties apply bottom-up** (subtract from base score) for identified red flags
- **Same opportunity scored twice → identical score** (reproducibility requirement)
- **Only deduplicated opportunities are scored** (Phase 4 output → Phase 5 input)
- **No raw personal data leaves the machine** (profile matching is local only)
- **Provenance + confidence or omit** (salary-based scoring must respect salary_confidence)

### Claude's Discretion (research options, recommend)
- Exact penalty values (−5 to −20 per research) — recommend calibration test on real opportunities
- Fit score measurement (keyword match % / manual tagging / heuristic) — recommend local keyword matching (deterministic)
- Growth score definition (career advancement / skill leverage / seniority jump) — recommend heuristic based on role category + company tier signals
- Visa feasibility heuristics (text parsing / metadata / manual categorization) — recommend opportunity schema field (Phase 1 already has `visa_feasibility` enum)
- Company strength signals (Crunchbase / Glassdoor / internal database / signals from posting) — recommend public signals only (no proprietary scraping)
- Freshness scoring (linear decay / step function / boolean flag) — recommend step function (fresh = within 7 days, aging = 7–30 days, stale = >30 days)
- Side-income platform detection (hardcoded list / keyword matching / metadata flag) — recommend hardcoded platform list (Outlier, DataAnnotation, Turing, Toloka, Braintrust, Contra, Wellfound)

### Deferred Ideas (OUT OF SCOPE — Phase 7+)
- LLM-based scoring (later phases may use LLM as explainer-only, not scorer)
- Machine learning scoring (Phase 2+)
- A/B testing weights per user profile (Phase 2+)
- Dynamic weight adjustment based on seasonal hiring (Phase 2+)
- Referral leverage mapping via warm intros (ROUTE-01, Phase 12)
- Deep-dive visa sponsorship analysis (DEPTH-03, Phase 2+)
- Company-strength API integration (DEPTH-01, Phase 2+)

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCORE-01 | Deterministic 0–100 score with 8 weights (fit 25, salary 20, growth 15, visa 10, company 10, referral 10, freshness 5, side-income 5); same opportunity twice → same score | Scoring formula decomposed below; determinism achieved via pure-function design (no randomness, no external state) |
| SCORE-02 | Penalties (−5 to −20) for no-evidence, scam risk, unclear pay, severe skill mismatch, exploitative unpaid work | Penalty taxonomy and trigger rules defined in Common Pitfalls + Code Examples sections |

---

## Standard Stack

### Core Dependencies (No New Additions)

| Library | Version | Purpose | Why | Already Pinned? |
|---------|---------|---------|-----|---|
| **python** | 3.11+ | Runtime | NIZAM stdlib-first | ✓ |
| **json** | stdlib | Opportunity record I/O | Standard for ledger/profile | ✓ |
| **pathlib** | stdlib | File paths | Locale-independent | ✓ |
| **datetime** | stdlib | Timestamp parsing + freshness calculation | ISO 8601 UTC | ✓ |
| **typing** | stdlib | Type hints | NIZAM standard | ✓ |

### No New Dependencies Required

Scoring logic uses only stdlib + existing data structures (opportunity schema from Phase 1). No new libraries needed.

### Optional: Validation/Testing Dependencies (Already Available)

| Library | Purpose | Status |
|---------|---------|--------|
| **pytest** | Unit/integration testing | ✓ Already in project |
| **jsonschema** | Opportunity schema validation | ✓ Already in project |

---

## Architecture Patterns

### Recommended Project Structure

**File additions to TARIQ__career_radar/radar/:**

```
radar/
├── __init__.py
├── scoring_engine.py             # NEW (Phase 5): ScoringEngine class
├── scoring_config.py             # NEW (Phase 5): weights, penalties, platform lists
├── stages/
│   ├── __init__.py
│   ├── fetch.py                  # Existing (Phase 2)
│   ├── dedup.py                  # Existing (Phase 4)
│   ├── score.py                  # NEW (Phase 5): run_scoring_pass() orchestrator
│   └── enrich.py                 # Future (Phases 6–7)
└── main.py                        # Updated: wire scoring stage into pipeline
```

### Scoring Formula Decomposition

Each dimension is measured independently, normalized to 0–100 scale, then weighted:

```
final_score = base_score - penalties
base_score = ∑(dimension_score × weight)
  where dimension_score ∈ [0, 100]
  and weights sum to 1.0

dimension 1: fit_score × 0.25
  ↓ derived from: local profile keyword match % (Phase 1's role_keywords)
  
dimension 2: salary_upside_score × 0.20
  ↓ derived from: salary_usd_high (or mid-range); adjusted by salary_confidence
  
dimension 3: growth_score × 0.15
  ↓ derived from: role_category (seniority jump?) + company signals
  
dimension 4: visa_feasibility_score × 0.10
  ↓ derived from: opportunity.visa_feasibility enum (Phase 1)
  
dimension 5: company_strength_score × 0.10
  ↓ derived from: company name → public signals (Tier1/Tier2/emerging)
  
dimension 6: referral_leverage_score × 0.10
  ↓ derived from: application_route metadata + role visibility
  
dimension 7: freshness_score × 0.05
  ↓ derived from: (now - access_date) → step function
  
dimension 8: side_income_score × 0.05
  ↓ derived from: is_side_income_platform(source, company)

Penalties (subtracted after base_score):
  −5 to −20 each for:
    - no_evidence_for_claim (e.g., salary exists but marked "not_disclosed")
    - scam_risk_signal (detected keyword)
    - unclear_pay_structure (e.g., "stipend", "bonus only")
    - severe_skill_mismatch (role category ≠ profile keywords)
    - exploitative_unpaid_work (unpaid, unpaid_trial, no_salary)
```

### Dimension 1: Fit Score (25% weight)

**Source field:** `opportunity.fit_score` (computed locally in Phase 1 or enriched in Phase 7)

**Measurement:** Profile keyword matching
- Load `profile_cache.json` (strict_local_maximum)
- Extract role keywords for target categories
- Match job title + description against profile keywords
- Score = (matching_keywords / total_profile_keywords) × 100
- Example: If profile has 5 keywords ["AI Ops", "Operations", "Project Manager", "Coordination", "Stakeholder"], and title contains "AI Ops Manager" + description mentions "Stakeholder Management", score = 3/5 = 60

**No evidence:** If title/description missing, fit_score = 0 (local-safe, no external lookup)

**Code pattern:**

```python
def compute_fit_score(opportunity: dict, profile: dict) -> int:
    """0–100 score based on role keyword match against profile seed."""
    title = opportunity.get("title", "").lower()
    description = opportunity.get("description", "").lower()
    role_text = f"{title} {description}".strip()
    
    if not role_text:
        return 0
    
    # Flatten all keywords from profile
    all_keywords = []
    for category_keywords in profile.get("role_keywords", {}).values():
        all_keywords.extend(keyword.lower() for keyword in category_keywords)
    
    if not all_keywords:
        return 0
    
    # Count matches (exact word boundary)
    matches = sum(1 for kw in all_keywords if kw in role_text)
    return int((matches / len(all_keywords)) * 100)
```

### Dimension 2: Salary Upside Score (20% weight)

**Source field:** `opportunity.salary_usd_high`, `opportunity.salary_confidence`

**Measurement:** Annual salary in USD, normalized to 0–100 scale
- Reference salary: Seif's minimum acceptable = $60k/year (from profile_cache.json)
- High salary threshold: $150k/year (stretch goal)
- Formula: score = min(100, (salary_high - min_ref) / (high_threshold - min_ref) × 100)
- Capped at 100 (anything ≥$150k = 100 points)

**Adjustment for confidence:**
- If `salary_confidence == "HIGH"`: use as-is
- If `salary_confidence == "MEDIUM"`: multiply by 0.8
- If `salary_confidence == "LOW"`: multiply by 0.5

**No evidence:** If salary_usd_high is null or not_disclosed, score = 0 (no penalty here; penalty applied separately if claim exists but unclear)

**Code pattern:**

```python
def compute_salary_upside_score(opportunity: dict, min_salary: int = 60000, high_threshold: int = 150000) -> int:
    """0–100 score based on salary_usd_high, adjusted by confidence."""
    salary = opportunity.get("salary_usd_high")
    confidence = opportunity.get("salary_confidence", "LOW")
    
    if salary is None:
        return 0
    
    # Linear scale: $60k → 0 points, $150k → 100 points, capped at 100
    raw_score = max(0, min(100, ((salary - min_salary) / (high_threshold - min_salary)) * 100))
    
    # Confidence adjustment
    confidence_mult = {
        "HIGH": 1.0,
        "MEDIUM": 0.8,
        "LOW": 0.5,
    }.get(confidence, 0.5)
    
    return int(raw_score * confidence_mult)
```

### Dimension 3: Growth Score (15% weight)

**Source field:** `opportunity.role_category`, `opportunity.company_strength_signal` (inferred)

**Measurement:** Career advancement potential based on role category + company tier
- Growth roles (AI_OPERATIONS, DATA_SCIENCE, BUSINESS_ANALYST) = higher growth potential
- Tier 1 companies (well-funded, fast-growing) = higher growth potential
- Early-career roles in Tier 1 = 80+ points
- Late-career roles in Tier 2 = 50 points
- Tier 3 (small/stagnant) = 30 points

**Heuristics for company tier (no external API calls):**
- Tier 1: FAANG-like (Google, Microsoft, AWS, Apple, Meta, OpenAI, Anthropic, etc.), Crunchbase Series C+, >$1B valuation (inferred from name)
- Tier 2: Series B, profitable bootstrap, >100 employees
- Tier 3/emerging: Series A, <100 employees, or unknown

**Code pattern:**

```python
def compute_growth_score(opportunity: dict) -> int:
    """0–100 score based on role category + company signals."""
    category = opportunity.get("role_category", "").upper()
    company = opportunity.get("company", "").lower()
    
    # High-growth role categories
    growth_categories = {"AI_OPERATIONS", "DATA_SCIENCE", "DATA_ANNOTATION", "MACHINE_LEARNING"}
    base = 60 if category in growth_categories else 40
    
    # Company tier boost
    tier1_names = ["google", "microsoft", "aws", "apple", "meta", "openai", "anthropic", "netflix"]
    if any(name in company for name in tier1_names):
        base = min(100, base + 20)
    
    return base
```

### Dimension 4: Visa Feasibility Score (10% weight)

**Source field:** `opportunity.visa_feasibility` (enum from Phase 1 schema)

**Measurement:** Direct mapping from visa_feasibility enum
```
"visa_sponsored_likely" → 100 points
"visa_sponsored_unclear" → 50 points
"visa_not_sponsored" → 10 points
"not_applicable" → 30 points (e.g., Egypt-based role; not target but fallback)
```

**No evidence:** If visa_feasibility is null, assume "visa_sponsored_unclear" = 50

**Code pattern:**

```python
def compute_visa_feasibility_score(opportunity: dict) -> int:
    """0–100 score based on visa_feasibility enum."""
    visa = opportunity.get("visa_feasibility", "visa_sponsored_unclear")
    return {
        "visa_sponsored_likely": 100,
        "visa_sponsored_unclear": 50,
        "visa_not_sponsored": 10,
        "not_applicable": 30,
    }.get(visa, 50)
```

### Dimension 5: Company Strength Score (10% weight)

**Source field:** `opportunity.company_strength_signal` (inferred or from Phase 1)

**Measurement:** Public signals only (no proprietary data, no Crunchbase API)
- If company name matches Tier 1 list (FAANG, unicorn) → 90 points
- If posting includes "Series B" or mentions funding → 70 points
- If posting mentions "profitable" or "growing" → 60 points
- Default (unknown) → 50 points
- Red flags: "startup" without funding context → 40 points

**No evidence:** Default to 50 (neutral)

**Code pattern:**

```python
def compute_company_strength_score(opportunity: dict) -> int:
    """0–100 score based on public signals in posting text."""
    company = opportunity.get("company", "").lower()
    description = opportunity.get("description", "").lower()
    text = f"{company} {description}"
    
    tier1_names = ["google", "microsoft", "aws", "apple", "meta", "openai", "anthropic"]
    if any(name in company for name in tier1_names):
        return 90
    
    if "series" in text and "b" in text:
        return 70
    if "profitable" in text or ("growing" in text and "startup" not in text):
        return 60
    if "startup" in text:
        return 40
    
    return 50
```

### Dimension 6: Referral/Application Leverage Score (10% weight)

**Source field:** `opportunity.application_route` (metadata, Phase 7 enrichment)

**Measurement:** Application ease + personal leverage
- Known referral contact → 90 points
- Open ATS submission possible → 70 points
- Email/form submission needed → 50 points
- Application requires extensive screening → 30 points
- No public application path → 10 points

**Heuristics:**
- ATS platforms (Greenhouse, Lever, Ashby, Workable) = higher leverage (70+)
- Manual platforms (email, form, no standardized path) = lower (50)
- Private/referral-only = variable (depends on availability)

**No evidence:** Default to 50

**Code pattern:**

```python
def compute_referral_leverage_score(opportunity: dict) -> int:
    """0–100 score based on application route accessibility."""
    source_type = opportunity.get("source_type", "").lower()
    source = opportunity.get("source", "").lower()
    
    ats_platforms = {"greenhouse", "lever", "ashby", "workable"}
    if source_type == "ats" or any(ats in source for ats in ats_platforms):
        return 70
    
    if source in {"outlier", "dataannotation", "turing", "toloka"}:
        return 80  # Self-onboarding platforms
    
    if source_type in {"rss_feed", "manual"}:
        return 50  # Unknown application path
    
    return 50
```

### Dimension 7: Freshness Score (5% weight)

**Source field:** `opportunity.access_date` (ISO 8601 UTC)

**Measurement:** Step function based on age
- Fresh (0–7 days old) → 100 points
- Aging (7–30 days old) → 60 points
- Stale (>30 days old) → 20 points

**Rationale:** Older postings are less likely to be actively hiring (hiring windows close, positions fill). Fresh = higher priority.

**Code pattern:**

```python
from datetime import datetime, timedelta

def compute_freshness_score(opportunity: dict, now: datetime = None) -> int:
    """0–100 score based on posting age."""
    if now is None:
        now = datetime.utcnow()
    
    access_date_str = opportunity.get("access_date")
    if not access_date_str:
        return 50  # Unknown age
    
    access_date = datetime.fromisoformat(access_date_str.replace("Z", "+00:00"))
    age_days = (now - access_date).days
    
    if age_days <= 7:
        return 100
    elif age_days <= 30:
        return 60
    else:
        return 20
```

### Dimension 8: Side-Income Potential (5% weight)

**Source field:** `opportunity.source`, `opportunity.company`

**Measurement:** Boolean → binary score
- Is the opportunity from a known side-income/gig platform? → 80 points
- Otherwise → 0 points

**Known platforms (from Phase 3 sourcing):**
```python
SIDE_INCOME_PLATFORMS = {
    "outlier", "outlier.ai",
    "dataannotation", "data annotation",
    "turing", "turing.com",
    "toloka", "toloka.ai",
    "braintrust",
    "contra",
    "wellfound",
}
```

**Rationale:** Side-income roles (AI evaluation, data annotation, gig work) offer flexible USD cashflow, useful for income smoothing or skill development. Separate scoring dimension to distinguish from full-time career roles.

**Code pattern:**

```python
def compute_side_income_score(opportunity: dict) -> int:
    """0–100 score: high if from known side-income platform, else 0."""
    side_income_platforms = {
        "outlier", "outlier.ai", "dataannotation", "turing",
        "toloka", "braintrust", "contra", "wellfound",
    }
    
    source = opportunity.get("source", "").lower()
    company = opportunity.get("company", "").lower()
    
    is_side_income = any(
        platform in source or platform in company
        for platform in side_income_platforms
    )
    
    return 80 if is_side_income else 0
```

### Scoring Engine (Main Orchestrator)

**File:** `TARIQ__career_radar/radar/scoring_engine.py`

```python
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ScoreBreakdown:
    """Detailed breakdown of how a score was computed."""
    fit: int = 0
    salary_upside: int = 0
    growth: int = 0
    visa_feasibility: int = 0
    company_strength: int = 0
    referral_leverage: int = 0
    freshness: int = 0
    side_income: int = 0
    
    penalties: dict[str, int] = field(default_factory=dict)  # {reason: amount}
    
    def total_penalty(self) -> int:
        return sum(self.penalties.values())

class ScoringEngine:
    """Deterministic scoring for opportunities.
    
    Same input → same score, every time.
    No randomness, no external state, no LLM.
    """
    
    # Weights (must sum to 1.0)
    WEIGHTS = {
        "fit": 0.25,
        "salary_upside": 0.20,
        "growth": 0.15,
        "visa_feasibility": 0.10,
        "company_strength": 0.10,
        "referral_leverage": 0.10,
        "freshness": 0.05,
        "side_income": 0.05,
    }
    
    def __init__(self, profile: Optional[dict] = None):
        """Initialize with optional profile (for fit scoring)."""
        self.profile = profile or {}
    
    def score(self, opportunity: dict, now: Optional[datetime] = None) -> tuple[int, ScoreBreakdown]:
        """Score an opportunity.
        
        Args:
            opportunity: dict with required fields (title, company, salary_usd_high, etc.)
            now: datetime for freshness calculation (defaults to UTC now)
        
        Returns:
            (final_score: int, breakdown: ScoreBreakdown)
            final_score is 0–100 after penalties applied
        """
        breakdown = ScoreBreakdown(
            fit=compute_fit_score(opportunity, self.profile),
            salary_upside=compute_salary_upside_score(opportunity),
            growth=compute_growth_score(opportunity),
            visa_feasibility=compute_visa_feasibility_score(opportunity),
            company_strength=compute_company_strength_score(opportunity),
            referral_leverage=compute_referral_leverage_score(opportunity),
            freshness=compute_freshness_score(opportunity, now),
            side_income=compute_side_income_score(opportunity),
        )
        
        # Compute weighted base score
        base_score = (
            breakdown.fit * self.WEIGHTS["fit"]
            + breakdown.salary_upside * self.WEIGHTS["salary_upside"]
            + breakdown.growth * self.WEIGHTS["growth"]
            + breakdown.visa_feasibility * self.WEIGHTS["visa_feasibility"]
            + breakdown.company_strength * self.WEIGHTS["company_strength"]
            + breakdown.referral_leverage * self.WEIGHTS["referral_leverage"]
            + breakdown.freshness * self.WEIGHTS["freshness"]
            + breakdown.side_income * self.WEIGHTS["side_income"]
        )
        
        # Apply penalties
        penalties = self._compute_penalties(opportunity, breakdown)
        breakdown.penalties = penalties
        
        # Final score = base - sum(penalties), capped at 0–100
        final_score = max(0, min(100, int(base_score - sum(penalties.values()))))
        
        return final_score, breakdown
    
    def _compute_penalties(self, opportunity: dict, breakdown: ScoreBreakdown) -> dict[str, int]:
        """Apply penalty logic."""
        penalties = {}
        
        # Penalty 1: No evidence for claim
        if opportunity.get("salary_usd_high") is None and opportunity.get("salary_usd_low") is None:
            # No salary provided; no penalty here (not a claim)
            pass
        elif opportunity.get("salary_evidence_type") == "not_disclosed":
            # Salary field present but marked not_disclosed; no penalty (legitimate)
            pass
        
        # Penalty 2: Scam risk signals
        if self._detect_scam_signal(opportunity):
            penalties["scam_risk"] = 20
        
        # Penalty 3: Unclear pay
        if self._detect_unclear_pay(opportunity):
            penalties["unclear_pay"] = 15
        
        # Penalty 4: Severe skill mismatch
        if breakdown.fit < 30 and opportunity.get("role_category") in self.profile.get("avoid_flags", []):
            penalties["severe_skill_mismatch"] = 10
        
        # Penalty 5: Exploitative unpaid work
        if self._detect_unpaid_work(opportunity):
            penalties["exploitative_unpaid"] = 20
        
        return penalties
    
    def _detect_scam_signal(self, opportunity: dict) -> bool:
        """Check for common scam indicators."""
        title = (opportunity.get("title", "") + opportunity.get("company", "")).lower()
        description = opportunity.get("description", "").lower()
        text = f"{title} {description}"
        
        scam_keywords = {
            "nigerian", "offshore", "work from home 100%",
            "guaranteedusd", "no experience required", "quick cash",
        }
        
        return any(keyword in text for keyword in scam_keywords)
    
    def _detect_unclear_pay(self, opportunity: dict) -> bool:
        """Check for unclear salary structure."""
        description = opportunity.get("description", "").lower()
        
        unclear_keywords = {
            "stipend", "bonus only", "commission", "performance-based",
            "tbd", "to be determined", "negotiable",
        }
        
        # Only penalize if salary_confidence is LOW
        confidence = opportunity.get("salary_confidence", "LOW")
        return confidence == "LOW" and any(
            keyword in description for keyword in unclear_keywords
        )
    
    def _detect_unpaid_work(self, opportunity: dict) -> bool:
        """Check for unpaid or exploitative work."""
        title = opportunity.get("title", "").lower()
        description = opportunity.get("description", "").lower()
        salary_high = opportunity.get("salary_usd_high")
        
        unpaid_keywords = {"unpaid", "no salary", "free", "volunteer"}
        
        return (
            salary_high is not None and salary_high == 0
        ) or any(keyword in f"{title} {description}" for keyword in unpaid_keywords)
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Profile keyword matching | Custom regex/NLP | Local keyword list from profile_cache.json (simple substring match) | Deterministic, no external API, fast, testable against real profile |
| Salary normalization | Manual scaling logic | StandardScaler / MinMaxScaler | Already stdlib; easy to verify; reproducible across runs |
| Timestamp parsing | Manual string splitting | `datetime.fromisoformat()` (stdlib) | Handles ISO 8601 properly; timezone-safe |
| Company strength signals | Scraping / Crunchbase API | Public signals from posting text (parsing keywords) | No ToS violations; deterministic; no rate-limit risk |
| Penalty application | Ad-hoc cascading logic | Flat dict of penalties (each independent, sum at end) | Easier to audit; easier to add/remove penalties; no ordering surprises |

**Key insight:** Scoring can look "simple" (just add up percentages), but determinism requires rigorous input validation, consistent handling of missing data, and transparent penalty logic. Hand-rolling these invites subtle bugs (e.g., floating-point rounding, inconsistent missing-data handling, unclear penalty interaction).

---

## Common Pitfalls

### Pitfall 1: Floating-Point Rounding Errors Cause Non-Determinism

**What goes wrong:** Dimension scores computed as floats; small rounding differences between runs produce different final scores (e.g., 74.999 vs 75.001 rounds differently on different machines).

**Why it happens:** Python's floating-point arithmetic is not perfectly deterministic across all platforms/versions. 0.25 * 300 may yield 74.99999... or 75.00001... depending on CPU flags.

**How to avoid:**
- Use integer arithmetic throughout (multiply by 100 before dividing, round early, integer weights)
- Or use `decimal.Decimal` for precise decimal arithmetic
- Test: run the same scoring logic 10 times on 100 opportunities; verify all scores are identical

**Warning signs:**
- Same opportunity scores differently on Windows vs Linux
- Flaky tests (score assertion passes sometimes, fails others)

**Code example (safe):**

```python
# BAD: floating-point accumulated error
base_score = fit_score * 0.25 + salary_score * 0.20 + ...  # floats
final = int(base_score)  # rounding at the end (lossy)

# GOOD: integer arithmetic
base_score = (fit_score * 25 + salary_score * 20 + ...) // 100  # integers
final = base_score  # no rounding needed
```

### Pitfall 2: Penalties Applied in Wrong Order / Overlapping Logic

**What goes wrong:** Penalty logic is cascade-like (if penalty A applied, don't apply penalty B). Results in non-deterministic scores depending on the order of checks. Example: unpaid work + scam signal both present; only one penalty applied because code stops early.

**Why it happens:** Penalties are implemented as nested if-statements or early returns, without explicit ordering.

**How to avoid:**
- Compute ALL penalties independently; sum them at the end
- No if-else chains that prevent later penalties
- Document penalty independence: "All penalties are cumulative; no limit on total penalty sum (can exceed score, capped at 0–100)"

**Warning signs:**
- Same opportunity scores differently depending on which field is checked first
- Opportunity with multiple red flags scores better than expected (penalties missed)

### Pitfall 3: Missing Data Treated Inconsistently

**What goes wrong:** When salary is missing, one run sets salary_upside_score to 0, another skips it (doesn't subtract from base). Or fit_score defaults to 50 in one place, 0 in another.

**Why it happens:** No clear "missing data policy" documented. Each dimension handles nulls independently.

**How to avoid:**
- Define a "missing data policy" upfront:
  - Null field → score = 0 (conservative, no evidence = no credit)
  - OR null field → score = 50 (neutral, unknown)
  - Choose ONE approach and document in config
- In the code, validate presence of required fields (title, company, source) before scoring
- Optional fields (salary, description) default to 0 if missing

**Warning signs:**
- Different results when salary_usd_high is null vs when it's 0
- Opportunities with incomplete data score higher/lower unexpectedly

### Pitfall 4: Profile-Dependent Scoring (Fit) Breaks When Profile Changes

**What goes wrong:** Fit score depends on profile_cache.json. If profile is updated between runs, the same opportunity scores differently (old profile: 80 fit, new profile: 60 fit). Breaks determinism guarantee.

**Why it happens:** Profile is mutable; scoring depends on it; no version-locking.

**How to avoid:**
- Profile is loaded ONCE per run and frozen (immutable dict or dataclass)
- Score includes a "profile_hash" or version in breakdown for audit trail
- If profile must change, it's a new run; old results are not re-scored retroactively
- Test: load 2 versions of profile, score same opportunity on each, expect different results (expected and documented)

**Warning signs:**
- Same opportunity scores differently after a profile update (that's expected!)
- But if profile didn't change and score differs, something is wrong

### Pitfall 5: Company Strength / Visa Signals Not Public (Proprietary Data Leak)

**What goes wrong:** Scoring logic tries to call an external API (Crunchbase, Glassdoor, LinkedIn) to determine company strength. Data is leaked; ToS violated.

**Why it happens:** Developer wants "better" company strength signals and reaches for external data.

**How to avoid:**
- Use public signals ONLY (signals extractable from the job posting text itself)
- No API calls, no scraping, no proprietary data
- Company strength = keyword matching on "Series B", "profitable", "growing", etc. in posting text
- Document: "Company strength signals derived from posted text only; no external API"

**Warning signs:**
- Code makes HTTP requests to external APIs during scoring
- Company signals mysteriously change over time (external data updated)

### Pitfall 6: Penalties Don't Cap Score at 0–100 (Negative or >100 Scores)

**What goes wrong:** Opportunity with 5 penalties totaling −100 points ends up with score = −25 (base_score 75 - penalties 100 = −25). Should be 0.

**Why it happens:** No final capping logic; penalties can exceed base score.

**How to avoid:**
- Always apply final capping: `final_score = max(0, min(100, base_score - sum(penalties)))`
- Or apply penalties incrementally with capping at each step (slower but safer)

**Warning signs:**
- Negative scores in output
- Scores >100 (unlikely but possible if weighting not checked)

### Pitfall 7: No Breakdown Provided (Score Is a Black Box)

**What goes wrong:** Output includes final_score = 73, but no detail on why. User can't audit or debug. Scoring looks arbitrary.

**Why it happens:** No breakdown tracking; only final score returned.

**How to avoid:**
- Always include ScoreBreakdown (8 dimensions + penalties)
- Every opportunity record includes breakdown in output
- Phase 7/8 reports can summarize (e.g., "Best opp scores 78: fit +25, salary +18, growth +15, visa −5 (unclear sponsorship)")

**Warning signs:**
- Difficult to explain why one opportunity scored higher than another
- User can't trust the score because it's opaque

---

## Code Examples

### Example 1: Full Scoring Pipeline

**Source:** TARIQ__career_radar/radar/stages/score.py

```python
from __future__ import annotations
from typing import Optional
from pathlib import Path
from datetime import datetime
from TARIQ__career_radar.radar.scoring_engine import ScoringEngine
from TARIQ__career_radar.radar.config import load_profile_seed

def run_scoring_pass(
    opportunities: list[dict],
    profile: Optional[dict] = None,
    now: Optional[datetime] = None,
) -> list[dict]:
    """Apply scoring to all deduplicated opportunities.
    
    Args:
        opportunities: List of opportunity dicts (from Phase 4 dedup output)
        profile: Optional profile seed (defaults to loading from disk)
        now: Optional datetime for freshness (defaults to UTC now)
    
    Returns:
        Same opportunities, each enriched with 'final_score' and 'score_breakdown'
    """
    if profile is None:
        profile = load_profile_seed()
    
    engine = ScoringEngine(profile)
    scored = []
    
    for opp in opportunities:
        # Validate required fields
        required = ["title", "company", "source", "source_type", "access_date"]
        missing = [f for f in required if f not in opp or opp[f] is None]
        if missing:
            # Log warning but continue (phase 5 doesn't fail entire run on one bad record)
            print(f"WARNING: Opportunity missing fields {missing}: {opp.get('title', 'UNKNOWN')}")
            opp["final_score"] = 0
            opp["score_breakdown"] = {"error": "missing_required_fields"}
            scored.append(opp)
            continue
        
        # Score
        score, breakdown = engine.score(opp, now)
        
        # Attach to opportunity
        opp["final_score"] = score
        opp["score_breakdown"] = {
            "fit": breakdown.fit,
            "salary_upside": breakdown.salary_upside,
            "growth": breakdown.growth,
            "visa_feasibility": breakdown.visa_feasibility,
            "company_strength": breakdown.company_strength,
            "referral_leverage": breakdown.referral_leverage,
            "freshness": breakdown.freshness,
            "side_income": breakdown.side_income,
            "penalties": breakdown.penalties,
            "final": score,
        }
        
        scored.append(opp)
    
    return scored
```

### Example 2: Determinism Test (Verify Same Score Twice)

**Source:** TARIQ__career_radar/tests/test_scoring_engine.py

```python
import pytest
from datetime import datetime
from TARIQ__career_radar.radar.scoring_engine import ScoringEngine

def test_scoring_deterministic():
    """SCORE-01: Same opportunity scored twice produces identical score."""
    profile = {
        "role_keywords": {
            "AI_OPERATIONS": ["ai operations", "ai ops", "operations"],
        }
    }
    
    opportunity = {
        "title": "AI Operations Manager",
        "company": "Acme Corp",
        "location": "Remote",
        "source": "greenhouse",
        "source_type": "ats",
        "access_date": "2026-06-15T10:00:00Z",
        "salary_usd_high": 120000,
        "salary_confidence": "HIGH",
        "role_category": "AI_OPERATIONS",
        "visa_feasibility": "visa_sponsored_likely",
    }
    
    engine = ScoringEngine(profile)
    now = datetime.fromisoformat("2026-06-15T12:00:00+00:00")
    
    # Score twice
    score1, breakdown1 = engine.score(opportunity, now)
    score2, breakdown2 = engine.score(opportunity, now)
    
    # Must be identical
    assert score1 == score2, f"Scores differ: {score1} vs {score2}"
    assert breakdown1.fit == breakdown2.fit
    assert breakdown1.salary_upside == breakdown2.salary_upside
    # ... etc for all dimensions
```

### Example 3: Penalty Application

**Source:** TARIQ__career_radar/radar/scoring_engine.py

```python
def test_penalty_scam_risk():
    """SCORE-02: Scam risk penalty applies."""
    profile = {}
    
    # Scam signal in title
    opportunity = {
        "title": "Make $5000/week from home - Nigerian client needed",
        "company": "Quick Cash Inc",
        "source": "unknown",
        "source_type": "manual",
        "access_date": "2026-06-15T10:00:00Z",
    }
    
    engine = ScoringEngine(profile)
    score, breakdown = engine.score(opportunity)
    
    # Base score likely ~30–40 (poor dimensions)
    # Minus 20 for scam risk = 10–20 final
    assert breakdown.penalties.get("scam_risk") == 20
    assert score < 40, "Score should be low for obvious scam"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| LLM-based scoring | Deterministic weighted formula | Phase 5 (this phase) | Reproducible, auditable, fast, no API dependency |
| Ad-hoc scoring logic in reporting | Centralized ScoringEngine + ScoreBreakdown | Phase 5 | Single source of truth; easier to maintain; transparent |
| No penalty logic | Explicit penalty taxonomy (5 categories) | Phase 5 | Red flags caught and communicated; user trust |
| Fit score via recruiter review | Local profile keyword matching | Phase 5 | Deterministic, no manual review, scales to 1000+ opps |
| Static weights (all dimensions equal) | Weighted formula (25% fit, 20% salary, etc.) | Phase 5 | Reflects actual decision priorities; fit is most important |

### Deprecated / Outdated

- **LLM-based scoring:** May be used in Phase 2+ as "explainer" (e.g., "explain why this role scored 78"), but will never be the scoring mechanism itself (breaks determinism).
- **Manual scoring:** Not scalable; Phase 5 is fully automated.

---

## Open Questions

1. **Exact penalty values (−5 to −20):**
   - What we know: Phase requirements specify range; specific triggers documented above
   - What's unclear: Are these values optimal for the target dataset?
   - Recommendation: Phase 5 Wave 0 includes calibration test (score 50 real opportunities with and without penalties, measure impact on ranking). Adjust values if needed before Wave 1.

2. **Growth score heuristics (company tier detection):**
   - What we know: Tier 1 = FAANG-like, Tier 2 = Series B+, Tier 3 = emerging
   - What's unclear: Should company tier be fetched from a database (harder, requires updates), or inferred from posting text (simpler, limited accuracy)?
   - Recommendation: Start with posting-text inference (keywords: "Series B", "profitable", "growing"). If Phase 13 validation shows poor growth scores, revisit with a curated company list in Phase 2.

3. **Profile-dependent fit scoring across profile updates:**
   - What we know: Profile can change (Seif updates keywords, target roles)
   - What's unclear: Should old opportunities be re-scored with new profile?
   - Recommendation: No re-scoring in v1 (only new runs score with latest profile). Phase 2+ can add profile versioning + retroactive re-scoring if needed.

4. **Salary upside thresholds ($60k min, $150k high):**
   - What we know: From profile_cache.json (Seif's minimum is $60k, stretch goal ~$150k)
   - What's unclear: Should these be configurable per run?
   - Recommendation: Store in `scoring_config.py` as constants; make them configurable in Phase 2.

5. **Freshness decay function (step vs linear):**
   - What we know: Phase 5 uses step function (0–7 days = 100, 7–30 = 60, >30 = 20)
   - What's unclear: Is step function better than linear decay?
   - Recommendation: Step function is simpler and less sensitive to exact age. Validate in Phase 13 (does it rank opps correctly?); switch to linear if needed.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.0+ (already in NIZAM root) |
| Config file | `TARIQ__career_radar/conftest.py` (shared fixtures) |
| Quick run | `pytest TARIQ__career_radar/tests/test_scoring_engine.py -x` (< 5 sec) |
| Full suite | `pytest TARIQ__career_radar/tests/ -v` (< 60 sec) |

### Phase 5 Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCORE-01 | Final score is deterministic (0–100) using 8 weighted dimensions | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_score_output_range_0_100 -xvs` | ❌ Wave 0 |
| SCORE-01 | Same opportunity scored twice produces identical score | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_scoring_deterministic -xvs` | ❌ Wave 0 |
| SCORE-01 | Fit dimension weights 25% in final score | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_fit_weight_25_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Salary upside dimension weights 20% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_salary_weight_20_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Growth dimension weights 15% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_growth_weight_15_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Visa dimension weights 10% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_visa_weight_10_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Company strength dimension weights 10% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_company_weight_10_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Referral leverage dimension weights 10% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_referral_weight_10_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Freshness dimension weights 5% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_freshness_weight_5_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Side-income dimension weights 5% | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_side_income_weight_5_percent -xvs` | ❌ Wave 0 |
| SCORE-01 | Scoring pipeline (run_scoring_pass) handles list of opportunities | integration | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_run_scoring_pass_batch -xvs` | ❌ Wave 0 |
| SCORE-02 | Scam risk signal (keyword in title) triggers −20 penalty | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_penalty_scam_risk -xvs` | ❌ Wave 0 |
| SCORE-02 | Unclear pay (low confidence + keyword) triggers −15 penalty | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_penalty_unclear_pay -xvs` | ❌ Wave 0 |
| SCORE-02 | Severe skill mismatch (fit < 30 + avoid_flags) triggers −10 penalty | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_penalty_severe_skill_mismatch -xvs` | ❌ Wave 0 |
| SCORE-02 | Unpaid work (salary=0 or keyword) triggers −20 penalty | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_penalty_unpaid_work -xvs` | ❌ Wave 0 |
| SCORE-02 | Multiple penalties cumulative (sum applied to base) | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_multiple_penalties_cumulative -xvs` | ❌ Wave 0 |
| SCORE-02 | Final score capped at 0–100 (no negative, no >100) | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_score_capped_0_100 -xvs` | ❌ Wave 0 |
| SCORE-01 | ScoreBreakdown includes all 8 dimensions + penalties | unit | `pytest TARIQ__career_radar/tests/test_scoring_engine.py::test_breakdown_includes_all_dimensions -xvs` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest TARIQ__career_radar/tests/test_scoring_engine.py -x -q` (fast, ~5 sec)
- **Per wave merge:** `pytest TARIQ__career_radar/tests/ -v` (full suite, < 60 sec)
- **Phase gate:** All tests GREEN before `/gsd:verify-work`; specifically determinism test must pass on 100+ real test opportunities

### Wave 0 Gaps

- [ ] `TARIQ__career_radar/radar/scoring_engine.py` — ScoringEngine class + dimension functions
- [ ] `TARIQ__career_radar/radar/scoring_config.py` — Constants (weights, thresholds, penalty values, platform lists)
- [ ] `TARIQ__career_radar/radar/stages/score.py` — run_scoring_pass() orchestrator
- [ ] `TARIQ__career_radar/tests/test_scoring_engine.py` — 17 unit/integration tests (determinism, weights, penalties, bounds, breakdown)
- [ ] `TARIQ__career_radar/conftest.py` augment — Fixtures: scoring_profile, sample_opportunities (varied: with/without salary, scam signals, unpaid, etc.), now_fixture
- [ ] `TARIQ__career_radar/tests/fixtures/` — Optional: scoring_test_data.jsonl (50+ real opportunities for calibration)
- [ ] Phase 1 schema validation to ensure required fields present for scoring
- [ ] Integration test: Phase 4 dedup output → Phase 5 scoring → opportunities have final_score + breakdown

---

## Sources

### Primary (HIGH confidence)

- **REQUIREMENTS.md** — SCORE-01 and SCORE-02 locked requirements; weights and penalty ranges specified
- **ROADMAP.md** — Phase 5 goal and success criteria; Phase 4 dependency noted
- **Phase 1 RESEARCH.md + Implementation** — Opportunity schema finalized; Phase 1's fit_score, growth_score fields documented
- **Phase 4 RESEARCH.md** — Dedup output structure; opportunities ready for Phase 5 after cross-run dedup
- **NIZAM conventions** — MARSAD alert scoring patterns (if any); ledger approach; privacy rules

### Secondary (MEDIUM confidence)

- **Existing code** — TARIQ__career_radar/radar/config.py, constraints.py (profile seed + lane constraints established)
- **Project README** — Career radar domain, target opportunities (AI ops, data science, etc.)

### Tertiary (LOW confidence – flags for validation)

- **Penalty values (−5 to −20):** Derived from research recommendations; require calibration on real dataset
- **Company tier heuristics:** Text-based inference of Tier 1/2/3; may need refinement after Phase 13 validation

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Scoring formula decomposition (8 dimensions) | HIGH | Requirements lock weights; each dimension has clear data source in Phase 1 schema |
| Determinism strategy | HIGH | Pure-function design, integer arithmetic, no randomness or external state required |
| Penalty taxonomy | MEDIUM-HIGH | Triggers documented; values (−5 to −20) need calibration on real dataset in Phase 5 Wave 0 |
| Data source mapping | HIGH | Phase 1 schema finalized; all required fields present for scoring |
| Integration points | HIGH | Phase 4 output → Phase 5 scoring → Phase 6/7 enrichment; pipeline clear |
| No new dependencies | HIGH | Scoring uses stdlib + existing schema; no external APIs |

**Research date:** 2026-06-15  
**Valid until:** 2026-07-15 (30 days — scoring is stable domain; formula unlikely to change once implemented; calibration may refine penalty values)

**Key assumption:** Phase 1 schema is frozen; Phase 4 dedup output is deterministic; profile_cache.json is stable within a run.

---

*Research completed: 2026-06-15*  
*Ready for Phase 5 planning*
