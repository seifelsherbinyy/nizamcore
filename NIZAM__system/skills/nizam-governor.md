---
name: nizam-governor
module: NIZAM
trigger: "/nizam-governor-mirror | /nizam-governor-push"
config: NIZAM__system/policies/DUAL_WRITE_GOVERNOR.json
doc: NIZAM__system/docs/DUAL_WRITE_GOVERNOR.md
record_schema: NIZAM__system/schemas/governor_runtime_record.schema.json
mirror_script: HIFZ__github_version_control/scripts/nizam_drive_mirror.py
dual_write_script: HIFZ__github_version_control/scripts/nizam_dual_write.py
preflight_script: HIFZ__github_version_control/scripts/notion_preflight.py
gates: [HIMAYAH, THABAT]
privacy: review_before_commit
---

## For future Claude

Write-path governor: mirror nizamcore → Google Drive; dual-write runtime records → Notion + Drive `Records/`. Full system prompt in `doc`. **Last output must be fenced write-receipt JSON only.**

---

## `/nizam-governor-mirror` (Stage 0)

1. Confirm `GOOGLE_APPLICATION_CREDENTIALS` (or report dry-run only).
2. Run mirror script:
   - Dry-run: `python HIFZ__github_version_control/scripts/nizam_drive_mirror.py --dry-run`
   - Apply: `python .../nizam_drive_mirror.py --apply --confirm-overwrite`
3. If receipt `status` is `NEEDS_CONFIRMATION`, ask operator to re-run with `--confirm-overwrite`.
4. Emit script receipt as **final** message (nothing after fenced JSON).

**Rules:** Repo wins on conflict. Never delete repo-backed Drive items without confirmation. Off-repo root clutter → `_Archive/`. Preserve `Records/`, `Projects/`, `Meetings/`, `Reviews/`.

---

## `/nizam-governor-push` (runtime dual-write)

**Input:** normalized payload (from conversational skill or stdin JSON):

```json
{
  "session_type": "checkin",
  "captured_at": "2026-05-21T12:00:00Z",
  "slug": "morning-checkin",
  "notion_title": "Recovery Check-In (2026-05-21)",
  "notion_payload": {},
  "drive_narrative": "Human-readable narrative...",
  "operator_confirmed_externalize": true,
  "privacy_classification": "strict_local",
  "repo_commit": null,
  "source_artifact": "YAWMIYAT__journaling/sessions/..."
}
```

### Procedure (strict order — spec §6)

1. **HIMAYAH:** Load `PRIVACY_CLASSIFICATION.json`. If source is `strict_local` or `strict_local_maximum`, require `operator_confirmed_externalize: true` or **refuse** (receipt `FAILED`, `failed_stage: himayah_gate`).
2. **Normalize:** `dedupe_key` = `{Lane}:{Type}:{YYYY-MM-DD}:{slug}`; map `session_type` → Type; default Lane from config.
3. **Stage human-only fields** (habit completion, Decision Made?, calendar approval) — never write to Notion; list in `human_only_fields_staged`.
4. **CHECK Notion** for `dedupe_key` on primary DB (Witness or Pulse per routing).
5. **CHECK Drive** path under `Records/...` (see config `drive_runtime_paths`).
6. **WRITE Notion** — decimals for %; ISO dates; capture `page_id`.
7. **WRITE Drive** `.docx` with header: `notion_page_id`, `dedupe_key`, `captured_at`, `repo_commit`.
8. **PATCH** Notion `DriveLink` with Drive URL.
9. **Audit Log** row (`event_type`, `time`, `entity_id`, `payload_hash`, `outcome`).
10. On any failure after partial write: receipt `FAILED` + `failed_stage`; do not claim OK.

**CLI:** `python HIFZ__github_version_control/scripts/nizam_dual_write.py -i payload.json`  
**Dry-run:** add `--dry-run`

**Notion MCP:** If using MCP instead of CLI, follow the same order; on approval-prompt failure, retry without mutating payload.

**Pulse:** Stimulant Load = **prior day** only. Schema version `1.0.0`. Witness `v1`.

### Pre-flight

`python HIFZ__github_version_control/scripts/notion_preflight.py` — confirm `dedupe_key`, `DriveLink`, `captured_at` exist on Pulse, Witness, Audit Log.

---

## Write-receipt (always last)

```json
{
  "status": "OK|FAILED|NEEDS_CONFIRMATION",
  "mode": "CREATE|UPDATE",
  "scope": "repo_mirror|runtime_record",
  "dedupe_key": "...|null",
  "notion": { "db": "name", "data_source_id": "...|null", "page_id": "...|null" },
  "drive": { "folder": "...", "filename": "...", "url": "...|null" },
  "drivelink_written_back": true,
  "audit_logged": true,
  "human_only_fields_staged": [],
  "failed_stage": "null|step name",
  "notes": "one line"
}
```
