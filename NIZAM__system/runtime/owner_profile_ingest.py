#!/usr/bin/env python3
"""NIZAM owner-profile ingestion (one-shot, idempotent).

Parses the confirmed owner-context items and writes one LEARNING_LEDGER row each,
tagged by owning pillar + tier + provenance. Reuses the DEPLOYED nizam-governor
primitives (same _scrub, _sha16 dedupe, _encrypt_atrest Fernet key, row schema) so
ingested rows are byte-compatible with live captures.

Tiers: ordinary -> plaintext, mirrored to Drive.
       strict_local_maximum (AHEL) -> ahel:true, text_enc (Fernet), VPS-ledger ONLY (never mirrored).
Idempotent: dedupe_key = sha16("owner_profile_ingest|<pillar>|<text>"); re-runs skip seen rows.
"""
import os
import sys
import json
import subprocess
from importlib.machinery import SourceFileLoader

GOV_PATH = "/home/nizam/.hermes/plugins/nizam-governor/__init__.py"
gov = SourceFileLoader("nizam_governor_live", GOV_PATH).load_module()

REC = "non_canonical_session_reconstruction"   # from the (non-canonical) profile export
SELF = "owner_self_assessment"                 # owner-stated, NOT from the export doc

# (pillar, tier, ahel, provenance, text, extra)
ORD = "ordinary"
SLM = "strict_local_maximum"
ITEMS = [
    # ---------------- TAFRIGH / Amin (identity, style, values, background) — 17
    ("tafrigh", ORD, False, REC, "26-year-old Egyptian, based in Cairo (Africa/Cairo, EET timezone).", {}),
    ("tafrigh", ORD, False, REC, "Role: Brand Specialist — GCC at Amazon Vendor Services (AVS).", {}),
    ("tafrigh", ORD, False, REC, "Education: B.A. Communication & Media Arts, AUC (2022); Business Administration studies, Paris (2017).", {}),
    ("tafrigh", ORD, False, REC, "Muslim, Sunni.", {}),
    ("tafrigh", ORD, False, REC, "Bilingual; code-switches fluently between Arabic and English.", {}),
    ("tafrigh", ORD, False, REC, "Communication style: direct, logic-based, no fluff; begins with factual content.", {}),
    ("tafrigh", ORD, False, REC, "Format preference: lists over paragraphs for multi-point answers; section headers for complex ones.", {}),
    ("tafrigh", ORD, False, REC, "Default working mode: builds layered personal operating systems.", {}),
    ("tafrigh", ORD, False, REC, "Stated productivity order: 'recovery first, then output.'", {}),
    ("tafrigh", ORD, False, REC, "Uses AI tooling as primary professional leverage.", {}),
    ("tafrigh", ORD, False, REC, "Values: faith, family, and personal optimization rated high-importance.", {}),
    ("tafrigh", ORD, False, REC, "Values: peace and calm in relationships described as deeply important.", {}),
    ("tafrigh", ORD, False, REC, "Values: ethics and integrity alongside ambition.", {}),
    ("tafrigh", ORD, False, REC, "Values: recognition that reflects actual impact created.", {}),
    ("tafrigh", ORD, False, REC, "Values: precision, structure, and improvement through data and reflection.", {}),
    ("tafrigh", ORD, False, REC, "Self-described pattern: fatigue with a sustained 'warrior-mode' identity carried across all life domains (his framing, not a diagnosis).", {}),
    ("tafrigh", ORD, False, REC, "Career background: before Amazon, an 18-month accelerated management program at Philip Morris International (Customer Care, Field Channel Strategy, Omnichannel); felt contributions were undervalued relative to grade placement.", {}),

    # ---------------- SHURA / Salman (projects, strategic approach, aspirations, SESHAT arch) — 13
    ("shura", ORD, False, REC, "Project — SESHAT multi-agent AI platform (active): Pharaonic-themed, AKI-based AVS analytics; deity-agent calibration, deal-cost intelligence, infrastructure build-out under KHEPRI.", {}),
    ("shura", ORD, False, REC, "Project — FORGE prompt-engineering system (active): iterated v4.0->v7.1 sovereign architecture; JSON prompt generation, eval harness, continuity bridges; shift toward creative intelligence over rule density.", {}),
    ("shura", ORD, False, REC, "Project — NIZAM personal OS (in progress): PARA framework, Notion, 7-database model; conversational hub -> routing -> learning loop; framework-complete, content population ongoing.", {}),
    ("shura", ORD, False, REC, "Project — ARES Football Intelligence Engine (active): 18 dimensions, 42 clubs.", {}),
    ("shura", ORD, False, REC, "Project — AVS deal-cost intelligence engine (active): NetPPM% headroom, dual vendor confirmation, per-ASIN push recommendations.", {}),
    ("shura", ORD, False, REC, "Project — AI model benchmark research (in progress): frontier-model comparisons (MiniMax, Kimi, GLM, DeepSeek, Qwen).", {}),
    ("shura", ORD, False, REC, "Project — Amazon LP coaching system for Abdulrahman Moussa (paused): multi-round story-library + PDF coaching.", {}),
    ("shura", ORD, False, REC, "Project — n8n news intelligence workflow (in progress): 4-hour news + sentiment + market-impact pipeline.", {}),
    ("shura", ORD, False, REC, "Project — SESHAT Living Office visualization (planned): browser-based Pharaonic pixel-art agent visualization (Phaser).", {}),
    ("shura", ORD, False, REC, "Working approach to projects: inspect-first, verify-before-build; weights strategic direction and QC over raw execution.", {}),
    ("shura", ORD, False, REC, "Aspirations: GCC / Middle East roles; longer-term relocation or European nationality; interest in a master's in data science (University of Minnesota).", {}),
    ("shura", ORD, False, REC, "FIREWALL NOTE — the SESHAT deity-council agents are part of the SESHAT/AVS work system, NOT NIZAM's personas. Roster: KHEPRI (orchestration/router), THOTH (knowledge), SESHAT (records/analytics), PTAH (design/architecture), OSIRIS/RA/SEKHMET (council, under calibration), BES (connector), NEPHTHYS (project/research), KHONSU (mapped).", {}),
    ("shura", ORD, False, REC, "SESHAT council expansion plan (SESHAT system, not NIZAM): toward ~14 agents / 60+ skills (3-5 per deity, mutually exclusive); CallOutHub inter-agent bus; 7 profiles flagged for reconstruction due to manifest.json null-field errors.", {}),

    # ---------------- NAQD / Hazim (obstacles, blind-spots, failure patterns) — 10 (8 REC + 2 SELF)
    ("naqd", ORD, False, REC, "Self-identified pattern: recurrently ends up 'the accused' despite believing he did nothing wrong (his framing — blame absorption, not a diagnosis).", {}),
    ("naqd", ORD, False, REC, "Self-identified friction: analysis paralysis / perfectionism.", {}),
    ("naqd", ORD, False, REC, "Recurring obstacle: NIZAM content-empty despite a complete framework (SOUL.md unfilled, ledgers untouched at last inspection).", {}),
    ("naqd", ORD, False, REC, "Recurring obstacle: remote GitHub repo lagging local state by several versions.", {}),
    ("naqd", ORD, False, REC, "Recurring obstacle: manifest.json null-field errors breaking 7 deity profiles.", {}),
    ("naqd", ORD, False, REC, "Recurring obstacle (now resolved): dual-schedule strain from running a secondary role (RPM) alongside Amazon — see MUNAWARA for the exit.", {}),
    ("naqd", ORD, False, REC, "Recurring obstacle: tooling sprawl / complexity-ceiling signal across parallel agentic systems.", {}),
    ("naqd", ORD, False, REC, "Stated tension: between high-performance ambition and a need for calm (self-stated).", {}),
    ("naqd", ORD, False, SELF, "Self-assessment (owner-stated, not from the profile doc): a pattern of overriding his own correct instincts.", {}),
    ("naqd", ORD, False, SELF, "Self-assessment (owner-stated, not from the profile doc): a pattern of accepting the bare minimum / settling.", {}),

    # ---------------- MUNAWARA / Khalid (current workstreams + commitments) — 4
    ("munawara", ORD, False, REC, "Employer: Amazon Vendor Services; role: Brand Specialist — GCC; manager: Noor Shehata; joined late 2025.", {}),
    ("munawara", ORD, False, REC, "Portfolio: WJ Towell, Al Maya, Champion Foods, McLane, Link Max, Perfetti Van Melle — ~3,000 ASINs on amazon.ae.", {}),
    ("munawara", ORD, False, REC, "Colleagues: Abdul Rafay, Christos Karaisaridis, Nikhil Yadav, Hema J, Sumukh Jeevan.", {}),
    ("munawara", ORD, False, REC, "Exited the RPM secondary part-time role (Q1/Q2 2026) to reduce dual-schedule strain and refocus on Amazon.", {}),

    # ---------------- YAWMIYAT / Sadiq (faith practice, reflection, life-state) — 4
    ("yawmiyat", ORD, False, REC, "Faith practice: «سورة اليوم» daily surah-study system (last completed Surah Al-Falaq #113; 3 surahs complete); investigative tafsir workflow in Egyptian Arabic; dua composition grounded in Qur'an/Sunnah/Salaf; Jumu'ah prayer protected in Friday plans (~20 min).", {}),
    ("yawmiyat", ORD, False, REC, "Faith-career alignment named as a live tension he works with.", {}),
    ("yawmiyat", ORD, False, REC, "In ongoing therapy (~4 years) with structured journaling (DAIR-15).", {}),
    ("yawmiyat", ORD, False, REC, "Current life-state: based in Cairo; drives a 2022 Ford Focus; invests in U.S. and Egyptian markets (Interactive Brokers, Thndr).", {}),

    # ---------------- BADAN / Hayat (objective biometrics only) — 3
    ("badan", ORD, False, REC, "Biometric snapshot (2026-03-05): weight 94.3 kg, body fat 29.7%, BMI 28.7, muscle mass 63.0 kg, BMR 1910 kcal/day, resting HR 85 bpm, visceral fat index 11; height 182 cm (stated, undated).", {"staleness": "~3mo (2026-03-05)"}),
    ("badan", ORD, False, REC, "Stated goal: reach 85 kg with daily cardio (context, not a biometric reading).", {}),
    ("badan", ORD, False, REC, "Substance intake: ~5 espressos/day; nicotine pouches ~20 mg/day (ZYN, KLINT), after quitting smoking.", {}),

    # ---------------- HIKMAH / Khaldun (growth baselines) — 1 (gap marker)
    ("hikmah", ORD, False, REC, "GAP: muhasaba baseline-vs-now growth data was NOT captured in this export; populate from the canonical muhasaba ledger on the VPS.", {"confidence": "gap_not_captured"}),

    # ---------------- AHEL / Ammar (family + relationship) — 6  [ahel:true, encrypted, VPS-only]
    ("ahel", SLM, True, REC, "Relationship — Aya: long-distance partner; met 2019, reconnected 2022 in Cairo; fitness instructor in Saudi Arabia (Al-Sharqeya origin); at last capture (Apr 2026) described as deteriorating; operator's stated position: marriage-track or closure, no indefinite LDR.", {}),
    ("ahel", SLM, True, REC, "Relationship history: prior dating / communication-coaching threads (Zoya, Raneem, Yas) appear as past; current status not captured.", {"confidence": "low_uncertain"}),
    ("ahel", SLM, True, REC, "Family — brother lives in Minnesota, USA.", {}),
    ("ahel", SLM, True, REC, "Family — sister referenced as at MSU (Mankato) in one session; UNCERTAIN, flagged to verify.", {"confidence": "low_uncertain"}),
    ("ahel", SLM, True, REC, "Family — father supported with a Forge/Claude tutorial guide.", {}),
    ("ahel", SLM, True, REC, "Family — family referenced in Minnesota; family well-being a stated dua/priority.", {}),
]


