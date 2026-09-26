from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

RUBRIC = {
    "identity_subject_preservation": 20,
    "photorealism_natural_texture": 15,
    "requested_edit_accuracy": 15,
    "edit_locality_unrequested_changes": 15,
    "reference_realism_alignment": 10,
    "lighting_shadow_geometry_consistency": 10,
    "artifact_anatomy_text_reflection_quality": 10,
    "composition_social_media_usability": 5,
}

HARD_GATES = {
    "identity_failure": False,
    "major_unrequested_change": False,
    "gross_artifact": False,
}

@dataclass(frozen=True)
class Candidate:
    asset_id: str
    candidate_id: str
    path_code: str
    provider: str
    model: str
    output_ref: str
    marginal_cost_usd: float
    latency_seconds: float | None = None
    retry_count: int = 0


def stable_blind_id(run_id: str, candidate_id: str) -> str:
    digest = hashlib.sha256(f"{run_id}:{candidate_id}".encode()).hexdigest()[:10]
    return f"C-{digest.upper()}"


def blind_candidates(run_id: str, candidates: Iterable[Candidate]) -> list[dict[str, Any]]:
    blinded = []
    for c in candidates:
        row = asdict(c)
        row["blind_id"] = stable_blind_id(run_id, c.candidate_id)
        evaluator = {
            "asset_id": c.asset_id,
            "blind_id": row["blind_id"],
            "output_ref": c.output_ref,
        }
        blinded.append({"private": row, "evaluator": evaluator})
    return blinded


def pairwise_schedule(blinded: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_asset: dict[str, list[dict[str, Any]]] = {}
    for row in blinded:
        by_asset.setdefault(row["private"]["asset_id"], []).append(row)
    pairs: list[dict[str, str]] = []
    for asset_id, rows in by_asset.items():
        for a, b in itertools.combinations(rows, 2):
            ids = sorted([a["evaluator"]["blind_id"], b["evaluator"]["blind_id"]])
            pairs.append({"asset_id": asset_id, "a": ids[0], "b": ids[1]})
    return pairs


def weighted_score(dimension_scores: dict[str, float]) -> float | None:
    """Exploratory score only. Missing dimensions remain missing; never impute them."""
    if not dimension_scores:
        return None
    used = [(RUBRIC[k], float(v)) for k, v in dimension_scores.items() if k in RUBRIC]
    if not used:
        return None
    weight_sum = sum(w for w, _ in used)
    return sum(w * v for w, v in used) / weight_sum


def hard_gate_pass(flags: dict[str, bool]) -> bool:
    return not any(bool(flags.get(k, False)) for k in HARD_GATES)


def pareto_frontier(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Maximize quality, minimize cost and latency among accepted candidates."""
    valid = [r for r in rows if r.get("accepted") and r.get("quality") is not None]
    front: list[dict[str, Any]] = []
    for x in valid:
        dominated = False
        for y in valid:
            if x is y:
                continue
            yq, xq = float(y["quality"]), float(x["quality"])
            yc, xc = float(y.get("cost", math.inf)), float(x.get("cost", math.inf))
            yl, xl = float(y.get("latency", math.inf)), float(x.get("latency", math.inf))
            no_worse = yq >= xq and yc <= xc and yl <= xl
            strictly_better = yq > xq or yc < xc or yl < xl
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            front.append(x)
    return sorted(front, key=lambda r: (-float(r["quality"]), float(r.get("cost", math.inf))))


def agreement_rate(judge_rows: list[dict[str, Any]], human_rows: list[dict[str, Any]]) -> float | None:
    human = {(r["asset_id"], r["a"], r["b"]): r["winner"] for r in human_rows}
    hits = total = 0
    for r in judge_rows:
        key = (r["asset_id"], r["a"], r["b"])
        if key in human and r.get("winner") in {"a", "b", "tie"}:
            total += 1
            hits += int(r["winner"] == human[key])
    return hits / total if total else None


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> None:
    run = Path(args.run_dir)
    for d in ["sources", "candidates", "refs", "eval/objective", "eval/judges", "eval/human", "reports"]:
        (run / d).mkdir(parents=True, exist_ok=True)
    write_json(run / "run.json", {
        "run_id": args.run_id,
        "paid_calls_enabled": False,
        "rubric": RUBRIC,
        "hard_gates": list(HARD_GATES),
        "notes": "Paid generation is disabled by default. P0 ChatGPT outputs are imported manually.",
    })
    print(run)


def cmd_blind(args: argparse.Namespace) -> None:
    rows = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    candidates = [Candidate(**r) for r in rows]
    blinded = blind_candidates(args.run_id, candidates)
    out = Path(args.out)
    write_json(out, blinded)
    write_json(out.with_name(out.stem + "_pairs.json"), pairwise_schedule(blinded))


def cmd_pareto(args: argparse.Namespace) -> None:
    rows = json.loads(Path(args.results).read_text(encoding="utf-8"))
    write_json(Path(args.out), pareto_frontier(rows))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NIZAM image-edit benchmark harness")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("run_dir")
    s.add_argument("--run-id", required=True)
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("blind")
    s.add_argument("--run-id", required=True)
    s.add_argument("--candidates", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_blind)

    s = sub.add_parser("pareto")
    s.add_argument("--results", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_pareto)
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
