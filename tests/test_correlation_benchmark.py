from experiments.foreign_opa.benchmark import build_case, evaluate, run_matcher, scenarios


def measure(**kwargs):
    observations, truth = build_case("test", groups=4, **kwargs)
    return evaluate(run_matcher(observations), truth)


def test_baseline_and_repetition_failure():
    baseline = measure(repetitions=1)
    assert baseline["precision"] == baseline["recall"] == 1
    repeated = measure(repetitions=2, separation_ns=0)
    assert repeated["precision"] is None
    assert repeated["recall"] == 0
    assert repeated["ambiguity_rate"] == 1


def test_skew_alias_produces_wrong_unique_links():
    result = measure(repetitions=5, separation_ns=5_000_000_000, skew_ns=5_000_000_000)
    assert result["false_accepted_links"] == 16
    assert result["precision"] == result["recall"] == 0
    assert result["unmatched_rate"] == 0.2


def test_missing_and_replacement_impostor_denominators():
    result = measure(missing_fraction=0.5)
    assert result["recall"] == 0.5
    assert result["observable_recall"] == 1
    assert result["unmatched_rate"] == 1 / 3
    replaced = measure(missing_fraction=1, impostor_fraction=1)
    assert replaced["false_accepted_links"] == 4
    assert replaced["precision"] == replaced["recall"] == 0
    assert replaced["observable_recall"] is None


def test_ground_truth_is_not_in_matcher_input_and_runs_are_reproducible():
    inputs, truth = build_case("case", repetitions=2)
    assert (inputs, truth) == build_case("case", repetitions=2)
    assert set(inputs) == {"opa", "journal", "window_seconds"}
    allowed = {"evidence_ref", "actor", "action", "resource_id", "resource_type", "observed_at"}
    assert all(set(record) == allowed for source in ("opa", "journal") for record in inputs[source])
    assert not ({r["evidence_ref"] for r in inputs["opa"]} &
                {r["evidence_ref"] for r in inputs["journal"]})


def test_scenario_names_are_unique():
    names = [name for name, _ in scenarios()]
    assert len(names) == len(set(names))


def test_benchmark_worker_has_no_truth_artifact_and_results_are_auditable(tmp_path, monkeypatch):
    import json
    from experiments.foreign_opa import benchmark as module

    output = tmp_path / "results"
    original_run = module.subprocess.run

    def inspect_worker(command, **kwargs):
        assert not (output / "ground-truth.json").exists()
        payload = json.loads((output / "matcher-inputs.json").read_text())
        assert all(set(case) == {"opa", "journal", "window_seconds"} for case in payload.values())
        return original_run(command, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", inspect_worker)
    rows = module.benchmark(output, groups=4)
    findings = json.loads((output / "findings.json").read_text())
    truth = json.loads((output / "ground-truth.json").read_text())
    assert len(rows) == 107
    for row in rows:
        scores = module.evaluate(findings[row["scenario"]], truth[row["scenario"]])
        assert all(row[key] == value for key, value in scores.items())
    assert (output / "README.md").is_file()
    assert (output / "metrics.csv").is_file()
