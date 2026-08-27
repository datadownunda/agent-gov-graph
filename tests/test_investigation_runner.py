from src.investigation_runner import (
    INVESTIGATION_PATH,
    load_json,
    run_control,
    run_experiment,
    run_investigation,
)


def test_control_run_reproduces_prohibited_attempt():
    control_run = run_control()

    assert (
        control_run["conditions"]["resource_selection_constraints"]
        == "original"
    )

    assert (
        control_run["conditions"]["task_context_specificity"]
        == "original"
    )

    assert (
        control_run["observation"]["prohibited_resource_attempt"]
        is True
    )

    assert (
        control_run["observation"]["governance_decision"]
        == "DENY"
    )


def test_each_experiment_changes_only_its_independent_variable():
    investigation = load_json(INVESTIGATION_PATH)

    control_run = run_control()

    for experiment in investigation["experiments"]:
        treatment_run = run_experiment(experiment)

        control_conditions = control_run["conditions"]
        treatment_conditions = treatment_run["conditions"]

        changed_variables = [
            variable
            for variable in control_conditions
            if (
                control_conditions[variable]
                != treatment_conditions[variable]
            )
        ]

        assert changed_variables == [
            experiment["independent_variable"]
        ]


def test_investigation_supports_both_hypotheses_without_root_cause_claim():
    result = run_investigation()

    assert len(result["experiment_results"]) == 2

    relationships = [
        experiment["comparison"]["relationship"]
        for experiment in result["experiment_results"]
    ]

    assert relationships == [
        "SUPPORTS",
        "SUPPORTS",
    ]

    control_run_ids = {
        experiment["control_run_id"]
        for experiment in result["experiment_results"]
    }

    assert len(control_run_ids) == 1