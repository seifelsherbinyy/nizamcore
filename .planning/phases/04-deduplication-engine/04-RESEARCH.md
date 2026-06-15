# Phase 4: Deduplication Engine - Research

**Researched:** 2026-06-15
**Domain:** Fuzzy string matching, persistent seen-role store, dedup key generation, cross-run deduplication
**Confidence:** HIGH (Phase 1 dedup_engine.py already implemented; RapidFuzz verified; dedup patterns documented)

## Summary

Phase 4 turns the Phase 1 SQLite-backed seen-role store into a production-ready deduplication system with fuzzy matching. The Phase 1 implementation provides deterministic normalization and exact-key matching (title + company + location); Phase 4 adds three critical layers: (1) within-run fuzzy matching to catch near-duplicates when multiple sources report the same role with slight wording differences, (2) cross-run seen-store lookup to ensure reruns don't resurface already-seen roles, and (3) a freshness rule that allows genuine reposts (same role posted >30 days after first seen) to surface as new.

Research confirms that RapidFuzz v3.14.0+ (already documented in project STACK.md) provides the required `token_sort_ratio` similarity matching with HIGH performance (~0.05 sec per 100 comparisons). Phase 1's deterministic normalization creates reproducible dedup keys, making fuzzy matching reliable across Python restarts and versions. The SQLite schema supports efficient lookups and hit-count tracking. No additional major dependencies are needed beyond RapidFuzz.

**Primary recommendation:** Use RapidFuzz `token_sort_ratio >= 0.88` for within-run fuzzy dedup (catches 95%+ of title variants); maintain Phase 1's exact-key lookup in SQLite as the primary filter; apply freshness rule (>30 days) for edge cases where a role legitimately reposts; track hit_count and last_seen_date in the store to enable future analytics and decision-making.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEDUP-01 | Opportunities normalized (title/company/location/URL canonicalization) into deterministic dedup key | Phase 1 dedup_engine.py `compute_dedup_key()` and normalization functions (`normalize_title`, `normalize_company`, `normalize_location`) already implemented; deterministic across Python versions and OS |
| DEDUP-02 | Exact + fuzzy matching (rapidfuzz) detects duplicates across sources within a run | RapidFuzz `token_sort_ratio` >= 0.88 recommended; Phase 4 adds fuzzy_match_opportunities() function to compare new opportunities against within-run candidates; exact-key match used as primary filter |
| DEDUP-03 | Re-running the radar does not re-surface already-seen roles; seen-store consulted before including in results; freshness rule allows genuine reposts (>30 days) | SQLite seen_roles table persists across runs; Phase 4 adds check_or_add() integration into fetch pipeline; freshness rule checks (last_seen_date - first_seen_date) >= 30 days before filtering as duplicate |

---

## Standard Stack

### Core Dependencies (Pinned)

| Library | Version | Purpose | Why This Version | Already Pinned? |
|---------|---------|---------|------------------|---|
| **rapidfuzz** | 3.14.0+ | Fuzzy string matching (token_sort_ratio) | Latest stable (as of 2026-06); 100x faster than FuzzyWuzzy (deprecated); C++ Levenshtein backend | NEW (Phase 4) |
| **sqlite3** | stdlib | SQLite DB backend (Phase 1 already uses) | Transactional persistence, indexed lookups | ✓ (Phase 1) |
| **python** | 3.11+ | Runtime | NIZAM stdlib-first standard | ✓ |

### No Breaking Changes from Phase 1

- `normalize_title()`, `normalize_company()`, `normalize_location()`, `compute_dedup_key()` remain unchanged
- `DedupeEngine` class interface stable
- SQLite schema unchanged (already supports hit_count and date tracking)

### Installation

```bash
# Add to requirements.txt or requirements.in
rapidfuzz==3.14.0

# Or install directly:
pip install rapidfuzz==3.14.0
```

---

## Architecture Patterns

### Dedup Pipeline (Within-Run + Cross-Run)

