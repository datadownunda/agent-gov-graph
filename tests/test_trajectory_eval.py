from copy import deepcopy

from src.trajectory_eval import (
    EXPECTATIONS_PATH,
    TRAJECTORY_PATH,
    evaluate_trajectory,
    load_json,
)


def test_trajectory_detects_agent_failure_but_control_success():
    trajectory = load_json(TRAJECTORY_PATH)
    expectations = load_json(EXPECTATIONS_PATH)

    result = evaluate_trajectory(
        trajectory,
        expectations,
    )

    assert result["agent_behavior"]["status"] == "FAIL"
    assert result["control_effectiveness"]["status"] == "PASS"
    assert result["recovery_behavior"]["status"] == "PASS"
    assert result["evidence_completeness"]["status"] == "PASS"

    assert (
        result["agent_behavior"]["findings"][0]["type"]
        == "prohibited_resource_attempt"
    )

    assert (
        result["agent_behavior"]["findings"][0]["step_id"]
        == "step-003"
    )


def test_control_fails_if_prohibited_access_is_allowed():
    trajectory = deepcopy(
        load_json(TRAJECTORY_PATH)
    )
    expectations = load_json(EXPECTATIONS_PATH)

    for step in trajectory["steps"]:
        if step["step_id"] == "step-003":
            step["observed_outcome"] = "ALLOW"

    result = evaluate_trajectory(
        trajectory,
        expectations,
    )

    assert result["agent_behavior"]["status"] == "FAIL"
    assert result["control_effectiveness"]["status"] == "FAIL"

    assert (
        result["control_effectiveness"]["findings"][0]["type"]
        == "control_failed_to_deny"
    )