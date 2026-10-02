#!/usr/bin/env python3
"""Sync MAL/Zayd's PFA projection from PFOS's finance.db (the "sync, not estimate" routine, v2).

Companion to scripts/export/export-pfa-snapshot.ts in PFOS__personal_finance_app. This script is
the second half described in MAL__financial_engine/pfa/README.md's "Update Routine (v2)" Step 1-2,
and in NIZAM__system/docs/ADR-ZAYD-001-pfos-engine-into-mal-zayd.md:

  1. Run the TS export script as a subprocess (it is the only thing that opens finance.db; this
     script never touches SQLite itself, so there is exactly one place that knows the schema).
  2. Lightly validate the JSON it printed against pfa_canonical_state.schema.json's shape.
  3. Diff each debt in the new snapshot against the previous canonical_state.json (if any) and
     append any changed fact to ledgers/debts.jsonl / ledgers/payments.jsonl, each entry's
     idempotency_key = sha256(ts+debt_id+event_type) where ts is the PFOS row's OWN updatedAt
     (export-pfa-snapshot.ts's pfos_updated_at field) \u2014 not this run's wall-clock time \u2014 so a
     resync that finds no PFOS-side change recomputes the identical key and is skipped, never
     appended twice. The ledger file is scanned for an existing line with that key before any
     append (check-before-write idempotency, not merely diff-based).
  4. Overwrite canonical_state.json with the new snapshot last, only after the ledger appends
     succeeded, so a crash mid-sync leaves the ledger ahead of canonical_state.json rather than
     the reverse \u2014 the next run's diff still has the true previous state to compare against and
     will not lose an event. (Known gap, stated plainly: this is not a single atomic transaction
     across two files; see "Known limitations" below.)

Nothing in this script estimates, guesses, or asks the user for a figure. If the export script
produced no data for a field, this script carries the null/0 placeholder through unchanged and
leaves the exporter's provenance.open_items as the record of what is still outstanding.

Config is explicit CLI flags, matching this repository's "nothing ambient" convention:

  python3 sync_from_pfos.py \
    --pfos-dir <path to PFOS__personal_finance_app> \
    --pfa-dir  <path to MAL__financial_engine/pfa> \
    --data-dir <abs path PFOS finance.db lives in> \
    --file-name <finance.db file name> \
    [--store-name <name>] [--as-of YYYY-MM-DD] [--node-bin node] [--dry-run]

Exit codes: 0 success (including "nothing changed"), 1 on any failure (export script failed,
JSON unparseable, required field missing, ledger append failed, canonical_state.json write
failed). A failure prints a diagnosis to stderr and writes nothing partial \u2014 either the full set
of ledger appends for this run succeeded or none of canonical_state.json's new content is kept.

Known limitations (stated, not hidden):
  - Append-then-overwrite is two separate filesystem writes, not one transaction. A crash between
    them is possible; the ordering is chosen so that failure mode loses nothing (next run just
    re-detects the same diff), rather than silently dropping a ledger entry.
  - Validation here is manual required-field/pattern checks against the real schema files, not a
    full JSON Schema validator \u2014 the `jsonschema` PyPI package's availability on the target
    machine was not confirmed when this was written. If it is available, swap `_validate_manual`
    for a real `jsonschema.validate` call; the manual checks were written directly from the
    schema's `required` and `pattern` fields, not guessed.
  - debt_architecture.summary and cash_flow roll-ups are passed through from the exporter
    verbatim; this script does not recompute or sanity-check them, matching MAL/Zayd's rule that
    it does not compute money figures of its own.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEBT_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
DEBT_TYPES = {"credit_card", "bnpl_recycling", "bnpl_installment", "family_loan", "personal_loan", "other"}
DEBT_STATUSES = {"active", "paid_off", "restructured", "deferred"}

REQUIRED_SNAPSHOT_FIELDS = (
    "snapshot_date",
    "currency",
    "exchange_rate",
    "income",
    "debt_architecture",
    "cash_flow",
    "provenance",
    "source_of_truth",
)
REQUIRED_DEBT_ENTRY_FIELDS = ("id", "name", "type", "recycling_eligible")


class SyncError(RuntimeError):
    """Raised for any condition that must stop the sync with exit 1 and no partial write."""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync MAL/Zayd's PFA canonical_state.json and ledgers from PFOS's finance.db."
    )
    parser.add_argument("--pfos-dir", required=True, help="Path to PFOS__personal_finance_app")
    parser.add_argument("--pfa-dir", required=True, help="Path to MAL__financial_engine/pfa")
    parser.add_argument("--data-dir", required=True, help="Absolute path PFOS's finance.db lives in")
    parser.add_argument("--file-name", required=True, help="finance.db file name")
    parser.add_argument("--store-name", default="finance-agent")
    parser.add_argument("--as-of", default=None, help="YYYY-MM-DD; defaults to today UTC in the exporter")
    parser.add_argument("--node-bin", default="node", help="Node executable to run the TS exporter with")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the export and print what would change; write nothing to canonical_state.json or the ledgers.",
    )
    return parser.parse_args(argv)


def run_exporter(args: argparse.Namespace) -> dict[str, Any]:
    """Run export-pfa-snapshot.ts as a subprocess and parse its stdout. Never touches SQLite itself."""
    script = Path(args.pfos_dir) / "scripts" / "export" / "export-pfa-snapshot.ts"
    if not script.is_file():
        raise SyncError(f"exporter not found at {script}")

    cmd = [
        args.node_bin,
        str(script),
        "--data-dir",
        args.data_dir,
        "--file-name",
        args.file_name,
        "--store-name",
        args.store_name,
    ]
    if args.as_of:
        cmd += ["--as-of", args.as_of]

    completed = subprocess.run(
        cmd,
        cwd=args.pfos_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SyncError(
            f"exporter exited {completed.returncode}\nstderr:\n{completed.stderr}\nstdout:\n{completed.stdout}"
        )
    try:
        snapshot = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SyncError(f"exporter stdout was not valid JSON: {exc}\nstdout was:\n{completed.stdout}") from exc
    if completed.stderr.strip():
        print(f"[sync_from_pfos] exporter stderr (non-fatal):\n{completed.stderr}", file=sys.stderr)
    return snapshot


def _validate_manual(snapshot: dict[str, Any]) -> list[str]:
    """Required-field and pattern checks lifted directly from the schema files' own `required`/
    `pattern` keys (NIZAM__system/schemas/pfa_canonical_state.schema.json). Not a full JSON Schema
    validator \u2014 see the "Known limitations" note at the top of this file.
    """
    problems: list[str] = []

    for field in REQUIRED_SNAPSHOT_FIELDS:
        if field not in snapshot:
            problems.append(f"missing required top-level field: {field}")

    source_of_truth = snapshot.get("source_of_truth", {})
    for field in ("engine", "storeRef", "projectedAt"):
        if field not in source_of_truth:
            problems.append(f"missing required source_of_truth.{field}")
    if source_of_truth.get("engine") != "PFOS":
        problems.append(f"source_of_truth.engine must be the literal \"PFOS\", got {source_of_truth.get('engine')!r}")

    income = snapshot.get("income", {})
    if "stable_net_monthly_milliunits" not in income:
        problems.append("missing required income.stable_net_monthly_milliunits")
    elif not isinstance(income["stable_net_monthly_milliunits"], int):
        problems.append("income.stable_net_monthly_milliunits must be an integer (schema has no null in its type)")

    debt_architecture = snapshot.get("debt_architecture", {})
    debts = debt_architecture.get("debts")
    if debts is None:
        problems.append("missing required debt_architecture.debts")
    else:
        for i, debt in enumerate(debts):
            for field in REQUIRED_DEBT_ENTRY_FIELDS:
                if field not in debt:
                    problems.append(f"debts[{i}] missing required field: {field}")
            debt_id = debt.get("id", "")
            if debt_id and not DEBT_ID_PATTERN.match(debt_id):
                problems.append(f"debts[{i}].id {debt_id!r} does not match ^[a-z0-9_]+$")
            if debt.get("type") not in DEBT_TYPES and "type" in debt:
                problems.append(f"debts[{i}].type {debt.get('type')!r} is not one of {sorted(DEBT_TYPES)}")
            if debt.get("status") not in DEBT_STATUSES and "status" in debt:
                problems.append(f"debts[{i}].status {debt.get('status')!r} is not one of {sorted(DEBT_STATUSES)}")

    provenance = snapshot.get("provenance", {})
    for field in ("last_updated", "update_method"):
        if field not in provenance:
            problems.append(f"missing required provenance.{field}")

    return problems


def load_previous_state(pfa_dir: Path) -> dict[str, Any] | None:
    path = pfa_dir / "canonical_state.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SyncError(f"existing {path} is not valid JSON, refusing to overwrite blind: {exc}") from exc


def previous_debts_by_id(previous_state: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if previous_state is None:
        return {}
    debts = previous_state.get("debt_architecture", {}).get("debts", [])
    return {d["id"]: d for d in debts if "id" in d}


def idempotency_key(ts: str, debt_id: str, event_type: str) -> str:
    """sha256(ts+debt_id+event_type), per pfa_debt_event.schema.json / pfa_payment_event.schema.json.

    `ts` is the PFOS row's own updatedAt (export-pfa-snapshot.ts's pfos_updated_at field), not this
    run's wall-clock time, so re-running the sync when PFOS has not changed the row recomputes the
    identical key every time rather than minting a new one on every pass.
    """
    return hashlib.sha256(f"{ts}{debt_id}{event_type}".encode("utf-8")).hexdigest()


def existing_keys(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = entry.get("idempotency_key")
        if key:
            keys.add(key)
    return keys


def balance_field(debt: dict[str, Any]) -> int | None:
    """A debt's "current amount owed", whichever field the exporter populated for its kind."""
    if debt.get("current_balance_milliunits") is not None:
        return debt["current_balance_milliunits"]
    return debt.get("original_amount_milliunits")