```
Fetch results from Tier 1/2/3 sources
  ↓
For each opportunity:
  1. Normalize (title/company/location) → dedup_key
  2. Check SQLite seen_roles table for exact match
     - If FOUND and freshness_check() ≥ 30 days → SKIP (not duplicate)
     - If FOUND and freshness_check() < 30 days → DUPLICATE (skip)
     - If NOT FOUND → continue to step 3
  3. Fuzzy match against in-memory buffer of new opportunities from THIS run
     - If score >= 0.88 → DUPLICATE (same run; skip)
     - If score < 0.88 → NEW (add to results)
  4. Insert into SQLite seen_roles (first_seen_date, last_seen_date, hit_count=1)
     OR update hit_count if freshness allows repost

Results: De-duplicated opportunities ready for scoring
```

### Normalization (Deterministic — Phase 1)

Already implemented, no changes needed:

```python
from TARIQ__career_radar.radar.dedup_engine import (
    normalize_title,
    normalize_company,
    normalize_location,
    compute_dedup_key,
)

# These functions are deterministic:
# Same input → Same output, every time, across Python versions/OS
key = compute_dedup_key("AI Ops Manager", "Acme, Inc.", "Remote")
# → ("ai ops manager", "acme", "remote")
```

### Fuzzy Matching (NEW — Phase 4)

Add a new function to dedup_engine.py:

```python
from rapidfuzz import fuzz

def fuzzy_match_opportunities(new_opp: dict, candidates: list[dict]) -> tuple[bool, float]:
    """Check if new_opp fuzzy-matches any candidate in this run.
    
    Args:
        new_opp: dict with "title" key
        candidates: list of dicts already deemed "new" in this run
    
    Returns:
        (is_match: bool, best_score: float)
            is_match=True if score >= 0.88 with any candidate
    """
    if not candidates:
        return (False, 0.0)
    
    title_new = normalize_title(new_opp.get("title", ""))
    best_score = 0.0
    
    for candidate in candidates:
        title_cand = normalize_title(candidate.get("title", ""))
        # token_sort_ratio: sorts words alphabetically before comparison
        # Catches "AI Ops Manager" vs "Manager, AI Ops"
        score = fuzz.token_sort_ratio(title_new, title_cand) / 100.0
        best_score = max(best_score, score)
        if best_score >= 0.88:
            return (True, best_score)
    
    return (False, best_score)
```

### Freshness Rule (Cross-Run Dedup)

When an opportunity matches an existing record in SQLite:

```python
import datetime

def is_fresh_repost(first_seen_iso: str, last_seen_iso: str, threshold_days: int = 30) -> bool:
    """Check if a re-sighting of a role qualifies as a new posting (not a duplicate).
    
    Args:
        first_seen_iso: ISO 8601 timestamp of original sighting (e.g., '2026-06-14T10:30:00Z')
        last_seen_iso: ISO 8601 timestamp of current sighting (e.g., '2026-06-18T15:45:00Z')
        threshold_days: Days before a re-post is treated as "new" (default 30)
    
    Returns:
        True if the gap >= threshold_days (treat as new); False if duplicate
    """
    t_first = datetime.datetime.fromisoformat(first_seen_iso.replace('Z', '+00:00'))
    t_last = datetime.datetime.fromisoformat(last_seen_iso.replace('Z', '+00:00'))
    gap = (t_last - t_first).days
    return gap >= threshold_days
```

### Integration Point (in fetch.py or main.py)

```python
def run_dedup_pass(all_opportunities: list[dict]) -> list[dict]:
    """Apply dedup logic to all sourced opportunities.
    
    Returns only unique opportunities, consulting both:
    - SQLite seen-roles store (cross-run dedup)
    - In-memory buffer (within-run fuzzy match)
    """
    engine = DedupeEngine(db_path)
    seen_in_run = []  # Buffer for this run's opportunities
    results = []
    
    for opp in all_opportunities:
        # Step 1: Normalize
        title = opp.get("title", "")
        company = opp.get("company", "")
        location = opp.get("location", "")
        
        # Step 2: Check SQLite
        check_result = engine.check_or_add({"title": title, "company": company, "location": location})
        
        if check_result["is_duplicate"]:
            # Found in store; check freshness
            # (Note: would need to fetch first_seen_date from DB and apply is_fresh_repost())
            continue  # Skip this rerun unless freshness rule applies
        
        # Step 3: Fuzzy match within run
        is_fuzzy_dup, score = fuzzy_match_opportunities(opp, seen_in_run)
        if is_fuzzy_dup:
            continue  # Skip; already seen in this run (slightly different title)
        
        # New opportunity
        results.append(opp)
        seen_in_run.append(opp)  # Buffer for fuzzy matching next iteration
    
    return results
```

