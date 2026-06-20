"""NIZAM governor package — Ammar (STEWARD).

Components:
    classifier            — HIMAYAH egress firewall classifier
    ledger_writer         — sole writer for hash-chained JSONL ledgers
    cost_ceiling          — $50 soft / $300 hard / panic stop
    kill_switch           — NIZAM_KILL_ALL=1 panic stop
    sync_arbiter          — VPS-authoritative cross-plane arbitration
    utils                 — generic helpers (refactored from
                            HIFZ__github_version_control/scripts/
                            nizam_governor_lib.py per B1.1)
"""
from __future__ import annotations

from . import (  # noqa: F401
    classifier,
    cost_ceiling,
    kill_switch,
    ledger_writer,
    strategy_sth,
    sync_arbiter,
    trace,
    utils,
)

__all__ = [
    "classifier",
    "cost_ceiling",
    "kill_switch",
    "ledger_writer",
    "strategy_sth",
    "sync_arbiter",
    "trace",
    "utils",
]

__version__ = "0.1.0"
