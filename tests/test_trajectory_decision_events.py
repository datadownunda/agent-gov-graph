from src.trajectory_decision_events import (
    generate_trajectory_decision_events,
)

from src.trajectory_eval import (
    MULTIAGENT_EXPECTATIONS_PATH,
    MULTIAGENT_TRAJECTORY_PATH,
    load_json,
)


def test_trajectory_generates_two_governance_decision_events():
    trajectory = load_json(
        MULTIAGENT_TRAJECTORY_PATH
    )

    expectations = load_json(
        MULTIAGENT_EXPECTATIONS_PATH
    )

    results = generate_trajectory_decision_events(
        trajectory,
        expectations,
    )

    assert len(results) == 2


def test_generated_decisions_match_observed_trajectory():
    trajectory = load_json(
        MULTIAGENT_TRAJECTORY_PATH
    )

    expectations = load_json(
        MULTIAGENT_EXPECTATIONS_PATH
    )

    results = generate_trajectory_decision_events(
        trajectory,
        expectations,
    )

    for result in results:
        assert (
            result["outcome_matches_observation"]
            is True
        )


def test_decision_events_are_correlated_to_run_and_step():
    trajectory = load_json(
        MULTIAGENT_TRAJECTORY_PATH
    )

    expectations = load_json(
        MULTIAGENT_EXPECTATIONS_PATH
    )

    results = generate_trajectory_decision_events(
        trajectory,
        expectations,
    )

    results_by_step = {
        result["step_id"]: result
        for result in results
    }

    step_001 = results_by_step["step-001"]
    step_004 = results_by_step["step-004"]

    assert (
        step_001["decision_event"]["decision"]["status"]
        == "ALLOW"
    )

    assert (
        step_004["decision_event"]["decision"]["status"]
        == "DENY"
    )

    for step_id, result in results_by_step.items():
        context = result["decision_event"]["context"]

        assert (
            context["run_id"]
            == "run-complaint-multiagent-001"
        )

        assert context["step_id"] == step_id

        assert (
            context["agent_id"]
            == "complaint-review-agent"
        )

        assert (
            result["decision_event"]["policy"]["name"]
            == "employee_complaint_access"
        )

        assert (
            result["decision_event"]["policy"]["version"]
            == "1.0"
        )