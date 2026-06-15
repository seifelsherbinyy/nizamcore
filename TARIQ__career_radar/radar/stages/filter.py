"""filter.py — Role-keyword filter stage for TARIQ Career Radar (SRC-06).

Runs after fetch + normalize (Stage 1) and before dedup (Stage 2).
Filters opportunities to remote-USD AI/data/AI-ops/coordination roles by
matching opportunity titles against Seif's profile_cache.json role_keywords.

Exact substring match (deterministic, simple) — fuzzy matching deferred to Phase 4.
Fail-open: if profile seed is unavailable, all opportunities pass through.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def run_filter(
    opportunities: list[dict],
    profile_seed: Optional[dict] = None,
) -> dict:
    """Filter opportunities by role keyword match against profile seed (SRC-06).

    Args:
        opportunities: List of normalized opportunity dicts from the fetch stage.
                       Each dict must have at least a "title" key.
        profile_seed:  Profile dict with "role_keywords" (dict[group_name, list[keyword]]).
                       If None, attempts to load via radar.config.load_profile_seed().
                       On load failure, returns fail-open (all opportunities in-scope).

    Returns:
        Dict with keys:
            "in_scope":       List of opportunities matching at least one keyword.
            "out_of_scope":   List of opportunities matching no keyword.
            "filter_summary": {total, in_scope_count, out_of_scope_count, filter_rate}

    Note: Mutates each in-scope opportunity dict in-place by adding "matched_role_group".
    """
    if profile_seed is None:
        profile_seed = _load_profile_seed_safe()

    if profile_seed is None:
        # Fail-open: pass all opportunities through
        logger.warning(
            "run_filter: profile seed unavailable — all %d opps pass through",
            len(opportunities),
        )
        return _build_result(
            in_scope=list(opportunities), out_of_scope=[], total=len(opportunities)
        )

    role_keywords: dict = profile_seed.get("role_keywords", {})

    if not role_keywords:
        logger.warning(
            "run_filter: role_keywords empty in profile seed — all opps pass through"
        )
        return _build_result(
            in_scope=list(opportunities), out_of_scope=[], total=len(opportunities)
        )

    in_scope: list[dict] = []
    out_of_scope: list[dict] = []

    for opp in opportunities:
        title_lower = (opp.get("title") or "").lower()
        matched = False
        matched_group: Optional[str] = None

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
        "run_filter: %d in-scope, %d out-of-scope (%.1f%% pass rate)",
        len(in_scope),
        len(out_of_scope),
        100.0 * len(in_scope) / max(len(opportunities), 1),
    )

    return _build_result(
        in_scope=in_scope, out_of_scope=out_of_scope, total=len(opportunities)
    )


def _build_result(in_scope: list, out_of_scope: list, total: int) -> dict:
    """Build the standard run_filter return dict."""
    return {
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "filter_summary": {
            "total": total,
            "in_scope_count": len(in_scope),
            "out_of_scope_count": len(out_of_scope),
            "filter_rate": len(in_scope) / max(total, 1),
        },
    }


def _load_profile_seed_safe() -> Optional[dict]:
    """Load profile seed via radar.config; return None on any failure (fail-open)."""
    try:
        from radar.config import load_profile_seed  # lazy import — avoids circular deps

        return load_profile_seed()
    except Exception as exc:
        logger.warning("run_filter: failed to load profile seed: %s", exc)
        return None