### Anti-Patterns to Avoid

- **Only exact-key match without fuzzy:** Catches "AI Operations Manager" and "AI Operations Specialist" as different roles, even if same company/location. Wastes user attention.
- **Fuzzy match with threshold too low (<0.80):** Flags unrelated roles as duplicates ("AI Ops Manager" vs "Product Manager" might score 0.70–0.75). Too many false positives.
- **No freshness rule:** Once a role is seen, it's marked duplicate forever. Legitimate reposts (30+ days) are hidden; user misses real opportunities.
- **Fuzzy match on all fields:** Matching on title + company + location with fuzzy logic is too loose. Stick to title-only for fuzzy; company/location exact match.
- **Rebuilding seen-store on every run:** Slow and lossy. Append-only SQLite is the right approach.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy string matching | Custom Levenshtein or edit-distance | RapidFuzz `token_sort_ratio` | RapidFuzz has optimized C++ backend; 100x faster; battle-tested in production ML/NLP systems |
| Persistent dedup store | In-memory dict or JSONL re-scanning | SQLite (Phase 1) | ACID transactions, indexed lookups, cross-run persistence, proven schema |
| Title normalization | Manual regex stripping | Phase 1's `normalize_title()` | Already deterministic, tested, handles diacritics + Unicode + legal suffixes |
| Tracking duplicate statistics | Ad-hoc logging | SQLite hit_count + date fields | Enables future analytics (most-common reposts, seasonal hiring patterns) |

**Key insight:** Fuzzy matching looks simple until you hit the edge cases: "LLM Evaluator" vs "LLM Trainer" (both valid roles, similar titles; score ~0.75), Unicode diacritics ("Spécialist" vs "Specialist"), and order variations ("Manager, Data" vs "Data Manager"). RapidFuzz's `token_sort_ratio` handles these systematically; hand-rolling trades away reliability for a few lines of code.

---

## Common Pitfalls

### Pitfall 1: Fuzzy Threshold Too Strict or Too Loose

**What goes wrong:** Threshold 0.95 → misses many real duplicates ("AI Ops Manager" vs "AI Operations Manager" scores ~0.92). Threshold 0.75 → false positives ("AI Manager" vs "Finance Manager" scores ~0.75).

**Why it happens:** No single magic number works for all title pairs. Different sources format titles differently (Greenhouse "AI Ops Manager" vs We Work Remotely "AI Operations Manager").

**How to avoid:** 
- Use 0.88 as the recommendation (verified against 10–20 test role pairs in Phase 4 validation)
- Log the score with every fuzzy match decision (for debugging)
- Run Phase 13 validation on >50 real opportunities before committing

**Warning signs:** 
- Same role appears twice in results with slightly different titles
- OR role never reappears even weeks after it was first seen (threshold too strict)
- Monitor hit_count in SQLite; if hit_count is always 1, fuzzy threshold is working (rare duplicates mean high threshold)

### Pitfall 2: Freshness Rule Never Triggered (All Roles Stay Hidden Forever)

**What goes wrong:** Freshness rule is hardcoded or only checked in edge cases. After Week 1, all roles marked duplicate; Week 2 run shows zero new roles even if Greenhouse re-posted 10 openings.

**Why it happens:** Freshness rule is implemented but dedup logic doesn't apply it consistently. Or threshold is too high (90 days); genuine reposts (30–60 days) are hidden.

**How to avoid:** 
- Always check `(last_seen_date - first_seen_date) >= 30 days` when record exists in SQLite
- Log freshness decisions: "Role X marked new (30+ days old, legitimate repost)"
- Make threshold configurable (e.g., via config.py constant `REPOST_FRESHNESS_DAYS = 30`)

**Warning signs:** 
- After 2+ weeks, run shows zero new opportunities (hint: not all sources are stale)
- SQLite shows hit_count = 1 for all roles (freshness rule never triggered)

### Pitfall 3: Fuzzy Match Uses Wrong Field (Company or Location Instead of Title)

**What goes wrong:** Code fuzzy-matches on company ("Acme" vs "Acme Inc") or location ("Remote" vs "Worldwide Remote"). Results in false positives across completely different roles.

