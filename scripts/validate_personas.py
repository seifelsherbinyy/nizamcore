#!/usr/bin/env python3
"""validate_personas.py — schema + opening_voice lint for all personas.

Implements B2.9:
  1. Validate each persona JSON against
     NIZAM__system/schemas/persona.schema.json (where the schema lists
     a field as required, ensure it exists and is non-empty).
  2. opening_voice lint: ensure no persona declares subjective/scored
     inner state language in the file. Allowed objective fields only
     (biometric measurements, ledger names, gate names).

Pure stdlib (no external jsonschema package).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = REPO_ROOT / "NIZAM__system" / "personas"
SCHEMA_PATH = REPO_ROOT / "NIZAM__system" / "schemas" / "persona.schema.json"

# These persona names are the v1.1 set under the locked agent roster.
EXPECTED = ["TAFRIGH", "SHURA", "NAQD", "TARIQ", "MUNAWARA", "BADAN",
            "MARSAD", "HIKMAH", "AHEL", "MAL", "AMMAR"]

# Heuristic forbidden tokens in opening_voice / role / mode that indicate
# subjective scored inner-state — these are reserved for genuine biometric
# data (Hayat/BADAN only).
SUBJECTIVE_REGEX = re.compile(
    r"\b(?:mood_score|happiness_score|self_esteem|confidence_score_inner|"
    r"i\s*feel|i\s*think\s*you\s*are|inner_state_score)\b",
    re.IGNORECASE,
)


def _required_from_schema() -> tuple[set[str], set[str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    top = set(schema.get("required", []))
    runtime = set(
        schema.get("properties", {})
              .get("runtime", {})
              .get("required", [])
    )
    return top, runtime


def _check_required(data: dict, required: set[str]) -> list[str]:
    missing: list[str] = []
    for f in required:
        if f not in data:
            missing.append(f"missing top-level field: {f}")
        elif data[f] in (None, "", [], {}):
            missing.append(f"empty top-level field: {f}")
    return missing


def _check_runtime(data: dict, required_rt: set[str]) -> list[str]:
    rt = data.get("runtime", {})
    if not rt:
        return ["missing runtime block"]
    errs: list[str] = []
    for f in required_rt:
        if f not in rt:
            errs.append(f"missing runtime.{f}")
    return errs


def _check_opening_voice(name: str, data: dict) -> list[str]:
    # Lint only the fields that would surface to the user during runtime
    # (the opening_voice / outputs that the agent emits). Meta-prohibitions
    # in role/mode/tone/voice_constraints/operating_rules are intentional
    # and should not trip the check.
    target_fields = ("opening_voice", "outputs")
    blob_parts: list[str] = []
    for k in target_fields:
        v = data.get(k)
        if v is None:
            continue
        if isinstance(v, str):
            blob_parts.append(v)
        else:
            blob_parts.append(json.dumps(v))
    blob = "\n".join(blob_parts)
    if SUBJECTIVE_REGEX.search(blob):
        return [f"{name}: subjective-state token found in opening_voice/outputs"]
    ov = data.get("opening_voice", "")
    if ov is not None and not isinstance(ov, str):
        return [f"{name}: opening_voice must be a string when present"]
    return []


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"FAIL: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        return 2
    top_req, rt_req = _required_from_schema()

    overall_ok = True
    for name in EXPECTED:
        path = PERSONAS / f"{name}.json"
        if not path.exists():
            print(f"[MISSING] {path}")
            overall_ok = False
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        errs: list[str] = []
        errs += _check_required(data, top_req)
        errs += _check_runtime(data, rt_req)
        errs += _check_opening_voice(name, data)
        if errs:
            overall_ok = False
            print(f"[FAIL] {name}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"[OK]   {name}")

    print()
    if overall_ok:
        print("All personas validated.")
        return 0
    print("Some personas failed validation.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
