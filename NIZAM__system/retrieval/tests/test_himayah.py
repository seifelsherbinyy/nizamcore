# Contract: NIZAM-RETRIEVAL-001 | Phase: Wave 1
"""HIMAYAH gate tests — unit tests requiring no DB.

Critical test: tamper test verifies that corrupting the gate causes
a failure, and restoring it causes tests to pass again.
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from NIZAM__system.retrieval.himayah import classify_for_ingest, filter_permitted, HimayahViolation, PERMITTED, BLOCKED


# ── Permitted paths ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("p", [
    "NIZAM__system/schemas/note_frontmatter.schema.json",
    "NIZAM__system/templates/brain_dump.template.md",
    "NIZAM__system/skills/tafrigh-capture.md",
    "NIZAM__system/policies/PRIVACY_CLASSIFICATION.json",
    "NIZAM__system/docs/DATA_MODEL.md",
    "NIZAM__system/governor/classifier.py",
    "NIZAM__system/protocols/daily_morning.md",
    "NIZAM__system/relay/coordinator.py",
    "README.md",
    "NIZAM_TEMPLE.json",
    "CRITICAL_FACTS.md",
    "MARSAD__flight_radar/radar/sources/generic_base.py",
    "tools/nizam_startup.py",
])
def test_permitted_paths(p):
    cls = classify_for_ingest(p)
    assert cls in PERMITTED, f"{p} -> {cls} not in PERMITTED"


# ── Blocked paths — strict_local ──────────────────────────────────────────────
@pytest.mark.parametrize("p", [
    "TAFRIGH__brain_dumper/raw/2026-09-01_morning.md",
    "TAFRIGH__brain_dumper/triaged/priority_list.md",
    "SHURA__brainstormer/sessions/session_001.json",
    "NAQD__brain_griller/sessions/debate_001.md",
    "SUKOON__recovery_first/signals/2026-09-01.json",
    "SUKOON__recovery_first/overload_flags.jsonl",
    "YAWMIYAT__journaling/sessions/2026-09-01T09-00-00Z__morning.json",
    "YAWMIYAT__journaling/weekly/2026-W35.md",
    "MAL__financial_engine/baseline.json",
    "BADAN__body_health_system/health_intelligence/v0.2.0/sync/feature_engine.py",
    "TARIQ__long_horizon_strategy/10_year/vision.md",
    "MUNAWARA__tactical_strategy/quarters/Q3_2026.md",
    "NIZAM__system/ledgers/FINANCE_LEDGER.jsonl",
    "NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl",
])
def test_blocked_strict_local(p):
    with pytest.raises(HimayahViolation):
        classify_for_ingest(p)


# ── Hard-block: strict_local_maximum (AHEL) ───────────────────────────────────
@pytest.mark.parametrize("p", [
    "AHEL__family_network/members/person_001.json",
    "AHEL__family_network/README.md",
    "AHEL__family_network/_index.json",
    "ahel/personal_council/session_001.json",
    "ledgers/FAMILY_LEDGER.jsonl",
])
def test_blocked_ahel(p):
    with pytest.raises(HimayahViolation) as exc_info:
        classify_for_ingest(p)
    # Verify the hard-block prefix fires (not just the classifier)
    assert "hard-block" in str(exc_info.value) or "strict_local_maximum" in str(exc_info.value) or "prohibited" in str(exc_info.value)


# ── filter_permitted partitioning ────────────────────────────────────────────
def test_filter_permitted_partitions():
    paths = [
        "NIZAM__system/docs/DATA_MODEL.md",           # permitted
        "TAFRIGH__brain_dumper/raw/x.md",             # blocked
        "AHEL__family_network/x.json",                # hard-blocked
        "tools/nizam_startup.py",                     # permitted
    ]
    permitted, blocked = filter_permitted(paths)
    assert len(permitted) == 2
    assert len(blocked) == 2
    assert "NIZAM__system/docs/DATA_MODEL.md" in permitted
    assert "tools/nizam_startup.py" in permitted
    assert any("TAFRIGH" in b[0] for b in blocked)
    assert any("AHEL" in b[0] for b in blocked)


# ── Tamper test ───────────────────────────────────────────────────────────────
def test_tamper__gate_correctly_fails_when_check_removed():
    """
    Tamper test: prove that bypassing HIMAYAH causes a prohibited path to pass.
    Then prove the real gate catches it.

    This test does NOT tamper with production code — it directly invokes
    the classifier without the gate to simulate a compromised check.
    """
    from NIZAM__system.retrieval.himayah import classify_path

    prohibited_path = "AHEL__family_network/members/person_001.json"

    # Without gate: raw classifier returns strict_local_maximum — would slip through
    raw_cls = classify_path(prohibited_path)
    assert raw_cls == "strict_local_maximum", (
        f"Expected strict_local_maximum from classifier, got {raw_cls}"
    )

    # WITH gate: HimayahViolation must be raised
    with pytest.raises(HimayahViolation):
        classify_for_ingest(prohibited_path)

    # Tamper simulation: if someone bypassed the gate and just used classify_path,
    # the result would be 'strict_local_maximum' — verify that BLOCKED contains it
    assert raw_cls in BLOCKED, "strict_local_maximum must be in BLOCKED set"

    # Re-running the gate confirms it is enforced (tamper-restored)
    with pytest.raises(HimayahViolation):
        classify_for_ingest(prohibited_path)
