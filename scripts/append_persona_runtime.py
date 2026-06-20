#!/usr/bin/env python3
"""append_persona_runtime.py — add v1.1 runtime block to personas.

Implements B2.1–B2.8 of NIZAM Next Plan v2:
  - Append `runtime` block + `codename` + `schema_version` to each
    existing persona JSON (TAFRIGH, SHURA, NAQD, TARIQ, MUNAWARA, BADAN).
  - Create new persona files for MARSAD (Tahir) and HIKMAH (Khaldun).
  - Leave AHEL.json (Yusra) and MAL.json untouched at this pass.

The script is IDEMPOTENT: re-running emits no diff.

Pure stdlib.

Acceptance:
  - 8 persona files exist (TAFRIGH, SHURA, NAQD, TARIQ, MUNAWARA, MARSAD,
    HIKMAH, BADAN) with a non-empty `runtime` block.
  - Each runtime block carries: agent_enabled, primary_model,
    reviewer_model, fallback_chain, delegates_to, max_tool_calls,
    timeout_seconds, retry_backoff_seconds, context_sources, egress_class,
    cost_ceiling, feedback_ledger, writes_to_ledgers, gates.
  - The 14 soul fields are NOT modified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = REPO_ROOT / "NIZAM__system" / "personas"

DEFAULTS_FALLBACK = ["deepseek-v4-flash", "kimi-k2"]
DEFAULTS_BACKOFF = [2, 5, 15]
DEFAULTS_COST = {"soft_usd": 50, "hard_usd": 300}
GATES_STD = {"pre": ["SUKOON"], "pre_write": ["HIMAYAH"], "post": ["THABAT"]}
LEARNING = "NIZAM__system/ledgers/LEARNING_LEDGER.jsonl"


SPEC = {
    "TAFRIGH": {
        "codename": "Amin",
        "runtime": {
            "agent_enabled": True,
            "primary_model": "deepseek-v4-flash",
            "reviewer_model": "kimi-k2.6",
            "fallback_chain": DEFAULTS_FALLBACK,
            "delegates_to": ["Salman"],
            "max_tool_calls": 4,
            "timeout_seconds": 90,
            "retry_backoff_seconds": DEFAULTS_BACKOFF,
            "context_sources": [
                "SOUL.md",
                "CRITICAL_FACTS.md",
                "NIZAM__system/personas/TAFRIGH.json",
            ],
            "egress_class": "strict_local",
            "cost_ceiling": DEFAULTS_COST,
            "feedback_ledger": LEARNING,
            "writes_to_ledgers": ["EVENT_LEDGER.jsonl"],
            "gates": GATES_STD,
        },
    },
    "SHURA": {
        "codename": "Salman",
        "runtime": {
            "agent_enabled": True,
            "primary_model": "deepseek-v4-pro",
            "reviewer_model": "kimi-k2.6",
            "fallback_chain": ["deepseek-v4-flash", "kimi-k2"],
            "delegates_to": ["Hazim", "Khalid"],
            "max_tool_calls": 8,
            "timeout_seconds": 120,
            "retry_backoff_seconds": DEFAULTS_BACKOFF,
            "context_sources": [
                "SOUL.md",
                "CRITICAL_FACTS.md",
                "NIZAM_TEMPLE.json",
                "NIZAM__system/personas/SHURA.json",
            ],
            "egress_class": "strict_local",
            "cost_ceiling": DEFAULTS_COST,
            "feedback_ledger": LEARNING,
            "writes_to_ledgers": ["EVENT_LEDGER.jsonl", "LEARNING_LEDGER.jsonl"],
            "gates": GATES_STD,
        },
    },
    "NAQD": {
        "codename": "Hazim",
        "runtime": {
            "agent_enabled": True,
            "primary_model": "claude-sonnet-4-6",
            "reviewer_model": "kimi-k2.6",
            "fallback_chain": ["deepseek-v4-pro", "kimi-k2"],
            "delegates_to": [],
            "max_tool_calls": 8,
            "timeout_seconds": 180,
            "retry_backoff_seconds": DEFAULTS_BACKOFF,
            "context_sources": [
                "SOUL.md",
                "CRITICAL_FACTS.md",
                "NIZAM_TEMPLE.json",
                "NIZAM__system/personas/NAQD.json",
            ],
            "egress_class": "strict_local",
            "cost_ceiling": DEFAULTS_COST,
            "feedback_ledger": LEARNING,
            "writes_to_ledgers": ["EVENT_LEDGER.jsonl", "LEARNING_LEDGER.jsonl"],
            "gates": GATES_STD,
        },
    },
    "TARIQ": {
        "codename": "Tariq",
        "runtime": {
            "agent_enabled": True,
            "primary_model": "claude-sonnet-4-6",
            "reviewer_model": "kimi-k2.6",
            "fallback_chain": ["deepseek-v4-pro", "kimi-k2"],
            "delegates_to": ["Khaldun", "Khalid", "Tahir"],
            "max_tool_calls": 12,
            "timeout_seconds": 240,
            "retry_backoff_seconds": DEFAULTS_BACKOFF,
            "context_sources": [
                "SOUL.md",
                "CRITICAL_FACTS.md",
                "NIZAM_TEMPLE.json",
                "NIZAM__system/personas/TARIQ.json",
                "TARIQ__long_horizon_strategy/",
            ],
            "egress_class": "strict_local",
            "cost_ceiling": DEFAULTS_COST,
            "feedback_ledger": LEARNING,
            "writes_to_ledgers": ["STRATEGY_LEDGER.jsonl", "EVENT_LEDGER.jsonl"],
            "gates": GATES_STD,
        },
    },
    "MUNAWARA": {
        "codename": "Khalid",
        "runtime": {
            "agent_enabled": True,
            "primary_model": "deepseek-v4-pro",
            "reviewer_model": "kimi-k2.6",
            "fallback_chain": DEFAULTS_FALLBACK,
            "delegates_to": ["Khaldun", "Tariq"],
            "max_tool_calls": 10,
            "timeout_seconds": 180,
            "retry_backoff_seconds": DEFAULTS_BACKOFF,
            "context_sources": [
                "SOUL.md",
                "NIZAM__system/personas/MUNAWARA.json",
                "MUNAWARA__tactical_strategy/",
            ],
            "egress_class": "strict_local",
            "cost_ceiling": DEFAULTS_COST,
            "feedback_ledger": LEARNING,
            "writes_to_ledgers": ["BATTLE_LEDGER.jsonl", "EVENT_LEDGER.jsonl",
                                  "STRATEGY_LEDGER.jsonl"],
            "gates": GATES_STD,
        },
    },
    "BADAN": {
        "codename": "Hayat",
        "runtime": {
            "agent_enabled": True,
            "primary_model": "deepseek-v4-flash",
            "reviewer_model": "kimi-k2.6",
            "fallback_chain": DEFAULTS_FALLBACK,
            "delegates_to": [],
            "max_tool_calls": 4,
            "timeout_seconds": 90,
            "retry_backoff_seconds": DEFAULTS_BACKOFF,
            "context_sources": [
                "NIZAM__system/personas/BADAN.json",
            ],
            "egress_class": "strict_local",
            "cost_ceiling": DEFAULTS_COST,
            "feedback_ledger": LEARNING,
            "writes_to_ledgers": ["BODY_LEDGER.jsonl", "EVENT_LEDGER.jsonl"],
            "gates": {"pre": ["SUKOON"], "pre_write": ["HIMAYAH"], "post": ["THABAT"]},
        },
    },
}


MARSAD_BODY = {
    "module": "MARSAD",
    "codename": "Tahir",
    "meaning_ar": "observatory / lookout",
    "phase": 2,
    "namesake": "Tahir — the watchful scout. Plain, alert, brings news without embroidery.",
    "role": "Intelligence scout — surveys external sources (news, scholarly, market, regulatory, infra) for changes relevant to TARIQ/MUNAWARA decisions. Reports facts; does not interpret strategy.",
    "mode": "Pull-based observation. Cite sources. Mark confidence per finding.",
    "tone": "Terse, sourced, dated. No editorializing.",
    "inputs": [
        "watchlist topics from TARIQ/Khalid",
        "scheduled scans (RSS feeds, search alerts, public APIs)",
        "operator ad-hoc queries"
    ],
    "outputs": [
        "intel briefs (per-topic, dated, sourced)",
        "delta reports (what changed vs last scan)",
        "flagged anomalies for Salman/Hazim review"
    ],
    "operating_rules": [
        "Every finding cites a source with timestamp and URL/path.",
        "Mark confidence: CONFIRMED / LIKELY / RUMOR.",
        "Never recommend strategy — escalate to Tariq/Khalid for interpretation.",
        "Pull only; never push. Operator controls the watchlist.",
        "All external fetches go through HIMAYAH egress check (egress_class: review_before_commit) and respect ZDR for any LLM-summarization step."
    ],
    "skills": ["/marsad-watchlist", "/marsad-scan", "/marsad-brief"],
    "gates": ["HIMAYAH", "THABAT"],
    "target_folders": {
        "briefs": "MARSAD__flight_radar/briefs/",
        "watchlist": "MARSAD__flight_radar/watchlist/",
        "scans": "MARSAD__flight_radar/scans/"
    },
    "privacy": "review_before_commit",
    "ledger_writes_to": ["EVENT_LEDGER.jsonl", "LEARNING_LEDGER.jsonl"],
    "runtime": {
        "agent_enabled": True,
        "primary_model": "deepseek-v4-flash",
        "reviewer_model": "kimi-k2.6",
        "fallback_chain": DEFAULTS_FALLBACK,
        "delegates_to": ["Salman"],
        "max_tool_calls": 6,
        "timeout_seconds": 120,
        "retry_backoff_seconds": DEFAULTS_BACKOFF,
        "context_sources": [
            "NIZAM__system/personas/MARSAD.json",
            "MARSAD__flight_radar/watchlist/"
        ],
        "egress_class": "review_before_commit",
        "cost_ceiling": DEFAULTS_COST,
        "feedback_ledger": LEARNING,
        "writes_to_ledgers": ["EVENT_LEDGER.jsonl", "LEARNING_LEDGER.jsonl"],
        "gates": {"pre": [], "pre_write": ["HIMAYAH"], "post": ["THABAT"]}
    },
    "schema_version": "1.1"
}


HIKMAH_BODY = {
    "module": "HIKMAH",
    "codename": "Khaldun",
    "meaning_ar": "wisdom",
    "phase": 1,
    "namesake": "Ibn Khaldun — the chronicler-synthesist. Patterns over time, civilizational arcs over single events.",
    "role": "Weekly synthesist — reads the week's EVENT_LEDGER + LEARNING_LEDGER and emits a single integrative brief that updates LEARNING_LEDGER with promoted patterns.",
    "mode": "Reflective, longitudinal. Operates on Sunday cadence.",
    "tone": "Calm, observant, integrative. Names patterns without overclaim.",
    "inputs": [
        "last 7 days of EVENT_LEDGER",
        "last 7 days of LEARNING_LEDGER",
        "open battles from MUNAWARA",
        "watchlist deltas from MARSAD"
    ],
    "outputs": [
        "weekly brief (markdown)",
        "patterns_promoted entries to LEARNING_LEDGER",
        "candidate items for STRATEGY_LEDGER (for Tariq review)"
    ],
    "operating_rules": [
        "Read-only over EVENT_LEDGER; write-only to LEARNING_LEDGER and STRATEGY_LEDGER (the latter via Tariq's confirmation).",
        "Promote patterns with confidence labels — CONFIRMED requires ≥3 corroborating events.",
        "Flag contradictions; do not silently resolve. Hazim arbitrates.",
        "Cadence: Sunday 09:00 local; ad-hoc allowed."
    ],
    "skills": ["/hikmah-weekly", "/hikmah-pattern-promote", "/hikmah-contradictions"],
    "gates": ["HIMAYAH", "THABAT"],
    "target_folders": {
        "weekly": "HIKMAH__weekly_synthesis/weekly/",
        "patterns": "HIKMAH__weekly_synthesis/patterns/"
    },
    "privacy": "strict_local",
    "ledger_writes_to": ["LEARNING_LEDGER.jsonl"],
    "runtime": {
        "agent_enabled": True,
        "primary_model": "claude-sonnet-4-6",
        "reviewer_model": "kimi-k2.6",
        "fallback_chain": ["deepseek-v4-pro", "kimi-k2"],
        "delegates_to": [],
        "max_tool_calls": 10,
        "timeout_seconds": 300,
        "retry_backoff_seconds": DEFAULTS_BACKOFF,
        "context_sources": [
            "SOUL.md",
            "NIZAM__system/personas/HIKMAH.json",
            "NIZAM__system/ledgers/EVENT_LEDGER.jsonl",
            "NIZAM__system/ledgers/LEARNING_LEDGER.jsonl"
        ],
        "egress_class": "strict_local",
        "cost_ceiling": DEFAULTS_COST,
        "feedback_ledger": LEARNING,
        "writes_to_ledgers": ["LEARNING_LEDGER.jsonl"],
        "gates": {"pre": [], "pre_write": ["HIMAYAH"], "post": ["THABAT"]}
    },
    "schema_version": "1.1"
}


def update_existing(name: str) -> tuple[bool, str]:
    path = PERSONAS / f"{name}.json"
    if not path.exists():
        return False, f"MISSING {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    spec = SPEC[name]
    changed = False
    if data.get("codename") != spec["codename"]:
        data["codename"] = spec["codename"]
        changed = True
    if data.get("schema_version") != "1.1":
        data["schema_version"] = "1.1"
        changed = True
    if "runtime" not in data or data["runtime"] != spec["runtime"]:
        data["runtime"] = spec["runtime"]
        changed = True
    if changed:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return True, f"UPDATED {name}"
    return False, f"NOOP    {name}"


def create_new(name: str, body: dict) -> tuple[bool, str]:
    path = PERSONAS / f"{name}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing == body:
            return False, f"NOOP    {name} (already canonical)"
    path.write_text(
        json.dumps(body, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True, f"CREATED {name}"


def main() -> int:
    results: list[str] = []
    for name in SPEC:
        _, msg = update_existing(name)
        results.append(msg)
    _, msg = create_new("MARSAD", MARSAD_BODY)
    results.append(msg)
    _, msg = create_new("HIKMAH", HIKMAH_BODY)
    results.append(msg)
    for r in results:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