def diff_debt_events(
    new_debts: list[dict[str, Any]],
    previous_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """One debt_event per debt that is new or whose balance/status changed since the last sync."""
    events: list[dict[str, Any]] = []
    for debt in new_debts:
        debt_id = debt["id"]
        ts = debt.get("pfos_updated_at") or debt.get("as_of_date")
        prior = previous_by_id.get(debt_id)
        new_balance = balance_field(debt)

        if prior is None:
            event_type = "debt_opened"
            previous_balance = None
        else:
            prior_balance = balance_field(prior)
            if debt.get("status") == "paid_off" and prior.get("status") != "paid_off":
                event_type = "debt_paid_off"
            elif prior_balance != new_balance:
                event_type = "balance_updated"
            elif prior.get("status") != debt.get("status"):
                event_type = "debt_restructured"
            else:
                continue  # nothing PFOS-visible changed for this debt since the last sync
            previous_balance = prior_balance

        events.append(
            {
                "ts": ts,
                "module": "MAL",
                "event_type": event_type,
                "debt_id": debt_id,
                "debt_name": debt.get("name"),
                "debt_type": debt.get("type"),
                "previous_balance_milliunits": previous_balance,
                "new_balance_milliunits": new_balance,
                "amount_milliunits": None,
                "credit_limit_milliunits": debt.get("credit_limit_milliunits"),
                "available_credit_milliunits": debt.get("available_credit_milliunits"),
                "installment_monthly_milliunits": debt.get("installment_monthly_milliunits"),
                "term_remaining_months": debt.get("term_remaining_months"),
                "source": "PFOS_engine",
                "idempotency_key": idempotency_key(ts, debt_id, event_type),
                "notes": debt.get("notes"),
                "privacy_level": "strict_local",
            }
        )
    return events


def append_jsonl(path: Path, entries: list[dict[str, Any]], already_present: set[str]) -> int:
    """Append entries whose idempotency_key is not already in the file. Returns count appended."""
    to_write = [e for e in entries if e["idempotency_key"] not in already_present]
    if not to_write:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        for entry in to_write:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return len(to_write)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    pfa_dir = Path(args.pfa_dir)
    debts_ledger = pfa_dir / "ledgers" / "debts.jsonl"

    try:
        snapshot = run_exporter(args)
        problems = _validate_manual(snapshot)
        if problems:
            raise SyncError("exported snapshot failed validation:\n  " + "\n  ".join(problems))

        previous_state = load_previous_state(pfa_dir)
        previous_by_id = previous_debts_by_id(previous_state)
        new_debts = snapshot.get("debt_architecture", {}).get("debts", [])
        debt_events = diff_debt_events(new_debts, previous_by_id)

        already_present = existing_keys(debts_ledger)
        new_events = [e for e in debt_events if e["idempotency_key"] not in already_present]

        print(
            f"[sync_from_pfos] {len(new_debts)} debt(s) in snapshot, "
            f"{len(debt_events)} changed since last sync, {len(new_events)} not already in the ledger."
        )
        for e in new_events:
            print(f"  + {e['event_type']} debt_id={e['debt_id']} new_balance_milliunits={e['new_balance_milliunits']}")

        if snapshot.get("provenance", {}).get("open_items"):
            print("[sync_from_pfos] open_items from exporter:")
            for item in snapshot["provenance"]["open_items"]:
                print(f"  - {item}")

        if args.dry_run:
            print("[sync_from_pfos] --dry-run: nothing written.")
            return 0

        appended = append_jsonl(debts_ledger, new_events, already_present)

        canonical_state_path = pfa_dir / "canonical_state.json"
        canonical_state_path.parent.mkdir(parents=True, exist_ok=True)
        canonical_state_path.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )

        print(f"[sync_from_pfos] appended {appended} event(s) to {debts_ledger}")
        print(f"[sync_from_pfos] wrote {canonical_state_path}")
        return 0

    except SyncError as exc:
        print(f"[sync_from_pfos] FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
