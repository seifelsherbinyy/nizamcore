"""constraints.py — Remote USD lane constraints for TARIQ Career Radar.

Defines the filtering and targeting constraints for the v1 Remote USD lane.
Extensible to GCC/Europe lanes in future phases.

Pure stdlib.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RemoteUSDConstraints:
    lane: str = "Remote USD"
    target_role_keywords: list[str] = field(default_factory=lambda: [
        "ai operations",
        "ai ops",
        "llm evaluation",
        "data scientist",
        "machine learning",
        "data analyst",
        "business analyst",
        "project coordinator",
        "program manager",
        "growth analyst",
    ])
    exclude_keywords: list[str] = field(default_factory=lambda: [
        "sales",
        "marketing only",
        "non-technical",
        "unpaid",
    ])
    min_salary_usd: int = 0   # Phase 5 scoring applies salary filter
    require_remote: bool = True


REMOTE_USD_CONSTRAINTS = RemoteUSDConstraints()
