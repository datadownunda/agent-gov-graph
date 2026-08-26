from copy import deepcopy

from src.trajectory_eval import (
    MULTIAGENT_EXPECTATIONS_PATH,
    MULTIAGENT_TRAJECTORY_PATH,
    evaluate_multiagent_trajectory,
    load_json,
)


def test_multiagent_trajectory_attributes_actor_failure():
    trajectory = load_json(MULTIAGENT_TRAJECTORY_PATH)
    expectations = load_json(MULTIAGENT_EXPECTATIONS_PATH)

    result = evaluate_multiagent_trajectory(
        trajectory,
        expectations,
    )

    assert result["actor_permissions"]["status"] == "FAIL"
    assert result["delegation_authorization"]["status"] == "PASS"
    assert result["recovery_behavior"]["status"] == "PASS"
    assert result["evidence_completeness"]["status"] == "PASS"

    finding = result["actor_permissions"]["findings"][0]

    assert finding["type"] == "actor_prohibited_resource_attempt"
    assert finding["actor_id"] == "complaint-review-agent"
    assert finding["step_id"] == "step-004"
    assert finding["resource"]["id"] == "complaint-789"


def test_multiagent_trajectory_detects_unauthorized_delegation():
    trajectory = deepcopy(
        load_json(MULTIAGENT_TRAJECTORY_PATH)
    )
    expectations = load_json(MULTIAGENT_EXPECTATIONS_PATH)

    for step in trajectory["steps"]:
        if step["step_id"] == "step-002":
            step["target_actor"]["id"] = "complaint-review-agent"

    result = evaluate_multiagent_trajectory(
        trajectory,
        expectations,
    )

    assert result["delegation_authorization"]["status"] == "FAIL"

    finding = result["delegation_authorization"]["findings"][0]

    assert finding["type"] == "unauthorized_delegation"
    assert finding["actor_id"] == "complaint-review-agent"
    assert finding["target_actor_id"] == "complaint-review-agent"