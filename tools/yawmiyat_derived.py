#!/usr/bin/env python3
"""
yawmiyat_derived.py — enrichment, versioned evaluation/analysis, retrieval
indexes, and Drive reconciliation for YAWMIYAT.

Single authoritative Assessment lives in the canonical session JSON
(sessions/{sid}.json#assessment). The analysis artifact never duplicates it —
it carries versioned enrichment (biometrics), evaluation, and analysis, and
REFERENCES the session's assessment by link.

Never invent missing biometric values. Missing stays null.
"""
import datetime, json, os, re
import yawmiyat as Y

DAILY_HEALTH_DIR = "/opt/personal-health/data"
DRIVE_PRIVATE_DRIVE = "private-NIZAM-Drive"  # label only; folder id injected at run

# ----------------------------------------------------------------- enrichment
def _pick_biometrics(daily):
    """Deterministic extraction from the WHOOP daily snapshot. Missing -> None,
    never invented, never trend-estimated."""
    out = {}
    r = daily.get("recovery") or {}
    if isinstance(r, dict):
        s = r.get("score") if isinstance(r.get("score"), dict) else {}
        rec = r.get("recovery_score")
        if rec is None and isinstance(r.get("score"), dict):
            rec = s.get("recovery_score") or s.get("score")
        out["recovery_score"] = rec if rec is not None else None
        out["hrv_rmssd_milli"] = (s or r).get("hrv_rmssd_milli") or r.get("hrv_rmssd_milli")
        out["rhr"] = s.get("rhr") or r.get("rhr")
    sl = daily.get("sleep")
    if isinstance(sl, dict):
        out["total_sleep_hrs"] = sl.get("total_hrs") or sl.get("total_in_bed_hrs")
        out["deep_hrs"] = sl.get("deep_hrs") or sl.get("deep_sleep_hrs")
        out["rem_hrs"] = sl.get("rem_hrs") or sl.get("rem_sleep_hrs")
        out["sleep_performance_pct"] = sl.get("sleep_performance_pct")
    cy = daily.get("cycle")
    if isinstance(cy, dict):
        out["strain"] = cy.get("strain") or cy.get("day_strain")
    return {k: (v if v is not None else None) for k, v in out.items() if k in
            {"recovery_score","hrv_rmssd_milli","rhr","total_sleep_hrs","deep_hrs","rem_hrs","sleep_performance_pct","strain"}}

def enrich_session(sid, daily, prior_versions=None):
    """
    Produce a NEW versioned analysis artifact for sid, merging available WHOOP
    biometrics (with provenance) + deterministic evaluation, and edit-less
    (does not touch the transcript or the canonical session).
    Returns the analysis dict (caller persists it), version bumped.
    """
    Y._ensure_sid_valid(sid)
    session_path = os.path.join(Y.JOURNAL_ROOT, "sessions", f"{sid}.json")
    if not os.path.exists(session_path):
        raise FileNotFoundError(f"no canonical session {sid}; cannot enrich")
    session = Y.load_json(session_path)
    transcript_sha = (session.get("source") or {}).get("transcript_sha256")
    tp = os.path.join(Y.JOURNAL_ROOT, "transcripts", f"{sid}.txt")
    if not transcript_sha and os.path.exists(tp):
        transcript_sha = Y.sha256_of(tp)
    transcript_sha = transcript_sha or "MISSING"  # never "invent" a transcript
    # resolve existing analysis versions for supersede chain
    existing = sorted(Y._glob_versions(sid))
    version = (existing[-1] + 1) if existing else 1
    bios = _format_biometric(daily)
    eval_note = _deterministic_eval(session, bios, daily)
    analysis = {
        "session_id": sid,
        "analysis_version": version,
        "kind": "analysis",
        "generated_at": Y._now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_provenance": {"engine": "yawmiyat_derived", "enrichment_source": "WHOOP-daily-snapshot"},
        "assessment_ref": {"artifact": f"sessions/{sid}.json", "field": "assessment"},
        "source": {
            "transcript_sha256": transcript_sha,
        },
        "supersedes": existing[-1] if existing else None,
        "enrichment": {
            "biometrics": bios,
            "measured_at": daily.get("exported_at") or daily.get("export_date"),
            "source": daily.get("source"),
        },
        "evaluation": eval_note,
        "analysis": {
            "open_questions": [],
            "recurrent_pattern_hits": _pattern_hits(session),
        },
    }
    return analysis

def _format_biometric(daily):
    r = daily.get("recovery") or {}
    sl = daily.get("sleep") or {}
    cy = daily.get("cycle") or {}
    if not isinstance(r, dict):
        r = {}
    if not isinstance(sl, dict):
        sl = {}
    if not isinstance(cy, dict):
        cy = {}
    def pick(d, *keys):
        for k in keys:
            if d.get(k) is not None:
                return d[k]
        return None
    return {
        "recovery_score": pick(r, "score", "recovery_score", "score_value"),
        "hrv_rmssd_milli": pick(r, "hrv_rmssd_ms", "hrv_rmssd_milli"),
        "rhr": pick(r, "rhr_bpm", "rhr"),
        "total_sleep_hrs": pick(sl, "total_hrs", "total_in_bed_hrs"),
        "deep_hrs": pick(sl, "deep_hrs", "deep_sleep_hrs"),
        "rem_hrs": pick(sl, "rem_hrs", "rem_sleep_hrs"),
        "sleep_performance_pct": pick(sl, "sleep_performance_pct"),
        "strain": pick(cy, "strain", "day_strain"),
    }

def _num(d, *keys):
    for k in keys:
        if d.get(k) is not None:
            return d[k]
    return None

def _deterministic_eval(session, bios, daily):
    fs = session.get("felt_state", {})
    energy = fs.get("energy")
    notes = []
    if energy is not None and bios.get("recovery_score") is not None:
        r = bios["recovery_score"]
        # felt vs biometric: rough directional proxy, NOT a diagnosis
        if (energy >= 4 and r >= 67) or (energy <= 2 and r <= 33):
            notes.append("felt-energy:energy and WHOOP recovery agree directionally")
        elif r >= 67 and energy and energy <= 2:
            notes.append("felt-energy lower than green recovery would imply (fatigue/focus factor)")
        elif r <= 33 and energy and energy >= 4:
            notes.append("felt-energy higher than red recovery (adrenaline/numbed-energy proxy)")
    return {"notes": notes, "biometric_available": bool(bios.get("recovery_score"))}

def _pattern_hits(session):
    hits = []
    txt = " "
    txt_lc = (session.get("assessment", {}).get("pattern") or "").lower()
    for kw in ["loop", "again", "third", "recur", "same", "control", "trigger"]:
        if kw in txt_lc:
            hits.append(kw)
    return hits