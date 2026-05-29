#!/usr/bin/env python3
"""extraction_dry_run.py — offline shape-test for extraction.config.yaml.

B3.2 acceptance:
  - Confirm extraction_confidence bands are monotonic
    (high_min > medium_min > low_min >= drop_below).
  - Run the 6 artifact-separation tests against each fixture row using
    deterministic stub Artifact A (verbatim capture) + stub Artifact B
    (a non-overlapping themes/tensions/loops dict).
  - All 6 tests pass on all 10 inputs.

We do NOT call an LLM here; we exercise the contract that Salman's
extraction output cannot contaminate Amin's verbatim capture, and vice
versa. The actual extraction model is engaged only post-K2/U5.

Pure stdlib.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CFG = REPO / "NIZAM__system" / "config" / "extraction.config.yaml"
FIX = REPO / "NIZAM__system" / "config" / "fixtures" / "extraction_10_inputs.jsonl"


def _read_yaml_minimal(path: Path) -> dict:
    sys.path.insert(0, str(Path(__file__).parent))
    import router_dry_run as r
    return r._read_yaml(path)


def _stub_artifact_a(capture: str) -> dict:
    return {"capture": capture, "owner": "Amin", "fields": ["capture", "owner"]}


def _stub_artifact_b(row: dict) -> dict:
    return {
        "owner": "Salman",
        "themes": row.get("expected_themes", []),
        "tensions": row.get("expected_tensions", []),
        "loops": row.get("expected_loops", []),
        "source_offsets": [(0, len(row["capture"]))],
        "quoted_snippets": [],
    }


def six_tests(art_a: dict, art_b: dict, capture: str) -> dict:
    return {
        "artifact_a_contains_zero_themes": "themes" not in art_a,
        "artifact_a_contains_zero_tensions": "tensions" not in art_a,
        "artifact_a_contains_zero_loops": "loops" not in art_a,
        "artifact_a_preserves_verbatim_capture": art_a.get("capture") == capture,
        "artifact_b_cites_artifact_a_offsets": (
            isinstance(art_b.get("source_offsets"), list)
            and all(isinstance(o, (list, tuple)) and len(o) == 2
                    for o in art_b["source_offsets"])
            and all(0 <= o[0] <= o[1] <= len(capture)
                    for o in art_b["source_offsets"])
        ),
        "artifact_b_no_fabricated_quotes": all(
            q in capture for q in art_b.get("quoted_snippets", [])
        ),
    }


def main() -> int:
    cfg = _read_yaml_minimal(CFG)
    bands = cfg.get("extraction_confidence", {})
    hi = float(bands.get("high_min", 0))
    md = float(bands.get("medium_min", 0))
    lo = float(bands.get("low_min", 0))
    drop = float(bands.get("drop_below", 0))
    monotone = hi > md > lo >= drop
    print(f"confidence bands monotone? {monotone} "
          f"(high={hi} medium={md} low={lo} drop={drop})")
    if not monotone:
        return 1

    total = 0
    all_pass_count = 0
    with FIX.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            total += 1
            capture = row["capture"]
            art_a = _stub_artifact_a(capture)
            art_b = _stub_artifact_b(row)
            results = six_tests(art_a, art_b, capture)
            all_pass = all(results.values())
            if all_pass:
                all_pass_count += 1
            mark = "OK " if all_pass else "FAIL"
            print(f"  [{mark}] capture={capture[:50]!r}  results={results}")

    expected = float(cfg.get("fixture", {}).get(
        "expected_separation_pass_rate", 1.00))
    actual = all_pass_count / total if total else 0.0
    print(f"separation pass rate: {actual:.0%} (expected={expected:.0%})")
    return 0 if actual >= expected else 1


if __name__ == "__main__":
    sys.exit(main())