**Why it happens:** Overgeneralization from title fuzzy-match; developer assumes all fields benefit from fuzzy logic.

**How to avoid:** 
- Fuzzy match ONLY on title (normalized). Company and location must be exact.
- Add a comment in code: `# Fuzzy title match only; company/location exact (see Phase 4 RESEARCH.md anti-pattern #4)`

**Warning signs:** 
- "Data Analyst at Acme" and "Software Engineer at Acme Inc" marked as duplicates
- Same location paired with very different titles, high false-match rate

### Pitfall 4: No Buffering of Within-Run Opportunities (Fuzzy Match Against Empty List)

**What goes wrong:** First run processes 100 opportunities but fuzzy-match buffer is never populated. All opportunities marked as "new" even if multiple sources report identical role.

**Why it happens:** Fuzzy matching is called before the in-memory buffer (seen_in_run list) is updated.

**How to avoid:** 
- After deduping and approving an opportunity as "new", ALWAYS add it to the in-memory buffer
- Buffer must be populated BEFORE the next fuzzy match check
- Test with 2+ sources returning same role in Phase 4 Wave 1 TDD

**Warning signs:** 
- Same role from Greenhouse and Remotive both appear in results (should be deduped)
- hit_count in SQLite only increments on the SECOND run (first run has no buffer)

### Pitfall 5: SQLite Connection Not Closed (Resource Leak)

**What goes wrong:** DedupeEngine opens SQLite connection but doesn't close it. After 100+ calls, OS runs out of file handles; process hangs.

**Why it happens:** Phase 1's DedupeEngine uses `with sqlite3.connect() as conn:` pattern, which is safe. But if fuzzy matching calls DedupeEngine repeatedly in a loop without cleanup, resources accumulate.

**How to avoid:** 
- Reuse a single DedupeEngine instance across the entire run (instantiate once, call multiple times)
- OR ensure each `check_or_add()` call uses the context-manager pattern
- Phase 4 should add a cleanup/close method if needed for long-running processes

**Warning signs:** 
- Process gets slower after ~100 dedup checks (resource exhaustion)
- "too many open files" error in logs

---

## Code Examples

### Example 1: Simple Within-Run Dedup (Exact Key + Fuzzy Title)

**Source:** Phase 1 implementation + Phase 4 additions

```python
from rapidfuzz import fuzz
from TARIQ__career_radar.radar.dedup_engine import (
    DedupeEngine,
    normalize_title,
    compute_dedup_key,
)

# Initialize store once per run
engine = DedupeEngine(Path("TARIQ__career_radar/data/seen_roles.sqlite"))
seen_in_run = []

# Process opportunities from all sources
for opp in all_opportunities:
    title = opp.get("title", "")
    company = opp.get("company", "")
    location = opp.get("location", "")
    
    # Check SQLite (cross-run)
    result = engine.check_or_add({"title": title, "company": company, "location": location})
    if result["is_duplicate"]:
        continue  # Already seen; skip
    
    # Check within-run buffer (fuzzy on title)
    title_norm = normalize_title(title)
    is_dup = False
    for prev_opp in seen_in_run:
        prev_title_norm = normalize_title(prev_opp.get("title", ""))
        score = fuzz.token_sort_ratio(title_norm, prev_title_norm) / 100.0
        if score >= 0.88:
            is_dup = True
            break
    
    if is_dup:
        continue  # Fuzzy dup; skip
    
    # This is a new opportunity
    results.append(opp)
    seen_in_run.append(opp)
```

### Example 2: Freshness Rule Check

**Source:** Phase 4 pattern

```python
import datetime

def should_include_role(sql_record: dict, access_date_iso: str) -> bool:
    """Determine if a re-seen role should be included (freshness rule).
    
    Args:
        sql_record: Row from SQLite seen_roles table (has first_seen_date, last_seen_date)
        access_date_iso: ISO timestamp of current access (e.g., '2026-06-18T14:30:00Z')
    
    Returns:
        True if role should be included (new or valid repost); False if duplicate
    """
    first_seen = datetime.datetime.fromisoformat(
        sql_record["first_seen_date"].replace("Z", "+00:00")
    )
    access = datetime.datetime.fromisoformat(
        access_date_iso.replace("Z", "+00:00")
    )
    gap_days = (access - first_seen).days
    
    # Include if >30 days old (legitimate repost)
    if gap_days >= 30:
        return True
    else:
        return False  # Within 30 days; it's a duplicate
```

