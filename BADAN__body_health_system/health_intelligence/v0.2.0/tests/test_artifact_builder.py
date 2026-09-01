#!/usr/bin/env python3
"""
test_artifact_builder.py — Classification, secret-scan and provenance tests.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0 (Drive durable-knowledge plane)
Phase: cloud-first reconciliation

These are the gate tests. They must fail closed, so every negative case here
asserts that a write is BLOCKED, not merely warned about. No real credential
value appears anywhere in this file; only credential shapes.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SYNC = os.path.join(os.path.dirname(_HERE), "sync")
if _SYNC not in sys.path:
    sys.path.insert(0, _SYNC)

import artifact_builder as AB  # noqa: E402
import storage_policy as P     # noqa: E402


# ── Storage-class gate ───────────────────────────────────────────────────────
def test_strict_local_is_never_drive_allowed():
    assert "strict_local" in P.DRIVE_FORBIDDEN_CLASSES
    assert "strict_local" not in P.DRIVE_ALLOWED_CLASSES


def test_vps_secret_is_never_drive_allowed():
    assert "vps_secret" in P.DRIVE_FORBIDDEN_CLASSES


def test_allowed_and_forbidden_are_disjoint():
    assert not (P.DRIVE_ALLOWED_CLASSES & P.DRIVE_FORBIDDEN_CLASSES)


@pytest.mark.parametrize("cls", sorted(P.DRIVE_FORBIDDEN_CLASSES))
def test_forbidden_class_blocks_write(cls):
    with pytest.raises(AB.ClassificationError):
        AB.assert_drive_permitted(cls, {"a": 1}, '{"a": 1}')


def test_unknown_class_blocks_write():
    with pytest.raises(AB.ClassificationError):
        AB.assert_drive_permitted("something_new", {"a": 1}, '{"a": 1}')


@pytest.mark.parametrize("cls", sorted(P.DRIVE_ALLOWED_CLASSES))
def test_allowed_class_with_clean_payload_passes(cls):
    AB.assert_drive_permitted(cls, {"recovery_score": 42}, '{"recovery_score": 42}')


# ── Secret scanning: shapes only, never real values ─────────────────────────
SECRET_SHAPES = [
    ("slack_bot_token", "xoxb-" + "0" * 12 + "-" + "1" * 12 + "-" + "A" * 24),
    ("google_oauth_client_secret", "GOCSPX-" + "A" * 28),
    ("google_api_key", "AIza" + "B" * 35),
    ("openai_key", "sk-" + "C" * 32),
    ("anthropic_key", "sk-ant-" + "D" * 40),
    ("github_token", "ghp_" + "E" * 36),
    ("bearer_header", "Authorization: Bearer " + "F" * 40),
    ("private_key_block", "-----BEGIN RSA PRIVATE KEY-----"),
    ("jwt", "eyJ" + "a" * 20 + "." + "b" * 20 + "." + "c" * 20),
    ("postgres_uri_with_password", "postgresql://user:notarealpw@db:5432/x"),
]


@pytest.mark.parametrize("rule,sample", SECRET_SHAPES, ids=[s[0] for s in SECRET_SHAPES])
def test_secret_shape_is_detected(rule, sample):
    findings = AB.scan_for_secrets(sample)
    assert findings, f"{rule} shape was not detected"
    assert rule in {f["rule"] for f in findings}


@pytest.mark.parametrize("rule,sample", SECRET_SHAPES, ids=[s[0] for s in SECRET_SHAPES])
def test_secret_shape_blocks_drive_write(rule, sample):
    payload = {"notes": f"harmless text {sample} more text"}
    text = json.dumps(payload)
    with pytest.raises(AB.ClassificationError):
        AB.assert_drive_permitted("drive_knowledge", payload, text)


def test_findings_never_echo_the_matched_value():
    sample = "ghp_" + "E" * 36
    findings = AB.scan_for_secrets(sample)
    blob = json.dumps(findings)
    assert sample not in blob
    assert "E" * 36 not in blob


def test_clean_health_text_is_not_flagged():
    text = json.dumps({
        "recovery_score": 31, "hrv_rmssd_ms": 40.53347,
        "note": "sleep 5.68 h, strain 4.38, no workout recorded",
        "planning_date": "2026-09-01",
    })
    assert AB.scan_for_secrets(text) == []


# ── Structural key gate ─────────────────────────────────────────────────────
@pytest.mark.parametrize("key", [
    "access_token", "refresh_token", "client_secret", "api_key",
    "password", "private_key", "authorization", "database_url", "webhook_url",
])
def test_credential_shaped_key_blocks_write(key):
    payload = {"data": {"nested": [{key: "short"}]}}
    with pytest.raises(AB.ClassificationError):
        AB.assert_drive_permitted("drive_knowledge", payload, json.dumps(payload))


def test_forbidden_key_path_is_reported():
    payload = {"a": {"b": [{"client_secret": "x"}]}}
    hits = AB.find_forbidden_keys(payload)
    assert hits == ["$.a.b[0].client_secret"]


def test_key_gate_is_case_insensitive():
    payload = {"Refresh_Token": "x"}
    assert AB.find_forbidden_keys(payload) == ["$.Refresh_Token"]


# ── Canonical serialization ─────────────────────────────────────────────────
def test_canonical_json_is_stable_across_key_order():
    a = AB.canonical_json({"b": 1, "a": 2})
    b = AB.canonical_json({"a": 2, "b": 1})
    assert a == b
    assert AB.sha256_hex(a) == AB.sha256_hex(b)


def test_canonical_json_ends_with_single_newline():
    data = AB.canonical_json({"a": 1})
    assert data.endswith(b"\n")
    assert not data.endswith(b"\n\n")


def test_canonical_json_uses_lf_only():
    data = AB.canonical_json({"a": "x", "b": {"c": 1}})
    assert b"\r" not in data


def test_sha256_hex_is_the_real_digest():
    import hashlib
    data = b"nizam"
    assert AB.sha256_hex(data) == hashlib.sha256(data).hexdigest()


# ── Readiness bands: lookup, never inference ────────────────────────────────
@pytest.mark.parametrize("score,expected", [
    (0, "low"), (33, "low"), (33.9, "low"),
    (34, "moderate"), (50, "moderate"), (66.9, "moderate"),
    (67, "high"), (100, "high"),
])
def test_readiness_band_boundaries(score, expected):
    assert AB.readiness_band(score) == expected


def test_readiness_band_missing_score_is_none_not_guessed():
    assert AB.readiness_band(None) is None


def test_readiness_band_out_of_range_is_none():
    assert AB.readiness_band(101) is None
    assert AB.readiness_band(-1) is None


# ── Daily plan artifact ─────────────────────────────────────────────────────
NOW = "2026-09-01T08:00:00+00:00"

VECTOR = {
    "today": {"recovery_score": 31.0, "rhr_bpm": 64.0, "sleep_total_hrs": 5.6752},
    "baselines": {
        "recovery_score": {"center": 50.0, "dispersion": 11.0,
                           "n_obs": 27, "basis_window_days": 30},
        "rhr_bpm": {"center": 60.0, "dispersion": 3.0,
                    "n_obs": 27, "basis_window_days": 30},
    },
    "windows": {
        "7": {
            "recovery_score": {"robust_z": -1.16, "percentile_rank": 0.14, "slope": -1.5},
            "rhr_bpm": {"robust_z": 0.9, "percentile_rank": 0.86, "slope": 0.3},
        }
    },
    "acceleration_proxy_7": {},
}
DQ = {"display_label": "medium", "ruleset_version": "nhi-0.2.0-mvp1"}


def _plan():
    return AB.build_daily_plan_artifact(
        "2026-09-01", NOW, VECTOR, DQ, "nhi-0.2.0-mvp1", ["whoop_cycles:1"])


def test_plan_is_drive_permitted():
    plan = _plan()
    AB.assert_drive_permitted("cloud_private", plan,
                              AB.canonical_json(plan).decode("utf-8"))


def test_plan_delta_is_exact_arithmetic():
    plan = _plan()
    d = plan["metrics_vs_personal_baseline"]["recovery_score"]
    assert d["today"] == 31.0
    assert d["baseline_center"] == 50.0
    assert d["delta_vs_baseline"] == -19.0


def test_plan_copies_engine_stats_without_recomputing():
    plan = _plan()
    d = plan["metrics_vs_personal_baseline"]["rhr_bpm"]
    assert d["robust_z"] == 0.9
    assert d["percentile_rank_7d"] == 0.86
    assert d["slope_7d"] == 0.3


def test_plan_missing_metric_stays_missing():
    vec = json.loads(json.dumps(VECTOR))
    vec["today"]["spo2_pct"] = None
    plan = AB.build_daily_plan_artifact("2026-09-01", NOW, vec, DQ, "m", [])
    d = plan["metrics_vs_personal_baseline"]["spo2_pct"]
    assert d["today"] is None
    assert d["delta_vs_baseline"] is None
    assert d["status"] == "insufficient_data"


def test_plan_metric_without_baseline_has_no_delta():
    plan = _plan()
    d = plan["metrics_vs_personal_baseline"]["sleep_total_hrs"]
    assert d["baseline_center"] is None
    assert d["delta_vs_baseline"] is None


def test_plan_band_is_insufficient_data_when_recovery_absent():
    vec = json.loads(json.dumps(VECTOR))
    vec["today"]["recovery_score"] = None
    plan = AB.build_daily_plan_artifact("2026-09-01", NOW, vec, DQ, "m", [])
    assert plan["readiness"]["band"] == "insufficient_data"


def test_plan_calendar_is_never_pre_approved():
    plan = _plan()
    assert plan["calendar"]["write_status"] == "not_written"
    assert plan["calendar"]["approved_by_human"] is False
    assert plan["calendar"]["proposals"] == []
    assert plan["calendar"]["reason"] == "human_approval_required"


def test_plan_declares_no_llm_contribution():
    plan = _plan()
    assert plan["llm_contribution"] == "none"
    assert plan["generated_by"] == "deterministic_engine"
    assert plan["narrative"] is None


def test_plan_uses_personal_not_population_baselines():
    plan = _plan()
    assert plan["population_norms_used"] is False
    assert plan["baseline_kind"] == "personal_trailing_median"
    assert "your own recent baseline" in plan["interpretation_frame"]


def test_plan_carries_advisory_disclaimer():
    assert "not medical diagnosis" in _plan()["advisory_disclaimer"]


def test_plan_provenance_envelope_is_complete():
    plan = _plan()
    for key in ("artifact_id", "artifact_kind", "schema_version", "contract",
                "source_system", "created_at", "updated_at", "effective_period",
                "storage_class", "canonical_authority", "canonical_pointer",
                "sensitivity", "upstream_evidence_refs", "methods_version",
                "timezone"):
        assert key in plan, f"missing provenance field {key}"
    assert plan["storage_class"] == "cloud_private"
    assert plan["canonical_authority"] == "vps"
    assert plan["timezone"] == "Africa/Cairo"
    assert plan["effective_period"] == {"from": "2026-09-01", "to": "2026-09-01"}


def test_plan_is_byte_identical_for_identical_input():
    assert AB.canonical_json(_plan()) == AB.canonical_json(_plan())


# ── Rolling artifact ────────────────────────────────────────────────────────
def test_rolling_artifact_preserves_windows_verbatim():
    art = AB.build_rolling_artifact("2026-09-01", NOW, VECTOR, DQ, "m", [])
    assert art["windows"] == VECTOR["windows"]
    assert art["baselines"] == VECTOR["baselines"]
    assert art["windows_days"] == [3, 7, 14, 30, 90]


def test_rolling_artifact_is_drive_permitted():
    art = AB.build_rolling_artifact("2026-09-01", NOW, VECTOR, DQ, "m", [])
    AB.assert_drive_permitted("cloud_private", art,
                              AB.canonical_json(art).decode("utf-8"))


# ── Tamper tests: a poisoned vector must not reach Drive ───────────────────
def test_tampered_vector_carrying_a_token_is_blocked():
    vec = json.loads(json.dumps(VECTOR))
    vec["today"]["note"] = "leaked ghp_" + "E" * 36
    plan = AB.build_daily_plan_artifact("2026-09-01", NOW, vec, DQ, "m", [])
    with pytest.raises(AB.ClassificationError):
        AB.assert_drive_permitted("cloud_private", plan,
                                  AB.canonical_json(plan).decode("utf-8"))


def test_tampered_vector_carrying_a_credential_key_is_blocked():
    """Poison on a path the builder DOES copy must be caught by the gate."""
    vec = json.loads(json.dumps(VECTOR))
    vec["baselines"]["refresh_token"] = "x" * 40
    art = AB.build_rolling_artifact("2026-09-01", NOW, vec, DQ, "m", [])
    assert "refresh_token" in json.dumps(art), "test premise: poison must propagate"
    with pytest.raises(AB.ClassificationError):
        AB.assert_drive_permitted("cloud_private", art,
                                  AB.canonical_json(art).decode("utf-8"))


def test_builder_copies_only_allow_listed_paths():
    """Defence in depth: an unexpected top-level vector key is dropped, not carried.

    The builders name every field they emit, so a poisoned or malformed upstream
    vector cannot smuggle an extra key into a Drive artifact even before the
    classification gate runs.
    """
    vec = json.loads(json.dumps(VECTOR))
    vec["refresh_token"] = "x" * 40
    vec["unexpected_upstream_field"] = {"anything": 1}
    art = AB.build_rolling_artifact("2026-09-01", NOW, vec, DQ, "m", [])
    blob = json.dumps(art)
    assert "refresh_token" not in blob
    assert "unexpected_upstream_field" not in blob
    # The legitimate content still came through.
    assert art["baselines"] == VECTOR["baselines"]

    plan = AB.build_daily_plan_artifact("2026-09-01", NOW, vec, DQ, "m", [])
    plan_blob = json.dumps(plan)
    assert "refresh_token" not in plan_blob
    assert "unexpected_upstream_field" not in plan_blob


def test_downgrading_storage_class_does_not_bypass_the_scan():
    payload = {"notes": "ghp_" + "E" * 36}
    for cls in sorted(P.DRIVE_ALLOWED_CLASSES):
        with pytest.raises(AB.ClassificationError):
            AB.assert_drive_permitted(cls, payload, json.dumps(payload))
