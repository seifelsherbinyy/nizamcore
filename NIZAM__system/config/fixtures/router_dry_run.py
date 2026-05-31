#!/usr/bin/env python3
"""router_dry_run.py — offline dry-run via nizam_router.resolve (IR-1..IR-8).

B3.1 acceptance: full resolve path (not raw exemplar Jaccard), confidence bands,
IR-6 SUKOON overlay visible when fixture sets simulate_sukoon_hot.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO / "NIZAM__system" / "config"
ROUTER_YAML = CONFIG_DIR / "router.config.yaml"
EXEMPLARS_YAML = CONFIG_DIR / "intent_exemplars.yaml"

sys.path.insert(0, str(CONFIG_DIR))
import nizam_router  # noqa: E402


def _fixture_path(config: dict) -> Path:
    rel = (config.get("fixture") or {}).get("path", "")
    return REPO / rel if rel else REPO / "NIZAM__system/config/fixtures/router_13_inputs.jsonl"


def main() -> int:
    config = nizam_router.load_config(ROUTER_YAML)
    exemplars = nizam_router.load_exemplars(EXEMPLARS_YAML)
    fixture = _fixture_path(config)
    min_acc = float((config.get("fixture") or {}).get("expected_routing_min_accuracy", 0.80))

    results: list[dict] = []
    matches = 0
    total = 0
    with fixture.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            total += 1
            sukoon_hot = bool(row.get("simulate_sukoon_hot"))
            out = nizam_router.resolve(
                row["input"], config, exemplars, sukoon_hot=sukoon_hot,
            )
            ok = out["target"] == row.get("expected_target")
            if ok:
                matches += 1
            results.append({**out, "input": row["input"], "label": row.get("label"),
                            "expected_target": row.get("expected_target"), "match": ok})

    acc = matches / total if total else 0.0
    print(f"router dry-run (nizam_router.resolve): {matches}/{total} matches "
          f"(acc={acc:.0%}, min={min_acc:.0%})")
    print()
    for r in results:
        mark = "OK " if r["match"] else "FAIL"
        label = (" [" + r["label"] + "]") if r.get("label") else ""
        steps = " -> ".join(r["resolver_steps"])
        ir6 = "IR-6:overlay=YES,target=UNCHANGED" if r.get("target_swap_blocked_by_ir6") else "IR-6:overlay=no"
        print(f"  [{mark}]{label} target={r['target']:<8} conf={r['confidence']:.2f} "
              f"action={r['route_action']:<16} {ir6}")
        print(f"         steps: {steps}")
        print(f"         input: {r['input'][:72]!r}")
        if r.get("expected_target") and not r["match"]:
            print(f"         WANT: {r['expected_target']}")
        print()

    return 0 if acc >= min_acc else 1


if __name__ == "__main__":
    sys.exit(main())
