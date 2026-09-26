from NIZAM__system.image_benchmark.benchmark_harness import Candidate, blind_candidates, pairwise_schedule, weighted_score, hard_gate_pass, pareto_frontier, agreement_rate


def test_blinding_is_stable_and_hides_producer():
    c = Candidate("a1", "x", "P0", "openai", "unknown", "file.png", 0.0)
    x = blind_candidates("r1", [c])[0]
    y = blind_candidates("r1", [c])[0]
    assert x["evaluator"] == y["evaluator"]
    assert "provider" not in x["evaluator"]
    assert "model" not in x["evaluator"]


def test_pair_count():
    cs = [Candidate("a1", str(i), "P0", "p", "m", f"{i}.png", 0) for i in range(3)]
    assert len(pairwise_schedule(blind_candidates("r", cs))) == 3


def test_missing_dimensions_not_imputed():
    assert weighted_score({"identity_subject_preservation": 80}) == 80


def test_hard_gates():
    assert hard_gate_pass({"identity_failure": False})
    assert not hard_gate_pass({"identity_failure": True})


def test_pareto():
    rows = [
        {"id": "a", "accepted": True, "quality": 90, "cost": 1, "latency": 10},
        {"id": "b", "accepted": True, "quality": 85, "cost": 0.1, "latency": 5},
        {"id": "c", "accepted": True, "quality": 80, "cost": 2, "latency": 20},
    ]
    assert [x["id"] for x in pareto_frontier(rows)] == ["a", "b"]


def test_agreement():
    j = [{"asset_id": "x", "a": "1", "b": "2", "winner": "a"}]
    h = [{"asset_id": "x", "a": "1", "b": "2", "winner": "a"}]
    assert agreement_rate(j, h) == 1.0