def main():
    ll = gov.LEARNING_LEDGER
    before = sum(1 for _ in open(ll, encoding="utf-8")) if os.path.exists(ll) else 0

    written = {"ordinary": 0, "ahel": 0}
    skipped = 0
    redaction_total = 0
    by_pillar = {}

    for pillar, tier, ahel, prov, text, extra in ITEMS:
        scrubbed, redactions = gov._scrub(text)
        redaction_total += len(redactions)
        key = gov._sha16("owner_profile_ingest|" + pillar + "|" + text)
        if gov._seen(key):
            skipped += 1
            continue
        row = {
            "ts": gov._utc(), "source": "owner_profile_ingest", "session": "owner_profile_ingest",
            "dedupe_key": key, "pillar": pillar, "tier": tier, "ahel": bool(ahel),
            "provenance": prov,
        }
        row.update(extra)
        if redactions:
            row["redacted"] = redactions
        if ahel:
            enc = gov._encrypt_atrest(scrubbed)
            if enc:
                row["text_enc"] = enc
                row["enc"] = "fernet"
            else:
                row["text"] = scrubbed
                row["enc"] = "unavailable"
            written["ahel"] += 1
        else:
            row["text"] = scrubbed
            written["ordinary"] += 1
        gov._append(ll, row)
        gov._mark_seen(key)
        gov._event("owner_profile_ingest", pillar=pillar, tier=tier, ahel=bool(ahel))
        by_pillar[pillar] = by_pillar.get(pillar, 0) + 1

    after = sum(1 for _ in open(ll, encoding="utf-8"))

    # Synchronous AHEL-excluded mirror (bypass throttle) so we can verify byte-advance now.
    try:
        os.remove(gov.MIRROR_STATE)
    except Exception:
        pass
    kept = gov._build_ledger_projection()
    proj_rows = sum(1 for _ in open(gov.MIRROR_PROJECTION, encoding="utf-8")) if os.path.exists(gov.MIRROR_PROJECTION) else -1
    mirror_rc = None
    if os.path.exists(gov.RCLONE) and kept >= 0:
        cp = subprocess.run(
            [gov.RCLONE, "--config", gov.RCLONE_CONF, "copy", gov.MIRROR_PROJECTION, gov.DRIVE_REMOTE + gov.DRIVE_LEDGER_DIR],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180,
        )
        mirror_rc = cp.returncode
        gov._egress_audit("google_drive", "drive_mirror", file="LEARNING_LEDGER.jsonl", ahel_excluded=True, source="owner_profile_ingest")

    # AHEL rows present in ledger but absent from projection?
    ahel_in_ledger = 0
    ahel_in_projection = 0
    for line in open(ll, encoding="utf-8"):
        try:
            if json.loads(line).get("ahel"):
                ahel_in_ledger += 1
        except Exception:
            pass
    if os.path.exists(gov.MIRROR_PROJECTION):
        for line in open(gov.MIRROR_PROJECTION, encoding="utf-8"):
            try:
                if json.loads(line).get("ahel"):
                    ahel_in_projection += 1
            except Exception:
                pass

    print(json.dumps({
        "ledger_rows_before": before,
        "ledger_rows_after": after,
        "newly_written": written,
        "newly_written_total": written["ordinary"] + written["ahel"],
        "skipped_already_seen": skipped,
        "by_pillar": by_pillar,
        "secret_redactions": redaction_total,
        "projection_rows_mirrored": proj_rows,
        "projection_kept_count": kept,
        "mirror_rclone_rc": mirror_rc,
        "ahel_rows_in_ledger": ahel_in_ledger,
        "ahel_rows_in_projection_SHOULD_BE_0": ahel_in_projection,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