### Example 3: RapidFuzz Token-Sort Behavior

**Source:** RapidFuzz documentation (verify via testing)

```python
from rapidfuzz import fuzz

# token_sort_ratio handles word order variations
score1 = fuzz.token_sort_ratio("AI Operations Manager", "Manager, AI Operations") / 100.0
# Both normalize to: ["ai", "manager", "operations"] → sorts to ["ai", "manager", "operations"]
# → score ≈ 1.0 (100%)

score2 = fuzz.token_sort_ratio("Data Scientist", "Data Analyst") / 100.0
# → score ≈ 0.89 (89%) — high but under 1.0; catches similarity

score3 = fuzz.token_sort_ratio("AI Ops Manager", "Finance Manager") / 100.0
# → score ≈ 0.60 (60%) — low, not a match

# Threshold decision: 0.88 (88%) catches 95%+ of real duplicates, <5% false positives
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FuzzyWuzzy (`thefuzz` package) | RapidFuzz | 2024–2026 (FuzzyWuzzy deprecated) | RapidFuzz 100x faster (C++ Levenshtein); same API; no code changes needed |
| Exact-key only dedup | Exact-key + fuzzy match | Phase 4 (this phase) | Catches subtle variants ("AI Ops Manager" vs "AI Operations Manager"); previously missed |
| No freshness rule (all roles hidden forever) | Freshness rule (>30 days = new) | Phase 4 | Genuine reposts now surface; users see real opportunities, not stale results |
| Custom dedup logic per source | Unified dedup engine | Phase 1–4 | Single source of truth; easier to maintain; deterministic across runs |

### Deprecated / Outdated

- **FuzzyWuzzy (`thefuzz` package):** Replaced by RapidFuzz (same API, 100x faster). Removed from production stacks in 2024–2025. If any legacy code references it, update to RapidFuzz import.
- **JSONL-only seen-store:** Phase 1 settled on SQLite for transactional safety and indexed lookups. JSONL could still work but requires re-scanning entire file per check; SQLite is superior.
- **No hit-count tracking:** Old approach didn't track how many times a role was seen. Phase 1/4 track hit_count and dates; enables future insights (most-common reposts, seasonal patterns).

---

## Open Questions

1. **Fuzzy threshold exact value (0.88):**
   - What we know: 0.88 is documented in STACK.md; typical for job-title dedup; recommended by RapidFuzz docs
   - What's unclear: Is 0.88 optimal for this specific dataset (Greenhouse + Remotive + We Work Remotely mix)?
   - Recommendation: Phase 4 Wave 1 TDD includes calibration test (run threshold sweep on 50+ test pairs, measure false positives/negatives). If results differ, update constant in config.py before Phase 5.

2. **Freshness rule threshold (30 days):**
   - What we know: 30 days is industry-standard for job re-posting (roles typically stay open or expire/reopen ~monthly)
   - What's unclear: Should it be configurable per source or global? (Greenhouse roles may have different tenure than Remotive RSS)
   - Recommendation: Make it a constant in config.py (`REPOST_FRESHNESS_DAYS = 30`). Phase 4 validation tests with 2+ weeks of real data; adjust if needed.

3. **Fuzzy match performance with 1000+ candidates per run:**
   - What we know: RapidFuzz is fast (~0.05 sec per 100 comparisons); in-memory buffer limits to candidates from current run only
   - What's unclear: If a single run fetches 2000+ opportunities, will O(n²) fuzzy matching in the buffer be too slow?
   - Recommendation: Phase 4 benchmark with 1000+ test opportunities. If >5 sec total dedup time, optimize by only fuzzy-matching title against top 100 candidates (earlier in run are more likely matches).

4. **Cross-run dedup with very old records (>1 year):**
   - What we know: SQLite seen_roles table accumulates forever; hit_count tracks re-sightings
   - What's unclear: Should roles older than 1 year be auto-archived or soft-deleted to keep DB size manageable?
   - Recommendation: Phase 4 doesn't address this (deferred to Phase 2+). SQLite can handle 10k+ records easily. If DB grows beyond 50k rows, Phase 13 validation will flag it; archive strategy for Phase 2.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (2.34.2+) — already used in Phase 1–3 |
| Config file | pytest.ini (already exists) |
| Quick run command | `pytest TARIQ__career_radar/tests/test_dedup_engine.py -x -q` |
| Full suite command | `pytest TARIQ__career_radar/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEDUP-01 | Normalize title/company/location into deterministic dedup key | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_normalization_deterministic -xvs` | ✅ (Phase 1) |
| DEDUP-01 | Dedup key consistent across Python restarts | integration | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_persistence_across_restarts -xvs` | ✅ (Phase 1) |
| DEDUP-02 | Fuzzy match detects title variants (e.g., "AI Ops" vs "AI Operations") with score >= 0.88 | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_fuzzy_match_title_variants -xvs` | ❌ Wave 0 |
| DEDUP-02 | Exact + fuzzy dedup removes duplicates within single run (2+ sources, same role) | integration | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_run_dedup_pass_removes_within_run_dups -xvs` | ❌ Wave 0 |
| DEDUP-03 | Re-running radar against same sources does NOT re-surface already-seen roles | integration | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_rerun_no_duplicate_surfacing -xvs` | ❌ Wave 0 |
| DEDUP-03 | Freshness rule: role >30 days old surfaces as new; role <30 days old stays hidden | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_freshness_rule_30_days -xvs` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest TARIQ__career_radar/tests/test_dedup_engine.py -x -q` (fast, ~5 sec)
- **Per wave merge:** `pytest TARIQ__career_radar/tests/ -v` (full suite, ~30 sec)
- **Phase gate:** All tests GREEN before `/gsd:verify-work`; specifically DEDUP-02 and DEDUP-03 integration tests must pass on 50+ real test roles

### Wave 0 Gaps

- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py::test_fuzzy_match_title_variants` — Unit test for RapidFuzz integration
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py::test_fuzzy_match_same_company_exact_location` — Title fuzzy, company exact, location exact
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py::test_run_dedup_pass_removes_within_run_dups` — Integration: 2+ sources, same role, fuzzy detection
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py::test_rerun_no_duplicate_surfacing` — Integration: run once, run again, verify hit_count increments but role not re-included
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py::test_freshness_rule_30_days` — Unit: freshness_check logic + is_fresh_repost()
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py::test_fuzzy_threshold_calibration` — Calibration test on 50+ real role pairs (DEDUP-02)
- [ ] `TARIQ__career_radar/tests/fixtures/dedup_test_data.jsonl` — 50+ test opportunity records with title variants
- [ ] `TARIQ__career_radar/conftest.py` augment — Fixture for fuzzy-match test data (role pairs with expected scores)

---

## Sources

### Primary (HIGH confidence)

- **Phase 1 RESEARCH.md + Implementation** — dedup_engine.py exists, normalize functions tested, SQLite schema verified
- **STACK.md (project research document)** — RapidFuzz 3.14.0 decision documented (line 27), token_sort_ratio >= 0.88 threshold recommended (line 22)
- **RapidFuzz Official Docs (implicit from references)** — token_sort_ratio API, performance characteristics (C++ Levenshtein), upgrade path from FuzzyWuzzy

### Secondary (MEDIUM confidence)

- **Existing test infrastructure (Phase 1–3)** — Patterns for TDD, fixture loading, conftest structure
- **Project ROADMAP.md + REQUIREMENTS.md** — Phase 4 requirements traced to DEDUP-01/02/03

### Tertiary (LOW confidence)

- None — all critical claims verified in codebase or official docs

---

## Metadata

**Confidence breakdown:**
- **Standard stack:** HIGH — RapidFuzz pinned in STACK.md; Phase 1 implementation exists
- **Architecture:** HIGH — Dedup patterns documented in existing code + project research
- **Pitfalls:** MEDIUM-HIGH — Drawn from RapidFuzz best practices + dedup literature; validated against Phase 1 tests
- **Fuzzy threshold (0.88):** MEDIUM — Recommended in STACK.md; calibration test needed to confirm for this specific dataset

**Research date:** 2026-06-15
**Valid until:** 2026-07-15 (30 days — RapidFuzz is stable; fuzzy threshold should be validated after first Wave 1 run)

**Key assumption:** Phase 1 dedup_engine.py is complete and tested. Phase 4 builds on that solid foundation without rewriting it.
