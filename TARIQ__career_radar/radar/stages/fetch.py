"""fetch.py — Stage 1: fetch all ATS sources, normalize to DATA-01 schema, return manifest.

Implements run_fetch() orchestrator + normalize_opportunity() + infer_remote_status().

Accepts an inline platform config dict (keys: greenhouse, lever, ashby, workable) as the
first argument — each value is a single-board config with at least {enabled: bool}.
When a platform key is absent, that platform is skipped.

Falls back to loading config_sources.yaml when no inline config keys are present (CLI use).

Error contract (SRC-05):
  - Each source fetch is wrapped in try/except; errors are appended to blocked_sources.
  - When ALL sources fail or return zero, run_fetch returns normally — never raises.
  - Disabled sources are silently skipped (not added to blocked_sources).

No new dependencies.  Imports: stdlib only + existing radar.* modules.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml  # PyYAML — already pinned in requirements.txt

from radar.sources.greenhouse_source import GreenhouseSource
from radar.sources.lever_source import LeverSource
from radar.sources.ashby_source import AshbySource
from radar.sources.workable_source import WorkableSource
from radar.sources.rss_source import RemotiveSource, WeWorkRemotelySource, RemoteOKSource
from radar.sources.manual_import_source import ManualImportSource
from radar.sources.base import OpportunityRaw
from radar.stages.filter import run_filter
from radar.stages.dedup import run_dedup_pass
from radar.stages.score import run_scoring_pass
from radar.dedup_engine import normalize_title, normalize_company, normalize_location, _DEFAULT_DB_PATH

logger = logging.getLogger(__name__)

# stages/ → radar/ → TARIQ__career_radar/
MODULE_ROOT = Path(__file__).resolve().parent.parent.parent

# Known ATS platform keys (used to detect inline config vs. search constraints)
_ATS_PLATFORM_KEYS = {"greenhouse", "lever", "ashby", "workable"}


# ---------------------------------------------------------------------------
# Remote-status inference
# ---------------------------------------------------------------------------

def infer_remote_status(location: str, remote_policy: str = None) -> str:
    """Infer remote_status from location string and optional explicit remote_policy.

    Args:
        location:      Raw location string from the ATS response.
        remote_policy: Explicit policy string from the ATS (e.g. Ashby remotePolicy).

    Returns:
        One of: "fully_remote", "hybrid_remote_preferred",
                "hybrid_onsite_required", "onsite_only".
    """
    _VALID_POLICIES = {
        "fully_remote",
        "hybrid_remote_preferred",
        "hybrid_onsite_required",
        "onsite_only",
    }
    if remote_policy and remote_policy in _VALID_POLICIES:
        return remote_policy

    location_lower = (location or "").lower()
    if "remote" in location_lower:
        return "fully_remote"
    elif "hybrid" in location_lower:
        return "hybrid_remote_preferred"
    return "onsite_only"


# ---------------------------------------------------------------------------
# Salary helpers
# ---------------------------------------------------------------------------

def _infer_salary_confidence(source: str, has_salary: bool) -> str:
    """Return salary_confidence based on ATS source and whether salary fields are present.

    Greenhouse and Ashby expose employer-posted salary → HIGH confidence.
    Lever and Workable do not include salary in API responses → LOW confidence.

    Args:
        source:     Source name (e.g. "greenhouse", "lever").
        has_salary: True when salary_usd_low is not None / non-zero.

    Returns:
        "HIGH" or "LOW".
    """
    if source in ("greenhouse", "ashby") and has_salary:
        return "HIGH"
    return "LOW"


def _infer_salary_evidence_type(source: str, has_salary: bool) -> str:
    """Return salary_evidence_type based on source and salary presence.

    Args:
        source:     Source name.
        has_salary: True when salary_usd_low is not None / non-zero.

    Returns:
        "employer_posted" when source is Greenhouse/Ashby with salary; else "not_disclosed".
    """
    if has_salary and source in ("greenhouse", "ashby"):
        return "employer_posted"
    return "not_disclosed"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_opportunity(raw: OpportunityRaw, run_id: str) -> dict:
    """Normalize a raw ATS opportunity to the DATA-01 career_opportunity_record schema.

    Args:
        raw:    OpportunityRaw from a source connector.
        run_id: Identifies the radar run that produced this record.

    Returns:
        Dict conforming to career_opportunity_record.schema.json (all required fields
        present).  opportunity_id is a fresh UUIDv4 per record.
    """
    now_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    has_salary = bool(raw.salary_usd_low)

    # Extract remotePolicy from raw_payload (Ashby provides this field)
    remote_policy = None
    if raw.raw_payload and isinstance(raw.raw_payload, dict):
        remote_policy = raw.raw_payload.get("remotePolicy")

    return {
        "opportunity_id": str(uuid.uuid4()),
        "title": normalize_title(raw.title),
        "company": normalize_company(raw.company),
        "location": normalize_location(raw.location),
        "remote_status": infer_remote_status(raw.location, remote_policy),
        "source": raw.source,
        "source_type": raw.source_type,
        "source_url": raw.source_url,
        "access_date": now_iso,
        "fit_score": 0,
        "growth_score": 0,
        "confidence": "LOW",
        "tags": [],
        "salary_usd_low": raw.salary_usd_low,
        "salary_usd_high": raw.salary_usd_high,
        "salary_evidence_type": _infer_salary_evidence_type(raw.source, has_salary),
        "salary_confidence": _infer_salary_confidence(raw.source, has_salary),
        "observed_at": now_iso,
        "lane": "Remote USD",
        "data_quality": "confirmed",
        "run_id": run_id,
    }


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_ats_config() -> dict:
    """Load tier_1_ats config from config_sources.yaml.

    Returns a minimal disabled config if the file is not found, so the caller
    always gets a consistent structure.

    Returns:
        Dict with key "tier_1_ats" containing per-platform sub-configs.
    """
    config_path = MODULE_ROOT / "radar" / "config_sources.yaml"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except Exception as exc:
            logger.warning("Failed to load config_sources.yaml: %s — using empty config", exc)

    # Minimal fallback: all platforms disabled, no boards
    return {
        "tier_1_ats": {
            "greenhouse": {"enabled": False, "boards": []},
            "lever": {"enabled": False, "boards": []},
            "ashby": {"enabled": False, "boards": []},
            "workable": {"enabled": False, "boards": []},
        }
    }


def _load_tier2_config() -> dict:
    """Load tier_2_rss and manual_import config from config_sources.yaml.

    Returns dict with tier_2_rss, manual_import, role_filter keys.
    Falls back to all-disabled if file not found.
    """
    config_path = MODULE_ROOT / "radar" / "config_sources.yaml"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as fh:
                full = yaml.safe_load(fh) or {}
                return {
                    "tier_2_rss": full.get("tier_2_rss", {"enabled": False}),
                    "manual_import": full.get("manual_import", {"enabled": False}),
                    "role_filter": full.get("role_filter", {"enabled": False}),
                }
        except Exception as exc:
            logger.warning("Failed to load tier2 config: %s — tier 2 disabled", exc)
    return {
        "tier_2_rss": {"enabled": False},
        "manual_import": {"enabled": False},
        "role_filter": {"enabled": False},
    }


# ---------------------------------------------------------------------------
# Source instance builder — supports both inline and YAML-based configs
# ---------------------------------------------------------------------------

def _build_sources_from_inline(constraints: dict) -> list:
    """Build source instances from an inline per-platform config dict.

    Inline format (used by tests):
        {
          "greenhouse": {"board_token": "acme", "enabled": True},
          "lever":      {"site": "acme", "company_name": "Acme Corp", "enabled": True},
          "ashby":      {"board_name": "acme", "enabled": False},
          "workable":   {"account_subdomain": "acme", "enabled": False},
        }

    Each value is a single-board config.  Missing platforms are skipped.
    Disabled platforms (enabled=False) are silently skipped.

    Returns:
        List of (source_instance, board_identifier) tuples for enabled boards.
    """
    sources = []
    gh_cfg = constraints.get("greenhouse")
    if gh_cfg and gh_cfg.get("enabled", False):
        src = GreenhouseSource(gh_cfg)
        board_id = gh_cfg.get("board_token", "")
        sources.append((src, board_id))

    lv_cfg = constraints.get("lever")
    if lv_cfg and lv_cfg.get("enabled", False):
        src = LeverSource(lv_cfg)
        board_id = lv_cfg.get("site", "")
        sources.append((src, board_id))

    ashby_cfg = constraints.get("ashby")
    if ashby_cfg and ashby_cfg.get("enabled", False):
        src = AshbySource(ashby_cfg)
        board_id = ashby_cfg.get("board_name", "")
        sources.append((src, board_id))

    wk_cfg = constraints.get("workable")
    if wk_cfg and wk_cfg.get("enabled", False):
        src = WorkableSource(wk_cfg)
        board_id = wk_cfg.get("account_subdomain", "")
        sources.append((src, board_id))

    return sources


def _build_tier2_sources(tier2_cfg: dict) -> list:
    """Build Tier 2 source instances from tier2 config section.

    Returns list of (source_instance, board_identifier) tuples for enabled sources.
    Mirrors the _build_sources_from_yaml() pattern.
    """
    sources = []
    rss_cfg = tier2_cfg.get("tier_2_rss", {})

    if rss_cfg.get("enabled", False):
        rem_cfg = rss_cfg.get("remotive", {})
        if rem_cfg.get("enabled", False):
            sources.append((RemotiveSource(rem_cfg), rem_cfg.get("feed_url", "")))

        wwr_cfg = rss_cfg.get("weworkremotely", {})
        if wwr_cfg.get("enabled", False):
            sources.append((WeWorkRemotelySource(wwr_cfg), wwr_cfg.get("feed_url", "")))

        rok_cfg = rss_cfg.get("remoteok", {})
        if rok_cfg.get("enabled", False):
            sources.append((RemoteOKSource(rok_cfg), rok_cfg.get("api_url", "")))

    manual_cfg = tier2_cfg.get("manual_import", {})
    if manual_cfg.get("enabled", False):
        # Resolve import_file_path relative to MODULE_ROOT if not absolute
        import_path = manual_cfg.get("import_file_path", "")
        if import_path and not Path(import_path).is_absolute():
            import_path = str(MODULE_ROOT / import_path)
        cfg_with_abs = dict(manual_cfg)
        cfg_with_abs["import_file_path"] = import_path
        sources.append((ManualImportSource(cfg_with_abs), import_path))

    return sources


def _build_sources_from_yaml() -> list:
    """Build source instances from config_sources.yaml (CLI / production use).

    Returns:
        List of (source_instance, board_identifier) tuples for all enabled boards.
    """
    config = _load_ats_config()
    tier1 = config.get("tier_1_ats", {})
    sources = []

    gh = tier1.get("greenhouse", {})
    if gh.get("enabled", False):
        for board in gh.get("boards", []):
            cfg = dict(board)
            cfg["enabled"] = True
            src = GreenhouseSource(cfg)
            sources.append((src, cfg.get("board_token", "")))

    lv = tier1.get("lever", {})
    if lv.get("enabled", False):
        for board in lv.get("boards", []):
            cfg = dict(board)
            cfg["enabled"] = True
            src = LeverSource(cfg)
            sources.append((src, cfg.get("site", "")))

    ashby = tier1.get("ashby", {})
    if ashby.get("enabled", False):
        for board in ashby.get("boards", []):
            cfg = dict(board)
            cfg["enabled"] = True
            src = AshbySource(cfg)
            sources.append((src, cfg.get("board_name", "")))

    wk = tier1.get("workable", {})
    if wk.get("enabled", False):
        for board in wk.get("boards", []):
            cfg = dict(board)
            cfg["enabled"] = True
            src = WorkableSource(cfg)
            sources.append((src, cfg.get("account_subdomain", "")))

    # Tier 2: RSS feeds + manual import (Phase 3)
    tier2_cfg = _load_tier2_config()
    sources.extend(_build_tier2_sources(tier2_cfg))

    return sources


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_fetch(constraints: dict, run_id: str) -> dict:
    """Stage 1 orchestrator: fetch from all configured ATS sources and normalize.

    Accepts either:
    - An inline per-platform config dict (keys: greenhouse, lever, ashby, workable)
      → used by tests and direct CLI invocation with overrides
    - An empty dict or non-ATS-key dict → loads config from config_sources.yaml

    SRC-05 graceful degradation:
    - A source that raises any exception is caught and logged to blocked_sources.
    - A source with SourceResult.errors gets logged to blocked_sources (errors present
      means the fetch was partially or fully blocked).
    - When ALL sources fail, returns normally with opportunities=[], run_result="failure".
    - Disabled sources are silently skipped.

    Args:
        constraints: Inline platform config dict (if it contains ATS platform keys)
                     OR job-search filter constraints (if loaded from YAML).
        run_id:      Identifies this radar run (stamped onto every opportunity).

    Returns:
        Dict with keys:
            "opportunities":    list of normalized DATA-01 dicts
            "blocked_sources":  list of {source, board, errors, rate_limited} dicts
            "fetch_summary":    {total_fetched, total_blocked_sources, run_result}
    """
    all_opportunities: list[dict] = []
    blocked_sources: list[dict] = []

    # Detect whether constraints carries inline platform configs or is a search filter
    has_inline_config = bool(constraints and _ATS_PLATFORM_KEYS.intersection(constraints.keys()))

    if has_inline_config:
        source_list = _build_sources_from_inline(constraints)
    else:
        source_list = _build_sources_from_yaml()

    for source_instance, board_id in source_list:
        try:
            result = source_instance.fetch(constraints if not has_inline_config else {})

            # Normalize each raw opportunity to the DATA-01 schema
            for raw_opp in result.opportunities:
                normalized = normalize_opportunity(raw_opp, run_id)
                all_opportunities.append(normalized)

            # Log sources that returned errors (partially or fully blocked)
            if result.errors:
                blocked_sources.append({
                    "source": source_instance.name,
                    "board": board_id,
                    "errors": result.errors,
                    "rate_limited": result.rate_limited,
                })
                logger.warning(
                    "%s [%s]: errors=%s", source_instance.name, board_id, result.errors
                )
            else:
                logger.info(
                    "%s [%s]: fetched %d opportunities",
                    source_instance.name,
                    board_id,
                    len(result.opportunities),
                )

        except Exception as exc:
            # Defensive catch: connectors should never raise, but guard anyway
            blocked_sources.append({
                "source": source_instance.name,
                "board": board_id,
                "errors": [f"Unhandled exception: {type(exc).__name__}: {exc}"],
                "rate_limited": False,
            })
            logger.exception(
                "%s [%s]: crashed unexpectedly", source_instance.name, board_id
            )

    # Apply role-keyword filter (SRC-06) — Stage 1.5
    # Keeps only in-scope opportunities; out_of_scope logged for transparency
    if not all_opportunities:
        filter_result = {
            "in_scope": [],
            "out_of_scope": [],
            "filter_summary": {
                "total": 0,
                "in_scope_count": 0,
                "out_of_scope_count": 0,
                "filter_rate": 0.0,
            }
        }
        in_scope_opportunities = []
        filter_summary = filter_result["filter_summary"]
    else:
        filter_result = run_filter(all_opportunities)
        in_scope_opportunities = filter_result["in_scope"]
        filter_summary = filter_result["filter_summary"]
        if filter_summary.get("out_of_scope_count", 0) > 0:
            logger.info(
                "run_filter: %d out-of-scope opportunities excluded (%.1f%% pass rate)",
                filter_summary["out_of_scope_count"],
                100.0 * filter_summary.get("filter_rate", 0.0),
            )

    # Phase 4: deduplication pass (cross-run seen-store + within-run fuzzy)
    try:
        deduped = run_dedup_pass(in_scope_opportunities, db_path=_DEFAULT_DB_PATH)
        print(f"[DEDUP] {len(in_scope_opportunities)} raw -> {len(deduped)} unique opportunities")
        in_scope_opportunities = deduped
    except Exception as exc:
        print(f"[DEDUP] WARNING: dedup pass failed ({exc}); returning raw results")

    # Phase 5: score deduplicated opportunities
    in_scope_opportunities = run_scoring_pass(in_scope_opportunities)

    # Determine run result
    if not blocked_sources:
        run_result = "success"
    elif in_scope_opportunities:
        run_result = "partial_success"
    else:
        run_result = "failure"

    return {
        "opportunities": in_scope_opportunities,
        "blocked_sources": blocked_sources,
        "out_of_scope_opportunities": filter_result["out_of_scope"],
        "filter_summary": filter_summary,
        "fetch_summary": {
            "total_fetched": len(in_scope_opportunities),
            "total_blocked_sources": len(blocked_sources),
            "run_result": run_result,
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO)
    result = run_fetch({}, "cli-test-run")
    print(json.dumps(result["fetch_summary"], indent=2))
    print(f"Fetched: {result['fetch_summary']['total_fetched']} opportunities")
    sys.exit(0)
