#!/usr/bin/env python3
"""
backfill_migrate.py — safe backfill/reindex migration for pre-existing legacy
YAWMIYAT sessions that predate the persistence architecture.

Rules (amendment 6):
  - Assigns a deterministic, immutable session_id to each legacy session
    (derived from original content sha), NEVER invents transcript content.
  - Historical missing raw transcripts remain EXPLICITLY MISSING: the record's
    links.transcript is set to "MISSING" and no transcript file is fabricated.
  - Rewrites the legacy file into the new sessions/{sid}.json shape, keeps a
    copy of the original raw JSON in _recovery/archive_legacy/ for audit.
  - Builds manifest + index. Does not enrich (enrichment is a separate pass).

Usage:
  python3 backfill_migrate.py            # migrate all legacy sessions
  python3 backfill_migrate.py --dry-run  # report only
"""
import json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yawmiyat as Y
import yawmiyat_index as I

LEGACY_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})Z__([a-z_]+)\.json$")


def _sid_from_legacy(path, session_type):
    raw = open(path).read()
    h = Y.sha256_bytes(raw.encode())[:4]
    m = LEGACY_RE.match(os.path.basename(path))
    if m:
        YY, mo, dd, hh, mi, ss = m.groups()[:6]
        return f"YWM-{YY}{mo}{dd}-{hh}{mi}{ss}-{session_type}-{h}"
    # fallback: derive from captured_at in the record
    try:
        sj = Y.load_json(path)
        ca = (sj.get("captured_at") or "").replace("-", "").replace(".", "").replace("Z", "").replace("T", "")
        if len(ca) >= 14 and ca.isdigit():
            return f"YWM-{ca[:8]}-{ca[8:14]}-{session_type}-{h}"
    except Exception:
        pass
    raise ValueError(f"cannot derive stable session_id from {path}")


def migrate(dry_run=False):
    rep = {"migrated": [], "skipped:has_sid": [], "missing_transcript": [], "errors": []}
    d = os.path.join(Y.JOURNAL_ROOT, "sessions")
    if not os.path.isdir(d):
        return rep
    legacy_archive = os.path.join(Y.JOURNAL_ROOT, "_recovery", "archive_legacy")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(d, fn)
        try:
            rec = Y.load_json(p)
        except Exception as e:
            rep["errors"].append(f"{fn}: {e}")
            continue
        if rec.get("session_id"):
            rep["skipped:has_sid"].append(fn)
            continue
        m = LEGACY_RE.match(fn)
        session_type = (m.group(7) if m else rec.get("session_type", "checkin"))
        sid = _sid_from_legacy(p, session_type)
        # archive original raw JSON for audit
        if not dry_run:
            os.makedirs(legacy_archive, exist_ok=True)
            shutil.copy2(p, os.path.join(legacy_archive, fn))
        rec["session_id"] = sid
        rec.setdefault("links", {})["transcript"] = "MISSING"
        if not dry_run:
            commit = Y.commit_machine_record(sid, session_type, rec, transcript_sha256=None)
            if commit["status"] in ("committed", "noop"):
                # register old names -> canonical sid (G8)
                old_stem = os.path.basename(p)[:-5] if fn.endswith(".json") else os.path.basename(p)
                Y.register_alias(os.path.basename(p), sid, old_path=p)
                Y.register_alias(old_stem, sid, old_path=p)
                # remove legacy original now that one canonical sid record exists
                if os.path.exists(p) and os.path.abspath(p) != os.path.abspath(commit["path"]):
                    os.remove(p)
        rep["migrated"].append({"old": fn, "new_sid": sid})
        rep["missing_transcript"].append(sid)
    return rep


def main():
    dry = "--dry-run" in sys.argv
    Y.ensure_layout()
    rep = migrate(dry_run=dry)
    if not dry and rep.get("migrated"):
        I.build_manifest(force=True)
        I.build_index()
    print(json.dumps(rep, indent=2, default=str))


if __name__ == "__main__":
    main()