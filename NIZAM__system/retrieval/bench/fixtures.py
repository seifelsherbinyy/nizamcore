# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""Synthetic / redacted benchmark corpus.

NO real strict_local content. All personal identifiers replaced with
synthetic stand-ins. All dates shifted by a fixed offset. All monetary
values replaced with milliunit-format synthetic integers.

Fixture types match the real NIZAM corpus structure so chunking,
lexical, and dense retrieval can be realistically measured.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone

# ── Content templates (all synthetic) ────────────────────────────────────────
SYNTHETIC_DOCS = [
    {
        "rel_path": "NIZAM__system/docs/bench/synth_protocol_01.md",
        "classification": "private_github",
        "content": """# NIZAM Daily Morning Protocol

## Purpose
This protocol establishes the morning initialization sequence for the NIZAM system.
It covers recovery gate check, priority queue review, and system health verification.

## SUKOON Gate
Before any tactical work, check recovery status. If recovery score < 50 or
HRV is more than 20% below personal baseline, activate downshift mode.
Downshift mode: no new commitments, reduce workload by 50%, prioritize rest.

## Priority Queue
1. Check CRITICAL_FACTS for active gates.
2. Review MUNAWARA weekly battle plan.
3. Scan NAQD for unresolved contradictions.
4. Check MARSAD for active flight alerts.

## Health Check
Run `python3 tools/nizam_startup.py` to verify all systems operational.
""",
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_schema_finance_01.json",
        "classification": "private_github",
        "content": json.dumps({
            "schema_id": "finance_baseline_v1",
            "description": "Synthetic financial baseline schema for benchmark purposes.",
            "fields": {
                "monthly_income_milli": {"type": "integer", "description": "Income in milliunits. 1 EGP = 1000 milliunits."},
                "monthly_expenses_milli": {"type": "integer"},
                "savings_rate": {"type": "number"},
                "currency": {"type": "string", "enum": ["EGP", "USD"]},
            },
            "examples": [
                {"monthly_income_milli": 45000000, "monthly_expenses_milli": 32000000,
                 "savings_rate": 0.289, "currency": "EGP"}
            ]
        }, indent=2),
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_protocol_decisions.md",
        "classification": "private_github",
        "content": """# QARAR Decision Framework

## Decision Score Model
Every significant decision receives a score across three dimensions:
1. Alignment with long-horizon strategy (TARIQ gate)
2. SUKOON impact (will this increase or decrease load?)
3. Reversibility (can this be undone if wrong?)

## Syntax
Use `qarar-decide` skill with the following inputs:
- decision_text: plain description
- options: list of alternatives
- constraints: hard limits (financial, time, energy)

## Output
QARAR returns: recommended option, risk score, dissenting view (NAQD),
and a THABAT receipt if the decision is logged.

## Arabic/English note
QARAR operates in both Arabic and English. The decision ledger records
both the original language and a normalized English summary.
""",
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_ledger_events.jsonl",
        "classification": "review_before_commit",
        "content": "\n".join([
            json.dumps({"event_id": "EVT-SYNTH-001", "date": "2026-07-15", "type": "milestone",
                        "title": "Q3 review completed", "module": "MUNAWARA",
                        "privacy_level": "review_before_commit"}),
            json.dumps({"event_id": "EVT-SYNTH-002", "date": "2026-07-22", "type": "decision",
                        "title": "Framework upgrade approved", "module": "NIZAM__system",
                        "privacy_level": "review_before_commit"}),
            json.dumps({"event_id": "EVT-SYNTH-003", "date": "2026-08-01", "type": "learning",
                        "title": "Retrieval latency measurement methodology defined",
                        "module": "NIZAM__system", "privacy_level": "review_before_commit"}),
        ]),
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_arabic_note.md",
        "classification": "private_github",
        "content": """# ملاحظة تجريبية — نظام الاسترجاع

## الغرض
هذه ملاحظة اصطناعية لاختبار قدرة نظام الاسترجاع على معالجة النصوص العربية.
جميع المعلومات الواردة هنا مصطنعة ولا تمثل بيانات حقيقية.

## المتطلبات
- دعم الترميز UTF-8 الكامل
- الفهرسة الصحيحة للنص العربي
- البحث النصي في كلا اللغتين

## Bilingual note
This fixture tests Arabic + English hybrid retrieval. The NIZAM system
operates in both languages. Decision records and strategy documents
may appear in either language or both.
""",
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_superseded_v1.md",
        "classification": "review_before_commit",
        "content": "# Old Protocol v1\n\nThis is version 1 of the protocol. SUPERSEDED by v2.\n\nOld rule: check recovery every 2 hours.\n",
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_superseded_v2.md",
        "classification": "review_before_commit",
        "content": "# Updated Protocol v2\n\nThis supersedes v1. Check recovery once at morning initialization only.\n\nCurrent rule: single morning recovery check is sufficient per SUKOON gate data.\n",
    },
    {
        "rel_path": "NIZAM__system/docs/bench/synth_exact_id.md",
        "classification": "private_github",
        "content": """# Artifact EVT-SYNTH-EXACT-9371

## Purpose
This document has an exact synthetic identifier: EVT-SYNTH-EXACT-9371.
It tests that exact-ID lookup retrieves this document and not others.

## Content
Schema version: nizam_schema_v3.
Module: NIZAM__system.
Status: active.
""",
    },
]

# ── Query families ─────────────────────────────────────────────────────────────
BENCHMARK_QUERIES = [
    # exact_lookup
    {"qid": "Q-EXACT-01", "family": "exact_lookup",
     "text": "EVT-SYNTH-EXACT-9371",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_exact_id.md"]},
    # semantic_paraphrase
    {"qid": "Q-SEM-01", "family": "semantic_paraphrase",
     "text": "morning system initialization and recovery gate check",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_protocol_01.md"]},
    # current_state
    {"qid": "Q-CURR-01", "family": "current_state",
     "text": "current rule for recovery check frequency",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_superseded_v2.md"]},
    # historical
    {"qid": "Q-HIST-01", "family": "historical",
     "text": "old protocol v1 recovery rule",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_superseded_v1.md"]},
    # multilingual
    {"qid": "Q-ML-01", "family": "multilingual",
     "text": "Arabic text retrieval UTF-8 support",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_arabic_note.md"]},
    # decision_framework
    {"qid": "Q-DEC-01", "family": "semantic_paraphrase",
     "text": "how to score a decision using QARAR and NAQD",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_protocol_decisions.md"]},
    # jsonl
    {"qid": "Q-JSONL-01", "family": "exact_lookup",
     "text": "milestone Q3 review EVT-SYNTH-002",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_ledger_events.jsonl"]},
    # schema
    {"qid": "Q-SCHEMA-01", "family": "semantic_paraphrase",
     "text": "financial milliunits monthly income schema definition",
     "relevant_paths": ["NIZAM__system/docs/bench/synth_schema_finance_01.json"]},
]


def write_fixtures(dest_root: str) -> list[tuple[str, str]]:
    """Write synthetic fixture files to dest_root. Returns [(rel_path, abs_path)]."""
    import pathlib
    written = []
    for doc in SYNTHETIC_DOCS:
        p = pathlib.Path(dest_root) / doc["rel_path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(doc["content"], encoding="utf-8")
        written.append((doc["rel_path"], str(p)))
    return written
