#!/usr/bin/env python3
"""
artifact_builder.py — Pure builders for Drive-bound knowledge artifacts.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0 (Drive durable-knowledge plane)
Phase: cloud-first reconciliation

NO network, NO database, NO clock reads beyond an injected `now`. Every function
here is deterministic so the tamper tests can pin exact bytes.

Doctrine enforced here:
  * The deterministic engine is the only source of numbers. This module copies
    values; it never computes health arithmetic and never imputes a missing one.
  * Missing stays missing: `null` / `insufficient_data`, never a filled-in guess.
  * Deny-by-default secret scan runs before any bytes are handed to Drive.
  * Calendar writes are proposal-only. Nothing here can mark one approved.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional

import storage_policy as P

ARTIFACT_SCHEMA_VERSION = "0.2.0"

# ── Secret scanning (spec 06: "secrets copied to Drive -> Critical") ─────────
# Deny-by-default. Patterns target credential SHAPES, so no real secret value is
# ever embedded in this repository.
_SECRET_PATTERNS = [
    ("slack_bot_token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("google_oauth_client_secret", re.compile(r"GOCSPX-[0-9A-Za-z_-]{10,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{30,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("github_token", re.compile(r"gh[pousr]_[0-9A-Za-z]{20,}")),
    ("bearer_header", re.compile(r"(?i)\bbearer\s+[0-9A-Za-z._~+/-]{20,}")),
    ("private_key_block", re.compile(r"-----BEGIN[ A-Z]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}")),
    ("refresh_token_assignment", re.compile(
        r"(?i)\b(refresh_token|client_secret|access_token|api_key|password|passwd)\b"
        r"\s*[:=]\s*[\"']?[0-9A-Za-z._~+/-]{12,}")),
    ("postgres_uri_with_password", re.compile(r"(?i)postgres(?:ql)?://[^:\s]+:[^@\s]+@")),
]

# Keys whose presence is itself disqualifying, regardless of value shape.
_FORBIDDEN_KEYS = frozenset({
    "access_token", "refresh_token", "client_secret", "client_id",
    "api_key", "apikey", "password", "passwd", "secret", "private_key",
    "authorization", "token", "bot_token", "webhook_url", "database_url",
})


def scan_for_secrets(text: str) -> List[Dict[str, Any]]:
    """Return a list of findings. Empty list means the payload is clean.

    Findings never include the matched value, only its label and offset, so a
    log line can prove detection without leaking the thing it detected.
    """
    findings: List[Dict[str, Any]] = []
    for label, pat in _SECRET_PATTERNS:
        for m in pat.finditer(text):
            findings.append({"rule": label, "offset": m.start(),
                             "matched_len": m.end() - m.start()})
    return findings


def find_forbidden_keys(obj: Any, path: str = "$") -> List[str]:
    """Walk a JSON-able structure and report any credential-shaped key path."""
    hits: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{path}.{k}"
            if str(k).strip().lower() in _FORBIDDEN_KEYS:
                hits.append(kp)
            hits.extend(find_forbidden_keys(v, kp))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(find_forbidden_keys(v, f"{path}[{i}]"))
    return hits


class ClassificationError(Exception):
    """Raised when an artifact is not permitted to leave the VPS."""


def assert_drive_permitted(storage_class: str, payload: Any, text: str) -> None:
    """Fail closed before any byte reaches Drive.

    Three independent gates: class allow-list, structural key scan, and a
    value-shape regex scan. Any one of them blocks the write.
    """
    if storage_class in P.DRIVE_FORBIDDEN_CLASSES:
        raise ClassificationError(
            f"storage_class '{storage_class}' is VPS-only and must not reach Drive")
    if storage_class not in P.DRIVE_ALLOWED_CLASSES:
        raise ClassificationError(f"storage_class '{storage_class}' is not on the Drive allow-list")
    keys = find_forbidden_keys(payload)
    if keys:
        raise ClassificationError(f"credential-shaped keys present: {sorted(keys)}")
    findings = scan_for_secrets(text)
    if findings:
        rules = sorted({f["rule"] for f in findings})
        raise ClassificationError(f"secret-shaped values present: {rules}")


# ── Canonical serialization ──────────────────────────────────────────────────
def canonical_json(payload: Any) -> bytes:
    """Stable bytes: sorted keys, LF, trailing newline. Same input, same sha256."""
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── Provenance envelope (spec 08 "required metadata on durable records") ────
def envelope(
    artifact_id: str,
    artifact_kind: str,
    storage_class: str,
    now_iso: str,
    effective_from: Optional[str],
    effective_to: Optional[str],
    canonical_pointer: Dict[str, Any],
    upstream_refs: List[str],
    methods_version: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_kind": artifact_kind,
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "contract": P.CONTRACT,
        "source_system": "nizam-vps/personal-health",
        "created_at": now_iso,
        "updated_at": now_iso,
        "effective_period": {"from": effective_from, "to": effective_to},
        "storage_class": storage_class,
        "canonical_authority": "vps" if storage_class == "cloud_private" else "drive",
        "canonical_pointer": canonical_pointer,
        "sensitivity": "personal_health_private",
        "upstream_evidence_refs": upstream_refs,
        "methods_version": methods_version,
        "timezone": P.TIMEZONE,
        "generated_by": "deterministic_engine",
        "llm_contribution": "none",
    }


# ── Daily plan artifact ─────────────────────────────────────────────────────
_READINESS_BANDS = (
    # (inclusive_low, exclusive_high, label)
    (0.0, 34.0, "low"),
    (34.0, 67.0, "moderate"),
    (67.0, 101.0, "high"),
)


def readiness_band(recovery_score: Optional[float]) -> Optional[str]:
    """WHOOP's own published recovery bands. Returns None when the score is absent.

    This is a lookup, not an inference. A missing recovery score yields None so
    downstream text must say 'insufficient_data' rather than guess a band.
    """
    if recovery_score is None:
        return None
    for lo, hi, label in _READINESS_BANDS:
        if lo <= float(recovery_score) < hi:
            return label
    return None


def build_daily_plan_artifact(
    planning_date: str,
    now_iso: str,
    vector: Dict[str, Any],
    data_quality: Dict[str, Any],
    methods_version: str,
    source_refs: List[str],
) -> Dict[str, Any]:
    """Deterministic daily plan INPUTS. Contains no generated narrative.

    Hermes may later attach narrative and a proposed agenda, but the numbers in
    this artifact come only from the feature engine, and the calendar fields
    stay in a not-written state that no automated step can advance.
    """
    today = vector.get("today") or {}
    baselines = vector.get("baselines") or {}
    windows = vector.get("windows") or {}
    w7 = windows.get("7") or windows.get(7) or {}

    rec = today.get("recovery_score")
    band = readiness_band(rec)

    deltas: Dict[str, Any] = {}
    for metric, value in sorted(today.items()):
        base = baselines.get(metric) or {}
        center = base.get("center")
        stat7 = w7.get(metric) or {}
        deltas[metric] = {
            "today": value,
            "baseline_center": center,
            "baseline_basis_window_days": base.get("basis_window_days"),
            "baseline_n_obs": base.get("n_obs"),
            "delta_vs_baseline": (None if (value is None or center is None)
                                  else round(float(value) - float(center), 6)),
            "robust_z": stat7.get("robust_z"),
            "percentile_rank_7d": stat7.get("percentile_rank"),
            "slope_7d": stat7.get("slope"),
            "status": "ok" if value is not None else "insufficient_data",
        }

    payload = envelope(
        artifact_id=f"daily_health_plan:{planning_date}",
        artifact_kind="daily_health_plan",
        storage_class="cloud_private",
        now_iso=now_iso,
        effective_from=planning_date,
        effective_to=planning_date,
        canonical_pointer={
            "authority": "vps",
            "table": "daily_feature_vectors",
            "key": {"planning_date": planning_date},
        },
        upstream_refs=list(source_refs),
        methods_version=methods_version,
    )
    payload.update({
        "planning_date": planning_date,
        "readiness": {
            "recovery_score": rec,
            "band": band if band is not None else "insufficient_data",
            "band_source": "whoop_published_recovery_bands",
        },
        "metrics_vs_personal_baseline": deltas,
        "baseline_kind": "personal_trailing_median",
        "population_norms_used": False,
        "data_quality": data_quality,
        "interventions_proposed": [],
        "calendar": {
            "write_status": "not_written",
            "reason": "human_approval_required",
            "approved_by_human": False,
            "proposals": [],
        },
        "narrative": None,
        "narrative_status": "not_generated_this_run",
        "advisory_disclaimer": (
            "Advisory only \u2014 not medical diagnosis. "
            "Red flags route to qualified professionals."
        ),
        "interpretation_frame": "unusual versus your own recent baseline, not versus a population",
    })
    return payload


def build_rolling_artifact(
    planning_date: str,
    now_iso: str,
    vector: Dict[str, Any],
    data_quality: Dict[str, Any],
    methods_version: str,
    source_refs: List[str],
) -> Dict[str, Any]:
    """Longitudinal rolling-window record. Straight copy of engine output."""
    payload = envelope(
        artifact_id=f"rolling_windows:{planning_date}",
        artifact_kind="rolling_window_summary",
        storage_class="cloud_private",
        now_iso=now_iso,
        effective_from=planning_date,
        effective_to=planning_date,
        canonical_pointer={
            "authority": "vps",
            "table": "daily_feature_vectors",
            "key": {"planning_date": planning_date},
        },
        upstream_refs=list(source_refs),
        methods_version=methods_version,
    )
    payload.update({
        "planning_date": planning_date,
        "windows_days": [3, 7, 14, 30, 90],
        "windows": vector.get("windows") or {},
        "baselines": vector.get("baselines") or {},
        "acceleration_proxy_7": vector.get("acceleration_proxy_7") or {},
        "data_quality": data_quality,
        "baseline_kind": "personal_trailing_median",
        "population_norms_used": False,
    })
    return payload
